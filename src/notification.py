"""
Notification Module
===================
Provides notification capabilities via:
- Discord (Webhook) - Original implementation
- Email (SMTP/Gmail) - New implementation

Both notifiers use async (threaded) sending to avoid blocking the main thread.
"""

import requests
import os
import logging
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import time

# Load environment variables from .env
load_dotenv()

# Logger
logger = logging.getLogger("SwineMonitor.Notifier")


# =============================================================================
# Discord Notifier (Original - Kept for backward compatibility)
# =============================================================================

class DiscordNotifier:
    """Send notifications to Discord via Webhook."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)

    def send(self, message: str, image_path: Optional[str] = None):
        """
        Send a message and optional image to Discord via Webhook.
        Non-blocking (async via thread).
        """
        if not self.webhook_url:
            logger.warning("No Discord webhook URL provided, skipping notification.")
            return

        thread = threading.Thread(
            target=self._send_sync,
            args=(message, image_path),
            daemon=True,
        )
        thread.start()

    def _send_sync(self, message: str, image_path: Optional[str] = None):
        """Synchronous send (called in thread)."""
        payload = {"content": message}

        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    files = {"file": (os.path.basename(image_path), f.read())}
                response = requests.post(
                    self.webhook_url, data=payload, files=files, timeout=30
                )
            else:
                response = requests.post(self.webhook_url, json=payload, timeout=30)

            if response.status_code in [200, 204]:
                logger.info("Discord notification sent successfully.")
            else:
                logger.error(
                    f"Discord notification failed: {response.status_code}, {response.text}"
                )

        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")


# Alias for backward compatibility
Notifier = DiscordNotifier


# =============================================================================
# Email Notifier (New - Gmail SMTP)
# =============================================================================

class EmailNotifier:
    """Send notifications via Email (SMTP)."""
    
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        recipient_email: str = "",
        enabled: bool = True,
    ):
        """
        Initialize Email Notifier.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port (587 for TLS)
            smtp_user: SMTP username (email address)
            smtp_password: SMTP password (decrypted)
            recipient_email: Email address to send notifications to
            enabled: Whether email notifications are enabled
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.recipient_email = recipient_email
        self.enabled = enabled and bool(smtp_user and smtp_password and recipient_email)
    
    @classmethod
    def from_config(cls, config: dict) -> "EmailNotifier":
        """
        Create EmailNotifier from configuration dictionary.
        
        Args:
            config: Dictionary with email settings
            
        Returns:
            EmailNotifier instance
        """
        from .encryption import decrypt_password
        
        encrypted_password = config.get("smtp_password_encrypted", "")
        password = decrypt_password(encrypted_password) if encrypted_password else ""
        
        return cls(
            smtp_host=config.get("smtp_host", "smtp.gmail.com"),
            smtp_port=config.get("smtp_port", 587),
            smtp_user=config.get("smtp_user", ""),
            smtp_password=password,
            recipient_email=config.get("recipient_email", ""),
            enabled=config.get("email_enabled", True),
        )
    
    def send(self, subject: str, detections: List[Dict]):
        """
        Send email notification with detection list.
        Non-blocking (async via thread).
        
        Args:
            subject: Email subject
            detections: List of detection dictionaries with keys:
                       'barn_id', 'timestamp', 'confidence'
        """
        if not self.enabled:
            logger.warning("Email notifications disabled, skipping.")
            return
        
        if not detections:
            logger.warning("No detections to send, skipping email.")
            return

        thread = threading.Thread(
            target=self._send_sync,
            args=(subject, detections),
            daemon=True,
        )
        thread.start()
    
    def send_single(self, barn_id: str, confidence: float, timestamp: Optional[str] = None, class_name: str = "Unknown"):
        """
        Convenience method to send a single detection notification.
        
        Args:
            barn_id: The barn identifier
            confidence: Detection confidence score
            timestamp: Detection timestamp (uses current time if None)
            class_name: Name of the detected class
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        detection = {
            "barn_id": barn_id,
            "timestamp": timestamp,
            "confidence": confidence,
            "class_name": class_name,
        }
        
        self.send(
            subject="[Swine Monitor] Mating Behavior Detected",
            detections=[detection]
        )
    
    def _send_sync(self, subject: str, detections: List[Dict]):
        """Synchronous send (called in thread)."""
        try:
            body = self._format_detection_list(detections)
            
            msg = MIMEMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = self.recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {self.recipient_email}")
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Email authentication failed: {e}")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def _format_detection_list(self, detections: List[Dict]) -> str:
        """
        Format detections as a readable list.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Formatted string for email body
        """
        lines = [
            "Mating Behavior Detection Report",
            "=" * 40,
            "",
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Detections: {len(detections)}",
            "",
            "-" * 40,
            "",
        ]
        
        for i, d in enumerate(detections, 1):
            barn_id = d.get("barn_id", "Unknown")
            class_name = d.get("class_name", "Unknown")
            timestamp = d.get("timestamp", "Unknown")
            confidence = d.get("confidence", 0.0)
            
            lines.append(f"[{i}] Barn: {barn_id}")
            lines.append(f"    Class: {class_name}")
            lines.append(f"    Time: {timestamp}")
            lines.append(f"    Confidence: {confidence:.1%}")
            lines.append("")
        
        lines.extend([
            "-" * 40,
            "",
            "This is an automated message from Swine Monitor System.",
            "Do not reply to this email.",
        ])
        
        return "\n".join(lines)
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test SMTP connection and authentication.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
            return True, "Connection successful"
        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed - check username/password"
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {e}"
        except Exception as e:
            return False, f"Connection error: {e}"


# =============================================================================
# Test Code
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("Notification Module Test")
    print("=" * 50)
    
    # Test Discord
    print("\n[1] Discord Notifier Test")
    discord_url = os.getenv("DISCORD_WEBHOOK_URL")
    if discord_url:
        discord = DiscordNotifier(discord_url)
        start = time.time()
        discord.send("🧪 Test message from notification module")
        print(f"    Discord send initiated in {time.time() - start:.4f}s")
    else:
        print("    Skipped - DISCORD_WEBHOOK_URL not set")
    
    # Test Email (manual test - requires credentials)
    print("\n[2] Email Notifier Test")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    
    if smtp_user and smtp_pass:
        email = EmailNotifier(
            smtp_user=smtp_user,
            smtp_password=smtp_pass,
            recipient_email=smtp_user,  # Send to self
        )
        
        success, msg = email.test_connection()
        print(f"    Connection test: {'✅' if success else '❌'} {msg}")
        
        if success:
            test_detections = [
                {"barn_id": "Barn 1", "timestamp": "2026-02-07 17:00:00", "confidence": 0.95},
                {"barn_id": "Barn 3", "timestamp": "2026-02-07 17:05:00", "confidence": 0.87},
            ]
            email.send("[Test] Swine Monitor Email Test", test_detections)
            print("    Test email sent!")
    else:
        print("    Skipped - SMTP_USER/SMTP_PASSWORD not set in .env")
    
    # Wait for async sends to complete
    print("\nWaiting for async operations...")
    time.sleep(3)
    print("Done!")
