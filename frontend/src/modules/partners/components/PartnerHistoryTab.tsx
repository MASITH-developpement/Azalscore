/**
 * AZALSCORE Module - Partners - History Tab
 * Onglet historique du partenaire
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  UserPlus, Mail, Phone, ShoppingCart, Receipt
} from 'lucide-react';
import { Card } from '@ui/layout';
import { formatDateTime } from '@/utils/formatters';
import type { Partner, PartnerHistoryEntry, Client } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * PartnerHistoryTab - Historique
 */
export const PartnerHistoryTab: React.FC<TabContentProps<Partner>> = ({ data: partner }) => {
  const history = generateHistoryFromPartner(partner);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique des interactions" icon={<Clock size={18} />}>
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

      {/* Journal d'audit (ERP only) */}
      <Card
        title="Journal d'audit"
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
  entry: PartnerHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation')) {
      return <UserPlus size={16} className="text-green-500" />;
    }
    if (action.includes('email') || action.includes('mail')) {
      return <Mail size={16} className="text-blue-500" />;
    }
    if (action.includes('appel') || action.includes('tel')) {
      return <Phone size={16} className="text-blue-500" />;
    }
    if (action.includes('commande') || action.includes('devis')) {
      return <ShoppingCart size={16} className="text-purple-500" />;
    }
    if (action.includes('facture') || action.includes('paiement')) {
      return <Receipt size={16} className="text-green-500" />;
    }
    if (action.includes('modif')) {
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
 * Generer l'historique a partir des donnees du partenaire
 */
function generateHistoryFromPartner(partner: Partner): PartnerHistoryEntry[] {
  const history: PartnerHistoryEntry[] = [];

  // Creation du partenaire
  history.push({
    id: 'created',
    timestamp: partner.created_at,
    action: 'Fiche creee',
    details: `${partner.type === 'client' ? 'Client' : partner.type === 'supplier' ? 'Fournisseur' : 'Contact'}: ${partner.name}`,
  });

  // Derniere modification
  if (partner.updated_at && partner.updated_at !== partner.created_at) {
    history.push({
      id: 'updated',
      timestamp: partner.updated_at,
      action: 'Fiche modifiee',
      details: 'Mise a jour des informations',
    });
  }

  // Stats - premiere commande
  if (partner.type === 'client') {
    const client = partner as Client;
    if (client.first_order_date) {
      history.push({
        id: 'first-order',
        timestamp: client.first_order_date,
        action: 'Premiere commande',
        details: 'Le client a passe sa premiere commande',
      });
    }
    if (client.last_order_date && client.last_order_date !== client.first_order_date) {
      history.push({
        id: 'last-order',
        timestamp: client.last_order_date,
        action: 'Derniere commande',
        details: 'Commande la plus recente',
      });
    }
  }

  // Historique fourni par l'API
  if (partner.history && partner.history.length > 0) {
    history.push(...partner.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default PartnerHistoryTab;
