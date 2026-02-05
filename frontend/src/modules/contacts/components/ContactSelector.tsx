/**
 * AZALS SOUS-PROGRAMME - ContactSelector
 * =======================================
 *
 * Sélecteur de contact réutilisable avec autocomplete.
 * Permet de sélectionner ou créer rapidement un contact.
 *
 * Usage:
 * ```tsx
 * <ContactSelector
 *   value={contactId}
 *   onChange={(contact) => setContactId(contact?.id)}
 *   relationFilter="SUPPLIER"
 *   allowCreate={true}
 *   placeholder="Sélectionner un fournisseur..."
 * />
 * ```
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { contactsApi } from '../api';
import type { ContactLookup, RelationType, EntityType } from '../types';
import { EntityTypeLabels } from '../types';

interface ContactSelectorProps {
  /** ID du contact sélectionné */
  value?: string;
  /** Callback appelé lors de la sélection */
  onChange: (contact: ContactLookup | null) => void;
  /** Filtrer par type de relation (CUSTOMER, SUPPLIER) */
  relationFilter?: RelationType;
  /** Autoriser la création rapide */
  allowCreate?: boolean;
  /** Placeholder du champ */
  placeholder?: string;
  /** Label du champ */
  label?: string;
  /** Champ requis */
  required?: boolean;
  /** Champ désactivé */
  disabled?: boolean;
  /** Classe CSS additionnelle */
  className?: string;
  /** Message d'erreur */
  error?: string;
}

