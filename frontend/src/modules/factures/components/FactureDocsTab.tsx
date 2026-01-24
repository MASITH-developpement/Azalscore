/**
 * AZALSCORE Module - FACTURES - Documents Tab
 * Onglet documents attachés à la facture
 */

import React from 'react';
import {
  FileText, Download, Printer, Eye, Upload, Trash2,
  File, FileImage, FilePlus, Send
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Facture, FactureDocument } from '../types';
import { formatDate, TYPE_CONFIG } from '../types';

/**
 * FactureDocsTab - Gestion des documents attachés
 */
export const FactureDocsTab: React.FC<TabContentProps<Facture>> = ({ data: facture }) => {
  const canEdit = facture.status === 'DRAFT';
  const isCreditNote = facture.type === 'CREDIT_NOTE';

  // Documents simulés (à remplacer par des vraies données)
  const documents: FactureDocument[] = [
    ...(facture.pdf_url
      ? [
          {
            id: 'pdf-main',
            name: `${facture.number}.pdf`,
            type: 'pdf' as const,
            url: facture.pdf_url,
            size: 156000,
            created_at: facture.created_at,
          },
        ]
      : []),
  ];

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Download size={16} />}>
          Télécharger le PDF
        </Button>
        <Button variant="secondary" leftIcon={<Printer size={16} />}>
          Imprimer
        </Button>
        {facture.status === 'VALIDATED' && (
          <Button variant="secondary" leftIcon={<Send size={16} />}>
            Envoyer par email
          </Button>
        )}
        {canEdit && (
          <Button variant="ghost" leftIcon={<Upload size={16} />}>
            Ajouter un document
          </Button>
        )}
      </div>

      <Grid cols={2} gap="lg">
        {/* Document principal */}
        <Card title={TYPE_CONFIG[facture.type].label} icon={<FileText size={18} />}>
          <div className="azals-document-preview">
            <div className="azals-document-preview__icon">
              <FileText size={48} className={isCreditNote ? 'text-orange' : 'text-primary'} />
            </div>
            <div className="azals-document-preview__info">
              <h4>{facture.number}.pdf</h4>
              <p className="text-muted text-sm">
                {TYPE_CONFIG[facture.type].label} générée automatiquement
              </p>
              <div className="azals-document-preview__actions mt-2">
                <Button size="sm" leftIcon={<Eye size={14} />}>
                  Aperçu
                </Button>
                <Button size="sm" variant="ghost" leftIcon={<Download size={14} />}>
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
                <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />}>
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
            {facture.parent_number && (
              <tr>
                <td>
                  <span className="azals-badge azals-badge--blue">
                    {facture.parent_type === 'ORDER' ? 'Commande' : 'Intervention'}
                  </span>
                </td>
                <td>{facture.parent_number}</td>
                <td>{formatDate(facture.created_at)}</td>
                <td>
                  <span className="azals-badge azals-badge--green">Terminé</span>
                </td>
                <td>
                  <Button size="sm" variant="ghost" leftIcon={<Eye size={14} />}>
                    Voir
                  </Button>
                </td>
              </tr>
            )}
            {/* Afficher l'avoir lié si c'est une facture avec avoir */}
            {facture.type === 'INVOICE' && facture.status === 'PAID' && (
              <tr className="text-muted">
                <td colSpan={5} className="text-center py-2">
                  <Button size="sm" variant="ghost">
                    + Créer un avoir
                  </Button>
                </td>
              </tr>
            )}
            {!facture.parent_number && (
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
              <td>{formatDate(facture.created_at)}</td>
              <td>{facture.created_by || 'Système'}</td>
              <td>Création initiale</td>
              <td>
                <Button size="sm" variant="ghost" leftIcon={<Eye size={14} />}>
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
  document: FactureDocument;
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
        <button className="azals-btn-icon" title="Télécharger">
          <Download size={16} />
        </button>
        {canEdit && (
          <button className="azals-btn-icon azals-btn-icon--danger" title="Supprimer">
            <Trash2 size={16} />
          </button>
        )}
      </div>
    </li>
  );
};

export default FactureDocsTab;
