"use client";

import { useState, useEffect } from "react";
import { ChevronDown, Check, FolderOpen, Plus, LayoutGrid } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { projectService } from "@/services";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import type { UserProjectInfo } from "@/types";

interface ProjectSwitcherProps {
  currentProject: UserProjectInfo | null;
  onProjectChange: (project: UserProjectInfo) => void;
  onCreateProject: () => void;
  refreshTrigger?: number;
}

export function ProjectSwitcher({ 
  currentProject, 
  onProjectChange, 
  onCreateProject,
  refreshTrigger
}: ProjectSwitcherProps) {
  const { currentOrganization, setCurrentProject } = useAuth();
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [projects, setProjects] = useState<UserProjectInfo[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentOrganization) {
      loadProjects();
    }
  }, [currentOrganization, refreshTrigger]);

  const loadProjects = async () => {
    if (!currentOrganization) return;
    
    setLoading(true);
    try {
      const userProjects = await projectService.getUserProjects();
      // Filter projects for current organization
      const orgProjects = userProjects.filter(
        p => p.project.organization_id === currentOrganization.id
      );
      setProjects(orgProjects);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (project: UserProjectInfo) => {
    onProjectChange(project);
    setIsOpen(false);
  };

  if (!currentOrganization) {
    return null;
  }

  return (
    <div className="relative">
      <Button
        variant="ghost"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full justify-between px-3 py-2 h-auto text-left font-normal"
        disabled={loading}
      >
        <div className="flex items-center gap-2 min-w-0">
          <FolderOpen className="h-4 w-4 flex-shrink-0" />
          <div className="min-w-0">
            {currentProject ? (
              <div className="text-sm font-medium truncate">
                {currentProject.project.name}
              </div>
            ) : (
              <div className="text-sm text-gray-500">
                {loading ? "Loading..." : "Select project"}
              </div>
            )}
          </div>
        </div>
        <ChevronDown className="h-4 w-4 flex-shrink-0" />
      </Button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-20 max-h-64 overflow-y-auto">
            {/* Create new project option */}
            <button
              onClick={() => {
                onCreateProject();
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-md flex-shrink-0">
                <Plus className="h-4 w-4 text-blue-600" />
              </div>
              
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-blue-600">
                  Create new project
                </div>
                <div className="text-xs text-gray-500">
                  Set up a new AI agent project
                </div>
              </div>
            </button>

            {/* View all projects option */}
            <button
              onClick={() => {
                setCurrentProject(null);
                router.push('/home');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-gray-50 transition-colors border-b border-gray-100"
            >
              <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-md flex-shrink-0">
                <LayoutGrid className="h-4 w-4 text-gray-600" />
              </div>
              
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-gray-700">
                  View all projects
                </div>
                <div className="text-xs text-gray-500">
                  Browse and manage projects
                </div>
              </div>
            </button>

            {/* Project list */}
            {projects.map((projectInfo) => (
              <button
                key={projectInfo.project.id}
                onClick={() => handleSelect(projectInfo)}
                className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-md flex-shrink-0">
                  <FolderOpen className="h-4 w-4 text-gray-600" />
                </div>
                
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium truncate">
                    {projectInfo.project.name}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    {projectInfo.project.platform_type}
                  </div>
                </div>
                
                {currentProject?.project.id === projectInfo.project.id && (
                  <Check className="h-4 w-4 text-blue-600 flex-shrink-0" />
                )}
              </button>
            ))}

            {projects.length === 0 && !loading && (
              <div className="px-3 py-4 text-center text-gray-500 text-sm">
                No projects in this organization
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}