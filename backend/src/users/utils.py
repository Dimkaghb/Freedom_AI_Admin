
import logging
import secrets
import string
import re
from datetime import datetime
from typing import Dict, Any
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
import bcrypt
from email_validator import validate_email, EmailNotValidError

from ..settings import settings
from .models import UserInDB, UserCreateResponse, CreateUserLink

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_secure_password(length: int = 12) -> str:
    """
    Generate a secure random password with mixed case, numbers, and special characters.
    
    Args:
        length (int): Password length (minimum 12 characters)
        
    Returns:
        str: Secure random password
        
    Raises:
        ValueError: If length is less than 12
    """
    if length < 12:
        raise ValueError("Password length must be at least 12 characters")
    
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]
    
    # Fill the rest with random characters from all sets
    all_chars = lowercase + uppercase + digits + special_chars
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Shuffle the password list
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def validate_email_format(email: str) -> str:
    """
    Validate email format using email-validator.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        str: Normalized email address
        
    Raises:
        ValueError: If email format is invalid
    """
    try:
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email format: {str(e)}")


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


def add_user_by_admin(email: str, role: str, full_name: str = None) -> UserCreateResponse:
    """
    Create a new user by admin with secure password generation and database storage.
    
    This function handles comprehensive user creation including:
    - Email validation and normalization
    - Role validation
    - Secure password generation (12+ characters with mixed case, numbers, special chars)
    - Password hashing using bcrypt
    - MongoDB document insertion with proper error handling
    - Duplicate email detection
    
    Args:
        email (str): User's email address (will be validated and normalized)
        role (str): User role, must be either 'admin' or 'user'
        full_name (str, optional): User's full name. Defaults to None.
        
    Returns:
        UserCreateResponse: Complete user document with temporary password for one-time display
        
    Raises:
        ValueError: For invalid input parameters (email format, role, etc.)
        DuplicateKeyError: If user with email already exists
        ConnectionFailure: If database connection fails
        Exception: For other database operation errors
        
    Example:
        >>> user = add_user_by_admin("admin@example.com", "admin", "John Doe")
        >>> print(f"User created with temporary password: {user.temporary_password}")
        
    Security Notes:
        - Passwords are never stored in plain text
        - Uses bcrypt for secure password hashing
        - Generates cryptographically secure random passwords
        - Logs important operations for audit trail
        
    Future Compatibility:
        - Designed to be easily extendable for additional user fields
        - Uses Pydantic models for type safety and validation
        - Follows repository pattern for database operations
    """
    logger.info(f"Starting user creation process for email: {email}")
    
    # Input validation
    if not email or not email.strip():
        raise ValueError("Email is required and cannot be empty")
    
    if not role or role not in ["admin", "user"]:
        raise ValueError("Role must be either 'admin' or 'user'")
    
    # Validate and normalize email
    try:
        normalized_email = validate_email_format(email.strip().lower())
    except ValueError as e:
        logger.error(f"Email validation failed for {email}: {str(e)}")
        raise
    
    # Generate secure password
    try:
        temporary_password = generate_secure_password()
        hashed_password = hash_password(temporary_password)
        logger.info(f"Generated secure password for user: {normalized_email}")
    except Exception as e:
        logger.error(f"Password generation failed: {str(e)}")
        raise ValueError(f"Failed to generate secure password: {str(e)}")
    
    # Prepare user document
    current_time = datetime.utcnow()
    user_doc = {
        "email": normalized_email,
        "role": role,
        "full_name": full_name,
        "is_active": True,
        "hashed_password": hashed_password,
        "created_at": current_time,
        "updated_at": current_time
    }
    
    # Database operations
    client = None
    try:
        # Get database connection
        client = get_mongodb_connection()
        db = client[settings.DATABASE_NAME]
        users_collection = db[settings.USERS_COLLECTION]
        
        # Create unique index on email if it doesn't exist
        users_collection.create_index("email", unique=True)
        
        # Insert user document
        result = users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        
        logger.info(f"Successfully created user in database: {normalized_email} with ID: {result.inserted_id}")
        
        # Create response model
        user_response = UserCreateResponse(
            id=str(result.inserted_id),
            email=normalized_email,
            role=role,
            full_name=full_name,
            is_active=True,
            created_at=current_time,
            updated_at=current_time,
            temporary_password=temporary_password
        )
        
        logger.info(f"User creation completed successfully for: {normalized_email}")
        return user_response
        
    except DuplicateKeyError:
        error_msg = f"User with email {normalized_email} already exists"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        raise ConnectionFailure(error_msg)
        
    except Exception as e:
        error_msg = f"Unexpected error during user creation: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
        
    finally:
        # Clean up database connection
        if client:
            client.close()
            logger.debug("Database connection closed")


# Legacy function for backward compatibility
def add_user(user_email: str, user_role: str):
    """
    Legacy function for backward compatibility.
    
    Deprecated: Use add_user_by_admin instead for enhanced security and features.
    """
    logger.warning("add_user function is deprecated. Use add_user_by_admin instead.")
    try:
        result = add_user_by_admin(user_email, user_role)
        return result
    except Exception as e:
        raise ValueError(f"Error adding user to database: {e}")
    

def create_registration_link(CreateUserLink: CreateUserLink) -> str:
    user_link_id = secrets.token_urlsafe(16)
    # Here you would typically store the link in the database with an expiration time
    logger.info(f"Created registration link with ID: {user_link_id} for company ID: {CreateUserLink.company_id}")
    db = get_mongodb_connection()[settings.DATABASE_NAME]
    links_collection = db[settings.USER_LINKS_COLLECTION]
    link_doc = {
        "link_id": user_link_id,
        "company_id": CreateUserLink.company_id,
        "department_id": CreateUserLink.department_id,
        "role": CreateUserLink.role,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + settings.USER_LINK_EXPIRATION_DELTA
    }
    links_collection.insert_one(link_doc)
    registration_url = f"{settings.FRONTEND_URL}/register?link_id={user_link_id}"
    return registration_url

def verify_registration_link(link_id: str) -> Dict[str, Any]:
    db = get_mongodb_connection()[settings.DATABASE_NAME]
    links_collection = db[settings.USER_LINKS_COLLECTION]
    link_doc = links_collection.find_one({"link_id": link_id})
    if not link_doc:
        raise ValueError("Invalid registration link")
    if link_doc["expires_at"] < datetime.utcnow():
        raise ValueError("Registration link has expired")
    logger.info(f"Verified registration link with ID: {link_id}")
    return {
        "company_id": link_doc["company_id"],
        "department_id": link_doc.get("department_id"),
        "role": link_doc["role"]
    }

