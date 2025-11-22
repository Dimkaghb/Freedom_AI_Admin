"""
Dashboard utilities for role-based data aggregation.

This module provides business logic for aggregating dashboard statistics
based on user roles. It uses MongoDB aggregation pipelines for efficient
data retrieval and applies RBAC filtering.

Performance considerations:
- Uses aggregation pipelines to minimize database round trips
- Applies filters at database level for efficiency
- Implements proper indexing requirements
- Limits result sets to prevent memory issues
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from bson.errors import InvalidId

from ..settings import settings
from ..auth.rbac import get_user_scope, UserScope
from ..database import get_database
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
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions - Data Aggregation
# ============================================================================

def _get_holdings_with_counts(scope: UserScope, limit: Optional[int] = None) -> List[HoldingSummary]:
    """
    Get holdings with company counts based on user scope.

    Args:
        scope: User's access scope
        limit: Optional limit for number of holdings

    Returns:
        List of HoldingSummary objects
    """
    try:
        db = get_database()
        holdings_collection = db[settings.HOLDINGS_COLLECTION]

        # Build filter based on scope
        holdings_filter = scope.get_holdings_filter()

        # Aggregation pipeline to get holdings with company counts
        pipeline = [
            {"$match": holdings_filter},
            {
                "$lookup": {
                    "from": settings.COMPANIES_COLLECTION,
                    "let": {"holding_id": {"$toString": "$_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$holding_id", "$$holding_id"]},
                                "is_deleted": False
                            }
                        },
                        {"$count": "count"}
                    ],
                    "as": "companies_data"
                }
            },
            {
                "$addFields": {
                    "companies_count": {
                        "$ifNull": [{"$arrayElemAt": ["$companies_data.count", 0]}, 0]
                    }
                }
            },
            {"$sort": {"created_at": -1}},
            {"$project": {
                "_id": 1,
                "name": 1,
                "description": 1,
                "companies_count": 1,
                "created_at": 1
            }}
        ]

        if limit:
            pipeline.append({"$limit": limit})

        holdings = list(holdings_collection.aggregate(pipeline))

        return [
            HoldingSummary(
                id=str(h["_id"]),
                name=h["name"],
                description=h.get("description"),
                companies_count=h.get("companies_count", 0),
                created_at=h["created_at"]
            )
            for h in holdings
        ]

    except Exception as e:
        logger.error(f"Error fetching holdings with counts: {str(e)}")
        raise


def _get_companies_with_counts(
    scope: UserScope,
    limit: Optional[int] = None,
    include_holding_name: bool = True
) -> List[CompanySummary]:
    """
    Get companies with department and user counts based on user scope.

    Args:
        scope: User's access scope
        limit: Optional limit for number of companies
        include_holding_name: Whether to include holding name

    Returns:
        List of CompanySummary objects
    """
    try:
        db = get_database()
        companies_collection = db[settings.COMPANIES_COLLECTION]

        # Build filter based on scope
        companies_filter = scope.get_companies_filter()

        # Aggregation pipeline
        pipeline = [
            {"$match": companies_filter},
            # Get departments count
            {
                "$lookup": {
                    "from": settings.DEPARTMENTS_COLLECTION,
                    "let": {"company_id": {"$toString": "$_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$company_id", "$$company_id"]},
                                "is_deleted": False
                            }
                        },
                        {"$count": "count"}
                    ],
                    "as": "departments_data"
                }
            },
            # Get users count
            {
                "$lookup": {
                    "from": settings.USERS_COLLECTION,
                    "let": {"company_id": {"$toString": "$_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$company_id", "$$company_id"]}
                            }
                        },
                        {"$count": "count"}
                    ],
                    "as": "users_data"
                }
            },
            {
                "$addFields": {
                    "departments_count": {
                        "$ifNull": [{"$arrayElemAt": ["$departments_data.count", 0]}, 0]
                    },
                    "users_count": {
                        "$ifNull": [{"$arrayElemAt": ["$users_data.count", 0]}, 0]
                    }
                }
            },
            {"$sort": {"created_at": -1}},
        ]

        # Optionally join with holdings to get holding name
        if include_holding_name:
            pipeline.extend([
                {
                    "$lookup": {
                        "from": settings.HOLDINGS_COLLECTION,
                        "let": {"holding_id": "$holding_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": [{"$toString": "$_id"}, "$$holding_id"]
                                    }
                                }
                            },
                            {"$project": {"name": 1}}
                        ],
                        "as": "holding_data"
                    }
                },
                {
                    "$addFields": {
                        "holding_name": {"$arrayElemAt": ["$holding_data.name", 0]}
                    }
                }
            ])

        pipeline.append({
            "$project": {
                "_id": 1,
                "name": 1,
                "description": 1,
                "holding_id": 1,
                "holding_name": 1,
                "departments_count": 1,
                "users_count": 1,
                "created_at": 1
            }
        })

        if limit:
            pipeline.append({"$limit": limit})

        companies = list(companies_collection.aggregate(pipeline))

        return [
            CompanySummary(
                id=str(c["_id"]),
                name=c["name"],
                description=c.get("description"),
                holding_id=c["holding_id"],
                holding_name=c.get("holding_name"),
                departments_count=c.get("departments_count", 0),
                users_count=c.get("users_count", 0),
                created_at=c["created_at"]
            )
            for c in companies
        ]

    except Exception as e:
        logger.error(f"Error fetching companies with counts: {str(e)}")
        raise


def _get_departments_with_counts(
    scope: UserScope,
    limit: Optional[int] = None,
    include_names: bool = True
) -> List[DepartmentSummary]:
    """
    Get departments with user counts and manager info based on user scope.

    Args:
        scope: User's access scope
        limit: Optional limit for number of departments
        include_names: Whether to include company and manager names

    Returns:
        List of DepartmentSummary objects
    """
    try:
        db = get_database()
        departments_collection = db[settings.DEPARTMENTS_COLLECTION]

        # Build filter based on scope
        departments_filter = scope.get_departments_filter()

        # Aggregation pipeline
        pipeline = [
            {"$match": departments_filter},
            # Get users count
            {
                "$lookup": {
                    "from": settings.USERS_COLLECTION,
                    "let": {"department_id": {"$toString": "$_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$department_id", "$$department_id"]}
                            }
                        },
                        {"$count": "count"}
                    ],
                    "as": "users_data"
                }
            },
            {
                "$addFields": {
                    "users_count": {
                        "$ifNull": [{"$arrayElemAt": ["$users_data.count", 0]}, 0]
                    }
                }
            },
            {"$sort": {"created_at": -1}},
        ]

        # Optionally join with companies and managers
        if include_names:
            pipeline.extend([
                # Get company name
                {
                    "$lookup": {
                        "from": settings.COMPANIES_COLLECTION,
                        "let": {"company_id": "$company_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": [{"$toString": "$_id"}, "$$company_id"]
                                    }
                                }
                            },
                            {"$project": {"name": 1}}
                        ],
                        "as": "company_data"
                    }
                },
                # Get manager name
                {
                    "$lookup": {
                        "from": settings.USERS_COLLECTION,
                        "let": {"manager_id": "$manager_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": [{"$toString": "$_id"}, "$$manager_id"]
                                    }
                                }
                            },
                            {
                                "$project": {
                                    "fullName": {
                                        "$concat": [
                                            {"$ifNull": ["$firstName", ""]},
                                            " ",
                                            {"$ifNull": ["$lastName", ""]}
                                        ]
                                    }
                                }
                            }
                        ],
                        "as": "manager_data"
                    }
                },
                {
                    "$addFields": {
                        "company_name": {"$arrayElemAt": ["$company_data.name", 0]},
                        "manager_name": {"$arrayElemAt": ["$manager_data.fullName", 0]}
                    }
                }
            ])

        pipeline.append({
            "$project": {
                "_id": 1,
                "name": 1,
                "description": 1,
                "company_id": 1,
                "company_name": 1,
                "manager_id": 1,
                "manager_name": 1,
                "users_count": 1,
                "created_at": 1
            }
        })

        if limit:
            pipeline.append({"$limit": limit})

        departments = list(departments_collection.aggregate(pipeline))

        return [
            DepartmentSummary(
                id=str(d["_id"]),
                name=d["name"],
                description=d.get("description"),
                company_id=d["company_id"],
                company_name=d.get("company_name"),
                manager_id=d.get("manager_id"),
                manager_name=d.get("manager_name"),
                users_count=d.get("users_count", 0),
                created_at=d["created_at"]
            )
            for d in departments
        ]

    except Exception as e:
        logger.error(f"Error fetching departments with counts: {str(e)}")
        raise


def _get_users_with_details(
    scope: UserScope,
    limit: Optional[int] = None,
    active_only: bool = False
) -> List[UserSummary]:
    """
    Get users with department and company details based on user scope.

    Args:
        scope: User's access scope
        limit: Optional limit for number of users
        active_only: Filter for active users only

    Returns:
        List of UserSummary objects
    """
    try:
        db = get_database()
        users_collection = db[settings.USERS_COLLECTION]

        # Build filter based on scope
        users_filter = scope.get_users_filter()

        if active_only:
            users_filter["is_active"] = True

        # Aggregation pipeline
        pipeline = [
            {"$match": users_filter},
            # Get department name
            {
                "$lookup": {
                    "from": settings.DEPARTMENTS_COLLECTION,
                    "let": {"department_id": "$department_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [{"$toString": "$_id"}, "$$department_id"]
                                }
                            }
                        },
                        {"$project": {"name": 1}}
                    ],
                    "as": "department_data"
                }
            },
            # Get company name
            {
                "$lookup": {
                    "from": settings.COMPANIES_COLLECTION,
                    "let": {"company_id": "$company_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [{"$toString": "$_id"}, "$$company_id"]
                                }
                            }
                        },
                        {"$project": {"name": 1}}
                    ],
                    "as": "company_data"
                }
            },
            {
                "$addFields": {
                    "department_name": {"$arrayElemAt": ["$department_data.name", 0]},
                    "company_name": {"$arrayElemAt": ["$company_data.name", 0]}
                }
            },
            {"$sort": {"created_at": -1}},
            {
                "$project": {
                    "_id": 1,
                    "email": 1,
                    "firstName": 1,
                    "lastName": 1,
                    "role": 1,
                    "is_active": 1,
                    "department_id": 1,
                    "department_name": 1,
                    "company_id": 1,
                    "company_name": 1
                }
            }
        ]

        if limit:
            pipeline.append({"$limit": limit})

        users = list(users_collection.aggregate(pipeline))

        return [
            UserSummary(
                id=str(u["_id"]),
                email=u["email"],
                firstName=u.get("firstName"),
                lastName=u.get("lastName"),
                role=u.get("role", "user"),  # Default to "user" if role is missing
                is_active=u.get("is_active", True),
                department_id=u.get("department_id"),
                department_name=u.get("department_name"),
                company_id=u.get("company_id"),
                company_name=u.get("company_name")
            )
            for u in users
        ]

    except Exception as e:
        logger.error(f"Error fetching users with details: {str(e)}")
        raise


def _get_dashboard_counts(scope: UserScope) -> DashboardCounts:
    """
    Get aggregated counts for all resources based on user scope.

    This uses efficient count queries with proper filtering.

    Args:
        scope: User's access scope

    Returns:
        DashboardCounts object with all counts
    """
    try:
        db = get_database()

        # Get counts based on scope
        holdings_count = db[settings.HOLDINGS_COLLECTION].count_documents(
            scope.get_holdings_filter()
        )

        companies_count = db[settings.COMPANIES_COLLECTION].count_documents(
            scope.get_companies_filter()
        )

        departments_count = db[settings.DEPARTMENTS_COLLECTION].count_documents(
            scope.get_departments_filter()
        )

        users_filter = scope.get_users_filter()
        users_count = db[settings.USERS_COLLECTION].count_documents(users_filter)

        active_users_filter = {**users_filter, "is_active": True}
        active_users_count = db[settings.USERS_COLLECTION].count_documents(
            active_users_filter
        )

        # Pending users - only visible to admins and superadmins
        pending_users_count = 0
        if scope.is_superadmin:
            pending_users_count = db[settings.PENDING_USERS_COLLECTION].count_documents(
                {"status": "pending"}
            )
        elif scope.is_admin and scope.company_id:
            pending_users_count = db[settings.PENDING_USERS_COLLECTION].count_documents(
                {"status": "pending", "company_id": scope.company_id}
            )

        return DashboardCounts(
            holdings=holdings_count,
            companies=companies_count,
            departments=departments_count,
            users=users_count,
            active_users=active_users_count,
            pending_users=pending_users_count
        )

    except Exception as e:
        logger.error(f"Error fetching dashboard counts: {str(e)}")
        raise


# ============================================================================
# Main Dashboard Functions - Role-Specific
# ============================================================================

def get_superadmin_dashboard(
    current_user: Dict[str, Any],
    include_recent: bool = True,
    recent_limit: int = 10
) -> SuperadminDashboardResponse:
    """
    Get dashboard data for superadmin role.

    Superadmin sees:
    - All holdings with company counts
    - Recent companies
    - Recent departments
    - Recent users
    - Full aggregated counts

    Args:
        current_user: Current user dict from database
        include_recent: Whether to include recent items
        recent_limit: Limit for recent items (1-50)

    Returns:
        SuperadminDashboardResponse with all data

    Raises:
        ValueError: If user is not superadmin
    """
    scope = get_user_scope(current_user)

    if not scope.is_superadmin:
        raise ValueError("User is not a superadmin")

    logger.info(f"Fetching superadmin dashboard for user {current_user.get('email')}")

    # Get counts
    counts = _get_dashboard_counts(scope)

    # Get all holdings
    holdings = _get_holdings_with_counts(scope)

    recent_companies = []
    recent_departments = []
    recent_users = []

    if include_recent:
        # Get recent companies
        recent_companies = _get_companies_with_counts(
            scope,
            limit=recent_limit,
            include_holding_name=True
        )

        # Get recent departments
        recent_departments = _get_departments_with_counts(
            scope,
            limit=recent_limit,
            include_names=True
        )

        # Get recent users
        recent_users = _get_users_with_details(
            scope,
            limit=recent_limit
        )

    return SuperadminDashboardResponse(
        role="superadmin",
        counts=counts,
        holdings=holdings,
        recent_companies=recent_companies,
        recent_departments=recent_departments,
        recent_users=recent_users
    )


def get_admin_dashboard(
    current_user: Dict[str, Any],
    include_recent: bool = True,
    recent_limit: int = 10
) -> AdminDashboardResponse:
    """
    Get dashboard data for admin role.

    Admin sees:
    - Their company details
    - All departments in their company
    - Recent users in their company
    - Aggregated counts for their company

    Args:
        current_user: Current user dict from database
        include_recent: Whether to include recent items
        recent_limit: Limit for recent items (1-50)

    Returns:
        AdminDashboardResponse with company data

    Raises:
        ValueError: If user is not admin or missing company_id
    """
    scope = get_user_scope(current_user)

    if not scope.is_admin:
        raise ValueError("User is not an admin")

    if not scope.company_id:
        raise ValueError("Admin user must have a company_id")

    logger.info(
        f"Fetching admin dashboard for user {current_user.get('email')} "
        f"(company_id={scope.company_id})"
    )

    # Get counts
    counts = _get_dashboard_counts(scope)

    # Get company details
    companies = _get_companies_with_counts(scope, limit=1, include_holding_name=True)
    company = companies[0] if companies else None

    # Get all departments in the company
    departments = _get_departments_with_counts(scope, include_names=True)

    recent_users = []
    if include_recent:
        # Get recent users in the company
        recent_users = _get_users_with_details(scope, limit=recent_limit)

    return AdminDashboardResponse(
        role="admin",
        counts=counts,
        company=company,
        departments=departments,
        recent_users=recent_users
    )


def get_director_dashboard(
    current_user: Dict[str, Any]
) -> DirectorDashboardResponse:
    """
    Get dashboard data for director role.

    Director sees:
    - Their department details
    - Parent company info (limited)
    - All users in their department
    - Aggregated counts for their department

    Args:
        current_user: Current user dict from database

    Returns:
        DirectorDashboardResponse with department data

    Raises:
        ValueError: If user is not director or missing department_id
    """
    scope = get_user_scope(current_user)

    if not scope.is_director:
        raise ValueError("User is not a director")

    if not scope.department_id:
        raise ValueError("Director user must have a department_id")

    logger.info(
        f"Fetching director dashboard for user {current_user.get('email')} "
        f"(department_id={scope.department_id})"
    )

    # Get counts
    counts = _get_dashboard_counts(scope)

    # Get department details
    departments = _get_departments_with_counts(scope, limit=1, include_names=True)
    department = departments[0] if departments else None

    # Get company details (limited info)
    company = None
    if scope.company_id:
        companies = _get_companies_with_counts(
            scope,
            limit=1,
            include_holding_name=False
        )
        company = companies[0] if companies else None

    # Get all users in the department
    users = _get_users_with_details(scope)

    return DirectorDashboardResponse(
        role="director",
        counts=counts,
        department=department,
        company=company,
        users=users
    )


def get_user_dashboard(
    current_user: Dict[str, Any]
) -> UserDashboardResponse:
    """
    Get dashboard data for regular user role.

    User sees (read-only):
    - Their department details
    - Parent company info (limited)
    - Colleagues in their department
    - Aggregated counts for their department

    Args:
        current_user: Current user dict from database

    Returns:
        UserDashboardResponse with department data

    Raises:
        ValueError: If user is missing department_id
    """
    scope = get_user_scope(current_user)

    if not scope.department_id:
        raise ValueError("User must have a department_id")

    logger.info(
        f"Fetching user dashboard for user {current_user.get('email')} "
        f"(department_id={scope.department_id})"
    )

    # Get counts
    counts = _get_dashboard_counts(scope)

    # Get department details
    departments = _get_departments_with_counts(scope, limit=1, include_names=True)
    department = departments[0] if departments else None

    # Get company details (limited info)
    company = None
    if scope.company_id:
        companies = _get_companies_with_counts(
            scope,
            limit=1,
            include_holding_name=False
        )
        company = companies[0] if companies else None

    # Get colleagues in the department
    colleagues = _get_users_with_details(scope)

    return UserDashboardResponse(
        role="user",
        counts=counts,
        department=department,
        company=company,
        colleagues=colleagues
    )


# ============================================================================
# Main Entry Point - Role-Based Dispatcher
# ============================================================================

def get_dashboard_stats(
    current_user: Dict[str, Any],
    include_recent: bool = True,
    recent_limit: int = 10
) -> Union[
    SuperadminDashboardResponse,
    AdminDashboardResponse,
    DirectorDashboardResponse,
    UserDashboardResponse
]:
    """
    Get dashboard statistics based on user role.

    This is the main entry point that dispatches to role-specific functions.

    Args:
        current_user: Current user dict from database
        include_recent: Whether to include recent items (for superadmin/admin)
        recent_limit: Limit for recent items (1-50)

    Returns:
        Role-specific dashboard response

    Raises:
        ValueError: If user role is invalid or missing required fields
        ConnectionFailure: If database connection fails

    Example:
        >>> user = {"role": "admin", "company_id": "123", "email": "admin@example.com"}
        >>> dashboard = get_dashboard_stats(user)
        >>> print(dashboard.counts.users)
        45
    """
    role = current_user.get("role", "").lower()

    logger.info(f"Getting dashboard stats for user {current_user.get('email')} with role {role}")

    try:
        if role == "superadmin":
            return get_superadmin_dashboard(current_user, include_recent, recent_limit)
        elif role == "admin":
            return get_admin_dashboard(current_user, include_recent, recent_limit)
        elif role == "director":
            return get_director_dashboard(current_user)
        elif role == "user":
            return get_user_dashboard(current_user)
        else:
            raise ValueError(f"Invalid user role: {role}")

    except ValueError as e:
        logger.error(f"Validation error in get_dashboard_stats: {str(e)}")
        raise
    except ConnectionFailure as e:
        logger.error(f"Database connection error in get_dashboard_stats: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_dashboard_stats: {str(e)}")
        raise
