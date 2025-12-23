/**
 * File Manager API Service
 *
 * API client for file and folder operations in the knowledge base.
 * Handles authentication, error handling, and type safety.
 */

import apiClient from '../lib/axios';

/**
 * API endpoints
 */
const FILEMANAGER_ENDPOINTS = {
  FOLDERS: '/kbase/folders',
  FILES: '/kbase/files',
  STORAGE: '/kbase/storage',
  HEALTH: '/kbase/health',
} as const;

/**
 * Type definitions
 */
export interface Folder {
  id: string;
  name: string;
  type: string;
  parentID: string | null;
  fileIds: string[];
  foldersids: string[];
  company_id: string;
  department_id: string;
  holding_id: string;
  created_at: string;
  updated_at: string;
}

export interface File {
  id: string;
  filename: string;
  file_key: string;
  file_type: string;
  file_size: number;
  company_id: string;
  department_id: string;
  holding_id: string;
  chat_id: string | null;
  folder_id: string | null;
  description: string;
  tags: string[];
  download_url?: string;
  created_at: string;
  updated_at: string;
}

export interface FolderListResponse {
  folders: Folder[];
  total: number;
}

export interface FileListResponse {
  files: File[];
  total: number;
}

export interface BreadcrumbItem {
  id: string | null;
  name: string;
}

export interface FolderPathResponse {
  path: BreadcrumbItem[];
}

export interface StorageInfo {
  total_files: number;
  total_size_bytes: number;
  total_size_formatted: string;
  by_company?: Record<string, any>;
  by_department?: Record<string, any>;
}

/**
 * Error response from API
 */
interface ApiError {
  detail: string;
}

/**
 * File Manager API error with details
 */
export class FileManagerApiError extends Error {
  public statusCode: number;
  public detail: string;

  constructor(message: string, statusCode: number, detail: string) {
    super(message);
    this.name = 'FileManagerApiError';
    this.statusCode = statusCode;
    this.detail = detail;
  }
}

/**
 * List folders based on parent ID
 *
 * @param parentId - Parent folder ID (null for root folders)
 * @returns Promise<FolderListResponse>
 */
export const listFolders = async (parentId: string | null = null): Promise<FolderListResponse> => {
  try {
    const params = parentId ? { parent_id: parentId } : {};
    const response = await apiClient.get<FolderListResponse>(
      FILEMANAGER_ENDPOINTS.FOLDERS,
      { params }
    );
    return response.data;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const detail = error.response?.data?.detail || 'Failed to fetch folders';
    throw new FileManagerApiError('Failed to fetch folders', statusCode, detail);
  }
};

/**
 * Get a single folder by ID
 *
 * @param folderId - Folder ID
 * @returns Promise<Folder>
 */
export const getFolder = async (folderId: string): Promise<Folder> => {
  try {
    const response = await apiClient.get<Folder>(
      `${FILEMANAGER_ENDPOINTS.FOLDERS}/${folderId}`
    );
    return response.data;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const detail = error.response?.data?.detail || 'Failed to fetch folder';
    throw new FileManagerApiError('Failed to fetch folder', statusCode, detail);
  }
};

/**
 * Get breadcrumb path for a folder
 *
 * @param folderId - Folder ID
 * @returns Promise<FolderPathResponse>
 */
export const getFolderPath = async (folderId: string): Promise<FolderPathResponse> => {
  try {
    const response = await apiClient.get<FolderPathResponse>(
      `${FILEMANAGER_ENDPOINTS.FOLDERS}/${folderId}/path`
    );
    return response.data;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const detail = error.response?.data?.detail || 'Failed to fetch folder path';
    throw new FileManagerApiError('Failed to fetch folder path', statusCode, detail);
  }
};

/**
 * List files in a folder
 *
 * @param folderId - Folder ID (null for root files)
 * @returns Promise<FileListResponse>
 */
export const listFiles = async (folderId: string | null = null): Promise<FileListResponse> => {
  try {
    const params = folderId ? { folder_id: folderId } : {};
    const response = await apiClient.get<FileListResponse>(
      FILEMANAGER_ENDPOINTS.FILES,
      { params }
    );
    return response.data;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const detail = error.response?.data?.detail || 'Failed to fetch files';
    throw new FileManagerApiError('Failed to fetch files', statusCode, detail);
  }
};

/**
 * Get a single file by ID
 *
 * @param fileId - File ID
 * @returns Promise<File>
 */
export const getFile = async (fileId: string): Promise<File> => {
  try {
    const response = await apiClient.get<File>(
      `${FILEMANAGER_ENDPOINTS.FILES}/${fileId}`
    );
    return response.data;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const detail = error.response?.data?.detail || 'Failed to fetch file';
    throw new FileManagerApiError('Failed to fetch file', statusCode, detail);
  }
};

/**
 * Get storage usage information
 *
 * @returns Promise<StorageInfo>
 */
export const getStorageInfo = async (): Promise<StorageInfo> => {
  try {
    const response = await apiClient.get<StorageInfo>(
      FILEMANAGER_ENDPOINTS.STORAGE
    );
    return response.data;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const detail = error.response?.data?.detail || 'Failed to fetch storage info';
    throw new FileManagerApiError('Failed to fetch storage info', statusCode, detail);
  }
};

/**
 * Handle File Manager API errors
 *
 * @param error - Unknown error object
 * @returns User-friendly error message
 */
export const handleFileManagerError = (error: unknown): string => {
  if (error instanceof FileManagerApiError) {
    switch (error.statusCode) {
      case 401:
        return 'Authentication required. Please log in again.';
      case 403:
        return 'Access denied. You do not have permission to access this resource.';
      case 404:
        return 'Resource not found.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return error.detail || 'An unexpected error occurred.';
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred.';
};
