from fastapi import APIRouter, HTTPException, status, Path, Query, Depends
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure
import logging
from typing import Optional

from .models import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse
from ..auth.dependencies import get_current_user, require_admin
from .utils import (
    create_company as db_create_company,
    get_all_companies as db_get_all_companies,
    get_company_by_id as db_get_company_by_id,
    update_company as db_update_company,
    delete_company as db_delete_company
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router for companies endpoints
router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/create", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company_endpoint(company_data: CompanyCreate, current_admin: dict = Depends(require_admin)):
    """
    Create a new company.

    This endpoint allows creating new companies with a name, holding reference, and optional description.

    Args:
        company_data (CompanyCreate): Company creation data including name, holding_id, and optional description

    Returns:
        CompanyResponse: Created company data with MongoDB ObjectId

    Raises:
        HTTPException: 400 for validation errors (empty name, duplicate name, invalid holding_id),
                      500 for server/database errors

    Example Request:
        ```json
        {
            "name": "TechCorp Inc",
            "description": "Technology company",
            "holding_id": "507f1f77bcf86cd799439011",
            "admin_id": "507f1f77bcf86cd799439012"
        }
        ```
    """
    try:
        new_company = db_create_company(
            name=company_data.name,
            holding_id=company_data.holding_id,
            description=company_data.description,
            admin_id=company_data.admin_id
        )

        logger.info(f"Company created successfully via API: {company_data.name}")
        return new_company

    except ValueError as e:
        # Handle validation errors (empty name, duplicate name, invalid IDs, etc.)
        logger.warning(f"Company creation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during company creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during company creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/list", response_model=CompanyListResponse)
def list_companies_endpoint(
    holding_id: Optional[str] = Query(None, description="Filter by holding ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all companies, optionally filtered by holding.

    This endpoint retrieves all active (non-deleted) companies from the database,
    sorted by creation date (newest first). Can be filtered by holding_id.

    Args:
        holding_id (str, optional): Filter companies by holding ID

    Returns:
        CompanyListResponse: List of companies with total count

    Raises:
        HTTPException: 500 for server/database errors

    Example Response:
        ```json
        {
            "companies": [
                {
                    "id": "507f1f77bcf86cd799439011",
                    "name": "TechCorp Inc",
                    "description": "Technology company",
                    "holding_id": "507f1f77bcf86cd799439012",
                    "admin_id": "507f1f77bcf86cd799439013",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                }
            ],
            "total": 1
        }
        ```
    """
    try:
        companies = db_get_all_companies(holding_id=holding_id)

        logger.info(f"Retrieved {len(companies)} companies via API")

        return CompanyListResponse(
            companies=companies,
            total=len(companies)
        )

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during companies retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during companies retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company_endpoint(
    company_id: str = Path(..., description="MongoDB ObjectId of the company"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific company by ID.

    Args:
        company_id (str): MongoDB ObjectId as string

    Returns:
        CompanyResponse: Company data

    Raises:
        HTTPException: 400 for invalid ID format,
                      404 if company not found,
                      500 for server/database errors
    """
    try:
        company = db_get_company_by_id(company_id)

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company not found with ID: {company_id}"
            )

        logger.info(f"Retrieved company {company_id} via API")
        return company

    except ValueError as e:
        # Handle invalid ObjectId format
        logger.warning(f"Invalid company ID format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except HTTPException:
        # Re-raise HTTPException as is
        raise

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during company retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during company retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company_endpoint(
    company_id: str = Path(..., description="MongoDB ObjectId of the company"),
    company_data: CompanyUpdate = None,
    current_admin: dict = Depends(require_admin)
):
    """
    Update a company.

    This endpoint allows updating the name, description, and admin_id of an existing company.

    Args:
        company_id (str): MongoDB ObjectId as string
        company_data (CompanyUpdate): Updated company data

    Returns:
        CompanyResponse: Updated company data

    Raises:
        HTTPException: 400 for validation errors (invalid ID, empty name, duplicate name),
                      404 if company not found,
                      500 for server/database errors

    Example Request:
        ```json
        {
            "name": "Updated Company Name",
            "description": "Updated description",
            "admin_id": "507f1f77bcf86cd799439013"
        }
        ```
    """
    try:
        updated_company = db_update_company(
            company_id=company_id,
            name=company_data.name,
            description=company_data.description,
            admin_id=company_data.admin_id
        )

        logger.info(f"Company {company_id} updated successfully via API")
        return updated_company

    except ValueError as e:
        # Handle validation errors (invalid ID, empty name, duplicate name, not found)
        logger.warning(f"Company update validation error: {str(e)}")

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
        logger.error(f"Database connection error during company update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during company update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.delete("/{company_id}", status_code=status.HTTP_200_OK)
def delete_company_endpoint(
    company_id: str = Path(..., description="MongoDB ObjectId of the company"),
    current_admin: dict = Depends(require_admin)
):
    """
    Delete a company permanently.

    This endpoint permanently removes a company from the database.

    Args:
        company_id (str): MongoDB ObjectId as string

    Returns:
        dict: Success message

    Raises:
        HTTPException: 400 for invalid ID format,
                      404 if company not found,
                      500 for server/database errors

    Example Response:
        ```json
        {
            "message": "Company deleted successfully",
            "company_id": "507f1f77bcf86cd799439011"
        }
        ```
    """
    try:
        success = db_delete_company(company_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company not found with ID: {company_id}"
            )

        logger.info(f"Company {company_id} deleted successfully via API")

        return {
            "message": "Company deleted successfully",
            "company_id": company_id
        }

    except ValueError as e:
        # Handle validation errors (invalid ID, not found)
        logger.warning(f"Company deletion validation error: {str(e)}")

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
        logger.error(f"Database connection error during company deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during company deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/health/status")
def health_check():
    """
    Health check endpoint for the companies service.

    Returns:
        dict: Service status information
    """
    return {
        "status": "healthy",
        "service": "companies",
        "message": "Companies service is running"
    }
