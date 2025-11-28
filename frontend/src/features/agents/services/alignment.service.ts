/**
 * Alignment service
 *
 * @description Service for managing alignment sessions.
 * Provides methods to fetch alignment sessions for an agent.
 *
 * @module alignment.service
 */

import { get } from '@/shared/lib/api-client';
import type { AlignmentSessionListResponse, SessionData } from '../types';

/**
 * Alignment service interface
 */
export const alignmentService = {
  /**
   * Get list of alignment sessions for an agent
   *
   * @param agentId - Agent UUID
   * @returns Promise resolving to session list response
   *
   * @example
   * ```typescript
   * const sessions = await alignmentService.listSessions('agent-uuid');
   * console.log(sessions.sessions); // Array of alignment sessions
   * ```
   */
  async listSessions(agentId: string): Promise<AlignmentSessionListResponse> {
    return get<AlignmentSessionListResponse>(`/agents/${agentId}/sessions`);
  },

  /**
   * Get detailed information for a specific alignment session
   *
   * @param agentId - Agent UUID
   * @param sessionId - Session ID
   * @returns Promise resolving to session data
   *
   * @example
   * ```typescript
   * const session = await alignmentService.getSessionDetail('agent-uuid', 'session-id');
   * console.log(session.inference_result); // Inference result data
   * ```
   */
  async getSessionDetail(
    agentId: string,
    sessionId: string
  ): Promise<SessionData> {
    return get<SessionData>(`/agents/${agentId}/sessions/${sessionId}`);
  },
};
