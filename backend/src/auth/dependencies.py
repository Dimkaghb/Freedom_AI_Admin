from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from .crud import verify_token, get_user_by_email
from ..users.models import UserInDB

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify JWT token and return current user

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        User dict from database

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user email from token
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current active user

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        Active user dict

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def require_admin(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Require admin role for endpoint access

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        Admin user dict

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.get("role") not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def require_superadmin(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Require superadmin role for endpoint access

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        Superadmin user dict

    Raises:
        HTTPException: If user is not a superadmin
    """
    if current_user.get("role") != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required"
        )
    return current_user


async def require_director(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Require director, admin, or superadmin role for endpoint access

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        User dict with director or higher privileges

    Raises:
        HTTPException: If user does not have director privileges
    """
    if current_user.get("role") not in ["director", "admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Director privileges or higher required"
        )
    return current_user


def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify refresh token and return user email

    Args:
        token: Refresh token string

    Returns:
        User email if valid, None otherwise
    """
    payload = verify_token(token)
    if not payload:
        return None

    # Check token type
    if payload.get("type") != "refresh":
        logger.warning("Invalid token type for refresh")
        return None

    return payload.get("sub")
