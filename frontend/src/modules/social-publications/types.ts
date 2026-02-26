/**
 * AZALSCORE - Module Publications Réseaux Sociaux - Types
 * =======================================================
 * Types TypeScript pour la gestion des publications et leads
 */

// ============================================================
// ENUMS
// ============================================================

export type PostStatus = 'draft' | 'scheduled' | 'publishing' | 'published' | 'failed' | 'archived';
export type PostType = 'text' | 'image' | 'video' | 'carousel' | 'link' | 'story' | 'reel';
export type CampaignStatus = 'draft' | 'active' | 'paused' | 'completed' | 'archived';
export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'proposal' | 'negotiation' | 'won' | 'lost' | 'nurturing';
export type LeadSource = 'facebook' | 'instagram' | 'linkedin' | 'twitter' | 'google_ads' | 'website' | 'referral' | 'organic' | 'other';

export type MarketingPlatform =
  | 'google_analytics'
  | 'google_ads'
  | 'google_search_console'
  | 'google_my_business'
  | 'meta_facebook'
  | 'meta_instagram'
  | 'linkedin'
  | 'solocal'
  | 'twitter'
  | 'tiktok'
  | 'youtube';

// ============================================================
// CAMPAGNES
// ============================================================

export interface Campaign {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  status: CampaignStatus;
  start_date?: string;
  end_date?: string;
  objective?: string;
  target_audience?: string;
  target_leads: number;
  target_impressions: number;
  budget: number;
  platforms: MarketingPlatform[];
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  total_posts: number;
  total_impressions: number;
  total_clicks: number;
  total_leads: number;
  total_conversions: number;
  actual_spend: number;
  created_at: string;
  updated_at?: string;
  created_by?: string;
}

export interface CampaignCreate {
  name: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  objective?: string;
  target_audience?: string;
  target_leads?: number;
  target_impressions?: number;
  budget?: number;
  platforms?: MarketingPlatform[];
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
}

export interface CampaignUpdate extends Partial<CampaignCreate> {
  status?: CampaignStatus;
}

export interface CampaignStats {
  campaign_id: string;
  period_start: string;
  period_end: string;
  posts_published: number;
  impressions: number;
  reach: number;
  clicks: number;
  engagement: number;
  leads_generated: number;
  leads_converted: number;
  cost_per_lead: number;
  conversion_rate: number;
  roi: number;
}

// ============================================================
// PUBLICATIONS
// ============================================================

export interface SocialPost {
  id: string;
  tenant_id: string;
  campaign_id?: string;
  title?: string;
  content: string;
  post_type: PostType;
  media_urls: string[];
  thumbnail_url?: string;
  link_url?: string;
  link_title?: string;
  link_description?: string;
  status: PostStatus;
  platforms: MarketingPlatform[];
  scheduled_at?: string;
  published_at?: string;
  external_ids: Record<string, string>;
  hashtags: string[];
  mentions: string[];
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  impressions: number;
  reach: number;
  clicks: number;
  likes: number;
  comments: number;
  shares: number;
  saves: number;
  last_error?: string;
  created_at: string;
  updated_at?: string;
  created_by?: string;
}

export interface PostCreate {
  title?: string;
  content: string;
  post_type?: PostType;
  media_urls?: string[];
  thumbnail_url?: string;
  link_url?: string;
  link_title?: string;
  link_description?: string;
  platforms: MarketingPlatform[];
  scheduled_at?: string;
  campaign_id?: string;
  hashtags?: string[];
  mentions?: string[];
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
}

export interface PostUpdate extends Partial<Omit<PostCreate, 'campaign_id'>> {}

// ============================================================
// LEADS
// ============================================================

export interface SocialLead {
  id: string;
  tenant_id: string;
  source: LeadSource;
  source_platform?: MarketingPlatform;
  campaign_id?: string;
  post_id?: string;
  email?: string;
  phone?: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  job_title?: string;
  social_profile_url?: string;
  social_username?: string;
  status: LeadStatus;
  score: number;
  interest?: string;
  budget_range?: string;
  timeline?: string;
  notes?: string;
  tags: string[];
  assigned_to?: string;
  created_at: string;
  updated_at?: string;
  converted_at?: string;
  contact_id?: string;
  opportunity_id?: string;
  last_interaction_at?: string;
  emails_sent: number;
  emails_opened: number;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
}

export interface LeadCreate {
  source: LeadSource;
  source_platform?: MarketingPlatform;
  campaign_id?: string;
  post_id?: string;
  email?: string;
  phone?: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  job_title?: string;
  interest?: string;
  budget_range?: string;
  timeline?: string;
  notes?: string;
  tags?: string[];
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
}

export interface LeadUpdate {
  status?: LeadStatus;
  score?: number;
  email?: string;
  phone?: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  job_title?: string;
  interest?: string;
  budget_range?: string;
  timeline?: string;
  notes?: string;
  tags?: string[];
  assigned_to?: string;
}

