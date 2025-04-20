"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Token constants
export const ACCESS_TOKEN_KEY = 'access_token';
// Use a simpler cookie format for better compatibility
export const TOKEN_COOKIE_OPTIONS = 'path=/; max-age=86400';

// Auth API endpoints
export const getAuthApiUrl = (endpoint: string) => 
  `${process.env.NEXT_PUBLIC_API_URL}/api/${process.env.NEXT_PUBLIC_API_VERSION}/auth/${endpoint}`;

// Types
export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
}

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  created_at?: string;
  updated_at?: string;
  is_active?: boolean;
}

// Token management functions
export function getToken(): string | null {
  // localStorage から認証トークンを取得（主要な保存場所として使用）
  if (typeof window !== 'undefined') {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }
  return null;
}

export function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    // メイン保存場所としてlocalStorageを使用
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
    
    // ミドルウェアのために必要最小限のCookieのみを設定
    // (SameSite, Secure等の属性は環境に応じて適切に設定)
    document.cookie = `${ACCESS_TOKEN_KEY}=${token}; ${TOKEN_COOKIE_OPTIONS}`;
    document.cookie = `session=true; ${TOKEN_COOKIE_OPTIONS}`;
  }
}

export function clearToken(): void {
  if (typeof window !== 'undefined') {
    // localStorage からクリア（主要な保存場所）
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    
    // Cookie もクリア
    document.cookie = `${ACCESS_TOKEN_KEY}=; max-age=0; path=/`;
    document.cookie = `session=; max-age=0; path=/`;
  }
}

// Auth status check
export function isAuthenticated(): boolean {
  // localStorageのトークンのみをチェック（認証の単一の情報源）
  if (typeof window !== 'undefined') {
    const token = getToken();
    return !!token;
  }
  return false;
}

export function isAuthenticationError(error: unknown): boolean {
  return error instanceof Error && error.message === 'Authentication required';
}

export function handleAuthError(error: unknown): void {
  if (isAuthenticationError(error)) {
    redirectToLogin();
  }
}

export function redirectToLogin(redirectPath?: string): void {
  // ログイン画面へのリダイレクト（認証エラー時やログアウト時に必要）
  if (typeof window !== 'undefined') {
    window.location.href = '/sign-in';
  }
}

// Fetch and set user's organization ID
export async function fetchOrganizationId(): Promise<boolean> {
  // Only attempt to fetch if the user is authenticated
  if (!isAuthenticated()) {
    // Don't redirect or throw error here, just return false
    return false;
  }
  
  try {
    const token = getToken();
    if (!token) {
      return false;
    }
    
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const apiVersion = process.env.NEXT_PUBLIC_API_VERSION;
    
    if (!apiUrl || !apiVersion) {
      console.error('API URL or version not configured');
      return false;
    }
    
    const response = await fetch(`${apiUrl}/api/${apiVersion}/users/me/organizations`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      cache: 'no-store',
    });
    
    if (!response.ok) {
      // If unauthorized, clear token but don't redirect
      if (response.status === 401) {
        clearToken();
        return false;
      }
      throw new Error('Failed to fetch organizations');
    }
    
    const organizations = await response.json();
    
    // User belongs to exactly one organization, so we take the first one
    if (organizations && organizations.length > 0) {
      const organizationId = organizations[0].id;
      
      if (typeof window !== 'undefined') {
        localStorage.removeItem('currentOrganizationId');
        localStorage.setItem('currentOrganizationId', organizationId);
      }
      
      return true;
    } else {
      console.error('No organizations found for user');
      return false;
    }
  } catch (error) {
    console.error('Error fetching organization ID:', error);
    return false;
  }
}

