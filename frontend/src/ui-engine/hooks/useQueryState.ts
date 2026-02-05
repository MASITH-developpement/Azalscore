/**
 * AZALSCORE UI Engine - useQueryState Hook
 * Wraps React Query result with timeout detection and normalized state.
 */

import { useState, useEffect, useRef } from 'react';
import type { UseQueryResult } from '@tanstack/react-query';

export type QueryState = 'loading' | 'loading-slow' | 'error' | 'empty' | 'success';

export interface UseQueryStateOptions<T> {
  /** Timeout in ms before switching to loading-slow (default: 5000) */
  timeoutMs?: number;
  /** Custom isEmpty predicate. Default checks null/undefined/empty array/items.length===0 */
  isEmpty?: (data: T | undefined) => boolean;
}

export interface UseQueryStateResult<T> {
  state: QueryState;
  data: T | undefined;
  error: Error | null;
  refetch: () => void;
  isLoadingSlow: boolean;
}

function defaultIsEmpty<T>(data: T | undefined): boolean {
  if (data === null || data === undefined) return true;
  if (Array.isArray(data)) return data.length === 0;
  if (typeof data === 'object' && data !== null) {
    // Check for paginated responses with items/results/data arrays
    const obj = data as Record<string, unknown>;
    if ('items' in obj && Array.isArray(obj.items)) return obj.items.length === 0;
    if ('results' in obj && Array.isArray(obj.results)) return obj.results.length === 0;
    if ('data' in obj && Array.isArray(obj.data)) return (obj.data as unknown[]).length === 0;
  }
  return false;
}

export function useQueryState<T>(
  query: UseQueryResult<T>,
  options?: UseQueryStateOptions<T>
): UseQueryStateResult<T> {
  const timeoutMs = options?.timeoutMs ?? 5000;
  const isEmpty = options?.isEmpty ?? defaultIsEmpty;

  const [isLoadingSlow, setIsLoadingSlow] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (query.isLoading || query.isFetching) {
      timerRef.current = setTimeout(() => {
        setIsLoadingSlow(true);
      }, timeoutMs);
    } else {
      setIsLoadingSlow(false);
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [query.isLoading, query.isFetching, timeoutMs]);

  let state: QueryState;
  if (query.isLoading || query.isFetching) {
    state = isLoadingSlow ? 'loading-slow' : 'loading';
  } else if (query.isError) {
    state = 'error';
  } else if (isEmpty(query.data)) {
    state = 'empty';
  } else {
    state = 'success';
  }

  return {
    state,
    data: query.data,
    error: query.error instanceof Error ? query.error : query.error ? new Error(String(query.error)) : null,
    refetch: () => { query.refetch(); },
    isLoadingSlow,
  };
}
