from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ============================================================================
# FOLDER MODELS
# ============================================================================

class FolderBase(BaseModel):
    """
    Base model for folder operations matching database schema.

    Database Schema:
    - _id: ObjectId (auto-generated)
    - name: str
    - fileIds: List[str]
    - type: str (e.g., "documents")
    - parentID: str | null
    - foldersids: List[str]
    - company_id: str
    - department_id: str
    - holding_id: str
    - created_at: datetime
    - updated_at: datetime
    """
    name: str = Field(..., min_length=1, max_length=255, description="Folder name")
    type: Optional[str] = Field(default="documents", description="Folder type")
    parentID: Optional[str] = Field(default=None, description="Parent folder ID (null for root)")


class FolderCreate(FolderBase):
    """Model for creating a new folder"""
    pass


class FolderUpdate(BaseModel):
    """Model for updating folder properties"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New folder name")
    parentID: Optional[str] = Field(None, description="New parent folder ID")


class FolderRename(BaseModel):
    """Model for folder rename operations"""
    name: str = Field(..., min_length=1, max_length=255, description="New folder name")


class FolderMove(BaseModel):
    """Model for moving folder to a new parent"""
    new_parent_id: Optional[str] = Field(None, description="New parent folder ID (null for root)")


class FolderResponse(BaseModel):
    """Model for folder response data"""
    id: str = Field(..., description="Folder ID")
    name: str
    fileIds: List[str] = Field(default_factory=list)
    type: str
    parentID: Optional[str] = None
    foldersids: List[str] = Field(default_factory=list)
    company_id: str
    department_id: str
    holding_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FolderListResponse(BaseModel):
    """Response model for list of folders"""
    folders: List[FolderResponse]
    total: int


# ============================================================================
# FILE MODELS
# ============================================================================

class FileBase(BaseModel):
    """
    Base model for file operations matching database schema.

    Database Schema:
    - _id: ObjectId (auto-generated)
    - filename: str
    - file_key: str (S3 key)
    - file_type: str (MIME type)
    - file_size: int (bytes)
    - company_id: str
    - department_id: str
    - holding_id: str
    - chat_id: str | null
    - folder_id: str | null
    - description: str
    - tags: List[str]
    - created_at: datetime
    - updated_at: datetime
    """
    filename: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default="", description="File description")
    tags: List[str] = Field(default_factory=list, description="File tags")
    folder_id: Optional[str] = Field(default=None, description="Parent folder ID")


class FileCreate(FileBase):
    """Model for file creation (used after upload)"""
    file_key: str = Field(..., description="S3 storage key")
    file_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")


class FileUpdate(BaseModel):
    """Model for updating file metadata"""
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    folder_id: Optional[str] = None


class FileRename(BaseModel):
    """Model for file rename operations"""
    filename: str = Field(..., min_length=1, max_length=255, description="New filename")


class FileMove(BaseModel):
    """Model for moving file to a new folder"""
    folder_id: Optional[str] = Field(None, description="New folder ID (null for root)")


class FileResponse(BaseModel):
    """Model for file response data"""
    id: str = Field(..., description="File ID")
    filename: str
    file_key: str
    file_type: str
    file_size: int
    company_id: str
    department_id: str
    holding_id: str
    chat_id: Optional[str] = None
    folder_id: Optional[str] = None
    description: str
    tags: List[str]
    download_url: Optional[str] = None  # Presigned URL (generated on request)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """Response model for list of files"""
    files: List[FileResponse]
    total: int


class FileUploadRequest(BaseModel):
    """Request model for initiating file upload"""
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    folder_id: Optional[str] = Field(None, description="Target folder ID")
    description: Optional[str] = Field(default="")
    tags: List[str] = Field(default_factory=list)


class FileUploadResponse(BaseModel):
    """Response model for file upload initiation"""
    upload_url: str = Field(..., description="Presigned S3 upload URL")
    file_id: str = Field(..., description="File ID in database")
    file_key: str = Field(..., description="S3 storage key")
    expires_in: int = Field(default=3600, description="URL expiration time in seconds")


# ============================================================================
# BREADCRUMB / NAVIGATION MODELS
# ============================================================================

class BreadcrumbItem(BaseModel):
    """Single breadcrumb item"""
    id: Optional[str] = None
    name: str


class FolderPathResponse(BaseModel):
    """Response model for folder path (breadcrumbs)"""
    path: List[BreadcrumbItem]


# ============================================================================
# STORAGE INFO MODELS
# ============================================================================

class StorageInfo(BaseModel):
    """Storage usage information"""
    total_files: int
    total_size_bytes: int
    total_size_formatted: str
    by_company: Optional[dict] = None
    by_department: Optional[dict] = None
