"""
Pax Modernica - Security & Authentication Utilities
Argon2id password hashing and cryptographically secure session management.
"""

import secrets
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

ph = PasswordHasher(
    time_cost=2,
    memory_cost=16384,  # 16 MB
    parallelism=2,
    hash_len=32,
    salt_len=16
)

def hash_password(password: str) -> str:
    """Hashes a password with Argon2id."""
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a password against an Argon2id hash."""
    try:
        return ph.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError):
        return False

def generate_session_token() -> str:
    """Generates a high-entropy URL-safe session token."""
    return secrets.token_hex(32)

def calculate_expiry(hours: int = 72) -> datetime:
    """Calculates session expiry datetime."""
    return datetime.now(timezone.utc) + timedelta(hours=hours)
