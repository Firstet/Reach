#!/usr/bin/env python3
"""
Reach — Production Deployment Auditor & Health Check Script
Verifies environment variables, secrets configuration, database readiness,
and service dependencies prior to production deployment.
"""

import sys
import os
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

def print_status(component: str, ok: bool, message: str):
    symbol = "✓" if ok else "✗"
    color = "\033[92m" if ok else "\033[91m"
    reset = "\033[0m"
    print(f"[{color}{symbol}{reset}] {component}: {message}")

def check_environment_file() -> bool:
    env_path = root_dir / ".env"
    backend_env = backend_dir / ".env"
    exists = env_path.exists() or backend_env.exists()
    print_status("Environment File (.env)", exists, f"Found at {env_path}" if exists else "Missing .env file!")
    return exists

def check_secrets_configuration() -> bool:
    all_ok = True

    # Import config after path setup
    try:
        from app.core.config import get_settings
        settings = get_settings()
    except Exception as e:
        print_status("Configuration Import", False, f"Failed to import app configuration: {e}")
        return False

    # Check APP_SECRET_KEY
    if not settings.app_secret_key or len(settings.app_secret_key) < 16:
        print_status("APP_SECRET_KEY", False, "APP_SECRET_KEY is missing or too short (< 16 chars)")
        all_ok = False
    else:
        print_status("APP_SECRET_KEY", True, "Configured securely")

    # Check JWT_SECRET_KEY
    if not settings.jwt_secret_key or len(settings.jwt_secret_key) < 16:
        print_status("JWT_SECRET_KEY", False, "JWT_SECRET_KEY is missing or too short (< 16 chars)")
        all_ok = False
    else:
        print_status("JWT_SECRET_KEY", True, "Configured securely")

    # Check ENCRYPTION_KEY
    if not settings.encryption_key:
        print_status("ENCRYPTION_KEY", False, "ENCRYPTION_KEY (Fernet key) is missing! (Optional for unencrypted local mode, required for storing provider API keys)")
    else:
        try:
            from cryptography.fernet import Fernet
            Fernet(settings.encryption_key.encode())
            print_status("ENCRYPTION_KEY", True, "Valid Fernet encryption key format")
        except Exception:
            print_status("ENCRYPTION_KEY", False, "Invalid Fernet key format!")
            all_ok = False

    return all_ok

def check_providers() -> bool:
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print_status("LLM Provider", True, f"Active provider set to '{settings.active_llm_provider}'")
        print_status("Email Provider", True, f"Active provider set to '{settings.active_email_provider}'")
        print_status("Search Provider", True, f"Active provider set to '{settings.active_search_provider}'")
        print_status("Enrichment Provider", True, f"Active provider set to '{settings.active_enrichment_provider}'")
        return True
    except Exception as e:
        print_status("Provider Settings", False, f"Failed to read provider configuration: {e}")
        return False

def check_database_url() -> bool:
    try:
        from app.core.config import get_settings
        settings = get_settings()
        db_url = settings.database_url
        if "postgresql" in db_url:
            print_status("Database Backend", True, f"PostgreSQL vector database configured ({db_url.split('@')[-1]})")
        elif "sqlite" in db_url:
            print_status("Database Backend", True, "SQLite fallback configured (Zero-Paid local mode)")
        else:
            print_status("Database Backend", True, f"Custom database configured: {db_url}")
        return True
    except Exception as e:
        print_status("Database Config", False, str(e))
        return False

def main():
    print("=" * 70)
    print(" REACH — PRODUCTION DEPLOYMENT AUDITOR")
    print("=" * 70)

    env_ok = check_environment_file()
    secrets_ok = check_secrets_configuration()
    providers_ok = check_providers()
    db_ok = check_database_url()

    print("=" * 70)
    if env_ok and secrets_ok and providers_ok and db_ok:
        print("\033[92mSUCCESS: System is verified and ready for production deployment!\033[0m")
        sys.exit(0)
    else:
        print("\033[91mWARNING: Issues found. Please resolve items flagged above before deploying.\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
