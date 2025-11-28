/**
 * Tool Invocation Ratio Statistics Component
 *
 * @description Displays statistics about the ratio of tool invocations to user inputs.
 * Shows aggregated statistics and time-series visualization.
 *
 * @module tool-invocation-ratio-chart
 */

'use client';

import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from '@/components/ui/chart';
import type { ChartConfig } from '@/components/ui/chart';

/**
 * Chart configuration for tool invocation ratio
 */
const chartConfig = {
  user_inputs: {
    label: 'User Inputs',
    color: 'hsl(var(--chart-1))',
  },
  tool_invocations: {
    label: 'Tool Invocations',
    color: 'hsl(var(--chart-2))',
  },
  ratio: {
    label: 'Invocation Ratio (%)',
    color: 'hsl(var(--chart-4))',
  },
} satisfies ChartConfig;

/**
 * Dummy data for tool invocation ratio analysis
 *
 * @description Simulates 14 days of data including:
 * - user_inputs: Number of user inputs per day
 * - tool_invocations: Number of get_user_files invocations per day
 * - ratio: Percentage ratio (tool_invocations / user_inputs * 100)
 *
 * Note: Ratio is kept at 10% or below (10 invocations per 100 user inputs)
 * to demonstrate typical usage patterns for blocking cases explanation.
 */
const dummyData = [
  {
    date: '10/08',
    user_inputs: 45,
    tool_invocations: 4,
    ratio: 8.9,
  },
  {
    date: '10/09',
    user_inputs: 52,
    tool_invocations: 5,
    ratio: 9.6,
  },
  {
    date: '10/10',
    user_inputs: 38,
    tool_invocations: 3,
    ratio: 7.9,
  },
  {
    date: '10/11',
    user_inputs: 48,
    tool_invocations: 4,
    ratio: 8.3,
  },
  {
    date: '10/12',
    user_inputs: 55,
    tool_invocations: 5,
    ratio: 9.1,
  },
  {
    date: '10/13',
    user_inputs: 42,
    tool_invocations: 4,
    ratio: 9.5,
  },
  {
    date: '10/14',
    user_inputs: 50,
    tool_invocations: 5,
    ratio: 10.0,
  },
  {
    date: '10/15',
    user_inputs: 47,
    tool_invocations: 4,
    ratio: 8.5,
  },
  {
    date: '10/16',
    user_inputs: 60,
    tool_invocations: 6,
    ratio: 10.0,
  },
  {
    date: '10/17',
    user_inputs: 53,
    tool_invocations: 5,
    ratio: 9.4,
  },
  {
    date: '10/18',
    user_inputs: 44,
    tool_invocations: 4,
    ratio: 9.1,
  },
  {
    date: '10/19',
    user_inputs: 58,
    tool_invocations: 5,
    ratio: 8.6,
  },
  {
    date: '10/20',
    user_inputs: 51,
    tool_invocations: 5,
    ratio: 9.8,
  },
  {
    date: '10/21',
    user_inputs: 56,
    tool_invocations: 5,
    ratio: 8.9,
  },
];

/**
 * Dummy statistics for past 7 days
 */
const past7DaysStats = {
  total_user_inputs: 349,
  total_tool_invocations: 33,
  invocations_per_100_inputs: 9.5,
};

/**
 * Tool Invocation Ratio Chart Component Props
 *
 * @interface ToolInvocationRatioChartProps
 */
interface ToolInvocationRatioChartProps {
  /** Tool name to display in the chart title */
  toolName?: string;
}

/**
 * Tool Invocation Ratio Statistics Component
 *
 * @description Displays aggregated statistics and time-series visualization
 * for tool invocations relative to user inputs.
 *
 * **Key Metrics**:
 * - Invocations per 100 user inputs (normalized ratio)
 * - Total user inputs in past 7 days
 * - Total tool invocations in past 7 days
 * - Daily trend chart
 *
 * @param props - Component props
 * @param props.toolName - Name of the tool being analyzed (default: "get_user_files")
 *
 * @example
 * ```tsx
 * <ToolInvocationRatioChart toolName="get_user_files" />
 * ```
 */
