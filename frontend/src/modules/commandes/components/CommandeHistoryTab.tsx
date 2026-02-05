/**
 * AZALSCORE Module - COMMANDES - History Tab
 * Onglet historique et audit de la commande
 */

import React from 'react';
import {
  Clock, User, Edit, Check, Send, X, Plus,
  FileText, ArrowRight, Truck, Package
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Commande, CommandeHistoryEntry } from '../types';
import { STATUS_CONFIG } from '../types';
import { formatDateTime } from '@/utils/formatters';

/**
 * CommandeHistoryTab - Historique et audit trail de la commande
 */
export const CommandeHistoryTab: React.FC<TabContentProps<Commande>> = ({ data: commande }) => {
  // Générer l'historique à partir des données de la commande
  const history = generateHistoryFromCommande(commande);

  return (
    <div className="azals-std-tab-content">
      <Card title="Historique des modifications" icon={<Clock size={18} />}>
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

      {/* Détail des changements (ERP only) */}
      <Card
        title="Journal d'audit détaillé"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <table className="azals-table azals-table--simple azals-table--compact">
          <thead>
            <tr>
              <th>Date/Heure</th>
              <th>Action</th>
              <th>Utilisateur</th>
              <th>Détails</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry) => (
              <tr key={entry.id}>
                <td className="text-muted text-sm">{formatDateTime(entry.timestamp)}</td>
                <td>{entry.action}</td>
                <td>{entry.user_name || 'Système'}</td>
                <td className="text-muted text-sm">
                  {entry.details || '-'}
                  {entry.old_value && entry.new_value && (
                    <span className="ml-2">
                      <span className="text-danger">{entry.old_value}</span>
                      <ArrowRight size={12} className="mx-1" />
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
 * Composant entrée de timeline
 */
interface HistoryEntryProps {
  entry: CommandeHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('créé') || action.includes('création')) {
      return <Plus size={16} className="text-success" />;
    }
    if (action.includes('validé') || action.includes('validation')) {
      return <Check size={16} className="text-primary" />;
    }
    if (action.includes('livré') || action.includes('livraison')) {
      return <Truck size={16} className="text-green" />;
    }
    if (action.includes('facturé') || action.includes('facture')) {
      return <FileText size={16} className="text-purple" />;
    }
    if (action.includes('modifié') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    if (action.includes('annulé')) {
      return <X size={16} className="text-danger" />;
    }
    if (action.includes('affaire')) {
      return <Package size={16} className="text-blue" />;
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
 * Générer l'historique à partir des données de la commande
 */
function generateHistoryFromCommande(commande: Commande): CommandeHistoryEntry[] {
  const history: CommandeHistoryEntry[] = [];

  // Création
  history.push({
    id: 'created',
    timestamp: commande.created_at,
    action: 'Commande créée',
    user_name: commande.created_by,
    details: `Numéro: ${commande.number}${commande.parent_number ? ` (depuis devis ${commande.parent_number})` : ''}`,
  });

  // Validation
  if (commande.validated_at) {
    history.push({
      id: 'validated',
      timestamp: commande.validated_at,
      action: 'Commande validée',
      user_name: commande.validated_by,
      old_value: STATUS_CONFIG.DRAFT.label,
      new_value: STATUS_CONFIG.VALIDATED.label,
    });
  }

  // Livraison
  if (commande.status === 'DELIVERED' || commande.status === 'INVOICED') {
    history.push({
      id: 'delivered',
      timestamp: commande.delivered_at || commande.updated_at,
      action: 'Commande livrée',
      details: commande.tracking_number ? `N° suivi: ${commande.tracking_number}` : undefined,
      old_value: STATUS_CONFIG.VALIDATED.label,
      new_value: STATUS_CONFIG.DELIVERED.label,
    });
  }

  // Facturation
  if (commande.status === 'INVOICED') {
    history.push({
      id: 'invoiced',
      timestamp: commande.updated_at,
      action: 'Commande facturée',
      old_value: STATUS_CONFIG.DELIVERED.label,
      new_value: STATUS_CONFIG.INVOICED.label,
    });
  }

  // Annulation
  if (commande.status === 'CANCELLED') {
    history.push({
      id: 'cancelled',
      timestamp: commande.updated_at,
      action: 'Commande annulée',
      new_value: STATUS_CONFIG.CANCELLED.label,
    });
  }

  // Trier par date décroissante (plus récent en premier)
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default CommandeHistoryTab;
