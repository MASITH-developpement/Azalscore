/**
 * AZALSCORE - Système d'internationalisation
 * Configuration i18next pour le support multilingue
 * Langue source : français
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import fr from './locales/fr';

// Configuration i18next
i18n
  .use(initReactI18next)
  .init({
    resources: {
      fr: { translation: fr },
    },
    lng: 'fr', // Langue par défaut
    fallbackLng: 'fr',
    interpolation: {
      escapeValue: false, // React gère déjà l'échappement
    },
    // Permettre les clés imbriquées avec points
    keySeparator: '.',
    nsSeparator: ':',
  });

export default i18n;

// Hook personnalisé pour obtenir le traducteur
export { useTranslation } from 'react-i18next';

// Type pour les clés de traduction (autocomplétion)
export type TranslationKey = keyof typeof fr;
