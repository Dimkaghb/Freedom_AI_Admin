from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile
from typing import List, Optional
from pymongo.errors import ConnectionFailure
import logging

from .models import FolderCreate, FolderRename, FolderResponse, FolderInDB
from ..auth.dependencies import get_current_user
from .utils import list_folders_for_user
from ..settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kbase", tags=["knowledge_base"])


@router.get("/list", response_model=List[dict])
async def list_folders_endpoint(current_user: dict = Depends(get_current_user)):
    """
    List all folders for the current user based on their role and permissions.

    Role-based access control:
    - **superadmin**: Sees all folders across all holdings, companies, and departments
    - **admin**: Sees folders for their specific company and all its departments
    - **director**: Sees folders for their specific department only
    - **user**: Sees folders for their specific department (read-only access)

    Args:
        current_user (dict): Current authenticated user from JWT token

    Returns:
        List[dict]: List of folder documents the user has access to

    Raises:
        HTTPException:
            - 500: Database connection error or server error

    Example Response:
        ```json
        [
            {
                "id": "507f1f77bcf86cd799439011",
                "name": "Company Documents",
                "type": "documents",
                "holding_id": "507f1f77bcf86cd799439012",
                "company_id": "507f1f77bcf86cd799439013",
                "department_id": null,
                "admin_id": "507f1f77bcf86cd799439014",
                "fileIds": [],
                "foldersids": [],
                "parentID": null,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        ]
        ```
    """
    try:
        folders = list_folders_for_user(current_user)

        user_id = str(current_user.get("_id"))
        user_email = current_user.get("email")
        user_role = current_user.get("role")

        logger.info(
            f"Successfully retrieved {len(folders)} folders for user {user_email} "
            f"(ID: {user_id}, Role: {user_role})"
        )

        return folders

    except ConnectionFailure as e:
        logger.error(f"Database connection error while listing folders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        user_id = str(current_user.get("_id", "unknown"))
        logger.error(f"Unexpected error while listing folders for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving folders."
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the knowledge base service.

    Returns:
        dict: Service status information
    """
    return {
        "status": "healthy",
        "service": "knowledge_base",
        "message": "Knowledge base service is running"
    }
