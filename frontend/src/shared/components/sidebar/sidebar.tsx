'use client';

import Link from 'next/link';
import { usePathname, useParams } from 'next/navigation';
import { useAuthStore } from '@/features/auth/stores';
import { UserMenu } from './user-menu';

export function Sidebar() {
  const pathname = usePathname();
  const params = useParams();
  const currentOrganizationId = useAuthStore((state) => state.currentOrganizationId);

  // Check if we're on a project detail page
  const projectId = params?.projectId as string | undefined;
  const isProjectPage = pathname.startsWith('/projects/') && projectId;

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen">
      {/* Logo */}
      <div className="p-6">
        <Link href="/dashboard" className="text-xl font-bold text-gray-900">
          datagusto
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {isProjectPage ? (
          <>
            {/* Back to Projects link */}
            <Link
              href={currentOrganizationId ? `/organizations/${currentOrganizationId}` : '/select-organization'}
              className="flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-gray-600 hover:bg-gray-50 mb-4"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
              <span className="font-medium">Back to Projects</span>
            </Link>

            {/* Divider */}
            <div className="border-t border-gray-200 my-2"></div>

            {/* Project-specific navigation */}
            <Link
              href={`/projects/${projectId}/agents`}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                pathname.includes('/agents')
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <span className="font-medium">Agents</span>
            </Link>

            <Link
              href={`/projects/${projectId}/guardrails`}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                pathname.includes('/guardrails')
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
              <span className="font-medium">Guardrails</span>
            </Link>

            <Link
              href={`/projects/${projectId}/traces`}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                pathname.includes('/traces')
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <span className="font-medium">Traces</span>
            </Link>
          </>
        ) : (
          <>
            {/* Global navigation */}
            <Link
              href="/projects"
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                pathname.startsWith('/projects') || pathname.startsWith('/organizations')
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                />
              </svg>
              <span className="font-medium">Projects</span>
            </Link>
          </>
        )}
      </nav>

      {/* User Menu at bottom */}
      <div className="p-4 border-t border-gray-200">
        <UserMenu />
      </div>
    </aside>
  );
}