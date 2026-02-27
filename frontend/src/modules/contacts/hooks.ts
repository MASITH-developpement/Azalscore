/**
 * AZALSCORE - Contacts React Query Hooks
 * =======================================
 * Hooks pour le module Contacts Unifiés
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contactsApi, contactPersonsApi, contactAddressesApi } from './api';
import type {
  Contact,
  ContactCreate,
  ContactUpdate,
  ContactFilters,
  ContactPerson,
  ContactPersonCreate,
  ContactPersonUpdate,
  ContactAddress,
  ContactAddressCreate,
  ContactAddressUpdate,
  RelationType,
} from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const contactsKeys = {
  all: ['contacts'] as const,
  lists: () => [...contactsKeys.all, 'list'] as const,
  list: (filters?: ContactFilters) => [...contactsKeys.lists(), filters] as const,
  lookup: (relation?: RelationType, search?: string) => [...contactsKeys.all, 'lookup', relation, search] as const,
  details: () => [...contactsKeys.all, 'detail'] as const,
  detail: (id: string) => [...contactsKeys.details(), id] as const,
  stats: (id: string) => [...contactsKeys.detail(id), 'stats'] as const,
  persons: (contactId: string) => [...contactsKeys.detail(contactId), 'persons'] as const,
  addresses: (contactId: string) => [...contactsKeys.detail(contactId), 'addresses'] as const,
};

// ============================================================================
// CONTACTS QUERY HOOKS
// ============================================================================

export const useContacts = (filters?: ContactFilters) => {
  return useQuery({
    queryKey: contactsKeys.list(filters),
    queryFn: () => contactsApi.list(filters),
  });
};

export const useContactLookup = (relation?: RelationType, search?: string, limit = 50) => {
  return useQuery({
    queryKey: contactsKeys.lookup(relation, search),
    queryFn: () => contactsApi.lookup(relation, search, limit),
  });
};

export const useContact = (id?: string) => {
  return useQuery({
    queryKey: contactsKeys.detail(id || ''),
    queryFn: () => contactsApi.get(id!),
    enabled: !!id,
  });
};

export const useContactStats = (id?: string) => {
  return useQuery({
    queryKey: contactsKeys.stats(id || ''),
    queryFn: () => contactsApi.getStats(id!),
    enabled: !!id,
  });
};

// ============================================================================
// CONTACTS MUTATION HOOKS
// ============================================================================

export const useCreateContact = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ContactCreate) => contactsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.lists() });
    },
  });
};

export const useUpdateContact = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ContactUpdate }) => contactsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: contactsKeys.lists() });
    },
  });
};

export const useDeleteContact = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, permanent = false }: { id: string; permanent?: boolean }) =>
      contactsApi.delete(id, permanent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.lists() });
    },
  });
};

export const useUploadContactLogo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) => contactsApi.uploadLogo(id, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.detail(variables.id) });
    },
  });
};

export const useDeleteContactLogo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => contactsApi.deleteLogo(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.detail(id) });
    },
  });
};

// ============================================================================
// CONTACT PERSONS HOOKS
// ============================================================================

export const useContactPersons = (contactId?: string, isActive?: boolean) => {
  return useQuery({
    queryKey: contactsKeys.persons(contactId || ''),
    queryFn: () => contactPersonsApi.list(contactId!, isActive),
    enabled: !!contactId,
  });
};

export const useCreateContactPerson = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactId, data }: { contactId: string; data: ContactPersonCreate }) =>
      contactPersonsApi.create(contactId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.persons(variables.contactId) });
    },
  });
};

export const useUpdateContactPerson = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactId, personId, data }: { contactId: string; personId: string; data: ContactPersonUpdate }) =>
      contactPersonsApi.update(contactId, personId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.persons(variables.contactId) });
    },
  });
};

export const useDeleteContactPerson = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactId, personId }: { contactId: string; personId: string }) =>
      contactPersonsApi.delete(contactId, personId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.persons(variables.contactId) });
    },
  });
};

// ============================================================================
// CONTACT ADDRESSES HOOKS
// ============================================================================

export const useContactAddresses = (contactId?: string, isActive?: boolean) => {
  return useQuery({
    queryKey: contactsKeys.addresses(contactId || ''),
    queryFn: () => contactAddressesApi.list(contactId!, isActive),
    enabled: !!contactId,
  });
};

export const useCreateContactAddress = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactId, data }: { contactId: string; data: ContactAddressCreate }) =>
      contactAddressesApi.create(contactId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.addresses(variables.contactId) });
    },
  });
};

export const useUpdateContactAddress = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactId, addressId, data }: { contactId: string; addressId: string; data: ContactAddressUpdate }) =>
      contactAddressesApi.update(contactId, addressId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.addresses(variables.contactId) });
    },
  });
};

export const useDeleteContactAddress = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactId, addressId }: { contactId: string; addressId: string }) =>
      contactAddressesApi.delete(contactId, addressId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: contactsKeys.addresses(variables.contactId) });
    },
  });
};
