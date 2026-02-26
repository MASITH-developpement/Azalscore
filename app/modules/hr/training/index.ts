/**
 * Module RH - Formation
 */
import type { SupportedLanguage, ModuleTrainingContent } from '@/modules/onboarding/training';
import { fr } from './i18n/fr';

const translations: Record<SupportedLanguage, ModuleTrainingContent> = {
  fr: fr as ModuleTrainingContent,
  en: fr as ModuleTrainingContent,
  es: fr as ModuleTrainingContent,
  de: fr as ModuleTrainingContent,
  ar: fr as ModuleTrainingContent,
};

export async function loadTrainingContent(language: SupportedLanguage): Promise<ModuleTrainingContent> {
  return translations[language] || translations.fr;
}

export const HR_TRAINING_CONFIG = {
  moduleId: 'hr',
  loader: loadTrainingContent,
  requiredPermissions: ['hr.view'],
};

export default loadTrainingContent;
