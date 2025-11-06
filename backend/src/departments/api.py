from fastapi import APIRouter, HTTPException, status, Path, Query, Depends
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure
import logging
from typing import Optional

from .models import DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentListResponse
from ..auth.dependencies import get_current_user, require_admin
from .utils import (
    create_department as db_create_department,
    get_all_departments as db_get_all_departments,
    get_department_by_id as db_get_department_by_id,
    update_department as db_update_department,
    delete_department as db_delete_department
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router for departments endpoints
router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("/create", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department_endpoint(department_data: DepartmentCreate, current_admin: dict = Depends(require_admin)):
    """
    Create a new department.

    This endpoint allows creating new departments with a name, company reference, and optional description.

    Args:
        department_data (DepartmentCreate): Department creation data including name, company_id, and optional description

    Returns:
        DepartmentResponse: Created department data with MongoDB ObjectId

    Raises:
        HTTPException: 400 for validation errors (empty name, duplicate name, invalid company_id),
                      500 for server/database errors

    Example Request:
        ```json
        {
            "name": "Research and Development",
            "description": "R&D Department",
            "company_id": "507f1f77bcf86cd799439011",
            "manager_id": "507f1f77bcf86cd799439012"
        }
        ```
    """
    try:
        new_department = db_create_department(
            name=department_data.name,
            company_id=department_data.company_id,
            description=department_data.description,
            manager_id=department_data.manager_id
        )

        logger.info(f"Department created successfully via API: {department_data.name}")
        return new_department

    except ValueError as e:
        # Handle validation errors (empty name, duplicate name, invalid IDs, etc.)
        logger.warning(f"Department creation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during department creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during department creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/list", response_model=DepartmentListResponse)
def list_departments_endpoint(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all departments, optionally filtered by company.

    This endpoint retrieves all active (non-deleted) departments from the database,
    sorted by creation date (newest first). Can be filtered by company_id.

    Args:
        company_id (str, optional): Filter departments by company ID

    Returns:
        DepartmentListResponse: List of departments with total count

    Raises:
        HTTPException: 500 for server/database errors

    Example Response:
        ```json
        {
            "departments": [
                {
                    "id": "607f1f77bcf86cd799439021",
                    "name": "Research and Development",
                    "description": "R&D Department",
                    "company_id": "507f1f77bcf86cd799439011",
                    "manager_id": "507f1f77bcf86cd799439013",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                }
            ],
            "total_count": 1
        }
        ```
    """
    try:
        departments = db_get_all_departments(company_id=company_id)

        logger.info(f"Retrieved {len(departments)} departments via API")

        return DepartmentListResponse(
            departments=departments,
            total_count=len(departments)
        )

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during departments retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during departments retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department_endpoint(
    department_id: str = Path(..., description="MongoDB ObjectId of the department"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific department by ID.

    Args:
        department_id (str): MongoDB ObjectId as string

    Returns:
        DepartmentResponse: Department data

    Raises:
        HTTPException: 400 for invalid ID format,
                      404 if department not found,
                      500 for server/database errors
    """
    try:
        department = db_get_department_by_id(department_id)

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department not found with ID: {department_id}"
            )

        logger.info(f"Retrieved department {department_id} via API")
        return department

    except ValueError as e:
        # Handle invalid ObjectId format
        logger.warning(f"Invalid department ID format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except HTTPException:
        # Re-raise HTTPException as is
        raise

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during department retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during department retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department_endpoint(
    department_id: str = Path(..., description="MongoDB ObjectId of the department"),
    department_data: DepartmentUpdate = None,
    current_admin: dict = Depends(require_admin)
):
    """
    Update a department.

    This endpoint allows updating the name, description, and manager_id of an existing department.

    Args:
        department_id (str): MongoDB ObjectId as string
        department_data (DepartmentUpdate): Updated department data

    Returns:
        DepartmentResponse: Updated department data

    Raises:
        HTTPException: 400 for validation errors (invalid ID, empty name, duplicate name),
                      404 if department not found,
                      500 for server/database errors

    Example Request:
        ```json
        {
            "name": "Updated Department Name",
            "description": "Updated description",
            "manager_id": "507f1f77bcf86cd799439013"
        }
        ```
    """
    try:
        updated_department = db_update_department(
            department_id=department_id,
            name=department_data.name,
            description=department_data.description,
            manager_id=department_data.manager_id
        )

        logger.info(f"Department {department_id} updated successfully via API")
        return updated_department

    except ValueError as e:
        # Handle validation errors (invalid ID, empty name, duplicate name, not found)
        logger.warning(f"Department update validation error: {str(e)}")

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
        logger.error(f"Database connection error during department update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during department update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.delete("/{department_id}", status_code=status.HTTP_200_OK)
def delete_department_endpoint(
    department_id: str = Path(..., description="MongoDB ObjectId of the department"),
    current_admin: dict = Depends(require_admin)
):
    """
    Delete a department permanently.

    This endpoint permanently removes a department from the database.

    Args:
        department_id (str): MongoDB ObjectId as string

    Returns:
        dict: Success message

    Raises:
        HTTPException: 400 for invalid ID format,
                      404 if department not found,
                      500 for server/database errors

    Example Response:
        ```json
        {
            "message": "Department deleted successfully",
            "department_id": "607f1f77bcf86cd799439021"
        }
        ```
    """
    try:
        success = db_delete_department(department_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department not found with ID: {department_id}"
            )

        logger.info(f"Department {department_id} deleted successfully via API")

        return {
            "message": "Department deleted successfully",
            "department_id": department_id
        }

    except ValueError as e:
        # Handle validation errors (invalid ID, not found)
        logger.warning(f"Department deletion validation error: {str(e)}")

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
        logger.error(f"Database connection error during department deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during department deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/health/status")
def health_check():
    """
    Health check endpoint for the departments service.

    Returns:
        dict: Service status information
    """
    return {
        "status": "healthy",
        "service": "departments",
        "message": "Departments service is running"
    }
