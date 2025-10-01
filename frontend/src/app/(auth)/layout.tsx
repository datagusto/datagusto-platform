/**
 * Authentication route group layout
 *
 * @description Layout for authentication pages (sign-in, sign-up).
 * Uses AuthLayout component for consistent styling.
 *
 * @module auth-layout
 */

import { AuthLayout } from '@/shared/components/layouts';

/**
 * Auth route group layout props
 *
 * @interface AuthRouteLayoutProps
 */
interface AuthRouteLayoutProps {
  /** Child pages to render */
  children: React.ReactNode;
}

/**
 * Auth route group layout
 *
 * @description Wraps all pages in the (auth) route group with AuthLayout.
 * Provides consistent visual structure for sign-in, sign-up, etc.
 *
 * @param props - Component props
 * @param props.children - Child page content
 *
 * @example
 * ```
 * // This layout wraps:
 * // - /sign-in (app/(auth)/sign-in/page.tsx)
 * // - /sign-up (app/(auth)/sign-up/page.tsx)
 * ```
 */
export default function AuthRouteLayout({ children }: AuthRouteLayoutProps) {
  return <AuthLayout>{children}</AuthLayout>;
}
