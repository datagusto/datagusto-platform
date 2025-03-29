"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  getToken, 
  isAuthenticated as checkAuthentication, 
  login, 
  logout, 
  fetchOrganizationId, 
  fetchCurrentUser,
  getStoredUserInfo,
  UserInfo
} from '@/utils/auth';
import type { LoginCredentials, AuthResponse } from '@/utils/auth';
import { toast } from "sonner";

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  user: UserInfo | null;
  login: (credentials: LoginCredentials) => Promise<AuthResponse>;
  logout: () => void;
  loading: boolean;
  refreshUserInfo: () => Promise<UserInfo | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<UserInfo | null>(null);

  // ユーザー情報を更新する関数
  const refreshUserInfo = async () => {
    const userInfo = await fetchCurrentUser();
    setUser(userInfo);
    return userInfo;
  };

  // ログイン状態の初期化
  useEffect(() => {
    const initAuth = async () => {
      const currentToken = getToken();
      const authState = checkAuthentication();
      
      setToken(currentToken);
      setIsAuthenticated(authState);
      
      // キャッシュからユーザー情報を取得
      const cachedUserInfo = getStoredUserInfo();
      if (cachedUserInfo) {
        setUser(cachedUserInfo);
      }
      
      // すでに認証済みの場合、組織IDとユーザー情報を取得する
      if (authState) {
        const hasOrganization = await fetchOrganizationId();
        
        // ユーザー情報を取得
        const userInfo = await fetchCurrentUser();
        if (userInfo) {
          setUser(userInfo);
        }
        
        // 組織が見つからない場合、ログアウトして再ログインを促す
        if (!hasOrganization) {
          console.warn('No organization found for user. Logging out...');
          logout();
          setToken(null);
          setIsAuthenticated(false);
          setUser(null);
          // ユーザーがすでにページを見ている場合のために通知
          if (typeof window !== 'undefined') {
            toast.error("組織情報が見つかりません。再度ログインしてください。");
          }
        }
      }
      
      setLoading(false);
    };

    initAuth();
  }, []);

  const handleLogin = async (credentials: LoginCredentials) => {
    setLoading(true);
    try {
      const response = await login(credentials);
      setToken(response.access_token);
      setIsAuthenticated(true);
      
      // ログイン直後に組織情報を取得する
      const hasOrganization = await fetchOrganizationId();
      
      // ユーザー情報を取得
      const userInfo = await fetchCurrentUser();
      if (userInfo) {
        setUser(userInfo);
      }
      
      // 組織が見つからない場合、エラーを表示
      if (!hasOrganization) {
        toast.error("組織情報が見つかりません。システム管理者に連絡してください。");
        logout();
        setToken(null);
        setIsAuthenticated(false);
        setUser(null);
        throw new Error('組織情報が見つかりません');
      }
      
      // Return the response so the component can decide what to do next
      return response;
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    setToken(null);
    setIsAuthenticated(false);
    setUser(null);
  };

  const value = {
    isAuthenticated,
    token,
    user,
    login: handleLogin,
    logout: handleLogout,
    loading,
    refreshUserInfo
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 