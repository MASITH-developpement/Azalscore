/**
 * AZALSCORE Module - Vehicles - Vehicle Fuel Tab
 * Onglet carburant et consommation du vehicule
 */

import React, { useState } from 'react';
import {
  Fuel, Plus, TrendingUp, TrendingDown, Calendar,
  MapPin, Euro, Gauge
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Vehicule, FuelLog } from '../types';
import {
  formatDate, formatCurrency, formatKilometers,
  calculateAverageConsumption, FUEL_TYPE_ICONS
} from '../types';

/**
 * VehicleFuelTab - Suivi carburant et consommation
 */
export const VehicleFuelTab: React.FC<TabContentProps<Vehicule>> = ({ data: vehicle }) => {
  const [showForm, setShowForm] = useState(false);
  const fuelLogs = vehicle.fuel_logs || [];
  const avgConsumption = calculateAverageConsumption(vehicle);

  // Calculs
  const totalLiters = fuelLogs.reduce((sum, log) => sum + log.liters, 0);
  const totalCost = fuelLogs.reduce((sum, log) => sum + log.total_cost, 0);
  const avgPricePerLiter = totalLiters > 0 ? totalCost / totalLiters : 0;

  // Derniers pleins
  const recentLogs = [...fuelLogs]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 10);

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button
          variant="secondary"
          leftIcon={<Plus size={16} />}
          onClick={() => setShowForm(!showForm)}
        >
          Enregistrer un plein
        </Button>
      </div>

      {/* Resume consommation */}
      <Grid cols={4} gap="md" className="mb-4">
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__icon">
              {FUEL_TYPE_ICONS[vehicle.type_carburant]}
            </span>
            <span className="azals-stat__label">Conso. theorique</span>
            <span className="azals-stat__value">
              {vehicle.conso_100km} {vehicle.type_carburant === 'electrique' ? 'kWh' : 'L'}/100km
            </span>
          </div>
        </Card>

        <Card>
          <div className="azals-stat">
            <Gauge size={20} className="text-blue-500" />
            <span className="azals-stat__label">Conso. reelle</span>
            <span className="azals-stat__value">
              {avgConsumption
                ? `${avgConsumption.toFixed(1)} ${vehicle.type_carburant === 'electrique' ? 'kWh' : 'L'}/100km`
                : 'N/A'
              }
            </span>
            {avgConsumption && (
              <span className={`azals-stat__trend ${avgConsumption <= vehicle.conso_100km ? 'text-success' : 'text-danger'}`}>
                {avgConsumption <= vehicle.conso_100km ? <TrendingDown size={14} /> : <TrendingUp size={14} />}
                {((avgConsumption - vehicle.conso_100km) / vehicle.conso_100km * 100).toFixed(0)}%
              </span>
            )}
          </div>
        </Card>

        <Card>
          <div className="azals-stat">
            <Fuel size={20} className="text-green-500" />
            <span className="azals-stat__label">Total carburant</span>
            <span className="azals-stat__value">
              {totalLiters.toFixed(0)} {vehicle.type_carburant === 'electrique' ? 'kWh' : 'L'}
            </span>
          </div>
        </Card>

        <Card>
          <div className="azals-stat">
            <Euro size={20} className="text-orange-500" />
            <span className="azals-stat__label">Depenses totales</span>
            <span className="azals-stat__value">{formatCurrency(totalCost)}</span>
          </div>
        </Card>
      </Grid>

      {/* Historique des pleins */}
      <Card title="Historique des pleins" icon={<Fuel size={18} />}>
        {recentLogs.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Date</th>
                <th>Kilometrage</th>
                <th className="text-right">Quantite</th>
                <th className="text-right">Prix/L</th>
                <th className="text-right">Total</th>
                <th>Station</th>
                <th>Plein</th>
              </tr>
            </thead>
            <tbody>
              {recentLogs.map((log) => (
                <FuelLogRow key={log.id} log={log} vehicle={vehicle} />
              ))}
            </tbody>
            <tfoot>
              <tr className="font-medium">
                <td colSpan={2}>Total</td>
                <td className="text-right">
                  {totalLiters.toFixed(1)} {vehicle.type_carburant === 'electrique' ? 'kWh' : 'L'}
                </td>
                <td className="text-right">
                  {avgPricePerLiter.toFixed(3)} Euro
                </td>
                <td className="text-right">{formatCurrency(totalCost)}</td>
                <td colSpan={2}></td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Fuel size={32} className="text-muted" />
            <p className="text-muted">Aucun plein enregistre</p>
            <Button size="sm" variant="ghost" leftIcon={<Plus size={14} />} onClick={() => setShowForm(true)}>
              Enregistrer un plein
            </Button>
          </div>
        )}
      </Card>

      {/* Statistiques detaillees (ERP only) */}
      <Card
        title="Statistiques detaillees"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={3} gap="md">
          <div className="azals-stat-card">
            <Calendar size={20} className="text-blue-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">Nombre de pleins</span>
              <span className="azals-stat-card__value">{fuelLogs.length}</span>
            </div>
          </div>

          <div className="azals-stat-card">
            <Euro size={20} className="text-green-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">Prix moyen/L</span>
              <span className="azals-stat-card__value">
                {avgPricePerLiter.toFixed(3)} Euro
              </span>
            </div>
          </div>

          <div className="azals-stat-card">
            <Gauge size={20} className="text-orange-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">Km par plein (moy)</span>
              <span className="azals-stat-card__value">
                {fuelLogs.length > 1
                  ? formatKilometers(Math.round(vehicle.kilometrage_actuel / fuelLogs.length))
                  : 'N/A'
                }
              </span>
            </div>
          </div>
        </Grid>

        {/* Evolution des prix */}
        {fuelLogs.length > 1 && (
          <div className="mt-4">
            <h4 className="text-sm font-medium mb-2">Evolution du prix au litre</h4>
            <div className="azals-price-evolution">
              {recentLogs.slice(0, 6).reverse().map((log, index) => (
                <div key={log.id} className="azals-price-evolution__bar">
                  <div
                    className="azals-price-evolution__fill"
                    style={{
                      height: `${(log.price_per_liter / 2.5) * 100}%`,
                      backgroundColor: log.price_per_liter > avgPricePerLiter
                        ? 'var(--azals-danger-500)'
                        : 'var(--azals-success-500)'
                    }}
                  />
                  <span className="azals-price-evolution__label">
                    {log.price_per_liter.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

/**
 * Ligne de log carburant
 */
const FuelLogRow: React.FC<{ log: FuelLog; vehicle: Vehicule }> = ({ log, vehicle }) => {
  return (
    <tr>
      <td>{formatDate(log.date)}</td>
      <td>{formatKilometers(log.mileage_at_fill)}</td>
      <td className="text-right">
        {log.liters.toFixed(1)} {vehicle.type_carburant === 'electrique' ? 'kWh' : 'L'}
      </td>
      <td className="text-right">{log.price_per_liter.toFixed(3)} Euro</td>
      <td className="text-right font-medium">{formatCurrency(log.total_cost)}</td>
      <td>
        {log.station ? (
          <span className="flex items-center gap-1">
            <MapPin size={12} className="text-muted" />
            {log.station}
          </span>
        ) : (
          <span className="text-muted">-</span>
        )}
      </td>
      <td>
        <span className={`azals-badge azals-badge--${log.full_tank ? 'green' : 'gray'} azals-badge--sm`}>
          {log.full_tank ? 'Complet' : 'Partiel'}
        </span>
      </td>
    </tr>
  );
};

export default VehicleFuelTab;
