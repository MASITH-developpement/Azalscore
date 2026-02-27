/**
 * AZALSCORE Module - Subscriptions - Plan Tab
 * Onglet details du plan d'abonnement
 */

import React from 'react';
import {
  Package, Check, DollarSign, Repeat, Gift
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatCurrency } from '@/utils/formatters';
import {
  getMonthlyEquivalent, getYearlyEquivalent,
  INTERVAL_CONFIG
} from '../types';
import type { Subscription, SubscriptionInterval } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * SubscriptionPlanTab - Details du plan
 */
export const SubscriptionPlanTab: React.FC<TabContentProps<Subscription>> = ({ data: subscription }) => {
  // Simuler les features du plan (normalement viendrait de l'API)
  const planFeatures = [
    'Acces a toutes les fonctionnalites',
    'Support prioritaire',
    'Stockage illimite',
    'API access',
    'Rapports avances'
  ];

  const intervalConfig = INTERVAL_CONFIG[subscription.plan_code as keyof typeof INTERVAL_CONFIG] || INTERVAL_CONFIG.MONTHLY;

  return (
    <div className="azals-std-tab-content">
      {/* Resume du plan */}
      <Card className="mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-lg bg-primary-100 flex items-center justify-center">
              <Package size={32} className="text-primary" />
            </div>
            <div>
              <h3 className="text-xl font-bold">{subscription.plan_name}</h3>
              <p className="text-muted">Plan {intervalConfig.label.toLowerCase()}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-primary">
              {formatCurrency(subscription.amount, subscription.currency)}
            </div>
            <div className="text-sm text-muted">{intervalConfig.shortLabel}</div>
          </div>
        </div>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Tarification */}
        <Card title="Tarification" icon={<DollarSign size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <span>Prix actuel</span>
              <div className="text-lg font-bold">
                {formatCurrency(subscription.amount, subscription.currency)} {intervalConfig.shortLabel}
              </div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span>Equivalent mensuel</span>
              <div>
                {formatCurrency(getMonthlyEquivalent(subscription.amount || 0, (subscription.plan_code || 'MONTHLY') as SubscriptionInterval), subscription.currency)} /mois
              </div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span>Equivalent annuel</span>
              <div>
                {formatCurrency(getYearlyEquivalent(subscription.amount || 0, (subscription.plan_code || 'MONTHLY') as SubscriptionInterval), subscription.currency)} /an
              </div>
            </div>
            <div className="azals-std-field">
              <span>Devise</span>
              <div>{subscription.currency}</div>
            </div>
          </div>
        </Card>

        {/* Cycle de facturation */}
        <Card title="Cycle de facturation" icon={<Repeat size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <span>Frequence</span>
              <div className="font-medium">{intervalConfig.label}</div>
            </div>
            <div className="azals-std-field">
              <span>Duree du cycle</span>
              <div>{intervalConfig.months} mois</div>
            </div>
            {subscription.trial_end && (
              <div className="azals-std-field">
                <span>Periode d'essai</span>
                <div className="flex items-center gap-2">
                  <Gift size={14} className="text-blue-500" />
                  Incluse
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Fonctionnalites incluses */}
        <Card title="Fonctionnalites incluses" icon={<Check size={18} />} className="col-span-2">
          <div className="grid grid-cols-2 gap-3">
            {planFeatures.map((feature, index) => (
              <div key={index} className="flex items-center gap-2">
                <Check size={16} className="text-success" />
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </Card>
      </Grid>

      {/* Actions (ERP only) */}
      <Card
        title="Gestion du plan"
        icon={<Package size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'changePlan', subscriptionId: subscription.id } })); }}>
            Changer de plan
          </Button>
          <Button variant="secondary" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'modifyBilling', subscriptionId: subscription.id } })); }}>
            Modifier la facturation
          </Button>
        </div>
        <p className="text-sm text-muted mt-3">
          Les changements de plan prennent effet a la prochaine periode de facturation.
        </p>
      </Card>
    </div>
  );
};

export default SubscriptionPlanTab;
