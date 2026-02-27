/**
 * AZALSCORE - Helpdesk React Query Hooks
 * =======================================
 * Hooks pour le module Support / Helpdesk
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { Ticket, TicketCategory, KnowledgeArticle, HelpdeskDashboard } from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const helpdeskKeys = {
  all: ['helpdesk'] as const,

  // Dashboard
  dashboard: () => [...helpdeskKeys.all, 'dashboard'] as const,

  // Categories
  categories: () => [...helpdeskKeys.all, 'categories'] as const,

  // Tickets
  tickets: () => [...helpdeskKeys.all, 'tickets'] as const,
  ticketsList: (filters?: { status?: string; priority?: string; category_id?: string }) =>
    [...helpdeskKeys.tickets(), serializeFilters(filters)] as const,
  ticketDetail: (id: string) => [...helpdeskKeys.tickets(), id] as const,

  // Articles
  articles: () => [...helpdeskKeys.all, 'articles'] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export const useHelpdeskDashboard = () => {
  return useQuery({
    queryKey: helpdeskKeys.dashboard(),
    queryFn: async () => {
      return api.get<HelpdeskDashboard>('/helpdesk/dashboard').then(r => r.data);
    },
  });
};

// ============================================================================
// CATEGORY HOOKS
// ============================================================================

export const useTicketCategories = () => {
  return useQuery({
    queryKey: helpdeskKeys.categories(),
    queryFn: async () => {
      return api.get<TicketCategory[]>('/helpdesk/categories').then(r => r.data);
    },
  });
};

// ============================================================================
// TICKET HOOKS
// ============================================================================

export const useTickets = (filters?: { status?: string; priority?: string; category_id?: string }) => {
  return useQuery({
    queryKey: helpdeskKeys.ticketsList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.priority) params.append('priority', filters.priority);
      if (filters?.category_id) params.append('category_id', filters.category_id);
      const queryString = params.toString();
      const url = queryString ? `/helpdesk/tickets?${queryString}` : '/helpdesk/tickets';
      return api.get<Ticket[]>(url).then(r => r.data);
    },
  });
};

export const useTicket = (id: string) => {
  return useQuery({
    queryKey: helpdeskKeys.ticketDetail(id),
    queryFn: async () => {
      return api.get<Ticket>(`/helpdesk/tickets/${id}`).then(r => r.data);
    },
    enabled: !!id,
  });
};

export const useCreateTicket = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Ticket>) => {
      return api.post('/helpdesk/tickets', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: helpdeskKeys.all }),
  });
};

export const useUpdateTicketStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/helpdesk/tickets/${id}`, { status }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: helpdeskKeys.all }),
  });
};

// ============================================================================
// KNOWLEDGE BASE HOOKS
// ============================================================================

export const useKnowledgeArticles = () => {
  return useQuery({
    queryKey: helpdeskKeys.articles(),
    queryFn: async () => {
      return api.get<KnowledgeArticle[]>('/helpdesk/articles').then(r => r.data);
    },
  });
};
