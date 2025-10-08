/**
 * Create project dialog component
 *
 * @description Dialog component for creating a new project.
 * Uses Radix UI Dialog for accessible modal implementation.
 *
 * **Features**:
 * - Modal dialog with backdrop
 * - Create project form
 * - Auto-close on success
 * - Cancel button
 *
 * @module create-project-dialog
 */

'use client';

import { useCreateProject } from '../hooks';
import { CreateProjectForm } from './create-project-form';
import type { CreateProjectFormData } from '../schemas';

/**
 * Create project dialog props
 *
 * @property {boolean} open - Whether dialog is open
 * @property {function} onOpenChange - Callback when open state changes
 */
interface CreateProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Create project dialog component
 *
 * @description Renders a dialog with project creation form.
 * Automatically closes on successful creation.
 *
 * **User Flow**:
 * 1. User clicks "New project" button
 * 2. Dialog opens with form
 * 3. User enters project name
 * 4. User clicks "Create Project"
 * 5. On success, dialog closes and project list refreshes
 * 6. On error, error message shown in form
 *
 * @example
 * ```tsx
 * const [dialogOpen, setDialogOpen] = useState(false);
 *
 * <button onClick={() => setDialogOpen(true)}>New project</button>
 * <CreateProjectDialog
 *   open={dialogOpen}
 *   onOpenChange={setDialogOpen}
 * />
 * ```
 */
export function CreateProjectDialog({
  open,
  onOpenChange,
}: CreateProjectDialogProps) {
  const createMutation = useCreateProject();

  /**
   * Form submission handler
   *
   * @description Creates project and closes dialog on success.
   *
   * @param data - Validated form data
   */
  const handleSubmit = (data: CreateProjectFormData) => {
    createMutation.mutate(data, {
      onSuccess: () => {
        // Close dialog on success
        onOpenChange(false);
      },
    });
  };

  // Close handler
  const handleClose = () => {
    if (!createMutation.isPending) {
      onOpenChange(false);
    }
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div
          className="bg-white rounded-lg shadow-xl max-w-md w-full p-6"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              Create New Project
            </h2>
            <p className="mt-1 text-sm text-gray-600">
              Enter a name for your new project
            </p>
          </div>

          {/* Form */}
          <CreateProjectForm
            onSubmit={handleSubmit}
            isLoading={createMutation.isPending}
            error={createMutation.error}
          />

          {/* Cancel Button */}
          <button
            type="button"
            onClick={handleClose}
            disabled={createMutation.isPending}
            className="mt-3 w-full px-4 py-2 text-sm text-gray-700 hover:text-gray-900 disabled:opacity-60"
          >
            Cancel
          </button>
        </div>
      </div>
    </>
  );
}
