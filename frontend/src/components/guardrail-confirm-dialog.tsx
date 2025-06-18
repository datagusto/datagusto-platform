"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GuardrailFormData } from "@/types/guardrail";
import { GuardrailPreset, GUARDRAIL_CATEGORIES } from "@/types/guardrail-presets";

interface GuardrailConfirmDialogProps {
  preset: GuardrailPreset;
  formData: GuardrailFormData;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function GuardrailConfirmDialog({
  preset,
  formData,
  onConfirm,
  onCancel,
  isLoading = false
}: GuardrailConfirmDialogProps) {
  const getTriggerText = () => {
    switch (formData.triggerType) {
      case 'always':
        return 'Always active';
      case 'specific_tool':
        return `When tool "${formData.toolName}" is called`;
      case 'tool_regex':
        return `When tool matches pattern "${formData.toolRegex}"`;
      default:
        return 'Unknown trigger';
    }
  };

  const getCheckText = () => {
    switch (formData.checkType) {
      case 'missing_values_any':
        return 'Check for any missing values in records';
      case 'missing_values_column':
        return `Check for missing values in "${formData.targetColumn}" column`;
      case 'old_date_records':
        return `Check for records older than ${formData.dateThresholdDays} days`;
      default:
        return 'Unknown check';
    }
  };

  const getActionText = () => {
    switch (formData.actionType) {
      case 'filter_records':
        return 'Remove matching records from results';
      case 'interrupt_agent':
        return 'Stop agent execution immediately';
      default:
        return 'Unknown action';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="max-w-2xl w-full">
        <CardHeader>
          <div className="flex items-start gap-4">
            <div className="text-3xl">{preset.icon}</div>
            <div className="flex-1">
              <CardTitle className="text-xl mb-2">Confirm Guardrail Creation</CardTitle>
              <CardDescription>
                You're about to create the following guardrail. Please review the configuration.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Guardrail Info */}
          <div className="space-y-3">
            <div>
              <h3 className="font-semibold text-lg">{formData.name}</h3>
              <p className="text-gray-600">{formData.description}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge 
                variant="secondary" 
                className={GUARDRAIL_CATEGORIES[preset.category].color}
              >
                {GUARDRAIL_CATEGORIES[preset.category].name}
              </Badge>
              {preset.tags.map((tag) => (
                <Badge key={tag} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>

          {/* Configuration Details */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-4">
            <h4 className="font-medium text-sm text-gray-700 uppercase tracking-wide">Configuration</h4>
            
            <div className="space-y-3 text-sm">
              <div>
                <span className="font-medium text-gray-700">Trigger:</span>
                <p className="text-gray-900 mt-1">{getTriggerText()}</p>
              </div>
              
              <div>
                <span className="font-medium text-gray-700">Check:</span>
                <p className="text-gray-900 mt-1">{getCheckText()}</p>
              </div>
              
              <div>
                <span className="font-medium text-gray-700">Action:</span>
                <p className="text-gray-900 mt-1">{getActionText()}</p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button 
              variant="outline" 
              onClick={onCancel}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              onClick={onConfirm}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isLoading ? 'Creating...' : 'Create Guardrail'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}