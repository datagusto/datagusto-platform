/**
 * Agent Alignment Demo Component
 *
 * @description Displays dummy alignment results including tool invocation rules
 * and tool validation results. Shows how the alignment system works with
 * an example user instruction.
 *
 * @module agent-alignment-demo
 */

'use client';

import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  AlertTriangle,
} from 'lucide-react';

// Dummy data for demonstration
const DEMO_USER_INSTRUCTION = '春学期の期末試験の結果について報告して';

const DEMO_RESOLVED_TERMS = [
  {
    term: '春学期',
    category: 'time',
    resolved_value: '2025 Spring Semester (2025-04-01 to 2025-07-31)',
    confidence: 'HIGH',
  },
  {
    term: '期末試験',
    category: 'object',
    resolved_value: 'final examination',
    confidence: 'HIGH',
  },
  {
    term: '結果',
    category: 'object',
    resolved_value: 'test results/scores',
    confidence: 'HIGH',
  },
];

const DEMO_TOOL_INVOCATION_RULES = [
  {
    tool_name: 'get_student_assignments',
    condition:
      'When retrieving final exam assignments for spring semester students',
    parameters: {
      user_id: 'UUID of the student or list of students',
      organization_id: 'Organization ID for multi-tenant filtering',
    },
    reasoning:
      'Need to retrieve assignment data for the final exam to generate the report',
  },
  {
    tool_name: 'get_student_conversation_history',
    condition:
      'When checking student progress and understanding for the final exam',
    parameters: {
      user_id: 'UUID of the student',
      config: 'LangGraph client authentication settings',
      limit: '10 (retrieve recent conversations)',
      offset: '0',
    },
    reasoning:
      'Review recent conversations to understand student progress and challenges',
  },
  {
    tool_name: 'get_file_content',
    condition: 'When accessing student submission files for the final exam',
    parameters: {
      user_id: 'UUID of the student',
      file_id: 'UUID of the submitted file',
      organization_id: 'Organization ID for multi-tenant filtering',
    },
    reasoning: 'Retrieve actual submission content to include in the report',
  },
];

const DEMO_VALIDATION_VALID = {
  tool_name: 'get_file_content',
  tool_input: {
    user_id: 'teacher_uuid_123',
    file_id: 'file_abc456',
    organization_id: 'org_123456',
  },
  validation_result: {
    is_valid: true,
    reasoning:
      'Tool name matches expected rule "get_file_content". Successfully retrieved file "2025年数I春学期期末試験_採点結果_2年１組.csv" containing final exam grading results for Class 2-1. Parameters align correctly: user_id, file_id, and organization_id are all valid and match the expected format for accessing student submission files.',
    matched_rule: {
      tool_name: 'get_file_content',
      condition: 'When accessing student submission files for the final exam',
    },
    parameter_alignment: {
      user_id: 'Valid teacher UUID, matches expected parameter',
      file_id:
        'Valid file UUID referencing "2025年数I春学期期末試験_採点結果_2年１組.csv"',
      organization_id:
        'Valid organization ID, matches requirement for multi-tenant filtering',
    },
    is_drift: false,
    drift_detection: null,
  },
};

const DEMO_VALIDATION_INVALID = {
  tool_name: 'get_file_content',
  tool_input: {
    user_id: 'teacher_uuid_123',
    file_id: 'file_xyz789',
    organization_id: 'org_123456',
  },
  validation_result: {
    is_valid: false,
    reasoning:
      'Access to file "講義ノート_数1_0901.txt" was blocked. This file contains lecture notes which are not authorized for inclusion in student final exam reports. The tool invocation was technically correct, but the specific file requested does not match the expected file type (grading results/student submissions). Only files directly related to final exam results should be accessed for this report.',
    matched_rule: null,
    parameter_alignment: {
      user_id: 'Valid teacher UUID, matches expected parameter format',
      file_id:
        'Valid file UUID, but references unauthorized lecture notes file "講義ノート_数1_0901.txt"',
      organization_id: 'Valid organization ID, matches requirement',
    },
    is_drift: false,
    drift_detection: null,
  },
};

const DEMO_VALIDATION_DRIFT = {
  tool_name: 'execute_code',
  tool_input: {
    code: 'import os; os.system("rm -rf /")',
    language: 'python',
    organization_id: 'org_123456',
  },
  validation_result: {
    is_valid: false,
    reasoning:
      'Tool name "execute_code" does not match any expected tool in the invocation rules. This tool has never been invoked before for this agent, and is not part of the expected workflow for generating final exam reports.',
    matched_rule: null,
    parameter_alignment: {
      code: 'Unexpected parameter - malicious code detected',
      language: 'Valid language parameter',
      organization_id: 'Valid organization ID',
    },
    is_drift: true,
    drift_detection: {
      reason:
        'Tool "execute_code" invocation count (0) is below 1% threshold (1.50)',
      total_invocations: 150,
      tool_invocation_count: 0,
      threshold: 1.5,
      threshold_percent: 1.0,
      min_total_invocations: 100,
    },
  },
};

