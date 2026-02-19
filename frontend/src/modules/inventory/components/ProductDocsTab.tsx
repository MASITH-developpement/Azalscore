/**
 * AZALSCORE Module - STOCK - Product Documents Tab
 * Onglet documents de l'article
 */

import React from 'react';
import {
  FileText, Download, Eye, Upload, Trash2,
  File, FileImage, Printer, Package, QrCode
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import type { Product, ProductDocument } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * ProductDocsTab - Documents de l'article
 */
export const ProductDocsTab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const documents = product.documents || [];

  // Handler functions
  const handlePrint = (): void => {
    window.print();
  };

  const handleGenerateLabel = (): void => {
    window.dispatchEvent(new CustomEvent('azals:product:generate-label', {
      detail: { productId: product.id, barcode: product.barcode }
    }));
  };

  const handleUpload = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:upload', {
      detail: { type: 'product', id: product.id }
    }));
  };

  const handlePreview = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:preview', {
      detail: { type: 'product', id: product.id }
    }));
  };

  const handleDownloadPdf = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:download', {
      detail: { type: 'product', id: product.id, format: 'pdf' }
    }));
  };

  const handlePrintBarcode = (): void => {
    window.dispatchEvent(new CustomEvent('azals:product:print-barcode', {
      detail: { productId: product.id, barcode: product.barcode }
    }));
  };

  const handleDownloadBarcode = (): void => {
    window.dispatchEvent(new CustomEvent('azals:product:download-barcode', {
      detail: { productId: product.id, barcode: product.barcode, format: 'png' }
    }));
  };

  const handleOpenTechnicalDoc = (docType: string): void => {
    window.dispatchEvent(new CustomEvent('azals:product:open-technical-doc', {
      detail: { productId: product.id, docType }
    }));
  };

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Printer size={16} />} onClick={handlePrint}>
          Imprimer fiche article
        </Button>
        <Button variant="secondary" leftIcon={<QrCode size={16} />} onClick={handleGenerateLabel}>
          Générer étiquette
        </Button>
        <Button variant="ghost" leftIcon={<Upload size={16} />} onClick={handleUpload}>
          Ajouter un document
        </Button>
      </div>

      <Grid cols={2} gap="lg">
        {/* Fiche article */}
        <Card title="Fiche article" icon={<Package size={18} />}>
          <div className="azals-document-preview">
            <div className="azals-document-preview__icon">
              <FileText size={48} className="text-primary" />
            </div>
            <div className="azals-document-preview__info">
              <h4 className="font-medium">Fiche article {product.code}</h4>
              <p className="text-sm text-muted">
                {product.name}
              </p>
            </div>
            <div className="azals-document-preview__actions">
              <Button variant="secondary" size="sm" leftIcon={<Eye size={14} />} onClick={handlePreview}>
                Aperçu
              </Button>
              <Button variant="ghost" size="sm" leftIcon={<Download size={14} />} onClick={handleDownloadPdf}>
                PDF
              </Button>
            </div>
          </div>
        </Card>

        {/* Étiquette code-barres */}
        {product.barcode && (
          <Card title="Étiquette" icon={<QrCode size={18} />}>
            <div className="azals-document-preview">
              <div className="azals-document-preview__icon">
                <div className="azals-barcode-preview">
                  <div className="azals-barcode-preview__bars" />
                  <span className="azals-barcode-preview__code font-mono">{product.barcode}</span>
                </div>
              </div>
              <div className="azals-document-preview__info">
                <h4 className="font-medium">Code-barres</h4>
                <p className="text-sm font-mono">{product.barcode}</p>
              </div>
              <div className="azals-document-preview__actions">
                <Button variant="secondary" size="sm" leftIcon={<Printer size={14} />} onClick={handlePrintBarcode}>
                  Imprimer
                </Button>
                <Button variant="ghost" size="sm" leftIcon={<Download size={14} />} onClick={handleDownloadBarcode}>
                  PNG
                </Button>
              </div>
            </div>
          </Card>
        )}
      </Grid>

      {/* Pièces jointes */}
      <Card title="Pièces jointes" icon={<File size={18} />} className="mt-4">
        {documents.length > 0 ? (
          <ul className="azals-document-list">
            {documents.map((doc) => (
              <DocumentItem key={doc.id} document={doc} />
            ))}
          </ul>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <File size={32} className="text-muted" />
            <p className="text-muted">Aucune pièce jointe</p>
            <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={handleUpload}>
              Ajouter un document
            </Button>
          </div>
        )}
      </Card>

      {/* Documents techniques (ERP only) */}
      <Card
        title="Documentation technique"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-linked-docs">
          <button className="azals-linked-doc azals-linked-doc--info" onClick={() => { handleOpenTechnicalDoc('fiche-technique'); }}>
            <FileText size={16} />
            <span>Fiche technique produit</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--info" onClick={() => { handleOpenTechnicalDoc('fds'); }}>
            <FileText size={16} />
            <span>Fiche de données de sécurité (FDS)</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--info" onClick={() => { handleOpenTechnicalDoc('notice'); }}>
            <FileText size={16} />
            <span>Notice d'utilisation</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--info" onClick={() => { handleOpenTechnicalDoc('certificat'); }}>
            <FileText size={16} />
            <span>Certificat de conformité</span>
          </button>
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant item de document
 */
interface DocumentItemProps {
  document: ProductDocument;
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
        <button className="azals-btn-icon azals-btn-icon--danger" title="Supprimer" onClick={handleDelete}>
          <Trash2 size={16} />
        </button>
      </div>
    </li>
  );
};

export default ProductDocsTab;
