/**
 * AZALSCORE Module - POS - Session Transactions Tab
 * Onglet transactions de la session
 */

import React, { useState } from 'react';
import {
  Receipt, ShoppingCart, ArrowDownCircle, ArrowUpCircle,
  XCircle, CreditCard, Banknote, CheckCircle2
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Select } from '@ui/forms';
import type { TabContentProps } from '@ui/standards';
import type { POSSession, POSTransaction } from '../types';
import {
  formatNumber,
  TRANSACTION_TYPE_CONFIG, TRANSACTION_STATUS_CONFIG, PAYMENT_METHOD_CONFIG,
  isSaleTransaction, isReturnTransaction, isVoidedTransaction
} from '../types';
import { formatCurrency, formatDateTime, formatTime } from '@/utils/formatters';

/**
 * SessionTransactionsTab - Transactions de la session
 */
export const SessionTransactionsTab: React.FC<TabContentProps<POSSession>> = ({ data: session }) => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');

  const transactions = session.transactions || [];

  const filteredTransactions = transactions.filter(t => {
    if (filterType && t.type !== filterType) return false;
    if (filterStatus && t.status !== filterStatus) return false;
    return true;
  });

  const salesCount = transactions.filter(isSaleTransaction).length;
  const returnsCount = transactions.filter(isReturnTransaction).length;
  const voidedCount = transactions.filter(isVoidedTransaction).length;
  const completedCount = transactions.filter(t => t.status === 'COMPLETED').length;

  return (
    <div className="azals-std-tab-content">
      {/* Resume */}
      <Card title="Resume des transactions" icon={<Receipt size={18} />}>
        <Grid cols={4} gap="md">
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-2xl font-bold text-primary">{transactions.length}</div>
            <div className="text-sm text-muted">Total</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">{salesCount}</div>
            <div className="text-sm text-muted">Ventes</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded">
            <div className="text-2xl font-bold text-red-600">{returnsCount}</div>
            <div className="text-sm text-muted">Retours</div>
          </div>
          <div className="text-center p-3 bg-gray-100 rounded">
            <div className="text-2xl font-bold text-gray-600">{voidedCount}</div>
            <div className="text-sm text-muted">Annulees</div>
          </div>
        </Grid>
      </Card>

      {/* Filtres et liste */}
      <Card
        title={`Transactions (${filteredTransactions.length})`}
        icon={<Receipt size={18} />}
        className="mt-4"
      >
        {/* Filtres */}
        <div className="flex gap-2 mb-4">
          <Select
            value={filterType}
            onChange={setFilterType}
            options={[
              { value: '', label: 'Tous types' },
              { value: 'SALE', label: 'Ventes' },
              { value: 'RETURN', label: 'Retours' },
              { value: 'EXCHANGE', label: 'Echanges' },
              { value: 'VOID', label: 'Annulations' }
            ]}
            className="w-36"
          />
          <Select
            value={filterStatus}
            onChange={setFilterStatus}
            options={[
              { value: '', label: 'Tous statuts' },
              { value: 'COMPLETED', label: 'Terminees' },
              { value: 'VOIDED', label: 'Annulees' },
              { value: 'REFUNDED', label: 'Remboursees' }
            ]}
            className="w-36"
          />
        </div>

        {/* Liste des transactions */}
        {filteredTransactions.length > 0 ? (
          <div className="space-y-3">
            {filteredTransactions.map((transaction) => (
              <TransactionCard key={transaction.id} transaction={transaction} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Receipt size={32} className="text-muted" />
            <p className="text-muted">Aucune transaction</p>
          </div>
        )}
      </Card>

      {/* Stats par type de paiement (ERP only) */}
      <Card
        title="Statistiques par mode de paiement"
        icon={<CreditCard size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={3} gap="md">
          {Object.entries(PAYMENT_METHOD_CONFIG).map(([method, config]) => {
            const count = transactions.filter(t => t.payment_method === method).length;
            const total = transactions
              .filter(t => t.payment_method === method)
              .reduce((sum, t) => sum + t.total, 0);
            return (
              <div key={method} className="p-3 bg-gray-50 rounded">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`azals-badge azals-badge--${config.color}`}>
                    {config.label}
                  </span>
                </div>
                <div className="text-lg font-bold">{count} transactions</div>
                <div className="text-sm text-muted">{formatCurrency(total)}</div>
              </div>
            );
          })}
        </Grid>
      </Card>
    </div>
  );
};

/**
 * Composant carte de transaction
 */
const TransactionCard: React.FC<{ transaction: POSTransaction }> = ({ transaction }) => {
  const typeConfig = TRANSACTION_TYPE_CONFIG[transaction.type];
  const statusConfig = TRANSACTION_STATUS_CONFIG[transaction.status];
  const paymentConfig = PAYMENT_METHOD_CONFIG[transaction.payment_method];
  const isVoided = isVoidedTransaction(transaction);

  const getTypeIcon = () => {
    switch (transaction.type) {
      case 'SALE':
        return <ArrowUpCircle size={18} className="text-green-600" />;
      case 'RETURN':
        return <ArrowDownCircle size={18} className="text-red-600" />;
      case 'EXCHANGE':
        return <ShoppingCart size={18} className="text-blue-600" />;
      case 'VOID':
        return <XCircle size={18} className="text-gray-600" />;
    }
  };

  return (
    <div className={`p-4 rounded border ${isVoided ? 'border-gray-200 bg-gray-50 opacity-70' : 'border-gray-200 bg-white'}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          {getTypeIcon()}
          <div>
            <div className="flex items-center gap-2 mb-1">
              <code className="font-mono text-sm">{transaction.number}</code>
              <span className={`azals-badge azals-badge--${typeConfig.color}`}>
                {typeConfig.label}
              </span>
              <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
            <div className="text-sm text-muted">
              {formatTime(transaction.created_at)}
              {transaction.customer_name && (
                <span className="ml-2">- {transaction.customer_name}</span>
              )}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-xl font-bold ${transaction.type === 'RETURN' ? 'text-red-600' : 'text-green-600'}`}>
            {transaction.type === 'RETURN' ? '-' : ''}{formatCurrency(transaction.total)}
          </div>
          <div className="flex items-center gap-1 text-sm text-muted justify-end">
            <span className={`azals-badge azals-badge--${paymentConfig.color} text-xs`}>
              {paymentConfig.label}
            </span>
          </div>
        </div>
      </div>

      {/* Details des articles */}
      {transaction.items && transaction.items.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="text-sm text-muted mb-2">
            {transaction.items.length} article(s)
          </div>
          <div className="space-y-1">
            {transaction.items.slice(0, 3).map((item) => (
              <div key={item.id} className="flex justify-between text-sm">
                <span>
                  {item.quantity}x {item.product_name || item.product_code}
                </span>
                <span>{formatCurrency(item.total)}</span>
              </div>
            ))}
            {transaction.items.length > 3 && (
              <div className="text-sm text-muted">
                + {transaction.items.length - 3} autre(s) article(s)
              </div>
            )}
          </div>
        </div>
      )}

      {/* Remise */}
      {transaction.discount > 0 && (
        <div className="mt-2 text-sm text-orange-600">
          Remise: -{formatCurrency(transaction.discount)}
          {transaction.discount_reason && (
            <span className="text-muted ml-2">({transaction.discount_reason})</span>
          )}
        </div>
      )}
    </div>
  );
};

export default SessionTransactionsTab;
