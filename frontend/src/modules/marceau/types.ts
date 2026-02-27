/**
 * AZALSCORE Module - Marceau AI Assistant Types
 * Types TypeScript pour l'assistant IA Marceau
 */

// ============================================================================
// ENUMS
// ============================================================================

export type MarceauModule =
  | 'telephony'
  | 'email'
  | 'calendar'
  | 'social'
  | 'crm'
  | 'quotes'
  | 'appointments'
  | 'knowledge';

export type ActionStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'requires_validation';

export type ActionType =
  | 'answer_call'
  | 'transfer_call'
  | 'schedule_appointment'
  | 'create_quote'
  | 'send_email'
  | 'update_crm'
  | 'post_social'
  | 'lookup_info';

export type ConversationOutcome =
  | 'appointment_scheduled'
  | 'quote_sent'
  | 'information_provided'
  | 'transferred'
  | 'voicemail_left'
  | 'callback_requested'
  | 'no_action_needed';

export type ConversationIntent =
  | 'appointment_request'
  | 'quote_request'
  | 'information_request'
  | 'complaint'
  | 'follow_up'
  | 'other';

// ============================================================================
// CONFIGURATION
// ============================================================================

export interface TelephonyConfig {
  asterisk_ami_host: string;
  asterisk_ami_port: number;
  asterisk_ami_username: string;
  asterisk_ami_password: string;
  working_hours: {
    start: string;
    end: string;
  };
  overflow_threshold: number;
  overflow_number: string;
  appointment_duration_minutes: number;
  max_wait_days: number;
  use_travel_time: boolean;
  travel_buffer_minutes: number;
}

export interface IntegrationsConfig {
  ors_api_key?: string;
  gmail_credentials?: Record<string, unknown>;
  google_calendar_id?: string;
  linkedin_token?: string;
  facebook_token?: string;
  instagram_token?: string;
  slack_webhook?: string;
  hubspot_api_key?: string;
  wordpress_url?: string;
  wordpress_token?: string;
}

export interface MarceauConfig {
  id: string;
  tenant_id: string;
  enabled_modules: Record<MarceauModule, boolean>;
  autonomy_levels: Record<MarceauModule, number>;
  llm_temperature: number;
  llm_model: string;
  stt_model: string;
  tts_voice: string;
  telephony_config: TelephonyConfig;
  integrations: IntegrationsConfig;
  total_actions: number;
  total_conversations: number;
  total_quotes_created: number;
  total_appointments_scheduled: number;
  created_at: string;
  updated_at: string;
}

export interface MarceauConfigCreate {
  enabled_modules?: Record<string, boolean>;
  autonomy_levels?: Record<string, number>;
  llm_temperature?: number;
  llm_model?: string;
  stt_model?: string;
  tts_voice?: string;
  telephony_config?: Partial<TelephonyConfig>;
  integrations?: Partial<IntegrationsConfig>;
}

export interface MarceauConfigUpdate {
  enabled_modules?: Record<string, boolean>;
  autonomy_levels?: Record<string, number>;
  llm_temperature?: number;
  llm_model?: string;
  stt_model?: string;
  tts_voice?: string;
  telephony_config?: Partial<TelephonyConfig>;
  integrations?: Partial<IntegrationsConfig>;
}

// ============================================================================
// ACTION
// ============================================================================

export interface MarceauAction {
  id: string;
  tenant_id: string;
  module: MarceauModule;
  action_type: ActionType;
  status: ActionStatus;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  confidence_score: number;
  required_human_validation: boolean;
  validated_by?: string;
  validated_at?: string;
  validation_notes?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  conversation_id?: string;
  duration_seconds: number;
  tokens_used: number;
  error_message?: string;
  created_at: string;
}

export interface MarceauActionCreate {
  module: MarceauModule;
  action_type: ActionType;
  input_data?: Record<string, unknown>;
  confidence_score?: number;
  related_entity_type?: string;
  related_entity_id?: string;
  conversation_id?: string;
}

export interface ActionValidation {
  approved: boolean;
  notes?: string;
}

// ============================================================================
// CONVERSATION
// ============================================================================

export interface MarceauConversation {
  id: string;
  tenant_id: string;
  caller_phone: string;
  caller_name?: string;
  customer_id?: string;
  transcript?: string;
  summary?: string;
  intent?: ConversationIntent;
  duration_seconds: number;
  satisfaction_score?: number;
  outcome?: ConversationOutcome;
  recording_url?: string;
  asterisk_call_id?: string;
  transferred_to?: string;
  transfer_reason?: string;
  started_at: string;
  ended_at?: string;
  created_at: string;
}

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  audio_url?: string;
  confidence?: number;
}

// ============================================================================
// KNOWLEDGE BASE
// ============================================================================

export interface KnowledgeDocument {
  id: string;
  tenant_id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  embedding_id?: string;
  is_active: boolean;
  usage_count: number;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeDocumentCreate {
  title: string;
  content: string;
  category?: string;
  tags?: string[];
}

export interface KnowledgeSearch {
  query: string;
  category?: string;
  limit?: number;
}

export interface KnowledgeSearchResult {
  document: KnowledgeDocument;
  score: number;
  matched_excerpt: string;
}

// ============================================================================
// STATS & DASHBOARD
// ============================================================================

export interface MarceauStats {
  total_conversations: number;
  total_actions: number;
  actions_pending_validation: number;
  avg_conversation_duration: number;
  avg_satisfaction_score?: number;
  quotes_created_today: number;
  appointments_scheduled_today: number;
  success_rate: number;
  tokens_used_today: number;
}

export interface ConversationStats {
  total_conversations: number;
  avg_duration_seconds: number;
  avg_satisfaction_score?: number;
  outcomes_distribution: Record<string, number>;
  intents_distribution: Record<string, number>;
  calls_by_hour: Record<number, number>;
  calls_by_day: Record<string, number>;
}

export interface MarceauDashboard {
  stats: MarceauStats;
  recent_conversations: MarceauConversation[];
  pending_actions: MarceauAction[];
  conversation_stats: ConversationStats;
}

// ============================================================================
// VOICE
// ============================================================================

export interface VoiceConfig {
  voice_id: string;
  voice_name: string;
  language: string;
  speed: number;
  pitch: number;
}

export interface TTSRequest {
  text: string;
  voice_id?: string;
}

export interface STTResult {
  text: string;
  confidence: number;
  language: string;
  duration_seconds: number;
}

// ============================================================================
// LIST RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export type ActionListResponse = PaginatedResponse<MarceauAction>;
export type ConversationListResponse = PaginatedResponse<MarceauConversation>;
export type KnowledgeListResponse = PaginatedResponse<KnowledgeDocument>;

// ============================================================================
// FILTERS
// ============================================================================

export interface ActionFilters {
  module?: MarceauModule;
  action_type?: ActionType;
  status?: ActionStatus;
  requires_validation?: boolean;
  from_date?: string;
  to_date?: string;
  skip?: number;
  limit?: number;
}

export interface ConversationFilters {
  intent?: ConversationIntent;
  outcome?: ConversationOutcome;
  from_date?: string;
  to_date?: string;
  caller_phone?: string;
  customer_id?: string;
  min_duration?: number;
  max_duration?: number;
  skip?: number;
  limit?: number;
}

export interface KnowledgeFilters {
  category?: string;
  tags?: string[];
  is_active?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}
