
import logging
import secrets
import string
import re
from datetime import datetime
from typing import Dict, Any
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
import bcrypt
from email_validator import validate_email, EmailNotValidError

from ..settings import settings
from ..database import get_database
from .models import (
    UserInDB,
    UserCreateResponse,
    CreateUserLink,
    RegistrationLinkCreate,
    RegistrationLinkResponse,
    PendingUserCreate,
    PendingUserResponse,
    PendingUserInDB
)
from bson import ObjectId
from ..smtp.service import get_email_service

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


# MongoDB connection is now managed by the global database manager
# Use get_database() from ..database instead


def add_user_by_admin(email: str, role: str, firstName: str = None, lastName: str = None,
                      company_id: str = None, department_id: str = None, holding_id: str = None) -> UserCreateResponse:
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
        firstName (str, optional): User's first name. Defaults to None.
        lastName (str, optional): User's last name. Defaults to None.
        
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
        "firstName": firstName,
        "lastName": lastName,
        "is_active": True,
        "hashed_password": hashed_password,
        "company_id": company_id,
        "department_id": department_id,
        "holding_id": holding_id,
        "created_at": current_time,
        "updated_at": current_time
    }
    
    # Database operations
    try:
        # Get database connection
        db = get_database()
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
            firstName=firstName,
            lastName=lastName,
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
    

def create_registration_link(link_data: RegistrationLinkCreate) -> RegistrationLinkResponse:
    """
    Create a registration link for new users to register.

    The link expires after 24 hours and can be used to register users
    at company level (admin role) or department level (director/user roles).

    Args:
        link_data: Registration link creation data

    Returns:
        RegistrationLinkResponse: Created link with registration URL

    Raises:
        ValueError: If company_id or department_id is invalid
        ConnectionFailure: If database connection fails
    """
    try:
        # Generate secure link ID
        link_id = secrets.token_urlsafe(32)

        # Validate company_id exists
        db = get_database()
        companies_collection = db[settings.COMPANIES_COLLECTION]

        if not ObjectId.is_valid(link_data.company_id):
            raise ValueError(f"Invalid company_id format: {link_data.company_id}")

        company = companies_collection.find_one({"_id": ObjectId(link_data.company_id)})
        if not company:
            raise ValueError(f"Company not found with ID: {link_data.company_id}")

        # Get holding_id from company
        holding_id = company.get("holding_id")

        # If department_id provided, validate it
        if link_data.department_id:
            if not ObjectId.is_valid(link_data.department_id):
                raise ValueError(f"Invalid department_id format: {link_data.department_id}")

            departments_collection = db[settings.DEPARTMENTS_COLLECTION]
            department = departments_collection.find_one({"_id": ObjectId(link_data.department_id)})
            if not department:
                raise ValueError(f"Department not found with ID: {link_data.department_id}")

            # Verify department belongs to the company
            if department.get("company_id") != link_data.company_id:
                raise ValueError(f"Department {link_data.department_id} does not belong to company {link_data.company_id}")

        # Create link document
        current_time = datetime.utcnow()
        expires_at = current_time + settings.USER_LINK_EXPIRATION_DELTA

        link_doc = {
            "link_id": link_id,
            "company_id": link_data.company_id,
            "department_id": link_data.department_id,
            "holding_id": holding_id,
            "role": link_data.role,
            "created_at": current_time,
            "expires_at": expires_at,
            "is_used": False
        }

        # Store in database
        links_collection = db[settings.USER_LINKS_COLLECTION]
        links_collection.insert_one(link_doc)

        # Generate registration URL
        registration_url = f"{settings.FRONTEND_URL}/register?link_id={link_id}"

        logger.info(
            f"Created registration link {link_id} for company {link_data.company_id}, "
            f"department {link_data.department_id}, role {link_data.role}"
        )

        return RegistrationLinkResponse(
            link_id=link_id,
            registration_url=registration_url,
            company_id=link_data.company_id,
            department_id=link_data.department_id,
            role=link_data.role,
            created_at=current_time,
            expires_at=expires_at,
            is_used=False
        )

    except ValueError:
        raise
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Database connection error while creating registration link: {str(e)}")
        raise ConnectionFailure(f"Failed to create registration link: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while creating registration link: {str(e)}")
        raise Exception(f"Failed to create registration link: {str(e)}")


