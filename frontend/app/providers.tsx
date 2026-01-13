'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ToastContainer } from '@/components/ui/Toast';
import { analytics } from '@/lib/monitoring';

// ============================================================================
// THEME MANAGEMENT
// ============================================================================

function ThemeManager() {
  useEffect(() => {
    // Check for system preference
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const savedTheme = localStorage.getItem('theme');

    const applyTheme = (isDark: boolean) => {
      document.documentElement.classList.toggle('dark', isDark);
    };

    if (savedTheme === 'dark') {
      applyTheme(true);
    } else if (savedTheme === 'light') {
      applyTheme(false);
    } else {
      applyTheme(mediaQuery.matches);
    }

    // Listen for system changes
    const listener = (e: MediaQueryListEvent) => {
      if (!savedTheme || savedTheme === 'system') {
        applyTheme(e.matches);
      }
    };

    mediaQuery.addEventListener('change', listener);
    return () => mediaQuery.removeEventListener('change', listener);
  }, []);

  return null;
}

// ============================================================================
// ANALYTICS INITIALIZATION
// ============================================================================

function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Track page views
    const path = window.location.pathname;
    analytics.page(path);

    // Track navigation
    const handleRouteChange = () => {
      analytics.page(window.location.pathname);
    };

    window.addEventListener('popstate', handleRouteChange);
    return () => window.removeEventListener('popstate', handleRouteChange);
  }, []);

  return <>{children}</>;
}

// ============================================================================
// KEYBOARD SHORTCUTS
// ============================================================================

function KeyboardShortcuts() {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K for search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        // Dispatch custom event for search modal
        window.dispatchEvent(new CustomEvent('open-search'));
      }

      // Escape to close modals
      if (e.key === 'Escape') {
        window.dispatchEvent(new CustomEvent('close-modal'));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return null;
}

// ============================================================================
// PROVIDERS COMPONENT
// ============================================================================

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
            retry: 3,
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
          },
          mutations: {
            retry: 1,
          },
        },
      })
  );

  return (
    <ErrorBoundary showDetails={process.env.NODE_ENV === 'development'}>
      <QueryClientProvider client={queryClient}>
        <AnalyticsProvider>
          <ThemeManager />
          <KeyboardShortcuts />
          {children}
          <ToastContainer />
        </AnalyticsProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
