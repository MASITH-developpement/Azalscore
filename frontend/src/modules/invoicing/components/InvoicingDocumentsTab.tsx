/**
 * AZALSCORE Module - Invoicing - Documents Tab
 * Onglet documents lies et pieces jointes
 */

import React from 'react';
import {
  FileText, Link2, ArrowRight, Upload, Download, File, Image, FileSpreadsheet
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Document, RelatedDocument } from '../types';
import { formatDate, formatCurrency, DOCUMENT_TYPE_CONFIG, DOCUMENT_STATUS_CONFIG } from '../types';

/**
 * InvoicingDocumentsTab - Documents lies
 */
export const InvoicingDocumentsTab: React.FC<TabContentProps<Document>> = ({ data: doc }) => {
  const relatedDocs = doc.related_documents || [];
  const parentDoc = doc.parent_id ? relatedDocs.find(d => d.id === doc.parent_id) : null;
  const childDocs = doc.children || [];

  const handleUpload = () => {
    console.log('Upload attachment for document:', doc.id);
  };

  return (
    <div className="azals-std-tab-content">
      {/* Document parent */}
      {parentDoc && (
        <Card title="Document source" icon={<Link2 size={18} />}>
          <div className="flex items-center gap-4 p-4 bg-blue-50 rounded border border-blue-200">
            <FileText size={24} className="text-blue-500" />
            <div className="flex-1">
              <div className="font-medium">{parentDoc.number}</div>
              <div className="text-sm text-muted">
                {DOCUMENT_TYPE_CONFIG[parentDoc.type]?.label} du {formatDate(parentDoc.date)}
              </div>
            </div>
            <div className="text-right">
              <div className="font-medium">{formatCurrency(parentDoc.total)}</div>
              <span className={`azals-badge azals-badge--${DOCUMENT_STATUS_CONFIG[parentDoc.status]?.color}`}>
                {DOCUMENT_STATUS_CONFIG[parentDoc.status]?.label}
              </span>
            </div>
            <Button variant="ghost" size="sm">
              Voir
            </Button>
          </div>
          <div className="mt-2 text-sm text-muted">
            Ce document a ete cree a partir de {DOCUMENT_TYPE_CONFIG[parentDoc.type]?.label.toLowerCase()} {parentDoc.number}
          </div>
        </Card>
      )}

      {/* Documents enfants */}
      {childDocs.length > 0 && (
        <Card title="Documents generes" icon={<ArrowRight size={18} />} className={parentDoc ? 'mt-4' : ''}>
          <div className="space-y-2">
            {childDocs.map((child) => (
              <div
                key={child.id}
                className="flex items-center gap-4 p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
              >
                <FileText size={20} className={`text-${DOCUMENT_TYPE_CONFIG[child.type]?.color}`} />
                <div className="flex-1">
                  <div className="font-medium">{child.number}</div>
                  <div className="text-sm text-muted">
                    {DOCUMENT_TYPE_CONFIG[child.type]?.label} du {formatDate(child.date)}
                  </div>
                </div>
                <div className="text-right font-medium">
                  {formatCurrency(child.total)}
                </div>
                <Button variant="ghost" size="sm">
                  Voir
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Chaine documentaire */}
      {(parentDoc || childDocs.length > 0) && (
        <Card title="Chaine documentaire" icon={<Link2 size={18} />} className="mt-4 azals-std-field--secondary">
          <div className="azals-document-chain">
            {parentDoc && (
              <>
                <div className="azals-document-chain__item azals-document-chain__item--parent">
                  <span className={`azals-badge azals-badge--${DOCUMENT_TYPE_CONFIG[parentDoc.type]?.color}`}>
                    {DOCUMENT_TYPE_CONFIG[parentDoc.type]?.label}
                  </span>
                  <span className="text-sm">{parentDoc.number}</span>
                </div>
                <ArrowRight size={16} className="text-muted" />
              </>
            )}
            <div className="azals-document-chain__item azals-document-chain__item--current">
              <span className={`azals-badge azals-badge--${DOCUMENT_TYPE_CONFIG[doc.type]?.color}`}>
                {DOCUMENT_TYPE_CONFIG[doc.type]?.label}
              </span>
              <span className="text-sm font-medium">{doc.number}</span>
              <span className="text-xs text-muted">(actuel)</span>
            </div>
            {childDocs.map((child) => (
              <React.Fragment key={child.id}>
                <ArrowRight size={16} className="text-muted" />
                <div className="azals-document-chain__item azals-document-chain__item--child">
                  <span className={`azals-badge azals-badge--${DOCUMENT_TYPE_CONFIG[child.type]?.color}`}>
                    {DOCUMENT_TYPE_CONFIG[child.type]?.label}
                  </span>
                  <span className="text-sm">{child.number}</span>
                </div>
              </React.Fragment>
            ))}
          </div>
        </Card>
      )}

      {/* Pieces jointes */}
      <Card
        title="Pieces jointes"
        icon={<File size={18} />}
        className="mt-4"
        actions={
          <Button variant="secondary" size="sm" leftIcon={<Upload size={14} />} onClick={handleUpload}>
            Ajouter
          </Button>
        }
      >
        <div className="azals-empty azals-empty--sm">
          <File size={32} className="text-muted" />
          <p className="text-muted">Aucune piece jointe</p>
          <Button variant="ghost" size="sm" leftIcon={<Upload size={14} />} onClick={handleUpload} className="mt-2">
            Ajouter un fichier
          </Button>
        </div>
      </Card>

      {/* Zone de depot (ERP only) */}
      <Card className="mt-4 azals-std-field--secondary">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <Upload size={48} className="text-muted mx-auto mb-4" />
          <p className="text-muted mb-2">Glissez-deposez vos fichiers ici</p>
          <p className="text-sm text-muted mb-4">ou</p>
          <Button variant="secondary" onClick={handleUpload}>
            Parcourir
          </Button>
          <p className="text-xs text-muted mt-4">
            Formats acceptes: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG (max 10 Mo)
          </p>
        </div>
      </Card>
    </div>
  );
};

export default InvoicingDocumentsTab;
