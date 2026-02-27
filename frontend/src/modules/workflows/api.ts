/**
 * AZALSCORE Module - Workflows API
 * Client API pour le module BPM/Workflows
 */

import { api } from '@core/api-client';
import type {
  WorkflowDefinition, WorkflowCreate, WorkflowUpdate, WorkflowListResponse, WorkflowFilters,
  WorkflowInstance, InstanceCreate, InstanceListResponse, InstanceFilters,
  TaskInstance, TaskListResponse, TaskFilters, TaskCompleteData, TaskDelegateData,
  WorkflowHistory, WorkflowStats, Step, Transition, Condition,
} from './types';

const BASE_URL = '/workflows';

// ============================================================================
// WORKFLOW DEFINITION API
// ============================================================================

export const workflowApi = {
  list: async (filters?: WorkflowFilters): Promise<WorkflowListResponse> => {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.category) params.set('category', filters.category);
    if (filters?.search) params.set('search', filters.search);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    const queryString = params.toString();
    const url = `${BASE_URL}/definitions${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<WorkflowListResponse>(url);
    return response as unknown as WorkflowListResponse;
  },

  get: async (id: string): Promise<WorkflowDefinition> => {
    const response = await api.get<WorkflowDefinition>(`${BASE_URL}/definitions/${id}`);
    return response as unknown as WorkflowDefinition;
  },

  create: async (data: WorkflowCreate): Promise<WorkflowDefinition> => {
    const response = await api.post<WorkflowDefinition>(`${BASE_URL}/definitions`, data);
    return response as unknown as WorkflowDefinition;
  },

  update: async (id: string, data: WorkflowUpdate): Promise<WorkflowDefinition> => {
    const response = await api.put<WorkflowDefinition>(`${BASE_URL}/definitions/${id}`, data);
    return response as unknown as WorkflowDefinition;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/definitions/${id}`);
  },

  activate: async (id: string): Promise<WorkflowDefinition> => {
    const response = await api.post<WorkflowDefinition>(`${BASE_URL}/definitions/${id}/activate`);
    return response as unknown as WorkflowDefinition;
  },

  suspend: async (id: string): Promise<WorkflowDefinition> => {
    const response = await api.post<WorkflowDefinition>(`${BASE_URL}/definitions/${id}/suspend`);
    return response as unknown as WorkflowDefinition;
  },

  archive: async (id: string): Promise<WorkflowDefinition> => {
    const response = await api.post<WorkflowDefinition>(`${BASE_URL}/definitions/${id}/archive`);
    return response as unknown as WorkflowDefinition;
  },

  createVersion: async (id: string): Promise<WorkflowDefinition> => {
    const response = await api.post<WorkflowDefinition>(`${BASE_URL}/definitions/${id}/new-version`);
    return response as unknown as WorkflowDefinition;
  },

  // Steps
  addStep: async (workflowId: string, data: Partial<Step>): Promise<Step> => {
    const response = await api.post<Step>(`${BASE_URL}/definitions/${workflowId}/steps`, data);
    return response as unknown as Step;
  },

  updateStep: async (workflowId: string, stepId: string, data: Partial<Step>): Promise<Step> => {
    const response = await api.put<Step>(`${BASE_URL}/definitions/${workflowId}/steps/${stepId}`, data);
    return response as unknown as Step;
  },

  deleteStep: async (workflowId: string, stepId: string): Promise<void> => {
    await api.delete(`${BASE_URL}/definitions/${workflowId}/steps/${stepId}`);
  },

  // Transitions
  addTransition: async (workflowId: string, data: { from_step_id: string; to_step_id: string; name?: string; conditions?: Condition[]; is_default?: boolean }): Promise<Transition> => {
    const response = await api.post<Transition>(`${BASE_URL}/definitions/${workflowId}/transitions`, data);
    return response as unknown as Transition;
  },

  deleteTransition: async (workflowId: string, transitionId: string): Promise<void> => {
    await api.delete(`${BASE_URL}/definitions/${workflowId}/transitions/${transitionId}`);
  },
};

// ============================================================================
// WORKFLOW INSTANCE API
// ============================================================================

