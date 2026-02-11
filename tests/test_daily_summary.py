
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.notification_scheduler import NotificationScheduler

class TestNotificationScheduler(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.scheduler = NotificationScheduler(db=self.mock_db)
        self.scheduler.email = MagicMock()
        self.scheduler.discord = MagicMock()
        self.scheduler._scheduler_thread = MagicMock()

    def test_daily_summary_queueing(self):
        """Test that detections are queued when daily summary is enabled."""
        self.scheduler.daily_summary_enabled = True
        detection = {"barn_id": "test_barn", "confidence": 0.8, "timestamp": "12:00:00"}
        
        self.scheduler.on_detection(detection)
        
        # Check if queued
        self.assertEqual(self.scheduler.get_pending_count(), 1, "Detection should be queued")
        # Check content
        self.assertEqual(self.scheduler._today_detections[0], detection)

    def test_daily_summary_send(self):
        """Test sending daily summary."""
        self.scheduler.daily_summary_enabled = True
        self.scheduler.email_enabled = True
        
        # Queue dummy detections
        self.scheduler._queue_detection({"barn_id": "1", "confidence": 0.9})
        self.scheduler._queue_detection({"barn_id": "2", "confidence": 0.8})
        
        self.assertEqual(self.scheduler.get_pending_count(), 2)
        
        # Send summary
        self.scheduler._send_daily_summary()
        
        # Queue should be empty now
        self.assertEqual(self.scheduler.get_pending_count(), 0)
        
        # Email send should be called
        self.scheduler.email.send.assert_called()

    def test_dual_mode(self):
        """Test simultaneous immediate and daily notifications."""
        self.scheduler.immediate_enabled = True
        self.scheduler.daily_summary_enabled = True
        
        detection = {"barn_id": "dual", "confidence": 0.99}
        
        with patch.object(self.scheduler, '_send_immediate') as mock_immediate:
            self.scheduler.on_detection(detection)
            
            # Should be queued for daily
            self.assertEqual(self.scheduler.get_pending_count(), 1)
            
            # Should also trigger immediate send
            mock_immediate.assert_called_once()

if __name__ == '__main__':
    unittest.main()
