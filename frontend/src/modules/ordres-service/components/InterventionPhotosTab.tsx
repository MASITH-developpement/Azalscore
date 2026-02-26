/**
 * AZALSCORE Module - Ordres de Service - Intervention Photos Tab
 * Onglet photos et documents de l'intervention
 */

import React, { useState } from 'react';
import {
  Camera, FileText, Download, ExternalLink, Upload, Image, File
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import type { Intervention } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * InterventionPhotosTab - Photos et documents
 */
export const InterventionPhotosTab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const [selectedPhoto, setSelectedPhoto] = useState<string | null>(null);

  const photos = intervention.photos || [];
  const documents = intervention.documents || [];

  const handleAddPhoto = () => {
  };

  const handleAddDocument = () => {
  };

  return (
    <div className="azals-std-tab-content">
      {/* Photos */}
      <Card
        title={`Photos (${photos.length})`}
        icon={<Camera size={18} />}
        className="mb-4"
        actions={
          <Button variant="ghost" size="sm" leftIcon={<Upload size={14} />} onClick={handleAddPhoto}>
            Ajouter
          </Button>
        }
      >
        {photos.length > 0 ? (
          <div className="azals-photo-grid">
            {photos.map((url, index) => (
              <div
                key={index}
                className="azals-photo-grid__item"
                onClick={() => setSelectedPhoto(url)}
              >
                <img src={url} alt={`Photo ${index + 1}`} />
                <div className="azals-photo-grid__overlay">
                  <span>Photo {index + 1}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Camera size={32} className="text-muted" />
            <p className="text-muted">Aucune photo</p>
            <Button
              variant="secondary"
              size="sm"
              leftIcon={<Upload size={14} />}
              onClick={handleAddPhoto}
            >
              Ajouter une photo
            </Button>
          </div>
        )}
      </Card>

      {/* Signature client */}
      {intervention.signature_client && (
        <Card title="Signature client" icon={<FileText size={18} />} className="mb-4">
          <div className="azals-signature">
            <img
              src={intervention.signature_client}
              alt="Signature du client"
              className="azals-signature__image"
            />
            <p className="text-sm text-muted mt-2">
              Signature recueillie lors de la cloture de l'intervention
            </p>
          </div>
        </Card>
      )}

      {/* Documents (ERP only) */}
      <Card
        title={`Documents (${documents.length})`}
        icon={<FileText size={18} />}
        className="azals-std-field--secondary"
        actions={
          <Button variant="ghost" size="sm" leftIcon={<Upload size={14} />} onClick={handleAddDocument}>
            Ajouter
          </Button>
        }
      >
        {documents.length > 0 ? (
          <div className="azals-documents-list">
            {documents.map((doc) => (
              <DocumentItem key={doc.id} document={doc} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <File size={32} className="text-muted" />
            <p className="text-muted">Aucun document</p>
          </div>
        )}
      </Card>

      {/* Modal photo plein ecran */}
      {selectedPhoto && (
        <div className="azals-lightbox" onClick={() => setSelectedPhoto(null)}>
          <div className="azals-lightbox__content" onClick={(e) => e.stopPropagation()}>
            <img src={selectedPhoto} alt="Photo en grand" />
            <button
              className="azals-lightbox__close"
              onClick={() => setSelectedPhoto(null)}
            >
              &times;
            </button>
            <div className="azals-lightbox__actions">
              <a
                href={selectedPhoto}
                download
                className="azals-btn azals-btn--secondary"
                onClick={(e) => e.stopPropagation()}
              >
                <Download size={16} />
                Telecharger
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Composant document
 */
interface DocumentItemProps {
  document: {
    id: string;
    name: string;
    file_url?: string;
    file_size?: number;
    mime_type?: string;
    doc_type?: string;
    created_at: string;
  };
}

const DocumentItem: React.FC<DocumentItemProps> = ({ document }) => {
  const getIcon = () => {
    if (document.doc_type === 'photo') return <Image size={16} />;
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

export default InterventionPhotosTab;
