# src/notification_scheduler.py
"""
Notification Scheduler
======================

Manages notification timing with flexible configuration:
- Immediate notifications: Send on each detection
- Daily summary: Send summary at specified time (can be combined with immediate)

The system now supports combining immediate notifications with daily summaries,
allowing users to get both real-time alerts and end-of-day reports.
"""

import logging
import os
import smtplib
import threading
import time as time_module
from datetime import datetime, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Callable, Dict, List, Optional

from src.database import Database
from src.notification import DiscordNotifier, EmailNotifier

logger = logging.getLogger("SwineMonitor.Scheduler")


class NotificationScheduler:
    """
    Manages notification scheduling with immediate + daily summary support.
    
    The scheduler can now operate in two modes simultaneously:
    - Immediate: Send notification immediately when detection occurs
    - Daily Summary: Collect detections and send summary at specified time
    
    Both can be enabled at the same time.
    
    Attributes:
        immediate_enabled: Whether to send immediate notifications
        daily_summary_enabled: Whether to send daily summary
        daily_summary_time: Time to send daily summary (default 09:00)
        email_enabled: Whether email notifications are enabled
        discord_enabled: Whether Discord notifications are enabled
    """
    
    def __init__(
        self,
        email_notifier: Optional[EmailNotifier] = None,
        discord_notifier: Optional[DiscordNotifier] = None,
        db: Optional[Database] = None,
    ) -> None:
        """
        Initialize the notification scheduler.
        
        Args:
            email_notifier: EmailNotifier instance for email notifications
            discord_notifier: DiscordNotifier instance for Discord notifications
            db: Database instance for queuing notifications
        """
        self.email = email_notifier
        self.discord = discord_notifier
        self.db = db
        
        # Notification modes (can be combined)
        self.immediate_enabled: bool = True
        self.daily_summary_enabled: bool = False
        self.daily_summary_time: time = time(9, 0)  # Default 09:00
        
        # Channel enabled flags
        self.email_enabled: bool = True
        self.discord_enabled: bool = False
        
        # Today's detections (for daily summary)
        self._today_detections: List[Dict] = []
        self._lock = threading.Lock()
        
        # Background scheduler
        self._scheduler_thread: Optional[threading.Thread] = None
        self._running: bool = False
        
        # Callbacks
        self._on_notification_sent: Optional[Callable] = None
    
    @classmethod
    def from_config(cls, config: Dict[str, Any], db: Optional[Database] = None) -> "NotificationScheduler":
        """
        Create scheduler from configuration dictionary.
        
        Args:
            config: Dictionary with notification settings
            db: Database instance
            
        Returns:
            NotificationScheduler instance
        """
        scheduler = cls(db=db)
        
        # Set notification modes
        scheduler.immediate_enabled = config.get("immediate_enabled", True)
        scheduler.daily_summary_enabled = config.get("daily_summary_enabled", False)
        
        # Set daily summary time
        daily_str = config.get("daily_summary_time", "09:00")
        scheduler.daily_summary_time = cls._parse_time(daily_str)
        
        # Email configuration
        if config.get("email_enabled", True):
            scheduler.email = EmailNotifier.from_config(config)
            scheduler.email_enabled = True
        else:
            scheduler.email_enabled = False
        
        # Discord configuration
        discord_url = config.get("discord_webhook_url") or os.getenv("DISCORD_WEBHOOK_URL")
        if discord_url and config.get("discord_enabled", False):
            scheduler.discord = DiscordNotifier(discord_url)
            scheduler.discord_enabled = True
        else:
            scheduler.discord_enabled = False
        
        return scheduler
    
    @staticmethod
    def _parse_time(time_str: str) -> time:
        """Parse time string (HH:MM) to time object."""
        try:
            parts = time_str.split(":")
            return time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return time(9, 0)
    
    def start(self) -> None:
        """Start the background scheduler thread."""
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="NotificationScheduler"
        )
        self._scheduler_thread.start()
        
        mode_desc = []
        if self.immediate_enabled:
            mode_desc.append("Immediate")
        if self.daily_summary_enabled:
            mode_desc.append(f"Daily@{self.daily_summary_time.strftime('%H:%M')}")
        
        logger.info(f"Notification scheduler started (modes: {', '.join(mode_desc) or 'None'})")
    
    def stop(self) -> None:
        """Stop the background scheduler thread."""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2)
        logger.info("Notification scheduler stopped")
    
    def set_immediate_enabled(self, enabled: bool) -> None:
        """Enable or disable immediate notifications."""
        self.immediate_enabled = enabled
        logger.info(f"Immediate notifications: {'enabled' if enabled else 'disabled'}")
    
    def set_daily_summary_enabled(self, enabled: bool) -> None:
        """Enable or disable daily summary."""
        self.daily_summary_enabled = enabled
        logger.info(f"Daily summary: {'enabled' if enabled else 'disabled'}")
    
    def set_daily_summary_time(self, hour: int, minute: int = 0) -> None:
        """Set the daily summary time."""
        self.daily_summary_time = time(hour, minute)
        logger.info(f"Daily summary time set to: {self.daily_summary_time}")
    
    def on_detection(self, detection: Dict[str, Any]) -> None:
        """
        Handle a new detection event.
        
        Args:
            detection: Dictionary with detection info:
                - barn_id: str
                - timestamp: str
                - confidence: float
                - image_path: str (optional)
        """
        logger.info(
            f"Detection received: {detection.get('barn_id')} "
            f"({detection.get('confidence', 0):.1%})"
        )
        
        # Always record for daily summary
        if self.daily_summary_enabled:
            self._queue_detection(detection)
        
        # Send immediate notification if enabled
        if self.immediate_enabled:
            self._send_immediate(detection)
    
    def _send_immediate(self, detection: Dict[str, Any]) -> None:
        """Send notification immediately."""
        barn_id = detection.get("barn_id", "Unknown")
        class_name = detection.get("class_name", "Unknown")
        conf = detection.get("confidence", 0)
        timestamp = detection.get("timestamp", "")
        image_path = detection.get("image_path")
        
        # Email
        if self.email_enabled and self.email:
            self.email.send(
                subject=f"[Swine Monitor] {class_name} Detected",
                detections=[detection]
            )
            logger.info("Immediate email notification sent")
        
        # Discord
        if self.discord_enabled and self.discord:
            msg = (
                f"🐷 **{class_name} Detected**\n"
                f"• Barn: {barn_id}\n"
                f"• Class: {class_name}\n"
                f"• Confidence: {conf:.1%}\n"
                f"• Time: {timestamp}"
            )
            self.discord.send(msg, image_path)
            logger.info("Immediate Discord notification sent")
        
        # Callback
        if self._on_notification_sent:
            self._on_notification_sent("immediate", [detection])
    
    def _queue_detection(self, detection: Dict[str, Any]) -> None:
        """Add detection to today's queue for daily summary."""
        with self._lock:
            self._today_detections.append(detection)
            logger.debug(f"Detection queued. Total today: {len(self._today_detections)}")
    
    def _scheduler_loop(self) -> None:
        """Background loop to check and send daily summary."""
        last_summary_date: Optional[str] = None
        
        while self._running:
            if not self.daily_summary_enabled:
                time_module.sleep(60)
                continue
            
            now = datetime.now()
            current_time = now.time()
            current_date = now.strftime("%Y-%m-%d")
            
            # Check if it's time to send daily summary
            if (self._is_target_time(current_time, self.daily_summary_time) and 
                last_summary_date != current_date):
                
                self._send_daily_summary()
                last_summary_date = current_date
            
            time_module.sleep(30)
    
    def _is_target_time(self, current: time, target: time) -> bool:
        """Check if current time is within 1 minute of target time."""
        current_minutes = current.hour * 60 + current.minute
        target_minutes = target.hour * 60 + target.minute
        return abs(current_minutes - target_minutes) <= 1
    
    def _send_daily_summary(self) -> None:
        """Send daily summary with all detections from the past 24 hours."""
        with self._lock:
            detections = self._today_detections.copy()
            self._today_detections.clear()
        
        detection_count = len(detections)
        logger.info(f"Sending daily summary: {detection_count} detections")
        
        # Email - always send, even with no detections
        if self.email_enabled and self.email:
            if detection_count > 0:
                self.email.send(
                    subject=f"[Swine Monitor] Daily Summary ({detection_count} detections)",
                    detections=detections
                )
            else:
                self._send_no_detection_email()
        
        # Discord - always send status
        if self.discord_enabled and self.discord:
            if detection_count > 0:
                summary_lines = ["📊 **Daily Summary**", ""]
                for d in detections[:10]:
                    barn = d.get("barn_id", "?")
                    cls = d.get("class_name", "?")
                    conf = d.get("confidence", 0)
                    ts = d.get("timestamp", "?")
                    summary_lines.append(f"• {barn} [{cls}]: {conf:.1%} @ {ts}")
                
                if len(detections) > 10:
                    summary_lines.append(f"... and {len(detections) - 10} more")
                
                self.discord.send("\n".join(summary_lines))
            else:
                self.discord.send(
                    "📊 **Daily Summary**\n\n"
                    "✅ No mating behavior detected during the past 24 hours."
                )
        
        # Callback
        if self._on_notification_sent:
            self._on_notification_sent("daily", detections)
    
    def _send_no_detection_email(self) -> None:
        """Send email when no detections occurred during the day."""
        body = f"""Swine Monitor - Daily Summary
{'=' * 40}

Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ No mating behavior was detected during the past 24 hours.

This is a routine status report confirming that the monitoring system
is operating normally and no mating activity was observed.

{'=' * 40}
This is an automated message from Swine Monitor System.
"""
        
        # Guard against None email
        if not self.email:
            logger.warning("Cannot send no-detection email: email not configured")
            return
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email.smtp_user
            msg["To"] = self.email.recipient_email
            msg["Subject"] = "[Swine Monitor] Daily Summary - No Detections"
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            with smtplib.SMTP(self.email.smtp_host, self.email.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.email.smtp_user, self.email.smtp_password)
                server.send_message(msg)
            
            logger.info(f"No-detection email sent to {self.email.recipient_email}")
        except Exception as e:
            logger.error(f"Failed to send no-detection email: {e}")
    
    def get_pending_count(self) -> int:
        """Get the number of pending detections for daily summary."""
        with self._lock:
            return len(self._today_detections)
    
    def force_send_summary(self) -> None:
        """Manually trigger sending of daily summary."""
        logger.info("Force sending daily summary")
        self._send_daily_summary()
    
    def clear_pending(self) -> None:
        """Clear all pending detections without sending."""
        with self._lock:
            count = len(self._today_detections)
            self._today_detections.clear()
        logger.info(f"Cleared {count} pending detections")
    
    def set_notification_callback(self, callback: Callable) -> None:
        """Set callback function for notification events."""
        self._on_notification_sent = callback
    
    def send_test_notification(self, test_email: bool = True, test_discord: bool = True) -> Dict[str, Any]:
        """
        Send test notifications to verify configuration.
        
        Args:
            test_email: Whether to send test email
            test_discord: Whether to send test Discord message
            
        Returns:
            Dictionary with results:
                - email_success: bool
                - email_message: str
                - discord_success: bool
                - discord_message: str
        """
        results = {
            "email_success": False,
            "email_message": "",
            "discord_success": False,
            "discord_message": "",
        }
        
        # Test Email
        if test_email:
            if not self.email_enabled or not self.email:
                results["email_message"] = "Email not configured"
            else:
                try:
                    test_body = f"""Swine Monitor - Test Email
{'=' * 40}

This is a test email to verify your notification settings.

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you received this email, your email notifications are working correctly!

{'=' * 40}
"""
                    msg = MIMEMultipart()
                    msg["From"] = self.email.smtp_user
                    msg["To"] = self.email.recipient_email
                    msg["Subject"] = "[Swine Monitor] Test Notification"
                    msg.attach(MIMEText(test_body, "plain", "utf-8"))
                    
                    with smtplib.SMTP(self.email.smtp_host, self.email.smtp_port, timeout=30) as server:
                        server.starttls()
                        server.login(self.email.smtp_user, self.email.smtp_password)
                        server.send_message(msg)
                    
                    results["email_success"] = True
                    results["email_message"] = f"Test email sent to {self.email.recipient_email}"
                    logger.info(results["email_message"])
                    
                except smtplib.SMTPAuthenticationError:
                    results["email_message"] = "Authentication failed - check username/password"
                    logger.error(results["email_message"])
                except smtplib.SMTPException as e:
                    results["email_message"] = f"SMTP error: {e}"
                    logger.error(results["email_message"])
                except Exception as e:
                    results["email_message"] = f"Error: {e}"
                    logger.error(results["email_message"])
        
        # Test Discord
        if test_discord:
            if not self.discord_enabled:
                results["discord_message"] = "Discord not enabled"
            elif not self.discord or not self.discord.webhook_url:
                results["discord_success"] = False
                results["discord_message"] = "Discord webhook URL not configured"
            else:
                try:
                    import requests
                    test_msg = (
                        "🧪 **Swine Monitor - Test Notification**\n\n"
                        f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        "If you see this message, Discord notifications are working!"
                    )
                    response = requests.post(
                        self.discord.webhook_url,
                        json={"content": test_msg},
                        timeout=10
                    )
                    if response.status_code in [200, 204]:
                        results["discord_success"] = True
                        results["discord_message"] = "Test message sent to Discord"
                        logger.info(results["discord_message"])
                    else:
                        results["discord_message"] = f"Discord error: {response.status_code}"
                        logger.error(results["discord_message"])
                except Exception as e:
                    results["discord_message"] = f"Error: {e}"
                    logger.error(results["discord_message"])
        
        return results


