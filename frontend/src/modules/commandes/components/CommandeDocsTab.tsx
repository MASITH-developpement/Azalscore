/**
 * AZALSCORE Module - COMMANDES - Documents Tab
 * Onglet documents attachés à la commande
 */

import React from 'react';
import {
  FileText, Download, Printer, Eye, Upload, Trash2,
  File, FileImage, FilePlus
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Commande, CommandeDocument } from '../types';
import { formatDate } from '@/utils/formatters';

/**
 * CommandeDocsTab - Gestion des documents attachés
 */
export const CommandeDocsTab: React.FC<TabContentProps<Commande>> = ({ data: commande }) => {
  const canEdit = commande.status === 'DRAFT';

  // Handler functions
  const handleDownloadPdf = (): void => {
    if (commande.pdf_url) {
      window.open(commande.pdf_url, '_blank');
    } else {
      window.dispatchEvent(new CustomEvent('azals:document:download', {
        detail: { type: 'commande', id: commande.id, format: 'pdf' }
      }));
    }
  };

  const handlePrint = (): void => {
    window.print();
  };

  const handleUpload = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:upload', {
      detail: { type: 'commande', id: commande.id }
    }));
  };

  const handlePreview = (): void => {
    if (commande.pdf_url) {
      window.open(commande.pdf_url, '_blank');
    } else {
      window.dispatchEvent(new CustomEvent('azals:document:preview', {
        detail: { type: 'commande', id: commande.id }
      }));
    }
  };

  const handleViewRelated = (type: string, reference: string): void => {
    window.dispatchEvent(new CustomEvent('azals:navigate', {
      detail: { view: type, params: { reference } }
    }));
  };

  const handleViewVersion = (version: string): void => {
    window.dispatchEvent(new CustomEvent('azals:document:version', {
      detail: { type: 'commande', id: commande.id, version }
    }));
  };

  // Documents simulés (à remplacer par des vraies données)
  const documents: CommandeDocument[] = [
    ...(commande.pdf_url
      ? [
          {
            id: 'pdf-main',
            name: `${commande.number}.pdf`,
            type: 'pdf' as const,
            url: commande.pdf_url,
            size: 145000,
            created_at: commande.created_at,
          },
        ]
      : []),
  ];

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Download size={16} />} onClick={handleDownloadPdf}>
          Télécharger le PDF
        </Button>
        <Button variant="secondary" leftIcon={<Printer size={16} />} onClick={handlePrint}>
          Imprimer
        </Button>
        {canEdit && (
          <Button variant="ghost" leftIcon={<Upload size={16} />} onClick={handleUpload}>
            Ajouter un document
          </Button>
        )}
      </div>

      <Grid cols={2} gap="lg">
        {/* Document principal */}
        <Card title="Bon de commande" icon={<FileText size={18} />}>
          <div className="azals-document-preview">
            <div className="azals-document-preview__icon">
              <FileText size={48} className="text-primary" />
            </div>
            <div className="azals-document-preview__info">
              <h4>{commande.number}.pdf</h4>
              <p className="text-muted text-sm">
                Généré automatiquement
              </p>
              <div className="azals-document-preview__actions mt-2">
                <Button size="sm" leftIcon={<Eye size={14} />} onClick={handlePreview}>
                  Aperçu
                </Button>
                <Button size="sm" variant="ghost" leftIcon={<Download size={14} />} onClick={handleDownloadPdf}>
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
                <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={handleUpload}>
                  Ajouter
                </Button>
              )}
            </div>
          )}
        </Card>
      </Grid>

      {/* Documents liés */}
      <Card title="Documents liés" icon={<FileText size={18} />} className="mt-4">
        <table className="azals-table azals-table--simple">
          <thead>
            <tr>
              <th>Type</th>
              <th>Numéro</th>
              <th>Date</th>
              <th>Statut</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {commande.parent_number && (
              <tr>
                <td>
                  <span className="azals-badge azals-badge--blue">Devis</span>
                </td>
                <td>{commande.parent_number}</td>
                <td>{formatDate(commande.created_at)}</td>
                <td>
                  <span className="azals-badge azals-badge--green">Accepté</span>
                </td>
                <td>
                  <Button size="sm" variant="ghost" leftIcon={<Eye size={14} />} onClick={() => { handleViewRelated('devis', commande.parent_number || ''); }}>
                    Voir
                  </Button>
                </td>
              </tr>
            )}
            {commande.status === 'INVOICED' && (
              <tr>
                <td>
                  <span className="azals-badge azals-badge--purple">Facture</span>
                </td>
                <td>FAC-{commande.number.replace('COM-', '')}</td>
                <td>{formatDate(commande.updated_at)}</td>
                <td>
                  <span className="azals-badge azals-badge--green">Émise</span>
                </td>
                <td>
                  <Button size="sm" variant="ghost" leftIcon={<Eye size={14} />} onClick={() => { handleViewRelated('factures', `FAC-${commande.number.replace('COM-', '')}`); }}>
                    Voir
                  </Button>
                </td>
              </tr>
            )}
            {!commande.parent_number && commande.status !== 'INVOICED' && (
              <tr>
                <td colSpan={5} className="text-center text-muted py-4">
                  Aucun document lié
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>

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
              <td>{formatDate(commande.created_at)}</td>
              <td>{commande.created_by || 'Système'}</td>
              <td>Création initiale</td>
              <td>
                <Button size="sm" variant="ghost" leftIcon={<Eye size={14} />} onClick={() => { handleViewVersion('v1.0'); }}>
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
  document: CommandeDocument;
  canEdit: boolean;
}

const DocumentItem: React.FC<DocumentItemProps> = ({ document, canEdit }) => {
  const handleDownload = (): void => {
    if (document.url) {
      window.open(document.url, '_blank');
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
        <button className="azals-btn-icon" title="Télécharger" onClick={handleDownload}>
          <Download size={16} />
        </button>
        {canEdit && (
          <button className="azals-btn-icon azals-btn-icon--danger" title="Supprimer" onClick={handleDelete}>
            <Trash2 size={16} />
          </button>
        )}
      </div>
    </li>
  );
};

export default CommandeDocsTab;
