/**
 * AZALSCORE Module - HR Vault - Local Components
 * Composants UI locaux
 */

import React from 'react';

// Badge simple
export const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

// Navigation par onglets
export interface TabNavProps {
  tabs: { id: string; label: string; icon?: React.ReactNode; badge?: number }[];
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
        {tab.badge !== undefined && tab.badge > 0 && (
          <span className="ml-2 azals-badge azals-badge--red azals-badge--sm">{tab.badge}</span>
        )}
      </button>
    ))}
  </nav>
);
