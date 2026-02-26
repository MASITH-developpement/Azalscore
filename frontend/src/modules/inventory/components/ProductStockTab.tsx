/**
 * AZALSCORE Module - STOCK - Product Stock Tab
 * Onglet stock par emplacement, lots et numéros de série
 */

import React from 'react';
import {
  MapPin, Package, Layers, Hash, Calendar,
  AlertTriangle, CheckCircle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import {
  formatQuantity, isLotExpired, isLotExpiringSoon,
  getDaysUntilExpiry, LOT_STATUS_CONFIG, SERIAL_STATUS_CONFIG
} from '../types';
import type { Product, Lot, Serial } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * ProductStockTab - Stock par emplacement et traçabilité
 */
export const ProductStockTab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const stockByLocation = product.stock_by_location || [];
  const lots = product.lots || [];
  const serials = product.serials || [];

  return (
    <div className="azals-std-tab-content">
      {/* Résumé stock */}
      <Card title="Résumé du stock" icon={<Package size={18} />} className="mb-4">
        <Grid cols={4} gap="md">
          <div className="azals-stat-mini">
            <span className="azals-stat-mini__label">Stock total</span>
            <span className={`azals-stat-mini__value ${
              product.current_stock <= 0 ? 'text-danger' :
              product.current_stock <= product.min_stock ? 'text-warning' : ''
            }`}>
              {formatQuantity(product.current_stock, product.unit)}
            </span>
          </div>
          <div className="azals-stat-mini">
            <span className="azals-stat-mini__label">Réservé</span>
            <span className="azals-stat-mini__value text-blue">
              {formatQuantity(product.reserved_stock || 0, product.unit)}
            </span>
          </div>
          <div className="azals-stat-mini">
            <span className="azals-stat-mini__label">Disponible</span>
            <span className="azals-stat-mini__value text-success">
              {formatQuantity(product.available_stock ?? product.current_stock, product.unit)}
            </span>
          </div>
          <div className="azals-stat-mini">
            <span className="azals-stat-mini__label">Emplacements</span>
            <span className="azals-stat-mini__value">{stockByLocation.length}</span>
          </div>
        </Grid>
      </Card>

      {/* Stock par emplacement */}
      <Card title="Stock par emplacement" icon={<MapPin size={18} />} className="mb-4">
        {stockByLocation.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Entrepôt</th>
                <th>Emplacement</th>
                <th className="text-right">Quantité</th>
                <th className="text-right">Réservé</th>
                <th className="text-right">Disponible</th>
              </tr>
            </thead>
            <tbody>
              {stockByLocation.map((item) => (
                <tr key={item.id}>
                  <td>{item.warehouse_name}</td>
                  <td className="font-mono">{item.location_name}</td>
                  <td className="text-right">{formatQuantity(item.quantity, product.unit)}</td>
                  <td className="text-right text-blue">{formatQuantity(item.reserved_quantity, product.unit)}</td>
                  <td className="text-right text-success font-medium">
                    {formatQuantity(item.available_quantity, product.unit)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="font-semibold">
                <td colSpan={2}>Total</td>
                <td className="text-right">{formatQuantity(product.current_stock, product.unit)}</td>
                <td className="text-right text-blue">{formatQuantity(product.reserved_stock || 0, product.unit)}</td>
                <td className="text-right text-success">
                  {formatQuantity(product.available_stock ?? product.current_stock, product.unit)}
                </td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <MapPin size={32} className="text-muted" />
            <p className="text-muted">Aucun stock enregistré</p>
          </div>
        )}
      </Card>

      <Grid cols={2} gap="lg">
        {/* Lots */}
        {product.is_lot_tracked && (
          <Card title="Lots" icon={<Layers size={18} />}>
            {lots.length > 0 ? (
              <div className="azals-lots-list">
                {lots.map((lot) => (
                  <LotItem key={lot.id} lot={lot} unit={product.unit} />
                ))}
              </div>
            ) : (
              <div className="azals-empty azals-empty--sm">
                <Layers size={32} className="text-muted" />
                <p className="text-muted">Aucun lot</p>
              </div>
            )}
          </Card>
        )}

        {/* Numéros de série */}
        {product.is_serialized && (
          <Card title="Numéros de série" icon={<Hash size={18} />}>
            {serials.length > 0 ? (
              <div className="azals-serials-list">
                {serials.map((serial) => (
                  <SerialItem key={serial.id} serial={serial} />
                ))}
              </div>
            ) : (
              <div className="azals-empty azals-empty--sm">
                <Hash size={32} className="text-muted" />
                <p className="text-muted">Aucun numéro de série</p>
              </div>
            )}
          </Card>
        )}
      </Grid>
    </div>
  );
};

/**
 * Composant item de lot
 */
interface LotItemProps {
  lot: Lot;
  unit: string;
}

const LotItem: React.FC<LotItemProps> = ({ lot, unit }) => {
  const expired = isLotExpired(lot);
  const expiringSoon = isLotExpiringSoon(lot);
  const daysUntil = getDaysUntilExpiry(lot);
  const statusConfig = LOT_STATUS_CONFIG[lot.status];

  return (
    <div className={`azals-lot-item ${expired ? 'azals-lot-item--expired' : expiringSoon ? 'azals-lot-item--warning' : ''}`}>
      <div className="azals-lot-item__header">
        <span className="azals-lot-item__number font-mono font-medium">{lot.number}</span>
        <span className={`azals-badge azals-badge--${statusConfig.color}`}>
          {statusConfig.label}
        </span>
      </div>
      <div className="azals-lot-item__details">
        <span className="azals-lot-item__qty">
          <Package size={12} />
          {formatQuantity(lot.quantity, unit)}
          {lot.reserved_quantity ? ` (${lot.reserved_quantity} rés.)` : ''}
        </span>
        <span className="azals-lot-item__location text-muted">
          <MapPin size={12} />
          {lot.warehouse_name} {lot.location_name ? `/ ${lot.location_name}` : ''}
        </span>
      </div>
      {lot.expiry_date && (
        <div className={`azals-lot-item__expiry ${expired ? 'text-danger' : expiringSoon ? 'text-warning' : 'text-muted'}`}>
          {expired ? (
            <>
              <AlertTriangle size={12} />
              Expiré le {formatDate(lot.expiry_date)}
            </>
          ) : expiringSoon ? (
            <>
              <AlertTriangle size={12} />
              Expire dans {daysUntil} jour(s)
            </>
          ) : (
            <>
              <Calendar size={12} />
              Expire le {formatDate(lot.expiry_date)}
            </>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Composant item de numéro de série
 */
interface SerialItemProps {
  serial: Serial;
}

const SerialItem: React.FC<SerialItemProps> = ({ serial }) => {
  const statusConfig = SERIAL_STATUS_CONFIG[serial.status];

  return (
    <div className="azals-serial-item">
      <div className="azals-serial-item__header">
        <span className="azals-serial-item__number font-mono">{serial.number}</span>
        <span className={`azals-badge azals-badge--${statusConfig.color}`}>
          {statusConfig.label}
        </span>
      </div>
      <div className="azals-serial-item__details text-sm text-muted">
        {serial.lot_number && (
          <span>
            <Layers size={12} />
            Lot: {serial.lot_number}
          </span>
        )}
        <span>
          <MapPin size={12} />
          {serial.warehouse_name} {serial.location_name ? `/ ${serial.location_name}` : ''}
        </span>
        {serial.warranty_end_date && (
          <span>
            <CheckCircle size={12} />
            Garantie: {formatDate(serial.warranty_end_date)}
          </span>
        )}
      </div>
    </div>
  );
};

export default ProductStockTab;
