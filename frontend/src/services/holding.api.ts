import apiClient from '../lib/axios';

/**
 * Holding creation request interface
 */
export interface CreateHoldingRequest {
  name: string;
  description?: string;
}

/**
 * Holding creation response interface
 */
export interface CreateHoldingResponse {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Holding response interface for list operations
 */
export interface HoldingResponse {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Create a new holding
 *
 * @param holdingData - Holding creation data
 * @returns Promise with created holding data
 * @throws Error if creation fails
 */
export const createHolding = async (
  holdingData: CreateHoldingRequest
): Promise<CreateHoldingResponse> => {
  try {
    const response = await apiClient.post<CreateHoldingResponse>(
      '/holdings/create',
      holdingData
    );
    return response.data;
  } catch (error: any) {
    // Extract error message from API response
    const errorMessage = error.response?.data?.detail || 'Failed to create holding';
    throw new Error(errorMessage);
  }
};

/**
 * Get list of holdings
 *
 * @returns Promise with list of holdings
 */
export const listHoldings = async (): Promise<HoldingResponse[]> => {
  try {
    const response = await apiClient.get<{ holdings: HoldingResponse[]; total: number }>(
      '/holdings/list'
    );
    return response.data.holdings;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to fetch holdings';
    throw new Error(errorMessage);
  }
};

/**
 * Get holding by ID
 *
 * @param id - Holding ID
 * @returns Promise with holding data
 */
export const getHolding = async (id: string): Promise<HoldingResponse> => {
  try {
    const response = await apiClient.get<HoldingResponse>(`/holdings/${id}`);
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to fetch holding';
    throw new Error(errorMessage);
  }
};
