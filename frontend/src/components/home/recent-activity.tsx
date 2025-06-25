"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity } from "lucide-react";
import { TraceService } from "@/services";
import Link from "next/link";
import { useProjectStats } from "@/hooks/use-traces";

interface RecentActivityProps {
  currentProjectId: string;
}

export function RecentActivity({ currentProjectId }: RecentActivityProps) {
  const { recentTraces, isLoading } = useProjectStats(currentProjectId);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Latest traces and incidents from your AI agent</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">
            Loading recent activity...
          </div>
        ) : recentTraces && recentTraces.length > 0 ? (
          <div className="space-y-3">
            {recentTraces.map((trace) => {
              const traceName = TraceService.getTraceName(trace);
              const status = TraceService.getTraceStatus(trace);
              const timestamp = new Date(trace.timestamp).toLocaleString();
              
              return (
                <Link
                  key={trace.id}
                  href={`/projects/${currentProjectId}/traces/${trace.id}`}
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
              href={`/projects/${currentProjectId}/traces`}
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
  );
}