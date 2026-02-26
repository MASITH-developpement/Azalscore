/**
 * AZALSCORE - AI Assistant API
 * ============================
 * Complete typed API client for AI Assistant module.
 * Covers: Conversations, Analysis, Predictions, Risk Alerts, Decision Support
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const aiKeys = {
  all: ['ai'] as const,
  conversations: () => [...aiKeys.all, 'conversations'] as const,
  conversation: (id: string) => [...aiKeys.conversations(), id] as const,
  messages: (conversationId: string) => [...aiKeys.conversation(conversationId), 'messages'] as const,
  analysis: () => [...aiKeys.all, 'analysis'] as const,
  predictions: () => [...aiKeys.all, 'predictions'] as const,
  risks: () => [...aiKeys.all, 'risks'] as const,
  decisions: () => [...aiKeys.all, 'decisions'] as const,
  stats: () => [...aiKeys.all, 'stats'] as const,
  config: () => [...aiKeys.all, 'config'] as const,
};

// ============================================================================
// TYPES - CONVERSATIONS
// ============================================================================

export interface Conversation {
  id: string;
  tenant_id: string;
  user_id: string;
  title: string;
  context?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface ConversationCreate {
  title?: string;
  context?: Record<string, unknown>;
}

export interface MessageCreate {
  content: string;
  context?: Record<string, unknown>;
}

// ============================================================================
// TYPES - ANALYSIS
// ============================================================================

export interface AnalysisRequest {
  data: Record<string, unknown>;
  analysis_type: 'trend' | 'anomaly' | 'forecast' | 'summary';
  options?: Record<string, unknown>;
}

export interface AnalysisResponse {
  id: string;
  analysis_type: string;
  result: Record<string, unknown>;
  confidence: number;
  insights: string[];
  recommendations: string[];
  created_at: string;
}

// ============================================================================
// TYPES - PREDICTIONS
// ============================================================================

export interface PredictionRequest {
  metric: string;
  horizon_days: number;
  include_confidence?: boolean;
}

export interface PredictionResponse {
  id: string;
  metric: string;
  predictions: {
    date: string;
    value: number;
    lower_bound?: number;
    upper_bound?: number;
  }[];
  confidence: number;
  model_used: string;
  created_at: string;
}

// ============================================================================
// TYPES - RISK ALERTS
// ============================================================================

export type RiskSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type RiskStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';

export interface RiskAlert {
  id: string;
  tenant_id: string;
  title: string;
  description: string;
  severity: RiskSeverity;
  status: RiskStatus;
  category: string;
  source: string;
  affected_entity?: string | null;
  recommendations: string[];
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RiskAlertCreate {
  title: string;
  description: string;
  severity: RiskSeverity;
  category: string;
  source?: string;
  affected_entity?: string;
  recommendations?: string[];
}

// ============================================================================
// TYPES - DECISION SUPPORT
// ============================================================================

export interface DecisionSupport {
  id: string;
  tenant_id: string;
  user_id: string;
  question: string;
  context: Record<string, unknown>;
  analysis: Record<string, unknown>;
  recommendations: string[];
  confidence: number;
  requires_confirmation: boolean;
  confirmed: boolean;
  confirmed_by?: string | null;
  confirmed_at?: string | null;
  created_at: string;
}

export interface DecisionSupportCreate {
  question: string;
  context?: Record<string, unknown>;
}

// ============================================================================
// TYPES - STATS & CONFIG
// ============================================================================

export interface AIStats {
  total_conversations: number;
  total_messages: number;
  avg_response_time_ms: number;
  active_risks: number;
  predictions_made: number;
  decisions_supported: number;
  satisfaction_rate: number;
}

export interface AIConfig {
  model: string;
  temperature: number;
  max_tokens: number;
  auto_analysis: boolean;
  risk_threshold: number;
  features_enabled: string[];
}

// ============================================================================
// HOOKS - CONVERSATIONS
// ============================================================================

export function useConversations() {
  return useQuery({
    queryKey: aiKeys.conversations(),
    queryFn: async () => {
      const response = await api.get<{ items: Conversation[]; total: number }>('/ai/conversations');
      return response;
    },
  });
}

export function useConversation(id: string) {
  return useQuery({
    queryKey: aiKeys.conversation(id),
    queryFn: async () => {
      const response = await api.get<Conversation>(`/ai/conversations/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useConversationMessages(conversationId: string) {
  return useQuery({
    queryKey: aiKeys.messages(conversationId),
    queryFn: async () => {
      const response = await api.get<{ items: Message[] }>(`/ai/conversations/${conversationId}/messages`);
      return response;
    },
    enabled: !!conversationId,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ConversationCreate) => {
      return api.post<Conversation>('/ai/conversations', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiKeys.conversations() });
    },
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ conversationId, data }: { conversationId: string; data: MessageCreate }) => {
      return api.post<Message>(`/ai/conversations/${conversationId}/messages`, data);
    },
    onSuccess: (_, { conversationId }) => {
      queryClient.invalidateQueries({ queryKey: aiKeys.messages(conversationId) });
    },
  });
}

// ============================================================================
// HOOKS - QUICK QUESTION (Sans conversation)
// ============================================================================

export function useAskQuestion() {
  return useMutation({
    mutationFn: async (data: { question: string; context?: Record<string, unknown> }) => {
      return api.post<{ answer: string; confidence: number; sources: string[] }>('/ai/ask', data);
    },
  });
}

// ============================================================================
// HOOKS - ANALYSIS
// ============================================================================

export function useRequestAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: AnalysisRequest) => {
      return api.post<AnalysisResponse>('/ai/analysis', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiKeys.analysis() });
    },
  });
}

export function useAnalysisHistory() {
  return useQuery({
    queryKey: aiKeys.analysis(),
    queryFn: async () => {
      const response = await api.get<{ items: AnalysisResponse[] }>('/ai/analysis/history');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - PREDICTIONS
// ============================================================================

export function useRequestPrediction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: PredictionRequest) => {
      return api.post<PredictionResponse>('/ai/predictions', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiKeys.predictions() });
    },
  });
}

export function usePredictions() {
  return useQuery({
    queryKey: aiKeys.predictions(),
    queryFn: async () => {
      const response = await api.get<{ items: PredictionResponse[] }>('/ai/predictions');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - RISK ALERTS
// ============================================================================

export function useRiskAlerts(filters?: { status?: RiskStatus; severity?: RiskSeverity }) {
  return useQuery({
    queryKey: [...aiKeys.risks(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.severity) params.append('severity', filters.severity);
      const queryString = params.toString();
      const response = await api.get<{ items: RiskAlert[]; total: number }>(
        `/ai/risks${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useAcknowledgeRisk() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes?: string }) => {
      return api.post(`/ai/risks/${id}/acknowledge`, { notes });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiKeys.risks() });
    },
  });
}

export function useResolveRisk() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, resolution }: { id: string; resolution: string }) => {
      return api.post(`/ai/risks/${id}/resolve`, { resolution });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiKeys.risks() });
    },
  });
}

// ============================================================================
// HOOKS - DECISION SUPPORT
// ============================================================================

export function useDecisionSupport() {
  return useQuery({
    queryKey: aiKeys.decisions(),
    queryFn: async () => {
      const response = await api.get<{ items: DecisionSupport[] }>('/ai/decisions');
      return response;
    },
  });
}

export function useRequestDecisionSupport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: DecisionSupportCreate) => {
      return api.post<DecisionSupport>('/ai/decisions', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiKeys.decisions() });
    },
  });
}

export function useConfirmDecision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, confirmed }: { id: string; confirmed: boolean }) => {
      return api.post(`/ai/decisions/${id}/confirm`, { confirmed });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiKeys.decisions() });
    },
  });
}

// ============================================================================
// HOOKS - STATS & CONFIG
// ============================================================================

export function useAIStats() {
  return useQuery({
    queryKey: aiKeys.stats(),
    queryFn: async () => {
      const response = await api.get<AIStats>('/ai/stats');
      return response;
    },
  });
}

export function useAIConfig() {
  return useQuery({
    queryKey: aiKeys.config(),
    queryFn: async () => {
      const response = await api.get<AIConfig>('/ai/config');
      return response;
    },
  });
}

export function useUpdateAIConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<AIConfig>) => {
      return api.put<AIConfig>('/ai/config', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiKeys.config() });
    },
  });
}

// ============================================================================
// HOOKS - SYNTHESIS
// ============================================================================

export function useGenerateSynthesis() {
  return useMutation({
    mutationFn: async (data: { topic: string; data_sources: string[]; format?: 'brief' | 'detailed' }) => {
      return api.post<{ synthesis: string; sources_used: string[]; generated_at: string }>(
        '/ai/synthesis',
        data
      );
    },
  });
}

// ============================================================================
// HOOKS - HEALTH CHECK
// ============================================================================

export function useAIHealth() {
  return useQuery({
    queryKey: [...aiKeys.all, 'health'],
    queryFn: async () => {
      const response = await api.get<{ status: string; models_available: string[]; latency_ms: number }>(
        '/ai/health'
      );
      return response;
    },
    refetchInterval: 60000, // Refresh every minute
  });
}
