/**
 * AZALSCORE - Marceau AI Assistant React Query Hooks
 * ===================================================
 * Hooks pour le module Marceau (Assistant IA)
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@core/api-client';

// ============================================================================
// TYPES
// ============================================================================

export interface DashboardStats {
  total_actions_today: number;
  total_conversations_today: number;
  pending_validations: number;
  avg_confidence_score: number;
  llm_configured?: boolean;
  llm_provider?: string | null;
}

export interface ChatMessageRequest {
  message: string;
  conversation_id?: string | null;
}

export interface ChatMessageResponse {
  message: string;
  conversation_id: string;
  intent: string | null;
  confidence: number;
  action_created?: {
    id: string;
    action_type: string;
    status: string;
  };
}

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const marceauKeys = {
  all: ['marceau'] as const,
  dashboard: () => [...marceauKeys.all, 'dashboard'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

export const useMarceauDashboard = () => {
  return useQuery({
    queryKey: marceauKeys.dashboard(),
    queryFn: async () => {
      try {
        const response = await api.get<DashboardStats>('/marceau/dashboard');
        return response.data;
      } catch {
        return null;
      }
    },
  });
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

export const useSendMarceauMessage = () => {
  return useMutation({
    mutationFn: async (data: ChatMessageRequest) => {
      const response = await api.post<ChatMessageResponse>('/marceau/chat/message', data);
      return response.data;
    },
  });
};
