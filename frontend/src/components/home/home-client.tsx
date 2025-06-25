"use client";

import { useAuth } from "@/lib/auth-context";
import { ProjectCard } from "./project-card";
import { ProjectActions } from "./project-actions";
import { StatsDisplay } from "./stats-display";
import { RecentActivity } from "./recent-activity";
import { UserProjectInfo } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useUserProjects, useCreateProject } from "@/hooks/use-projects";

interface HomeClientProps {
  serverProjects: UserProjectInfo[];
}

export function HomeClient({ serverProjects }: HomeClientProps) {
  const { currentProject, currentOrganization, setCurrentProject } = useAuth();
  
  // Use React Query for projects data
  const { data: projects = serverProjects, isLoading: isLoadingProjects } = useUserProjects();
  const createProjectMutation = useCreateProject();

  const handleProjectCreated = (project: any) => {
    if (project && setCurrentProject) {
      setCurrentProject({ 
        project, 
        membership: { 
          id: '', 
          user_id: '', 
          project_id: project.id, 
          role: 'owner', 
          joined_at: new Date().toISOString(), 
          created_at: new Date().toISOString(), 
          updated_at: new Date().toISOString() 
        },
        is_owner: true 
      });
    }
    // React Query automatically handles cache invalidation
  };

  const handleProjectSelect = (projectInfo: UserProjectInfo) => {
    setCurrentProject(projectInfo);
  };

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
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {isLoadingProjects ? (
            <div className="col-span-2 text-center py-8 text-gray-500">
              Loading projects...
            </div>
          ) : (
            <>
              {projects
                .filter(p => p.project.organization_id === currentOrganization.id)
                .map((projectInfo) => (
                  <ProjectCard
                    key={projectInfo.project.id}
                    projectInfo={projectInfo}
                    onSelect={handleProjectSelect}
                  />
                ))}
              
              <ProjectActions 
                projects={projects}
                onProjectCreated={handleProjectCreated}
              />
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-8 space-y-6">
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

      <StatsDisplay currentProjectId={currentProject.project.id} />

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

      <RecentActivity currentProjectId={currentProject.project.id} />
    </div>
  );
}