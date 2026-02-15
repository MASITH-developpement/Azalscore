/**
 * AZALSCORE Module - Production - Order Documents Tab
 * Onglet documents de l'ordre de fabrication
 */

import React from 'react';
import {
  FileText, Download, Eye, Upload, Trash2,
  File, FileImage, Printer, ClipboardList, Package
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { ProductionOrder, OrderDocument } from '../types';
import { formatDate } from '@/utils/formatters';

/**
 * OrderDocsTab - Documents de l'ordre de fabrication
 */
export const OrderDocsTab: React.FC<TabContentProps<ProductionOrder>> = ({ data: order }) => {
  const documents = order.documents || [];

  // Handler functions
  const handlePrint = (): void => {
    window.print();
  };

  const handleExportPdf = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:download', {
      detail: { type: 'production-order', id: order.id, format: 'pdf' }
    }));
  };

  const handleUpload = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:upload', {
      detail: { type: 'production-order', id: order.id }
    }));
  };

  const handlePreview = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:preview', {
      detail: { type: 'production-order', id: order.id }
    }));
  };

  const handleDownloadPdf = (): void => {
    window.dispatchEvent(new CustomEvent('azals:document:download', {
      detail: { type: 'production-order', id: order.id, format: 'pdf' }
    }));
  };

  const handleOpenNomenclature = (): void => {
    window.dispatchEvent(new CustomEvent('azals:production:open-nomenclature', {
      detail: { orderId: order.id, productId: order.product_id }
    }));
  };

  const handleOpenTechnicalDoc = (docType: string): void => {
    window.dispatchEvent(new CustomEvent('azals:production:open-technical-doc', {
      detail: { orderId: order.id, docType }
    }));
  };

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Printer size={16} />} onClick={handlePrint}>
          Imprimer bon de travail
        </Button>
        <Button variant="secondary" leftIcon={<Download size={16} />} onClick={handleExportPdf}>
          Exporter PDF
        </Button>
        <Button variant="ghost" leftIcon={<Upload size={16} />} onClick={handleUpload}>
          Ajouter un document
        </Button>
      </div>

      <Grid cols={2} gap="lg">
        {/* Fiche de fabrication */}
        <Card title="Fiche de fabrication" icon={<ClipboardList size={18} />}>
          <div className="azals-document-preview">
            <div className="azals-document-preview__icon">
              <FileText size={48} className="text-primary" />
            </div>
            <div className="azals-document-preview__info">
              <h4 className="font-medium">Ordre de fabrication {order.number}</h4>
              <p className="text-sm text-muted">
                {order.product_name || order.product_code}
              </p>
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

        {/* Pieces jointes */}
        <Card title="Pieces jointes" icon={<File size={18} />}>
          {documents.length > 0 ? (
            <ul className="azals-document-list">
              {documents.map((doc) => (
                <DocumentItem key={doc.id} document={doc} />
              ))}
            </ul>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <File size={32} className="text-muted" />
              <p className="text-muted">Aucune piece jointe</p>
              <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />} onClick={handleUpload}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>
      </Grid>

      {/* Documents lies */}
      <Card title="Documents lies" icon={<FileText size={18} />} className="mt-4">
        <div className="azals-linked-docs">
          <button
            className="azals-linked-doc azals-linked-doc--info"
            onClick={() => {
              window.dispatchEvent(new CustomEvent('azals:navigate', {
                detail: { view: 'stock', params: { productId: order.product_id } }
              }));
            }}
          >
            <Package size={16} />
            <span>Fiche produit</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--info" onClick={handleOpenNomenclature}>
            <ClipboardList size={16} />
            <span>Nomenclature</span>
          </button>
          {order.customer_order_id && (
            <button
              className="azals-linked-doc azals-linked-doc--info"
              onClick={() => {
                window.dispatchEvent(new CustomEvent('azals:navigate', {
                  detail: { view: 'commandes', params: { id: order.customer_order_id } }
                }));
              }}
            >
              <FileText size={16} />
              <span>Commande client</span>
            </button>
          )}
        </div>
      </Card>

      {/* Documents techniques (ERP only) */}
      <Card
        title="Documents techniques"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-linked-docs">
          <button className="azals-linked-doc azals-linked-doc--technical" onClick={() => { handleOpenTechnicalDoc('gamme-operatoire'); }}>
            <FileText size={16} />
            <span>Gamme operatoire</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--technical" onClick={() => { handleOpenTechnicalDoc('instructions'); }}>
            <FileText size={16} />
            <span>Instructions de travail</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--technical" onClick={() => { handleOpenTechnicalDoc('fiches-controle'); }}>
            <FileText size={16} />
            <span>Fiches de controle</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--technical" onClick={() => { handleOpenTechnicalDoc('plans-techniques'); }}>
            <FileText size={16} />
            <span>Plans techniques</span>
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
  document: OrderDocument;
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
      case 'excel':
        return <FileText size={20} className="text-green" />;
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
          {formatSize(document.size)} . {formatDate(document.created_at)}
          {document.category && ` . ${document.category}`}
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

export default OrderDocsTab;
