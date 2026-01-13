from .jwt import (
    create_access_token,
    verify_access_token,
    decode_access_token,
    create_refresh_token,
    verify_refresh_token,
    decode_refresh_token
)
from .password import verify_password, hash_password
from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_user_response,
    oauth2_scheme
)

__all__ = [
    "Auth",
    "create_access_token",
    "verify_access_token",
    "decode_access_token",
    "create_refresh_token",
    "verify_refresh_token",
    "decode_refresh_token",
    "verify_password",
    "hash_password",
    "get_current_user",
    "get_current_active_user",
    "get_current_user_response",
    "oauth2_scheme"
]


class Auth:
    """Authentication utility class with static methods"""
    
    @staticmethod
    def create_access_token(data: dict):
        """Create an access token"""
        return create_access_token(data)
    
    @staticmethod
    def verify_access_token(token: str):
        """Verify an access token"""
        return verify_access_token(token)
    
    @staticmethod
    def decode_access_token(token: str):
        """Decode an access token"""
        return decode_access_token(token)
    
    @staticmethod
    def create_refresh_token(data: dict):
        """Create a refresh token"""
        return create_refresh_token(data)
    
    @staticmethod
    def verify_refresh_token(token: str):
        """Verify a refresh token"""
        return verify_refresh_token(token)
    
    @staticmethod
    def decode_refresh_token(token: str):
        """Decode a refresh token"""
        return decode_refresh_token(token)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str):
        """Verify a plain password against a hashed password"""
        return verify_password(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str):
        """Hash a password"""
        return hash_password(password)

