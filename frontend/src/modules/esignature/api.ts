/**
 * AZALSCORE - E-Signature API
 * ===========================
 * Complete typed API client for Electronic Signature module.
 * Covers: Envelopes, Signers, Documents, Templates, Audit Trail
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const esignatureKeys = {
  all: ['esignature'] as const,
  envelopes: () => [...esignatureKeys.all, 'envelopes'] as const,
  envelope: (id: string) => [...esignatureKeys.envelopes(), id] as const,
  signers: (envelopeId: string) => [...esignatureKeys.envelope(envelopeId), 'signers'] as const,
  documents: (envelopeId: string) => [...esignatureKeys.envelope(envelopeId), 'documents'] as const,
  audit: (envelopeId: string) => [...esignatureKeys.envelope(envelopeId), 'audit'] as const,
  templates: () => [...esignatureKeys.all, 'templates'] as const,
  config: () => [...esignatureKeys.all, 'config'] as const,
  stats: () => [...esignatureKeys.all, 'stats'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type SignatureProvider = 'internal' | 'yousign' | 'docusign' | 'hellosign' | 'adobe_sign';
export type SignatureLevel = 'simple' | 'advanced' | 'qualified';

export type EnvelopeStatus =
  | 'draft' | 'pending_approval' | 'approved' | 'sent'
  | 'in_progress' | 'completed' | 'declined'
  | 'expired' | 'cancelled' | 'voided';

export type SignerStatus =
  | 'pending' | 'notified' | 'viewed'
  | 'signed' | 'declined' | 'delegated' | 'expired';

export type DocumentType =
  | 'contract' | 'invoice' | 'quote' | 'purchase_order'
  | 'nda' | 'employment' | 'amendment' | 'mandate'
  | 'gdpr_consent' | 'lease' | 'loan' | 'policy' | 'other';

export type FieldType =
  | 'signature' | 'initials' | 'date' | 'text'
  | 'checkbox' | 'radio' | 'dropdown' | 'attachment' | 'company_stamp';

export type AuthMethod =
  | 'email' | 'sms_otp' | 'email_otp'
  | 'id_verification' | 'knowledge_based' | 'two_factor';

export type TemplateCategory =
  | 'sales' | 'hr' | 'legal' | 'finance'
  | 'procurement' | 'operations' | 'custom';

export type AuditEventType =
  | 'created' | 'sent' | 'viewed' | 'signed' | 'declined'
  | 'delegated' | 'reminder_sent' | 'downloaded'
  | 'cancelled' | 'expired' | 'completed' | 'voided';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface Envelope {
  id: string;
  tenant_id: string;
  reference: string;
  title: string;
  description?: string | null;
  document_type: DocumentType;
  status: EnvelopeStatus;
  signature_level: SignatureLevel;
  provider: SignatureProvider;
  expires_at?: string | null;
  completed_at?: string | null;
  created_by: string;
  requires_approval: boolean;
  approved_by?: string | null;
  approved_at?: string | null;
  external_id?: string | null;
  callback_url?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Signer {
  id: string;
  envelope_id: string;
  email: string;
  name: string;
  phone?: string | null;
  role?: string | null;
  order: number;
  status: SignerStatus;
  auth_method: AuthMethod;
  viewed_at?: string | null;
  signed_at?: string | null;
  declined_at?: string | null;
  decline_reason?: string | null;
  delegated_to?: string | null;
  delegated_at?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  signature_image?: string | null;
  external_id?: string | null;
}

export interface EnvelopeDocument {
  id: string;
  envelope_id: string;
  name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  page_count?: number | null;
  is_template: boolean;
  order: number;
  signed_file_path?: string | null;
  external_id?: string | null;
  created_at: string;
}

export interface SignatureField {
  id: string;
  document_id: string;
  signer_id: string;
  field_type: FieldType;
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
  required: boolean;
  placeholder?: string | null;
  value?: string | null;
  filled_at?: string | null;
}

export interface AuditEvent {
  id: string;
  envelope_id: string;
  event_type: AuditEventType;
  actor_email?: string | null;
  actor_name?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  details?: Record<string, unknown> | null;
  created_at: string;
}

export interface SignatureTemplate {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  category: TemplateCategory;
  document_type: DocumentType;
  file_path?: string | null;
  default_signers: { role: string; order: number }[];
  default_fields: Omit<SignatureField, 'id' | 'document_id' | 'signer_id' | 'filled_at' | 'value'>[];
  is_active: boolean;
  created_at: string;
}

export interface ESignatureConfig {
  id: string;
  tenant_id: string;
  default_provider: SignatureProvider;
  default_signature_level: SignatureLevel;
  default_expiry_days: number;
  max_expiry_days: number;
  auto_reminders_enabled: boolean;
  reminder_interval_days: number;
  max_reminders: number;
  notify_on_view: boolean;
  notify_on_sign: boolean;
  notify_on_complete: boolean;
  notify_on_decline: boolean;
  require_auth_before_view: boolean;
  allow_decline: boolean;
  allow_delegation: boolean;
  require_approval_before_send: boolean;
  company_logo_url?: string | null;
  primary_color: string;
  email_footer?: string | null;
}

export interface ESignatureStats {
  total_envelopes: number;
  completed_envelopes: number;
  pending_envelopes: number;
  average_completion_time_hours: number;
  by_status: Record<EnvelopeStatus, number>;
  by_document_type: Record<DocumentType, number>;
  completion_rate: number;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface EnvelopeCreate {
  title: string;
  description?: string;
  document_type: DocumentType;
  signature_level?: SignatureLevel;
  provider?: SignatureProvider;
  expires_in_days?: number;
  requires_approval?: boolean;
  callback_url?: string;
  metadata?: Record<string, unknown>;
}

export interface SignerCreate {
  email: string;
  name: string;
  phone?: string;
  role?: string;
  order?: number;
  auth_method?: AuthMethod;
}

export interface FieldCreate {
  signer_id: string;
  field_type: FieldType;
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
  required?: boolean;
  placeholder?: string;
}

// ============================================================================
// HOOKS - ENVELOPES
// ============================================================================

export function useEnvelopes(filters?: {
  status?: EnvelopeStatus;
  document_type?: DocumentType;
  created_by?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...esignatureKeys.envelopes(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.document_type) params.append('document_type', filters.document_type);
      if (filters?.created_by) params.append('created_by', filters.created_by);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Envelope[]; total: number }>(
        `/esignature/envelopes${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useEnvelope(id: string) {
  return useQuery({
    queryKey: esignatureKeys.envelope(id),
    queryFn: async () => {
      const response = await api.get<Envelope>(`/esignature/envelopes/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateEnvelope() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: EnvelopeCreate) => {
      return api.post<Envelope>('/esignature/envelopes', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.envelopes() });
    },
  });
}

export function useDeleteEnvelope() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/esignature/envelopes/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.envelopes() });
    },
  });
}

export function useSendEnvelope() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, message }: { id: string; message?: string }) => {
      return api.post(`/esignature/envelopes/${id}/send`, { message });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.envelopes() });
      queryClient.invalidateQueries({ queryKey: esignatureKeys.envelope(id) });
    },
  });
}

export function useCancelEnvelope() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      return api.post(`/esignature/envelopes/${id}/cancel`, { reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.envelopes() });
      queryClient.invalidateQueries({ queryKey: esignatureKeys.envelope(id) });
    },
  });
}

export function useResendEnvelope() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, signerIds }: { id: string; signerIds?: string[] }) => {
      return api.post(`/esignature/envelopes/${id}/resend`, { signer_ids: signerIds });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.envelope(id) });
    },
  });
}

// ============================================================================
// HOOKS - SIGNERS
// ============================================================================

export function useEnvelopeSigners(envelopeId: string) {
  return useQuery({
    queryKey: esignatureKeys.signers(envelopeId),
    queryFn: async () => {
      const response = await api.get<{ items: Signer[] }>(
        `/esignature/envelopes/${envelopeId}/signers`
      );
      return response;
    },
    enabled: !!envelopeId,
  });
}

export function useAddSigner() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ envelopeId, data }: { envelopeId: string; data: SignerCreate }) => {
      return api.post<Signer>(`/esignature/envelopes/${envelopeId}/signers`, data);
    },
    onSuccess: (_, { envelopeId }) => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.signers(envelopeId) });
    },
  });
}

export function useRemoveSigner() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ envelopeId, signerId }: { envelopeId: string; signerId: string }) => {
      return api.delete(`/esignature/envelopes/${envelopeId}/signers/${signerId}`);
    },
    onSuccess: (_, { envelopeId }) => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.signers(envelopeId) });
    },
  });
}

export function useGetSigningUrl() {
  return useMutation({
    mutationFn: async ({ envelopeId, signerId }: { envelopeId: string; signerId: string }) => {
      return api.get<{ url: string; expires_at: string }>(
        `/esignature/envelopes/${envelopeId}/signers/${signerId}/signing-url`
      );
    },
  });
}

// ============================================================================
// HOOKS - DOCUMENTS
// ============================================================================

export function useEnvelopeDocuments(envelopeId: string) {
  return useQuery({
    queryKey: esignatureKeys.documents(envelopeId),
    queryFn: async () => {
      const response = await api.get<{ items: EnvelopeDocument[] }>(
        `/esignature/envelopes/${envelopeId}/documents`
      );
      return response;
    },
    enabled: !!envelopeId,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ envelopeId, file }: { envelopeId: string; file: File }) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post<EnvelopeDocument>(`/esignature/envelopes/${envelopeId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: (_, { envelopeId }) => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.documents(envelopeId) });
    },
  });
}

export function useDownloadSignedDocument() {
  return useMutation({
    mutationFn: async ({ envelopeId, documentId }: { envelopeId: string; documentId: string }) => {
      return api.get<Blob>(`/esignature/envelopes/${envelopeId}/documents/${documentId}/download`, {
        responseType: 'blob',
      });
    },
  });
}

// ============================================================================
// HOOKS - SIGNATURE FIELDS
// ============================================================================

export function useAddSignatureField() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      envelopeId,
      documentId,
      data,
    }: {
      envelopeId: string;
      documentId: string;
      data: FieldCreate;
    }) => {
      return api.post<SignatureField>(
        `/esignature/envelopes/${envelopeId}/documents/${documentId}/fields`,
        data
      );
    },
    onSuccess: (_, { envelopeId }) => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.documents(envelopeId) });
    },
  });
}

// ============================================================================
// HOOKS - AUDIT TRAIL
// ============================================================================

export function useEnvelopeAuditTrail(envelopeId: string) {
  return useQuery({
    queryKey: esignatureKeys.audit(envelopeId),
    queryFn: async () => {
      const response = await api.get<{ items: AuditEvent[] }>(
        `/esignature/envelopes/${envelopeId}/audit`
      );
      return response;
    },
    enabled: !!envelopeId,
  });
}

export function useDownloadAuditCertificate() {
  return useMutation({
    mutationFn: async (envelopeId: string) => {
      return api.get<Blob>(`/esignature/envelopes/${envelopeId}/audit/certificate`, {
        responseType: 'blob',
      });
    },
  });
}

// ============================================================================
// HOOKS - TEMPLATES
// ============================================================================

export function useSignatureTemplates(category?: TemplateCategory) {
  return useQuery({
    queryKey: [...esignatureKeys.templates(), category],
    queryFn: async () => {
      const params = category ? `?category=${category}` : '';
      const response = await api.get<{ items: SignatureTemplate[] }>(
        `/esignature/templates${params}`
      );
      return response;
    },
  });
}

export function useCreateFromTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { template_id: string; title: string; signers: SignerCreate[] }) => {
      return api.post<Envelope>('/esignature/envelopes/from-template', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.envelopes() });
    },
  });
}

// ============================================================================
// HOOKS - CONFIG & STATS
// ============================================================================

export function useESignatureConfig() {
  return useQuery({
    queryKey: esignatureKeys.config(),
    queryFn: async () => {
      const response = await api.get<ESignatureConfig>('/esignature/config');
      return response;
    },
  });
}

export function useUpdateESignatureConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<ESignatureConfig>) => {
      return api.put<ESignatureConfig>('/esignature/config', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: esignatureKeys.config() });
    },
  });
}

export function useESignatureStats() {
  return useQuery({
    queryKey: esignatureKeys.stats(),
    queryFn: async () => {
      const response = await api.get<ESignatureStats>('/esignature/stats');
      return response;
    },
  });
}
