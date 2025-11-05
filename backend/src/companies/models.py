from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# Request/Response Models for API
class CompanyCreate(BaseModel):
    """Model for creating a new company"""
    name: str = Field(..., min_length=1, max_length=100, description="Company name")
    description: Optional[str] = Field(None, max_length=500, description="Company description")
    holding_id: str = Field(..., description="MongoDB ObjectId of the parent holding")
    admin_id: Optional[str] = Field(None, description="MongoDB ObjectId of the admin user")


class CompanyUpdate(BaseModel):
    """Model for updating a company"""
    name: str = Field(..., min_length=1, max_length=100, description="New company name")
    description: Optional[str] = Field(None, max_length=500, description="Updated description")
    admin_id: Optional[str] = Field(None, description="Updated admin user ObjectId")


class CompanyResponse(BaseModel):
    """Model for company response from API"""
    id: str = Field(..., description="MongoDB ObjectId as string")
    name: str
    description: Optional[str] = None
    holding_id: str
    admin_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "TechCorp Inc",
                "description": "Technology company",
                "holding_id": "507f1f77bcf86cd799439012",
                "admin_id": "507f1f77bcf86cd799439013",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )


class CompanyInDB(BaseModel):
    """Model for company document in MongoDB"""
    name: str
    description: Optional[str] = None
    holding_id: str
    admin_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False  # Soft delete flag


class CompanyListResponse(BaseModel):
    """Model for listing companies"""
    companies: List[CompanyResponse]
    total: int
