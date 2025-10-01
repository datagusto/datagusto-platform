/**
 * Project type definitions
 *
 * @description Type definitions for project-related data structures.
 * Maps to backend Pydantic schemas.
 *
 * @module project.types
 */

/**
 * Project response type
 *
 * @description Represents a project entity with all its properties.
 * Matches backend ProjectResponse schema.
 *
 * @property {string} id - Project UUID
 * @property {string} organization_id - Organization UUID this project belongs to
 * @property {string} name - Project display name
 * @property {string} created_by - User UUID who created the project
 * @property {string} created_at - ISO 8601 creation timestamp
 * @property {string} updated_at - ISO 8601 last update timestamp
 * @property {boolean} is_active - Whether project is active
 * @property {boolean} is_archived - Whether project is archived
 */
export interface Project {
  id: string;
  organization_id: string;
  name: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  is_archived: boolean;
}

/**
 * Project list response type
 *
 * @description Paginated project list response.
 * Matches backend ProjectListResponse schema.
 *
 * @property {Project[]} items - Array of projects
 * @property {number} total - Total number of projects
 * @property {number} page - Current page number (1-indexed)
 * @property {number} page_size - Number of items per page
 */
export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Project creation data type
 *
 * @description Data required to create a new project.
 * Matches backend ProjectCreate schema.
 *
 * @property {string} name - Project display name
 */
export interface ProjectCreate {
  name: string;
}

/**
 * Project update data type
 *
 * @description Data for updating a project.
 * All fields are optional for partial updates.
 * Matches backend ProjectUpdate schema.
 *
 * @property {string} [name] - Updated project name
 */
export interface ProjectUpdate {
  name?: string;
}

/**
 * Project member type
 *
 * @description Represents a project member.
 * Matches backend ProjectMemberResponse schema.
 *
 * @property {number} id - Membership record ID
 * @property {string} project_id - Project UUID
 * @property {string} user_id - Member user UUID
 * @property {string} created_at - ISO 8601 timestamp when user joined
 * @property {string} updated_at - ISO 8601 last update timestamp
 */
export interface ProjectMember {
  id: number;
  project_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

/**
 * Project owner type
 *
 * @description Represents project ownership.
 * Matches backend ProjectOwnerResponse schema.
 *
 * @property {string} project_id - Project UUID
 * @property {string} user_id - Owner user UUID
 * @property {string} created_at - ISO 8601 timestamp when ownership was established
 * @property {string} updated_at - ISO 8601 last update timestamp
 */
export interface ProjectOwner {
  project_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}
