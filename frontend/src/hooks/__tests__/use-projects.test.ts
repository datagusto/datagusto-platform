import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useUserProjects, useCreateProject } from '../use-projects';
import { projectService } from '@/services';

// Mock the project service
vi.mock('@/services', () => ({
  projectService: {
    getUserProjects: vi.fn(),
    createProject: vi.fn(),
  },
}));

// Create a wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('useUserProjects', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches user projects successfully', async () => {
    const mockProjects = [
      {
        project: {
          id: '1',
          name: 'Project 1',
          organization_id: 'org-1',
          platform_type: 'langfuse',
          platform_config: {},
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
        membership: {
          id: '1',
          user_id: 'user-1',
          project_id: '1',
          role: 'owner' as const,
          joined_at: '2024-01-01',
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      },
    ];

    vi.mocked(projectService.getUserProjects).mockResolvedValue(mockProjects);

    const { result } = renderHook(() => useUserProjects(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockProjects);
    expect(projectService.getUserProjects).toHaveBeenCalledTimes(1);
  });

  it('handles error when fetching projects fails', async () => {
    const mockError = new Error('Failed to fetch projects');
    vi.mocked(projectService.getUserProjects).mockRejectedValue(mockError);

    const { result } = renderHook(() => useUserProjects(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(mockError);
  });
});

describe('useCreateProject', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('creates project successfully', async () => {
    const mockProject = {
      id: '1',
      name: 'New Project',
      organization_id: 'org-1',
      platform_type: 'langfuse',
      platform_config: {},
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
    };

    const mockProjectData = {
      name: 'New Project',
      organization_id: 'org-1',
      platform_type: 'langfuse',
      platform_config: {},
    };

    vi.mocked(projectService.createProject).mockResolvedValue(mockProject);

    const { result } = renderHook(() => useCreateProject(), {
      wrapper: createWrapper(),
    });

    result.current.mutate(mockProjectData);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockProject);
    expect(projectService.createProject).toHaveBeenCalledWith(mockProjectData);
  });

  it('handles error when creating project fails', async () => {
    const mockError = new Error('Failed to create project');
    const mockProjectData = {
      name: 'New Project',
      organization_id: 'org-1',
      platform_type: 'langfuse',
      platform_config: {},
    };

    vi.mocked(projectService.createProject).mockRejectedValue(mockError);

    const { result } = renderHook(() => useCreateProject(), {
      wrapper: createWrapper(),
    });

    result.current.mutate(mockProjectData);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(mockError);
  });
});