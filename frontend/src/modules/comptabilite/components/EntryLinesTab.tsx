/**
 * AZALSCORE Module - Comptabilite - Entry Lines Tab
 * Onglet lignes d'ecriture (debit/credit)
 */

import React from 'react';
import { List, Calculator, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Entry, EntryLine } from '../types';
import { formatAccountCode, isEntryBalanced } from '../types';
import { formatCurrency } from '@/utils/formatters';

/**
 * EntryLinesTab - Lignes de l'ecriture
 */
export const EntryLinesTab: React.FC<TabContentProps<Entry>> = ({ data: entry }) => {
  const lines = entry.lines || [];
  const isBalanced = isEntryBalanced(entry);
  const difference = Math.abs(entry.total_debit - entry.total_credit);

  // Grouper par compte pour analyse
  const accountSummary = lines.reduce((acc, line) => {
    const key = line.account_code || line.account_id;
    if (!acc[key]) {
      acc[key] = {
        code: line.account_code || '-',
        name: line.account_name || '-',
        debit: 0,
        credit: 0
      };
    }
    acc[key].debit += line.debit || 0;
    acc[key].credit += line.credit || 0;
    return acc;
  }, {} as Record<string, { code: string; name: string; debit: number; credit: number }>);

  return (
    <div className="azals-std-tab-content">
      {/* Alerte equilibre */}
      {!isBalanced && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertCircle size={20} />
          <div>
            <strong>Ecriture desequilibree</strong>
            <p className="text-sm">
              Difference de {formatCurrency(difference)} entre debit et credit
            </p>
          </div>
        </div>
      )}

      {isBalanced && entry.status === 'DRAFT' && (
        <div className="azals-alert azals-alert--success mb-4">
          <CheckCircle2 size={20} />
          <div>
            <strong>Ecriture equilibree</strong>
            <p className="text-sm">L'ecriture peut etre validee</p>
          </div>
        </div>
      )}

      {/* Liste des lignes */}
      <Card title={`Lignes d'ecriture (${lines.length})`} icon={<List size={18} />}>
        {lines.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="azals-table azals-table--simple">
              <thead>
                <tr>
                  <th style={{ width: '15%' }}>Compte</th>
                  <th style={{ width: '35%' }}>Libelle</th>
                  <th style={{ width: '15%' }} className="text-right">Debit</th>
                  <th style={{ width: '15%' }} className="text-right">Credit</th>
                  <th style={{ width: '20%' }}>Reference</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line, index) => (
                  <LineRow key={line.id || index} line={line} />
                ))}
              </tbody>
              <tfoot>
                <tr className="font-medium bg-gray-50">
                  <td colSpan={2} className="text-right">Total</td>
                  <td className="text-right">{formatCurrency(entry.total_debit)}</td>
                  <td className="text-right">{formatCurrency(entry.total_credit)}</td>
                  <td></td>
                </tr>
                {!isBalanced && (
                  <tr className="text-danger font-medium">
                    <td colSpan={2} className="text-right">Ecart</td>
                    <td colSpan={2} className="text-center">{formatCurrency(difference)}</td>
                    <td></td>
                  </tr>
                )}
              </tfoot>
            </table>
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <List size={32} className="text-muted" />
            <p className="text-muted">Aucune ligne</p>
          </div>
        )}
      </Card>

      {/* Totaux */}
      <Card title="Resume" icon={<Calculator size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-sm text-muted mb-1">Total Debit</div>
            <div className="text-xl font-bold text-blue-600">
              {formatCurrency(entry.total_debit)}
            </div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-sm text-muted mb-1">Total Credit</div>
            <div className="text-xl font-bold text-green-600">
              {formatCurrency(entry.total_credit)}
            </div>
          </div>
          <div className={`text-center p-4 rounded ${isBalanced ? 'bg-green-50' : 'bg-red-50'}`}>
            <div className="text-sm text-muted mb-1">Ecart</div>
            <div className={`text-xl font-bold ${isBalanced ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(difference)}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Resume par compte (ERP only) */}
      {Object.keys(accountSummary).length > 0 && (
        <Card
          title="Resume par compte"
          icon={<Calculator size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <table className="azals-table azals-table--simple azals-table--compact">
            <thead>
              <tr>
                <th>Compte</th>
                <th>Libelle</th>
                <th className="text-right">Debit</th>
                <th className="text-right">Credit</th>
                <th className="text-right">Solde</th>
              </tr>
            </thead>
            <tbody>
              {Object.values(accountSummary).map((summary, idx) => {
                const balance = summary.debit - summary.credit;
                return (
                  <tr key={idx}>
                    <td className="font-mono">{formatAccountCode(summary.code)}</td>
                    <td>{summary.name}</td>
                    <td className="text-right">{summary.debit > 0 ? formatCurrency(summary.debit) : '-'}</td>
                    <td className="text-right">{summary.credit > 0 ? formatCurrency(summary.credit) : '-'}</td>
                    <td className={`text-right font-medium ${balance >= 0 ? 'text-blue-600' : 'text-green-600'}`}>
                      {formatCurrency(Math.abs(balance))} {balance >= 0 ? 'D' : 'C'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
};

/**
 * Composant ligne
 */
interface LineRowProps {
  line: EntryLine;
}

const LineRow: React.FC<LineRowProps> = ({ line }) => {
  return (
    <tr>
      <td>
        <code className="font-mono text-sm">{formatAccountCode(line.account_code || '-')}</code>
        <div className="text-xs text-muted">{line.account_name}</div>
      </td>
      <td>{line.label || '-'}</td>
      <td className="text-right">
        {line.debit > 0 ? (
          <span className="font-medium text-blue-600">{formatCurrency(line.debit)}</span>
        ) : '-'}
      </td>
      <td className="text-right">
        {line.credit > 0 ? (
          <span className="font-medium text-green-600">{formatCurrency(line.credit)}</span>
        ) : '-'}
      </td>
      <td className="text-muted text-sm">{line.reference || '-'}</td>
    </tr>
  );
};

export default EntryLinesTab;
