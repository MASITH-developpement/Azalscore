/**
 * AZALSCORE Module - Maintenance - Asset Documents Tab
 * Onglet documents de l'equipement
 */

import React from 'react';
import {
  FileText, Download, Eye, Upload, Trash2,
  File, Image, Award, Shield, AlertTriangle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Asset, AssetDocument } from '../types';
import { DOCUMENT_TYPE_CONFIG, getExpiringDocuments } from '../types';
import { formatDate } from '@/utils/formatters';

/**
 * AssetDocsTab - Documents de l'equipement
 */
export const AssetDocsTab: React.FC<TabContentProps<Asset>> = ({ data: asset }) => {
  const documents = asset.documents || [];

  // Handler functions
  const handleExportDossier = (): void => {
    window.dispatchEvent(new CustomEvent('azals:asset:export-dossier', {
      detail: { assetId: asset.id }
    }));
  };

  const handleUpload = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:upload', {
      detail: { type: 'asset', id: asset.id }
    }));
  };

  const handlePreview = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:preview', {
      detail: { type: 'asset', id: asset.id }
    }));
  };

  const handleDownloadPdf = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:download', {
      detail: { type: 'asset', id: asset.id, format: 'pdf' }
    }));
  };

  // Grouper par type
  const manuals = documents.filter(d => d.type === 'manual');
  const certificates = documents.filter(d => d.type === 'certificate');
  const warranties = documents.filter(d => d.type === 'warranty');
  const inspections = documents.filter(d => d.type === 'inspection');
  const photos = documents.filter(d => d.type === 'photo');
  const others = documents.filter(d => d.type === 'other');

  // Documents expires ou expirant
  const expiringDocs = getExpiringDocuments(asset);

  return (
    <div className="azals-std-tab-content">
      {/* Alertes documents expirant */}
      {expiringDocs.length > 0 && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertTriangle size={18} />
          <span>
            {expiringDocs.length} document(s) expirant bientot ou expire(s).
          </span>
        </div>
      )}

      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Download size={16} />} onClick={handleExportDossier}>
          Exporter dossier
        </Button>
        <Button variant="ghost" leftIcon={<Upload size={16} />} onClick={handleUpload}>
          Ajouter un document
        </Button>
      </div>

      <Grid cols={2} gap="lg">
        {/* Fiche equipement */}
        <Card title="Fiche equipement" icon={<FileText size={18} />}>
          <div className="azals-document-preview">
            <div className="azals-document-preview__icon">
              <FileText size={48} className="text-primary" />
            </div>
            <div className="azals-document-preview__info">
              <h4 className="font-medium">Fiche equipement {asset.code}</h4>
              <p className="text-sm text-muted">{asset.name}</p>
            </div>
            <div className="azals-document-preview__actions">
              <Button variant="secondary" size="sm" leftIcon={<Eye size={14} />} onClick={handlePreview}>
                Apercu
              </Button>
              <Button variant="ghost" size="sm" leftIcon={<Download size={14} />} onClick={handleDownloadPdf}>
                PDF
              </Button>
            </div>
          </div>
        </Card>

        {/* Manuels */}
        <Card title="Manuels techniques" icon={<FileText size={18} />}>
          {manuals.length > 0 ? (
            <ul className="azals-document-list">
              {manuals.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <FileText size={32} className="text-muted" />
              <p className="text-muted">Aucun manuel</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={handleUpload}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>

        {/* Certificats */}
        <Card title="Certificats" icon={<Award size={18} />}>
          {certificates.length > 0 ? (
            <ul className="azals-document-list">
              {certificates.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Award size={32} className="text-muted" />
              <p className="text-muted">Aucun certificat</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={handleUpload}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>

        {/* Garanties */}
        <Card title="Documents de garantie" icon={<Shield size={18} />}>
          {warranties.length > 0 ? (
            <ul className="azals-document-list">
              {warranties.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Shield size={32} className="text-muted" />
              <p className="text-muted">Aucun document de garantie</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={handleUpload}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>
      </Grid>

      {/* Rapports d'inspection (ERP only) */}
      {inspections.length > 0 && (
        <Card title="Rapports d'inspection" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
          <ul className="azals-document-list">
            {inspections.map((doc) => (
              <DocumentItem key={doc.id} document={doc} />
            ))}
          </ul>
        </Card>
      )}

      {/* Photos (ERP only) */}
      {photos.length > 0 && (
        <Card title="Photos" icon={<Image size={18} />} className="mt-4 azals-std-field--secondary">
          <div className="azals-photo-grid">
            {photos.map((doc) => (
              <div key={doc.id} className="azals-photo-item">
                <div className="azals-photo-item__preview">
                  <Image size={32} className="text-muted" />
                </div>
                <span className="azals-photo-item__name text-sm">{doc.name}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Autres documents (ERP only) */}
      {others.length > 0 && (
        <Card title="Autres documents" icon={<File size={18} />} className="mt-4 azals-std-field--secondary">
          <ul className="azals-document-list">
            {others.map((doc) => (
              <DocumentItem key={doc.id} document={doc} />
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
};

/**
 * Composant item de document
 */
interface DocumentItemProps {
  document: AssetDocument;
}

const DocumentItem: React.FC<DocumentItemProps> = ({ document }) => {
  const handlePreview = (): void => {
    if (document.file_url) {
      window.open(document.file_url, '_blank');
    } else {
      window.dispatchEvent(new CustomEvent('azals:document:preview', {
        detail: { documentId: document.id }
      }));
    }
  };

  const handleDownload = (): void => {
    if (document.file_url) {
      window.open(document.file_url, '_blank');
    } else {
      window.dispatchEvent(new CustomEvent('azals:document:download', {
        detail: { documentId: document.id }
      }));
    }
  };

  const handleDelete = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:delete', {
      detail: { documentId: document.id }
    }));
  };

  const typeConfig = DOCUMENT_TYPE_CONFIG[document.type] || DOCUMENT_TYPE_CONFIG.other;

  const isExpiringSoon = document.expiry_date && (() => {
    const expiry = new Date(document.expiry_date);
    const now = new Date();
    const daysUntilExpiry = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
    return daysUntilExpiry <= 30;
  })();

  const isExpired = document.expiry_date && new Date(document.expiry_date) < new Date();

  const getIcon = () => {
    switch (document.type) {
      case 'manual':
        return <FileText size={20} className="text-blue-500" />;
      case 'certificate':
        return <Award size={20} className="text-green-500" />;
      case 'warranty':
        return <Shield size={20} className="text-purple-500" />;
      case 'inspection':
        return <FileText size={20} className="text-orange-500" />;
      case 'photo':
        return <Image size={20} className="text-cyan-500" />;
      default:
        return <File size={20} className="text-gray-500" />;
    }
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <li className={`azals-document-list__item ${isExpired ? 'azals-document-list__item--expired' : ''}`}>
      <div className="azals-document-list__icon">{getIcon()}</div>
      <div className="azals-document-list__info">
        <span className="azals-document-list__name">{document.name}</span>
        <span className="azals-document-list__meta text-muted text-sm">
          {formatSize(document.file_size)} . {formatDate(document.created_at)}
          {document.expiry_date && (
            <span className={isExpired ? 'text-danger' : isExpiringSoon ? 'text-warning' : ''}>
              {' . '}Expire: {formatDate(document.expiry_date)}
              {isExpired && ' (Expire)'}
              {isExpiringSoon && !isExpired && ' (Bientot)'}
            </span>
          )}
        </span>
      </div>
      <span className={`azals-badge azals-badge--${typeConfig.color} azals-badge--sm`}>
        {typeConfig.label}
      </span>
      <div className="azals-document-list__actions">
        <button className="azals-btn-icon" title="Apercu" onClick={handlePreview}>
          <Eye size={16} />
        </button>
        <button className="azals-btn-icon" title="Telecharger" onClick={handleDownload}>
          <Download size={16} />
        </button>
        <button className="azals-btn-icon azals-btn-icon--danger" title="Supprimer" onClick={handleDelete}>
          <Trash2 size={16} />
        </button>
      </div>
    </li>
  );
};

export default AssetDocsTab;
