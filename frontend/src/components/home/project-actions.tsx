"use client";

import { useState, lazy, Suspense } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus } from "lucide-react";
import { UserProjectInfo } from "@/types";

// Lazy load the modal to reduce initial bundle size
const CreateProjectModal = lazy(() => import("@/components/create-project-modal").then(module => ({
  default: module.CreateProjectModal
})));

interface ProjectActionsProps {
  projects: UserProjectInfo[];
  onProjectCreated: (project: any) => void;
}

export function ProjectActions({ projects, onProjectCreated }: ProjectActionsProps) {
  const [isCreateProjectModalOpen, setIsCreateProjectModalOpen] = useState(false);

  const handleCreateProject = () => {
    setIsCreateProjectModalOpen(true);
  };

  const handleProjectCreated = (project: any) => {
    setIsCreateProjectModalOpen(false);
    onProjectCreated(project);
  };

  return (
    <>
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

      {isCreateProjectModalOpen && (
        <Suspense fallback={<div className="fixed inset-0 bg-black/50 flex items-center justify-center">
          <div className="bg-background p-4 rounded-lg">Loading...</div>
        </div>}>
          <CreateProjectModal
            open={isCreateProjectModalOpen}
            onOpenChange={setIsCreateProjectModalOpen}
            onProjectCreated={handleProjectCreated}
          />
        </Suspense>
      )}
    </>
  );
}