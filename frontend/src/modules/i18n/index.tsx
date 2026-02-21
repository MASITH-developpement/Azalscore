/**
 * AZALSCORE - Module I18N (Internationalisation)
 * ================================================
 *
 * Module complet d'internationalisation avec:
 * - Dashboard de couverture traduction
 * - Gestion des langues
 * - Gestion des traductions
 * - Import/Export
 * - Traduction automatique
 * - Glossaire
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';

// Types
import {
  Language,
  TranslationNamespace,
  TranslationKey,
  TranslationDashboard,
  LanguageStats,
  TranslationKeyWithTranslations,
  PaginatedResponse,
  LANGUAGE_STATUS_OPTIONS,
  TRANSLATION_STATUS_OPTIONS,
  COMMON_LANGUAGES,
  TRANSLATION_PROVIDER_OPTIONS,
} from './types';

// API
import { i18nApi } from './api';

// ============================================================================
// DASHBOARD COMPONENT
// ============================================================================

const DashboardView: React.FC = () => {
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
    } catch (err: any) {
      setError(err.message);
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

// ============================================================================
// LANGUAGES VIEW
// ============================================================================

const LanguagesView: React.FC = () => {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadLanguages();
  }, []);

  const loadLanguages = async () => {
    try {
      setLoading(true);
      const data = await i18nApi.language.list({ page_size: 100 });
      setLanguages(data.items);
    } catch (err) {
      console.error('Failed to load languages:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await i18nApi.language.setDefault(id);
      await loadLanguages();
    } catch (err) {
      console.error('Failed to set default language:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Supprimer cette langue ?')) return;
    try {
      await i18nApi.language.delete(id);
      await loadLanguages();
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Langues configurees</h3>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Ajouter une langue
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Langue
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Code
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Statut
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Couverture
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {languages.map((lang) => (
              <tr key={lang.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className="text-xl mr-2">{lang.flag_emoji || ''}</span>
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {lang.name}
                        {lang.is_default && (
                          <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">
                            Par defaut
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">{lang.native_name}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {lang.code}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge status={lang.status} options={LANGUAGE_STATUS_OPTIONS} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${Math.min(lang.translation_coverage, 100)}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600">
                      {lang.translation_coverage.toFixed(1)}%
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                  {!lang.is_default && (
                    <button
                      onClick={() => handleSetDefault(lang.id)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Defaut
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(lang.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Supprimer
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Language Modal */}
      {showAddModal && (
        <AddLanguageModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            loadLanguages();
          }}
        />
      )}
    </div>
  );
};

// ============================================================================
// TRANSLATIONS VIEW
// ============================================================================

