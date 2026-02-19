/**
 * AZALSCORE Module - Payments - Payment Details Tab
 * Onglet details techniques du paiement
 */

import React from 'react';
import {
  CreditCard, Hash, Building, Shield, Receipt, Percent
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatCurrency } from '@/utils/formatters';
import {
  METHOD_CONFIG
} from '../types';
import type { Payment } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * PaymentDetailsTab - Details techniques
 */
export const PaymentDetailsTab: React.FC<TabContentProps<Payment>> = ({ data: payment }) => {
  const methodConfig = METHOD_CONFIG[payment.method];

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Methode de paiement */}
        <Card title="Methode de paiement" icon={<CreditCard size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <span>Type</span>
              <div className="flex items-center gap-2">
                <span className="text-2xl">{methodConfig.icon}</span>
                <span className="font-medium">{methodConfig.label}</span>
              </div>
            </div>

            {payment.method === 'CARD' && (
              <>
                {payment.card_brand && (
                  <div className="azals-std-field">
                    <span>Reseau</span>
                    <div className="font-medium">{payment.card_brand}</div>
                  </div>
                )}
                {payment.card_last_four && (
                  <div className="azals-std-field">
                    <span>Numero de carte</span>
                    <div className="font-mono">**** **** **** {payment.card_last_four}</div>
                  </div>
                )}
              </>
            )}

            {payment.method === 'BANK_TRANSFER' && payment.bank_name && (
              <div className="azals-std-field">
                <span>Banque</span>
                <div className="flex items-center gap-2">
                  <Building size={16} className="text-muted" />
                  {payment.bank_name}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Identifiants de transaction */}
        <Card title="Identifiants" icon={<Hash size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <span>Reference paiement</span>
              <div className="font-mono">{payment.reference}</div>
            </div>
            {payment.transaction_id && (
              <div className="azals-std-field">
                <span>ID Transaction (processeur)</span>
                <div className="font-mono text-sm">{payment.transaction_id}</div>
              </div>
            )}
            {payment.authorization_code && (
              <div className="azals-std-field">
                <span>Code d'autorisation</span>
                <div className="font-mono">{payment.authorization_code}</div>
              </div>
            )}
            <div className="azals-std-field azals-std-field--secondary">
              <span>ID interne</span>
              <div className="font-mono text-xs">{payment.id}</div>
            </div>
          </div>
        </Card>

        {/* Montants detailles */}
        <Card title="Montants" icon={<Receipt size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <span>Montant brut</span>
              <div className="text-lg font-medium">
                {formatCurrency(payment.amount, payment.currency)}
              </div>
            </div>
            {payment.fees !== undefined && payment.fees > 0 && (
              <div className="azals-std-field azals-std-field--secondary">
                <span>Frais de traitement</span>
                <div className="text-danger">
                  -{formatCurrency(payment.fees, payment.currency)}
                </div>
              </div>
            )}
            {payment.net_amount !== undefined && (
              <div className="azals-std-field azals-std-field--secondary">
                <span>Montant net</span>
                <div className="text-success font-medium">
                  {formatCurrency(payment.net_amount, payment.currency)}
                </div>
              </div>
            )}
            <div className="azals-std-field">
              <span>Devise</span>
              <div>{payment.currency}</div>
            </div>
          </div>
        </Card>

        {/* Securite */}
        <Card title="Securite" icon={<Shield size={18} />} className="azals-std-field--secondary">
          <div className="space-y-3">
            <div className="azals-std-field">
              <span>Verification 3D Secure</span>
              <div className={payment.metadata?.['3ds_authenticated'] ? 'text-success' : 'text-muted'}>
                {payment.metadata?.['3ds_authenticated'] ? 'Authentifie' : 'Non applicable'}
              </div>
            </div>
            <div className="azals-std-field">
              <span>Code AVS</span>
              <div className="font-mono">
                {payment.metadata?.avs_code || '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <span>Code CVC</span>
              <div className="font-mono">
                {payment.metadata?.cvc_check || '-'}
              </div>
            </div>
          </div>
        </Card>
      </Grid>

      {/* Metadata (ERP only) */}
      {payment.metadata && Object.keys(payment.metadata).length > 0 && (
        <Card title="Metadata" icon={<Percent size={18} />} className="mt-4 azals-std-field--secondary">
          <div className="font-mono text-sm bg-gray-50 p-4 rounded overflow-auto max-h-48">
            <pre>{JSON.stringify(payment.metadata, null, 2)}</pre>
          </div>
        </Card>
      )}
    </div>
  );
};

export default PaymentDetailsTab;
