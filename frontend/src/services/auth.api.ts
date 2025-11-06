import apiClient from '../lib/axios';
import { setTokens, clearTokens } from '../lib/axios';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
  message: string;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

/**
 * Login user with email and password
 */
export const login = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  try {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials);

    // Store tokens
    setTokens(response.data.access_token, response.data.refresh_token);

    // Store user info
    localStorage.setItem('user', JSON.stringify(response.data.user));

    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Login failed');
  }
};

/**
 * Logout user
 */
export const logout = (): void => {
  clearTokens();
};

/**
 * Get current user info from server
 */
export const getCurrentUser = async (): Promise<User> => {
  try {
    const response = await apiClient.get<User>('/auth/me');

    // Update stored user info
    localStorage.setItem('user', JSON.stringify(response.data));

    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to get user info');
  }
};

/**
 * Refresh access token
 */
export const refreshAccessToken = async (refreshToken: string): Promise<RefreshResponse> => {
  try {
    const response = await apiClient.post<RefreshResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Token refresh failed');
  }
};
