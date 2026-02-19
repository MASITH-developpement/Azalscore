/**
 * AZALSCORE Module - Marketplace - Seller Info Tab
 * Onglet informations generales du vendeur
 */

import React from 'react';
import {
  User, Building2, Mail, MapPin, CreditCard,
  CheckCircle2, XCircle, Star, Calendar
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatPercent } from '@/utils/formatters';
import { formatRating, SELLER_STATUS_CONFIG } from '../types';
import type { Seller } from '../types';
import type { TabContentProps } from '@ui/standards';

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
            <span className="azals-field__label">Code vendeur</span>
            <div className="azals-field__value font-mono">{seller.code}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Nom / Raison sociale</span>
            <div className="azals-field__value">{seller.name}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Statut</span>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${SELLER_STATUS_CONFIG[seller.status].color}`}>
                {SELLER_STATUS_CONFIG[seller.status].label}
              </span>
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Entreprise</span>
            <div className="azals-field__value">{seller.company_name || '-'}</div>
          </div>
          <div className="azals-field azals-std-field--secondary">
            <span className="azals-field__label">SIRET</span>
            <div className="azals-field__value font-mono">{seller.siret || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Verifie</span>
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
            <span className="azals-field__label">Email</span>
            <div className="azals-field__value">
              <a href={`mailto:${seller.email}`} className="text-primary hover:underline">
                {seller.email}
              </a>
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Telephone</span>
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
            <span className="azals-field__label">Adresse</span>
            <div className="azals-field__value">{seller.address || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Code postal / Ville</span>
            <div className="azals-field__value">
              {seller.postal_code || seller.city
                ? `${seller.postal_code || ''} ${seller.city || ''}`.trim()
                : '-'}
            </div>
          </div>
          <div className="azals-field azals-std-field--secondary">
            <span className="azals-field__label">Pays</span>
            <div className="azals-field__value">{seller.country || 'France'}</div>
          </div>
        </Grid>
      </Card>

      {/* Informations commerciales */}
      <Card title="Informations commerciales" icon={<Building2 size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Taux de commission</span>
            <div className="azals-field__value text-lg font-medium text-primary">
              {formatPercent(seller.commission_rate)}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Note moyenne</span>
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
            <span className="azals-field__label">Membre depuis</span>
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
            <span className="azals-field__label">IBAN</span>
            <div className="azals-field__value font-mono text-sm">
              {seller.bank_iban || '-'}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">BIC</span>
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