def verify_registration_link(link_id: str) -> Dict[str, Any]:
    """
    Verify registration link is valid and not expired.

    Args:
        link_id: Registration link identifier

    Returns:
        Dict containing company_id, department_id, role, holding_id

    Raises:
        ValueError: If link is invalid, expired, or already used
        ConnectionFailure: If database connection fails
    """
    try:
        db = get_database()
        links_collection = db[settings.USER_LINKS_COLLECTION]

        link_doc = links_collection.find_one({"link_id": link_id})
        if not link_doc:
            raise ValueError("Invalid registration link")

        if link_doc.get("is_used", False):
            raise ValueError("Registration link has already been used")

        if link_doc["expires_at"] < datetime.utcnow():
            raise ValueError("Registration link has expired")

        logger.info(f"Verified registration link with ID: {link_id}")

        return {
            "company_id": link_doc["company_id"],
            "department_id": link_doc.get("department_id"),
            "holding_id": link_doc.get("holding_id"),
            "role": link_doc["role"]
        }

    except ValueError:
        raise
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Database connection error while verifying link: {str(e)}")
        raise ConnectionFailure(f"Failed to verify link: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while verifying link: {str(e)}")
        raise Exception(f"Failed to verify link: {str(e)}")


def register_pending_user(registration_data: PendingUserCreate) -> PendingUserResponse:
    """
    Register a new user via registration link, creating a pending user application.

    The user will be added to pending_users collection and must be approved
    by an admin before being added to the users collection.

    Args:
        registration_data: User registration data from form

    Returns:
        PendingUserResponse: Created pending user information

    Raises:
        ValueError: If link is invalid, passwords don't match, or email exists
        ConnectionFailure: If database connection fails
    """
    try:
        # Validate passwords match
        if registration_data.password != registration_data.password_confirm:
            raise ValueError("Passwords do not match")

        # Verify registration link
        link_info = verify_registration_link(registration_data.link_id)

        # Validate and normalize email
        normalized_email = validate_email_format(registration_data.email.strip().lower())

        db = get_database()

        # Check if email already exists in users or pending_users
        users_collection = db[settings.USERS_COLLECTION]
        pending_users_collection = db[settings.PENDING_USERS_COLLECTION]

        if users_collection.find_one({"email": normalized_email}):
            raise ValueError(f"User with email {normalized_email} already exists")

        existing_pending = pending_users_collection.find_one({
            "email": normalized_email,
            "status": "pending"
        })
        if existing_pending:
            raise ValueError(f"A pending registration already exists for email {normalized_email}")

        # Hash password
        hashed_password = hash_password(registration_data.password)

        # Create pending user document
        current_time = datetime.utcnow()
        pending_user_doc = {
            "email": normalized_email,
            "firstName": registration_data.firstName,
            "lastName": registration_data.lastName,
            "hashed_password": hashed_password,
            "company_id": link_info["company_id"],
            "department_id": link_info.get("department_id"),
            "holding_id": link_info.get("holding_id"),
            "role": link_info["role"],
            "status": "pending",
            "created_at": current_time,
            "updated_at": current_time,
            "link_id": registration_data.link_id
        }

        # Insert pending user
        result = pending_users_collection.insert_one(pending_user_doc)

        # Mark link as used
        links_collection = db[settings.USER_LINKS_COLLECTION]
        links_collection.update_one(
            {"link_id": registration_data.link_id},
            {"$set": {"is_used": True, "used_at": current_time}}
        )

        logger.info(
            f"Created pending user registration for {normalized_email} "
            f"with ID {result.inserted_id}"
        )

        return PendingUserResponse(
            id=str(result.inserted_id),
            email=normalized_email,
            firstName=registration_data.firstName,
            lastName=registration_data.lastName,
            company_id=link_info["company_id"],
            department_id=link_info.get("department_id"),
            role=link_info["role"],
            status="pending",
            created_at=current_time,
            updated_at=current_time
        )

    except ValueError:
        raise
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Database connection error during user registration: {str(e)}")
        raise ConnectionFailure(f"Failed to register user: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during user registration: {str(e)}")
        raise Exception(f"Failed to register user: {str(e)}")





