/**
 * AZALSCORE Module - Maintenance - Asset Info Tab
 * Onglet informations generales de l'equipement
 */

import React from 'react';
import {
  Wrench, MapPin, Building2, Calendar, Shield,
  Tag, FileText, Gauge, AlertTriangle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Asset, AssetMeter } from '../types';
import {
  formatDate, formatCurrency,
  ASSET_TYPE_CONFIG, ASSET_STATUS_CONFIG, CRITICALITY_CONFIG,
  getAssetAge, isWarrantyExpired, isWarrantyExpiringSoon,
  getDaysUntilMaintenance, isMaintenanceOverdue, isMaintenanceDueSoon
} from '../types';

/**
 * AssetInfoTab - Informations generales de l'equipement
 */
export const AssetInfoTab: React.FC<TabContentProps<Asset>> = ({ data: asset }) => {
  const assetAge = getAssetAge(asset);
  const warrantyExpired = isWarrantyExpired(asset);
  const warrantyExpiringSoon = isWarrantyExpiringSoon(asset);
  const daysUntilMaintenance = getDaysUntilMaintenance(asset);
  const maintenanceOverdue = isMaintenanceOverdue(asset);
  const maintenanceDueSoon = isMaintenanceDueSoon(asset);

  return (
    <div className="azals-std-tab-content">
      {/* Alertes */}
      {(maintenanceOverdue || warrantyExpired) && (
        <div className={`azals-alert azals-alert--${maintenanceOverdue ? 'danger' : 'warning'} mb-4`}>
          <AlertTriangle size={18} />
          <span>
            {maintenanceOverdue && 'Maintenance en retard. '}
            {warrantyExpired && 'Garantie expiree.'}
          </span>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Informations principales */}
        <Card title="Informations principales" icon={<Wrench size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Code</label>
              <span className="azals-field__value font-mono">{asset.code}</span>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Nom</label>
              <span className="azals-field__value">{asset.name}</span>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Type</label>
              <span className={`azals-badge azals-badge--${ASSET_TYPE_CONFIG[asset.type].color}`}>
                {ASSET_TYPE_CONFIG[asset.type].label}
              </span>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Statut</label>
              <span className={`azals-badge azals-badge--${ASSET_STATUS_CONFIG[asset.status].color}`}>
                {ASSET_STATUS_CONFIG[asset.status].label}
              </span>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Criticite</label>
              <span className={`azals-badge azals-badge--${CRITICALITY_CONFIG[asset.criticality].color}`}>
                {CRITICALITY_CONFIG[asset.criticality].label}
              </span>
            </div>
            {asset.category_name && (
              <div className="azals-field">
                <label className="azals-field__label">Categorie</label>
                <span className="azals-field__value">{asset.category_name}</span>
              </div>
            )}
            {asset.description && (
              <div className="azals-field azals-field--full">
                <label className="azals-field__label">Description</label>
                <p className="azals-field__value text-muted">{asset.description}</p>
              </div>
            )}
          </div>
        </Card>

        {/* Localisation */}
        <Card title="Localisation" icon={<MapPin size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Emplacement</label>
              <span className="azals-field__value">{asset.location || '-'}</span>
            </div>
            {asset.department_name && (
              <div className="azals-field">
                <label className="azals-field__label">Departement</label>
                <span className="azals-field__value">{asset.department_name}</span>
              </div>
            )}
          </div>
        </Card>

        {/* Specifications techniques */}
        <Card title="Specifications techniques" icon={<Tag size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Fabricant</label>
              <span className="azals-field__value">{asset.manufacturer || '-'}</span>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Modele</label>
              <span className="azals-field__value">{asset.model || '-'}</span>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">N de serie</label>
              <span className="azals-field__value font-mono">{asset.serial_number || '-'}</span>
            </div>
          </div>
        </Card>

        {/* Dates et garantie */}
        <Card title="Dates et garantie" icon={<Calendar size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Date d'achat</label>
              <span className="azals-field__value">{formatDate(asset.purchase_date)}</span>
            </div>
            {asset.purchase_cost && (
              <div className="azals-field">
                <label className="azals-field__label">Cout d'achat</label>
                <span className="azals-field__value">{formatCurrency(asset.purchase_cost)}</span>
              </div>
            )}
            <div className="azals-field">
              <label className="azals-field__label">Age</label>
              <span className="azals-field__value">
                {assetAge !== null ? `${assetAge} an(s)` : '-'}
              </span>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Fin de garantie</label>
              <span className={`azals-field__value ${warrantyExpired ? 'text-danger' : warrantyExpiringSoon ? 'text-warning' : ''}`}>
                {formatDate(asset.warranty_end_date)}
                {warrantyExpired && ' (Expiree)'}
                {warrantyExpiringSoon && !warrantyExpired && ' (Bientot)'}
              </span>
            </div>
          </div>
        </Card>

        {/* Planning maintenance */}
        <Card title="Planning maintenance" icon={<Shield size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Derniere maintenance</label>
              <span className="azals-field__value">{formatDate(asset.last_maintenance_date)}</span>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Prochaine maintenance</label>
              <span className={`azals-field__value ${maintenanceOverdue ? 'text-danger font-medium' : maintenanceDueSoon ? 'text-warning' : ''}`}>
                {formatDate(asset.next_maintenance_date)}
                {maintenanceOverdue && ' (En retard)'}
                {maintenanceDueSoon && !maintenanceOverdue && ' (Proche)'}
              </span>
            </div>
            {daysUntilMaintenance !== null && (
              <div className="azals-field">
                <label className="azals-field__label">Jours restants</label>
                <span className={`azals-field__value font-medium ${daysUntilMaintenance < 0 ? 'text-danger' : daysUntilMaintenance <= 7 ? 'text-warning' : 'text-success'}`}>
                  {daysUntilMaintenance < 0 ? `${Math.abs(daysUntilMaintenance)} jours de retard` : `${daysUntilMaintenance} jours`}
                </span>
              </div>
            )}
            {asset.total_maintenance_cost && (
              <div className="azals-field">
                <label className="azals-field__label">Cout total maintenance</label>
                <span className="azals-field__value">{formatCurrency(asset.total_maintenance_cost)}</span>
              </div>
            )}
          </div>
        </Card>

        {/* Compteurs */}
        {asset.meters && asset.meters.length > 0 && (
          <Card title="Compteurs" icon={<Gauge size={18} />}>
            <div className="azals-meters-list">
              {asset.meters.map((meter) => (
                <MeterItem key={meter.id} meter={meter} />
              ))}
            </div>
          </Card>
        )}
      </Grid>

      {/* Notes (ERP only) */}
      {asset.notes && (
        <Card
          title="Notes"
          icon={<FileText size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <p className="text-muted whitespace-pre-wrap">{asset.notes}</p>
        </Card>
      )}
    </div>
  );
};

/**
 * Composant compteur
 */
const MeterItem: React.FC<{ meter: AssetMeter }> = ({ meter }) => {
  return (
    <div className="azals-meter-item">
      <div className="azals-meter-item__info">
        <span className="azals-meter-item__name">{meter.name}</span>
        <span className="azals-meter-item__type text-muted text-sm">{meter.type}</span>
      </div>
      <div className="azals-meter-item__value">
        <span className="font-medium text-lg">{meter.current_value.toLocaleString()}</span>
        <span className="text-muted ml-1">{meter.unit}</span>
      </div>
      {meter.last_reading_date && (
        <span className="text-xs text-muted">
          Maj: {new Date(meter.last_reading_date).toLocaleDateString('fr-FR')}
        </span>
      )}
    </div>
  );
};

export default AssetInfoTab;
