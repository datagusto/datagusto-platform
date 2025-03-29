"use client";

import Link from "next/link";
import { 
  Bot, 
  Edit, 
  Trash2, 
  Activity, 
  Server, 
  Settings, 
  AlertTriangle,
  Loader2
} from "lucide-react";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { toast } from "sonner";
import { agentService } from "@/services";
import { traceService } from "@/services/trace-service";
import type { Agent } from "@/types/agent";
import type { Trace } from "@/types";
import { format } from "date-fns";

// Additional interface for displaying traces in UI
interface TraceDisplay {
  id: string;
  status: string;
  time: string;
  duration: string;
  tokens: number;
}

export default function AgentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;
  
  const [agent, setAgent] = useState<Agent | null>(null);
  const [recentTraces, setRecentTraces] = useState<TraceDisplay[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    refreshData();
  }, [agentId]);
  
  const refreshData = async () => {
    setIsLoading(true);
    
    try {
      // Fetch agent data
      const agentData = await agentService.getAgent(agentId);
      setAgent(agentData);

      // Use traceService to get agent traces
      const tracesData = await traceService.getAgentTraces(agentId);

      // Transform trace data for display
      const displayTraces = tracesData.map(trace => ({
        id: trace.id,
        status: trace.status,
        time: format(new Date(trace.started_at), 'yyyy-MM-dd HH:mm:ss'),
        duration: trace.latency_ms ? `${trace.latency_ms}ms` : 'N/A',
        tokens: trace.total_tokens || 0
      }));

      setRecentTraces(displayTraces);
      toast.success("Agent data loaded successfully");
    } catch (error) {
      toast.error("Failed to load agent data");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !agent) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  // Get API key from agent configuration if available
  const apiKey = (agent as any).api_key;
  
  // Create the code sample with the API key
  const codeSample = `import os
from datagusto import DatagustoTools, DatagustoCallbackHandler

from langchain_openai import ChatOpenAI

os.environ["DATAGUSTO_SECRET_KEY"] = "${apiKey}"

agent = ChatOpenAI(model="gpt-4o-mini", callbacks=[CallbackHandler()])
agent_with_tools = llm.bind_tools(tools=DatagustoTools())

agent_with_tools.invoke("Hello World!")`;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2">
          <Bot className="h-8 w-8" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{agent.name}</h1>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{agent.config?.model || "Custom"}</Badge>
              <Badge
                variant={agent.status === "ACTIVE" ? "default" : "secondary"}
                className={agent.status === "ACTIVE" ? "bg-green-500" : ""}
              >
                {agent.status}
              </Badge>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" asChild>
            <Link href={`/agents/${params.id}/edit`}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Link>
          </Button>
          <Button variant="destructive">
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      <p className="text-muted-foreground">{agent.description || "No description provided"}</p>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Total Logs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recentTraces.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Average Response</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">N/A</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">N/A</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">N/A</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid grid-cols-2 lg:grid-cols-2">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="traces">Traces</TabsTrigger>
        </TabsList>
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Integration Guide</CardTitle>
              <CardDescription>
                Connect your AI agent to the DataGusto platform
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="bg-muted rounded-md p-4">
                  <h3 className="text-sm font-medium mb-2">API Key</h3>
                  <div className="flex">
                    <code className="text-sm font-mono">{apiKey}</code>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Use this API key to authenticate your agent with the DataGusto platform.</p>
                </div>

                <div className="bg-muted rounded-md p-4">
                  <h3 className="text-sm font-medium mb-2">Integration Code</h3>
                  <pre className="text-sm p-2 bg-background rounded-md">
                    <code>{codeSample}</code>
                  </pre>
                  <p className="text-xs text-muted-foreground mt-1">Use this code to integrate your agent with the DataGusto platform.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="traces" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Trace Logs</CardTitle>
              <CardDescription>
                View detailed trace logs for this agent
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Tokens</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentTraces.length > 0 ? (
                    recentTraces.map((trace) => (
                      <TableRow key={trace.id}>
                        <TableCell className="font-medium">#{trace.id}</TableCell>
                        <TableCell>
                          <Badge
                            variant={trace.status === "ERROR" ? "destructive" : "default"}
                            className={trace.status === "COMPLETED" ? "bg-green-500" : ""}
                          >
                            {trace.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{trace.time}</TableCell>
                        <TableCell>{trace.duration}</TableCell>
                        <TableCell>{trace.tokens}</TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/traces/${trace.id}`}>View</Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-4">
                        No traces found for this agent
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}