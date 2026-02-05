/**
 * AZALSCORE - Shared Documents Component - DocumentUploadWidget
 * ==============================================================
 * Composant partagé pour uploader des documents.
 * Réutilisable dans tous les modules de l'application.
 */

import React, { useState, useRef, useCallback } from 'react';
import {
  Upload, FileText, X, CheckCircle, AlertCircle,
  Loader2, Cloud
} from 'lucide-react';
import { Button } from '@ui/actions';
import { formatFileSize } from '@/utils/formatters';

/**
 * États d'upload
 */
export type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

/**
 * Interface d'un fichier en cours d'upload
 */
export interface UploadFile {
  id: string;
  file: File;
  status: UploadStatus;
  progress: number;
  error?: string;
  result?: unknown;
}

/**
 * Props du composant DocumentUploadWidget
 */
export interface DocumentUploadWidgetProps {
  onUpload: (files: File[]) => Promise<void>;
  accept?: string;
  maxSize?: number; // en bytes
  maxFiles?: number;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
}

/**
 * DocumentUploadWidget - Composant d'upload de documents avec drag & drop
 */
export const DocumentUploadWidget: React.FC<DocumentUploadWidgetProps> = ({
  onUpload,
  accept = '*/*',
  maxSize = 10 * 1024 * 1024, // 10MB par défaut
  maxFiles = 5,
  multiple = true,
  disabled = false,
  className = '',
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const generateId = () => Math.random().toString(36).substring(2, 9);

  const validateFile = (file: File): string | null => {
    if (file.size > maxSize) {
      return `Fichier trop volumineux (max ${formatFileSize(maxSize)})`;
    }
    // Vérification du type si spécifié
    if (accept !== '*/*') {
      const acceptedTypes = accept.split(',').map(t => t.trim());
      const isAccepted = acceptedTypes.some(type => {
        if (type.startsWith('.')) {
          return file.name.toLowerCase().endsWith(type.toLowerCase());
        }
        if (type.endsWith('/*')) {
          return file.type.startsWith(type.replace('/*', '/'));
        }
        return file.type === type;
      });
      if (!isAccepted) {
        return 'Type de fichier non accepté';
      }
    }
    return null;
  };

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    const currentCount = files.length;
    const availableSlots = maxFiles - currentCount;

    if (availableSlots <= 0) {
      return;
    }

    const filesToAdd: UploadFile[] = fileArray.slice(0, availableSlots).map(file => {
      const error = validateFile(file);
      return {
        id: generateId(),
        file,
        status: error ? 'error' : 'idle' as UploadStatus,
        progress: 0,
        error: error || undefined,
      };
    });

    setFiles(prev => [...prev, ...filesToAdd]);
  }, [files.length, maxFiles, maxSize, accept]);

  const removeFile = useCallback((id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (!disabled && e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  }, [disabled, addFiles]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
      // Reset input
      e.target.value = '';
    }
  }, [addFiles]);

  const handleUpload = async () => {
    const validFiles = files.filter(f => f.status === 'idle');
    if (validFiles.length === 0) return;

    setIsUploading(true);

    // Marquer comme uploading
    setFiles(prev => prev.map(f =>
      f.status === 'idle' ? { ...f, status: 'uploading' as UploadStatus } : f
    ));

    try {
      await onUpload(validFiles.map(f => f.file));

      // Marquer comme succès
      setFiles(prev => prev.map(f =>
        f.status === 'uploading' ? { ...f, status: 'success' as UploadStatus, progress: 100 } : f
      ));
    } catch (error) {
      // Marquer comme erreur
      setFiles(prev => prev.map(f =>
        f.status === 'uploading' ? {
          ...f,
          status: 'error' as UploadStatus,
          error: error instanceof Error ? error.message : 'Erreur lors de l\'upload'
        } : f
      ));
    } finally {
      setIsUploading(false);
    }
  };

  const clearCompleted = () => {
    setFiles(prev => prev.filter(f => f.status !== 'success'));
  };

  const hasFilesToUpload = files.some(f => f.status === 'idle');
  const hasCompletedFiles = files.some(f => f.status === 'success');

  return (
    <div className={`azals-upload-widget ${className}`}>
      {/* Zone de drop */}
      <div
        className={`azals-upload-zone ${isDragging ? 'azals-upload-zone--dragging' : ''} ${disabled ? 'azals-upload-zone--disabled' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled}
        />
        <Cloud size={40} className="text-muted mb-2" />
        <p className="text-muted">
          Glissez vos fichiers ici ou <span className="text-primary">parcourir</span>
        </p>
        <p className="text-xs text-muted mt-1">
          Max {formatFileSize(maxSize)} par fichier • {maxFiles} fichiers max
        </p>
      </div>

      {/* Liste des fichiers */}
      {files.length > 0 && (
        <div className="azals-upload-files mt-4">
          {files.map((uploadFile) => (
            <div key={uploadFile.id} className="azals-upload-file">
              <div className="azals-upload-file__icon">
                {uploadFile.status === 'uploading' ? (
                  <Loader2 size={18} className="azals-spin text-primary" />
                ) : uploadFile.status === 'success' ? (
                  <CheckCircle size={18} className="text-success" />
                ) : uploadFile.status === 'error' ? (
                  <AlertCircle size={18} className="text-danger" />
                ) : (
                  <FileText size={18} className="text-muted" />
                )}
              </div>

              <div className="azals-upload-file__content">
                <div className="azals-upload-file__name">{uploadFile.file.name}</div>
                <div className="azals-upload-file__size text-xs text-muted">
                  {formatFileSize(uploadFile.file.size)}
                  {uploadFile.error && (
                    <span className="text-danger ml-2">{uploadFile.error}</span>
                  )}
                </div>
                {uploadFile.status === 'uploading' && (
                  <div className="azals-upload-file__progress">
                    <div
                      className="azals-upload-file__progress-bar"
                      style={{ width: `${uploadFile.progress}%` }}
                    />
                  </div>
                )}
              </div>

              {uploadFile.status !== 'uploading' && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => removeFile(uploadFile.id)}
                >
                  <X size={14} />
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      {files.length > 0 && (
        <div className="azals-upload-actions mt-4 flex gap-2">
          {hasFilesToUpload && (
            <Button
              leftIcon={<Upload size={16} />}
              onClick={handleUpload}
              disabled={isUploading}
              isLoading={isUploading}
            >
              Uploader
            </Button>
          )}
          {hasCompletedFiles && (
            <Button variant="secondary" onClick={clearCompleted}>
              Effacer terminés
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentUploadWidget;
