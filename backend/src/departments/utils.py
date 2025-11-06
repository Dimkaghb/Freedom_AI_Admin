import logging
from datetime import datetime
from typing import List, Optional
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from bson.errors import InvalidId

from ..settings import settings
from .models import DepartmentInDB, DepartmentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_mongodb_connection():
    """
    Get MongoDB connection using settings configuration.

    Returns:
        MongoClient: MongoDB client instance

    Raises:
        ConnectionFailure: If unable to connect to MongoDB
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


def validate_object_id(object_id: str, field_name: str = "ID") -> ObjectId:
    """
    Validate and convert string ID to MongoDB ObjectId.

    Args:
        object_id (str): String representation of ObjectId
        field_name (str): Name of the field for error messages

    Returns:
        ObjectId: Valid MongoDB ObjectId

    Raises:
        ValueError: If ID format is invalid
    """
    try:
        return ObjectId(object_id)
    except (InvalidId, TypeError) as e:
        logger.error(f"Invalid ObjectId format for {field_name}: {object_id}")
        raise ValueError(f"Invalid {field_name} format: {object_id}")


def validate_company_exists(client: MongoClient, company_id: str) -> bool:
    """
    Validate that a company exists in the database.

    Args:
        client (MongoClient): MongoDB client instance
        company_id (str): Company ObjectId as string

    Returns:
        bool: True if company exists

    Raises:
        ValueError: If company doesn't exist
    """
    company_obj_id = validate_object_id(company_id, "company_id")

    db = client[settings.DATABASE_NAME]
    companies_collection = db[settings.COMPANIES_COLLECTION]

    company = companies_collection.find_one({
        "_id": company_obj_id,
        "is_deleted": False
    })

    if not company:
        raise ValueError(f"Company not found with ID: {company_id}")

    return True


def create_department(
    name: str,
    company_id: str,
    description: Optional[str] = None,
    manager_id: Optional[str] = None
) -> DepartmentResponse:
    """
    Create a new department in MongoDB.

    Args:
        name (str): Department name
        company_id (str): Parent company ObjectId as string
        description (str, optional): Department description
        manager_id (str, optional): Manager user ObjectId as string

    Returns:
        DepartmentResponse: Created department data

    Raises:
        ValueError: For invalid input or duplicate department name
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Creating new department: {name}")

    # Input validation
    if not name or not name.strip():
        raise ValueError("Department name is required and cannot be empty")

    client = None
    try:
        # Get database connection
        client = get_mongodb_connection()

        # Validate that company exists
        validate_company_exists(client, company_id)

        # Validate manager_id if provided
        if manager_id:
            validate_object_id(manager_id, "manager_id")

        db = client[settings.DATABASE_NAME]
        departments_collection = db[settings.DEPARTMENTS_COLLECTION]

        # Create unique index on name within each company (case-insensitive)
        departments_collection.create_index(
            [("name", 1), ("company_id", 1)],
            unique=True,
            collation={"locale": "en", "strength": 2}
        )

        # Check if department with same name already exists in this company
        existing = departments_collection.find_one(
            {
                "name": name.strip(),
                "company_id": company_id,
                "is_deleted": False
            },
            collation={"locale": "en", "strength": 2}
        )
        if existing:
            raise ValueError(f"Department with name '{name}' already exists in this company")

        # Prepare department document
        current_time = datetime.utcnow()
        department_doc = {
            "name": name.strip(),
            "description": description.strip() if description else None,
            "company_id": company_id,
            "manager_id": manager_id,
            "created_at": current_time,
            "updated_at": current_time,
            "is_deleted": False
        }

        # Insert department document
        result = departments_collection.insert_one(department_doc)

        logger.info(f"Successfully created department: {name} with ID: {result.inserted_id}")

        # Create response model
        return DepartmentResponse(
            id=str(result.inserted_id),
            name=department_doc["name"],
            description=department_doc["description"],
            company_id=company_id,
            manager_id=manager_id,
            created_at=current_time,
            updated_at=current_time
        )

    except DuplicateKeyError:
        error_msg = f"Department with name '{name}' already exists in this company"
        logger.error(error_msg)
        raise ValueError(error_msg)

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during department creation: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def get_all_departments(company_id: Optional[str] = None) -> List[DepartmentResponse]:
    """
    Get all active departments from MongoDB, optionally filtered by company.

    Args:
        company_id (str, optional): Filter by company ID

    Returns:
        List[DepartmentResponse]: List of all active departments

    Raises:
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Fetching all departments{f' for company {company_id}' if company_id else ''}")

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        departments_collection = db[settings.DEPARTMENTS_COLLECTION]

        # Build query
        query = {"is_deleted": False}
        if company_id:
            # Validate company_id if provided
            validate_object_id(company_id, "company_id")
            query["company_id"] = company_id

        # Fetch all non-deleted departments
        departments_cursor = departments_collection.find(query).sort("created_at", -1)

        departments = []
        for doc in departments_cursor:
            departments.append(
                DepartmentResponse(
                    id=str(doc["_id"]),
                    name=doc["name"],
                    description=doc.get("description"),
                    company_id=doc["company_id"],
                    manager_id=doc.get("manager_id"),
                    created_at=doc["created_at"],
                    updated_at=doc["updated_at"]
                )
            )

        logger.info(f"Retrieved {len(departments)} departments")
        return departments

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error while fetching departments: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def get_department_by_id(department_id: str) -> Optional[DepartmentResponse]:
    """
    Get a specific department by ID.

    Args:
        department_id (str): Department ObjectId as string

    Returns:
        DepartmentResponse: Department data if found, None otherwise

    Raises:
        ValueError: If department ID format is invalid
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Fetching department with ID: {department_id}")

    # Validate ObjectId
    obj_id = validate_object_id(department_id, "department_id")

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        departments_collection = db[settings.DEPARTMENTS_COLLECTION]

        # Find department by ID
        doc = departments_collection.find_one({
            "_id": obj_id,
            "is_deleted": False
        })

        if not doc:
            logger.warning(f"Department not found with ID: {department_id}")
            return None

        return DepartmentResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            description=doc.get("description"),
            company_id=doc["company_id"],
            manager_id=doc.get("manager_id"),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"]
        )

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error while fetching department: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def update_department(
    department_id: str,
    name: str,
    description: Optional[str] = None,
    manager_id: Optional[str] = None
) -> DepartmentResponse:
    """
    Update a department.

    Args:
        department_id (str): Department ObjectId as string
        name (str): New department name
        description (str, optional): New description
        manager_id (str, optional): New manager user ObjectId

    Returns:
        DepartmentResponse: Updated department data

    Raises:
        ValueError: If department not found or name already exists
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Updating department {department_id} with new name: {name}")

    # Validate inputs
    if not name or not name.strip():
        raise ValueError("Department name is required and cannot be empty")

    obj_id = validate_object_id(department_id, "department_id")

    # Validate manager_id if provided
    if manager_id:
        validate_object_id(manager_id, "manager_id")

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        departments_collection = db[settings.DEPARTMENTS_COLLECTION]

        # Check if department exists
        existing = departments_collection.find_one({
            "_id": obj_id,
            "is_deleted": False
        })

        if not existing:
            raise ValueError(f"Department not found with ID: {department_id}")

        # Check if new name is already taken by another department in the same company
        name_conflict = departments_collection.find_one(
            {
                "_id": {"$ne": obj_id},
                "name": name.strip(),
                "company_id": existing["company_id"],
                "is_deleted": False
            },
            collation={"locale": "en", "strength": 2}
        )

        if name_conflict:
            raise ValueError(f"Department with name '{name}' already exists in this company")

        # Update department
        update_data = {
            "name": name.strip(),
            "description": description.strip() if description else None,
            "manager_id": manager_id,
            "updated_at": datetime.utcnow()
        }

        departments_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )

        logger.info(f"Successfully updated department: {department_id}")

        # Return updated department
        return get_department_by_id(department_id)

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during department update: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def delete_department(department_id: str) -> bool:
    """
    Delete a department permanently from the database.

    Args:
        department_id (str): Department ObjectId as string

    Returns:
        bool: True if deleted successfully

    Raises:
        ValueError: If department not found
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Deleting department with ID: {department_id}")

    # Validate ObjectId
    obj_id = validate_object_id(department_id, "department_id")

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        departments_collection = db[settings.DEPARTMENTS_COLLECTION]

        # Check if department exists
        existing = departments_collection.find_one({
            "_id": obj_id,
            "is_deleted": False
        })

        if not existing:
            raise ValueError(f"Department not found with ID: {department_id}")

        # Permanently delete the department
        result = departments_collection.delete_one({"_id": obj_id})

        if result.deleted_count > 0:
            logger.info(f"Successfully deleted department: {department_id}")
            return True
        else:
            logger.warning(f"Department could not be deleted: {department_id}")
            return False

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during department deletion: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")
