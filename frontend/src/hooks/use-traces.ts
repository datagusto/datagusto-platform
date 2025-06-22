import { useQuery } from '@tanstack/react-query';
import { TraceService } from '@/services';
import { queryKeys } from '@/lib/query-client';
import type { Trace, TraceListResponse } from '@/types';

interface TraceParams {
  limit?: number;
  offset?: number;
  search?: string;
}

export function useProjectTraces(projectId: string | undefined, params: TraceParams = {}) {
  return useQuery({
    queryKey: queryKeys.projectTraces(projectId || '', params),
    queryFn: () => TraceService.getTracesByProject(projectId!, params),
    enabled: !!projectId,
    staleTime: 30 * 1000, // 30 seconds for traces (more dynamic data)
    placeholderData: (previousData) => previousData, // Keep previous data while fetching
  });
}

export function useTrace(projectId: string | undefined, traceId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.trace(traceId || ''),
    queryFn: () => TraceService.getTraceById(projectId!, traceId!),
    enabled: !!projectId && !!traceId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// Hook for real-time stats (used in dashboard)
export function useProjectStats(projectId: string | undefined) {
  const { data: allTraces, isLoading: isLoadingAll } = useQuery({
    queryKey: [...queryKeys.projectTraces(projectId || '', { limit: 1000 }), 'stats'],
    queryFn: () => TraceService.getTracesByProject(projectId!, { limit: 1000 }),
    enabled: !!projectId,
    staleTime: 60 * 1000, // 1 minute
    select: (data: TraceListResponse) => {
      const traces = data.traces;
      const totalTraces = traces.length;
      const activeIncidents = traces.filter((trace: Trace) => {
        const status = TraceService.getTraceStatus(trace).toLowerCase();
        return status.includes('error') || status.includes('incident') || status.includes('failed');
      }).length;
      
      return {
        totalTraces,
        activeIncidents,
        guardrails: 0, // TODO: Implement when guardrails API is available
      };
    },
  });

  const { data: recentTraces, isLoading: isLoadingRecent } = useQuery({
    queryKey: [...queryKeys.projectTraces(projectId || '', { limit: 5 }), 'recent'],
    queryFn: () => TraceService.getTracesByProject(projectId!, { limit: 5 }),
    enabled: !!projectId,
    staleTime: 30 * 1000, // 30 seconds
    select: (data: TraceListResponse) => data.traces,
  });

  return {
    stats: allTraces,
    recentTraces,
    isLoading: isLoadingAll || isLoadingRecent,
  };
}