/**
 * AZALSCORE Module - Compliance - React Query Hooks
 * Hooks pour la gestion de la conformite et RGPD
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { Audit } from './types';

// ============================================================================
// LOCAL TYPES
// ============================================================================

export interface Policy {
  id: string;
  code: string;
  name: string;
  description?: string;
  type: 'SECURITY' | 'PRIVACY' | 'DATA_RETENTION' | 'ACCESS_CONTROL' | 'OTHER';
  version: string;
  status: 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
  effective_date?: string;
  review_date?: string;
  content?: string;
  is_mandatory: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuditListItem {
  id: string;
  code: string;
  name: string;
  type: 'INTERNAL' | 'EXTERNAL' | 'REGULATORY';
  status: 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  auditor?: string;
  planned_date?: string;
  completed_date?: string;
  findings_count: number;
  critical_findings: number;
  score?: number;
  report_url?: string;
  created_at: string;
}

export interface GDPRRequest {
  id: string;
  reference: string;
  type: 'ACCESS' | 'RECTIFICATION' | 'ERASURE' | 'PORTABILITY' | 'OBJECTION' | 'RESTRICTION';
  requester_name: string;
  requester_email: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED';
  request_date: string;
  due_date: string;
  completed_date?: string;
  notes?: string;
  created_at: string;
}

export interface Consent {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  consent_type: 'MARKETING' | 'ANALYTICS' | 'THIRD_PARTY' | 'NEWSLETTER' | 'TERMS';
  status: boolean;
  given_at?: string;
  withdrawn_at?: string;
  source: string;
  version: string;
}

export interface ComplianceStats {
  active_policies: number;
  pending_reviews: number;
  audits_year: number;
  open_findings: number;
  gdpr_requests_pending: number;
  gdpr_requests_completed: number;
  compliance_score: number;
  consent_rate: number;
}

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const complianceKeys = {
  all: ['compliance'] as const,

  // Stats
  stats: () => [...complianceKeys.all, 'stats'] as const,

  // Policies
  policies: () => [...complianceKeys.all, 'policies'] as const,
  policiesList: (filters?: { type?: string; status?: string }) =>
    [...complianceKeys.policies(), serializeFilters(filters)] as const,
  policyDetail: (id: string) => [...complianceKeys.policies(), id] as const,

  // Audits
  audits: () => [...complianceKeys.all, 'audits'] as const,
  auditsList: (filters?: { type?: string; status?: string }) =>
    [...complianceKeys.audits(), serializeFilters(filters)] as const,
  auditDetail: (id: string) => [...complianceKeys.audits(), id] as const,

  // GDPR
  gdpr: () => [...complianceKeys.all, 'gdpr'] as const,
  gdprList: (filters?: { type?: string; status?: string }) =>
    [...complianceKeys.gdpr(), serializeFilters(filters)] as const,

  // Consents
  consents: () => [...complianceKeys.all, 'consents'] as const,
  consentsList: (filters?: { consent_type?: string }) =>
    [...complianceKeys.consents(), serializeFilters(filters)] as const,
};

// ============================================================================
// STATS HOOKS
// ============================================================================

export const useComplianceStats = () => {
  return useQuery({
    queryKey: complianceKeys.stats(),
    queryFn: async () => {
      return api.get<ComplianceStats>('/compliance/stats').then(r => r.data);
    }
  });
};

// ============================================================================
// POLICY HOOKS
// ============================================================================

export const usePolicies = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: complianceKeys.policiesList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/compliance/policies?${queryString}` : '/compliance/policies';
      return api.get<Policy[]>(url).then(r => r.data);
    }
  });
};

export const usePolicy = (id: string) => {
  return useQuery({
    queryKey: complianceKeys.policyDetail(id),
    queryFn: async () => {
      return api.get<Policy>(`/compliance/policies/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreatePolicy = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Policy>) => {
      return api.post<Policy>('/compliance/policies', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: complianceKeys.policies() })
  });
};

export const useUpdatePolicy = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Policy> }) => {
      return api.put<Policy>(`/compliance/policies/${id}`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: complianceKeys.policies() })
  });
};

// ============================================================================
// AUDIT HOOKS
// ============================================================================

export const useAudits = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: complianceKeys.auditsList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/compliance/audits?${queryString}` : '/compliance/audits';
      return api.get<AuditListItem[]>(url).then(r => r.data);
    }
  });
};

export const useAudit = (id: string) => {
  return useQuery({
    queryKey: complianceKeys.auditDetail(id),
    queryFn: async () => {
      return api.get<Audit>(`/compliance/audits/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreateAudit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Audit>) => {
      return api.post<Audit>('/compliance/audits', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: complianceKeys.audits() })
  });
};

export const useStartAudit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Audit>(`/compliance/audits/${id}/start`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: complianceKeys.all })
  });
};

export const useCompleteAudit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Audit>(`/compliance/audits/${id}/complete`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: complianceKeys.all })
  });
};

// ============================================================================
// GDPR HOOKS
// ============================================================================

export const useGDPRRequests = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: complianceKeys.gdprList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/compliance/gdpr-requests?${queryString}` : '/compliance/gdpr-requests';
      return api.get<GDPRRequest[]>(url).then(r => r.data);
    }
  });
};

export const useUpdateGDPRStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch<void>(`/compliance/gdpr-requests/${id}/status`, { status }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: complianceKeys.gdpr() });
      queryClient.invalidateQueries({ queryKey: complianceKeys.stats() });
    }
  });
};

// ============================================================================
// CONSENT HOOKS
// ============================================================================

export const useConsents = (filters?: { consent_type?: string }) => {
  return useQuery({
    queryKey: complianceKeys.consentsList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.consent_type) params.append('consent_type', filters.consent_type);
      const queryString = params.toString();
      const url = queryString ? `/compliance/consents?${queryString}` : '/compliance/consents';
      return api.get<Consent[]>(url).then(r => r.data);
    }
  });
};
