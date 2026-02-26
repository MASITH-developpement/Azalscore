/**
 * AZALSCORE Module - Compliance - Audit Documents Tab
 * Onglet documents de l'audit
 */

import React from 'react';
import { FileText, Download, ExternalLink, Upload, Calendar } from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatDateTime } from '@/utils/formatters';
import { formatFileSize } from '../types';
import type { Audit, AuditDocument } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * AuditDocumentsTab - Documents de l'audit
 */
export const AuditDocumentsTab: React.FC<TabContentProps<Audit>> = ({ data: audit }) => {
  const documents = audit.documents || [];

  const handleDownload = (doc: AuditDocument) => {
    if (doc.url) {
      window.open(doc.url, '_blank');
    }
  };

  return (
    <div className="azals-std-tab-content">
      {/* Rapport d'audit */}
      {audit.report_url && (
        <Card title="Rapport d'audit" icon={<FileText size={18} />}>
          <div className="flex items-center gap-4 p-4 bg-green-50 rounded border border-green-200">
            <FileText size={32} className="text-green-500" />
            <div className="flex-1">
              <div className="font-medium">Rapport d&apos;audit - {audit.code}</div>
              <div className="text-sm text-muted">
                {audit.report_date ? `Emis le ${formatDate(audit.report_date)}` : 'Rapport disponible'}
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<Download size={14} />}
                onClick={() => { window.open(audit.report_url, '_blank'); }}
              >
                Telecharger
              </Button>
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<ExternalLink size={14} />}
                onClick={() => { window.open(audit.report_url, '_blank'); }}
              >
                Ouvrir
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Documents attaches */}
      <Card
        title={`Documents (${documents.length})`}
        icon={<FileText size={18} />}
        className={audit.report_url ? 'mt-4' : ''}
      >
        {documents.length > 0 ? (
          <div className="space-y-2">
            {documents.map((doc) => (
              <DocumentRow key={doc.id} document={doc} onDownload={handleDownload} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <FileText size={32} className="text-muted" />
            <p className="text-muted">Aucun document attache</p>
          </div>
        )}
      </Card>

      {/* Actions documents (ERP only) */}
      <Card title="Gestion des documents" className="mt-4 azals-std-field--secondary">
        <Grid cols={3} gap="md">
          <Button variant="secondary" className="justify-start" leftIcon={<Upload size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'addDocument', auditId: audit.id } })); }}>
            Ajouter un document
          </Button>
          <Button variant="secondary" className="justify-start" leftIcon={<FileText size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'generateReport', auditId: audit.id } })); }}>
            Generer rapport
          </Button>
          <Button variant="secondary" className="justify-start" leftIcon={<Download size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'exportAllDocuments', auditId: audit.id } })); }}>
            Exporter tous les documents
          </Button>
        </Grid>
      </Card>

      {/* Tracabilite */}
      <Card title="Tracabilite" icon={<Calendar size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Cree par</span>
            <div className="azals-field__value">{audit.created_by_name || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Cree le</span>
            <div className="azals-field__value">{formatDateTime(audit.created_at)}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Modifie le</span>
            <div className="azals-field__value">{formatDateTime(audit.updated_at)}</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

/**
 * Composant ligne document
 */
const DocumentRow: React.FC<{
  document: AuditDocument;
  onDownload: (doc: AuditDocument) => void;
}> = ({ document, onDownload }) => {
  const getFileIcon = () => {
    const type = document.type.toLowerCase();
    if (type.includes('pdf')) return '📄';
    if (type.includes('excel') || type.includes('xlsx') || type.includes('xls')) return '📊';
    if (type.includes('word') || type.includes('doc')) return '📝';
    if (type.includes('image') || type.includes('png') || type.includes('jpg')) return '🖼️';
    return '📎';
  };

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors">
      <span className="text-2xl">{getFileIcon()}</span>
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{document.name}</div>
        <div className="text-sm text-muted">
          {document.type} - {formatFileSize(document.size)} - {formatDateTime(document.uploaded_at)}
          {document.uploaded_by && ` par ${document.uploaded_by}`}
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        leftIcon={<Download size={14} />}
        onClick={() => onDownload(document)}
      >
        Telecharger
      </Button>
    </div>
  );
};

export default AuditDocumentsTab;
