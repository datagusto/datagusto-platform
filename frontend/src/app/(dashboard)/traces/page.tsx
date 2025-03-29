"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, Search, Filter, Download, AlertCircle, CheckCircle, Calendar, ArrowUpDown, Bot, Loader2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { traceService } from "@/services";
import type { Trace } from "@/types";

export default function TracesPage() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [agentFilter, setAgentFilter] = useState<string>("all");
  const [filteredTraces, setFilteredTraces] = useState<Trace[]>([]);
  const [agents, setAgents] = useState<{id: string, name: string}[]>([]);

  useEffect(() => {
    async function fetchTraces() {
      try {
        setIsLoading(true);
        const data = await traceService.getTraces();
        if (Array.isArray(data)) {
          setTraces(data);
          setFilteredTraces(data);
          
          // Extract unique agents from traces
          const uniqueAgents = data.reduce((acc: {id: string, name: string}[], trace) => {
            if (!acc.some(a => a.id === trace.agent_id)) {
              // Using agent_id instead of agentId to match backend structure
              acc.push({ id: trace.agent_id, name: trace.agent_id });  // Using agent_id as name since agentName is not available
            }
            return acc;
          }, []);
          setAgents(uniqueAgents);
        } else {
          // Handle case where API doesn't return an array
          setTraces([]);
          setFilteredTraces([]);
          setAgents([]);
          console.error("API did not return an array:", data);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Failed to fetch traces";
        toast.error(errorMessage);
        setError(errorMessage);
        setTraces([]);
        setFilteredTraces([]);
        setAgents([]);
      } finally {
        setIsLoading(false);
      }
    }

    fetchTraces();
  }, []);

  useEffect(() => {
    if (!Array.isArray(traces)) {
      setFilteredTraces([]);
      return;
    }
    
    let result = [...traces];
    
    // Apply search filter - updated to use user_query instead of name/input
    if (searchQuery) {
      result = result.filter(
        trace => 
          (trace.user_query && trace.user_query.toLowerCase().includes(searchQuery.toLowerCase())) ||
          trace.agent_id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // Apply status filter
    if (statusFilter !== "all") {
      result = result.filter(
        trace => trace.status.toLowerCase() === statusFilter.toLowerCase()
      );
    }
    
    // Apply agent filter
    if (agentFilter !== "all") {
      result = result.filter(
        trace => trace.agent_id === agentFilter
      );
    }
    
    setFilteredTraces(result);
  }, [searchQuery, statusFilter, agentFilter, traces]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleStatusFilter = (value: string) => {
    setStatusFilter(value);
  };

  const handleAgentFilter = (value: string) => {
    setAgentFilter(value);
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  // Calculate metrics - ensure traces is an array before calculations
  const tracesArray = Array.isArray(traces) ? traces : [];
  const successRate = tracesArray.length > 0 
    ? Math.round((tracesArray.filter(t => t.status === "COMPLETED").length / tracesArray.length) * 100)
    : 0;
  
  const errorCount = tracesArray.filter(t => t.status === "ERROR").length;
  
  const avgDuration = tracesArray.length > 0
    ? tracesArray.reduce((sum, trace) => {
        // Using latency_ms instead of duration
        const duration = typeof trace.latency_ms === 'number' 
          ? trace.latency_ms / 1000 // Convert ms to seconds 
          : 0;
        return sum + duration;
      }, 0) / tracesArray.length
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Trace Logs</h1>
          <p className="text-muted-foreground">
            View and analyze agent trace logs
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline">
            <Calendar className="mr-2 h-4 w-4" />
            Date Range
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export Logs
          </Button>
        </div>
      </div>

      {error ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-10">
            <div className="rounded-full bg-red-100 p-3 mb-4">
              <AlertCircle className="h-8 w-8 text-red-600" />
            </div>
            <h3 className="text-xl font-medium mb-2">Unable to load traces</h3>
            <p className="text-muted-foreground text-center mb-4">{error}</p>
            <Button onClick={() => window.location.reload()}>
              Retry
            </Button>
          </CardContent>
        </Card>
      ) : tracesArray.length > 0 ? (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Traces</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{tracesArray.length}</div>
                <p className="text-xs text-muted-foreground">
                  Over the last 24 hours
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {successRate}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {errorCount} errors detected
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Average Duration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{avgDuration.toFixed(2)}s</div>
                <p className="text-xs text-muted-foreground">
                  Across all agents
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="flex flex-col gap-4 md:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search traces by name or agent..."
                className="pl-8"
                value={searchQuery}
                onChange={handleSearch}
              />
            </div>
            <Select value={statusFilter} onValueChange={handleStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="COMPLETED">Completed</SelectItem>
                <SelectItem value="ERROR">Error</SelectItem>
                <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
              </SelectContent>
            </Select>
            <Select value={agentFilter} onValueChange={handleAgentFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by agent" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All agents</SelectItem>
                {agents.map(agent => (
                  <SelectItem key={agent.id} value={agent.id}>
                    {agent.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Recent Trace Logs</CardTitle>
              <CardDescription>
                View detailed trace logs for all agents
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">ID</TableHead>
                    <TableHead>
                      <div className="flex items-center space-x-1">
                        <span>Query</span>
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </TableHead>
                    <TableHead>Agent ID</TableHead>
                    <TableHead className="text-center">Status</TableHead>
                    <TableHead className="hidden md:table-cell">Start Time</TableHead>
                    <TableHead className="hidden md:table-cell">Duration</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTraces.length > 0 ? (
                    filteredTraces.map((trace) => (
                      <TableRow key={trace.id}>
                        <TableCell className="font-medium">#{trace.id.substring(0, 8)}</TableCell>
                        <TableCell className="font-medium max-w-[200px] truncate" title={trace.user_query}>
                          <div className="flex flex-col">
                            <span>{trace.user_query || "No query"}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Link href={`/agents/${trace.agent_id}`} className="hover:underline text-sm">
                            {trace.agent_id}
                          </Link>
                        </TableCell>
                        <TableCell className="text-center">
                          {trace.status === "COMPLETED" ? (
                            <div className="inline-flex items-center text-green-600 text-xs font-medium">
                              <CheckCircle className="mr-1 h-3 w-3" />
                              {trace.status}
                            </div>
                          ) : trace.status === "ERROR" ? (
                            <div className="inline-flex items-center text-red-600 text-xs font-medium">
                              <AlertCircle className="mr-1 h-3 w-3" />
                              {trace.status}
                            </div>
                          ) : (
                            <div className="inline-flex items-center text-yellow-600 text-xs font-medium">
                              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                              {trace.status}
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="hidden md:table-cell text-sm">
                          <div className="flex flex-col">
                            <span>{new Date(trace.started_at).toLocaleDateString()}</span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(trace.started_at).toLocaleTimeString()}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          {trace.latency_ms ? `${(trace.latency_ms / 1000).toFixed(2)}s` : "In progress"}
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                Actions
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem asChild>
                                <Link href={`/traces/${trace.id}`}>View Details</Link>
                              </DropdownMenuItem>
                              <DropdownMenuItem>Export JSON</DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={7} className="h-24 text-center">
                        No traces found matching your search
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-10">
            <div className="rounded-full bg-slate-100 p-3 mb-4">
              <Activity className="h-8 w-8 text-slate-400" />
            </div>
            <h3 className="text-xl font-medium mb-2">No Traces Found</h3>
            <p className="text-muted-foreground text-center mb-4">
              There are no trace logs yet. Traces will appear here when agents process requests.
            </p>
            <Button asChild variant="outline">
              <Link href="/agents">
                <Bot className="mr-2 h-4 w-4" />
                View Agents
              </Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}