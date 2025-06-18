import { Guardrail, GuardrailFormData, GuardrailCreateRequest } from '@/types/guardrail';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class GuardrailService {
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  async getGuardrails(projectId: string): Promise<Guardrail[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/guardrails`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch guardrails');
    }

    return response.json();
  }

  async createGuardrail(
    projectId: string,
    formData: GuardrailFormData
  ): Promise<Guardrail> {
    const requestData: GuardrailCreateRequest = {
      name: formData.name,
      description: formData.description,
      trigger_condition: {
        type: formData.triggerType,
        ...(formData.triggerType === 'specific_tool' && { tool_name: formData.toolName }),
        ...(formData.triggerType === 'tool_regex' && { tool_regex: formData.toolRegex }),
      },
      check_config: {
        type: formData.checkType,
        ...(formData.checkType === 'missing_values_column' && { target_column: formData.targetColumn }),
        ...(formData.checkType === 'old_date_records' && { date_threshold_days: formData.dateThresholdDays }),
      },
      action: {
        type: formData.actionType,
      },
      is_active: true,
    };

    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/guardrails`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(requestData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create guardrail');
    }

    return response.json();
  }

  async updateGuardrail(
    projectId: string,
    guardrailId: string,
    formData: GuardrailFormData
  ): Promise<Guardrail> {
    const requestData: Partial<GuardrailCreateRequest> = {
      name: formData.name,
      description: formData.description,
      trigger_condition: {
        type: formData.triggerType,
        ...(formData.triggerType === 'specific_tool' && { tool_name: formData.toolName }),
        ...(formData.triggerType === 'tool_regex' && { tool_regex: formData.toolRegex }),
      },
      check_config: {
        type: formData.checkType,
        ...(formData.checkType === 'missing_values_column' && { target_column: formData.targetColumn }),
        ...(formData.checkType === 'old_date_records' && { date_threshold_days: formData.dateThresholdDays }),
      },
      action: {
        type: formData.actionType,
      },
    };

    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/guardrails/${guardrailId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(requestData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update guardrail');
    }

    return response.json();
  }

  async deleteGuardrail(projectId: string, guardrailId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/guardrails/${guardrailId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete guardrail');
    }
  }

  async toggleGuardrailStatus(
    projectId: string,
    guardrailId: string,
    isActive: boolean
  ): Promise<Guardrail> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/guardrails/${guardrailId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ is_active: isActive }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to toggle guardrail status');
    }

    return response.json();
  }
}

export const guardrailService = new GuardrailService();