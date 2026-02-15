/**
 * AZALSCORE Module - Treasury - Account Reconciliation Tab
 * Onglet rapprochement bancaire du compte
 */

import React from 'react';
import {
  CheckCircle2, XCircle, AlertTriangle, Link2, FileText
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { BankAccount, Transaction } from '../types';
import { isTransactionReconciled } from '../types';
import { formatCurrency, formatDate } from '@/utils/formatters';

/**
 * AccountReconciliationTab - Rapprochement bancaire
 */
export const AccountReconciliationTab: React.FC<TabContentProps<BankAccount>> = ({ data: account }) => {
  const transactions = account.transactions || [];

  const reconciledTransactions = transactions.filter(isTransactionReconciled);
  const unreconciledTransactions = transactions.filter(t => !isTransactionReconciled(t));

  const unreconciledCredits = unreconciledTransactions
    .filter(t => t.type === 'credit')
    .reduce((sum, t) => sum + t.amount, 0);
  const unreconciledDebits = unreconciledTransactions
    .filter(t => t.type === 'debit')
    .reduce((sum, t) => sum + t.amount, 0);

  const reconciliationRate = transactions.length > 0
    ? Math.round((reconciledTransactions.length / transactions.length) * 100)
    : 100;

  return (
    <div className="azals-std-tab-content">
      {/* Resume rapprochement */}
      <Card title="Etat du rapprochement" icon={<CheckCircle2 size={18} />}>
        <Grid cols={4} gap="md">
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-3xl font-bold text-primary">{reconciliationRate}%</div>
            <div className="text-sm text-muted">Taux de rapprochement</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">{reconciledTransactions.length}</div>
            <div className="text-sm text-muted">Rapprochees</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded">
            <div className="text-2xl font-bold text-orange-600">{unreconciledTransactions.length}</div>
            <div className="text-sm text-muted">A rapprocher</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">{transactions.length}</div>
            <div className="text-sm text-muted">Total</div>
          </div>
        </Grid>
      </Card>

      {/* Alerte */}
      {unreconciledTransactions.length > 0 && (
        <Card className="mt-4 border-orange-200 bg-orange-50">
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="text-orange-600 mt-0.5" />
            <div>
              <p className="font-medium text-orange-700">
                {unreconciledTransactions.length} transaction(s) en attente de rapprochement
              </p>
              <div className="mt-2 text-sm text-orange-600">
                <span className="mr-4">
                  Credits: +{formatCurrency(unreconciledCredits, account.currency)}
                </span>
                <span>
                  Debits: -{formatCurrency(unreconciledDebits, account.currency)}
                </span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Transactions a rapprocher */}
      <Card
        title={`Transactions a rapprocher (${unreconciledTransactions.length})`}
        icon={<XCircle size={18} />}
        className="mt-4"
      >
        {unreconciledTransactions.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th className="text-right">Montant</th>
                <th className="text-center">Action</th>
              </tr>
            </thead>
            <tbody>
              {unreconciledTransactions.map((transaction) => (
                <UnreconciledRow key={transaction.id} transaction={transaction} currency={account.currency} />
              ))}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <CheckCircle2 size={32} className="text-green-500" />
            <p className="text-green-600 font-medium">Toutes les transactions sont rapprochees</p>
          </div>
        )}
      </Card>

      {/* Transactions rapprochees (ERP only) */}
      <Card
        title={`Transactions rapprochees (${reconciledTransactions.length})`}
        icon={<CheckCircle2 size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        {reconciledTransactions.length > 0 ? (
          <table className="azals-table azals-table--simple azals-table--compact">
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th className="text-right">Montant</th>
                <th>Document lie</th>
                <th>Rapproche le</th>
              </tr>
            </thead>
            <tbody>
              {reconciledTransactions.slice(0, 20).map((transaction) => (
                <ReconciledRow key={transaction.id} transaction={transaction} currency={account.currency} />
              ))}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <FileText size={32} className="text-muted" />
            <p className="text-muted">Aucune transaction rapprochee</p>
          </div>
        )}
        {reconciledTransactions.length > 20 && (
          <p className="text-center text-muted text-sm mt-2">
            ... et {reconciledTransactions.length - 20} autres transactions
          </p>
        )}
      </Card>
    </div>
  );
};

/**
 * Ligne transaction non rapprochee
 */
const UnreconciledRow: React.FC<{ transaction: Transaction; currency: string }> = ({ transaction, currency }) => {
  const isCredit = transaction.type === 'credit';

  return (
    <tr>
      <td className="text-sm">{formatDate(transaction.date)}</td>
      <td>
        <div className="font-medium">{transaction.description}</div>
        {transaction.reference && (
          <div className="text-muted text-xs font-mono">{transaction.reference}</div>
        )}
      </td>
      <td className={`text-right font-medium ${isCredit ? 'text-green-600' : 'text-red-600'}`}>
        {isCredit ? '+' : '-'}{formatCurrency(transaction.amount, currency)}
      </td>
      <td className="text-center">
        <Button size="sm" variant="secondary" leftIcon={<Link2 size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'reconcileTransaction', transactionId: transaction.id } })); }}>
          Rapprocher
        </Button>
      </td>
    </tr>
  );
};

/**
 * Ligne transaction rapprochee
 */
const ReconciledRow: React.FC<{ transaction: Transaction; currency: string }> = ({ transaction, currency }) => {
  const isCredit = transaction.type === 'credit';

  return (
    <tr>
      <td className="text-sm text-muted">{formatDate(transaction.date)}</td>
      <td className="text-muted">{transaction.description}</td>
      <td className={`text-right ${isCredit ? 'text-green-600' : 'text-red-600'}`}>
        {isCredit ? '+' : '-'}{formatCurrency(transaction.amount, currency)}
      </td>
      <td>
        {transaction.linked_document ? (
          <span className="text-sm">
            <span className="azals-badge azals-badge--blue text-xs">
              {transaction.linked_document.type}
            </span>
            <span className="ml-1 font-mono text-xs">{transaction.linked_document.number}</span>
          </span>
        ) : (
          <span className="text-muted">-</span>
        )}
      </td>
      <td className="text-sm text-muted">
        {transaction.reconciled_at ? formatDate(transaction.reconciled_at) : '-'}
      </td>
    </tr>
  );
};

export default AccountReconciliationTab;
