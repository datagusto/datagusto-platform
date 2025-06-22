"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, AlertTriangle, Shield } from "lucide-react";
import { useProjectStats } from "@/hooks/use-traces";

interface StatsDisplayProps {
  currentProjectId: string;
}

export function StatsDisplay({ currentProjectId }: StatsDisplayProps) {
  const { stats, isLoading } = useProjectStats(currentProjectId);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Traces</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{isLoading ? "..." : stats?.totalTraces || 0}</div>
          <p className="text-xs text-muted-foreground">
            {!stats?.totalTraces ? "No recent traces" : `${stats.totalTraces} trace${stats.totalTraces !== 1 ? 's' : ''} found`}
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Incidents</CardTitle>
          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{isLoading ? "..." : stats?.activeIncidents || 0}</div>
          <p className="text-xs text-muted-foreground">
            {!stats?.activeIncidents ? "No active incidents" : `${stats.activeIncidents} incident${stats.activeIncidents !== 1 ? 's' : ''} detected`}
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Guardrails</CardTitle>
          <Shield className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{isLoading ? "..." : stats?.guardrails || 0}</div>
          <p className="text-xs text-muted-foreground">
            No guardrails configured
          </p>
        </CardContent>
      </Card>
    </div>
  );
}