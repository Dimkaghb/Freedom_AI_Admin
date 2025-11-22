from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# Request/Response Models for API
class HoldingCreate(BaseModel):
    """Model for creating a new holding"""
    name: str = Field(..., min_length=1, max_length=100, description="Holding name")
    description: Optional[str] = Field(None, max_length=500, description="Holding description")


class HoldingUpdate(BaseModel):
    """Model for updating/renaming a holding"""
    name: str = Field(..., min_length=1, max_length=100, description="New holding name")
    description: Optional[str] = Field(None, max_length=500, description="Updated description")


class HoldingResponse(BaseModel):
    """Model for holding response from API"""
    id: str = Field(..., description="MongoDB ObjectId as string")
    name: str
    description: Optional[str] = None
    company_ids: List[str] = Field(default_factory=list, description="List of company IDs belonging to this holding")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "TechCorp Holdings",
                "description": "Technology conglomerate",
                "company_ids": ["507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )


class HoldingInDB(BaseModel):
    """Model for holding document in MongoDB"""
    name: str
    description: Optional[str] = None
    company_ids: List[str] = Field(default_factory=list, description="List of company IDs belonging to this holding")
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False  # Soft delete flag


class HoldingListResponse(BaseModel):
    """Model for listing holdings"""
    holdings: List[HoldingResponse]
    total: int


# Future models for companies and departments
class Company(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    holding_id: str


class Department(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    company_id: str
