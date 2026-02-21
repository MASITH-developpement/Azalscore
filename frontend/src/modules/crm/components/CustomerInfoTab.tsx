/**
 * AZALSCORE Module - CRM - Customer Info Tab
 * Onglet informations générales du client
 */

import React from 'react';
import {
  User, Building2, Mail, Phone, MapPin, Globe,
  Hash, Calendar, Tag, Briefcase
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import {
  CUSTOMER_TYPE_CONFIG, getContactFullName
} from '../types';
import type { Customer } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * CustomerInfoTab - Informations générales du client
 */
export const CustomerInfoTab: React.FC<TabContentProps<Customer>> = ({ data: customer }) => {
  const contacts = customer.contacts || [];
  const primaryContact = contacts.find(c => c.is_primary);
  const typeConfig = CUSTOMER_TYPE_CONFIG[customer.type];

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Identification */}
        <Card title="Identification" icon={<Building2 size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Hash size={14} />
                Code client
              </span>
              <div className="azals-std-field__value font-mono">{customer.code}</div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Tag size={14} />
                Type
              </span>
              <div className="azals-std-field__value">
                <span className={`azals-badge azals-badge--${typeConfig.color}`}>
                  {typeConfig.label}
                </span>
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Building2 size={14} />
                Nom
              </span>
              <div className="azals-std-field__value font-medium">{customer.name}</div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Raison sociale</span>
              <div className="azals-std-field__value">{customer.legal_name || '-'}</div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span className="azals-std-field__label">
                <Briefcase size={14} />
                Secteur d&apos;activité
              </span>
              <div className="azals-std-field__value">{customer.industry || '-'}</div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span className="azals-std-field__label">Source</span>
              <div className="azals-std-field__value">{customer.source || '-'}</div>
            </div>
          </div>
        </Card>

        {/* Coordonnées */}
        <Card title="Coordonnées" icon={<Phone size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Mail size={14} />
                Email
              </span>
              <div className="azals-std-field__value">
                {customer.email ? (
                  <a href={`mailto:${customer.email}`} className="text-primary hover:underline">
                    {customer.email}
                  </a>
                ) : '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Phone size={14} />
                Téléphone
              </span>
              <div className="azals-std-field__value">
                {customer.phone ? (
                  <a href={`tel:${customer.phone}`} className="text-primary hover:underline">
                    {customer.phone}
                  </a>
                ) : '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">
                <Phone size={14} />
                Mobile
              </span>
              <div className="azals-std-field__value">
                {customer.mobile ? (
                  <a href={`tel:${customer.mobile}`} className="text-primary hover:underline">
                    {customer.mobile}
                  </a>
                ) : '-'}
              </div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span className="azals-std-field__label">
                <Globe size={14} />
                Site web
              </span>
              <div className="azals-std-field__value">
                {customer.website ? (
                  <a href={customer.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    {customer.website}
                  </a>
                ) : '-'}
              </div>
            </div>
          </div>
        </Card>

        {/* Adresse */}
        <Card title="Adresse" icon={<MapPin size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field azals-std-field--full">
              <span className="azals-std-field__label">
                <MapPin size={14} />
                Adresse
              </span>
              <div className="azals-std-field__value">
                {customer.address_line1 || '-'}
                {customer.address_line2 && <div>{customer.address_line2}</div>}
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Code postal</span>
              <div className="azals-std-field__value">{customer.postal_code || '-'}</div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Ville</span>
              <div className="azals-std-field__value">{customer.city || '-'}</div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <span className="azals-std-field__label">Pays</span>
              <div className="azals-std-field__value">{customer.country_code || 'FR'}</div>
            </div>
          </div>
        </Card>

        {/* Informations légales */}
        <Card title="Informations légales" icon={<Briefcase size={18} />} className="azals-std-field--secondary">
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <span className="azals-std-field__label">N° TVA</span>
              <div className="azals-std-field__value font-mono">{customer.tax_id || '-'}</div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">SIRET</span>
              <div className="azals-std-field__value font-mono">{customer.registration_number || '-'}</div>
            </div>
          </div>
        </Card>
      </Grid>

      {/* Contact principal */}
      {primaryContact && (
        <Card title="Contact principal" icon={<User size={18} />} className="mt-4">
          <div className="azals-contact-card">
            <div className="azals-contact-card__avatar">
              <User size={24} />
            </div>
            <div className="azals-contact-card__info">
              <h4 className="font-medium">{getContactFullName(primaryContact)}</h4>
              {primaryContact.job_title && (
                <p className="text-sm text-muted">{primaryContact.job_title}</p>
              )}
              <div className="azals-contact-card__details mt-2">
                {primaryContact.email && (
                  <a href={`mailto:${primaryContact.email}`} className="text-sm text-primary">
                    <Mail size={12} className="mr-1" />
                    {primaryContact.email}
                  </a>
                )}
                {primaryContact.phone && (
                  <a href={`tel:${primaryContact.phone}`} className="text-sm text-primary ml-4">
                    <Phone size={12} className="mr-1" />
                    {primaryContact.phone}
                  </a>
                )}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Autres contacts */}
      {contacts.filter(c => !c.is_primary).length > 0 && (
        <Card title="Autres contacts" icon={<User size={18} />} className="mt-4 azals-std-field--secondary">
          <div className="azals-contacts-list">
            {contacts.filter(c => !c.is_primary).map((contact) => (
              <div key={contact.id} className="azals-contact-item">
                <div className="azals-contact-item__name">
                  {getContactFullName(contact)}
                  {contact.job_title && (
                    <span className="text-muted ml-2">- {contact.job_title}</span>
                  )}
                </div>
                <div className="azals-contact-item__actions">
                  {contact.email && (
                    <a href={`mailto:${contact.email}`} className="azals-btn-icon" title={contact.email}>
                      <Mail size={14} />
                    </a>
                  )}
                  {contact.phone && (
                    <a href={`tel:${contact.phone}`} className="azals-btn-icon" title={contact.phone}>
                      <Phone size={14} />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Notes */}
      {customer.notes && (
        <Card title="Notes" icon={<Tag size={18} />} className="mt-4">
          <p className="text-muted whitespace-pre-wrap">{customer.notes}</p>
        </Card>
      )}

      {/* Métadonnées (ERP only) */}
      <Card
        title="Métadonnées"
        icon={<Calendar size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={4} gap="md">
          <div className="azals-std-field">
            <span className="azals-std-field__label">Date de création</span>
            <div className="azals-std-field__value text-sm">{formatDate(customer.created_at)}</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">Créé par</span>
            <div className="azals-std-field__value text-sm">{customer.created_by || '-'}</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">Dernière modification</span>
            <div className="azals-std-field__value text-sm">{formatDate(customer.updated_at)}</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">Commercial assigné</span>
            <div className="azals-std-field__value text-sm">{customer.assigned_to_name || '-'}</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default CustomerInfoTab;
