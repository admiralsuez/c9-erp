#!/usr/bin/env python3
"""
Validate required Cloud9 ERP deployment environment variables before startup.
This fails fast in Docker so deployment errors are visible in container logs.
"""

import os
import sys
from urllib.parse import urlparse


REQUIRED_VARS = [
    "DATABASE_URL",
    "JWT_SECRET",
]


def fail(message: str) -> None:
    print(f"[✗] {message}")
    sys.exit(1)


def warn(message: str) -> None:
    print(f"[!] {message}")


def validate_database_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"postgresql", "postgresql+psycopg2"}:
        fail("DATABASE_URL must use postgresql:// or postgresql+psycopg2://")
    if not parsed.hostname:
        fail("DATABASE_URL is missing a database host")
    if not parsed.path or parsed.path == "/":
        fail("DATABASE_URL is missing a database name")


def main() -> None:
    missing = [name for name in REQUIRED_VARS if not os.getenv(name)]
    if missing:
        fail(f"Missing required environment variables: {', '.join(missing)}")

    validate_database_url(os.environ["DATABASE_URL"])

    jwt_secret = os.environ["JWT_SECRET"]
    if len(jwt_secret) < 32:
        fail("JWT_SECRET must be at least 32 characters")

    admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@cloud9.local")
    admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin@12345")
    if "@" not in admin_email:
        fail("INITIAL_ADMIN_EMAIL must be a valid email-like value")
    if len(admin_password) < 8:
        fail("INITIAL_ADMIN_PASSWORD must be at least 8 characters")

    if admin_password == "Admin@12345":
        warn("INITIAL_ADMIN_PASSWORD is the default bootstrap password. Change it after first login.")

    print("[✓] Environment validation passed")


if __name__ == "__main__":
    main()
