/**
 * AZALSCORE - Module Publications Réseaux Sociaux - API
 * =====================================================
 * React Query hooks pour l'API publications et leads
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import type {
  Campaign,
  CampaignCreate,
  CampaignUpdate,
  CampaignStats,
  SocialPost,
  PostCreate,
  PostUpdate,
  SocialLead,
  LeadCreate,
  LeadUpdate,
  LeadInteraction,
  LeadFunnel,
  PostTemplate,
  TemplateCreate,
  TemplateRenderResponse,
  PublishingSlot,
  CalendarDay,
  PlatformPerformance,
  ContentSuggestion,
  PostStatus,
  CampaignStatus,
  LeadStatus,
  LeadSource,
  MarketingPlatform,
} from './types';

const BASE_URL = '/api/v1/social/publications';

// ============================================================
// CAMPAGNES
// ============================================================

export function useCampaigns(params?: {
  status?: CampaignStatus;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['social-campaigns', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.append('status', params.status);
      if (params?.limit) searchParams.append('limit', String(params.limit));
      if (params?.offset) searchParams.append('offset', String(params.offset));

      const response = await api.get<Campaign[]>(
        `${BASE_URL}/campaigns?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

export function useCampaign(campaignId: string) {
  return useQuery({
    queryKey: ['social-campaign', campaignId],
    queryFn: async () => {
      const response = await api.get<Campaign>(
        `${BASE_URL}/campaigns/${campaignId}`
      );
      return response.data;
    },
    enabled: !!campaignId,
  });
}

export function useCampaignStats(
  campaignId: string,
  params?: { start_date?: string; end_date?: string }
) {
  return useQuery({
    queryKey: ['social-campaign-stats', campaignId, params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.start_date) searchParams.append('start_date', params.start_date);
      if (params?.end_date) searchParams.append('end_date', params.end_date);

      const response = await api.get<CampaignStats>(
        `${BASE_URL}/campaigns/${campaignId}/stats?${searchParams.toString()}`
      );
      return response.data;
    },
    enabled: !!campaignId,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CampaignCreate) => {
      const response = await api.post<Campaign>(`${BASE_URL}/campaigns`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-campaigns'] });
    },
  });
}

export function useUpdateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: CampaignUpdate;
    }) => {
      const response = await api.put<Campaign>(
        `${BASE_URL}/campaigns/${id}`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['social-campaigns'] });
      queryClient.invalidateQueries({
        queryKey: ['social-campaign', variables.id],
      });
    },
  });
}

export function useDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${BASE_URL}/campaigns/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-campaigns'] });
    },
  });
}

// ============================================================
// PUBLICATIONS
// ============================================================

export function usePosts(params?: {
  status?: PostStatus;
  campaign_id?: string;
  platform?: MarketingPlatform;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['social-posts', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.append('status', params.status);
      if (params?.campaign_id) searchParams.append('campaign_id', params.campaign_id);
      if (params?.platform) searchParams.append('platform', params.platform);
      if (params?.start_date) searchParams.append('start_date', params.start_date);
      if (params?.end_date) searchParams.append('end_date', params.end_date);
      if (params?.limit) searchParams.append('limit', String(params.limit));
      if (params?.offset) searchParams.append('offset', String(params.offset));

      const response = await api.get<SocialPost[]>(
        `${BASE_URL}/posts?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

export function usePost(postId: string) {
  return useQuery({
    queryKey: ['social-post', postId],
    queryFn: async () => {
      const response = await api.get<SocialPost>(`${BASE_URL}/posts/${postId}`);
      return response.data;
    },
    enabled: !!postId,
  });
}

export function useCreatePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: PostCreate) => {
      const response = await api.post<SocialPost>(`${BASE_URL}/posts`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-posts'] });
      queryClient.invalidateQueries({ queryKey: ['social-campaigns'] });
    },
  });
}

export function useUpdatePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PostUpdate }) => {
      const response = await api.put<SocialPost>(
        `${BASE_URL}/posts/${id}`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['social-posts'] });
      queryClient.invalidateQueries({ queryKey: ['social-post', variables.id] });
    },
  });
}

export function useDeletePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${BASE_URL}/posts/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-posts'] });
      queryClient.invalidateQueries({ queryKey: ['social-campaigns'] });
    },
  });
}

export function useSchedulePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      scheduled_at,
      platforms,
    }: {
      id: string;
      scheduled_at: string;
      platforms?: MarketingPlatform[];
    }) => {
      const searchParams = new URLSearchParams();
      searchParams.append('scheduled_at', scheduled_at);
      if (platforms) {
        platforms.forEach((p) => searchParams.append('platforms', p));
      }

      const response = await api.post<SocialPost>(
        `${BASE_URL}/posts/${id}/schedule?${searchParams.toString()}`
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['social-posts'] });
      queryClient.invalidateQueries({ queryKey: ['social-post', variables.id] });
    },
  });
}

export function usePublishPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      platforms,
    }: {
      id: string;
      platforms?: MarketingPlatform[];
    }) => {
      const searchParams = new URLSearchParams();
      if (platforms) {
        platforms.forEach((p) => searchParams.append('platforms', p));
      }

      const response = await api.post<SocialPost>(
        `${BASE_URL}/posts/${id}/publish?${searchParams.toString()}`
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['social-posts'] });
      queryClient.invalidateQueries({ queryKey: ['social-post', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['social-campaigns'] });
    },
  });
}

export function useDuplicatePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<SocialPost>(
        `${BASE_URL}/posts/${id}/duplicate`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-posts'] });
    },
  });
}

// ============================================================
// LEADS
// ============================================================

export function useLeads(params?: {
  status?: LeadStatus;
  source?: LeadSource;
  campaign_id?: string;
  assigned_to?: string;
  search?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['social-leads', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.append('status', params.status);
      if (params?.source) searchParams.append('source', params.source);
      if (params?.campaign_id) searchParams.append('campaign_id', params.campaign_id);
      if (params?.assigned_to) searchParams.append('assigned_to', params.assigned_to);
      if (params?.search) searchParams.append('search', params.search);
      if (params?.limit) searchParams.append('limit', String(params.limit));
      if (params?.offset) searchParams.append('offset', String(params.offset));

      const response = await api.get<SocialLead[]>(
        `${BASE_URL}/leads?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

export function useLead(leadId: string) {
  return useQuery({
    queryKey: ['social-lead', leadId],
    queryFn: async () => {
      const response = await api.get<SocialLead>(`${BASE_URL}/leads/${leadId}`);
      return response.data;
    },
    enabled: !!leadId,
  });
}

export function useLeadFunnel(campaignId?: string) {
  return useQuery({
    queryKey: ['social-lead-funnel', campaignId],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (campaignId) searchParams.append('campaign_id', campaignId);

      const response = await api.get<LeadFunnel>(
        `${BASE_URL}/leads/funnel?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

export function useCreateLead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: LeadCreate) => {
      const response = await api.post<SocialLead>(`${BASE_URL}/leads`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-leads'] });
      queryClient.invalidateQueries({ queryKey: ['social-lead-funnel'] });
      queryClient.invalidateQueries({ queryKey: ['social-campaigns'] });
    },
  });
}

export function useUpdateLead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: LeadUpdate }) => {
      const response = await api.put<SocialLead>(
        `${BASE_URL}/leads/${id}`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['social-leads'] });
      queryClient.invalidateQueries({ queryKey: ['social-lead', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['social-lead-funnel'] });
    },
  });
}

export function useDeleteLead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${BASE_URL}/leads/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-leads'] });
      queryClient.invalidateQueries({ queryKey: ['social-lead-funnel'] });
      queryClient.invalidateQueries({ queryKey: ['social-campaigns'] });
    },
  });
}

export function useAddLeadInteraction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      interaction,
    }: {
      id: string;
      interaction: LeadInteraction;
    }) => {
      const response = await api.post<SocialLead>(
        `${BASE_URL}/leads/${id}/interactions`,
        interaction
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['social-leads'] });
      queryClient.invalidateQueries({ queryKey: ['social-lead', variables.id] });
    },
  });
}

export function useConvertLead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      create_contact,
      create_opportunity,
      opportunity_value,
    }: {
      id: string;
      create_contact?: boolean;
      create_opportunity?: boolean;
      opportunity_value?: number;
    }) => {
      const searchParams = new URLSearchParams();
      if (create_contact !== undefined)
        searchParams.append('create_contact', String(create_contact));
      if (create_opportunity !== undefined)
        searchParams.append('create_opportunity', String(create_opportunity));
      if (opportunity_value !== undefined)
        searchParams.append('opportunity_value', String(opportunity_value));

      const response = await api.post(
        `${BASE_URL}/leads/${id}/convert?${searchParams.toString()}`
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['social-leads'] });
      queryClient.invalidateQueries({ queryKey: ['social-lead', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['social-lead-funnel'] });
      queryClient.invalidateQueries({ queryKey: ['social-campaigns'] });
    },
  });
}

// ============================================================
// TEMPLATES
// ============================================================

export function useTemplates(params?: {
  category?: string;
  active_only?: boolean;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['social-templates', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.category) searchParams.append('category', params.category);
      if (params?.active_only !== undefined)
        searchParams.append('active_only', String(params.active_only));
      if (params?.limit) searchParams.append('limit', String(params.limit));

      const response = await api.get<PostTemplate[]>(
        `${BASE_URL}/templates?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

export function useTemplate(templateId: string) {
  return useQuery({
    queryKey: ['social-template', templateId],
    queryFn: async () => {
      const response = await api.get<PostTemplate>(
        `${BASE_URL}/templates/${templateId}`
      );
      return response.data;
    },
    enabled: !!templateId,
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: TemplateCreate) => {
      const response = await api.post<PostTemplate>(
        `${BASE_URL}/templates`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-templates'] });
    },
  });
}

export function useRenderTemplate() {
  return useMutation({
    mutationFn: async ({
      id,
      variables,
      platforms,
    }: {
      id: string;
      variables?: Record<string, string>;
      platforms?: MarketingPlatform[];
    }) => {
      const searchParams = new URLSearchParams();
      if (platforms) {
        platforms.forEach((p) => searchParams.append('platforms', p));
      }

      const response = await api.post<TemplateRenderResponse>(
        `${BASE_URL}/templates/${id}/render?${searchParams.toString()}`,
        variables || {}
      );
      return response.data;
    },
  });
}

// ============================================================
// CALENDRIER & ANALYTICS
// ============================================================

export function useCalendar(params: { start_date: string; end_date: string }) {
  return useQuery({
    queryKey: ['social-calendar', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      searchParams.append('start_date', params.start_date);
      searchParams.append('end_date', params.end_date);

      const response = await api.get<CalendarDay[]>(
        `${BASE_URL}/calendar?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

export function usePublishingSlots(platform?: MarketingPlatform) {
  return useQuery({
    queryKey: ['social-slots', platform],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (platform) searchParams.append('platform', platform);

      const response = await api.get<PublishingSlot[]>(
        `${BASE_URL}/slots?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

export function useOptimalTime(platform: MarketingPlatform, preferredDate?: string) {
  return useQuery({
    queryKey: ['social-optimal-time', platform, preferredDate],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      searchParams.append('platform', platform);
      if (preferredDate) searchParams.append('preferred_date', preferredDate);

      const response = await api.get<{
        platform: string;
        suggested_datetime: string;
        day: string;
        time: string;
      }>(`${BASE_URL}/optimal-time?${searchParams.toString()}`);
      return response.data;
    },
    enabled: !!platform,
  });
}

export function usePlatformAnalytics(params?: {
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ['social-platform-analytics', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.start_date) searchParams.append('start_date', params.start_date);
      if (params?.end_date) searchParams.append('end_date', params.end_date);

      const response = await api.get<PlatformPerformance[]>(
        `${BASE_URL}/analytics/platforms?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

export function useContentSuggestions() {
  return useMutation({
    mutationFn: async ({
      topic,
      platforms,
      count,
    }: {
      topic: string;
      platforms: MarketingPlatform[];
      count?: number;
    }) => {
      const searchParams = new URLSearchParams();
      searchParams.append('topic', topic);
      platforms.forEach((p) => searchParams.append('platforms', p));
      if (count) searchParams.append('count', String(count));

      const response = await api.post<ContentSuggestion[]>(
        `${BASE_URL}/analytics/suggestions?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

// ============================================================
// ENUMS (pour les formulaires)
// ============================================================

export function useEnums() {
  return useQuery({
    queryKey: ['social-enums'],
    queryFn: async () => {
      const response = await api.get<{
        post_status: string[];
        post_type: string[];
        campaign_status: string[];
        lead_status: string[];
        lead_source: string[];
        platforms: Array<{ id: string; name: string }>;
      }>(`${BASE_URL}/enums`);
      return response.data;
    },
    staleTime: Infinity, // Les enums ne changent pas
  });
}
