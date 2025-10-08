from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ACCESS_TOKEN_SECRET_KEY = settings.JWT_SECRET_KEY
REFRESH_TOKEN_SECRET_KEY = settings.JWT_REFRESH_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Token payload data. Should include:
            - sub: User ID (required)
            - Additional custom claims as needed
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Note:
        - Automatically adds 'exp' (expiration) and 'type' claims
        - Organization context provided via X-Organization-ID header (not in token)
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, ACCESS_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Token payload data. Should include:
            - sub: User ID (required)
            - Additional custom claims as needed
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Note:
        - Automatically adds 'exp' (expiration) and 'type' claims
        - Organization context provided via X-Organization-ID header (not in token)
        - Longer expiration than access tokens
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, ACCESS_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, REFRESH_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


# API Key generation and verification


def generate_api_key(prefix: str = "agt_live") -> str:
    """
    Generate a new API key with prefix and random suffix.

    Args:
        prefix: API key prefix (default: "agt_live" for agent live keys)

    Returns:
        Full API key string (e.g., "agt_live_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p")

    Example:
        >>> api_key = generate_api_key()
        >>> print(api_key[:16])
        'agt_live_1a2b3c4'
        >>> len(api_key)
        48

    Note:
        - Format: {prefix}_{random_32_chars}
        - Random part uses URL-safe base64 encoding (a-zA-Z0-9_-)
        - Total length: ~48 characters
        - Key should be stored hashed, this plaintext is shown only once
    """
    import secrets

    # Generate URL-safe random suffix (24 bytes -> 32 base64 characters)
    random_suffix = secrets.token_urlsafe(24)[:32]

    return f"{prefix}_{random_suffix}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using bcrypt.

    Args:
        api_key: Plain text API key to hash

    Returns:
        Bcrypt hash of the API key

    Example:
        >>> api_key = "agt_live_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p"
        >>> key_hash = hash_api_key(api_key)
        >>> print(key_hash[:7])
        '$2b$12$'

    Note:
        - Uses the same pwd_context (bcrypt) as password hashing
        - Hash is ~60 characters long
        - Bcrypt automatically includes salt
    """
    return pwd_context.hash(api_key)


def verify_api_key_hash(api_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its bcrypt hash.

    Args:
        api_key: Plain text API key to verify
        hashed_key: Bcrypt hash to check against

    Returns:
        True if key matches hash, False otherwise

    Example:
        >>> api_key = "agt_live_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p"
        >>> key_hash = hash_api_key(api_key)
        >>> verify_api_key_hash(api_key, key_hash)
        True
        >>> verify_api_key_hash("wrong_key", key_hash)
        False

    Note:
        - Uses the same pwd_context (bcrypt) as password verification
        - Timing-safe comparison
    """
    return pwd_context.verify(api_key, hashed_key)


def extract_key_prefix(api_key: str, prefix_length: int = 16) -> str:
    """
    Extract the prefix from an API key for identification.

    Args:
        api_key: Full API key string
        prefix_length: Number of characters to extract (default: 16)

    Returns:
        First N characters of the API key

    Example:
        >>> api_key = "agt_live_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p"
        >>> extract_key_prefix(api_key)
        'agt_live_1a2b3c4'
        >>> extract_key_prefix(api_key, 12)
        'agt_live_1a2'

    Note:
        - Used for fast lookup before expensive bcrypt verification
        - Stored in database with unique constraint
        - Default 16 chars provides good uniqueness while being identifiable
    """
    return api_key[:prefix_length]
