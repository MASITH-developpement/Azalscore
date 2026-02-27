/**
 * AZALSCORE Module - I18N - Helper Components
 * Composants utilitaires réutilisables
 */

import React from 'react';
import type { LanguageStats } from '../types';

export interface StatCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  color: 'blue' | 'green' | 'purple' | 'yellow';
}

export const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    purple: 'bg-purple-50 border-purple-200',
    yellow: 'bg-yellow-50 border-yellow-200',
  };

  return (
    <div className={`rounded-lg border p-4 ${colorClasses[color]}`}>
      <h4 className="text-sm font-medium text-gray-600">{title}</h4>
      <p className="text-2xl font-bold mt-1">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  );
};

export interface LanguageCoverageBarProps {
  stat: LanguageStats;
}

export const LanguageCoverageBar: React.FC<LanguageCoverageBarProps> = ({ stat }) => {
  const coverageColor =
    stat.coverage_percent >= 80
      ? 'bg-green-500'
      : stat.coverage_percent >= 50
      ? 'bg-yellow-500'
      : 'bg-red-500';

  return (
    <div className="flex items-center gap-4">
      <div className="w-24 text-sm font-medium text-gray-700">{stat.language_name}</div>
      <div className="flex-1">
        <div className="bg-gray-200 rounded-full h-3">
          <div
            className={`${coverageColor} h-3 rounded-full transition-all`}
            style={{ width: `${Math.min(stat.coverage_percent, 100)}%` }}
          ></div>
        </div>
      </div>
      <div className="w-20 text-right text-sm">
        <span className="font-medium">{stat.coverage_percent.toFixed(1)}%</span>
        <span className="text-gray-400 text-xs ml-1">
          ({stat.translated_keys}/{stat.total_keys})
        </span>
      </div>
      {stat.needs_review > 0 && (
        <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">
          {stat.needs_review} a revoir
        </span>
      )}
    </div>
  );
};

export interface StatusBadgeProps {
  status: string;
  options: ReadonlyArray<{ value: string; label: string; color: string }>;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, options }) => {
  const option = options.find((o) => o.value === status);
  const colorClasses: Record<string, string> = {
    green: 'bg-green-100 text-green-800',
    gray: 'bg-gray-100 text-gray-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    blue: 'bg-blue-100 text-blue-800',
    red: 'bg-red-100 text-red-800',
  };

  return (
    <span
      className={`px-2 py-1 text-xs font-medium rounded-full ${
        colorClasses[option?.color || 'gray']
      }`}
    >
      {option?.label || status}
    </span>
  );
};

export const LoadingSpinner: React.FC = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
);
