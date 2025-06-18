"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Settings, Plus, Activity, AlertTriangle, Shield, FolderOpen } from "lucide-react";
import { TraceService, projectService } from "@/services";
import { Trace, UserProjectInfo } from "@/types";
import { CreateProjectModal } from "@/components/create-project-modal";

export default function Home() {
  const { currentProject, currentOrganization, setCurrentProject } = useAuth();
  const [traces, setTraces] = useState<Trace[]>([]);
  const [loading, setLoading] = useState(false);
  const [isCreateProjectModalOpen, setIsCreateProjectModalOpen] = useState(false);
  const [projects, setProjects] = useState<UserProjectInfo[]>([]);
  const [stats, setStats] = useState({
    totalTraces: 0,
    activeIncidents: 0,
    guardrails: 0,
    recentTraces: [] as Trace[]
  });

  const handleCreateProject = () => {
    console.log('Create project button clicked');
    setIsCreateProjectModalOpen(true);
  };

  const handleProjectCreated = async (project: any) => {
    // Close modal and set the newly created project as current
    setIsCreateProjectModalOpen(false);
    if (project && setCurrentProject) {
      setCurrentProject({ project, is_owner: true });
    }
    // Refresh project list
    await fetchProjects();
  };

  const fetchProjects = async () => {
    if (!currentOrganization) return;
    
    try {
      const userProjects = await projectService.getUserProjects();
      const orgProjects = userProjects.filter(p => 
        p.project.organization_id === currentOrganization.id
      );
      setProjects(orgProjects);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    }
  };

  useEffect(() => {
    const fetchStats = async () => {
      if (!currentProject?.project?.id) return;
      
      try {
        setLoading(true);
        
        // First, get all traces to count the total (without limit)
        const allTracesResponse = await TraceService.getTracesByProject(currentProject.project.id, { limit: 1000 });
        const allTraces = allTracesResponse.traces;
        
        // Get recent traces for display (limit 10)
        const recentTracesResponse = await TraceService.getTracesByProject(currentProject.project.id, { limit: 10 });
        const recentTraces = recentTracesResponse.traces;
        
        // Calculate stats from all traces
        const totalTraces = allTraces.length;
        const activeIncidents = allTraces.filter((trace: Trace) => {
          const status = TraceService.getTraceStatus(trace).toLowerCase();
          return status.includes('error') || status.includes('incident') || status.includes('failed');
        }).length;
        
        setStats({
          totalTraces,
          activeIncidents,
          guardrails: 0, // TODO: Implement when guardrails API is available
          recentTraces: recentTraces.slice(0, 5) // Show 5 most recent
        });
        
        setTraces(recentTraces);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [currentProject?.project?.id]);

  useEffect(() => {
    fetchProjects();
  }, [currentOrganization]);

  if (!currentOrganization) {
    return (
      <div className="flex-1 p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Please select an organization</div>
        </div>
      </div>
    );
  }

  if (!currentProject) {
    return (
      <div className="flex-1 p-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Welcome to {currentOrganization.name}</h1>
          <p className="text-gray-600 mt-2">
            {projects.length > 0 
              ? "Select a project or create a new one" 
              : "Get started by creating your first project"}
          </p>
        </div>
        
        {/* Project List and Create Card */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Existing Projects */}
          {projects.map((projectInfo) => (
            <Card 
              key={projectInfo.project.id}
              className="max-w-md cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => setCurrentProject(projectInfo)}
            >
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FolderOpen className="h-5 w-5" />
                    {projectInfo.project.name}
                  </CardTitle>
                  <CardDescription>
                    {projectInfo.project.description || "AI agent data quality monitoring"}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-gray-600 mb-4">
                    <div className="flex items-center justify-between">
                      <span>Platform:</span>
                      <span className="font-medium capitalize">{projectInfo.project.platform_type}</span>
                    </div>
                  </div>
                  <Button className="w-full" variant="outline">
                    <Activity className="h-4 w-4 mr-2" />
                    View Project
                  </Button>
                </CardContent>
              </Card>
          ))}
          
          {/* Create Project Card */}
          <Card className="max-w-md cursor-pointer hover:shadow-lg transition-shadow" onClick={handleCreateProject}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              {projects.length > 0 ? "Create New Project" : "Create Your First Project"}
            </CardTitle>
            <CardDescription>
              Set up a new AI agent project with data quality monitoring
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4">
              Projects help you organize and monitor your AI agents, track data quality, and manage incidents.
            </p>
            <div className="w-full py-2 text-center text-blue-600 font-medium">
              Click to create →
            </div>
          </CardContent>
        </Card>
        </div>
        
        {/* Create Project Modal */}
        <CreateProjectModal
          open={isCreateProjectModalOpen}
          onOpenChange={setIsCreateProjectModalOpen}
          onProjectCreated={handleProjectCreated}
        />
      </div>
    );
  }

  return (
    <div className="flex-1 p-8 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{currentProject.project.name}</h1>
          <p className="text-gray-600 mt-2">
            {currentProject.project.description || "AI agent data quality monitoring"}
          </p>
        </div>
        <Link href={`/projects/${currentProject.project.id}`}>
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Project Settings
          </Button>
        </Link>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Traces</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loading ? "..." : stats.totalTraces}</div>
            <p className="text-xs text-muted-foreground">
              {stats.totalTraces === 0 ? "No recent traces" : `${stats.totalTraces} trace${stats.totalTraces !== 1 ? 's' : ''} found`}
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Incidents</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loading ? "..." : stats.activeIncidents}</div>
            <p className="text-xs text-muted-foreground">
              {stats.activeIncidents === 0 ? "No active incidents" : `${stats.activeIncidents} incident${stats.activeIncidents !== 1 ? 's' : ''} detected`}
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Guardrails</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loading ? "..." : stats.guardrails}</div>
            <p className="text-xs text-muted-foreground">
              No guardrails configured
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Platform Info */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Integration</CardTitle>
          <CardDescription>Connected observation platform details</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">{currentProject.project.platform_type}</div>
              <div className="text-sm text-gray-500">
                {currentProject.project.platform_type === 'langfuse' && 
                  `URL: ${currentProject.project.platform_config?.url || 'Not configured'}`
                }
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-green-600">Connected</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest traces and incidents from your AI agent</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-gray-500">
              Loading recent activity...
            </div>
          ) : stats.recentTraces.length > 0 ? (
            <div className="space-y-3">
              {stats.recentTraces.map((trace) => {
                const traceName = TraceService.getTraceName(trace);
                const status = TraceService.getTraceStatus(trace);
                const timestamp = new Date(trace.timestamp).toLocaleString();
                
                return (
                  <Link
                    key={trace.id}
                    href={`/projects/${currentProject?.project.id}/traces/${trace.id}`}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <Activity className="h-4 w-4 text-gray-400" />
                      <div>
                        <div className="font-medium text-sm">{traceName}</div>
                        <div className="text-xs text-gray-500">#{trace.external_id?.slice(0, 8) || trace.id.slice(0, 8)}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-medium">{status}</div>
                      <div className="text-xs text-gray-500">{timestamp}</div>
                    </div>
                  </Link>
                );
              })}
              <Link 
                href={`/projects/${currentProject?.project.id}/traces`}
                className="block text-center text-sm text-blue-600 hover:text-blue-700 pt-3"
              >
                View all traces →
              </Link>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No recent activity to display
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Create Project Modal */}
      <CreateProjectModal
        open={isCreateProjectModalOpen}
        onOpenChange={setIsCreateProjectModalOpen}
        onProjectCreated={handleProjectCreated}
      />
    </div>
  );
}