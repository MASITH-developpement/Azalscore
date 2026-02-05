/**
 * AZALSCORE Module - E-commerce - Product History Tab
 * Onglet historique du produit
 */

import React from 'react';
import { Clock, User, Edit, Plus, Tag, Package, ArrowRight } from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Product, ProductHistoryEntry } from '../types';
import { formatDateTime } from '@/utils/formatters';

/**
 * ProductHistoryTab - Historique
 */
export const ProductHistoryTab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const history = generateHistoryFromProduct(product);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique du produit" icon={<Clock size={18} />}>
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
  entry: ProductHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntryComponent: React.FC<HistoryEntryComponentProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation')) {
      return <Plus size={16} className="text-green-500" />;
    }
    if (action.includes('prix') || action.includes('price')) {
      return <Tag size={16} className="text-blue-500" />;
    }
    if (action.includes('stock')) {
      return <Package size={16} className="text-orange-500" />;
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
 * Generer l'historique a partir des donnees du produit
 */
function generateHistoryFromProduct(product: Product): ProductHistoryEntry[] {
  const history: ProductHistoryEntry[] = [];

  // Creation
  history.push({
    id: 'created',
    timestamp: product.created_at,
    action: 'Produit cree',
    user_name: product.created_by_name,
    details: `SKU: ${product.sku}`,
  });

  // Derniere modification
  if (product.updated_at !== product.created_at) {
    history.push({
      id: 'updated',
      timestamp: product.updated_at,
      action: 'Produit modifie',
      details: 'Mise a jour des informations',
    });
  }

  // Historique fourni par l'API
  if (product.history && product.history.length > 0) {
    history.push(...product.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

export default ProductHistoryTab;
