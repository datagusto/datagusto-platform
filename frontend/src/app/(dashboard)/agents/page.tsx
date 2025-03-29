"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Bot, 
  Plus, 
  Search,
  MoreHorizontal,
  ChevronRight,
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
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { agentService } from "@/services";
import type { Agent } from "@/types/agent";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAgents() {
      try {
        const data = await agentService.getAgents();
        setAgents(data);
        setFilteredAgents(data);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Failed to fetch agents";
        toast.error(errorMessage);
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    }

    fetchAgents();
  }, []);

  useEffect(() => {
    if (searchQuery) {
      const filtered = agents.filter(agent => 
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (agent.description && agent.description.toLowerCase().includes(searchQuery.toLowerCase()))
      );
      setFilteredAgents(filtered);
    } else {
      setFilteredAgents(agents);
    }
  }, [searchQuery, agents]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Agents</h1>
          <p className="text-muted-foreground">
            Manage and monitor your AI agents
          </p>
        </div>
        <Button asChild>
          <Link href="/agents/new">
            <Plus className="mr-2 h-4 w-4" />
            Add New Agent
          </Link>
        </Button>
      </div>

      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle>Get Started</CardTitle>
          <CardDescription>Creating and managing your AI agents is easy</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border rounded-md bg-slate-50 space-y-2">
              <div className="rounded-full bg-primary/10 w-8 h-8 flex items-center justify-center mb-2">
                <span className="font-bold text-primary">1</span>
              </div>
              <h3 className="font-medium">Create an Agent</h3>
              <p className="text-sm text-muted-foreground">Define your agent type and settings</p>
            </div>
            <div className="p-4 border rounded-md bg-slate-50 space-y-2">
              <div className="rounded-full bg-primary/10 w-8 h-8 flex items-center justify-center mb-2">
                <span className="font-bold text-primary">2</span>
              </div>
              <h3 className="font-medium">Configure & Deploy</h3>
              <p className="text-sm text-muted-foreground">Set up behavior and make it online</p>
            </div>
            <div className="p-4 border rounded-md bg-slate-50 space-y-2">
              <div className="rounded-full bg-primary/10 w-8 h-8 flex items-center justify-center mb-2">
                <span className="font-bold text-primary">3</span>
              </div>
              <h3 className="font-medium">Monitor & Improve</h3>
              <p className="text-sm text-muted-foreground">Track logs and optimize performance</p>
            </div>
          </div>
          <div className="mt-4">
            <Button variant="outline" asChild className="w-full mt-2 md:w-auto">
              <Link href="/agents/new" className="flex items-center">
                Start creating a new agent
                <ChevronRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {error ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-10">
            <div className="rounded-full bg-red-100 p-3 mb-4">
              <Bot className="h-8 w-8 text-red-600" />
            </div>
            <h3 className="text-xl font-medium mb-2">Unable to load agents</h3>
            <p className="text-muted-foreground text-center mb-4">{error}</p>
            <Button onClick={() => window.location.reload()}>
              Retry
            </Button>
          </CardContent>
        </Card>
      ) : agents.length > 0 ? (
        <>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search agents..."
                className="pl-8"
                value={searchQuery}
                onChange={handleSearch}
              />
            </div>
            <Button variant="outline">
              Filter
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Your AI Agents</CardTitle>
              <CardDescription>
                You have {agents.length} AI agent{agents.length !== 1 ? 's' : ''} registered
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created At</TableHead>
                    <TableHead>Updated At</TableHead>
                    <TableHead className="w-[80px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAgents.length > 0 ? (
                    filteredAgents.map((agent) => (
                      <TableRow key={agent.id}>
                        <TableCell className="font-medium">
                          <Link href={`/agents/${agent.id}`} className="hover:underline">
                            {agent.name}
                          </Link>
                        </TableCell>
                        <TableCell>{agent.description || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={agent.status.toLowerCase() === "active" ? "default" : "secondary"}>
                            {agent.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{new Date(agent.created_at).toLocaleDateString()}</TableCell>
                        <TableCell>{new Date(agent.updated_at).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <span className="sr-only">Open menu</span>
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem asChild>
                                <Link href={`/agents/${agent.id}`}>View details</Link>
                              </DropdownMenuItem>
                              <DropdownMenuItem asChild>
                                <Link href={`/agents/${agent.id}/edit`}>Edit</Link>
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="h-24 text-center">
                        No agents found matching your search
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
              <Bot className="h-8 w-8 text-slate-400" />
            </div>
            <h3 className="text-xl font-medium mb-2">No Agents Found</h3>
            <p className="text-muted-foreground text-center mb-4">
              You don't have any agents yet. Get started by creating your first agent.
            </p>
            <Button asChild>
              <Link href="/agents/new">
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Agent
              </Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 