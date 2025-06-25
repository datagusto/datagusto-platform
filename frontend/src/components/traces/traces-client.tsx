"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { TraceService } from '@/services';
import { Trace, TraceSyncStatus } from '@/types';
import { RefreshCw } from 'lucide-react';

interface TracesClientProps {
  projectId: string;
}

export function TracesClient({ projectId }: TracesClientProps) {
  const router = useRouter();
  
  const [traces, setTraces] = useState<Trace[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<TraceSyncStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchTraces = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await TraceService.getTracesByProject(projectId);
      setTraces(response.traces);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch traces');
    } finally {
      setLoading(false);
    }
  };

  const handleSyncTraces = async () => {
    try {
      setSyncing(true);
      setError(null);
      const status = await TraceService.syncTraces(projectId);
      setSyncStatus(status);
      
      // Refresh traces after sync
      if (!status.error) {
        await fetchTraces();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sync traces');
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    fetchTraces();
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex-1 p-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading traces...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Recent Trace Logs</h1>
          <p className="text-gray-600">
            View detailed trace logs for all agents
          </p>
        </div>
        <Button 
          onClick={handleSyncTraces}
          disabled={syncing}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing...' : 'Sync Traces'}
        </Button>
      </div>

      {error && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}

      {syncStatus && (
        <Card className="mb-6 border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="font-medium text-blue-900">Sync Completed</p>
              <div className="text-sm text-blue-700">
                <p>Total traces: {syncStatus.total_traces}</p>
                <p>New traces: {syncStatus.new_traces}</p>
                <p>Updated traces: {syncStatus.updated_traces}</p>
                {syncStatus.sync_completed_at && (
                  <p>Completed at: {TraceService.formatTimestamp(syncStatus.sync_completed_at)}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {traces.length === 0 ? (
            <div className="text-center py-16 px-6">
              <div className="text-gray-400 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No traces found</h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                No AI agent traces have been synced yet. Click "Sync Traces" to import traces from your observability platform.
              </p>
              <Button onClick={handleSyncTraces} disabled={syncing} className="bg-blue-600 hover:bg-blue-700">
                <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Sync Traces'}
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-b">
                    <TableHead className="font-semibold text-gray-900">ID</TableHead>
                    <TableHead className="font-semibold text-gray-900">Name ↕</TableHead>
                    <TableHead className="font-semibold text-gray-900">Status</TableHead>
                    <TableHead className="font-semibold text-gray-900">Start Time</TableHead>
                    <TableHead className="font-semibold text-gray-900">Duration</TableHead>
                  </TableRow>
                </TableHeader>
              <TableBody>
                {traces.map((trace) => {
                  const status = TraceService.getTraceStatus(trace) || 'Unknown';
                  const duration = TraceService.getTraceDuration(trace) || '0.00s';
                  const agentName = trace.raw_data?.metadata?.agent_name || 
                                   trace.raw_data?.name || 
                                   trace.raw_data?.sessionId ||
                                   'Unknown Agent';
                  const traceName = TraceService.getTraceName(trace) || `Trace ${trace.external_id.slice(0, 8)}`;
                  
                  return (
                    <TableRow 
                      key={trace.id} 
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => router.push(`/projects/${projectId}/traces/${trace.id}`)}
                    >
                      <TableCell className="font-mono text-sm">
                        #{trace.external_id?.slice(0, 8) || trace.id.slice(0, 8)}
                      </TableCell>
                      <TableCell className="font-medium">
                        {traceName}
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={
                            status.toLowerCase().includes('completed') || status.toLowerCase().includes('success') ? 'success' :
                            status.toLowerCase().includes('error') || status.toLowerCase().includes('failed') || status.toLowerCase().includes('incident') ? 'error' :
                            status.toLowerCase().includes('running') || status.toLowerCase().includes('pending') ? 'warning' :
                            'secondary'
                          }
                        >
                          {status.toLowerCase().includes('incident') ? '● INCIDENT' :
                           status.toLowerCase().includes('completed') || status.toLowerCase().includes('success') ? '● COMPLETED' :
                           status.toLowerCase().includes('error') || status.toLowerCase().includes('failed') ? '● ERROR' :
                           '● ' + status.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div className="font-medium">
                            {new Date(trace.timestamp).toLocaleDateString('en-US', {
                              day: '2-digit',
                              month: '2-digit', 
                              year: 'numeric'
                            })}
                          </div>
                          <div className="text-gray-500">
                            {new Date(trace.timestamp).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit',
                              second: '2-digit'
                            })}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {duration}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}