// @ts-nocheck
/**
 * AZALS MODULE - Réseaux Sociaux
 * ==============================
 * Administration des métriques marketing des réseaux sociaux
 * Accessible via : Administration > Réseaux Sociaux
 */

import React, { useState } from 'react';
import {
  BarChart3, Target, Search, MapPin,
  RefreshCw, CheckCircle, AlertCircle,
  TrendingUp, DollarSign, Users, MousePointer, Calendar,
  Settings, PenLine
} from 'lucide-react';
import {
  GoogleAnalyticsForm,
  GoogleAdsForm,
  SearchConsoleForm,
  GoogleMyBusinessForm,
  MetaBusinessForm,
  LinkedInForm,
  SolocalForm,
  ConfigurationPanel,
} from './components';
import {
  PLATFORMS,
  formatNumber,
  formatCurrency,
  formatPercent,
  formatDate,
  type MarketingPlatform,
  type MarketingSummary,
} from './types';
import {
  socialNetworksKeys,
  useSocialSummary,
  useSocialMetrics,
  useSyncToPrometheus,
  useSaveGoogleAnalytics,
  useSaveGoogleAds,
  useSaveGoogleSearchConsole,
  useSaveGoogleMyBusiness,
  useSaveMetaBusiness,
  useSaveLinkedIn,
  useSaveSolocal,
} from './hooks';

type TabType = 'manual' | 'config';

