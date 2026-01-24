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
import type { TabContentProps } from '@ui/standards';
import type { Product, ProductDocument } from '../types';
import { formatDate } from '../types';

/**
 * ProductDocsTab - Documents de l'article
 */
export const ProductDocsTab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const documents = product.documents || [];

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Printer size={16} />}>
          Imprimer fiche article
        </Button>
        <Button variant="secondary" leftIcon={<QrCode size={16} />}>
          Générer étiquette
        </Button>
        <Button variant="ghost" leftIcon={<Upload size={16} />}>
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
              <Button variant="secondary" size="sm" leftIcon={<Eye size={14} />}>
                Aperçu
              </Button>
              <Button variant="ghost" size="sm" leftIcon={<Download size={14} />}>
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
                <Button variant="secondary" size="sm" leftIcon={<Printer size={14} />}>
                  Imprimer
                </Button>
                <Button variant="ghost" size="sm" leftIcon={<Download size={14} />}>
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
            <Button size="sm" variant="ghost" leftIcon={<Upload size={14} />}>
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
          <button className="azals-linked-doc azals-linked-doc--info">
            <FileText size={16} />
            <span>Fiche technique produit</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--info">
            <FileText size={16} />
            <span>Fiche de données de sécurité (FDS)</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--info">
            <FileText size={16} />
            <span>Notice d'utilisation</span>
          </button>
          <button className="azals-linked-doc azals-linked-doc--info">
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
        <button className="azals-btn-icon" title="Aperçu">
          <Eye size={16} />
        </button>
        <button className="azals-btn-icon" title="Télécharger">
          <Download size={16} />
        </button>
        <button className="azals-btn-icon azals-btn-icon--danger" title="Supprimer">
          <Trash2 size={16} />
        </button>
      </div>
    </li>
  );
};

export default ProductDocsTab;
