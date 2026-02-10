/**
 * AZALSCORE Module - Vehicles - Vehicle Docs Tab
 * Onglet documents du vehicule
 */

import React from 'react';
import {
  FileText, Download, Eye, Upload, Trash2,
  File, Shield, Award, AlertTriangle, Car
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Vehicule, VehicleDocument } from '../types';
import { DOCUMENT_TYPE_CONFIG, getExpiringDocuments } from '../types';
import { formatDate } from '@/utils/formatters';

/**
 * VehicleDocsTab - Documents du vehicule
 */
export const VehicleDocsTab: React.FC<TabContentProps<Vehicule>> = ({ data: vehicle }) => {
  const documents = vehicle.documents || [];

  // Grouper par type
  const registrations = documents.filter(d => d.type === 'registration');
  const insurances = documents.filter(d => d.type === 'insurance');
  const inspections = documents.filter(d => d.type === 'inspection');
  const manuals = documents.filter(d => d.type === 'manual');
  const others = documents.filter(d => d.type === 'other');

  // Documents expires ou expirant
  const expiringDocs = getExpiringDocuments(vehicle);

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
        <Button variant="secondary" leftIcon={<Download size={16} />}>
          Exporter dossier
        </Button>
        <Button variant="ghost" leftIcon={<Upload size={16} />}>
          Ajouter un document
        </Button>
      </div>

      <Grid cols={2} gap="lg">
        {/* Carte grise */}
        <Card title="Carte grise" icon={<Car size={18} />}>
          {registrations.length > 0 ? (
            <ul className="azals-document-list">
              {registrations.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Car size={32} className="text-muted" />
              <p className="text-muted">Aucune carte grise</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>

        {/* Assurance */}
        <Card title="Assurance" icon={<Shield size={18} />}>
          {insurances.length > 0 ? (
            <ul className="azals-document-list">
              {insurances.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Shield size={32} className="text-muted" />
              <p className="text-muted">Aucun document d'assurance</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>

        {/* Controle technique */}
        <Card title="Controle technique" icon={<Award size={18} />}>
          {inspections.length > 0 ? (
            <ul className="azals-document-list">
              {inspections.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Award size={32} className="text-muted" />
              <p className="text-muted">Aucun controle technique</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>

        {/* Fiche vehicule */}
        <Card title="Fiche vehicule" icon={<FileText size={18} />}>
          <div className="azals-document-preview">
            <div className="azals-document-preview__icon">
              <FileText size={48} className="text-primary" />
            </div>
            <div className="azals-document-preview__info">
              <h4 className="font-medium">Fiche vehicule {vehicle.immatriculation}</h4>
              <p className="text-sm text-muted">{vehicle.marque} {vehicle.modele}</p>
            </div>
            <div className="azals-document-preview__actions">
              <Button variant="secondary" size="sm" leftIcon={<Eye size={14} />}>
                Apercu
              </Button>
              <Button variant="ghost" size="sm" leftIcon={<Download size={14} />}>
                PDF
              </Button>
            </div>
          </div>
        </Card>
      </Grid>

      {/* Manuels (ERP only) */}
      {manuals.length > 0 && (
        <Card title="Manuels et documentation" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
          <ul className="azals-document-list">
            {manuals.map((doc) => (
              <DocumentItem key={doc.id} document={doc} />
            ))}
          </ul>
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
  document: VehicleDocument;
}

const DocumentItem: React.FC<DocumentItemProps> = ({ document }) => {
  const typeConfig = DOCUMENT_TYPE_CONFIG[document.type] || DOCUMENT_TYPE_CONFIG.other;

  const isExpiringSoon = document.expiry_date && (() => {
    const expiry = new Date(document.expiry_date);
    const now = new Date();
    const daysUntilExpiry = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
    return daysUntilExpiry <= 30 && daysUntilExpiry > 0;
  })();

  const isExpired = document.expiry_date && new Date(document.expiry_date) < new Date();

  const getIcon = () => {
    switch (document.type) {
      case 'registration':
        return <Car size={20} className="text-blue-500" />;
      case 'insurance':
        return <Shield size={20} className="text-green-500" />;
      case 'inspection':
        return <Award size={20} className="text-purple-500" />;
      case 'manual':
        return <FileText size={20} className="text-orange-500" />;
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
        <button className="azals-btn-icon" title="Apercu">
          <Eye size={16} />
        </button>
        <button className="azals-btn-icon" title="Telecharger">
          <Download size={16} />
        </button>
        <button className="azals-btn-icon azals-btn-icon--danger" title="Supprimer">
          <Trash2 size={16} />
        </button>
      </div>
    </li>
  );
};

export default VehicleDocsTab;
