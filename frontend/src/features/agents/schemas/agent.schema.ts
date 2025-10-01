/**
 * Agent validation schemas
 *
 * @description Zod schemas for agent-related form validation.
 * Provides type-safe validation for agent creation and updates.
 *
 * @module agent.schema
 */

import { z } from 'zod';

/**
 * Agent creation schema
 *
 * @description Validation schema for creating a new agent.
 * Matches backend AgentCreate schema requirements.
 *
 * **Validation Rules**:
 * - name: Required, minimum 1 character, maximum 255 characters
 *
 * @example
 * ```typescript
 * import { createAgentSchema } from '@/features/agents/schemas';
 *
 * const result = createAgentSchema.safeParse({
 *   name: 'Production API Agent',
 * });
 *
 * if (result.success) {
 *   console.log('Valid data:', result.data);
 * }
 * ```
 */
export const createAgentSchema = z.object({
  name: z
    .string()
    .min(1, 'Agent name is required')
    .max(255, 'Agent name must be 255 characters or less')
    .trim(),
});

/**
 * Agent creation form data type
 *
 * @description Inferred TypeScript type from createAgentSchema.
 * Use this type for form data in components.
 */
export type CreateAgentFormData = z.infer<typeof createAgentSchema>;

/**
 * Agent update schema
 *
 * @description Validation schema for updating an existing agent.
 * All fields are optional for partial updates.
 *
 * **Validation Rules**:
 * - name: Optional, minimum 1 character, maximum 255 characters
 *
 * @example
 * ```typescript
 * import { updateAgentSchema } from '@/features/agents/schemas';
 *
 * const result = updateAgentSchema.safeParse({
 *   name: 'Updated Agent Name',
 * });
 * ```
 */
export const updateAgentSchema = z.object({
  name: z
    .string()
    .min(1, 'Agent name is required')
    .max(255, 'Agent name must be 255 characters or less')
    .trim()
    .optional(),
});

/**
 * Agent update form data type
 *
 * @description Inferred TypeScript type from updateAgentSchema.
 */
export type UpdateAgentFormData = z.infer<typeof updateAgentSchema>;
