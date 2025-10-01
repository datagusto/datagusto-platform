/**
 * Organization service
 *
 * @description Service for managing user organization memberships.
 * Provides methods to fetch organizations the current user belongs to.
 *
 * @module organization.service
 */

import { get } from '@/shared/lib/api-client';
import type { UserOrganization } from '../types';

/**
 * Organization details interface
 *
 * @interface Organization
 * @description Full organization details from the API
 */
export interface Organization {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

/**
 * Organization service interface
 *
 * @description Service object containing organization-related API methods.
 * All methods are async and return Promises.
 *
 * @example
 * ```typescript
 * import { organizationService } from '@/features/auth/services';
 *
 * // Fetch user's organizations
 * const orgs = await organizationService.listMyOrganizations();
 * console.log('User belongs to', orgs.length, 'organizations');
 * ```
 */
export const organizationService = {
  /**
   * Get list of organizations current user belongs to
   *
   * @description Fetches all organizations the authenticated user is a member of.
   * Uses the GET /auth/me/organizations endpoint.
   *
   * @returns Promise resolving to array of UserOrganization objects
   * @throws {ApiError} When request fails or user is not authenticated
   *
   * @example
   * ```typescript
   * try {
   *   const organizations = await organizationService.listMyOrganizations();
   *
   *   if (organizations.length === 0) {
   *     console.log('User does not belong to any organization');
   *   } else if (organizations.length === 1) {
   *     console.log('Auto-selecting organization:', organizations[0].name);
   *   } else {
   *     console.log('User can choose from', organizations.length, 'organizations');
   *   }
   * } catch (error) {
   *   console.error('Failed to fetch organizations:', error);
   * }
   * ```
   */
  async listMyOrganizations(): Promise<UserOrganization[]> {
    const response = await get<{ organizations: UserOrganization[] }>(
      '/auth/me/organizations'
    );
    return response.organizations;
  },

  /**
   * Get organization details by ID
   *
   * @description Fetches detailed information for a specific organization.
   * Uses the GET /organizations/{organization_id} endpoint.
   *
   * @param organizationId - Organization UUID
   * @returns Promise resolving to organization details
   * @throws {ApiError} When organization not found or user lacks access
   *
   * @example
   * ```typescript
   * const org = await organizationService.getOrganization('123e4567-e89b-12d3-a456-426614174000');
   * console.log('Organization name:', org.name);
   * ```
   */
  async getOrganization(organizationId: string): Promise<Organization> {
    return get<Organization>(`/organizations/${organizationId}`);
  },
};