import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from ..settings import settings
from ..database import get_database

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_org_context(user: dict) -> Dict[str, str]:
    """Extract organizational context from user"""
    return {
        "company_id": user.get("company_id", ""),
        "department_id": user.get("department_id", ""),
        "holding_id": user.get("holding_id", "")
    }


def build_access_filter(user: dict) -> Dict[str, Any]:
    """
    Build MongoDB filter based on user role for data access.

    Args:
        user: User document with role and org IDs

    Returns:
        MongoDB query filter
    """
    role = user.get("role", "user")

    if role == "superadmin":
        return {}  # Access to everything

    elif role == "admin":
        company_id = user.get("company_id")
        if not company_id:
            return {"_id": {"$exists": False}}  # No access
        return {"company_id": company_id}

    elif role in ["director", "user"]:
        department_id = user.get("department_id")
        if not department_id:
            return {"_id": {"$exists": False}}  # No access
        return {"department_id": department_id}

    return {"_id": {"$exists": False}}  # No access for unknown roles


def format_file_size(bytes: int) -> str:
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"


# ============================================================================
# FOLDER OPERATIONS
# ============================================================================

def list_folders_for_user(user: dict, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List folders based on user role and parent folder.

    Args:
        user: User document
        parent_id: Parent folder ID (None for root folders)

    Returns:
        List of folder documents
    """
    try:
        db = get_database()
        folders_collection = db[settings.FOLDERS_COLLECTION]

        # Build access filter
        access_filter = build_access_filter(user)

        # Add parent filter
        query = {**access_filter}
        if parent_id is None:
            query["$or"] = [
                {"parentID": None},
                {"parentID": {"$exists": False}}
            ]
        else:
            query["parentID"] = parent_id

        # Execute query
        folders = list(folders_collection.find(query).sort("name", 1))

        # Convert ObjectId to string
        for folder in folders:
            if "_id" in folder:
                folder["id"] = str(folder["_id"])
                del folder["_id"]

        logger.info(f"Retrieved {len(folders)} folders for user {user.get('email')}")
        return folders

    except Exception as e:
        logger.error(f"Error listing folders: {str(e)}")
        raise


def get_folder_by_id(folder_id: str, user: dict) -> Optional[Dict[str, Any]]:
    """
    Get single folder by ID with access control.

    Args:
        folder_id: Folder ID
        user: User document

    Returns:
        Folder document or None
    """
    try:
        db = get_database()
        folders_collection = db[settings.FOLDERS_COLLECTION]

        # Build query with access control
        access_filter = build_access_filter(user)
        query = {"_id": ObjectId(folder_id), **access_filter}

        folder = folders_collection.find_one(query)

        if folder:
            folder["id"] = str(folder["_id"])
            del folder["_id"]

        return folder

    except Exception as e:
        logger.error(f"Error getting folder {folder_id}: {str(e)}")
        raise


def create_folder(name: str, user: dict, parent_id: Optional[str] = None, folder_type: str = "documents") -> Dict[str, Any]:
    """
    Create a new folder.

    Args:
        name: Folder name
        user: User document
        parent_id: Parent folder ID (None for root)
        folder_type: Folder type

    Returns:
        Created folder document
    """
    try:
        db = get_database()
        folders_collection = db[settings.FOLDERS_COLLECTION]

        # Get organizational context
        org_context = get_user_org_context(user)

        # If parent exists, verify access and get its org context
        if parent_id:
            parent = get_folder_by_id(parent_id, user)
            if not parent:
                raise ValueError("Parent folder not found or access denied")

            # Inherit org context from parent
            org_context = {
                "company_id": parent.get("company_id", ""),
                "department_id": parent.get("department_id", ""),
                "holding_id": parent.get("holding_id", "")
            }

        # Check for duplicate name in same parent
        duplicate_query = {
            "name": name,
            "parentID": parent_id,
            **org_context
        }
        if folders_collection.find_one(duplicate_query):
            raise ValueError(f"Folder '{name}' already exists in this location")

        # Create folder document
        now = datetime.utcnow()
        folder_doc = {
            "name": name,
            "type": folder_type,
            "parentID": parent_id,
            "fileIds": [],
            "foldersids": [],
            **org_context,
            "created_at": now,
            "updated_at": now
        }

        result = folders_collection.insert_one(folder_doc)

        # Update parent's foldersids if parent exists
        if parent_id:
            folders_collection.update_one(
                {"_id": ObjectId(parent_id)},
                {
                    "$addToSet": {"foldersids": str(result.inserted_id)},
                    "$set": {"updated_at": now}
                }
            )

        # Prepare response
        folder_doc["id"] = str(result.inserted_id)
        logger.info(f"Created folder '{name}' with ID {folder_doc['id']}")

        return folder_doc

    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}")
        raise


def rename_folder(folder_id: str, new_name: str, user: dict) -> Dict[str, Any]:
    """
    Rename a folder.

    Args:
        folder_id: Folder ID
        new_name: New folder name
        user: User document

    Returns:
        Updated folder document
    """
    try:
        db = get_database()
        folders_collection = db[settings.FOLDERS_COLLECTION]

        # Verify access
        folder = get_folder_by_id(folder_id, user)
        if not folder:
            raise ValueError("Folder not found or access denied")

        # Check for duplicate name in same parent
        duplicate_query = {
            "name": new_name,
            "parentID": folder.get("parentID"),
            "company_id": folder.get("company_id"),
            "department_id": folder.get("department_id"),
            "_id": {"$ne": ObjectId(folder_id)}
        }
        if folders_collection.find_one(duplicate_query):
            raise ValueError(f"Folder '{new_name}' already exists in this location")

        # Update folder
        result = folders_collection.update_one(
            {"_id": ObjectId(folder_id)},
            {
                "$set": {
                    "name": new_name,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Failed to rename folder")

        folder["name"] = new_name
        logger.info(f"Renamed folder {folder_id} to '{new_name}'")

        return folder

    except Exception as e:
        logger.error(f"Error renaming folder: {str(e)}")
        raise


def move_folder(folder_id: str, new_parent_id: Optional[str], user: dict) -> Dict[str, Any]:
    """
    Move folder to a new parent.

    Args:
        folder_id: Folder ID to move
        new_parent_id: New parent folder ID (None for root)
        user: User document

    Returns:
        Updated folder document
    """
    try:
        db = get_database()
        folders_collection = db[settings.FOLDERS_COLLECTION]

        # Verify access to folder
        folder = get_folder_by_id(folder_id, user)
        if not folder:
            raise ValueError("Folder not found or access denied")

        # Verify access to new parent
        if new_parent_id:
            new_parent = get_folder_by_id(new_parent_id, user)
            if not new_parent:
                raise ValueError("New parent folder not found or access denied")

            # Prevent moving folder into itself or its descendants
            if new_parent_id == folder_id:
                raise ValueError("Cannot move folder into itself")

        old_parent_id = folder.get("parentID")

        # Update folder's parent
        folders_collection.update_one(
            {"_id": ObjectId(folder_id)},
            {
                "$set": {
                    "parentID": new_parent_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Remove from old parent's foldersids
        if old_parent_id:
            folders_collection.update_one(
                {"_id": ObjectId(old_parent_id)},
                {"$pull": {"foldersids": folder_id}}
            )

        # Add to new parent's foldersids
        if new_parent_id:
            folders_collection.update_one(
                {"_id": ObjectId(new_parent_id)},
                {"$addToSet": {"foldersids": folder_id}}
            )

        folder["parentID"] = new_parent_id
        logger.info(f"Moved folder {folder_id} to parent {new_parent_id}")

        return folder

    except Exception as e:
        logger.error(f"Error moving folder: {str(e)}")
        raise


def delete_folder(folder_id: str, user: dict) -> bool:
    """
    Delete a folder and all its contents recursively.

    Args:
        folder_id: Folder ID
        user: User document

    Returns:
        True if successful
    """
    try:
        db = get_database()
        folders_collection = db[settings.FOLDERS_COLLECTION]
        files_collection = db[settings.FILES_COLLECTION]

        # Verify access
        folder = get_folder_by_id(folder_id, user)
        if not folder:
            raise ValueError("Folder not found or access denied")

        # Delete all files in this folder
        files_collection.delete_many({"folder_id": folder_id})

        # Recursively delete subfolders
        subfolders = list(folders_collection.find({"parentID": folder_id}))
        for subfolder in subfolders:
            delete_folder(str(subfolder["_id"]), user)

        # Remove from parent's foldersids
        parent_id = folder.get("parentID")
        if parent_id:
            folders_collection.update_one(
                {"_id": ObjectId(parent_id)},
                {"$pull": {"foldersids": folder_id}}
            )

        # Delete the folder itself
        result = folders_collection.delete_one({"_id": ObjectId(folder_id)})

        logger.info(f"Deleted folder {folder_id}")
        return result.deleted_count > 0

    except Exception as e:
        logger.error(f"Error deleting folder: {str(e)}")
        raise


def get_folder_path(folder_id: str, user: dict) -> List[Dict[str, Any]]:
    """
    Get breadcrumb path from root to folder.

    Args:
        folder_id: Target folder ID
        user: User document

    Returns:
        List of folders from root to target (for breadcrumbs)
    """
    try:
        db = get_database()
        folders_collection = db[settings.FOLDERS_COLLECTION]

        path = []
        current_id = folder_id

        while current_id:
            folder = get_folder_by_id(current_id, user)
            if not folder:
                break

            path.insert(0, {
                "id": folder["id"],
                "name": folder["name"]
            })

            current_id = folder.get("parentID")

        return path

    except Exception as e:
        logger.error(f"Error getting folder path: {str(e)}")
        raise


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def list_files_in_folder(folder_id: Optional[str], user: dict) -> List[Dict[str, Any]]:
    """
    List files in a specific folder.

    Args:
        folder_id: Folder ID (None for root files)
        user: User document

    Returns:
        List of file documents
    """
    try:
        db = get_database()
        files_collection = db[settings.FILES_COLLECTION]

        # Build access filter
        access_filter = build_access_filter(user)

        # Add folder filter
        query = {**access_filter}
        if folder_id is None:
            query["$or"] = [
                {"folder_id": None},
                {"folder_id": {"$exists": False}}
            ]
        else:
            query["folder_id"] = folder_id

        # Execute query
        files = list(files_collection.find(query).sort("filename", 1))

        # Convert ObjectId to string
        for file in files:
            if "_id" in file:
                file["id"] = str(file["_id"])
                del file["_id"]

        logger.info(f"Retrieved {len(files)} files for folder {folder_id}")
        return files

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise


def get_file_by_id(file_id: str, user: dict) -> Optional[Dict[str, Any]]:
    """
    Get single file by ID with access control.

    Args:
        file_id: File ID
        user: User document

    Returns:
        File document or None
    """
    try:
        db = get_database()
        files_collection = db[settings.FILES_COLLECTION]

        # Build query with access control
        access_filter = build_access_filter(user)
        query = {"_id": ObjectId(file_id), **access_filter}

        file = files_collection.find_one(query)

        if file:
            file["id"] = str(file["_id"])
            del file["_id"]

        return file

    except Exception as e:
        logger.error(f"Error getting file {file_id}: {str(e)}")
        raise


def create_file_metadata(
    filename: str,
    file_key: str,
    file_type: str,
    file_size: int,
    user: dict,
    folder_id: Optional[str] = None,
    description: str = "",
    tags: List[str] = None
) -> Dict[str, Any]:
    """
    Create file metadata in database after upload.

    Args:
        filename: Original filename
        file_key: S3 storage key
        file_type: MIME type
        file_size: File size in bytes
        user: User document
        folder_id: Parent folder ID
        description: File description
        tags: File tags

    Returns:
        Created file document
    """
    try:
        db = get_database()
        files_collection = db[settings.FILES_COLLECTION]
        folders_collection = db[settings.FOLDERS_COLLECTION]

        # Get organizational context
        org_context = get_user_org_context(user)

        # If folder exists, verify access and get its org context
        if folder_id:
            folder = get_folder_by_id(folder_id, user)
            if not folder:
                raise ValueError("Folder not found or access denied")

            org_context = {
                "company_id": folder.get("company_id", ""),
                "department_id": folder.get("department_id", ""),
                "holding_id": folder.get("holding_id", "")
            }

        # Create file document
        now = datetime.utcnow()
        file_doc = {
            "filename": filename,
            "file_key": file_key,
            "file_type": file_type,
            "file_size": file_size,
            "folder_id": folder_id,
            "description": description or "",
            "tags": tags or [],
            "chat_id": None,
            **org_context,
            "created_at": now,
            "updated_at": now
        }

        result = files_collection.insert_one(file_doc)

        # Update folder's fileIds if folder exists
        if folder_id:
            folders_collection.update_one(
                {"_id": ObjectId(folder_id)},
                {
                    "$addToSet": {"fileIds": str(result.inserted_id)},
                    "$set": {"updated_at": now}
                }
            )

        # Prepare response
        file_doc["id"] = str(result.inserted_id)
        logger.info(f"Created file metadata for '{filename}' with ID {file_doc['id']}")

        return file_doc

    except Exception as e:
        logger.error(f"Error creating file metadata: {str(e)}")
        raise


def rename_file(file_id: str, new_filename: str, user: dict) -> Dict[str, Any]:
    """
    Rename a file.

    Args:
        file_id: File ID
        new_filename: New filename
        user: User document

    Returns:
        Updated file document
    """
    try:
        db = get_database()
        files_collection = db[settings.FILES_COLLECTION]

        # Verify access
        file = get_file_by_id(file_id, user)
        if not file:
            raise ValueError("File not found or access denied")

        # Update file
        result = files_collection.update_one(
            {"_id": ObjectId(file_id)},
            {
                "$set": {
                    "filename": new_filename,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Failed to rename file")

        file["filename"] = new_filename
        logger.info(f"Renamed file {file_id} to '{new_filename}'")

        return file

    except Exception as e:
        logger.error(f"Error renaming file: {str(e)}")
        raise


def move_file(file_id: str, new_folder_id: Optional[str], user: dict) -> Dict[str, Any]:
    """
    Move file to a new folder.

    Args:
        file_id: File ID
        new_folder_id: New folder ID (None for root)
        user: User document

    Returns:
        Updated file document
    """
    try:
        db = get_database()
        files_collection = db[settings.FILES_COLLECTION]
        folders_collection = db[settings.FOLDERS_COLLECTION]

        # Verify access to file
        file = get_file_by_id(file_id, user)
        if not file:
            raise ValueError("File not found or access denied")

        # Verify access to new folder
        if new_folder_id:
            new_folder = get_folder_by_id(new_folder_id, user)
            if not new_folder:
                raise ValueError("New folder not found or access denied")

        old_folder_id = file.get("folder_id")

        # Update file's folder
        files_collection.update_one(
            {"_id": ObjectId(file_id)},
            {
                "$set": {
                    "folder_id": new_folder_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Remove from old folder's fileIds
        if old_folder_id:
            folders_collection.update_one(
                {"_id": ObjectId(old_folder_id)},
                {"$pull": {"fileIds": file_id}}
            )

        # Add to new folder's fileIds
        if new_folder_id:
            folders_collection.update_one(
                {"_id": ObjectId(new_folder_id)},
                {"$addToSet": {"fileIds": file_id}}
            )

        file["folder_id"] = new_folder_id
        logger.info(f"Moved file {file_id} to folder {new_folder_id}")

        return file

    except Exception as e:
        logger.error(f"Error moving file: {str(e)}")
        raise


def delete_file(file_id: str, user: dict) -> bool:
    """
    Delete a file.

    Args:
        file_id: File ID
        user: User document

    Returns:
        True if successful
    """
    try:
        db = get_database()
        files_collection = db[settings.FILES_COLLECTION]
        folders_collection = db[settings.FOLDERS_COLLECTION]

        # Verify access
        file = get_file_by_id(file_id, user)
        if not file:
            raise ValueError("File not found or access denied")

        # Remove from folder's fileIds
        folder_id = file.get("folder_id")
        if folder_id:
            folders_collection.update_one(
                {"_id": ObjectId(folder_id)},
                {"$pull": {"fileIds": file_id}}
            )

        # Delete the file metadata
        result = files_collection.delete_one({"_id": ObjectId(file_id)})

        logger.info(f"Deleted file {file_id}")
        return result.deleted_count > 0

    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise


def get_storage_info(user: dict) -> Dict[str, Any]:
    """
    Get storage usage information for user.

    Args:
        user: User document

    Returns:
        Storage statistics
    """
    try:
        db = get_database()
        files_collection = db[settings.FILES_COLLECTION]

        # Build access filter
        access_filter = build_access_filter(user)

        # Get total file count and size
        pipeline = [
            {"$match": access_filter},
            {
                "$group": {
                    "_id": None,
                    "total_files": {"$sum": 1},
                    "total_size": {"$sum": "$file_size"}
                }
            }
        ]

        result = list(files_collection.aggregate(pipeline))

        if result:
            total_files = result[0].get("total_files", 0)
            total_size = result[0].get("total_size", 0)
        else:
            total_files = 0
            total_size = 0

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_formatted": format_file_size(total_size)
        }

    except Exception as e:
        logger.error(f"Error getting storage info: {str(e)}")
        raise
