/**
 * Project service
 *
 * @description Service for managing projects within an organization.
 * Provides methods to fetch, create, update, and delete projects.
 *
 * **Note**: All methods require X-Organization-ID header, which is automatically
 * added by the API client from the current organization in Zustand store.
 *
 * @module project.service
 */

import { get, post, patch, del } from '@/shared/lib/api-client';
import type {
  Project,
  ProjectListResponse,
  ProjectCreate,
  ProjectUpdate,
} from '../types';

/**
 * Project service interface
 *
 * @description Service object containing project-related API methods.
 * All methods are async and return Promises.
 *
 * @example
 * ```typescript
 * import { projectService } from '@/features/projects/services';
 *
 * // List projects in current organization
 * const response = await projectService.listProjects();
 * console.log('Projects:', response.items);
 * ```
 */
export const projectService = {
  /**
   * Get list of projects in the organization
   *
   * @description Fetches paginated list of projects for the current organization.
   * Uses the GET /projects endpoint with X-Organization-ID header.
   *
   * @param params - Query parameters for filtering and pagination
   * @param params.page - Page number (1-indexed, default: 1)
   * @param params.page_size - Items per page (default: 20, max: 100)
   * @param params.is_active - Filter by active status
   * @param params.is_archived - Filter by archived status
   * @returns Promise resolving to paginated project list
   * @throws {ApiError} When request fails or user is not authenticated
   *
   * @example
   * ```typescript
   * // Get first page of active projects
   * const response = await projectService.listProjects({
   *   page: 1,
   *   page_size: 20,
   *   is_active: true,
   *   is_archived: false,
   * });
   *
   * console.log('Total projects:', response.total);
   * response.items.forEach(project => {
   *   console.log(`- ${project.name} (${project.id})`);
   * });
   * ```
   */
  async listProjects(params?: {
    page?: number;
    page_size?: number;
    is_active?: boolean;
    is_archived?: boolean;
  }): Promise<ProjectListResponse> {
    const queryParams = new URLSearchParams();

    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size)
      queryParams.append('page_size', params.page_size.toString());
    if (params?.is_active !== undefined)
      queryParams.append('is_active', params.is_active.toString());
    if (params?.is_archived !== undefined)
      queryParams.append('is_archived', params.is_archived.toString());

    const query = queryParams.toString();
    const endpoint = query ? `/projects?${query}` : '/projects';

    return get<ProjectListResponse>(endpoint);
  },

  /**
   * Get project details by ID
   *
   * @description Fetches detailed information for a specific project.
   * Uses the GET /projects/{project_id} endpoint.
   *
   * @param projectId - Project UUID
   * @returns Promise resolving to project details
   * @throws {ApiError} When project not found or user lacks access
   *
   * @example
   * ```typescript
   * const project = await projectService.getProject('123e4567-e89b-12d3-a456-426614174000');
   * console.log('Project name:', project.name);
   * console.log('Created by:', project.created_by);
   * ```
   */
  async getProject(projectId: string): Promise<Project> {
    return get<Project>(`/projects/${projectId}`);
  },

  /**
   * Create a new project
   *
   * @description Creates a new project in the current organization.
   * User automatically becomes project owner and member.
   * Uses the POST /projects endpoint.
   *
   * @param data - Project creation data
   * @returns Promise resolving to created project
   * @throws {ApiError} When creation fails
   *
   * @example
   * ```typescript
   * const newProject = await projectService.createProject({
   *   name: 'Q4 Marketing Campaign',
   * });
   *
   * console.log('Created project:', newProject.id);
   * console.log('Is active:', newProject.is_active); // true
   * ```
   */
  async createProject(data: ProjectCreate): Promise<Project> {
    return post<Project>('/projects', data);
  },

  /**
   * Update project information
   *
   * @description Updates project details (currently only name).
   * Only project owner or organization admin can update.
   * Uses the PATCH /projects/{project_id} endpoint.
   *
   * @param projectId - Project UUID
   * @param data - Project update data
   * @returns Promise resolving to updated project
   * @throws {ApiError} When update fails or user lacks permission
   *
   * @example
   * ```typescript
   * const updated = await projectService.updateProject(
   *   '123e4567-e89b-12d3-a456-426614174000',
   *   { name: 'Updated Project Name' }
   * );
   * console.log('New name:', updated.name);
   * ```
   */
  async updateProject(
    projectId: string,
    data: ProjectUpdate
  ): Promise<Project> {
    return patch<Project>(`/projects/${projectId}`, data);
  },

  /**
   * Archive a project (soft delete)
   *
   * @description Archives a project, marking it as deleted.
   * Only project owner or organization admin can archive.
   * Uses the DELETE /projects/{project_id} endpoint.
   *
   * @param projectId - Project UUID
   * @param reason - Optional reason for archiving
   * @returns Promise resolving when archive succeeds
   * @throws {ApiError} When archive fails or user lacks permission
   *
   * @example
   * ```typescript
   * await projectService.archiveProject(
   *   '123e4567-e89b-12d3-a456-426614174000',
   *   'Project completed successfully'
   * );
   * console.log('Project archived');
   * ```
   */
  async archiveProject(projectId: string, reason?: string): Promise<void> {
    return del(`/projects/${projectId}`, {
      body: reason ? JSON.stringify({ reason }) : undefined,
    });
  },
};
