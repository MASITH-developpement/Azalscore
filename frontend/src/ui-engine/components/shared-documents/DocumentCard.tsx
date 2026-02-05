/**
 * AZALSCORE - Shared Documents Component - DocumentCard
 * ======================================================
 * Composant partagé pour afficher une carte de document.
 * Réutilisable dans tous les onglets documents de l'application.
 */

import React from 'react';
import {
  FileText, File, FileImage, FileArchive, FileSpreadsheet,
  FileCode, Download, Eye, Trash2, ExternalLink, Clock,
  User, Lock, AlertCircle, Check
} from 'lucide-react';
import { Button } from '@ui/actions';
import { formatDate, formatFileSize } from '@/utils/formatters';

/**
 * Types de documents supportés
 */
export type DocumentType =
  | 'pdf' | 'image' | 'spreadsheet' | 'archive' | 'code'
  | 'word' | 'presentation' | 'text' | 'other';

/**
 * Statuts de document
 */
export type DocumentStatus = 'pending' | 'approved' | 'rejected' | 'expired' | 'active';

/**
 * Interface d'un document
 */
export interface DocumentData {
  id: string;
  name: string;
  type?: DocumentType;
  mime_type?: string;
  size?: number;
  url?: string;
  thumbnail_url?: string;
  status?: DocumentStatus;
  created_at: string;
  updated_at?: string;
  uploaded_by?: string;
  description?: string;
  is_private?: boolean;
  expiry_date?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Props du composant DocumentCard
 */
export interface DocumentCardProps {
  document: DocumentData;
  onView?: (doc: DocumentData) => void;
  onDownload?: (doc: DocumentData) => void;
  onDelete?: (doc: DocumentData) => void;
  onOpen?: (doc: DocumentData) => void;
  showActions?: boolean;
  showMeta?: boolean;
  compact?: boolean;
  className?: string;
}

/**
 * Détermine l'icône en fonction du type de document
 */
function getDocumentIcon(doc: DocumentData): React.ReactNode {
  // Déterminer le type par mime_type ou extension
  const mimeType = doc.mime_type?.toLowerCase() || '';
  const name = doc.name.toLowerCase();

  if (mimeType.includes('pdf') || name.endsWith('.pdf')) {
    return <FileText size={20} className="text-red-500" />;
  }
  if (mimeType.includes('image') || /\.(jpg|jpeg|png|gif|webp|svg)$/.test(name)) {
    return <FileImage size={20} className="text-blue-500" />;
  }
  if (mimeType.includes('spreadsheet') || mimeType.includes('excel') || /\.(xlsx?|csv)$/.test(name)) {
    return <FileSpreadsheet size={20} className="text-green-500" />;
  }
  if (mimeType.includes('zip') || mimeType.includes('archive') || /\.(zip|rar|7z|tar|gz)$/.test(name)) {
    return <FileArchive size={20} className="text-yellow-500" />;
  }
  if (mimeType.includes('json') || mimeType.includes('xml') || /\.(json|xml|html|css|js|ts)$/.test(name)) {
    return <FileCode size={20} className="text-purple-500" />;
  }

  // Type explicite
  const typeIcons: Record<DocumentType, React.ReactNode> = {
    pdf: <FileText size={20} className="text-red-500" />,
    image: <FileImage size={20} className="text-blue-500" />,
    spreadsheet: <FileSpreadsheet size={20} className="text-green-500" />,
    archive: <FileArchive size={20} className="text-yellow-500" />,
    code: <FileCode size={20} className="text-purple-500" />,
    word: <FileText size={20} className="text-blue-600" />,
    presentation: <FileText size={20} className="text-orange-500" />,
    text: <FileText size={20} className="text-gray-500" />,
    other: <File size={20} className="text-gray-500" />,
  };

  return typeIcons[doc.type || 'other'];
}

/**
 * Configuration des statuts
 */
const STATUS_CONFIG: Record<DocumentStatus, { label: string; color: string; icon: React.ReactNode }> = {
  pending: { label: 'En attente', color: 'yellow', icon: <Clock size={12} /> },
  approved: { label: 'Validé', color: 'green', icon: <Check size={12} /> },
  rejected: { label: 'Rejeté', color: 'red', icon: <AlertCircle size={12} /> },
  expired: { label: 'Expiré', color: 'gray', icon: <AlertCircle size={12} /> },
  active: { label: 'Actif', color: 'blue', icon: <Check size={12} /> },
};

/**
 * DocumentCard - Composant d'affichage d'une carte de document
 */
export const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onView,
  onDownload,
  onDelete,
  onOpen,
  showActions = true,
  showMeta = true,
  compact = false,
  className = '',
}) => {
  const statusConfig = document.status ? STATUS_CONFIG[document.status] : null;

  return (
    <div className={`azals-document-card ${compact ? 'azals-document-card--compact' : ''} ${className}`}>
      {/* Aperçu / Icône */}
      <div className="azals-document-card__preview">
        {document.thumbnail_url ? (
          <img
            src={document.thumbnail_url}
            alt={document.name}
            className="azals-document-card__thumbnail"
          />
        ) : (
          getDocumentIcon(document)
        )}
        {document.is_private && (
          <span className="azals-document-card__private-badge">
            <Lock size={12} />
          </span>
        )}
      </div>

      {/* Contenu */}
      <div className="azals-document-card__content">
        <div className="azals-document-card__header">
          <h4 className="azals-document-card__name" title={document.name}>
            {document.name}
          </h4>
          {statusConfig && (
            <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--sm`}>
              {statusConfig.icon}
              <span className="ml-1">{statusConfig.label}</span>
            </span>
          )}
        </div>

        {!compact && document.description && (
          <p className="azals-document-card__description text-sm text-muted">
            {document.description}
          </p>
        )}

        {showMeta && (
          <div className="azals-document-card__meta text-xs text-muted">
            {document.size !== undefined && (
              <span>{formatFileSize(document.size)}</span>
            )}
            <span>
              <Clock size={10} className="mr-1" />
              {formatDate(document.created_at)}
            </span>
            {document.uploaded_by && (
              <span>
                <User size={10} className="mr-1" />
                {document.uploaded_by}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      {showActions && (
        <div className="azals-document-card__actions">
          {onView && (
            <span title="Aperçu">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onView(document)}
              >
                <Eye size={14} />
              </Button>
            </span>
          )}
          {onDownload && (
            <span title="Télécharger">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onDownload(document)}
              >
                <Download size={14} />
              </Button>
            </span>
          )}
          {onOpen && document.url && (
            <span title="Ouvrir">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onOpen(document)}
              >
                <ExternalLink size={14} />
              </Button>
            </span>
          )}
          {onDelete && (
            <span title="Supprimer">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onDelete(document)}
                className="text-danger"
              >
                <Trash2 size={14} />
              </Button>
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentCard;
