/**
 * AZALSCORE Module - Admin - Types
 * Types TypeScript pour le module administration
 */

import type { SemanticColor } from '@ui/standards';

// ============================================================================
// ENTITES PRINCIPALES
// ============================================================================

/**
 * Utilisateur admin
 */
export interface AdminUser {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role_id?: string;
  role_name?: string;
  role?: Role;
  status: UserStatus;
  last_login?: string;
  last_ip?: string;
  login_count: number;
  failed_login_count: number;
  password_changed_at?: string;
  must_change_password: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
  // Relations
  permissions?: Permission[];
  sessions?: UserSession[];
  audit_logs?: AuditLog[];
}

/**
 * Role utilisateur
 */
export interface Role {
  id: string;
  code: string;
  name: string;
  description?: string;
  permissions: string[];
  is_system: boolean;
  user_count: number;
  created_at: string;
}

/**
 * Permission
 */
export interface Permission {
  id: string;
  code: string;
  name: string;
  description?: string;
  module: string;
  category: 'READ' | 'WRITE' | 'DELETE' | 'ADMIN';
}

/**
 * Session utilisateur
 */
export interface UserSession {
  id: string;
  user_id: string;
  started_at: string;
  last_activity: string;
  ended_at?: string;
  ip_address: string;
  user_agent: string;
  device_type: 'DESKTOP' | 'MOBILE' | 'TABLET';
  location?: string;
  is_active: boolean;
}

/**
 * Journal d'audit
 */
export interface AuditLog {
  id: string;
  timestamp: string;
  user_id?: string;
  user_name?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
  status: 'SUCCESS' | 'FAILURE';
}

/**
 * Tenant
 */
export interface Tenant {
  id: string;
  code: string;
  name: string;
  domain?: string;
  status: TenantStatus;
  plan: TenantPlan;
  modules_enabled: string[];
  user_count: number;
  storage_used: number;
  max_users: number;
  max_storage: number;
  created_at: string;
  expires_at?: string;
}

/**
 * Configuration de sauvegarde
 */
export interface BackupConfig {
  id: string;
  name: string;
  type: BackupType;
  schedule: string;
  retention_days: number;
  destination: BackupDestination;
  last_backup?: string;
  last_status?: BackupStatus;
  next_scheduled?: string;
  is_active: boolean;
}

/**
 * Entree historique utilisateur
 */
export interface UserHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  field?: string;
  old_value?: string;
  new_value?: string;
  performed_by?: string;
  details?: string;
}

// ============================================================================
// TYPES ENUM
// ============================================================================

export type UserStatus = 'ACTIVE' | 'INACTIVE' | 'SUSPENDED' | 'PENDING' | 'LOCKED';
export type TenantStatus = 'ACTIVE' | 'INACTIVE' | 'TRIAL' | 'SUSPENDED';
export type TenantPlan = 'FREE' | 'STARTER' | 'PROFESSIONAL' | 'ENTERPRISE';
export type BackupType = 'FULL' | 'INCREMENTAL' | 'DIFFERENTIAL';
export type BackupDestination = 'LOCAL' | 'S3' | 'GCS' | 'AZURE';
export type BackupStatus = 'SUCCESS' | 'FAILED' | 'IN_PROGRESS';

// ============================================================================
// CONFIGURATIONS STATUTS
// ============================================================================

export const USER_STATUS_CONFIG: Record<UserStatus, { label: string; color: SemanticColor }> = {
  ACTIVE: { label: 'Actif', color: 'green' },
  INACTIVE: { label: 'Inactif', color: 'gray' },
  SUSPENDED: { label: 'Suspendu', color: 'red' },
  PENDING: { label: 'En attente', color: 'orange' },
  LOCKED: { label: 'Verrouille', color: 'red' }
};

export const TENANT_STATUS_CONFIG: Record<TenantStatus, { label: string; color: SemanticColor }> = {
  ACTIVE: { label: 'Actif', color: 'green' },
  INACTIVE: { label: 'Inactif', color: 'gray' },
  TRIAL: { label: 'Essai', color: 'blue' },
  SUSPENDED: { label: 'Suspendu', color: 'red' }
};

export const TENANT_PLAN_CONFIG: Record<TenantPlan, { label: string; color: SemanticColor }> = {
  FREE: { label: 'Gratuit', color: 'gray' },
  STARTER: { label: 'Starter', color: 'blue' },
  PROFESSIONAL: { label: 'Professionnel', color: 'purple' },
  ENTERPRISE: { label: 'Enterprise', color: 'orange' }
};

export const BACKUP_TYPE_CONFIG: Record<BackupType, { label: string; color: SemanticColor }> = {
  FULL: { label: 'Complete', color: 'blue' },
  INCREMENTAL: { label: 'Incrementale', color: 'green' },
  DIFFERENTIAL: { label: 'Differentielle', color: 'purple' }
};

export const BACKUP_STATUS_CONFIG: Record<BackupStatus, { label: string; color: SemanticColor }> = {
  SUCCESS: { label: 'Succes', color: 'green' },
  FAILED: { label: 'Echoue', color: 'red' },
  IN_PROGRESS: { label: 'En cours', color: 'orange' }
};

export const PERMISSION_CATEGORY_CONFIG: Record<string, { label: string; color: SemanticColor }> = {
  READ: { label: 'Lecture', color: 'blue' },
  WRITE: { label: 'Ecriture', color: 'green' },
  DELETE: { label: 'Suppression', color: 'red' },
  ADMIN: { label: 'Administration', color: 'purple' }
};

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Formater une date
 */
export const formatDate = (date: string | undefined): string => {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
};

/**
 * Formater une date/heure
 */
export const formatDateTime = (date: string | undefined): string => {
  if (!date) return '-';
  return new Date(date).toLocaleString('fr-FR');
};

/**
 * Formater heure uniquement
 */
export const formatTime = (date: string | undefined): string => {
  if (!date) return '-';
  return new Date(date).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
};

/**
 * Formater un pourcentage
 */
export const formatPercent = (value: number): string => {
  return `${Math.round(value)}%`;
};

/**
 * Formater des bytes
 */
export const formatBytes = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
};

/**
 * Obtenir le nom complet de l'utilisateur
 */
export const getUserFullName = (user: AdminUser): string => {
  const parts = [user.first_name, user.last_name].filter(Boolean);
  return parts.length > 0 ? parts.join(' ') : user.username;
};

/**
 * Verifier si l'utilisateur est actif
 */
export const isUserActive = (user: AdminUser): boolean => {
  return user.status === 'ACTIVE';
};

/**
 * Verifier si l'utilisateur est verrouille
 */
export const isUserLocked = (user: AdminUser): boolean => {
  return user.status === 'LOCKED' || user.status === 'SUSPENDED';
};

/**
 * Verifier si l'utilisateur doit changer son mot de passe
 */
export const mustChangePassword = (user: AdminUser): boolean => {
  return user.must_change_password;
};

/**
 * Verifier si 2FA est active
 */
export const hasTwoFactorEnabled = (user: AdminUser): boolean => {
  return user.two_factor_enabled;
};

/**
 * Calculer l'anciennete du mot de passe en jours
 */
export const getPasswordAgeDays = (user: AdminUser): number => {
  if (!user.password_changed_at) return -1;
  const changed = new Date(user.password_changed_at);
  const now = new Date();
  return Math.floor((now.getTime() - changed.getTime()) / (1000 * 60 * 60 * 24));
};

/**
 * Verifier si le mot de passe est ancien (>90 jours)
 */
export const isPasswordOld = (user: AdminUser): boolean => {
  const age = getPasswordAgeDays(user);
  return age > 90;
};
