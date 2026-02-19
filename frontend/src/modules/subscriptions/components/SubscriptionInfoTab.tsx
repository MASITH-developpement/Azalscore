/**
 * AZALSCORE Module - Subscriptions - Info Tab
 * Onglet informations generales de l'abonnement
 */

import React from 'react';
import {
  User, Mail, Calendar, CreditCard, Clock, AlertTriangle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatCurrency, formatDate, formatDateTime } from '@/utils/formatters';
import {
  getSubscriptionAge, getDaysUntilRenewal, getTrialDaysRemaining,
  isInTrial, willCancel, isPastDue,
  SUBSCRIPTION_STATUS_CONFIG, INTERVAL_CONFIG
} from '../types';
import type { Subscription } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * SubscriptionInfoTab - Informations generales
 */
export const SubscriptionInfoTab: React.FC<TabContentProps<Subscription>> = ({ data: subscription }) => {
  const statusConfig = SUBSCRIPTION_STATUS_CONFIG[subscription.status];
  const daysUntilRenewal = getDaysUntilRenewal(subscription);
  const trialDaysRemaining = getTrialDaysRemaining(subscription);

  return (
    <div className="azals-std-tab-content">
      {/* Alertes */}
      {isPastDue(subscription) && (
        <div className="azals-alert azals-alert--danger mb-4">
          <AlertTriangle size={18} />
          <div>
            <strong>Paiement en retard</strong>
            <p className="text-sm">Le dernier paiement n'a pas ete effectue.</p>
          </div>
        </div>
      )}

      {willCancel(subscription) && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertTriangle size={18} />
          <div>
            <strong>Annulation programmee</strong>
            <p className="text-sm">
              Cet abonnement sera annule le {formatDate(subscription.current_period_end)}.
            </p>
          </div>
        </div>
      )}

      {isInTrial(subscription) && trialDaysRemaining !== null && (
        <div className="azals-alert azals-alert--info mb-4">
          <Clock size={18} />
          <div>
            <strong>Periode d'essai</strong>
            <p className="text-sm">
              {trialDaysRemaining > 0
                ? `${trialDaysRemaining} jour${trialDaysRemaining > 1 ? 's' : ''} restant${trialDaysRemaining > 1 ? 's' : ''}`
                : 'Se termine aujourd\'hui'}
            </p>
          </div>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Client */}
        <Card title="Client" icon={<User size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <span>Nom</span>
              <div className="font-medium">{subscription.customer_name}</div>
            </div>
            <div className="azals-std-field">
              <span>Email</span>
              <div className="flex items-center gap-2">
                <Mail size={14} className="text-muted" />
                {subscription.customer_email}
              </div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span>ID Client</span>
              <div className="font-mono text-sm">{subscription.customer_id}</div>
            </div>
          </div>
        </Card>

        {/* Abonnement */}
        <Card title="Abonnement" icon={<CreditCard size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <span>Plan</span>
              <div className="font-medium">{subscription.plan_name}</div>
            </div>
            <div className="azals-std-field">
              <span>Montant</span>
              <div className="text-lg font-bold text-primary">
                {formatCurrency(subscription.amount, subscription.currency)}
                <span className="text-sm font-normal text-muted ml-1">
                  {INTERVAL_CONFIG[subscription.plan_code as keyof typeof INTERVAL_CONFIG]?.shortLabel || '/periode'}
                </span>
              </div>
            </div>
            <div className="azals-std-field">
              <span>Statut</span>
              <div className={`font-medium text-${statusConfig.color}`}>
                {statusConfig.label}
              </div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span>Anciennete</span>
              <div>{getSubscriptionAge(subscription)}</div>
            </div>
          </div>
        </Card>

        {/* Periode en cours */}
        <Card title="Periode en cours" icon={<Calendar size={18} />}>
          <div className="space-y-3">
            {subscription.current_period_start && (
              <div className="azals-std-field">
                <span>Debut de periode</span>
                <div>{formatDate(subscription.current_period_start)}</div>
              </div>
            )}
            <div className="azals-std-field">
              <span>Fin de periode</span>
              <div>{formatDate(subscription.current_period_end)}</div>
            </div>
            <div className="azals-std-field">
              <span>Prochain renouvellement</span>
              <div className={daysUntilRenewal <= 7 ? 'text-warning font-medium' : ''}>
                {daysUntilRenewal > 0
                  ? `Dans ${daysUntilRenewal} jour${daysUntilRenewal > 1 ? 's' : ''}`
                  : 'Aujourd\'hui'}
              </div>
            </div>
            {subscription.cancel_at_period_end && (
              <div className="azals-std-field">
                <span>Action en fin de periode</span>
                <div className="text-danger font-medium">Annulation</div>
              </div>
            )}
          </div>
        </Card>

        {/* Dates cles */}
        <Card title="Dates cles" icon={<Clock size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <span>Date de souscription</span>
              <div>{formatDate(subscription.start_date)}</div>
            </div>
            <div className="azals-std-field">
              <span>Date de creation</span>
              <div>{formatDateTime(subscription.created_at)}</div>
            </div>
            {subscription.trial_end && (
              <div className="azals-std-field">
                <span>Fin de l'essai</span>
                <div>{formatDate(subscription.trial_end)}</div>
              </div>
            )}
            {subscription.cancelled_at && (
              <div className="azals-std-field">
                <span>Date d'annulation</span>
                <div className="text-danger">{formatDateTime(subscription.cancelled_at)}</div>
              </div>
            )}
            {subscription.updated_at && (
              <div className="azals-std-field azals-std-field--secondary">
                <span>Derniere modification</span>
                <div>{formatDateTime(subscription.updated_at)}</div>
              </div>
            )}
          </div>
        </Card>
      </Grid>
    </div>
  );
};

export default SubscriptionInfoTab;
