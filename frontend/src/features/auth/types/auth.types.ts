/**
 * Authentication type definitions
 *
 * @description TypeScript types and interfaces for authentication-related data structures.
 * These types match the backend API specification and ensure type safety across the auth feature.
 *
 * @module auth.types
 */

/**
 * User data structure
 *
 * @interface User
 * @description Represents an authenticated user in the system.
 * Returned by the `/api/v1/auth/me` endpoint and stored in Zustand store.
 * Matches the backend UserAuth schema.
 *
 * @property {string} id - Unique user identifier (UUID)
 * @property {string} organization_id - Organization identifier (UUID)
 * @property {string} email - User's email address (unique)
 * @property {string} [name] - User's display name (optional)
 * @property {string} [bio] - User biography (optional)
 * @property {string} [avatar_url] - Avatar image URL (optional)
 * @property {boolean} is_active - Whether the user account is active
 * @property {boolean} is_suspended - Whether the user is suspended
 * @property {boolean} is_archived - Whether the user is archived
 * @property {string} [created_at] - ISO 8601 timestamp of account creation (optional)
 * @property {string} [updated_at] - ISO 8601 timestamp of last update (optional)
 *
 * @example
 * ```typescript
 * const user: User = {
 *   id: '123e4567-e89b-12d3-a456-426614174000',
 *   organization_id: '456e7890-e12b-34c5-a678-123456789000',
 *   email: 'user@example.com',
 *   name: 'John Doe',
 *   bio: 'Software engineer',
 *   avatar_url: 'https://example.com/avatar.jpg',
 *   is_active: true,
 *   is_suspended: false,
 *   is_archived: false,
 *   created_at: '2024-01-15T10:30:00Z',
 *   updated_at: '2024-01-15T10:30:00Z',
 * };
 * ```
 */
export interface User {
  /** Unique user identifier (UUID format) */
  id: string;

  /** User's email address (unique, used for login) */
  email: string;

  /** User's display name (optional) */
  name?: string;

  /** User biography (optional) */
  bio?: string;

  /** Avatar image URL (optional) */
  avatar_url?: string;

  /** Whether the user account is active (can be deactivated by admin) */
  is_active: boolean;

  /** Whether the user is suspended */
  is_suspended: boolean;

  /** Whether the user is archived (soft delete) */
  is_archived: boolean;

  /** ISO 8601 timestamp of when the account was created (optional) */
  created_at?: string;

  /** ISO 8601 timestamp of when the account was last updated (optional) */
  updated_at?: string;
}

/**
 * Login credentials
 *
 * @interface LoginCredentials
 * @description Data structure for user login requests.
 * Used as payload for the `/api/v1/auth/token` endpoint.
 *
 * @property {string} email - User's email address
 * @property {string} password - User's password (plain text, encrypted in transit via HTTPS)
 *
 * @example
 * ```typescript
 * const credentials: LoginCredentials = {
 *   email: 'user@example.com',
 *   password: 'securePassword123',
 * };
 *
 * const response = await authService.login(credentials);
 * ```
 */
export interface LoginCredentials {
  /** User's email address for authentication */
  email: string;

  /** User's password (sent over HTTPS, never stored in plain text on server) */
  password: string;
}

/**
 * User registration data
 *
 * @interface RegisterData
 * @description Data structure for new user registration.
 * Used as payload for the `/api/v1/auth/register` endpoint.
 * Matches the backend UserCreate schema.
 *
 * @property {string} email - New user's email address (must be unique)
 * @property {string} password - New user's password (plain text, will be hashed on server)
 * @property {string} name - New user's display name (required)
 * @property {string} [organization_name] - Organization name (optional, creates new org if provided)
 *
 * @example
 * ```typescript
 * const registrationData: RegisterData = {
 *   email: 'newuser@example.com',
 *   password: 'securePassword123',
 *   name: 'Jane Doe',
 *   organization_name: 'My Company',
 * };
 *
 * const newUser = await authService.register(registrationData);
 * ```
 */
export interface RegisterData {
  /** Email address for the new account (must be unique in the system) */
  email: string;

  /** Password for the new account (will be hashed server-side) */
  password: string;

  /** Display name for the new user (required) */
  name: string;

  /** Organization name (optional, creates new organization if provided) */
  organization_name?: string;
}

/**
 * Token response from authentication
 *
 * @interface TokenResponse
 * @description Response from login/token endpoints containing JWT tokens and user data.
 * Access token is used for API authentication, refresh token for obtaining new access tokens.
 * Matches the backend UserAuth schema.
 *
 * @property {string} user_id - User UUID
 * @property {string} email - User's email address
 * @property {string} [name] - User's display name (optional)
 * @property {string} access_token - JWT access token (short-lived, e.g., 15 minutes)
 * @property {string} refresh_token - JWT refresh token (long-lived, e.g., 7 days)
 * @property {"bearer"} token_type - OAuth 2.0 token type (always "bearer")
 *
 * @example
 * ```typescript
 * // Login response
 * const tokens: TokenResponse = {
 *   user_id: '123e4567-e89b-12d3-a456-426614174000',
 *   email: 'user@example.com',
 *   name: 'John Doe',
 *   access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
 *   refresh_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
 *   token_type: 'bearer',
 * };
 *
 * // Use access token in Authorization header
 * fetch('/api/v1/data', {
 *   headers: {
 *     Authorization: `Bearer ${tokens.access_token}`,
 *   },
 * });
 * ```
 */
export interface TokenResponse {
  /** User UUID */
  user_id: string;

  /** User's email address */
  email: string;

  /** User's display name (optional) */
  name?: string;

  /** JWT access token for API authentication (include in Authorization header) */
  access_token: string;

  /** JWT refresh token for obtaining new access tokens */
  refresh_token: string;

  /** OAuth 2.0 token type (always "bearer" for JWT tokens) */
  token_type: 'bearer';
}

/**
 * API error response
 *
 * @interface ApiError
 * @description Standard error response format from the backend API.
 * All API errors follow this structure for consistent error handling.
 *
 * @property {string} detail - Human-readable error message describing what went wrong
 *
 * @example
 * ```typescript
 * // Example error response
 * const error: ApiError = {
 *   detail: 'Invalid email or password',
 * };
 * ```
 *
 * @example
 * ```typescript
 * // Error handling
 * try {
 *   await authService.login(credentials);
 * } catch (error) {
 *   if (error instanceof Error) {
 *     const apiError = error as ApiError;
 *     console.error('Login failed:', apiError.detail);
 *   }
 * }
 * ```
 */
export interface ApiError {
  /** Human-readable error message from the API */
  detail: string;
}

/**
 * User organization membership
 *
 * @interface UserOrganization
 * @description Organization membership information for a user.
 * Users can belong to multiple organizations with different roles.
 *
 * @property {string} id - Organization UUID
 * @property {string} name - Organization name
 * @property {'owner' | 'admin' | 'member'} role - User's role in this organization
 * @property {string} [joined_at] - ISO 8601 timestamp of when user joined (optional)
 *
 * @example
 * ```typescript
 * const org: UserOrganization = {
 *   id: '456e7890-e12b-34c5-a678-123456789000',
 *   name: 'Acme Corp',
 *   role: 'owner',
 *   joined_at: '2024-01-15T10:30:00Z',
 * };
 * ```
 */
export interface UserOrganization {
  /** Organization UUID */
  id: string;

  /** Organization name */
  name: string;

  /** User's role in this organization */
  role: 'owner' | 'admin' | 'member';

  /** ISO 8601 timestamp of when user joined this organization (optional) */
  joined_at?: string;
}
