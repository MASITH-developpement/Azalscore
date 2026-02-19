/**
 * AZALSCORE - Marceau AI API
 * ==========================
 * API client pour le module Marceau AI Assistant
 * Couvre: Actions IA, Conversations, Memoire, Configuration
 */

import { api } from '@/core/api-client';

// ============================================================================
// TYPES
// ============================================================================

export type ActionStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
export type ConversationStatus = 'active' | 'waiting' | 'closed';
export type DomainType =
  | 'commercial'
  | 'accounting'
  | 'hr'
  | 'production'
  | 'inventory'
  | 'crm'
  | 'support'
  | 'legal'
  | 'general';

export interface AIAction {
  id: string;
  type: string;
  domain: DomainType;
  description: string;
  status: ActionStatus;
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  status: ConversationStatus;
  domain?: DomainType;
  messages_count: number;
  last_message_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface MemoryItem {
  id: string;
  key: string;
  value: string;
  domain?: DomainType;
  expires_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface MarceauStats {
  total_actions: number;
  completed_actions: number;
  failed_actions: number;
  total_conversations: number;
  active_conversations: number;
  memory_items: number;
  avg_response_time_ms: number;
}

export interface MarceauConfig {
  enabled_domains: DomainType[];
  auto_response: boolean;
  response_delay_ms: number;
  max_context_messages: number;
  memory_retention_days: number;
  temperature: number;
}

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface ActionFilters {
  status?: ActionStatus;
  domain?: DomainType;
  type?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface ConversationFilters {
  status?: ConversationStatus;
  domain?: DomainType;
  page?: number;
  page_size?: number;
}

export interface ActionCreate {
  type: string;
  domain: DomainType;
  description?: string;
  input_data?: Record<string, unknown>;
}

export interface MessageCreate {
  content: string;
  metadata?: Record<string, unknown>;
}

export interface MemoryItemCreate {
  key: string;
  value: string;
  domain?: DomainType;
  expires_at?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/marceau';

function buildQueryString<T extends object>(params: T): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// API CLIENT
// ============================================================================

export const marceauApi = {
  // ==========================================================================
  // Stats & Dashboard
  // ==========================================================================

  /**
   * Recupere les statistiques Marceau
   */
  getStats: () =>
    api.get<MarceauStats>(`${BASE_PATH}/stats`),

  /**
   * Recupere la configuration
   */
  getConfig: () =>
    api.get<MarceauConfig>(`${BASE_PATH}/config`),

  /**
   * Met a jour la configuration
   */
  updateConfig: (data: Partial<MarceauConfig>) =>
    api.put<MarceauConfig>(`${BASE_PATH}/config`, data),

  // ==========================================================================
  // Actions
  // ==========================================================================

  /**
   * Liste les actions
   */
  listActions: (filters?: ActionFilters) =>
    api.get<PaginatedResponse<AIAction>>(
      `${BASE_PATH}/actions${buildQueryString(filters || {})}`
    ),

  /**
   * Recupere une action par son ID
   */
  getAction: (id: string) =>
    api.get<AIAction>(`${BASE_PATH}/actions/${id}`),

  /**
   * Cree une nouvelle action
   */
  createAction: (data: ActionCreate) =>
    api.post<AIAction>(`${BASE_PATH}/actions`, data),

  /**
   * Annule une action
   */
  cancelAction: (id: string) =>
    api.post<AIAction>(`${BASE_PATH}/actions/${id}/cancel`, {}),

  /**
   * Relance une action echouee
   */
  retryAction: (id: string) =>
    api.post<AIAction>(`${BASE_PATH}/actions/${id}/retry`, {}),

  // ==========================================================================
  // Conversations
  // ==========================================================================

  /**
   * Liste les conversations
   */
  listConversations: (filters?: ConversationFilters) =>
    api.get<PaginatedResponse<Conversation>>(
      `${BASE_PATH}/conversations${buildQueryString(filters || {})}`
    ),

  /**
   * Recupere une conversation par son ID
   */
  getConversation: (id: string) =>
    api.get<Conversation>(`${BASE_PATH}/conversations/${id}`),

  /**
   * Cree une nouvelle conversation
   */
  createConversation: (title?: string, domain?: DomainType) =>
    api.post<Conversation>(`${BASE_PATH}/conversations`, { title, domain }),

  /**
   * Ferme une conversation
   */
  closeConversation: (id: string) =>
    api.post<Conversation>(`${BASE_PATH}/conversations/${id}/close`, {}),

  /**
   * Supprime une conversation
   */
  deleteConversation: (id: string) =>
    api.delete(`${BASE_PATH}/conversations/${id}`),

  // ==========================================================================
  // Messages
  // ==========================================================================

  /**
   * Liste les messages d'une conversation
   */
  listMessages: (conversationId: string) =>
    api.get<Message[]>(`${BASE_PATH}/conversations/${conversationId}/messages`),

  /**
   * Envoie un message et recoit une reponse
   */
  sendMessage: (conversationId: string, data: MessageCreate) =>
    api.post<{ user_message: Message; assistant_message: Message }>(
      `${BASE_PATH}/conversations/${conversationId}/messages`,
      data
    ),

  // ==========================================================================
  // Memory
  // ==========================================================================

  /**
   * Liste les elements de memoire
   */
  listMemory: (domain?: DomainType) =>
    api.get<MemoryItem[]>(
      `${BASE_PATH}/memory${domain ? `?domain=${domain}` : ''}`
    ),

  /**
   * Recupere un element de memoire par sa cle
   */
  getMemoryItem: (key: string) =>
    api.get<MemoryItem>(`${BASE_PATH}/memory/${key}`),

  /**
   * Cree ou met a jour un element de memoire
   */
  setMemoryItem: (data: MemoryItemCreate) =>
    api.post<MemoryItem>(`${BASE_PATH}/memory`, data),

  /**
   * Supprime un element de memoire
   */
  deleteMemoryItem: (key: string) =>
    api.delete(`${BASE_PATH}/memory/${key}`),

  /**
   * Vide la memoire (optionnellement par domaine)
   */
  clearMemory: (domain?: DomainType) =>
    api.delete(`${BASE_PATH}/memory${domain ? `?domain=${domain}` : ''}`),

  // ==========================================================================
  // Quick Actions (raccourcis pour actions courantes)
  // ==========================================================================

  /**
   * Pose une question rapide
   */
  ask: (question: string, domain?: DomainType) =>
    api.post<{ answer: string; sources?: string[] }>(`${BASE_PATH}/ask`, {
      question,
      domain,
    }),

  /**
   * Resume un document ou texte
   */
  summarize: (text: string) =>
    api.post<{ summary: string }>(`${BASE_PATH}/summarize`, { text }),

  /**
   * Extrait des informations d'un document
   */
  extract: (documentId: string, fields: string[]) =>
    api.post<Record<string, unknown>>(`${BASE_PATH}/extract`, {
      document_id: documentId,
      fields,
    }),
};

export default marceauApi;
