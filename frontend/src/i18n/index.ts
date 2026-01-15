/**
 * AZALSCORE - Système d'internationalisation (i18n)
 *
 * Configuration de react-i18next avec :
 * - Français comme langue par défaut
 * - Chargement synchrone des traductions
 * - Support des clés hiérarchiques
 *
 * Usage :
 * import { useTranslation } from '@/i18n';
 * const { t } = useTranslation();
 * t('documents.types.QUOTE') → "Devis"
 */

import i18n from 'i18next';
import { initReactI18next, useTranslation as useI18nTranslation } from 'react-i18next';
import frTranslations from './locales/fr.json';

// Langues supportées
export const SUPPORTED_LANGUAGES = ['fr', 'en'] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

// Langue par défaut
export const DEFAULT_LANGUAGE: SupportedLanguage = 'fr';

// Ressources de traduction
const resources = {
  fr: {
    translation: frTranslations,
  },
  // Les autres langues seront ajoutées ultérieurement
  // en: { translation: enTranslations },
};

// Initialisation de i18next
i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: DEFAULT_LANGUAGE,
    fallbackLng: DEFAULT_LANGUAGE,

    // Interpolation
    interpolation: {
      escapeValue: false, // React gère déjà l'échappement
    },

    // Détection de la langue (localStorage)
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'azals_language',
    },

    // Options de namespace
    defaultNS: 'translation',
    ns: ['translation'],

    // Réagir aux changements de langue
    react: {
      useSuspense: false,
    },
  });

// Hook personnalisé avec typage
export const useTranslation = () => {
  const { t, i18n: i18nInstance } = useI18nTranslation();

  return {
    t,
    i18n: i18nInstance,
    language: i18nInstance.language as SupportedLanguage,
    changeLanguage: (lang: SupportedLanguage) => i18nInstance.changeLanguage(lang),
  };
};

// Fonction utilitaire pour traduire en dehors des composants React
export const translate = (key: string, options?: Record<string, unknown>): string => {
  return i18n.t(key, options) as string;
};

// Changer la langue
export const changeLanguage = async (lang: SupportedLanguage): Promise<void> => {
  localStorage.setItem('azals_language', lang);
  await i18n.changeLanguage(lang);
};

// Obtenir la langue courante
export const getCurrentLanguage = (): SupportedLanguage => {
  return (localStorage.getItem('azals_language') as SupportedLanguage) || DEFAULT_LANGUAGE;
};

export default i18n;
