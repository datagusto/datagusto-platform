import { GuardrailFormData } from './guardrail';

export interface GuardrailPreset {
  id: string;
  name: string;
  description: string;
  category: 'data_quality' | 'performance' | 'security';
  icon: string;
  formData: GuardrailFormData;
  tags: string[];
}

export const GUARDRAIL_PRESETS: GuardrailPreset[] = [
  {
    id: 'missing_values_filter',
    name: 'Missing Values Filter',
    description: 'Automatically removes records with any missing values from tool results',
    category: 'data_quality',
    icon: '🔍',
    tags: ['Data Quality', 'Auto-Filter', 'Missing Values'],
    formData: {
      name: 'Missing Values Filter',
      description: 'Automatically removes records with any missing values from tool results',
      triggerType: 'always',
      checkType: 'missing_values_any',
      actionType: 'filter_records'
    }
  }
];

export const GUARDRAIL_CATEGORIES = {
  data_quality: {
    name: 'Data Quality',
    description: 'Ensure data integrity and completeness',
    color: 'bg-blue-100 text-blue-800'
  },
  performance: {
    name: 'Performance',
    description: 'Optimize processing speed and efficiency',
    color: 'bg-green-100 text-green-800'
  },
  security: {
    name: 'Security',
    description: 'Protect sensitive data and access',
    color: 'bg-red-100 text-red-800'
  }
} as const;