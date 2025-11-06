import logging
from datetime import datetime
from typing import Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from ..settings import settings

logger = logging.getLogger(__name__)


def get_mongodb_connection():
    """
    Establish connection to MongoDB

    Returns:
        MongoClient: Connected MongoDB client

    Raises:
        ConnectionFailure: If connection fails
    """
    try:
        client = MongoClient(
            settings.MONGODB_URL,
            connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT,
            serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT
        )
        # Test the connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise ConnectionFailure(f"Database connection failed: {str(e)}")


def list_folders_for_user(user: dict) -> List[Dict[str, Any]]:
    """
    List folders based on user role and permissions.

    Role-based access control:
    - superadmin: sees all folders across all holdings, companies, and departments
    - admin: sees folders for their specific company and all its departments
    - director: sees folders for their specific department only
    - user: sees folders for their specific department (read-only access)

    Args:
        user (dict): User document from MongoDB containing role, holding_id, company_id, department_id

    Returns:
        List[Dict[str, Any]]: List of folder documents matching user's permissions

    Raises:
        ConnectionFailure: If database connection fails
        ValueError: If user data is invalid
    """
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        folders_collection = db[settings.FOLDERS_COLLECTION]

        user_id = str(user.get("_id"))
        role = user.get("role", "user")
        holding_id = user.get("holding_id")
        company_id = user.get("company_id")
        department_id = user.get("department_id")

        logger.info(f"Listing folders for user {user_id} with role {role}")

        # Query based on role
        if role == "superadmin":
            # Superadmin sees all folders
            query = {}
            logger.info("Superadmin access: retrieving all folders")

        elif role == "admin":
            # Admin sees folders for their company (company_id matches their company_id OR admin_id matches their user_id)
            if not company_id:
                logger.warning(f"Admin user {user_id} has no company_id")
                return []

            query = {
                "$or": [
                    {"company_id": company_id},
                    {"admin_id": user_id}
                ]
            }
            logger.info(f"Admin access: retrieving folders for company {company_id}")

        elif role == "director":
            # Director sees folders for their department (department_id matches OR user_id matches OR admin_id matches)
            if not department_id:
                logger.warning(f"Director user {user_id} has no department_id")
                return []

            query = {
                "$or": [
                    {"department_id": department_id},
                    {"admin_id": user_id}
                ]
            }
            logger.info(f"Director access: retrieving folders for department {department_id}")

        elif role == "user":
            # Regular user sees folders for their department only
            if not department_id:
                logger.warning(f"User {user_id} has no department_id")
                return []

            query = {"department_id": department_id}
            logger.info(f"User access: retrieving folders for department {department_id}")

        else:
            logger.warning(f"Unknown role {role} for user {user_id}")
            return []

        # Execute query and convert to list
        folders = list(folders_collection.find(query).sort("created_at", -1))

        # Convert ObjectId to string for JSON serialization
        for folder in folders:
            if "_id" in folder:
                folder["id"] = str(folder["_id"])
                del folder["_id"]

        logger.info(f"Retrieved {len(folders)} folders for user {user_id}")
        return folders

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Database connection error while listing folders: {str(e)}")
        raise ConnectionFailure(f"Failed to retrieve folders: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error while listing folders for user {user_id}: {str(e)}")
        raise Exception(f"Failed to retrieve folders: {str(e)}")