export const instanceApi = {
  list: async (filters?: InstanceFilters): Promise<InstanceListResponse> => {
    const params = new URLSearchParams();
    if (filters?.workflow_id) params.set('workflow_id', filters.workflow_id);
    if (filters?.status) params.set('status', filters.status);
    if (filters?.initiated_by) params.set('initiated_by', filters.initiated_by);
    if (filters?.reference_type) params.set('reference_type', filters.reference_type);
    if (filters?.reference_id) params.set('reference_id', filters.reference_id);
    if (filters?.from_date) params.set('from_date', filters.from_date);
    if (filters?.to_date) params.set('to_date', filters.to_date);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    const queryString = params.toString();
    const url = `${BASE_URL}/instances${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<InstanceListResponse>(url);
    return response as unknown as InstanceListResponse;
  },

  get: async (id: string): Promise<WorkflowInstance> => {
    const response = await api.get<WorkflowInstance>(`${BASE_URL}/instances/${id}`);
    return response as unknown as WorkflowInstance;
  },

  start: async (data: InstanceCreate): Promise<WorkflowInstance> => {
    const response = await api.post<WorkflowInstance>(`${BASE_URL}/instances`, data);
    return response as unknown as WorkflowInstance;
  },

  cancel: async (id: string, reason?: string): Promise<WorkflowInstance> => {
    const response = await api.post<WorkflowInstance>(`${BASE_URL}/instances/${id}/cancel`, { reason });
    return response as unknown as WorkflowInstance;
  },

  suspend: async (id: string, reason?: string): Promise<WorkflowInstance> => {
    const response = await api.post<WorkflowInstance>(`${BASE_URL}/instances/${id}/suspend`, { reason });
    return response as unknown as WorkflowInstance;
  },

  resume: async (id: string): Promise<WorkflowInstance> => {
    const response = await api.post<WorkflowInstance>(`${BASE_URL}/instances/${id}/resume`);
    return response as unknown as WorkflowInstance;
  },

  getHistory: async (id: string): Promise<WorkflowHistory[]> => {
    const response = await api.get<WorkflowHistory[]>(`${BASE_URL}/instances/${id}/history`);
    return response as unknown as WorkflowHistory[];
  },

  // Timeline view
  getTimeline: async (id: string): Promise<{ steps: unknown[]; current: string[] }> => {
    const response = await api.get<{ steps: unknown[]; current: string[] }>(`${BASE_URL}/instances/${id}/timeline`);
    return response as unknown as { steps: unknown[]; current: string[] };
  },
};

// ============================================================================
// TASK API
// ============================================================================

export const taskApi = {
  list: async (filters?: TaskFilters): Promise<TaskListResponse> => {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.assigned_to) params.set('assigned_to', filters.assigned_to);
    if (filters?.workflow_id) params.set('workflow_id', filters.workflow_id);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    const queryString = params.toString();
    const url = `${BASE_URL}/tasks${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<TaskListResponse>(url);
    return response as unknown as TaskListResponse;
  },

  getMyTasks: async (status?: string): Promise<TaskInstance[]> => {
    const params = status ? `?status=${status}` : '';
    const response = await api.get<TaskInstance[]>(`${BASE_URL}/tasks/my${params}`);
    return response as unknown as TaskInstance[];
  },

  get: async (id: string): Promise<TaskInstance> => {
    const response = await api.get<TaskInstance>(`${BASE_URL}/tasks/${id}`);
    return response as unknown as TaskInstance;
  },

  start: async (id: string): Promise<TaskInstance> => {
    const response = await api.post<TaskInstance>(`${BASE_URL}/tasks/${id}/start`);
    return response as unknown as TaskInstance;
  },

  complete: async (id: string, data: TaskCompleteData): Promise<TaskInstance> => {
    const response = await api.post<TaskInstance>(`${BASE_URL}/tasks/${id}/complete`, data);
    return response as unknown as TaskInstance;
  },

  reject: async (id: string, reason?: string): Promise<TaskInstance> => {
    const response = await api.post<TaskInstance>(`${BASE_URL}/tasks/${id}/reject`, { reason });
    return response as unknown as TaskInstance;
  },

  delegate: async (id: string, data: TaskDelegateData): Promise<TaskInstance> => {
    const response = await api.post<TaskInstance>(`${BASE_URL}/tasks/${id}/delegate`, data);
    return response as unknown as TaskInstance;
  },

  escalate: async (id: string, escalate_to: string, reason: string): Promise<TaskInstance> => {
    const response = await api.post<TaskInstance>(`${BASE_URL}/tasks/${id}/escalate`, { escalate_to, reason });
    return response as unknown as TaskInstance;
  },
};

// ============================================================================
// STATS API
// ============================================================================

export const statsApi = {
  getStats: async (): Promise<WorkflowStats> => {
    const response = await api.get<WorkflowStats>(`${BASE_URL}/stats`);
    return response as unknown as WorkflowStats;
  },

  getDashboard: async (): Promise<{ stats: WorkflowStats; recent_instances: WorkflowInstance[]; pending_tasks: TaskInstance[] }> => {
    const response = await api.get<{ stats: WorkflowStats; recent_instances: WorkflowInstance[]; pending_tasks: TaskInstance[] }>(`${BASE_URL}/dashboard`);
    return response as unknown as { stats: WorkflowStats; recent_instances: WorkflowInstance[]; pending_tasks: TaskInstance[] };
  },
};
