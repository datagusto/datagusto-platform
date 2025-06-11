"use client";

import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { projectService, TraceService } from "@/services";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Eye, EyeOff, Copy, RefreshCw, BarChart3 } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import type { UserProjectInfo } from "@/types";

export default function ProjectDetailPage() {
  const params = useParams();
  const { currentOrganization } = useAuth();
  const [project, setProject] = useState<UserProjectInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSecretKey, setShowSecretKey] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [traceCount, setTraceCount] = useState<number>(0);

  useEffect(() => {
    const loadProject = async () => {
      if (!currentOrganization || !params.id) return;
      
      setLoading(true);
      try {
        const userProjects = await projectService.getUserProjects();
        const projectInfo = userProjects.find(p => 
          p.project.id === params.id && 
          p.project.organization_id === currentOrganization.id
        );
        
        if (projectInfo) {
          setProject(projectInfo);
          // Load trace count
          try {
            const tracesResponse = await TraceService.getTracesByProject(projectInfo.project.id, { limit: 1, offset: 0 });
            setTraceCount(tracesResponse.total);
          } catch (error) {
            console.error('Failed to load trace count:', error);
          }
        }
      } catch (error) {
        console.error('Failed to load project:', error);
      } finally {
        setLoading(false);
      }
    };

    loadProject();
  }, [currentOrganization, params.id]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const regenerateApiKey = async () => {
    if (!project) return;
    
    try {
      // TODO: Implement API key regeneration
      console.log('Regenerate API key for project:', project.project.id);
    } catch (error) {
      console.error('Failed to regenerate API key:', error);
    }
  };

  const handleSync = async () => {
    if (!project) return;
    
    setSyncing(true);
    try {
      const result = await projectService.syncLangfuseData(project.project.id);
      setLastSync(new Date().toISOString());
      toast.success(
        `Sync completed! ${result.total_traces} traces processed (${result.new_traces} new, ${result.updated_traces} updated).`
      );
    } catch (error) {
      console.error('Sync failed:', error);
      toast.error(error instanceof Error ? error.message : 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading project details...</div>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex-1 p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Project not found</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">{project.project.name}</h1>
        <p className="text-gray-600 mt-2">{project.project.description || "No description"}</p>
      </div>

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Project Information</CardTitle>
          <CardDescription>Basic details about your project</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="project-name">Project Name</Label>
              <Input
                id="project-name"
                value={project.project.name}
                readOnly
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="platform-type">Platform Type</Label>
              <Input
                id="platform-type"
                value={project.project.platform_type}
                readOnly
                className="mt-1"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={project.project.description || ""}
              readOnly
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="role">Your Role</Label>
            <Input
              id="role"
              value={project.membership.role}
              readOnly
              className="mt-1"
            />
          </div>
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <CardTitle>API Configuration</CardTitle>
          <CardDescription>API keys and configuration for SDK integration</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Project API Key */}
          <div>
            <Label htmlFor="api-key">Project API Key</Label>
            <div className="flex gap-2 mt-1">
              <Input
                id="api-key"
                type={showApiKey ? "text" : "password"}
                value={project.project.api_key}
                readOnly
                className="flex-1"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => copyToClipboard(project.project.api_key)}
              >
                <Copy className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={regenerateApiKey}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Platform Configuration */}
          {project.project.platform_type === 'langfuse' && (
            <>
              <div>
                <Label htmlFor="public-key">Langfuse Public Key</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    id="public-key"
                    value={project.project.platform_config?.public_key || ""}
                    readOnly
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => copyToClipboard(project.project.platform_config?.public_key || "")}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div>
                <Label htmlFor="secret-key">Langfuse Secret Key</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    id="secret-key"
                    type={showSecretKey ? "text" : "password"}
                    value={project.project.platform_config?.secret_key || ""}
                    readOnly
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setShowSecretKey(!showSecretKey)}
                  >
                    {showSecretKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => copyToClipboard(project.project.platform_config?.secret_key || "")}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div>
                <Label htmlFor="langfuse-url">Langfuse URL</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    id="langfuse-url"
                    value={project.project.platform_config?.url || ""}
                    readOnly
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => copyToClipboard(project.project.platform_config?.url || "")}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              {/* Sync Section */}
              <div>
                <Label htmlFor="sync-data">Data Synchronization</Label>
                <div className="flex gap-2 mt-1">
                  <Button
                    variant="outline"
                    onClick={handleSync}
                    disabled={syncing}
                    className="flex-1"
                  >
                    {syncing ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Syncing Langfuse Data...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Sync Langfuse Data
                      </>
                    )}
                  </Button>
                </div>
                {lastSync && (
                  <p className="text-xs text-gray-500 mt-1">
                    Last synced: {new Date(lastSync).toLocaleString()}
                  </p>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Project Statistics */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Project Statistics</CardTitle>
              <CardDescription>Overview of project activity and metrics</CardDescription>
            </div>
            <Link href={`/projects/${project.project.id}/traces`}>
              <Button variant="outline" size="sm">
                <BarChart3 className="h-4 w-4 mr-2" />
                View Traces
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900">{traceCount}</div>
              <div className="text-sm text-gray-500">Total Traces</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">0</div>
              <div className="text-sm text-gray-500">Active Incidents</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">0</div>
              <div className="text-sm text-gray-500">Guardrails</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}