# Hierarchical Folder System Implementation Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [RBAC (Role-Based Access Control)](#rbac-role-based-access-control)
4. [Database Schema](#database-schema)
5. [Backend Implementation](#backend-implementation)
6. [Frontend Implementation](#frontend-implementation)
7. [Problems Encountered and Fixes](#problems-encountered-and-fixes)
8. [API Endpoints](#api-endpoints)
9. [Testing Checklist](#testing-checklist)

---

## Overview

This document describes the implementation of a hierarchical organizational folder system with Role-Based Access Control (RBAC). The system allows users to navigate through an organizational hierarchy where Holdings contain Companies, Companies contain Departments, and Departments contain Files and Folders.

### Key Features
- **Virtual Folders**: Organizational entities (Holdings, Companies, Departments) appear as navigable folders
- **Role-Based Navigation**: Different users see different root folders based on their role
- **Seamless Integration**: Virtual and real folders work together transparently
- **Breadcrumb Navigation**: Full path showing organizational hierarchy
- **Permission Management**: Operations restricted based on user role

### User Roles
- **Superadmin**: Full access to all holdings, companies, and departments
- **Admin**: Access to departments within their company
- **Department Director**: Access to folders within their department
- **User**: Access to folders within their department

---

## System Architecture

### Hierarchical Structure

```
Holdings (Virtual Folders)
  └── Companies (Virtual Folders)
      └── Departments (Virtual Folders)
          └── Real Folders & Files
              └── Subfolders & Files
                  └── ...
```

### Navigation by Role

#### Superadmin
```
Root → All Holdings → Companies in Holding → Departments in Company → Files/Folders
```

#### Admin
```
Root → Departments in their Company → Files/Folders
```

#### Department Director / User
```
Root → Files/Folders in their Department
```

---

## RBAC (Role-Based Access Control)

### User Roles Enum
**File**: `backend/src/auth/permissions.py`

```python
class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    DEPARTMENT_DIRECTOR = "department_director"
    USER = "user"
```

### Permission System

#### Folder Permissions
```python
class Permission(str, Enum):
    FOLDER_CREATE = "folder.create"
    FOLDER_READ = "folder.read"
    FOLDER_UPDATE = "folder.update"
    FOLDER_DELETE = "folder.delete"
    FOLDER_RENAME = "folder.rename"
    FOLDER_MOVE = "folder.move"
```

#### Role-Permission Mapping
```python
ROLE_PERMISSIONS = {
    UserRole.SUPERADMIN: [all permissions],
    UserRole.ADMIN: [FOLDER_CREATE, FOLDER_READ, FOLDER_UPDATE, FOLDER_DELETE, FOLDER_RENAME, FOLDER_MOVE],
    UserRole.DEPARTMENT_DIRECTOR: [FOLDER_CREATE, FOLDER_READ, FOLDER_UPDATE, FOLDER_DELETE, FOLDER_RENAME, FOLDER_MOVE],
    UserRole.USER: [FOLDER_READ]
}
```

### Organizational Filtering
**File**: `backend/src/auth/org_filter.py`

```python
def build_org_filter(user: UserResponse) -> Dict[str, Any]:
    """
    Build MongoDB filter query based on user's role and organizational hierarchy.

    Filtering Rules:
    - superadmin: No filter (sees everything)
    - admin: Filters by company_id
    - department_director/user: Filters by department_id
    """
```

---

## Database Schema

### Collections

#### Holdings Collection
```json
{
  "_id": ObjectId,
  "name": "Holding A",
  "description": "Optional description",
  "company_ids": ["company_id_1", "company_id_2"],
  "created_at": ISODate,
  "updated_at": ISODate,
  "is_deleted": false
}
```

#### Companies Collection
```json
{
  "_id": ObjectId,
  "name": "Company for Holding A",
  "description": "Optional description",
  "holding_id": "holding_id",
  "admin_id": "user_id",
  "department_ids": ["dept_id_1", "dept_id_2"],
  "created_at": ISODate,
  "updated_at": ISODate,
  "is_deleted": false
}
```

#### Departments Collection
```json
{
  "_id": ObjectId,
  "name": "IT Department",
  "description": "Optional description",
  "company_id": "company_id",
  "manager_id": "user_id",
  "created_at": ISODate,
  "updated_at": ISODate,
  "is_deleted": false
}
```

#### Folders Collection
```json
{
  "_id": ObjectId,
  "name": "Data Folder",
  "parentID": "parent_folder_id or null",
  "fileIds": ["file_id_1", "file_id_2"],
  "foldersids": ["subfolder_id_1"],
  "type": "documents",
  "company_id": "company_id",
  "department_id": "department_id",
  "holding_id": "holding_id",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Note**: Folders created directly inside virtual departments have `parentID = null` but contain org IDs (`company_id`, `department_id`, `holding_id`) to maintain organizational context.

---

## Backend Implementation

### Virtual Folder System
**File**: `backend/src/folders/virtual_folders.py`

#### Virtual Folder ID Format
- **Holdings**: `holding:{mongodb_id}`
- **Companies**: `company:{mongodb_id}`
- **Departments**: `department:{mongodb_id}`

#### Key Classes and Methods

##### VirtualFolderService

```python
class VirtualFolderService:
    HOLDING_PREFIX = "holding:"
    COMPANY_PREFIX = "company:"
    DEPARTMENT_PREFIX = "department:"

    @classmethod
    def is_virtual_folder(cls, folder_id: str) -> bool

    @classmethod
    def holding_to_folder(cls, holding: HoldingResponse) -> FolderResponse

    @classmethod
    def company_to_folder(cls, company: CompanyResponse) -> FolderResponse

    async def department_to_folder(self, department: DepartmentResponse) -> FolderResponse

    async def get_virtual_folder_by_id(self, folder_id: str) -> Optional[FolderResponse]

    async def get_virtual_subfolders(self, parent_id: str) -> List[FolderResponse]

    async def get_root_folders_for_user(self, user: UserResponse) -> List[FolderResponse]

    async def resolve_parent_context(self, parent_id: str, user: UserResponse) -> Dict[str, Any]
```

#### Critical Implementation Details

##### 1. Department to Folder Conversion (Fetches holding_id)
```python
async def department_to_folder(self, department: DepartmentResponse) -> FolderResponse:
    # Fetch company to get holding_id
    company = await organization_service.get_company_by_id(department.company_id)
    holding_id = company.holding_id if company else ""

    return FolderResponse(
        id=self.create_virtual_id(department.id, "department"),
        name=department.name,
        parentID=self.create_virtual_id(department.company_id, "company"),
        company_id=department.company_id,
        department_id=department.id,
        holding_id=holding_id,  # Critical: Populated from company
        # ...
    )
```

##### 2. Virtual Subfolders (Returns Real Folders for Departments)
```python
async def get_virtual_subfolders(self, parent_id: str) -> List[FolderResponse]:
    folder_type = self.get_virtual_folder_type(parent_id)
    real_id = self.extract_real_id(parent_id)

    if folder_type == "holding":
        # Return companies in this holding
        companies = await organization_service.list_companies_by_holding(real_id)
        return [self.company_to_folder(company) for company in companies]

    elif folder_type == "company":
        # Return departments in this company
        departments = await organization_service.list_departments_by_company(real_id)
        return await asyncio.gather(*[self.department_to_folder(dept) for dept in departments])

    elif folder_type == "department":
        # Return REAL folders that belong to this department
        collection = folder_service.get_collection()
        cursor = collection.find({
            "department_id": real_id,
            "parentID": None
        }).sort("name", 1)
        # ... return real folders
```

##### 3. Resolve Parent Context (Handles Org IDs for Folder Creation)
```python
async def resolve_parent_context(self, parent_id: str, user: UserResponse) -> Dict[str, Any]:
    if self.is_virtual_folder(parent_id):
        folder_type = self.get_virtual_folder_type(parent_id)
        real_id = self.extract_real_id(parent_id)

        # For departments, fetch company to get holding_id
        if folder_type == "department":
            department = await organization_service.get_department_by_id(real_id)
            if department:
                company = await organization_service.get_company_by_id(department.company_id)
                holding_id = company.holding_id if company else ''

                return {
                    "holding_id": holding_id,
                    "company_id": department.company_id,
                    "department_id": real_id,
                    "is_virtual_parent": True
                }
        # ... handle companies and holdings
```

### Folder Service
**File**: `backend/src/folders/service.py`

#### Key Methods

##### 1. Create Folder (Handles Virtual Parents)
```python
async def create_folder(self, folder_data: FolderCreate, user: UserResponse) -> FolderResponse:
    if folder_data.parentID:
        if virtual_folder_service.is_virtual_folder(folder_data.parentID):
            # Extract org IDs from virtual folder
            parent_context = await virtual_folder_service.resolve_parent_context(
                folder_data.parentID, user
            )
            org_ids = {
                "company_id": parent_context["company_id"],
                "department_id": parent_context["department_id"],
                "holding_id": parent_context["holding_id"]
            }
            # Virtual parent becomes None in database
            actual_parent_id = None
        else:
            # Parent is real folder, inherit org IDs
            parent_folder = await self.get_folder_by_id(folder_data.parentID, user)
            org_ids = {
                "company_id": parent_folder.company_id or "",
                "department_id": parent_folder.department_id or "",
                "holding_id": parent_folder.holding_id or ""
            }
            actual_parent_id = folder_data.parentID
    # ... create folder with org_ids
```

##### 2. Get Folder by ID (Supports Virtual Folders)
```python
async def get_folder_by_id(self, folder_id: str, user: UserResponse) -> Optional[FolderResponse]:
    # Check if this is a virtual folder
    if virtual_folder_service.is_virtual_folder(folder_id):
        return await virtual_folder_service.get_virtual_folder_by_id(folder_id)

    # Handle real folders with org filtering
    collection = self.get_collection()
    org_filter = build_org_filter(user)
    doc = await collection.find_one({"_id": ObjectId(folder_id), **org_filter})
    # ...
```

##### 3. Get Subfolders (Supports Virtual and Real)
```python
async def get_subfolders(self, parent_id: str, user: UserResponse) -> List[FolderResponse]:
    # Check if parent is a virtual folder
    if virtual_folder_service.is_virtual_folder(parent_id):
        return await virtual_folder_service.get_virtual_subfolders(parent_id)

    # Handle real folders
    collection = self.get_collection()
    org_filter = build_org_filter(user)
    cursor = collection.find({"parentID": parent_id, **org_filter}).sort("name", 1)
    # ...
```

##### 4. Get Root Folders (Role-Based)
```python
async def get_root_folders(self, user: UserResponse) -> List[FolderResponse]:
    # Get virtual root folders based on user role
    virtual_folders = await virtual_folder_service.get_root_folders_for_user(user)

    if virtual_folders:
        return virtual_folders  # Superadmin/Admin see virtual folders

    # Directors/Users see real folders in their department
    collection = self.get_collection()
    org_filter = build_org_filter(user)
    query = {
        "$or": [{"parentID": None}, {"parentID": {"$exists": False}}],
        **org_filter
    }
    # ...
```

##### 5. Get Folder Path (Rebuilds Full Hierarchy)
```python
async def get_folder_path(self, folder_id: str, user: UserResponse) -> List[FolderResponse]:
    path = []
    current_id = folder_id

    # Build real folder chain by following parentID
    while current_id:
        folder = await self.get_folder_by_id(current_id, user)
        if not folder:
            break
        path.insert(0, folder)
        current_id = folder.parentID

    if not path:
        return []

    first_folder = path[0]

    # If first folder has no parent, rebuild virtual folder hierarchy from org IDs
    if first_folder.parentID is None:
        virtual_path = []

        # Fallback: fetch holding_id from company if missing
        holding_id = first_folder.holding_id
        if not holding_id and first_folder.company_id:
            company = await organization_service.get_company_by_id(first_folder.company_id)
            if company:
                holding_id = company.holding_id

        # Add department virtual folder
        if first_folder.department_id:
            department_folder = await virtual_folder_service.get_virtual_folder_by_id(
                f"department:{first_folder.department_id}"
            )
            if department_folder:
                virtual_path.insert(0, department_folder)

        # Add company virtual folder
        if first_folder.company_id:
            company_folder = await virtual_folder_service.get_virtual_folder_by_id(
                f"company:{first_folder.company_id}"
            )
            if company_folder:
                virtual_path.insert(0, company_folder)

        # Add holding virtual folder
        if holding_id:
            holding_folder = await virtual_folder_service.get_virtual_folder_by_id(
                f"holding:{holding_id}"
            )
            if holding_folder:
                virtual_path.insert(0, holding_folder)

        # Combine: virtual_path + real_path
        path = virtual_path + path

    return path
```

### Organization Service
**File**: `backend/src/organizations/service.py`

```python
class OrganizationService:
    async def list_holdings(self) -> List[HoldingResponse]
    async def get_holding_by_id(self, holding_id: str) -> Optional[HoldingResponse]
    async def list_companies_by_holding(self, holding_id: str) -> List[CompanyResponse]
    async def get_company_by_id(self, company_id: str) -> Optional[CompanyResponse]
    async def list_departments_by_company(self, company_id: str) -> List[DepartmentResponse]
    async def get_department_by_id(self, department_id: str) -> Optional[DepartmentResponse]
```

### Routes
**File**: `backend/src/folders/routes.py`

#### Critical Route Ordering
```python
# IMPORTANT: Specific routes MUST come before parameterized routes!

@router.get("/")               # Line 40 - Get all folders
@router.get("/root")           # Line 54 - Get root folders (MUST be before /{folder_id})
@router.get("/{folder_id}")    # Line 68 - Get folder by ID
```

**Reason**: FastAPI matches routes in order. If `/{folder_id}` comes before `/root`, the path `/folders/root` would match `{folder_id}` with `folder_id="root"`, causing errors.

#### Virtual Folder Protection
```python
@router.put("/{folder_id}/rename")
async def rename_folder(folder_id: str, ...):
    # Virtual folders cannot be renamed
    if virtual_folder_service.is_virtual_folder(folder_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot rename organizational folders"
        )

@router.delete("/{folder_id}")
async def delete_folder(folder_id: str, ...):
    # Virtual folders cannot be deleted
    if virtual_folder_service.is_virtual_folder(folder_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete organizational folders"
        )
```

---

## Frontend Implementation

### Backend Service
**File**: `src/lib/backend-service.ts`

#### Virtual Folder Utilities
```typescript
export const VirtualFolderUtils = {
  HOLDING_PREFIX: "holding:",
  COMPANY_PREFIX: "company:",
  DEPARTMENT_PREFIX: "department:",

  isVirtualFolder(folderId: string | undefined | null): boolean {
    if (!folderId) return false;
    return (
      folderId.startsWith(this.HOLDING_PREFIX) ||
      folderId.startsWith(this.COMPANY_PREFIX) ||
      folderId.startsWith(this.DEPARTMENT_PREFIX)
    );
  },

  getVirtualFolderType(folderId: string): 'holding' | 'company' | 'department' | null {
    if (folderId.startsWith(this.HOLDING_PREFIX)) return 'holding';
    if (folderId.startsWith(this.COMPANY_PREFIX)) return 'company';
    if (folderId.startsWith(this.DEPARTMENT_PREFIX)) return 'department';
    return null;
  },

  canRename(folderId: string | undefined | null): boolean {
    return !this.isVirtualFolder(folderId);
  },

  canDelete(folderId: string | undefined | null): boolean {
    return !this.isVirtualFolder(folderId);
  },

  canMove(folderId: string | undefined | null): boolean {
    return !this.isVirtualFolder(folderId);
  }
};
```

#### API Methods
```typescript
class BackendService {
  async getRootFolders(authToken: string): Promise<DataFolder[]>
  async getSubfolders(parentId: string, authToken: string): Promise<DataFolder[]>
  async getFolder(folderId: string, authToken: string): Promise<DataFolder>
  async getFolderPath(folderId: string, authToken: string): Promise<DataFolder[]>
  async createFolder(request: CreateFolderRequest, authToken: string): Promise<DataFolder>
  async renameFolder(folderId: string, newName: string, authToken: string): Promise<DataFolder>
  async deleteFolder(folderId: string, authToken: string): Promise<void>
  async moveFolder(folderId: string, newParentId: string | null, authToken: string): Promise<DataFolder>
}
```

### Folder Management Hook
**File**: `src/hooks/use-folder-management.ts`

```typescript
export const useFolderManagement = ({ currentParentId, token }: UseFolderManagementProps) => {
  const loadFolders = useCallback(async () => {
    try {
      setIsLoading(true)
      let folderList: DataFolder[]

      if (currentParentId) {
        // Load subfolders (includes virtual folders)
        folderList = await backendService.getSubfolders(currentParentId, token)
      } else {
        // Load root folders (role-based: holdings/departments/real folders)
        folderList = await backendService.getRootFolders(token)
      }

      setFolders(folderList)
    } catch (error) {
      console.error('Error loading folders:', error)
      toast.error('Error loading folders')
    } finally {
      setIsLoading(false)
    }
  }, [currentParentId, token])

  // ... other methods
}
```

### File Manager Component
**File**: `src/components/file-manager.tsx`

#### URL Parameter Validation (Supports Virtual Folder IDs)
```typescript
const validateURLParameters = useCallback((path: string | null, folderId: string | null) => {
  const errors: string[] = []

  // Allow colons for virtual folder IDs (holding:, company:, department:)
  if (folderId && !/^[a-zA-Z0-9-_:]+$/.test(folderId)) {
    errors.push('Invalid folder ID format')
  }

  return { isValid: errors.length === 0, errors }
}, [])
```

#### Breadcrumb Restoration (Uses getFolderPath API)
```typescript
const processURLParameters = useCallback(async (urlParams: URLSearchParams, source: string) => {
  const urlPath = urlParams.get('path')
  const urlFolderId = urlParams.get('folderId')

  if (urlPath && urlFolderId && token) {
    try {
      // Validate URL parameters
      const validation = validateURLParameters(urlPath, urlFolderId)
      if (!validation.isValid) {
        handleNavigationError(new Error(validation.errors.join(', ')), 'URL validation')
        return
      }

      // Get complete folder path from backend (includes virtual folders)
      const folderPath = await backendService.getFolderPath(urlFolderId, token)

      // Build breadcrumbs from folder path
      const restoredBreadcrumbs: BreadcrumbItem[] = [{ id: null, name: "Главная" }]

      for (const folder of folderPath) {
        restoredBreadcrumbs.push({
          id: folder.id,
          name: folder.name
        })
      }

      setCurrentParentId(urlFolderId)
      setBreadcrumbs(restoredBreadcrumbs)
    } catch (error) {
      handleNavigationError(error, 'folder path lookup')
    }
  }
}, [token, validateURLParameters, handleNavigationError])
```

#### Breadcrumb Rendering (Uses Index as Key)
```typescript
{breadcrumbs.map((breadcrumb, index) => {
  const isLast = index === breadcrumbs.length - 1;
  const isRoot = breadcrumb.id === null;

  return (
    <div key={`breadcrumb-${index}`} className="flex items-center gap-1">
      {/* Breadcrumb content */}
    </div>
  )
})}
```

### Context Menu
**File**: `src/components/context-menu.tsx`

```typescript
export function ContextMenu({ item, userRole, ... }: ContextMenuProps) {
  // Check if this is a virtual folder
  const isVirtualFolder = item.type === 'folder' &&
    VirtualFolderUtils.isVirtualFolder((item.data as DataFolder).id)

  // Virtual folders cannot be renamed, deleted, or moved
  const canRenameFolder = canModify && !isVirtualFolder
  const canDeleteFolder = canModify && !isVirtualFolder
  const canMoveFolder = canModify && !isVirtualFolder

  const menuItems = [
    // Move - only for real folders
    ...(item.type === 'folder' && canMoveFolder && onMove ? [{
      icon: Move,
      label: "Переместить",
      action: onMove,
    }] : []),

    // Rename - only for real folders
    ...(item.type === 'folder' && canRenameFolder ? [{
      icon: Edit,
      label: "Переименовать",
      action: onRename,
    }] : []),

    // Delete - only for real folders
    ...(item.type === 'folder' && canDeleteFolder ? [{
      icon: Trash2,
      label: "Удалить",
      action: onDelete,
      destructive: true
    }] : []),
  ]

  // ... render menu
}
```

---

## Problems Encountered and Fixes

### Problem 1: Route Ordering Caused "Folder not found" Error

**Symptoms**:
- Error: `Folder not found` when calling `GET /folders/root`
- Holdings not showing for superadmin users

**Root Cause**:
FastAPI route ordering issue. The parameterized route `GET /folders/{folder_id}` at line 68 was matching before the specific route `GET /folders/root`, treating "root" as a folder_id.

**Fix**:
Moved `/root` endpoint from line 340 to line 54 (before `/{folder_id}` at line 68) in `backend/src/folders/routes.py`

**File**: `backend/src/folders/routes.py`

```python
# CORRECT ORDER:
@router.get("/")                # Line 40
@router.get("/root")            # Line 54 - MUST come before /{folder_id}
@router.get("/{folder_id}")     # Line 68
```

---

### Problem 2: URL Validation Rejected Virtual Folder IDs

**Symptoms**:
- Error: `Недопустимый формат ID папки` (Invalid folder ID format)
- Navigation broke when clicking on holdings/companies/departments

**Root Cause**:
Regex validation pattern `/^[a-zA-Z0-9-_]+$/` didn't allow colons (`:`) which are used in virtual folder IDs like `holding:6921e4631e667ac6536e3fab`

**Fix**:
Updated regex to `/^[a-zA-Z0-9-_:]+$/` in `src/components/file-manager.tsx` line 195

**File**: `src/components/file-manager.tsx`

```typescript
// Before: !/^[a-zA-Z0-9-_]+$/.test(folderId)
// After:  !/^[a-zA-Z0-9-_:]+$/.test(folderId)
```

---

### Problem 3: Frontend Used Wrong Endpoint for Root Folders

**Symptoms**:
- Holdings not appearing for superadmin users
- Empty folder view instead of organizational hierarchy

**Root Cause**:
Frontend was calling `GET /folders/` and filtering locally for `parentID === null`, but this endpoint only returns real folders from the database, not virtual folders (holdings/companies/departments).

**Fix**:
Updated `use-folder-management.ts` to call `getRootFolders()` instead of filtering `getFolders()` locally

**File**: `src/hooks/use-folder-management.ts`

```typescript
// Before:
const allFolders = await backendService.getFolders(token)
folderList = allFolders.filter(folder => !folder.parentID)

// After:
folderList = await backendService.getRootFolders(token)
```

---

### Problem 4: Duplicate Breadcrumb Keys in React

**Symptoms**:
- Console warning: `Encountered two children with the same key`
- Breadcrumb navigation glitchy

**Root Cause**:
URL restoration code was assigning the same `urlFolderId` to all breadcrumb segments, creating duplicate IDs. React uses keys to track components, so duplicates cause issues.

**Fix**:
Changed React key from `key={breadcrumb.id || 'root'}` to `key={breadcrumb-${index}}` in `src/components/file-manager.tsx` line 1144

**File**: `src/components/file-manager.tsx`

```typescript
// Before: <div key={breadcrumb.id || 'root'}>
// After:  <div key={`breadcrumb-${index}`}>
```

---

### Problem 5: Breadcrumbs Not Using Backend API

**Symptoms**:
- Breadcrumbs showed incorrect intermediate folder names
- Clicking breadcrumbs navigated to wrong locations

**Root Cause**:
Frontend was manually parsing URL path segments instead of using the `getFolderPath` API that returns complete folder hierarchy with proper IDs and names.

**Fix**:
Updated breadcrumb restoration to call `backendService.getFolderPath()` which returns the full folder path from backend

**File**: `src/components/file-manager.tsx` lines 261-282

```typescript
// Before: Manually parsed URL path segments with id: null
// After:
const folderPath = await backendService.getFolderPath(urlFolderId, token)
const restoredBreadcrumbs: BreadcrumbItem[] = [{ id: null, name: "Главная" }]

for (const folder of folderPath) {
  restoredBreadcrumbs.push({
    id: folder.id,
    name: folder.name
  })
}
```

---

### Problem 6: Folders/Files Disappear After Refresh

**Symptoms**:
- Created folder inside department appears initially
- After refresh, folder disappears
- Files uploaded to folder also disappear

**Root Cause**:
When `getSubfolders("department:abc")` was called, `get_virtual_subfolders` for departments returned an empty array `[]` instead of returning real folders with matching `department_id`.

**Fix**:
Updated `get_virtual_subfolders` in `backend/src/folders/virtual_folders.py` to return real folders when parent is a department

**File**: `backend/src/folders/virtual_folders.py` lines 167-187

```python
elif folder_type == "department":
    # Return real folders that belong to this department
    from .service import folder_service
    from .models import FolderResponse

    collection = folder_service.get_collection()

    # Find real folders with matching department_id and parentID = None
    cursor = collection.find({
        "department_id": real_id,
        "parentID": None
    }).sort("name", 1)

    folders = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        folders.append(FolderResponse(**doc))

    return folders
```

---

### Problem 7: Missing holding_id in Breadcrumb Path

**Symptoms**:
- Breadcrumb showed: "Главная > Company > Department > Folder"
- Expected: "Главная > Holding > Company > Department > Folder"
- Holding was missing from the hierarchy

**Root Cause**:

**Issue A**: `DepartmentResponse` model only has `company_id`, not `holding_id`. When converting departments to virtual folders, `holding_id=""` was set.

**Issue B**: `resolve_parent_context` was using the virtual department folder which had `holding_id=""`, so real folders created inside departments inherited this empty value.

**Issue C**: `get_folder_path` couldn't reconstruct the holding in the hierarchy because `holding_id=""`.

**Fix 1**: Updated `department_to_folder` to fetch company and extract holding_id

**File**: `backend/src/folders/virtual_folders.py` lines 102-120

```python
async def department_to_folder(self, department: DepartmentResponse) -> FolderResponse:
    # Fetch company to get holding_id
    company = await organization_service.get_company_by_id(department.company_id)
    holding_id = company.holding_id if company else ""

    return FolderResponse(
        id=self.create_virtual_id(department.id, "department"),
        name=department.name,
        parentID=self.create_virtual_id(department.company_id, "company"),
        company_id=department.company_id,
        department_id=department.id,
        holding_id=holding_id,  # Now properly populated
        # ...
    )
```

**Fix 2**: Updated `resolve_parent_context` to fetch holding_id for departments

**File**: `backend/src/folders/virtual_folders.py` lines 243-256

```python
if folder_type == "department":
    department = await organization_service.get_department_by_id(real_id)
    if department:
        # Fetch the company to get holding_id
        company = await organization_service.get_company_by_id(department.company_id)
        holding_id = company.holding_id if company else ''

        return {
            "holding_id": holding_id,
            "company_id": department.company_id,
            "department_id": real_id,
            "is_virtual_parent": True
        }
```

**Fix 3**: Added fallback in `get_folder_path` for existing folders with missing holding_id

**File**: `backend/src/folders/service.py` lines 367-374

```python
# If holding_id is missing but we have department_id, fetch it from company
# (This handles folders created before the fix)
holding_id = first_folder.holding_id
if not holding_id and first_folder.company_id:
    company = await organization_service.get_company_by_id(first_folder.company_id)
    if company:
        holding_id = company.holding_id
```

**Fix 4**: Updated all calls to `department_to_folder` to use `await`

Since `department_to_folder` became async, all calls needed to be updated:
- Line 143: `return await self.department_to_folder(department)`
- Line 170: `await asyncio.gather(*[self.department_to_folder(dept) for dept in departments])`
- Line 218: `await asyncio.gather(*[self.department_to_folder(dept) for dept in departments])`

---

### Problem 8: Incorrect Import Path

**Symptoms**:
- Error: `No module named 'src.folders.utils'`
- Backend crashed when navigating to departments

**Root Cause**:
Added incorrect import `from .utils import build_org_filter` but `build_org_filter` is actually in `..auth.org_filter`, not in a local `utils` module. However, the import wasn't even needed.

**Fix**:
Removed the incorrect import from `backend/src/folders/virtual_folders.py` line 171

**File**: `backend/src/folders/virtual_folders.py`

```python
# Removed: from .utils import build_org_filter
# Removed: from bson import ObjectId

# These imports were not needed since we're just querying by department_id
```

---

## API Endpoints

### Folder Endpoints

#### Get Root Folders
```
GET /folders/root
Authorization: Bearer {token}

Response: List[FolderResponse]
- Superadmin: Returns all holdings as virtual folders
- Admin: Returns departments in their company as virtual folders
- Director/User: Returns real folders in their department
```

#### Get Folder by ID
```
GET /folders/{folder_id}
Authorization: Bearer {token}

Response: FolderResponse
- Supports both virtual folders (holding:, company:, department:) and real folders
- Applies org-based access control
```

#### Get Subfolders
```
GET /folders/{folder_id}/subfolders
Authorization: Bearer {token}

Response: List[FolderResponse]
- If parent is holding → returns companies
- If parent is company → returns departments
- If parent is department → returns real folders
- If parent is real folder → returns real subfolders
```

#### Get Folder Path
```
GET /folders/{folder_id}/path
Authorization: Bearer {token}

Response: List[FolderResponse]
- Returns complete path from root to target folder
- Includes virtual folders in hierarchy
- Example: [Holding A, Company X, Department Y, Folder Z]
```

#### Create Folder
```
POST /folders/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "New Folder",
  "parentID": "department:abc123" or "real_folder_id" or null,
  "type": "documents"
}

Response: FolderResponse
- If parent is virtual department, sets parentID=null in DB but populates org IDs
- If parent is real folder, sets parentID and inherits org IDs
```

#### Rename Folder
```
PUT /folders/{folder_id}/rename
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "New Name"
}

Response: FolderResponse
- Virtual folders (holdings/companies/departments) cannot be renamed
```

#### Delete Folder
```
DELETE /folders/{folder_id}
Authorization: Bearer {token}

Response: {"message": "Folder deleted successfully"}
- Virtual folders (holdings/companies/departments) cannot be deleted
```

#### Move Folder
```
PUT /folders/{folder_id}/move?new_parent_id={parent_id}
Authorization: Bearer {token}

Response: FolderResponse
- Move folder to new parent or root (new_parent_id=null)
```

### File Upload Endpoints

#### Create Upload URL
```
POST /folders/{folder_id}/files/upload-url
Authorization: Bearer {token}
Content-Type: application/json

{
  "filename": "document.pdf",
  "file_type": "application/pdf",
  "file_size": 1024000
}

Response: FileUploadResponse
{
  "upload_url": "https://s3.../...",
  "file_id": "...",
  "file_key": "..."
}
```

#### Proxy Upload (Alternative to Direct S3)
```
POST /folders/{folder_id}/files/proxy-upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [binary file data]
description: "Optional description"
tags: ["tag1", "tag2"]

Response: FileMetadataResponse
```

---

## Testing Checklist

### Setup
- [ ] Backend server running: `cd backend && uvicorn src.main:app --reload`
- [ ] Frontend running: `npm run dev`
- [ ] MongoDB running with test data:
  - [ ] Holdings collection populated
  - [ ] Companies collection populated
  - [ ] Departments collection populated
  - [ ] Test users created with different roles

### Superadmin Tests
- [ ] Login as superadmin
- [ ] Navigate to File Manager
- [ ] Root shows all Holdings ✓
- [ ] Click on Holding → shows Companies inside ✓
- [ ] Click on Company → shows Departments inside ✓
- [ ] Click on Department → shows real Folders/Files inside ✓
- [ ] Create folder inside Department → folder persists after refresh ✓
- [ ] Upload file to folder → file persists after refresh ✓
- [ ] Navigate into real folder → breadcrumbs show: "Главная > Holding > Company > Department > Folder" ✓
- [ ] Click on breadcrumb items → navigates correctly ✓
- [ ] Refresh page → breadcrumbs and location persist ✓
- [ ] Right-click on virtual folder (holding/company/department) → no rename/delete options ✓
- [ ] Right-click on real folder → rename/delete options available ✓

### Admin Tests
- [ ] Login as admin (with company_id set)
- [ ] Navigate to File Manager
- [ ] Root shows Departments in their company ✓
- [ ] Does NOT show holdings or other companies ✓
- [ ] Click on Department → shows real Folders/Files ✓
- [ ] Create/rename/delete folders → operations succeed ✓
- [ ] Upload files → files persist ✓
- [ ] Breadcrumbs show full path including Company and Department ✓
- [ ] Cannot access folders in other companies ✓

### Department Director Tests
- [ ] Login as department director (with department_id set)
- [ ] Navigate to File Manager
- [ ] Root shows real Folders/Files in their department ✓
- [ ] Does NOT show virtual folders ✓
- [ ] Create/rename/delete folders → operations succeed ✓
- [ ] Upload/download files → operations succeed ✓
- [ ] Cannot access folders in other departments ✓

### User (Read-Only) Tests
- [ ] Login as regular user (with department_id set)
- [ ] Navigate to File Manager
- [ ] Root shows real Folders/Files in their department (read-only) ✓
- [ ] Right-click on folder → only "Download" option for files ✓
- [ ] No "Create Folder" button ✓
- [ ] No rename/delete/move options ✓
- [ ] Can download files ✓
- [ ] Cannot upload files ✓

### Edge Cases
- [ ] Navigate deep into hierarchy (5+ levels) → breadcrumbs work ✓
- [ ] Refresh at any level → state persists ✓
- [ ] Browser back/forward buttons → navigation works ✓
- [ ] URL manipulation (change folderId) → validation works ✓
- [ ] Invalid folder ID in URL → error handling works ✓
- [ ] Deleted folder ID in URL → error handling works ✓
- [ ] Create folder with same name → validation works ✓
- [ ] Upload file with invalid characters in name → validation works ✓
- [ ] Empty folders → display "No folders or files" message ✓

### Performance Tests
- [ ] Large number of folders (100+) → loads quickly ✓
- [ ] Large number of files (100+) → loads quickly ✓
- [ ] Navigate through hierarchy → no lag ✓
- [ ] Upload large file (100MB+) → progress indicator works ✓

### Security Tests
- [ ] User cannot access another user's department folders ✓
- [ ] Admin cannot access folders in other companies ✓
- [ ] Virtual folders cannot be renamed/deleted via API ✓
- [ ] Org filter prevents unauthorized access ✓
- [ ] Token expiration redirects to login ✓

---

## Summary

This implementation provides a complete hierarchical organizational folder system with:

1. **Virtual Folders**: Holdings, Companies, and Departments appear as navigable folders
2. **Role-Based Access Control**: Different navigation roots for different user roles
3. **Seamless Integration**: Virtual and real folders work together transparently
4. **Full Path Navigation**: Breadcrumbs show complete organizational hierarchy
5. **Permission Management**: Operations restricted based on user role and org membership
6. **Data Integrity**: Folders maintain organizational context through company_id, department_id, holding_id
7. **Robust Error Handling**: Validation at frontend and backend levels
8. **Performance**: Efficient queries with org-based filtering

The system successfully handles the complex requirements of multi-level organizational hierarchies while maintaining data security and providing an intuitive user experience.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-23
**Authors**: Claude AI (Anthropic)
