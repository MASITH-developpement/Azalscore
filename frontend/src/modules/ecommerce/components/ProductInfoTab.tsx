/**
 * AZALSCORE Module - E-commerce - Product Info Tab
 * Onglet informations du produit
 */

import React from 'react';
import { Package, Tag, Barcode, Scale, Box } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatCurrency } from '@/utils/formatters';
import { PRODUCT_STATUS_CONFIG, formatWeight, calculateMargin } from '../types';
import type { Product } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * ProductInfoTab - Informations generales
 */
export const ProductInfoTab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const statusConfig = PRODUCT_STATUS_CONFIG[product.status];
  const margin = calculateMargin(product.price, product.cost);

  return (
    <div className="azals-std-tab-content">
      {/* Informations principales */}
      <Card title="Identification" icon={<Package size={18} />}>
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">SKU</span>
            <div className="azals-field__value font-mono">{product.sku}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Nom</span>
            <div className="azals-field__value">{product.name}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Categorie</span>
            <div className="azals-field__value">{product.category_name || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Statut</span>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
          </div>
        </Grid>

        {product.description && (
          <div className="azals-field mt-4">
            <span className="azals-field__label">Description</span>
            <div className="azals-field__value text-sm">{product.description}</div>
          </div>
        )}

        {product.barcode && (
          <div className="azals-field mt-4 azals-std-field--secondary">
            <span className="azals-field__label">
              <Barcode size={14} className="inline mr-1" />
              Code-barres
            </span>
            <div className="azals-field__value font-mono">{product.barcode}</div>
          </div>
        )}
      </Card>

      {/* Tarification */}
      <Card title="Tarification" icon={<Tag size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Prix de vente</span>
            <div className="azals-field__value text-lg font-semibold text-green-600">
              {formatCurrency(product.price, product.currency)}
            </div>
          </div>
          {product.compare_price && product.compare_price > product.price && (
            <div className="azals-field">
              <span className="azals-field__label">Prix barre</span>
              <div className="azals-field__value text-lg text-muted line-through">
                {formatCurrency(product.compare_price, product.currency)}
              </div>
            </div>
          )}
          <div className="azals-field azals-std-field--secondary">
            <span className="azals-field__label">Prix d&apos;achat</span>
            <div className="azals-field__value">
              {product.cost ? formatCurrency(product.cost, product.currency) : '-'}
            </div>
          </div>
        </Grid>

        {/* Marge (ERP only) */}
        {product.cost && (
          <div className="mt-4 p-4 bg-gray-50 rounded azals-std-field--secondary">
            <Grid cols={2} gap="md">
              <div className="azals-field">
                <span className="azals-field__label">Marge brute</span>
                <div className="azals-field__value font-semibold">
                  {formatCurrency(product.price - product.cost, product.currency)}
                </div>
              </div>
              <div className="azals-field">
                <span className="azals-field__label">Taux de marge</span>
                <div className={`azals-field__value font-semibold ${margin >= 30 ? 'text-green-600' : margin >= 15 ? 'text-orange-600' : 'text-red-600'}`}>
                  {margin.toFixed(1)}%
                </div>
              </div>
            </Grid>
          </div>
        )}

        {/* TVA */}
        <Grid cols={2} gap="md" className="mt-4 azals-std-field--secondary">
          <div className="azals-field">
            <span className="azals-field__label">Soumis a TVA</span>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${product.is_taxable ? 'green' : 'gray'}`}>
                {product.is_taxable ? 'Oui' : 'Non'}
              </span>
            </div>
          </div>
          {product.is_taxable && product.tax_rate !== undefined && (
            <div className="azals-field">
              <span className="azals-field__label">Taux TVA</span>
              <div className="azals-field__value">{product.tax_rate}%</div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Caracteristiques physiques */}
      <Card title="Caracteristiques" icon={<Box size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">
              <Scale size={14} className="inline mr-1" />
              Poids
            </span>
            <div className="azals-field__value">{formatWeight(product.weight)}</div>
          </div>
          {product.dimensions && (
            <div className="azals-field">
              <span className="azals-field__label">Dimensions (L x l x h)</span>
              <div className="azals-field__value">
                {product.dimensions.length} x {product.dimensions.width} x {product.dimensions.height} cm
              </div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Attributs personnalises */}
      {product.attributes && Object.keys(product.attributes).length > 0 && (
        <Card title="Attributs" className="mt-4 azals-std-field--secondary">
          <Grid cols={2} gap="md">
            {Object.entries(product.attributes).map(([key, value]) => (
              <div key={key} className="azals-field">
                <span className="azals-field__label">{key}</span>
                <div className="azals-field__value">{value}</div>
              </div>
            ))}
          </Grid>
        </Card>
      )}

      {/* Tags */}
      {product.tags && product.tags.length > 0 && (
        <Card title="Tags" className="mt-4">
          <div className="flex flex-wrap gap-2">
            {product.tags.map((tag) => (
              <span key={tag} className="azals-badge azals-badge--blue">{tag}</span>
            ))}
          </div>
        </Card>
      )}

      {/* SEO (ERP only) */}
      {(product.seo_title || product.seo_description) && (
        <Card title="Referencement SEO" className="mt-4 azals-std-field--secondary">
          <Grid cols={1} gap="md">
            {product.seo_title && (
              <div className="azals-field">
                <span className="azals-field__label">Titre SEO</span>
                <div className="azals-field__value">{product.seo_title}</div>
              </div>
            )}
            {product.seo_description && (
              <div className="azals-field">
                <span className="azals-field__label">Meta description</span>
                <div className="azals-field__value text-sm">{product.seo_description}</div>
              </div>
            )}
          </Grid>
        </Card>
      )}
    </div>
  );
};

export default ProductInfoTab;
