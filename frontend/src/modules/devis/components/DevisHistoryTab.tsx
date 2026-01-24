/**
 * AZALSCORE Module - DEVIS - History Tab
 * Onglet historique et audit du devis
 */

import React from 'react';
import {
  Clock, User, Edit, Check, Send, X, Plus,
  FileText, ArrowRight, RefreshCw
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Devis, DevisHistoryEntry } from '../types';
import { formatDateTime, STATUS_CONFIG } from '../types';

/**
 * DevisHistoryTab - Historique et audit trail du devis
 */
export const DevisHistoryTab: React.FC<TabContentProps<Devis>> = ({ data: devis }) => {
  // Générer l'historique à partir des données du devis
  // En production, cela viendrait d'une API dédiée
  const history = generateHistoryFromDevis(devis);

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
  entry: DevisHistoryEntry;
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
    if (action.includes('envoyé') || action.includes('envoi')) {
      return <Send size={16} className="text-purple" />;
    }
    if (action.includes('modifié') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    if (action.includes('annulé') || action.includes('refusé')) {
      return <X size={16} className="text-danger" />;
    }
    if (action.includes('converti')) {
      return <RefreshCw size={16} className="text-success" />;
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
 * Générer l'historique à partir des données du devis
 */
function generateHistoryFromDevis(devis: Devis): DevisHistoryEntry[] {
  const history: DevisHistoryEntry[] = [];

  // Création
  history.push({
    id: 'created',
    timestamp: devis.created_at,
    action: 'Devis créé',
    user_name: devis.created_by,
    details: `Numéro: ${devis.number}`,
  });

  // Validation
  if (devis.validated_at) {
    history.push({
      id: 'validated',
      timestamp: devis.validated_at,
      action: 'Devis validé',
      user_name: devis.validated_by,
      old_value: STATUS_CONFIG.DRAFT.label,
      new_value: STATUS_CONFIG.VALIDATED.label,
    });
  }

  // Statut envoyé
  if (devis.status === 'SENT' || devis.status === 'ACCEPTED' || devis.status === 'REJECTED') {
    history.push({
      id: 'sent',
      timestamp: devis.updated_at, // Approximation
      action: 'Devis envoyé au client',
      details: `Client: ${devis.customer_name}`,
    });
  }

  // Statut accepté/refusé
  if (devis.status === 'ACCEPTED') {
    history.push({
      id: 'accepted',
      timestamp: devis.updated_at,
      action: 'Devis accepté par le client',
      old_value: STATUS_CONFIG.SENT.label,
      new_value: STATUS_CONFIG.ACCEPTED.label,
    });
  } else if (devis.status === 'REJECTED') {
    history.push({
      id: 'rejected',
      timestamp: devis.updated_at,
      action: 'Devis refusé par le client',
      old_value: STATUS_CONFIG.SENT.label,
      new_value: STATUS_CONFIG.REJECTED.label,
    });
  }

  // Trier par date décroissante (plus récent en premier)
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default DevisHistoryTab;