export const ContactSelector: React.FC<ContactSelectorProps> = ({
  value,
  onChange,
  relationFilter,
  allowCreate = false,
  placeholder = 'Rechercher un contact...',
  label,
  required = false,
  disabled = false,
  className = '',
  error,
}) => {
  const [search, setSearch] = useState('');
  const [results, setResults] = useState<ContactLookup[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedContact, setSelectedContact] = useState<ContactLookup | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Charger le contact sélectionné au montage
  useEffect(() => {
    if (value && !selectedContact) {
      contactsApi.get(value).then((contact) => {
        setSelectedContact({
          id: contact.id,
          code: contact.code,
          name: contact.name,
          entity_type: contact.entity_type,
          is_customer: contact.is_customer,
          is_supplier: contact.is_supplier,
          logo_url: contact.logo_url,
        });
        setSearch(contact.name);
      }).catch(() => {
        // Contact non trouvé
      });
    }
  }, [value, selectedContact]);

  // Recherche avec debounce
  const searchContacts = useCallback(async (query: string) => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    try {
      const response = await contactsApi.lookup(relationFilter, query, 10);
      setResults(response.items);
    } catch (err) {
      console.error('Erreur recherche contacts:', err);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, [relationFilter]);

  // Debounce de la recherche
  useEffect(() => {
    const timer = setTimeout(() => {
      if (search && !selectedContact) {
        searchContacts(search);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [search, searchContacts, selectedContact]);

  // Fermer le dropdown au clic extérieur
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (contact: ContactLookup) => {
    setSelectedContact(contact);
    setSearch(contact.name);
    setIsOpen(false);
    onChange(contact);
  };

  const handleClear = () => {
    setSelectedContact(null);
    setSearch('');
    setResults([]);
    onChange(null);
    inputRef.current?.focus();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearch(val);
    setIsOpen(true);
    if (selectedContact && val !== selectedContact.name) {
      setSelectedContact(null);
      onChange(null);
    }
  };

  const handleInputFocus = () => {
    if (search.length >= 2) {
      setIsOpen(true);
    }
  };

  return (
    <div className={`contact-selector ${className}`} ref={dropdownRef}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      <div className="relative">
        <div className="relative">
          {/* Logo du contact sélectionné */}
          {selectedContact?.logo_url && (
            <div className="absolute left-2 top-1/2 transform -translate-y-1/2">
              <img
                src={selectedContact.logo_url}
                alt=""
                className="w-6 h-6 rounded object-cover"
              />
            </div>
          )}

          <input
            ref={inputRef}
            type="text"
            value={search}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            placeholder={placeholder}
            disabled={disabled}
            className={`
              w-full px-3 py-2 border rounded-md shadow-sm
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              ${selectedContact?.logo_url ? 'pl-10' : ''}
              ${selectedContact ? 'bg-blue-50 border-blue-300' : 'border-gray-300'}
              ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}
              ${error ? 'border-red-500' : ''}
            `}
          />

          {/* Badge code */}
          {selectedContact && (
            <span className="absolute right-8 top-1/2 transform -translate-y-1/2 text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
              {selectedContact.code}
            </span>
          )}

          {/* Bouton clear */}
          {selectedContact && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}

          {/* Indicateur de chargement */}
          {isLoading && (
            <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
              <svg className="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          )}
        </div>

        {/* Dropdown des résultats */}
        {isOpen && !disabled && (results.length > 0 || (allowCreate && search.length >= 2)) && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto">
            {results.map((contact) => (
              <button
                key={contact.id}
                type="button"
                onClick={() => handleSelect(contact)}
                className="w-full px-3 py-2 text-left hover:bg-blue-50 flex items-center gap-2 border-b border-gray-100 last:border-b-0"
              >
                {contact.logo_url ? (
                  <img src={contact.logo_url} alt="" className="w-8 h-8 rounded object-cover" />
                ) : (
                  <div className="w-8 h-8 rounded bg-gray-200 flex items-center justify-center text-gray-500 text-sm font-medium">
                    {contact.name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">{contact.name}</div>
                  <div className="text-xs text-gray-500 flex items-center gap-2">
                    <span>{contact.code}</span>
                    <span className="text-gray-300">|</span>
                    <span>{EntityTypeLabels[contact.entity_type]}</span>
                    {contact.is_customer && <span className="bg-green-100 text-green-700 px-1 rounded">Client</span>}
                    {contact.is_supplier && <span className="bg-purple-100 text-purple-700 px-1 rounded">Fournisseur</span>}
                  </div>
                </div>
              </button>
            ))}

            {/* Option créer */}
            {allowCreate && search.length >= 2 && (
              <button
                type="button"
                onClick={() => setShowCreateModal(true)}
                className="w-full px-3 py-2 text-left hover:bg-green-50 flex items-center gap-2 text-green-600 border-t border-gray-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Créer "{search}"</span>
              </button>
            )}

            {/* Aucun résultat */}
            {results.length === 0 && !allowCreate && search.length >= 2 && (
              <div className="px-3 py-2 text-gray-500 text-center">
                Aucun contact trouvé
              </div>
            )}
          </div>
        )}
      </div>

      {error && <p className="mt-1 text-sm text-red-500">{error}</p>}

      {/* Modal de création rapide */}
      {showCreateModal && (
        <QuickCreateModal
          initialName={search}
          relationFilter={relationFilter}
          onClose={() => setShowCreateModal(false)}
          onCreated={(contact) => {
            handleSelect(contact);
            setShowCreateModal(false);
          }}
        />
      )}
    </div>
  );
};

// ============================================================================
// MODAL CRÉATION RAPIDE
// ============================================================================

interface QuickCreateModalProps {
  initialName: string;
  relationFilter?: RelationType;
  onClose: () => void;
  onCreated: (contact: ContactLookup) => void;
}

const QuickCreateModal: React.FC<QuickCreateModalProps> = ({
  initialName,
  relationFilter,
  onClose,
  onCreated,
}) => {
  const [name, setName] = useState(initialName);
  const [entityType, setEntityType] = useState<EntityType>('COMPANY' as EntityType);
  const [isCustomer, setIsCustomer] = useState(relationFilter === 'CUSTOMER' || !relationFilter);
  const [isSupplier, setIsSupplier] = useState(relationFilter === 'SUPPLIER' || !relationFilter);
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setError('Le nom est requis');
      return;
    }

    if (!isCustomer && !isSupplier) {
      setError('Sélectionnez au moins Client ou Fournisseur');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const relationTypes: RelationType[] = [];
      if (isCustomer) relationTypes.push('CUSTOMER' as RelationType);
      if (isSupplier) relationTypes.push('SUPPLIER' as RelationType);

      const contact = await contactsApi.create({
        name: name.trim(),
        entity_type: entityType,
        relation_types: relationTypes,
        email: email || undefined,
        phone: phone || undefined,
      });

      onCreated({
        id: contact.id,
        code: contact.code,
        name: contact.name,
        entity_type: contact.entity_type,
        is_customer: contact.is_customer,
        is_supplier: contact.is_supplier,
        logo_url: contact.logo_url,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la création');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Créer un contact</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Type d'entité */}
          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="entityType"
                checked={entityType === 'COMPANY'}
                onChange={() => setEntityType('COMPANY' as EntityType)}
                className="text-blue-600"
              />
              <span>Société</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="entityType"
                checked={entityType === 'INDIVIDUAL'}
                onChange={() => setEntityType('INDIVIDUAL' as EntityType)}
                className="text-blue-600"
              />
              <span>Particulier</span>
            </label>
          </div>

          {/* Types de relation */}
          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isCustomer}
                onChange={(e) => setIsCustomer(e.target.checked)}
                className="text-green-600 rounded"
              />
              <span>Client</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isSupplier}
                onChange={(e) => setIsSupplier(e.target.checked)}
                className="text-purple-600 rounded"
              />
              <span>Fournisseur</span>
            </label>
          </div>

          {/* Nom */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nom <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Téléphone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {error && (
            <div className="text-red-500 text-sm">{error}</div>
          )}

          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Création...' : 'Créer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ContactSelector;
