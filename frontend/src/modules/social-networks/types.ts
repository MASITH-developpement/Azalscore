/**
 * AZALS MODULE - Réseaux Sociaux - Types
 * ======================================
 * Types TypeScript pour le module d'administration des métriques marketing
 */

// Plateformes marketing supportées
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

// Configuration des plateformes
export interface PlatformConfig {
  id: MarketingPlatform;
  name: string;
  icon: string;
  color: string;
  description: string;
}

// Métriques sociales (réponse API)
export interface SocialMetrics {
  id: string;
  tenant_id: string;
  platform: MarketingPlatform;
  metrics_date: string;

  // Métriques communes
  impressions: number;
  clicks: number;
  reach: number;
  engagement: number;
  followers: number;

  // Taux
  ctr: number;
  engagement_rate: number;
  bounce_rate: number;
  conversion_rate: number;

  // Analytics
  sessions: number;
  users: number;
  pageviews: number;
  avg_session_duration: number;
  conversions: number;

  // Publicité
  cost: number;
  cpc: number;
  cpm: number;
  roas: number;

  // SEO
  avg_position: number;

  // Local
  calls: number;
  directions: number;
  reviews_count: number;
  rating: number;

  // Vidéo
  views: number;
  watch_time: number;
  likes: number;
  shares: number;
  comments: number;
  subscribers: number;

  notes: string | null;
  created_at: string;
  updated_at: string | null;
}

// Formulaires de saisie par plateforme
export interface GoogleAnalyticsInput {
  metrics_date: string;
  sessions: number;
  users: number;
  pageviews: number;
  bounce_rate: number;
  avg_session_duration: number;
  conversions: number;
  conversion_rate: number;
  notes?: string;
}

export interface GoogleAdsInput {
  metrics_date: string;
  impressions: number;
  clicks: number;
  cost: number;
  conversions: number;
  ctr: number;
  cpc: number;
  roas: number;
  notes?: string;
}

export interface GoogleSearchConsoleInput {
  metrics_date: string;
  impressions: number;
  clicks: number;
  ctr: number;
  avg_position: number;
  notes?: string;
}

export interface GoogleMyBusinessInput {
  metrics_date: string;
  views: number;
  clicks: number;
  calls: number;
  directions: number;
  reviews_count: number;
  rating: number;
  notes?: string;
}

export interface MetaBusinessInput {
  metrics_date: string;
  platform: 'meta_facebook' | 'meta_instagram';
  reach: number;
  impressions: number;
  engagement: number;
  clicks: number;
  followers: number;
  cost: number;
  ctr: number;
  cpm: number;
  notes?: string;
}

export interface LinkedInInput {
  metrics_date: string;
  followers: number;
  impressions: number;
  clicks: number;
  engagement: number;
  engagement_rate: number;
  reach: number;
  notes?: string;
}

export interface SolocalInput {
  metrics_date: string;
  impressions: number;
  clicks: number;
  calls: number;
  directions: number;
  reviews_count: number;
  rating: number;
  notes?: string;
}

// Récapitulatif marketing
export interface MarketingSummary {
  date: string;
  total_spend: number;
  total_conversions: number;
  total_impressions: number;
  total_clicks: number;
  overall_ctr: number;
  estimated_roi: number;

  google_analytics: Record<string, number> | null;
  google_ads: Record<string, number> | null;
  google_search_console: Record<string, number> | null;
  google_my_business: Record<string, number> | null;
  meta_facebook: Record<string, number> | null;
  meta_instagram: Record<string, number> | null;
  linkedin: Record<string, number> | null;
  solocal: Record<string, number> | null;
}

