import logging
from datetime import datetime
from typing import List, Optional
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from bson.errors import InvalidId

from ..settings import settings
from .models import HoldingInDB, HoldingResponse

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


def validate_object_id(holding_id: str) -> ObjectId:
    """
    Validate and convert string ID to MongoDB ObjectId.

    Args:
        holding_id (str): String representation of ObjectId

    Returns:
        ObjectId: Valid MongoDB ObjectId

    Raises:
        ValueError: If ID format is invalid
    """
    try:
        return ObjectId(holding_id)
    except (InvalidId, TypeError) as e:
        logger.error(f"Invalid ObjectId format: {holding_id}")
        raise ValueError(f"Invalid holding ID format: {holding_id}")


def create_holding(name: str, description: Optional[str] = None) -> HoldingResponse:
    """
    Create a new holding in MongoDB.

    Args:
        name (str): Holding name
        description (str, optional): Holding description

    Returns:
        HoldingResponse: Created holding data

    Raises:
        ValueError: For invalid input or duplicate holding name
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Creating new holding: {name}")

    # Input validation
    if not name or not name.strip():
        raise ValueError("Holding name is required and cannot be empty")

    # Prepare holding document
    current_time = datetime.utcnow()
    holding_doc = {
        "name": name.strip(),
        "description": description.strip() if description else None,
        "created_at": current_time,
        "updated_at": current_time,
        "is_deleted": False
    }

    client = None
    try:
        # Get database connection
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        holdings_collection = db[settings.HOLDINGS_COLLECTION]

        # Create unique index on name (case-insensitive)
        holdings_collection.create_index(
            [("name", 1)],
            unique=True,
            collation={"locale": "en", "strength": 2}
        )

        # Check if holding with same name already exists
        existing = holdings_collection.find_one(
            {"name": name.strip(), "is_deleted": False},
            collation={"locale": "en", "strength": 2}
        )
        if existing:
            raise ValueError(f"Holding with name '{name}' already exists")

        # Insert holding document
        result = holdings_collection.insert_one(holding_doc)

        logger.info(f"Successfully created holding: {name} with ID: {result.inserted_id}")

        # Create response model
        return HoldingResponse(
            id=str(result.inserted_id),
            name=holding_doc["name"],
            description=holding_doc["description"],
            created_at=current_time,
            updated_at=current_time
        )

    except DuplicateKeyError:
        error_msg = f"Holding with name '{name}' already exists"
        logger.error(error_msg)
        raise ValueError(error_msg)

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during holding creation: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def get_all_holdings() -> List[HoldingResponse]:
    """
    Get all active holdings from MongoDB.

    Returns:
        List[HoldingResponse]: List of all active holdings

    Raises:
        ConnectionFailure: If database connection fails
    """
    logger.info("Fetching all holdings")

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        holdings_collection = db[settings.HOLDINGS_COLLECTION]

        # Fetch all non-deleted holdings
        holdings_cursor = holdings_collection.find(
            {"is_deleted": False}
        ).sort("created_at", -1)

        holdings = []
        for doc in holdings_cursor:
            holdings.append(
                HoldingResponse(
                    id=str(doc["_id"]),
                    name=doc["name"],
                    description=doc.get("description"),
                    created_at=doc["created_at"],
                    updated_at=doc["updated_at"]
                )
            )

        logger.info(f"Retrieved {len(holdings)} holdings")
        return holdings

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error while fetching holdings: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def get_holding_by_id(holding_id: str) -> Optional[HoldingResponse]:
    """
    Get a specific holding by ID.

    Args:
        holding_id (str): Holding ObjectId as string

    Returns:
        HoldingResponse: Holding data if found, None otherwise

    Raises:
        ValueError: If holding ID format is invalid
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Fetching holding with ID: {holding_id}")

    # Validate ObjectId
    obj_id = validate_object_id(holding_id)

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        holdings_collection = db[settings.HOLDINGS_COLLECTION]

        # Find holding by ID
        doc = holdings_collection.find_one({
            "_id": obj_id,
            "is_deleted": False
        })

        if not doc:
            logger.warning(f"Holding not found with ID: {holding_id}")
            return None

        return HoldingResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            description=doc.get("description"),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"]
        )

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error while fetching holding: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def update_holding(holding_id: str, name: str, description: Optional[str] = None) -> HoldingResponse:
    """
    Update/rename a holding.

    Args:
        holding_id (str): Holding ObjectId as string
        name (str): New holding name
        description (str, optional): New description

    Returns:
        HoldingResponse: Updated holding data

    Raises:
        ValueError: If holding not found or name already exists
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Updating holding {holding_id} with new name: {name}")

    # Validate inputs
    if not name or not name.strip():
        raise ValueError("Holding name is required and cannot be empty")

    obj_id = validate_object_id(holding_id)

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        holdings_collection = db[settings.HOLDINGS_COLLECTION]

        # Check if holding exists
        existing = holdings_collection.find_one({
            "_id": obj_id,
            "is_deleted": False
        })

        if not existing:
            raise ValueError(f"Holding not found with ID: {holding_id}")

        # Check if new name is already taken by another holding
        name_conflict = holdings_collection.find_one(
            {
                "_id": {"$ne": obj_id},
                "name": name.strip(),
                "is_deleted": False
            },
            collation={"locale": "en", "strength": 2}
        )

        if name_conflict:
            raise ValueError(f"Holding with name '{name}' already exists")

        # Update holding
        update_data = {
            "name": name.strip(),
            "description": description.strip() if description else None,
            "updated_at": datetime.utcnow()
        }

        holdings_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )

        logger.info(f"Successfully updated holding: {holding_id}")

        # Return updated holding
        return get_holding_by_id(holding_id)

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during holding update: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")


def delete_holding(holding_id: str) -> bool:
    """
    Delete a holding permanently from the database.

    Args:
        holding_id (str): Holding ObjectId as string

    Returns:
        bool: True if deleted successfully

    Raises:
        ValueError: If holding not found
        ConnectionFailure: If database connection fails
    """
    logger.info(f"Deleting holding with ID: {holding_id}")

    # Validate ObjectId
    obj_id = validate_object_id(holding_id)

    client = None
    try:
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        holdings_collection = db[settings.HOLDINGS_COLLECTION]

        # Check if holding exists
        existing = holdings_collection.find_one({
            "_id": obj_id,
            "is_deleted": False
        })

        if not existing:
            raise ValueError(f"Holding not found with ID: {holding_id}")

        # Permanently delete the holding
        result = holdings_collection.delete_one({"_id": obj_id})

        if result.deleted_count > 0:
            logger.info(f"Successfully deleted holding: {holding_id}")
            return True
        else:
            logger.warning(f"Holding could not be deleted: {holding_id}")
            return False

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during holding deletion: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        if client:
            client.close()
            logger.debug("Database connection closed")
