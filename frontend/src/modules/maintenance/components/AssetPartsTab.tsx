/**
 * AZALSCORE Module - Maintenance - Asset Parts Tab
 * Onglet pieces de rechange de l'equipement
 */

import React from 'react';
import {
  Package, AlertTriangle, TrendingDown, ShoppingCart,
  CheckCircle, XCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Asset, SparePart, MaintenancePlan } from '../types';
import { formatFrequency, FREQUENCY_CONFIG } from '../types';

/**
 * AssetPartsTab - Pieces de rechange et plans de maintenance
 */
export const AssetPartsTab: React.FC<TabContentProps<Asset>> = ({ data: asset }) => {
  const spareParts = asset.spare_parts || [];
  const plans = asset.maintenance_plans || [];

  // Pieces en rupture ou sous le seuil
  const lowStockParts = spareParts.filter(p => p.quantity_on_hand <= p.minimum_quantity);
  const criticalParts = spareParts.filter(p => p.quantity_on_hand === 0);

  return (
    <div className="azals-std-tab-content">
      {/* Alertes stock */}
      {criticalParts.length > 0 && (
        <div className="azals-alert azals-alert--danger mb-4">
          <XCircle size={18} />
          <span>
            {criticalParts.length} piece(s) en rupture de stock!
          </span>
        </div>
      )}
      {lowStockParts.length > 0 && criticalParts.length === 0 && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertTriangle size={18} />
          <span>
            {lowStockParts.length} piece(s) sous le seuil minimum.
          </span>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Pieces de rechange */}
        <Card title="Pieces de rechange" icon={<Package size={18} />}>
          {spareParts.length > 0 ? (
            <div className="azals-parts-list">
              {spareParts.map((part) => (
                <SparePartItem key={part.id} part={part} />
              ))}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Package size={32} className="text-muted" />
              <p className="text-muted">Aucune piece de rechange definie</p>
              <Button size="sm" variant="ghost" leftIcon={<Package size={14} />}>
                Ajouter
              </Button>
            </div>
          )}
        </Card>

        {/* Plans de maintenance */}
        <Card title="Plans de maintenance" icon={<CheckCircle size={18} />}>
          {plans.length > 0 ? (
            <div className="azals-plans-list">
              {plans.map((plan) => (
                <MaintenancePlanItem key={plan.id} plan={plan} />
              ))}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <CheckCircle size={32} className="text-muted" />
              <p className="text-muted">Aucun plan de maintenance</p>
              <Button size="sm" variant="ghost">
                Creer un plan
              </Button>
            </div>
          )}
        </Card>
      </Grid>

      {/* Resume stock (ERP only) */}
      <Card
        title="Resume du stock"
        icon={<TrendingDown size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-stock-summary">
          <div className="azals-stock-summary__item">
            <span className="text-muted">Total references</span>
            <span className="font-medium">{spareParts.length}</span>
          </div>
          <div className="azals-stock-summary__item">
            <span className="text-muted">En stock</span>
            <span className="font-medium text-success">
              {spareParts.filter(p => p.quantity_on_hand > p.minimum_quantity).length}
            </span>
          </div>
          <div className="azals-stock-summary__item">
            <span className="text-muted">Sous seuil</span>
            <span className="font-medium text-warning">{lowStockParts.length}</span>
          </div>
          <div className="azals-stock-summary__item">
            <span className="text-muted">En rupture</span>
            <span className="font-medium text-danger">{criticalParts.length}</span>
          </div>
        </div>
        {lowStockParts.length > 0 && (
          <div className="mt-4">
            <Button variant="secondary" leftIcon={<ShoppingCart size={16} />}>
              Commander les pieces manquantes
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

/**
 * Composant item piece de rechange
 */
const SparePartItem: React.FC<{ part: SparePart }> = ({ part }) => {
  const isLowStock = part.quantity_on_hand <= part.minimum_quantity;
  const isOutOfStock = part.quantity_on_hand === 0;

  return (
    <div className={`azals-part-item ${isOutOfStock ? 'azals-part-item--danger' : isLowStock ? 'azals-part-item--warning' : ''}`}>
      <div className="azals-part-item__icon">
        <Package size={20} className={isOutOfStock ? 'text-danger' : isLowStock ? 'text-warning' : 'text-muted'} />
      </div>
      <div className="azals-part-item__info">
        <span className="azals-part-item__name">{part.product_name || part.product_code}</span>
        {part.product_code && part.product_name && (
          <span className="azals-part-item__code text-muted text-sm font-mono">{part.product_code}</span>
        )}
      </div>
      <div className="azals-part-item__stock">
        <span className={`font-medium ${isOutOfStock ? 'text-danger' : isLowStock ? 'text-warning' : 'text-success'}`}>
          {part.quantity_on_hand}
        </span>
        <span className="text-muted text-sm">/ min. {part.minimum_quantity}</span>
      </div>
      {isOutOfStock && (
        <span className="azals-badge azals-badge--red azals-badge--sm">Rupture</span>
      )}
      {isLowStock && !isOutOfStock && (
        <span className="azals-badge azals-badge--orange azals-badge--sm">Faible</span>
      )}
    </div>
  );
};

/**
 * Composant item plan de maintenance
 */
const MaintenancePlanItem: React.FC<{ plan: MaintenancePlan }> = ({ plan }) => {
  const nextExecution = plan.next_execution_date ? new Date(plan.next_execution_date) : null;
  const isOverdue = nextExecution && nextExecution < new Date();
  const isDueSoon = nextExecution && !isOverdue &&
    (nextExecution.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24) <= 7;

  return (
    <div className={`azals-plan-item ${!plan.is_active ? 'azals-plan-item--inactive' : ''}`}>
      <div className="azals-plan-item__icon">
        <CheckCircle size={20} className={plan.is_active ? 'text-success' : 'text-gray-400'} />
      </div>
      <div className="azals-plan-item__info">
        <span className="azals-plan-item__name">{plan.name}</span>
        <span className="azals-plan-item__code text-muted text-sm font-mono">{plan.code}</span>
      </div>
      <div className="azals-plan-item__frequency">
        <span className="text-sm">{formatFrequency(plan)}</span>
      </div>
      <div className="azals-plan-item__next">
        {nextExecution ? (
          <span className={`text-sm ${isOverdue ? 'text-danger' : isDueSoon ? 'text-warning' : ''}`}>
            {nextExecution.toLocaleDateString('fr-FR')}
            {isOverdue && ' (En retard)'}
          </span>
        ) : (
          <span className="text-muted text-sm">-</span>
        )}
      </div>
      <span className={`azals-badge azals-badge--${plan.is_active ? 'green' : 'gray'} azals-badge--sm`}>
        {plan.is_active ? 'Actif' : 'Inactif'}
      </span>
    </div>
  );
};

export default AssetPartsTab;
