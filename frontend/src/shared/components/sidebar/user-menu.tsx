'use client';

import { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '@/features/auth/stores';
import { useSwitchOrganization } from '@/features/auth/hooks/use-switch-organization';
import { useRouter } from 'next/navigation';

export function UserMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const router = useRouter();

  // Fetch organizations and current organization
  const {
    organizations,
    currentOrganization,
    isLoading: isLoadingOrganizations,
    switchOrganization,
  } = useSwitchOrganization();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleLogout = () => {
    clearAuth();
    router.push('/sign-in');
  };

  if (!user) return null;

  const initials = user.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : user.email[0].toUpperCase();

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 w-full p-3 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <div className="w-8 h-8 rounded-full bg-gray-800 text-white flex items-center justify-center text-sm font-medium">
          {initials}
        </div>
        <div className="flex-1 text-left">
          <div className="text-sm font-medium text-gray-900">{user.name || 'User'}</div>
          {currentOrganization && (
            <div className="text-xs text-gray-500">{currentOrganization.name}</div>
          )}
        </div>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-white rounded-lg shadow-lg border border-gray-200 py-2">
          <div className="px-4 py-2 border-b border-gray-100">
            <div className="text-xs text-gray-500">{user.email}</div>
          </div>

          <div className="px-2 py-1">
            <button
              className="flex items-center gap-3 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded transition-colors"
              onClick={() => {
                setIsOpen(false);
              }}
            >
              <div className="w-8 h-8 rounded-full bg-gray-800 text-white flex items-center justify-center text-sm font-medium">
                {initials}
              </div>
              <span className="font-medium">{user.name || 'User'}</span>
            </button>
          </div>

          {/* Current Organization Info */}
          {!isLoadingOrganizations && currentOrganization && (
            <div className="border-t border-gray-100 mt-1 pt-1">
              <div className="px-4 py-3">
                <div className="flex items-start gap-2 mb-2">
                  <svg
                    className="w-4 h-4 text-gray-500 mt-0.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                    />
                  </svg>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">
                      {currentOrganization.name}
                    </div>
                    <div className="text-xs text-gray-500 capitalize">
                      {currentOrganization.role}
                    </div>
                  </div>
                </div>

                {/* Switch Organization Button - only show if multiple organizations */}
                {organizations.length > 1 && (
                  <button
                    className="flex items-center justify-between w-full px-3 py-2 text-sm text-gray-700 bg-gray-50 hover:bg-gray-100 rounded transition-colors"
                    onClick={() => {
                      setIsOpen(false);
                      router.push('/select-organization?from=menu');
                    }}
                  >
                    <span>Switch Organization</span>
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          )}

          <div className="border-t border-gray-100 mt-1 pt-1">
            <button
              className="flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              onClick={() => {
                setIsOpen(false);
              }}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              Settings
            </button>

            <button
              className="flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              onClick={() => {
                setIsOpen(false);
              }}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Get help
            </button>

            <button
              className="flex items-center gap-3 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors rounded"
              onClick={handleLogout}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
              Log out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}