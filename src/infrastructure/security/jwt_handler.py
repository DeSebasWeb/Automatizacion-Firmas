"""JWT token handling."""
from datetime import datetime, timedelta, timezone
from typing import Dict
import jwt
from src.infrastructure.api.config import settings


class JWTHandler:
    """
    Handle JWT token creation and validation.

    Responsibilities:
    - Create access tokens
    - Create refresh tokens
    - Decode and validate tokens
    - Handle token expiration

    Token payload structure:
    - sub: User ID (UUID string)
    - email: User email
    - exp: Expiration timestamp
    - iat: Issued at timestamp
    - type: Token type ("access" or "refresh")
    """

    def __init__(self):
        """Initialize JWT handler with settings from config."""
        self._secret_key = settings.SECRET_KEY
        self._algorithm = settings.ALGORITHM
        self._access_token_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self._refresh_token_expire = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User identifier (UUID string)
            email: User email

        Returns:
            Encoded JWT token

        Example:
            >>> handler = JWTHandler()
            >>> token = handler.create_access_token("123e4567-e89b-12d3-a456-426614174000", "user@example.com")
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._access_token_expire)

        payload = {
            "sub": user_id,
            "email": email,
            "exp": expires_at,
            "iat": now,
            "type": "access"
        }

        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        return token

    def create_refresh_token(self, user_id: str) -> str:
        """
        Create JWT refresh token.

        Refresh tokens have longer expiration and fewer claims for security.

        Args:
            user_id: User identifier (UUID string)

        Returns:
            Encoded JWT refresh token

        Example:
            >>> handler = JWTHandler()
            >>> refresh_token = handler.create_refresh_token("123e4567-e89b-12d3-a456-426614174000")
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=self._refresh_token_expire)

        payload = {
            "sub": user_id,
            "exp": expires_at,
            "iat": now,
            "type": "refresh"
        }

        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        return token

    def decode_token(self, token: str) -> Dict:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dictionary

        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid or malformed

        Example:
            >>> handler = JWTHandler()
            >>> payload = handler.decode_token(token)
            >>> user_id = payload["sub"]
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            # Re-raise for caller to handle
            raise
        except jwt.InvalidTokenError:
            # Re-raise for caller to handle
            raise

    def get_user_id_from_token(self, token: str) -> str:
        """
        Extract user ID from token.

        Convenience method that decodes token and extracts the user ID.

        Args:
            token: JWT token string

        Returns:
            User ID (UUID string) from token's "sub" claim

        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
            KeyError: Token missing "sub" claim

        Example:
            >>> handler = JWTHandler()
            >>> user_id = handler.get_user_id_from_token(token)
        """
        payload = self.decode_token(token)
        return payload["sub"]

    def get_token_type(self, token: str) -> str:
        """
        Get token type from payload.

        Args:
            token: JWT token string

        Returns:
            Token type ("access" or "refresh")

        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
        """
        payload = self.decode_token(token)
        return payload.get("type", "access")

    def get_expiration_seconds(self) -> int:
        """
        Get access token expiration in seconds.

        Useful for returning to client how long the token is valid.

        Returns:
            Number of seconds until access token expires
        """
        return self._access_token_expire * 60
