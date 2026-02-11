"""
Email Notifier Integration Test
================================
Test the EmailNotifier class with encryption.

Usage:
    uv run python -m tests.test_email_notifier
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.notification import EmailNotifier
from src.encryption import PasswordEncryption


def main():
    load_dotenv()
    
    print("=" * 50)
    print("Email Notifier Integration Test")
    print("=" * 50)
    
    # Get credentials from environment
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    recipient = os.getenv("RECIPIENT_EMAIL", smtp_user)
    
    if not smtp_user or not smtp_password:
        print("\n❌ Missing credentials!")
        print("Please set the following environment variables in .env:")
        print("  SMTP_USER=your-email@gmail.com")
        print("  SMTP_PASSWORD=your-password")
        print("  RECIPIENT_EMAIL=recipient@example.com (optional)")
        return False
    
    print(f"\nSMTP User: {smtp_user}")
    print(f"Recipient: {recipient}")
    
    # Test 1: Direct password (unencrypted)
    print("\n" + "-" * 50)
    print("[Test 1] EmailNotifier with direct password")
    
    email = EmailNotifier(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        recipient_email=recipient,
    )
    
    success, msg = email.test_connection()
    print(f"Connection: {'✅' if success else '❌'} {msg}")
    
    if not success:
        print("\n⛔ Cannot proceed - connection test failed")
        return False
    
    # Test 2: Encryption flow
    print("\n" + "-" * 50)
    print("[Test 2] Password encryption/decryption")
    
    enc = PasswordEncryption()
    encrypted = enc.encrypt(smtp_password)
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = enc.decrypt(encrypted)
    match = decrypted == smtp_password
    print(f"Decryption successful: {'✅' if match else '❌'}")
    
    if not match:
        print("⛔ Encryption test failed!")
        return False
    
    # Test 3: EmailNotifier.from_config()
    print("\n" + "-" * 50)
    print("[Test 3] EmailNotifier.from_config()")
    
    config = {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": smtp_user,
        "smtp_password_encrypted": encrypted,
        "recipient_email": recipient,
        "email_enabled": True,
    }
    
    email2 = EmailNotifier.from_config(config)
    success2, msg2 = email2.test_connection()
    print(f"Connection: {'✅' if success2 else '❌'} {msg2}")
    
    if not success2:
        print("⛔ from_config() test failed!")
        return False
    
    # Test 4: Send actual email
    print("\n" + "-" * 50)
    print("[Test 4] Send test email")
    
    send_email = input("Send a test email? [y/N]: ").strip().lower()
    
    if send_email == 'y':
        test_detections = [
            {
                "barn_id": "Barn 1",
                "timestamp": "2026-02-07 17:00:00",
                "confidence": 0.95,
            },
            {
                "barn_id": "Barn 3",
                "timestamp": "2026-02-07 17:05:22",
                "confidence": 0.87,
            },
            {
                "barn_id": "Barn 5",
                "timestamp": "2026-02-07 17:12:45",
                "confidence": 0.92,
            },
        ]
        
        print(f"\nSending email with {len(test_detections)} detections...")
        email.send("[Swine Monitor] Test Email - Detection Report", test_detections)
        
        print("Waiting for async send to complete...")
        time.sleep(5)
        print(f"✅ Email sent to {recipient}")
        print("   Please check your inbox!")
    
    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