export interface LeadInteraction {
  type: 'email' | 'call' | 'meeting' | 'note';
  subject?: string;
  content?: string;
  outcome?: string;
  next_action?: string;
  next_action_date?: string;
}

export interface LeadFunnel {
  total_leads: number;
  new: number;
  contacted: number;
  qualified: number;
  proposal: number;
  negotiation: number;
  won: number;
  lost: number;
  conversion_rate: number;
  avg_time_to_convert?: number;
}

// ============================================================
// TEMPLATES
// ============================================================

export interface PostTemplate {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  category?: string;
  content_template: string;
  post_type: PostType;
  suggested_hashtags: string[];
  suggested_media: string[];
  recommended_platforms: MarketingPlatform[];
  variables: TemplateVariable[];
  is_active: boolean;
  usage_count: number;
  avg_engagement_rate: number;
  created_at: string;
  updated_at?: string;
  created_by?: string;
}

export interface TemplateVariable {
  name: string;
  description?: string;
  default_value?: string;
  required: boolean;
}

export interface TemplateCreate {
  name: string;
  description?: string;
  category?: string;
  content_template: string;
  post_type?: PostType;
  suggested_hashtags?: string[];
  suggested_media?: string[];
  recommended_platforms?: MarketingPlatform[];
  variables?: TemplateVariable[];
}

export interface TemplateRenderResponse {
  content: string;
  hashtags: string[];
  platforms: MarketingPlatform[];
  warnings: string[];
}

// ============================================================
// CALENDRIER & ANALYTICS
// ============================================================

export interface PublishingSlot {
  id: string;
  tenant_id: string;
  platform: MarketingPlatform;
  day_of_week: number;
  hour: number;
  minute: number;
  is_optimal: boolean;
  avg_engagement: number;
  posts_count: number;
  created_at: string;
}

export interface CalendarDay {
  date: string;
  posts: SocialPost[];
  optimal_slots: PublishingSlot[];
}

export interface PlatformPerformance {
  platform: MarketingPlatform;
  posts_count: number;
  total_impressions: number;
  total_reach: number;
  total_clicks: number;
  total_engagement: number;
  avg_engagement_rate: number;
  leads_generated: number;
  best_post_id?: string;
}

export interface ContentSuggestion {
  title: string;
  content: string;
  hashtags: string[];
  best_platforms: MarketingPlatform[];
  best_time?: string;
  estimated_reach?: number;
  relevance_score: number;
}

// ============================================================
// CONSTANTES
// ============================================================

export const POST_STATUS_OPTIONS = [
  { value: 'draft', label: 'Brouillon', color: 'gray' },
  { value: 'scheduled', label: 'Programmé', color: 'blue' },
  { value: 'publishing', label: 'Publication...', color: 'yellow' },
  { value: 'published', label: 'Publié', color: 'green' },
  { value: 'failed', label: 'Échec', color: 'red' },
  { value: 'archived', label: 'Archivé', color: 'gray' },
] as const;

export const LEAD_STATUS_OPTIONS = [
  { value: 'new', label: 'Nouveau', color: 'blue' },
  { value: 'contacted', label: 'Contacté', color: 'cyan' },
  { value: 'qualified', label: 'Qualifié', color: 'purple' },
  { value: 'proposal', label: 'Proposition', color: 'orange' },
  { value: 'negotiation', label: 'Négociation', color: 'yellow' },
  { value: 'won', label: 'Gagné', color: 'green' },
  { value: 'lost', label: 'Perdu', color: 'red' },
  { value: 'nurturing', label: 'Nurturing', color: 'gray' },
] as const;

export const PLATFORM_OPTIONS = [
  { value: 'meta_facebook', label: 'Facebook', icon: 'facebook' },
  { value: 'meta_instagram', label: 'Instagram', icon: 'instagram' },
  { value: 'linkedin', label: 'LinkedIn', icon: 'linkedin' },
  { value: 'twitter', label: 'Twitter/X', icon: 'twitter' },
  { value: 'tiktok', label: 'TikTok', icon: 'video' },
  { value: 'youtube', label: 'YouTube', icon: 'youtube' },
] as const;

export const POST_TYPE_OPTIONS = [
  { value: 'text', label: 'Texte', icon: 'type' },
  { value: 'image', label: 'Image', icon: 'image' },
  { value: 'video', label: 'Vidéo', icon: 'video' },
  { value: 'carousel', label: 'Carrousel', icon: 'layers' },
  { value: 'link', label: 'Lien', icon: 'link' },
  { value: 'story', label: 'Story', icon: 'clock' },
  { value: 'reel', label: 'Reel', icon: 'film' },
] as const;

export const TEMPLATE_CATEGORIES = [
  { value: 'promo', label: 'Promotion' },
  { value: 'event', label: 'Événement' },
  { value: 'tips', label: 'Conseils' },
  { value: 'testimonial', label: 'Témoignage' },
  { value: 'announcement', label: 'Annonce' },
  { value: 'engagement', label: 'Engagement' },
] as const;
