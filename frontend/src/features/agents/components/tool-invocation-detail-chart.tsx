/**
 * Tool Invocation Detail Chart Component
 *
 * @description Displays detailed analysis of a specific tool's invocation patterns.
 * Shows daily counts, 7-day moving average, and confidence intervals.
 *
 * @module tool-invocation-detail-chart
 */

'use client';

import {
  ComposedChart,
  Line,
  Bar,
  Area,
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
 * Chart configuration for tool invocation detail analysis
 *
 * @description Defines colors and labels for daily counts, moving average, and confidence intervals
 */
const chartConfig = {
  daily_count: {
    label: 'Daily Count',
    color: 'hsl(var(--chart-1))',
  },
  moving_average: {
    label: '7-Day Moving Average',
    color: 'hsl(var(--chart-2))',
  },
  confidence_upper: {
    label: 'CI Upper (95%)',
    color: 'hsl(var(--chart-3))',
  },
  confidence_lower: {
    label: 'CI Lower (95%)',
    color: 'hsl(var(--chart-3))',
  },
  confidence_range: {
    label: 'Confidence Interval',
    color: 'hsl(var(--chart-3))',
  },
} satisfies ChartConfig;

/**
 * Dummy data for get_user_files tool invocation analysis
 *
 * @description Simulates 14 days of data including:
 * - daily_count: Actual invocations per day
 * - moving_average: 7-day moving average (dummy values from start)
 * - confidence_upper: Upper bound of 95% confidence interval
 * - confidence_lower: Lower bound of 95% confidence interval
 */
const dummyData = [
  {
    date: '10/08',
    daily_count: 4,
    moving_average: 4.5,
    confidence_upper: 6.2,
    confidence_lower: 2.8,
  },
  {
    date: '10/09',
    daily_count: 6,
    moving_average: 4.7,
    confidence_upper: 6.5,
    confidence_lower: 2.9,
  },
  {
    date: '10/10',
    daily_count: 3,
    moving_average: 4.6,
    confidence_upper: 6.4,
    confidence_lower: 2.8,
  },
  {
    date: '10/11',
    daily_count: 5,
    moving_average: 4.7,
    confidence_upper: 6.5,
    confidence_lower: 2.9,
  },
  {
    date: '10/12',
    daily_count: 7,
    moving_average: 4.9,
    confidence_upper: 6.7,
    confidence_lower: 3.1,
  },
  {
    date: '10/13',
    daily_count: 4,
    moving_average: 4.9,
    confidence_upper: 6.7,
    confidence_lower: 3.1,
  },
  {
    date: '10/14',
    daily_count: 6,
    moving_average: 5.0,
    confidence_upper: 6.8,
    confidence_lower: 3.2,
  },
  {
    date: '10/15',
    daily_count: 5,
    moving_average: 5.1,
    confidence_upper: 7.0,
    confidence_lower: 3.2,
  },
  {
    date: '10/16',
    daily_count: 8,
    moving_average: 5.6,
    confidence_upper: 7.5,
    confidence_lower: 3.7,
  },
  {
    date: '10/17',
    daily_count: 7,
    moving_average: 6.0,
    confidence_upper: 7.8,
    confidence_lower: 4.2,
  },
  {
    date: '10/18',
    daily_count: 4,
    moving_average: 5.9,
    confidence_upper: 7.6,
    confidence_lower: 4.2,
  },
  {
    date: '10/19',
    daily_count: 11,
    moving_average: 6.4,
    confidence_upper: 8.5,
    confidence_lower: 4.3,
  },
  {
    date: '10/20',
    daily_count: 6,
    moving_average: 6.7,
    confidence_upper: 8.9,
    confidence_lower: 4.5,
  },
  {
    date: '10/21',
    daily_count: 8,
    moving_average: 7.0,
    confidence_upper: 9.2,
    confidence_lower: 4.8,
  },
];

/**
 * Tool Invocation Detail Chart Component Props
 *
 * @interface ToolInvocationDetailChartProps
 */
interface ToolInvocationDetailChartProps {
  /** Tool name to display in the chart title */
  toolName?: string;
}

/**
 * Tool Invocation Detail Chart Component
 *
 * @description Renders a composed chart showing detailed analysis of tool invocations:
 * - Bar chart for daily invocation counts
 * - Line chart for 7-day moving average
 * - Shaded area for 95% confidence interval
 *
 * **Statistical Features**:
 * - Moving average smooths out daily variations
 * - Confidence interval shows statistical uncertainty
 * - Helps identify trends and anomalies
 *
 * **Visual Elements**:
 * - Bars: Daily actual counts (blue)
 * - Line: 7-day moving average (teal)
 * - Shaded area: 95% confidence interval (light teal)
 *
 * @param props - Component props
 * @param props.toolName - Name of the tool being analyzed (default: "get_user_files")
 *
 * @example
 * ```tsx
 * <ToolInvocationDetailChart toolName="get_user_files" />
 * ```
 */
export function ToolInvocationDetailChart({
  toolName = 'get_user_files',
}: ToolInvocationDetailChartProps) {
  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-base font-medium">
          Detailed Analysis:{' '}
          <code className="text-sm bg-gray-100 px-2 py-1 rounded">
            {toolName}
          </code>
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Daily invocations with 7-day moving average and 95% confidence
          interval
        </p>
      </div>

      <ChartContainer config={chartConfig} className="h-[400px] w-full">
        <ComposedChart
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
            label={{
              value: 'Invocations',
              angle: -90,
              position: 'insideLeft',
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

          {/* Confidence Interval Area (shaded region between upper and lower bounds) */}
          <Area
            type="monotone"
            dataKey="confidence_upper"
            stroke="none"
            fill="var(--color-confidence_range)"
            fillOpacity={0.2}
            connectNulls
            baseLine={0}
          />
          <Area
            type="monotone"
            dataKey="confidence_lower"
            stroke="none"
            fill="#ffffff"
            fillOpacity={1}
            connectNulls
            baseLine={0}
          />

          {/* Daily Count Bars */}
          <Bar
            dataKey="daily_count"
            fill="var(--color-daily_count)"
            radius={[4, 4, 0, 0]}
            maxBarSize={50}
          />

          {/* Confidence Interval Bounds (dashed lines) */}
          <Line
            type="monotone"
            dataKey="confidence_upper"
            stroke="var(--color-confidence_upper)"
            strokeWidth={1.5}
            strokeDasharray="5 5"
            dot={false}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="confidence_lower"
            stroke="var(--color-confidence_lower)"
            strokeWidth={1.5}
            strokeDasharray="5 5"
            dot={false}
            connectNulls
          />

          {/* Moving Average Line */}
          <Line
            type="monotone"
            dataKey="moving_average"
            stroke="var(--color-moving_average)"
            strokeWidth={3}
            dot={false}
            connectNulls
          />
        </ComposedChart>
      </ChartContainer>

      {/* Statistics Summary */}
      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-gray-600 text-xs">Average (7-day)</div>
          <div className="text-lg font-semibold mt-1">7.0</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-gray-600 text-xs">Peak Daily Count</div>
          <div className="text-lg font-semibold mt-1">11</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-gray-600 text-xs">Total (14 days)</div>
          <div className="text-lg font-semibold mt-1">90</div>
        </div>
      </div>
    </div>
  );
}
