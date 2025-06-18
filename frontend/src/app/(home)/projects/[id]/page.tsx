"use client";

import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { projectService, TraceService } from "@/services";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Eye, EyeOff, Copy, RefreshCw } from "lucide-react";
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
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [loadingApiKey, setLoadingApiKey] = useState(false);

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

  const loadApiKey = async () => {
    if (!project || loadingApiKey) return;
    
    setLoadingApiKey(true);
    try {
      const response = await projectService.getProjectApiKey(project.project.id);
      setApiKey(response.api_key);
    } catch (error) {
      console.error('Failed to load API key:', error);
      toast.error('Failed to load API key');
    } finally {
      setLoadingApiKey(false);
    }
  };


  const clearApiKey = () => {
    setApiKey(null);
    setShowApiKey(false);
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

      {/* Project Information */}
      <Card>
        <CardHeader>
          <CardTitle>Project Information</CardTitle>
          <CardDescription>Basic details about your project and API key</CardDescription>
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
          
          {/* API Key Display */}
          <div>
            <Label htmlFor="api-key">Project API Key</Label>
            <div className="flex gap-2 mt-1">
              <Input
                id="api-key"
                type="text"
                value={
                  loadingApiKey 
                    ? 'Loading API key...' 
                    : !apiKey 
                      ? 'Click to load API key' 
                      : showApiKey 
                        ? apiKey 
                        : `${apiKey.substring(0, 8)}${'*'.repeat(Math.max(0, apiKey.length - 8))}`
                }
                readOnly
                className="flex-1 font-mono"
                placeholder={!apiKey && !loadingApiKey ? "Click load button to view API key" : ""}
                onClick={!apiKey && !loadingApiKey ? loadApiKey : undefined}
                style={!apiKey && !loadingApiKey ? { cursor: 'pointer' } : {}}
              />
              {!apiKey ? (
                <Button
                  variant="outline"
                  onClick={loadApiKey}
                  disabled={loadingApiKey}
                  title="Load API key"
                >
                  {loadingApiKey ? 'Loading...' : 'Load'}
                </Button>
              ) : (
                <>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setShowApiKey(!showApiKey)}
                    title={showApiKey ? "Hide API key" : "Show API key"}
                  >
                    {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => copyToClipboard(apiKey)}
                    title="Copy API key to clipboard"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Integration Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Integration Configuration</CardTitle>
          <CardDescription>Connected observability platform settings and configuration</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Platform Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="connected-platform">Connected Platform</Label>
              <Input
                id="connected-platform"
                value={project.project.platform_type.charAt(0).toUpperCase() + project.project.platform_type.slice(1)}
                readOnly
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="connection-status">Connection Status</Label>
              <Input
                id="connection-status"
                value="Connected"
                readOnly
                className="mt-1 text-green-600"
              />
            </div>
          </div>

          {/* Platform Configuration Details */}
          {project.project.platform_type === 'langfuse' && (
            <>
              <div>
                <Label htmlFor="public-key">Langfuse Public Key</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    id="public-key"
                    value={project.project.platform_config?.public_key || ""}
                    readOnly
                    className="flex-1 font-mono"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => copyToClipboard(project.project.platform_config?.public_key || "")}
                    title="Copy public key to clipboard"
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
                    className="flex-1 font-mono"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setShowSecretKey(!showSecretKey)}
                    title={showSecretKey ? "Hide secret key" : "Show secret key"}
                  >
                    {showSecretKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => copyToClipboard(project.project.platform_config?.secret_key || "")}
                    title="Copy secret key to clipboard"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div>
                <Label htmlFor="langfuse-url">Langfuse Server URL</Label>
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
                    title="Copy URL to clipboard"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              {/* Data Synchronization */}
              <div className="border-t pt-4">
                <div className="mb-2">
                  <h4 className="text-sm font-medium text-gray-900">Data Synchronization</h4>
                  <p className="text-sm text-gray-500">Manually sync trace data from your connected Langfuse instance</p>
                </div>
                <div className="flex gap-2">
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
                  <p className="text-xs text-gray-500 mt-2">
                    Last synced: {new Date(lastSync).toLocaleString()}
                  </p>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

    </div>
  );
}