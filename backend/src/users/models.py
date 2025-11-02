from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId class for Pydantic compatibility"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    role: str = Field(..., regex="^(admin|user)$")
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """User creation model"""
    pass


class UserInDB(UserBase):
    """User model as stored in database"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserResponse(UserBase):
    """User response model (without sensitive data)"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCreateResponse(UserResponse):
    """User creation response model with temporary password"""
    temporary_password: str