/**
 * AZALSCORE UI Standards - SidebarSummary Component
 * Sidebar avec résumé et totaux
 */

import React from 'react';
import { clsx } from 'clsx';
import type { SidebarSummaryProps, SidebarSection, SidebarSummaryItem } from './types';

/**
 * SidebarSummary - Sidebar de résumé
 *
 * Caractéristiques:
 * - Sections avec items label/valeur
 * - Support des totaux par section
 * - Champs secondaires masqués en mode AZALSCORE
 * - Formatage automatique (devise, %, date)
 */
export const SidebarSummary: React.FC<SidebarSummaryProps> = ({
  sections,
  className,
}) => {
  if (!sections || sections.length === 0) {
    return null;
  }

  return (
    <aside className={clsx('azals-std-sidebar', className)}>
      {sections.map((section) => (
        <SidebarSectionComponent key={section.id} section={section} />
      ))}
    </aside>
  );
};

/**
 * Composant section de sidebar
 */
interface SidebarSectionComponentProps {
  section: SidebarSection;
}

const SidebarSectionComponent: React.FC<SidebarSectionComponentProps> = ({
  section,
}) => {
  return (
    <div className="azals-std-sidebar__card">
      <h3 className="azals-std-sidebar__title">{section.title}</h3>

      <div className="azals-std-sidebar__items">
        {section.items.map((item) => (
          <SidebarItemComponent key={item.id} item={item} />
        ))}
      </div>

      {section.total && (
        <div className="azals-std-sidebar__total">
          <span className="azals-std-sidebar__total-label">
            {section.total.label}
          </span>
          <span className="azals-std-sidebar__total-value">
            {formatItemValue(section.total.value, 'currency')}
          </span>
        </div>
      )}
    </div>
  );
};

/**
 * Composant item de sidebar
 */
interface SidebarItemComponentProps {
  item: SidebarSummaryItem;
}

const SidebarItemComponent: React.FC<SidebarItemComponentProps> = ({ item }) => {
  const itemClasses = clsx('azals-std-sidebar__item', {
    'azals-std-field--secondary': item.secondary,
  });

  const valueClasses = clsx('azals-std-sidebar__item-value', {
    'azals-std-sidebar__item-value--highlight': item.highlight,
  });

  return (
    <div className={itemClasses}>
      <span className="azals-std-sidebar__item-label">{item.label}</span>
      <span className={valueClasses}>
        {formatItemValue(item.value, item.format)}
      </span>
    </div>
  );
};

/**
 * Formater une valeur selon son format
 */
function formatItemValue(
  value: string | number,
  format?: 'currency' | 'percent' | 'date' | 'number' | 'text'
): string {
  if (typeof value === 'string' && !format) {
    return value;
  }

  switch (format) {
    case 'currency':
      if (typeof value === 'number') {
        return new Intl.NumberFormat('fr-FR', {
          style: 'currency',
          currency: 'EUR',
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }).format(value);
      }
      return value.toString();

    case 'percent':
      if (typeof value === 'number') {
        return new Intl.NumberFormat('fr-FR', {
          style: 'percent',
          minimumFractionDigits: 1,
          maximumFractionDigits: 1,
        }).format(value / 100);
      }
      return value.toString();

    case 'date':
      if (typeof value === 'string') {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          return new Intl.DateTimeFormat('fr-FR').format(date);
        }
      }
      return value.toString();

    case 'number':
      if (typeof value === 'number') {
        return new Intl.NumberFormat('fr-FR').format(value);
      }
      return value.toString();

    default:
      if (typeof value === 'number') {
        return new Intl.NumberFormat('fr-FR').format(value);
      }
      return value.toString();
  }
}

export default SidebarSummary;
