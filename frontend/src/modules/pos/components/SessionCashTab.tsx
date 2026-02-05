/**
 * AZALSCORE Module - POS - Session Cash Tab
 * Onglet gestion de caisse de la session
 */

import React from 'react';
import {
  Banknote, ArrowUpCircle, ArrowDownCircle, AlertTriangle,
  CheckCircle2, Calculator, TrendingUp, TrendingDown
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { POSSession, CashMovement } from '../types';
import {
  CASH_MOVEMENT_TYPE_CONFIG,
  hasCashDifference, hasSignificantDifference, isSessionClosed
} from '../types';
import { formatCurrency, formatDateTime, formatTime } from '@/utils/formatters';

/**
 * SessionCashTab - Gestion de caisse
 */
export const SessionCashTab: React.FC<TabContentProps<POSSession>> = ({ data: session }) => {
  const cashMovements = session.cash_movements || [];
  const deposits = cashMovements.filter(m => m.type === 'DEPOSIT');
  const withdrawals = cashMovements.filter(m => m.type === 'WITHDRAWAL');
  const adjustments = cashMovements.filter(m => m.type === 'ADJUSTMENT');

  const totalDeposits = deposits.reduce((sum, m) => sum + m.amount, 0);
  const totalWithdrawals = withdrawals.reduce((sum, m) => sum + m.amount, 0);

  return (
    <div className="azals-std-tab-content">
      {/* Soldes de caisse */}
      <Card title="Soldes de caisse" icon={<Banknote size={18} />}>
        <Grid cols={4} gap="md">
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-sm text-muted mb-1">Ouverture</div>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(session.opening_balance)}
            </div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-sm text-muted mb-1">Encaissements especes</div>
            <div className="text-2xl font-bold text-green-600">
              + {formatCurrency(session.cash_payments)}
            </div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded">
            <div className="text-sm text-muted mb-1">Mouvements nets</div>
            <div className="text-2xl font-bold text-orange-600">
              {formatCurrency(totalDeposits - totalWithdrawals)}
            </div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded">
            <div className="text-sm text-muted mb-1">Solde attendu</div>
            <div className="text-2xl font-bold text-purple-600">
              {formatCurrency(session.expected_balance || 0)}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Ecart de caisse */}
      {isSessionClosed(session) && (
        <Card
          title="Cloture de caisse"
          icon={hasCashDifference(session) ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
          className={`mt-4 ${hasSignificantDifference(session) ? 'border-red-200 bg-red-50' : ''}`}
        >
          <Grid cols={3} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Solde declare</label>
              <div className="azals-field__value text-xl font-bold">
                {formatCurrency(session.closing_balance || 0)}
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Solde attendu</label>
              <div className="azals-field__value text-xl font-bold">
                {formatCurrency(session.expected_balance || 0)}
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Ecart</label>
              <div className={`azals-field__value text-xl font-bold ${
                !hasCashDifference(session) ? 'text-green-600' :
                hasSignificantDifference(session) ? 'text-red-600' : 'text-orange-600'
              }`}>
                {session.cash_difference !== undefined ? (
                  <>
                    {session.cash_difference >= 0 ? '+' : ''}
                    {formatCurrency(session.cash_difference)}
                  </>
                ) : '-'}
              </div>
            </div>
          </Grid>

          {hasSignificantDifference(session) && (
            <div className="mt-4 p-3 bg-red-100 rounded flex items-center gap-2 text-red-700">
              <AlertTriangle size={18} />
              <span className="font-medium">
                Ecart de caisse significatif detecte - verification requise
              </span>
            </div>
          )}

          {!hasCashDifference(session) && (
            <div className="mt-4 p-3 bg-green-100 rounded flex items-center gap-2 text-green-700">
              <CheckCircle2 size={18} />
              <span className="font-medium">Caisse equilibree</span>
            </div>
          )}
        </Card>
      )}

      {/* Mouvements de caisse */}
      <Card title="Mouvements de caisse" icon={<Calculator size={18} />} className="mt-4">
        {cashMovements.length > 0 ? (
          <div className="space-y-3">
            {cashMovements.map((movement) => (
              <CashMovementCard key={movement.id} movement={movement} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Calculator size={32} className="text-muted" />
            <p className="text-muted">Aucun mouvement de caisse</p>
          </div>
        )}
      </Card>

      {/* Resume des mouvements (ERP only) */}
      <Card
        title="Resume des mouvements"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={3} gap="md">
          <div className="p-3 bg-green-50 rounded">
            <div className="flex items-center gap-2 mb-2">
              <ArrowUpCircle size={18} className="text-green-600" />
              <span className="font-medium">Depots</span>
            </div>
            <div className="text-lg font-bold text-green-600">
              {formatCurrency(totalDeposits)}
            </div>
            <div className="text-sm text-muted">{deposits.length} operation(s)</div>
          </div>
          <div className="p-3 bg-red-50 rounded">
            <div className="flex items-center gap-2 mb-2">
              <ArrowDownCircle size={18} className="text-red-600" />
              <span className="font-medium">Retraits</span>
            </div>
            <div className="text-lg font-bold text-red-600">
              {formatCurrency(totalWithdrawals)}
            </div>
            <div className="text-sm text-muted">{withdrawals.length} operation(s)</div>
          </div>
          <div className="p-3 bg-blue-50 rounded">
            <div className="flex items-center gap-2 mb-2">
              <Calculator size={18} className="text-blue-600" />
              <span className="font-medium">Ajustements</span>
            </div>
            <div className="text-lg font-bold text-blue-600">
              {adjustments.length}
            </div>
            <div className="text-sm text-muted">correction(s)</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

/**
 * Composant carte de mouvement
 */
const CashMovementCard: React.FC<{ movement: CashMovement }> = ({ movement }) => {
  const config = CASH_MOVEMENT_TYPE_CONFIG[movement.type];

  const getIcon = () => {
    switch (movement.type) {
      case 'DEPOSIT':
        return <ArrowUpCircle size={18} className="text-green-600" />;
      case 'WITHDRAWAL':
        return <ArrowDownCircle size={18} className="text-red-600" />;
      case 'ADJUSTMENT':
        return <Calculator size={18} className="text-blue-600" />;
    }
  };

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded">
      {getIcon()}
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className={`azals-badge azals-badge--${config.color}`}>
            {config.label}
          </span>
          <span className="text-sm text-muted">
            {formatTime(movement.performed_at)}
          </span>
        </div>
        <p className="text-sm mt-1">{movement.reason}</p>
        {movement.performed_by && (
          <p className="text-xs text-muted mt-1">Par: {movement.performed_by}</p>
        )}
      </div>
      <div className={`text-lg font-bold ${
        movement.type === 'WITHDRAWAL' ? 'text-red-600' : 'text-green-600'
      }`}>
        {movement.type === 'WITHDRAWAL' ? '-' : '+'}{formatCurrency(movement.amount)}
      </div>
    </div>
  );
};

export default SessionCashTab;
