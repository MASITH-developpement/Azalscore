/**
 * AZALSCORE Module - I18N - Translations View
 * Vue de gestion des traductions avec namespace/keys
 */

import React, { useState, useEffect } from 'react';
import { i18nApi } from '../api';
import type { TranslationNamespace, TranslationKey, Language, TranslationKeyWithTranslations } from '../types';
import { LoadingSpinner } from './helpers';
import { TranslationEditModal } from './modals';

export const TranslationsView: React.FC = () => {
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

export default TranslationsView;
