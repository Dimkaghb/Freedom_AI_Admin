from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure
import logging

from .models import UserCreate, UserCreateResponse
from .utils import add_user_by_admin
from ..auth.dependencies import require_admin

# Configure logging
logger = logging.getLogger(__name__)

# Create router for user endpoints
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/create", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user_data: UserCreate, current_admin: dict = Depends(require_admin)):
    """
    Create a new user by admin.
    
    This endpoint allows administrators to create new users with automatically
    generated secure passwords. The temporary password is returned once for
    the admin to share with the new user.
    
    Args:
        user_data (UserCreate): User creation data including email, role, and optional full_name
        
    Returns:
        UserCreateResponse: Created user data with temporary password
        
    Raises:
        HTTPException: 400 for validation errors, 409 for duplicate email, 500 for server errors
    """
    try:
        # Create user using the comprehensive function
        new_user = add_user_by_admin(
            email=user_data.email,
            role=user_data.role,
            full_name=user_data.full_name
        )
        
        logger.info(f"User created successfully via API: {user_data.email}")
        return new_user
        
    except ValueError as e:
        # Handle validation errors (invalid email, role, duplicate user, etc.)
        logger.warning(f"User creation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during user creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during user creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the users service.
    
    Returns:
        dict: Service status information
    """
    return {
        "status": "healthy",
        "service": "users",
        "message": "Users service is running"
    }