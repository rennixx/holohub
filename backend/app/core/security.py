"""
Security Module

Provides utilities for password hashing, JWT token management,
and multi-factor authentication (MFA).
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import argon2
import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# Password hashing context using argon2 (more secure and better compatibility)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Argon2 for device secrets (more resistant to GPU attacks)
argon2_hasher = argon2.PasswordHasher(
    time_cost=3,  # Number of iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,  # Number of parallel threads
    hash_len=32,  # Hash length in bytes
    salt_len=16,  # Salt length in bytes
)


# =============================================================================
# Password Management
# =============================================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password strength against requirements.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if len(password) < settings.password_min_length:
        errors.append(
            f"Password must be at least {settings.password_min_length} characters long"
        )

    if settings.password_require_uppercase and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if settings.password_require_lowercase and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if settings.password_require_digit and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if settings.password_require_special:
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append(f"Password must contain at least one special character ({special_chars})")

    return len(errors) == 0, errors


def generate_reset_token() -> str:
    """
    Generate a secure password reset token.

    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(32)


# =============================================================================
# JWT Token Management
# =============================================================================
def create_access_token(
    subject: str | Any,
    org_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT access token.

    Args:
        subject: User ID (typically)
        org_id: Organization ID
        role: User role
        expires_delta: Custom expiration time (optional)

    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "sub": str(subject),
        "org": str(org_id),
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(
    subject: str | Any,
    org_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT refresh token.

    Args:
        subject: User ID (typically)
        org_id: Organization ID
        expires_delta: Custom expiration time (optional)

    Returns:
        Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    to_encode = {
        "sub": str(subject),
        "org": str(org_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(16),  # Unique token ID for revocation
    }

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_device_token(
    device_id: str,
    org_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT token for device authentication.

    Args:
        device_id: Device ID
        org_id: Organization ID
        expires_delta: Custom expiration time (optional)

    Returns:
        Encoded JWT device token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.device_token_expire_days)

    to_encode = {
        "sub": str(device_id),
        "org": str(org_id),
        "type": "device",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token_type(token: str, expected_type: str) -> Optional[dict[str, Any]]:
    """
    Decode token and verify its type.

    Args:
        token: JWT token string
        expected_type: Expected token type (access, refresh, device)

    Returns:
        Decoded token payload if valid and correct type, None otherwise
    """
    payload = decode_token(token)
    if payload and payload.get("type") == expected_type:
        return payload
    return None


def extract_token_id(token: str) -> Optional[str]:
    """
    Extract the jti (JWT ID) from a token.

    Args:
        token: JWT token string

    Returns:
        Token ID if found, None otherwise
    """
    payload = decode_token(token)
    if payload:
        return payload.get("jti")
    return None


# =============================================================================
# Multi-Factor Authentication (MFA)
# =============================================================================
def generate_mfa_secret() -> str:
    """
    Generate a new TOTP secret for MFA.

    Returns:
        Base32-encoded secret
    """
    return pyotp.random_base32()


def generate_mfa_backup_codes(count: int = 10) -> list[str]:
    """
    Generate backup codes for MFA recovery.

    Args:
        count: Number of backup codes to generate

    Returns:
        List of backup code strings
    """
    return [secrets.token_hex(4).upper() for _ in range(count)]


def get_mfa_totp_uri(secret: str, email: str, issuer: str = "HoloHub") -> str:
    """
    Generate TOTP URI for QR code generation.

    Args:
        secret: TOTP secret
        email: User email
        issuer: Application name

    Returns:
        otpauth:// URI for QR code
    """
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=issuer,
    )


def verify_mfa_totp(secret: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify TOTP code against secret.

    Args:
        secret: TOTP secret
        code: 6-digit TOTP code
        valid_window: Time window to accept (default: 1 = past & present)

    Returns:
        True if code is valid
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=valid_window)


def hash_backup_code(code: str) -> str:
    """
    Hash a backup code for storage.

    Args:
        code: Backup code string

    Returns:
        Hashed backup code
    """
    return get_password_hash(code.upper())


def verify_backup_code(code: str, hashed_code: str) -> bool:
    """
    Verify a backup code against its hash.

    Args:
        code: Backup code to verify
        hashed_code: Hashed code from database

    Returns:
        True if code matches
    """
    return verify_password(code.upper(), hashed_code)


# =============================================================================
# Device Authentication
# =============================================================================
def hash_device_secret(secret: str) -> str:
    """
    Hash a device secret using Argon2id.

    Argon2 is more resistant to GPU/ASIC attacks than bcrypt,
    making it suitable for device authentication.

    Args:
        secret: Device secret string

    Returns:
        Argon2id hash
    """
    return argon2_hasher.hash(secret)


def verify_device_secret(secret: str, hash: str) -> bool:
    """
    Verify a device secret against its hash.

    Args:
        secret: Device secret to verify
        hash: Argon2id hash from database

    Returns:
        True if secret matches
    """
    try:
        return argon2_hasher.verify(hash, secret)
    except argon2.exceptions.VerifyMismatchError:
        return False


def generate_activation_code(length: int = 9) -> str:
    """
    Generate a device activation code.

    Args:
        length: Code length (default 9 for XXX-XXX-XXX format)

    Returns:
        Activation code string
    """
    code = secrets.token_hex(length)[:length].upper()
    # Format as XXX-XXX-XXX
    if length == 9:
        return f"{code[:3]}-{code[3:6]}-{code[6:]}"
    return code


# =============================================================================
# General Security Utilities
# =============================================================================
def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        API key string
    """
    return f"hh_{secrets.token_urlsafe(32)}"


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS attacks.

    Args:
        text: Input text

    Returns:
        Sanitized text
    """
    # Remove null bytes
    text = text.replace("\x00", "")
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address

    Returns:
        True if email format is valid
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_slug(slug: str) -> bool:
    """
    Validate slug format for URLs.

    Args:
        slug: Slug string

    Returns:
        True if slug format is valid
    """
    import re

    # Only lowercase alphanumeric, hyphens, no consecutive hyphens
    pattern = r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
    return re.match(pattern, slug) is not None


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.

    Args:
        text: Text to slugify

    Returns:
        Slug string
    """
    import re

    # Convert to lowercase
    slug = text.lower()
    # Replace spaces with hyphens
    slug = re.sub(r"\s+", "-", slug)
    # Remove special characters
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    # Remove consecutive hyphens
    slug = re.sub(r"-{2,}", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug
