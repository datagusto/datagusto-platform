/**
 * Create guardrail form component
 *
 * @description Comprehensive form for creating guardrails with triggers, conditions, and actions.
 * Supports dynamic condition and action builders with validation.
 *
 * **Features**:
 * - Basic information (name, description)
 * - Trigger settings (timing, logic)
 * - Dynamic conditions array
 * - Dynamic actions array with type-specific configs
 * - Full validation with Zod
 *
 * @module create-guardrail-form
 */

'use client';

import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  createGuardrailSchema,
  type CreateGuardrailFormData,
  type Condition,
  type Action,
  TriggerTypeEnum,
  ConditionLogicEnum,
  ConditionOperatorEnum,
  ActionTypeEnum,
  SeverityEnum,
  ModificationTypeEnum,
  ModifyConditionOperatorEnum,
} from '../schemas/guardrail.schema';

/**
 * Create guardrail form props
 */
interface CreateGuardrailFormProps {
  onSubmit: (data: CreateGuardrailFormData) => void;
  isLoading?: boolean;
  error?: Error | null;
}

/**
 * Create guardrail form component
 *
 * @description Main form component with all sections:
 * 1. Basic Information (name, description)
 * 2. Trigger Settings (timing, logic)
 * 3. Conditions (dynamic array)
 * 4. Actions (dynamic array with type-specific configs)
 */