// Configuration des plateformes avec métadonnées
export const PLATFORMS: PlatformConfig[] = [
  {
    id: 'google_analytics',
    name: 'Google Analytics',
    icon: 'BarChart3',
    color: '#E37400',
    description: 'Sessions, utilisateurs, pages vues, taux de rebond'
  },
  {
    id: 'google_ads',
    name: 'Google Ads',
    icon: 'Target',
    color: '#4285F4',
    description: 'Impressions, clics, coût, conversions, ROAS'
  },
  {
    id: 'google_search_console',
    name: 'Search Console',
    icon: 'Search',
    color: '#34A853',
    description: 'Impressions, clics, CTR, position moyenne'
  },
  {
    id: 'google_my_business',
    name: 'Google My Business',
    icon: 'MapPin',
    color: '#EA4335',
    description: 'Vues, clics, appels, itinéraires, avis'
  },
  {
    id: 'meta_facebook',
    name: 'Facebook',
    icon: 'Facebook',
    color: '#1877F2',
    description: 'Portée, engagements, abonnés, budget pub'
  },
  {
    id: 'meta_instagram',
    name: 'Instagram',
    icon: 'Instagram',
    color: '#E4405F',
    description: 'Portée, engagements, abonnés, stories'
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    icon: 'Linkedin',
    color: '#0A66C2',
    description: 'Abonnés, impressions, engagements, visiteurs'
  },
  {
    id: 'solocal',
    name: 'Solocal (PagesJaunes)',
    icon: 'BookOpen',
    color: '#FFCC00',
    description: 'Vues fiche, clics, appels, itinéraires, avis'
  }
];

// Helper pour obtenir la config d'une plateforme
export function getPlatformConfig(platformId: MarketingPlatform): PlatformConfig | undefined {
  return PLATFORMS.find(p => p.id === platformId);
}

// Helper pour formater un nombre avec séparateur de milliers
export function formatNumber(value: number): string {
  return new Intl.NumberFormat('fr-FR').format(value);
}

// Helper pour formater un montant en euros
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);
}

// Helper pour formater un pourcentage
export function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

// Helper pour formater une date
export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

// === Types pour la configuration des plateformes ===

export type OAuthStatus = 'not_connected' | 'connected' | 'expired' | 'error';
export type SyncStatus = 'never' | 'success' | 'error' | 'in_progress';

export interface PlatformStatus {
  platform: MarketingPlatform;
  name: string;
  is_configured: boolean;
  is_connected: boolean;
  is_enabled: boolean;
  last_sync_at: string | null;
  sync_status: SyncStatus;
  error_message: string | null;
  account_id: string | null;
  account_name: string | null;
}

export interface AllPlatformsStatus {
  platforms: PlatformStatus[];
  total_configured: number;
  total_connected: number;
  last_global_sync: string | null;
}

export interface PlatformConfigInput {
  platform: MarketingPlatform;
  is_enabled?: boolean;
  account_id?: string;
  property_id?: string;
  api_key?: string;
  api_secret?: string;
}

export interface OAuthInitResponse {
  auth_url: string;
  state: string;
  platform: MarketingPlatform;
}

export interface OAuthCallbackRequest {
  platform: MarketingPlatform;
  code: string;
  state: string;
}

export interface OAuthCallbackResponse {
  success: boolean;
  platform: MarketingPlatform;
  message: string;
  account_id?: string;
  account_name?: string;
}

export interface SyncRequest {
  platform?: MarketingPlatform;
  date_from?: string;
  date_to?: string;
}

export interface SyncResponse {
  success: boolean;
  platform?: MarketingPlatform;
  message: string;
  records_synced: number;
  errors: string[];
}

// Plateformes supportant OAuth
export const OAUTH_PLATFORMS: MarketingPlatform[] = [
  'google_analytics',
  'google_ads',
  'google_search_console',
  'google_my_business',
  'meta_facebook',
  'meta_instagram',
  'linkedin'
];

// Plateformes avec clé API simple
export const API_KEY_PLATFORMS: MarketingPlatform[] = [
  'solocal'
];

// Helper pour savoir si une plateforme utilise OAuth
export function usesOAuth(platform: MarketingPlatform): boolean {
  return OAUTH_PLATFORMS.includes(platform);
}
