/**
 * AZALSCORE Module - Workflows Hooks
 * React Query hooks pour le module BPM/Workflows
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowApi, instanceApi, taskApi, statsApi } from './api';
import type {
  WorkflowCreate, WorkflowUpdate, WorkflowFilters,
  InstanceCreate, InstanceFilters,
  TaskFilters, TaskCompleteData, TaskDelegateData,
  Step, Condition,
} from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const workflowKeys = {
  all: ['workflows'] as const,

  // Definitions
  definitions: () => [...workflowKeys.all, 'definitions'] as const,
  definitionList: (filters?: WorkflowFilters) => [...workflowKeys.definitions(), 'list', filters] as const,
  definitionDetail: (id: string) => [...workflowKeys.definitions(), 'detail', id] as const,

  // Instances
  instances: () => [...workflowKeys.all, 'instances'] as const,
  instanceList: (filters?: InstanceFilters) => [...workflowKeys.instances(), 'list', filters] as const,
  instanceDetail: (id: string) => [...workflowKeys.instances(), 'detail', id] as const,
  instanceHistory: (id: string) => [...workflowKeys.instances(), 'history', id] as const,
  instanceTimeline: (id: string) => [...workflowKeys.instances(), 'timeline', id] as const,

  // Tasks
  tasks: () => [...workflowKeys.all, 'tasks'] as const,
  taskList: (filters?: TaskFilters) => [...workflowKeys.tasks(), 'list', filters] as const,
  taskDetail: (id: string) => [...workflowKeys.tasks(), 'detail', id] as const,
  myTasks: (status?: string) => [...workflowKeys.tasks(), 'my', status] as const,

  // Stats
  stats: () => [...workflowKeys.all, 'stats'] as const,
  dashboard: () => [...workflowKeys.all, 'dashboard'] as const,
};

// ============================================================================
// WORKFLOW DEFINITION HOOKS
// ============================================================================

export function useWorkflowList(filters?: WorkflowFilters) {
  return useQuery({
    queryKey: workflowKeys.definitionList(filters),
    queryFn: () => workflowApi.list(filters),
  });
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: workflowKeys.definitionDetail(id),
    queryFn: () => workflowApi.get(id),
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WorkflowCreate) => workflowApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitions() });
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkflowUpdate }) => workflowApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitionDetail(id) });
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitions() });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workflowApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitions() });
    },
  });
}

export function useActivateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workflowApi.activate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitionDetail(id) });
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitions() });
    },
  });
}

export function useSuspendWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workflowApi.suspend(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitionDetail(id) });
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitions() });
    },
  });
}

export function useArchiveWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workflowApi.archive(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitionDetail(id) });
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitions() });
    },
  });
}

export function useCreateWorkflowVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workflowApi.createVersion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitions() });
    },
  });
}

// Step management
export function useAddStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workflowId, data }: { workflowId: string; data: Partial<Step> }) =>
      workflowApi.addStep(workflowId, data),
    onSuccess: (_, { workflowId }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitionDetail(workflowId) });
    },
  });
}

export function useUpdateStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workflowId, stepId, data }: { workflowId: string; stepId: string; data: Partial<Step> }) =>
      workflowApi.updateStep(workflowId, stepId, data),
    onSuccess: (_, { workflowId }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitionDetail(workflowId) });
    },
  });
}

export function useDeleteStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workflowId, stepId }: { workflowId: string; stepId: string }) =>
      workflowApi.deleteStep(workflowId, stepId),
    onSuccess: (_, { workflowId }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitionDetail(workflowId) });
    },
  });
}

// Transition management
export function useAddTransition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workflowId, data }: { workflowId: string; data: { from_step_id: string; to_step_id: string; name?: string; conditions?: Condition[]; is_default?: boolean } }) =>
      workflowApi.addTransition(workflowId, data),
    onSuccess: (_, { workflowId }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitionDetail(workflowId) });
    },
  });
}

export function useDeleteTransition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workflowId, transitionId }: { workflowId: string; transitionId: string }) =>
      workflowApi.deleteTransition(workflowId, transitionId),
    onSuccess: (_, { workflowId }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.definitionDetail(workflowId) });
    },
  });
}

// ============================================================================
// WORKFLOW INSTANCE HOOKS
// ============================================================================

export function useInstanceList(filters?: InstanceFilters) {
  return useQuery({
    queryKey: workflowKeys.instanceList(filters),
    queryFn: () => instanceApi.list(filters),
  });
}

export function useInstance(id: string) {
  return useQuery({
    queryKey: workflowKeys.instanceDetail(id),
    queryFn: () => instanceApi.get(id),
    enabled: !!id,
  });
}

export function useInstanceHistory(id: string) {
  return useQuery({
    queryKey: workflowKeys.instanceHistory(id),
    queryFn: () => instanceApi.getHistory(id),
    enabled: !!id,
  });
}

export function useInstanceTimeline(id: string) {
  return useQuery({
    queryKey: workflowKeys.instanceTimeline(id),
    queryFn: () => instanceApi.getTimeline(id),
    enabled: !!id,
  });
}

export function useStartInstance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InstanceCreate) => instanceApi.start(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.instances() });
      queryClient.invalidateQueries({ queryKey: workflowKeys.stats() });
    },
  });
}

export function useCancelInstance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => instanceApi.cancel(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.instanceDetail(id) });
      queryClient.invalidateQueries({ queryKey: workflowKeys.instances() });
      queryClient.invalidateQueries({ queryKey: workflowKeys.stats() });
    },
  });
}

export function useSuspendInstance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => instanceApi.suspend(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.instanceDetail(id) });
      queryClient.invalidateQueries({ queryKey: workflowKeys.instances() });
    },
  });
}

export function useResumeInstance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => instanceApi.resume(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.instanceDetail(id) });
      queryClient.invalidateQueries({ queryKey: workflowKeys.instances() });
    },
  });
}

// ============================================================================
// TASK HOOKS
// ============================================================================

export function useTaskList(filters?: TaskFilters) {
  return useQuery({
    queryKey: workflowKeys.taskList(filters),
    queryFn: () => taskApi.list(filters),
  });
}

export function useMyTasks(status?: string) {
  return useQuery({
    queryKey: workflowKeys.myTasks(status),
    queryFn: () => taskApi.getMyTasks(status),
  });
}

export function useTask(id: string) {
  return useQuery({
    queryKey: workflowKeys.taskDetail(id),
    queryFn: () => taskApi.get(id),
    enabled: !!id,
  });
}

export function useStartTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => taskApi.start(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.taskDetail(id) });
      queryClient.invalidateQueries({ queryKey: workflowKeys.tasks() });
    },
  });
}

export function useCompleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskCompleteData }) => taskApi.complete(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: workflowKeys.instances() });
      queryClient.invalidateQueries({ queryKey: workflowKeys.stats() });
    },
  });
}

export function useRejectTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => taskApi.reject(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: workflowKeys.instances() });
    },
  });
}

export function useDelegateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskDelegateData }) => taskApi.delegate(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.taskDetail(id) });
      queryClient.invalidateQueries({ queryKey: workflowKeys.tasks() });
    },
  });
}

export function useEscalateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, escalate_to, reason }: { id: string; escalate_to: string; reason: string }) =>
      taskApi.escalate(id, escalate_to, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.taskDetail(id) });
      queryClient.invalidateQueries({ queryKey: workflowKeys.tasks() });
    },
  });
}

// ============================================================================
// STATS HOOKS
// ============================================================================

export function useWorkflowStats() {
  return useQuery({
    queryKey: workflowKeys.stats(),
    queryFn: () => statsApi.getStats(),
  });
}

export function useWorkflowDashboard() {
  return useQuery({
    queryKey: workflowKeys.dashboard(),
    queryFn: () => statsApi.getDashboard(),
  });
}
