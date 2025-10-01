/**
 * Root layout component
 *
 * @description The root layout for the entire application. Provides:
 * - Font configuration (Inter font family)
 * - Global styles
 * - Application-level providers (TanStack Query, Auth context)
 * - HTML structure and metadata
 *
 * This is a Server Component that wraps the application with necessary providers.
 *
 * @module layout
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

/**
 * Inter font configuration
 *
 * @description Configures the Inter font family with:
 * - Latin character subset for optimal bundle size
 * - Swap display strategy for better performance (shows fallback font first)
 * - Fallback fonts for progressive enhancement
 */
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  fallback: ['system-ui', 'arial'],
});

/**
 * Application metadata
 *
 * @description Defines metadata for SEO and browser display.
 * These values are used in the HTML <head> section.
 */
export const metadata: Metadata = {
  title: 'DataGusto v2',
  description: 'Data quality management and guardrail automation platform',
};

/**
 * Root Layout Component
 *
 * @description The root layout that wraps all pages in the application.
 * Provides HTML structure, font styling, and application providers.
 *
 * **Structure**:
 * - html: Sets language attribute for accessibility
 * - body: Applies Inter font and global styles
 * - Providers: Wraps children with TanStack Query and other providers
 *
 * **Server Component**:
 * This is a Server Component by default. The Providers component handles
 * all client-side functionality (React Query, etc.).
 *
 * @param props - Component props
 * @param props.children - Page content to render within the layout
 *
 * @example
 * ```tsx
 * // This layout automatically wraps all pages
 * // No need to import or use directly in page components
 * ```
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
