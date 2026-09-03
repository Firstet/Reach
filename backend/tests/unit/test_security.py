"""Unit tests for security utilities."""

import pytest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    encrypt_secret,
    decrypt_secret,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        plain = "super-secure-password-123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)


class TestJWT:
    def test_access_token_roundtrip(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_refresh_token_type(self):
        token = create_refresh_token({"sub": "user-456"})
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_invalid_token_returns_none(self):
        assert decode_token("invalid.token.here") is None

    def test_access_token_rejected_as_refresh(self):
        token = create_access_token({"sub": "user-789"})
        payload = decode_token(token)
        assert payload["type"] != "refresh"


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        secret = "my-api-key-abc123"
        encrypted = encrypt_secret(secret)
        assert encrypted != secret
        decrypted = decrypt_secret(encrypted)
        assert decrypted == secret

    def test_different_secrets_produce_different_ciphertext(self):
        a = encrypt_secret("secret-a")
        b = encrypt_secret("secret-b")
        assert a != b
