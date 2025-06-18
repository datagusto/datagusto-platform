import type { 
  Organization, 
  UserOrganizationInfo, 
  OrganizationWithMembers,
  OrganizationUpdateData 
} from '@/types/organization';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class OrganizationService {
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  async getUserOrganizations(): Promise<UserOrganizationInfo[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/organizations/`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch organizations');
    }

    return response.json();
  }

  async getOrganizationDetails(orgId: string): Promise<OrganizationWithMembers> {
    const response = await fetch(`${API_BASE_URL}/api/v1/organizations/${orgId}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch organization details');
    }

    return response.json();
  }

  async updateOrganization(orgId: string, data: OrganizationUpdateData): Promise<Organization> {
    const response = await fetch(`${API_BASE_URL}/api/v1/organizations/${orgId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update organization');
    }

    return response.json();
  }
}

export const organizationService = new OrganizationService();