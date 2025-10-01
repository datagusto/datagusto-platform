/**
 * Create guardrail page
 *
 * @description Page for creating a new guardrail in a project.
 * Uses the CreateGuardrailForm component with React Query mutation.
 *
 * @module create-guardrail-page
 */

'use client';

import { useParams, useRouter } from 'next/navigation';
import { CreateGuardrailForm } from '@/features/guardrails/components';
import { useCreateGuardrail } from '@/features/guardrails/hooks';
import type { CreateGuardrailFormData } from '@/features/guardrails/schemas';

/**
 * Create guardrail page component
 *
 * @description Renders the guardrail creation form and handles submission.
 * Redirects to guardrails list on success.
 */
export default function CreateGuardrailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.projectId as string;

  const createMutation = useCreateGuardrail();

  /**
   * Handle form submission
   *
   * @param data - Validated form data from CreateGuardrailForm
   */
  const handleSubmit = (data: CreateGuardrailFormData) => {
    createMutation.mutate(
      {
        project_id: projectId,
        name: data.name,
        definition: data.definition,
      },
      {
        onSuccess: () => {
          // Redirect to guardrails list on success
          router.push(`/projects/${projectId}/guardrails`);
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-100 rounded-md transition-colors"
              aria-label="Go back"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
            <h1 className="text-2xl font-bold">Create Guardrail</h1>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <CreateGuardrailForm
            onSubmit={handleSubmit}
            isLoading={createMutation.isPending}
            error={createMutation.error}
          />
        </div>
      </div>
    </div>
  );
}
