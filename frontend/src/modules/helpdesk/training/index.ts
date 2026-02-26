/**
 * Module Helpdesk - Formation
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

export const HELPDESK_TRAINING_CONFIG = {
  moduleId: 'helpdesk',
  loader: loadTrainingContent,
  requiredPermissions: ['helpdesk.view'],
};

export default loadTrainingContent;
