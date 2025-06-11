'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { TraceService } from '@/services';
import { Trace, QualityIssue } from '@/types';
import { QualityMetrics } from '@/components/quality-metrics';
import { ArrowLeft, Clock, Activity, User, Calendar, AlertTriangle, Eye, TrendingDown, CheckCircle } from 'lucide-react';

export default function TraceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const traceId = params.traceId as string;

  const [trace, setTrace] = useState<Trace | null>(null);
  const [observations, setObservations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedObservation, setSelectedObservation] = useState<any | null>(null);
  const [isObservationModalOpen, setIsObservationModalOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch trace data and observations separately
        const [traceData, observationsData] = await Promise.all([
          TraceService.getTraceById(projectId, traceId),
          TraceService.getObservations(projectId, traceId)
        ]);

        // Debug quality issues matching
        if (process.env.NODE_ENV === 'development' && traceData.quality_issues) {
          console.log('Quality issues:', traceData.quality_issues);
          console.log('Observations from API:', observationsData?.map(obs => ({ id: obs.id, external_id: obs.external_id })));
        }

        setTrace(traceData);
        setObservations(observationsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [projectId, traceId]);

  if (loading) {
    return (
      <div className="flex-1 p-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading trace details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !trace) {
    return (
      <div className="flex-1 p-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {error || 'Trace not found'}
            </h3>
            <Link href={`/projects/${projectId}/traces`}>
              <Button variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Traces
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-8">
      {/* Breadcrumb */}
      <div className="flex items-center space-x-2 text-sm text-gray-600 mb-6">
        <Link href={`/projects/${projectId}/traces`} className="hover:text-gray-900">
          Traces
        </Link>
        <span>›</span>
        <span className="text-gray-900">#{trace.external_id.slice(0, 8)}</span>
      </div>

      {/* Trace Info */}
      <div className="mb-8">
        <div className="flex items-center text-sm text-gray-600 mb-2">
          <Clock className="h-4 w-4 mr-1" />
          <span>{new Date(trace.timestamp).toLocaleDateString()} {new Date(trace.timestamp).toLocaleTimeString()}</span>
        </div>
        <h1 className="text-3xl font-bold mb-2">{TraceService.getTraceName(trace)}</h1>

        {/* Quality Score Display */}
        {trace.quality_score !== undefined && (
          <div className="flex items-center space-x-3 mt-4">
            <Badge
              variant={
                trace.quality_score >= 0.8 ? 'default' :
                  trace.quality_score >= 0.5 ? 'secondary' : 'destructive'
              }
              className="flex items-center space-x-1"
            >
              <CheckCircle className="h-3 w-3" />
              <span>Quality Score: {(trace.quality_score * 100).toFixed(1)}%</span>
            </Badge>

            {trace.quality_issues && trace.quality_issues.length > 0 && (
              <Badge variant="destructive" className="flex items-center space-x-1">
                <TrendingDown className="h-3 w-3" />
                <span>{trace.quality_issues.length} Issue{trace.quality_issues.length > 1 ? 's' : ''} Found</span>
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* Trace Observations */}
      <div className="mb-8">
        <div className="mb-4">
          <h2 className="text-xl font-semibold">Trace Observations</h2>
          <p className="text-gray-600">Step-by-step details of the trace execution</p>
        </div>

        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-b">
                    <TableHead className="font-semibold text-gray-900 w-16">Type</TableHead>
                    <TableHead className="font-semibold text-gray-900">Name</TableHead>
                    <TableHead className="font-semibold text-gray-900 text-right">Duration</TableHead>
                    <TableHead className="font-semibold text-gray-900 text-right w-24">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {observations && observations.length > 0 ? (
                    (() => {
                      // バックエンドと同じロジック：親になっているObservation IDのセットを作成
                      const parentIds = new Set();

                      // まず、parent_observation_idを持つObservationを見つけて、その親IDをセットに追加
                      observations.forEach((obs: any) => {
                        const rawData = obs.raw_data;
                        if (rawData && typeof rawData === 'object') {
                          // LangfuseのrawDataから親IDを取得
                          const parentObservationId = rawData.parentObservationId;
                          if (parentObservationId) {
                            parentIds.add(parentObservationId);
                          }
                        }
                      });

                      if (process.env.NODE_ENV === 'development') {
                        console.log('Parent IDs found:', Array.from(parentIds));
                        console.log('All observations:', observations.map(obs => ({
                          id: obs.raw_data?.id,
                          parentId: obs.raw_data?.parentObservationId,
                          isParent: parentIds.has(obs.raw_data?.id)
                        })));
                      }

                      // 親になっていないObservation（リーフノード）だけをフィルタ
                      return observations
                        .filter((observation: any) => {
                          const rawData = observation.raw_data;
                          if (rawData && typeof rawData === 'object' && rawData.id) {
                            // このObservationのIDが、誰かの親になっていないかチェック
                            const isLeaf = !parentIds.has(rawData.id);
                            if (process.env.NODE_ENV === 'development') {
                              console.log(`Observation ${rawData.id}: isLeaf=${isLeaf}`);
                            }
                            return isLeaf;
                          }
                          // raw_dataにidがない場合はリーフとして扱う
                          return true;
                        })
                    })()
                      .sort((a: any, b: any) => {
                        const aStartTime = a.raw_data?.startTime || a.start_time;
                        const bStartTime = b.raw_data?.startTime || b.start_time;
                        if (!aStartTime) return 1;
                        if (!bStartTime) return -1;
                        return new Date(aStartTime).getTime() - new Date(bStartTime).getTime();
                      })
                      .map((observation: any, index: number) => {
                        // observation.raw_dataから正しくデータを取得
                        const observationData = observation.raw_data || observation;
                        const observationType = (observationData.type || 'OBSERVATION').toUpperCase();

                        // Name決定のロジック改善
                        let observationName = observationData.name || `Step ${index + 1}`;

                        // Tool使用の場合、より詳細な名前を表示
                        if (observationData.output?.messages?.[0]?.content) {
                          // Outputメッセージの内容から名前を抽出
                          const content = observationData.output.messages[0].content;
                          if (typeof content === 'string' && content.length > 0) {
                            observationName = content.length > 50 ? content.substring(0, 50) + '...' : content;
                          }
                        } else if (observationData.input?.messages?.[0]?.tool_calls?.[0]?.function?.name) {
                          observationName = observationData.input.messages[0].tool_calls[0].function.name;
                        } else if (observationData.input?.messages?.[0]?.content) {
                          const content = observationData.input.messages[0].content;
                          if (typeof content === 'string' && content.length > 0) {
                            observationName = content.length > 50 ? content.substring(0, 50) + '...' : content;
                          }
                        }

                        const hasError = observationData.level === 'ERROR' || observationData.status === 'ERROR' ||
                          observationData.statusMessage;

                        // Check if this observation has quality issues
                        const hasQualityIssues = trace.quality_issues?.some(
                          issue => {
                            const match = issue.observation_id === observation.id;
                            if (process.env.NODE_ENV === 'development') {
                              console.log(`Quality check: ${issue.observation_id} === ${observation.id} ? ${match}`);
                              if (match) {
                                console.log(`🎯 MATCH: Quality issue found for observation ${observation.id}`);
                              }
                            }
                            return match;
                          }
                        ) || false;

                        // Duration計算
                        let duration = '0s';
                        if (observationData.endTime && observationData.startTime) {
                          const start = new Date(observationData.startTime).getTime();
                          const end = new Date(observationData.endTime).getTime();
                          const diff = end - start;
                          duration = diff < 1000 ? `${diff}ms` : `${(diff / 1000).toFixed(3)}s`;
                        } else if (observationData.latency) {
                          duration = typeof observationData.latency === 'number' ? `${observationData.latency}ms` : observationData.latency;
                        }

                        // Row styling: simple yellow background if quality issues exist
                        const rowClassName = hasQualityIssues
                          ? "hover:bg-gray-50 bg-yellow-50"
                          : "hover:bg-gray-50";

                        return (
                          <TableRow key={index} className={rowClassName}>
                            <TableCell>
                              <div className="flex items-center space-x-2">
                                <span className={`inline-flex items-center justify-center w-6 h-6 rounded text-xs font-semibold ${observationType === 'GENERATION' ? 'bg-gray-800 text-white' : 'bg-gray-200 text-gray-700'
                                  }`}>
                                  {observationType.charAt(0)}
                                </span>
                                <span className="text-xs uppercase text-gray-700">{observationType}</span>
                              </div>
                            </TableCell>
                            <TableCell className="font-medium">
                              <div className="flex items-center">
                                {hasError && <AlertTriangle className="inline h-4 w-4 text-red-500 mr-2" />}
                                {hasQualityIssues && <TrendingDown className="inline h-4 w-4 text-yellow-600 mr-2" />}
                                <span>{observationName}</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-right font-mono text-sm">
                              {duration}
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-blue-600 hover:text-blue-800"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedObservation(observation);
                                  setIsObservationModalOpen(true);
                                }}
                              >
                                <Eye className="h-4 w-4 mr-1" />
                                View
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })
                  ) : (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-8 text-gray-500">
                        No observations available for this trace
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Observation Detail Modal */}
      <Dialog open={isObservationModalOpen} onOpenChange={setIsObservationModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Observation Details
            </DialogTitle>
            <DialogDescription>
              {selectedObservation && (
                <span>
                  {(() => {
                    const observationData = selectedObservation.raw_data || selectedObservation;
                    const observationType = (observationData.type || 'OBSERVATION').toUpperCase();
                    let observationName = observationData.name || 'Unnamed';

                    if (observationData.output?.messages?.[0]?.content) {
                      const content = observationData.output.messages[0].content;
                      if (typeof content === 'string' && content.length > 0) {
                        observationName = content.length > 50 ? content.substring(0, 50) + '...' : content;
                      }
                    } else if (observationData.input?.messages?.[0]?.tool_calls?.[0]?.function?.name) {
                      observationName = observationData.input.messages[0].tool_calls[0].function.name;
                    } else if (observationData.input?.messages?.[0]?.content) {
                      const content = observationData.input.messages[0].content;
                      if (typeof content === 'string' && content.length > 0) {
                        observationName = content.length > 50 ? content.substring(0, 50) + '...' : content;
                      }
                    }

                    return `${observationType}: ${observationName}`;
                  })()}
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          {selectedObservation && (
            <div className="space-y-6">
              {(() => {
                const rawData = selectedObservation.raw_data || selectedObservation;

                return (
                  <>
                    {/* Basic Information */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Basic Information</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm font-medium text-gray-500">ID</label>
                            <p className="text-sm font-mono">{selectedObservation.id || rawData.id || 'N/A'}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-gray-500">Type</label>
                            <p className="text-sm font-mono">{(rawData.type || selectedObservation.type || 'OBSERVATION').toUpperCase()}</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm font-medium text-gray-500">Name</label>
                            <p className="text-sm">{rawData.name || selectedObservation.name || 'Unnamed'}</p>
                          </div>
                        </div>

                        {rawData.startTime && (
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="text-sm font-medium text-gray-500">Start Time</label>
                              <p className="text-sm font-mono">{new Date(rawData.startTime).toLocaleString()}</p>
                            </div>
                            {rawData.endTime && (
                              <div>
                                <label className="text-sm font-medium text-gray-500">End Time</label>
                                <p className="text-sm font-mono">{new Date(rawData.endTime).toLocaleString()}</p>
                              </div>
                            )}
                          </div>
                        )}

                        {rawData.latency && (
                          <div>
                            <label className="text-sm font-medium text-gray-500">Latency</label>
                            <p className="text-sm font-mono">{typeof rawData.latency === 'number' ? `${rawData.latency}ms` : rawData.latency}</p>
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {/* Quality Metrics */}
                    <QualityMetrics
                      observationId={selectedObservation.id}
                      qualityIssues={trace.quality_issues || []}
                    />

                    {/* Input Data */}
                    {rawData.input && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-lg">Input</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap break-words max-w-full">
                            {JSON.stringify(rawData.input, null, 2)}
                          </pre>
                        </CardContent>
                      </Card>
                    )}

                    {/* Output Data */}
                    {rawData.output && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-lg">Output</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap break-words max-w-full">
                            {JSON.stringify(rawData.output, null, 2)}
                          </pre>
                        </CardContent>
                      </Card>
                    )}

                    {/* Metadata */}
                    {rawData.metadata && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-lg">Metadata</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap break-words max-w-full">
                            {JSON.stringify(rawData.metadata, null, 2)}
                          </pre>
                        </CardContent>
                      </Card>
                    )}

                    {/* Raw Data (fallback) */}
                    {!rawData.input && !rawData.output && !rawData.metadata && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-lg">Raw Data</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap break-words max-w-full">
                            {JSON.stringify(rawData, null, 2)}
                          </pre>
                        </CardContent>
                      </Card>
                    )}
                  </>
                );
              })()}
            </div>
          )}
        </DialogContent>
      </Dialog>

    </div>
  );
}