def list_pending_users(admin_user: dict) -> list[PendingUserResponse]:
    """
    List pending user registrations for admin approval.

    Filters based on admin's role:
    - superadmin: sees all pending users
    - admin: sees pending users for their company

    Args:
        admin_user: Admin user dict from authentication

    Returns:
        List of pending users

    Raises:
        ValueError: If admin doesn't have required permissions
        ConnectionFailure: If database connection fails
    """
    try:
        user_role = admin_user.get("role")
        user_company_id = admin_user.get("company_id")

        db = get_database()
        pending_users_collection = db[settings.PENDING_USERS_COLLECTION]

        # Build query based on role
        query = {"status": "pending"}

        if user_role == "superadmin":
            # Superadmin sees all pending users
            pass
        elif user_role == "admin":
            # Admin sees pending users for their company
            if not user_company_id:
                raise ValueError("Admin user must have a company_id")
            query["company_id"] = user_company_id
        else:
            raise ValueError(f"User with role {user_role} cannot view pending users")

        # Fetch pending users
        pending_users = list(pending_users_collection.find(query).sort("created_at", -1))

        # Convert to response models
        result = []
        for user in pending_users:
            result.append(PendingUserResponse(
                id=str(user["_id"]),
                email=user["email"],
                firstName=user["firstName"],
                lastName=user["lastName"],
                company_id=user["company_id"],
                department_id=user.get("department_id"),
                role=user["role"],
                status=user["status"],
                created_at=user["created_at"],
                updated_at=user["updated_at"]
            ))

        logger.info(f"Retrieved {len(result)} pending users for admin {admin_user.get('email')}")
        return result

    except ValueError:
        raise
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Database connection error while listing pending users: {str(e)}")
        raise ConnectionFailure(f"Failed to list pending users: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while listing pending users: {str(e)}")
        raise Exception(f"Failed to list pending users: {str(e)}")


