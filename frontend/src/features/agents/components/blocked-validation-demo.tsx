/**
 * Blocked Validation Demo Component
 *
 * @description Displays a demo of blocked validation history items.
 * Shows what happens when a tool invocation is blocked by guardrails.
 *
 * @module blocked-validation-demo
 */

'use client';

/**
 * Badge component for status display
 */
function Badge({
  children,
  variant = 'default',
}: {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'danger' | 'warning' | 'drift' | 'normal';
}) {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    danger: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
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
 * Dummy blocked validation data
 */
const blockedValidations = [
  {
    tool_name: 'get_user_files',
    timestamp: '2025-10-19T08:52:32.703176',
    is_valid: false,
    is_drift: false,
    reasoning:
      'The tool invocation is INVALID due to a critical parameter mismatch. While the tool name "get_user_files" matches Rule 1, the actual parameter value for "file_type" is null, which contradicts the expected parameter specification. Rule 1 explicitly expects file_type to be "csv or excel" since exam data is typically stored in spreadsheet formats. The null value means the system won\'t be able to filter for the appropriate exam data files, which are essential for generating the requested exam statistics.',
    tool_input: {
      user_id: 'e3701c1d-a2ca-400b-b2c1-f40cc7c14db3',
      organization_id: 'cbc634ff-ebf4-4880-a553-188ae19d2a3d',
      file_type: null,
    },
    matched_rule: {
      tool_name: 'get_user_files',
      condition:
        'When the user requests exam statistics and needs to access exam data files',
      parameters: {
        user_id: "Current user's UUID (teacher requesting the statistics)",
        organization_id: 'Organization ID for multi-tenant filtering',
        file_type:
          'csv or excel (exam data is typically stored in spreadsheet formats)',
      },
      reasoning:
        'Need to first locate exam data files that contain the final exam results for the math class in Spring 2025. These files would contain the raw exam scores and problem section data needed to generate statistics.',
    },
    parameter_alignment: {
      user_id:
        'ALIGNED - The provided UUID "e3701c1d-a2ca-400b-b2c1-f40cc7c14db3" matches the expected format for the current user\'s UUID (teacher requesting statistics)',
      organization_id:
        'ALIGNED - The provided UUID "cbc634ff-ebf4-4880-a553-188ae19d2a3d" matches the expected format for organization ID required for multi-tenant filtering',
      file_type:
        'MISALIGNED - The actual value is null, but the rule expects "csv or excel" since exam data is typically stored in spreadsheet formats. This null value will prevent proper filtering of exam data files.',
    },
    drift_detection: null,
  },
];

/**
 * Blocked Validation Demo Component
 *
 * @description Displays examples of blocked validation history items.
 * Shows the detailed breakdown of why tool invocations were blocked.
 *
 * **Features**:
 * - Red highlighting for blocked items
 * - Detailed reasoning for blocking
 * - Tool input display
 * - Matched rule information
 * - Parameter alignment details
 *
 * @example
 * ```tsx
 * <BlockedValidationDemo />
 * ```
 */
export function BlockedValidationDemo() {
  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-base font-medium">Blocked Validation Example</h3>
        <p className="text-sm text-gray-600 mt-1">
          Example of a tool invocation that was blocked by guardrails due to
          parameter misalignment
        </p>
      </div>

      <div className="space-y-4">
        {blockedValidations.map((entry, idx) => (
          <div
            key={idx}
            className="p-4 rounded border bg-red-50 border-red-200"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-semibold text-sm">{entry.tool_name}</p>
                <p className="text-xs text-gray-600">
                  {formatDate(entry.timestamp)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="danger">Blocked</Badge>
                <Badge variant="normal">Normal</Badge>
              </div>
            </div>

            <p className="text-sm mt-2">
              <strong>Reasoning:</strong> {entry.reasoning}
            </p>

            <div className="mt-2">
              <p className="text-xs text-gray-600 mb-1">Tool Input:</p>
              <div className="bg-white p-2 rounded border text-xs font-mono">
                <pre>{JSON.stringify(entry.tool_input, null, 2)}</pre>
              </div>
            </div>

            {entry.matched_rule && (
              <div className="mt-2">
                <p className="text-xs text-gray-600 mb-1">Matched Rule:</p>
                <div className="bg-white p-2 rounded border text-xs">
                  <p>
                    <strong>Tool:</strong> {entry.matched_rule.tool_name}
                  </p>
                  <p>
                    <strong>Condition:</strong> {entry.matched_rule.condition}
                  </p>
                  <div className="mt-1">
                    <strong>Expected Parameters:</strong>
                    <div className="ml-2 mt-1 space-y-1">
                      {Object.entries(entry.matched_rule.parameters).map(
                        ([key, value]) => (
                          <div key={key}>
                            <span className="text-blue-600">{key}:</span>{' '}
                            {value}
                          </div>
                        )
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="mt-2">
              <p className="text-xs text-gray-600 mb-1">Parameter Alignment:</p>
              <div className="bg-white p-2 rounded border text-xs">
                {Object.entries(entry.parameter_alignment).map(
                  ([key, value]) => (
                    <div key={key} className="mb-1">
                      <span className="font-semibold">{key}:</span> {value}
                    </div>
                  )
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
