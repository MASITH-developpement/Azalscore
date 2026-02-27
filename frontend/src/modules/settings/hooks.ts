/**
 * AZALSCORE - Settings Hooks
 * ==========================
 * Hooks pour les paramètres utilisateur et les réexports des paramètres admin
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';

// Re-export all admin settings hooks from api.ts
export * from './api';

// ============================================================================
// USER PREFERENCES TYPES
// ============================================================================

export type AccentColor = 'orange' | 'blue' | 'violet' | 'emerald' | 'rose';
export type LogoIcon = 'text' | 'letter-a' | 'cube' | 'spark' | 'shield' | 'hexagon';

export interface UserPreferences {
  theme_mode: 'LIGHT' | 'DARK' | 'SYSTEM';
  ui_style: 'CLASSIC' | 'MODERN' | 'GLASS';
  accent_color: AccentColor;
  logo_icon: LogoIcon;
  custom_logo: string | null;
  language: string;
  toolbar_dense: boolean;
  desktop_notifications: boolean;
  sound_enabled: boolean;
}

export const DEFAULT_PREFERENCES: UserPreferences = {
  theme_mode: 'SYSTEM',
  ui_style: 'CLASSIC',
  accent_color: 'orange',
  logo_icon: 'text',
  custom_logo: null,
  language: 'fr',
  toolbar_dense: false,
  desktop_notifications: false,
  sound_enabled: true,
};

// ============================================================================
// USER PREFERENCES QUERY KEYS
// ============================================================================

export const userPreferencesKeys = {
  all: ['user-preferences'] as const,
  current: () => [...userPreferencesKeys.all, 'current'] as const,
};

// ============================================================================
// USER PREFERENCES HOOKS
// ============================================================================

/**
 * Charge les préférences utilisateur depuis localStorage (pour le rendu initial)
 */
export const loadLocalPreferences = (): UserPreferences => {
  try {
    const stored = localStorage.getItem('azals_preferences');
    if (stored) {
      return { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) };
    }
  } catch {
    // ignore
  }
  return DEFAULT_PREFERENCES;
};

/**
 * Récupère les préférences utilisateur depuis l'API
 */
export const useUserPreferences = () => {
  return useQuery({
    queryKey: userPreferencesKeys.current(),
    queryFn: async () => {
      const response = await api.get<UserPreferences>('/web/preferences');
      if (response.data) {
        return {
          theme_mode: response.data.theme_mode || 'SYSTEM',
          ui_style: response.data.ui_style || 'CLASSIC',
          accent_color: (response.data.accent_color as AccentColor) || 'orange',
          logo_icon: (response.data.logo_icon as LogoIcon) || 'text',
          custom_logo: response.data.custom_logo || null,
          language: response.data.language || 'fr',
          toolbar_dense: response.data.toolbar_dense || false,
          desktop_notifications: response.data.desktop_notifications || false,
          sound_enabled: response.data.sound_enabled ?? true,
        };
      }
      return DEFAULT_PREFERENCES;
    },
    placeholderData: loadLocalPreferences,
  });
};

/**
 * Sauvegarde les préférences utilisateur
 */
export const useSaveUserPreferences = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (settings: UserPreferences) => {
      return api.put<UserPreferences>('/web/preferences', settings);
    },
    onSuccess: (_, settings) => {
      queryClient.invalidateQueries({ queryKey: userPreferencesKeys.all });
      // Persist to localStorage for initial load
      localStorage.setItem('azals_preferences', JSON.stringify(settings));
    },
  });
};
