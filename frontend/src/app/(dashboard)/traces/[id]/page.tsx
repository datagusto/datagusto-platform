"use client";

import { useEffect, useRef, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { format, isValid } from 'date-fns';
import {
  ArrowLeft,
  ChevronDown,
  CheckCircle,
  AlertCircle,
  Clock,
  Layers,
  MessageSquare,
  Info,
  ArrowRight,
  Loader2,
  Terminal,
  AlertTriangle,
  Cpu
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Button } from '@/components/ui/button';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import { traceService, agentService } from '@/services';
import type { Trace } from '@/types';
import type { Agent } from '@/types/agent';
import { VisuallyHidden } from "@/components/ui/visually-hidden";

// Extended trace type for this page with additional UI-specific properties
interface TraceFull extends Omit<Trace, 'agent_id' | 'user_query' | 'final_response' | 'started_at' | 'completed_at' | 'latency_ms' | 'total_tokens'> {
  startTime: string;
  endTime: string;
  agentId: string;
  agentName: string | null;
  name: string;
  input: string;
  output: string;
  duration: string;
  modelVersion: string;
  sessionId: string;
  tokens: {
    total: number;
    input: number;
    output: number;
  };
  request?: any;
  response?: any;
  cost?: any;
  evaluation_results?: any;
}

// API response observation type
interface ApiObservation {
  id: string;
  type: string;
  name: string;
  input: any;
  output: any;
  latency_ms: number;
  tokens: number;
  cost: number;
  observation_metadata: any;
  parent_id: string | null;
  start_time?: string;
  end_time?: string | null;
  started_at?: string;
  completed_at?: string | null;
  trace_id: string;
}

// UI observation type with validation results
interface ObservationWithValidation {
  id: string;
  type: string;
  name: string;
  input: any;
  output: any;
  startTime: string;
  endTime: string;
  duration: string;
  metadata?: any;
  model?: string;
  model_parameters?: any;
  usage?: any;
  validationResults?: {
    pass: boolean;
    details: string;
  }[];
}

export default function TraceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [trace, setTrace] = useState<TraceFull | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [observations, setObservations] = useState<ObservationWithValidation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedObservation, setSelectedObservation] = useState<string | null>(null);
  const [observationDialogOpen, setObservationDialogOpen] = useState(false);
  const [selectedObservationDetails, setSelectedObservationDetails] = useState<ObservationWithValidation | null>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function fetchTraceData() {
      try {
        setIsLoading(true);
        // Fetch trace and observations
        const trace = await traceService.getTrace(id);
        const rawObservations = await traceService.getTraceObservations(id);
        const apiObservations = rawObservations as unknown as ApiObservation[];

        // Get the trace data fields with type safety
        const traceData = trace as unknown as {
          id: string;
          status: "IN_PROGRESS" | "COMPLETED" | "ERROR";
          cost: number | null;
          trace_metadata: Record<string, unknown>;
          agent_id: string;
          name: string;
          input: string;
          output: string;
          timestamp: string;
          start_time?: string;
          end_time?: string | null;
          started_at?: string;
          completed_at?: string | null;
          latency_ms?: number | null;
          total_tokens: number | null;
          observability_id: string;
          evaluation_results: any;
          latency: number;
        };

        // Fetch agent data if agent_id is available
        let agentName = null;
        let agentData = null;

        if (traceData.agent_id) {
          try {
            agentData = await agentService.getAgent(traceData.agent_id);
            setAgent(agentData);
            agentName = agentData.name;
          } catch (agentError) {
            console.error("Error fetching agent:", agentError);
            // Continue without agent data if it fails
          }
        }

        // Map API trace data to the TraceFull interface
        const mappedTrace: TraceFull = {
          id: traceData.id,
          status: traceData.status,
          cost: traceData.cost,
          trace_metadata: traceData.trace_metadata,
          // Use the new field structure
          startTime: traceData.start_time || traceData.started_at || traceData.timestamp || new Date().toISOString(),
          endTime: traceData.end_time || traceData.completed_at || new Date().toISOString(),
          agentId: traceData.agent_id,
          agentName: agentName,
          name: traceData.name || `Trace #${traceData.id.substring(0, 8)}`,
          input: traceData.input || '',
          output: traceData.output || '',
          duration: traceData.latency ? `${traceData.latency_ms}ms` : formatDuration(
            new Date(traceData.start_time || traceData.started_at || traceData.timestamp || new Date().toISOString()),
            new Date(traceData.end_time || traceData.completed_at || new Date().toISOString())
          ),
          modelVersion: traceData.trace_metadata?.model_version as string || 'Unknown',
          sessionId: traceData.trace_metadata?.session_id as string || 'Unknown',
          tokens: {
            total: traceData.total_tokens || 0,
            input: Number(traceData.trace_metadata?.input_tokens) || 0,
            output: Number(traceData.trace_metadata?.output_tokens) || 0,
          },
          request: traceData.trace_metadata?.request,
          response: traceData.trace_metadata?.response,
          created_at: '',
          // Check both locations for evaluation_results
          evaluation_results: traceData.evaluation_results ||
            (traceData.trace_metadata && typeof traceData.trace_metadata === 'object' ?
              (traceData.trace_metadata as any)?.evaluation_results : null)
        };

        // Log the evaluation results for debugging
        console.log("Mapped trace evaluation results:", mappedTrace.evaluation_results);
        if (traceData.trace_metadata?.evaluation_results) {
          console.log("Found evaluation results in trace_metadata:", traceData.trace_metadata.evaluation_results);
        }

        // Map observation data and handle null values
        const mappedObservations: ObservationWithValidation[] = apiObservations.map(obs => {
          // Determine the start and end times from either naming convention
          const startTime = obs.start_time || obs.started_at || new Date().toISOString();
          const endTime = obs.end_time || obs.completed_at || new Date().toISOString();

          return {
            id: obs.id,
            type: obs.type.toLowerCase(),
            name: obs.name,
            input: obs.input,
            output: obs.output,
            startTime,
            endTime,
            duration: obs.latency_ms ? `${obs.latency_ms}ms` : formatDuration(
              new Date(startTime),
              new Date(endTime)
            ),
            metadata: obs.observation_metadata,
            model: obs.observation_metadata?.model,
            model_parameters: obs.observation_metadata?.model_parameters,
            usage: obs.observation_metadata?.usage_details || obs.observation_metadata?.usage
          };
        });

        setTrace(mappedTrace);
        setObservations(mappedObservations);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to fetch trace data";
        toast.error(errorMessage);
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    }

    fetchTraceData();
  }, [id]);

  // Helper function to safely format dates
  const formatDate = (dateString: string, formatPattern: string = 'PPpp') => {
    try {
      const date = new Date(dateString);
      if (!isValid(date)) {
        return "Invalid date";
      }
      return format(date, formatPattern);
    } catch (error) {
      console.error("Date formatting error:", error);
      return "Invalid date";
    }
  };

  // Helper function to format duration
  const formatDuration = (start: Date, end: Date): string => {
    const durationMs = end.getTime() - start.getTime();

    if (durationMs < 1000) {
      return `${durationMs}ms`;
    } else if (durationMs < 60000) {
      return `${(durationMs / 1000).toFixed(2)}s`;
    } else {
      const minutes = Math.floor(durationMs / 60000);
      const seconds = ((durationMs % 60000) / 1000).toFixed(0);
      return `${minutes}m ${seconds}s`;
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error || !trace) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" asChild>
            <Link href="/traces">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href="/traces">Traces</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink>Error</BreadcrumbLink>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>

        <Card>
          <CardContent className="flex flex-col items-center justify-center py-10">
            <div className="rounded-full bg-red-100 p-3 mb-4">
              <AlertCircle className="h-8 w-8 text-red-600" />
            </div>
            <h3 className="text-xl font-medium mb-2">Unable to load trace</h3>
            <p className="text-muted-foreground text-center mb-4">{error || "Trace not found"}</p>
            <div className="flex gap-2">
              <Button variant="outline" asChild>
                <Link href="/traces">
                  Go Back
                </Link>
              </Button>
              <Button onClick={() => window.location.reload()}>
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Format and sort the observations for the timeline
  const sortedObservations = [...observations].sort(
    (a, b) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime()
  );

  // Calculate the timeline boundaries
  const traceStartTime = new Date(trace.startTime).getTime();
  const traceEndTime = new Date(trace.endTime).getTime();
  const traceDuration = traceEndTime - traceStartTime;

  // Calculate position and width for timeline items
  const getTimelinePosition = (startTime: string, endTime: string) => {
    const start = new Date(startTime).getTime();
    const end = new Date(endTime).getTime();

    const startPercentage = ((start - traceStartTime) / traceDuration) * 100;
    const widthPercentage = ((end - start) / traceDuration) * 100;

    return {
      left: `${Math.max(0, startPercentage)}%`,
      width: `${Math.max(0.5, widthPercentage)}%`
    };
  };

  // Handle selecting an observation
  const handleSelectObservation = (observation: ObservationWithValidation) => {
    setSelectedObservation(observation.id);
    setSelectedObservationDetails(observation);
    setObservationDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="icon" asChild>
          <Link href="/traces">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/traces">Traces</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink>#{id.substring(0, 8)}</BreadcrumbLink>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center text-xs text-muted-foreground">
                <Clock className="h-3.5 w-3.5 mr-1" />
                {formatDate(trace.startTime)}
              </div>
            </div>
            <CardTitle className="text-xl">{trace.name}</CardTitle>
            <CardDescription>
              <div className="flex flex-col gap-2 mt-2">
                {agent && (
                  <div className="text-sm">
                    <span className="font-medium">Agent:</span>{' '}
                    <Link href={`/agents/${trace.agentId}`} className="hover:underline">
                      {agent.name}
                    </Link>
                  </div>
                )}
                <div className="flex flex-wrap gap-4 text-sm">
                  <div>
                    <span className="font-medium">Tokens:</span> {trace.tokens.total} ({trace.tokens.input} in / {trace.tokens.output} out)
                  </div>
                  <div>
                    <span className="font-medium">Cost:</span> {trace.cost}
                  </div>
                </div>
              </div>
            </CardDescription>
          </CardHeader>
        </Card>

        {trace.evaluation_results?.root_cause?.number_of_issues > 0 && (
          <Card className="border-amber-300 bg-amber-50">

            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                <CardTitle className="text-base">Quality Issues Detected</CardTitle>
              </div>
              <CardDescription>
                {trace.evaluation_results?.root_cause?.number_of_issues} issue(s) found during evaluation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 text-sm">
                <p className="font-medium mb-1">Description:</p>
                <p className="text-muted-foreground">{trace.evaluation_results?.root_cause?.description}</p>
              </div>
              <div className="space-y-3">
                <p className="font-medium text-sm">Issue History:</p>
                <div className="space-y-2">
                  {trace.evaluation_results?.root_cause?.history.map((item: any, index: number) => (
                    <div key={index} className="text-sm border-l-2 border-amber-300 pl-3 py-1">
                      <div className="flex justify-between">
                        <span className="font-medium">{item.name || 'Unknown'}</span>
                        <span className="text-xs text-muted-foreground">
                          {typeof item.timestamp === 'string' ? formatDate(item.timestamp, 'PP p') : ''}
                        </span>
                      </div>
                      <p className="text-muted-foreground mt-1">{item.description || ''}</p>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Trace Observations</CardTitle>
            <CardDescription>
              Step-by-step details of the trace execution
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {observations.length > 0 ? (
              <div className="w-full">
                <div className="grid grid-cols-[150px_1fr_120px_100px] py-4 px-6 border-b font-medium text-sm">
                  <div>Type</div>
                  <div>Name</div>
                  <div>Duration</div>
                  <div className="text-center">Actions</div>
                </div>

                {sortedObservations.map(observation => (
                  <div
                    key={observation.id}
                    className="grid grid-cols-[150px_1fr_120px_100px] py-4 px-6 border-b items-center text-sm hover:bg-slate-50"
                  >
                    <div className="flex items-center gap-2">
                      {observation.type === 'user query' && (
                        <div className="rounded-full w-5 h-5 bg-green-100 flex items-center justify-center">
                          <span className="text-xs">U</span>
                        </div>
                      )}
                      {observation.type === 'database query' && (
                        <div className="rounded-full w-5 h-5 bg-amber-100 flex items-center justify-center">
                          <span className="text-xs">D</span>
                        </div>
                      )}
                      {observation.type === 'function call' && (
                        <div className="rounded-full w-5 h-5 bg-blue-100 flex items-center justify-center">
                          <span className="text-xs">{'{}'}</span>
                        </div>
                      )}
                      {observation.type === 'llm' && (
                        <div className="rounded-full w-5 h-5 bg-purple-100 flex items-center justify-center">
                          <span className="text-xs">L</span>
                        </div>
                      )}
                      {observation.type === 'output generation' && (
                        <div className="rounded-full w-5 h-5 bg-slate-100 flex items-center justify-center">
                          <span className="text-xs">O</span>
                        </div>
                      )}
                      {!['user query', 'database query', 'function call', 'llm', 'output generation'].includes(observation.type) && (
                        <div className="rounded-full w-5 h-5 bg-gray-100 flex items-center justify-center">
                          <span className="text-xs">{observation.type.charAt(0).toUpperCase()}</span>
                        </div>
                      )}
                      <span className="uppercase text-xs font-medium">{observation.type}</span>
                    </div>
                    <div className="truncate">{observation.name}</div>
                    <div>{observation.duration}</div>
                    <div className="text-center">
                      <Button
                        variant="link"
                        size="sm"
                        className="text-blue-500 hover:text-blue-700"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectObservation(observation);
                        }}
                      >
                        View
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-muted-foreground">
                No observations available for this trace
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={observationDialogOpen} onOpenChange={setObservationDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle>{selectedObservationDetails?.name || 'Observation Details'}</DialogTitle>
            <DialogDescription className="flex justify-between">
              <span>Type: {selectedObservationDetails?.type?.toUpperCase() || 'Unknown'}</span>
              <span>Duration: {selectedObservationDetails?.duration || 'N/A'}</span>
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[calc(80vh-120px)]">
            <div className="grid gap-6 pr-4">
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Times</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Start Time</div>
                    <div className="text-sm">
                      {selectedObservationDetails?.startTime ? formatDate(selectedObservationDetails.startTime) : 'Not provided'}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">End Time</div>
                    <div className="text-sm">
                      {selectedObservationDetails?.endTime ? formatDate(selectedObservationDetails.endTime) : 'Not provided'}
                    </div>
                  </div>
                </div>
              </div>

              {(selectedObservationDetails?.type === 'llm' || selectedObservationDetails?.type === 'generation') && (
                <>
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Model Information</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">Model</div>
                        <div className="text-sm">
                          {selectedObservationDetails?.model || 'Not provided'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">Model Parameters</div>
                        <div className="rounded-md border bg-muted/50 p-2">
                          <ScrollArea className="h-[80px]">
                            <pre className="text-xs whitespace-pre-wrap break-all">
                              {selectedObservationDetails?.model_parameters
                                ? JSON.stringify(selectedObservationDetails.model_parameters, null, 2)
                                : 'Not provided'}
                            </pre>
                          </ScrollArea>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Usage</h4>
                    <div className="rounded-md border bg-muted/50 p-2">
                      <ScrollArea className="h-[80px]">
                        <pre className="text-xs whitespace-pre-wrap break-all">
                          {selectedObservationDetails?.usage
                            ? JSON.stringify(selectedObservationDetails.usage, null, 2)
                            : 'Not provided'}
                        </pre>
                      </ScrollArea>
                    </div>
                  </div>
                </>
              )}

              <div className="space-y-2">
                <h4 className="text-sm font-medium">Input</h4>
                <div className="rounded-md border bg-muted/50 p-4">
                  <ScrollArea className="h-[180px]">
                    <pre className="text-sm whitespace-pre-wrap break-all">
                      {selectedObservationDetails?.input
                        ? typeof selectedObservationDetails.input === 'string'
                          ? decodeUnicodeEscapes(selectedObservationDetails.input)
                          : decodeUnicodeEscapes(JSON.stringify(selectedObservationDetails.input, null, 2))
                        : 'No input available'}
                    </pre>
                  </ScrollArea>
                </div>
              </div>
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Output</h4>
                <div className="rounded-md border bg-muted/50 p-4">
                  <ScrollArea className="h-[180px]">
                    <pre className="text-sm whitespace-pre-wrap break-all">
                      {selectedObservationDetails?.output
                        ? typeof selectedObservationDetails.output === 'string'
                          ? decodeUnicodeEscapes(selectedObservationDetails.output)
                          : decodeUnicodeEscapes(JSON.stringify(selectedObservationDetails.output, null, 2))
                        : 'No output available'}
                    </pre>
                  </ScrollArea>
                </div>
              </div>
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Add Unicode decoder function
function decodeUnicodeEscapes(str: string): string {
  try {
    return str.replace(/\\u([0-9a-fA-F]{4})/g, (match, grp) => {
      return String.fromCharCode(parseInt(grp, 16));
    });
  } catch (e) {
    console.error("Error decoding Unicode:", e);
    return str;
  }
} 