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
  Loader2,
  AlertCircle,
  CheckCircle
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
import { format, isValid } from "date-fns";

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
  const [recentTraces, setRecentTraces] = useState<Trace[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    refreshData();
  }, [agentId]);

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      if (!isValid(date)) {
        return "Invalid date";
      }
      return format(date, 'yyyy-MM-dd HH:mm:ss');
    } catch (error) {
      console.error("Date formatting error:", error);
      return "Invalid date";
    }
  };

  const refreshData = async () => {
    setIsLoading(true);

    try {
      // Fetch agent data
      const agentData = await agentService.getAgent(agentId);
      setAgent(agentData);

      // Use traceService to get agent traces
      const tracesData = await traceService.getAgentTraces(agentId);
      setRecentTraces(tracesData);

      toast.success("Agent data loaded successfully");
    } catch (error) {
      toast.error("Failed to load agent data");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to sync agent data with backend
  const syncAgentData = async () => {
    setIsLoading(true);

    try {
      // Call backend sync endpoint
      await agentService.syncAgent(agentId);

      // Refresh data to show updated traces
      await refreshData();

      toast.success("Agent traces synced successfully");
    } catch (error) {
      toast.error("Failed to sync agent traces");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to extract user query from input
  const extractUserQuery = (trace: Trace): string => {
    if (!trace.input) return "No input";

    try {
      const inputObj = JSON.parse(trace.input);
      // Check if input contains messages
      if (inputObj && inputObj.messages && Array.isArray(inputObj.messages)) {
        // Find the latest human/user message
        const humanMessages = inputObj.messages.filter((msg: any) =>
          msg.type === 'human' || msg.role === 'user'
        );

        if (humanMessages.length > 0 && typeof humanMessages[humanMessages.length - 1].content === 'string') {
          // Return the content of the most recent human message
          return humanMessages[humanMessages.length - 1].content;
        }
      }
    } catch (e) {
      // If we can't parse JSON, just return the raw input (truncated)
      if (typeof trace.input === 'string' && trace.input.length > 50) {
        return trace.input.substring(0, 50) + '...';
      }
      return trace.input;
    }

    return trace.name || "No query";
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

      <Tabs defaultValue="traces" className="space-y-4">
        <TabsList className="grid grid-cols-1 lg:grid-cols-1">
          <TabsTrigger value="traces">Traces</TabsTrigger>
        </TabsList>
        <TabsContent value="traces" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Recent Trace Logs</CardTitle>
                <CardDescription>
                  View detailed trace logs for this agent
                </CardDescription>
              </div>
              <Button variant="outline" onClick={syncAgentData} size="sm">
                <Server className="mr-2 h-4 w-4" />
                Sync data
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead className="text-center">Status</TableHead>
                    <TableHead className="hidden md:table-cell">Start Time</TableHead>
                    <TableHead className="hidden md:table-cell">Duration</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentTraces.length > 0 ? (
                    recentTraces.map((trace) => (
                      <TableRow key={trace.id}>
                        <TableCell className="font-medium">
                          <Link href={`/traces/${trace.id}`} className="hover:underline">
                            #{trace.id.substring(0, 8)}
                          </Link>
                        </TableCell>
                        <TableCell className="font-medium max-w-[200px] truncate" title={extractUserQuery(trace)}>
                          <div className="flex flex-col">
                            <Link href={`/traces/${trace.id}`} className="hover:underline">
                              {trace.name || "Unnamed trace"}
                            </Link>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">
                          {(trace.evaluation_results?.root_cause?.number_of_issues ?? 0) > 0 ? (
                            <div className="inline-flex items-center text-red-600 text-xs font-medium">
                              <AlertCircle className="mr-1 h-3 w-3" />
                              INCIDENT
                            </div>
                          ) : (
                            <div className="inline-flex items-center text-green-600 text-xs font-medium">
                              <CheckCircle className="mr-1 h-3 w-3" />
                              COMPLETED
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="hidden md:table-cell text-sm">
                          <div className="flex flex-col">
                            <span>{new Date(trace.timestamp || trace.created_at).toLocaleDateString()}</span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(trace.timestamp || trace.created_at).toLocaleTimeString()}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          {trace.latency ? `${trace.latency}s` : 'N/A'}
                        </TableCell>
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