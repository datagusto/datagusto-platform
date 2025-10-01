/**
 * Authentication layout component
 *
 * @description Layout wrapper for authentication pages (sign-in, sign-up).
 * Provides consistent styling and structure for auth-related pages.
 *
 * **Features**:
 * - Centered content layout
 * - Gray background for visual distinction
 * - Responsive design
 * - Consistent spacing
 *
 * @module auth-layout
 */

/**
 * AuthLayout component props
 *
 * @interface AuthLayoutProps
 */
interface AuthLayoutProps {
  /** Child components to render within the layout */
  children: React.ReactNode;
}

/**
 * Authentication layout component
 *
 * @description Wraps authentication pages with centered layout and gray background.
 * Used for sign-in, sign-up, forgot password, and other auth-related pages.
 *
 * **Visual Design**:
 * - Full viewport height (min-h-screen)
 * - Gray background (bg-gray-50)
 * - Vertically centered content
 * - Horizontal padding for mobile responsiveness
 *
 * **Usage**:
 * This component is typically used in layout.tsx files within auth route groups.
 * It provides the visual structure while child components contain the actual forms.
 *
 * @param props - Component props
 * @param props.children - Page content to display (forms, messages, etc.)
 *
 * @example
 * ```tsx
 * // In app/(auth)/layout.tsx
 * import { AuthLayout } from '@/shared/components/layouts';
 *
 * export default function Layout({ children }) {
 *   return <AuthLayout>{children}</AuthLayout>;
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Resulting structure for sign-in page
 * <AuthLayout>
 *   <div>
 *     <h1>Sign In</h1>
 *     <SignInForm />
 *   </div>
 * </AuthLayout>
 * ```
 *
 * @example
 * ```tsx
 * // Custom wrapper with additional content
 * <AuthLayout>
 *   <div className="w-full max-w-md">
 *     <div className="mb-8 text-center">
 *       <Logo />
 *       <h1 className="text-2xl font-bold">Welcome Back</h1>
 *     </div>
 *     <SignInForm />
 *   </div>
 * </AuthLayout>
 * ```
 */
export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center">
      {children}
    </div>
  );
}
