/**
 * AZALSCORE Module - I18N - Modal Components
 * Composants de dialogue modal
 */

import React, { useState, useEffect } from 'react';
import { i18nApi } from '../api';
import { COMMON_LANGUAGES } from '../types';
import type { Language, TranslationKeyWithTranslations } from '../types';

// ============================================================================
// ADD LANGUAGE MODAL
// ============================================================================

export interface AddLanguageModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const AddLanguageModal: React.FC<AddLanguageModalProps> = ({ onClose, onSuccess }) => {
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
    } catch (err: unknown) {
      alert((err as Error).message);
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

// ============================================================================
// TRANSLATION EDIT MODAL
// ============================================================================

export interface TranslationEditModalProps {
  translationKey: TranslationKeyWithTranslations;
  languages: Language[];
  onSave: (keyId: string, langId: string, value: string) => Promise<void>;
  onClose: () => void;
}

export const TranslationEditModal: React.FC<TranslationEditModalProps> = ({
  translationKey,
  languages,
  onSave,
  onClose
}) => {
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
