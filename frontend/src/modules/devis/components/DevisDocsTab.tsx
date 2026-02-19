/**
 * AZALSCORE Module - DEVIS - Documents Tab
 * Onglet documents attachés au devis
 */

import React from 'react';
import {
  FileText, Download, Printer, Eye, Upload, Trash2,
  File, FileImage, FilePlus
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import type { Devis, DevisDocument } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * DevisDocsTab - Gestion des documents attachés
 */
export const DevisDocsTab: React.FC<TabContentProps<Devis>> = ({ data: devis }) => {
  const canEdit = devis.status === 'DRAFT';

  // Documents simulés (à remplacer par des vraies données)
  const documents: DevisDocument[] = [
    ...(devis.pdf_url
      ? [
          {
            id: 'pdf-main',
            name: `${devis.number}.pdf`,
            type: 'pdf' as const,
            url: devis.pdf_url,
            size: 125000,
            created_at: devis.created_at,
          },
        ]
      : []),
  ];

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button
          variant="secondary"
          leftIcon={<Download size={16} />}
          onClick={() => { if (devis.pdf_url) window.open(devis.pdf_url, '_blank'); }}
        >
          Télécharger le PDF
        </Button>
        <Button
          variant="secondary"
          leftIcon={<Printer size={16} />}
          onClick={() => window.print()}
        >
          Imprimer
        </Button>
        {canEdit && (
          <Button
            variant="ghost"
            leftIcon={<Upload size={16} />}
            onClick={() => { window.dispatchEvent(new CustomEvent('azals:upload', { detail: { entity: 'devis', id: devis.id } })); }}
          >
            Ajouter un document
          </Button>
        )}
      </div>

      <Grid cols={2} gap="lg">
        {/* Document principal */}
        <Card title="Document principal" icon={<FileText size={18} />}>
          <div className="azals-document-preview">
            <div className="azals-document-preview__icon">
              <FileText size={48} className="text-primary" />
            </div>
            <div className="azals-document-preview__info">
              <h4>{devis.number}.pdf</h4>
              <p className="text-muted text-sm">
                Généré automatiquement
              </p>
              <div className="azals-document-preview__actions mt-2">
                <Button size="sm" leftIcon={<Eye size={14} />} onClick={() => { if (devis.pdf_url) window.open(devis.pdf_url, '_blank'); }}>
                  Aperçu
                </Button>
                <Button size="sm" variant="ghost" leftIcon={<Download size={14} />} onClick={() => { if (devis.pdf_url) window.open(devis.pdf_url, '_blank'); }}>
                  Télécharger
                </Button>
              </div>
            </div>
          </div>
        </Card>

        {/* Pièces jointes */}
        <Card title="Pièces jointes" icon={<FilePlus size={18} />}>
          {documents.length > 0 ? (
            <ul className="azals-document-list">
              {documents.map((doc) => (
                <DocumentItem key={doc.id} document={doc} canEdit={canEdit} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <File size={32} className="text-muted" />
              <p className="text-muted">Aucune pièce jointe</p>
              {canEdit && (
                <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:upload', { detail: { entity: 'devis', id: devis.id } })); }}>
                  Ajouter
                </Button>
              )}
            </div>
          )}
        </Card>
      </Grid>

      {/* Historique des versions (ERP only) */}
      <Card
        title="Historique des versions"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <table className="azals-table azals-table--simple">
          <thead>
            <tr>
              <th>Version</th>
              <th>Date</th>
              <th>Modifié par</th>
              <th>Changements</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>v1.0</td>
              <td>{formatDate(devis.created_at)}</td>
              <td>{devis.created_by || 'Système'}</td>
              <td>Création initiale</td>
              <td>
                <Button size="sm" variant="ghost" leftIcon={<Eye size={14} />} onClick={() => { if (devis.pdf_url) window.open(devis.pdf_url, '_blank'); }}>
                  Voir
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </Card>
    </div>
  );
};

/**
 * Composant item de document
 */
interface DocumentItemProps {
  document: DevisDocument;
  canEdit: boolean;
}

const DocumentItem: React.FC<DocumentItemProps> = ({ document, canEdit }) => {
  const getIcon = () => {
    switch (document.type) {
      case 'pdf':
        return <FileText size={20} className="text-danger" />;
      case 'image':
        return <FileImage size={20} className="text-primary" />;
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
        </span>
      </div>
      <div className="azals-document-list__actions">
        <button className="azals-btn-icon" title="Télécharger" onClick={() => { if (document.url) window.open(document.url, '_blank'); }}>
          <Download size={16} />
        </button>
        {canEdit && (
          <button className="azals-btn-icon azals-btn-icon--danger" title="Supprimer" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'deleteDocument', documentId: document.id } })); }}>
            <Trash2 size={16} />
          </button>
        )}
      </div>
    </li>
  );
};

export default DevisDocsTab;
