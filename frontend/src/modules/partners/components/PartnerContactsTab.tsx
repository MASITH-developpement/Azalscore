/**
 * AZALSCORE Module - Partners - Contacts Tab
 * Onglet contacts lies au partenaire
 */

import React, { useState } from 'react';
import {
  Users, Mail, Phone, Briefcase, Plus, Star, User
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { getFullName } from '../types';
import type { Partner, Contact } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * PartnerContactsTab - Contacts
 */
export const PartnerContactsTab: React.FC<TabContentProps<Partner>> = ({ data: partner }) => {
  const [_showAddContact, setShowAddContact] = useState(false);
  const contacts = partner.contacts || [];

  return (
    <div className="azals-std-tab-content">
      {/* En-tete */}
      <Card
        title={`Contacts (${contacts.length})`}
        icon={<Users size={18} />}
        actions={
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<Plus size={14} />}
            onClick={() => setShowAddContact(true)}
          >
            Ajouter
          </Button>
        }
      >
        {contacts.length > 0 ? (
          <div className="space-y-3">
            {contacts.map((contact) => (
              <ContactCard key={contact.id} contact={contact} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Users size={32} className="text-muted" />
            <p className="text-muted">Aucun contact enregistre</p>
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<Plus size={14} />}
              onClick={() => setShowAddContact(true)}
              className="mt-2"
            >
              Ajouter un contact
            </Button>
          </div>
        )}
      </Card>

      {/* Informations (ERP only) */}
      <Card
        title="Informations sur les contacts"
        icon={<User size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="text-sm text-muted space-y-2">
          <p>
            Les contacts sont les personnes physiques associees a ce partenaire.
            Ils peuvent etre utilises pour:
          </p>
          <ul className="list-disc list-inside ml-2">
            <li>L&apos;envoi de documents (devis, factures, etc.)</li>
            <li>Les communications commerciales</li>
            <li>Le suivi des interactions</li>
          </ul>
          <p className="mt-3">
            Le contact principal est marque d&apos;une etoile et recoit par defaut
            les communications du partenaire.
          </p>
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant carte contact
 */
interface ContactCardProps {
  contact: Contact;
}

const ContactCard: React.FC<ContactCardProps> = ({ contact }) => {
  return (
    <div className={`p-4 rounded-lg border ${contact.is_primary ? 'border-primary bg-primary-50' : 'border-gray-200 bg-gray-50'}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${contact.is_primary ? 'bg-primary text-white' : 'bg-gray-300 text-gray-600'}`}>
            {contact.first_name?.[0]?.toUpperCase() || contact.last_name?.[0]?.toUpperCase() || '?'}
          </div>
          <div>
            <div className="font-medium flex items-center gap-2">
              {getFullName(contact)}
              {contact.is_primary && (
                <Star size={14} className="text-warning fill-warning" />
              )}
            </div>
            {contact.job_title && (
              <div className="text-sm text-muted flex items-center gap-1">
                <Briefcase size={12} />
                {contact.job_title}
                {contact.department && <span> - {contact.department}</span>}
              </div>
            )}
          </div>
        </div>
        <div className={`text-xs ${contact.is_active ? 'text-success' : 'text-muted'}`}>
          {contact.is_active ? 'Actif' : 'Inactif'}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-4 text-sm">
        {contact.email && (
          <a href={`mailto:${contact.email}`} className="flex items-center gap-1 text-primary hover:underline">
            <Mail size={14} />
            {contact.email}
          </a>
        )}
        {contact.phone && (
          <a href={`tel:${contact.phone}`} className="flex items-center gap-1 text-primary hover:underline">
            <Phone size={14} />
            {contact.phone}
          </a>
        )}
        {contact.mobile && (
          <a href={`tel:${contact.mobile}`} className="flex items-center gap-1 text-muted">
            <Phone size={14} />
            {contact.mobile}
          </a>
        )}
      </div>

      {contact.notes && (
        <div className="mt-2 text-sm text-muted">
          {contact.notes}
        </div>
      )}
    </div>
  );
};

export default PartnerContactsTab;
