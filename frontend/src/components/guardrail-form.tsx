"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { ArrowLeft } from "lucide-react";
import { Guardrail, GuardrailFormData } from "@/types/guardrail";

interface GuardrailFormProps {
  projectId: string;
  guardrail?: Guardrail;
  initialFormData?: GuardrailFormData | null;
  onSave: (guardrail: GuardrailFormData) => void;
  onCancel: () => void;
}

export function GuardrailForm({ projectId, guardrail, initialFormData, onSave, onCancel }: GuardrailFormProps) {
  // プリセットデータ、既存ガードレール、デフォルトの優先順位で初期値を設定
  const getInitialFormData = (): GuardrailFormData => {
    if (initialFormData) {
      return initialFormData;
    }
    if (guardrail) {
      return {
        name: guardrail.name,
        description: guardrail.description,
        triggerType: guardrail.trigger_condition.type,
        toolName: guardrail.trigger_condition.tool_name,
        toolRegex: guardrail.trigger_condition.tool_regex,
        checkType: guardrail.check_config.type,
        targetColumn: guardrail.check_config.target_column,
        dateThresholdDays: guardrail.check_config.date_threshold_days || 365,
        actionType: guardrail.action.type
      };
    }
    return {
      name: '',
      description: '',
      triggerType: 'always',
      toolName: '',
      toolRegex: '',
      checkType: 'missing_values_any',
      targetColumn: '',
      dateThresholdDays: 365,
      actionType: 'filter_records'
    };
  };

  const [formData, setFormData] = useState<GuardrailFormData>(getInitialFormData());

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (formData.triggerType === 'specific_tool' && !formData.toolName?.trim()) {
      newErrors.toolName = 'Tool name is required';
    }

    if (formData.triggerType === 'tool_regex' && !formData.toolRegex?.trim()) {
      newErrors.toolRegex = 'Tool regex is required';
    }

    if (formData.checkType === 'missing_values_column' && !formData.targetColumn?.trim()) {
      newErrors.targetColumn = 'Target column is required';
    }

    if (formData.checkType === 'old_date_records' && (!formData.dateThresholdDays || formData.dateThresholdDays <= 0)) {
      newErrors.dateThresholdDays = 'Valid days threshold is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSave(formData);
    }
  };

  const getTriggerDisplayText = () => {
    switch (formData.triggerType) {
      case 'always':
        return 'Always apply this guardrail to all tool results';
      case 'specific_tool':
        return 'Apply only when a specific tool is executed';
      case 'tool_regex':
        return 'Apply when tool name matches a regular expression pattern';
      default:
        return '';
    }
  };

  const getCheckDisplayText = () => {
    switch (formData.checkType) {
      case 'missing_values_any':
        return 'Check if any record has missing values in any field';
      case 'missing_values_column':
        return 'Check if any record has missing values in a specific column';
      case 'old_date_records':
        return 'Check if any record contains date values older than the threshold';
      default:
        return '';
    }
  };

  const getActionDisplayText = () => {
    switch (formData.actionType) {
      case 'filter_records':
        return 'Remove matching records from the tool result';
      case 'interrupt_agent':
        return 'Stop agent execution when condition is met';
      default:
        return '';
    }
  };

  return (
    <div className="flex-1 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="sm" onClick={onCancel}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {guardrail ? 'Edit Guardrail' : 'Create New Guardrail'}
            </h1>
            <p className="text-gray-600">
              {guardrail ? 'Update guardrail configuration' : 'Configure a new guardrail for this project'}
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter guardrail name"
                  className={errors.name ? 'border-red-500' : ''}
                />
                {errors.name && <p className="text-sm text-red-500 mt-1">{errors.name}</p>}
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Enter guardrail description"
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          {/* Trigger Condition */}
          <Card>
            <CardHeader>
              <CardTitle>When to Apply</CardTitle>
              <p className="text-sm text-gray-600">{getTriggerDisplayText()}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <RadioGroup 
                value={formData.triggerType} 
                onValueChange={(value) => setFormData({ ...formData, triggerType: value as any })}
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="always" id="trigger-always" />
                  <Label htmlFor="trigger-always" className="cursor-pointer">Always apply</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="specific_tool" id="trigger-specific" />
                  <Label htmlFor="trigger-specific" className="cursor-pointer">Specific tool name</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="tool_regex" id="trigger-regex" />
                  <Label htmlFor="trigger-regex" className="cursor-pointer">Tool name regex pattern</Label>
                </div>
              </RadioGroup>

              {formData.triggerType === 'specific_tool' && (
                <div>
                  <Label htmlFor="toolName">Tool Name *</Label>
                  <Input
                    id="toolName"
                    placeholder="e.g., database_query, api_call"
                    value={formData.toolName}
                    onChange={(e) => setFormData({ ...formData, toolName: e.target.value })}
                    className={errors.toolName ? 'border-red-500' : ''}
                  />
                  {errors.toolName && <p className="text-sm text-red-500 mt-1">{errors.toolName}</p>}
                </div>
              )}

              {formData.triggerType === 'tool_regex' && (
                <div>
                  <Label htmlFor="toolRegex">Regular Expression *</Label>
                  <Input
                    id="toolRegex"
                    placeholder="e.g., ^data_.*_tool$, .*_query.*"
                    value={formData.toolRegex}
                    onChange={(e) => setFormData({ ...formData, toolRegex: e.target.value })}
                    className={errors.toolRegex ? 'border-red-500' : ''}
                  />
                  {errors.toolRegex && <p className="text-sm text-red-500 mt-1">{errors.toolRegex}</p>}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Check Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>What to Check</CardTitle>
              <p className="text-sm text-gray-600">{getCheckDisplayText()}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <RadioGroup 
                value={formData.checkType} 
                onValueChange={(value) => setFormData({ ...formData, checkType: value as any })}
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="missing_values_any" id="check-any" />
                  <Label htmlFor="check-any" className="cursor-pointer">Any missing values in any field</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="missing_values_column" id="check-column" />
                  <Label htmlFor="check-column" className="cursor-pointer">Missing values in specific column</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="old_date_records" id="check-date" />
                  <Label htmlFor="check-date" className="cursor-pointer">Records with old date values</Label>
                </div>
              </RadioGroup>

              {formData.checkType === 'missing_values_column' && (
                <div>
                  <Label htmlFor="targetColumn">Target Column Name *</Label>
                  <Input
                    id="targetColumn"
                    placeholder="e.g., user_id, email, name"
                    value={formData.targetColumn}
                    onChange={(e) => setFormData({ ...formData, targetColumn: e.target.value })}
                    className={errors.targetColumn ? 'border-red-500' : ''}
                  />
                  {errors.targetColumn && <p className="text-sm text-red-500 mt-1">{errors.targetColumn}</p>}
                </div>
              )}

              {formData.checkType === 'old_date_records' && (
                <div>
                  <Label htmlFor="dateThresholdDays">Days Threshold *</Label>
                  <Input
                    id="dateThresholdDays"
                    type="number"
                    min="1"
                    placeholder="365"
                    value={formData.dateThresholdDays}
                    onChange={(e) => setFormData({ ...formData, dateThresholdDays: parseInt(e.target.value) || 365 })}
                    className={errors.dateThresholdDays ? 'border-red-500' : ''}
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Records with dates older than {formData.dateThresholdDays || 365} days will be flagged
                  </p>
                  {errors.dateThresholdDays && <p className="text-sm text-red-500 mt-1">{errors.dateThresholdDays}</p>}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Action Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>What to Do</CardTitle>
              <p className="text-sm text-gray-600">{getActionDisplayText()}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <RadioGroup 
                value={formData.actionType} 
                onValueChange={(value) => setFormData({ ...formData, actionType: value as any })}
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="filter_records" id="action-filter" />
                  <Label htmlFor="action-filter" className="cursor-pointer">Remove matching records</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="interrupt_agent" id="action-interrupt" />
                  <Label htmlFor="action-interrupt" className="cursor-pointer">Interrupt agent execution</Label>
                </div>
              </RadioGroup>
            </CardContent>
          </Card>

          {/* Form Actions */}
          <div className="flex justify-end space-x-4">
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
              {guardrail ? 'Update Guardrail' : 'Create Guardrail'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}