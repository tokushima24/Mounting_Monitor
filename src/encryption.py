"""
Password Encryption Module
==========================

Provides secure encryption/decryption for sensitive data like SMTP passwords.
Uses Fernet symmetric encryption from the cryptography library.

Security Notes:
    - The encryption key is stored in .encryption_key file
    - The key file should have restricted permissions (chmod 600)
    - Never commit the .encryption_key file to version control
"""

import logging
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

logger = logging.getLogger("SwineMonitor.Encryption")


class PasswordEncryption:
    """
    Handles encryption and decryption of sensitive passwords.
    
    Uses Fernet symmetric encryption which provides:
    - AES 128-bit encryption in CBC mode
    - HMAC for authentication
    - Timestamps for freshness
    
    Attributes:
        KEY_FILE: Name of the file storing the encryption key.
        key_path: Full path to the encryption key file.
        
    Examples:
        >>> enc = PasswordEncryption()
        >>> encrypted = enc.encrypt("my_secret_password")
        >>> original = enc.decrypt(encrypted)
    """
    
    KEY_FILE: str = ".encryption_key"
    
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        """
        Initialize encryption utility.
        
        Args:
            base_dir: Directory to store the encryption key file.
                     Defaults to the project root directory.
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        self.key_path: Path = base_dir / self.KEY_FILE
        self._fernet: Optional[Fernet] = None
    
    def _get_or_create_key(self) -> bytes:
        """
        Get existing key or create a new one.
        
        Returns:
            The encryption key as bytes.
        """
        if self.key_path.exists():
            key = self.key_path.read_bytes()
            logger.debug("Loaded existing encryption key")
        else:
            key = Fernet.generate_key()
            self.key_path.write_bytes(key)
            # Set restrictive permissions (owner read/write only)
            try:
                os.chmod(self.key_path, 0o600)
            except (OSError, NotImplementedError):
                pass  # Windows doesn't support Unix-style permissions
            logger.info(f"Generated new encryption key: {self.key_path}")
        return key
    
    @property
    def fernet(self) -> Fernet:
        """
        Get or create Fernet instance.
        
        Returns:
            Fernet: The Fernet encryption instance.
        """
        if self._fernet is None:
            key = self._get_or_create_key()
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt.
            
        Returns:
            Encrypted string (base64 encoded). Empty string if input is empty.
        """
        if not plaintext:
            return ""
        encrypted = self.fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted.decode("utf-8")
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            encrypted: The encrypted string (base64 encoded).
            
        Returns:
            Decrypted plaintext string. Empty string on failure.
        """
        if not encrypted:
            return ""
        try:
            decrypted = self.fernet.decrypt(encrypted.encode("utf-8"))
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""
    
    def is_encrypted(self, text: str) -> bool:
        """
        Check if a string appears to be Fernet-encrypted.
        
        Fernet tokens always start with 'gAAAAA' (base64 encoded version byte).
        
        Args:
            text: String to check.
            
        Returns:
            True if the string appears to be encrypted.
        """
        return text.startswith("gAAAAA") if text else False


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_encryption: Optional[PasswordEncryption] = None


def get_encryption() -> PasswordEncryption:
    """
    Get the default encryption instance (singleton pattern).
    
    Returns:
        PasswordEncryption: The shared encryption instance.
    """
    global _default_encryption
    if _default_encryption is None:
        _default_encryption = PasswordEncryption()
    return _default_encryption


def encrypt_password(password: str) -> str:
    """
    Encrypt a password using the default encryption instance.
    
    Args:
        password: The plaintext password to encrypt.
        
    Returns:
        The encrypted password string.
    """
    return get_encryption().encrypt(password)


def decrypt_password(encrypted: str) -> str:
    """
    Decrypt a password using the default encryption instance.
    
    Args:
        encrypted: The encrypted password string.
        
    Returns:
        The decrypted plaintext password.
    """
    return get_encryption().decrypt(encrypted)


# =============================================================================
# Self-test when run directly
# =============================================================================

if __name__ == "__main__":
    print("Password Encryption Test")
    print("=" * 40)
    
    enc = PasswordEncryption()
    
    test_password = "my_secret_password_123"
    print(f"Original: {test_password}")
    
    encrypted = enc.encrypt(test_password)
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = enc.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    
    assert test_password == decrypted, "Decryption failed!"
    print("\n[OK] Encryption test passed!")
