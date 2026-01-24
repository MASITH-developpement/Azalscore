/**
 * AZALSCORE Module - CRM - Customer Documents Tab
 * Onglet documents du client
 */

import React from 'react';
import {
  FileText, Download, Eye, Upload, Trash2,
  File, FileImage, Printer, Building2, Receipt
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Customer, CustomerDocument } from '../types';
import { formatDate } from '../types';

/**
 * CustomerDocsTab - Documents du client
 */
export const CustomerDocsTab: React.FC<TabContentProps<Customer>> = ({ data: customer }) => {
  const documents = customer.documents || [];

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Printer size={16} />}>
          Imprimer fiche client
        </Button>
        <Button variant="secondary" leftIcon={<Download size={16} />}>
          Exporter PDF
        </Button>
        <Button variant="ghost" leftIcon={<Upload size={16} />}>
          Ajouter un document
        </Button>
      </div>

      <Grid cols={2} gap="lg">
        {/* Fiche client */}
        <Card title="Fiche client" icon={<Building2 size={18} />}>
          <div className="azals-document-preview">
            <div className="azals-document-preview__icon">
              <FileText size={48} className="text-primary" />
            </div>
            <div className="azals-document-preview__info">
              <h4 className="font-medium">Fiche client {customer.code}</h4>
              <p className="text-sm text-muted">
                {customer.name}
              </p>
            </div>
            <div className="azals-document-preview__actions">
              <Button variant="secondary" size="sm" leftIcon={<Eye size={14} />}>
                Aperçu
              </Button>
              <Button variant="ghost" size="sm" leftIcon={<Download size={14} />}>
                PDF
              </Button>
            </div>
          </div>
        </Card>

        {/* Pièces jointes */}
        <Card title="Pièces jointes" icon={<File size={18} />}>
          {documents.length > 0 ? (
            <ul className="azals-document-list">
              {documents.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <File size={32} className="text-muted" />
              <p className="text-muted">Aucune pièce jointe</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>
      </Grid>

      {/* Documents commerciaux liés */}
      <Card title="Documents commerciaux" icon={<Receipt size={18} />} className="mt-4">
        <div className="azals-linked-docs">
          <button
            className="azals-linked-doc azals-linked-doc--info"
            onClick={() => {
              window.dispatchEvent(new CustomEvent('azals:navigate', {
                detail: { view: 'devis', params: { customerId: customer.id } }
              }));
            }}
          >
            <FileText size={16} />
            <span>Devis ({customer.quote_count || 0})</span>
          </button>
          <button
            className="azals-linked-doc azals-linked-doc--info"
            onClick={() => {
              window.dispatchEvent(new CustomEvent('azals:navigate', {
                detail: { view: 'commandes', params: { customerId: customer.id } }
              }));
            }}
          >
            <FileText size={16} />
            <span>Commandes ({customer.order_count || 0})</span>
          </button>
          <button
            className="azals-linked-doc azals-linked-doc--info"
            onClick={() => {
              window.dispatchEvent(new CustomEvent('azals:navigate', {
                detail: { view: 'factures', params: { customerId: customer.id } }
              }));
            }}
          >
            <FileText size={16} />
            <span>Factures ({customer.invoice_count || 0})</span>
          </button>
        </div>
      </Card>

      {/* Documents contractuels (ERP only) */}
      <Card
        title="Documents contractuels"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-linked-docs">
          <button className="azals-linked-doc azals-linked-doc--contract">
            <FileText size={16} />
            <span>Contrats</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--contract">
            <FileText size={16} />
            <span>CGV signées</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--contract">
            <FileText size={16} />
            <span>Mandats SEPA</span>
          </button>
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant item de document
 */
interface DocumentItemProps {
  document: CustomerDocument;
}

const DocumentItem: React.FC<DocumentItemProps> = ({ document }) => {
  const getIcon = () => {
    switch (document.type) {
      case 'pdf':
        return <FileText size={20} className="text-danger" />;
      case 'image':
        return <FileImage size={20} className="text-primary" />;
      case 'contract':
        return <FileText size={20} className="text-purple" />;
      default:
        return <File size={20} className="text-muted" />;
    }
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <li className="azals-document-list__item">
      <div className="azals-document-list__icon">{getIcon()}</div>
      <div className="azals-document-list__info">
        <span className="azals-document-list__name">{document.name}</span>
        <span className="azals-document-list__meta text-muted text-sm">
          {formatSize(document.size)} • {formatDate(document.created_at)}
          {document.category && ` • ${document.category}`}
        </span>
      </div>
      <div className="azals-document-list__actions">
        <button className="azals-btn-icon" title="Aperçu">
          <Eye size={16} />
        </button>
        <button className="azals-btn-icon" title="Télécharger">
          <Download size={16} />
        </button>
        <button className="azals-btn-icon azals-btn-icon--danger" title="Supprimer">
          <Trash2 size={16} />
        </button>
      </div>
    </li>
  );
};

export default CustomerDocsTab;
