/**
 * AZALSCORE Module - Production - Order Materials Tab
 * Onglet materiaux/composants de l'ordre de fabrication
 */

import React from 'react';
import {
  Package, Layers, AlertTriangle, CheckCircle,
  ArrowRight, Box, BarChart3
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { ProductionOrder, MaterialConsumption, ProductionOutput } from '../types';
import { formatQuantity, formatDateTime } from '../types';

/**
 * OrderMaterialsTab - Materiaux et consommations
 */
export const OrderMaterialsTab: React.FC<TabContentProps<ProductionOrder>> = ({ data: order }) => {
  const consumptions = order.material_consumptions || [];
  const outputs = order.outputs || [];

  // Calculer les statistiques de consommation
  const totalPlanned = consumptions.reduce((sum, c) => sum + c.quantity_planned, 0);
  const totalConsumed = consumptions.reduce((sum, c) => sum + c.quantity_consumed, 0);
  const consumptionRate = totalPlanned > 0 ? totalConsumed / totalPlanned : 0;

  // Composants avec ecart
  const overConsumed = consumptions.filter(c => c.quantity_consumed > c.quantity_planned);
  const underConsumed = consumptions.filter(c => c.quantity_consumed < c.quantity_planned && c.quantity_consumed > 0);

  return (
    <div className="azals-std-tab-content">
      {/* Resume */}
      <div className="azals-materials-summary mb-4">
        <Grid cols={4} gap="md">
          <div className="azals-stat-mini">
            <span className="azals-stat-mini__value">{consumptions.length}</span>
            <span className="azals-stat-mini__label">Composants</span>
          </div>
          <div className="azals-stat-mini">
            <span className="azals-stat-mini__value">{(consumptionRate * 100).toFixed(0)}%</span>
            <span className="azals-stat-mini__label">Consommation</span>
          </div>
          <div className="azals-stat-mini azals-stat-mini--warning">
            <span className="azals-stat-mini__value">{overConsumed.length}</span>
            <span className="azals-stat-mini__label">Surconsommations</span>
          </div>
          <div className="azals-stat-mini azals-stat-mini--success">
            <span className="azals-stat-mini__value">{outputs.length}</span>
            <span className="azals-stat-mini__label">Sorties</span>
          </div>
        </Grid>
      </div>

      <Grid cols={2} gap="lg">
        {/* Composants a consommer */}
        <Card title="Composants" icon={<Package size={18} />}>
          {consumptions.length > 0 ? (
            <div className="azals-materials-list">
              {consumptions.map((consumption) => (
                <MaterialItem key={consumption.id} consumption={consumption} />
              ))}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Package size={32} className="text-muted" />
              <p className="text-muted">Aucun composant defini</p>
            </div>
          )}
        </Card>

        {/* Production realisee */}
        <Card title="Production realisee" icon={<Box size={18} />}>
          {outputs.length > 0 ? (
            <div className="azals-outputs-list">
              {outputs.map((output) => (
                <OutputItem key={output.id} output={output} />
              ))}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Box size={32} className="text-muted" />
              <p className="text-muted">Aucune production enregistree</p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Alertes consommation */}
      {overConsumed.length > 0 && (
        <Card title="Alertes de surconsommation" icon={<AlertTriangle size={18} />} className="mt-4">
          <div className="azals-alerts-list">
            {overConsumed.map((c) => {
              const variance = c.quantity_consumed - c.quantity_planned;
              const variancePercent = (variance / c.quantity_planned) * 100;
              return (
                <div key={c.id} className="azals-alert-item azals-alert-item--warning">
                  <div className="azals-alert-item__icon">
                    <AlertTriangle size={16} />
                  </div>
                  <div className="azals-alert-item__content">
                    <strong>{c.component_name || c.component_code}</strong>
                    <span className="text-muted mx-2">-</span>
                    <span>Surconsommation de {formatQuantity(variance, c.unit)}</span>
                    <span className="text-muted ml-1">(+{variancePercent.toFixed(1)}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Tableau detaille (ERP only) */}
      {consumptions.length > 0 && (
        <Card title="Detail des consommations" icon={<Layers size={18} />} className="mt-4 azals-std-field--secondary">
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Code</th>
                <th>Composant</th>
                <th>Qte prevue</th>
                <th>Qte consommee</th>
                <th>Ecart</th>
                <th>Lot</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {consumptions.map((c) => {
                const variance = c.quantity_consumed - c.quantity_planned;
                const isOver = variance > 0;
                const isUnder = variance < 0 && c.quantity_consumed > 0;
                return (
                  <tr key={c.id}>
                    <td className="font-mono">{c.component_code || '-'}</td>
                    <td>{c.component_name || '-'}</td>
                    <td>{formatQuantity(c.quantity_planned, c.unit)}</td>
                    <td>{formatQuantity(c.quantity_consumed, c.unit)}</td>
                    <td className={isOver ? 'text-danger' : isUnder ? 'text-warning' : 'text-success'}>
                      {variance !== 0 ? (
                        <>
                          {variance > 0 ? '+' : ''}{formatQuantity(variance, c.unit)}
                        </>
                      ) : (
                        <CheckCircle size={14} className="text-success" />
                      )}
                    </td>
                    <td className="font-mono">{c.lot_number || '-'}</td>
                    <td className="text-muted">{c.consumed_at ? formatDateTime(c.consumed_at) : '-'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}

      {/* Tableau des sorties (ERP only) */}
      {outputs.length > 0 && (
        <Card title="Detail des sorties" icon={<BarChart3 size={18} />} className="mt-4 azals-std-field--secondary">
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Code</th>
                <th>Produit</th>
                <th>Quantite</th>
                <th>Lot</th>
                <th>Qualite</th>
                <th>Date</th>
                <th>Operateur</th>
              </tr>
            </thead>
            <tbody>
              {outputs.map((o) => (
                <tr key={o.id}>
                  <td className="font-mono">{o.product_code || '-'}</td>
                  <td>{o.product_name || '-'}</td>
                  <td>{formatQuantity(o.quantity, o.unit)}</td>
                  <td className="font-mono">{o.lot_number || '-'}</td>
                  <td>
                    {o.quality_status === 'OK' && (
                      <span className="azals-badge azals-badge--green azals-badge--sm">OK</span>
                    )}
                    {o.quality_status === 'NOK' && (
                      <span className="azals-badge azals-badge--red azals-badge--sm">NOK</span>
                    )}
                    {o.quality_status === 'PENDING' && (
                      <span className="azals-badge azals-badge--gray azals-badge--sm">A controler</span>
                    )}
                    {!o.quality_status && '-'}
                  </td>
                  <td className="text-muted">{formatDateTime(o.produced_at)}</td>
                  <td>{o.produced_by || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
};

/**
 * Composant item de materiau
 */
interface MaterialItemProps {
  consumption: MaterialConsumption;
}

const MaterialItem: React.FC<MaterialItemProps> = ({ consumption }) => {
  const progress = consumption.quantity_planned > 0
    ? (consumption.quantity_consumed / consumption.quantity_planned) * 100
    : 0;
  const isOver = progress > 100;
  const isComplete = progress >= 100;

  return (
    <div className={`azals-material-item ${isOver ? 'azals-material-item--over' : isComplete ? 'azals-material-item--complete' : ''}`}>
      <div className="azals-material-item__icon">
        <Package size={16} />
      </div>
      <div className="azals-material-item__content">
        <div className="azals-material-item__header">
          <span className="azals-material-item__name">
            {consumption.component_name || consumption.component_code}
          </span>
          {consumption.lot_number && (
            <span className="azals-material-item__lot font-mono text-sm text-muted">
              Lot: {consumption.lot_number}
            </span>
          )}
        </div>
        <div className="azals-material-item__quantities">
          <span>{formatQuantity(consumption.quantity_consumed, consumption.unit)}</span>
          <ArrowRight size={12} className="mx-1" />
          <span className="text-muted">{formatQuantity(consumption.quantity_planned, consumption.unit)}</span>
        </div>
        <div className="azals-progress azals-progress--sm mt-1">
          <div
            className={`azals-progress__bar azals-progress__bar--${isOver ? 'danger' : isComplete ? 'success' : 'primary'}`}
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
      </div>
      <div className="azals-material-item__status">
        {isOver && <AlertTriangle size={16} className="text-danger" />}
        {isComplete && !isOver && <CheckCircle size={16} className="text-success" />}
      </div>
    </div>
  );
};

/**
 * Composant item de sortie
 */
interface OutputItemProps {
  output: ProductionOutput;
}

const OutputItem: React.FC<OutputItemProps> = ({ output }) => {
  return (
    <div className={`azals-output-item ${output.quality_status === 'NOK' ? 'azals-output-item--nok' : ''}`}>
      <div className="azals-output-item__icon">
        <Box size={16} />
      </div>
      <div className="azals-output-item__content">
        <div className="azals-output-item__header">
          <span className="azals-output-item__name">
            {output.product_name || output.product_code}
          </span>
          <span className={`azals-badge azals-badge--sm azals-badge--${
            output.quality_status === 'OK' ? 'green' :
            output.quality_status === 'NOK' ? 'red' : 'gray'
          }`}>
            {output.quality_status || 'N/A'}
          </span>
        </div>
        <div className="azals-output-item__details text-sm">
          <span className="font-semibold">{formatQuantity(output.quantity, output.unit)}</span>
          {output.lot_number && (
            <span className="text-muted ml-2">Lot: {output.lot_number}</span>
          )}
          <span className="text-muted ml-2">{formatDateTime(output.produced_at)}</span>
        </div>
      </div>
    </div>
  );
};

export default OrderMaterialsTab;
