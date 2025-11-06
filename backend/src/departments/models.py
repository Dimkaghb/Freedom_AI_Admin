from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class DepartmentCreate(BaseModel):
    """Model for creating a new department"""
    name: str = Field(..., min_length=1, max_length=100, description="Department name")
    description: Optional[str] = Field(None, max_length=500, description="Department description")
    company_id: str = Field(..., description="MongoDB ObjectId of the parent company")
    manager_id: Optional[str] = Field(None, description="MongoDB ObjectId of the department manager")

class DepartmentUpdate(BaseModel):
    """Model for updating a department"""
    name: str = Field(..., min_length=1, max_length=100, description="New department name")
    description: Optional[str] = Field(None, max_length=500, description="Updated description")
    manager_id: Optional[str] = Field(None, description="Updated manager user ObjectId")

class DepartmentResponse(BaseModel):
    """Model for department response from API"""
    id: str = Field(..., description="MongoDB ObjectId as string")
    name: str
    description: Optional[str] = None
    company_id: str
    manager_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "607f1f77bcf86cd799439021",
                "name": "Research and Development",
                "description": "R&D Department",
                "company_id": "507f1f77bcf86cd799439011",
                "manager_id": "507f1f77bcf86cd799439013",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )

class DepartmentInDB(BaseModel):
    """Model for department document in MongoDB"""
    name: str
    description: Optional[str] = None
    company_id: str
    manager_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False  # Soft delete flag

class DepartmentListResponse(BaseModel):
    """Model for listing departments"""
    departments: List[DepartmentResponse] 
    total_count: int = Field(..., description="Total number of departments")