/**
 * AZALSCORE Module - I18N - Languages View
 * Vue de gestion des langues
 */

import React, { useState, useEffect } from 'react';
import { i18nApi } from '../api';
import { LANGUAGE_STATUS_OPTIONS } from '../types';
import type { Language } from '../types';
import { StatusBadge, LoadingSpinner } from './helpers';
import { AddLanguageModal } from './modals';

export const LanguagesView: React.FC = () => {
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
    } catch (err: unknown) {
      alert((err as Error).message);
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

export default LanguagesView;
