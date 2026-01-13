from datetime import datetime, timedelta
from typing import Optional
import jwt
from starlette.config import Config

config = Config(".env")

SECRET_KEY = config("SECRET_KEY", default="67804844a853335c220adfade1ac937e5d53ad3ec8724ba2b9ed4ebf761888f5")
ALGORITHM = config("ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=30)
REFRESH_TOKEN_EXPIRE_DAYS = config("REFRESH_TOKEN_EXPIRE_DAYS", cast=int, default=7)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """Verify and decode an access token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def verify_refresh_token(token: str) -> dict:
    """Verify and decode a refresh token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Refresh token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid refresh token")


def decode_access_token(token: str) -> dict:
    """Decode access token without verification (use verify_access_token for validation)"""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False})


def decode_refresh_token(token: str) -> dict:
    """Decode refresh token without verification (use verify_refresh_token for validation)"""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False})

