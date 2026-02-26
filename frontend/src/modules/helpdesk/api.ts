/**
 * AZALSCORE - Helpdesk API
 * =========================
 * Client API typé pour le système de support client
 */

import { api } from '@core/api-client';

// ============================================================================
// HELPERS
// ============================================================================

function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const str = query.toString();
  return str ? `?${str}` : '';
}

// ============================================================================
// ENUMS
// ============================================================================

export type TicketStatus = 'OPEN' | 'PENDING' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED' | 'CANCELLED';
export type TicketPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT' | 'CRITICAL';
export type AgentStatus = 'ONLINE' | 'AWAY' | 'BUSY' | 'OFFLINE';
export type TicketSource = 'WEB' | 'EMAIL' | 'PHONE' | 'CHAT' | 'API';

// ============================================================================
// TYPES - Categories
// ============================================================================

export interface Category {
  id: number;
  tenant_id: string;
  name: string;
  slug: string;
  description: string | null;
  parent_id: number | null;
  icon: string | null;
  color: string | null;
  is_active: boolean;
  is_public: boolean;
  sort_order: number;
  created_at: string;
}

export interface CategoryCreate {
  name: string;
  slug?: string;
  description?: string | null;
  parent_id?: number | null;
  icon?: string | null;
  color?: string | null;
  is_public?: boolean;
  sort_order?: number;
}

export type CategoryUpdate = Partial<CategoryCreate> & { is_active?: boolean };

// ============================================================================
// TYPES - Tickets
// ============================================================================

export interface Ticket {
  id: number;
  tenant_id: string;
  ticket_number: string;
  subject: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  source: TicketSource;
  category_id: number | null;
  category_name: string | null;
  requester_email: string;
  requester_name: string;
  requester_phone: string | null;
  contact_id: number | null;
  assigned_agent_id: number | null;
  assigned_agent_name: string | null;
  assigned_team_id: number | null;
  sla_response_due: string | null;
  sla_resolution_due: string | null;
  first_response_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  tags: string[];
  attachments_count: number;
  replies_count: number;
  satisfaction_rating: number | null;
  is_escalated: boolean;
  created_at: string;
  updated_at: string;
}

export interface TicketCreate {
  subject: string;
  description: string;
  priority?: TicketPriority;
  source?: TicketSource;
  category_id?: number | null;
  requester_email: string;
  requester_name: string;
  requester_phone?: string | null;
  contact_id?: number | null;
  assigned_agent_id?: number | null;
  assigned_team_id?: number | null;
  tags?: string[];
}

export interface TicketUpdate {
  subject?: string;
  description?: string;
  priority?: TicketPriority;
  category_id?: number | null;
  tags?: string[];
}

export interface TicketAssign {
  agent_id?: number | null;
  team_id?: number | null;
}

