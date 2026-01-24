/**
 * AZALSCORE Module - Partners - Documents Tab
 * Onglet documents du partenaire
 */

import React from 'react';
import {
  FileText, Upload, Download, Trash2, File, Image, FileSpreadsheet
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Partner, PartnerDocument } from '../types';
import { formatDate } from '../types';

/**
 * PartnerDocumentsTab - Documents
 */
export const PartnerDocumentsTab: React.FC<TabContentProps<Partner>> = ({ data: partner }) => {
  const documents = partner.documents || [];

  const handleUpload = () => {
    console.log('Upload document for partner:', partner.id);
  };

  return (
    <div className="azals-std-tab-content">
      {/* Liste des documents */}
      <Card
        title={`Documents (${documents.length})`}
        icon={<FileText size={18} />}
        actions={
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<Upload size={14} />}
            onClick={handleUpload}
          >
            Ajouter
          </Button>
        }
      >
        {documents.length > 0 ? (
          <div className="space-y-2">
            {documents.map((doc) => (
              <DocumentRow key={doc.id} document={doc} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <FileText size={32} className="text-muted" />
            <p className="text-muted">Aucun document</p>
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<Upload size={14} />}
              onClick={handleUpload}
              className="mt-2"
            >
              Telecharger un document
            </Button>
          </div>
        )}
      </Card>

      {/* Categories de documents */}
      <Card
        title="Categories"
        icon={<File size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={3} gap="md">
          <div className="p-3 bg-gray-50 rounded text-center">
            <FileText size={24} className="text-blue-500 mx-auto mb-2" />
            <div className="font-medium">Contrats</div>
            <div className="text-sm text-muted">0 fichier</div>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <FileSpreadsheet size={24} className="text-green-500 mx-auto mb-2" />
            <div className="font-medium">Factures</div>
            <div className="text-sm text-muted">0 fichier</div>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <Image size={24} className="text-purple-500 mx-auto mb-2" />
            <div className="font-medium">Autres</div>
            <div className="text-sm text-muted">0 fichier</div>
          </div>
        </Grid>
      </Card>

      {/* Zone de depot */}
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

/**
 * Composant ligne de document
 */
interface DocumentRowProps {
  document: PartnerDocument;
}

const DocumentRow: React.FC<DocumentRowProps> = ({ document }) => {
  const getIcon = () => {
    const ext = document.name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return <FileText size={20} className="text-red-500" />;
      case 'doc':
      case 'docx':
        return <FileText size={20} className="text-blue-500" />;
      case 'xls':
      case 'xlsx':
        return <FileSpreadsheet size={20} className="text-green-500" />;
      case 'jpg':
      case 'jpeg':
      case 'png':
        return <Image size={20} className="text-purple-500" />;
      default:
        return <File size={20} className="text-gray-500" />;
    }
  };

  const formatSize = (bytes?: number): string => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} o`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  };

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors">
      <div className="flex items-center gap-3">
        {getIcon()}
        <div>
          <div className="font-medium">{document.name}</div>
          <div className="text-xs text-muted">
            {formatDate(document.uploaded_at)}
            {document.size && <span> • {formatSize(document.size)}</span>}
            {document.uploaded_by && <span> • Par {document.uploaded_by}</span>}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm">
          <Download size={16} />
        </Button>
        <Button variant="ghost" size="sm" className="text-danger">
          <Trash2 size={16} />
        </Button>
      </div>
    </div>
  );
};

export default PartnerDocumentsTab;
