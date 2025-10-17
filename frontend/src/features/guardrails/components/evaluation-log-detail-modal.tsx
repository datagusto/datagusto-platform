/**
 * Evaluation log detail modal component
 *
 * @description Displays detailed information about a guardrail evaluation log.
 * Shows all evaluated guardrails, matched conditions, actions, and context.
 *
 * **Features**:
 * - Full evaluation details
 * - Request context (input/output)
 * - All guardrails (triggered and non-triggered)
 * - Action results with reasons
 * - Evaluation metadata
 *
 * @module evaluation-log-detail-modal
 */

'use client';

import { GuardrailEvaluationLog } from '../types';

/**
 * Evaluation log detail modal props
 */
interface EvaluationLogDetailModalProps {
  log: GuardrailEvaluationLog | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Badge component for status display
 */
function Badge({
  children,
  variant = 'default',
}: {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'danger' | 'warning' | 'info';
}) {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    danger: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
    info: 'bg-blue-100 text-blue-800',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${variantClasses[variant]}`}
    >
      {children}
    </span>
  );
}

/**
 * Format date string to readable format
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(date);
}

/**
 * Evaluation log detail modal component
 *
 * @description Renders a modal dialog with comprehensive evaluation log details.
 * Organized into sections for better readability.
 *
 * @example
 * ```tsx
 * const [selectedLog, setSelectedLog] = useState<GuardrailEvaluationLog | null>(null);
 * const [modalOpen, setModalOpen] = useState(false);
 *
 * <EvaluationLogDetailModal
 *   log={selectedLog}
 *   open={modalOpen}
 *   onOpenChange={setModalOpen}
 * />
 * ```
 */
export function EvaluationLogDetailModal({
  log,
  open,
  onOpenChange,
}: EvaluationLogDetailModalProps) {
  if (!open || !log) return null;

  const { log_data } = log;
  const { evaluation_result } = log_data;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={() => onOpenChange(false)}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Evaluation Log Details
              </h2>
              <p className="text-sm text-gray-500 mt-1 font-mono">
                {log.request_id}
              </p>
            </div>
            <button
              onClick={() => onOpenChange(false)}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
            {/* Overview Section */}
            <section>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Overview
              </h3>
              <div className="grid grid-cols-2 gap-4 bg-gray-50 rounded-lg p-4">
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                    Process
                  </div>
                  <div className="text-sm font-medium text-gray-900">
                    {log_data.process_name}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                    Type
                  </div>
                  <div>
                    <Badge variant="info">{log.process_type}</Badge>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                    Timing
                  </div>
                  <div>
                    <Badge
                      variant={log.timing === 'on_start' ? 'default' : 'warning'}
                    >
                      {log.timing}
                    </Badge>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                    Decision
                  </div>
                  <div>
                    <Badge variant={log.should_proceed ? 'success' : 'danger'}>
                      {log.should_proceed ? 'Proceed' : 'Blocked'}
                    </Badge>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                    Created At
                  </div>
                  <div className="text-sm text-gray-700">
                    {formatDate(log.created_at)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                    Evaluation Time
                  </div>
                  <div className="text-sm text-gray-700">
                    {evaluation_result.metadata.evaluation_time_ms}ms
                  </div>
                </div>
              </div>
            </section>

            {/* Statistics Section */}
            <section>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Statistics
              </h3>
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-xs text-blue-600 uppercase tracking-wider mb-1">
                    Evaluated
                  </div>
                  <div className="text-2xl font-bold text-blue-900">
                    {evaluation_result.metadata.evaluated_guardrails_count}
                  </div>
                </div>
                <div className="bg-red-50 rounded-lg p-4">
                  <div className="text-xs text-red-600 uppercase tracking-wider mb-1">
                    Triggered
                  </div>
                  <div className="text-2xl font-bold text-red-900">
                    {evaluation_result.metadata.triggered_guardrails_count}
                  </div>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-xs text-green-600 uppercase tracking-wider mb-1">
                    Passed
                  </div>
                  <div className="text-2xl font-bold text-green-900">
                    {evaluation_result.metadata.evaluated_guardrails_count -
                      evaluation_result.metadata.triggered_guardrails_count}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-xs text-gray-600 uppercase tracking-wider mb-1">
                    Ignored
                  </div>
                  <div className="text-2xl font-bold text-gray-900">
                    {evaluation_result.metadata.ignored_guardrails_count}
                  </div>
                </div>
              </div>
            </section>

            {/* Guardrails Section */}
            <section>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Evaluated Guardrails
              </h3>
              <div className="space-y-3">
                {evaluation_result.triggered_guardrails.map((guardrail, idx) => (
                  <div
                    key={guardrail.guardrail_id}
                    className={`border rounded-lg p-4 ${
                      guardrail.triggered
                        ? 'border-red-200 bg-red-50'
                        : guardrail.ignored
                          ? 'border-gray-300 bg-gray-50'
                          : guardrail.error
                            ? 'border-orange-200 bg-orange-50'
                            : 'border-gray-200 bg-white'
                    }`}
                  >
                    {/* Guardrail Header */}
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-gray-900">
                            {guardrail.guardrail_name}
                          </span>
                          {guardrail.triggered && (
                            <Badge variant="danger">Triggered</Badge>
                          )}
                          {!guardrail.triggered &&
                            !guardrail.ignored &&
                            !guardrail.error && (
                              <Badge variant="success">Passed</Badge>
                            )}
                          {guardrail.ignored && (
                            <Badge variant="warning">Ignored</Badge>
                          )}
                          {guardrail.error && (
                            <Badge variant="danger">Error</Badge>
                          )}
                        </div>
                        <div className="text-xs text-gray-500 font-mono">
                          {guardrail.guardrail_id}
                        </div>
                      </div>
                    </div>

                    {/* Ignored Reason */}
                    {guardrail.ignored && guardrail.ignored_reason && (
                      <div className="mt-2 p-2 bg-gray-100 rounded text-sm text-gray-700">
                        <strong>Ignored Reason:</strong> {guardrail.ignored_reason}
                      </div>
                    )}

                    {/* Error Message */}
                    {guardrail.error && guardrail.error_message && (
                      <div className="mt-2 p-2 bg-orange-100 rounded text-sm text-orange-800">
                        <strong>Error:</strong> {guardrail.error_message}
                      </div>
                    )}

                    {/* Matched Conditions */}
                    {guardrail.matched_conditions.length > 0 && (
                      <div className="mt-2">
                        <div className="text-xs text-gray-600 font-medium mb-1">
                          Matched Conditions:
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {guardrail.matched_conditions.map((condIdx) => (
                            <Badge key={condIdx} variant="info">
                              Condition {condIdx}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    {guardrail.actions.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <div className="text-xs text-gray-600 font-medium">
                          Actions:
                        </div>
                        {guardrail.actions.map((action, actionIdx) => (
                          <div
                            key={actionIdx}
                            className="bg-white border border-gray-200 rounded p-3"
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <Badge
                                variant={
                                  action.action_type === 'block'
                                    ? 'danger'
                                    : action.action_type === 'warn'
                                      ? 'warning'
                                      : 'info'
                                }
                              >
                                {action.action_type.toUpperCase()}
                              </Badge>
                              <span className="text-xs text-gray-500">
                                Priority: {action.priority}
                              </span>
                            </div>
                            <div className="space-y-1">
                              {Object.entries(action.result).map(
                                ([key, value]) => (
                                  <div key={key} className="text-sm">
                                    <span className="text-gray-600 font-medium">
                                      {key}:
                                    </span>{' '}
                                    <span className="text-gray-900">
                                      {typeof value === 'boolean'
                                        ? value.toString()
                                        : String(value)}
                                    </span>
                                  </div>
                                )
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>

            {/* Request Context Section */}
            <section>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Request Context
              </h3>
              <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <pre className="text-xs text-gray-100 font-mono">
                  {JSON.stringify(log_data.request_context, null, 2)}
                </pre>
              </div>
            </section>

            {/* Trace ID (if available) */}
            {log.trace_id && (
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Trace Information
                </h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                    Trace ID
                  </div>
                  <div className="text-sm font-mono text-gray-900">
                    {log.trace_id}
                  </div>
                </div>
              </section>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
            <button
              onClick={() => onOpenChange(false)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
