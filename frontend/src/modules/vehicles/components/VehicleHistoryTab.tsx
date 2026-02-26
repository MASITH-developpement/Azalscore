/**
 * AZALSCORE Module - Vehicles - Vehicle History Tab
 * Onglet historique du vehicule
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  Wrench, CheckCircle, Fuel, MapPin, Car, AlertTriangle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDateTime, formatDate, formatCurrency } from '@/utils/formatters';
import {
  formatKilometers,
  MAINTENANCE_TYPE_CONFIG
} from '../types';
import type { Vehicule, VehicleHistoryEntry, MaintenanceLog, MileageLog } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * VehicleHistoryTab - Historique du vehicule
 */
export const VehicleHistoryTab: React.FC<TabContentProps<Vehicule>> = ({ data: vehicle }) => {
  // Generer l'historique combine
  const history = generateHistoryFromVehicle(vehicle);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique des evenements" icon={<Clock size={18} />}>
        {history.length > 0 ? (
          <div className="azals-timeline">
            {history.map((entry, index) => (
              <HistoryEntry
                key={entry.id}
                entry={entry}
                isFirst={index === 0}
                isLast={index === history.length - 1}
              />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Clock size={32} className="text-muted" />
            <p className="text-muted">Aucun historique disponible</p>
          </div>
        )}
      </Card>

      <Grid cols={2} gap="lg" className="mt-4">
        {/* Historique maintenance */}
        <Card title="Historique maintenance" icon={<Wrench size={18} />}>
          {(vehicle.maintenance_logs?.length || 0) > 0 ? (
            <table className="azals-table azals-table--simple azals-table--compact">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Km</th>
                  <th className="text-right">Cout</th>
                </tr>
              </thead>
              <tbody>
                {vehicle.maintenance_logs?.slice(0, 10).map((log) => (
                  <MaintenanceRow key={log.id} log={log} />
                ))}
              </tbody>
            </table>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Wrench size={32} className="text-muted" />
              <p className="text-muted">Aucune maintenance enregistree</p>
            </div>
          )}
        </Card>

        {/* Historique deplacements */}
        <Card title="Deplacements recents" icon={<MapPin size={18} />}>
          {(vehicle.mileage_logs?.length || 0) > 0 ? (
            <table className="azals-table azals-table--simple azals-table--compact">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Motif</th>
                  <th className="text-right">Km</th>
                  <th className="text-right">Cout</th>
                </tr>
              </thead>
              <tbody>
                {vehicle.mileage_logs?.slice(0, 10).map((log) => (
                  <MileageRow key={log.id} log={log} />
                ))}
              </tbody>
            </table>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <MapPin size={32} className="text-muted" />
              <p className="text-muted">Aucun deplacement enregistre</p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Journal d'audit detaille (ERP only) */}
      <Card
        title="Journal d'audit detaille"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <table className="azals-table azals-table--simple azals-table--compact">
          <thead>
            <tr>
              <th>Date/Heure</th>
              <th>Action</th>
              <th>Utilisateur</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry) => (
              <tr key={entry.id}>
                <td className="text-muted text-sm">{formatDateTime(entry.timestamp)}</td>
                <td>{entry.action}</td>
                <td>{entry.user_name || 'Systeme'}</td>
                <td className="text-muted text-sm">
                  {entry.details || '-'}
                  {entry.old_value && entry.new_value && (
                    <span className="ml-2">
                      <span className="text-danger">{entry.old_value}</span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className="text-success">{entry.new_value}</span>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

/**
 * Composant entree de timeline
 */
interface HistoryEntryProps {
  entry: VehicleHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation') || action.includes('acquisition')) {
      return <Car size={16} className="text-success" />;
    }
    if (action.includes('maintenance') || action.includes('revision') || action.includes('entretien')) {
      return <Wrench size={16} className="text-blue-500" />;
    }
    if (action.includes('carburant') || action.includes('plein')) {
      return <Fuel size={16} className="text-orange-500" />;
    }
    if (action.includes('deplacement') || action.includes('trajet')) {
      return <MapPin size={16} className="text-purple-500" />;
    }
    if (action.includes('controle') || action.includes('inspection')) {
      return <CheckCircle size={16} className="text-green-500" />;
    }
    if (action.includes('panne') || action.includes('incident')) {
      return <AlertTriangle size={16} className="text-danger" />;
    }
    if (action.includes('modifie') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    return <Clock size={16} className="text-muted" />;
  };

  return (
    <div className={`azals-timeline__entry ${isFirst ? 'azals-timeline__entry--first' : ''} ${isLast ? 'azals-timeline__entry--last' : ''}`}>
      <div className="azals-timeline__icon">{getIcon()}</div>
      <div className="azals-timeline__content">
        <div className="azals-timeline__header">
          <span className="azals-timeline__action">{entry.action}</span>
          <span className="azals-timeline__time text-muted">
            {formatDateTime(entry.timestamp)}
          </span>
        </div>
        {entry.user_name && (
          <div className="azals-timeline__user text-sm">
            <User size={12} className="mr-1" />
            {entry.user_name}
          </div>
        )}
        {entry.details && (
          <p className="azals-timeline__details text-muted text-sm mt-1">
            {entry.details}
          </p>
        )}
        {entry.old_value && entry.new_value && (
          <div className="azals-timeline__change text-sm mt-1">
            <span className="text-danger line-through">{entry.old_value}</span>
            <ArrowRight size={12} className="mx-2" />
            <span className="text-success">{entry.new_value}</span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Ligne de maintenance
 */
const MaintenanceRow: React.FC<{ log: MaintenanceLog }> = ({ log }) => {
  const typeConfig = MAINTENANCE_TYPE_CONFIG[log.type] || MAINTENANCE_TYPE_CONFIG.other;

  return (
    <tr>
      <td>{formatDate(log.date)}</td>
      <td>
        <span className={`azals-badge azals-badge--${typeConfig.color} azals-badge--sm`}>
          {typeConfig.label}
        </span>
      </td>
      <td>{formatKilometers(log.mileage_at_service)}</td>
      <td className="text-right font-medium">{formatCurrency(log.cost)}</td>
    </tr>
  );
};

/**
 * Ligne de deplacement
 */
const MileageRow: React.FC<{ log: MileageLog }> = ({ log }) => {
  return (
    <tr>
      <td>{formatDate(log.date)}</td>
      <td>
        {log.affaire_numero ? (
          <span className="text-primary">{log.affaire_numero}</span>
        ) : (
          <span className="text-muted">{log.motif.substring(0, 30)}</span>
        )}
      </td>
      <td className="text-right">{log.km_total} km</td>
      <td className="text-right font-medium">{formatCurrency(log.cost_total)}</td>
    </tr>
  );
};

/**
 * Generer l'historique a partir des donnees du vehicule
 */
function generateHistoryFromVehicle(vehicle: Vehicule): VehicleHistoryEntry[] {
  const history: VehicleHistoryEntry[] = [];

  // Creation/acquisition
  history.push({
    id: 'created',
    timestamp: vehicle.created_at,
    action: 'Vehicule enregistre',
    details: `${vehicle.marque} ${vehicle.modele} - ${vehicle.immatriculation}`,
  });

  // Date mise en service
  if (vehicle.date_mise_service) {
    history.push({
      id: 'service',
      timestamp: vehicle.date_mise_service,
      action: 'Mise en service',
      details: `Kilometrage initial: ${vehicle.kilometrage_actuel || 0} km`,
    });
  }

  // Maintenances
  (vehicle.maintenance_logs || []).forEach((log, index) => {
    history.push({
      id: `maintenance-${index}`,
      timestamp: log.date,
      action: `Maintenance ${MAINTENANCE_TYPE_CONFIG[log.type]?.label || log.type}`,
      details: `${log.description} - ${formatCurrency(log.cost)}`,
      user_name: log.provider,
    });
  });

  // Derniere revision
  if (vehicle.date_derniere_revision) {
    const alreadyHasEntry = history.some(h =>
      h.timestamp === vehicle.date_derniere_revision && h.action.includes('Maintenance')
    );
    if (!alreadyHasEntry) {
      history.push({
        id: 'last-revision',
        timestamp: vehicle.date_derniere_revision,
        action: 'Derniere revision effectuee',
        details: `Kilometrage: ${formatKilometers(vehicle.kilometrage_actuel)}`,
      });
    }
  }

  // Deplacements significatifs (>100km)
  (vehicle.mileage_logs || [])
    .filter(log => log.km_total > 100)
    .slice(0, 5)
    .forEach((log, index) => {
      history.push({
        id: `mileage-${index}`,
        timestamp: log.date,
        action: 'Deplacement enregistre',
        details: `${log.motif} - ${log.km_total} km`,
        user_name: log.employe_nom,
      });
    });

  // Derniere modification
  if (vehicle.updated_at && vehicle.updated_at !== vehicle.created_at) {
    history.push({
      id: 'updated',
      timestamp: vehicle.updated_at,
      action: 'Fiche vehicule modifiee',
      details: 'Mise a jour des informations',
    });
  }

  // Historique fourni par l'API
  if (vehicle.history && vehicle.history.length > 0) {
    history.push(...vehicle.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default VehicleHistoryTab;
