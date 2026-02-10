/**
 * AZALS SOUS-PROGRAMME - AddressManager
 * =====================================
 *
 * Gestionnaire des adresses multiples (Facturation, Livraison, Chantier, etc.)
 *
 * Usage:
 * ```tsx
 * <AddressManager
 *   contactId={contact.id}
 *   types={['BILLING', 'SHIPPING', 'SITE']}
 *   allowMultiple={true}
 * />
 * ```
 */

import React, { useState, useEffect } from 'react';
import { contactAddressesApi } from '../api';
import {
  AddressType,
  AddressTypeLabels,
} from '../types';
import type {
  ContactAddress,
  ContactAddressCreate,
  ContactAddressUpdate,
} from '../types';
import { AddressAutocomplete } from '@/modules/enrichment';
import type { AddressSuggestion } from '@/modules/enrichment';

interface AddressManagerProps {
  /** ID du contact parent */
  contactId: string;
  /** Types d'adresses disponibles */
  types?: AddressType[];
  /** Autoriser plusieurs adresses du même type */
  allowMultiple?: boolean;
  /** Mode lecture seule */
  readOnly?: boolean;
  /** Classe CSS additionnelle */
  className?: string;
  /** Callback après modification */
  onChange?: (addresses: ContactAddress[]) => void;
}

