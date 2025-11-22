from fastapi import APIRouter, HTTPException, status, Path, Depends
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure
import logging

from .models import HoldingCreate, HoldingUpdate, HoldingResponse, HoldingListResponse
from ..auth.dependencies import get_current_user, require_admin
from ..auth.rbac import get_user_scope, require_resource_access
from .utils import (
    create_holding as db_create_holding,
    get_all_holdings as db_get_all_holdings,
    get_holding_by_id as db_get_holding_by_id,
    update_holding as db_update_holding,
    delete_holding as db_delete_holding
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router for holdings endpoints
router = APIRouter(prefix="/holdings", tags=["holdings"])


@router.post("/create", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
def create_holding_endpoint(holding_data: HoldingCreate, current_admin: dict = Depends(require_admin)):
    """
    Create a new holding.

    This endpoint allows creating new holdings with a name and optional description.

    Args:
        holding_data (HoldingCreate): Holding creation data including name and optional description

    Returns:
        HoldingResponse: Created holding data with MongoDB ObjectId

    Raises:
        HTTPException: 400 for validation errors (empty name, duplicate name),
                      500 for server/database errors

    Example Request:
        ```json
        {
            "name": "TechCorp Holdings",
            "description": "Technology conglomerate"
        }
        ```
    """
    try:
        new_holding = db_create_holding(
            name=holding_data.name,
            description=holding_data.description
        )

        logger.info(f"Holding created successfully via API: {holding_data.name}")
        return new_holding

    except ValueError as e:
        # Handle validation errors (empty name, duplicate name, etc.)
        logger.warning(f"Holding creation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during holding creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during holding creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/list", response_model=HoldingListResponse)
def list_holdings_endpoint(current_user: dict = Depends(get_current_user)):
    """
    Get all holdings based on user role.

    This endpoint retrieves holdings that the user has access to:
    - Superadmin: All holdings
    - Admin/Director/User: Only their associated holding (if any)

    Returns:
        HoldingListResponse: List of holdings with total count

    Raises:
        HTTPException: 403 for unauthorized access, 500 for server/database errors

    Example Response:
        ```json
        {
            "holdings": [
                {
                    "id": "507f1f77bcf86cd799439011",
                    "name": "TechCorp Holdings",
                    "description": "Technology conglomerate",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                }
            ],
            "total": 1
        }
        ```
    """
    try:
        # Get user scope for filtering
        scope = get_user_scope(current_user)

        # Get all holdings (will be filtered based on scope)
        all_holdings = db_get_all_holdings()

        # Apply role-based filtering
        if scope.is_superadmin:
            # Superadmin sees all holdings
            filtered_holdings = all_holdings
        elif scope.holding_id:
            # Other roles see only their holding (if they have one)
            filtered_holdings = [h for h in all_holdings if h.id == scope.holding_id]
        else:
            # No holding access
            filtered_holdings = []

        logger.info(
            f"Retrieved {len(filtered_holdings)} holdings for user "
            f"{current_user.get('email')} (role: {scope.role})"
        )

        return HoldingListResponse(
            holdings=filtered_holdings,
            total=len(filtered_holdings)
        )

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during holdings retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during holdings retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/{holding_id}", response_model=HoldingResponse)
def get_holding_endpoint(
    holding_id: str = Path(..., description="MongoDB ObjectId of the holding"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific holding by ID.

    Users can only access holdings they have permission to view:
    - Superadmin: Any holding
    - Admin/Director/User: Only their associated holding

    Args:
        holding_id (str): MongoDB ObjectId as string

    Returns:
        HoldingResponse: Holding data

    Raises:
        HTTPException: 400 for invalid ID format,
                      403 for unauthorized access,
                      404 if holding not found,
                      500 for server/database errors
    """
    try:
        # Check if user has access to this holding
        try:
            require_resource_access(
                current_user=current_user,
                resource_type="holding",
                resource_id=holding_id
            )
        except PermissionError as e:
            logger.warning(f"Access denied: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this holding"
            )

        holding = db_get_holding_by_id(holding_id)

        if not holding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Holding not found with ID: {holding_id}"
            )

        logger.info(f"Retrieved holding {holding_id} via API")
        return holding

    except ValueError as e:
        # Handle invalid ObjectId format
        logger.warning(f"Invalid holding ID format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except HTTPException:
        # Re-raise HTTPException as is
        raise

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during holding retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during holding retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.put("/{holding_id}", response_model=HoldingResponse)
def rename_holding_endpoint(
    holding_id: str = Path(..., description="MongoDB ObjectId of the holding"),
    holding_data: HoldingUpdate = None,
    current_admin: dict = Depends(require_admin)
):
    """
    Update/rename a holding.

    This endpoint allows updating the name and description of an existing holding.

    Args:
        holding_id (str): MongoDB ObjectId as string
        holding_data (HoldingUpdate): Updated holding data

    Returns:
        HoldingResponse: Updated holding data

    Raises:
        HTTPException: 400 for validation errors (invalid ID, empty name, duplicate name),
                      404 if holding not found,
                      500 for server/database errors

    Example Request:
        ```json
        {
            "name": "Updated Holdings Name",
            "description": "Updated description"
        }
        ```
    """
    try:
        updated_holding = db_update_holding(
            holding_id=holding_id,
            name=holding_data.name,
            description=holding_data.description
        )

        logger.info(f"Holding {holding_id} updated successfully via API")
        return updated_holding

    except ValueError as e:
        # Handle validation errors (invalid ID, empty name, duplicate name, not found)
        logger.warning(f"Holding update validation error: {str(e)}")

        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during holding update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during holding update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.delete("/{holding_id}", status_code=status.HTTP_200_OK)
def delete_holding_endpoint(
    holding_id: str = Path(..., description="MongoDB ObjectId of the holding"),
    current_admin: dict = Depends(require_admin)
):
    """
    Delete a holding permanently.

    This endpoint permanently removes a holding from the database.

    Args:
        holding_id (str): MongoDB ObjectId as string

    Returns:
        dict: Success message

    Raises:
        HTTPException: 400 for invalid ID format,
                      404 if holding not found,
                      500 for server/database errors

    Example Response:
        ```json
        {
            "message": "Holding deleted successfully",
            "holding_id": "507f1f77bcf86cd799439011"
        }
        ```
    """
    try:
        success = db_delete_holding(holding_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Holding not found with ID: {holding_id}"
            )

        logger.info(f"Holding {holding_id} deleted successfully via API")

        return {
            "message": "Holding deleted successfully",
            "holding_id": holding_id
        }

    except ValueError as e:
        # Handle validation errors (invalid ID, not found)
        logger.warning(f"Holding deletion validation error: {str(e)}")

        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except HTTPException:
        # Re-raise HTTPException as is
        raise

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during holding deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during holding deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/health/status")
def health_check():
    """
    Health check endpoint for the holdings service.

    Returns:
        dict: Service status information
    """
    return {
        "status": "healthy",
        "service": "holdings",
        "message": "Holdings service is running"
    }
