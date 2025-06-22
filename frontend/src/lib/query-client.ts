import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors except 401
        if (error?.status >= 400 && error?.status < 500 && error?.status !== 401) {
          return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: (failureCount, error: any) => {
        // Don't retry mutations on client errors
        if (error?.status >= 400 && error?.status < 500) {
          return false;
        }
        return failureCount < 2;
      },
    },
  },
});

// Query keys factory for better organization
export const queryKeys = {
  all: ['datagusto'] as const,
  
  // Projects
  projects: () => [...queryKeys.all, 'projects'] as const,
  userProjects: () => [...queryKeys.projects(), 'user'] as const,
  organizationProjects: (orgId: string) => [...queryKeys.projects(), 'organization', orgId] as const,
  project: (projectId: string) => [...queryKeys.projects(), projectId] as const,
  
  // Traces
  traces: () => [...queryKeys.all, 'traces'] as const,
  projectTraces: (projectId: string, params?: Record<string, any>) => 
    [...queryKeys.traces(), 'project', projectId, params] as const,
  trace: (traceId: string) => [...queryKeys.traces(), traceId] as const,
  
  // Organizations
  organizations: () => [...queryKeys.all, 'organizations'] as const,
  userOrganizations: () => [...queryKeys.organizations(), 'user'] as const,
  organization: (orgId: string) => [...queryKeys.organizations(), orgId] as const,
  
  // Guardrails
  guardrails: () => [...queryKeys.all, 'guardrails'] as const,
  projectGuardrails: (projectId: string) => [...queryKeys.guardrails(), 'project', projectId] as const,
  guardrail: (guardrailId: string) => [...queryKeys.guardrails(), guardrailId] as const,
} as const;