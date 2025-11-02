// User role types for the Freedom AI Analysis admin system
export type UserRole = 'superadmin' | 'companyadmin' | 'departmentdirector' | 'user';

// User interface definition
export interface User {
  id: string;
  email: string;
  role: UserRole;
  fullName?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// Dashboard statistics interface for different user roles
export interface DashboardStats {
  holdings?: number;
  companies?: number;
  departments?: number;
  users?: number;
  activeRequests?: number;
  activeUsers?: number;
  participants?: number;
}

// Company information interface
export interface Company {
  id: string;
  name: string;
  logo?: string;
  description?: string;
  departmentCount: number;
  userCount: number;
}

// Department information interface
export interface Department {
  id: string;
  name: string;
  companyId: string;
  companyName: string;
  participantCount: number;
  directorId: string;
}

// Activity log entry interface
export interface ActivityLogEntry {
  id: string;
  userId: string;
  userName: string;
  action: string;
  timestamp: string;
  details?: string;
}

// Request/Application interface
export interface Request {
  id: string;
  title: string;
  status: 'pending' | 'approved' | 'rejected';
  priority: 'low' | 'medium' | 'high';
  submittedBy: string;
  submittedAt: string;
  lastUpdated: string;
}