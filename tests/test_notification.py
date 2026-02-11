#!/usr/bin/env python3
"""
Notification Module Unit Tests
==============================

Tests for DiscordNotifier and EmailNotifier in src/notification.py.

Usage:
    uv run pytest tests/test_notification.py -v
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.notification import DiscordNotifier, EmailNotifier


# =============================================================================
# Tests: DiscordNotifier
# =============================================================================

class TestDiscordNotifierInit:
    """Tests for DiscordNotifier initialization."""
    
    def test_init_with_webhook(self):
        """Test initialization with webhook URL."""
        webhook = "https://discord.com/api/webhooks/123/abc"
        notifier = DiscordNotifier(webhook_url=webhook)
        
        assert notifier.webhook_url == webhook
        assert notifier.enabled is True
    
    def test_init_without_webhook(self):
        """Test initialization without webhook URL."""
        notifier = DiscordNotifier()
        
        assert notifier.webhook_url is None
        assert notifier.enabled is False
    
    def test_init_with_empty_webhook(self):
        """Test initialization with empty webhook URL."""
        notifier = DiscordNotifier(webhook_url="")
        
        assert notifier.enabled is False


class TestDiscordNotifierSend:
    """Tests for DiscordNotifier send method."""
    
    def test_send_without_webhook_logs_warning(self):
        """Test that send without webhook logs warning."""
        notifier = DiscordNotifier()
        
        with patch("src.notification.logger") as mock_logger:
            notifier.send("Test message")
            mock_logger.warning.assert_called_once()
    
    @patch("src.notification.requests.post")
    def test_send_message_only(self, mock_post):
        """Test sending message without image."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        webhook = "https://discord.com/api/webhooks/123/abc"
        notifier = DiscordNotifier(webhook_url=webhook)
        
        # Call _send_sync directly to avoid threading
        notifier._send_sync("Test message")
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.kwargs["json"]["content"] == "Test message"
        assert call_args.kwargs["timeout"] == 30
    
    @patch("src.notification.requests.post")
    @patch("builtins.open", mock_open(read_data=b"fake_image_data"))
    @patch("os.path.exists", return_value=True)
    def test_send_with_image(self, mock_exists, mock_post):
        """Test sending message with image."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        webhook = "https://discord.com/api/webhooks/123/abc"
        notifier = DiscordNotifier(webhook_url=webhook)
        
        notifier._send_sync("Test message", image_path="/path/to/image.jpg")
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "files" in call_args.kwargs
    
    @patch("src.notification.requests.post")
    def test_send_handles_error_response(self, mock_post):
        """Test handling of error response from Discord."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        webhook = "https://discord.com/api/webhooks/123/abc"
        notifier = DiscordNotifier(webhook_url=webhook)
        
        with patch("src.notification.logger") as mock_logger:
            notifier._send_sync("Test message")
            mock_logger.error.assert_called_once()
    
    @patch("src.notification.requests.post")
    def test_send_handles_exception(self, mock_post):
        """Test handling of network exception."""
        mock_post.side_effect = Exception("Network error")
        
        webhook = "https://discord.com/api/webhooks/123/abc"
        notifier = DiscordNotifier(webhook_url=webhook)
        
        with patch("src.notification.logger") as mock_logger:
            notifier._send_sync("Test message")
            mock_logger.error.assert_called_once()


# =============================================================================
# Tests: EmailNotifier
# =============================================================================

class TestEmailNotifierInit:
    """Tests for EmailNotifier initialization."""
    
    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        notifier = EmailNotifier(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="user@test.com",
            smtp_password="password",
            recipient_email="recipient@test.com",
            enabled=True
        )
        
        assert notifier.smtp_host == "smtp.test.com"
        assert notifier.smtp_port == 587
        assert notifier.smtp_user == "user@test.com"
        assert notifier.smtp_password == "password"
        assert notifier.recipient_email == "recipient@test.com"
        assert notifier.enabled is True
    
    def test_init_default_values(self):
        """Test default values."""
        notifier = EmailNotifier()
        
        assert notifier.smtp_host == "smtp.gmail.com"
        assert notifier.smtp_port == 587
        assert notifier.enabled is False  # No credentials = disabled
    
    def test_init_disabled_without_credentials(self):
        """Test that notifier is disabled without credentials."""
        notifier = EmailNotifier(
            smtp_user="user@test.com",
            smtp_password="",  # Missing password
            recipient_email="recipient@test.com",
            enabled=True
        )
        
        assert notifier.enabled is False
    
    def test_init_disabled_without_recipient(self):
        """Test that notifier is disabled without recipient."""
        notifier = EmailNotifier(
            smtp_user="user@test.com",
            smtp_password="password",
            recipient_email="",  # Missing recipient
            enabled=True
        )
        
        assert notifier.enabled is False


class TestEmailNotifierFromConfig:
    """Tests for EmailNotifier.from_config class method."""
    
    def test_from_config_basic(self):
        """Test creating from config dict."""
        config = {
            "smtp_host": "smtp.custom.com",
            "smtp_port": 465,
            "smtp_user": "custom@test.com",
            "smtp_password_encrypted": "",  # No encryption for test
            "recipient_email": "recipient@test.com",
            "email_enabled": True
        }
        
        notifier = EmailNotifier.from_config(config)
        
        assert notifier.smtp_host == "smtp.custom.com"
        assert notifier.smtp_port == 465
        assert notifier.smtp_user == "custom@test.com"
    
    def test_from_config_defaults(self):
        """Test from_config with empty config uses defaults."""
        config = {}
        notifier = EmailNotifier.from_config(config)
        
        assert notifier.smtp_host == "smtp.gmail.com"
        assert notifier.smtp_port == 587


