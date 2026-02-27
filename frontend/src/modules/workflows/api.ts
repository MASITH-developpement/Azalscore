/**
 * AZALSCORE Module - Workflows API
 * Client API pour le module BPM/Workflows
 */

import { api } from '@/core/api-client';
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
    return api.get(`${BASE_URL}/definitions?${params}`);
  },

  get: async (id: string): Promise<WorkflowDefinition> => {
    return api.get(`${BASE_URL}/definitions/${id}`);
  },

  create: async (data: WorkflowCreate): Promise<WorkflowDefinition> => {
    return api.post(`${BASE_URL}/definitions`, data);
  },

  update: async (id: string, data: WorkflowUpdate): Promise<WorkflowDefinition> => {
    return api.put(`${BASE_URL}/definitions/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/definitions/${id}`);
  },

  activate: async (id: string): Promise<WorkflowDefinition> => {
    return api.post(`${BASE_URL}/definitions/${id}/activate`);
  },

  suspend: async (id: string): Promise<WorkflowDefinition> => {
    return api.post(`${BASE_URL}/definitions/${id}/suspend`);
  },

  archive: async (id: string): Promise<WorkflowDefinition> => {
    return api.post(`${BASE_URL}/definitions/${id}/archive`);
  },

  createVersion: async (id: string): Promise<WorkflowDefinition> => {
    return api.post(`${BASE_URL}/definitions/${id}/new-version`);
  },

  // Steps
  addStep: async (workflowId: string, data: Partial<Step>): Promise<Step> => {
    return api.post(`${BASE_URL}/definitions/${workflowId}/steps`, data);
  },

  updateStep: async (workflowId: string, stepId: string, data: Partial<Step>): Promise<Step> => {
    return api.put(`${BASE_URL}/definitions/${workflowId}/steps/${stepId}`, data);
  },

  deleteStep: async (workflowId: string, stepId: string): Promise<void> => {
    return api.delete(`${BASE_URL}/definitions/${workflowId}/steps/${stepId}`);
  },

  // Transitions
  addTransition: async (workflowId: string, data: { from_step_id: string; to_step_id: string; name?: string; conditions?: Condition[]; is_default?: boolean }): Promise<Transition> => {
    return api.post(`${BASE_URL}/definitions/${workflowId}/transitions`, data);
  },

  deleteTransition: async (workflowId: string, transitionId: string): Promise<void> => {
    return api.delete(`${BASE_URL}/definitions/${workflowId}/transitions/${transitionId}`);
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
    return api.get(`${BASE_URL}/instances?${params}`);
  },

  get: async (id: string): Promise<WorkflowInstance> => {
    return api.get(`${BASE_URL}/instances/${id}`);
  },

  start: async (data: InstanceCreate): Promise<WorkflowInstance> => {
    return api.post(`${BASE_URL}/instances`, data);
  },

  cancel: async (id: string, reason?: string): Promise<WorkflowInstance> => {
    return api.post(`${BASE_URL}/instances/${id}/cancel`, { reason });
  },

  suspend: async (id: string, reason?: string): Promise<WorkflowInstance> => {
    return api.post(`${BASE_URL}/instances/${id}/suspend`, { reason });
  },

  resume: async (id: string): Promise<WorkflowInstance> => {
    return api.post(`${BASE_URL}/instances/${id}/resume`);
  },

  getHistory: async (id: string): Promise<WorkflowHistory[]> => {
    return api.get(`${BASE_URL}/instances/${id}/history`);
  },

  // Timeline view
  getTimeline: async (id: string): Promise<{ steps: unknown[]; current: string[] }> => {
    return api.get(`${BASE_URL}/instances/${id}/timeline`);
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
    return api.get(`${BASE_URL}/tasks?${params}`);
  },

  getMyTasks: async (status?: string): Promise<TaskInstance[]> => {
    const params = status ? `?status=${status}` : '';
    return api.get(`${BASE_URL}/tasks/my${params}`);
  },

  get: async (id: string): Promise<TaskInstance> => {
    return api.get(`${BASE_URL}/tasks/${id}`);
  },

  start: async (id: string): Promise<TaskInstance> => {
    return api.post(`${BASE_URL}/tasks/${id}/start`);
  },

  complete: async (id: string, data: TaskCompleteData): Promise<TaskInstance> => {
    return api.post(`${BASE_URL}/tasks/${id}/complete`, data);
  },

  reject: async (id: string, reason?: string): Promise<TaskInstance> => {
    return api.post(`${BASE_URL}/tasks/${id}/reject`, { reason });
  },

  delegate: async (id: string, data: TaskDelegateData): Promise<TaskInstance> => {
    return api.post(`${BASE_URL}/tasks/${id}/delegate`, data);
  },

  escalate: async (id: string, escalate_to: string, reason: string): Promise<TaskInstance> => {
    return api.post(`${BASE_URL}/tasks/${id}/escalate`, { escalate_to, reason });
  },
};

// ============================================================================
// STATS API
// ============================================================================

export const statsApi = {
  getStats: async (): Promise<WorkflowStats> => {
    return api.get(`${BASE_URL}/stats`);
  },

  getDashboard: async (): Promise<{ stats: WorkflowStats; recent_instances: WorkflowInstance[]; pending_tasks: TaskInstance[] }> => {
    return api.get(`${BASE_URL}/dashboard`);
  },
};
