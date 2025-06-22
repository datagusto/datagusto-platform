import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectService } from '@/services';
import { queryKeys } from '@/lib/query-client';
import type { UserProjectInfo, ProjectCreateData, ProjectUpdateData } from '@/types';

export function useUserProjects() {
  return useQuery({
    queryKey: queryKeys.userProjects(),
    queryFn: () => projectService.getUserProjects(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useOrganizationProjects(orgId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.organizationProjects(orgId || ''),
    queryFn: () => projectService.getOrganizationProjects(orgId!),
    enabled: !!orgId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.project(projectId || ''),
    queryFn: () => projectService.getProjectDetails(projectId!),
    enabled: !!projectId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: ProjectCreateData) => projectService.createProject(data),
    onSuccess: (newProject, variables) => {
      // Invalidate and refetch user projects
      queryClient.invalidateQueries({ queryKey: queryKeys.userProjects() });
      
      // Invalidate organization projects if we know the org
      if (variables.organization_id) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.organizationProjects(variables.organization_id) 
        });
      }
      
      // Optimistically add the new project to the cache
      queryClient.setQueryData<UserProjectInfo[]>(
        queryKeys.userProjects(),
        (oldData) => {
          if (!oldData) return oldData;
          
          const newProjectInfo: UserProjectInfo = {
            project: newProject,
            membership: {
              id: '',
              user_id: '',
              project_id: newProject.id,
              role: 'owner',
              joined_at: new Date().toISOString(),
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
            is_owner: true,
          };
          
          return [...oldData, newProjectInfo];
        }
      );
    },
    onError: (error) => {
      console.error('Failed to create project:', error);
    },
  });
}

export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: ProjectUpdateData) => projectService.updateProject(projectId, data),
    onSuccess: (updatedProject) => {
      // Update the specific project in cache
      queryClient.setQueryData(queryKeys.project(projectId), updatedProject);
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.userProjects() });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.organizationProjects(updatedProject.organization_id) 
      });
    },
    onError: (error) => {
      console.error('Failed to update project:', error);
    },
  });
}

export function useDeleteProject(projectId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => projectService.deleteProject(projectId),
    onSuccess: (_, variables) => {
      // Remove from all relevant caches
      queryClient.removeQueries({ queryKey: queryKeys.project(projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.userProjects() });
      queryClient.invalidateQueries({ queryKey: queryKeys.organizations() });
    },
    onError: (error) => {
      console.error('Failed to delete project:', error);
    },
  });
}