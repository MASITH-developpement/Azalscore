/**
 * AZALSCORE Module - Marketplace - Seller History Tab
 * Onglet historique du vendeur
 */

import React from 'react';
import {
  Clock, User, CheckCircle2, XCircle, AlertTriangle,
  UserPlus, UserCheck, UserX, ArrowRight
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Seller, SellerHistoryEntry } from '../types';
import { formatDateTime, SELLER_STATUS_CONFIG } from '../types';

/**
 * SellerHistoryTab - Historique
 */
export const SellerHistoryTab: React.FC<TabContentProps<Seller>> = ({ data: seller }) => {
  const history = generateHistoryFromSeller(seller);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique du vendeur" icon={<Clock size={18} />}>
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
                      <span className={`azals-badge azals-badge--${SELLER_STATUS_CONFIG[item.old_status as keyof typeof SELLER_STATUS_CONFIG]?.color || 'gray'} text-xs`}>
                        {SELLER_STATUS_CONFIG[item.old_status as keyof typeof SELLER_STATUS_CONFIG]?.label || item.old_status}
                      </span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className={`azals-badge azals-badge--${SELLER_STATUS_CONFIG[item.new_status as keyof typeof SELLER_STATUS_CONFIG]?.color || 'gray'} text-xs`}>
                        {SELLER_STATUS_CONFIG[item.new_status as keyof typeof SELLER_STATUS_CONFIG]?.label || item.new_status}
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
  entry: SellerHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntryComponent: React.FC<HistoryEntryComponentProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('inscri') || action.includes('cree') || action.includes('creation')) {
      return <UserPlus size={16} className="text-blue-500" />;
    }
    if (action.includes('valid') || action.includes('approu') || action.includes('activ')) {
      return <UserCheck size={16} className="text-green-500" />;
    }
    if (action.includes('suspen') || action.includes('refus') || action.includes('reject')) {
      return <UserX size={16} className="text-red-500" />;
    }
    if (action.includes('verif')) {
      return <CheckCircle2 size={16} className="text-green-500" />;
    }
    if (action.includes('modif') || action.includes('mise a jour')) {
      return <Clock size={16} className="text-blue-500" />;
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
            <span className={`azals-badge azals-badge--${SELLER_STATUS_CONFIG[entry.old_status as keyof typeof SELLER_STATUS_CONFIG]?.color || 'gray'}`}>
              {SELLER_STATUS_CONFIG[entry.old_status as keyof typeof SELLER_STATUS_CONFIG]?.label || entry.old_status}
            </span>
            <ArrowRight size={12} className="mx-2" />
            <span className={`azals-badge azals-badge--${SELLER_STATUS_CONFIG[entry.new_status as keyof typeof SELLER_STATUS_CONFIG]?.color || 'gray'}`}>
              {SELLER_STATUS_CONFIG[entry.new_status as keyof typeof SELLER_STATUS_CONFIG]?.label || entry.new_status}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Generer l'historique a partir des donnees du vendeur
 */
function generateHistoryFromSeller(seller: Seller): SellerHistoryEntry[] {
  const history: SellerHistoryEntry[] = [];

  // Inscription
  history.push({
    id: 'created',
    timestamp: seller.joined_at || seller.created_at,
    action: 'Inscription vendeur',
    user_name: seller.name,
    details: `Code: ${seller.code}`,
  });

  // Verification
  if (seller.is_verified && seller.verified_at) {
    history.push({
      id: 'verified',
      timestamp: seller.verified_at,
      action: 'Compte verifie',
      details: 'Le compte vendeur a ete verifie',
    });
  }

  // Statut actuel si different de PENDING
  if (seller.status === 'ACTIVE') {
    history.push({
      id: 'activated',
      timestamp: seller.updated_at,
      action: 'Compte active',
      old_status: 'PENDING',
      new_status: 'ACTIVE',
      details: 'Le vendeur a ete approuve',
    });
  } else if (seller.status === 'SUSPENDED') {
    history.push({
      id: 'suspended',
      timestamp: seller.updated_at,
      action: 'Compte suspendu',
      old_status: 'ACTIVE',
      new_status: 'SUSPENDED',
      details: 'Le compte vendeur a ete suspendu',
    });
  } else if (seller.status === 'REJECTED') {
    history.push({
      id: 'rejected',
      timestamp: seller.updated_at,
      action: 'Inscription refusee',
      old_status: 'PENDING',
      new_status: 'REJECTED',
      details: 'La demande d\'inscription a ete refusee',
    });
  }

  // Historique fourni par l'API
  if (seller.history && seller.history.length > 0) {
    history.push(...seller.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

export default SellerHistoryTab;