# =============================================================================
# Convenience function for quick setup
# =============================================================================

def create_scheduler_from_env(db: Optional[Database] = None) -> NotificationScheduler:
    """
    Create a NotificationScheduler using environment variables.
    
    Environment variables used:
        - SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAIL (for email)
        - DISCORD_WEBHOOK_URL (for Discord)
        - IMMEDIATE_ENABLED (true/false)
        - DAILY_SUMMARY_ENABLED (true/false)
        - DAILY_SUMMARY_TIME (HH:MM format)
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    # Read enabled flags from environment
    master_enabled = os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"
    email_enabled_env = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
    discord_enabled_env = os.getenv("DISCORD_ENABLED", "false").lower() == "true"
    
    immediate_enabled = os.getenv("IMMEDIATE_ENABLED", "true").lower() == "true"
    daily_enabled = os.getenv("DAILY_SUMMARY_ENABLED", "false").lower() == "true"
    
    # Apply master switch
    if not master_enabled:
        immediate_enabled = False
        daily_enabled = False
    
    scheduler = NotificationScheduler(db=db)
    
    # Set notification modes
    scheduler.immediate_enabled = immediate_enabled
    scheduler.daily_summary_enabled = daily_enabled
    scheduler.daily_summary_time = NotificationScheduler._parse_time(
        os.getenv("DAILY_SUMMARY_TIME", "09:00")
    )
    
    # Email configuration
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_user = os.getenv("SMTP_USER", "")
    if email_enabled_env and smtp_user and smtp_password:
        scheduler.email = EmailNotifier(
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            recipient_email=os.getenv("RECIPIENT_EMAIL", ""),
        )
        scheduler.email_enabled = True
    else:
        scheduler.email_enabled = False
    
    # Discord configuration
    discord_url = os.getenv("DISCORD_WEBHOOK_URL", "")
    if discord_enabled_env and discord_url:
        scheduler.discord = DiscordNotifier(discord_url)
        scheduler.discord_enabled = True
    else:
        scheduler.discord_enabled = False
    
    return scheduler


# =============================================================================
# Test code
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("Notification Scheduler Test")
    print("=" * 50)
    
    scheduler = create_scheduler_from_env()
    
    print(f"\nImmediate Enabled: {scheduler.immediate_enabled}")
    print(f"Daily Summary Enabled: {scheduler.daily_summary_enabled}")
    print(f"Daily Summary Time: {scheduler.daily_summary_time}")
    print(f"Email Enabled: {scheduler.email_enabled}")
    print(f"Discord Enabled: {scheduler.discord_enabled}")
    
    # Test notification sending
    print("\n--- Testing notification ---")
    results = scheduler.send_test_notification()
    print(f"Email: {'✅' if results['email_success'] else '❌'} {results['email_message']}")
    print(f"Discord: {'✅' if results['discord_success'] else '❌'} {results['discord_message']}")
    
    time_module.sleep(3)
    print("\n✅ Test completed!")
