"""
Dashboard API endpoints for role-based data aggregation.

This module provides REST API endpoints for fetching dashboard statistics
and summaries based on user roles. All endpoints are protected and require
authentication.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure
from typing import Union
import logging

from .models import (
    SuperadminDashboardResponse,
    AdminDashboardResponse,
    DirectorDashboardResponse,
    UserDashboardResponse,
)
from .utils import get_dashboard_stats
from ..auth.dependencies import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router for dashboard endpoints
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/stats",
    response_model=Union[
        SuperadminDashboardResponse,
        AdminDashboardResponse,
        DirectorDashboardResponse,
        UserDashboardResponse
    ],
    status_code=status.HTTP_200_OK,
    summary="Get role-based dashboard statistics",
    description="""
    Get dashboard statistics and summaries based on user role.

    **Role-based responses:**

    - **Superadmin**: All holdings, recent companies, departments, and users
    - **Admin**: Their company, all departments, and recent users in the company
    - **Director**: Their department, company info, and all department users
    - **User**: Their department, company info, and colleagues (read-only)

    **Authentication required**: Bearer token in Authorization header

    **Rate limiting**: Recommended to cache results for 5-10 minutes on client side
    """,
    responses={
        200: {
            "description": "Dashboard statistics retrieved successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "superadmin": {
                            "summary": "Superadmin Response",
                            "value": {
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
                        },
                        "admin": {
                            "summary": "Admin Response",
                            "value": {
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
                        },
                        "director": {
                            "summary": "Director Response",
                            "value": {
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
                        },
                        "user": {
                            "summary": "User Response",
                            "value": {
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
                    }
                }
            }
        },
        401: {
            "description": "Not authenticated or invalid token",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            }
        },
        403: {
            "description": "User is inactive or lacks required permissions",
            "content": {
                "application/json": {
                    "example": {"detail": "Inactive user"}
                }
            }
        },
        400: {
            "description": "Invalid request or user missing required fields",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_company": {
                            "summary": "Admin without company_id",
                            "value": {"detail": "Admin user must have a company_id"}
                        },
                        "missing_department": {
                            "summary": "Director without department_id",
                            "value": {"detail": "Director user must have a department_id"}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error or database connection failure",
            "content": {
                "application/json": {
                    "example": {"detail": "Database connection error. Please try again later."}
                }
            }
        }
    }
)
async def get_dashboard_stats_endpoint(
    include_recent: bool = Query(
        True,
        description="Include recent items (companies, departments, users). Only applies to superadmin and admin roles."
    ),
    recent_limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Limit for recent items (1-50). Only applies when include_recent=true."
    ),
    current_user: dict = Depends(get_current_user)
):
    """
    Get dashboard statistics based on authenticated user's role.

    This endpoint automatically detects the user's role and returns
    appropriate dashboard data with proper access control.

    **Query Parameters:**
    - `include_recent`: Include recent items (default: true)
    - `recent_limit`: Number of recent items to return (default: 10, max: 50)

    **Authorization:**
    Requires valid JWT token in Authorization header:
    ```
    Authorization: Bearer <access_token>
    ```

    **Performance:**
    - Uses MongoDB aggregation pipelines for efficiency
    - Typical response time: 100-300ms
    - Recommend client-side caching for 5-10 minutes

    **Example Request:**
    ```bash
    curl -X GET "http://localhost:8000/dashboard/stats?include_recent=true&recent_limit=10" \
         -H "Authorization: Bearer <token>"
    ```

    **Example Response (Admin):**
    ```json
    {
      "role": "admin",
      "counts": {
        "holdings": 0,
        "companies": 1,
        "departments": 8,
        "users": 45,
        "active_users": 42,
        "pending_users": 2
      },
      "company": {
        "id": "507f1f77bcf86cd799439012",
        "name": "TechCorp Inc",
        "description": "Technology company",
        "holding_id": "507f1f77bcf86cd799439011",
        "holding_name": "Global Holdings Inc",
        "departments_count": 8,
        "users_count": 45,
        "created_at": "2024-01-01T00:00:00"
      },
      "departments": [...],
      "recent_users": [...]
    }
    ```
    """
    try:
        # Log the request
        user_email = current_user.get("email", "unknown")
        user_role = current_user.get("role", "unknown")
        logger.info(
            f"Dashboard stats requested by user {user_email} (role: {user_role})"
        )

        # Validate recent_limit
        if recent_limit < 1 or recent_limit > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="recent_limit must be between 1 and 50"
            )

        # Get dashboard statistics based on user role
        dashboard_data = get_dashboard_stats(
            current_user=current_user,
            include_recent=include_recent,
            recent_limit=recent_limit
        )

        # Log successful response
        logger.info(
            f"Dashboard stats retrieved successfully for user {user_email} "
            f"(holdings={dashboard_data.counts.holdings}, "
            f"companies={dashboard_data.counts.companies}, "
            f"departments={dashboard_data.counts.departments}, "
            f"users={dashboard_data.counts.users})"
        )

        return dashboard_data

    except ValueError as e:
        # Handle validation errors (invalid role, missing fields, etc.)
        error_message = str(e)
        logger.warning(f"Dashboard stats validation error: {error_message}")

        # Check for specific error types
        if "must have a company_id" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        elif "must have a department_id" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        elif "Invalid user role" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        else:
            # Generic validation error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation error: {error_message}"
            )

    except ConnectionFailure as e:
        # Handle database connection errors
        logger.error(f"Database connection error during dashboard stats retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during dashboard stats retrieval: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for the dashboard service.

    Returns basic service status without requiring authentication.
    Useful for monitoring and load balancer health checks.

    **Example Response:**
    ```json
    {
      "status": "healthy",
      "service": "dashboard",
      "message": "Dashboard service is running"
    }
    ```
    """
    return {
        "status": "healthy",
        "service": "dashboard",
        "message": "Dashboard service is running"
    }


# Optional: Endpoint to get counts only (faster, no detailed data)
@router.get(
    "/counts",
    status_code=status.HTTP_200_OK,
    summary="Get dashboard counts only (lightweight)",
    description="""
    Get only the aggregated counts without detailed data.
    This is a faster endpoint for displaying quick stats.

    Returns holdings, companies, departments, users, active users, and pending users counts
    based on user role and access permissions.
    """
)
async def get_dashboard_counts_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """
    Get dashboard counts only without detailed data.

    This is a lightweight alternative to /stats endpoint that returns
    only aggregated counts. Useful for quick stats display or mobile apps.

    **Response is faster** because it doesn't fetch detailed lists.

    **Example Response:**
    ```json
    {
      "role": "admin",
      "holdings": 0,
      "companies": 1,
      "departments": 8,
      "users": 45,
      "active_users": 42,
      "pending_users": 2
    }
    ```
    """
    try:
        user_email = current_user.get("email", "unknown")
        user_role = current_user.get("role", "unknown")

        logger.info(f"Dashboard counts requested by user {user_email} (role: {user_role})")

        # Get full dashboard data (which includes counts)
        # In production, you might want to optimize this to only fetch counts
        dashboard_data = get_dashboard_stats(
            current_user=current_user,
            include_recent=False,  # Don't fetch recent items
            recent_limit=1
        )

        # Return only counts
        return {
            "role": user_role,
            **dashboard_data.counts.model_dump()
        }

    except ValueError as e:
        logger.warning(f"Dashboard counts validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ConnectionFailure as e:
        logger.error(f"Database connection error during dashboard counts retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error during dashboard counts retrieval: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support."
        )
