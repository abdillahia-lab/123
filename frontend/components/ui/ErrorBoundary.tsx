'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';
import { errorTracker } from '@/lib/monitoring';

// ============================================================================
// ERROR BOUNDARY PROPS & STATE
// ============================================================================

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  resetKeys?: unknown[];
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

// ============================================================================
// ERROR BOUNDARY COMPONENT
// ============================================================================

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Track error
    const errorId = errorTracker.reportError(error, {
      componentStack: errorInfo.componentStack,
      type: 'react_error_boundary',
    });

    this.setState({ errorInfo, errorId });

    // Call custom error handler
    this.props.onError?.(error, errorInfo);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    // Reset error state if resetKeys change
    if (this.state.hasError && this.props.resetKeys) {
      const changed = this.props.resetKeys.some(
        (key, index) => key !== prevProps.resetKeys?.[index]
      );
      if (changed) {
        this.handleReset();
      }
    }
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  handleGoHome = (): void => {
    window.location.href = '/';
  };

  render(): ReactNode {
    const { hasError, error, errorInfo, errorId } = this.state;
    const { children, fallback, showDetails = false } = this.props;

    if (hasError) {
      // Custom fallback
      if (fallback) {
        return fallback;
      }

      // Default error UI
      return (
        <div
          role="alert"
          aria-live="assertive"
          className="min-h-[400px] flex items-center justify-center p-8 bg-gray-50 dark:bg-gray-900"
        >
          <div className="max-w-lg w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
            {/* Icon */}
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
            </div>

            {/* Title */}
            <h2 className="text-xl font-bold text-gray-900 dark:text-white text-center mb-2">
              Something went wrong
            </h2>

            {/* Description */}
            <p className="text-gray-600 dark:text-gray-400 text-center mb-6">
              We encountered an unexpected error. Our team has been notified and is working on a fix.
            </p>

            {/* Error ID */}
            {errorId && (
              <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-3 mb-6">
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  Error ID: <code className="font-mono">{errorId}</code>
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={this.handleReset}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-terra-600 text-white rounded-lg hover:bg-terra-700 focus:outline-none focus:ring-2 focus:ring-terra-500 focus:ring-offset-2 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
              >
                <Home className="w-4 h-4" />
                Go Home
              </button>
            </div>

            {/* Technical details (development only) */}
            {showDetails && error && (
              <details className="mt-6">
                <summary className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300">
                  <Bug className="w-4 h-4" />
                  Technical Details
                </summary>
                <div className="mt-3 p-4 bg-gray-900 rounded-lg overflow-x-auto">
                  <pre className="text-xs text-red-400 whitespace-pre-wrap font-mono">
                    {error.message}
                    {'\n\n'}
                    {error.stack}
                    {errorInfo?.componentStack && (
                      <>
                        {'\n\nComponent Stack:'}
                        {errorInfo.componentStack}
                      </>
                    )}
                  </pre>
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return children;
  }
}

// ============================================================================
// HOC FOR FUNCTIONAL COMPONENTS
// ============================================================================

export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
): React.FC<P> {
  const WrappedComponent: React.FC<P> = (props) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name || 'Component'})`;

  return WrappedComponent;
}

// ============================================================================
// SUSPENSE BOUNDARY WITH ERROR HANDLING
// ============================================================================

interface SuspenseBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  errorFallback?: ReactNode;
}

export function SuspenseBoundary({
  children,
  fallback,
  errorFallback,
}: SuspenseBoundaryProps): JSX.Element {
  return (
    <ErrorBoundary fallback={errorFallback}>
      <React.Suspense
        fallback={
          fallback || (
            <div className="flex items-center justify-center min-h-[200px]">
              <div className="w-8 h-8 border-4 border-terra-200 border-t-terra-600 rounded-full animate-spin" />
            </div>
          )
        }
      >
        {children}
      </React.Suspense>
    </ErrorBoundary>
  );
}
