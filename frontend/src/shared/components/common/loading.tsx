/**
 * Loading component
 *
 * @description Reusable loading spinner component for displaying loading states.
 * Provides a consistent loading experience across the application.
 *
 * **Features**:
 * - Centered layout with full height
 * - Customizable message
 * - Responsive design
 * - Accessible with ARIA attributes
 *
 * @module loading
 */

/**
 * Loading component props
 *
 * @interface LoadingProps
 */
interface LoadingProps {
  /** Loading message to display (default: "Loading...") */
  message?: string;
  /** Whether to use full screen height (default: true) */
  fullScreen?: boolean;
}

/**
 * Loading component
 *
 * @description Displays a loading spinner with optional message.
 * Can be used in full-screen mode or inline.
 *
 * @param props - Component props
 * @param props.message - Loading message text
 * @param props.fullScreen - Use full viewport height
 *
 * @example
 * ```tsx
 * // Full screen loading
 * <Loading />
 * ```
 *
 * @example
 * ```tsx
 * // Custom message
 * <Loading message="Fetching data..." />
 * ```
 *
 * @example
 * ```tsx
 * // Inline loading (not full screen)
 * <Loading message="Processing..." fullScreen={false} />
 * ```
 */
export function Loading({
  message = 'Loading...',
  fullScreen = true,
}: LoadingProps) {
  return (
    <div
      className={`flex items-center justify-center ${fullScreen ? 'min-h-screen' : 'py-8'}`}
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      <div className="text-gray-500">{message}</div>
    </div>
  );
}
