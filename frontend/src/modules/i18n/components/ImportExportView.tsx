/**
 * AZALSCORE Module - I18N - Import/Export View
 * Vue d'import et export des traductions
 */

import React, { useState, useEffect } from 'react';
import { i18nApi } from '../api';
import type { Language } from '../types';

export const ImportExportView: React.FC = () => {
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
    } catch (err: unknown) {
      alert((err as Error).message);
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
    } catch (err: unknown) {
      alert((err as Error).message);
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

export default ImportExportView;