export interface TicketListResponse {
  items: Ticket[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ============================================================================
// TYPES - Replies
// ============================================================================

export interface Attachment {
  id: number;
  file_name: string;
  file_size: number;
  mime_type: string;
  url: string;
  created_at: string;
}

export interface Reply {
  id: number;
  ticket_id: number;
  author_type: 'AGENT' | 'CUSTOMER' | 'SYSTEM';
  author_id: number | null;
  author_name: string;
  content: string;
  is_internal: boolean;
  attachments: Attachment[];
  created_at: string;
}

export interface ReplyCreate {
  ticket_id: number;
  content: string;
  is_internal?: boolean;
}

// ============================================================================
// TYPES - Agents & Teams
// ============================================================================

export interface Agent {
  id: number;
  tenant_id: string;
  user_id: number;
  name: string;
  email: string;
  status: AgentStatus;
  team_ids: number[];
  max_tickets: number;
  current_tickets: number;
  is_active: boolean;
  created_at: string;
}

export interface AgentCreate {
  user_id: number;
  team_ids?: number[];
  max_tickets?: number;
}

export interface AgentUpdate {
  team_ids?: number[];
  max_tickets?: number;
  is_active?: boolean;
}

export interface Team {
  id: number;
  tenant_id: string;
  name: string;
  description: string | null;
  lead_agent_id: number | null;
  members_count: number;
  is_active: boolean;
  created_at: string;
}

export interface TeamCreate {
  name: string;
  description?: string | null;
  lead_agent_id?: number | null;
}

export type TeamUpdate = Partial<TeamCreate> & { is_active?: boolean };

// ============================================================================
// TYPES - SLA
// ============================================================================

export interface SLA {
  id: number;
  tenant_id: string;
  name: string;
  description: string | null;
  priorities: Record<TicketPriority, {
    response_time_hours: number;
    resolution_time_hours: number;
  }>;
  business_hours_only: boolean;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
}

export interface SLACreate {
  name: string;
  description?: string | null;
  priorities: Record<TicketPriority, {
    response_time_hours: number;
    resolution_time_hours: number;
  }>;
  business_hours_only?: boolean;
  is_default?: boolean;
}

export type SLAUpdate = Partial<SLACreate> & { is_active?: boolean };

// ============================================================================
// TYPES - Knowledge Base
// ============================================================================

export interface KBCategory {
  id: number;
  tenant_id: string;
  name: string;
  slug: string;
  description: string | null;
  parent_id: number | null;
  articles_count: number;
  is_public: boolean;
  sort_order: number;
  created_at: string;
}

export interface KBCategoryCreate {
  name: string;
  slug?: string;
  description?: string | null;
  parent_id?: number | null;
  is_public?: boolean;
  sort_order?: number;
}

export interface KBArticle {
  id: number;
  tenant_id: string;
  category_id: number;
  category_name: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string | null;
  author_id: number;
  author_name: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  is_featured: boolean;
  view_count: number;
  helpful_yes: number;
  helpful_no: number;
  tags: string[];
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export interface KBArticleCreate {
  category_id: number;
  title: string;
  slug?: string;
  content: string;
  excerpt?: string | null;
  status?: 'DRAFT' | 'PUBLISHED';
  is_featured?: boolean;
  tags?: string[];
}

export type KBArticleUpdate = Partial<KBArticleCreate>;

// ============================================================================
// TYPES - Canned Responses
// ============================================================================

export interface CannedResponse {
  id: number;
  tenant_id: string;
  name: string;
  category: string | null;
  content: string;
  shortcut: string | null;
  is_shared: boolean;
  created_by: number;
  usage_count: number;
  created_at: string;
}

export interface CannedResponseCreate {
  name: string;
  category?: string | null;
  content: string;
  shortcut?: string | null;
  is_shared?: boolean;
}

// ============================================================================
// TYPES - Automations
// ============================================================================

export interface Automation {
  id: number;
  tenant_id: string;
  name: string;
  description: string | null;
  trigger_event: string;
  conditions: Array<{
    field: string;
    operator: string;
    value: unknown;
  }>;
  actions: Array<{
    type: string;
    params: Record<string, unknown>;
  }>;
  is_active: boolean;
  execution_count: number;
  created_at: string;
}

export interface AutomationCreate {
  name: string;
  description?: string | null;
  trigger_event: string;
  conditions: Array<{
    field: string;
    operator: string;
    value: unknown;
  }>;
  actions: Array<{
    type: string;
    params: Record<string, unknown>;
  }>;
  is_active?: boolean;
}

// ============================================================================
// TYPES - Satisfaction
// ============================================================================

export interface SatisfactionSurvey {
  id: number;
  ticket_id: number;
  rating: number;
  comment: string | null;
  submitted_at: string;
}

export interface SatisfactionCreate {
  ticket_id: number;
  rating: number;
  comment?: string | null;
}

// ============================================================================
// TYPES - Dashboard & Stats
// ============================================================================

export interface HelpdeskDashboard {
  tickets_open: number;
  tickets_pending: number;
  tickets_resolved_today: number;
  avg_response_time_hours: number;
  avg_resolution_time_hours: number;
  sla_compliance_rate: number;
  satisfaction_rating: number;
  agents_online: number;
  tickets_by_priority: Record<TicketPriority, number>;
  tickets_by_category: Array<{ category_id: number; category_name: string; count: number }>;
  recent_tickets: Ticket[];
}

export interface TicketStats {
  total: number;
  by_status: Record<TicketStatus, number>;
  by_priority: Record<TicketPriority, number>;
  created_today: number;
  resolved_today: number;
  avg_response_time: number;
  avg_resolution_time: number;
}

// ============================================================================
// API CLIENT
// ============================================================================

const BASE_PATH = '/v1/helpdesk';

export const helpdeskApi = {
  // Dashboard
  getDashboard: () =>
    api.get<HelpdeskDashboard>(`${BASE_PATH}/dashboard`),

  getStats: (params?: { date_from?: string; date_to?: string }) =>
    api.get<TicketStats>(`${BASE_PATH}/stats${qs(params || {})}`),

  // Categories
  listCategories: (params?: { active_only?: boolean; public_only?: boolean; parent_id?: number }) =>
    api.get<Category[]>(`${BASE_PATH}/categories${qs(params || {})}`),

  getCategory: (id: number) =>
    api.get<Category>(`${BASE_PATH}/categories/${id}`),

  createCategory: (data: CategoryCreate) =>
    api.post<Category>(`${BASE_PATH}/categories`, data),

  updateCategory: (id: number, data: CategoryUpdate) =>
    api.patch<Category>(`${BASE_PATH}/categories/${id}`, data),

  deleteCategory: (id: number) =>
    api.delete(`${BASE_PATH}/categories/${id}`),

  // Tickets
  listTickets: (params?: {
    page?: number;
    page_size?: number;
    status?: TicketStatus;
    priority?: TicketPriority;
    category_id?: number;
    assigned_agent_id?: number;
    search?: string;
  }) =>
    api.get<TicketListResponse>(`${BASE_PATH}/tickets${qs(params || {})}`),

  getTicket: (id: number) =>
    api.get<Ticket>(`${BASE_PATH}/tickets/${id}`),

  getTicketByNumber: (ticketNumber: string) =>
    api.get<Ticket>(`${BASE_PATH}/tickets/number/${ticketNumber}`),

  createTicket: (data: TicketCreate) =>
    api.post<Ticket>(`${BASE_PATH}/tickets`, data),

  updateTicket: (id: number, data: TicketUpdate) =>
    api.patch<Ticket>(`${BASE_PATH}/tickets/${id}`, data),

  changeTicketStatus: (id: number, status: TicketStatus) =>
    api.post<Ticket>(`${BASE_PATH}/tickets/${id}/status`, { status }),

  assignTicket: (id: number, data: TicketAssign) =>
    api.post<Ticket>(`${BASE_PATH}/tickets/${id}/assign`, data),

  escalateTicket: (id: number, reason?: string) =>
    api.post<Ticket>(`${BASE_PATH}/tickets/${id}/escalate`, { reason }),

  mergeTickets: (targetId: number, sourceIds: number[]) =>
    api.post<Ticket>(`${BASE_PATH}/tickets/${targetId}/merge`, { source_ids: sourceIds }),

  // Replies
  listReplies: (ticketId: number) =>
    api.get<Reply[]>(`${BASE_PATH}/tickets/${ticketId}/replies`),

  createReply: (data: ReplyCreate) =>
    api.post<Reply>(`${BASE_PATH}/replies`, data),

  // Agents
  listAgents: (params?: { status?: AgentStatus; team_id?: number }) =>
    api.get<Agent[]>(`${BASE_PATH}/agents${qs(params || {})}`),

  getAgent: (id: number) =>
    api.get<Agent>(`${BASE_PATH}/agents/${id}`),

  createAgent: (data: AgentCreate) =>
    api.post<Agent>(`${BASE_PATH}/agents`, data),

  updateAgent: (id: number, data: AgentUpdate) =>
    api.patch<Agent>(`${BASE_PATH}/agents/${id}`, data),

  updateAgentStatus: (id: number, status: AgentStatus) =>
    api.post<Agent>(`${BASE_PATH}/agents/${id}/status`, { status }),

  // Teams
  listTeams: () =>
    api.get<Team[]>(`${BASE_PATH}/teams`),

  getTeam: (id: number) =>
    api.get<Team>(`${BASE_PATH}/teams/${id}`),

  createTeam: (data: TeamCreate) =>
    api.post<Team>(`${BASE_PATH}/teams`, data),

  updateTeam: (id: number, data: TeamUpdate) =>
    api.patch<Team>(`${BASE_PATH}/teams/${id}`, data),

  deleteTeam: (id: number) =>
    api.delete(`${BASE_PATH}/teams/${id}`),

  // SLA
  listSLAs: () =>
    api.get<SLA[]>(`${BASE_PATH}/sla`),

  getSLA: (id: number) =>
    api.get<SLA>(`${BASE_PATH}/sla/${id}`),

  createSLA: (data: SLACreate) =>
    api.post<SLA>(`${BASE_PATH}/sla`, data),

  updateSLA: (id: number, data: SLAUpdate) =>
    api.patch<SLA>(`${BASE_PATH}/sla/${id}`, data),

  deleteSLA: (id: number) =>
    api.delete(`${BASE_PATH}/sla/${id}`),

  // Knowledge Base
  listKBCategories: (params?: { public_only?: boolean }) =>
    api.get<KBCategory[]>(`${BASE_PATH}/kb/categories${qs(params || {})}`),

  createKBCategory: (data: KBCategoryCreate) =>
    api.post<KBCategory>(`${BASE_PATH}/kb/categories`, data),

  listKBArticles: (params?: { category_id?: number; status?: string; search?: string }) =>
    api.get<KBArticle[]>(`${BASE_PATH}/kb/articles${qs(params || {})}`),

  getKBArticle: (id: number) =>
    api.get<KBArticle>(`${BASE_PATH}/kb/articles/${id}`),

  getKBArticleBySlug: (slug: string) =>
    api.get<KBArticle>(`${BASE_PATH}/kb/articles/slug/${slug}`),

  createKBArticle: (data: KBArticleCreate) =>
    api.post<KBArticle>(`${BASE_PATH}/kb/articles`, data),

  updateKBArticle: (id: number, data: KBArticleUpdate) =>
    api.patch<KBArticle>(`${BASE_PATH}/kb/articles/${id}`, data),

  publishKBArticle: (id: number) =>
    api.post<KBArticle>(`${BASE_PATH}/kb/articles/${id}/publish`),

  recordArticleHelpful: (id: number, helpful: boolean) =>
    api.post(`${BASE_PATH}/kb/articles/${id}/helpful`, { helpful }),

  // Canned Responses
  listCannedResponses: (params?: { category?: string }) =>
    api.get<CannedResponse[]>(`${BASE_PATH}/canned-responses${qs(params || {})}`),

  createCannedResponse: (data: CannedResponseCreate) =>
    api.post<CannedResponse>(`${BASE_PATH}/canned-responses`, data),

  updateCannedResponse: (id: number, data: Partial<CannedResponseCreate>) =>
    api.patch<CannedResponse>(`${BASE_PATH}/canned-responses/${id}`, data),

  deleteCannedResponse: (id: number) =>
    api.delete(`${BASE_PATH}/canned-responses/${id}`),

  // Automations
  listAutomations: () =>
    api.get<Automation[]>(`${BASE_PATH}/automations`),

  createAutomation: (data: AutomationCreate) =>
    api.post<Automation>(`${BASE_PATH}/automations`, data),

  updateAutomation: (id: number, data: Partial<AutomationCreate>) =>
    api.patch<Automation>(`${BASE_PATH}/automations/${id}`, data),

  deleteAutomation: (id: number) =>
    api.delete(`${BASE_PATH}/automations/${id}`),

  // Satisfaction
  submitSatisfaction: (data: SatisfactionCreate) =>
    api.post<SatisfactionSurvey>(`${BASE_PATH}/satisfaction`, data),
};

export default helpdeskApi;
