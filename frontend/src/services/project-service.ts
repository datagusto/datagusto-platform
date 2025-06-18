import type {
  Project,
  UserProjectInfo,
  ProjectWithMembers,
  ProjectCreateData,
  ProjectUpdateData,
  ApiKeyResponse,
  TraceSyncStatus
} from '@/types/project';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ProjectService {
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  async getUserProjects(): Promise<UserProjectInfo[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch projects');
    }

    return response.json();
  }

  async getOrganizationProjects(orgId: string): Promise<Project[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/organization/${orgId}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch organization projects');
    }

    return response.json();
  }

  async createProject(data: ProjectCreateData): Promise<Project> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create project');
    }

    return response.json();
  }

  async getProjectDetails(projectId: string): Promise<ProjectWithMembers> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch project details');
    }

    return response.json();
  }

  async updateProject(projectId: string, data: ProjectUpdateData): Promise<Project> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update project');
    }

    return response.json();
  }

  async deleteProject(projectId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete project');
    }
  }

  async getProjectApiKey(projectId: string): Promise<ApiKeyResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/api-key`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get API key');
    }

    return response.json();
  }

  async regenerateApiKey(projectId: string): Promise<ApiKeyResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/regenerate-api-key`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to regenerate API key');
    }

    return response.json();
  }

  async syncLangfuseData(projectId: string): Promise<TraceSyncStatus> {
    const response = await fetch(`${API_BASE_URL}/api/v1/traces/${projectId}/sync`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to sync Langfuse data');
    }

    return response.json();
  }
}

export const projectService = new ProjectService();