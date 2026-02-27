/**
 * AZALSCORE Module - DOCUMENTS (GED) - Types
 * ==========================================
 * Types TypeScript pour la Gestion Electronique de Documents
 */

// ============================================================================
// ENUMS
// ============================================================================

export type DocumentStatus = 'DRAFT' | 'PENDING' | 'APPROVED' | 'PUBLISHED' | 'ARCHIVED' | 'DELETED';
export type DocumentType = 'FILE' | 'FOLDER' | 'LINK' | 'TEMPLATE';
export type AccessLevel = 'NONE' | 'VIEW' | 'COMMENT' | 'EDIT' | 'MANAGE' | 'OWNER';
export type RetentionPolicy = 'NONE' | 'DELETE' | 'ARCHIVE' | 'REVIEW';
export type ShareType = 'INTERNAL' | 'EXTERNAL' | 'PUBLIC' | 'LINK';
export type FileCategory = 'DOCUMENT' | 'IMAGE' | 'VIDEO' | 'AUDIO' | 'ARCHIVE' | 'SPREADSHEET' | 'PRESENTATION' | 'OTHER';

// ============================================================================
// INTERFACES
// ============================================================================

export interface Folder {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  parent_id?: string;
  path: string;
  level: number;
  is_system: boolean;
  is_template: boolean;
  default_access_level: AccessLevel;
  inherit_permissions: boolean;
  retention_policy: RetentionPolicy;
  retention_days?: number;
  document_count: number;
  subfolder_count: number;
  total_size: number;
  metadata: Record<string, unknown>;
  tags: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface Document {
  id: string;
  tenant_id: string;
  folder_id?: string;
  name: string;
  description?: string;
  file_name: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  file_category: FileCategory;
  document_type: DocumentType;
  status: DocumentStatus;
  version: number;
  version_label?: string;
  checksum?: string;
  is_locked: boolean;
  locked_by?: string;
  locked_at?: string;
  access_level: AccessLevel;
  retention_policy: RetentionPolicy;
  retention_date?: string;
  metadata: Record<string, unknown>;
  tags: string[];
  preview_url?: string;
  download_url?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  version: number;
  version_label?: string;
  file_name: string;
  file_size: number;
  checksum?: string;
  comment?: string;
  created_at: string;
  created_by?: string;
}

export interface DocumentShare {
  id: string;
  document_id: string;
  share_type: ShareType;
  shared_with_id?: string;
  shared_with_email?: string;
  access_level: AccessLevel;
  expires_at?: string;
  password_protected: boolean;
  download_count: number;
  max_downloads?: number;
  link_token?: string;
  created_at: string;
  created_by?: string;
}

export interface DocumentStats {
  total_documents: number;
  total_folders: number;
  total_size: number;
  documents_by_type: Record<string, number>;
  documents_by_status: Record<string, number>;
  recent_uploads: number;
  shared_documents: number;
}

// ============================================================================
// CONFIGURATION
// ============================================================================

export const DOCUMENT_STATUS_CONFIG: Record<DocumentStatus, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  PENDING: { label: 'En attente', color: 'orange' },
  APPROVED: { label: 'Approuve', color: 'blue' },
  PUBLISHED: { label: 'Publie', color: 'green' },
  ARCHIVED: { label: 'Archive', color: 'purple' },
  DELETED: { label: 'Supprime', color: 'red' },
};

export const ACCESS_LEVEL_CONFIG: Record<AccessLevel, { label: string; color: string }> = {
  NONE: { label: 'Aucun', color: 'gray' },
  VIEW: { label: 'Lecture', color: 'blue' },
  COMMENT: { label: 'Commentaire', color: 'cyan' },
  EDIT: { label: 'Edition', color: 'orange' },
  MANAGE: { label: 'Gestion', color: 'purple' },
  OWNER: { label: 'Proprietaire', color: 'green' },
};

export const FILE_CATEGORY_CONFIG: Record<FileCategory, { label: string; icon: string; color: string }> = {
  DOCUMENT: { label: 'Document', icon: 'file-text', color: 'blue' },
  IMAGE: { label: 'Image', icon: 'image', color: 'green' },
  VIDEO: { label: 'Video', icon: 'video', color: 'purple' },
  AUDIO: { label: 'Audio', icon: 'music', color: 'pink' },
  ARCHIVE: { label: 'Archive', icon: 'archive', color: 'orange' },
  SPREADSHEET: { label: 'Tableur', icon: 'table', color: 'emerald' },
  PRESENTATION: { label: 'Presentation', icon: 'presentation', color: 'yellow' },
  OTHER: { label: 'Autre', icon: 'file', color: 'gray' },
};
