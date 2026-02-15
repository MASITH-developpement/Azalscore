/**
 * AZALSCORE Module - Purchases - Supplier Documents Tab
 * Onglet documents du fournisseur
 */

import React from 'react';
import { Paperclip, Upload, File, FileText, Image } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Supplier } from '../types';
import { formatDate } from '@/utils/formatters';

interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  uploaded_at: string;
  uploaded_by?: string;
}

/**
 * SupplierDocumentsTab - Documents du fournisseur
 */
export const SupplierDocumentsTab: React.FC<TabContentProps<Supplier & { documents?: Document[] }>> = ({ data }) => {
  const documents = data.documents || [];

  const handleUpload = () => {
    window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'uploadDocument', supplierId: data.id } }));
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return <Image size={20} className="text-blue-500" />;
    if (type.includes('pdf')) return <FileText size={20} className="text-red-500" />;
    return <File size={20} className="text-gray-500" />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="azals-std-tab-content">
      {/* Documents */}
      <Card
        title="Documents"
        icon={<Paperclip size={18} />}
        actions={
          <Button variant="secondary" size="sm" leftIcon={<Upload size={14} />} onClick={handleUpload}>
            Ajouter
          </Button>
        }
      >
        {documents.length > 0 ? (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-4 p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
              >
                {getFileIcon(doc.type)}
                <div className="flex-1">
                  <div className="font-medium">{doc.name}</div>
                  <div className="text-sm text-muted">
                    {formatFileSize(doc.size)} - {formatDate(doc.uploaded_at)}
                    {doc.uploaded_by && ` par ${doc.uploaded_by}`}
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'downloadDocument', documentId: doc.id } })); }}>
                  Telecharger
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Paperclip size={32} className="text-muted" />
            <p className="text-muted">Aucun document</p>
            <Button variant="secondary" size="sm" leftIcon={<Upload size={14} />} onClick={handleUpload} className="mt-2">
              Ajouter un document
            </Button>
          </div>
        )}
      </Card>

      {/* Zone de depot (ERP only) */}
      <Card className="mt-4 azals-std-field--secondary">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <Upload size={48} className="text-muted mx-auto mb-4" />
          <p className="text-muted mb-2">Glissez-deposez vos documents ici</p>
          <p className="text-sm text-muted mb-4">ou</p>
          <Button variant="secondary" onClick={handleUpload}>
            Parcourir
          </Button>
          <p className="text-xs text-muted mt-4">
            Formats acceptes: PDF, JPG, PNG, DOC, XLS (max 10 Mo)
          </p>
        </div>
      </Card>

      {/* Tracabilite */}
      <Card title="Tracabilite" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Cree par</label>
            <div className="azals-field__value">{data.created_by_name || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Cree le</label>
            <div className="azals-field__value">{formatDate(data.created_at)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Modifie le</label>
            <div className="azals-field__value">{formatDate(data.updated_at)}</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default SupplierDocumentsTab;
