/**
 * Dashboard TypeScript Types
 *
 * Type definitions for role-based dashboard data.
 * These types match the backend Pydantic models for type safety.
 */

// ============================================================================
// Summary Types - Lightweight representations of resources
// ============================================================================

export interface HoldingSummary {
  id: string;
  name: string;
  description: string | null;
  companies_count: number;
  created_at: string;
}

export interface CompanySummary {
  id: string;
  name: string;
  description: string | null;
  holding_id: string;
  holding_name: string | null;
  departments_count: number;
  users_count: number;
  created_at: string;
}

export interface DepartmentSummary {
  id: string;
  name: string;
  description: string | null;
  company_id: string;
  company_name: string | null;
  manager_id: string | null;
  manager_name: string | null;
  users_count: number;
  created_at: string;
}

export interface UserSummary {
  id: string;
  email: string;
  firstName: string | null;
  lastName: string | null;
  role: string;
  is_active: boolean;
  department_id: string | null;
  department_name: string | null;
  company_id: string | null;
  company_name: string | null;
}

// ============================================================================
// Statistics Types - Aggregated counts and metrics
// ============================================================================

export interface DashboardCounts {
  holdings: number;
  companies: number;
  departments: number;
  users: number;
  active_users: number;
  pending_users: number;
}

// ============================================================================
// Dashboard Response Types - Role-specific responses
// ============================================================================

export interface SuperadminDashboardResponse {
  role: 'superadmin';
  counts: DashboardCounts;
  holdings: HoldingSummary[];
  recent_companies: CompanySummary[];
  recent_departments: DepartmentSummary[];
  recent_users: UserSummary[];
}

export interface AdminDashboardResponse {
  role: 'admin';
  counts: DashboardCounts;
  company: CompanySummary | null;
  departments: DepartmentSummary[];
  recent_users: UserSummary[];
}

export interface DirectorDashboardResponse {
  role: 'director';
  counts: DashboardCounts;
  department: DepartmentSummary | null;
  company: CompanySummary | null;
  users: UserSummary[];
}

export interface UserDashboardResponse {
  role: 'user';
  counts: DashboardCounts;
  department: DepartmentSummary | null;
  company: CompanySummary | null;
  colleagues: UserSummary[];
}

// ============================================================================
// Union Type for All Dashboard Responses
// ============================================================================

export type DashboardResponse =
  | SuperadminDashboardResponse
  | AdminDashboardResponse
  | DirectorDashboardResponse
  | UserDashboardResponse;

// ============================================================================
// Request Types
// ============================================================================

export interface DashboardStatsRequest {
  include_recent?: boolean;
  recent_limit?: number;
}

// ============================================================================
// Helper Types for UI State
// ============================================================================

export interface DashboardState {
  data: DashboardResponse | null;
  loading: boolean;
  error: string | null;
}

export interface DashboardFilters {
  searchQuery: string;
  timeRange: string;
}

// ============================================================================
// Type Guards - Runtime type checking
// ============================================================================

export function isSuperadminDashboard(
  data: DashboardResponse
): data is SuperadminDashboardResponse {
  return data.role === 'superadmin';
}

export function isAdminDashboard(
  data: DashboardResponse
): data is AdminDashboardResponse {
  return data.role === 'admin';
}

export function isDirectorDashboard(
  data: DashboardResponse
): data is DirectorDashboardResponse {
  return data.role === 'director';
}

export function isUserDashboard(
  data: DashboardResponse
): data is UserDashboardResponse {
  return data.role === 'user';
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Extract user's full name from UserSummary
 */
export function getUserFullName(user: UserSummary): string {
  const firstName = user.firstName || '';
  const lastName = user.lastName || '';
  const fullName = `${firstName} ${lastName}`.trim();
  return fullName || user.email;
}

/**
 * Format date string to readable format
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Format date string to relative time (e.g., "2 days ago")
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'только что';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} ${getPluralForm(minutes, 'минуту', 'минуты', 'минут')} назад`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} ${getPluralForm(hours, 'час', 'часа', 'часов')} назад`;
  } else if (diffInSeconds < 2592000) {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} ${getPluralForm(days, 'день', 'дня', 'дней')} назад`;
  } else {
    return formatDate(dateString);
  }
}

/**
 * Get Russian plural form based on number
 */
function getPluralForm(
  count: number,
  one: string,
  few: string,
  many: string
): string {
  const mod10 = count % 10;
  const mod100 = count % 100;

  if (mod10 === 1 && mod100 !== 11) {
    return one;
  } else if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return few;
  } else {
    return many;
  }
}

/**
 * Get role display name in Russian
 */
export function getRoleDisplayName(role: string): string {
  const roleMap: Record<string, string> = {
    'superadmin': 'Суперадмин',
    'admin': 'Администратор',
    'director': 'Директор',
    'user': 'Пользователь',
  };
  return roleMap[role] || role;
}

/**
 * Get status badge color based on user active status
 */
export function getStatusColor(isActive: boolean): string {
  return isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
}

/**
 * Get status text based on user active status
 */
export function getStatusText(isActive: boolean): string {
  return isActive ? 'Активен' : 'Заблокирован';
}
