"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService, organizationService, projectService } from '@/services';
import type { User, LoginCredentials, RegisterData, Organization, UserOrganizationInfo, UserProjectInfo } from '@/types';

interface AuthContextType {
  user: User | null;
  organizations: UserOrganizationInfo[];
  currentOrganization: Organization | null;
  currentProject: UserProjectInfo | null;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  setCurrentOrganization: (org: Organization) => void;
  setCurrentProject: (project: UserProjectInfo | null) => void;
  refreshOrganizations: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<UserOrganizationInfo[]>([]);
  const [currentOrganization, setCurrentOrganizationState] = useState<Organization | null>(null);
  const [currentProject, setCurrentProjectState] = useState<UserProjectInfo | null>(null);
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

  // Load current project from localStorage when organization is set
  useEffect(() => {
    const loadCurrentProject = async () => {
      if (!currentOrganization) return;
      
      const savedProjectId = localStorage.getItem('current_project_id');
      if (savedProjectId) {
        try {
          const userProjects = await projectService.getUserProjects();
          const projectInfo = userProjects.find(p => 
            p.project.id === savedProjectId && 
            p.project.organization_id === currentOrganization.id
          );
          
          if (projectInfo) {
            setCurrentProjectState(projectInfo);
          } else {
            // Project not found or not in current organization, clear saved ID
            localStorage.removeItem('current_project_id');
          }
        } catch (error) {
          console.error('Failed to load saved project:', error);
          localStorage.removeItem('current_project_id');
        }
      }
    };

    loadCurrentProject();
  }, [currentOrganization]);

  const refreshOrganizations = async () => {
    try {
      const userOrgs = await organizationService.getUserOrganizations();
      setOrganizations(userOrgs);
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  // Check token expiration periodically
  useEffect(() => {
    const checkTokenExpiration = () => {
      const token = authService.getToken();
      if (!token) return;

      try {
        // Parse JWT token
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expirationTime = payload.exp * 1000;
        const currentTime = Date.now();
        const timeUntilExpiry = expirationTime - currentTime;

        // If token expires in less than 5 minutes, refresh it
        if (timeUntilExpiry < 5 * 60 * 1000 && timeUntilExpiry > 0) {
          authService.refreshToken().catch((error) => {
            console.error('Failed to refresh token:', error);
            logout();
          });
        } else if (timeUntilExpiry <= 0) {
          // Token already expired
          logout();
        }
      } catch (error) {
        console.error('Error checking token expiration:', error);
      }
    };

    // Check every minute
    const interval = setInterval(checkTokenExpiration, 60 * 1000);
    return () => clearInterval(interval);
  }, []);

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
    setCurrentProjectState(null);
    localStorage.removeItem('current_organization_id');
    localStorage.removeItem('current_project_id');
  };

  const setCurrentOrganization = (org: Organization) => {
    setCurrentOrganizationState(org);
    setCurrentProjectState(null); // Reset project when changing organization
    localStorage.setItem('current_organization_id', org.id);
    localStorage.removeItem('current_project_id');
  };

  const setCurrentProject = (project: UserProjectInfo | null) => {
    setCurrentProjectState(project);
    if (project) {
      localStorage.setItem('current_project_id', project.project.id);
    } else {
      localStorage.removeItem('current_project_id');
    }
  };

  const value: AuthContextType = {
    user,
    organizations,
    currentOrganization,
    currentProject,
    loading,
    login,
    register,
    logout,
    setCurrentOrganization,
    setCurrentProject,
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