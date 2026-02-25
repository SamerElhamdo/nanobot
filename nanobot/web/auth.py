"""Admin API authentication via Gateway Token."""

import os
import hmac
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_ADMIN_TOKEN_ENV = "GATEWAY_ADMIN_TOKEN"
_ALTERNATIVE_ENV = "NANOBOT_ADMIN_TOKEN"

security = HTTPBearer(auto_error=False)


def _get_expected_token() -> str | None:
    token = os.environ.get(_ADMIN_TOKEN_ENV) or os.environ.get(_ALTERNATIVE_ENV)
    return (token or "").strip() or None


def require_admin_token(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> None:
    """Dependency: require valid Bearer token for admin API. Raises 401 if missing or invalid."""
    expected = _get_expected_token()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin UI disabled: GATEWAY_ADMIN_TOKEN not set",
        )
    if not credentials or credentials.credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    token = (credentials.credentials or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty token",
        )
    if not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def is_admin_configured() -> bool:
    """Return True if admin token is set (admin UI enabled)."""
    return _get_expected_token() is not None
