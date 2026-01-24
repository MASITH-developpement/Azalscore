/**
 * AZALSCORE UI Standards - TabsStandard Component
 * Navigation par onglets avec support dual-mode
 */

import React, { useCallback, useRef, useEffect, useState } from 'react';
import { clsx } from 'clsx';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { TabsStandardProps, TabDefinition } from './types';

/**
 * TabsStandard - Composant de navigation par onglets
 *
 * Caractéristiques:
 * - Navigation clavier (flèches gauche/droite)
 * - Scroll horizontal avec boutons sur mobile
 * - Support du mode IA proéminent (AZALSCORE)
 * - Onglets hidden = CSS hidden, jamais supprimés du DOM
 */
export function TabsStandard<T>({
  tabs,
  activeTab,
  onTabChange,
  data,
  onDataChange,
  className,
}: TabsStandardProps<T>): React.ReactElement {
  const tabListRef = useRef<HTMLDivElement>(null);
  const [showScrollLeft, setShowScrollLeft] = useState(false);
  const [showScrollRight, setShowScrollRight] = useState(false);

  // Vérifier si le scroll est nécessaire
  const checkScroll = useCallback(() => {
    const el = tabListRef.current;
    if (!el) return;

    setShowScrollLeft(el.scrollLeft > 0);
    setShowScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 1);
  }, []);

  useEffect(() => {
    checkScroll();
    window.addEventListener('resize', checkScroll);
    return () => window.removeEventListener('resize', checkScroll);
  }, [checkScroll]);

  // Scroll horizontal
  const scrollTabs = useCallback((direction: 'left' | 'right') => {
    const el = tabListRef.current;
    if (!el) return;

    const scrollAmount = 200;
    el.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth',
    });

    setTimeout(checkScroll, 300);
  }, [checkScroll]);

  // Navigation clavier
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, currentIndex: number) => {
      const visibleTabs = tabs.filter((t) => !t.hidden && !t.disabled);
      const currentVisibleIndex = visibleTabs.findIndex(
        (t) => t.id === tabs[currentIndex].id
      );

      let nextIndex = -1;

      if (e.key === 'ArrowLeft') {
        nextIndex = currentVisibleIndex > 0 ? currentVisibleIndex - 1 : visibleTabs.length - 1;
      } else if (e.key === 'ArrowRight') {
        nextIndex = currentVisibleIndex < visibleTabs.length - 1 ? currentVisibleIndex + 1 : 0;
      } else if (e.key === 'Home') {
        nextIndex = 0;
      } else if (e.key === 'End') {
        nextIndex = visibleTabs.length - 1;
      }

      if (nextIndex !== -1) {
        e.preventDefault();
        onTabChange(visibleTabs[nextIndex].id);
      }
    },
    [tabs, onTabChange]
  );

  // Trouver l'onglet actif (ou le premier visible si l'actif n'existe pas)
  const activeTabDef = tabs.find((t) => t.id === activeTab) || tabs.find((t) => !t.hidden);
  const ActiveComponent = activeTabDef?.component;

  return (
    <div className={clsx('azals-std-tabs', className)}>
      {/* Tab List avec scroll */}
      <div className="azals-std-tabs__scroll-container">
        {/* Bouton scroll gauche */}
        <button
          type="button"
          className={clsx(
            'azals-std-tabs__scroll-btn azals-std-tabs__scroll-btn--left',
            { 'azals-std-tabs__scroll-btn--visible': showScrollLeft }
          )}
          onClick={() => scrollTabs('left')}
          aria-label="Défiler vers la gauche"
          tabIndex={-1}
        >
          <ChevronLeft size={20} />
        </button>

        {/* Liste des onglets */}
        <div
          ref={tabListRef}
          className="azals-std-tabs__list"
          role="tablist"
          aria-label="Onglets de navigation"
          onScroll={checkScroll}
        >
          {tabs.map((tab, index) => (
            <TabButton
              key={tab.id}
              tab={tab}
              isActive={activeTab === tab.id}
              onClick={() => onTabChange(tab.id)}
              onKeyDown={(e) => handleKeyDown(e, index)}
            />
          ))}
        </div>

        {/* Bouton scroll droite */}
        <button
          type="button"
          className={clsx(
            'azals-std-tabs__scroll-btn azals-std-tabs__scroll-btn--right',
            { 'azals-std-tabs__scroll-btn--visible': showScrollRight }
          )}
          onClick={() => scrollTabs('right')}
          aria-label="Défiler vers la droite"
          tabIndex={-1}
        >
          <ChevronRight size={20} />
        </button>
      </div>

      {/* Tab Panels */}
      {tabs.map((tab) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={`tabpanel-${tab.id}`}
          aria-labelledby={`tab-${tab.id}`}
          className={clsx('azals-std-tabs__panel', {
            'azals-std-tabs__panel--active': activeTab === tab.id,
          })}
          hidden={activeTab !== tab.id}
        >
          {activeTab === tab.id && tab.component && (
            <tab.component
              data={data}
              isActive={true}
              onDataChange={onDataChange}
            />
          )}
        </div>
      ))}
    </div>
  );
}

/**
 * Composant bouton d'onglet individuel
 */
interface TabButtonProps<T> {
  tab: TabDefinition<T>;
  isActive: boolean;
  onClick: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
}

function TabButton<T>({
  tab,
  isActive,
  onClick,
  onKeyDown,
}: TabButtonProps<T>): React.ReactElement {
  return (
    <button
      type="button"
      id={`tab-${tab.id}`}
      role="tab"
      aria-selected={isActive}
      aria-controls={`tabpanel-${tab.id}`}
      tabIndex={isActive ? 0 : -1}
      className={clsx('azals-std-tabs__tab', {
        'azals-std-tabs__tab--active': isActive,
        'azals-std-tabs__tab--hidden': tab.hidden,
        'azals-std-tabs__tab--ia': tab.isIA,
      })}
      onClick={onClick}
      onKeyDown={onKeyDown}
      disabled={tab.disabled}
    >
      {tab.icon && <span className="azals-std-tabs__icon">{tab.icon}</span>}
      <span className="azals-std-tabs__label">{tab.label}</span>
      {tab.badge !== undefined && tab.badge > 0 && (
        <span
          className={clsx('azals-std-tabs__badge', {
            [`azals-std-tabs__badge--${tab.badgeColor}`]: tab.badgeColor,
          })}
        >
          {tab.badge > 99 ? '99+' : tab.badge}
        </span>
      )}
    </button>
  );
}

export default TabsStandard;
