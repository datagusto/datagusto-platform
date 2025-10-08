/**
 * Guardrail form validation schemas
 *
 * @description Zod schemas for validating guardrail creation and update forms.
 * Defines the structure of guardrail definitions including triggers, conditions, and actions.
 *
 * @module guardrail.schema
 */

import { z } from 'zod';

/**
 * Trigger type enum
 */
export const TriggerTypeEnum = z.enum(['on_start', 'on_end']);

/**
 * Condition logic enum
 */
export const ConditionLogicEnum = z.enum(['and', 'or']);

/**
 * Condition operator enum
 */
export const ConditionOperatorEnum = z.enum([
  'contains',
  'equals',
  'regex',
  'gt',
  'lt',
  'gte',
  'lte',
  'size_gt',
  'size_lt',
  'size_gte',
  'size_lte',
  'llm_judge',
]);

/**
 * Action type enum
 */
export const ActionTypeEnum = z.enum(['block', 'warn', 'modify']);

/**
 * Modification type enum (for modify actions)
 */
export const ModificationTypeEnum = z.enum(['drop_field', 'drop_item']);

/**
 * Modify condition operator enum
 */
export const ModifyConditionOperatorEnum = z.enum([
  'is_null',
  'is_empty',
  'equals',
]);

/**
 * Severity level enum
 */
export const SeverityEnum = z.enum(['low', 'medium', 'high', 'critical']);

/**
 * Field path validation regex
 * Matches patterns like: input.query, data.users[0].email, matrix[1][2]
 */
const fieldPathRegex =
  /^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*$/;

/**
 * Condition schema
 *
 * @description Defines a single condition in a guardrail trigger.
 */
export const conditionSchema = z.object({
  field: z
    .string()
    .min(1, 'Field path is required')
    .regex(fieldPathRegex, 'Invalid field path format'),
  operator: ConditionOperatorEnum,
  value: z.any().optional(),
});

/**
 * Block action config schema
 */
export const blockActionConfigSchema = z.object({
  message: z.string().min(1, 'Block message is required'),
});

/**
 * Warn action config schema
 */
export const warnActionConfigSchema = z.object({
  message: z.string().min(1, 'Warning message is required'),
  severity: SeverityEnum,
  allow_proceed: z.boolean(),
});

/**
 * Modify action condition schema
 */
export const modifyConditionSchema = z.object({
  fields: z.array(z.string()).min(1, 'At least one field is required'),
  operator: ModifyConditionOperatorEnum,
  value: z.any().optional(),
});

/**
 * Modify action config schema
 */
export const modifyActionConfigSchema = z.object({
  modification_type: ModificationTypeEnum,
  target: z
    .string()
    .min(1, 'Target path is required')
    .regex(fieldPathRegex, 'Invalid target path format'),
  condition: modifyConditionSchema,
});

/**
 * Action schema (discriminated union based on type)
 */
export const actionSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('block'),
    priority: z.number().int().min(1).max(100),
    config: blockActionConfigSchema,
  }),
  z.object({
    type: z.literal('warn'),
    priority: z.number().int().min(1).max(100),
    config: warnActionConfigSchema,
  }),
  z.object({
    type: z.literal('modify'),
    priority: z.number().int().min(1).max(100),
    config: modifyActionConfigSchema,
  }),
]);

/**
 * Trigger schema
 */
export const triggerSchema = z.object({
  type: TriggerTypeEnum,
  logic: ConditionLogicEnum,
  conditions: z
    .array(conditionSchema)
    .min(1, 'At least one condition is required'),
});

/**
 * Guardrail definition schema
 */
export const guardrailDefinitionSchema = z.object({
  trigger: triggerSchema,
  actions: z.array(actionSchema).min(1, 'At least one action is required'),
});

/**
 * Create guardrail form schema
 */
export const createGuardrailSchema = z.object({
  name: z
    .string()
    .min(1, 'Guardrail name is required')
    .max(255, 'Guardrail name must be less than 255 characters'),
  description: z.string().optional(),
  definition: guardrailDefinitionSchema,
});

/**
 * Type exports for TypeScript
 */
export type TriggerType = z.infer<typeof TriggerTypeEnum>;
export type ConditionLogic = z.infer<typeof ConditionLogicEnum>;
export type ConditionOperator = z.infer<typeof ConditionOperatorEnum>;
export type ActionType = z.infer<typeof ActionTypeEnum>;
export type ModificationType = z.infer<typeof ModificationTypeEnum>;
export type ModifyConditionOperator = z.infer<
  typeof ModifyConditionOperatorEnum
>;
export type Severity = z.infer<typeof SeverityEnum>;

export type Condition = z.infer<typeof conditionSchema>;
export type BlockActionConfig = z.infer<typeof blockActionConfigSchema>;
export type WarnActionConfig = z.infer<typeof warnActionConfigSchema>;
export type ModifyCondition = z.infer<typeof modifyConditionSchema>;
export type ModifyActionConfig = z.infer<typeof modifyActionConfigSchema>;
export type Action = z.infer<typeof actionSchema>;
export type Trigger = z.infer<typeof triggerSchema>;
export type GuardrailDefinition = z.infer<typeof guardrailDefinitionSchema>;
export type CreateGuardrailFormData = z.infer<typeof createGuardrailSchema>;
