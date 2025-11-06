from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class FolderBase(BaseModel):
    """
    Base model for folder operations with hierarchical support.

    Fields:
    - name: Folder name (required, 1-255 characters)
    - fileIds: List of file IDs contained in this folder
    - type: Folder type (default: "documents")
    - parentID: ID of parent folder (None for root folders)
    - foldersids: Array of child folder IDs
    - holding_id: ID of the holding this folder belongs to (optional)
    - company_id: ID of the company this folder belongs to (optional)
    - department_id: ID of the department this folder belongs to (optional)
    - admin_id: ID of the admin who manages this folder (for company-level folders)
    """
    name: str = Field(..., min_length=1, max_length=255)
    fileIds: List[str] = Field(default_factory=list)
    type: Optional[str] = Field(default="documents")
    parentID: Optional[str] = Field(default=None, description="ID of parent folder, None for root folders")
    foldersids: List[str] = Field(default_factory=list, description="Array of child folder IDs")
    holding_id: Optional[str] = Field(default=None, description="ID of the holding")
    company_id: Optional[str] = Field(default=None, description="ID of the company")
    department_id: Optional[str] = Field(default=None, description="ID of the department")
    admin_id: Optional[str] = Field(default=None, description="ID of the admin managing this folder")

class FolderCreate(FolderBase):
    name = Field(..., min_length=1, max_length=255)


class FolderRename(BaseModel):
    """Model for folder rename operations"""
    name: str = Field(..., min_length=1, max_length=255, description="New folder name")

class FolderResponse(FolderBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FolderInDB(FolderBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    fileIds: List[str] = Field(default_factory=list)
