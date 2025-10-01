/**
 * Dashboard page
 *
 * @description Main dashboard page for authenticated users.
 * Displays dashboard content and primary application interface.
 *
 * @module dashboard-page
 */

/**
 * Dashboard page component
 *
 * @description Renders the main dashboard page.
 * This is a placeholder that will be replaced with actual dashboard content.
 *
 * **Route**: /dashboard
 *
 * **Features**:
 * - Protected by authentication (DashboardLayout)
 * - Main landing page for authenticated users
 * - Will contain widgets, metrics, and navigation
 *
 * @example
 * ```
 * // User logs in and is redirected to /dashboard
 * // Sees this page with dashboard content
 * ```
 */
export default function DashboardPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="text-gray-600 mt-2">
        Welcome to your dashboard. This is a placeholder page.
      </p>
    </div>
  );
}
