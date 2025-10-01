/**
 * API Key validation schemas
 *
 * @description Zod schemas for API key form validation.
 *
 * @module api-key.schema
 */

import { z } from 'zod';

/**
 * API Key creation schema
 *
 * @description Validates API key creation form data.
 */
export const createAPIKeySchema = z.object({
  name: z
    .string()
    .max(255, 'Name must be 255 characters or less')
    .optional()
    .or(z.literal('')),
});

/**
 * API Key creation form data type
 */
export type CreateAPIKeyFormData = z.infer<typeof createAPIKeySchema>;
