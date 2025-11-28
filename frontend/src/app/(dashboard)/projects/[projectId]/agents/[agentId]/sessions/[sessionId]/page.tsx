/**
 * Alignment session detail page
 *
 * @description Displays detailed information about a specific alignment session.
 * Shows inference results, validation rules, and validation history.
 *
 * @module session-detail-page
 */

'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { alignmentService } from '@/features/agents/services';

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
 * Badge component for status display
 */
function Badge({
  children,
  variant = 'default',
}: {
  children: React.ReactNode;
  variant?:
    | 'default'
    | 'success'
    | 'danger'
    | 'warning'
    | 'info'
    | 'drift'
    | 'normal';
}) {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    danger: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
    info: 'bg-blue-100 text-blue-800',
    drift: 'bg-amber-100 text-amber-800 border border-amber-300',
    normal: 'bg-green-100 text-green-800',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${variantClasses[variant]}`}
    >
      {children}
    </span>
  );
}

/**
 * Session detail page component
 */
export default function SessionDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.projectId as string;
  const agentId = params.agentId as string;
  const sessionId = params.sessionId as string;

  // Fetch session detail
  const {
    data: session,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['alignment-session-detail', agentId, sessionId],
    queryFn: () => alignmentService.getSessionDetail(agentId, sessionId),
    enabled: !!agentId && !!sessionId,
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() =>
                router.push(`/projects/${projectId}/agents/${agentId}`)
              }
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              ← Back to Agent
            </button>
            <h1 className="text-2xl font-bold">Session Detail</h1>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Loading state */}
        {isLoading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h3 className="text-lg font-medium text-red-900 mb-2">Error</h3>
            <p className="text-red-700">
              {error instanceof Error
                ? error.message
                : 'Failed to load session detail'}
            </p>
          </div>
        )}

        {/* Session content */}
        {!isLoading && !error && session && (
          <div className="space-y-8">
            {/* Session Info */}
            <section className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4">
                Session Information
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Session ID</p>
                  <p className="font-mono text-sm">{sessionId}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Created At</p>
                  <p className="text-sm">{formatDate(session.created_at)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Updated At</p>
                  <p className="text-sm">{formatDate(session.updated_at)}</p>
                </div>
              </div>
            </section>

            {/* Inference Result */}
            <section className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4">Inference Result</h2>

              <div className="space-y-4">
                {/* User Instruction History */}
                <div>
                  <p className="text-sm text-gray-600 mb-2">
                    User Instruction History (
                    {session.user_instruction_history?.length || 0})
                  </p>
                  {!session.user_instruction_history ||
                  session.user_instruction_history.length === 0 ? (
                    <p className="text-sm text-gray-500 italic">
                      No user instructions
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {session.user_instruction_history.map((item, idx) => (
                        <div
                          key={idx}
                          className="bg-gray-50 p-3 rounded border"
                        >
                          <p className="text-sm">{item.user_instruction}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {formatDate(item.created_at)}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Inferred User Intention */}
                <div>
                  <p className="text-sm text-gray-600 mb-2">
                    Inferred User Intention (
                    {session.inference_result.ambiguous_terms.length +
                      session.inference_result.resolved_terms.length}
                    )
                  </p>
                  {session.inference_result.ambiguous_terms.length === 0 &&
                  session.inference_result.resolved_terms.length === 0 ? (
                    <p className="text-sm text-gray-500 italic">
                      No inferred intentions
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {/* Resolved Terms (with user_context) */}
                      {session.inference_result.resolved_terms.map(
                        (term, idx) => (
                          <div
                            key={`resolved-${idx}`}
                            className="bg-green-50 p-3 rounded border border-green-200"
                          >
                            <div className="flex-1">
                              <p className="font-medium text-sm">{term.term}</p>
                              <p className="text-xs text-gray-600">
                                Category: {term.category}
                              </p>
                              <p className="text-sm mt-1 text-gray-700">
                                {term.resolved_value}
                              </p>
                            </div>
                          </div>
                        )
                      )}
                      {/* Ambiguous Terms (without user_context) */}
                      {session.inference_result.ambiguous_terms.map(
                        (term, idx) => (
                          <div
                            key={`ambiguous-${idx}`}
                            className="bg-yellow-50 p-3 rounded border border-yellow-200"
                          >
                            <p className="font-medium text-sm">{term.term}</p>
                            <p className="text-xs text-gray-600">
                              Category: {term.category}
                            </p>
                            <p className="text-sm mt-1 text-gray-400 italic">
                              No information
                            </p>
                          </div>
                        )
                      )}
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* Generated Guardrails */}
            <section className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4">
                Generated Guardrails ({session.validation_rules.length})
              </h2>
              {session.validation_rules.length === 0 ? (
                <p className="text-sm text-gray-500 italic">
                  No generated guardrails
                </p>
              ) : (
                <div className="space-y-4">
                  {session.validation_rules.map((rule, idx) => {
                    const gd = rule.guardrail_definition;
                    const trigger = gd?.trigger;
                    const actions = gd?.actions || [];

                    return (
                      <div
                        key={idx}
                        className="bg-white rounded-lg border border-gray-200 overflow-hidden"
                      >
                        {/* Header */}
                        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                          <div className="flex items-center gap-3">
                            <div className="bg-gray-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                              {idx + 1}
                            </div>
                            <span className="font-semibold text-gray-900">
                              {rule.tool_name}
                            </span>
                          </div>
                        </div>

                        <div className="p-4 space-y-4">
                          {/* Trigger Section */}
                          {trigger && (
                            <div>
                              <p className="text-sm font-semibold text-gray-700 mb-2">
                                Trigger
                              </p>
                              <div className="ml-4 space-y-3 text-sm">
                                <div>
                                  <span className="text-gray-500">When: </span>
                                  <span className="text-gray-900">
                                    {trigger.type}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-gray-500">Logic: </span>
                                  <span className="text-gray-900">
                                    {trigger.logic}
                                  </span>
                                </div>
                                {trigger.conditions.length > 0 && (
                                  <div>
                                    <span className="text-gray-500">
                                      Conditions:
                                    </span>
                                    <div className="mt-2 space-y-2">
                                      {trigger.conditions.map((cond, cIdx) => (
                                        <div
                                          key={cIdx}
                                          className="bg-gray-50 rounded p-3 ml-2 border border-gray-200"
                                        >
                                          <div className="space-y-1 text-sm">
                                            <div>
                                              <span className="text-gray-500">
                                                field:{' '}
                                              </span>
                                              <span className="text-gray-900">
                                                {cond.field}
                                              </span>
                                            </div>
                                            <div>
                                              <span className="text-gray-500">
                                                operator:{' '}
                                              </span>
                                              <span className="text-gray-900">
                                                {cond.operator}
                                              </span>
                                            </div>
                                            <div>
                                              <span className="text-gray-500">
                                                value:{' '}
                                              </span>
                                              <span className="text-gray-900">
                                                {cond.value}
                                              </span>
                                            </div>
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Actions Section */}
                          {actions.length > 0 && (
                            <div>
                              <p className="text-sm font-semibold text-gray-700 mb-2">
                                Actions
                              </p>
                              <div className="ml-4 space-y-2">
                                {actions.map((action, aIdx) => (
                                  <div
                                    key={aIdx}
                                    className="bg-gray-50 rounded p-3 border border-gray-200"
                                  >
                                    <div className="space-y-1 text-sm">
                                      <div>
                                        <span className="text-gray-500">
                                          type:{' '}
                                        </span>
                                        <span className="text-gray-900">
                                          {action.type}
                                        </span>
                                      </div>
                                      <div>
                                        <span className="text-gray-500">
                                          priority:{' '}
                                        </span>
                                        <span className="text-gray-900">
                                          {action.priority}
                                        </span>
                                      </div>
                                      {action.config?.message && (
                                        <div>
                                          <span className="text-gray-500">
                                            message:{' '}
                                          </span>
                                          <span className="text-gray-900">
                                            {action.config.message}
                                          </span>
                                        </div>
                                      )}
                                      {action.config?.allow_proceed !== null &&
                                        action.config?.allow_proceed !==
                                          undefined && (
                                          <div>
                                            <span className="text-gray-500">
                                              allow_proceed:{' '}
                                            </span>
                                            <span className="text-gray-900">
                                              {action.config.allow_proceed
                                                ? 'true'
                                                : 'false'}
                                            </span>
                                          </div>
                                        )}
                                      {action.config?.drop_field && (
                                        <div>
                                          <span className="text-gray-500">
                                            drop_field:{' '}
                                          </span>
                                          <span className="text-gray-900">
                                            {action.config.drop_field}
                                          </span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Why this guardrail is generated Section */}
                          {(rule.reasoning || rule.condition) && (
                            <div>
                              <p className="text-sm font-semibold text-gray-700 mb-2">
                                Why this guardrail is generated?
                              </p>
                              <p className="ml-4 text-sm text-gray-900">
                                {[rule.reasoning, rule.condition]
                                  .filter(Boolean)
                                  .join(' ')}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Automatically Blocked Tools */}
              {session.disallowed_tools &&
                session.disallowed_tools.length > 0 && (
                  <div className="mt-6 pt-6 border-t border-gray-200">
                    <h3 className="text-lg font-semibold mb-3">
                      Automatically Blocked Tools (
                      {session.disallowed_tools.length})
                    </h3>
                    <p className="text-sm text-gray-600 mb-3">
                      The following tools are automatically blocked for this
                      session:
                    </p>
                    <ul className="list-disc list-inside space-y-1">
                      {session.disallowed_tools.map((tool, idx) => (
                        <li key={idx} className="text-sm text-gray-900">
                          {tool}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
            </section>

            {/* Validation History */}
            <section className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4">
                Validation History ({session.validation_history.length})
              </h2>
              {session.validation_history.length === 0 ? (
                <p className="text-sm text-gray-500 italic">
                  No validation history
                </p>
              ) : (
                <div className="space-y-4">
                  {[...session.validation_history]
                    .sort(
                      (a, b) =>
                        new Date(a.timestamp).getTime() -
                        new Date(b.timestamp).getTime()
                    )
                    .map((entry, idx) => (
                      <div
                        key={idx}
                        className={`p-4 rounded border ${
                          entry.should_proceed
                            ? 'bg-white border-gray-200'
                            : 'bg-red-50 border-red-200'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <p className="font-semibold text-sm">
                              {entry.process_name}
                            </p>
                            <p className="text-xs text-gray-600">
                              {formatDate(entry.timestamp)}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="default">{entry.timing}</Badge>
                            <Badge variant="default">
                              {entry.process_type}
                            </Badge>
                            <Badge
                              variant={
                                entry.should_proceed ? 'success' : 'danger'
                              }
                            >
                              {entry.should_proceed ? 'Approved' : 'Blocked'}
                            </Badge>
                          </div>
                        </div>

                        <div className="mt-2">
                          <p className="text-xs text-gray-600 mb-1">Input:</p>
                          <div className="bg-gray-50 p-2 rounded border text-xs font-mono overflow-auto max-h-40">
                            <pre>
                              {JSON.stringify(
                                entry.request_context.input,
                                null,
                                2
                              )}
                            </pre>
                          </div>
                        </div>

                        {entry.request_context.output && (
                          <div className="mt-2">
                            <p className="text-xs text-gray-600 mb-1">
                              Output:
                            </p>
                            <div className="bg-gray-50 p-2 rounded border text-xs font-mono overflow-auto max-h-40">
                              <pre>
                                {JSON.stringify(
                                  entry.request_context.output,
                                  null,
                                  2
                                )}
                              </pre>
                            </div>
                          </div>
                        )}

                        {entry.evaluation_result.triggered_guardrails.length >
                          0 && (
                          <div className="mt-2">
                            <p className="text-xs text-gray-600 mb-1">
                              Evaluated Guardrails:
                            </p>
                            <div className="space-y-1">
                              {entry.evaluation_result.triggered_guardrails.map(
                                (guardrail, gIdx) => (
                                  <div
                                    key={gIdx}
                                    className={`p-2 rounded border text-xs ${
                                      guardrail.triggered
                                        ? 'bg-red-50 border-red-200'
                                        : 'bg-green-50 border-green-200'
                                    }`}
                                  >
                                    <span className="font-semibold">
                                      {guardrail.guardrail_name}
                                    </span>
                                    {guardrail.triggered && (
                                      <span className="ml-2 text-red-600">
                                        (triggered)
                                      </span>
                                    )}
                                    {guardrail.error && (
                                      <span className="ml-2 text-amber-600">
                                        Error: {guardrail.error_message}
                                      </span>
                                    )}
                                  </div>
                                )
                              )}
                            </div>
                          </div>
                        )}

                        <div className="mt-2 text-xs text-gray-500">
                          Evaluation time:{' '}
                          {entry.evaluation_result.metadata.evaluation_time_ms}
                          ms
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
