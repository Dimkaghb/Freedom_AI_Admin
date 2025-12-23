from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from pymongo.errors import ConnectionFailure
import logging

from .models import (
    FolderResponse,
    FolderListResponse,
    FileResponse,
    FileListResponse,
    FolderPathResponse,
    BreadcrumbItem,
    StorageInfo
)
from ..auth.dependencies import get_current_user
from .utils import (
    list_folders_for_user,
    get_folder_by_id,
    get_folder_path,
    list_files_in_folder,
    get_file_by_id,
    get_storage_info
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kbase", tags=["knowledge_base"])


# ============================================================================
# FOLDER ENDPOINTS
# ============================================================================

@router.get("/folders", response_model=FolderListResponse)
async def list_folders(
    parent_id: Optional[str] = Query(None, description="Parent folder ID (null for root)"),
    current_user: dict = Depends(get_current_user)
):
    """
    List folders based on user role and parent folder.

    Args:
        parent_id: Parent folder ID (None for root folders)
        current_user: Authenticated user from JWT

    Returns:
        FolderListResponse: List of folders with total count

    Raises:
        HTTPException: 500 for database errors

    Example:
        GET /kbase/folders              # Get root folders
        GET /kbase/folders?parent_id=123 # Get subfolders of folder 123
    """
    try:
        folders = list_folders_for_user(current_user, parent_id)

        logger.info(
            f"User {current_user.get('email')} retrieved {len(folders)} folders "
            f"(parent_id: {parent_id})"
        )

        return FolderListResponse(
            folders=folders,
            total=len(folders)
        )

    except ConnectionFailure as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        logger.error(f"Error listing folders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving folders."
        )


@router.get("/folders/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a single folder by ID.

    Args:
        folder_id: Folder ID
        current_user: Authenticated user from JWT

    Returns:
        FolderResponse: Folder details

    Raises:
        HTTPException: 404 if folder not found, 403 if access denied
    """
    try:
        folder = get_folder_by_id(folder_id, current_user)

        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found or access denied"
            )

        logger.info(f"User {current_user.get('email')} retrieved folder {folder_id}")

        return FolderResponse(**folder)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting folder {folder_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving folder."
        )


@router.get("/folders/{folder_id}/path", response_model=FolderPathResponse)
async def get_folder_breadcrumbs(
    folder_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get breadcrumb path from root to folder.

    Args:
        folder_id: Target folder ID
        current_user: Authenticated user from JWT

    Returns:
        FolderPathResponse: Breadcrumb path

    Example Response:
        {
            "path": [
                {"id": null, "name": "Home"},
                {"id": "123", "name": "Documents"},
                {"id": "456", "name": "Reports"}
            ]
        }
    """
    try:
        path = get_folder_path(folder_id, current_user)

        # Add Home at the beginning
        breadcrumbs = [BreadcrumbItem(id=None, name="Home")]
        breadcrumbs.extend([BreadcrumbItem(**item) for item in path])

        logger.info(f"User {current_user.get('email')} retrieved path for folder {folder_id}")

        return FolderPathResponse(path=breadcrumbs)

    except Exception as e:
        logger.error(f"Error getting folder path: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving folder path."
        )


# ============================================================================
# FILE ENDPOINTS
# ============================================================================

@router.get("/files", response_model=FileListResponse)
async def list_files(
    folder_id: Optional[str] = Query(None, description="Folder ID (null for root files)"),
    current_user: dict = Depends(get_current_user)
):
    """
    List files in a specific folder.

    Args:
        folder_id: Folder ID (None for root files)
        current_user: Authenticated user from JWT

    Returns:
        FileListResponse: List of files with total count

    Example:
        GET /kbase/files               # Get root files
        GET /kbase/files?folder_id=123 # Get files in folder 123
    """
    try:
        files = list_files_in_folder(folder_id, current_user)

        logger.info(
            f"User {current_user.get('email')} retrieved {len(files)} files "
            f"(folder_id: {folder_id})"
        )

        return FileListResponse(
            files=files,
            total=len(files)
        )

    except ConnectionFailure as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving files."
        )


@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a single file by ID.

    Args:
        file_id: File ID
        current_user: Authenticated user from JWT

    Returns:
        FileResponse: File details

    Raises:
        HTTPException: 404 if file not found, 403 if access denied
    """
    try:
        file = get_file_by_id(file_id, current_user)

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or access denied"
            )

        logger.info(f"User {current_user.get('email')} retrieved file {file_id}")

        return FileResponse(**file)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving file."
        )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/storage", response_model=StorageInfo)
async def get_storage(
    current_user: dict = Depends(get_current_user)
):
    """
    Get storage usage information for current user.

    Returns:
        StorageInfo: Storage statistics including total files and size
    """
    try:
        storage_info = get_storage_info(current_user)

        logger.info(f"User {current_user.get('email')} retrieved storage info")

        return StorageInfo(**storage_info)

    except Exception as e:
        logger.error(f"Error getting storage info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving storage information."
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
