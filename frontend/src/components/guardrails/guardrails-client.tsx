"use client";

import React, { useState, useEffect } from "react";
import { Settings, Plus, Edit, Trash2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import { GuardrailForm } from "@/components/guardrail-form";
import { GuardrailPresetSelector } from "@/components/guardrail-preset-selector";
import { GuardrailConfirmDialog } from "@/components/guardrail-confirm-dialog";
import { guardrailService } from "@/services/guardrail-service";
import { Guardrail, GuardrailFormData } from "@/types/guardrail";
import { GuardrailPreset } from "@/types/guardrail-presets";

interface GuardrailsClientProps {
  projectId: string;
}

export function GuardrailsClient({ projectId }: GuardrailsClientProps) {
  const [guardrails, setGuardrails] = useState<Guardrail[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [showPresetSelector, setShowPresetSelector] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingGuardrail, setEditingGuardrail] = useState<Guardrail | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<GuardrailPreset | null>(null);
  const { toast } = useToast();

  const fetchGuardrails = async () => {
    try {
      setIsLoading(true);
      const data = await guardrailService.getGuardrails(projectId);
      setGuardrails(data);
    } catch (error) {
      console.error('Failed to fetch guardrails:', error);
      toast({
        title: "Error",
        description: "Failed to load guardrails. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGuardrails();
  }, [projectId]);

  const handleSave = async (formData: GuardrailFormData) => {
    try {
      if (editingGuardrail) {
        await guardrailService.updateGuardrail(projectId, editingGuardrail.id, formData);
        toast({
          title: "Success",
          description: "Guardrail updated successfully.",
        });
      } else {
        await guardrailService.createGuardrail(projectId, formData);
        toast({
          title: "Success",
          description: "Guardrail created successfully.",
        });
      }
      
      setShowForm(false);
      setShowPresetSelector(false);
      setShowConfirmDialog(false);
      setEditingGuardrail(null);
      setSelectedPreset(null);
      fetchGuardrails();
    } catch (error) {
      console.error('Failed to save guardrail:', error);
      toast({
        title: "Error",
        description: "Failed to save guardrail. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await guardrailService.deleteGuardrail(projectId, id);
      toast({
        title: "Success",
        description: "Guardrail deleted successfully.",
      });
      fetchGuardrails();
    } catch (error) {
      console.error('Failed to delete guardrail:', error);
      toast({
        title: "Error",
        description: "Failed to delete guardrail. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleToggleStatus = async (guardrail: Guardrail) => {
    try {
      await guardrailService.toggleGuardrailStatus(projectId, guardrail.id, !guardrail.is_active);
      toast({
        title: "Success",
        description: `Guardrail ${guardrail.is_active ? 'deactivated' : 'activated'} successfully.`,
      });
      fetchGuardrails();
    } catch (error) {
      console.error('Failed to toggle guardrail status:', error);
      toast({
        title: "Error",
        description: "Failed to update guardrail status. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handlePresetSelect = (preset: GuardrailPreset) => {
    setSelectedPreset(preset);
    setShowPresetSelector(false);
    setShowConfirmDialog(true);
  };

  const handleCustomCreate = () => {
    setSelectedPreset(null);
    setShowPresetSelector(false);
    setShowForm(true);
  };

  const handleAddGuardrail = () => {
    setEditingGuardrail(null);
    setSelectedPreset(null);
    setShowPresetSelector(true);
  };

  const handleConfirmCreate = async () => {
    if (!selectedPreset) return;

    try {
      setIsCreating(true);
      await guardrailService.createGuardrail(projectId, selectedPreset.formData);
      toast({
        title: "Success",
        description: "Guardrail created successfully.",
      });
      
      setShowConfirmDialog(false);
      setSelectedPreset(null);
      fetchGuardrails();
    } catch (error) {
      console.error('Failed to create guardrail:', error);
      toast({
        title: "Error",
        description: "Failed to create guardrail. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  };

  const getTriggerDescription = (guardrail: Guardrail): string => {
    const { trigger_condition } = guardrail;
    switch (trigger_condition.type) {
      case 'always':
        return 'Always';
      case 'specific_tool':
        return `Tool: ${trigger_condition.tool_name}`;
      case 'tool_regex':
        return `Regex: ${trigger_condition.tool_regex}`;
      default:
        return 'Unknown';
    }
  };

  const getCheckDescription = (guardrail: Guardrail): string => {
    const { check_config } = guardrail;
    switch (check_config.type) {
      case 'missing_values_any':
        return 'Any missing values';
      case 'missing_values_column':
        return `Missing in: ${check_config.target_column}`;
      case 'old_date_records':
        return `Dates older than ${check_config.date_threshold_days} days`;
      default:
        return 'Unknown';
    }
  };

  const getActionDescription = (guardrail: Guardrail): string => {
    return guardrail.action.type === 'filter_records' ? 'Filter' : 'Interrupt';
  };

  if (showPresetSelector) {
    return (
      <GuardrailPresetSelector
        projectId={projectId}
        onSelectPreset={handlePresetSelect}
        onCustomCreate={handleCustomCreate}
        onCancel={() => setShowPresetSelector(false)}
      />
    );
  }

  if (showForm) {
    return (
      <GuardrailForm
        projectId={projectId}
        guardrail={editingGuardrail || undefined}
        onSave={handleSave}
        onCancel={() => {
          setShowForm(false);
          setEditingGuardrail(null);
        }}
      />
    );
  }

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
          <Button 
            size="sm" 
            className="bg-blue-600 hover:bg-blue-700"
            onClick={handleAddGuardrail}
          >
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
                  <TableHead className="font-semibold text-gray-900">Name</TableHead>
                  <TableHead className="font-semibold text-gray-900">Trigger</TableHead>
                  <TableHead className="font-semibold text-gray-900">Check</TableHead>
                  <TableHead className="font-semibold text-gray-900">Action</TableHead>
                  <TableHead className="font-semibold text-gray-900">Status</TableHead>
                  <TableHead className="font-semibold text-gray-900">Stats</TableHead>
                  <TableHead className="font-semibold text-gray-900">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <div className="flex items-center justify-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        <span>Loading guardrails...</span>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : guardrails.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <div className="flex flex-col items-center space-y-2">
                        <AlertCircle className="h-8 w-8 text-gray-400" />
                        <p className="text-gray-500">No guardrails configured yet</p>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={handleAddGuardrail}
                        >
                          Create your first guardrail
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  guardrails.map((guardrail) => (
                    <TableRow key={guardrail.id} className="hover:bg-gray-50 transition-colors">
                      <TableCell>
                        <div>
                          <div className="font-medium">{guardrail.name}</div>
                          <div className="text-sm text-gray-500">{guardrail.description}</div>
                        </div>
                      </TableCell>
                      <TableCell className="text-gray-600">
                        {getTriggerDescription(guardrail)}
                      </TableCell>
                      <TableCell className="text-gray-600">
                        {getCheckDescription(guardrail)}
                      </TableCell>
                      <TableCell className="text-gray-600">
                        {getActionDescription(guardrail)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleStatus(guardrail)}
                          className="p-0 h-auto"
                        >
                          <Badge 
                            variant={guardrail.is_active ? "default" : "secondary"}
                            className={guardrail.is_active ? "bg-green-100 text-green-800 hover:bg-green-200" : ""}
                          >
                            {guardrail.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </Button>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div>Executed: {guardrail.execution_count}</div>
                          <div>Applied: {guardrail.applied_count}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="h-8 w-8 p-0"
                            onClick={() => {
                              setEditingGuardrail(guardrail);
                              setShowForm(true);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                            onClick={() => handleDelete(guardrail.id, guardrail.name)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
      
      {/* Confirmation Dialog */}
      {showConfirmDialog && selectedPreset && (
        <GuardrailConfirmDialog
          preset={selectedPreset}
          formData={selectedPreset.formData}
          onConfirm={handleConfirmCreate}
          onCancel={() => {
            setShowConfirmDialog(false);
            setSelectedPreset(null);
          }}
          isLoading={isCreating}
        />
      )}
    </div>
  );
}