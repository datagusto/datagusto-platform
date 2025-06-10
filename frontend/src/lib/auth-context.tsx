"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService, organizationService } from '@/services';
import type { User, LoginCredentials, RegisterData, Organization, UserOrganizationInfo } from '@/types';

interface AuthContextType {
  user: User | null;
  organizations: UserOrganizationInfo[];
  currentOrganization: Organization | null;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  setCurrentOrganization: (org: Organization) => void;
  refreshOrganizations: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<UserOrganizationInfo[]>([]);
  const [currentOrganization, setCurrentOrganizationState] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);

  // Load current organization from localStorage
  useEffect(() => {
    const savedOrgId = localStorage.getItem('current_organization_id');
    if (savedOrgId && organizations.length > 0) {
      const org = organizations.find(o => o.organization.id === savedOrgId)?.organization;
      if (org) {
        setCurrentOrganizationState(org);
      } else {
        // Fallback to first organization if saved one not found
        setCurrentOrganizationState(organizations[0].organization);
        localStorage.setItem('current_organization_id', organizations[0].organization.id);
      }
    } else if (organizations.length > 0) {
      // Set first organization as default
      setCurrentOrganizationState(organizations[0].organization);
      localStorage.setItem('current_organization_id', organizations[0].organization.id);
    }
  }, [organizations]);

  const refreshOrganizations = async () => {
    try {
      const userOrgs = await organizationService.getUserOrganizations();
      setOrganizations(userOrgs);
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        if (authService.isAuthenticated()) {
          const userData = await authService.getCurrentUser();
          setUser(userData);
          await refreshOrganizations();
        }
      } catch (error) {
        // Token might be invalid, clear it
        authService.logout();
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const tokenResponse = await authService.login(credentials);
    const userData = await authService.getCurrentUser();
    setUser(userData);
    await refreshOrganizations();
  };

  const register = async (userData: RegisterData) => {
    await authService.register(userData);
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setOrganizations([]);
    setCurrentOrganizationState(null);
    localStorage.removeItem('current_organization_id');
  };

  const setCurrentOrganization = (org: Organization) => {
    setCurrentOrganizationState(org);
    localStorage.setItem('current_organization_id', org.id);
  };

  const value: AuthContextType = {
    user,
    organizations,
    currentOrganization,
    loading,
    login,
    register,
    logout,
    setCurrentOrganization,
    refreshOrganizations,
    isAuthenticated: !!user,
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