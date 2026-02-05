/**
 * AZALS MODULE - Contacts Unifiés
 * ================================
 *
 * Module de gestion unifiée des contacts (Clients ET Fournisseurs).
 * Fournit des sous-programmes réutilisables par tous les autres modules.
 *
 * Routes:
 * - /contacts         → Liste des contacts
 * - /contacts/new     → Nouveau contact
 * - /contacts/:id     → Fiche contact
 */

import React, { useState, useEffect } from 'react';
import { Routes, Route, useParams, useNavigate, Link } from 'react-router-dom';

// API et Types
import { contactsApi } from './api';
import type {
  Contact,
  ContactCreate,
  ContactUpdate,
  ContactSummary,
  ContactFilters,
  EntityType,
  RelationType,
} from './types';
import {
  EntityTypeLabels,
  RelationTypeLabels,
  CustomerTypeLabels,
  SupplierStatusLabels,
} from './types';

// Sous-programmes réutilisables
import {
  ContactPersonsManager,
  AddressManager,
  LogoUploader,
} from './components';

// ============================================================================
// COMPOSANT PRINCIPAL (ROUTES)
// ============================================================================

const ContactsModule: React.FC = () => {
  return (
    <Routes>
      <Route index element={<ContactsListPage />} />
      <Route path="new" element={<ContactFormPage />} />
      <Route path=":id" element={<ContactFormPage />} />
    </Routes>
  );
};

export default ContactsModule;

// ============================================================================
// PAGE LISTE DES CONTACTS
// ============================================================================

const ContactsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [contacts, setContacts] = useState<ContactSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState<ContactFilters>({
    page: 1,
    page_size: 20,
  });

  useEffect(() => {
    loadContacts();
  }, [filters]);

  const loadContacts = async () => {
    setIsLoading(true);
    try {
      const response = await contactsApi.list(filters);
      setContacts(response.items);
      setTotal(response.total);
    } catch (err) {
      console.error('Erreur chargement contacts:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6">
      {/* En-tête */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Contacts</h1>
          <p className="text-gray-500">Gestion unifiée des clients et fournisseurs</p>
        </div>
        <button
          onClick={() => navigate('/contacts/new')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Nouveau contact
        </button>
      </div>

      {/* Filtres */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <div className="flex flex-wrap gap-4">
          {/* Recherche */}
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Rechercher..."
              value={filters.search || ''}
              onChange={(e) => setFilters({ ...filters, search: e.target.value, page: 1 })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Type d'entité */}
          <select
            value={filters.entity_type || ''}
            onChange={(e) => setFilters({ ...filters, entity_type: e.target.value as EntityType || undefined, page: 1 })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Tous les types</option>
            <option value="COMPANY">Sociétés</option>
            <option value="INDIVIDUAL">Particuliers</option>
          </select>

          {/* Type de relation */}
          <select
            value={filters.relation_type || ''}
            onChange={(e) => setFilters({ ...filters, relation_type: e.target.value as RelationType || undefined, page: 1 })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Clients & Fournisseurs</option>
            <option value="CUSTOMER">Clients uniquement</option>
            <option value="SUPPLIER">Fournisseurs uniquement</option>
          </select>
        </div>
      </div>

      {/* Tableau */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Contact</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Relation</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Téléphone</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Chargement...
                </td>
              </tr>
            ) : contacts.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Aucun contact trouvé
                </td>
              </tr>
            ) : (
              contacts.map((contact) => (
                <tr
                  key={contact.id}
                  onClick={() => navigate(`/contacts/${contact.id}`)}
                  className="hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {contact.logo_url ? (
                        <img src={contact.logo_url} alt="" className="w-10 h-10 rounded-full object-cover" />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 font-medium">
                          {contact.name.charAt(0).toUpperCase()}
                        </div>
                      )}
                      <div>
                        <div className="font-medium text-gray-900">{contact.name}</div>
                        <div className="text-xs text-gray-500">{contact.code}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded ${
                      contact.entity_type === 'COMPANY' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
                    }`}>
                      {EntityTypeLabels[contact.entity_type]}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {contact.is_customer && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Client</span>
                      )}
                      {contact.is_supplier && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">Fournisseur</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{contact.email || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{contact.phone || '-'}</td>
                  <td className="px-4 py-3">
                    {contact.is_active ? (
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Actif</span>
                    ) : (
                      <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">Inactif</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {total > filters.page_size! && (
          <div className="px-4 py-3 border-t border-gray-200 flex justify-between items-center">
            <div className="text-sm text-gray-500">
              {((filters.page! - 1) * filters.page_size!) + 1} - {Math.min(filters.page! * filters.page_size!, total)} sur {total}
            </div>
            <div className="flex gap-2">
              <button
                disabled={filters.page === 1}
                onClick={() => setFilters({ ...filters, page: filters.page! - 1 })}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                Précédent
              </button>
              <button
                disabled={filters.page! * filters.page_size! >= total}
                onClick={() => setFilters({ ...filters, page: filters.page! + 1 })}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                Suivant
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// PAGE FORMULAIRE CONTACT
// ============================================================================

const ContactFormPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = !id;

  const [contact, setContact] = useState<Contact | null>(null);
  const [isLoading, setIsLoading] = useState(!isNew);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  // État du formulaire
  const [formData, setFormData] = useState<ContactCreate>({
    entity_type: 'COMPANY' as EntityType,
    relation_types: ['CUSTOMER' as RelationType],
    name: '',
    email: '',
    phone: '',
  });

  useEffect(() => {
    if (id) {
      loadContact(id);
    }
  }, [id]);

  const loadContact = async (contactId: string) => {
    setIsLoading(true);
    try {
      const data = await contactsApi.get(contactId);
      setContact(data);
      setFormData({
        entity_type: data.entity_type,
        relation_types: data.relation_types,
        name: data.name,
        legal_name: data.legal_name,
        first_name: data.first_name,
        last_name: data.last_name,
        email: data.email,
        phone: data.phone,
        mobile: data.mobile,
        website: data.website,
        tax_id: data.tax_id,
        registration_number: data.registration_number,
        legal_form: data.legal_form,
        notes: data.notes,
        internal_notes: data.internal_notes,
        customer_type: data.customer_type,
        customer_payment_terms: data.customer_payment_terms,
        supplier_status: data.supplier_status,
        supplier_type: data.supplier_type,
        supplier_payment_terms: data.supplier_payment_terms,
      });
    } catch (err) {
      setError('Erreur chargement du contact');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: keyof ContactCreate, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleRelationType = (type: RelationType) => {
    const current = formData.relation_types || [];
    if (current.includes(type)) {
      if (current.length > 1) {
        handleChange('relation_types', current.filter((t) => t !== type));
      }
    } else {
      handleChange('relation_types', [...current, type]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError('');

    try {
      if (isNew) {
        const newContact = await contactsApi.create(formData);
        navigate(`/contacts/${newContact.id}`);
      } else {
        await contactsApi.update(id!, formData as ContactUpdate);
        await loadContact(id!);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur sauvegarde');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Supprimer ce contact ?')) return;
    try {
      await contactsApi.delete(id!);
      navigate('/contacts');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur suppression');
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const isCustomer = formData.relation_types?.includes('CUSTOMER' as RelationType);
  const isSupplier = formData.relation_types?.includes('SUPPLIER' as RelationType);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* En-tête */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <Link to="/contacts" className="text-blue-600 hover:underline text-sm mb-1 block">
            &larr; Retour aux contacts
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            {isNew ? 'Nouveau contact' : contact?.display_name || 'Contact'}
          </h1>
          {contact && <p className="text-gray-500">{contact.code}</p>}
        </div>
        {!isNew && (
          <button
            onClick={handleDelete}
            className="px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50"
          >
            Supprimer
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg">{error}</div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-3 gap-6">
          {/* Colonne principale */}
          <div className="col-span-2 space-y-6">
            {/* Type d'entité et relation */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 mb-4">Type de contact</h3>

              {/* Entité */}
              <div className="flex gap-4 mb-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="entityType"
                    checked={formData.entity_type === 'COMPANY'}
                    onChange={() => handleChange('entity_type', 'COMPANY' as EntityType)}
                    className="text-blue-600"
                  />
                  <span className="text-sm">Société</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="entityType"
                    checked={formData.entity_type === 'INDIVIDUAL'}
                    onChange={() => handleChange('entity_type', 'INDIVIDUAL' as EntityType)}
                    className="text-blue-600"
                  />
                  <span className="text-sm">Particulier</span>
                </label>
              </div>

              {/* Relation */}
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isCustomer}
                    onChange={() => toggleRelationType('CUSTOMER' as RelationType)}
                    className="rounded text-green-600"
                  />
                  <span className="text-sm">Client</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isSupplier}
                    onChange={() => toggleRelationType('SUPPLIER' as RelationType)}
                    className="rounded text-purple-600"
                  />
                  <span className="text-sm">Fournisseur</span>
                </label>
              </div>
            </div>

            {/* Identification */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 mb-4">Identification</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {formData.entity_type === 'COMPANY' ? 'Raison sociale' : 'Nom complet'} *
                  </label>
                  <input
                    type="text"
                    value={formData.name || ''}
                    onChange={(e) => handleChange('name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>

                {formData.entity_type === 'COMPANY' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">SIRET</label>
                      <input
                        type="text"
                        value={formData.registration_number || ''}
                        onChange={(e) => handleChange('registration_number', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">N° TVA</label>
                      <input
                        type="text"
                        value={formData.tax_id || ''}
                        onChange={(e) => handleChange('tax_id', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Forme juridique</label>
                      <input
                        type="text"
                        value={formData.legal_form || ''}
                        onChange={(e) => handleChange('legal_form', e.target.value)}
                        placeholder="SAS, SARL, EURL..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </>
                )}

                {formData.entity_type === 'INDIVIDUAL' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
                      <input
                        type="text"
                        value={formData.first_name || ''}
                        onChange={(e) => handleChange('first_name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                      <input
                        type="text"
                        value={formData.last_name || ''}
                        onChange={(e) => handleChange('last_name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Coordonnées */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 mb-4">Coordonnées</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) => handleChange('email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                  <input
                    type="tel"
                    value={formData.phone || ''}
                    onChange={(e) => handleChange('phone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mobile</label>
                  <input
                    type="tel"
                    value={formData.mobile || ''}
                    onChange={(e) => handleChange('mobile', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Site web</label>
                  <input
                    type="url"
                    value={formData.website || ''}
                    onChange={(e) => handleChange('website', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Personnes de contact (si édition) */}
            {contact && (
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="font-medium text-gray-900 mb-4">Personnes de contact</h3>
                <ContactPersonsManager contactId={contact.id} />
              </div>
            )}

            {/* Adresses (si édition) */}
            {contact && (
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="font-medium text-gray-900 mb-4">Adresses</h3>
                <AddressManager contactId={contact.id} />
              </div>
            )}
          </div>

          {/* Colonne latérale */}
          <div className="space-y-6">
            {/* Logo */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <LogoUploader
                contactId={contact?.id}
                value={contact?.logo_url}
                label="Logo / Photo"
                size="lg"
              />
            </div>

            {/* Boutons d'action */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <button
                type="submit"
                disabled={isSaving}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isSaving ? 'Enregistrement...' : 'Enregistrer'}
              </button>
            </div>

            {/* Notes */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 mb-4">Notes</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes publiques</label>
                  <textarea
                    value={formData.notes || ''}
                    onChange={(e) => handleChange('notes', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes internes</label>
                  <textarea
                    value={formData.internal_notes || ''}
                    onChange={(e) => handleChange('internal_notes', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};
