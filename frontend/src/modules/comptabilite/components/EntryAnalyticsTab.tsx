/**
 * AZALSCORE Module - Comptabilite - Entry Analytics Tab
 * Onglet analytique et centres de couts
 */

import React from 'react';
import { PieChart, TrendingUp, Target, Building2 } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatCurrency } from '@/utils/formatters';
import type { Entry } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * EntryAnalyticsTab - Analytique
 */
export const EntryAnalyticsTab: React.FC<TabContentProps<Entry>> = ({ data: entry }) => {
  const lines = entry.lines || [];

  // Grouper par centre de cout
  const costCenterBreakdown = lines.reduce((acc, line) => {
    const center = line.cost_center || 'Non affecte';
    if (!acc[center]) {
      acc[center] = { debit: 0, credit: 0, lines: 0 };
    }
    acc[center].debit += line.debit || 0;
    acc[center].credit += line.credit || 0;
    acc[center].lines += 1;
    return acc;
  }, {} as Record<string, { debit: number; credit: number; lines: number }>);

  // Grouper par compte analytique
  const analyticBreakdown = lines.reduce((acc, line) => {
    const account = line.analytic_account || 'Non affecte';
    if (!acc[account]) {
      acc[account] = { debit: 0, credit: 0, lines: 0 };
    }
    acc[account].debit += line.debit || 0;
    acc[account].credit += line.credit || 0;
    acc[account].lines += 1;
    return acc;
  }, {} as Record<string, { debit: number; credit: number; lines: number }>);

  const hasCostCenters = Object.keys(costCenterBreakdown).some(k => k !== 'Non affecte');
  const hasAnalyticAccounts = Object.keys(analyticBreakdown).some(k => k !== 'Non affecte');

  return (
    <div className="azals-std-tab-content">
      {/* Resume analytique */}
      <Card title="Analyse de l'ecriture" icon={<PieChart size={18} />}>
        <Grid cols={4} gap="md">
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-sm text-muted mb-1">Lignes</div>
            <div className="text-2xl font-bold">{lines.length}</div>
          </div>
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
          <div className="text-center p-4 bg-purple-50 rounded">
            <div className="text-sm text-muted mb-1">Comptes touches</div>
            <div className="text-2xl font-bold text-purple-600">
              {new Set(lines.map(l => l.account_id)).size}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Centres de couts */}
      <Card
        title="Repartition par centre de cout"
        icon={<Building2 size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        {hasCostCenters ? (
          <table className="azals-table azals-table--simple azals-table--compact">
            <thead>
              <tr>
                <th>Centre de cout</th>
                <th className="text-right">Lignes</th>
                <th className="text-right">Debit</th>
                <th className="text-right">Credit</th>
                <th className="text-right">Net</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(costCenterBreakdown).map(([center, data]) => {
                const net = data.debit - data.credit;
                return (
                  <tr key={center}>
                    <td className="font-medium">{center}</td>
                    <td className="text-right">{data.lines}</td>
                    <td className="text-right">{formatCurrency(data.debit)}</td>
                    <td className="text-right">{formatCurrency(data.credit)}</td>
                    <td className={`text-right font-medium ${net >= 0 ? 'text-blue-600' : 'text-green-600'}`}>
                      {formatCurrency(Math.abs(net))} {net >= 0 ? 'D' : 'C'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Building2 size={32} className="text-muted" />
            <p className="text-muted">Aucun centre de cout affecte</p>
          </div>
        )}
      </Card>

      {/* Comptes analytiques */}
      <Card
        title="Repartition par compte analytique"
        icon={<Target size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        {hasAnalyticAccounts ? (
          <table className="azals-table azals-table--simple azals-table--compact">
            <thead>
              <tr>
                <th>Compte analytique</th>
                <th className="text-right">Lignes</th>
                <th className="text-right">Debit</th>
                <th className="text-right">Credit</th>
                <th className="text-right">Net</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(analyticBreakdown).map(([account, data]) => {
                const net = data.debit - data.credit;
                return (
                  <tr key={account}>
                    <td className="font-medium">{account}</td>
                    <td className="text-right">{data.lines}</td>
                    <td className="text-right">{formatCurrency(data.debit)}</td>
                    <td className="text-right">{formatCurrency(data.credit)}</td>
                    <td className={`text-right font-medium ${net >= 0 ? 'text-blue-600' : 'text-green-600'}`}>
                      {formatCurrency(Math.abs(net))} {net >= 0 ? 'D' : 'C'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Target size={32} className="text-muted" />
            <p className="text-muted">Aucun compte analytique affecte</p>
          </div>
        )}
      </Card>

      {/* Impact par type de compte */}
      <Card
        title="Impact par nature de compte"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="text-sm text-muted">
          <p>
            Cette ecriture impacte {new Set(lines.map(l => l.account_id)).size} compte(s)
            pour un total de {formatCurrency(entry.total_debit)} en mouvements.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default EntryAnalyticsTab;
