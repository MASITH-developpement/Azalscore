/**
 * AZALSCORE Module - Treasury - Account Info Tab
 * Onglet informations generales du compte bancaire
 */

import React from 'react';
import {
  Building2, CreditCard, Calendar, CheckCircle2, XCircle,
  Star, RefreshCw, Mail, Phone, User
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { BankAccount } from '../types';
import { formatDate, formatDateTime, formatIBAN, formatCurrency } from '@/utils/formatters';
import {
  ACCOUNT_TYPE_CONFIG
} from '../types';

/**
 * AccountInfoTab - Informations generales
 */
export const AccountInfoTab: React.FC<TabContentProps<BankAccount>> = ({ data: account }) => {
  return (
    <div className="azals-std-tab-content">
      {/* Identification */}
      <Card title="Identification" icon={<Building2 size={18} />}>
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Nom du compte</label>
            <div className="azals-field__value">{account.name}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Banque</label>
            <div className="azals-field__value">{account.bank_name}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Statut</label>
            <div className="azals-field__value">
              {account.is_active ? (
                <span className="azals-badge azals-badge--green">Actif</span>
              ) : (
                <span className="azals-badge azals-badge--gray">Inactif</span>
              )}
            </div>
          </div>
          {account.code && (
            <div className="azals-field azals-std-field--secondary">
              <label className="azals-field__label">Code interne</label>
              <div className="azals-field__value font-mono">{account.code}</div>
            </div>
          )}
          {account.account_type && (
            <div className="azals-field">
              <label className="azals-field__label">Type de compte</label>
              <div className="azals-field__value">
                <span className={`azals-badge azals-badge--${ACCOUNT_TYPE_CONFIG[account.account_type]?.color || 'blue'}`}>
                  {ACCOUNT_TYPE_CONFIG[account.account_type]?.label || account.account_type}
                </span>
              </div>
            </div>
          )}
          <div className="azals-field">
            <label className="azals-field__label">Compte par defaut</label>
            <div className="azals-field__value">
              {account.is_default ? (
                <span className="flex items-center gap-1 text-yellow-600">
                  <Star size={16} className="fill-yellow-500" /> Oui
                </span>
              ) : (
                <span className="text-muted">Non</span>
              )}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Coordonnees bancaires */}
      <Card title="Coordonnees bancaires" icon={<CreditCard size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">IBAN</label>
            <div className="azals-field__value font-mono text-sm">
              {formatIBAN(account.iban)}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">BIC / SWIFT</label>
            <div className="azals-field__value font-mono">{account.bic}</div>
          </div>
          {account.account_number && (
            <div className="azals-field azals-std-field--secondary">
              <label className="azals-field__label">Numero de compte</label>
              <div className="azals-field__value font-mono">{account.account_number}</div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Soldes */}
      <Card title="Situation financiere" icon={<CreditCard size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Solde actuel</label>
            <div className={`azals-field__value text-xl font-bold ${account.balance < 0 ? 'text-red-600' : 'text-green-600'}`}>
              {formatCurrency(account.balance, account.currency)}
            </div>
          </div>
          {account.available_balance !== undefined && (
            <div className="azals-field">
              <label className="azals-field__label">Solde disponible</label>
              <div className="azals-field__value text-lg font-medium">
                {formatCurrency(account.available_balance, account.currency)}
              </div>
            </div>
          )}
          <div className="azals-field">
            <label className="azals-field__label">Devise</label>
            <div className="azals-field__value">{account.currency}</div>
          </div>
        </Grid>

        {(account.pending_in !== undefined || account.pending_out !== undefined) && (
          <div className="mt-4 pt-4 border-t">
            <Grid cols={2} gap="md">
              {account.pending_in !== undefined && (
                <div className="azals-field">
                  <label className="azals-field__label">Encaissements en attente</label>
                  <div className="azals-field__value text-green-600">
                    +{formatCurrency(account.pending_in, account.currency)}
                  </div>
                </div>
              )}
              {account.pending_out !== undefined && (
                <div className="azals-field">
                  <label className="azals-field__label">Decaissements prevus</label>
                  <div className="azals-field__value text-red-600">
                    -{formatCurrency(account.pending_out, account.currency)}
                  </div>
                </div>
              )}
            </Grid>
          </div>
        )}
      </Card>

      {/* Synchronisation */}
      <Card title="Synchronisation" icon={<RefreshCw size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          {account.last_sync && (
            <div className="azals-field">
              <label className="azals-field__label">Derniere synchronisation</label>
              <div className="azals-field__value flex items-center gap-1">
                <RefreshCw size={14} className="text-muted" />
                {formatDateTime(account.last_sync)}
              </div>
            </div>
          )}
          {account.last_statement_date && (
            <div className="azals-field">
              <label className="azals-field__label">Dernier releve</label>
              <div className="azals-field__value">
                {formatDate(account.last_statement_date)}
              </div>
            </div>
          )}
          {account.opening_date && (
            <div className="azals-field azals-std-field--secondary">
              <label className="azals-field__label">Date d'ouverture</label>
              <div className="azals-field__value flex items-center gap-1">
                <Calendar size={14} className="text-muted" />
                {formatDate(account.opening_date)}
              </div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Contact bancaire (ERP only) */}
      {(account.contact_name || account.contact_phone || account.contact_email) && (
        <Card title="Contact bancaire" icon={<User size={18} />} className="mt-4 azals-std-field--secondary">
          <Grid cols={3} gap="md">
            {account.contact_name && (
              <div className="azals-field">
                <label className="azals-field__label">Nom du contact</label>
                <div className="azals-field__value">{account.contact_name}</div>
              </div>
            )}
            {account.contact_phone && (
              <div className="azals-field">
                <label className="azals-field__label">Telephone</label>
                <div className="azals-field__value">
                  <a href={`tel:${account.contact_phone}`} className="text-primary hover:underline flex items-center gap-1">
                    <Phone size={14} />
                    {account.contact_phone}
                  </a>
                </div>
              </div>
            )}
            {account.contact_email && (
              <div className="azals-field">
                <label className="azals-field__label">Email</label>
                <div className="azals-field__value">
                  <a href={`mailto:${account.contact_email}`} className="text-primary hover:underline flex items-center gap-1">
                    <Mail size={14} />
                    {account.contact_email}
                  </a>
                </div>
              </div>
            )}
          </Grid>
        </Card>
      )}

      {/* Notes (ERP only) */}
      {account.notes && (
        <Card title="Notes internes" className="mt-4 azals-std-field--secondary">
          <p className="text-muted whitespace-pre-wrap">{account.notes}</p>
        </Card>
      )}
    </div>
  );
};

export default AccountInfoTab;
