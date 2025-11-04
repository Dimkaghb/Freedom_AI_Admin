from datetime import datetime, timedelta
import uuid
import logging
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient

from ..settings import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_mongodb_client():
    """Get MongoDB client"""
    try:
        client = MongoClient(settings.MONGODB_URL)
        client.admin.command('ping')
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None

def get_user_by_email(email: str):
    """Get user by email from MongoDB"""
    client = None
    try:
        client = get_mongodb_client()
        if not client:
            logger.error("Could not connect to MongoDB")
            return None

        db = client[settings.DATABASE_NAME]
        users_collection = db[settings.USERS_COLLECTION]
        user = users_collection.find_one({"email": email})
        return user
    except Exception as e:
        logger.error(f"Error querying MongoDB: {e}")
        return None
    finally:
        if client:
            client.close()


async def authenticate_user(email: str, password: str):
    """Authenticate user by email and password"""
    user = get_user_by_email(email)
    if not user:
        return False

    if not verify_password(password, user["hashed_password"]):
        return False

    return user


async def update_user_profile(email: str, name: str):
    """Update user profile information"""
    client = None
    try:
        client = get_mongodb_client()
        if not client:
            logger.error("Could not connect to MongoDB")
            return None

        db = client[settings.DATABASE_NAME]
        users_collection = db[settings.USERS_COLLECTION]

        # Update in MongoDB
        result = users_collection.update_one(
            {"email": email},
            {"$set": {"name": name}}
        )

        if result.modified_count > 0:
            # Return updated user
            updated_user = users_collection.find_one({"email": email})
            logger.info(f"User {email} profile updated in MongoDB")
            return updated_user
    except Exception as e:
        logger.error(f"Error updating user profile in MongoDB: {e}")
        return None
    finally:
        if client:
            client.close()

    return None