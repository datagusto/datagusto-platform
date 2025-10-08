/**
 * Evaluation logs API service
 *
 * @description API client functions for fetching guardrail evaluation logs.
 * Communicates with backend evaluation logs endpoints.
 *
 * @module evaluation-logs.service
 */

import { get } from '@/shared/lib/api-client';
import type { EvaluationLogsListResponse } from '../types/evaluation-log.types';

/**
 * Fetch evaluation logs for an agent
 *
 * @description Get paginated list of evaluation logs for a specific agent.
 * Requires authentication and project membership.
 *
 * @param agentId - Agent UUID
 * @param page - Page number (1-indexed)
 * @param pageSize - Number of items per page
 * @returns Promise resolving to evaluation logs list response
 *
 * @example
 * ```typescript
 * const logs = await fetchEvaluationLogsByAgent(
 *   'agent-uuid',
 *   1,
 *   20
 * );
 * console.log(logs.items); // Array of evaluation logs
 * console.log(logs.total); // Total count
 * ```
 */
export async function fetchEvaluationLogsByAgent(
  agentId: string,
  page: number = 1,
  pageSize: number = 20
): Promise<EvaluationLogsListResponse> {
  const queryParams = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  return get<EvaluationLogsListResponse>(
    `/guardrails/agents/${agentId}/evaluation-logs?${queryParams}`
  );
}

/**
 * Fetch evaluation logs for a project
 *
 * @description Get paginated list of evaluation logs for a specific project.
 * Requires authentication and project membership.
 *
 * @param projectId - Project UUID
 * @param page - Page number (1-indexed)
 * @param pageSize - Number of items per page
 * @returns Promise resolving to evaluation logs list response
 *
 * @example
 * ```typescript
 * const logs = await fetchEvaluationLogsByProject(
 *   'project-uuid',
 *   1,
 *   20
 * );
 * ```
 */
export async function fetchEvaluationLogsByProject(
  projectId: string,
  page: number = 1,
  pageSize: number = 20
): Promise<EvaluationLogsListResponse> {
  const queryParams = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  return get<EvaluationLogsListResponse>(
    `/guardrails/projects/${projectId}/evaluation-logs?${queryParams}`
  );
}

/**
 * Fetch single evaluation log by request ID
 *
 * @description Get detailed evaluation log for a specific request.
 * Useful for viewing full evaluation details.
 *
 * @param requestId - Evaluation request ID
 * @returns Promise resolving to evaluation log
 *
 * @example
 * ```typescript
 * const log = await fetchEvaluationLogByRequestId('req_abc123def456');
 * console.log(log.log_data.evaluation_result);
 * ```
 */
export async function fetchEvaluationLogByRequestId(
  requestId: string
): Promise<EvaluationLogsListResponse['items'][0]> {
  return get<EvaluationLogsListResponse['items'][0]>(
    `/guardrails/evaluation-logs/${requestId}`
  );
}
