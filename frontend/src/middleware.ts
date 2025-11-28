/**
 * Next.js Middleware
 *
 * @description Middleware for handling route-level logic before requests reach pages.
 * Currently configured for future authentication enhancements.
 *
 * **Current Limitations**:
 * - localStorage-based auth cannot be accessed in middleware (server-side)
 * - Authentication checks are handled client-side in layout components
 *
 * **Future Enhancements** (when migrating to HttpOnly cookies):
 * - Server-side authentication verification
 * - Automatic redirects for protected routes
 * - Token refresh handling
 *
 * @module middleware
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Protected routes that require authentication
 *
 * @description List of route patterns that should be protected.
 * Currently not enforced in middleware due to localStorage limitations.
 *
 * **Future Use**:
 * When HttpOnly cookies are implemented, middleware will check authentication
 * and redirect unauthenticated users to /sign-in automatically.
 */
const protectedRoutes: string[] = [];

/**
 * Middleware function
 *
 * @description Executes before requests reach pages.
 * Currently passes through all requests due to localStorage auth limitations.
 *
 * **Current Behavior**:
 * - Passes all requests through without blocking
 * - Authentication is handled client-side by layout components
 *
 * **Why Not Enforce Auth Here?**:
 * - localStorage is only accessible on client-side (browser)
 * - Middleware runs on server-side (cannot read localStorage)
 * - Client-side layout components handle auth checks and redirects
 *
 * **Future Implementation** (with HttpOnly cookies):
 * ```typescript
 * const token = request.cookies.get('access_token');
 * if (isProtectedRoute && !token) {
 *   return NextResponse.redirect(new URL('/sign-in', request.url));
 * }
 * ```
 *
 * @param request - Next.js request object
 * @returns Next.js response (currently always NextResponse.next())
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if current path is a protected route
  const _isProtectedRoute = protectedRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );

  // TODO: When migrating to HttpOnly cookies, implement server-side auth check here:
  // const token = request.cookies.get('access_token');
  // if (isProtectedRoute && !token) {
  //   return NextResponse.redirect(new URL('/sign-in', request.url));
  // }

  // Currently: Pass through all requests
  // Authentication is handled client-side by layout components
  return NextResponse.next();
}

/**
 * Middleware configuration
 *
 * @description Specifies which routes should trigger the middleware.
 *
 * **Current Matcher**:
 * - `/` - Root page
 * - `/sign-in` - Sign-in page
 * - `/sign-up` - Sign-up page
 *
 * **Why Include Auth Pages?**:
 * - Future: Redirect already-authenticated users away from auth pages
 * - Currently: No-op, but prepared for future enhancement
 */
export const config = {
  matcher: ['/', '/sign-in', '/sign-up'],
};
