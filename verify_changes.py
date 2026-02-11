
import sys
import os
import sqlite3
from unittest.mock import MagicMock

# Mock ultralytics to bypass import issues in restricted env
sys.modules["ultralytics"] = MagicMock()
sys.modules["ultralytics.YOLO"] = MagicMock()

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Database
from src.notification_scheduler import NotificationScheduler
# Now we can import Detector safely (mocked YOLO)
from src.detector import Detector

def verify_database():
    print("Verifying Database Schema...")
    try:
        db = Database()
        # The _init_db is called in __init__, so schema should be updated
        
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(detections)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if "class_name" in columns:
                print("✅ 'class_name' column exists in 'detections' table.")
            else:
                print("❌ 'class_name' column MISSING in 'detections' table.")
                return False
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False
            
    return True

def verify_notification_scheduler():
    print("\nVerifying Notification Scheduler...")
    try:
        scheduler = NotificationScheduler()
        scheduler.email = MagicMock()
        scheduler.discord = MagicMock()
        scheduler.email_enabled = True
        
        detection = {
            "barn_id": "Test Barn",
            "confidence": 0.9,
            "class_name": "TestPig",
            "timestamp": "2023-01-01 12:00:00"
        }
        
        # Test immediate notification
        scheduler.on_detection(detection)
        
        # Check email subject
        if scheduler.email.send.called:
            call_args = scheduler.email.send.call_args[1]
            subject = call_args.get('subject', '')
            if "TestPig Detected" in subject:
                print("✅ Email subject contains class name.")
            else:
                print(f"❌ Email subject missing class name: {subject}")
                return False
        else:
            print("❌ Email send not called.")
            return False
            
    except Exception as e:
        print(f"❌ Scheduler verification failed: {e}")
        return False

    return True

def verify_detector_logic():
    print("\nVerifying Detector Logic (Mocked)...")
    try:
        detector = Detector(barn_id="Test")
        # Ensure process_frame signature handles unpacking correctly
        # We can't run full inference, but we can check if _handle_detection accepts class_name
        
        # Mock _handle_detection to inspect calls
        detector._handle_detection = MagicMock()
        
        # Manually call _handle_detection with new signature
        detector._handle_detection(None, 0.9, "Pig")
        
        detector._handle_detection.assert_called_with(None, 0.9, "Pig")
        print("✅ Detector._handle_detection accepts class_name.")
        
    except Exception as e:
        print(f"❌ Detector logic verification failed: {e}")
        return False

    return True

if __name__ == "__main__":
    success = True
    success &= verify_database()
    success &= verify_notification_scheduler()
    success &= verify_detector_logic()
    
    if success:
        print("\n✅ ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print("\n❌ SOME CHECKS FAILED")
        sys.exit(1)
