/**
 * Dummy dashboard page
 *
 * @description Placeholder page for testing and development purposes.
 * Uses the same dashboard layout as other pages.
 *
 * @module dummy-dashboard-page
 */

'use client';

import {
  ToolInvocationTrendChart,
  ToolInvocationDetailChart,
  ToolInvocationBreakdownChart,
  BlockedValidationDemo,
  ToolInvocationRatioChart,
} from '@/features/agents/components';

/**
 * Dummy dashboard page component
 *
 * @description Demo page showing tool invocation trend chart.
 * Automatically inherits dashboard layout with navigation menu.
 *
 * **Route**: /dummy/dashboard
 *
 * **Features**:
 * - Uses (dashboard) layout group for consistent styling
 * - Displays tool invocation trend chart with dummy data
 * - Protected by authentication (DashboardLayout)
 *
 * @example
 * ```
 * // User navigates to /dummy/dashboard
 * // Sees page with tool invocation trend visualization
 * ```
 */
export default function DummyDashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Dummy Dashboard</h1>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Tool Invocation Trend Chart */}
        <section>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">
              Tool Invocation Trends
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              Daily trend of tool invocations over the past week
            </p>
            <ToolInvocationTrendChart />
          </div>
        </section>

        {/* Tool Invocation Detail Chart */}
        <section>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <ToolInvocationDetailChart toolName="get_user_files" />
          </div>
        </section>

        {/* Tool Invocation Breakdown Chart */}
        <section>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <ToolInvocationBreakdownChart toolName="get_user_files" />
          </div>
        </section>

        {/* Tool Invocation Ratio Chart */}
        <section>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <ToolInvocationRatioChart toolName="get_user_files" />
          </div>
        </section>

        {/* Blocked Validation Examples */}
        <section>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <BlockedValidationDemo />
          </div>
        </section>

        {/* Placeholder for future content */}
        <section>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <p className="text-gray-600">
              Additional dashboard content can be added here.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
