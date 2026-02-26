/**
 * AZALSCORE Module - INTERVENTIONS - Documents Tab
 * Onglet documents et rapport d'intervention
 */

import React from 'react';
import {
  FileText, Download, Eye, Upload, Trash2,
  File, FileImage, FilePlus, Camera, CheckCircle2,
  PenTool, AlertTriangle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatDuration } from '@/utils/formatters';
import type { Intervention, InterventionDocument } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * InterventionDocsTab - Documents et rapport d'intervention
 */
export const InterventionDocsTab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const canEdit = intervention.statut !== 'TERMINEE' && intervention.statut !== 'ANNULEE';
  const documents = intervention.documents || [];
  const rapport = intervention.rapport;

  // Handler functions
  const handleDownloadAll = (): void => {
    window.dispatchEvent(new CustomEvent('azals:intervention:download-all', {
      detail: { interventionId: intervention.id }
    }));
  };

  const handleUpload = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:upload', {
      detail: { type: 'intervention', id: intervention.id }
    }));
  };

  const handleViewRapport = (): void => {
    window.dispatchEvent(new CustomEvent('azals:intervention:view-rapport', {
      detail: { interventionId: intervention.id, rapportId: rapport?.id }
    }));
  };

  const handleDownloadRapportPdf = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:download', {
      detail: { type: 'rapport-intervention', id: intervention.id, format: 'pdf' }
    }));
  };

  const handleSaisirRapport = (): void => {
    window.dispatchEvent(new CustomEvent('azals:intervention:saisir-rapport', {
      detail: { interventionId: intervention.id }
    }));
  };

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Download size={16} />} onClick={handleDownloadAll}>
          Télécharger tout
        </Button>
        {canEdit && (
          <Button variant="ghost" leftIcon={<Upload size={16} />} onClick={handleUpload}>
            Ajouter un document
          </Button>
        )}
      </div>

      <Grid cols={2} gap="lg">
        {/* Rapport d'intervention */}
        <Card
          title="Rapport d'intervention"
          icon={<FileText size={18} />}
          className={rapport ? '' : 'col-span-2'}
        >
          {rapport ? (
            <div className="azals-rapport-summary">
              {/* Statut signature */}
              <div className={`azals-rapport-status azals-rapport-status--${rapport.is_signed ? 'signed' : 'unsigned'}`}>
                {rapport.is_signed ? (
                  <>
                    <CheckCircle2 size={20} className="text-success" />
                    <div>
                      <span className="font-medium">Rapport signé</span>
                      {rapport.nom_signataire && (
                        <span className="text-sm text-muted block">
                          Par {rapport.nom_signataire} le {formatDate(rapport.created_at)}
                        </span>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                    <AlertTriangle size={20} className="text-warning" />
                    <div>
                      <span className="font-medium">En attente de signature</span>
                      <span className="text-sm text-muted block">
                        Créé le {formatDate(rapport.created_at)}
                      </span>
                    </div>
                  </>
                )}
              </div>

              {/* Contenu résumé */}
              {rapport.travaux_realises && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-muted mb-1">Travaux réalisés</h4>
                  <p className="text-sm">{rapport.travaux_realises.substring(0, 200)}...</p>
                </div>
              )}

              {rapport.temps_passe_minutes && (
                <div className="mt-3">
                  <span className="text-sm text-muted">Temps passé: </span>
                  <span className="font-medium">{formatDuration(rapport.temps_passe_minutes)}</span>
                </div>
              )}

              {/* Photos */}
              {rapport.photos && rapport.photos.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-muted mb-2">
                    <Camera size={14} className="inline mr-1" />
                    Photos ({rapport.photos.length})
                  </h4>
                  <div className="azals-photo-grid">
                    {rapport.photos.slice(0, 4).map((photo, index) => (
                      <div key={index} className="azals-photo-thumb">
                        <img src={photo} alt={`Photo ${index + 1}`} />
                      </div>
                    ))}
                    {rapport.photos.length > 4 && (
                      <div className="azals-photo-more">
                        +{rapport.photos.length - 4}
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="mt-4 pt-4 border-t">
                <Button variant="secondary" size="sm" leftIcon={<Eye size={14} />} onClick={handleViewRapport}>
                  Voir le rapport complet
                </Button>
                <Button variant="ghost" size="sm" leftIcon={<Download size={14} />} className="ml-2" onClick={handleDownloadRapportPdf}>
                  Télécharger PDF
                </Button>
              </div>
            </div>
          ) : intervention.statut === 'TERMINEE' ? (
            <div className="azals-empty azals-empty--sm">
              <FileText size={32} className="text-warning" />
              <p className="text-muted">Aucun rapport enregistré</p>
              <p className="text-sm text-muted">L&apos;intervention est terminée mais le rapport n&apos;a pas été saisi.</p>
            </div>
          ) : intervention.statut === 'EN_COURS' ? (
            <div className="azals-empty azals-empty--sm">
              <PenTool size={32} className="text-primary" />
              <p className="text-muted">Rapport en attente</p>
              <p className="text-sm text-muted">Le rapport sera disponible une fois l'intervention terminée.</p>
              <Button size="sm" variant="secondary" leftIcon={<PenTool size={14} />} className="mt-2" onClick={handleSaisirRapport}>
                Saisir le rapport maintenant
              </Button>
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <FileText size={32} className="text-muted" />
              <p className="text-muted">Pas de rapport</p>
              <p className="text-sm text-muted">L'intervention n'a pas encore démarré.</p>
            </div>
          )}
        </Card>

        {/* Pièces jointes */}
        {rapport && (
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
        )}
      </Grid>

      {/* Détail rapport (ERP only) */}
      {rapport && (
        <Card title="Détail du rapport" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
          <Grid cols={2} gap="md">
            {rapport.observations && (
              <div>
                <h4 className="text-sm font-medium text-muted mb-1">Observations</h4>
                <p className="text-sm whitespace-pre-wrap">{rapport.observations}</p>
              </div>
            )}
            {rapport.recommandations && (
              <div>
                <h4 className="text-sm font-medium text-muted mb-1">Recommandations</h4>
                <p className="text-sm whitespace-pre-wrap">{rapport.recommandations}</p>
              </div>
            )}
            {rapport.pieces_remplacees && (
              <div>
                <h4 className="text-sm font-medium text-muted mb-1">Pièces remplacées</h4>
                <p className="text-sm whitespace-pre-wrap">{rapport.pieces_remplacees}</p>
              </div>
            )}
            {rapport.materiel_utilise && (
              <div>
                <h4 className="text-sm font-medium text-muted mb-1">Matériel utilisé</h4>
                <p className="text-sm whitespace-pre-wrap">{rapport.materiel_utilise}</p>
              </div>
            )}
          </Grid>
        </Card>
      )}

      {/* Documents liés */}
      {(intervention.affaire_reference || intervention.facture_reference) && (
        <Card title="Documents liés" icon={<FileText size={18} />} className="mt-4">
          <div className="azals-linked-docs">
            {intervention.affaire_reference && (
              <button
                className="azals-linked-doc azals-linked-doc--affaire"
                onClick={() => {
                  window.dispatchEvent(new CustomEvent('azals:navigate', {
                    detail: { view: 'affaires', params: { id: intervention.affaire_id } }
                  }));
                }}
              >
                <FileText size={16} />
                <span>Affaire: {intervention.affaire_reference}</span>
              </button>
            )}
            {intervention.facture_reference && (
              <button
                className="azals-linked-doc azals-linked-doc--facture"
                onClick={() => {
                  window.dispatchEvent(new CustomEvent('azals:navigate', {
                    detail: { view: 'factures', params: { id: intervention.facture_id } }
                  }));
                }}
              >
                <FileText size={16} />
                <span>Facture: {intervention.facture_reference}</span>
              </button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

/**
 * Composant item de document
 */
interface DocumentItemProps {
  document: InterventionDocument;
  canEdit: boolean;
}

const DocumentItem: React.FC<DocumentItemProps> = ({ document, canEdit }) => {
  const handlePreview = (): void => {
    if (document.url) {
      window.open(document.url, '_blank');
    } else {
      window.dispatchEvent(new CustomEvent('azals:document:preview', {
        detail: { documentId: document.id }
      }));
    }
  };

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
        <button className="azals-btn-icon" title="Aperçu" onClick={handlePreview}>
          <Eye size={16} />
        </button>
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

export default InterventionDocsTab;
