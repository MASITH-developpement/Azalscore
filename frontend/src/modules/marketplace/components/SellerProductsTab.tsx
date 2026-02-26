/**
 * AZALSCORE Module - Marketplace - Seller Products Tab
 * Onglet produits du vendeur
 */

import React from 'react';
import { Package, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { Card } from '@ui/layout';
import { formatCurrency, formatDate } from '@/utils/formatters';
import {
  PRODUCT_STATUS_CONFIG,
  isProductLowStock, isProductOutOfStock
} from '../types';
import type { Seller, MarketplaceProduct } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * SellerProductsTab - Produits du vendeur
 */
export const SellerProductsTab: React.FC<TabContentProps<Seller>> = ({ data: seller }) => {
  const products = seller.products || [];

  const activeProducts = products.filter(p => p.status === 'ACTIVE').length;
  const pendingProducts = products.filter(p => p.status === 'PENDING').length;
  const lowStockProducts = products.filter(isProductLowStock).length;
  const outOfStockProducts = products.filter(isProductOutOfStock).length;

  return (
    <div className="azals-std-tab-content">
      {/* Resume */}
      <Card title="Resume du catalogue" icon={<Package size={18} />}>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-2xl font-bold text-primary">{products.length}</div>
            <div className="text-sm text-muted">Total produits</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">{activeProducts}</div>
            <div className="text-sm text-muted">Actifs</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded">
            <div className="text-2xl font-bold text-orange-600">{pendingProducts}</div>
            <div className="text-sm text-muted">En attente</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded">
            <div className="text-2xl font-bold text-red-600">{outOfStockProducts}</div>
            <div className="text-sm text-muted">Rupture</div>
          </div>
        </div>
      </Card>

      {/* Alertes stock */}
      {(lowStockProducts > 0 || outOfStockProducts > 0) && (
        <Card className="mt-4 border-orange-200 bg-orange-50">
          <div className="flex items-center gap-2 text-orange-700">
            <AlertTriangle size={18} />
            <span className="font-medium">
              {outOfStockProducts > 0 && `${outOfStockProducts} produit(s) en rupture`}
              {outOfStockProducts > 0 && lowStockProducts > 0 && ' - '}
              {lowStockProducts > 0 && `${lowStockProducts} produit(s) stock faible`}
            </span>
          </div>
        </Card>
      )}

      {/* Liste des produits */}
      <Card title={`Produits (${products.length})`} icon={<Package size={18} />} className="mt-4">
        {products.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Produit</th>
                <th>Categorie</th>
                <th className="text-right">Prix</th>
                <th className="text-center">Stock</th>
                <th className="text-center">Statut</th>
                <th>Cree le</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <ProductRow key={product.id} product={product} />
              ))}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Package size={32} className="text-muted" />
            <p className="text-muted">Aucun produit enregistre</p>
          </div>
        )}
      </Card>

      {/* Stats detaillees (ERP only) */}
      <Card title="Statistiques produits" icon={<Package size={18} />} className="mt-4 azals-std-field--secondary">
        <div className="grid grid-cols-3 gap-4">
          <div className="azals-field">
            <span className="azals-field__label">Valeur totale stock</span>
            <div className="azals-field__value text-lg font-medium">
              {formatCurrency(
                products.reduce((sum, p) => sum + (p.price * p.stock), 0)
              )}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Prix moyen</span>
            <div className="azals-field__value text-lg font-medium">
              {products.length > 0
                ? formatCurrency(products.reduce((sum, p) => sum + p.price, 0) / products.length)
                : '-'}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Categories</span>
            <div className="azals-field__value text-lg font-medium">
              {new Set(products.map(p => p.category)).size}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant ligne produit
 */
const ProductRow: React.FC<{ product: MarketplaceProduct }> = ({ product }) => {
  const getStockDisplay = () => {
    if (isProductOutOfStock(product)) {
      return (
        <span className="flex items-center justify-center gap-1 text-red-600">
          <XCircle size={14} /> 0
        </span>
      );
    }
    if (isProductLowStock(product)) {
      return (
        <span className="flex items-center justify-center gap-1 text-orange-600">
          <AlertTriangle size={14} /> {product.stock}
        </span>
      );
    }
    return (
      <span className="flex items-center justify-center gap-1 text-green-600">
        <CheckCircle2 size={14} /> {product.stock}
      </span>
    );
  };

  const statusConfig = PRODUCT_STATUS_CONFIG[product.status];

  return (
    <tr>
      <td>
        <code className="font-mono text-sm">{product.sku}</code>
      </td>
      <td className="font-medium">{product.name}</td>
      <td className="text-muted">{product.category}</td>
      <td className="text-right font-medium">
        {formatCurrency(product.price, product.currency)}
      </td>
      <td className="text-center">{getStockDisplay()}</td>
      <td className="text-center">
        <span className={`azals-badge azals-badge--${statusConfig.color}`}>
          {statusConfig.label}
        </span>
      </td>
      <td className="text-muted text-sm">{formatDate(product.created_at)}</td>
    </tr>
  );
};

export default SellerProductsTab;
