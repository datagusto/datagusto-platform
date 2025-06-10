export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  avatar_url?: string;
  settings: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrganizationMember {
  id: string;
  user_id: string;
  organization_id: string;
  role: 'owner' | 'admin' | 'member';
  invited_by?: string;
  joined_at: string;
  created_at: string;
  updated_at: string;
}

export interface UserOrganizationInfo {
  organization: Organization;
  membership: OrganizationMember;
}

export interface OrganizationWithMembers extends Organization {
  members: OrganizationMember[];
}

export interface OrganizationCreateData {
  name: string;
  description?: string;
  avatar_url?: string;
}

export interface OrganizationUpdateData {
  name?: string;
  description?: string;
  avatar_url?: string;
  settings?: Record<string, any>;
}