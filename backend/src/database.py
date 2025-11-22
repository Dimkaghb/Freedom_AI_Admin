"""
MongoDB Connection Manager with Connection Pooling.

This module provides a singleton MongoDB client with connection pooling
for optimal performance. The connection is reused across all database
operations, eliminating the overhead of creating new connections for
each query.

Performance benefits:
- Single connection initialization on startup
- Connection pooling (default: 100 max connections)
- Automatic connection health monitoring
- Graceful shutdown handling
"""

import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo.database import Database

from .settings import settings

# Configure logging
logger = logging.getLogger(__name__)


class MongoDBManager:
    """
    Singleton MongoDB connection manager with connection pooling.

    This class ensures only one MongoDB client instance exists throughout
    the application lifecycle, providing efficient connection reuse.

    Usage:
        >>> db_manager = MongoDBManager()
        >>> db = db_manager.get_database()
        >>> users = db[settings.USERS_COLLECTION].find({"role": "admin"})
    """

    _instance: Optional['MongoDBManager'] = None
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None

    def __new__(cls) -> 'MongoDBManager':
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the MongoDB manager (only once)."""
        # Only initialize once
        if self._client is None:
            self._connect()

    def _connect(self) -> None:
        """
        Establish MongoDB connection with connection pooling.

        Connection pool configuration:
        - maxPoolSize: 100 (maximum concurrent connections)
        - minPoolSize: 10 (minimum connections to maintain)
        - maxIdleTimeMS: 300000 (5 minutes before idle connection cleanup)
        - waitQueueTimeoutMS: 10000 (10 seconds max wait for connection)

        Raises:
            ConnectionFailure: If unable to connect to MongoDB
        """
        try:
            logger.info("🔌 Initializing MongoDB connection pool...")
            logger.info(f"   Database: {settings.DATABASE_NAME}")
            logger.info(f"   URL: {settings.MONGODB_URL}")

            self._client = MongoClient(
                settings.MONGODB_URL,
                # Connection timeouts
                connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT,
                serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT,

                # Connection pool settings
                maxPoolSize=100,  # Maximum number of connections
                minPoolSize=10,   # Minimum number of connections to maintain
                maxIdleTimeMS=300000,  # 5 minutes before idle connection cleanup
                waitQueueTimeoutMS=10000,  # 10 seconds max wait for connection from pool

                # Reliability settings
                retryWrites=True,
                retryReads=True,
            )

            # Test the connection
            self._client.admin.command('ping')

            # Get database reference
            self._database = self._client[settings.DATABASE_NAME]

            logger.info("✅ MongoDB connection pool initialized successfully")
            logger.info(f"   Max pool size: 100 connections")
            logger.info(f"   Min pool size: 10 connections")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
            raise ConnectionFailure(f"Database connection failed: {str(e)}")

    def get_client(self) -> MongoClient:
        """
        Get the MongoDB client instance.

        Returns:
            MongoClient: MongoDB client with connection pooling

        Raises:
            ConnectionFailure: If connection is not established
        """
        if self._client is None:
            logger.warning("MongoDB client not initialized, attempting to connect...")
            self._connect()

        return self._client

    def get_database(self) -> Database:
        """
        Get the database instance.

        Returns:
            Database: MongoDB database instance

        Raises:
            ConnectionFailure: If connection is not established
        """
        if self._database is None:
            logger.warning("MongoDB database not initialized, attempting to connect...")
            self._connect()

        return self._database

    def close(self) -> None:
        """
        Close MongoDB connection and cleanup resources.

        This should be called during application shutdown.
        """
        if self._client is not None:
            logger.info("🔌 Closing MongoDB connection pool...")
            self._client.close()
            self._client = None
            self._database = None
            logger.info("✅ MongoDB connection pool closed")

    def ping(self) -> bool:
        """
        Test if MongoDB connection is alive.

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            if self._client is None:
                return False

            self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB ping failed: {str(e)}")
            return False

    def get_connection_info(self) -> dict:
        """
        Get current connection pool statistics.

        Returns:
            dict: Connection pool information
        """
        if self._client is None:
            return {
                "status": "disconnected",
                "database": None,
                "pool_size": 0
            }

        try:
            # Get server info
            server_info = self._client.server_info()

            return {
                "status": "connected",
                "database": settings.DATABASE_NAME,
                "mongodb_version": server_info.get("version"),
                "max_pool_size": 100,
                "min_pool_size": 10,
                "healthy": self.ping()
            }
        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }


# Global singleton instance
_db_manager: Optional[MongoDBManager] = None


def get_db_manager() -> MongoDBManager:
    """
    Get the global MongoDB manager instance.

    This function ensures thread-safe access to the singleton instance.

    Returns:
        MongoDBManager: Global MongoDB connection manager
    """
    global _db_manager

    if _db_manager is None:
        _db_manager = MongoDBManager()

    return _db_manager


def get_database() -> Database:
    """
    Get the MongoDB database instance (convenience function).

    This is the recommended way to access the database in your code.

    Returns:
        Database: MongoDB database instance

    Example:
        >>> from src.database import get_database
        >>> db = get_database()
        >>> users = db[settings.USERS_COLLECTION].find({"role": "admin"})
    """
    return get_db_manager().get_database()


def close_database_connection() -> None:
    """
    Close the global database connection.

    This should be called during application shutdown.
    """
    global _db_manager

    if _db_manager is not None:
        _db_manager.close()
        _db_manager = None
