/**
 * AZALSCORE Module - Helpdesk Types
 * Types et utilitaires pour le support client
 */

import { formatDuration } from '@/utils/formatters';

// ============================================================
// TYPES DE BASE
// ============================================================

export type TicketPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
export type TicketStatus = 'OPEN' | 'IN_PROGRESS' | 'WAITING' | 'RESOLVED' | 'CLOSED';
export type TicketSource = 'EMAIL' | 'PHONE' | 'WEB' | 'CHAT' | 'OTHER';

export interface TicketCategory {
  id: string;
  code: string;
  name: string;
  description?: string;
  sla_hours?: number;
  is_active: boolean;
}

export interface Ticket {
  id: string;
  number: string;
  subject: string;
  description: string;
  category_id?: string;
  category_name?: string;
  customer_id?: string;
  customer_name?: string;
  customer_email?: string;
  contact_id?: string;
  contact_name?: string;
  priority: TicketPriority;
  status: TicketStatus;
  assigned_to_id?: string;
  assigned_to_name?: string;
  source: TicketSource;
  sla_due_date?: string;
  first_response_at?: string;
  resolved_at?: string;
  closed_at?: string;
  satisfaction_rating?: number;
  satisfaction_comment?: string;
  tags?: string[];
  messages: TicketMessage[];
  attachments?: TicketAttachment[];
  history?: TicketHistoryEntry[];
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export interface TicketMessage {
  id: string;
  content: string;
  is_internal: boolean;
  author_id: string;
  author_name?: string;
  author_email?: string;
  attachments?: TicketAttachment[];
  created_at: string;
}

export interface TicketAttachment {
  id: string;
  ticket_id: string;
  message_id?: string;
  name: string;
  file_url?: string;
  file_size?: number;
  mime_type?: string;
  created_at: string;
}

export interface TicketHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

export interface KnowledgeArticle {
  id: string;
  title: string;
  content: string;
  summary?: string;
  category_id?: string;
  category_name?: string;
  tags: string[];
  views: number;
  helpful_count?: number;
  not_helpful_count?: number;
  is_published: boolean;
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export interface HelpdeskDashboard {
  open_tickets: number;
  in_progress_tickets: number;
  overdue_tickets: number;
  resolved_today: number;
  avg_response_time: number;
  avg_resolution_time: number;
  satisfaction_rate: number;
  tickets_by_priority: { priority: string; count: number }[];
  tickets_by_category: { category_name: string; count: number }[];
}

// ============================================================
// CONSTANTES & CONFIGURATIONS
// ============================================================

export const PRIORITY_CONFIG: Record<TicketPriority, { label: string; color: string; description: string }> = {
  LOW: { label: 'Basse', color: 'gray', description: 'Demande non urgente' },
  MEDIUM: { label: 'Moyenne', color: 'blue', description: 'Traitement normal' },
  HIGH: { label: 'Haute', color: 'orange', description: 'Traitement prioritaire' },
  URGENT: { label: 'Urgente', color: 'red', description: 'Traitement immediat requis' },
};

export const STATUS_CONFIG: Record<TicketStatus, { label: string; color: string; description: string }> = {
  OPEN: { label: 'Ouvert', color: 'blue', description: 'Ticket en attente de traitement' },
  IN_PROGRESS: { label: 'En cours', color: 'orange', description: 'Ticket en cours de traitement' },
  WAITING: { label: 'En attente', color: 'yellow', description: 'En attente de reponse client' },
  RESOLVED: { label: 'Resolu', color: 'green', description: 'Probleme resolu' },
  CLOSED: { label: 'Ferme', color: 'gray', description: 'Ticket cloture' },
};

export const SOURCE_CONFIG: Record<TicketSource, { label: string; icon: string }> = {
  EMAIL: { label: 'Email', icon: 'mail' },
  PHONE: { label: 'Telephone', icon: 'phone' },
  WEB: { label: 'Web', icon: 'globe' },
  CHAT: { label: 'Chat', icon: 'message-circle' },
  OTHER: { label: 'Autre', icon: 'more-horizontal' },
};

export const PRIORITIES = [
  { value: 'LOW', label: 'Basse', color: 'gray' },
  { value: 'MEDIUM', label: 'Moyenne', color: 'blue' },
  { value: 'HIGH', label: 'Haute', color: 'orange' },
  { value: 'URGENT', label: 'Urgente', color: 'red' },
];

export const STATUSES = [
  { value: 'OPEN', label: 'Ouvert', color: 'blue' },
  { value: 'IN_PROGRESS', label: 'En cours', color: 'orange' },
  { value: 'WAITING', label: 'En attente', color: 'yellow' },
  { value: 'RESOLVED', label: 'Resolu', color: 'green' },
  { value: 'CLOSED', label: 'Ferme', color: 'gray' },
];

export const SOURCES = [
  { value: 'EMAIL', label: 'Email' },
  { value: 'PHONE', label: 'Telephone' },
  { value: 'WEB', label: 'Web' },
  { value: 'CHAT', label: 'Chat' },
  { value: 'OTHER', label: 'Autre' },
];

// ============================================================
// FONCTIONS UTILITAIRES
// ============================================================

/**
 * Obtenir la configuration du statut
 */
export const getStatusConfig = (status: TicketStatus) => {
  return STATUS_CONFIG[status] || STATUS_CONFIG.OPEN;
};

/**
 * Obtenir la configuration de la priorite
 */
export const getPriorityConfig = (priority: TicketPriority) => {
  return PRIORITY_CONFIG[priority] || PRIORITY_CONFIG.MEDIUM;
};

/**
 * Obtenir la configuration de la source
 */
export const getSourceConfig = (source: TicketSource) => {
  return SOURCE_CONFIG[source] || SOURCE_CONFIG.OTHER;
};

/**
 * Verifier si le ticket est en retard (SLA depasse)
 */
export const isTicketOverdue = (ticket: Ticket): boolean => {
  if (!ticket.sla_due_date) return false;
  if (ticket.status === 'RESOLVED' || ticket.status === 'CLOSED') return false;
  return new Date(ticket.sla_due_date) < new Date();
};

/**
 * Verifier si le SLA est proche (moins de 2h)
 */
export const isSlaDueSoon = (ticket: Ticket): boolean => {
  if (!ticket.sla_due_date) return false;
  if (ticket.status === 'RESOLVED' || ticket.status === 'CLOSED') return false;
  const dueDate = new Date(ticket.sla_due_date);
  const now = new Date();
  const hoursUntilDue = (dueDate.getTime() - now.getTime()) / (1000 * 60 * 60);
  return hoursUntilDue > 0 && hoursUntilDue <= 2;
};

/**
 * Calculer le temps depuis la creation
 */
export const getTicketAge = (ticket: Ticket): string => {
  const created = new Date(ticket.created_at);
  const now = new Date();
  const hours = (now.getTime() - created.getTime()) / (1000 * 60 * 60);
  return formatDuration(hours);
};

/**
 * Calculer le temps de premiere reponse
 */
export const getFirstResponseTime = (ticket: Ticket): string | null => {
  if (!ticket.first_response_at) return null;
  const created = new Date(ticket.created_at);
  const response = new Date(ticket.first_response_at);
  const hours = (response.getTime() - created.getTime()) / (1000 * 60 * 60);
  return formatDuration(hours);
};

/**
 * Calculer le temps de resolution
 */
export const getResolutionTime = (ticket: Ticket): string | null => {
  if (!ticket.resolved_at) return null;
  const created = new Date(ticket.created_at);
  const resolved = new Date(ticket.resolved_at);
  const hours = (resolved.getTime() - created.getTime()) / (1000 * 60 * 60);
  return formatDuration(hours);
};

/**
 * Compter les messages publics
 */
export const getPublicMessageCount = (ticket: Ticket): number => {
  return (ticket.messages || []).filter(m => !m.is_internal).length;
};

/**
 * Compter les messages internes
 */
export const getInternalMessageCount = (ticket: Ticket): number => {
  return (ticket.messages || []).filter(m => m.is_internal).length;
};

/**
 * Obtenir le dernier message
 */
export const getLastMessage = (ticket: Ticket): TicketMessage | null => {
  if (!ticket.messages || ticket.messages.length === 0) return null;
  return ticket.messages[ticket.messages.length - 1];
};

/**
 * Verifier si le ticket attend une reponse client
 */
export const isWaitingForCustomer = (ticket: Ticket): boolean => {
  if (ticket.status !== 'WAITING') return false;
  const lastMsg = getLastMessage(ticket);
  return lastMsg ? !lastMsg.is_internal : false;
};

/**
 * Obtenir le temps restant avant SLA
 */
export const getTimeUntilSla = (ticket: Ticket): string | null => {
  if (!ticket.sla_due_date) return null;
  if (ticket.status === 'RESOLVED' || ticket.status === 'CLOSED') return null;

  const dueDate = new Date(ticket.sla_due_date);
  const now = new Date();
  const hours = (dueDate.getTime() - now.getTime()) / (1000 * 60 * 60);

  if (hours < 0) {
    return `Depasse de ${formatDuration(Math.abs(hours))}`;
  }
  return formatDuration(hours);
};
