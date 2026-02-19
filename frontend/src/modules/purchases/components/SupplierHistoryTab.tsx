/**
 * AZALSCORE Module - Purchases - Supplier History Tab
 * Onglet historique du fournisseur
 */

import React from 'react';
import { Clock, User, Edit, Plus, CheckCircle2, XCircle, ArrowRight } from 'lucide-react';
import { Card } from '@ui/layout';
import { formatDateTime } from '@/utils/formatters';
import type { Supplier, PurchaseHistoryEntry } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * SupplierHistoryTab - Historique
 */
export const SupplierHistoryTab: React.FC<TabContentProps<Supplier & { history?: PurchaseHistoryEntry[] }>> = ({ data: supplier }) => {
  const history = generateHistoryFromSupplier(supplier);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique du fournisseur" icon={<Clock size={18} />}>
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
    if (action.includes('approuv') || action.includes('valid')) {
      return <CheckCircle2 size={16} className="text-blue-500" />;
    }
    if (action.includes('bloqu') || action.includes('inactiv')) {
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
 * Generer l'historique a partir des donnees du fournisseur
 */
function generateHistoryFromSupplier(supplier: Supplier & { history?: PurchaseHistoryEntry[] }): PurchaseHistoryEntry[] {
  const history: PurchaseHistoryEntry[] = [];

  // Creation du fournisseur
  history.push({
    id: 'created',
    timestamp: supplier.created_at,
    action: 'Fournisseur cree',
    user_name: supplier.created_by_name,
    details: `Code: ${supplier.code}`,
  });

  // Statut
  if (supplier.status === 'APPROVED') {
    history.push({
      id: 'approved',
      timestamp: supplier.updated_at,
      action: 'Fournisseur approuve',
      details: 'Le fournisseur a ete approuve pour les achats',
    });
  } else if (supplier.status === 'BLOCKED') {
    history.push({
      id: 'blocked',
      timestamp: supplier.updated_at,
      action: 'Fournisseur bloque',
      details: 'Le fournisseur a ete bloque',
    });
  }

  // Derniere modification
  if (supplier.updated_at !== supplier.created_at) {
    history.push({
      id: 'updated',
      timestamp: supplier.updated_at,
      action: 'Fournisseur modifie',
      details: 'Mise a jour des informations',
    });
  }

  // Historique fourni par l'API
  if (supplier.history && supplier.history.length > 0) {
    history.push(...supplier.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

export default SupplierHistoryTab;
