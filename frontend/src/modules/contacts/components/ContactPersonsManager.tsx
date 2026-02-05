/**
 * AZALS SOUS-PROGRAMME - ContactPersonsManager
 * =============================================
 *
 * Gestionnaire des personnes de contact (Commercial, Comptabilité, etc.)
 * Permet l'ajout, modification et suppression inline.
 *
 * Usage:
 * ```tsx
 * <ContactPersonsManager
 *   contactId={contact.id}
 *   roles={['COMMERCIAL', 'ACCOUNTING', 'BUYER']}
 * />
 * ```
 */

import React, { useState, useEffect } from 'react';
import { contactPersonsApi } from '../api';
import {
  ContactPersonRole,
  ContactPersonRoleLabels,
} from '../types';
import type {
  ContactPerson,
  ContactPersonCreate,
  ContactPersonUpdate,
} from '../types';

interface ContactPersonsManagerProps {
  /** ID du contact parent */
  contactId: string;
  /** Rôles disponibles à la sélection */
  roles?: ContactPersonRole[];
  /** Mode lecture seule */
  readOnly?: boolean;
  /** Classe CSS additionnelle */
  className?: string;
  /** Callback après modification */
  onChange?: (persons: ContactPerson[]) => void;
}

export const ContactPersonsManager: React.FC<ContactPersonsManagerProps> = ({
  contactId,
  roles,
  readOnly = false,
  className = '',
  onChange,
}) => {
  const [persons, setPersons] = useState<ContactPerson[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [error, setError] = useState('');

  const availableRoles = roles || Object.values(ContactPersonRole);

  // Charger les personnes
  useEffect(() => {
    loadPersons();
  }, [contactId]);

  const loadPersons = async () => {
    setIsLoading(true);
    try {
      const data = await contactPersonsApi.list(contactId);
      setPersons(data);
      onChange?.(data);
    } catch (err) {
      setError('Erreur chargement des contacts');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdd = async (data: ContactPersonCreate) => {
    try {
      const newPerson = await contactPersonsApi.create(contactId, data);
      const updatedPersons = [...persons, newPerson];
      setPersons(updatedPersons);
      setShowAddForm(false);
      onChange?.(updatedPersons);
    } catch (err) {
      throw err;
    }
  };

  const handleUpdate = async (personId: string, data: ContactPersonCreate) => {
    try {
      const updated = await contactPersonsApi.update(contactId, personId, data as ContactPersonUpdate);
      const updatedPersons = persons.map((p) => (p.id === personId ? updated : p));
      setPersons(updatedPersons);
      setEditingId(null);
      onChange?.(updatedPersons);
    } catch (err) {
      throw err;
    }
  };

  const handleDelete = async (personId: string) => {
    if (!confirm('Supprimer cette personne de contact ?')) return;
    try {
      await contactPersonsApi.delete(contactId, personId);
      const updatedPersons = persons.filter((p) => p.id !== personId);
      setPersons(updatedPersons);
      onChange?.(updatedPersons);
    } catch (err) {
      setError('Erreur lors de la suppression');
    }
  };

  const handleSetPrimary = async (personId: string) => {
    try {
      const updated = await contactPersonsApi.update(contactId, personId, { is_primary: true });
      const updatedPersons = persons.map((p) => (p.id === personId ? updated : p));
      setPersons(updatedPersons);
      onChange?.(updatedPersons);
    } catch (err) {
      setError('Erreur lors de la mise à jour');
    }
  };

  if (isLoading) {
    return (
      <div className={`contact-persons-manager ${className}`}>
        <div className="animate-pulse space-y-2">
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`contact-persons-manager ${className}`}>
      {error && (
        <div className="mb-2 p-2 bg-red-50 text-red-600 rounded text-sm">{error}</div>
      )}

      {/* Liste des personnes */}
      <div className="space-y-2">
        {persons.map((person) => (
          <div key={person.id}>
            {editingId === person.id ? (
              <PersonForm
                person={person}
                roles={availableRoles}
                onSubmit={(data) => handleUpdate(person.id, data)}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <PersonCard
                person={person}
                readOnly={readOnly}
                onEdit={() => setEditingId(person.id)}
                onDelete={() => handleDelete(person.id)}
                onSetPrimary={() => handleSetPrimary(person.id)}
              />
            )}
          </div>
        ))}

        {persons.length === 0 && !showAddForm && (
          <div className="text-gray-500 text-center py-4">
            Aucune personne de contact
          </div>
        )}
      </div>

      {/* Formulaire d'ajout */}
      {showAddForm && (
        <div className="mt-2">
          <PersonForm
            roles={availableRoles}
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
          className="mt-2 w-full py-2 border-2 border-dashed border-gray-300 rounded-md text-gray-500 hover:border-blue-400 hover:text-blue-500 flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Ajouter une personne
        </button>
      )}
    </div>
  );
};

// ============================================================================
// CARTE PERSONNE
// ============================================================================

interface PersonCardProps {
  person: ContactPerson;
  readOnly: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onSetPrimary: () => void;
}

const PersonCard: React.FC<PersonCardProps> = ({
  person,
  readOnly,
  onEdit,
  onDelete,
  onSetPrimary,
}) => {
  return (
    <div className={`
      flex items-center gap-3 p-3 border rounded-md
      ${person.is_primary ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-white'}
    `}>
      {/* Avatar */}
      <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 font-medium">
        {person.first_name.charAt(0)}{person.last_name.charAt(0)}
      </div>

      {/* Infos */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-900">{person.full_name}</span>
          {person.is_primary && (
            <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">Principal</span>
          )}
        </div>
        <div className="text-sm text-gray-500 flex items-center gap-2 flex-wrap">
          <span className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">
            {person.display_role || ContactPersonRoleLabels[person.role]}
          </span>
          {person.job_title && <span>{person.job_title}</span>}
        </div>
        <div className="text-sm text-gray-500 flex items-center gap-3 mt-1">
          {person.email && (
            <a href={`mailto:${person.email}`} className="hover:text-blue-600 flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              {person.email}
            </a>
          )}
          {person.phone && (
            <a href={`tel:${person.phone}`} className="hover:text-blue-600 flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
              {person.phone}
            </a>
          )}
        </div>
      </div>

      {/* Actions */}
      {!readOnly && (
        <div className="flex items-center gap-1">
          {!person.is_primary && (
            <button
              type="button"
              onClick={onSetPrimary}
              title="Définir comme principal"
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
  );
};

// ============================================================================
// FORMULAIRE PERSONNE
// ============================================================================

interface PersonFormProps {
  person?: ContactPerson;
  roles: ContactPersonRole[];
  onSubmit: (data: ContactPersonCreate) => Promise<void>;
  onCancel: () => void;
}

const PersonForm: React.FC<PersonFormProps> = ({
  person,
  roles,
  onSubmit,
  onCancel,
}) => {
  const [formData, setFormData] = useState<ContactPersonCreate>({
    role: person?.role || ContactPersonRole.OTHER,
    custom_role: person?.custom_role || '',
    first_name: person?.first_name || '',
    last_name: person?.last_name || '',
    job_title: person?.job_title || '',
    email: person?.email || '',
    phone: person?.phone || '',
    mobile: person?.mobile || '',
    is_primary: person?.is_primary || false,
    notes: person?.notes || '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field: keyof ContactPersonCreate, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.first_name || !formData.last_name) {
      setError('Prénom et nom sont requis');
      return;
    }

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
        {/* Prénom */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Prénom *</label>
          <input
            type="text"
            value={formData.first_name}
            onChange={(e) => handleChange('first_name', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
            required
          />
        </div>

        {/* Nom */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Nom *</label>
          <input
            type="text"
            value={formData.last_name}
            onChange={(e) => handleChange('last_name', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
            required
          />
        </div>

        {/* Rôle */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Rôle</label>
          <select
            value={formData.role}
            onChange={(e) => handleChange('role', e.target.value as ContactPersonRole)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
          >
            {roles.map((role) => (
              <option key={role} value={role}>
                {ContactPersonRoleLabels[role]}
              </option>
            ))}
          </select>
        </div>

        {/* Fonction */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Fonction</label>
          <input
            type="text"
            value={formData.job_title}
            onChange={(e) => handleChange('job_title', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
            placeholder="Ex: Directeur commercial"
          />
        </div>

        {/* Email */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Téléphone */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Téléphone</label>
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => handleChange('phone', e.target.value)}
            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Contact principal */}
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={formData.is_primary}
          onChange={(e) => handleChange('is_primary', e.target.checked)}
          className="rounded text-blue-600"
        />
        Contact principal
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
          {isLoading ? '...' : person ? 'Modifier' : 'Ajouter'}
        </button>
      </div>
    </form>
  );
};

export default ContactPersonsManager;
