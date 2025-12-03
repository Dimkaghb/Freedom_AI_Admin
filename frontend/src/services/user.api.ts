import apiClient from '../lib/axios';

/**
 * User creation request interface matching backend UserCreate model
 */
export interface CreateUserRequest {
  email: string;
  role: 'admin' | 'user' | 'director';
  firstName?: string;
  lastName?: string;
}

/**
 * User creation response interface matching backend UserCreateResponse model
 */
export interface CreateUserResponse {
  id: string;
  email: string;
  role: string;
  firstName?: string;
  lastName?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  temporary_password: string;
}

/**
 * User response interface for list operations
 */
export interface UserResponse {
  id: string;
  email: string;
  role: string;
  firstName?: string;
  lastName?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Create a new user by admin
 *
 * @param userData - User creation data
 * @returns Promise with created user data including temporary password
 * @throws Error if creation fails
 */
export const createUser = async (userData: CreateUserRequest): Promise<CreateUserResponse> => {
  try {
    const response = await apiClient.post<CreateUserResponse>('/users/create', userData);
    return response.data;
  } catch (error: any) {
    // Extract error message from API response
    const errorMessage = error.response?.data?.detail || 'Failed to create user';
    throw new Error(errorMessage);
  }
};

/**
 * Pending user response interface
 */
export interface PendingUserResponse {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  company_id: string;
  department_id?: string;
  role: string;
  status: string;
  created_at: string;
  updated_at: string;
}

/**
 * Get list of users with optional status filter
 *
 * @param statusFilter - Filter by status: 'active' or 'blocked'
 * @returns Promise with list of users
 */
export const listUsers = async (statusFilter: 'active' | 'blocked' = 'active'): Promise<UserResponse[]> => {
  try {
    const response = await apiClient.get<{ users: UserResponse[]; total_count: number }>(
      `/users/list?status_filter=${statusFilter}`
    );
    return response.data.users;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to fetch users';
    throw new Error(errorMessage);
  }
};

/**
 * Get list of pending users awaiting approval
 *
 * @returns Promise with list of pending users
 */
export const listPendingUsers = async (): Promise<PendingUserResponse[]> => {
  try {
    const response = await apiClient.get<{ pending_users: PendingUserResponse[]; total_count: number }>(
      '/users/pending'
    );
    return response.data.pending_users;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to fetch pending users';
    throw new Error(errorMessage);
  }
};

/**
 * Approve a pending user
 *
 * @param pendingUserId - ID of the pending user to approve
 * @returns Promise with approved user data
 */
export const approvePendingUser = async (pendingUserId: string): Promise<UserResponse> => {
  try {
    const response = await apiClient.post<UserResponse>('/users/approve', {
      pending_user_id: pendingUserId,
      action: 'approve'
    });
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to approve user';
    throw new Error(errorMessage);
  }
};

/**
 * Reject a pending user
 *
 * @param pendingUserId - ID of the pending user to reject
 * @returns Promise with success message
 */
export const rejectPendingUser = async (pendingUserId: string): Promise<{message: string}> => {
  try {
    const response = await apiClient.post<{message: string}>('/users/approve', {
      pending_user_id: pendingUserId,
      action: 'reject'
    });
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to reject user';
    throw new Error(errorMessage);
  }
};

/**
 * Delete user response interface
 */
export interface DeleteUserResponse {
  message: string;
  user_id: string;
  email: string;
  name: string;
  companies_updated: number;
  departments_updated: number;
}

/**
 * Delete a user and handle cascade updates
 *
 * @param userId - ID of the user to delete
 * @returns Promise with deletion result details
 * @throws Error if deletion fails
 */
export const deleteUser = async (userId: string): Promise<DeleteUserResponse> => {
  try {
    const response = await apiClient.delete<DeleteUserResponse>(`/users/${userId}`);
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to delete user';
    throw new Error(errorMessage);
  }
};
