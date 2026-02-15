/**
 * AZALSCORE Module - HR - Employee Documents Tab
 * Onglet documents de l'employe
 */

import React from 'react';
import {
  FileText, Download, Eye, Upload, Trash2,
  File, FileImage, Award, CreditCard, GraduationCap,
  Printer, User, AlertTriangle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Employee, EmployeeDocument } from '../types';
import { getFullName } from '../types';
import { formatDate } from '@/utils/formatters';

/**
 * EmployeeDocsTab - Documents de l'employe
 */
export const EmployeeDocsTab: React.FC<TabContentProps<Employee>> = ({ data: employee }) => {
  const documents = employee.documents || [];

  // Handler functions
  const handlePrint = (): void => {
    window.print();
  };

  const handleExportDossier = (): void => {
    window.dispatchEvent(new CustomEvent('azals:employee:export-dossier', {
      detail: { employeeId: employee.id }
    }));
  };

  const handleUpload = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:upload', {
      detail: { type: 'employee', id: employee.id }
    }));
  };

  const handlePreview = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:preview', {
      detail: { type: 'employee', id: employee.id }
    }));
  };

  const handleDownloadPdf = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:download', {
      detail: { type: 'employee', id: employee.id, format: 'pdf' }
    }));
  };

  // Grouper par type
  const contracts = documents.filter(d => d.type === 'contract');
  const ids = documents.filter(d => d.type === 'id');
  const diplomas = documents.filter(d => d.type === 'diploma');
  const certificates = documents.filter(d => d.type === 'certificate');
  const others = documents.filter(d => d.type === 'other');

  // Documents expir\u00e9s ou expirant bient\u00f4t
  const expiringDocs = documents.filter(d => {
    if (!d.expiry_date) return false;
    const expiry = new Date(d.expiry_date);
    const now = new Date();
    const daysUntilExpiry = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
    return daysUntilExpiry <= 30;
  });

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
        <Button variant="secondary" leftIcon={<Printer size={16} />} onClick={handlePrint}>
          Imprimer fiche employe
        </Button>
        <Button variant="secondary" leftIcon={<Download size={16} />} onClick={handleExportDossier}>
          Exporter dossier
        </Button>
        <Button variant="ghost" leftIcon={<Upload size={16} />} onClick={handleUpload}>
          Ajouter un document
        </Button>
      </div>

      <Grid cols={2} gap="lg">
        {/* Fiche employe */}
        <Card title="Fiche employe" icon={<User size={18} />}>
          <div className="azals-document-preview">
            <div className="azals-document-preview__icon">
              <FileText size={48} className="text-primary" />
            </div>
            <div className="azals-document-preview__info">
              <h4 className="font-medium">Fiche employe {employee.employee_number}</h4>
              <p className="text-sm text-muted">{getFullName(employee)}</p>
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

        {/* Contrats */}
        <Card title="Contrats" icon={<FileText size={18} />}>
          {contracts.length > 0 ? (
            <ul className="azals-document-list">
              {contracts.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <FileText size={32} className="text-muted" />
              <p className="text-muted">Aucun contrat</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={handleUpload}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>

        {/* Pieces d'identite */}
        <Card title="Pieces d'identite" icon={<CreditCard size={18} />}>
          {ids.length > 0 ? (
            <ul className="azals-document-list">
              {ids.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <CreditCard size={32} className="text-muted" />
              <p className="text-muted">Aucune piece d'identite</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={handleUpload}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>

        {/* Diplomes et formations */}
        <Card title="Diplomes et formations" icon={<GraduationCap size={18} />}>
          {diplomas.length > 0 ? (
            <ul className="azals-document-list">
              {diplomas.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <GraduationCap size={32} className="text-muted" />
              <p className="text-muted">Aucun diplome</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={handleUpload}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>
      </Grid>

      {/* Certificats et attestations (ERP only) */}
      {certificates.length > 0 && (
        <Card title="Certificats et attestations" icon={<Award size={18} />} className="mt-4 azals-std-field--secondary">
          <ul className="azals-document-list">
            {certificates.map((doc) => (
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
  document: EmployeeDocument;
}

const DocumentItem: React.FC<DocumentItemProps> = ({ document }) => {
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

  const isExpiringSoon = document.expiry_date && (() => {
    const expiry = new Date(document.expiry_date);
    const now = new Date();
    const daysUntilExpiry = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
    return daysUntilExpiry <= 30;
  })();

  const isExpired = document.expiry_date && new Date(document.expiry_date) < new Date();

  const getIcon = () => {
    switch (document.type) {
      case 'contract':
        return <FileText size={20} className="text-primary" />;
      case 'id':
        return <CreditCard size={20} className="text-blue" />;
      case 'diploma':
        return <GraduationCap size={20} className="text-purple" />;
      case 'certificate':
        return <Award size={20} className="text-green" />;
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
    <li className={`azals-document-list__item ${isExpired ? 'azals-document-list__item--expired' : ''}`}>
      <div className="azals-document-list__icon">{getIcon()}</div>
      <div className="azals-document-list__info">
        <span className="azals-document-list__name">{document.name}</span>
        <span className="azals-document-list__meta text-muted text-sm">
          {formatSize(document.size)} . {formatDate(document.created_at)}
          {document.category && ` . ${document.category}`}
          {document.expiry_date && (
            <span className={isExpired ? 'text-danger' : isExpiringSoon ? 'text-warning' : ''}>
              {' . '}Expire: {formatDate(document.expiry_date)}
              {isExpired && ' (Expire)'}
              {isExpiringSoon && !isExpired && ' (Bientot)'}
            </span>
          )}
        </span>
      </div>
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

export default EmployeeDocsTab;