class TestEmailNotifierFormatDetectionList:
    """Tests for email formatting."""
    
    def test_format_empty_list(self):
        """Test formatting empty detection list."""
        notifier = EmailNotifier()
        result = notifier._format_detection_list([])
        
        assert "Total Detections: 0" in result
    
    def test_format_single_detection(self):
        """Test formatting single detection."""
        notifier = EmailNotifier()
        detections = [
            {
                "barn_id": "Barn 1",
                "timestamp": "2026-02-09 10:00:00",
                "confidence": 0.95
            }
        ]
        
        result = notifier._format_detection_list(detections)
        
        assert "Total Detections: 1" in result
        assert "Barn 1" in result
        assert "95.0%" in result
    
    def test_format_multiple_detections(self):
        """Test formatting multiple detections."""
        notifier = EmailNotifier()
        detections = [
            {"barn_id": "Barn 1", "timestamp": "2026-02-09 10:00:00", "confidence": 0.95},
            {"barn_id": "Barn 2", "timestamp": "2026-02-09 10:05:00", "confidence": 0.87},
            {"barn_id": "Barn 3", "timestamp": "2026-02-09 10:10:00", "confidence": 0.72},
        ]
        
        result = notifier._format_detection_list(detections)
        
        assert "Total Detections: 3" in result
        assert "[1]" in result
        assert "[2]" in result
        assert "[3]" in result
    
    def test_format_detections_with_missing_fields(self):
        """Test formatting detections with missing fields."""
        notifier = EmailNotifier()
        detections = [
            {"confidence": 0.90},  # Missing barn_id and timestamp
        ]
        
        result = notifier._format_detection_list(detections)
        
        assert "Unknown" in result  # Default for missing barn_id


class TestEmailNotifierSend:
    """Tests for EmailNotifier send method."""
    
    def test_send_when_disabled(self):
        """Test that send does nothing when disabled."""
        notifier = EmailNotifier(enabled=False)
        
        # Should not raise
        notifier.send("Test Subject", [{"barn_id": "Barn 1", "confidence": 0.9}])
    
    @patch("smtplib.SMTP")
    def test_send_sync_success(self, mock_smtp_class):
        """Test successful email sending."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        
        notifier = EmailNotifier(
            smtp_user="user@test.com",
            smtp_password="password",
            recipient_email="recipient@test.com"
        )
        
        detections = [{"barn_id": "Barn 1", "confidence": 0.95}]
        notifier._send_sync("Test Subject", detections)
        
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user@test.com", "password")
        mock_smtp.send_message.assert_called_once()
    
    @patch("smtplib.SMTP")
    def test_send_sync_auth_error(self, mock_smtp_class):
        """Test handling of authentication error."""
        import smtplib
        
        mock_smtp = MagicMock()
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        
        notifier = EmailNotifier(
            smtp_user="user@test.com",
            smtp_password="wrong_password",
            recipient_email="recipient@test.com"
        )
        
        with patch("src.notification.logger") as mock_logger:
            notifier._send_sync("Test Subject", [])
            mock_logger.error.assert_called()


class TestEmailNotifierTestConnection:
    """Tests for test_connection method."""
    
    @patch("smtplib.SMTP")
    def test_connection_success(self, mock_smtp_class):
        """Test successful connection test."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        
        notifier = EmailNotifier(
            smtp_user="user@test.com",
            smtp_password="password",
            recipient_email="recipient@test.com"
        )
        
        success, message = notifier.test_connection()
        
        assert success is True
        assert "successful" in message.lower()
    
    @patch("smtplib.SMTP")
    def test_connection_auth_failure(self, mock_smtp_class):
        """Test authentication failure in connection test."""
        import smtplib
        
        mock_smtp = MagicMock()
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        
        notifier = EmailNotifier(
            smtp_user="user@test.com",
            smtp_password="wrong",
            recipient_email="recipient@test.com"
        )
        
        success, message = notifier.test_connection()
        
        assert success is False
        assert "authentication" in message.lower()
    
    @patch("smtplib.SMTP")
    def test_connection_network_error(self, mock_smtp_class):
        """Test network error in connection test."""
        mock_smtp_class.side_effect = Exception("Network unreachable")
        
        notifier = EmailNotifier(
            smtp_user="user@test.com",
            smtp_password="password",
            recipient_email="recipient@test.com"
        )
        
        success, message = notifier.test_connection()
        
        assert success is False
        assert "error" in message.lower()


class TestEmailNotifierSendSingle:
    """Tests for send_single convenience method."""
    
    def test_send_single_creates_detection(self):
        """Test that send_single creates proper detection dict."""
        notifier = EmailNotifier()
        notifier.enabled = False  # Don't actually try to send
        
        # Just verify it doesn't raise
        notifier.send_single(
            barn_id="Barn 1",
            confidence=0.92,
            timestamp="2026-02-09 10:00:00"
        )
    
    def test_send_single_default_timestamp(self):
        """Test send_single with default timestamp."""
        notifier = EmailNotifier()
        notifier.enabled = False
        
        # Should use current time if not provided
        notifier.send_single(barn_id="Barn 1", confidence=0.85)


# =============================================================================
# Main entry point
# =============================================================================

def main():
    """Run tests using pytest."""
    print("=" * 60)
    print("Notification Module Unit Tests")
    print("=" * 60)
    
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