def approve_pending_user(pending_user_id: str, admin_user: dict):
    """
    Approve pending user and move them to the users collection.

    Args:
        pending_user_id: MongoDB ObjectId of pending user
        admin_user: Admin user performing the approval

    Returns:
        UserCreateResponse: Approved user information

    Raises:
        ValueError: If pending user not found or admin lacks permission
        ConnectionFailure: If database connection fails
    """
    try:
        if not ObjectId.is_valid(pending_user_id):
            raise ValueError(f"Invalid pending_user_id format: {pending_user_id}")

        db = get_database()
        pending_users_collection = db[settings.PENDING_USERS_COLLECTION]
        users_collection = db[settings.USERS_COLLECTION]

        # Fetch pending user
        pending_user = pending_users_collection.find_one({"_id": ObjectId(pending_user_id)})
        if not pending_user:
            raise ValueError(f"Pending user not found with ID: {pending_user_id}")

        if pending_user["status"] != "pending":
            raise ValueError(f"User application is not in pending status (current: {pending_user['status']})")

        # Check admin has permission to approve
        admin_role = admin_user.get("role")
        admin_company_id = admin_user.get("company_id")

        if admin_role == "admin":
            # Admin can only approve users for their company
            if pending_user["company_id"] != admin_company_id:
                raise ValueError("You can only approve users for your own company")
        elif admin_role != "superadmin":
            raise ValueError(f"User with role {admin_role} cannot approve pending users")

        # Check if email already exists in users (double-check)
        if users_collection.find_one({"email": pending_user["email"]}):
            raise ValueError(f"User with email {pending_user['email']} already exists")

        # Create user document
        current_time = datetime.utcnow()
        user_doc = {
            "email": pending_user["email"],
            "firstName": pending_user["firstName"],
            "lastName": pending_user["lastName"],
            "hashed_password": pending_user["hashed_password"],
            "company_id": pending_user.get("company_id"),
            "department_id": pending_user.get("department_id"),
            "holding_id": pending_user.get("holding_id"),
            "role": pending_user["role"],
            "is_active": True,
            "created_at": current_time,
            "updated_at": current_time
        }

        # Insert into users collection
        result = users_collection.insert_one(user_doc)

        # Update pending user status to approved
        pending_users_collection.update_one(
            {"_id": ObjectId(pending_user_id)},
            {
                "$set": {
                    "status": "approved",
                    "approved_by": str(admin_user.get("_id")),
                    "approved_at": current_time,
                    "updated_at": current_time
                }
            }
        )

        logger.info(
            f"Approved pending user {pending_user['email']} (ID: {pending_user_id}) "
            f"by admin {admin_user.get('email')}"
        )

        # Send approval email
        try:
            email_service = get_email_service()
            if email_service:
                # Get company name
                companies_collection = db[settings.COMPANIES_COLLECTION]
                company = companies_collection.find_one({"_id": ObjectId(pending_user["company_id"])})
                company_name = company.get("name", "Unknown Company") if company else "Unknown Company"

                # Get department name if exists
                department_name = None
                if pending_user.get("department_id"):
                    departments_collection = db[settings.DEPARTMENTS_COLLECTION]
                    department = departments_collection.find_one({"_id": ObjectId(pending_user["department_id"])})
                    department_name = department.get("name") if department else None

                # Send approval email
                user_full_name = f"{pending_user['firstName']} {pending_user['lastName']}"
                email_service.send_user_approval_email(
                    to_email=pending_user["email"],
                    user_name=user_full_name,
                    company_name=company_name,
                    role=pending_user["role"],
                    department_name=department_name,
                    login_url=settings.FRONTEND_URL
                )
                logger.info(f"Approval email sent to {pending_user['email']}")
            else:
                logger.warning("Email service not configured, skipping approval email")
        except Exception as e:
            logger.error(f"Failed to send approval email to {pending_user['email']}: {str(e)}")
            # Don't fail the approval if email fails

        return UserCreateResponse(
            id=str(result.inserted_id),
            email=user_doc["email"],
            role=user_doc["role"],
            firstName=user_doc["firstName"],
            lastName=user_doc["lastName"],
            is_active=user_doc["is_active"],
            created_at=user_doc["created_at"],
            updated_at=user_doc["updated_at"],
            temporary_password="N/A"
        )

    except ValueError:
        raise
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Database connection error while approving user: {str(e)}")
        raise ConnectionFailure(f"Failed to approve user: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while approving user: {str(e)}")
        raise Exception(f"Failed to approve user: {str(e)}")


