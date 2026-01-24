/**
 * AZALSCORE Module - STOCK - Product History Tab
 * Onglet historique de l'article
 */

import React from 'react';
import {
  Clock, User, Edit, Package, ArrowRight,
  FileText, ArrowUpRight, ArrowDownRight, RefreshCw
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Product, ProductHistoryEntry, Movement } from '../types';
import {
  formatDateTime, formatDate, formatQuantity,
  MOVEMENT_TYPE_CONFIG, MOVEMENT_STATUS_CONFIG
} from '../types';

/**
 * ProductHistoryTab - Historique de l'article
 */
export const ProductHistoryTab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  // Générer l'historique combiné
  const history = generateHistoryFromProduct(product);
  const movements = product.movements || [];

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des modifications */}
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

      {/* Historique des mouvements */}
      <Card
        title="Historique des mouvements de stock"
        icon={<Package size={18} />}
        className="mt-4"
      >
        {movements.length > 0 ? (
          <table className="azals-table azals-table--simple azals-table--compact">
            <thead>
              <tr>
                <th>Date</th>
                <th>N° Mouvement</th>
                <th>Type</th>
                <th className="text-right">Quantité</th>
                <th>Source</th>
                <th>Destination</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {movements.map((movement) => {
                const typeConfig = MOVEMENT_TYPE_CONFIG[movement.type];
                const statusConfig = MOVEMENT_STATUS_CONFIG[movement.status];
                return (
                  <tr key={movement.id}>
                    <td className="text-muted text-sm">{formatDate(movement.date)}</td>
                    <td className="font-mono text-sm">{movement.number}</td>
                    <td>
                      <span className={`azals-badge azals-badge--${typeConfig.color}`}>
                        {typeConfig.label}
                      </span>
                    </td>
                    <td className="text-right">
                      <span className={movement.type === 'IN' ? 'text-success' : movement.type === 'OUT' ? 'text-danger' : ''}>
                        {movement.type === 'IN' && <ArrowUpRight size={12} className="inline mr-1" />}
                        {movement.type === 'OUT' && <ArrowDownRight size={12} className="inline mr-1" />}
                        {movement.type === 'TRANSFER' && <RefreshCw size={12} className="inline mr-1" />}
                        {formatQuantity(movement.quantity, product.unit)}
                      </span>
                    </td>
                    <td className="text-muted text-sm">
                      {movement.source_warehouse_name && movement.source_location_name
                        ? `${movement.source_warehouse_name} / ${movement.source_location_name}`
                        : movement.source_location_name || '-'}
                    </td>
                    <td className="text-muted text-sm">
                      {movement.dest_warehouse_name && movement.dest_location_name
                        ? `${movement.dest_warehouse_name} / ${movement.dest_location_name}`
                        : movement.dest_location_name || '-'}
                    </td>
                    <td>
                      <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                        {statusConfig.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Package size={32} className="text-muted" />
            <p className="text-muted">Aucun mouvement de stock</p>
          </div>
        )}
      </Card>

      {/* Journal d'audit détaillé (ERP only) */}
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
 * Composant entrée de timeline
 */
interface HistoryEntryProps {
  entry: ProductHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('créé') || action.includes('création')) {
      return <FileText size={16} className="text-primary" />;
    }
    if (action.includes('entrée') || action.includes('réception')) {
      return <ArrowUpRight size={16} className="text-success" />;
    }
    if (action.includes('sortie') || action.includes('expédition')) {
      return <ArrowDownRight size={16} className="text-danger" />;
    }
    if (action.includes('transfert')) {
      return <RefreshCw size={16} className="text-blue" />;
    }
    if (action.includes('modifié') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    if (action.includes('inventaire')) {
      return <Package size={16} className="text-purple" />;
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
 * Générer l'historique à partir des données de l'article
 */
function generateHistoryFromProduct(product: Product): ProductHistoryEntry[] {
  const history: ProductHistoryEntry[] = [];

  // Création
  history.push({
    id: 'created',
    timestamp: product.created_at,
    action: 'Article créé',
    user_name: product.created_by,
    details: `Code: ${product.code}, Désignation: ${product.name}`,
  });

  // Dernière modification
  if (product.updated_at && product.updated_at !== product.created_at) {
    history.push({
      id: 'updated',
      timestamp: product.updated_at,
      action: 'Article modifié',
      details: 'Mise à jour des informations',
    });
  }

  // Historique des mouvements (résumé)
  if (product.movements && product.movements.length > 0) {
    const recentMovements = product.movements.slice(0, 5);
    recentMovements.forEach((movement, index) => {
      const typeConfig = MOVEMENT_TYPE_CONFIG[movement.type];
      history.push({
        id: `movement-${movement.id}`,
        timestamp: movement.date,
        action: `Mouvement: ${typeConfig.label}`,
        user_name: movement.created_by,
        details: `${movement.number} - ${movement.quantity} ${product.unit}`,
      });
    });
  }

  // Historique fourni par l'API
  if (product.history && product.history.length > 0) {
    history.push(...product.history);
  }

  // Trier par date décroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default ProductHistoryTab;
