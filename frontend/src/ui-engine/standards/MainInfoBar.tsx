/**
 * AZALSCORE UI Standards - MainInfoBar Component
 * Barre d'informations avec KPIs contextuels
 */

import React from 'react';
import { clsx } from 'clsx';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { MainInfoBarProps, InfoBarItem, TrendDirection } from './types';

/**
 * Icônes de tendance
 */
const TrendIcons: Record<TrendDirection, React.ReactNode> = {
  up: <TrendingUp size={14} />,
  down: <TrendingDown size={14} />,
  neutral: <Minus size={14} />,
};

/**
 * MainInfoBar - Barre d'informations KPI
 *
 * Caractéristiques:
 * - Affichage de KPIs contextuels
 * - Support des tendances (up/down/neutral)
 * - Champs secondaires masqués en mode AZALSCORE
 * - Scroll horizontal sur mobile
 */
export const MainInfoBar: React.FC<MainInfoBarProps> = ({ items, className }) => {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className={clsx('azals-std-infobar', className)}>
      {items.map((item) => (
        <InfoBarItemComponent key={item.id} item={item} />
      ))}
    </div>
  );
};

/**
 * Composant item individuel de la barre d'info
 */
interface InfoBarItemComponentProps {
  item: InfoBarItem;
}

const InfoBarItemComponent: React.FC<InfoBarItemComponentProps> = ({ item }) => {
  // Mapper les couleurs de valeur
  const valueColorClass = (() => {
    switch (item.valueColor) {
      case 'positive':
        return 'azals-std-infobar__value--positive';
      case 'negative':
        return 'azals-std-infobar__value--negative';
      case 'warning':
        return 'azals-std-infobar__value--warning';
      default:
        return item.valueColor ? `azals-std-infobar__value--${item.valueColor}` : '';
    }
  })();

  // Classes pour champs secondaires
  const itemClasses = clsx('azals-std-infobar__item', {
    'azals-std-field--secondary': item.secondary,
  });

  return (
    <div className={itemClasses}>
      <div className="azals-std-infobar__header">
        {item.icon && (
          <span className="azals-std-infobar__icon">{item.icon}</span>
        )}
        <span className="azals-std-infobar__label">{item.label}</span>
      </div>

      <div className={clsx('azals-std-infobar__value', valueColorClass)}>
        {formatValue(item.value)}
      </div>

      {item.trend && (
        <div
          className={clsx('azals-std-infobar__trend', {
            'azals-std-infobar__trend--up': item.trend.direction === 'up',
            'azals-std-infobar__trend--down': item.trend.direction === 'down',
          })}
        >
          {TrendIcons[item.trend.direction]}
          <span>{item.trend.value}</span>
        </div>
      )}
    </div>
  );
};

/**
 * Formater une valeur pour l'affichage
 */
function formatValue(value: string | number): string {
  if (typeof value === 'number') {
    // Formatter les grands nombres avec séparateurs
    return new Intl.NumberFormat('fr-FR').format(value);
  }
  return value;
}

export default MainInfoBar;
