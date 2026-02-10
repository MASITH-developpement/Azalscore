/**
 * AZALS SOUS-PROGRAMME - LogoUploader
 * ====================================
 *
 * Upload de logo/photo avec preview et suppression.
 *
 * Usage:
 * ```tsx
 * <LogoUploader
 *   value={contact.logo_url}
 *   onChange={(url) => updateContact({ logo_url: url })}
 *   maxSize={2 * 1024 * 1024}  // 2MB
 *   accept="image/*"
 * />
 * ```
 */

import React, { useState, useRef } from 'react';
import { contactsApi } from '../api';

interface LogoUploaderProps {
  /** ID du contact (pour upload direct) */
  contactId?: string;
  /** URL actuelle du logo */
  value?: string | null;
  /** Callback appelé après upload/suppression */
  onChange?: (url: string | null) => void;
  /** Taille maximale du fichier en bytes (défaut: 2MB) */
  maxSize?: number;
  /** Types de fichiers acceptés */
  accept?: string;
  /** Libellé */
  label?: string;
  /** Mode lecture seule */
  readOnly?: boolean;
  /** Classe CSS additionnelle */
  className?: string;
  /** Taille de l'aperçu (sm, md, lg) */
  size?: 'sm' | 'md' | 'lg';
}

export const LogoUploader: React.FC<LogoUploaderProps> = ({
  contactId,
  value,
  onChange,
  maxSize = 2 * 1024 * 1024,
  accept = 'image/jpeg,image/png,image/gif,image/webp',
  label = 'Logo',
  readOnly = false,
  className = '',
  size = 'md',
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(value || null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-32 h-32',
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validation taille
    if (file.size > maxSize) {
      setError(`Fichier trop volumineux (max ${Math.round(maxSize / 1024 / 1024)} MB)`);
      return;
    }

    // Validation type
    const allowedTypes = accept.split(',').map((t) => t.trim());
    if (!allowedTypes.includes(file.type) && !allowedTypes.includes('image/*')) {
      setError('Type de fichier non autorisé');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      // Créer un aperçu local immédiat
      const localPreview = URL.createObjectURL(file);
      setPreviewUrl(localPreview);

      // Upload vers l'API si contactId fourni
      if (contactId) {
        const contact = await contactsApi.uploadLogo(contactId, file);
        setPreviewUrl(contact.logo_url || null);
        onChange?.(contact.logo_url || null);
      } else {
        // Mode local (pour création de contact)
        // Convertir en base64 pour stockage temporaire
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result as string;
          onChange?.(base64);
        };
        reader.readAsDataURL(file);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur upload');
      setPreviewUrl(value || null);
    } finally {
      setIsLoading(false);
    }

    // Reset input pour permettre de resélectionner le même fichier
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDelete = async () => {
    if (!confirm('Supprimer le logo ?')) return;

    setIsLoading(true);
    setError('');

    try {
      if (contactId) {
        await contactsApi.deleteLogo(contactId);
      }
      setPreviewUrl(null);
      onChange?.(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur suppression');
    } finally {
      setIsLoading(false);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={`logo-uploader ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      )}

      <div className="flex items-center gap-4">
        {/* Zone d'aperçu / upload */}
        <div
          className={`
            relative ${sizeClasses[size]} rounded-lg overflow-hidden
            border-2 border-dashed
            ${previewUrl ? 'border-transparent' : 'border-gray-300 hover:border-blue-400'}
            ${readOnly ? '' : 'cursor-pointer'}
            ${isLoading ? 'opacity-50' : ''}
          `}
          onClick={readOnly ? undefined : triggerFileInput}
        >
          {previewUrl ? (
            <img
              src={previewUrl}
              alt="Logo"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-gray-400 bg-gray-50">
              <svg className="w-8 h-8 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span className="text-xs">Ajouter</span>
            </div>
          )}

          {/* Overlay de chargement */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75">
              <svg className="animate-spin h-6 w-6 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          )}
        </div>

        {/* Actions */}
        {!readOnly && (
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={triggerFileInput}
              disabled={isLoading}
              className="px-3 py-1.5 text-sm text-blue-600 border border-blue-300 rounded hover:bg-blue-50 disabled:opacity-50"
            >
              {previewUrl ? 'Changer' : 'Ajouter'}
            </button>
            {previewUrl && (
              <button
                type="button"
                onClick={handleDelete}
                disabled={isLoading}
                className="px-3 py-1.5 text-sm text-red-600 border border-red-300 rounded hover:bg-red-50 disabled:opacity-50"
              >
                Supprimer
              </button>
            )}
          </div>
        )}

        {/* Input file caché */}
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileSelect}
          className="hidden"
          disabled={readOnly || isLoading}
        />
      </div>

      {/* Erreur */}
      {error && (
        <p className="mt-1 text-sm text-red-500">{error}</p>
      )}

      {/* Info taille */}
      {!readOnly && !error && (
        <p className="mt-1 text-xs text-gray-500">
          PNG, JPG, GIF ou WebP. Max {Math.round(maxSize / 1024 / 1024)} MB.
        </p>
      )}
    </div>
  );
};

export default LogoUploader;
