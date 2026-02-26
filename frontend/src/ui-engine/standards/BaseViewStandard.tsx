/**
 * AZALSCORE UI Standards - BaseViewStandard Component
 * Conteneur principal pour toutes les vues standardisées
 *
 * Structure:
 * ┌─────────────────────────────────────────────────────┐
 * │ HeaderStandard (titre, statut, actions)            │
 * ├─────────────────────────────────────────────────────┤
 * │ MainInfoBar (KPIs contextuels)                     │
 * ├───────────────────────────────────┬─────────────────┤
 * │ ContentArea                       │ SidebarSummary  │
 * │ ┌─────────────────────────────┐   │                 │
 * │ │ TabsStandard               │   │                 │
 * │ │ ├─ Informations            │   │                 │
 * │ │ ├─ Lignes                  │   │                 │
 * │ │ ├─ Financier               │   │                 │
 * │ │ ├─ Documents               │   │                 │
 * │ │ ├─ Historique              │   │                 │
 * │ │ └─ NotesIA                 │   │                 │
 * │ └─────────────────────────────┘   │                 │
 * │                                   │                 │
 * ├───────────────────────────────────┴─────────────────┤
 * │ FooterActions (actions primaires/secondaires)      │
 * └─────────────────────────────────────────────────────┘
 */

import React, { useState, useCallback } from 'react';
import { clsx } from 'clsx';
import { FooterActions } from './FooterActions';
import { HeaderStandard } from './HeaderStandard';
import { MainInfoBar } from './MainInfoBar';
import { SidebarSummary } from './SidebarSummary';
import { TabsStandard } from './TabsStandard';
import { LoadingState, ErrorState, EmptyState } from '../components/StateViews';
import type { BaseViewStandardProps } from './types';

/**
 * BaseViewStandard - Conteneur principal pour les vues
 *
 * Ce composant assemble tous les composants standardisés
 * pour créer une vue cohérente avec support dual-mode.
 *
 * Règles absolues respectées:
 * 1. Un seul DOM - Pas de duplication HTML entre modes
 * 2. CSS uniquement - Aucune logique conditionnelle backend
 * 3. Jamais supprimé - Champs non-applicables = masqués, pas retirés
 * 4. Switch instantané - Aucun rechargement de page
 * 5. Héritage obligatoire - Toutes vues utilisent BaseViewStandard
 *
 * @example
 * ```tsx
 * <BaseViewStandard
 *   title="Devis"
 *   subtitle="DEV-24-01-0001"
 *   status={{ label: 'Brouillon', color: 'gray' }}
 *   data={devis}
 *   view="detail"
 *   tabs={[
 *     { id: 'info', label: 'Informations', component: DevisInfoTab },
 *     { id: 'lines', label: 'Lignes', component: DevisLinesTab },
 *     { id: 'ia', label: 'Assistant IA', component: DevisIATab, isIA: true },
 *   ]}
 *   infoBarItems={[
 *     { id: 'total', label: 'Total HT', value: devis.subtotal },
 *   ]}
 *   sidebarSections={[
 *     { id: 'totaux', title: 'Totaux', items: [...] },
 *   ]}
 * />
 * ```
 */
export function BaseViewStandard<T>({
  title,
  subtitle,
  status,
  data,
  view,
  tabs,
  defaultTab,
  infoBarItems,
  sidebarSections,
  headerActions,
  secondaryActions,
  primaryActions,
  backAction,
  onDataChange,
  onTabChange,
  isLoading,
  error,
  onRetry,
  isEmpty,
  emptyTitle,
  emptyMessage,
  emptyAction,
  className,
}: BaseViewStandardProps<T>): React.ReactElement {
  // État de l'onglet actif
  const [activeTab, setActiveTab] = useState<string>(
    defaultTab || (tabs.length > 0 ? tabs[0].id : '')
  );

  // Handler de changement d'onglet
  const handleTabChange = useCallback(
    (tabId: string) => {
      setActiveTab(tabId);
      onTabChange?.(tabId);
    },
    [onTabChange]
  );

  // Handler de changement de données
  const handleDataChange = useCallback(
    (partialData: Partial<T>) => {
      onDataChange?.(partialData);
    },
    [onDataChange]
  );

  // Loading state with timeout
  if (isLoading) {
    return (
      <div className={clsx('azals-std-view azals-std-view--loading', className)}>
        <LoadingState onRetry={onRetry} />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={clsx('azals-std-view azals-std-view--error', className)}>
        <ErrorState
          message={error.message}
          onRetry={onRetry}
          onBack={backAction?.onClick}
        />
      </div>
    );
  }

  // Empty state
  if (isEmpty) {
    return (
      <div className={clsx('azals-std-view azals-std-view--empty', className)}>
        <EmptyState
          title={emptyTitle}
          message={emptyMessage}
          action={emptyAction}
        />
      </div>
    );
  }

  // Déterminer si on affiche la sidebar
  const hasSidebar = sidebarSections && sidebarSections.length > 0;

  return (
    <div className={clsx('azals-std-view', `azals-std-view--${view}`, className)}>
      <div className="azals-std-view__container">
        {/* Colonne principale */}
        <div className="azals-std-view__main">
          {/* En-tête */}
          <HeaderStandard
            title={title}
            subtitle={subtitle}
            status={status}
            actions={headerActions}
            backAction={backAction}
          />

          {/* Barre d'info KPIs */}
          {infoBarItems && infoBarItems.length > 0 && (
            <MainInfoBar items={infoBarItems} />
          )}

          {/* Zone de contenu avec onglets */}
          <div className="azals-std-content">
            {tabs.length > 0 && (
              <TabsStandard
                tabs={tabs}
                activeTab={activeTab}
                onTabChange={handleTabChange}
                data={data}
                onDataChange={handleDataChange}
              />
            )}
          </div>

          {/* Actions footer */}
          {(secondaryActions || primaryActions) && (
            <FooterActions
              secondaryActions={secondaryActions}
              primaryActions={primaryActions}
            />
          )}
        </div>

        {/* Sidebar (optionnelle) */}
        {hasSidebar && <SidebarSummary sections={sidebarSections} />}
      </div>
    </div>
  );
}

export default BaseViewStandard;
