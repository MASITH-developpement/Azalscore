/**
 * AZALSCORE Module - Marketplace - Seller Info Tab
 * Onglet informations generales du vendeur
 */

import React from 'react';
import {
  User, Building2, Mail, Phone, MapPin, CreditCard,
  CheckCircle2, XCircle, Star, Calendar
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Seller } from '../types';
import { formatRating, SELLER_STATUS_CONFIG } from '../types';
import { formatDate, formatPercent } from '@/utils/formatters';

/**
 * SellerInfoTab - Informations generales
 */
export const SellerInfoTab: React.FC<TabContentProps<Seller>> = ({ data: seller }) => {
  return (
    <div className="azals-std-tab-content">
      {/* Identification */}
      <Card title="Identification" icon={<User size={18} />}>
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Code vendeur</label>
            <div className="azals-field__value font-mono">{seller.code}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Nom / Raison sociale</label>
            <div className="azals-field__value">{seller.name}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Statut</label>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${SELLER_STATUS_CONFIG[seller.status].color}`}>
                {SELLER_STATUS_CONFIG[seller.status].label}
              </span>
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Entreprise</label>
            <div className="azals-field__value">{seller.company_name || '-'}</div>
          </div>
          <div className="azals-field azals-std-field--secondary">
            <label className="azals-field__label">SIRET</label>
            <div className="azals-field__value font-mono">{seller.siret || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Verifie</label>
            <div className="azals-field__value">
              {seller.is_verified ? (
                <span className="flex items-center gap-1 text-green-600">
                  <CheckCircle2 size={16} /> Oui
                  {seller.verified_at && (
                    <span className="text-muted text-sm ml-2">
                      ({formatDate(seller.verified_at)})
                    </span>
                  )}
                </span>
              ) : (
                <span className="flex items-center gap-1 text-gray-500">
                  <XCircle size={16} /> Non
                </span>
              )}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Contact */}
      <Card title="Contact" icon={<Mail size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Email</label>
            <div className="azals-field__value">
              <a href={`mailto:${seller.email}`} className="text-primary hover:underline">
                {seller.email}
              </a>
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Telephone</label>
            <div className="azals-field__value">
              {seller.phone ? (
                <a href={`tel:${seller.phone}`} className="text-primary hover:underline">
                  {seller.phone}
                </a>
              ) : '-'}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Adresse */}
      <Card title="Adresse" icon={<MapPin size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Adresse</label>
            <div className="azals-field__value">{seller.address || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Code postal / Ville</label>
            <div className="azals-field__value">
              {seller.postal_code || seller.city
                ? `${seller.postal_code || ''} ${seller.city || ''}`.trim()
                : '-'}
            </div>
          </div>
          <div className="azals-field azals-std-field--secondary">
            <label className="azals-field__label">Pays</label>
            <div className="azals-field__value">{seller.country || 'France'}</div>
          </div>
        </Grid>
      </Card>

      {/* Informations commerciales */}
      <Card title="Informations commerciales" icon={<Building2 size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Taux de commission</label>
            <div className="azals-field__value text-lg font-medium text-primary">
              {formatPercent(seller.commission_rate)}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Note moyenne</label>
            <div className="azals-field__value">
              {seller.rating ? (
                <span className="flex items-center gap-1">
                  <Star size={16} className="text-yellow-500 fill-yellow-500" />
                  {formatRating(seller.rating)}
                  {seller.reviews_count !== undefined && (
                    <span className="text-muted text-sm">
                      ({seller.reviews_count} avis)
                    </span>
                  )}
                </span>
              ) : (
                <span className="text-muted">Pas encore note</span>
              )}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Membre depuis</label>
            <div className="azals-field__value flex items-center gap-1">
              <Calendar size={14} className="text-muted" />
              {formatDate(seller.joined_at)}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Coordonnees bancaires (ERP only) */}
      <Card title="Coordonnees bancaires" icon={<CreditCard size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">IBAN</label>
            <div className="azals-field__value font-mono text-sm">
              {seller.bank_iban || '-'}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">BIC</label>
            <div className="azals-field__value font-mono">
              {seller.bank_bic || '-'}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Notes (ERP only) */}
      {seller.notes && (
        <Card title="Notes internes" className="mt-4 azals-std-field--secondary">
          <p className="text-muted whitespace-pre-wrap">{seller.notes}</p>
        </Card>
      )}
    </div>
  );
};

export default SellerInfoTab;
