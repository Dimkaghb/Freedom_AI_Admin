"""
Role-Based Access Control (RBAC) utilities.

This module provides helper functions for implementing role-based access control
across the application. It defines scope rules for different user roles and
provides utilities for filtering data and validating access permissions.

Roles:
- superadmin: Full access to all holdings, companies, departments, and users
- admin: Access to their company, its departments, and users
- director: Access to their department and its users
- user: Read-only access to their department data
"""

from typing import Dict, Any, Optional, List
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class UserScope:
    """Class representing user's access scope based on their role"""

    def __init__(
        self,
        role: str,
        holding_id: Optional[str] = None,
        company_id: Optional[str] = None,
        department_id: Optional[str] = None
    ):
        self.role = role
        self.holding_id = holding_id
        self.company_id = company_id
        self.department_id = department_id
        self.is_superadmin = role == "superadmin"
        self.is_admin = role == "admin"
        self.is_director = role == "director"
        self.is_user = role == "user"

    def can_access_all_holdings(self) -> bool:
        """Check if user can access all holdings"""
        return self.is_superadmin

    def can_access_holding(self, holding_id: str) -> bool:
        """Check if user can access a specific holding"""
        if self.is_superadmin:
            return True
        return self.holding_id == holding_id if self.holding_id else False

    def can_access_all_companies(self) -> bool:
        """Check if user can access all companies"""
        return self.is_superadmin

    def can_access_company(self, company_id: str) -> bool:
        """Check if user can access a specific company"""
        if self.is_superadmin:
            return True
        if self.is_admin:
            return self.company_id == company_id if self.company_id else False
        if self.is_director or self.is_user:
            return self.company_id == company_id if self.company_id else False
        return False

    def can_access_all_departments(self) -> bool:
        """Check if user can access all departments"""
        return self.is_superadmin

    def can_access_department(self, department_id: str) -> bool:
        """Check if user can access a specific department"""
        if self.is_superadmin:
            return True
        if self.is_admin:
            # Admin can access all departments in their company
            # This needs to be validated by checking if department belongs to their company
            return True  # Will be validated at query level
        if self.is_director or self.is_user:
            return self.department_id == department_id if self.department_id else False
        return False

    def can_modify_resources(self) -> bool:
        """Check if user can modify resources (not read-only)"""
        return self.role in ["superadmin", "admin", "director"]

    def get_holdings_filter(self) -> Dict[str, Any]:
        """Get MongoDB filter for holdings based on user scope"""
        if self.is_superadmin:
            return {"is_deleted": False}
        elif self.holding_id:
            return {"_id": ObjectId(self.holding_id), "is_deleted": False}
        return {"_id": None}  # No access

    def get_companies_filter(self) -> Dict[str, Any]:
        """Get MongoDB filter for companies based on user scope"""
        if self.is_superadmin:
            return {"is_deleted": False}
        elif self.is_admin and self.company_id:
            return {"_id": ObjectId(self.company_id), "is_deleted": False}
        elif (self.is_director or self.is_user) and self.company_id:
            return {"_id": ObjectId(self.company_id), "is_deleted": False}
        return {"_id": None}  # No access

    def get_departments_filter(self) -> Dict[str, Any]:
        """Get MongoDB filter for departments based on user scope"""
        if self.is_superadmin:
            return {"is_deleted": False}
        elif self.is_admin and self.company_id:
            return {"company_id": self.company_id, "is_deleted": False}
        elif (self.is_director or self.is_user) and self.department_id:
            return {"_id": ObjectId(self.department_id), "is_deleted": False}
        return {"_id": None}  # No access

    def get_users_filter(self) -> Dict[str, Any]:
        """Get MongoDB filter for users based on user scope"""
        if self.is_superadmin:
            return {}  # Access all users
        elif self.is_admin and self.company_id:
            return {"company_id": self.company_id}
        elif (self.is_director or self.is_user) and self.department_id:
            return {"department_id": self.department_id}
        return {"_id": None}  # No access


def get_user_scope(current_user: Dict[str, Any]) -> UserScope:
    """
    Determine user's access scope based on their role and organizational assignment.

    Args:
        current_user: User dict from database containing role, holding_id, company_id, department_id

    Returns:
        UserScope: Object representing user's access scope

    Example:
        >>> user = {"role": "admin", "company_id": "507f1f77bcf86cd799439011"}
        >>> scope = get_user_scope(user)
        >>> scope.can_access_all_companies()
        False
        >>> scope.can_access_company("507f1f77bcf86cd799439011")
        True
    """
    role = current_user.get("role", "user")
    holding_id = current_user.get("holding_id")
    company_id = current_user.get("company_id")
    department_id = current_user.get("department_id")

    logger.debug(
        f"Creating scope for user role={role}, "
        f"holding_id={holding_id}, company_id={company_id}, department_id={department_id}"
    )

    return UserScope(
        role=role,
        holding_id=holding_id,
        company_id=company_id,
        department_id=department_id
    )


