from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import logging

from .crud import authenticate_user, update_user_profile, create_access_token, create_refresh_token
from .dependencies import verify_refresh_token, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str
  
@router.post("/login")
async def login(login_data: LoginRequest):
    """
    Login endpoint - returns access token, refresh token, and user info
    """
    try:
        logger.info(f"Login attempt for email: {login_data.email}")
        user = await authenticate_user(login_data.email, login_data.password)
        if not user:
            logger.warning(f"Failed login attempt for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неправильный email или пароль"
            )

        # Create access token and refresh token with user email
        access_token = create_access_token(data={"sub": user["email"], "role": user.get("role", "user")})
        refresh_token = create_refresh_token(data={"sub": user["email"]})
        logger.info(f"Successful login for email: {login_data.email}")

        try:
            user_info = {
                "id": str(user.get("id") or user.get("_id", "")),
                "name": user.get("full_name", "") or user.get("name", ""),
                "email": user.get("email", ""),
                "role": user.get("role", "user")
            }

            user_response = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": user_info,
                "message": "Login successful"
            }

            logger.debug(f"Login response: {user_response}")
            return user_response
        except Exception as e:
            logger.error(f"Error creating user response: {e}")
            # Return minimal response if user serialization fails
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh")
async def refresh_access_token(refresh_data: RefreshTokenRequest):
    """
    Refresh token endpoint - returns new access token using refresh token
    """
    try:
        # Verify refresh token
        email = verify_refresh_token(refresh_data.refresh_token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Get user from database (to check if still exists and active)
        from .crud import get_user_by_email
        user = get_user_by_email(email)
        if not user or not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new access token
        access_token = create_access_token(data={"sub": email, "role": user.get("role", "user")})

        logger.info(f"Token refreshed for email: {email}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user info from token
    """
    try:
        user_info = {
            "id": str(current_user.get("id") or current_user.get("_id", "")),
            "name": current_user.get("full_name", "") or current_user.get("name", ""),
            "email": current_user.get("email", ""),
            "role": current_user.get("role", "user"),
            "is_active": current_user.get("is_active", True)
        }
        return user_info
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user info: {str(e)}"
        )



