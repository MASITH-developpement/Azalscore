/**
 * AZALSCORE Module - DOCUMENTS (GED) - API Client
 * ================================================
 * Client API pour la Gestion Electronique de Documents
 */

import { api } from '@/core/api-client';
import type {
  Folder, Document, DocumentVersion, DocumentShare, DocumentStats,
  DocumentStatus, AccessLevel, FileCategory,
} from './types';

const BASE_URL = '/documents';

// ============================================================================
// TYPES API
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface FolderFilters {
  parent_id?: string;
  search?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface DocumentFilters {
  folder_id?: string;
  status?: DocumentStatus;
  file_category?: FileCategory;
  tags?: string[];
  search?: string;
  page?: number;
  page_size?: number;
}

export interface FolderCreate {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  parent_id?: string;
  default_access_level?: AccessLevel;
  inherit_permissions?: boolean;
  tags?: string[];
}

export interface DocumentUpload {
  folder_id?: string;
  description?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface ShareCreate {
  share_type: string;
  shared_with_id?: string;
  shared_with_email?: string;
  access_level: AccessLevel;
  expires_at?: string;
  password?: string;
  max_downloads?: number;
}

// ============================================================================
// FOLDERS API
// ============================================================================

async function listFolders(filters?: FolderFilters) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
  }
  return api.get<PaginatedResponse<Folder>>(`${BASE_URL}/folders?${params.toString()}`);
}

async function getFolder(id: string) {
  return api.get<Folder>(`${BASE_URL}/folders/${id}`);
}

async function createFolder(data: FolderCreate) {
  return api.post<Folder>(`${BASE_URL}/folders`, data);
}

async function updateFolder(id: string, data: Partial<FolderCreate>) {
  return api.put<Folder>(`${BASE_URL}/folders/${id}`, data);
}

async function deleteFolder(id: string) {
  return api.delete(`${BASE_URL}/folders/${id}`);
}

async function getFolderTree(rootId?: string) {
  const url = rootId ? `${BASE_URL}/folders/tree?root_id=${rootId}` : `${BASE_URL}/folders/tree`;
  return api.get<Folder[]>(url);
}

// ============================================================================
// DOCUMENTS API
// ============================================================================

async function listDocuments(filters?: DocumentFilters) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v));
        } else {
          params.append(key, String(value));
        }
      }
    });
  }
  return api.get<PaginatedResponse<Document>>(`${BASE_URL}?${params.toString()}`);
}

async function getDocument(id: string) {
  return api.get<Document>(`${BASE_URL}/${id}`);
}

async function uploadDocument(file: File, data?: DocumentUpload) {
  const formData = new FormData();
  formData.append('file', file);
  if (data) {
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value));
      }
    });
  }
  return api.post<Document>(`${BASE_URL}/upload`, formData);
}

async function updateDocument(id: string, data: Partial<DocumentUpload & { name?: string; status?: DocumentStatus }>) {
  return api.put<Document>(`${BASE_URL}/${id}`, data);
}

async function deleteDocument(id: string) {
  return api.delete(`${BASE_URL}/${id}`);
}

async function downloadDocument(id: string) {
  return api.get<Blob>(`${BASE_URL}/${id}/download`, { responseType: 'blob' });
}

async function getPreviewUrl(id: string) {
  return api.get<{ url: string }>(`${BASE_URL}/${id}/preview`);
}

async function moveDocument(id: string, folderId: string) {
  return api.post<Document>(`${BASE_URL}/${id}/move`, { folder_id: folderId });
}

async function copyDocument(id: string, folderId: string) {
  return api.post<Document>(`${BASE_URL}/${id}/copy`, { folder_id: folderId });
}

async function lockDocument(id: string) {
  return api.post<Document>(`${BASE_URL}/${id}/lock`);
}

async function unlockDocument(id: string) {
  return api.post<Document>(`${BASE_URL}/${id}/unlock`);
}

// ============================================================================
// VERSIONS API
// ============================================================================

async function listVersions(documentId: string) {
  return api.get<DocumentVersion[]>(`${BASE_URL}/${documentId}/versions`);
}

async function getVersion(documentId: string, version: number) {
  return api.get<DocumentVersion>(`${BASE_URL}/${documentId}/versions/${version}`);
}

async function restoreVersion(documentId: string, version: number) {
  return api.post<Document>(`${BASE_URL}/${documentId}/versions/${version}/restore`);
}

// ============================================================================
// SHARES API
// ============================================================================

async function listShares(documentId: string) {
  return api.get<DocumentShare[]>(`${BASE_URL}/${documentId}/shares`);
}

async function createShare(documentId: string, data: ShareCreate) {
  return api.post<DocumentShare>(`${BASE_URL}/${documentId}/shares`, data);
}

async function deleteShare(documentId: string, shareId: string) {
  return api.delete(`${BASE_URL}/${documentId}/shares/${shareId}`);
}

// ============================================================================
// STATS API
// ============================================================================

async function getStats() {
  return api.get<DocumentStats>(`${BASE_URL}/stats`);
}

async function search(query: string, filters?: DocumentFilters) {
  const params = new URLSearchParams({ q: query });
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
  }
  return api.get<PaginatedResponse<Document>>(`${BASE_URL}/search?${params.toString()}`);
}

// ============================================================================
// EXPORT
// ============================================================================

export const documentsApi = {
  // Folders
  listFolders,
  getFolder,
  createFolder,
  updateFolder,
  deleteFolder,
  getFolderTree,

  // Documents
  listDocuments,
  getDocument,
  uploadDocument,
  updateDocument,
  deleteDocument,
  downloadDocument,
  getPreviewUrl,
  moveDocument,
  copyDocument,
  lockDocument,
  unlockDocument,

  // Versions
  listVersions,
  getVersion,
  restoreVersion,

  // Shares
  listShares,
  createShare,
  deleteShare,

  // Stats & Search
  getStats,
  search,
};

export default documentsApi;
