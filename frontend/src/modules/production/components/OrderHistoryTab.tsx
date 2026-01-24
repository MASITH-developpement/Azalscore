/**
 * AZALSCORE Module - Production - Order History Tab
 * Onglet historique de l'ordre de fabrication
 */

import React from 'react';
import {
  Clock, User, Edit, Play, Pause, CheckCircle,
  FileText, ArrowRight, Settings, AlertTriangle, XCircle
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { ProductionOrder, OrderHistoryEntry } from '../types';
import { formatDateTime, ORDER_STATUS_CONFIG } from '../types';

/**
 * OrderHistoryTab - Historique de l'ordre de fabrication
 */
export const OrderHistoryTab: React.FC<TabContentProps<ProductionOrder>> = ({ data: order }) => {
  // Generer l'historique combine
  const history = generateHistoryFromOrder(order);

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
  entry: OrderHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation')) {
      return <FileText size={16} className="text-primary" />;
    }
    if (action.includes('confirme')) {
      return <CheckCircle size={16} className="text-blue" />;
    }
    if (action.includes('demarre') || action.includes('debut')) {
      return <Play size={16} className="text-green" />;
    }
    if (action.includes('pause')) {
      return <Pause size={16} className="text-orange" />;
    }
    if (action.includes('termine') || action.includes('complete')) {
      return <CheckCircle size={16} className="text-success" />;
    }
    if (action.includes('annule')) {
      return <XCircle size={16} className="text-danger" />;
    }
    if (action.includes('operation') || action.includes('travail')) {
      return <Settings size={16} className="text-purple" />;
    }
    if (action.includes('modifie') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    if (action.includes('alerte') || action.includes('retard')) {
      return <AlertTriangle size={16} className="text-danger" />;
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
 * Generer l'historique a partir des donnees de l'ordre
 */
function generateHistoryFromOrder(order: ProductionOrder): OrderHistoryEntry[] {
  const history: OrderHistoryEntry[] = [];

  // Creation
  history.push({
    id: 'created',
    timestamp: order.created_at,
    action: 'Ordre de fabrication cree',
    user_name: order.created_by,
    details: `Numero: ${order.number}, Produit: ${order.product_name || order.product_code}`,
  });

  // Confirmation
  if (order.status !== 'DRAFT') {
    history.push({
      id: 'confirmed',
      timestamp: order.updated_at || order.created_at,
      action: 'Ordre confirme',
      details: `Quantite: ${order.quantity_planned} ${order.unit || 'unites'}`,
    });
  }

  // Demarrage
  if (order.actual_start) {
    history.push({
      id: 'started',
      timestamp: order.actual_start,
      action: 'Production demarree',
    });
  }

  // Operations terminees
  const doneOperations = order.work_orders?.filter(wo => wo.status === 'DONE') || [];
  doneOperations.forEach((wo, index) => {
    if (wo.end_time) {
      history.push({
        id: `wo-done-${index}`,
        timestamp: wo.end_time,
        action: 'Operation terminee',
        user_name: wo.operator_name,
        details: wo.name,
      });
    }
  });

  // Fin
  if (order.actual_end) {
    history.push({
      id: 'completed',
      timestamp: order.actual_end,
      action: 'Production terminee',
      details: `Quantite produite: ${order.quantity_produced} ${order.unit || 'unites'}`,
    });
  }

  // Derniere modification
  if (order.updated_at && order.updated_at !== order.created_at && order.status !== 'DONE') {
    history.push({
      id: 'updated',
      timestamp: order.updated_at,
      action: 'Ordre modifie',
      details: 'Mise a jour des informations',
    });
  }

  // Historique fourni par l'API
  if (order.history && order.history.length > 0) {
    history.push(...order.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default OrderHistoryTab;
