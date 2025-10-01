/**
 * useCreateProject hook
 *
 * @description TanStack Query hook for creating a new project.
 * Provides mutation for project creation with automatic cache invalidation.
 *
 * @module use-create-project
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectService } from '../services';
import type { ProjectCreate, Project } from '../types';

/**
 * useCreateProject hook
 *
 * @description Creates a mutation hook for project creation.
 * Automatically invalidates project list queries on success.
 *
 * **Features**:
 * - Mutation for creating projects
 * - Automatic query invalidation on success
 * - Error handling
 * - Loading state management
 *
 * **Success Behavior**:
 * - Invalidates 'projects' query to refetch project list
 * - Can be extended with onSuccess callback
 *
 * @returns TanStack Query mutation object
 *
 * @example
 * ```typescript
 * import { useCreateProject } from '@/features/projects/hooks';
 *
 * function CreateProjectDialog() {
 *   const createMutation = useCreateProject();
 *
 *   const handleSubmit = (data: ProjectCreate) => {
 *     createMutation.mutate(data, {
 *       onSuccess: (project) => {
 *         console.log('Created:', project.id);
 *         closeDialog();
 *       },
 *     });
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       <input name="name" />
 *       <button disabled={createMutation.isPending}>
 *         {createMutation.isPending ? 'Creating...' : 'Create'}
 *       </button>
 *       {createMutation.error && <p>{createMutation.error.message}</p>}
 *     </form>
 *   );
 * }
 * ```
 */
export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation<Project, Error, ProjectCreate>({
    mutationFn: (data: ProjectCreate) => projectService.createProject(data),
    onSuccess: () => {
      // Invalidate projects query to trigger refetch
      // Note: The actual refetch is triggered by the parent component
      // when the dialog closes via refetchTrigger state change
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}