def validate_resource_access(
    current_user: Dict[str, Any],
    resource_type: str,
    resource_id: Optional[str] = None,
    company_id: Optional[str] = None,
    department_id: Optional[str] = None
) -> bool:
    """
    Validate if user has access to a specific resource.

    Args:
        current_user: User dict from database
        resource_type: Type of resource ("holding", "company", "department", "user")
        resource_id: ID of the specific resource
        company_id: Company ID for department/user resources
        department_id: Department ID for user resources

    Returns:
        bool: True if user has access, False otherwise

    Raises:
        ValueError: If resource_type is invalid

    Example:
        >>> user = {"role": "admin", "company_id": "123"}
        >>> validate_resource_access(user, "company", resource_id="123")
        True
        >>> validate_resource_access(user, "company", resource_id="456")
        False
    """
    scope = get_user_scope(current_user)

    if resource_type == "holding":
        if resource_id:
            return scope.can_access_holding(resource_id)
        return scope.can_access_all_holdings()

    elif resource_type == "company":
        if resource_id:
            return scope.can_access_company(resource_id)
        return scope.can_access_all_companies()

    elif resource_type == "department":
        if resource_id:
            # For department access, we need to validate company ownership for admin
            if scope.is_admin and company_id:
                return scope.can_access_company(company_id)
            return scope.can_access_department(resource_id)
        return scope.can_access_all_departments()

    elif resource_type == "user":
        # User access is determined by company or department
        if scope.is_superadmin:
            return True
        if scope.is_admin and company_id:
            return scope.can_access_company(company_id)
        if (scope.is_director or scope.is_user) and department_id:
            return scope.can_access_department(department_id)
        return False

    else:
        raise ValueError(f"Invalid resource_type: {resource_type}")


def filter_list_by_scope(
    items: List[Dict[str, Any]],
    current_user: Dict[str, Any],
    resource_type: str
) -> List[Dict[str, Any]]:
    """
    Filter a list of items based on user's access scope.

    This is a secondary filter for in-memory filtering after database query.
    Primary filtering should be done at the database query level.

    Args:
        items: List of resource items (holdings, companies, departments, users)
        current_user: User dict from database
        resource_type: Type of resources in the list

    Returns:
        List of filtered items user has access to
    """
    scope = get_user_scope(current_user)

    if scope.is_superadmin:
        return items  # Superadmin sees everything

    filtered_items = []

    for item in items:
        item_id = str(item.get("_id", item.get("id", "")))

        if resource_type == "holding":
            if scope.can_access_holding(item_id):
                filtered_items.append(item)

        elif resource_type == "company":
            if scope.can_access_company(item_id):
                filtered_items.append(item)

        elif resource_type == "department":
            department_company_id = item.get("company_id")
            if scope.is_admin and scope.can_access_company(department_company_id):
                filtered_items.append(item)
            elif scope.can_access_department(item_id):
                filtered_items.append(item)

        elif resource_type == "user":
            user_company_id = item.get("company_id")
            user_department_id = item.get("department_id")

            if scope.is_admin and user_company_id and scope.can_access_company(user_company_id):
                filtered_items.append(item)
            elif user_department_id and scope.can_access_department(user_department_id):
                filtered_items.append(item)

    return filtered_items


def require_resource_access(
    current_user: Dict[str, Any],
    resource_type: str,
    resource_id: Optional[str] = None,
    company_id: Optional[str] = None,
    department_id: Optional[str] = None
) -> None:
    """
    Validate resource access and raise exception if access is denied.

    Args:
        current_user: User dict from database
        resource_type: Type of resource
        resource_id: ID of the specific resource
        company_id: Company ID for department/user resources
        department_id: Department ID for user resources

    Raises:
        PermissionError: If user doesn't have access to the resource
    """
    has_access = validate_resource_access(
        current_user=current_user,
        resource_type=resource_type,
        resource_id=resource_id,
        company_id=company_id,
        department_id=department_id
    )

    if not has_access:
        role = current_user.get("role", "unknown")
        raise PermissionError(
            f"User with role '{role}' does not have access to {resource_type} "
            f"(resource_id={resource_id}, company_id={company_id}, department_id={department_id})"
        )
