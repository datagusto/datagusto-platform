export interface Project {
  id: string;
  name: string;
  description?: string;
  organization_id: string;
  platform_type: string;
  platform_config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ProjectWithApiKey extends Project {
  api_key: string;
}

export interface ProjectMember {
  id: string;
  user_id: string;
  project_id: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  invited_by?: string;
  joined_at: string;
  created_at: string;
  updated_at: string;
}

export interface UserProjectInfo {
  project: Project;
  membership: ProjectMember;
}

export interface ProjectWithMembers extends Project {
  members: ProjectMember[];
}

export interface ProjectCreateData {
  name: string;
  description?: string;
  organization_id: string;
  platform_type: string;
  platform_config: Record<string, any>;
}

export interface ProjectUpdateData {
  name?: string;
  description?: string;
  platform_type?: string;
  platform_config?: Record<string, any>;
}

export interface ApiKeyResponse {
  api_key: string;
  message: string;
}

export interface TraceSyncStatus {
  project_id: string;
  total_traces: number;
  new_traces: number;
  updated_traces: number;
  sync_started_at: string;
  sync_completed_at?: string;
  error?: string;
}