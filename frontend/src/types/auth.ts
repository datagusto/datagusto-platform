/**
 * Authentication types based on backend API specification
 */

// User data structure
export interface User {
  id: string;
  email: string;
  name?: string;
  is_active: boolean;
  email_confirmed?: boolean;
  created_at: string;
  updated_at: string;
}

// Login request
export interface LoginCredentials {
  email: string;
  password: string;
}

// Registration request
export interface RegisterData {
  email: string;
  password: string;
  name?: string;
}

// Token response from login
export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

// API error response
export interface ApiError {
  detail: string;
}