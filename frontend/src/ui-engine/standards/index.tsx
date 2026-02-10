/**
 * AZALSCORE UI Standards - Re-exports
 * Point d'entrée unique pour tous les composants standardisés
 *
 * @example
 * ```tsx
 * import {
 *   BaseViewStandard,
 *   TabsStandard,
 *   HeaderStandard,
 *   MainInfoBar,
 *   SidebarSummary,
 *   FooterActions,
 *   type TabDefinition,
 *   type BaseViewStandardProps,
 * } from '@ui/standards';
 * ```
 */

// Types
export type {
  UIMode,
  ViewType,
  SemanticColor,
  Size,
  ButtonVariant,
  StatusDefinition,
  ActionDefinition,
  TabContentProps,
  TabDefinition,
  TabsStandardProps,
  HeaderStandardProps,
  TrendDirection,
  InfoBarItem,
  MainInfoBarProps,
  SidebarSummaryItem,
  SidebarSection,
  SidebarSummaryProps,
  FooterActionsProps,
  BaseViewStandardProps,
  StandardComponentProps,
  FieldVisibilityProps,
  ValueFormatter,
  FormatConfig,
} from './types';

// Components
export { BaseViewStandard } from './BaseViewStandard';
export { TabsStandard } from './TabsStandard';
export { HeaderStandard } from './HeaderStandard';
export { MainInfoBar } from './MainInfoBar';
export { SidebarSummary } from './SidebarSummary';
export { FooterActions } from './FooterActions';

// Default export
export { BaseViewStandard as default } from './BaseViewStandard';
