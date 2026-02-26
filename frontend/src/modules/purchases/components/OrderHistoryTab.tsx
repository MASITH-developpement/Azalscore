/**
 * AZALSCORE Module - Purchases - Order History Tab
 * Onglet historique de la commande
 */

import React from 'react';
import { Clock, User, Edit, Plus, CheckCircle2, XCircle, Send, Package, ArrowRight } from 'lucide-react';
import { Card } from '@ui/layout';
import { formatDateTime } from '@/utils/formatters';
import type { PurchaseOrder, PurchaseHistoryEntry } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * OrderHistoryTab - Historique
 */
export const OrderHistoryTab: React.FC<TabContentProps<PurchaseOrder>> = ({ data: order }) => {
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
                  {item.old_value && item.new_value && (
                    <span className="ml-2">
                      <span className="text-danger">{item.old_value}</span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className="text-success">{item.new_value}</span>
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
  entry: PurchaseHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntryComponent: React.FC<HistoryEntryComponentProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation')) {
      return <Plus size={16} className="text-green-500" />;
    }
    if (action.includes('valid')) {
      return <CheckCircle2 size={16} className="text-blue-500" />;
    }
    if (action.includes('envoy') || action.includes('sent')) {
      return <Send size={16} className="text-blue-500" />;
    }
    if (action.includes('confirm')) {
      return <CheckCircle2 size={16} className="text-orange-500" />;
    }
    if (action.includes('recu') || action.includes('receiv')) {
      return <Package size={16} className="text-green-500" />;
    }
    if (action.includes('annul')) {
      return <XCircle size={16} className="text-red-500" />;
    }
    if (action.includes('modif')) {
      return <Edit size={16} className="text-orange-500" />;
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
 * Generer l'historique a partir des donnees de la commande
 */
function generateHistoryFromOrder(order: PurchaseOrder): PurchaseHistoryEntry[] {
  const history: PurchaseHistoryEntry[] = [];

  // Creation
  history.push({
    id: 'created',
    timestamp: order.created_at,
    action: 'Commande creee',
    user_name: order.created_by_name,
    details: `Numero: ${order.number}`,
  });

  // Validation
  if (order.validated_at) {
    history.push({
      id: 'validated',
      timestamp: order.validated_at,
      action: 'Commande validee',
      user_name: order.validated_by_name,
      details: 'La commande a ete validee',
    });
  }

  // Envoi
  if (order.sent_at) {
    history.push({
      id: 'sent',
      timestamp: order.sent_at,
      action: 'Commande envoyee',
      details: 'La commande a ete envoyee au fournisseur',
    });
  }

  // Confirmation
  if (order.confirmed_at) {
    history.push({
      id: 'confirmed',
      timestamp: order.confirmed_at,
      action: 'Commande confirmee',
      details: 'Le fournisseur a confirme la commande',
    });
  }

  // Reception
  if (order.received_at) {
    history.push({
      id: 'received',
      timestamp: order.received_at,
      action: 'Commande recue',
      details: 'La commande a ete receptionnee',
    });
  }

  // Derniere modification
  if (order.updated_at !== order.created_at && !order.validated_at) {
    history.push({
      id: 'updated',
      timestamp: order.updated_at,
      action: 'Commande modifiee',
      details: 'Mise a jour des informations',
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
