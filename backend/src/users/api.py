from fastapi import APIRouter, HTTPException, status, Depends, Query, Body
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure
import logging
from typing import Optional

from .models import (
    UserCreate,
    UserCreateResponse,
    RegistrationLinkCreate,
    RegistrationLinkResponse,
    PendingUserCreate,
    PendingUserResponse,
    PendingUsersListResponse,
    UserApprovalAction,
    UserListResponse
)
from .utils import (
    add_user_by_admin,
    create_registration_link,
    register_pending_user,
    list_pending_users,
    approve_pending_user,
    reject_pending_user,
    list_users_with_filter
)
from ..auth.dependencies import require_admin, get_current_user

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


@router.post("/create-registration-link", response_model=RegistrationLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_registration_link_endpoint(
    link_data: RegistrationLinkCreate,
    current_admin: dict = Depends(require_admin)
):
    """
    Create a registration link for new users (expires in 24 hours).

    Allows admins to generate registration links for:
    - Company-level: admin role (no department_id required)
    - Department-level: director or user roles (department_id required)

    Args:
        link_data: Registration link creation data
        current_admin: Authenticated admin user

    Returns:
        RegistrationLinkResponse: Created link with registration URL

    Raises:
        HTTPException:
            - 400: Invalid company_id or department_id
            - 403: Admin lacks permission
            - 500: Server error

    Example Request:
        ```json
        {
            "company_id": "507f1f77bcf86cd799439011",
            "department_id": "507f1f77bcf86cd799439013",
            "role": "user"
        }
        ```
    """
    try:
        link = create_registration_link(link_data)
        logger.info(f"Registration link created by admin {current_admin.get('email')}")
        return link

    except ValueError as e:
        logger.warning(f"Registration link creation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ConnectionFailure as e:
        logger.error(f"Database connection error during link creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error during link creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.post("/register", response_model=PendingUserResponse, status_code=status.HTTP_201_CREATED)
async def register_via_link_endpoint(registration_data: PendingUserCreate):
    """
    Register a new user via registration link (creates pending user application).

    The user fills out the registration form which submits to this endpoint.
    The registration creates a pending user that must be approved by an admin.

    Args:
        registration_data: User registration data from form

    Returns:
        PendingUserResponse: Created pending user information

    Raises:
        HTTPException:
            - 400: Invalid link, passwords don't match, or email exists
            - 500: Server error

    Example Request:
        ```json
        {
            "link_id": "abc123def456",
            "email": "user@example.com",
            "full_name": "John Doe",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!"
        }
        ```
    """
    try:
        pending_user = register_pending_user(registration_data)
        logger.info(f"Pending user registration created for {registration_data.email}")
        return pending_user

    except ValueError as e:
        logger.warning(f"User registration validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ConnectionFailure as e:
        logger.error(f"Database connection error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/pending", response_model=PendingUsersListResponse)
async def list_pending_users_endpoint(current_admin: dict = Depends(require_admin)):
    """
    List pending user registrations awaiting approval.

    Filters based on admin's role:
    - superadmin: sees all pending users
    - admin: sees pending users for their company

    Args:
        current_admin: Authenticated admin user

    Returns:
        PendingUsersListResponse: List of pending users with count

    Raises:
        HTTPException:
            - 403: Admin lacks permission
            - 500: Server error

    Example Response:
        ```json
        {
            "pending_users": [
                {
                    "id": "607f1f77bcf86cd799439021",
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "company_id": "507f1f77bcf86cd799439011",
                    "department_id": "507f1f77bcf86cd799439013",
                    "role": "user",
                    "status": "pending",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                }
            ],
            "total_count": 1
        }
        ```
    """
    try:
        pending_users = list_pending_users(current_admin)
        logger.info(f"Listed {len(pending_users)} pending users for admin {current_admin.get('email')}")

        return PendingUsersListResponse(
            pending_users=pending_users,
            total_count=len(pending_users)
        )

    except ValueError as e:
        logger.warning(f"Pending users list validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

    except ConnectionFailure as e:
        logger.error(f"Database connection error while listing pending users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error while listing pending users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.post("/pending/{pending_user_id}/approve", response_model=UserCreateResponse)
async def approve_pending_user_endpoint(
    pending_user_id: str,
    current_admin: dict = Depends(require_admin)
):
    """
    Approve pending user and move them to the users collection.

    Args:
        pending_user_id: MongoDB ObjectId of the pending user
        current_admin: Authenticated admin user

    Returns:
        UserCreateResponse: Approved user information

    Raises:
        HTTPException:
            - 400: Invalid pending_user_id or user not found
            - 403: Admin lacks permission
            - 500: Server error

    Example Response:
        ```json
        {
            "id": "607f1f77bcf86cd799439021",
            "email": "user@example.com",
            "role": "user",
            "full_name": "John Doe",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "temporary_password": "N/A"
        }
        ```
    """
    try:
        approved_user = approve_pending_user(pending_user_id, current_admin)
        logger.info(f"Pending user {pending_user_id} approved by admin {current_admin.get('email')}")
        return approved_user

    except ValueError as e:
        logger.warning(f"Approve user validation error: {str(e)}")
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "permission" in error_msg or "cannot" in error_msg or "only" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    except ConnectionFailure as e:
        logger.error(f"Database connection error while approving user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error while approving user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.post("/pending/{pending_user_id}/reject")
async def reject_pending_user_endpoint(
    pending_user_id: str,
    current_admin: dict = Depends(require_admin)
):
    """
    Reject pending user registration.

    Args:
        pending_user_id: MongoDB ObjectId of the pending user
        current_admin: Authenticated admin user

    Returns:
        dict: Success message with rejection details

    Raises:
        HTTPException:
            - 400: Invalid pending_user_id or user not found
            - 403: Admin lacks permission
            - 500: Server error

    Example Response:
        ```json
        {
            "message": "User registration rejected successfully",
            "pending_user_id": "607f1f77bcf86cd799439021",
            "email": "user@example.com"
        }
        ```
    """
    try:
        result = reject_pending_user(pending_user_id, current_admin)
        logger.info(f"Pending user {pending_user_id} rejected by admin {current_admin.get('email')}")
        return result

    except ValueError as e:
        logger.warning(f"Reject user validation error: {str(e)}")
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "permission" in error_msg or "cannot" in error_msg or "only" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    except ConnectionFailure as e:
        logger.error(f"Database connection error while rejecting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error while rejecting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/list", response_model=UserListResponse)
async def list_users_endpoint(
    status_filter: Optional[str] = Query("active", description="Filter by status: active, blocked"),
    current_admin: dict = Depends(require_admin)
):
    """
    List users with status filter.

    Filters:
    - active: Users with is_active=True
    - blocked: Users with is_active=False
    - pending: Use /users/pending endpoint instead

    Args:
        status_filter: Filter by user status (default: "active")
        current_admin: Authenticated admin user

    Returns:
        UserListResponse: List of users with total count

    Raises:
        HTTPException:
            - 400: Invalid status filter
            - 403: Admin lacks permission
            - 500: Server error

    Example Response:
        ```json
        {
            "users": [
                {
                    "id": "607f1f77bcf86cd799439021",
                    "email": "user@example.com",
                    "role": "user",
                    "full_name": "John Doe",
                    "is_active": true,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                }
            ],
            "total_count": 1
        }
        ```
    """
    try:
        users = list_users_with_filter(current_admin, status_filter)
        logger.info(f"Listed {len(users)} users with filter '{status_filter}' for admin {current_admin.get('email')}")

        return UserListResponse(
            users=users,
            total_count=len(users)
        )

    except ValueError as e:
        logger.warning(f"List users validation error: {str(e)}")
        error_msg = str(e).lower()
        if "permission" in error_msg or "cannot" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    except ConnectionFailure as e:
        logger.error(f"Database connection error while listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error while listing users: {str(e)}")
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