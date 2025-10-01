/**
 * Dashboard route group layout
 *
 * @description Layout for dashboard pages (main app pages after authentication).
 * Uses DashboardLayout component for authentication check and consistent styling.
 *
 * @module dashboard-layout
 */

import { DashboardLayout } from '@/shared/components/layouts';

/**
 * Dashboard route group layout props
 *
 * @interface DashboardRouteLayoutProps
 */
interface DashboardRouteLayoutProps {
  /** Child pages to render */
  children: React.ReactNode;
}

/**
 * Dashboard route group layout
 *
 * @description Wraps all pages in the (dashboard) route group with DashboardLayout.
 * Provides authentication check and consistent visual structure for dashboard pages.
 *
 * @param props - Component props
 * @param props.children - Child page content
 *
 * @example
 * ```
 * // This layout wraps:
 * // - /dashboard (app/(dashboard)/dashboard/page.tsx)
 * // - Any future dashboard sub-pages
 * ```
 */
export default function DashboardRouteLayout({
  children,
}: DashboardRouteLayoutProps) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
