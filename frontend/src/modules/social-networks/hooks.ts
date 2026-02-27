/**
 * AZALSCORE - Social Networks React Query Hooks
 * ==============================================
 * Hooks pour le module Réseaux Sociaux / Marketing
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { socialNetworksApi } from './api';
import type { SocialMetrics, MarketingSummary } from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const socialNetworksKeys = {
  all: ['social-networks'] as const,
  summary: (date: string) => [...socialNetworksKeys.all, 'summary', date] as const,
  metrics: (filters?: { limit?: number }) => [...socialNetworksKeys.all, 'metrics', filters] as const,
};

// ============================================================================
// HELPER
// ============================================================================

function unwrapResponse<T>(response: unknown): T | null {
  if (!response) return null;
  return ((response as { data?: T }).data || response) as T;
}

// ============================================================================
// QUERY HOOKS
// ============================================================================

export const useSocialSummary = (date: string) => {
  return useQuery({
    queryKey: socialNetworksKeys.summary(date),
    queryFn: () => socialNetworksApi.getSummary(date),
    select: (data) => unwrapResponse<MarketingSummary>(data),
  });
};

export const useSocialMetrics = (filters?: { limit?: number }) => {
  return useQuery({
    queryKey: socialNetworksKeys.metrics(filters),
    queryFn: () => socialNetworksApi.getMetrics(filters),
    select: (data) => unwrapResponse<SocialMetrics[]>(data) || [],
  });
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

export const useSyncToPrometheus = () => {
  return useMutation({
    mutationFn: (date: string) => socialNetworksApi.syncToPrometheus(date),
  });
};

export const useSaveGoogleAnalytics = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: socialNetworksApi.saveGoogleAnalytics,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: socialNetworksKeys.all });
    },
  });
};

export const useSaveGoogleAds = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: socialNetworksApi.saveGoogleAds,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: socialNetworksKeys.all });
    },
  });
};

export const useSaveGoogleSearchConsole = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: socialNetworksApi.saveGoogleSearchConsole,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: socialNetworksKeys.all });
    },
  });
};

export const useSaveGoogleMyBusiness = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: socialNetworksApi.saveGoogleMyBusiness,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: socialNetworksKeys.all });
    },
  });
};

export const useSaveMetaBusiness = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: socialNetworksApi.saveMetaBusiness,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: socialNetworksKeys.all });
    },
  });
};

export const useSaveLinkedIn = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: socialNetworksApi.saveLinkedIn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: socialNetworksKeys.all });
    },
  });
};

export const useSaveSolocal = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: socialNetworksApi.saveSolocal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: socialNetworksKeys.all });
    },
  });
};
