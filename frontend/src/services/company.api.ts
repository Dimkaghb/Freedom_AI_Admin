import apiClient from '../lib/axios';

/**
 * Company creation request interface
 */
export interface CreateCompanyRequest {
  name: string;
  description?: string;
  holding_id: string;
  admin_id?: string;
}

/**
 * Company creation response interface
 */
export interface CreateCompanyResponse {
  id: string;
  name: string;
  description?: string;
  holding_id: string;
  admin_id?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Company response interface for list operations
 */
export interface CompanyResponse {
  id: string;
  name: string;
  description?: string;
  holding_id: string;
  admin_id?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Create a new company
 *
 * @param companyData - Company creation data
 * @returns Promise with created company data
 * @throws Error if creation fails
 */
export const createCompany = async (
  companyData: CreateCompanyRequest
): Promise<CreateCompanyResponse> => {
  try {
    const response = await apiClient.post<CreateCompanyResponse>(
      '/companies/create',
      companyData
    );
    return response.data;
  } catch (error: any) {
    // Extract error message from API response
    const errorMessage = error.response?.data?.detail || 'Failed to create company';
    throw new Error(errorMessage);
  }
};

/**
 * Get list of companies
 *
 * @param holdingId - Optional holding ID to filter companies
 * @returns Promise with list of companies
 */
export const listCompanies = async (holdingId?: string): Promise<CompanyResponse[]> => {
  try {
    const url = holdingId ? `/companies/list?holding_id=${holdingId}` : '/companies/list';
    const response = await apiClient.get<{ companies: CompanyResponse[]; total: number }>(url);
    return response.data.companies;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to fetch companies';
    throw new Error(errorMessage);
  }
};

/**
 * Get company by ID
 *
 * @param id - Company ID
 * @returns Promise with company data
 */
export const getCompany = async (id: string): Promise<CompanyResponse> => {
  try {
    const response = await apiClient.get<CompanyResponse>(`/companies/${id}`);
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to fetch company';
    throw new Error(errorMessage);
  }
};
