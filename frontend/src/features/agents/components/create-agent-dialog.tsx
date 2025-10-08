/**
 * Create agent dialog component
 *
 * @description Dialog component for creating a new agent.
 * Uses simple modal implementation for accessible dialog.
 *
 * **Features**:
 * - Modal dialog with backdrop
 * - Create agent form
 * - Auto-close on success
 * - Cancel button
 *
 * @module create-agent-dialog
 */

'use client';

import { useCreateAgent } from '../hooks';
import { CreateAgentForm } from './create-agent-form';
import type { CreateAgentFormData } from '../schemas';

/**
 * Create agent dialog props
 *
 * @property {boolean} open - Whether dialog is open
 * @property {function} onOpenChange - Callback when open state changes
 * @property {string} projectId - Project UUID
 */
interface CreateAgentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
}

/**
 * Create agent dialog component
 *
 * @description Renders a dialog with agent creation form.
 * Automatically closes on successful creation.
 *
 * **User Flow**:
 * 1. User clicks "Add Agent" button
 * 2. Dialog opens with form
 * 3. User enters agent name
 * 4. User clicks "Add Agent"
 * 5. On success, dialog closes and agent list refreshes
 * 6. On error, error message shown in form
 *
 * @example
 * ```tsx
 * const [dialogOpen, setDialogOpen] = useState(false);
 *
 * <button onClick={() => setDialogOpen(true)}>Add Agent</button>
 * <CreateAgentDialog
 *   open={dialogOpen}
 *   onOpenChange={setDialogOpen}
 *   projectId={projectId}
 * />
 * ```
 */
export function CreateAgentDialog({
  open,
  onOpenChange,
  projectId,
}: CreateAgentDialogProps) {
  const createMutation = useCreateAgent();

  /**
   * Form submission handler
   *
   * @description Creates agent and closes dialog on success.
   *
   * @param data - Validated form data
   */
  const handleSubmit = (data: CreateAgentFormData) => {
    createMutation.mutate(
      {
        name: data.name,
        project_id: projectId,
      },
      {
        onSuccess: () => {
          // Close dialog on success
          onOpenChange(false);
        },
      }
    );
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
            <h2 className="text-xl font-bold text-gray-900">Add Agent</h2>
            <p className="mt-1 text-sm text-gray-600">Register your AI agent</p>
          </div>

          {/* Form */}
          <CreateAgentForm
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
