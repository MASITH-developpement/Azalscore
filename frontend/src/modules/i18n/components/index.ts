/**
 * AZALSCORE Module - I18N - Components Index
 * Re-exports de tous les composants
 */

// Helpers
export {
  StatCard,
  LanguageCoverageBar,
  StatusBadge,
  LoadingSpinner
} from './helpers';
export type { StatCardProps, LanguageCoverageBarProps, StatusBadgeProps } from './helpers';

// Views
export { DashboardView } from './DashboardView';
export { LanguagesView } from './LanguagesView';
export { TranslationsView } from './TranslationsView';
export { AutoTranslateView } from './AutoTranslateView';
export { ImportExportView } from './ImportExportView';

// Modals
export { AddLanguageModal, TranslationEditModal } from './modals';
export type { AddLanguageModalProps, TranslationEditModalProps } from './modals';
