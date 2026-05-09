"""CERN SSO authentication module for CDS MCP server."""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

import jwt
import requests

logger = logging.getLogger(__name__)


class CERNAuthError(Exception):
    """Base exception for CERN authentication errors."""

    pass


class TokenExpiredError(CERNAuthError):
    """Raised when the access token has expired."""

    pass


class CERNAuthenticator:
    """CERN SSO authenticator using OAuth2/OIDC client credentials flow."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        audience: str | None = None,
        token_endpoint: str = "https://auth.cern.ch/auth/realms/cern/api-access/token",
        jwks_endpoint: str = "https://auth.cern.ch/auth/realms/cern/protocol/openid-connect/certs",
    ):
        """Initialize CERN authenticator.

        Args:
            client_id: OIDC client ID (can be set via CERN_CLIENT_ID env var)
            client_secret: OIDC client secret (can be set via CERN_CLIENT_SECRET env var)
            audience: Target audience for the token (default: "cds-api")
            token_endpoint: CERN token endpoint URL
            jwks_endpoint: CERN JWKS endpoint for token validation
        """
        self.client_id = client_id or os.getenv("CERN_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("CERN_CLIENT_SECRET")
        self.audience = audience
        self.token_endpoint = token_endpoint
        self.jwks_endpoint = jwks_endpoint

        if not self.client_id or not self.client_secret:
            raise CERNAuthError(
                "CERN client credentials not provided. Set CERN_CLIENT_ID and CERN_CLIENT_SECRET "
                "environment variables or pass them to the constructor."
            )

        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_cache_expires: datetime | None = None

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Get a valid access token, refreshing if necessary.

        Args:
            force_refresh: Force token refresh even if current token is valid

        Returns:
            Valid access token

        Raises:
            CERNAuthError: If token acquisition fails
        """
        if (
            not force_refresh
            and self._is_token_valid()
            and self._access_token is not None
        ):
            return self._access_token

        logger.info("Acquiring new access token from CERN SSO")

        try:
            # Prepare token request data
            token_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            # Only add audience if specified
            if self.audience:
                token_data["audience"] = self.audience

            response = requests.post(
                self.token_endpoint,
                data=token_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "cds-mcp/0.1.2",
                },
                timeout=30,
            )
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]

            # Calculate expiry time (subtract 60 seconds for safety margin)
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

            logger.info(
                f"Successfully acquired access token, expires at {self._token_expires_at}"
            )
            return self._access_token

        except requests.RequestException as e:
            raise CERNAuthError(f"Failed to acquire access token: {e}") from e
        except KeyError as e:
            raise CERNAuthError(f"Invalid token response format: missing {e}") from e

    def validate_token(self, token: str) -> dict[str, Any]:
        """Validate an access token and return its claims.

        Args:
            token: JWT access token to validate

        Returns:
            Token claims dictionary

        Raises:
            CERNAuthError: If token validation fails
        """
        try:
            # Get JWKS for signature verification
            jwks = self._get_jwks()

            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise CERNAuthError("Token missing key ID (kid) in header")

            # Find the matching key in JWKS
            key_data = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    key_data = key
                    break

            if not key_data:
                raise CERNAuthError(f"Key ID {kid} not found in JWKS")

            # Convert JWK to PEM format for verification
            public_key = self._jwk_to_pem(key_data)

            # Verify and decode token
            jwt_options: dict[str, Any] = {"verify_exp": True}
            jwt_kwargs: dict[str, Any] = {"algorithms": ["RS256"]}

            # Only verify audience if we have one configured
            if self.audience:
                jwt_options["verify_aud"] = True
                jwt_kwargs["audience"] = self.audience
            else:
                jwt_options["verify_aud"] = False

            claims = jwt.decode(
                token,
                public_key,
                options=jwt_options,  # type: ignore[arg-type]
                **jwt_kwargs,
            )

            logger.debug(
                f"Token validated successfully for subject: {claims.get('sub')}"
            )
            return claims

        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError("Access token has expired") from e
        except jwt.InvalidTokenError as e:
            raise CERNAuthError(f"Token validation failed: {e}") from e
        except Exception as e:
            raise CERNAuthError(f"Unexpected error during token validation: {e}") from e

    def get_auth_headers(self) -> dict[str, str]:
        """Get HTTP headers for authenticated requests.

        Returns:
            Dictionary with Authorization header

        Raises:
            CERNAuthError: If token acquisition fails
        """
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}

    def _is_token_valid(self) -> bool:
        """Check if the current token is valid and not expired."""
        if not self._access_token or not self._token_expires_at:
            return False

        return datetime.now() < self._token_expires_at

    def _get_jwks(self) -> dict[str, Any]:
        """Get JWKS (JSON Web Key Set) for token validation, with caching."""
        # Check cache first
        if (
            self._jwks_cache
            and self._jwks_cache_expires
            and datetime.now() < self._jwks_cache_expires
        ):
            return self._jwks_cache

        logger.debug("Fetching JWKS from CERN SSO")

        try:
            response = requests.get(
                self.jwks_endpoint,
                headers={"User-Agent": "cds-mcp/0.1.0"},
                timeout=30,
            )
            response.raise_for_status()

            self._jwks_cache = response.json()
            # Cache JWKS for 1 hour
            self._jwks_cache_expires = datetime.now() + timedelta(hours=1)

            return self._jwks_cache

        except requests.RequestException as e:
            raise CERNAuthError(f"Failed to fetch JWKS: {e}") from e

    def _jwk_to_pem(self, jwk_data: dict[str, Any]) -> bytes:
        """Convert JWK to PEM format for cryptographic operations."""
        try:
            import base64

            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives.serialization import (
                Encoding,
                PublicFormat,
            )

            # Extract RSA components from JWK
            n = int.from_bytes(
                base64.urlsafe_b64decode(jwk_data["n"] + "=="), byteorder="big"
            )
            e = int.from_bytes(
                base64.urlsafe_b64decode(jwk_data["e"] + "=="), byteorder="big"
            )

            # Create RSA public key
            public_key = rsa.RSAPublicNumbers(e, n).public_key()

            # Convert to PEM format
            pem = public_key.public_bytes(
                encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo
            )

            return pem

        except Exception as e:
            raise CERNAuthError(f"Failed to convert JWK to PEM: {e}") from e


# Global authenticator instance
_authenticator: CERNAuthenticator | None = None


def get_authenticator() -> CERNAuthenticator:
    """Get the global CERN authenticator instance."""
    global _authenticator
    if _authenticator is None:
        _authenticator = CERNAuthenticator()
    return _authenticator


def get_auth_headers() -> dict[str, str]:
    """Convenience function to get authentication headers."""
    return get_authenticator().get_auth_headers()


def is_authenticated() -> bool:
    """Check if we have valid authentication credentials configured."""
    try:
        get_authenticator()
        return True
    except CERNAuthError:
        return False