export const AddressManager: React.FC<AddressManagerProps> = ({
  contactId,
  types,
  allowMultiple = true,
  readOnly = false,
  className = '',
  onChange,
}) => {
  const [addresses, setAddresses] = useState<ContactAddress[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [error, setError] = useState('');

  const availableTypes = types || Object.values(AddressType);

  // Charger les adresses
  useEffect(() => {
    loadAddresses();
  }, [contactId]);

  const loadAddresses = async () => {
    setIsLoading(true);
    try {
      const data = await contactAddressesApi.list(contactId);
      setAddresses(data);
      onChange?.(data);
    } catch (err) {
      setError('Erreur chargement des adresses');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdd = async (data: ContactAddressCreate) => {
    try {
      const newAddress = await contactAddressesApi.create(contactId, data);
      const updatedAddresses = [...addresses, newAddress];
      setAddresses(updatedAddresses);
      setShowAddForm(false);
      onChange?.(updatedAddresses);
    } catch (err) {
      throw err;
    }
  };

  const handleUpdate = async (addressId: string, data: ContactAddressUpdate) => {
    try {
      const updated = await contactAddressesApi.update(contactId, addressId, data);
      const updatedAddresses = addresses.map((a) => (a.id === addressId ? updated : a));
      setAddresses(updatedAddresses);
      setEditingId(null);
      onChange?.(updatedAddresses);
    } catch (err) {
      throw err;
    }
  };

  const handleDelete = async (addressId: string) => {
    if (!confirm('Supprimer cette adresse ?')) return;
    try {
      await contactAddressesApi.delete(contactId, addressId);
      const updatedAddresses = addresses.filter((a) => a.id !== addressId);
      setAddresses(updatedAddresses);
      onChange?.(updatedAddresses);
    } catch (err) {
      setError('Erreur lors de la suppression');
    }
  };

  const handleSetDefault = async (addressId: string) => {
    try {
      await handleUpdate(addressId, { is_default: true });
    } catch (err) {
      setError('Erreur lors de la mise à jour');
    }
  };

  if (isLoading) {
    return (
      <div className={`address-manager ${className}`}>
        <div className="animate-pulse space-y-2">
          <div className="h-24 bg-gray-200 rounded"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  // Grouper par type d'adresse
  const groupedAddresses = availableTypes.reduce((acc, type) => {
    acc[type] = addresses.filter((a) => a.address_type === type);
    return acc;
  }, {} as Record<AddressType, ContactAddress[]>);

  return (
    <div className={`address-manager ${className}`}>
      {error && (
        <div className="mb-2 p-2 bg-red-50 text-red-600 rounded text-sm">{error}</div>
      )}

      {/* Groupes par type */}
      <div className="space-y-4">
        {availableTypes.map((type) => (
          <div key={type} className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-3 py-2 border-b border-gray-200 flex justify-between items-center">
              <h4 className="font-medium text-gray-700 flex items-center gap-2">
                {getAddressIcon(type)}
                {AddressTypeLabels[type]}
                <span className="text-xs text-gray-500">({groupedAddresses[type].length})</span>
              </h4>
            </div>

            <div className="p-2 space-y-2">
              {groupedAddresses[type].map((address) => (
                <div key={address.id}>
                  {editingId === address.id ? (
                    <AddressForm
                      address={address}
                      types={availableTypes}
                      onSubmit={(data) => handleUpdate(address.id, data)}
                      onCancel={() => setEditingId(null)}
                    />
                  ) : (
                    <AddressCard
                      address={address}
                      readOnly={readOnly}
                      onEdit={() => setEditingId(address.id)}
                      onDelete={() => handleDelete(address.id)}
                      onSetDefault={() => handleSetDefault(address.id)}
                    />
                  )}
                </div>
              ))}

              {groupedAddresses[type].length === 0 && (
                <div className="text-gray-400 text-sm text-center py-3">
                  Aucune adresse {AddressTypeLabels[type].toLowerCase()}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Formulaire d'ajout */}
      {showAddForm && (
        <div className="mt-4">
          <AddressForm
            types={availableTypes}
            onSubmit={handleAdd}
            onCancel={() => setShowAddForm(false)}
          />
        </div>
      )}

      {/* Bouton ajouter */}
      {!readOnly && !showAddForm && (
        <button
          type="button"
          onClick={() => setShowAddForm(true)}
          className="mt-4 w-full py-2 border-2 border-dashed border-gray-300 rounded-md text-gray-500 hover:border-blue-400 hover:text-blue-500 flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Ajouter une adresse
        </button>
      )}
    </div>
  );
};

// ============================================================================
// HELPERS
// ============================================================================

const getAddressIcon = (type: AddressType) => {
  switch (type) {
    case AddressType.BILLING:
      return (
        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
        </svg>
      );
    case AddressType.SHIPPING:
      return (
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
        </svg>
      );
    case AddressType.SITE:
      return (
        <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      );
    case AddressType.HEAD_OFFICE:
      return (
        <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      );
    default:
      return (
        <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      );
  }
};

// ============================================================================
// CARTE ADRESSE
// ============================================================================

interface AddressCardProps {
  address: ContactAddress;
  readOnly: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onSetDefault: () => void;
}

const AddressCard: React.FC<AddressCardProps> = ({
  address,
  readOnly,
  onEdit,
  onDelete,
  onSetDefault,
}) => {
  return (
    <div className={`
      p-3 border rounded-md
      ${address.is_default ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-white'}
    `}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          {/* Label et badge par défaut */}
          <div className="flex items-center gap-2 mb-1">
            {address.label && (
              <span className="font-medium text-gray-900">{address.label}</span>
            )}
            {address.is_default && (
              <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">Par défaut</span>
            )}
          </div>

          {/* Adresse complète */}
          <div className="text-sm text-gray-600">
            {address.address_line1 && <div>{address.address_line1}</div>}
            {address.address_line2 && <div>{address.address_line2}</div>}
            <div>
              {address.postal_code} {address.city}
              {address.state && `, ${address.state}`}
            </div>
            {address.country_code && address.country_code !== 'FR' && (
              <div>{address.country_code}</div>
            )}
          </div>

          {/* Contact sur site */}
          {(address.contact_name || address.contact_phone) && (
            <div className="mt-2 text-sm text-gray-500 flex items-center gap-2">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              {address.contact_name}
              {address.contact_phone && ` - ${address.contact_phone}`}
            </div>
          )}
        </div>

        {/* Actions */}
        {!readOnly && (
          <div className="flex items-center gap-1">
            {!address.is_default && (
              <button
                type="button"
                onClick={onSetDefault}
                title="Définir par défaut"
                className="p-1.5 text-gray-400 hover:text-blue-600 rounded"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
            )}
            <button
              type="button"
              onClick={onEdit}
              className="p-1.5 text-gray-400 hover:text-blue-600 rounded"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              type="button"
              onClick={onDelete}
              className="p-1.5 text-gray-400 hover:text-red-600 rounded"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// FORMULAIRE ADRESSE
// ============================================================================

interface AddressFormProps {
  address?: ContactAddress;
  types: AddressType[];
  onSubmit: (data: ContactAddressCreate | ContactAddressUpdate) => Promise<void>;
  onCancel: () => void;
}

const AddressForm: React.FC<AddressFormProps> = ({
  address,
  types,
  onSubmit,
  onCancel,
}) => {
  const [formData, setFormData] = useState<ContactAddressCreate>({
    address_type: address?.address_type || types[0] || AddressType.BILLING,
    label: address?.label || '',
    address_line1: address?.address_line1 || '',
    address_line2: address?.address_line2 || '',
    city: address?.city || '',
    postal_code: address?.postal_code || '',
    state: address?.state || '',
    country_code: address?.country_code || 'FR',
    contact_name: address?.contact_name || '',
    contact_phone: address?.contact_phone || '',
    is_default: address?.is_default || false,
    notes: address?.notes || '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field: keyof ContactAddressCreate, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Handle address autocomplete selection
  const handleAddressSelect = (suggestion: AddressSuggestion) => {
    setFormData((prev) => ({
      ...prev,
      address_line1: suggestion.address_line1 || suggestion.label.split(',')[0] || '',
      postal_code: suggestion.postal_code,
      city: suggestion.city,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      await onSubmit(formData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-3 border border-blue-200 rounded-md bg-blue-50 space-y-3">
      <div className="grid grid-cols-2 gap-3">
        {/* Type */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Type d'adresse</label>
          <select
            value={formData.address_type}
            onChange={(e) => handleChange('address_type', e.target.value as AddressType)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
          >
            {types.map((type) => (
              <option key={type} value={type}>
                {AddressTypeLabels[type]}
              </option>
            ))}
          </select>
        </div>

        {/* Libellé */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Libellé</label>
          <input
            type="text"
            value={formData.label}
            onChange={(e) => handleChange('label', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
            placeholder="Ex: Chantier Paris"
          />
        </div>

        {/* Adresse ligne 1 - avec Autocomplete */}
        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-700 mb-1">Adresse</label>
          <AddressAutocomplete
            value={formData.address_line1}
            onChange={(value) => handleChange('address_line1', value)}
            onSelect={handleAddressSelect}
            placeholder="Rechercher une adresse..."
            className="address-autocomplete-form"
          />
        </div>

        {/* Adresse ligne 2 */}
        <div className="col-span-2">
          <input
            type="text"
            value={formData.address_line2}
            onChange={(e) => handleChange('address_line2', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
            placeholder="Complément d'adresse (optionnel)"
          />
        </div>

        {/* Code postal */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Code postal</label>
          <input
            type="text"
            value={formData.postal_code}
            onChange={(e) => handleChange('postal_code', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Ville */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Ville</label>
          <input
            type="text"
            value={formData.city}
            onChange={(e) => handleChange('city', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Contact sur site */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Contact sur site</label>
          <input
            type="text"
            value={formData.contact_name}
            onChange={(e) => handleChange('contact_name', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
            placeholder="Nom du contact"
          />
        </div>

        {/* Téléphone contact */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Téléphone</label>
          <input
            type="tel"
            value={formData.contact_phone}
            onChange={(e) => handleChange('contact_phone', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Adresse par défaut */}
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={formData.is_default}
          onChange={(e) => handleChange('is_default', e.target.checked)}
          className="rounded text-blue-600"
        />
        Adresse par défaut pour ce type
      </label>

      {error && <div className="text-red-500 text-sm">{error}</div>}

      {/* Actions */}
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
        >
          Annuler
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? '...' : address ? 'Modifier' : 'Ajouter'}
        </button>
      </div>
    </form>
  );
};

export default AddressManager;
