/**
 * Trace service
 *
 * @description Service for managing traces.
 * Provides methods to fetch traces by agent.
 *
 * @module trace.service
 */

import { get } from '@/shared/lib/api-client';
import type { Trace, TraceListResponse } from '../types';

/**
 * Trace service interface
 */
export const traceService = {
  /**
   * Get list of traces for an agent
   *
   * @param agentId - Agent UUID
   * @param params - Query parameters
   * @returns Promise resolving to paginated trace list
   */
  async listTraces(
    agentId: string,
    params?: {
      page?: number;
      page_size?: number;
      status?: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<TraceListResponse> {
    const queryParams = new URLSearchParams();

    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size)
      queryParams.append('page_size', params.page_size.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);

    const query = queryParams.toString();
    const endpoint = query
      ? `/agents/${agentId}/traces?${query}`
      : `/agents/${agentId}/traces`;

    return get<TraceListResponse>(endpoint);
  },

  /**
   * Get trace details by ID
   *
   * @param traceId - Trace UUID
   * @returns Promise resolving to trace details
   */
  async getTrace(traceId: string): Promise<Trace> {
    return get<Trace>(`/traces/${traceId}`);
  },
};