def reject_pending_user(pending_user_id: str, admin_user: dict) -> dict:
    """
    Reject pending user registration.

    Args:
        pending_user_id: MongoDB ObjectId of pending user
        admin_user: Admin user performing the rejection

    Returns:
        Dict with success message

    Raises:
        ValueError: If pending user not found or admin lacks permission
        ConnectionFailure: If database connection fails
    """
    try:
        if not ObjectId.is_valid(pending_user_id):
            raise ValueError(f"Invalid pending_user_id format: {pending_user_id}")

        db = get_database()
        pending_users_collection = db[settings.PENDING_USERS_COLLECTION]

        # Fetch pending user
        pending_user = pending_users_collection.find_one({"_id": ObjectId(pending_user_id)})
        if not pending_user:
            raise ValueError(f"Pending user not found with ID: {pending_user_id}")

        if pending_user["status"] != "pending":
            raise ValueError(f"User application is not in pending status (current: {pending_user['status']})")

        # Check admin has permission to reject
        admin_role = admin_user.get("role")
        admin_company_id = admin_user.get("company_id")

        if admin_role == "admin":
            # Admin can only reject users for their company
            if pending_user["company_id"] != admin_company_id:
                raise ValueError("You can only reject users for your own company")
        elif admin_role != "superadmin":
            raise ValueError(f"User with role {admin_role} cannot reject pending users")

        # Update pending user status to rejected
        current_time = datetime.utcnow()
        pending_users_collection.update_one(
            {"_id": ObjectId(pending_user_id)},
            {
                "$set": {
                    "status": "rejected",
                    "rejected_by": str(admin_user.get("_id")),
                    "rejected_at": current_time,
                    "updated_at": current_time
                }
            }
        )

        logger.info(
            f"Rejected pending user {pending_user['email']} (ID: {pending_user_id}) "
            f"by admin {admin_user.get('email')}"
        )

        # Send rejection email
        try:
            email_service = get_email_service()
            if email_service:
                # Get company name
                companies_collection = db[settings.COMPANIES_COLLECTION]
                company = companies_collection.find_one({"_id": ObjectId(pending_user["company_id"])})
                company_name = company.get("name", "Unknown Company") if company else "Unknown Company"

                # Send rejection email
                user_full_name = f"{pending_user['firstName']} {pending_user['lastName']}"
                email_service.send_user_rejection_email(
                    to_email=pending_user["email"],
                    user_name=user_full_name,
                    company_name=company_name
                )
                logger.info(f"Rejection email sent to {pending_user['email']}")
            else:
                logger.warning("Email service not configured, skipping rejection email")
        except Exception as e:
            logger.error(f"Failed to send rejection email to {pending_user['email']}: {str(e)}")
            # Don't fail the rejection if email fails

        return {
            "message": "User registration rejected successfully",
            "pending_user_id": pending_user_id,
            "email": pending_user["email"]
        }

    except ValueError:
        raise
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Database connection error while rejecting user: {str(e)}")
        raise ConnectionFailure(f"Failed to reject user: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while rejecting user: {str(e)}")
        raise Exception(f"Failed to reject user: {str(e)}")


def list_users_with_filter(admin_user: dict, status_filter: str = "active"):
    """
    List users with status filter (active, blocked).

    Args:
        admin_user: Admin user dict
        status_filter: "active" or "blocked"

    Returns:
        List of users matching filter

    Raises:
        ValueError: If invalid filter or admin lacks permission
        ConnectionFailure: If database connection fails
    """
    from .models import UserResponse

    try:
        if status_filter not in ["active", "blocked"]:
            raise ValueError(f"Invalid status filter: {status_filter}. Must be 'active' or 'blocked'")

        db = get_database()

        admin_role = admin_user.get("role")
        admin_company_id = admin_user.get("company_id")

        # Query regular users
        users_collection = db[settings.USERS_COLLECTION]

        query = {}
        if status_filter == "active":
            query["is_active"] = True
        elif status_filter == "blocked":
            query["is_active"] = False

        # Filter by admin's scope
        if admin_role == "admin":
            if not admin_company_id:
                raise ValueError("Admin user must have a company_id")
            query["company_id"] = admin_company_id
        elif admin_role != "superadmin":
            raise ValueError(f"User with role {admin_role} cannot list users")

        # Fetch users
        users = list(users_collection.find(query).sort("created_at", -1))

        # Convert to response models
        result = []
        for user in users:
            result.append(UserResponse(
                id=str(user["_id"]),
                email=user["email"],
                role=user.get("role", "user"),  # Default to "user" if role is missing
                firstName=user.get("firstName"),
                lastName=user.get("lastName"),
                is_active=user.get("is_active", True),
                created_at=user["created_at"],
                updated_at=user["updated_at"]
            ))

        logger.info(f"Retrieved {len(result)} users with filter '{status_filter}' for admin {admin_user.get('email')}")
        return result

    except ValueError:
        raise
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Database connection error while listing users: {str(e)}")
        raise ConnectionFailure(f"Failed to list users: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while listing users: {str(e)}")
        raise Exception(f"Failed to list users: {str(e)}")