// === Composant principal ===
export default function SocialNetworksModule() {
  const [activeTab, setActiveTab] = useState<TabType>('manual');
  const [selectedPlatform, setSelectedPlatform] = useState<MarketingPlatform | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [showSuccess, setShowSuccess] = useState(false);

  // Hooks de données
  const { data: summaryData, isLoading: summaryLoading } = useSocialSummary(selectedDate);
  const { data: recentMetrics = [], isLoading: metricsLoading } = useSocialMetrics({ limit: 50 });

  // Mutations
  const syncMutation = useSyncToPrometheus();
  const saveGAMutation = useSaveGoogleAnalytics();
  const saveAdsMutation = useSaveGoogleAds();
  const saveSCMutation = useSaveGoogleSearchConsole();
  const saveGMBMutation = useSaveGoogleMyBusiness();
  const saveMetaMutation = useSaveMetaBusiness();
  const saveLinkedInMutation = useSaveLinkedIn();
  const saveSolocalMutation = useSaveSolocal();

  function handleSaveSuccess() {
    setSelectedPlatform(null);
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
    // Sync automatique vers Prometheus
    syncMutation.mutate(selectedDate);
  }

  // Rendu du formulaire selon la plateforme sélectionnée
  const renderForm = () => {
    const commonProps = { defaultDate: selectedDate };
    const onSuccess = handleSaveSuccess;

    switch (selectedPlatform) {
      case 'google_analytics':
        return <GoogleAnalyticsForm onSubmit={(data) => saveGAMutation.mutate(data, { onSuccess })} isLoading={saveGAMutation.isPending} {...commonProps} />;
      case 'google_ads':
        return <GoogleAdsForm onSubmit={(data) => saveAdsMutation.mutate(data, { onSuccess })} isLoading={saveAdsMutation.isPending} {...commonProps} />;
      case 'google_search_console':
        return <SearchConsoleForm onSubmit={(data) => saveSCMutation.mutate(data, { onSuccess })} isLoading={saveSCMutation.isPending} {...commonProps} />;
      case 'google_my_business':
        return <GoogleMyBusinessForm onSubmit={(data) => saveGMBMutation.mutate(data, { onSuccess })} isLoading={saveGMBMutation.isPending} {...commonProps} />;
      case 'meta_facebook':
        return <MetaBusinessForm onSubmit={(data) => saveMetaMutation.mutate(data, { onSuccess })} isLoading={saveMetaMutation.isPending} defaultPlatform="meta_facebook" {...commonProps} />;
      case 'meta_instagram':
        return <MetaBusinessForm onSubmit={(data) => saveMetaMutation.mutate(data, { onSuccess })} isLoading={saveMetaMutation.isPending} defaultPlatform="meta_instagram" {...commonProps} />;
      case 'linkedin':
        return <LinkedInForm onSubmit={(data) => saveLinkedInMutation.mutate(data, { onSuccess })} isLoading={saveLinkedInMutation.isPending} {...commonProps} />;
      case 'solocal':
        return <SolocalForm onSubmit={(data) => saveSolocalMutation.mutate(data, { onSuccess })} isLoading={saveSolocalMutation.isPending} {...commonProps} />;
      default:
        return null;
    }
  };

  // Helper pour obtenir les données d'une plateforme dans le summary
  const getPlatformData = (platformId: string): Record<string, number> | null => {
    if (!summaryData) return null;
    const key = platformId as keyof MarketingSummary;
    const data = summaryData[key];
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      return data as Record<string, number>;
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Réseaux Sociaux</h1>
            <p className="text-gray-500 mt-1">Gestion des métriques marketing digitales</p>
          </div>
          <div className="flex items-center gap-4">
            {activeTab === 'manual' && (
              <>
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-gray-400" />
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button
                  onClick={() => syncMutation.mutate()}
                  disabled={syncMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                  Sync Grafana
                </button>
              </>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-6 flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('manual')}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
              activeTab === 'manual'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <PenLine className="w-4 h-4" />
            Saisie Manuelle
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
              activeTab === 'config'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Settings className="w-4 h-4" />
            Configuration & Sync Auto
          </button>
        </div>

        {/* Message de succès */}
        {showSuccess && (
          <div className="mt-4 flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700">
            <CheckCircle className="w-5 h-5" />
            Métriques enregistrées et synchronisées avec Grafana
          </div>
        )}
      </div>

      {/* Configuration Tab */}
      {activeTab === 'config' && (
        <ConfigurationPanel />
      )}

      {/* Manual Entry Tab */}
      {activeTab === 'manual' && (
        <>
      {/* KPIs Summary */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-100 rounded-lg">
              <DollarSign className="w-5 h-5 text-blue-600" />
            </div>
            <span className="text-gray-500 text-sm">Budget Total</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {summaryData ? formatCurrency(Number(summaryData.total_spend) || 0) : '—'}
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <span className="text-gray-500 text-sm">Conversions</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {summaryData ? formatNumber(summaryData.total_conversions || 0) : '—'}
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Users className="w-5 h-5 text-purple-600" />
            </div>
            <span className="text-gray-500 text-sm">Impressions</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {summaryData ? formatNumber(summaryData.total_impressions || 0) : '—'}
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-orange-100 rounded-lg">
              <MousePointer className="w-5 h-5 text-orange-600" />
            </div>
            <span className="text-gray-500 text-sm">CTR Global</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {summaryData ? formatPercent(Number(summaryData.overall_ctr) || 0) : '—'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Colonne gauche: Sélection plateforme */}
        <div className="col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Plateformes</h2>
            <div className="space-y-2">
              {PLATFORMS.map((platform) => {
                const isSelected = selectedPlatform === platform.id;
                const hasData = getPlatformData(platform.id) !== null;

                return (
                  <button
                    key={platform.id}
                    onClick={() => setSelectedPlatform(platform.id as MarketingPlatform)}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${
                      isSelected
                        ? 'bg-blue-50 border-2 border-blue-500'
                        : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                    }`}
                  >
                    <div
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: `${platform.color}20` }}
                    >
                      <BarChart3 className="w-5 h-5" style={{ color: platform.color }} />
                    </div>
                    <div className="flex-1 text-left">
                      <p className={`font-medium ${isSelected ? 'text-blue-700' : 'text-gray-900'}`}>
                        {platform.name}
                      </p>
                      <p className="text-xs text-gray-500">{platform.description}</p>
                    </div>
                    {hasData && (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Colonne droite: Formulaire ou récapitulatif */}
        <div className="col-span-2">
          {selectedPlatform ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  {(() => {
                    const platform = PLATFORMS.find(p => p.id === selectedPlatform);
                    return (
                      <>
                        <div
                          className="p-2 rounded-lg"
                          style={{ backgroundColor: `${platform?.color}20` }}
                        >
                          <BarChart3 className="w-6 h-6" style={{ color: platform?.color }} />
                        </div>
                        <div>
                          <h2 className="text-lg font-semibold text-gray-900">{platform?.name}</h2>
                          <p className="text-sm text-gray-500">Saisie des métriques pour le {formatDate(selectedDate)}</p>
                        </div>
                      </>
                    );
                  })()}
                </div>
                <button
                  onClick={() => setSelectedPlatform(null)}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                >
                  ×
                </button>
              </div>
              {renderForm()}
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Récapitulatif du {formatDate(selectedDate)}
              </h2>

              {summaryLoading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="w-8 h-8 text-gray-400 animate-spin" />
                </div>
              ) : summaryData ? (
                <div className="space-y-4">
                  {PLATFORMS.map((platform) => {
                    const data = getPlatformData(platform.id);
                    if (!data) return null;

                    return (
                      <div
                        key={platform.id}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className="p-2 rounded-lg"
                            style={{ backgroundColor: `${platform.color}20` }}
                          >
                            <BarChart3 className="w-5 h-5" style={{ color: platform.color }} />
                          </div>
                          <span className="font-medium text-gray-900">{platform.name}</span>
                        </div>
                        <div className="flex items-center gap-6 text-sm text-gray-600">
                          {data.impressions !== undefined && (
                            <span>{formatNumber(data.impressions)} imp.</span>
                          )}
                          {data.clicks !== undefined && (
                            <span>{formatNumber(data.clicks)} clics</span>
                          )}
                          {data.cost !== undefined && data.cost > 0 && (
                            <span>{formatCurrency(data.cost)}</span>
                          )}
                          {data.sessions !== undefined && (
                            <span>{formatNumber(data.sessions)} sessions</span>
                          )}
                        </div>
                      </div>
                    );
                  })}

                  {!PLATFORMS.some(p => getPlatformData(p.id) !== null) && (
                    <div className="text-center py-8 text-gray-500">
                      <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                      <p>Aucune donnée pour cette date</p>
                      <p className="text-sm mt-1">Sélectionnez une plateforme pour saisir des métriques</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>Sélectionnez une plateforme pour commencer</p>
                </div>
              )}
            </div>
          )}

          {/* Historique récent */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mt-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Historique récent</h2>
            {metricsLoading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
              </div>
            ) : recentMetrics.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="pb-3 font-medium">Date</th>
                      <th className="pb-3 font-medium">Plateforme</th>
                      <th className="pb-3 font-medium text-right">Impressions</th>
                      <th className="pb-3 font-medium text-right">Clics</th>
                      <th className="pb-3 font-medium text-right">Coût</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentMetrics.slice(0, 10).map((metric) => {
                      const platform = PLATFORMS.find(p => p.id === metric.platform);

                      return (
                        <tr key={metric.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3">{formatDate(metric.metrics_date)}</td>
                          <td className="py-3">
                            <div className="flex items-center gap-2">
                              <BarChart3 className="w-4 h-4" style={{ color: platform?.color }} />
                              <span>{platform?.name || metric.platform}</span>
                            </div>
                          </td>
                          <td className="py-3 text-right">{formatNumber(metric.impressions)}</td>
                          <td className="py-3 text-right">{formatNumber(metric.clicks)}</td>
                          <td className="py-3 text-right">
                            {metric.cost > 0 ? formatCurrency(metric.cost) : '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-center py-8 text-gray-500">Aucune donnée enregistrée</p>
            )}
          </div>
        </div>
      </div>
        </>
      )}
    </div>
  );
}

// Re-export hooks for external use
export {
  socialNetworksKeys,
  useSocialSummary,
  useSocialMetrics,
  useSyncToPrometheus,
  useSaveGoogleAnalytics,
  useSaveGoogleAds,
  useSaveGoogleSearchConsole,
  useSaveGoogleMyBusiness,
  useSaveMetaBusiness,
  useSaveLinkedIn,
  useSaveSolocal,
} from './hooks';

