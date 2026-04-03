# =============================================================================
# Zorvyn Finance Backend — Security Utilities
# =============================================================================
# Provides password hashing and JWT token management for authentication.
#
# Architecture:
#   1. Password Hashing — Uses bcrypt via passlib for secure, salted hashing.
#   2. JWT Tokens — Uses PyJWT for stateless authentication tokens.
#
# Security Notes:
#   - Passwords are NEVER stored in plaintext. Only bcrypt hashes are saved.
#   - JWT tokens contain the user ID and role in the payload.
#   - Token expiration is configurable via JWT_EXPIRE_MINUTES in .env.
#   - The JWT secret MUST be changed from the default in production.
#
# Usage:
#   from app.core.security import hash_password, verify_password
#   from app.core.security import create_access_token, decode_access_token
# =============================================================================

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings


# ---------------------------------------------------------------------------
# Password Hashing Context
# ---------------------------------------------------------------------------
# CryptContext manages the hashing algorithm and provides a clean API.
# - bcrypt is the recommended algorithm for password hashing.
# - "deprecated='auto'" means if we ever switch algorithms, old hashes
#   will still be verifiable but new hashes will use the new scheme.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt hash string (includes salt and algorithm info).

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> hashed  # "$2b$12$..." (60-character bcrypt hash)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password:  The password to check.
        hashed_password: The stored bcrypt hash to compare against.

    Returns:
        True if the password matches the hash, False otherwise.

    Example:
        >>> hashed = hash_password("my_password")
        >>> verify_password("my_password", hashed)      # True
        >>> verify_password("wrong_password", hashed)    # False
    """
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT Token Management
# ---------------------------------------------------------------------------

def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.

    The token payload includes:
    - All key-value pairs from `data` (typically 'sub' for user ID and 'role')
    - 'exp' (expiration timestamp) — auto-calculated from JWT_EXPIRE_MINUTES

    Args:
        data: Dictionary of claims to include in the token.
              Must include 'sub' (subject/user ID) at minimum.
              Example: {"sub": "660f1a...", "role": "admin"}

    Returns:
        Encoded JWT string.

    Example:
        >>> token = create_access_token({"sub": "user_id_1", "role": "admin"})
        >>> token  # "eyJhbGciOiJIUzI1NiIs..."
    """
    # Copy data to avoid mutating the original dict
    to_encode = data.copy()

    # Calculate expiration time
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Encode and sign the token
    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Checks:
    - Signature validity (using JWT_SECRET)
    - Token expiration (raises if expired)
    - Algorithm match (must be JWT_ALGORITHM)

    Args:
        token: The encoded JWT string from the Authorization header.

    Returns:
        Decoded payload dictionary containing claims (sub, role, exp, etc.).

    Raises:
        jwt.ExpiredSignatureError: Token has expired.
        jwt.InvalidTokenError: Token is malformed, has invalid signature, etc.

    Example:
        >>> payload = decode_access_token(token)
        >>> payload["sub"]   # "user_id_1"
        >>> payload["role"]  # "admin"
    """
    payload = jwt.decode(
        jwt=token,
        key=settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return payload