const TranslationsView: React.FC = () => {
  const [namespaces, setNamespaces] = useState<TranslationNamespace[]>([]);
  const [selectedNamespace, setSelectedNamespace] = useState<string>('');
  const [keys, setKeys] = useState<TranslationKey[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [editingKey, setEditingKey] = useState<TranslationKeyWithTranslations | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedNamespace) {
      loadKeys();
    }
  }, [selectedNamespace, search]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [nsData, langData] = await Promise.all([
        i18nApi.namespace.list({ page_size: 100 }),
        i18nApi.language.listActive(),
      ]);
      setNamespaces(nsData.items);
      setLanguages(langData);
      if (nsData.items.length > 0) {
        setSelectedNamespace(nsData.items[0].id);
      }
      if (langData.length > 0) {
        const defaultLang = langData.find(l => l.is_default) || langData[0];
        setSelectedLanguage(defaultLang.code);
      }
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadKeys = async () => {
    try {
      const data = await i18nApi.key.list({
        namespace_id: selectedNamespace,
        search: search || undefined,
        page_size: 100,
      });
      setKeys(data.items);
    } catch (err) {
      console.error('Failed to load keys:', err);
    }
  };

  const handleEditKey = async (keyId: string) => {
    try {
      const keyData = await i18nApi.key.get(keyId);
      setEditingKey(keyData);
    } catch (err) {
      console.error('Failed to load key:', err);
    }
  };

  const handleSaveTranslation = async (keyId: string, langId: string, value: string) => {
    try {
      await i18nApi.translation.set(keyId, langId, { value });
      // Refresh
      if (editingKey) {
        const updated = await i18nApi.key.get(keyId);
        setEditingKey(updated);
      }
    } catch (err) {
      console.error('Failed to save translation:', err);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="flex h-full">
      {/* Sidebar - Namespaces */}
      <div className="w-64 bg-gray-50 border-r border-gray-200 p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Namespaces</h3>
        <div className="space-y-1">
          {namespaces.map((ns) => (
            <button
              key={ns.id}
              onClick={() => setSelectedNamespace(ns.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                selectedNamespace === ns.id
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {ns.name}
              <span className="text-xs text-gray-400 ml-1">({ns.total_keys})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-4 overflow-auto">
        {/* Filters */}
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            placeholder="Rechercher une cle..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            {languages.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Keys Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Cle
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Traduction ({selectedLanguage})
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {keys.map((key) => (
                <tr key={key.id}>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{key.key}</div>
                    {key.description && (
                      <div className="text-xs text-gray-500">{key.description}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {/* Translation value would be loaded separately */}
                    <span className="text-gray-400 italic">Cliquez pour editer</span>
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => handleEditKey(key.id)}
                      className="text-blue-600 hover:text-blue-900 text-sm"
                    >
                      Editer
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Modal */}
      {editingKey && (
        <TranslationEditModal
          translationKey={editingKey}
          languages={languages}
          onSave={handleSaveTranslation}
          onClose={() => setEditingKey(null)}
        />
      )}
    </div>
  );
};

// ============================================================================
// AUTO-TRANSLATE VIEW
// ============================================================================

const AutoTranslateView: React.FC = () => {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [sourceLanguage, setSourceLanguage] = useState('fr');
  const [targetLanguages, setTargetLanguages] = useState<string[]>([]);
  const [provider, setProvider] = useState<'openai' | 'google' | 'deepl'>('openai');
  const [overwrite, setOverwrite] = useState(false);
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [langData, jobsData] = await Promise.all([
        i18nApi.language.listActive(),
        i18nApi.autoTranslate.listJobs({ page_size: 10 }),
      ]);
      setLanguages(langData);
      setJobs(jobsData.items);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  };

  const handleStartTranslation = async () => {
    if (targetLanguages.length === 0) {
      alert('Selectionnez au moins une langue cible');
      return;
    }

    try {
      setLoading(true);
      await i18nApi.autoTranslate.start({
        source_language_code: sourceLanguage,
        target_language_codes: targetLanguages,
        provider,
        overwrite_existing: overwrite,
      });
      await loadData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleTargetLanguage = (code: string) => {
    setTargetLanguages((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  return (
    <div className="space-y-6">
      {/* Configuration */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Traduction automatique</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Source Language */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Langue source
            </label>
            <select
              value={sourceLanguage}
              onChange={(e) => setSourceLanguage(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            >
              {languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          {/* Provider */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Service de traduction
            </label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as any)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            >
              {TRANSLATION_PROVIDER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Target Languages */}
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Langues cibles
          </label>
          <div className="flex flex-wrap gap-2">
            {languages
              .filter((l) => l.code !== sourceLanguage)
              .map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => toggleTargetLanguage(lang.code)}
                  className={`px-3 py-1 rounded-full text-sm ${
                    targetLanguages.includes(lang.code)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {lang.flag_emoji} {lang.name}
                </button>
              ))}
          </div>
        </div>

        {/* Options */}
        <div className="mt-6">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={overwrite}
              onChange={(e) => setOverwrite(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-600">
              Ecraser les traductions existantes
            </span>
          </label>
        </div>

        {/* Start Button */}
        <div className="mt-6">
          <button
            onClick={handleStartTranslation}
            disabled={loading || targetLanguages.length === 0}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Traduction en cours...' : 'Lancer la traduction'}
          </button>
        </div>
      </div>

      {/* Jobs History */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Historique des jobs</h3>
        <div className="space-y-3">
          {jobs.map((job) => (
            <div key={job.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-center">
                <div>
                  <span className="font-medium">{job.provider}</span>
                  <span className="text-sm text-gray-500 ml-2">
                    {new Date(job.created_at).toLocaleString()}
                  </span>
                </div>
                <StatusBadge
                  status={job.status}
                  options={[
                    { value: 'PENDING', label: 'En attente', color: 'gray' },
                    { value: 'IN_PROGRESS', label: 'En cours', color: 'blue' },
                    { value: 'COMPLETED', label: 'Termine', color: 'green' },
                    { value: 'FAILED', label: 'Echec', color: 'red' },
                  ]}
                />
              </div>
              {job.status === 'IN_PROGRESS' && (
                <div className="mt-2">
                  <div className="bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${job.progress_percent}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-500">
                    {job.processed_keys}/{job.total_keys} cles
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// IMPORT/EXPORT VIEW
// ============================================================================

const ImportExportView: React.FC = () => {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadLanguages();
  }, []);

  const loadLanguages = async () => {
    const data = await i18nApi.language.listActive();
    setLanguages(data);
    setSelectedLanguages(data.map((l) => l.code));
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      const data = await i18nApi.importExport.export({
        format: 'JSON',
        language_codes: selectedLanguages,
        include_metadata: true,
      });

      // Download as file
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `translations-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setExporting(false);
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setImporting(true);
      const result = await i18nApi.importExport.import(file, {
        format: 'JSON',
        overwrite_existing: false,
      });

      alert(
        `Import termine:\n- Crees: ${result.new_keys}\n- Mis a jour: ${result.updated_keys}\n- Ignores: ${result.skipped_keys}`
      );
    } catch (err: any) {
      alert(err.message);
    } finally {
      setImporting(false);
      event.target.value = '';
    }
  };

  return (
    <div className="space-y-6">
      {/* Export */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Exporter les traductions</h3>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Langues a exporter
          </label>
          <div className="flex flex-wrap gap-2">
            {languages.map((lang) => (
              <label key={lang.code} className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedLanguages.includes(lang.code)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedLanguages([...selectedLanguages, lang.code]);
                    } else {
                      setSelectedLanguages(selectedLanguages.filter((c) => c !== lang.code));
                    }
                  }}
                  className="rounded border-gray-300 text-blue-600 mr-2"
                />
                <span className="text-sm">{lang.name}</span>
              </label>
            ))}
          </div>
        </div>

        <button
          onClick={handleExport}
          disabled={exporting || selectedLanguages.length === 0}
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {exporting ? 'Export en cours...' : 'Exporter en JSON'}
        </button>
      </div>

      {/* Import */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Importer des traductions</h3>

        <p className="text-sm text-gray-600 mb-4">
          Selectionnez un fichier JSON contenant les traductions a importer.
        </p>

        <label className="inline-block">
          <input
            type="file"
            accept=".json"
            onChange={handleImport}
            className="hidden"
            disabled={importing}
          />
          <span className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer">
            {importing ? 'Import en cours...' : 'Choisir un fichier'}
          </span>
        </label>
      </div>
    </div>
  );
};

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle: string;
  color: 'blue' | 'green' | 'purple' | 'yellow';
}> = ({ title, value, subtitle, color }) => {
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

const LanguageCoverageBar: React.FC<{ stat: LanguageStats }> = ({ stat }) => {
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

const StatusBadge: React.FC<{
  status: string;
  options: ReadonlyArray<{ value: string; label: string; color: string }>;
}> = ({ status, options }) => {
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

const LoadingSpinner: React.FC = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
);

// ============================================================================
// MODAL COMPONENTS
// ============================================================================

const AddLanguageModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [nativeName, setNativeName] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await i18nApi.language.create({
        code,
        name,
        native_name: nativeName,
      });
      onSuccess();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCommon = (lang: typeof COMMON_LANGUAGES[number]) => {
    setCode(lang.code);
    setName(lang.name);
    setNativeName(lang.native);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h3 className="text-lg font-medium mb-4">Ajouter une langue</h3>

        {/* Quick select */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Selection rapide
          </label>
          <div className="flex flex-wrap gap-2">
            {COMMON_LANGUAGES.slice(0, 6).map((lang) => (
              <button
                key={lang.code}
                type="button"
                onClick={() => handleSelectCommon(lang)}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                {lang.flag} {lang.name}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Code (ISO 639-1)
            </label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toLowerCase())}
              maxLength={5}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nom (anglais)
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nom natif
            </label>
            <input
              type="text"
              value={nativeName}
              onChange={(e) => setNativeName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Ajout...' : 'Ajouter'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const TranslationEditModal: React.FC<{
  translationKey: TranslationKeyWithTranslations;
  languages: Language[];
  onSave: (keyId: string, langId: string, value: string) => Promise<void>;
  onClose: () => void;
}> = ({ translationKey, languages, onSave, onClose }) => {
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    const initial: Record<string, string> = {};
    languages.forEach((lang) => {
      const trans = translationKey.translations[lang.code];
      initial[lang.code] = trans?.value || '';
    });
    setValues(initial);
  }, [translationKey, languages]);

  const handleSave = async (langCode: string, langId: string) => {
    try {
      setSaving(langCode);
      await onSave(translationKey.id, langId, values[langCode]);
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium">Editer: {translationKey.key}</h3>
          {translationKey.description && (
            <p className="text-sm text-gray-500 mt-1">{translationKey.description}</p>
          )}
        </div>

        <div className="p-6 overflow-auto max-h-[60vh] space-y-4">
          {languages.map((lang) => (
            <div key={lang.code} className="space-y-2">
              <label className="flex items-center text-sm font-medium text-gray-700">
                <span className="mr-2">{lang.flag_emoji}</span>
                {lang.name}
                {translationKey.translations[lang.code]?.is_machine_translated && (
                  <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded">
                    Auto
                  </span>
                )}
              </label>
              <div className="flex gap-2">
                <textarea
                  value={values[lang.code] || ''}
                  onChange={(e) =>
                    setValues({ ...values, [lang.code]: e.target.value })
                  }
                  rows={2}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg resize-none"
                  dir={lang.rtl ? 'rtl' : 'ltr'}
                />
                <button
                  onClick={() => handleSave(lang.code, lang.id)}
                  disabled={saving === lang.code}
                  className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving === lang.code ? '...' : 'OK'}
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// MAIN MODULE COMPONENT
// ============================================================================

const I18NModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'languages', label: 'Langues' },
    { id: 'translations', label: 'Traductions' },
    { id: 'auto', label: 'Traduction auto' },
    { id: 'import-export', label: 'Import/Export' },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardView />;
      case 'languages':
        return <LanguagesView />;
      case 'translations':
        return <TranslationsView />;
      case 'auto':
        return <AutoTranslateView />;
      case 'import-export':
        return <ImportExportView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">Internationalisation</h1>
        <p className="text-sm text-gray-500 mt-1">
          Gestion des langues et traductions
        </p>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 px-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6 bg-gray-50">{renderContent()}</div>
    </div>
  );
};

// ============================================================================
// ROUTES
// ============================================================================

const I18NRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<I18NModule />} />
    </Routes>
  );
};

export default I18NRoutes;
