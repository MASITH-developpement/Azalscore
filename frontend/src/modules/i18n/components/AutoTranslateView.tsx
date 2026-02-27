/**
 * AZALSCORE Module - I18N - Auto Translate View
 * Vue de traduction automatique
 */

import React, { useState, useEffect } from 'react';
import { i18nApi } from '../api';
import { TRANSLATION_PROVIDER_OPTIONS } from '../types';
import type { Language } from '../types';
import { StatusBadge } from './helpers';

export const AutoTranslateView: React.FC = () => {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [sourceLanguage, setSourceLanguage] = useState('fr');
  const [targetLanguages, setTargetLanguages] = useState<string[]>([]);
  const [provider, setProvider] = useState<'openai' | 'google' | 'deepl'>('openai');
  const [overwrite, setOverwrite] = useState(false);
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState<Array<{
    id: string;
    provider: string;
    status: string;
    progress_percent: number;
    processed_keys: number;
    total_keys: number;
    created_at: string;
  }>>([]);

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
    } catch (err: unknown) {
      alert((err as Error).message);
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
              onChange={(e) => setProvider(e.target.value as 'openai' | 'google' | 'deepl')}
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

export default AutoTranslateView;
