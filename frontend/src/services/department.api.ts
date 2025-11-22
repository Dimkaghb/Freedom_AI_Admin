import apiClient from '../lib/axios';

/**
 * Department creation request interface
 */
export interface CreateDepartmentRequest {
  name: string;
  description?: string;
  manager_id: string;
  company_id?: string; // Optional - auto-set for admins based on their company
}

/**
 * Department creation response interface
 */
export interface CreateDepartmentResponse {
  id: string;
  name: string;
  description?: string;
  manager_id: string;
  company_id: string;
  created_at: string;
  updated_at: string;
}

/**
 * Department response interface for list operations
 */
export interface DepartmentResponse {
  id: string;
  name: string;
  description?: string;
  manager_id: string;
  manager_name?: string;
  company_id: string;
  company_name?: string;
  users_count: number;
  created_at: string;
  updated_at: string;
}

/**
 * Create a new department
 *
 * @param departmentData - Department creation data
 * @returns Promise with created department data
 * @throws Error if creation fails
 */
export const createDepartment = async (
  departmentData: CreateDepartmentRequest
): Promise<CreateDepartmentResponse> => {
  try {
    const response = await apiClient.post<CreateDepartmentResponse>(
      '/departments/create',
      departmentData
    );
    return response.data;
  } catch (error: any) {
    // Extract error message from API response
    const errorMessage = error.response?.data?.detail || 'Failed to create department';
    throw new Error(errorMessage);
  }
};

/**
 * Get list of departments
 *
 * @returns Promise with list of departments
 */
export const listDepartments = async (): Promise<DepartmentResponse[]> => {
  try {
    const response = await apiClient.get<{ departments: DepartmentResponse[]; total_count: number }>(
      '/departments/list'
    );
    return response.data.departments;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to fetch departments';
    throw new Error(errorMessage);
  }
};

/**
 * Get department by ID
 *
 * @param id - Department ID
 * @returns Promise with department data
 */
export const getDepartment = async (id: string): Promise<DepartmentResponse> => {
  try {
    const response = await apiClient.get<DepartmentResponse>(`/departments/${id}`);
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to fetch department';
    throw new Error(errorMessage);
  }
};
