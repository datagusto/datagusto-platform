/**
 * Error message component
 *
 * @description Reusable error message component for displaying errors.
 * Provides consistent error messaging across the application.
 *
 * **Features**:
 * - Consistent error styling
 * - Support for Error objects and strings
 * - Optional title
 * - Accessible with ARIA attributes
 *
 * @module error-message
 */

/**
 * Error message component props
 *
 * @interface ErrorMessageProps
 */
interface ErrorMessageProps {
  /** Error to display (Error object or string) */
  error: Error | string | null | undefined;
  /** Optional error title (default: "Error") */
  title?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Error message component
 *
 * @description Displays error messages in a consistent format.
 * Handles both Error objects and string messages.
 *
 * @param props - Component props
 * @param props.error - Error to display
 * @param props.title - Error title/heading
 * @param props.className - Additional CSS classes
 *
 * @example
 * ```tsx
 * // Display Error object
 * <ErrorMessage error={error} />
 * ```
 *
 * @example
 * ```tsx
 * // Display string message with custom title
 * <ErrorMessage error="Invalid credentials" title="Login Failed" />
 * ```
 *
 * @example
 * ```tsx
 * // With custom styling
 * <ErrorMessage error={error} className="mt-4" />
 * ```
 */
export function ErrorMessage({
  error,
  title = 'Error',
  className = '',
}: ErrorMessageProps) {
  if (!error) return null;

  const errorMessage =
    typeof error === 'string' ? error : error.message || 'An error occurred';

  return (
    <div
      className={`rounded-md border border-red-200 bg-red-50 p-4 ${className}`}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-red-400"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-800">{title}</h3>
          <div className="mt-2 text-sm text-red-700">
            <p>{errorMessage}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
