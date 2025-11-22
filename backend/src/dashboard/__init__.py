"""
Dashboard module for role-based data aggregation and statistics.

This module provides dashboard functionality with role-based access control,
ensuring users only see data they have permission to access.
"""

from .models import (
    HoldingSummary,
    CompanySummary,
    DepartmentSummary,
    UserSummary,
    DashboardCounts,
    SuperadminDashboardResponse,
    AdminDashboardResponse,
    DirectorDashboardResponse,
    UserDashboardResponse,
    DashboardStatsRequest,
)

from .utils import (
    get_dashboard_stats,
    get_superadmin_dashboard,
    get_admin_dashboard,
    get_director_dashboard,
    get_user_dashboard,
)

from .api import router

__all__ = [
    # Models
    "HoldingSummary",
    "CompanySummary",
    "DepartmentSummary",
    "UserSummary",
    "DashboardCounts",
    "SuperadminDashboardResponse",
    "AdminDashboardResponse",
    "DirectorDashboardResponse",
    "UserDashboardResponse",
    "DashboardStatsRequest",
    # Utils
    "get_dashboard_stats",
    "get_superadmin_dashboard",
    "get_admin_dashboard",
    "get_director_dashboard",
    "get_user_dashboard",
    # API
    "router",
]
