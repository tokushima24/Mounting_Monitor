#!/usr/bin/env python3
"""
Encryption Module Test
======================
Test the PasswordEncryption class.

Usage:
    uv run python -m tests.test_encryption
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.encryption import PasswordEncryption, encrypt_password, decrypt_password


def test_basic_encryption():
    """Test basic encrypt/decrypt flow."""
    print("[Test 1] Basic encryption/decryption")
    
    enc = PasswordEncryption()
    original = "my_secret_password_123!@#"
    
    encrypted = enc.encrypt(original)
    assert encrypted != original, "Encrypted should differ from original"
    assert enc.is_encrypted(encrypted), "Should detect encrypted text"
    
    decrypted = enc.decrypt(encrypted)
    assert decrypted == original, "Decrypted should match original"
    
    print(f"  Original:  {original}")
    print(f"  Encrypted: {encrypted[:40]}...")
    print(f"  Decrypted: {decrypted}")
    print("  ✅ Passed")


def test_empty_string():
    """Test handling of empty strings."""
    print("\n[Test 2] Empty string handling")
    
    enc = PasswordEncryption()
    
    encrypted = enc.encrypt("")
    assert encrypted == "", "Empty input should return empty output"
    
    decrypted = enc.decrypt("")
    assert decrypted == "", "Empty input should return empty output"
    
    print("  ✅ Passed")


def test_convenience_functions():
    """Test module-level convenience functions."""
    print("\n[Test 3] Convenience functions")
    
    original = "test_password_456"
    encrypted = encrypt_password(original)
    decrypted = decrypt_password(encrypted)
    
    assert decrypted == original
    print("  ✅ Passed")


def test_key_persistence():
    """Test that the key persists across instances."""
    print("\n[Test 4] Key persistence")
    
    enc1 = PasswordEncryption()
    encrypted = enc1.encrypt("persistent_test")
    
    enc2 = PasswordEncryption()
    decrypted = enc2.decrypt(encrypted)
    
    assert decrypted == "persistent_test", "Should decrypt with new instance"
    print("  ✅ Passed")


def test_special_characters():
    """Test passwords with special characters."""
    print("\n[Test 5] Special characters")
    
    enc = PasswordEncryption()
    special_passwords = [
        "パスワード日本語",
        "émoji🔐password",
        "spaces and\ttabs\nnewlines",
        "!@#$%^&*()_+-=[]{}|;':\",./<>?",
    ]
    
    for pwd in special_passwords:
        encrypted = enc.encrypt(pwd)
        decrypted = enc.decrypt(encrypted)
        assert decrypted == pwd, f"Failed for: {pwd[:20]}..."
    
    print(f"  Tested {len(special_passwords)} special passwords")
    print("  ✅ Passed")


def main():
    print("=" * 50)
    print("Encryption Module Test Suite")
    print("=" * 50)
    
    try:
        test_basic_encryption()
        test_empty_string()
        test_convenience_functions()
        test_key_persistence()
        test_special_characters()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
