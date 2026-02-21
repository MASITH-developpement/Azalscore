/**
 * AZALS MODULE - Réseaux Sociaux - API Client
 * ==========================================
 * Client API pour les métriques marketing
 */

import { api } from '@core/api-client';
import type {
  SocialMetrics,
  MarketingSummary,
  MarketingPlatform,
  GoogleAnalyticsInput,
  GoogleAdsInput,
  GoogleSearchConsoleInput,
  GoogleMyBusinessInput,
  MetaBusinessInput,
  LinkedInInput,
  SolocalInput,
  PlatformStatus,
  AllPlatformsStatus,
  PlatformConfigInput,
  OAuthInitResponse,
  OAuthCallbackRequest,
  OAuthCallbackResponse,
  SyncRequest,
  SyncResponse
} from './types';

const BASE_URL = '/admin/social-networks';

export interface MetricsFilters {
  platform?: MarketingPlatform;
  start_date?: string;
  end_date?: string;
  limit?: number;
}

export interface PlatformInfo {
  id: string;
  name: string;
}

export const socialNetworksApi = {
  // === Consultation ===

  /**
   * Liste des plateformes supportées
   */
  getPlatforms: () =>
    api.get<{ platforms: PlatformInfo[] }>(`${BASE_URL}/platforms`),

  /**
   * Liste des métriques avec filtres optionnels
   */
  getMetrics: (filters?: MetricsFilters) => {
    const params = new URLSearchParams();
    if (filters?.platform) params.append('platform', filters.platform);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const queryString = params.toString();
    return api.get<SocialMetrics[]>(`${BASE_URL}/metrics${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Récupère une entrée de métriques par ID
   */
  getMetricsById: (id: string) =>
    api.get<SocialMetrics>(`${BASE_URL}/metrics/${id}`),

  /**
   * Récapitulatif marketing pour une date
   */
  getSummary: (date?: string) => {
    const params = date ? `?metrics_date=${date}` : '';
    return api.get<MarketingSummary>(`${BASE_URL}/summary${params}`);
  },

  // === Saisie par plateforme ===

  /**
   * Enregistre les métriques Google Analytics
   */
  saveGoogleAnalytics: (data: GoogleAnalyticsInput) =>
    api.post<SocialMetrics>(`${BASE_URL}/google-analytics`, data),

  /**
   * Enregistre les métriques Google Ads
   */
  saveGoogleAds: (data: GoogleAdsInput) =>
    api.post<SocialMetrics>(`${BASE_URL}/google-ads`, data),

  /**
   * Enregistre les métriques Google Search Console
   */
  saveGoogleSearchConsole: (data: GoogleSearchConsoleInput) =>
    api.post<SocialMetrics>(`${BASE_URL}/google-search-console`, data),

  /**
   * Enregistre les métriques Google My Business
   */
  saveGoogleMyBusiness: (data: GoogleMyBusinessInput) =>
    api.post<SocialMetrics>(`${BASE_URL}/google-my-business`, data),

  /**
   * Enregistre les métriques Meta (Facebook ou Instagram)
   */
  saveMetaBusiness: (data: MetaBusinessInput) =>
    api.post<SocialMetrics>(`${BASE_URL}/meta`, data),

  /**
   * Enregistre les métriques LinkedIn
   */
  saveLinkedIn: (data: LinkedInInput) =>
    api.post<SocialMetrics>(`${BASE_URL}/linkedin`, data),

  /**
   * Enregistre les métriques Solocal
   */
  saveSolocal: (data: SolocalInput) =>
    api.post<SocialMetrics>(`${BASE_URL}/solocal`, data),

  // === Modification / Suppression ===

  /**
   * Met à jour des métriques existantes
   */
  updateMetrics: (id: string, data: Partial<SocialMetrics>) =>
    api.put<SocialMetrics>(`${BASE_URL}/metrics/${id}`, data),

  /**
   * Supprime une entrée de métriques
   */
  deleteMetrics: (id: string) =>
    api.delete<{ status: string; id: string }>(`${BASE_URL}/metrics/${id}`),

  // === Synchronisation ===

  /**
   * Synchronise les métriques vers Prometheus/Grafana
   */
  syncToPrometheus: (date?: string) => {
    const params = date ? `?metrics_date=${date}` : '';
    return api.post<{ status: string; message: string }>(`${BASE_URL}/sync-prometheus${params}`, {});
  },

  // === Configuration des plateformes ===

  /**
   * Récupère le statut de toutes les plateformes
   */
  getAllPlatformsStatus: () =>
    api.get<AllPlatformsStatus>(`${BASE_URL}/config/status`),

  /**
   * Récupère le statut d'une plateforme
   */
  getPlatformStatus: (platform: MarketingPlatform) =>
    api.get<PlatformStatus>(`${BASE_URL}/config/${platform}`),

  /**
   * Crée ou met à jour la configuration d'une plateforme
   */
  savePlatformConfig: (platform: MarketingPlatform, data: PlatformConfigInput) =>
    api.post<PlatformStatus>(`${BASE_URL}/config/${platform}`, data),

  /**
   * Met à jour la configuration d'une plateforme
   */
  updatePlatformConfig: (platform: MarketingPlatform, data: Partial<PlatformConfigInput>) =>
    api.put<PlatformStatus>(`${BASE_URL}/config/${platform}`, data),

  /**
   * Supprime la configuration d'une plateforme
   */
  deletePlatformConfig: (platform: MarketingPlatform) =>
    api.delete<{ status: string; platform: string }>(`${BASE_URL}/config/${platform}`),

  // === OAuth ===

  /**
   * Initialise le flux OAuth pour une plateforme
   */
  initOAuth: (platform: MarketingPlatform, redirectUri?: string) =>
    api.post<OAuthInitResponse>(`${BASE_URL}/config/oauth/init`, {
      platform,
      redirect_uri: redirectUri
    }),

  /**
   * Traite le callback OAuth
   */
  handleOAuthCallback: (data: OAuthCallbackRequest) =>
    api.post<OAuthCallbackResponse>(`${BASE_URL}/config/oauth/callback`, data),

  // === Synchronisation automatique ===

  /**
   * Synchronise les métriques depuis les APIs
   */
  syncPlatforms: (data: SyncRequest) =>
    api.post<SyncResponse>(`${BASE_URL}/sync`, data),

  /**
   * Synchronise une plateforme spécifique
   */
  syncPlatform: (platform: MarketingPlatform, dateFrom?: string, dateTo?: string) => {
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    const queryString = params.toString();
    return api.post<SyncResponse>(`${BASE_URL}/sync/${platform}${queryString ? `?${queryString}` : ''}`, {});
  },

  /**
   * Teste la connexion à une plateforme
   */
  testConnection: (platform: MarketingPlatform) =>
    api.post<{ status: string; platform: string; account_info?: Record<string, unknown> }>(
      `${BASE_URL}/test-connection/${platform}`,
      {}
    )
};

export default socialNetworksApi;
