/**
 * Alignment session list component
 *
 * @description Displays alignment sessions in a table format.
 * Shows key information like session ID, user instruction, and validation status.
 *
 * **Features**:
 * - Table display with session details
 * - Clickable rows to navigate to session detail
 * - Validation status indicator
 * - Responsive design
 * - Loading and error states
 * - Empty state handling
 *
 * @module alignment-session-list
 */

'use client';

import { useRouter, useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { alignmentService } from '../services';

/**
 * Alignment session list props
 */
interface AlignmentSessionListProps {
  agentId: string;
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
  }).format(date);
}

/**
 * Badge component for count display
 */
function Badge({
  children,
  variant = 'default',
}: {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'info';
}) {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    info: 'bg-blue-100 text-blue-800',
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
 * Truncate text to specified length
 */
function truncateText(text: string, maxLength: number = 50): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Alignment session list component
 *
 * @description Main table component that fetches and displays alignment sessions.
 * Includes loading states, error handling, and formatted data display.
 */
export function AlignmentSessionList({ agentId }: AlignmentSessionListProps) {
  const router = useRouter();
  const params = useParams();
  const projectId = params.projectId as string;

  // Fetch alignment sessions with React Query
  const { data, isLoading, error } = useQuery({
    queryKey: ['alignment-sessions', agentId],
    queryFn: () => alignmentService.listSessions(agentId),
    enabled: !!agentId,
  });

  // Handle row click
  const handleRowClick = (sessionId: string) => {
    router.push(
      `/projects/${projectId}/agents/${agentId}/sessions/${sessionId}`
    );
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading alignment sessions...</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <p className="text-sm text-red-600">
          Failed to load alignment sessions: {error.message}
        </p>
      </div>
    );
  }

  // Empty state
  if (!data || data.sessions.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No alignment sessions found</p>
        <p className="text-sm mt-2">
          Sessions will appear here when alignment is performed
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="text-sm text-gray-600">Total sessions: {data.total}</div>

      {/* Table */}
      <div className="overflow-x-auto border rounded-lg bg-white">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Session ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User Instruction
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Updated At
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.sessions.map((session) => {
              return (
                <tr
                  key={session.session_id}
                  onClick={() => handleRowClick(session.session_id)}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 text-sm font-mono text-gray-900">
                    <span
                      className="truncate max-w-32 block"
                      title={session.session_id}
                    >
                      {session.session_id.substring(0, 8)}...
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    <span title={session.user_instruction}>
                      {truncateText(session.user_instruction, 60)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {session.validation_history_count === 0 ? (
                      <Badge variant="default">No Validations</Badge>
                    ) : session.has_invalid_validations ? (
                      <Badge variant="warning">Issues Found</Badge>
                    ) : (
                      <Badge variant="success">All Valid</Badge>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {formatDate(session.updated_at)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
