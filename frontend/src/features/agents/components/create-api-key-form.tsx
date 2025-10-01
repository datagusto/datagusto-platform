/**
 * Create API key form component
 *
 * @description Form component for creating a new API key.
 * Allows optional name and expiration configuration.
 *
 * @module create-api-key-form
 */

'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createAPIKeySchema, type CreateAPIKeyFormData } from '../schemas/api-key.schema';

/**
 * Create API key form props
 */
interface CreateAPIKeyFormProps {
  onSubmit: (data: CreateAPIKeyFormData) => void;
  isLoading?: boolean;
  error?: Error | null;
}

/**
 * Create API key form component
 *
 * @description Renders a form with optional name and expiration fields.
 */
export function CreateAPIKeyForm({
  onSubmit,
  isLoading,
  error,
}: CreateAPIKeyFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateAPIKeyFormData>({
    resolver: zodResolver(createAPIKeySchema),
    defaultValues: {
      name: '',
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* API Error Display */}
      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
          {error.message || 'Failed to create API key'}
        </div>
      )}

      {/* Name Field */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium mb-1">
          Name (Optional)
        </label>
        <input
          id="name"
          type="text"
          className="w-full border rounded-md px-3 py-2"
          placeholder="Production API Key"
          {...register('name')}
        />
        {errors.name && (
          <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          API keys never expire
        </p>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isSubmitting || isLoading}
        className="w-full bg-black text-white rounded-md py-2 disabled:opacity-60"
      >
        {isLoading ? 'Creating...' : 'Create API Key'}
      </button>
    </form>
  );
}
