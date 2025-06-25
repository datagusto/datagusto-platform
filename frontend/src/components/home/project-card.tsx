"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FolderOpen, Activity } from "lucide-react";
import { UserProjectInfo } from "@/types";

interface ProjectCardProps {
  projectInfo: UserProjectInfo;
  onSelect: (projectInfo: UserProjectInfo) => void;
}

export function ProjectCard({ projectInfo, onSelect }: ProjectCardProps) {
  return (
    <Card 
      className="max-w-md cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => onSelect(projectInfo)}
      role="button"
      tabIndex={0}
      aria-label={`Select project ${projectInfo.project.name}`}
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
  );
}