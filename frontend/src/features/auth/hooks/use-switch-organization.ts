/**
 * Organization switching hook
 *
 * @description Custom hook for managing organization switching functionality.
 * Fetches user's organizations and provides methods to switch between them.
 *
 * **Features**:
 * - Fetches all organizations user belongs to
 * - Identifies currently selected organization
 * - Provides switch method with automatic page reload
 * - Loading and error states
 *
 * @module use-switch-organization
 */

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { organizationService } from '../services';
import { useAuthStore } from '../stores';
import type { UserOrganization } from '../types';

/**
 * Organization switching hook return type
 *
 * @interface UseSwitchOrganizationReturn
 */
interface UseSwitchOrganizationReturn {
  /** All organizations user belongs to */
  organizations: UserOrganization[];

  /** Currently selected organization ID */
  currentOrganizationId: string | null;

  /** Currently selected organization object */
  currentOrganization: UserOrganization | undefined;

  /** Whether organizations are being fetched */
  isLoading: boolean;

  /** Error if fetching organizations failed */
  error: Error | null;

  /** Switch to a different organization */
  switchOrganization: (organizationId: string) => void;

  /** Refetch organizations */
  refetch: () => void;
}

/**
 * Organization switching hook
 *
 * @description React hook for managing organization switching. Fetches user's organizations
 * using TanStack Query for optimal caching and provides a switch method.
 *
 * **Usage Pattern**:
 * 1. Hook fetches organizations on mount
 * 2. Component displays list of organizations
 * 3. User clicks to switch organization
 * 4. `switchOrganization()` updates state and reloads page
 *
 * **State Management**:
 * - Organizations cached by TanStack Query (5 minutes)
 * - Current organization ID stored in Zustand (persisted)
 * - Page reload ensures all components use new organization context
 *
 * **Performance**:
 * - TanStack Query caches results (avoids repeated API calls)
 * - Stale time: 5 minutes
 * - Cache time: 10 minutes
 *
 * @returns {UseSwitchOrganizationReturn} Hook result with organizations and switch method
 *
 * @example
 * ```tsx
 * import { useSwitchOrganization } from '@/features/auth/hooks';
 *
 * function OrganizationSwitcher() {
 *   const {
 *     organizations,
 *     currentOrganizationId,
 *     isLoading,
 *     switchOrganization,
 *   } = useSwitchOrganization();
 *
 *   if (isLoading) return <div>Loading...</div>;
 *
 *   return (
 *     <div>
 *       {organizations.map((org) => (
 *         <button
 *           key={org.id}
 *           onClick={() => switchOrganization(org.id)}
 *           disabled={org.id === currentOrganizationId}
 *         >
 *           {org.name} {org.id === currentOrganizationId && '✓'}
 *         </button>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // In a dropdown menu
 * function UserMenu() {
 *   const { organizations, currentOrganization, switchOrganization } =
 *     useSwitchOrganization();
 *
 *   return (
 *     <Menu>
 *       <MenuItem disabled>
 *         Current: {currentOrganization?.name}
 *       </MenuItem>
 *       <MenuDivider />
 *       {organizations
 *         .filter((org) => org.id !== currentOrganization?.id)
 *         .map((org) => (
 *           <MenuItem
 *             key={org.id}
 *             onClick={() => switchOrganization(org.id)}
 *           >
 *             {org.name}
 *           </MenuItem>
 *         ))}
 *     </Menu>
 *   );
 * }
 * ```
 */
export function useSwitchOrganization(): UseSwitchOrganizationReturn {
  const _router = useRouter();
  const currentOrganizationId = useAuthStore(
    (state) => state.currentOrganizationId
  );
  const setCurrentOrganization = useAuthStore(
    (state) => state.setCurrentOrganization
  );

  // Fetch organizations using TanStack Query
  const {
    data: organizations = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['organizations', 'my-organizations'],
    queryFn: () => organizationService.listMyOrganizations(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    retry: 2,
  });

  // Find current organization object
  const currentOrganization = organizations.find(
    (org) => org.id === currentOrganizationId
  );

  /**
   * Switch to a different organization
   *
   * @description Updates current organization ID in Zustand store and reloads the page.
   * Page reload ensures all components and cached data use the new organization context.
   *
   * @param organizationId - UUID of organization to switch to
   *
   * @example
   * ```typescript
   * switchOrganization('456e7890-e12b-34c5-a678-123456789000');
   * // Page reloads with new organization context
   * ```
   */
  const switchOrganization = (organizationId: string) => {
    // Validate organization exists
    const targetOrg = organizations.find((org) => org.id === organizationId);
    if (!targetOrg) {
      console.error('Organization not found:', organizationId);
      return;
    }

    // Don't switch if already current
    if (organizationId === currentOrganizationId) {
      return;
    }

    // Update current organization in Zustand
    setCurrentOrganization(organizationId);

    // Reload page to ensure all components use new organization context
    // This is simpler than invalidating all organization-specific queries
    window.location.reload();
  };

  return {
    organizations,
    currentOrganizationId,
    currentOrganization,
    isLoading,
    error: error as Error | null,
    switchOrganization,
    refetch,
  };
}