export function ToolInvocationRatioChart({
  toolName = 'get_user_files',
}: ToolInvocationRatioChartProps) {
  return (
    <div className="w-full space-y-6">
      <div className="mb-6">
        <h3 className="text-base font-medium">
          Invocation Ratio Statistics:{' '}
          <code className="text-sm bg-gray-100 px-2 py-1 rounded">
            {toolName}
          </code>
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Past 7 days aggregated statistics and trend
        </p>
      </div>

      {/* Main Metric - Large Display */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-8 border-2 border-blue-200">
        <div className="text-center">
          <p className="text-sm text-gray-600 mb-2">
            Invocations per 100 Similar User Inputs
          </p>
          <div className="text-6xl font-bold text-blue-600 mb-2">
            {past7DaysStats.invocations_per_100_inputs.toFixed(1)}
          </div>
          <p className="text-sm text-gray-500">
            calls per 100 inputs (≤ 10 is typical)
          </p>
        </div>
      </div>

      {/* Supporting Statistics */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="text-gray-600 text-xs mb-1">
            Total User Inputs (7d)
          </div>
          <div className="text-2xl font-semibold text-gray-900">
            {past7DaysStats.total_user_inputs.toLocaleString()}
          </div>
          <p className="text-xs text-gray-500 mt-1">Similar user inputs</p>
        </div>
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="text-gray-600 text-xs mb-1">
            Total Invocations (7d)
          </div>
          <div className="text-2xl font-semibold text-gray-900">
            {past7DaysStats.total_tool_invocations.toLocaleString()}
          </div>
          <p className="text-xs text-gray-500 mt-1">Tool calls made</p>
        </div>
      </div>

      {/* Time Series Chart */}
      <div>
        <h4 className="text-sm font-medium mb-3">Daily Trend (14 days)</h4>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <ComposedChart
            data={dummyData}
            margin={{
              top: 5,
              right: 60,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
              className="text-xs"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <YAxis
              yAxisId="left"
              className="text-xs"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
              label={{
                value: 'Count',
                angle: -90,
                position: 'insideLeft',
                style: {
                  textAnchor: 'middle',
                  fill: 'hsl(var(--muted-foreground))',
                },
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              className="text-xs"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
              domain={[0, 15]}
              label={{
                value: 'Ratio (%)',
                angle: 90,
                position: 'insideRight',
                style: {
                  textAnchor: 'middle',
                  fill: 'hsl(var(--muted-foreground))',
                },
              }}
            />
            <ChartTooltip
              content={<ChartTooltipContent />}
              cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }}
            />
            <ChartLegend content={<ChartLegendContent />} />

            {/* User Inputs Bar */}
            <Bar
              yAxisId="left"
              dataKey="user_inputs"
              fill="var(--color-user_inputs)"
              radius={[4, 4, 0, 0]}
              maxBarSize={30}
            />

            {/* Tool Invocations Bar */}
            <Bar
              yAxisId="left"
              dataKey="tool_invocations"
              fill="var(--color-tool_invocations)"
              radius={[4, 4, 0, 0]}
              maxBarSize={30}
            />

            {/* Ratio Line */}
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="ratio"
              stroke="var(--color-ratio)"
              strokeWidth={3}
              dot={{ fill: 'var(--color-ratio)', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </ComposedChart>
        </ChartContainer>
      </div>

      {/* Explanation Note */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-xs text-yellow-800">
          <strong>Note:</strong> For similar user inputs, this tool is typically
          invoked 10 times or less per 100 inputs. Significantly higher rates
          may indicate parameter misalignment or unexpected usage patterns.
        </p>
      </div>
    </div>
  );
}