export function CreateGuardrailForm({
  onSubmit,
  isLoading,
  error,
}: CreateGuardrailFormProps) {
  // Form state management
  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CreateGuardrailFormData>({
    resolver: zodResolver(createGuardrailSchema),
    defaultValues: {
      name: '',
      description: '',
      definition: {
        trigger: {
          type: 'on_start',
          logic: 'and',
          conditions: [
            {
              field: 'input.',
              operator: 'contains',
              value: '',
            },
          ],
        },
        actions: [
          {
            type: 'block',
            priority: 1,
            config: {
              message: '',
            },
          },
        ],
      },
    },
  });

  // Field arrays for dynamic conditions and actions
  const {
    fields: conditionFields,
    append: appendCondition,
    remove: removeCondition,
  } = useFieldArray({
    control,
    name: 'definition.trigger.conditions',
  });

  const {
    fields: actionFields,
    append: appendAction,
    remove: removeAction,
  } = useFieldArray({
    control,
    name: 'definition.actions',
  });

  // Watch action types to render appropriate configs
  const actions = watch('definition.actions');

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8 max-w-4xl">
      {/* API Error Display */}
      {error && (
        <div className="rounded-md bg-red-50 p-4 text-sm text-red-600">
          {error.message || 'Failed to create guardrail'}
        </div>
      )}

      {/* Section 1: Basic Information */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold border-b pb-2">Basic Information</h2>

        {/* Guardrail Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium mb-1">
            Guardrail Name <span className="text-red-500">*</span>
          </label>
          <input
            id="name"
            type="text"
            className="w-full border rounded-md px-3 py-2"
            placeholder="e.g., PII Detection, Harmful Content Filter"
            {...register('name')}
          />
          {errors.name && (
            <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium mb-1">
            Description
          </label>
          <textarea
            id="description"
            className="w-full border rounded-md px-3 py-2 min-h-20"
            placeholder="Describe what this guardrail does..."
            {...register('description')}
          />
          {errors.description && (
            <p className="mt-1 text-xs text-red-600">{errors.description.message}</p>
          )}
        </div>
      </section>

      {/* Section 2: Trigger Settings */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold border-b pb-2">Trigger Settings</h2>

        {/* Timing */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Timing <span className="text-red-500">*</span>
          </label>
          <div className="space-y-2">
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                value="on_start"
                {...register('definition.trigger.type')}
              />
              <span>
                <strong>On Start</strong> - Evaluate before process execution
              </span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                value="on_end"
                {...register('definition.trigger.type')}
              />
              <span>
                <strong>On End</strong> - Evaluate after process execution
              </span>
            </label>
          </div>
          {errors.definition?.trigger?.type && (
            <p className="mt-1 text-xs text-red-600">
              {errors.definition.trigger.type.message}
            </p>
          )}
        </div>

        {/* Condition Logic */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Condition Logic <span className="text-red-500">*</span>
          </label>
          <div className="space-y-2">
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                value="and"
                {...register('definition.trigger.logic')}
              />
              <span>
                <strong>AND</strong> - All conditions must match
              </span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                value="or"
                {...register('definition.trigger.logic')}
              />
              <span>
                <strong>OR</strong> - Any condition can match
              </span>
            </label>
          </div>
          {errors.definition?.trigger?.logic && (
            <p className="mt-1 text-xs text-red-600">
              {errors.definition.trigger.logic.message}
            </p>
          )}
        </div>
      </section>

      {/* Section 3: Conditions */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b pb-2">
          <h2 className="text-lg font-semibold">
            Conditions <span className="text-red-500">*</span>
          </h2>
          <button
            type="button"
            onClick={() =>
              appendCondition({
                field: 'input.',
                operator: 'contains',
                value: '',
              })
            }
            className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-md"
          >
            + Add Condition
          </button>
        </div>

        {conditionFields.map((field, index) => (
          <div
            key={field.id}
            className="border rounded-md p-4 space-y-3 bg-gray-50"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-sm">Condition {index + 1}</h3>
              {conditionFields.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeCondition(index)}
                  className="text-xs text-red-600 hover:text-red-800"
                >
                  Remove
                </button>
              )}
            </div>

            {/* Field Path */}
            <div>
              <label className="block text-xs font-medium mb-1">
                Field Path <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                className="w-full border rounded px-2 py-1 text-sm"
                placeholder="e.g., input.query, data.users[0].email"
                {...register(
                  `definition.trigger.conditions.${index}.field` as const
                )}
              />
              <p className="mt-1 text-xs text-gray-500">
                Examples: input.query, output.result, data.items[0].name
              </p>
              {errors.definition?.trigger?.conditions?.[index]?.field && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.definition.trigger.conditions[index]?.field?.message}
                </p>
              )}
            </div>

            {/* Operator */}
            <div>
              <label className="block text-xs font-medium mb-1">
                Operator <span className="text-red-500">*</span>
              </label>
              <select
                className="w-full border rounded px-2 py-1 text-sm"
                {...register(
                  `definition.trigger.conditions.${index}.operator` as const
                )}
              >
                <optgroup label="String Operators">
                  <option value="contains">Contains</option>
                  <option value="equals">Equals</option>
                  <option value="regex">Regex Match</option>
                </optgroup>
                <optgroup label="Numeric Operators">
                  <option value="gt">Greater Than</option>
                  <option value="lt">Less Than</option>
                  <option value="gte">Greater Than or Equal</option>
                  <option value="lte">Less Than or Equal</option>
                </optgroup>
                <optgroup label="Size Operators">
                  <option value="size_gt">Size Greater Than</option>
                  <option value="size_lt">Size Less Than</option>
                  <option value="size_gte">Size Greater Than or Equal</option>
                  <option value="size_lte">Size Less Than or Equal</option>
                </optgroup>
                <optgroup label="LLM Judge">
                  <option value="llm_judge">LLM Judge (AI Evaluation)</option>
                </optgroup>
              </select>
              {errors.definition?.trigger?.conditions?.[index]?.operator && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.definition.trigger.conditions[index]?.operator?.message}
                </p>
              )}
            </div>

            {/* Value (conditional based on operator) */}
            <div>
              <label className="block text-xs font-medium mb-1">Value</label>
              <input
                type="text"
                className="w-full border rounded px-2 py-1 text-sm"
                placeholder="Enter comparison value"
                {...register(
                  `definition.trigger.conditions.${index}.value` as const
                )}
              />
              {errors.definition?.trigger?.conditions?.[index]?.value && (
                <p className="mt-1 text-xs text-red-600">
                  {String(errors.definition.trigger.conditions[index]?.value?.message || '')}
                </p>
              )}
            </div>
          </div>
        ))}

        {errors.definition?.trigger?.conditions && (
          <p className="text-xs text-red-600">
            {String(errors.definition.trigger.conditions.message || 'Invalid conditions')}
          </p>
        )}
      </section>

      {/* Section 4: Actions */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b pb-2">
          <h2 className="text-lg font-semibold">
            Actions <span className="text-red-500">*</span>
          </h2>
          <button
            type="button"
            onClick={() =>
              appendAction({
                type: 'block',
                priority: actionFields.length + 1,
                config: {
                  message: '',
                },
              })
            }
            className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-md"
          >
            + Add Action
          </button>
        </div>

        {actionFields.map((field, index) => (
          <div
            key={field.id}
            className="border rounded-md p-4 space-y-3 bg-gray-50"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-sm">Action {index + 1}</h3>
              {actionFields.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeAction(index)}
                  className="text-xs text-red-600 hover:text-red-800"
                >
                  Remove
                </button>
              )}
            </div>

            {/* Action Type */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1">
                  Type <span className="text-red-500">*</span>
                </label>
                <select
                  className="w-full border rounded px-2 py-1 text-sm"
                  {...register(`definition.actions.${index}.type` as const)}
                >
                  <option value="block">Block</option>
                  <option value="warn">Warn</option>
                  <option value="modify">Modify</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium mb-1">
                  Priority <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  className="w-full border rounded px-2 py-1 text-sm"
                  {...register(`definition.actions.${index}.priority` as const, {
                    valueAsNumber: true,
                  })}
                />
              </div>
            </div>

            {/* Block Action Config */}
            {actions[index]?.type === 'block' && (
              <div>
                <label className="block text-xs font-medium mb-1">
                  Block Message <span className="text-red-500">*</span>
                </label>
                <textarea
                  className="w-full border rounded px-2 py-1 text-sm min-h-16"
                  placeholder="Message to display when blocked"
                  {...register(
                    `definition.actions.${index}.config.message` as const
                  )}
                />
                {errors.definition?.actions?.[index]?.config && (
                  <p className="mt-1 text-xs text-red-600">
                    {String((errors.definition.actions[index]?.config as any)?.message?.message || 'Invalid config')}
                  </p>
                )}
              </div>
            )}

            {/* Warn Action Config */}
            {actions[index]?.type === 'warn' && (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium mb-1">
                    Warning Message <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    className="w-full border rounded px-2 py-1 text-sm min-h-16"
                    placeholder="Warning message to display"
                    {...register(
                      `definition.actions.${index}.config.message` as const
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Severity <span className="text-red-500">*</span>
                    </label>
                    <select
                      className="w-full border rounded px-2 py-1 text-sm"
                      {...register(
                        `definition.actions.${index}.config.severity` as const
                      )}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>

                  <div className="flex items-center">
                    <label className="flex items-center space-x-2 text-xs">
                      <input
                        type="checkbox"
                        {...register(
                          `definition.actions.${index}.config.allow_proceed` as const
                        )}
                      />
                      <span>Allow Proceed</span>
                    </label>
                  </div>
                </div>

                {errors.definition?.actions?.[index]?.config && (
                  <p className="mt-1 text-xs text-red-600">
                    {String((errors.definition.actions[index]?.config as any)?.message?.message || 'Invalid config')}
                  </p>
                )}
              </div>
            )}

            {/* Modify Action Config */}
            {actions[index]?.type === 'modify' && (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium mb-1">
                    Modification Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    className="w-full border rounded px-2 py-1 text-sm"
                    {...register(
                      `definition.actions.${index}.config.modification_type` as const
                    )}
                  >
                    <option value="">Select type...</option>
                    <option value="drop_field">Drop Field</option>
                    <option value="drop_item">Drop Item</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    drop_field: Remove fields from objects | drop_item: Remove items from arrays
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-medium mb-1">
                    Target Path <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    className="w-full border rounded px-2 py-1 text-sm"
                    placeholder="e.g., input.user_data, output.items"
                    {...register(
                      `definition.actions.${index}.config.target` as const
                    )}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Field path to the object/array to modify
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-medium mb-1">
                    Condition Fields <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    className="w-full border rounded px-2 py-1 text-sm"
                    placeholder="field1,field2 or * for all fields"
                    {...register(
                      `definition.actions.${index}.config.condition.fields` as const,
                      {
                        setValueAs: (value: string) =>
                          value.split(',').map((f: string) => f.trim()).filter(Boolean)
                      }
                    )}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Comma-separated field names or * for all
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Condition Operator <span className="text-red-500">*</span>
                    </label>
                    <select
                      className="w-full border rounded px-2 py-1 text-sm"
                      {...register(
                        `definition.actions.${index}.config.condition.operator` as const
                      )}
                    >
                      <option value="">Select operator...</option>
                      <option value="is_null">Is Null</option>
                      <option value="is_empty">Is Empty</option>
                      <option value="equals">Equals</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Value (for equals)
                    </label>
                    <input
                      type="text"
                      className="w-full border rounded px-2 py-1 text-sm"
                      placeholder="Value to compare"
                      {...register(
                        `definition.actions.${index}.config.condition.value` as const
                      )}
                    />
                  </div>
                </div>

                {errors.definition?.actions?.[index]?.config && (
                  <p className="mt-1 text-xs text-red-600">
                    {String((errors.definition.actions[index]?.config as any)?.message || 'Invalid config')}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}

        {errors.definition?.actions && (
          <p className="text-xs text-red-600">
            {String(errors.definition.actions.message || 'Invalid actions')}
          </p>
        )}
      </section>

      {/* Submit Button */}
      <div className="flex justify-end space-x-3 pt-4 border-t">
        <button
          type="button"
          className="px-4 py-2 border rounded-md hover:bg-gray-50"
          onClick={() => window.history.back()}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting || isLoading}
          className="px-4 py-2 bg-black text-white rounded-md disabled:opacity-60 hover:bg-gray-800"
        >
          {isLoading ? 'Creating...' : 'Create Guardrail'}
        </button>
      </div>
    </form>
  );
}
