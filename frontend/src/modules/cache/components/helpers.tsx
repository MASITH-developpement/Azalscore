/**
 * AZALSCORE Module - Cache - Helper Components
 * Composants utilitaires pour le module cache
 */

import React from 'react';

// ============================================================================
// BADGE
// ============================================================================

export interface BadgeProps {
  color: string;
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

// ============================================================================
// TAB NAV
// ============================================================================

export interface TabNavItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

export interface TabNavProps {
  tabs: TabNavItem[];
  activeTab: string;
  onChange: (id: string) => void;
}

export const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <nav className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.icon && <span className="mr-2">{tab.icon}</span>}
        {tab.label}
      </button>
    ))}
  </nav>
);

// ============================================================================
// PROGRESS BAR
// ============================================================================

export interface ProgressBarProps {
  value: number;
  max: number;
  color?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max,
  color = 'blue',
}) => {
  const percent = max > 0 ? (value / max) * 100 : 0;
  const barColor = percent > 90 ? 'red' : percent > 70 ? 'yellow' : color;

  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className={`h-2 rounded-full bg-${barColor}-500`}
        style={{ width: `${Math.min(percent, 100)}%` }}
      />
    </div>
  );
};

// ============================================================================
// DATE FORMATTERS
// ============================================================================

export const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

export const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};