// Fetch current user information
export async function fetchCurrentUser(): Promise<UserInfo | null> {
  // Only attempt to fetch if the user is authenticated
  if (!isAuthenticated()) {
    return null;
  }
  
  try {
    const token = getToken();
    if (!token) {
      return null;
    }
    
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const apiVersion = process.env.NEXT_PUBLIC_API_VERSION;
    
    if (!apiUrl || !apiVersion) {
      console.error('API URL or version not configured');
      return null;
    }
    
    const response = await fetch(`${apiUrl}/api/${apiVersion}/users/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      // キャッシュを使わないようにする
      cache: 'no-store',
    });
    
    if (!response.ok) {
      // If unauthorized, clear token but don't redirect
      if (response.status === 401) {
        clearToken();
        return null;
      }
      throw new Error('Failed to fetch user information');
    }
    
    const userInfo: UserInfo = await response.json();
    
    // 既存の情報を削除してから新しい情報を設定
    if (typeof window !== 'undefined') {
      localStorage.removeItem('userInfo');
      localStorage.setItem('userInfo', JSON.stringify(userInfo));
    }
    
    return userInfo;
  } catch (error) {
    console.error('Error fetching user information:', error);
    return null;
  }
}

// Get stored user info from localStorage
export function getStoredUserInfo(): UserInfo | null {
  if (typeof window !== 'undefined') {
    const userInfoStr = localStorage.getItem('userInfo');
    if (userInfoStr) {
      try {
        return JSON.parse(userInfoStr);
      } catch (e) {
        console.error('Failed to parse user info:', e);
      }
    }
  }
  return null;
}

// Clear stored user info
export function clearUserInfo(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('userInfo');
  }
}

// Login function
export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  console.log('Login attempt with:', credentials.email);
  
  const response = await fetch(getAuthApiUrl('token'), {
    method: 'POST',
    headers: {
      'accept': 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'password',
      username: credentials.email,
      password: credentials.password,
      scope: '',
      client_id: process.env.NEXT_PUBLIC_CLIENT_ID || 'string',
      client_secret: process.env.NEXT_PUBLIC_CLIENT_SECRET || 'string',
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to sign in');
  }

  const data: AuthResponse = await response.json();
  console.log('Login successful, token received');
  
  // Store the token in localStorage (primary storage)
  setToken(data.access_token);
  
  // Fetch and set the user's organization ID after successful login
  await fetchOrganizationId();
  
  // Fetch user information
  await fetchCurrentUser();
  
  return data;
}

// Register function
export async function register(data: RegisterData): Promise<void> {
  const response = await fetch(getAuthApiUrl('register'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: data.name,
      email: data.email,
      password: data.password,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Registration failed');
  }
}

// Logout function
export function logout(): void {
  // まず認証関連データをクリア
  clearToken();
  clearUserInfo();
  
  // 組織IDもクリア
  if (typeof window !== 'undefined') {
    localStorage.removeItem('currentOrganizationId');
    
    // ログアウト時のリダイレクト（必要）
    window.location.href = '/sign-in';
  }
}

// Simple hook to check auth in protected components
export function useAuthCheck(): void {
  const router = useRouter();
  
  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated()) {
      // 認証されていない場合のみリダイレクト（必要）
      router.push('/sign-in');
    }
  }, [router]);
}

// Create an authenticated fetch function that includes credentials
export async function authFetch(
  url: string, 
  options: RequestInit = {}
): Promise<Response> {
  if (!isAuthenticated()) {
    // 認証が必要なAPI呼び出しで未認証の場合のみリダイレクト（必要）
    redirectToLogin();
    throw new Error('Authentication required');
  }
  
  try {
    const token = getToken();
    const headers = new Headers(options.headers || {});
    
    // Add Authorization header if we have a token
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include', // Always include credentials for authenticated requests
    });
    
    // 401エラー時のリダイレクト（認証情報が無効な場合に必要）
    if (response.status === 401) {
      clearToken();
      redirectToLogin();
      throw new Error('Authentication required');
    }
    
    return response;
  } catch (error) {
    // 認証エラー時のリダイレクト（必要）
    handleAuthError(error);
    throw error;
  }
} 