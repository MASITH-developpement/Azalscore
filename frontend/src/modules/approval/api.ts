/**
 * AZALSCORE Module - APPROVAL - API Client
 * =========================================
 * Client API pour les workflows d'approbation
 */

import { api } from '@/core/api-client';
import type {
  ApprovalWorkflow, ApprovalRequest, ApprovalAction, PendingApproval, ApprovalStats,
  ApprovalType, WorkflowStatus, RequestStatus, ActionType,
} from './types';

const BASE_URL = '/approval';

// ============================================================================
// TYPES API
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface WorkflowFilters {
  type?: ApprovalType;
  status?: WorkflowStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface RequestFilters {
  workflow_id?: string;
  type?: ApprovalType;
  status?: RequestStatus;
  requester_id?: string;
  pending_for_me?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  approval_type: ApprovalType;
  steps: Array<{
    name: string;
    description?: string;
    step_type: string;
    order: number;
    approvers: Array<{
      approver_type: string;
      approver_id: string;
      approver_name: string;
      order?: number;
      is_required?: boolean;
      can_delegate?: boolean;
    }>;
    timeout_hours?: number;
    auto_approve_on_timeout?: boolean;
  }>;
  conditions?: Record<string, unknown>[];
  is_default?: boolean;
}

export interface ActionRequest {
  action_type: ActionType;
  comment?: string;
  delegated_to_id?: string;
}

// ============================================================================
// WORKFLOWS API
// ============================================================================

async function listWorkflows(filters?: WorkflowFilters) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
  }
  return api.get<PaginatedResponse<ApprovalWorkflow>>(`${BASE_URL}/workflows?${params.toString()}`);
}

async function getWorkflow(id: string) {
  return api.get<ApprovalWorkflow>(`${BASE_URL}/workflows/${id}`);
}

async function createWorkflow(data: WorkflowCreate) {
  return api.post<ApprovalWorkflow>(`${BASE_URL}/workflows`, data);
}

async function updateWorkflow(id: string, data: Partial<WorkflowCreate>) {
  return api.put<ApprovalWorkflow>(`${BASE_URL}/workflows/${id}`, data);
}

async function deleteWorkflow(id: string) {
  return api.delete(`${BASE_URL}/workflows/${id}`);
}

async function activateWorkflow(id: string) {
  return api.post<ApprovalWorkflow>(`${BASE_URL}/workflows/${id}/activate`);
}

async function deactivateWorkflow(id: string) {
  return api.post<ApprovalWorkflow>(`${BASE_URL}/workflows/${id}/deactivate`);
}

// ============================================================================
// REQUESTS API
// ============================================================================

async function listRequests(filters?: RequestFilters) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
  }
  return api.get<PaginatedResponse<ApprovalRequest>>(`${BASE_URL}/requests?${params.toString()}`);
}

async function getRequest(id: string) {
  return api.get<ApprovalRequest>(`${BASE_URL}/requests/${id}`);
}

async function getRequestActions(id: string) {
  return api.get<ApprovalAction[]>(`${BASE_URL}/requests/${id}/actions`);
}

async function submitAction(requestId: string, data: ActionRequest) {
  return api.post<ApprovalRequest>(`${BASE_URL}/requests/${requestId}/action`, data);
}

async function cancelRequest(id: string, reason?: string) {
  return api.post<ApprovalRequest>(`${BASE_URL}/requests/${id}/cancel`, { reason });
}

// ============================================================================
// PENDING APPROVALS API
// ============================================================================

async function getPendingApprovals() {
  return api.get<PendingApproval[]>(`${BASE_URL}/pending`);
}

async function getPendingCount() {
  return api.get<{ count: number }>(`${BASE_URL}/pending/count`);
}

// ============================================================================
// STATS API
// ============================================================================

async function getStats() {
  return api.get<ApprovalStats>(`${BASE_URL}/stats`);
}

async function getMyStats() {
  return api.get<ApprovalStats>(`${BASE_URL}/stats/me`);
}

// ============================================================================
// EXPORT
// ============================================================================

export const approvalApi = {
  // Workflows
  listWorkflows,
  getWorkflow,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
  activateWorkflow,
  deactivateWorkflow,

  // Requests
  listRequests,
  getRequest,
  getRequestActions,
  submitAction,
  cancelRequest,

  // Pending
  getPendingApprovals,
  getPendingCount,

  // Stats
  getStats,
  getMyStats,
};

export default approvalApi;
