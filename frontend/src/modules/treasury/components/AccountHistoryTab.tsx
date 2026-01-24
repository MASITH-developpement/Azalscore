/**
 * AZALSCORE Module - Treasury - Account History Tab
 * Onglet historique du compte bancaire
 */

import React from 'react';
import {
  Clock, User, CheckCircle2, RefreshCw, Plus, Edit, ArrowRight
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { BankAccount, AccountHistoryEntry } from '../types';
import { formatDateTime, formatCurrency } from '../types';

/**
 * AccountHistoryTab - Historique
 */
export const AccountHistoryTab: React.FC<TabContentProps<BankAccount>> = ({ data: account }) => {
  const history = generateHistoryFromAccount(account);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique du compte" icon={<Clock size={18} />}>
        {history.length > 0 ? (
          <div className="azals-timeline">
            {history.map((item, index) => (
              <HistoryEntryComponent
                key={item.id}
                entry={item}
                isFirst={index === 0}
                isLast={index === history.length - 1}
                currency={account.currency}
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
                  {item.old_balance !== undefined && item.new_balance !== undefined && (
                    <span className="ml-2">
                      <span className="font-mono">
                        {formatCurrency(item.old_balance, account.currency)}
                      </span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className="font-mono">
                        {formatCurrency(item.new_balance, account.currency)}
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
  entry: AccountHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
  currency: string;
}

const HistoryEntryComponent: React.FC<HistoryEntryComponentProps> = ({ entry, isFirst, isLast, currency }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation') || action.includes('ouvert')) {
      return <Plus size={16} className="text-blue-500" />;
    }
    if (action.includes('sync') || action.includes('import')) {
      return <RefreshCw size={16} className="text-purple-500" />;
    }
    if (action.includes('rapproch') || action.includes('reconcil')) {
      return <CheckCircle2 size={16} className="text-green-500" />;
    }
    if (action.includes('modif') || action.includes('mise a jour')) {
      return <Edit size={16} className="text-blue-500" />;
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
        {entry.old_balance !== undefined && entry.new_balance !== undefined && (
          <div className="azals-timeline__change text-sm mt-1">
            <span className="font-mono">{formatCurrency(entry.old_balance, currency)}</span>
            <ArrowRight size={12} className="mx-2" />
            <span className={`font-mono ${entry.new_balance > entry.old_balance ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(entry.new_balance, currency)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Generer l'historique a partir des donnees du compte
 */
function generateHistoryFromAccount(account: BankAccount): AccountHistoryEntry[] {
  const history: AccountHistoryEntry[] = [];

  // Creation
  history.push({
    id: 'created',
    timestamp: account.created_at,
    action: 'Compte cree',
    user_name: account.created_by_name,
    details: `${account.name} - ${account.bank_name}`,
  });

  // Derniere synchronisation
  if (account.last_sync) {
    history.push({
      id: 'last-sync',
      timestamp: account.last_sync,
      action: 'Synchronisation bancaire',
      details: 'Import des transactions bancaires',
    });
  }

  // Historique fourni par l'API
  if (account.history && account.history.length > 0) {
    history.push(...account.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

export default AccountHistoryTab;
