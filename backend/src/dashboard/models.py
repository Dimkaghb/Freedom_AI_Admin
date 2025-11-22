"""
Dashboard models for role-based data aggregation.

This module defines Pydantic models for dashboard statistics and summaries.
Different models are returned based on user roles to ensure proper data access control.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Summary Models - Lightweight representations of resources
# ============================================================================

class HoldingSummary(BaseModel):
    """Lightweight holding information for dashboard display"""
    id: str = Field(..., description="MongoDB ObjectId as string")
    name: str = Field(..., description="Holding name")
    description: Optional[str] = Field(None, description="Holding description")
    companies_count: int = Field(0, description="Number of companies in this holding")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "Global Holdings Inc",
                "description": "International holding company",
                "companies_count": 5,
                "created_at": "2024-01-01T00:00:00"
            }
        }
    )


class CompanySummary(BaseModel):
    """Lightweight company information for dashboard display"""
    id: str = Field(..., description="MongoDB ObjectId as string")
    name: str = Field(..., description="Company name")
    description: Optional[str] = Field(None, description="Company description")
    holding_id: str = Field(..., description="Parent holding ID")
    holding_name: Optional[str] = Field(None, description="Parent holding name")
    departments_count: int = Field(0, description="Number of departments in this company")
    users_count: int = Field(0, description="Number of users in this company")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "name": "TechCorp Inc",
                "description": "Technology company",
                "holding_id": "507f1f77bcf86cd799439011",
                "holding_name": "Global Holdings Inc",
                "departments_count": 8,
                "users_count": 45,
                "created_at": "2024-01-01T00:00:00"
            }
        }
    )


class DepartmentSummary(BaseModel):
    """Lightweight department information for dashboard display"""
    id: str = Field(..., description="MongoDB ObjectId as string")
    name: str = Field(..., description="Department name")
    description: Optional[str] = Field(None, description="Department description")
    company_id: str = Field(..., description="Parent company ID")
    company_name: Optional[str] = Field(None, description="Parent company name")
    manager_id: Optional[str] = Field(None, description="Department manager user ID")
    manager_name: Optional[str] = Field(None, description="Department manager full name")
    users_count: int = Field(0, description="Number of users in this department")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "607f1f77bcf86cd799439021",
                "name": "Research and Development",
                "description": "R&D Department",
                "company_id": "507f1f77bcf86cd799439012",
                "company_name": "TechCorp Inc",
                "manager_id": "707f1f77bcf86cd799439031",
                "manager_name": "John Doe",
                "users_count": 12,
                "created_at": "2024-01-01T00:00:00"
            }
        }
    )


class UserSummary(BaseModel):
    """Lightweight user information for dashboard display"""
    id: str = Field(..., description="MongoDB ObjectId as string")
    email: str = Field(..., description="User email")
    firstName: Optional[str] = Field(None, description="User first name")
    lastName: Optional[str] = Field(None, description="User last name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(True, description="User active status")
    department_id: Optional[str] = Field(None, description="User's department ID")
    department_name: Optional[str] = Field(None, description="User's department name")
    company_id: Optional[str] = Field(None, description="User's company ID")
    company_name: Optional[str] = Field(None, description="User's company name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "707f1f77bcf86cd799439031",
                "email": "user@example.com",
                "firstName": "John",
                "lastName": "Doe",
                "role": "user",
                "is_active": True,
                "department_id": "607f1f77bcf86cd799439021",
                "department_name": "Research and Development",
                "company_id": "507f1f77bcf86cd799439012",
                "company_name": "TechCorp Inc"
            }
        }
    )


# ============================================================================
# Statistics Models - Aggregated counts and metrics
# ============================================================================

class DashboardCounts(BaseModel):
    """Aggregated counts for dashboard overview"""
    holdings: int = Field(0, description="Total number of holdings user can access")
    companies: int = Field(0, description="Total number of companies user can access")
    departments: int = Field(0, description="Total number of departments user can access")
    users: int = Field(0, description="Total number of users user can access")
    active_users: int = Field(0, description="Number of active users")
    pending_users: int = Field(0, description="Number of pending user registrations")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "holdings": 3,
                "companies": 12,
                "departments": 45,
                "users": 234,
                "active_users": 220,
                "pending_users": 5
            }
        }
    )


# ============================================================================
# Dashboard Response Models - Role-specific responses
# ============================================================================

class SuperadminDashboardResponse(BaseModel):
    """
    Dashboard response for superadmin role.

    Superadmin can see:
    - All holdings with company counts
    - All companies across holdings
    - All departments across companies
    - All users across the organization
    """
    role: str = Field("superadmin", description="User role")
    counts: DashboardCounts = Field(..., description="Aggregated counts")
    holdings: List[HoldingSummary] = Field(default_factory=list, description="List of all holdings")
    recent_companies: List[CompanySummary] = Field(
        default_factory=list,
        description="Recently created companies (limit 10)"
    )
    recent_departments: List[DepartmentSummary] = Field(
        default_factory=list,
        description="Recently created departments (limit 10)"
    )
    recent_users: List[UserSummary] = Field(
        default_factory=list,
        description="Recently registered users (limit 10)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "superadmin",
                "counts": {
                    "holdings": 3,
                    "companies": 12,
                    "departments": 45,
                    "users": 234,
                    "active_users": 220,
                    "pending_users": 5
                },
                "holdings": [],
                "recent_companies": [],
                "recent_departments": [],
                "recent_users": []
            }
        }
    )


class AdminDashboardResponse(BaseModel):
    """
    Dashboard response for admin role.

    Admin can see:
    - Their company details
    - All departments in their company
    - All users in their company
    """
    role: str = Field("admin", description="User role")
    counts: DashboardCounts = Field(..., description="Aggregated counts")
    company: Optional[CompanySummary] = Field(None, description="Admin's company details")
    departments: List[DepartmentSummary] = Field(
        default_factory=list,
        description="All departments in the company"
    )
    recent_users: List[UserSummary] = Field(
        default_factory=list,
        description="Recently registered users in the company (limit 10)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "admin",
                "counts": {
                    "holdings": 0,
                    "companies": 1,
                    "departments": 8,
                    "users": 45,
                    "active_users": 42,
                    "pending_users": 2
                },
                "company": None,
                "departments": [],
                "recent_users": []
            }
        }
    )


class DirectorDashboardResponse(BaseModel):
    """
    Dashboard response for director role.

    Director can see:
    - Their department details
    - All users in their department
    - Department performance metrics
    """
    role: str = Field("director", description="User role")
    counts: DashboardCounts = Field(..., description="Aggregated counts")
    department: Optional[DepartmentSummary] = Field(None, description="Director's department details")
    company: Optional[CompanySummary] = Field(None, description="Department's parent company (limited info)")
    users: List[UserSummary] = Field(
        default_factory=list,
        description="All users in the department"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "director",
                "counts": {
                    "holdings": 0,
                    "companies": 1,
                    "departments": 1,
                    "users": 12,
                    "active_users": 11,
                    "pending_users": 1
                },
                "department": None,
                "company": None,
                "users": []
            }
        }
    )


class UserDashboardResponse(BaseModel):
    """
    Dashboard response for regular user role.

    User can see (read-only):
    - Their department details
    - Other users in their department
    - Company information (limited)
    """
    role: str = Field("user", description="User role")
    counts: DashboardCounts = Field(..., description="Aggregated counts")
    department: Optional[DepartmentSummary] = Field(None, description="User's department details")
    company: Optional[CompanySummary] = Field(None, description="User's company (limited info)")
    colleagues: List[UserSummary] = Field(
        default_factory=list,
        description="Other users in the same department"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "counts": {
                    "holdings": 0,
                    "companies": 1,
                    "departments": 1,
                    "users": 12,
                    "active_users": 11,
                    "pending_users": 0
                },
                "department": None,
                "company": None,
                "colleagues": []
            }
        }
    )


# ============================================================================
# Request Models
# ============================================================================

class DashboardStatsRequest(BaseModel):
    """
    Optional request parameters for dashboard stats.
    Currently empty, but can be extended for filtering/pagination.
    """
    include_recent: bool = Field(
        True,
        description="Include recent items (companies, departments, users)"
    )
    recent_limit: int = Field(
        10,
        ge=1,
        le=50,
        description="Limit for recent items (1-50)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "include_recent": True,
                "recent_limit": 10
            }
        }
    )
