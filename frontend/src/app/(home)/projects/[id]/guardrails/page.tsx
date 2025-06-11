"use client";

import { useState } from "react";
import { Settings, Plus, Edit, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface Guardrail {
  id: string;
  name: string;
  description: string;
  type: string;
  status: "Active" | "Inactive";
}

const mockGuardrails: Guardrail[] = [
  {
    id: "#grl-001",
    name: "Incomplete record filter",
    description: "Detects and discard incomplete records",
    type: "Content Filter",
    status: "Active"
  }
];

export default function GuardrailsPage() {
  const [guardrails] = useState<Guardrail[]>(mockGuardrails);

  return (
    <div className="flex-1 p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Configured Guardrails</h1>
          <p className="text-gray-600">
            Manage guardrails applied to this agent
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4" />
          </Button>
          <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-4 w-4 mr-2" />
            Add Guardrail
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-b">
                  <TableHead className="font-semibold text-gray-900">ID</TableHead>
                  <TableHead className="font-semibold text-gray-900">Name</TableHead>
                  <TableHead className="font-semibold text-gray-900">Description</TableHead>
                  <TableHead className="font-semibold text-gray-900">Type</TableHead>
                  <TableHead className="font-semibold text-gray-900">Status</TableHead>
                  <TableHead className="font-semibold text-gray-900">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {guardrails.map((guardrail) => (
                  <TableRow key={guardrail.id} className="hover:bg-gray-50 transition-colors">
                    <TableCell className="font-mono text-sm">{guardrail.id}</TableCell>
                    <TableCell className="font-medium">{guardrail.name}</TableCell>
                    <TableCell className="text-gray-600">{guardrail.description}</TableCell>
                    <TableCell className="text-gray-600">{guardrail.type}</TableCell>
                    <TableCell>
                      <Badge 
                        variant={guardrail.status === "Active" ? "success" : "secondary"}
                      >
                        {guardrail.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <Settings className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-red-600 hover:text-red-700">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}