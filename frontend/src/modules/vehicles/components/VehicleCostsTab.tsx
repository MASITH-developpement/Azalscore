/**
 * AZALSCORE Module - Vehicles - Vehicle Costs Tab
 * Onglet couts et rentabilite du vehicule
 */

import React from 'react';
import {
  Calculator, Fuel, Wrench, Shield, TrendingDown,
  Leaf, Euro, PieChart, BarChart3
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Vehicule } from '../types';
import {
  calculCoutKm, getCO2Km, formatCurrencyKm, formatCurrency, formatKilometers,
  getTotalMaintenanceCost, getTotalMileageCost, getTotalCO2Emissions
} from '../types';

/**
 * VehicleCostsTab - Couts detailles du vehicule
 */
export const VehicleCostsTab: React.FC<TabContentProps<Vehicule>> = ({ data: vehicle }) => {
  const coutKm = calculCoutKm(vehicle);
  const co2Km = getCO2Km(vehicle);
  const totalMaintenance = getTotalMaintenanceCost(vehicle);
  const totalMileage = getTotalMileageCost(vehicle);
  const totalCO2 = getTotalCO2Emissions(vehicle);

  // Calcul des pourcentages pour le graphique
  const total = coutKm.total || 0.001;
  const percentCarburant = (coutKm.carburant / total) * 100;
  const percentEntretien = (coutKm.entretien / total) * 100;
  const percentAssurance = (coutKm.assurance / total) * 100;
  const percentAmort = (coutKm.amortissement / total) * 100;

  return (
    <div className="azals-std-tab-content">
      {/* Resume cout/km */}
      <Card title="Cout au kilometre" icon={<Calculator size={18} />} className="mb-4">
        <div className="azals-cost-summary">
          <div className="azals-cost-summary__total">
            <span className="azals-cost-summary__label">Cout total/km</span>
            <span className="azals-cost-summary__value">{formatCurrencyKm(coutKm.total)}</span>
          </div>
          <div className="azals-cost-summary__co2">
            <Leaf size={18} className="text-green-500" />
            <span>Emissions CO2: <strong>{co2Km.toFixed(3)} kg/km</strong></span>
          </div>
        </div>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Detail des couts */}
        <Card title="Decomposition des couts" icon={<PieChart size={18} />}>
          <div className="azals-cost-breakdown">
            <div className="azals-cost-breakdown__item">
              <div className="azals-cost-breakdown__icon">
                <Fuel size={18} className="text-blue-500" />
              </div>
              <div className="azals-cost-breakdown__info">
                <span className="azals-cost-breakdown__label">Carburant</span>
                <span className="azals-cost-breakdown__detail">
                  {vehicle.conso_100km} {vehicle.type_carburant === 'electrique' ? 'kWh' : 'L'}/100km x{' '}
                  {vehicle.prix_carburant.toFixed(2)} Euro
                </span>
              </div>
              <div className="azals-cost-breakdown__value">
                <span>{formatCurrencyKm(coutKm.carburant)}</span>
                <span className="azals-cost-breakdown__percent">{percentCarburant.toFixed(0)}%</span>
              </div>
              <div className="azals-cost-breakdown__bar">
                <div
                  className="azals-cost-breakdown__bar-fill azals-cost-breakdown__bar-fill--blue"
                  style={{ width: `${percentCarburant}%` }}
                />
              </div>
            </div>

            <div className="azals-cost-breakdown__item">
              <div className="azals-cost-breakdown__icon">
                <Wrench size={18} className="text-orange-500" />
              </div>
              <div className="azals-cost-breakdown__info">
                <span className="azals-cost-breakdown__label">Entretien</span>
                <span className="azals-cost-breakdown__detail">
                  Cout estime/km
                </span>
              </div>
              <div className="azals-cost-breakdown__value">
                <span>{formatCurrencyKm(coutKm.entretien)}</span>
                <span className="azals-cost-breakdown__percent">{percentEntretien.toFixed(0)}%</span>
              </div>
              <div className="azals-cost-breakdown__bar">
                <div
                  className="azals-cost-breakdown__bar-fill azals-cost-breakdown__bar-fill--orange"
                  style={{ width: `${percentEntretien}%` }}
                />
              </div>
            </div>

            <div className="azals-cost-breakdown__item">
              <div className="azals-cost-breakdown__icon">
                <Shield size={18} className="text-purple-500" />
              </div>
              <div className="azals-cost-breakdown__info">
                <span className="azals-cost-breakdown__label">Assurance</span>
                <span className="azals-cost-breakdown__detail">
                  {formatCurrency(vehicle.assurance_mois)}/mois / {formatKilometers(vehicle.km_mois_estime)}
                </span>
              </div>
              <div className="azals-cost-breakdown__value">
                <span>{formatCurrencyKm(coutKm.assurance)}</span>
                <span className="azals-cost-breakdown__percent">{percentAssurance.toFixed(0)}%</span>
              </div>
              <div className="azals-cost-breakdown__bar">
                <div
                  className="azals-cost-breakdown__bar-fill azals-cost-breakdown__bar-fill--purple"
                  style={{ width: `${percentAssurance}%` }}
                />
              </div>
            </div>

            <div className="azals-cost-breakdown__item">
              <div className="azals-cost-breakdown__icon">
                <TrendingDown size={18} className="text-gray-500" />
              </div>
              <div className="azals-cost-breakdown__info">
                <span className="azals-cost-breakdown__label">Amortissement</span>
                <span className="azals-cost-breakdown__detail">
                  {vehicle.prix_achat && vehicle.duree_amort_km
                    ? `${formatCurrency(vehicle.prix_achat)} / ${formatKilometers(vehicle.duree_amort_km)}`
                    : 'Non configure'
                  }
                </span>
              </div>
              <div className="azals-cost-breakdown__value">
                <span>{formatCurrencyKm(coutKm.amortissement)}</span>
                <span className="azals-cost-breakdown__percent">{percentAmort.toFixed(0)}%</span>
              </div>
              <div className="azals-cost-breakdown__bar">
                <div
                  className="azals-cost-breakdown__bar-fill azals-cost-breakdown__bar-fill--gray"
                  style={{ width: `${percentAmort}%` }}
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Comparaison et benchmarks */}
        <Card title="Comparaison" icon={<BarChart3 size={18} />}>
          <div className="azals-comparison">
            <div className="azals-comparison__item">
              <span className="azals-comparison__label">Bareme fiscal 2026</span>
              <span className="azals-comparison__value">0.603 Euro/km</span>
              <span className={`azals-comparison__diff ${coutKm.total < 0.603 ? 'text-success' : 'text-danger'}`}>
                {coutKm.total < 0.603 ? '▼' : '▲'} {Math.abs(((coutKm.total - 0.603) / 0.603) * 100).toFixed(0)}%
              </span>
            </div>
            <div className="azals-comparison__item">
              <span className="azals-comparison__label">Moyenne entreprise</span>
              <span className="azals-comparison__value">0.45 Euro/km</span>
              <span className={`azals-comparison__diff ${coutKm.total < 0.45 ? 'text-success' : 'text-danger'}`}>
                {coutKm.total < 0.45 ? '▼' : '▲'} {Math.abs(((coutKm.total - 0.45) / 0.45) * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <div className="azals-divider my-4" />

          <div className="azals-co2-indicator">
            <div className="azals-co2-indicator__header">
              <Leaf size={18} className="text-green-500" />
              <span>Impact environnemental</span>
            </div>
            <div className="azals-co2-indicator__scale">
              <div
                className="azals-co2-indicator__marker"
                style={{ left: `${Math.min(100, (co2Km / 0.3) * 100)}%` }}
              />
              <div className="azals-co2-indicator__labels">
                <span>Faible</span>
                <span>Moyen</span>
                <span>Eleve</span>
              </div>
            </div>
            <p className="text-sm text-muted mt-2">
              {co2Km < 0.1
                ? 'Excellent - Vehicule peu polluant'
                : co2Km < 0.2
                ? 'Correct - Emissions moderees'
                : 'Attention - Emissions elevees'
              }
            </p>
          </div>
        </Card>
      </Grid>

      {/* Totaux cumules (ERP only) */}
      <Card
        title="Totaux cumules"
        icon={<Euro size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={4} gap="md">
          <div className="azals-stat-card">
            <Wrench size={20} className="text-orange-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">Maintenance totale</span>
              <span className="azals-stat-card__value">{formatCurrency(totalMaintenance)}</span>
            </div>
          </div>

          <div className="azals-stat-card">
            <Euro size={20} className="text-blue-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">Frais km factures</span>
              <span className="azals-stat-card__value">{formatCurrency(totalMileage)}</span>
            </div>
          </div>

          <div className="azals-stat-card">
            <Leaf size={20} className="text-green-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">CO2 total emis</span>
              <span className="azals-stat-card__value">{totalCO2.toFixed(1)} kg</span>
            </div>
          </div>

          <div className="azals-stat-card">
            <Calculator size={20} className="text-purple-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">Cout total estime</span>
              <span className="azals-stat-card__value">
                {formatCurrency(coutKm.total * vehicle.kilometrage_actuel)}
              </span>
            </div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default VehicleCostsTab;
