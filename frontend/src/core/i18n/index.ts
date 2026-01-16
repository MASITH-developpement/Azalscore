/**
 * AZALSCORE - Système i18n simple et léger
 * Pas de dépendance externe, juste des clés et traductions
 */

import { create } from 'zustand';
import frTranslations from '@/locales/fr.json';

// ============================================================
// TYPES
// ============================================================

type TranslationValue = string | Record<string, unknown>;
type Translations = Record<string, TranslationValue>;

interface I18nState {
  locale: string;
  translations: Translations;
  setLocale: (locale: string) => void;
}

// ============================================================
// STORE
// ============================================================

export const useI18nStore = create<I18nState>((set) => ({
  locale: 'fr',
  translations: frTranslations as Translations,
  setLocale: (locale: string) => {
    // Pour l'instant, seul le français est supporté
    // Extension future : charger dynamiquement les traductions
    set({ locale });
  },
}));

// ============================================================
// HELPER - Récupérer une valeur imbriquée
// ============================================================

function getNestedValue(obj: Translations, path: string): string {
  const keys = path.split('.');
  let current: unknown = obj;

  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = (current as Record<string, unknown>)[key];
    } else {
      return path; // Retourne la clé si non trouvée
    }
  }

  return typeof current === 'string' ? current : path;
}

// ============================================================
// HOOK - useTranslation
// ============================================================

export function useTranslation() {
  const { translations, locale } = useI18nStore();

  /**
   * Traduit une clé i18n
   * @param key - Clé de traduction (ex: "workspace.title")
   * @param params - Paramètres de substitution (ex: { name: "Jean" })
   */
  const t = (key: string, params?: Record<string, string | number>): string => {
    let value = getNestedValue(translations, key);

    // Substitution des paramètres {{param}}
    if (params) {
      Object.entries(params).forEach(([paramKey, paramValue]) => {
        value = value.replace(new RegExp(`{{${paramKey}}}`, 'g'), String(paramValue));
      });
    }

    return value;
  };

  return { t, locale };
}

// ============================================================
// EXPORT DIRECT - Pour usage hors composant React
// ============================================================

export function t(key: string, params?: Record<string, string | number>): string {
  const { translations } = useI18nStore.getState();
  let value = getNestedValue(translations, key);

  if (params) {
    Object.entries(params).forEach(([paramKey, paramValue]) => {
      value = value.replace(new RegExp(`{{${paramKey}}}`, 'g'), String(paramValue));
    });
  }

  return value;
}

export default useTranslation;
