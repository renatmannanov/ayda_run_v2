"""
Token encryption utilities using Fernet (symmetric encryption).

Used to encrypt sensitive tokens (Strava OAuth tokens) at rest in the database.
"""
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
import logging

from config import settings

logger = logging.getLogger(__name__)

_fernet: Optional[Fernet] = None


def get_fernet() -> Fernet:
    """
    Get Fernet instance, lazily initialized.

    Raises:
        ValueError: If ENCRYPTION_KEY is not configured
    """
    global _fernet
    if _fernet is None:
        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY not configured in environment")
        _fernet = Fernet(settings.encryption_key.encode())
    return _fernet


def encrypt_token(token: Optional[str]) -> Optional[str]:
    """
    Encrypt a token string.

    Args:
        token: Plain text token to encrypt

    Returns:
        Encrypted token as string, or None if input is None/empty
    """
    if not token:
        return None
    try:
        return get_fernet().encrypt(token.encode()).decode()
    except Exception as e:
        logger.error(f"Error encrypting token: {e}")
        raise


def decrypt_token(encrypted: Optional[str]) -> Optional[str]:
    """
    Decrypt an encrypted token string.

    Args:
        encrypted: Encrypted token string

    Returns:
        Decrypted plain text token, or None if input is None/empty

    Raises:
        InvalidToken: If decryption fails (wrong key or corrupted data)
    """
    if not encrypted:
        return None
    try:
        return get_fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt token - invalid key or corrupted data")
        raise
    except Exception as e:
        logger.error(f"Error decrypting token: {e}")
        raise
