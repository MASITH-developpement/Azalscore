/**
 * AZALSCORE Module - POS - Session History Tab
 * Onglet historique de la session
 */

import React from 'react';
import {
  Clock, User, Play, CheckCircle2, XCircle,
  PauseCircle, ArrowRight
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { POSSession, SessionHistoryEntry } from '../types';
import { formatDateTime, SESSION_STATUS_CONFIG } from '../types';

/**
 * SessionHistoryTab - Historique de la session
 */
export const SessionHistoryTab: React.FC<TabContentProps<POSSession>> = ({ data: session }) => {
  const history = generateHistoryFromSession(session);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique de la session" icon={<Clock size={18} />}>
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

      {/* Journal detaille (ERP only) */}
      <Card title="Journal d'activite" icon={<Clock size={18} />} className="mt-4 azals-std-field--secondary">
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
                      <span className={`azals-badge azals-badge--${SESSION_STATUS_CONFIG[item.old_status as keyof typeof SESSION_STATUS_CONFIG]?.color || 'gray'} text-xs`}>
                        {SESSION_STATUS_CONFIG[item.old_status as keyof typeof SESSION_STATUS_CONFIG]?.label || item.old_status}
                      </span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className={`azals-badge azals-badge--${SESSION_STATUS_CONFIG[item.new_status as keyof typeof SESSION_STATUS_CONFIG]?.color || 'gray'} text-xs`}>
                        {SESSION_STATUS_CONFIG[item.new_status as keyof typeof SESSION_STATUS_CONFIG]?.label || item.new_status}
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
  entry: SessionHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntryComponent: React.FC<HistoryEntryComponentProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('ouvert') || action.includes('debut') || action.includes('demarre')) {
      return <Play size={16} className="text-green-500" />;
    }
    if (action.includes('ferme') || action.includes('cloture') || action.includes('termine')) {
      return <CheckCircle2 size={16} className="text-blue-500" />;
    }
    if (action.includes('suspend')) {
      return <PauseCircle size={16} className="text-orange-500" />;
    }
    if (action.includes('annul')) {
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
            <span className={`azals-badge azals-badge--${SESSION_STATUS_CONFIG[entry.old_status as keyof typeof SESSION_STATUS_CONFIG]?.color || 'gray'}`}>
              {SESSION_STATUS_CONFIG[entry.old_status as keyof typeof SESSION_STATUS_CONFIG]?.label || entry.old_status}
            </span>
            <ArrowRight size={12} className="mx-2" />
            <span className={`azals-badge azals-badge--${SESSION_STATUS_CONFIG[entry.new_status as keyof typeof SESSION_STATUS_CONFIG]?.color || 'gray'}`}>
              {SESSION_STATUS_CONFIG[entry.new_status as keyof typeof SESSION_STATUS_CONFIG]?.label || entry.new_status}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Generer l'historique a partir des donnees de la session
 */
function generateHistoryFromSession(session: POSSession): SessionHistoryEntry[] {
  const history: SessionHistoryEntry[] = [];

  // Ouverture
  history.push({
    id: 'opened',
    timestamp: session.opened_at,
    action: 'Session ouverte',
    user_name: session.cashier_name,
    details: `Fond de caisse: ${new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(session.opening_balance)}`,
  });

  // Mouvements de caisse
  if (session.cash_movements && session.cash_movements.length > 0) {
    session.cash_movements.forEach((movement, index) => {
      let action = '';
      switch (movement.type) {
        case 'DEPOSIT':
          action = 'Depot de caisse';
          break;
        case 'WITHDRAWAL':
          action = 'Retrait de caisse';
          break;
        case 'ADJUSTMENT':
          action = 'Ajustement de caisse';
          break;
      }
      history.push({
        id: `movement-${index}`,
        timestamp: movement.performed_at,
        action,
        user_name: movement.performed_by,
        details: `${movement.reason} - ${new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(movement.amount)}`,
      });
    });
  }

  // Suspension
  if (session.status === 'SUSPENDED') {
    history.push({
      id: 'suspended',
      timestamp: session.updated_at,
      action: 'Session suspendue',
      old_status: 'OPEN',
      new_status: 'SUSPENDED',
    });
  }

  // Fermeture
  if (session.closed_at) {
    history.push({
      id: 'closed',
      timestamp: session.closed_at,
      action: 'Session fermee',
      user_name: session.cashier_name,
      details: session.closing_balance !== undefined
        ? `Solde de cloture: ${new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(session.closing_balance)}`
        : undefined,
      old_status: 'OPEN',
      new_status: 'CLOSED',
    });
  }

  // Historique fourni par l'API
  if (session.history && session.history.length > 0) {
    history.push(...session.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

export default SessionHistoryTab;
