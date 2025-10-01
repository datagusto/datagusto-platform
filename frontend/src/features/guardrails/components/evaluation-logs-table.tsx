/**
 * Evaluation logs table component
 *
 * @description Displays guardrail evaluation logs in a table format.
 * Shows key information like request ID, timing, process type, and decision.
 *
 * **Features**:
 * - Paginated table display
 * - Badge styling for status indicators
 * - Responsive design
 * - Loading and error states
 *
 * @module evaluation-logs-table
 */

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchEvaluationLogsByAgent } from '../services/evaluation-logs.service';
import type { GuardrailEvaluationLog } from '../types/evaluation-log.types';

/**
 * Evaluation logs table props
 */
interface EvaluationLogsTableProps {
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
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${variantClasses[variant]}`}
    >
      {children}
    </span>
  );
}

/**
 * Evaluation logs table component
 *
 * @description Main table component that fetches and displays evaluation logs.
 * Includes pagination, loading states, and formatted data display.
 */
export function EvaluationLogsTable({ agentId }: EvaluationLogsTableProps) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Fetch evaluation logs with React Query
  const { data, isLoading, error } = useQuery({
    queryKey: ['evaluation-logs', agentId, page, pageSize],
    queryFn: () => fetchEvaluationLogsByAgent(agentId, page, pageSize),
    enabled: !!agentId,
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading evaluation logs...</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <p className="text-sm text-red-600">
          Failed to load evaluation logs: {error.message}
        </p>
      </div>
    );
  }

  // Empty state
  if (!data || data.items.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No evaluation logs found</p>
        <p className="text-sm mt-2">
          Logs will appear here when guardrails are evaluated
        </p>
      </div>
    );
  }

  const totalPages = Math.ceil(data.total / pageSize);

  return (
    <div className="space-y-4">
      {/* Page size selector */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Showing {data.items.length} of {data.total} logs
        </div>
        <div className="flex items-center space-x-2">
          <label className="text-sm text-gray-600">Per page:</label>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="border rounded px-2 py-1 text-sm"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Request ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created At
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Process
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Timing
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Decision
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Triggered
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.items.map((log) => (
              <tr key={log.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-mono text-gray-900">
                  <span
                    className="truncate max-w-32 block"
                    title={log.request_id}
                  >
                    {log.request_id}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {formatDate(log.created_at)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {log.log_data.process_name}
                </td>
                <td className="px-4 py-3 text-sm">
                  <Badge variant="info">{log.process_type}</Badge>
                </td>
                <td className="px-4 py-3 text-sm">
                  <Badge variant={log.timing === 'on_start' ? 'default' : 'warning'}>
                    {log.timing}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-sm">
                  <Badge
                    variant={log.should_proceed ? 'success' : 'danger'}
                  >
                    {log.should_proceed ? 'Proceed' : 'Blocked'}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {log.log_data.triggered_guardrail_ids.length} /{' '}
                  {log.log_data.evaluated_guardrail_ids.length}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination controls */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Page {page} of {totalPages}
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
