import logging
from datetime import datetime
from typing import List, Optional
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from bson.errors import InvalidId

from ..settings import settings
from .models import CompanyInDB, CompanyResponse

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


def validate_holding_exists(client: MongoClient, holding_id: str) -> bool:
    """
    Validate that a holding exists in the database.

    Args:
        client (MongoClient): MongoDB client instance
        holding_id (str): Holding ObjectId as string

    Returns:
        bool: True if holding exists

    Raises:
        ValueError: If holding doesn't exist
    """
    holding_obj_id = validate_object_id(holding_id, "holding_id")

    db = client[settings.DATABASE_NAME]
    holdings_collection = db[settings.HOLDINGS_COLLECTION]

    holding = holdings_collection.find_one({
        "_id": holding_obj_id,
        "is_deleted": False
    })

    if not holding:
        raise ValueError(f"Holding not found with ID: {holding_id}")

    return True


def create_company(
    name: str,
    holding_id: str,
    description: Optional[str] = None,
    admin_id: Optional[str] = None
) -> CompanyResponse:
    """
    Create a new company in MongoDB.

    Args:
        name (str): Company name
        holding_id (str): Parent holding ObjectId as string
        description (str, optional): Company description
        admin_id (str, optional): Admin user ObjectId as string

    Returns:
        CompanyResponse: Created company data

    Raises:
        ValueError: For invalid input or duplicate company name
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Creating new company: {name}")

    # Input validation
    if not name or not name.strip():
        raise ValueError("Company name is required and cannot be empty")

    client = None
    try:
        # Get database connection
        client = get_mongodb_connection()

        # Validate that holding exists
        validate_holding_exists(client, holding_id)

        # Validate admin_id if provided
        if admin_id:
            validate_object_id(admin_id, "admin_id")

        db = client[settings.DATABASE_NAME]
        companies_collection = db[settings.COMPANIES_COLLECTION]

        # Create unique index on name within each holding (case-insensitive)
        companies_collection.create_index(
            [("name", 1), ("holding_id", 1)],
            unique=True,
            collation={"locale": "en", "strength": 2}
        )

        # Check if company with same name already exists in this holding
        existing = companies_collection.find_one(
            {
                "name": name.strip(),
                "holding_id": holding_id,
                "is_deleted": False
            },
            collation={"locale": "en", "strength": 2}
        )
        if existing:
            raise ValueError(f"Company with name '{name}' already exists in this holding")

        # Prepare company document
        current_time = datetime.utcnow()
        company_doc = {
            "name": name.strip(),
            "description": description.strip() if description else None,
            "holding_id": holding_id,
            "admin_id": admin_id,
            "created_at": current_time,
            "updated_at": current_time,
            "is_deleted": False
        }

        # Insert company document
        result = companies_collection.insert_one(company_doc)

        logger.info(f"Successfully created company: {name} with ID: {result.inserted_id}")

        # Create response model
        return CompanyResponse(
            id=str(result.inserted_id),
            name=company_doc["name"],
            description=company_doc["description"],
            holding_id=holding_id,
            admin_id=admin_id,
            created_at=current_time,
            updated_at=current_time
        )

    except DuplicateKeyError:
        error_msg = f"Company with name '{name}' already exists in this holding"
        logger.error(error_msg)
        raise ValueError(error_msg)

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during company creation: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def get_all_companies(holding_id: Optional[str] = None) -> List[CompanyResponse]:
    """
    Get all active companies from MongoDB, optionally filtered by holding.

    Args:
        holding_id (str, optional): Filter by holding ID

    Returns:
        List[CompanyResponse]: List of all active companies

    Raises:
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Fetching all companies{f' for holding {holding_id}' if holding_id else ''}")

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        companies_collection = db[settings.COMPANIES_COLLECTION]

        # Build query
        query = {"is_deleted": False}
        if holding_id:
            # Validate holding_id if provided
            validate_object_id(holding_id, "holding_id")
            query["holding_id"] = holding_id

        # Fetch all non-deleted companies
        companies_cursor = companies_collection.find(query).sort("created_at", -1)

        companies = []
        for doc in companies_cursor:
            companies.append(
                CompanyResponse(
                    id=str(doc["_id"]),
                    name=doc["name"],
                    description=doc.get("description"),
                    holding_id=doc["holding_id"],
                    admin_id=doc.get("admin_id"),
                    created_at=doc["created_at"],
                    updated_at=doc["updated_at"]
                )
            )

        logger.info(f"Retrieved {len(companies)} companies")
        return companies

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error while fetching companies: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def get_company_by_id(company_id: str) -> Optional[CompanyResponse]:
    """
    Get a specific company by ID.

    Args:
        company_id (str): Company ObjectId as string

    Returns:
        CompanyResponse: Company data if found, None otherwise

    Raises:
        ValueError: If company ID format is invalid
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Fetching company with ID: {company_id}")

    # Validate ObjectId
    obj_id = validate_object_id(company_id, "company_id")

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        companies_collection = db[settings.COMPANIES_COLLECTION]

        # Find company by ID
        doc = companies_collection.find_one({
            "_id": obj_id,
            "is_deleted": False
        })

        if not doc:
            logger.warning(f"Company not found with ID: {company_id}")
            return None

        return CompanyResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            description=doc.get("description"),
            holding_id=doc["holding_id"],
            admin_id=doc.get("admin_id"),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"]
        )

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error while fetching company: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def update_company(
    company_id: str,
    name: str,
    description: Optional[str] = None,
    admin_id: Optional[str] = None
) -> CompanyResponse:
    """
    Update a company.

    Args:
        company_id (str): Company ObjectId as string
        name (str): New company name
        description (str, optional): New description
        admin_id (str, optional): New admin user ObjectId

    Returns:
        CompanyResponse: Updated company data

    Raises:
        ValueError: If company not found or name already exists
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Updating company {company_id} with new name: {name}")

    # Validate inputs
    if not name or not name.strip():
        raise ValueError("Company name is required and cannot be empty")

    obj_id = validate_object_id(company_id, "company_id")

    # Validate admin_id if provided
    if admin_id:
        validate_object_id(admin_id, "admin_id")

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        companies_collection = db[settings.COMPANIES_COLLECTION]

        # Check if company exists
        existing = companies_collection.find_one({
            "_id": obj_id,
            "is_deleted": False
        })

        if not existing:
            raise ValueError(f"Company not found with ID: {company_id}")

        # Check if new name is already taken by another company in the same holding
        name_conflict = companies_collection.find_one(
            {
                "_id": {"$ne": obj_id},
                "name": name.strip(),
                "holding_id": existing["holding_id"],
                "is_deleted": False
            },
            collation={"locale": "en", "strength": 2}
        )

        if name_conflict:
            raise ValueError(f"Company with name '{name}' already exists in this holding")

        # Update company
        update_data = {
            "name": name.strip(),
            "description": description.strip() if description else None,
            "admin_id": admin_id,
            "updated_at": datetime.utcnow()
        }

        companies_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )

        logger.info(f"Successfully updated company: {company_id}")

        # Return updated company
        return get_company_by_id(company_id)

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during company update: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def delete_company(company_id: str) -> bool:
    """
    Delete a company permanently from the database.

    Args:
        company_id (str): Company ObjectId as string

    Returns:
        bool: True if deleted successfully

    Raises:
        ValueError: If company not found
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Deleting company with ID: {company_id}")

    # Validate ObjectId
    obj_id = validate_object_id(company_id, "company_id")

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        companies_collection = db[settings.COMPANIES_COLLECTION]

        # Check if company exists
        existing = companies_collection.find_one({
            "_id": obj_id,
            "is_deleted": False
        })

        if not existing:
            raise ValueError(f"Company not found with ID: {company_id}")

        # Permanently delete the company
        result = companies_collection.delete_one({"_id": obj_id})

        if result.deleted_count > 0:
            logger.info(f"Successfully deleted company: {company_id}")
            return True
        else:
            logger.warning(f"Company could not be deleted: {company_id}")
            return False

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during company deletion: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")
