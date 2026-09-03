"""pytest configuration."""

import os
import pytest

# Use test environment
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://reach:reach_password@localhost:5432/reach_test")
os.environ.setdefault("DATABASE_SYNC_URL", "postgresql://reach:reach_password@localhost:5432/reach_test")
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-key-for-pytest-only")
os.environ.setdefault("ENCRYPTION_KEY", "")  # Uses derived key in tests
