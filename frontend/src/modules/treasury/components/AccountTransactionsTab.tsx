/**
 * AZALSCORE Module - Treasury - Account Transactions Tab
 * Onglet transactions du compte bancaire
 */

import React from 'react';
import {
  ArrowDownLeft, ArrowUpRight, CheckCircle2, XCircle,
  FileText, Calendar, Search
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { BankAccount, Transaction } from '../types';
import {
  formatCurrency, formatDate, formatDateTime,
  isCredit, isDebit, isTransactionReconciled
} from '../types';

/**
 * AccountTransactionsTab - Transactions du compte
 */
export const AccountTransactionsTab: React.FC<TabContentProps<BankAccount>> = ({ data: account }) => {
  const transactions = account.transactions || [];

  const totalCredits = transactions
    .filter(isCredit)
    .reduce((sum, t) => sum + t.amount, 0);
  const totalDebits = transactions
    .filter(isDebit)
    .reduce((sum, t) => sum + t.amount, 0);
  const reconciledCount = transactions.filter(isTransactionReconciled).length;
  const unreconciledCount = transactions.length - reconciledCount;

  return (
    <div className="azals-std-tab-content">
      {/* Resume */}
      <Card title="Resume des mouvements" icon={<FileText size={18} />}>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-2xl font-bold text-primary">{transactions.length}</div>
            <div className="text-sm text-muted">Transactions</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">
              +{formatCurrency(totalCredits, account.currency)}
            </div>
            <div className="text-sm text-muted">Credits</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded">
            <div className="text-2xl font-bold text-red-600">
              -{formatCurrency(totalDebits, account.currency)}
            </div>
            <div className="text-sm text-muted">Debits</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">
              {reconciledCount}/{transactions.length}
            </div>
            <div className="text-sm text-muted">Rapprochees</div>
          </div>
        </div>
      </Card>

      {/* Alerte rapprochement */}
      {unreconciledCount > 0 && (
        <Card className="mt-4 border-orange-200 bg-orange-50">
          <div className="flex items-center gap-2 text-orange-700">
            <XCircle size={18} />
            <span className="font-medium">
              {unreconciledCount} transaction(s) non rapprochee(s)
            </span>
          </div>
        </Card>
      )}

      {/* Liste des transactions */}
      <Card title={`Transactions (${transactions.length})`} icon={<FileText size={18} />} className="mt-4">
        {transactions.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th className="text-center">Type</th>
                <th className="text-right">Montant</th>
                <th className="text-center">Rapproche</th>
                <th className="azals-std-field--secondary">Document</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <TransactionRow key={transaction.id} transaction={transaction} currency={account.currency} />
              ))}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <FileText size={32} className="text-muted" />
            <p className="text-muted">Aucune transaction enregistree</p>
          </div>
        )}
      </Card>

      {/* Stats par categorie (ERP only) */}
      <Card title="Repartition par categorie" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium mb-2 text-green-600">Credits par categorie</h4>
            <CategoryBreakdown
              transactions={transactions.filter(isCredit)}
              currency={account.currency}
              type="credit"
            />
          </div>
          <div>
            <h4 className="font-medium mb-2 text-red-600">Debits par categorie</h4>
            <CategoryBreakdown
              transactions={transactions.filter(isDebit)}
              currency={account.currency}
              type="debit"
            />
          </div>
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant ligne transaction
 */
const TransactionRow: React.FC<{ transaction: Transaction; currency: string }> = ({ transaction, currency }) => {
  const isCredit = transaction.type === 'credit';

  return (
    <tr>
      <td className="text-sm">
        <div>{formatDate(transaction.date)}</div>
        {transaction.value_date !== transaction.date && (
          <div className="text-muted text-xs">
            Valeur: {formatDate(transaction.value_date)}
          </div>
        )}
      </td>
      <td>
        <div className="font-medium">{transaction.description}</div>
        {transaction.reference && (
          <div className="text-muted text-xs font-mono">{transaction.reference}</div>
        )}
      </td>
      <td className="text-center">
        {isCredit ? (
          <ArrowDownLeft size={18} className="text-green-600 mx-auto" />
        ) : (
          <ArrowUpRight size={18} className="text-red-600 mx-auto" />
        )}
      </td>
      <td className={`text-right font-medium ${isCredit ? 'text-green-600' : 'text-red-600'}`}>
        {isCredit ? '+' : '-'}{formatCurrency(transaction.amount, currency)}
      </td>
      <td className="text-center">
        {transaction.reconciled ? (
          <CheckCircle2 size={18} className="text-green-600 mx-auto" />
        ) : (
          <XCircle size={18} className="text-gray-400 mx-auto" />
        )}
      </td>
      <td className="azals-std-field--secondary">
        {transaction.linked_document ? (
          <span className="text-sm">
            <span className="azals-badge azals-badge--blue text-xs">
              {transaction.linked_document.type}
            </span>
            <span className="ml-1 font-mono">{transaction.linked_document.number}</span>
          </span>
        ) : (
          <span className="text-muted">-</span>
        )}
      </td>
    </tr>
  );
};

/**
 * Composant repartition par categorie
 */
const CategoryBreakdown: React.FC<{
  transactions: Transaction[];
  currency: string;
  type: 'credit' | 'debit';
}> = ({ transactions, currency, type }) => {
  // Group by category
  const categories = transactions.reduce((acc, t) => {
    const cat = t.category || 'Non categorise';
    if (!acc[cat]) acc[cat] = 0;
    acc[cat] += t.amount;
    return acc;
  }, {} as Record<string, number>);

  const sortedCategories = Object.entries(categories)
    .sort((a, b) => b[1] - a[1]);

  if (sortedCategories.length === 0) {
    return <p className="text-muted text-sm">Aucune transaction</p>;
  }

  return (
    <div className="space-y-2">
      {sortedCategories.map(([category, amount]) => (
        <div key={category} className="flex justify-between items-center p-2 bg-gray-50 rounded">
          <span className="text-sm">{category}</span>
          <span className={`font-medium ${type === 'credit' ? 'text-green-600' : 'text-red-600'}`}>
            {type === 'credit' ? '+' : '-'}{formatCurrency(amount, currency)}
          </span>
        </div>
      ))}
    </div>
  );
};

export default AccountTransactionsTab;
