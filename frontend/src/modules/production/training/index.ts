/**
 * Module Production - Formation
 */
import type { ModuleTrainingContent } from '@/modules/onboarding/training/types';
import type { SupportedLanguage } from '@/modules/onboarding/i18n';
import { fr } from './i18n/fr';

const translations: Record<SupportedLanguage, ModuleTrainingContent> = {
  fr: fr, en: fr, es: fr, de: fr, ar: fr,
};

export async function loadTrainingContent(language: SupportedLanguage): Promise<ModuleTrainingContent> {
  return translations[language] || translations.fr;
}

export const PRODUCTION_TRAINING_CONFIG = {
  moduleId: 'production',
  loader: loadTrainingContent,
  requiredPermissions: ['production.view'],
};

export default loadTrainingContent;
