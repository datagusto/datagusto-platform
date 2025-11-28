/**
 * Utility functions for common operations
 *
 * @description Provides helper functions for className merging, string manipulation, etc.
 *
 * @example
 * ```typescript
 * import { cn } from '@/shared/lib';
 *
 * const className = cn('base-class', condition && 'conditional-class', 'another-class');
 * ```
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merges multiple className values using clsx and tailwind-merge
 *
 * @description Combines multiple className values intelligently, handling conditional classes
 * and merging Tailwind CSS classes to avoid conflicts.
 *
 * @param inputs - Array of className values (strings, objects, arrays, etc.)
 * @returns Merged className string
 *
 * @example
 * ```typescript
 * // Basic usage
 * cn('px-4', 'py-2') // => 'px-4 py-2'
 *
 * // Conditional classes
 * cn('base', isActive && 'active') // => 'base active' (if isActive is true)
 *
 * // Tailwind merge (prevents conflicts)
 * cn('px-2', 'px-4') // => 'px-4' (px-4 overrides px-2)
 * ```
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
