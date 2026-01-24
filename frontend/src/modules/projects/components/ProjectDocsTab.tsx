/**
 * AZALSCORE Module - Projects - Project Documents Tab
 * Onglet documents du projet
 */

import React from 'react';
import {
  FileText, Download, Eye, Upload, Trash2,
  File, FileSpreadsheet, Award, Folder
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Project, ProjectDocument } from '../types';
import { formatDate, DOCUMENT_TYPE_CONFIG } from '../types';

/**
 * ProjectDocsTab - Documents du projet
 */
export const ProjectDocsTab: React.FC<TabContentProps<Project>> = ({ data: project }) => {
  const documents = project.documents || [];

  // Grouper par type
  const specifications = documents.filter(d => d.type === 'specification');
  const contracts = documents.filter(d => d.type === 'contract');
  const reports = documents.filter(d => d.type === 'report');
  const invoices = documents.filter(d => d.type === 'invoice');
  const others = documents.filter(d => d.type === 'other');

  return (
    <div className="azals-std-tab-content">
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
        {/* Fiche projet */}
        <Card title="Fiche projet" icon={<Folder size={18} />}>
          <div className="azals-document-preview">
            <div className="azals-document-preview__icon">
              <FileText size={48} className="text-primary" />
            </div>
            <div className="azals-document-preview__info">
              <h4 className="font-medium">Fiche projet {project.code}</h4>
              <p className="text-sm text-muted">{project.name}</p>
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

        {/* Specifications */}
        <Card title="Specifications" icon={<FileText size={18} />}>
          {specifications.length > 0 ? (
            <ul className="azals-document-list">
              {specifications.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <FileText size={32} className="text-muted" />
              <p className="text-muted">Aucune specification</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>

        {/* Contrats */}
        <Card title="Contrats" icon={<Award size={18} />}>
          {contracts.length > 0 ? (
            <ul className="azals-document-list">
              {contracts.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Award size={32} className="text-muted" />
              <p className="text-muted">Aucun contrat</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>

        {/* Rapports */}
        <Card title="Rapports" icon={<FileSpreadsheet size={18} />}>
          {reports.length > 0 ? (
            <ul className="azals-document-list">
              {reports.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <FileSpreadsheet size={32} className="text-muted" />
              <p className="text-muted">Aucun rapport</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>
      </Grid>

      {/* Factures (ERP only) */}
      {invoices.length > 0 && (
        <Card title="Factures" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
          <ul className="azals-document-list">
            {invoices.map((doc) => (
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
  document: ProjectDocument;
}

const DocumentItem: React.FC<DocumentItemProps> = ({ document }) => {
  const typeConfig = DOCUMENT_TYPE_CONFIG[document.type] || DOCUMENT_TYPE_CONFIG.other;

  const getIcon = () => {
    switch (document.type) {
      case 'specification':
        return <FileText size={20} className="text-blue-500" />;
      case 'contract':
        return <Award size={20} className="text-purple-500" />;
      case 'report':
        return <FileSpreadsheet size={20} className="text-green-500" />;
      case 'invoice':
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
    <li className="azals-document-list__item">
      <div className="azals-document-list__icon">{getIcon()}</div>
      <div className="azals-document-list__info">
        <span className="azals-document-list__name">{document.name}</span>
        <span className="azals-document-list__meta text-muted text-sm">
          {formatSize(document.file_size)} . {formatDate(document.created_at)}
          {document.category && ` . ${document.category}`}
          {document.uploaded_by_name && (
            <span> . Par {document.uploaded_by_name}</span>
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

export default ProjectDocsTab;