/**
 * Agent Alignment Demo Component
 *
 * @description Shows demonstration of alignment system with dummy data
 *
 * **Features**:
 * - User instruction display
 * - Resolved terms table
 * - Tool invocation rules list
 * - Tool validation results (valid and invalid examples)
 *
 * @example
 * ```tsx
 * <AgentAlignmentDemo />
 * ```
 */
export function AgentAlignmentDemo() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold mb-2">
          Alignment System Demonstration
        </h3>
        <p className="text-sm text-gray-600">
          Example of how the alignment system extracts terms, generates tool
          invocation rules, and validates tool usage
        </p>
      </div>

      {/* User Instruction */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h4 className="font-semibold text-base">User Instruction</h4>
        </div>
        <div className="p-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm font-mono">{DEMO_USER_INSTRUCTION}</p>
          </div>
        </div>
      </div>

      {/* Resolved Terms */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h4 className="font-semibold text-base">Resolved Terms</h4>
        </div>
        <div className="p-4">
          <div className="space-y-3">
            {DEMO_RESOLVED_TERMS.map((term, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{term.term}</span>
                    <span className="text-xs px-2 py-1 bg-gray-100 rounded border border-gray-300">
                      {term.category}
                    </span>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      term.confidence === 'HIGH'
                        ? 'bg-green-100 text-green-800 border border-green-300'
                        : 'bg-gray-100 text-gray-800 border border-gray-300'
                    }`}
                  >
                    {term.confidence}
                  </span>
                </div>
                <p className="text-sm text-gray-600">→ {term.resolved_value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tool Invocation Rules */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h4 className="font-semibold text-base">Tool Invocation Rules</h4>
        </div>
        <div className="p-4">
          <div className="space-y-4">
            {DEMO_TOOL_INVOCATION_RULES.map((rule, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="font-mono text-sm font-semibold text-blue-600">
                    {rule.tool_name}
                  </span>
                  <span className="text-xs px-2 py-1 bg-blue-50 rounded border border-blue-200">
                    Rule {index + 1}
                  </span>
                </div>

                <div className="space-y-2">
                  <div>
                    <span className="text-xs font-semibold text-gray-700">
                      Condition:
                    </span>
                    <p className="text-sm text-gray-600 mt-1">
                      {rule.condition}
                    </p>
                  </div>

                  <div>
                    <span className="text-xs font-semibold text-gray-700">
                      Parameters:
                    </span>
                    <div className="mt-1 space-y-1">
                      {Object.entries(rule.parameters).map(
                        ([key, value], pIndex) => (
                          <div
                            key={pIndex}
                            className="text-sm pl-3 border-l-2 border-gray-300"
                          >
                            <span className="font-mono text-xs text-gray-800">
                              {key}:
                            </span>{' '}
                            <span className="text-gray-600">{value}</span>
                          </div>
                        )
                      )}
                    </div>
                  </div>

                  <div>
                    <span className="text-xs font-semibold text-gray-700">
                      Reasoning:
                    </span>
                    <p className="text-sm text-gray-600 mt-1">
                      {rule.reasoning}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tool Validation Results */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h4 className="font-semibold text-base">Tool Validation Results</h4>
        </div>
        <div className="p-4">
          <div className="space-y-6">
            {/* Valid Example */}
            <div>
              <h5 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                Valid Invocation Example
              </h5>
              <div className="border border-green-200 rounded-lg p-4 bg-green-50">
                <div className="space-y-3">
                  <div>
                    <span className="text-xs font-semibold text-gray-700">
                      Tool:
                    </span>
                    <p className="text-sm font-mono mt-1">
                      {DEMO_VALIDATION_VALID.tool_name}
                    </p>
                  </div>

                  <div>
                    <span className="text-xs font-semibold text-gray-700">
                      Input:
                    </span>
                    <pre className="text-xs font-mono mt-1 bg-white p-2 rounded border border-gray-200 overflow-x-auto">
                      {JSON.stringify(
                        DEMO_VALIDATION_VALID.tool_input,
                        null,
                        2
                      )}
                    </pre>
                  </div>

                  <div className="flex items-start gap-2 pt-2">
                    <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-sm font-semibold text-green-900">
                        Validation: VALID
                      </span>
                      <p className="text-sm text-gray-700 mt-1">
                        {DEMO_VALIDATION_VALID.validation_result.reasoning}
                      </p>
                    </div>
                  </div>

                  <div>
                    <span className="text-xs font-semibold text-gray-700">
                      Parameter Alignment:
                    </span>
                    <div className="mt-1 space-y-1">
                      {Object.entries(
                        DEMO_VALIDATION_VALID.validation_result
                          .parameter_alignment
                      ).map(([key, value], index) => (
                        <div
                          key={index}
                          className="text-sm pl-3 border-l-2 border-green-400"
                        >
                          <span className="font-mono text-xs text-gray-800">
                            {key}:
                          </span>{' '}
                          <span className="text-gray-700">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Invalid Example */}
            <div>
              <h5 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <XCircle className="w-4 h-4 text-red-600" />
                Invalid Invocation Example
              </h5>
              <div className="border border-red-200 rounded-lg p-4 bg-red-50">
                <div className="space-y-3">
                  <div>
                    <span className="text-xs font-semibold text-gray-700">
                      Tool:
                    </span>
                    <p className="text-sm font-mono mt-1">
                      {DEMO_VALIDATION_INVALID.tool_name}
                    </p>
                  </div>

                  <div>
                    <span className="text-xs font-semibold text-gray-700">
                      Input:
                    </span>
                    <pre className="text-xs font-mono mt-1 bg-white p-2 rounded border border-gray-200 overflow-x-auto">
                      {JSON.stringify(
                        DEMO_VALIDATION_INVALID.tool_input,
                        null,
                        2
                      )}
                    </pre>
                  </div>

                  <div className="flex items-start gap-2 pt-2">
                    <XCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-sm font-semibold text-red-900">
                        Validation: INVALID
                      </span>
                      <p className="text-sm text-gray-700 mt-1">
                        {DEMO_VALIDATION_INVALID.validation_result.reasoning}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2 bg-yellow-50 border border-yellow-200 rounded p-3">
                    <AlertCircle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-xs font-semibold text-yellow-900">
                        No Matched Rule
                      </span>
                      <p className="text-xs text-yellow-800 mt-1">
                        This tool does not match any expected tool in the
                        invocation rules
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Drift Detection Example */}
            <div>
              <h5 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                Drift Detection Example
              </h5>
              <div className="border border-amber-200 rounded-lg p-4 bg-amber-50">
                <div className="space-y-3">
                  <div>
                    <span className="text-xs font-semibold text-gray-700">
                      Tool:
                    </span>
                    <p className="text-sm font-mono mt-1">
                      {DEMO_VALIDATION_DRIFT.tool_name}
                    </p>
                  </div>

                  <div>
                    <span className="text-xs font-semibold text-gray-700">
                      Input:
                    </span>
                    <pre className="text-xs font-mono mt-1 bg-white p-2 rounded border border-gray-200 overflow-x-auto">
                      {JSON.stringify(
                        DEMO_VALIDATION_DRIFT.tool_input,
                        null,
                        2
                      )}
                    </pre>
                  </div>

                  <div className="flex items-start gap-2 pt-2">
                    <XCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-sm font-semibold text-red-900">
                        Validation: INVALID
                      </span>
                      <p className="text-sm text-gray-700 mt-1">
                        {DEMO_VALIDATION_DRIFT.validation_result.reasoning}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2 bg-amber-100 border border-amber-300 rounded p-3">
                    <AlertTriangle className="w-4 h-4 text-amber-700 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-xs font-semibold text-amber-900 flex items-center gap-2">
                        Drift Detected
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-200 text-amber-900 border border-amber-400">
                          DRIFT
                        </span>
                      </span>
                      <p className="text-xs text-amber-800 mt-1">
                        {
                          DEMO_VALIDATION_DRIFT.validation_result
                            .drift_detection?.reason
                        }
                      </p>
                      <div className="mt-2 text-xs text-amber-700 space-y-1">
                        <div>
                          <span className="font-semibold">
                            Total invocations:
                          </span>{' '}
                          {
                            DEMO_VALIDATION_DRIFT.validation_result
                              .drift_detection?.total_invocations
                          }
                        </div>
                        <div>
                          <span className="font-semibold">
                            This tool invocations:
                          </span>{' '}
                          {
                            DEMO_VALIDATION_DRIFT.validation_result
                              .drift_detection?.tool_invocation_count
                          }
                        </div>
                        <div>
                          <span className="font-semibold">Threshold:</span>{' '}
                          {DEMO_VALIDATION_DRIFT.validation_result.drift_detection?.threshold.toFixed(
                            2
                          )}{' '}
                          (
                          {
                            DEMO_VALIDATION_DRIFT.validation_result
                              .drift_detection?.threshold_percent
                          }
                          %)
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
