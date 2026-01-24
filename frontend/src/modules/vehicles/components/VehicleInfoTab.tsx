/**
 * AZALSCORE Module - Vehicles - Vehicle Info Tab
 * Onglet informations generales du vehicule
 */

import React from 'react';
import {
  Car, MapPin, User, Calendar, Settings, Gauge,
  Fuel, Shield, Award
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Vehicule } from '../types';
import {
  formatDate, formatKilometers, formatCurrency,
  FUEL_TYPE_CONFIG, FUEL_TYPE_ICONS,
  getVehicleAge, getAverageYearlyMileage
} from '../types';

/**
 * VehicleInfoTab - Informations generales du vehicule
 */
export const VehicleInfoTab: React.FC<TabContentProps<Vehicule>> = ({ data: vehicle }) => {
  const age = getVehicleAge(vehicle);
  const avgYearlyKm = getAverageYearlyMileage(vehicle);
  const fuelConfig = FUEL_TYPE_CONFIG[vehicle.type_carburant];

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Identification */}
        <Card title="Identification" icon={<Car size={18} />}>
          <dl className="azals-dl">
            <dt>Immatriculation</dt>
            <dd className="font-medium text-lg">{vehicle.immatriculation}</dd>

            <dt>Marque</dt>
            <dd>{vehicle.marque}</dd>

            <dt>Modele</dt>
            <dd>{vehicle.modele}</dd>

            <dt>Type carburant</dt>
            <dd>
              <span className={`azals-badge azals-badge--${fuelConfig.color}`}>
                {FUEL_TYPE_ICONS[vehicle.type_carburant]} {fuelConfig.label}
              </span>
            </dd>

            <dt>Norme Euro</dt>
            <dd>{vehicle.norme_euro || '-'}</dd>

            <dt>Statut</dt>
            <dd>
              <span className={`azals-badge azals-badge--${vehicle.is_active ? 'green' : 'gray'}`}>
                {vehicle.is_active ? 'Actif' : 'Inactif'}
              </span>
            </dd>
          </dl>
        </Card>

        {/* Affectation */}
        <Card title="Affectation" icon={<User size={18} />}>
          <dl className="azals-dl">
            <dt>Conducteur attire</dt>
            <dd>
              {vehicle.employe_nom ? (
                <span className="flex items-center gap-2">
                  <User size={16} className="text-primary" />
                  {vehicle.employe_nom}
                </span>
              ) : (
                <span className="text-muted">Pool (non affecte)</span>
              )}
            </dd>

            <dt>Km estimes/mois</dt>
            <dd>{formatKilometers(vehicle.km_mois_estime)}</dd>

            <dt>Km annuel moyen</dt>
            <dd>{avgYearlyKm ? formatKilometers(avgYearlyKm) : '-'}</dd>
          </dl>
        </Card>

        {/* Compteurs */}
        <Card title="Compteurs" icon={<Gauge size={18} />}>
          <dl className="azals-dl">
            <dt>Kilometrage actuel</dt>
            <dd className="font-medium text-lg text-primary">
              {formatKilometers(vehicle.kilometrage_actuel)}
            </dd>

            <dt>Date mise en service</dt>
            <dd>{formatDate(vehicle.date_mise_service)}</dd>

            <dt>Age du vehicule</dt>
            <dd>{age !== null ? `${age} an(s)` : '-'}</dd>
          </dl>
        </Card>

        {/* Entretien */}
        <Card title="Entretien" icon={<Settings size={18} />}>
          <dl className="azals-dl">
            <dt>Derniere revision</dt>
            <dd>{formatDate(vehicle.date_derniere_revision)}</dd>

            <dt>Prochaine revision</dt>
            <dd>
              {vehicle.prochaine_revision ? (
                <span className="text-warning">{formatDate(vehicle.prochaine_revision)}</span>
              ) : (
                '-'
              )}
            </dd>
          </dl>
        </Card>
      </Grid>

      {/* Caracteristiques techniques (ERP only) */}
      <Card
        title="Caracteristiques techniques"
        icon={<Settings size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={4} gap="md">
          <div className="azals-stat-card">
            <Fuel size={20} className="text-blue-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">Consommation</span>
              <span className="azals-stat-card__value">
                {vehicle.conso_100km} {vehicle.type_carburant === 'electrique' ? 'kWh' : 'L'}/100km
              </span>
            </div>
          </div>

          <div className="azals-stat-card">
            <Fuel size={20} className="text-green-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">Prix carburant</span>
              <span className="azals-stat-card__value">
                {vehicle.prix_carburant.toFixed(2)} Euro/{vehicle.type_carburant === 'electrique' ? 'kWh' : 'L'}
              </span>
            </div>
          </div>

          <div className="azals-stat-card">
            <Shield size={20} className="text-purple-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">Assurance/mois</span>
              <span className="azals-stat-card__value">{formatCurrency(vehicle.assurance_mois)}</span>
            </div>
          </div>

          <div className="azals-stat-card">
            <Award size={20} className="text-orange-500" />
            <div className="azals-stat-card__content">
              <span className="azals-stat-card__label">Cout entretien</span>
              <span className="azals-stat-card__value">{vehicle.cout_entretien_km.toFixed(3)} Euro/km</span>
            </div>
          </div>
        </Grid>
      </Card>

      {/* Amortissement (ERP only) */}
      {(vehicle.prix_achat || vehicle.duree_amort_km) && (
        <Card
          title="Amortissement"
          icon={<Calendar size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <Grid cols={2} gap="md">
            <dl className="azals-dl">
              <dt>Prix d'achat</dt>
              <dd>{vehicle.prix_achat ? formatCurrency(vehicle.prix_achat) : '-'}</dd>

              <dt>Duree amortissement</dt>
              <dd>{vehicle.duree_amort_km ? formatKilometers(vehicle.duree_amort_km) : '-'}</dd>
            </dl>

            <dl className="azals-dl">
              <dt>Amortissement restant</dt>
              <dd>
                {vehicle.prix_achat && vehicle.duree_amort_km ? (
                  <>
                    {formatKilometers(Math.max(0, vehicle.duree_amort_km - vehicle.kilometrage_actuel))}
                    <span className="text-muted ml-2">
                      ({Math.round((vehicle.kilometrage_actuel / vehicle.duree_amort_km) * 100)}% amorti)
                    </span>
                  </>
                ) : (
                  '-'
                )}
              </dd>

              <dt>Valeur residuelle estimee</dt>
              <dd>
                {vehicle.prix_achat && vehicle.duree_amort_km ? (
                  formatCurrency(
                    Math.max(0, vehicle.prix_achat * (1 - vehicle.kilometrage_actuel / vehicle.duree_amort_km))
                  )
                ) : (
                  '-'
                )}
              </dd>
            </dl>
          </Grid>
        </Card>
      )}
    </div>
  );
};

export default VehicleInfoTab;
