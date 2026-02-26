/**
 * Module CRM - Formation
 */
import type { ModuleTrainingContent } from '@/modules/onboarding/training/types';
import type { SupportedLanguage } from '@/modules/onboarding/i18n';
import { fr } from './i18n/fr';

const translations: Record<SupportedLanguage, ModuleTrainingContent> = {
  fr: fr,
  en: fr, // TODO: Ajouter traduction anglaise
  es: fr,
  de: fr,
  ar: fr,
};

export async function loadTrainingContent(language: SupportedLanguage): Promise<ModuleTrainingContent> {
  return translations[language] || translations.fr;
}

export const CRM_TRAINING_CONFIG = {
  moduleId: 'crm',
  loader: loadTrainingContent,
  requiredPermissions: ['crm.view'],
};

export default loadTrainingContent;
