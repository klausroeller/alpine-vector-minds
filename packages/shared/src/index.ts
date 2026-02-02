// Shared types and utilities between frontend and backend

export interface User {
  id: string;
  email: string;
  fullName: string | null;
  isActive: boolean;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}