def delete_user(user_id: str, admin_user: dict) -> dict:
    """
    Delete a user and handle cascade updates.

    This function performs a hard delete of a user and handles all related references:
    - Removes user as company admin (sets company.admin_id to None)
    - Removes user as department manager (sets department.manager_id to None)
    - Deletes the user from the users collection
    - Maintains historical records in pending_users with action references

    Permissions:
    - Superadmin: Can delete any user (except other superadmins)
    - Admin: Can only delete users in their company (except superadmins)
    - Director/User: Cannot delete users

    Args:
        user_id: MongoDB ObjectId string of user to delete
        admin_user: Admin user performing the deletion

    Returns:
        Dict with success message and deleted user info

    Raises:
        ValueError: If user not found, invalid permissions, or attempting to delete superadmin
        ConnectionFailure: If database connection fails

    Example:
        >>> result = delete_user("507f1f77bcf86cd799439011", admin_user)
        >>> print(result["message"])
        'User deleted successfully'
    """
    try:
        if not ObjectId.is_valid(user_id):
            raise ValueError(f"Invalid user_id format: {user_id}")

        db = get_database()
        users_collection = db[settings.USERS_COLLECTION]
        companies_collection = db[settings.COMPANIES_COLLECTION]
        departments_collection = db[settings.DEPARTMENTS_COLLECTION]

        # Fetch user to delete
        user_to_delete = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user_to_delete:
            raise ValueError(f"User not found with ID: {user_id}")

        # Check if trying to delete a superadmin
        if user_to_delete.get("role") == "superadmin":
            raise ValueError("Cannot delete superadmin users")

        # Check admin has permission to delete
        admin_role = admin_user.get("role")
        admin_company_id = admin_user.get("company_id")

        if admin_role == "admin":
            # Admin can only delete users in their company
            if user_to_delete.get("company_id") != admin_company_id:
                raise ValueError("You can only delete users in your own company")
        elif admin_role != "superadmin":
            raise ValueError(f"User with role {admin_role} cannot delete users")

        user_email = user_to_delete.get("email")
        user_full_name = f"{user_to_delete.get('firstName', '')} {user_to_delete.get('lastName', '')}".strip() or user_email

        # Handle cascade updates - Remove user from companies where they are admin
        companies_with_user_as_admin = companies_collection.find({"admin_id": user_id})
        companies_updated = 0
        for company in companies_with_user_as_admin:
            companies_collection.update_one(
                {"_id": company["_id"]},
                {"$set": {"admin_id": None, "updated_at": datetime.utcnow()}}
            )
            companies_updated += 1
            logger.info(f"Removed user {user_id} as admin from company {company['_id']}")

        # Handle cascade updates - Remove user from departments where they are manager
        departments_with_user_as_manager = departments_collection.find({"manager_id": user_id})
        departments_updated = 0
        for department in departments_with_user_as_manager:
            departments_collection.update_one(
                {"_id": department["_id"]},
                {"$set": {"manager_id": None, "updated_at": datetime.utcnow()}}
            )
            departments_updated += 1
            logger.info(f"Removed user {user_id} as manager from department {department['_id']}")

        # Delete the user
        delete_result = users_collection.delete_one({"_id": ObjectId(user_id)})

        if delete_result.deleted_count == 0:
            raise ValueError(f"Failed to delete user with ID: {user_id}")

        logger.info(
            f"Successfully deleted user {user_email} (ID: {user_id}) "
            f"by admin {admin_user.get('email')}. "
            f"Updated {companies_updated} companies and {departments_updated} departments."
        )

        return {
            "message": "User deleted successfully",
            "user_id": user_id,
            "email": user_email,
            "name": user_full_name,
            "companies_updated": companies_updated,
            "departments_updated": departments_updated
        }

    except ValueError:
        raise
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Database connection error while deleting user: {str(e)}")
        raise ConnectionFailure(f"Failed to delete user: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while deleting user: {str(e)}")
        raise Exception(f"Failed to delete user: {str(e)}")
