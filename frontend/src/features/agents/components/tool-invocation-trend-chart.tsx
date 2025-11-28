/**
 * Tool Invocation Trend Chart Component
 *
 * @description Displays a line chart showing the trend of tool invocations over time.
 * Shows daily invocation counts for each tool type.
 *
 * @module tool-invocation-trend-chart
 */

'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
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
 * Chart configuration for tool invocation trends
 *
 * @description Defines colors and labels for each tool type in the chart
 */
const chartConfig = {
  get_user_files: {
    label: 'get_user_files',
    color: 'hsl(var(--chart-1))',
  },
  get_file_content: {
    label: 'get_file_content',
    color: 'hsl(var(--chart-2))',
  },
  get_student_assignments: {
    label: 'get_student_assignments',
    color: 'hsl(var(--chart-3))',
  },
  analysis_and_report: {
    label: 'analysis_and_report',
    color: 'hsl(var(--chart-4))',
  },
} satisfies ChartConfig;

/**
 * Dummy data for tool invocation trends
 *
 * @description Simulates 7 days of tool invocation data for demonstration
 */
const dummyData = [
  {
    date: '10/15',
    get_user_files: 5,
    get_file_content: 2,
    get_student_assignments: 1,
    analysis_and_report: 0,
  },
  {
    date: '10/16',
    get_user_files: 3,
    get_file_content: 4,
    get_student_assignments: 2,
    analysis_and_report: 1,
  },
  {
    date: '10/17',
    get_user_files: 7,
    get_file_content: 3,
    get_student_assignments: 1,
    analysis_and_report: 0,
  },
  {
    date: '10/18',
    get_user_files: 4,
    get_file_content: 5,
    get_student_assignments: 3,
    analysis_and_report: 2,
  },
  {
    date: '10/19',
    get_user_files: 11,
    get_file_content: 5,
    get_student_assignments: 0,
    analysis_and_report: 4,
  },
  {
    date: '10/20',
    get_user_files: 6,
    get_file_content: 3,
    get_student_assignments: 2,
    analysis_and_report: 1,
  },
  {
    date: '10/21',
    get_user_files: 8,
    get_file_content: 4,
    get_student_assignments: 1,
    analysis_and_report: 2,
  },
];

/**
 * Tool Invocation Trend Chart Component
 *
 * @description Renders a line chart showing tool invocation trends over time.
 * Uses recharts library with shadcn/ui chart components for consistent styling.
 *
 * **Features**:
 * - Multi-line chart showing different tool types
 * - Interactive tooltips showing exact values
 * - Legend for tool identification
 * - Responsive design
 * - Color-coded lines for each tool
 *
 * **Data Structure**:
 * - X-axis: Date (MM/DD format)
 * - Y-axis: Number of invocations
 * - Lines: One per tool type
 *
 * @example
 * ```tsx
 * <ToolInvocationTrendChart />
 * ```
 */
export function ToolInvocationTrendChart() {
  return (
    <div className="w-full">
      <ChartContainer config={chartConfig} className="h-[400px] w-full">
        <LineChart
          data={dummyData}
          margin={{
            top: 5,
            right: 30,
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
            className="text-xs"
            tick={{ fill: 'hsl(var(--muted-foreground))' }}
          />
          <ChartTooltip content={<ChartTooltipContent />} />
          <ChartLegend content={<ChartLegendContent />} />
          <Line
            type="monotone"
            dataKey="get_user_files"
            stroke="var(--color-get_user_files)"
            strokeWidth={2}
            dot={{ fill: 'var(--color-get_user_files)' }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="get_file_content"
            stroke="var(--color-get_file_content)"
            strokeWidth={2}
            dot={{ fill: 'var(--color-get_file_content)' }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="get_student_assignments"
            stroke="var(--color-get_student_assignments)"
            strokeWidth={2}
            dot={{ fill: 'var(--color-get_student_assignments)' }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="analysis_and_report"
            stroke="var(--color-analysis_and_report)"
            strokeWidth={2}
            dot={{ fill: 'var(--color-analysis_and_report)' }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ChartContainer>
    </div>
  );
}
