/**
 * AZALSCORE Module - AFFAIRES - Documents Tab
 * Onglet documents et pièces jointes de l'affaire
 */

import React from 'react';
import {
  FileText, Download, Printer, Eye, Upload, Trash2,
  File, FileImage, FilePlus, FolderOpen, ExternalLink
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Affaire, AffaireDocument } from '../types';
import { formatDate } from '@/utils/formatters';

/**
 * AffaireDocsTab - Gestion des documents attachés
 */
export const AffaireDocsTab: React.FC<TabContentProps<Affaire>> = ({ data: affaire }) => {
  const canEdit = affaire.status !== 'TERMINE' && affaire.status !== 'ANNULE';
  const documents = affaire.documents || [];

  // Grouper documents par type
  const pdfDocs = documents.filter(d => d.type === 'pdf');
  const imageDocs = documents.filter(d => d.type === 'image');
  const otherDocs = documents.filter(d => d.type === 'other');

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Download size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'downloadAll', affaireId: affaire.id } })); }}>
          Télécharger tout
        </Button>
        {canEdit && (
          <Button variant="ghost" leftIcon={<Upload size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'addDocument', affaireId: affaire.id } })); }}>
            Ajouter un document
          </Button>
        )}
      </div>

      <Grid cols={2} gap="lg">
        {/* Documents liés */}
        <Card title="Documents commerciaux" icon={<FolderOpen size={18} />}>
          <div className="azals-linked-docs-list">
            {affaire.devis_reference && (
              <LinkedDocItem
                type="devis"
                label="Devis"
                reference={affaire.devis_reference}
                onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', {
                  detail: { view: 'devis', params: { id: affaire.devis_id } }
                }))}
              />
            )}
            {affaire.commande_reference && (
              <LinkedDocItem
                type="commande"
                label="Commande"
                reference={affaire.commande_reference}
                onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', {
                  detail: { view: 'commandes', params: { id: affaire.commande_id } }
                }))}
              />
            )}
            {affaire.ods_reference && (
              <LinkedDocItem
                type="ods"
                label="Ordre de service"
                reference={affaire.ods_reference}
                onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', {
                  detail: { view: 'ordres-service', params: { id: affaire.ods_id } }
                }))}
              />
            )}
            {/* Factures liées */}
            <LinkedDocItem
              type="facture"
              label="Factures"
              reference="Voir toutes"
              onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', {
                detail: { view: 'factures', params: { affaire_id: affaire.id } }
              }))}
            />
          </div>
        </Card>

        {/* Pièces jointes */}
        <Card
          title="Pièces jointes"
          icon={<FilePlus size={18} />}
        >
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
                <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'addDocument', affaireId: affaire.id } })); }}>
                  Ajouter
                </Button>
              )}
            </div>
          )}
        </Card>
      </Grid>

      {/* Documents par catégorie (ERP only) */}
      {documents.length > 0 && (
        <Card title="Documents par catégorie" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
          <Grid cols={3} gap="md">
            {/* PDFs */}
            <div className="azals-doc-category">
              <h4 className="azals-doc-category__title">
                <FileText size={16} className="text-danger" />
                Documents PDF ({pdfDocs.length})
              </h4>
              {pdfDocs.length > 0 ? (
                <ul className="azals-doc-category__list">
                  {pdfDocs.map(doc => (
                    <li key={doc.id}>{doc.name}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted text-sm">Aucun</p>
              )}
            </div>

            {/* Images */}
            <div className="azals-doc-category">
              <h4 className="azals-doc-category__title">
                <FileImage size={16} className="text-primary" />
                Images ({imageDocs.length})
              </h4>
              {imageDocs.length > 0 ? (
                <ul className="azals-doc-category__list">
                  {imageDocs.map(doc => (
                    <li key={doc.id}>{doc.name}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted text-sm">Aucune</p>
              )}
            </div>

            {/* Autres */}
            <div className="azals-doc-category">
              <h4 className="azals-doc-category__title">
                <File size={16} className="text-muted" />
                Autres ({otherDocs.length})
              </h4>
              {otherDocs.length > 0 ? (
                <ul className="azals-doc-category__list">
                  {otherDocs.map(doc => (
                    <li key={doc.id}>{doc.name}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted text-sm">Aucun</p>
              )}
            </div>
          </Grid>
        </Card>
      )}

      {/* Interventions avec rapports */}
      {affaire.interventions && affaire.interventions.length > 0 && (
        <Card title="Rapports d'intervention" icon={<FileText size={18} />} className="mt-4">
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Intervention</th>
                <th>Date</th>
                <th>Technicien</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {affaire.interventions.map((intervention) => (
                <tr key={intervention.id}>
                  <td className="font-medium">{intervention.reference}</td>
                  <td>{formatDate(intervention.date)}</td>
                  <td>{intervention.technician_name || '-'}</td>
                  <td>
                    <Button
                      size="sm"
                      variant="ghost"
                      leftIcon={<Eye size={14} />}
                      onClick={() => {
                        window.dispatchEvent(new CustomEvent('azals:navigate', {
                          detail: { view: 'interventions', params: { id: intervention.id } }
                        }));
                      }}
                    >
                      Voir
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
};

/**
 * Composant document lié
 */
interface LinkedDocItemProps {
  type: 'devis' | 'commande' | 'ods' | 'facture';
  label: string;
  reference: string;
  onClick: () => void;
}

const LinkedDocItem: React.FC<LinkedDocItemProps> = ({ type, label, reference, onClick }) => {
  const getColor = () => {
    switch (type) {
      case 'devis': return 'purple';
      case 'commande': return 'blue';
      case 'ods': return 'orange';
      case 'facture': return 'green';
      default: return 'gray';
    }
  };

  return (
    <button
      className={`azals-linked-doc-item azals-linked-doc-item--${getColor()}`}
      onClick={onClick}
    >
      <FileText size={16} />
      <div className="azals-linked-doc-item__content">
        <span className="azals-linked-doc-item__label">{label}</span>
        <span className="azals-linked-doc-item__ref">{reference}</span>
      </div>
      <ExternalLink size={14} className="azals-linked-doc-item__arrow" />
    </button>
  );
};

/**
 * Composant item de document
 */
interface DocumentItemProps {
  document: AffaireDocument;
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
          {document.created_by && ` • ${document.created_by}`}
        </span>
      </div>
      <div className="azals-document-list__actions">
        <button className="azals-btn-icon" title="Aperçu" onClick={() => { window.open(document.url, '_blank'); }}>
          <Eye size={16} />
        </button>
        <button className="azals-btn-icon" title="Télécharger" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'download', documentId: document.id } })); }}>
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

export default AffaireDocsTab;
