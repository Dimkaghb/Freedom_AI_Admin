# User Management System Documentation

## Overview

This document describes the comprehensive user management system implemented in the FreedomAIAdmin backend, specifically focusing on the `add_user_by_admin` function and related components.

## Features

### 🔐 Security Features
- **Secure Password Generation**: 12+ character passwords with mixed case, numbers, and special characters
- **bcrypt Password Hashing**: Industry-standard password hashing with salt
- **Email Validation**: Comprehensive email format validation and normalization
- **Input Sanitization**: Proper validation of all input parameters

### 🗄️ Database Features
- **MongoDB Integration**: Full MongoDB Atlas support with connection pooling
- **Duplicate Prevention**: Unique email constraints with proper error handling
- **Transaction Safety**: Proper connection management and cleanup
- **Index Management**: Automatic creation of required database indexes

### 📊 Monitoring & Logging
- **Comprehensive Logging**: Detailed logging for all operations and errors
- **Audit Trail**: Complete tracking of user creation operations
- **Error Tracking**: Structured error handling with appropriate log levels

## Function Reference

### `add_user_by_admin(email: str, role: str, full_name: str = None) -> UserCreateResponse`

Creates a new user with secure password generation and database storage.

#### Parameters
- `email` (str): User's email address (validated and normalized)
- `role` (str): User role - must be either 'admin' or 'user'
- `full_name` (str, optional): User's full name

#### Returns
- `UserCreateResponse`: Complete user document with temporary password

#### Raises
- `ValueError`: Invalid input parameters (email format, role, duplicate email)
- `ConnectionFailure`: Database connection issues
- `Exception`: Other database operation errors

#### Example Usage

```python
from src.users.utils import add_user_by_admin

# Create an admin user
admin_user = add_user_by_admin(
    email="admin@company.com",
    role="admin",
    full_name="John Administrator"
)

print(f"User created: {admin_user.email}")
print(f"Temporary password: {admin_user.temporary_password}")
print(f"User ID: {admin_user.id}")

# Create a regular user
regular_user = add_user_by_admin(
    email="user@company.com",
    role="user"
)
```

## API Endpoints

### POST `/users/create`

Creates a new user via HTTP API.

#### Request Body
```json
{
    "email": "user@example.com",
    "role": "user",
    "full_name": "Optional Full Name"
}
```

#### Response (201 Created)
```json
{
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "role": "user",
    "full_name": "Optional Full Name",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "temporary_password": "Xy9#mK2$pL8@"
}
```

#### Error Responses
- `400 Bad Request`: Invalid input data
- `500 Internal Server Error`: Database or server errors

### GET `/users/health`

Health check endpoint for the users service.

## Data Models

### UserInDB
Complete user model as stored in the database.

```python
{
    "_id": ObjectId,
    "email": str,
    "role": str,  # "admin" or "user"
    "full_name": Optional[str],
    "is_active": bool,
    "hashed_password": str,
    "created_at": datetime,
    "updated_at": datetime
}
```

### UserCreateResponse
Response model for user creation (includes temporary password).

```python
{
    "id": str,
    "email": str,
    "role": str,
    "full_name": Optional[str],
    "is_active": bool,
    "created_at": datetime,
    "updated_at": datetime,
    "temporary_password": str  # Only returned once
}
```

## Security Considerations

### Password Security
- Passwords are generated using `secrets` module for cryptographic security
- Minimum 12 characters with guaranteed character diversity
- bcrypt hashing with automatic salt generation
- Plaintext passwords are never stored

### Database Security
- Connection strings use environment variables
- Proper connection timeout configurations
- Automatic connection cleanup
- Unique constraints prevent duplicate users

### Input Validation
- Email format validation using `email-validator`
- Role validation with whitelist approach
- Input sanitization and normalization
- Comprehensive error handling

## Environment Configuration

Required environment variables in `.env`:

```env
# MongoDB Configuration
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/database
DATABASE_NAME=your_database_name
USERS_COLLECTION=users_collection_name

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Security (Optional - has defaults)
SECRET_KEY=your-secret-key-for-jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=300
```

## Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Update MongoDB connection string
   - Set other required variables

3. **Run the Application**
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Test the API**
   - Visit `http://localhost:8000/docs` for interactive API documentation
   - Use the `/users/health` endpoint to verify service status

## Testing

### Unit Testing
```python
import pytest
from src.users.utils import add_user_by_admin, generate_secure_password

def test_password_generation():
    password = generate_secure_password()
    assert len(password) >= 12
    assert any(c.islower() for c in password)
    assert any(c.isupper() for c in password)
    assert any(c.isdigit() for c in password)

def test_user_creation():
    user = add_user_by_admin("test@example.com", "user")
    assert user.email == "test@example.com"
    assert user.role == "user"
    assert user.temporary_password is not None
```

### API Testing
```bash
# Test user creation
curl -X POST "http://localhost:8000/users/create" \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "role": "user"}'

# Test health endpoint
curl "http://localhost:8000/users/health"
```

## Future Extensions

The system is designed for easy extension:

### Additional User Fields
```python
# Add new fields to UserBase model
class UserBase(BaseModel):
    email: EmailStr
    role: str
    full_name: Optional[str] = None
    is_active: bool = True
    department: Optional[str] = None  # New field
    phone: Optional[str] = None       # New field
```

### Custom Password Policies
```python
def generate_secure_password(
    length: int = 12,
    require_special: bool = True,
    custom_special_chars: str = None
) -> str:
    # Enhanced password generation logic
```

### Role-Based Access Control
```python
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    READONLY = "readonly"
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Errors**
   - Verify connection string format
   - Check network connectivity
   - Ensure database credentials are correct

2. **Email Validation Errors**
   - Check email format
   - Verify email-validator dependency

3. **Duplicate User Errors**
   - Check if user already exists
   - Verify email uniqueness

### Logging

Check application logs for detailed error information:
```bash
# View logs in real-time
tail -f app.log

# Search for specific errors
grep "ERROR" app.log
```

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify environment configuration
3. Test database connectivity
4. Review API documentation at `/docs`

## Changelog

### Version 1.0.0
- Initial implementation of `add_user_by_admin` function
- Secure password generation with bcrypt hashing
- MongoDB integration with proper error handling
- Comprehensive input validation and logging
- FastAPI endpoint implementation
- Complete documentation and testing guidelines