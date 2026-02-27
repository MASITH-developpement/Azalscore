/**
 * AZALSCORE Module - APPROVAL - React Query Hooks
 * ================================================
 * Hooks pour les workflows d'approbation
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { approvalApi } from './api';
import type { WorkflowFilters, RequestFilters, WorkflowCreate, ActionRequest } from './api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const approvalKeys = {
  all: ['approval'] as const,
  stats: () => [...approvalKeys.all, 'stats'] as const,
  myStats: () => [...approvalKeys.all, 'stats', 'me'] as const,
  pending: () => [...approvalKeys.all, 'pending'] as const,
  pendingCount: () => [...approvalKeys.pending(), 'count'] as const,

  // Workflows
  workflows: () => [...approvalKeys.all, 'workflows'] as const,
  workflowsList: (filters?: WorkflowFilters) => [...approvalKeys.workflows(), 'list', filters] as const,
  workflow: (id: string) => [...approvalKeys.workflows(), id] as const,

  // Requests
  requests: () => [...approvalKeys.all, 'requests'] as const,
  requestsList: (filters?: RequestFilters) => [...approvalKeys.requests(), 'list', filters] as const,
  request: (id: string) => [...approvalKeys.requests(), id] as const,
  requestActions: (id: string) => [...approvalKeys.request(id), 'actions'] as const,
};

// ============================================================================
// STATS HOOKS
// ============================================================================

export function useApprovalStats() {
  return useQuery({
    queryKey: approvalKeys.stats(),
    queryFn: async () => {
      const response = await approvalApi.getStats();
      return response.data;
    },
  });
}

export function useMyApprovalStats() {
  return useQuery({
    queryKey: approvalKeys.myStats(),
    queryFn: async () => {
      const response = await approvalApi.getMyStats();
      return response.data;
    },
  });
}

// ============================================================================
// PENDING HOOKS
// ============================================================================

export function usePendingApprovals() {
  return useQuery({
    queryKey: approvalKeys.pending(),
    queryFn: async () => {
      const response = await approvalApi.getPendingApprovals();
      return response.data;
    },
  });
}

export function usePendingCount() {
  return useQuery({
    queryKey: approvalKeys.pendingCount(),
    queryFn: async () => {
      const response = await approvalApi.getPendingCount();
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });
}

// ============================================================================
// WORKFLOWS HOOKS
// ============================================================================

export function useWorkflows(filters?: WorkflowFilters) {
  return useQuery({
    queryKey: approvalKeys.workflowsList(filters),
    queryFn: async () => {
      const response = await approvalApi.listWorkflows(filters);
      return response.data;
    },
  });
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: approvalKeys.workflow(id),
    queryFn: async () => {
      const response = await approvalApi.getWorkflow(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: WorkflowCreate) => {
      const response = await approvalApi.createWorkflow(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: approvalKeys.workflows() });
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<WorkflowCreate> }) => {
      const response = await approvalApi.updateWorkflow(id, data);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: approvalKeys.workflow(id) });
      queryClient.invalidateQueries({ queryKey: approvalKeys.workflows() });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await approvalApi.deleteWorkflow(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: approvalKeys.workflows() });
    },
  });
}

export function useActivateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await approvalApi.activateWorkflow(id);
      return response.data;
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: approvalKeys.workflow(id) });
      queryClient.invalidateQueries({ queryKey: approvalKeys.workflows() });
    },
  });
}

export function useDeactivateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await approvalApi.deactivateWorkflow(id);
      return response.data;
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: approvalKeys.workflow(id) });
      queryClient.invalidateQueries({ queryKey: approvalKeys.workflows() });
    },
  });
}

// ============================================================================
// REQUESTS HOOKS
// ============================================================================

export function useApprovalRequests(filters?: RequestFilters) {
  return useQuery({
    queryKey: approvalKeys.requestsList(filters),
    queryFn: async () => {
      const response = await approvalApi.listRequests(filters);
      return response.data;
    },
  });
}

export function useApprovalRequest(id: string) {
  return useQuery({
    queryKey: approvalKeys.request(id),
    queryFn: async () => {
      const response = await approvalApi.getRequest(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useRequestActions(requestId: string) {
  return useQuery({
    queryKey: approvalKeys.requestActions(requestId),
    queryFn: async () => {
      const response = await approvalApi.getRequestActions(requestId);
      return response.data;
    },
    enabled: !!requestId,
  });
}

export function useSubmitAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ requestId, data }: { requestId: string; data: ActionRequest }) => {
      const response = await approvalApi.submitAction(requestId, data);
      return response.data;
    },
    onSuccess: (_data, { requestId }) => {
      queryClient.invalidateQueries({ queryKey: approvalKeys.request(requestId) });
      queryClient.invalidateQueries({ queryKey: approvalKeys.requestActions(requestId) });
      queryClient.invalidateQueries({ queryKey: approvalKeys.requests() });
      queryClient.invalidateQueries({ queryKey: approvalKeys.pending() });
      queryClient.invalidateQueries({ queryKey: approvalKeys.stats() });
    },
  });
}

export function useCancelRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      const response = await approvalApi.cancelRequest(id, reason);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: approvalKeys.request(id) });
      queryClient.invalidateQueries({ queryKey: approvalKeys.requests() });
      queryClient.invalidateQueries({ queryKey: approvalKeys.pending() });
    },
  });
}
