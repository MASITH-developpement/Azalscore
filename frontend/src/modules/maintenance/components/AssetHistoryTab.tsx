/**
 * AZALSCORE Module - Maintenance - Asset History Tab
 * Onglet historique de l'equipement
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  Wrench, CheckCircle, XCircle, AlertTriangle, Settings
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Asset, AssetHistoryEntry } from '../types';
import { formatDateTime, formatDate } from '@/utils/formatters';
import {
  ASSET_STATUS_CONFIG, ORDER_STATUS_CONFIG
} from '../types';

/**
 * AssetHistoryTab - Historique de l'equipement
 */
export const AssetHistoryTab: React.FC<TabContentProps<Asset>> = ({ data: asset }) => {
  // Generer l'historique combine
  const history = generateHistoryFromAsset(asset);

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
  entry: AssetHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation') || action.includes('acquisition')) {
      return <CheckCircle size={16} className="text-success" />;
    }
    if (action.includes('maintenance') || action.includes('ordre')) {
      return <Wrench size={16} className="text-blue-500" />;
    }
    if (action.includes('panne') || action.includes('defaillance')) {
      return <AlertTriangle size={16} className="text-danger" />;
    }
    if (action.includes('hors service') || action.includes('arret')) {
      return <XCircle size={16} className="text-danger" />;
    }
    if (action.includes('remis en service') || action.includes('operationnel')) {
      return <CheckCircle size={16} className="text-success" />;
    }
    if (action.includes('modifie') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    if (action.includes('configure') || action.includes('parametr')) {
      return <Settings size={16} className="text-purple-500" />;
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
 * Generer l'historique a partir des donnees de l'equipement
 */
function generateHistoryFromAsset(asset: Asset): AssetHistoryEntry[] {
  const history: AssetHistoryEntry[] = [];

  // Creation/acquisition
  history.push({
    id: 'created',
    timestamp: asset.created_at,
    action: 'Equipement cree',
    user_name: asset.created_by,
    details: `Code: ${asset.code}, Type: ${asset.type}`,
  });

  // Date d'achat
  if (asset.purchase_date) {
    history.push({
      id: 'purchased',
      timestamp: asset.purchase_date,
      action: 'Acquisition',
      details: `Fabricant: ${asset.manufacturer || 'N/A'}, Modele: ${asset.model || 'N/A'}`,
    });
  }

  // Ordres de maintenance completes
  const completedOrders = asset.maintenance_orders?.filter(o => o.status === 'COMPLETED') || [];
  completedOrders.forEach((order, index) => {
    if (order.actual_end_date) {
      history.push({
        id: `order-${index}`,
        timestamp: order.actual_end_date,
        action: `Maintenance ${order.type.toLowerCase()} terminee`,
        user_name: order.assigned_to_name,
        details: `Ordre ${order.number}: ${order.description.substring(0, 50)}${order.description.length > 50 ? '...' : ''}`,
      });
    }
  });

  // Derniere maintenance
  if (asset.last_maintenance_date) {
    const alreadyHasEntry = history.some(h =>
      h.timestamp === asset.last_maintenance_date && h.action.includes('maintenance')
    );
    if (!alreadyHasEntry) {
      history.push({
        id: 'last-maintenance',
        timestamp: asset.last_maintenance_date,
        action: 'Derniere maintenance effectuee',
        details: 'Maintenance preventive ou corrective',
      });
    }
  }

  // Derniere modification
  if (asset.updated_at && asset.updated_at !== asset.created_at) {
    history.push({
      id: 'updated',
      timestamp: asset.updated_at,
      action: 'Fiche equipement modifiee',
      details: 'Mise a jour des informations',
    });
  }

  // Historique fourni par l'API
  if (asset.history && asset.history.length > 0) {
    history.push(...asset.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default AssetHistoryTab;
