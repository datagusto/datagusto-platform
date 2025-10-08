/**
 * Create agent form component
 *
 * @description Form component for creating a new agent.
 * Simple form with only agent name input field.
 *
 * **Features**:
 * - Agent name input field
 * - Validation with Zod
 * - react-hook-form for form state management
 * - Error message display
 * - Loading state during submission
 *
 * @module create-agent-form
 */

'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createAgentSchema, type CreateAgentFormData } from '../schemas';

/**
 * Create agent form props
 *
 * @property {function} onSubmit - Form submission handler
 * @property {boolean} [isLoading] - Loading state from mutation
 * @property {Error | null} [error] - Error from mutation
 */
interface CreateAgentFormProps {
  onSubmit: (data: CreateAgentFormData) => void;
  isLoading?: boolean;
  error?: Error | null;
}

/**
 * Create agent form component
 *
 * @description Renders a form with agent name input field.
 * Handles validation, submission, and error display.
 *
 * **Form Fields**:
 * - Name: Required, minimum 1 character, maximum 255 characters
 *
 * **Validation**:
 * - Client-side validation with Zod schema
 * - Real-time error messages
 * - Submit button disabled during submission
 *
 * **Flow**:
 * 1. User enters agent name
 * 2. Client-side validation on blur/submit
 * 3. On submit, call onSubmit callback
 * 4. Parent component handles API call
 * 5. On error, display error message
 *
 * @example
 * ```tsx
 * <CreateAgentForm
 *   onSubmit={(data) => createMutation.mutate(data)}
 *   isLoading={createMutation.isPending}
 *   error={createMutation.error}
 * />
 * ```
 */
export function CreateAgentForm({
  onSubmit,
  isLoading,
  error,
}: CreateAgentFormProps) {
  // Form state management with react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateAgentFormData>({
    resolver: zodResolver(createAgentSchema),
    defaultValues: {
      name: '',
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* API Error Display */}
      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
          {error.message || 'Failed to create agent'}
        </div>
      )}

      {/* Agent Name Field */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium mb-1">
          Agent Name
        </label>
        <input
          id="name"
          type="text"
          className="w-full border rounded-md px-3 py-2"
          placeholder="Enter agent name"
          autoFocus
          {...register('name')}
        />
        {errors.name && (
          <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isSubmitting || isLoading}
        className="w-full bg-black text-white rounded-md py-2 disabled:opacity-60"
      >
        {isLoading ? 'Adding...' : 'Add Agent'}
      </button>
    </form>
  );
}
