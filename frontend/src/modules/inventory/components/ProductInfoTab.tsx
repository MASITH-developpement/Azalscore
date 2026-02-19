/**
 * AZALSCORE Module - STOCK - Product Info Tab
 * Onglet informations générales de l'article
 */

import React from 'react';
import {
  Package, Tag, Hash, Building2, Scale, Barcode,
  Truck, Calendar, User
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatCurrency } from '@/utils/formatters';
import { formatQuantity } from '../types';
import type { Product } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * ProductInfoTab - Informations générales de l'article
 */
export const ProductInfoTab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Identification */}
        <Card title="Identification" icon={<Package size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Hash size={14} />
                Code article
              </span>
              <div className="azals-std-field__value font-mono">{product.code}</div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Package size={14} />
                Désignation
              </span>
              <div className="azals-std-field__value">{product.name}</div>
            </div>
            <div className="azals-std-field azals-std-field--full">
              <span className="azals-std-field__label">Description</span>
              <div className="azals-std-field__value">{product.description || '-'}</div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Tag size={14} />
                Catégorie
              </span>
              <div className="azals-std-field__value">{product.category_name || '-'}</div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Barcode size={14} />
                Code-barres
              </span>
              <div className="azals-std-field__value font-mono">{product.barcode || '-'}</div>
            </div>
          </div>
        </Card>

        {/* Caractéristiques */}
        <Card title="Caractéristiques" icon={<Scale size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <span className="azals-std-field__label">Unité de mesure</span>
              <div className="azals-std-field__value">{product.unit}</div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span className="azals-std-field__label">Poids</span>
              <div className="azals-std-field__value">
                {product.weight ? `${product.weight} kg` : '-'}
              </div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span className="azals-std-field__label">Volume</span>
              <div className="azals-std-field__value">
                {product.volume ? `${product.volume} m³` : '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Suivi par lot</span>
              <div className="azals-std-field__value">
                <span className={`azals-badge azals-badge--${product.is_lot_tracked ? 'green' : 'gray'}`}>
                  {product.is_lot_tracked ? 'Oui' : 'Non'}
                </span>
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Suivi par N° série</span>
              <div className="azals-std-field__value">
                <span className={`azals-badge azals-badge--${product.is_serialized ? 'green' : 'gray'}`}>
                  {product.is_serialized ? 'Oui' : 'Non'}
                </span>
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Statut</span>
              <div className="azals-std-field__value">
                <span className={`azals-badge azals-badge--${product.is_active ? 'green' : 'gray'}`}>
                  {product.is_active ? 'Actif' : 'Inactif'}
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Fournisseur */}
        <Card title="Approvisionnement" icon={<Truck size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Building2 size={14} />
                Fournisseur principal
              </span>
              <div className="azals-std-field__value">{product.supplier_name || '-'}</div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span className="azals-std-field__label">Délai de livraison</span>
              <div className="azals-std-field__value">
                {product.lead_time_days ? `${product.lead_time_days} jours` : '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Prix d'achat</span>
              <div className="azals-std-field__value font-medium">
                {formatCurrency(product.cost_price)}
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Prix de vente</span>
              <div className="azals-std-field__value font-medium">
                {formatCurrency(product.sale_price)}
              </div>
            </div>
          </div>
        </Card>

        {/* Seuils de stock */}
        <Card title="Seuils de stock" icon={<Package size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <span className="azals-std-field__label">Stock minimum</span>
              <div className="azals-std-field__value text-warning font-medium">
                {formatQuantity(product.min_stock, product.unit)}
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Stock maximum</span>
              <div className="azals-std-field__value">
                {product.max_stock > 0 ? formatQuantity(product.max_stock, product.unit) : '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Stock actuel</span>
              <div className={`azals-std-field__value font-semibold ${
                product.current_stock <= 0 ? 'text-danger' :
                product.current_stock <= product.min_stock ? 'text-warning' : 'text-success'
              }`}>
                {formatQuantity(product.current_stock, product.unit)}
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Stock disponible</span>
              <div className="azals-std-field__value font-medium">
                {formatQuantity(product.available_stock ?? product.current_stock, product.unit)}
              </div>
            </div>
          </div>
        </Card>
      </Grid>

      {/* Métadonnées (ERP only) */}
      <Card
        title="Métadonnées"
        icon={<Calendar size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={4} gap="md">
          <div className="azals-std-field">
            <span className="azals-std-field__label">
              <Calendar size={14} />
              Date de création
            </span>
            <div className="azals-std-field__value text-sm">{formatDate(product.created_at)}</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">
              <User size={14} />
              Créé par
            </span>
            <div className="azals-std-field__value text-sm">{product.created_by || '-'}</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">Dernière modification</span>
            <div className="azals-std-field__value text-sm">{formatDate(product.updated_at)}</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">ID interne</span>
            <div className="azals-std-field__value text-sm font-mono">{product.id}</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default ProductInfoTab;
