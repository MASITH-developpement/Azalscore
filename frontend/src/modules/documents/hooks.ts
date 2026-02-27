/**
 * AZALSCORE Module - DOCUMENTS (GED) - React Query Hooks
 * =======================================================
 * Hooks pour la Gestion Electronique de Documents
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from './api';
import type { FolderFilters, DocumentFilters, FolderCreate, DocumentUpload, ShareCreate } from './api';
import type { DocumentStatus } from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const documentsKeys = {
  all: ['documents'] as const,
  stats: () => [...documentsKeys.all, 'stats'] as const,

  // Folders
  folders: () => [...documentsKeys.all, 'folders'] as const,
  foldersList: (filters?: FolderFilters) => [...documentsKeys.folders(), 'list', filters] as const,
  folder: (id: string) => [...documentsKeys.folders(), id] as const,
  folderTree: (rootId?: string) => [...documentsKeys.folders(), 'tree', rootId] as const,

  // Documents
  documents: () => [...documentsKeys.all, 'files'] as const,
  documentsList: (filters?: DocumentFilters) => [...documentsKeys.documents(), 'list', filters] as const,
  document: (id: string) => [...documentsKeys.documents(), id] as const,
  versions: (documentId: string) => [...documentsKeys.document(documentId), 'versions'] as const,
  shares: (documentId: string) => [...documentsKeys.document(documentId), 'shares'] as const,

  // Search
  search: (query: string, filters?: DocumentFilters) => [...documentsKeys.all, 'search', query, filters] as const,
};

// ============================================================================
// STATS HOOKS
// ============================================================================

export function useDocumentStats() {
  return useQuery({
    queryKey: documentsKeys.stats(),
    queryFn: async () => {
      const response = await documentsApi.getStats();
      return response.data;
    },
  });
}

// ============================================================================
// FOLDERS HOOKS
// ============================================================================

export function useFolders(filters?: FolderFilters) {
  return useQuery({
    queryKey: documentsKeys.foldersList(filters),
    queryFn: async () => {
      const response = await documentsApi.listFolders(filters);
      return response.data;
    },
  });
}

export function useFolder(id: string) {
  return useQuery({
    queryKey: documentsKeys.folder(id),
    queryFn: async () => {
      const response = await documentsApi.getFolder(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useFolderTree(rootId?: string) {
  return useQuery({
    queryKey: documentsKeys.folderTree(rootId),
    queryFn: async () => {
      const response = await documentsApi.getFolderTree(rootId);
      return response.data;
    },
  });
}

export function useCreateFolder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: FolderCreate) => {
      const response = await documentsApi.createFolder(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.folders() });
      queryClient.invalidateQueries({ queryKey: documentsKeys.stats() });
    },
  });
}

export function useUpdateFolder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<FolderCreate> }) => {
      const response = await documentsApi.updateFolder(id, data);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.folder(id) });
      queryClient.invalidateQueries({ queryKey: documentsKeys.folders() });
    },
  });
}

export function useDeleteFolder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await documentsApi.deleteFolder(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.folders() });
      queryClient.invalidateQueries({ queryKey: documentsKeys.stats() });
    },
  });
}

// ============================================================================
// DOCUMENTS HOOKS
// ============================================================================

export function useDocuments(filters?: DocumentFilters) {
  return useQuery({
    queryKey: documentsKeys.documentsList(filters),
    queryFn: async () => {
      const response = await documentsApi.listDocuments(filters);
      return response.data;
    },
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: documentsKeys.document(id),
    queryFn: async () => {
      const response = await documentsApi.getDocument(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, data }: { file: File; data?: DocumentUpload }) => {
      const response = await documentsApi.uploadDocument(file, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.documents() });
      queryClient.invalidateQueries({ queryKey: documentsKeys.folders() });
      queryClient.invalidateQueries({ queryKey: documentsKeys.stats() });
    },
  });
}

export function useUpdateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<DocumentUpload & { name?: string; status?: DocumentStatus }> }) => {
      const response = await documentsApi.updateDocument(id, data);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.document(id) });
      queryClient.invalidateQueries({ queryKey: documentsKeys.documents() });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await documentsApi.deleteDocument(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.documents() });
      queryClient.invalidateQueries({ queryKey: documentsKeys.folders() });
      queryClient.invalidateQueries({ queryKey: documentsKeys.stats() });
    },
  });
}

export function useMoveDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, folderId }: { id: string; folderId: string }) => {
      const response = await documentsApi.moveDocument(id, folderId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.documents() });
      queryClient.invalidateQueries({ queryKey: documentsKeys.folders() });
    },
  });
}

export function useCopyDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, folderId }: { id: string; folderId: string }) => {
      const response = await documentsApi.copyDocument(id, folderId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.documents() });
      queryClient.invalidateQueries({ queryKey: documentsKeys.stats() });
    },
  });
}

export function useLockDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await documentsApi.lockDocument(id);
      return response.data;
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.document(id) });
    },
  });
}

export function useUnlockDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await documentsApi.unlockDocument(id);
      return response.data;
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.document(id) });
    },
  });
}

// ============================================================================
// VERSIONS HOOKS
// ============================================================================

export function useDocumentVersions(documentId: string) {
  return useQuery({
    queryKey: documentsKeys.versions(documentId),
    queryFn: async () => {
      const response = await documentsApi.listVersions(documentId);
      return response.data;
    },
    enabled: !!documentId,
  });
}

export function useRestoreVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, version }: { documentId: string; version: number }) => {
      const response = await documentsApi.restoreVersion(documentId, version);
      return response.data;
    },
    onSuccess: (_data, { documentId }) => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.document(documentId) });
      queryClient.invalidateQueries({ queryKey: documentsKeys.versions(documentId) });
    },
  });
}

// ============================================================================
// SHARES HOOKS
// ============================================================================

export function useDocumentShares(documentId: string) {
  return useQuery({
    queryKey: documentsKeys.shares(documentId),
    queryFn: async () => {
      const response = await documentsApi.listShares(documentId);
      return response.data;
    },
    enabled: !!documentId,
  });
}

export function useCreateShare() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, data }: { documentId: string; data: ShareCreate }) => {
      const response = await documentsApi.createShare(documentId, data);
      return response.data;
    },
    onSuccess: (_data, { documentId }) => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.shares(documentId) });
    },
  });
}

export function useDeleteShare() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, shareId }: { documentId: string; shareId: string }) => {
      await documentsApi.deleteShare(documentId, shareId);
    },
    onSuccess: (_data, { documentId }) => {
      queryClient.invalidateQueries({ queryKey: documentsKeys.shares(documentId) });
    },
  });
}

// ============================================================================
// SEARCH HOOKS
// ============================================================================

export function useDocumentSearch(query: string, filters?: DocumentFilters) {
  return useQuery({
    queryKey: documentsKeys.search(query, filters),
    queryFn: async () => {
      const response = await documentsApi.search(query, filters);
      return response.data;
    },
    enabled: query.length >= 2,
  });
}
