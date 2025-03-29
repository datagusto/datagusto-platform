"use client";

import { useEffect, useRef, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { format } from 'date-fns';
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
import { traceService } from '@/services';
import type { Trace } from '@/types';

// Extended trace type for this page with additional UI-specific properties
interface TraceFull extends Omit<Trace, 'agent_id' | 'user_query' | 'final_response' | 'started_at' | 'completed_at' | 'latency_ms' | 'total_tokens'> {
  startTime: string;
  endTime: string;
  agentId: string;
  agentName: string;
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
  started_at: string;
  completed_at: string | null;
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
        // Replace getTraceWithObservations with separate calls to getTrace and getTraceObservations
        const trace = await traceService.getTrace(id);
        const rawObservations = await traceService.getTraceObservations(id);
        const apiObservations = rawObservations as unknown as ApiObservation[];
        
        // Map API trace data to the TraceFull interface
        const mappedTrace: TraceFull = {
          id: trace.id,
          status: trace.status,
          cost: trace.cost,
          trace_metadata: trace.trace_metadata,
          // Map API fields to UI-specific field names
          startTime: trace.started_at,
          endTime: trace.completed_at || new Date().toISOString(),
          agentId: trace.agent_id,
          agentName: trace.trace_metadata?.agent_name as string || 'Unknown Agent',
          name: trace.trace_metadata?.name as string || `Trace #${trace.id.substring(0, 8)}`,
          input: trace.user_query || '',
          output: trace.final_response || '',
          duration: formatDuration(new Date(trace.started_at), new Date(trace.completed_at || new Date())),
          modelVersion: trace.trace_metadata?.model_version as string || 'Unknown',
          sessionId: trace.trace_metadata?.session_id as string || 'Unknown',
          tokens: {
            total: trace.total_tokens || 0,
            input: Number(trace.trace_metadata?.input_tokens) || 0,
            output: Number(trace.trace_metadata?.output_tokens) || 0,
          },
          request: trace.trace_metadata?.request,
          response: trace.trace_metadata?.response
        };
        
        // Map observation data and handle null completed_at values
        const mappedObservations: ObservationWithValidation[] = apiObservations.map(obs => ({
          id: obs.id,
          type: obs.type.toLowerCase(),
          name: obs.name,
          input: obs.input,
          output: obs.output,
          startTime: obs.started_at,
          endTime: obs.completed_at || new Date().toISOString(),
          duration: formatDuration(
            new Date(obs.started_at), 
            new Date(obs.completed_at || new Date())
          ),
          metadata: obs.observation_metadata
        }));
        
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
              <Badge variant={trace.status.toLowerCase() === "completed" ? "default" : "destructive"}>
                {trace.status}
              </Badge>
              <div className="flex items-center text-xs text-muted-foreground">
                <Clock className="h-3.5 w-3.5 mr-1" />
                {format(new Date(trace.startTime), 'PPpp')}
              </div>
            </div>
            <CardTitle className="text-xl">{trace.name}</CardTitle>
            <CardDescription>
              <div className="flex flex-col gap-2 mt-2">
                <div className="text-sm">
                  <span className="font-medium">Input:</span> {trace.input}
                </div>
                <div className="text-sm">
                  <span className="font-medium">Agent:</span>{' '}
                  <Link href={`/agents/${trace.agentId}`} className="hover:underline">
                    {trace.agentName}
                  </Link>
                </div>
                <div className="flex flex-wrap gap-4 text-sm">
                  <div>
                    <span className="font-medium">Duration:</span> {trace.duration}
                  </div>
                  <div>
                    <span className="font-medium">Model:</span> {trace.modelVersion}
                  </div>
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
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Observations ({observations.length})</CardTitle>
            <CardDescription>
              List of operations performed during trace execution
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {observations.length > 0 ? (
              <div className="divide-y">
                {sortedObservations.map(observation => (
                  <div
                    key={observation.id}
                    className={`p-3 cursor-pointer hover:bg-slate-50 ${
                      selectedObservation === observation.id ? 'bg-slate-50' : ''
                    }`}
                    onClick={() => handleSelectObservation(observation)}
                  >
                    <div className="flex justify-between mb-1">
                      <div className="flex items-center">
                        {observation.type === 'llm' && <Terminal className="h-4 w-4 mr-1 text-blue-500" />}
                        {observation.type === 'tool' && <Cpu className="h-4 w-4 mr-1 text-purple-500" />}
                        <span className="font-medium">{observation.name}</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {observation.type}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground mb-1">
                      {format(new Date(observation.startTime), 'HH:mm:ss')} · {observation.duration}
                    </div>
                    <div className="text-sm truncate">
                      {typeof observation.input === 'string' 
                        ? observation.input 
                        : JSON.stringify(observation.input)}
                    </div>
                    {observation.validationResults && observation.validationResults.some(r => !r.pass) && (
                      <div className="mt-1 flex items-center text-amber-600 text-xs">
                        <AlertTriangle className="h-3.5 w-3.5 mr-1" />
                        Validation failed
                      </div>
                    )}
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
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedObservationDetails?.name}</DialogTitle>
            <DialogDescription className="flex justify-between">
              <span>Type: {selectedObservationDetails?.type}</span>
              <span>Duration: {selectedObservationDetails?.duration}</span>
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Input</h4>
              <div className="rounded border p-3">
                <ScrollArea className="h-[200px]">
                  <pre className="text-xs whitespace-pre-wrap">
                    {selectedObservationDetails?.input 
                      ? typeof selectedObservationDetails.input === 'string'
                        ? selectedObservationDetails.input
                        : JSON.stringify(selectedObservationDetails.input, null, 2)
                      : 'No input available'}
                  </pre>
                </ScrollArea>
              </div>
            </div>
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Output</h4>
              <div className="rounded border p-3">
                <ScrollArea className="h-[200px]">
                  <pre className="text-xs whitespace-pre-wrap">
                    {selectedObservationDetails?.output 
                      ? typeof selectedObservationDetails.output === 'string'
                        ? selectedObservationDetails.output
                        : JSON.stringify(selectedObservationDetails.output, null, 2)
                      : 'No output available'}
                  </pre>
                </ScrollArea>
              </div>
            </div>
            {selectedObservationDetails?.validationResults && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Validation Results</h4>
                <div className="rounded border p-3">
                  <div className="space-y-2">
                    {selectedObservationDetails.validationResults.map((result, index) => (
                      <div key={index} className="flex items-start gap-2">
                        {result.pass ? (
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-500 mt-0.5" />
                        )}
                        <div className="text-sm">
                          {result.details}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            {selectedObservationDetails?.metadata && Object.keys(selectedObservationDetails.metadata).length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Metadata</h4>
                <div className="rounded border p-3">
                  <pre className="text-xs whitespace-pre-wrap">
                    {JSON.stringify(selectedObservationDetails.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
} 