"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { LayoutDashboard, LogOut, Settings, Activity, Shield } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { OrganizationSwitcher } from "@/components/organization-switcher";
import { ProjectSwitcher } from "@/components/project-switcher";
import { CreateProjectModal } from "@/components/create-project-modal";

export function Sidebar() {
  const pathname = usePathname();
  const { logout, currentProject, setCurrentProject } = useAuth();
  const [isCreateProjectModalOpen, setIsCreateProjectModalOpen] = useState(false);
  const [projectRefreshTrigger, setProjectRefreshTrigger] = useState(0);

  const handleLogout = () => {
    logout();
  };

  const handleCreateProject = () => {
    setIsCreateProjectModalOpen(true);
  };

  const handleProjectCreated = (project: any) => {
    // Trigger project list refresh
    setProjectRefreshTrigger(prev => prev + 1);
    console.log('Project created successfully:', project);
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 h-full flex flex-col flex-shrink-0">
      {/* Logo/Brand */}
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">datagusto</h1>
      </div>

      {/* Organization Switcher */}
      <div className="p-4 border-b border-gray-200">
        <OrganizationSwitcher />
      </div>

      {/* Project Switcher */}
      <div className="p-4 border-b border-gray-200">
        <ProjectSwitcher 
          currentProject={currentProject}
          onProjectChange={setCurrentProject}
          onCreateProject={handleCreateProject}
          refreshTrigger={projectRefreshTrigger}
        />
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          <Link
            href="/home"
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              pathname === "/home"
                ? "bg-gray-100 text-gray-900"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            <LayoutDashboard className="h-4 w-4" />
            Home
          </Link>
          
          {currentProject && (
            <>
              <Link
                href={`/projects/${currentProject.project.id}/traces`}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname === `/projects/${currentProject.project.id}/traces`
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                }`}
              >
                <Activity className="h-4 w-4" />
                Traces
              </Link>
              
              <Link
                href={`/projects/${currentProject.project.id}/guardrails`}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname === `/projects/${currentProject.project.id}/guardrails`
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                }`}
              >
                <Shield className="h-4 w-4" />
                Guardrails
              </Link>
              
              <Link
                href={`/projects/${currentProject.project.id}`}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname === `/projects/${currentProject.project.id}`
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                }`}
              >
                <Settings className="h-4 w-4" />
                Project Settings
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Logout Button */}
      <div className="p-4 border-t border-gray-200">
        <Button
          onClick={handleLogout}
          variant="ghost"
          className="w-full justify-start text-gray-600 hover:text-gray-900 hover:bg-gray-50"
        >
          <LogOut className="h-4 w-4 mr-3" />
          Sign Out
        </Button>
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