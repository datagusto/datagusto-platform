/**
 * Tool Invocation Breakdown Chart Component
 *
 * @description Displays a breakdown of tool invocations by approval status.
 * Shows daily counts split into Auto Approved and Blocked categories.
 *
 * @module tool-invocation-breakdown-chart
 */

'use client';

import {
  BarChart,
  Bar,
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
 * Chart configuration for tool invocation breakdown
 *
 * @description Defines colors and labels for Auto Approved and Blocked statuses
 */
const chartConfig = {
  auto_approved: {
    label: 'Auto Approved',
    color: 'hsl(142, 76%, 36%)', // Green
  },
  blocked: {
    label: 'Blocked',
    color: 'hsl(0, 84%, 60%)', // Red
  },
} satisfies ChartConfig;

/**
 * Dummy data for tool invocation breakdown
 *
 * @description Simulates 14 days of data showing:
 * - auto_approved: Number of automatically approved invocations
 * - blocked: Number of blocked invocations
 * - total: Total invocations per day
 */
const dummyData = [
  {
    date: '10/08',
    auto_approved: 3,
    blocked: 1,
  },
  {
    date: '10/09',
    auto_approved: 5,
    blocked: 1,
  },
  {
    date: '10/10',
    auto_approved: 2,
    blocked: 1,
  },
  {
    date: '10/11',
    auto_approved: 4,
    blocked: 1,
  },
  {
    date: '10/12',
    auto_approved: 5,
    blocked: 2,
  },
  {
    date: '10/13',
    auto_approved: 3,
    blocked: 1,
  },
  {
    date: '10/14',
    auto_approved: 5,
    blocked: 1,
  },
  {
    date: '10/15',
    auto_approved: 3,
    blocked: 2,
  },
  {
    date: '10/16',
    auto_approved: 6,
    blocked: 2,
  },
  {
    date: '10/17',
    auto_approved: 5,
    blocked: 2,
  },
  {
    date: '10/18',
    auto_approved: 2,
    blocked: 2,
  },
  {
    date: '10/19',
    auto_approved: 8,
    blocked: 3,
  },
  {
    date: '10/20',
    auto_approved: 4,
    blocked: 2,
  },
  {
    date: '10/21',
    auto_approved: 6,
    blocked: 2,
  },
];

/**
 * Tool Invocation Breakdown Chart Component Props
 *
 * @interface ToolInvocationBreakdownChartProps
 */
interface ToolInvocationBreakdownChartProps {
  /** Tool name to display in the chart title */
  toolName?: string;
}

/**
 * Tool Invocation Breakdown Chart Component
 *
 * @description Renders a stacked bar chart showing the breakdown of tool invocations
 * by approval status (Auto Approved vs Blocked).
 *
 * **Visual Elements**:
 * - Green bars: Auto Approved invocations
 * - Red bars: Blocked invocations
 * - Stacked to show total daily volume
 *
 * **Use Cases**:
 * - Monitor approval/blocking patterns
 * - Identify days with high blocking rates
 * - Track guardrail effectiveness
 *
 * @param props - Component props
 * @param props.toolName - Name of the tool being analyzed (default: "get_user_files")
 *
 * @example
 * ```tsx
 * <ToolInvocationBreakdownChart toolName="get_user_files" />
 * ```
 */
export function ToolInvocationBreakdownChart({
  toolName = 'get_user_files',
}: ToolInvocationBreakdownChartProps) {
  // Calculate totals for summary statistics
  const totalApproved = dummyData.reduce(
    (sum, day) => sum + day.auto_approved,
    0
  );
  const totalBlocked = dummyData.reduce((sum, day) => sum + day.blocked, 0);
  const totalInvocations = totalApproved + totalBlocked;
  const approvalRate = ((totalApproved / totalInvocations) * 100).toFixed(1);
  const blockRate = ((totalBlocked / totalInvocations) * 100).toFixed(1);

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-base font-medium">
          Approval Status Breakdown:{' '}
          <code className="text-sm bg-gray-100 px-2 py-1 rounded">
            {toolName}
          </code>
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Daily invocations split by Auto Approved and Blocked status
        </p>
      </div>

      <ChartContainer config={chartConfig} className="h-[400px] w-full">
        <BarChart
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

          {/* Stacked Bars */}
          <Bar
            dataKey="auto_approved"
            stackId="status"
            fill="var(--color-auto_approved)"
            radius={[0, 0, 0, 0]}
            maxBarSize={50}
          />
          <Bar
            dataKey="blocked"
            stackId="status"
            fill="var(--color-blocked)"
            radius={[4, 4, 0, 0]}
            maxBarSize={50}
          />
        </BarChart>
      </ChartContainer>

      {/* Statistics Summary */}
      <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-gray-600 text-xs">Total Invocations</div>
          <div className="text-lg font-semibold mt-1">{totalInvocations}</div>
        </div>
        <div className="bg-green-50 rounded-lg p-3">
          <div className="text-green-700 text-xs">Auto Approved</div>
          <div className="text-lg font-semibold mt-1 text-green-700">
            {totalApproved}
          </div>
          <div className="text-xs text-green-600 mt-1">{approvalRate}%</div>
        </div>
        <div className="bg-red-50 rounded-lg p-3">
          <div className="text-red-700 text-xs">Blocked</div>
          <div className="text-lg font-semibold mt-1 text-red-700">
            {totalBlocked}
          </div>
          <div className="text-xs text-red-600 mt-1">{blockRate}%</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-gray-600 text-xs">Avg per Day</div>
          <div className="text-lg font-semibold mt-1">
            {(totalInvocations / dummyData.length).toFixed(1)}
          </div>
        </div>
      </div>
    </div>
  );
}
