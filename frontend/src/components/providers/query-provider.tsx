"use client";

import { ReactNode, useState, lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Lazy load devtools only in development
const ReactQueryDevtools = lazy(() => 
  import('@tanstack/react-query-devtools').then(module => ({
    default: module.ReactQueryDevtools
  }))
);

interface QueryProviderProps {
  children: ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  // Create a new QueryClient instance for each component tree
  // This ensures that server and client have different instances
  const [queryClient] = useState(
    () => new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 5 * 60 * 1000, // 5 minutes
          gcTime: 10 * 60 * 1000, // 10 minutes
          retry: (failureCount, error: any) => {
            // Don't retry on 4xx errors except 401
            if (error?.status >= 400 && error?.status < 500 && error?.status !== 401) {
              return false;
            }
            return failureCount < 3;
          },
          refetchOnWindowFocus: false,
        },
        mutations: {
          retry: (failureCount, error: any) => {
            // Don't retry mutations on client errors
            if (error?.status >= 400 && error?.status < 500) {
              return false;
            }
            return failureCount < 2;
          },
        },
      },
    })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <Suspense fallback={null}>
          <ReactQueryDevtools initialIsOpen={false} />
        </Suspense>
      )}
    </QueryClientProvider>
  );
}