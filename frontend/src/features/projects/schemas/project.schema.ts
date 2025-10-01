/**
 * Project validation schemas
 *
 * @description Zod schemas for project-related form validation.
 * Provides type-safe validation for project creation and updates.
 *
 * @module project.schema
 */

import { z } from 'zod';

/**
 * Project creation schema
 *
 * @description Validation schema for creating a new project.
 * Matches backend ProjectCreate schema requirements.
 *
 * **Validation Rules**:
 * - name: Required, minimum 1 character, maximum 255 characters
 *
 * @example
 * ```typescript
 * import { createProjectSchema } from '@/features/projects/schemas';
 *
 * const result = createProjectSchema.safeParse({
 *   name: 'Q4 Marketing Campaign',
 * });
 *
 * if (result.success) {
 *   console.log('Valid data:', result.data);
 * }
 * ```
 */
export const createProjectSchema = z.object({
  name: z
    .string()
    .min(1, 'Project name is required')
    .max(255, 'Project name must be 255 characters or less')
    .trim(),
});

/**
 * Project creation form data type
 *
 * @description Inferred TypeScript type from createProjectSchema.
 * Use this type for form data in components.
 */
export type CreateProjectFormData = z.infer<typeof createProjectSchema>;

/**
 * Project update schema
 *
 * @description Validation schema for updating an existing project.
 * All fields are optional for partial updates.
 *
 * **Validation Rules**:
 * - name: Optional, minimum 1 character, maximum 255 characters
 *
 * @example
 * ```typescript
 * import { updateProjectSchema } from '@/features/projects/schemas';
 *
 * const result = updateProjectSchema.safeParse({
 *   name: 'Updated Project Name',
 * });
 * ```
 */
export const updateProjectSchema = z.object({
  name: z
    .string()
    .min(1, 'Project name is required')
    .max(255, 'Project name must be 255 characters or less')
    .trim()
    .optional(),
});

/**
 * Project update form data type
 *
 * @description Inferred TypeScript type from updateProjectSchema.
 */
export type UpdateProjectFormData = z.infer<typeof updateProjectSchema>;
