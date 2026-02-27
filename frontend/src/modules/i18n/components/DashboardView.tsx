/**
 * AZALSCORE Module - I18N - Dashboard View
 * Vue tableau de bord avec statistiques de couverture
 */

import React, { useState, useEffect } from 'react';
import { i18nApi } from '../api';
import type { TranslationDashboard } from '../types';
import { StatCard, LanguageCoverageBar } from './helpers';

export const DashboardView: React.FC = () => {
  const [dashboard, setDashboard] = useState<TranslationDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await i18nApi.dashboard.get();
      setDashboard(data);
      setError(null);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">Erreur: {error}</p>
        <button
          onClick={loadDashboard}
          className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
        >
          Reessayer
        </button>
      </div>
    );
  }

  if (!dashboard) return null;

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Langues actives"
          value={dashboard.active_languages}
          subtitle={`sur ${dashboard.total_languages} total`}
          color="blue"
        />
        <StatCard
          title="Cles de traduction"
          value={dashboard.total_keys}
          subtitle={`${dashboard.total_translations} traductions`}
          color="green"
        />
        <StatCard
          title="Couverture globale"
          value={`${dashboard.overall_coverage.toFixed(1)}%`}
          subtitle="toutes langues"
          color="purple"
        />
        <StatCard
          title="A revoir"
          value={dashboard.pending_reviews}
          subtitle={`${dashboard.machine_translated_pending} auto-traduites`}
          color={dashboard.pending_reviews > 0 ? 'yellow' : 'green'}
        />
      </div>

      {/* Coverage by Language */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Couverture par langue
        </h3>
        <div className="space-y-4">
          {dashboard.languages_stats.map((stat) => (
            <LanguageCoverageBar key={stat.language_code} stat={stat} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
