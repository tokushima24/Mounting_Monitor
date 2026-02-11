#!/usr/bin/env python3
"""
SMTP Connection Test Tool
=========================
Interactive CLI tool to test SMTP connectivity with various email providers.

Usage:
    uv run python -m tests.test_smtp

Note: This is an interactive CLI tool, not automated unit tests.
      Functions are prefixed with 'check_' instead of 'test_' to avoid
      pytest auto-discovery.
"""


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import getpass
import sys


def check_smtp_connection(host: str, port: int) -> bool:
    """Check basic SMTP connection."""
    print(f"\n[1/4] Testing connection to {host}:{port}...")
    try:
        server = smtplib.SMTP(host, port, timeout=10)
        print(f"  ✅ Connected to {host}:{port}")
        server.quit()
        return True
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False


def check_tls(host: str, port: int) -> bool:
    """Check TLS/STARTTLS support."""
    print("\n[2/4] Testing TLS encryption...")
    try:
        server = smtplib.SMTP(host, port, timeout=10)
        server.starttls()
        print("  ✅ TLS encryption established")
        server.quit()
        return True
    except Exception as e:
        print(f"  ❌ TLS failed: {e}")
        return False


def check_authentication(host: str, port: int, user: str, password: str) -> bool:
    """Check SMTP authentication."""
    print(f"\n[3/4] Testing authentication for {user}...")
    try:
        server = smtplib.SMTP(host, port, timeout=10)
        server.starttls()
        server.login(user, password)
        print("  ✅ Authentication successful")
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"  ❌ Authentication failed: {e}")
        print("\n  💡 Hint: If MFA is enabled, you need an App Password.")
        print("     Create one at: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def check_send_email(host: str, port: int, user: str, password: str, recipient: str) -> bool:
    """Send a test email."""
    print(f"\n[4/4] Sending test email to {recipient}...")
    try:
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = recipient
        msg['Subject'] = "[Test] Swine Monitor SMTP Test"
        
        body = """
This is a test email from the Swine Monitor system.

If you received this email, the SMTP configuration is working correctly!

---
Swine Monitor System
        """
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(host, port, timeout=10)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        
        print("  ✅ Test email sent successfully!")
        print(f"     Check inbox: {recipient}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to send email: {e}")
        return False


def main():
    """Interactive SMTP configuration test."""
    print("=" * 50)
    print("SMTP Connection Test for Swine Monitor")
    print("=" * 50)
    
    # SMTP Settings
    SMTP_CONFIGS = [
        ("smtp.gmail.com", 587, "Gmail"),
        ("smtp.office365.com", 587, "Office 365"),
        ("smtp.tokushima-u.ac.jp", 587, "Tokushima University"),
    ]
    
    print("\nAvailable SMTP configurations:")
    for i, (host, port, name) in enumerate(SMTP_CONFIGS, 1):
        print(f"  {i}. {name} ({host}:{port})")
    print(f"  {len(SMTP_CONFIGS) + 1}. Custom")
    
    choice = input("\nSelect configuration [1]: ").strip() or "1"
    
    try:
        idx = int(choice) - 1
        if idx < len(SMTP_CONFIGS):
            smtp_host, smtp_port, _ = SMTP_CONFIGS[idx]
        else:
            smtp_host = input("Enter SMTP host: ").strip()
            smtp_port = int(input("Enter SMTP port [587]: ").strip() or "587")
    except (ValueError, IndexError):
        smtp_host, smtp_port, _ = SMTP_CONFIGS[0]
    
    print(f"\nUsing: {smtp_host}:{smtp_port}")
    
    # Test 1: Connection
    if not check_smtp_connection(smtp_host, smtp_port):
        print("\n⛔ Cannot connect. Please check network/firewall settings.")
        sys.exit(1)
    
    # Test 2: TLS
    if not check_tls(smtp_host, smtp_port):
        print("\n⛔ TLS not supported. Try a different port.")
        sys.exit(1)
    
    # Test 3: Authentication
    print("\n" + "-" * 50)
    email = input("Enter your email address: ").strip()
    password = getpass.getpass("Enter password (or App Password): ")
    
    if not check_authentication(smtp_host, smtp_port, email, password):
        print("\n⛔ Authentication failed. Check credentials or create App Password.")
        sys.exit(1)
    
    # Test 4: Send email (optional)
    print("\n" + "-" * 50)
    send_test = input("Send a test email? [y/N]: ").strip().lower()
    
    if send_test == 'y':
        recipient = input(f"Recipient email [{email}]: ").strip() or email
        check_send_email(smtp_host, smtp_port, email, password, recipient)
    
    # Summary
    print("\n" + "=" * 50)
    print("✅ SMTP Configuration Verified!")
    print("=" * 50)
    print(f"""
Save these settings for the Swine Monitor:

  SMTP Host: {smtp_host}
  SMTP Port: {smtp_port}
  Username:  {email}
  Password:  (your password/app password)
""")


if __name__ == "__main__":
    main()
