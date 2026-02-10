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
import type { TabContentProps } from '@ui/standards';
import type { Product } from '../types';
import { formatQuantity } from '../types';
import { formatDate, formatCurrency } from '@/utils/formatters';

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
              <label className="azals-std-field__label">
                <Hash size={14} />
                Code article
              </label>
              <div className="azals-std-field__value font-mono">{product.code}</div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">
                <Package size={14} />
                Désignation
              </label>
              <div className="azals-std-field__value">{product.name}</div>
            </div>
            <div className="azals-std-field azals-std-field--full">
              <label className="azals-std-field__label">Description</label>
              <div className="azals-std-field__value">{product.description || '-'}</div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">
                <Tag size={14} />
                Catégorie
              </label>
              <div className="azals-std-field__value">{product.category_name || '-'}</div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">
                <Barcode size={14} />
                Code-barres
              </label>
              <div className="azals-std-field__value font-mono">{product.barcode || '-'}</div>
            </div>
          </div>
        </Card>

        {/* Caractéristiques */}
        <Card title="Caractéristiques" icon={<Scale size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <label className="azals-std-field__label">Unité de mesure</label>
              <div className="azals-std-field__value">{product.unit}</div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <label className="azals-std-field__label">Poids</label>
              <div className="azals-std-field__value">
                {product.weight ? `${product.weight} kg` : '-'}
              </div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <label className="azals-std-field__label">Volume</label>
              <div className="azals-std-field__value">
                {product.volume ? `${product.volume} m³` : '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Suivi par lot</label>
              <div className="azals-std-field__value">
                <span className={`azals-badge azals-badge--${product.is_lot_tracked ? 'green' : 'gray'}`}>
                  {product.is_lot_tracked ? 'Oui' : 'Non'}
                </span>
              </div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Suivi par N° série</label>
              <div className="azals-std-field__value">
                <span className={`azals-badge azals-badge--${product.is_serialized ? 'green' : 'gray'}`}>
                  {product.is_serialized ? 'Oui' : 'Non'}
                </span>
              </div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Statut</label>
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
              <label className="azals-std-field__label">
                <Building2 size={14} />
                Fournisseur principal
              </label>
              <div className="azals-std-field__value">{product.supplier_name || '-'}</div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <label className="azals-std-field__label">Délai de livraison</label>
              <div className="azals-std-field__value">
                {product.lead_time_days ? `${product.lead_time_days} jours` : '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Prix d'achat</label>
              <div className="azals-std-field__value font-medium">
                {formatCurrency(product.cost_price)}
              </div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Prix de vente</label>
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
              <label className="azals-std-field__label">Stock minimum</label>
              <div className="azals-std-field__value text-warning font-medium">
                {formatQuantity(product.min_stock, product.unit)}
              </div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Stock maximum</label>
              <div className="azals-std-field__value">
                {product.max_stock > 0 ? formatQuantity(product.max_stock, product.unit) : '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Stock actuel</label>
              <div className={`azals-std-field__value font-semibold ${
                product.current_stock <= 0 ? 'text-danger' :
                product.current_stock <= product.min_stock ? 'text-warning' : 'text-success'
              }`}>
                {formatQuantity(product.current_stock, product.unit)}
              </div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Stock disponible</label>
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
            <label className="azals-std-field__label">
              <Calendar size={14} />
              Date de création
            </label>
            <div className="azals-std-field__value text-sm">{formatDate(product.created_at)}</div>
          </div>
          <div className="azals-std-field">
            <label className="azals-std-field__label">
              <User size={14} />
              Créé par
            </label>
            <div className="azals-std-field__value text-sm">{product.created_by || '-'}</div>
          </div>
          <div className="azals-std-field">
            <label className="azals-std-field__label">Dernière modification</label>
            <div className="azals-std-field__value text-sm">{formatDate(product.updated_at)}</div>
          </div>
          <div className="azals-std-field">
            <label className="azals-std-field__label">ID interne</label>
            <div className="azals-std-field__value text-sm font-mono">{product.id}</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default ProductInfoTab;
