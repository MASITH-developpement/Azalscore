/**
 * AZALSCORE Module - POS - Session Info Tab
 * Onglet informations generales de la session
 */

import React from 'react';
import {
  Monitor, User, Calendar, Store, CreditCard,
  ShoppingCart, TrendingUp
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatCurrency, formatDateTime } from '@/utils/formatters';
import {
  formatNumber,
  formatSessionDuration, SESSION_STATUS_CONFIG,
  getCashPaymentPercentage, getCardPaymentPercentage
} from '../types';
import type { POSSession } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * SessionInfoTab - Informations generales
 */
export const SessionInfoTab: React.FC<TabContentProps<POSSession>> = ({ data: session }) => {
  return (
    <div className="azals-std-tab-content">
      {/* Identification */}
      <Card title="Identification" icon={<Monitor size={18} />}>
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Code session</span>
            <div className="azals-field__value font-mono">{session.code}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Statut</span>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${SESSION_STATUS_CONFIG[session.status].color}`}>
                {SESSION_STATUS_CONFIG[session.status].label}
              </span>
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Duree</span>
            <div className="azals-field__value">{formatSessionDuration(session)}</div>
          </div>
        </Grid>
      </Card>

      {/* Terminal et magasin */}
      <Card title="Terminal et magasin" icon={<Store size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Terminal</span>
            <div className="azals-field__value">
              <code className="font-mono text-sm mr-2">{session.terminal_code}</code>
              {session.terminal_name}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Magasin</span>
            <div className="azals-field__value">
              {session.store_name || '-'}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Code magasin</span>
            <div className="azals-field__value font-mono">{session.store_code || '-'}</div>
          </div>
        </Grid>
      </Card>

      {/* Caissier */}
      <Card title="Caissier" icon={<User size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Nom</span>
            <div className="azals-field__value">{session.cashier_name || '-'}</div>
          </div>
          <div className="azals-field azals-std-field--secondary">
            <span className="azals-field__label">ID Caissier</span>
            <div className="azals-field__value font-mono">{session.cashier_id}</div>
          </div>
        </Grid>
      </Card>

      {/* Horaires */}
      <Card title="Horaires" icon={<Calendar size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Ouverture</span>
            <div className="azals-field__value">
              {formatDateTime(session.opened_at)}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Fermeture</span>
            <div className="azals-field__value">
              {session.closed_at ? formatDateTime(session.closed_at) : '-'}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Duree totale</span>
            <div className="azals-field__value">{formatSessionDuration(session)}</div>
          </div>
        </Grid>
      </Card>

      {/* Ventes */}
      <Card title="Synthese des ventes" icon={<ShoppingCart size={18} />} className="mt-4">
        <Grid cols={4} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Ventes brutes</span>
            <div className="azals-field__value text-xl font-bold text-green-600">
              {formatCurrency(session.total_sales)}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Retours</span>
            <div className="azals-field__value text-xl font-bold text-red-600">
              {formatCurrency(session.total_returns)}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Ventes nettes</span>
            <div className="azals-field__value text-xl font-bold text-primary">
              {formatCurrency(session.net_sales)}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Remises accordees</span>
            <div className="azals-field__value text-orange-600">
              {formatCurrency(session.discounts_given)}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Statistiques */}
      <Card title="Statistiques" icon={<TrendingUp size={18} />} className="mt-4">
        <Grid cols={4} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Transactions</span>
            <div className="azals-field__value text-xl font-medium">
              {formatNumber(session.total_transactions)}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Articles vendus</span>
            <div className="azals-field__value text-xl font-medium">
              {formatNumber(session.total_items_sold)}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Panier moyen</span>
            <div className="azals-field__value text-xl font-medium text-blue-600">
              {formatCurrency(session.average_basket)}
            </div>
          </div>
          <div className="azals-field azals-std-field--secondary">
            <span className="azals-field__label">Articles/transaction</span>
            <div className="azals-field__value">
              {session.total_transactions > 0
                ? (session.total_items_sold / session.total_transactions).toFixed(1)
                : '-'}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Paiements */}
      <Card title="Repartition des paiements" icon={<CreditCard size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Especes</span>
            <div className="azals-field__value">
              <span className="text-lg font-medium">{formatCurrency(session.cash_payments)}</span>
              <span className="text-sm text-muted ml-2">
                ({getCashPaymentPercentage(session).toFixed(0)}%)
              </span>
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Carte</span>
            <div className="azals-field__value">
              <span className="text-lg font-medium">{formatCurrency(session.card_payments)}</span>
              <span className="text-sm text-muted ml-2">
                ({getCardPaymentPercentage(session).toFixed(0)}%)
              </span>
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Autres</span>
            <div className="azals-field__value">
              <span className="text-lg font-medium">{formatCurrency(session.other_payments)}</span>
            </div>
          </div>
        </Grid>
      </Card>

      {/* Notes (ERP only) */}
      {session.notes && (
        <Card title="Notes" className="mt-4 azals-std-field--secondary">
          <p className="text-muted whitespace-pre-wrap">{session.notes}</p>
        </Card>
      )}
    </div>
  );
};

export default SessionInfoTab;
