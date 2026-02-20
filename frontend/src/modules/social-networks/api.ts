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
  SolocalInput
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
  }
};

export default socialNetworksApi;
