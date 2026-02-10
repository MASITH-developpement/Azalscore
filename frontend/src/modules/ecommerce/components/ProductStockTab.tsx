/**
 * AZALSCORE Module - E-commerce - Product Stock Tab
 * Onglet gestion des stocks du produit
 */

import React from 'react';
import { Package, AlertTriangle, TrendingUp, Warehouse } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Product } from '../types';
import { isLowStock, isOutOfStock, getAvailableStock } from '../types';

/**
 * ProductStockTab - Gestion des stocks
 */
export const ProductStockTab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const lowStock = isLowStock(product);
  const outOfStock = isOutOfStock(product);
  const availableStock = getAvailableStock(product);

  return (
    <div className="azals-std-tab-content">
      {/* Alertes stock */}
      {outOfStock && (
        <div className="azals-alert azals-alert--danger mb-4">
          <AlertTriangle size={20} />
          <div>
            <strong>Rupture de stock</strong>
            <p>Ce produit n'est plus disponible a la vente.</p>
          </div>
        </div>
      )}

      {!outOfStock && lowStock && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertTriangle size={20} />
          <div>
            <strong>Stock faible</strong>
            <p>Le stock est inferieur au seuil minimum ({product.min_stock} unites).</p>
          </div>
        </div>
      )}

      {/* Niveaux de stock */}
      <Card title="Niveaux de stock" icon={<Package size={18} />}>
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Stock actuel</label>
            <div className={`azals-field__value text-2xl font-bold ${
              outOfStock ? 'text-red-600' : lowStock ? 'text-orange-600' : 'text-green-600'
            }`}>
              {product.stock}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Reserve</label>
            <div className="azals-field__value text-2xl font-medium text-blue-600">
              {product.reserved_stock || 0}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Disponible</label>
            <div className={`azals-field__value text-2xl font-bold ${
              availableStock <= 0 ? 'text-red-600' : 'text-green-600'
            }`}>
              {availableStock}
            </div>
          </div>
        </Grid>

        {/* Barre de progression stock */}
        {product.max_stock && product.max_stock > 0 && (
          <div className="mt-4 azals-std-field--secondary">
            <div className="flex justify-between text-sm text-muted mb-1">
              <span>Taux de remplissage</span>
              <span>{Math.round((product.stock / product.max_stock) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${
                  product.stock >= product.max_stock * 0.7 ? 'bg-green-500' :
                  product.stock >= product.max_stock * 0.3 ? 'bg-orange-500' : 'bg-red-500'
                }`}
                style={{ width: `${Math.min((product.stock / product.max_stock) * 100, 100)}%` }}
              />
            </div>
          </div>
        )}
      </Card>

      {/* Seuils */}
      <Card title="Seuils de stock" icon={<AlertTriangle size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Stock minimum (alerte)</label>
            <div className="azals-field__value">
              {product.min_stock !== undefined ? `${product.min_stock} unites` : 'Non defini'}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Stock maximum</label>
            <div className="azals-field__value">
              {product.max_stock !== undefined ? `${product.max_stock} unites` : 'Non defini'}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Fournisseur */}
      {product.supplier_name && (
        <Card title="Approvisionnement" icon={<Warehouse size={18} />} className="mt-4 azals-std-field--secondary">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Fournisseur</label>
              <div className="azals-field__value">{product.supplier_name}</div>
            </div>
          </Grid>
        </Card>
      )}

      {/* Statistiques de vente */}
      {(product.total_sales !== undefined || product.total_revenue !== undefined) && (
        <Card title="Performance" icon={<TrendingUp size={18} />} className="mt-4 azals-std-field--secondary">
          <Grid cols={3} gap="md">
            {product.total_sales !== undefined && (
              <div className="azals-field">
                <label className="azals-field__label">Total vendu</label>
                <div className="azals-field__value text-lg font-medium">
                  {product.total_sales} unites
                </div>
              </div>
            )}
            {product.views_count !== undefined && (
              <div className="azals-field">
                <label className="azals-field__label">Vues</label>
                <div className="azals-field__value text-lg font-medium">
                  {product.views_count}
                </div>
              </div>
            )}
            {product.conversion_rate !== undefined && (
              <div className="azals-field">
                <label className="azals-field__label">Taux conversion</label>
                <div className="azals-field__value text-lg font-medium">
                  {(product.conversion_rate * 100).toFixed(1)}%
                </div>
              </div>
            )}
          </Grid>
        </Card>
      )}
    </div>
  );
};

export default ProductStockTab;
