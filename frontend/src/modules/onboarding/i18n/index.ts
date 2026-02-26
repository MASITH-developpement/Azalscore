/**
 * AZALSCORE - Module i18n (Internationalisation)
 * ===============================================
 * Gestion des langues et traductions pour le module de formation
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import {
  TranslationStrings,
  SupportedLanguage,
  translations,
  languageNames,
  languageFlags,
  isRTL,
  FR,
} from './translations';

// ============================================================================
// TYPES
// ============================================================================

interface I18nContextType {
  // Langue actuelle
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;

  // Traductions
  t: TranslationStrings;

  // Helpers
  isRTL: boolean;
  languageName: string;
  languageFlag: string;

  // Liste des langues
  availableLanguages: {
    code: SupportedLanguage;
    name: string;
    flag: string;
    isRTL: boolean;
  }[];

  // Formatage
  formatNumber: (num: number) => string;
  formatDate: (date: Date | string) => string;
  formatTime: (date: Date | string) => string;
  formatDuration: (minutes: number) => string;
  formatPercentage: (value: number) => string;
}

// ============================================================================
// CONTEXT
// ============================================================================

const I18nContext = createContext<I18nContextType | null>(null);

// ============================================================================
// HOOK
// ============================================================================

export function useI18n(): I18nContextType {
  const context = useContext(I18nContext);
  if (!context) {
    // Fallback si pas de provider - utilise le francais par defaut
    return createFallbackContext();
  }
  return context;
}

// ============================================================================
// FALLBACK CONTEXT (quand pas de provider)
// ============================================================================

function createFallbackContext(): I18nContextType {
  return {
    language: 'fr',
    setLanguage: () => {},
    t: FR,
    isRTL: false,
    languageName: 'Francais',
    languageFlag: '🇫🇷',
    availableLanguages: Object.keys(translations).map(code => ({
      code: code as SupportedLanguage,
      name: languageNames[code as SupportedLanguage],
      flag: languageFlags[code as SupportedLanguage],
      isRTL: isRTL[code as SupportedLanguage],
    })),
    formatNumber: (num: number) => num.toLocaleString('fr-FR'),
    formatDate: (date: Date | string) => new Date(date).toLocaleDateString('fr-FR'),
    formatTime: (date: Date | string) => new Date(date).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
    formatDuration: (minutes: number) => {
      if (minutes < 60) return `${minutes} min`;
      const h = Math.floor(minutes / 60);
      const m = minutes % 60;
      return m > 0 ? `${h}h ${m}min` : `${h}h`;
    },
    formatPercentage: (value: number) => `${value}%`,
  };
}

// ============================================================================
// PROVIDER
// ============================================================================

interface I18nProviderProps {
  children: ReactNode;
  defaultLanguage?: SupportedLanguage;
  storageKey?: string;
}

export function I18nProvider({
  children,
  defaultLanguage = 'fr',
  storageKey = 'azalscore_language',
}: I18nProviderProps) {
  // Detecter la langue du navigateur ou utiliser celle sauvegardee
  const [language, setLanguageState] = useState<SupportedLanguage>(() => {
    // 1. Verifier le localStorage
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(storageKey);
      if (saved && saved in translations) {
        return saved as SupportedLanguage;
      }

      // 2. Detecter la langue du navigateur
      const browserLang = navigator.language.split('-')[0];
      if (browserLang in translations) {
        return browserLang as SupportedLanguage;
      }
    }

    // 3. Utiliser la langue par defaut
    return defaultLanguage;
  });

  // Sauvegarder la langue quand elle change
  const setLanguage = useCallback((lang: SupportedLanguage) => {
    if (lang in translations) {
      setLanguageState(lang);
      if (typeof window !== 'undefined') {
        localStorage.setItem(storageKey, lang);
      }
    }
  }, [storageKey]);

  // Appliquer la direction RTL si necessaire
  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.dir = isRTL[language] ? 'rtl' : 'ltr';
      document.documentElement.lang = language;
    }
  }, [language]);

  // Formatage des nombres selon la locale
  const formatNumber = useCallback((num: number) => {
    const locales: Record<SupportedLanguage, string> = {
      fr: 'fr-FR',
      en: 'en-US',
      es: 'es-ES',
      de: 'de-DE',
      ar: 'ar-SA',
    };
    return num.toLocaleString(locales[language]);
  }, [language]);

  // Formatage des dates selon la locale
  const formatDate = useCallback((date: Date | string) => {
    const locales: Record<SupportedLanguage, string> = {
      fr: 'fr-FR',
      en: 'en-US',
      es: 'es-ES',
      de: 'de-DE',
      ar: 'ar-SA',
    };
    return new Date(date).toLocaleDateString(locales[language], {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  }, [language]);

  // Formatage de l'heure selon la locale
  const formatTime = useCallback((date: Date | string) => {
    const locales: Record<SupportedLanguage, string> = {
      fr: 'fr-FR',
      en: 'en-US',
      es: 'es-ES',
      de: 'de-DE',
      ar: 'ar-SA',
    };
    return new Date(date).toLocaleTimeString(locales[language], {
      hour: '2-digit',
      minute: '2-digit',
    });
  }, [language]);

  // Formatage de la duree
  const formatDuration = useCallback((minutes: number) => {
    const t = translations[language];
    if (minutes < 60) {
      return `${minutes} ${t.general.minutes}`;
    }
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    if (m === 0) {
      return `${h} ${t.general.hours}`;
    }
    return `${h}h ${m}min`;
  }, [language]);

  // Formatage des pourcentages
  const formatPercentage = useCallback((value: number) => {
    return `${value}%`;
  }, []);

  // Liste des langues disponibles
  const availableLanguages = Object.keys(translations).map(code => ({
    code: code as SupportedLanguage,
    name: languageNames[code as SupportedLanguage],
    flag: languageFlags[code as SupportedLanguage],
    isRTL: isRTL[code as SupportedLanguage],
  }));

  const value: I18nContextType = {
    language,
    setLanguage,
    t: translations[language],
    isRTL: isRTL[language],
    languageName: languageNames[language],
    languageFlag: languageFlags[language],
    availableLanguages,
    formatNumber,
    formatDate,
    formatTime,
    formatDuration,
    formatPercentage,
  };

  return React.createElement(I18nContext.Provider, { value }, children);
}

// ============================================================================
// COMPOSANT DE SELECTION DE LANGUE
// ============================================================================

interface LanguageSelectorProps {
  variant?: 'dropdown' | 'buttons' | 'flags';
  showFlag?: boolean;
  showName?: boolean;
  className?: string;
}

export function LanguageSelector({
  variant = 'dropdown',
  showFlag = true,
  showName = true,
  className = '',
}: LanguageSelectorProps) {
  const { language, setLanguage, availableLanguages } = useI18n();
  const [isOpen, setIsOpen] = useState(false);

  const currentLang = availableLanguages.find(l => l.code === language)!;

  if (variant === 'buttons') {
    return React.createElement('div', { className: `flex gap-2 ${className}` },
      availableLanguages.map(lang =>
        React.createElement('button', {
          key: lang.code,
          onClick: () => setLanguage(lang.code),
          className: `px-3 py-2 rounded-lg transition-all ${
            language === lang.code
              ? 'bg-blue-500 text-white shadow-lg'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`,
          title: lang.name,
        },
          showFlag && React.createElement('span', { className: 'mr-1' }, lang.flag),
          showName && React.createElement('span', null, lang.code.toUpperCase())
        )
      )
    );
  }

  if (variant === 'flags') {
    return React.createElement('div', { className: `flex gap-1 ${className}` },
      availableLanguages.map(lang =>
        React.createElement('button', {
          key: lang.code,
          onClick: () => setLanguage(lang.code),
          className: `text-2xl p-1 rounded transition-all ${
            language === lang.code
              ? 'ring-2 ring-blue-500 bg-blue-50'
              : 'opacity-60 hover:opacity-100'
          }`,
          title: lang.name,
        }, lang.flag)
      )
    );
  }

  // Dropdown (default)
  return React.createElement('div', { className: `relative ${className}` },
    React.createElement('button', {
      onClick: () => setIsOpen(!isOpen),
      className: 'flex items-center gap-2 px-3 py-2 bg-white border rounded-lg shadow-sm hover:bg-gray-50 transition-all',
    },
      showFlag && React.createElement('span', { className: 'text-xl' }, currentLang.flag),
      showName && React.createElement('span', { className: 'text-sm font-medium' }, currentLang.name),
      React.createElement('svg', {
        className: `w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`,
        fill: 'none',
        stroke: 'currentColor',
        viewBox: '0 0 24 24',
      },
        React.createElement('path', {
          strokeLinecap: 'round',
          strokeLinejoin: 'round',
          strokeWidth: 2,
          d: 'M19 9l-7 7-7-7',
        })
      )
    ),

    isOpen && React.createElement('div', {
      className: 'absolute top-full left-0 mt-1 bg-white border rounded-lg shadow-lg py-1 z-50 min-w-[150px]',
    },
      availableLanguages.map(lang =>
        React.createElement('button', {
          key: lang.code,
          onClick: () => {
            setLanguage(lang.code);
            setIsOpen(false);
          },
          className: `w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-100 ${
            language === lang.code ? 'bg-blue-50 text-blue-600' : ''
          }`,
        },
          React.createElement('span', { className: 'text-xl' }, lang.flag),
          React.createElement('span', { className: 'text-sm' }, lang.name),
          lang.isRTL && React.createElement('span', {
            className: 'text-xs text-gray-400 ml-auto',
          }, 'RTL')
        )
      )
    )
  );
}

// ============================================================================
// EXPORTS
// ============================================================================

export {
  translations,
  languageNames,
  languageFlags,
  isRTL,
  FR,
} from './translations';

export type { TranslationStrings, SupportedLanguage } from './translations';
export type { I18nContextType };
