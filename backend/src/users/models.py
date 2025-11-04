from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from bson import ObjectId


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    role: str = Field(..., pattern="^(admin|user)$")
    full_name: Optional[str] = None
    is_active: bool = True


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