/**
 * AZALSCORE Module - Qualite - NC Documents Tab
 * Onglet documents et pieces jointes
 */

import React from 'react';
import {
  FileText, Upload, Download, ExternalLink, Image, File, Camera
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { NonConformance, NCDocument } from '../types';
import { formatDate } from '@/utils/formatters';

/**
 * NCDocumentsTab - Documents
 */
export const NCDocumentsTab: React.FC<TabContentProps<NonConformance>> = ({ data: nc }) => {
  const documents = nc.documents || [];

  const photos = documents.filter(d => d.doc_type === 'photo' || d.mime_type?.startsWith('image/'));
  const reports = documents.filter(d => d.doc_type === 'rapport');
  const others = documents.filter(d => !['photo', 'rapport'].includes(d.doc_type || '') && !d.mime_type?.startsWith('image/'));

  const handleAddDocument = () => {
    console.log('Add document to NC', nc.id);
  };

  return (
    <div className="azals-std-tab-content">
      {/* Photos */}
      <Card
        title={`Photos (${photos.length})`}
        icon={<Camera size={18} />}
        className="mb-4"
        actions={
          <Button variant="ghost" size="sm" leftIcon={<Upload size={14} />} onClick={handleAddDocument}>
            Ajouter
          </Button>
        }
      >
        {photos.length > 0 ? (
          <div className="azals-photo-grid">
            {photos.map((photo) => (
              <div key={photo.id} className="azals-photo-grid__item">
                {photo.file_url ? (
                  <img src={photo.file_url} alt={photo.name} />
                ) : (
                  <div className="azals-photo-placeholder">
                    <Image size={24} className="text-muted" />
                  </div>
                )}
                <div className="azals-photo-grid__overlay">
                  <span>{photo.name}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Camera size={32} className="text-muted" />
            <p className="text-muted">Aucune photo</p>
            <p className="text-sm text-muted">
              Ajoutez des photos pour documenter la non-conformite.
            </p>
          </div>
        )}
      </Card>

      {/* Rapports */}
      <Card
        title={`Rapports (${reports.length})`}
        icon={<FileText size={18} />}
        className="mb-4"
        actions={
          <Button variant="ghost" size="sm" leftIcon={<Upload size={14} />} onClick={handleAddDocument}>
            Ajouter
          </Button>
        }
      >
        {reports.length > 0 ? (
          <div className="azals-documents-list">
            {reports.map((doc) => (
              <DocumentItem key={doc.id} document={doc} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <FileText size={32} className="text-muted" />
            <p className="text-muted">Aucun rapport</p>
          </div>
        )}
      </Card>

      {/* Autres documents (ERP only) */}
      <Card
        title={`Autres documents (${others.length})`}
        icon={<File size={18} />}
        className="azals-std-field--secondary"
        actions={
          <Button variant="ghost" size="sm" leftIcon={<Upload size={14} />} onClick={handleAddDocument}>
            Ajouter
          </Button>
        }
      >
        {others.length > 0 ? (
          <div className="azals-documents-list">
            {others.map((doc) => (
              <DocumentItem key={doc.id} document={doc} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <File size={32} className="text-muted" />
            <p className="text-muted">Aucun autre document</p>
          </div>
        )}
      </Card>
    </div>
  );
};

/**
 * Composant document
 */
const DocumentItem: React.FC<{ document: NCDocument }> = ({ document }) => {
  const getIcon = () => {
    if (document.mime_type?.startsWith('image/')) return <Image size={16} />;
    if (document.doc_type === 'rapport') return <FileText size={16} />;
    return <File size={16} />;
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} o`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  };

  return (
    <div className="azals-document-item">
      <div className="azals-document-item__icon">{getIcon()}</div>
      <div className="azals-document-item__info">
        <h4 className="azals-document-item__name">{document.name}</h4>
        <p className="azals-document-item__meta text-muted text-sm">
          {formatFileSize(document.file_size)} • {formatDate(document.created_at)}
        </p>
      </div>
      <div className="azals-document-item__actions">
        {document.file_url && (
          <>
            <a
              href={document.file_url}
              target="_blank"
              rel="noopener noreferrer"
              className="azals-btn-icon"
              title="Ouvrir"
            >
              <ExternalLink size={14} />
            </a>
            <a
              href={document.file_url}
              download={document.name}
              className="azals-btn-icon"
              title="Telecharger"
            >
              <Download size={14} />
            </a>
          </>
        )}
      </div>
    </div>
  );
};

export default NCDocumentsTab;
