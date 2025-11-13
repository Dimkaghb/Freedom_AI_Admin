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
