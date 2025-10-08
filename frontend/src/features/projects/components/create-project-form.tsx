/**
 * Create project form component
 *
 * @description Form component for creating a new project.
 * Simple form with only project name input field.
 *
 * **Features**:
 * - Project name input field
 * - Validation with Zod
 * - react-hook-form for form state management
 * - Error message display
 * - Loading state during submission
 *
 * @module create-project-form
 */

'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createProjectSchema, type CreateProjectFormData } from '../schemas';

/**
 * Create project form props
 *
 * @property {function} onSubmit - Form submission handler
 * @property {boolean} [isLoading] - Loading state from mutation
 * @property {Error | null} [error] - Error from mutation
 */
interface CreateProjectFormProps {
  onSubmit: (data: CreateProjectFormData) => void;
  isLoading?: boolean;
  error?: Error | null;
}

/**
 * Create project form component
 *
 * @description Renders a form with project name input field.
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
 * 1. User enters project name
 * 2. Client-side validation on blur/submit
 * 3. On submit, call onSubmit callback
 * 4. Parent component handles API call
 * 5. On error, display error message
 *
 * @example
 * ```tsx
 * <CreateProjectForm
 *   onSubmit={(data) => createMutation.mutate(data)}
 *   isLoading={createMutation.isPending}
 *   error={createMutation.error}
 * />
 * ```
 */
export function CreateProjectForm({
  onSubmit,
  isLoading,
  error,
}: CreateProjectFormProps) {
  // Form state management with react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateProjectFormData>({
    resolver: zodResolver(createProjectSchema),
    defaultValues: {
      name: '',
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* API Error Display */}
      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
          {error.message || 'Failed to create project'}
        </div>
      )}

      {/* Project Name Field */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium mb-1">
          Project Name
        </label>
        <input
          id="name"
          type="text"
          className="w-full border rounded-md px-3 py-2"
          placeholder="Enter project name"
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
        {isLoading ? 'Creating...' : 'Create Project'}
      </button>
    </form>
  );
}
