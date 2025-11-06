from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from bson import ObjectId


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    role: str = Field(..., pattern="^(superadmin|admin|director|user)$")
    full_name: Optional[str] = None
    is_active: bool = True
    holding_id: Optional[str] = Field(default=None, description="ID of the holding (for superadmin)")
    company_id: Optional[str] = Field(default=None, description="ID of the company (for admin)")
    department_id: Optional[str] = Field(default=None, description="ID of the department (for director/user)")


class UserCreate(UserBase):
    """User creation model"""
    pass


class UserInDB(BaseModel):
    """User model as stored in database"""
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr
    role: str
    full_name: Optional[str] = None
    is_active: bool = True
    hashed_password: str
    holding_id: Optional[str] = None
    company_id: Optional[str] = None
    department_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    @field_validator('id', mode='before')
    @classmethod
    def convert_objectid_to_str(cls, v: Any) -> str:
        """Convert ObjectId to string"""
        if isinstance(v, ObjectId):
            return str(v)
        return v


class UserResponse(UserBase):
    """User response model (without sensitive data)"""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreateResponse(UserResponse):
    """User creation response model with temporary password"""
    temporary_password: str


class CreateUserLink(BaseModel):
    company_id: str = Field(..., description="MongoDB ObjectId of the company")
    department_id: Optional[str] = Field(None, description="MongoDB ObjectId of the department")
    role: str = Field(..., pattern="^(superadmin|admin|director|user)$")

class UserLink(BaseModel):
    id: str = Field(..., description="MongoDB ObjectId as string")
    company_id: str
    department_id: Optional[str] = None
    role: str
    is_used: bool = False
    expired: bool = False
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "607f1f77bcf86cd799439021",
                "company_id": "507f1f77bcf86cd799439011",
                "department_id": "507f1f77bcf86cd799439013",
                "role": "user",
                "is_used": False,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )

class RegisterUserRequest(BaseModel):
    """Model for user registration request"""
    link_id: str = Field(..., description="MongoDB ObjectId of the CreateUserLink")
    email: EmailStr
    full_name: Optional[str] = None
    password: str = Field(..., min_length=8, description="User password")

class UserListResponse(BaseModel):
    """Model for listing users"""
    users: list[UserResponse]
    total_count: int = Field(..., description="Total number of users")


class RegistrationLinkCreate(BaseModel):
    """Model for creating a registration link"""
    company_id: str = Field(..., description="MongoDB ObjectId of the company")
    department_id: Optional[str] = Field(None, description="MongoDB ObjectId of the department (optional for company-level admin)")
    role: str = Field(..., pattern="^(admin|director|user)$", description="Role to assign: admin (company-level), director/user (department-level)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_id": "507f1f77bcf86cd799439011",
                "department_id": "507f1f77bcf86cd799439013",
                "role": "user"
            }
        }
    )


class RegistrationLinkResponse(BaseModel):
    """Model for registration link response"""
    link_id: str = Field(..., description="Unique link identifier")
    registration_url: str = Field(..., description="Full registration URL to share with user")
    company_id: str
    department_id: Optional[str] = None
    role: str
    created_at: datetime
    expires_at: datetime
    is_used: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "link_id": "abc123def456",
                "registration_url": "http://localhost:9002/register?link_id=abc123def456",
                "company_id": "507f1f77bcf86cd799439011",
                "department_id": "507f1f77bcf86cd799439013",
                "role": "user",
                "created_at": "2024-01-01T00:00:00",
                "expires_at": "2024-01-02T00:00:00",
                "is_used": False
            }
        }
    )


class PendingUserCreate(BaseModel):
    """Model for user registration via link"""
    link_id: str = Field(..., description="Registration link identifier")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    password_confirm: str = Field(..., min_length=8, description="Password confirmation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "link_id": "abc123def456",
                "email": "user@example.com",
                "full_name": "John Doe",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!"
            }
        }
    )


class PendingUserResponse(BaseModel):
    """Model for pending user response"""
    id: str = Field(..., description="MongoDB ObjectId as string")
    email: EmailStr
    full_name: str
    company_id: str
    department_id: Optional[str] = None
    role: str
    status: str = Field(..., description="Status: pending, approved, rejected")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "607f1f77bcf86cd799439021",
                "email": "user@example.com",
                "full_name": "John Doe",
                "company_id": "507f1f77bcf86cd799439011",
                "department_id": "507f1f77bcf86cd799439013",
                "role": "user",
                "status": "pending",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )


class PendingUserInDB(BaseModel):
    """Model for pending user document in MongoDB"""
    email: EmailStr
    full_name: str
    hashed_password: str
    company_id: str
    department_id: Optional[str] = None
    holding_id: Optional[str] = None
    role: str
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime
    updated_at: datetime
    link_id: str


class PendingUsersListResponse(BaseModel):
    """Model for listing pending users"""
    pending_users: list[PendingUserResponse]
    total_count: int = Field(..., description="Total number of pending users")


class UserApprovalAction(BaseModel):
    """Model for approving/rejecting pending user"""
    pending_user_id: str = Field(..., description="MongoDB ObjectId of the pending user")
    action: str = Field(..., pattern="^(approve|reject)$", description="Action to perform: approve or reject")