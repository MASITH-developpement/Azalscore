/**
 * AZALSCORE Module - E-commerce - Product Documents Tab
 * Onglet documents et images du produit
 */

import React from 'react';
import { FileText, Image, Upload, Download, ExternalLink } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Product } from '../types';
import { formatFileSize, formatDateTime } from '../types';

/**
 * ProductDocumentsTab - Documents et images
 */
export const ProductDocumentsTab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const handleUpload = () => {
    console.log('Upload document for product:', product.id);
  };

  return (
    <div className="azals-std-tab-content">
      {/* Image principale */}
      <Card title="Image principale" icon={<Image size={18} />}>
        {product.image_url ? (
          <div className="flex items-center gap-4">
            <div className="w-32 h-32 bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
              <img
                src={product.image_url}
                alt={product.name}
                className="max-w-full max-h-full object-contain"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
            <div className="flex-1">
              <p className="text-sm text-muted">Image du produit</p>
              <Button variant="ghost" size="sm" leftIcon={<ExternalLink size={14} />} className="mt-2">
                Voir en taille reelle
              </Button>
            </div>
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Image size={32} className="text-muted" />
            <p className="text-muted">Aucune image principale</p>
            <Button variant="secondary" size="sm" leftIcon={<Upload size={14} />} className="mt-2">
              Ajouter une image
            </Button>
          </div>
        )}
      </Card>

      {/* Galerie d'images */}
      {product.images && product.images.length > 0 && (
        <Card title="Galerie" icon={<Image size={18} />} className="mt-4">
          <div className="grid grid-cols-4 gap-4">
            {product.images.map((url, index) => (
              <div key={index} className="w-full aspect-square bg-gray-100 rounded-lg overflow-hidden">
                <img
                  src={url}
                  alt={`${product.name} - ${index + 1}`}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Documents */}
      <Card
        title="Documents"
        icon={<FileText size={18} />}
        className="mt-4"
        actions={
          <Button variant="secondary" size="sm" leftIcon={<Upload size={14} />} onClick={handleUpload}>
            Ajouter
          </Button>
        }
      >
        {product.documents && product.documents.length > 0 ? (
          <div className="space-y-2">
            {product.documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
              >
                <FileText size={20} className="text-blue-500" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{doc.name}</div>
                  <div className="text-sm text-muted">
                    {doc.type} - {formatFileSize(doc.size)} - {formatDateTime(doc.uploaded_at)}
                  </div>
                </div>
                <Button variant="ghost" size="sm" leftIcon={<Download size={14} />}>
                  Telecharger
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <FileText size={32} className="text-muted" />
            <p className="text-muted">Aucun document</p>
          </div>
        )}
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
            Formats acceptes: PDF, JPG, PNG (max 10 Mo)
          </p>
        </div>
      </Card>

      {/* Tracabilite */}
      <Card title="Tracabilite" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Cree par</label>
            <div className="azals-field__value">{product.created_by_name || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Cree le</label>
            <div className="azals-field__value">{formatDateTime(product.created_at)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Modifie le</label>
            <div className="azals-field__value">{formatDateTime(product.updated_at)}</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default ProductDocumentsTab;
