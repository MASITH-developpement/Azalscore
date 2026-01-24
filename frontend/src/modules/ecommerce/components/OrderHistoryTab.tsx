/**
 * AZALSCORE Module - E-commerce - Order History Tab
 * Onglet historique de la commande
 */

import React from 'react';
import { Clock, User, CheckCircle2, Truck, CreditCard, XCircle, ArrowRight, Package } from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Order, OrderHistoryEntry } from '../types';
import { formatDateTime, ORDER_STATUS_CONFIG } from '../types';

/**
 * OrderHistoryTab - Historique
 */
export const OrderHistoryTab: React.FC<TabContentProps<Order>> = ({ data: order }) => {
  const history = generateHistoryFromOrder(order);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique de la commande" icon={<Clock size={18} />}>
        {history.length > 0 ? (
          <div className="azals-timeline">
            {history.map((item, index) => (
              <HistoryEntryComponent
                key={item.id}
                entry={item}
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

      {/* Journal d'audit (ERP only) */}
      <Card title="Journal d'audit" icon={<Clock size={18} />} className="mt-4 azals-std-field--secondary">
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
            {history.map((item) => (
              <tr key={item.id}>
                <td className="text-muted text-sm">{formatDateTime(item.timestamp)}</td>
                <td>{item.action}</td>
                <td>{item.user_name || 'Systeme'}</td>
                <td className="text-muted text-sm">
                  {item.details || '-'}
                  {item.old_status && item.new_status && (
                    <span className="ml-2">
                      <span className={`azals-badge azals-badge--${ORDER_STATUS_CONFIG[item.old_status as keyof typeof ORDER_STATUS_CONFIG]?.color || 'gray'} text-xs`}>
                        {ORDER_STATUS_CONFIG[item.old_status as keyof typeof ORDER_STATUS_CONFIG]?.label || item.old_status}
                      </span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className={`azals-badge azals-badge--${ORDER_STATUS_CONFIG[item.new_status as keyof typeof ORDER_STATUS_CONFIG]?.color || 'gray'} text-xs`}>
                        {ORDER_STATUS_CONFIG[item.new_status as keyof typeof ORDER_STATUS_CONFIG]?.label || item.new_status}
                      </span>
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
interface HistoryEntryComponentProps {
  entry: OrderHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntryComponent: React.FC<HistoryEntryComponentProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation') || action.includes('passee')) {
      return <Package size={16} className="text-blue-500" />;
    }
    if (action.includes('confirm')) {
      return <CheckCircle2 size={16} className="text-blue-500" />;
    }
    if (action.includes('pay') || action.includes('paiement')) {
      return <CreditCard size={16} className="text-green-500" />;
    }
    if (action.includes('expedi') || action.includes('ship')) {
      return <Truck size={16} className="text-purple-500" />;
    }
    if (action.includes('livr') || action.includes('deliver')) {
      return <CheckCircle2 size={16} className="text-green-500" />;
    }
    if (action.includes('annul') || action.includes('cancel')) {
      return <XCircle size={16} className="text-red-500" />;
    }
    return <Clock size={16} className="text-muted" />;
  };

  return (
    <div className={`azals-timeline__entry ${isFirst ? 'azals-timeline__entry--first' : ''} ${isLast ? 'azals-timeline__entry--last' : ''}`}>
      <div className="azals-timeline__icon">{getIcon()}</div>
      <div className="azals-timeline__content">
        <div className="azals-timeline__header">
          <span className="azals-timeline__action">{entry.action}</span>
          <span className="azals-timeline__time text-muted">{formatDateTime(entry.timestamp)}</span>
        </div>
        {entry.user_name && (
          <div className="azals-timeline__user text-sm">
            <User size={12} className="mr-1" />
            {entry.user_name}
          </div>
        )}
        {entry.details && (
          <p className="azals-timeline__details text-muted text-sm mt-1">{entry.details}</p>
        )}
        {entry.old_status && entry.new_status && (
          <div className="azals-timeline__change text-sm mt-1">
            <span className={`azals-badge azals-badge--${ORDER_STATUS_CONFIG[entry.old_status as keyof typeof ORDER_STATUS_CONFIG]?.color || 'gray'}`}>
              {ORDER_STATUS_CONFIG[entry.old_status as keyof typeof ORDER_STATUS_CONFIG]?.label || entry.old_status}
            </span>
            <ArrowRight size={12} className="mx-2" />
            <span className={`azals-badge azals-badge--${ORDER_STATUS_CONFIG[entry.new_status as keyof typeof ORDER_STATUS_CONFIG]?.color || 'gray'}`}>
              {ORDER_STATUS_CONFIG[entry.new_status as keyof typeof ORDER_STATUS_CONFIG]?.label || entry.new_status}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Generer l'historique a partir des donnees de la commande
 */
function generateHistoryFromOrder(order: Order): OrderHistoryEntry[] {
  const history: OrderHistoryEntry[] = [];

  // Creation
  history.push({
    id: 'created',
    timestamp: order.created_at,
    action: 'Commande passee',
    user_name: order.created_by_name || 'Client',
    details: `Numero: ${order.number}`,
  });

  // Paiement
  if (order.payment_status === 'PAID') {
    history.push({
      id: 'paid',
      timestamp: order.updated_at,
      action: 'Paiement recu',
      details: order.payment_method || 'Paiement effectue',
    });
  }

  // Expedition
  if (order.shipped_at) {
    history.push({
      id: 'shipped',
      timestamp: order.shipped_at,
      action: 'Commande expediee',
      details: order.tracking_number ? `N° suivi: ${order.tracking_number}` : 'Colis expedie',
    });
  }

  // Livraison
  if (order.delivered_at) {
    history.push({
      id: 'delivered',
      timestamp: order.delivered_at,
      action: 'Commande livree',
      details: 'Le colis a ete livre',
    });
  }

  // Annulation
  if (order.status === 'CANCELLED') {
    history.push({
      id: 'cancelled',
      timestamp: order.updated_at,
      action: 'Commande annulee',
      details: 'La commande a ete annulee',
    });
  }

  // Remboursement
  if (order.status === 'REFUNDED') {
    history.push({
      id: 'refunded',
      timestamp: order.updated_at,
      action: 'Commande remboursee',
      details: 'Le remboursement a ete effectue',
    });
  }

  // Historique fourni par l'API
  if (order.history && order.history.length > 0) {
    history.push(...order.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

export default OrderHistoryTab;
