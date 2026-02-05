/**
 * AZALSCORE UI Engine - QueryStateView
 * Render-props wrapper that handles loading/error/empty states automatically.
 *
 * Usage:
 * ```tsx
 * <QueryStateView query={interventionsQuery} emptyTitle="Aucune intervention">
 *   {(data) => <DataTable data={data} ... />}
 * </QueryStateView>
 * ```
 */

import React from 'react';
import type { UseQueryResult } from '@tanstack/react-query';
import { useQueryState, type UseQueryStateOptions } from '../hooks/useQueryState';
import { LoadingState, ErrorState, EmptyState } from './StateViews';

export interface QueryStateViewProps<T> {
  /** The React Query result to observe */
  query: UseQueryResult<T>;
  /** Render function called with data when state is 'success' */
  children: (data: T) => React.ReactNode;
  /** Options for useQueryState */
  queryStateOptions?: UseQueryStateOptions<T>;
  /** Empty state title */
  emptyTitle?: string;
  /** Empty state message */
  emptyMessage?: string;
  /** Empty state icon */
  emptyIcon?: React.ReactNode;
  /** Empty state action */
  emptyAction?: { label: string; onClick: () => void; icon?: React.ReactNode };
  /** Error title override */
  errorTitle?: string;
  /** Error message override */
  errorMessage?: string;
  /** Back callback for error state */
  onBack?: () => void;
  /** Additional class */
  className?: string;
}

export function QueryStateView<T>({
  query,
  children,
  queryStateOptions,
  emptyTitle,
  emptyMessage,
  emptyIcon,
  emptyAction,
  errorTitle,
  errorMessage,
  onBack,
  className,
}: QueryStateViewProps<T>): React.ReactElement {
  const { state, data, error, refetch } = useQueryState(query, queryStateOptions);

  switch (state) {
    case 'loading':
    case 'loading-slow':
      return <LoadingState onRetry={refetch} className={className} />;
    case 'error':
      return (
        <ErrorState
          title={errorTitle}
          message={errorMessage || error?.message}
          onRetry={refetch}
          onBack={onBack}
          className={className}
        />
      );
    case 'empty':
      return (
        <EmptyState
          title={emptyTitle}
          message={emptyMessage}
          icon={emptyIcon}
          action={emptyAction}
          className={className}
        />
      );
    case 'success':
      return <>{children(data as T)}</>;
  }
}

export default QueryStateView;
