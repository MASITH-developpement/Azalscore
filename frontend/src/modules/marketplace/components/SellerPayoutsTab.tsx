/**
 * AZALSCORE Module - Marketplace - Seller Payouts Tab
 * Onglet paiements du vendeur
 */

import React from 'react';
import { Wallet, CheckCircle2, Clock, AlertTriangle, XCircle, ArrowRight } from 'lucide-react';
import { Card } from '@ui/layout';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { PAYOUT_STATUS_CONFIG } from '../types';
import type { Seller, Payout } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * SellerPayoutsTab - Paiements du vendeur
 */
export const SellerPayoutsTab: React.FC<TabContentProps<Seller>> = ({ data: seller }) => {
  const payouts = seller.payouts || [];

  const pendingPayouts = payouts.filter(p => p.status === 'PENDING');
  const completedPayouts = payouts.filter(p => p.status === 'COMPLETED');
  const totalPaid = completedPayouts.reduce((sum, p) => sum + p.amount, 0);
  const totalPending = pendingPayouts.reduce((sum, p) => sum + p.amount, 0);

  return (
    <div className="azals-std-tab-content">
      {/* Resume */}
      <Card title="Resume des paiements" icon={<Wallet size={18} />}>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-2xl font-bold text-primary">{payouts.length}</div>
            <div className="text-sm text-muted">Total paiements</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(totalPaid)}
            </div>
            <div className="text-sm text-muted">Total verse</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded">
            <div className="text-2xl font-bold text-orange-600">
              {formatCurrency(totalPending)}
            </div>
            <div className="text-sm text-muted">En attente</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(seller.pending_payout || 0)}
            </div>
            <div className="text-sm text-muted">A verser</div>
          </div>
        </div>
      </Card>

      {/* Alerte paiements en attente */}
      {pendingPayouts.length > 0 && (
        <Card className="mt-4 border-orange-200 bg-orange-50">
          <div className="flex items-center gap-2 text-orange-700">
            <AlertTriangle size={18} />
            <span className="font-medium">
              {pendingPayouts.length} paiement(s) en attente de traitement
              ({formatCurrency(totalPending)})
            </span>
          </div>
        </Card>
      )}

      {/* Liste des paiements */}
      <Card title={`Historique des paiements (${payouts.length})`} icon={<Wallet size={18} />} className="mt-4">
        {payouts.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Periode</th>
                <th className="text-right">Montant</th>
                <th className="text-center">Statut</th>
                <th>Cree le</th>
                <th>Paye le</th>
                <th className="azals-std-field--secondary">Reference</th>
              </tr>
            </thead>
            <tbody>
              {payouts.map((payout) => (
                <PayoutRow key={payout.id} payout={payout} />
              ))}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Wallet size={32} className="text-muted" />
            <p className="text-muted">Aucun paiement enregistre</p>
          </div>
        )}
      </Card>

      {/* Coordonnees bancaires */}
      <Card title="Coordonnees de versement" icon={<Wallet size={18} />} className="mt-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="azals-field">
            <span className="azals-field__label">IBAN</span>
            <div className="azals-field__value font-mono text-sm">
              {seller.bank_iban || (
                <span className="text-orange-600 flex items-center gap-1">
                  <AlertTriangle size={14} /> Non renseigne
                </span>
              )}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">BIC</span>
            <div className="azals-field__value font-mono">
              {seller.bank_bic || '-'}
            </div>
          </div>
        </div>
      </Card>

      {/* Stats par statut (ERP only) */}
      <Card title="Repartition par statut" icon={<Wallet size={18} />} className="mt-4 azals-std-field--secondary">
        <div className="grid grid-cols-4 gap-2">
          {Object.entries(PAYOUT_STATUS_CONFIG).map(([status, config]) => {
            const count = payouts.filter(p => p.status === status).length;
            const amount = payouts
              .filter(p => p.status === status)
              .reduce((sum, p) => sum + p.amount, 0);
            return (
              <div key={status} className="text-center p-2 bg-gray-50 rounded">
                <span className={`azals-badge azals-badge--${config.color} mb-1`}>
                  {config.label}
                </span>
                <div className="text-lg font-bold">{count}</div>
                <div className="text-xs text-muted">{formatCurrency(amount)}</div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant ligne paiement
 */
const PayoutRow: React.FC<{ payout: Payout }> = ({ payout }) => {
  const statusConfig = PAYOUT_STATUS_CONFIG[payout.status];

  const getStatusIcon = () => {
    switch (payout.status) {
      case 'COMPLETED':
        return <CheckCircle2 size={14} className="text-green-500" />;
      case 'PENDING':
        return <Clock size={14} className="text-orange-500" />;
      case 'PROCESSING':
        return <Clock size={14} className="text-blue-500" />;
      case 'FAILED':
        return <XCircle size={14} className="text-red-500" />;
    }
  };

  return (
    <tr>
      <td>
        <span className="flex items-center gap-1 text-sm">
          {formatDate(payout.period_start)}
          <ArrowRight size={12} className="text-muted" />
          {formatDate(payout.period_end)}
        </span>
      </td>
      <td className="text-right font-medium">
        {formatCurrency(payout.amount, payout.currency)}
      </td>
      <td className="text-center">
        <span className={`azals-badge azals-badge--${statusConfig.color} inline-flex items-center gap-1`}>
          {getStatusIcon()}
          {statusConfig.label}
        </span>
      </td>
      <td className="text-muted text-sm">{formatDate(payout.created_at)}</td>
      <td className="text-sm">
        {payout.paid_at ? (
          <span className="text-green-600">{formatDate(payout.paid_at)}</span>
        ) : (
          <span className="text-muted">-</span>
        )}
      </td>
      <td className="text-muted text-sm font-mono azals-std-field--secondary">
        {payout.bank_reference || payout.reference || '-'}
      </td>
    </tr>
  );
};

export default SellerPayoutsTab;
