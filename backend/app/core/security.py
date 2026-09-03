"""Security utilities: password hashing, JWT, encryption."""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any


from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


# ── Passwords ─────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm="HS256")


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def _get_fernet() -> Fernet:
    raw_key = getattr(settings, "encryption_key", "") or getattr(settings, "jwt_secret_key", "reach-secret-key-default")
    try:
        # Check if raw_key is already a valid 32 urlsafe base64 fernet key
        return Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
    except Exception:
        # Generate valid 32 urlsafe base64 key deterministically via SHA256
        digest = hashlib.sha256(raw_key.encode() if isinstance(raw_key, str) else raw_key).digest()
        valid_key = base64.urlsafe_b64encode(digest)
        return Fernet(valid_key)


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a sensitive credential for storage."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a stored credential."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()

