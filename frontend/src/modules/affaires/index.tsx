/**
 * AZALSCORE Module - Affaires (AFF)
 * ==================================
 *
 * Suivi de projet/chantier - Agrégateur central du flux commercial.
 * Numérotation: AFF-YY-MM-XXXX
 *
 * Flux: COM/ODS → [AFF] → FAC
 *
 * Backend: /v1/projects
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Briefcase, FileText, TrendingUp, Clock, CheckCircle2, X, Edit, Search,
  ArrowLeft, Euro, AlertTriangle, Package, Wrench, ChevronRight, Save, XCircle,
  Calendar, User, Building2
} from 'lucide-react';
import { api } from '@core/api-client';

// ============================================================
// TYPES
// ============================================================

type AffaireView = 'list' | 'detail' | 'form';

interface NavState {
  view: AffaireView;
  affaireId?: string;
  isNew?: boolean;
  fromCommande?: string;
  fromODS?: string;
}

type AffaireStatus = 'PLANIFIE' | 'EN_COURS' | 'EN_PAUSE' | 'TERMINE' | 'ANNULE';
type AffairePriority = 'BASSE' | 'NORMALE' | 'HAUTE' | 'URGENTE';

interface Affaire {
  id: string;
  reference: string;          // AFF-YY-MM-XXXX
  code: string;
  name: string;
  description?: string;

  // Client
  customer_id?: string;
  customer_name?: string;

  // Origine
  commande_id?: string;
  commande_reference?: string;
  ods_id?: string;
  ods_reference?: string;

  // Dates
  start_date?: string;
  end_date?: string;
  actual_end_date?: string;

  // Status
  status: AffaireStatus;
  priority: AffairePriority;
  progress: number;           // 0-100

  // Budget
  budget_total?: number;
  budget_spent?: number;
  budget_remaining?: number;

  // Facturation
  total_invoiced?: number;
  total_paid?: number;

  // Meta
  project_manager_id?: string;
  project_manager_name?: string;
  created_at: string;
  updated_at: string;
}

interface AffaireFilters {
  status?: AffaireStatus;
  priority?: AffairePriority;
  customer_id?: string;
  search?: string;
}

interface AffaireStats {
  total: number;
  en_cours: number;
  terminees: number;
  ca_total: number;
  marge_moyenne: number;
}

// ============================================================
// CONSTANTES
// ============================================================

const STATUS_CONFIG: Record<AffaireStatus, { label: string; color: string; icon: React.ReactNode }> = {
  PLANIFIE: { label: 'Planifié', color: '#6366f1', icon: <Calendar size={14} /> },
  EN_COURS: { label: 'En cours', color: '#3b82f6', icon: <Clock size={14} /> },
  EN_PAUSE: { label: 'En pause', color: '#f59e0b', icon: <Clock size={14} /> },
  TERMINE: { label: 'Terminé', color: '#10b981', icon: <CheckCircle2 size={14} /> },
  ANNULE: { label: 'Annulé', color: '#6b7280', icon: <XCircle size={14} /> },
};

const PRIORITY_CONFIG: Record<AffairePriority, { label: string; color: string }> = {
  BASSE: { label: 'Basse', color: '#6b7280' },
  NORMALE: { label: 'Normale', color: '#3b82f6' },
  HAUTE: { label: 'Haute', color: '#f59e0b' },
  URGENTE: { label: 'Urgente', color: '#ef4444' },
};

// ============================================================
// HELPERS
// ============================================================

const formatCurrency = (amount?: number): string => {
  if (amount === undefined || amount === null) return '-';
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
};

const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

const generateReference = (): string => {
  const now = new Date();
  const yy = String(now.getFullYear()).slice(-2);
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const xxxx = String(Math.floor(Math.random() * 10000)).padStart(4, '0');
  return `AFF-${yy}-${mm}-${xxxx}`;
};

// Navigation cross-module
const navigateToModule = (module: string, params?: Record<string, string>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', {
    detail: { view: module, params }
  }));
};

// ============================================================
// API HOOKS
// ============================================================

const useAffaires = (page = 1, pageSize = 25, filters: AffaireFilters = {}) => {
  const params = new URLSearchParams({
    skip: String((page - 1) * pageSize),
    limit: String(pageSize),
    ...(filters.status && { status: filters.status }),
    ...(filters.priority && { priority: filters.priority }),
    ...(filters.customer_id && { customer_id: filters.customer_id }),
    ...(filters.search && { search: filters.search }),
  });

  return useQuery({
    queryKey: ['affaires', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get(`/v1/projects?${params}`);
      const data = response as unknown as { items: Affaire[]; total: number };
      // Adapter la réponse pour ajouter les références AFF-YY-MM-XXXX si manquantes
      const items = (data.items || []).map((item: Affaire) => ({
        ...item,
        reference: item.reference || `AFF-${item.code || item.id.slice(0, 8).toUpperCase()}`,
      }));
      return { items, total: data.total || 0, page, page_size: pageSize };
    },
  });
};

const useAffaire = (id?: string) => {
  return useQuery({
    queryKey: ['affaire', id],
    queryFn: async () => {
      const response = await api.get(`/v1/projects/${id}`);
      const data = response as unknown as Affaire;
      return {
        ...data,
        reference: data.reference || `AFF-${data.code || data.id.slice(0, 8).toUpperCase()}`,
      };
    },
    enabled: !!id,
  });
};

const useAffaireStats = () => {
  return useQuery({
    queryKey: ['affaires-stats'],
    queryFn: async () => {
      // Récupérer les stats depuis le dashboard ou calculer
      const response = await api.get('/v1/projects?limit=200&is_active=true');
      const data = response as unknown as { items: Affaire[]; total: number };
      const items = data.items || [];

      const en_cours = items.filter(a => a.status === 'EN_COURS').length;
      const terminees = items.filter(a => a.status === 'TERMINE').length;
      const ca_total = items.reduce((sum, a) => sum + (a.budget_total || 0), 0);

      return {
        total: data.total || 0,
        en_cours,
        terminees,
        ca_total,
        marge_moyenne: 25, // Placeholder
      } as AffaireStats;
    },
  });
};

const useCreateAffaire = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Affaire>) => {
      const response = await api.post('/v1/projects', {
        ...data,
        code: data.code || generateReference().replace('AFF-', ''),
      });
      return response as unknown as Affaire;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['affaires'] });
      queryClient.invalidateQueries({ queryKey: ['affaires-stats'] });
    },
  });
};

const useUpdateAffaire = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Affaire> }) => {
      const response = await api.put(`/v1/projects/${id}`, data);
      return response as unknown as Affaire;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['affaire', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['affaires'] });
    },
  });
};

// ============================================================
// COMPOSANTS
// ============================================================

// Barre de progression
const ProgressBar: React.FC<{ value: number; color?: string }> = ({ value, color = '#3b82f6' }) => (
  <div style={{
    width: '100%',
    height: '8px',
    backgroundColor: '#e5e7eb',
    borderRadius: '4px',
    overflow: 'hidden'
  }}>
    <div style={{
      width: `${Math.min(value, 100)}%`,
      height: '100%',
      backgroundColor: color,
      transition: 'width 0.3s ease'
    }} />
  </div>
);

// Badge statut
const StatusBadge: React.FC<{ status: AffaireStatus }> = ({ status }) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.EN_COURS;
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '4px',
      padding: '4px 8px',
      backgroundColor: `${config.color}20`,
      color: config.color,
      borderRadius: '4px',
      fontSize: '12px',
      fontWeight: 500,
    }}>
      {config.icon}
      {config.label}
    </span>
  );
};

// KPI Card
const StatCard: React.FC<{
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
}> = ({ label, value, icon, color = '#3b82f6' }) => (
  <div style={{
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '16px',
    border: '1px solid #e5e7eb',
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      <div style={{
        width: '40px',
        height: '40px',
        borderRadius: '8px',
        backgroundColor: `${color}20`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: color,
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '12px', color: '#6b7280' }}>{label}</div>
        <div style={{ fontSize: '20px', fontWeight: 600, color: '#111827' }}>{value}</div>
      </div>
    </div>
  </div>
);

// ============================================================
// VUES INTERNES
// ============================================================

// Liste des affaires
const AffairesListInternal: React.FC<{
  onSelect: (id: string) => void;
  onCreate: () => void;
}> = ({ onSelect, onCreate }) => {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<AffaireFilters>({});

  const { data, isLoading } = useAffaires(page, 25, filters);
  const { data: stats } = useAffaireStats();

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 600, margin: 0 }}>Affaires</h1>
          <p style={{ color: '#6b7280', margin: '4px 0 0 0' }}>
            Suivi des projets et chantiers
          </p>
        </div>
        <button
          onClick={onCreate}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 16px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          <Plus size={16} />
          Nouvelle affaire
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <StatCard
            label="Total affaires"
            value={stats.total}
            icon={<Briefcase size={20} />}
          />
          <StatCard
            label="En cours"
            value={stats.en_cours}
            icon={<Clock size={20} />}
            color="#f59e0b"
          />
          <StatCard
            label="Terminées"
            value={stats.terminees}
            icon={<CheckCircle2 size={20} />}
            color="#10b981"
          />
          <StatCard
            label="CA Total"
            value={formatCurrency(stats.ca_total)}
            icon={<Euro size={20} />}
            color="#8b5cf6"
          />
        </div>
      )}

      {/* Filtres */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '16px',
        padding: '16px',
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
      }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <Search size={16} style={{
            position: 'absolute',
            left: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: '#9ca3af'
          }} />
          <input
            type="text"
            placeholder="Rechercher..."
            value={filters.search || ''}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            style={{
              width: '100%',
              padding: '8px 12px 8px 36px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px',
            }}
          />
        </div>
        <select
          value={filters.status || ''}
          onChange={(e) => setFilters({ ...filters, status: e.target.value as AffaireStatus || undefined })}
          style={{
            padding: '8px 12px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '14px',
            minWidth: '150px',
          }}
        >
          <option value="">Tous les statuts</option>
          {Object.entries(STATUS_CONFIG).map(([key, config]) => (
            <option key={key} value={key}>{config.label}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
        overflow: 'hidden',
      }}>
        {isLoading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
            Chargement...
          </div>
        ) : !data?.items?.length ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
            Aucune affaire trouvée
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f9fafb' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 500, fontSize: '12px', color: '#6b7280' }}>Référence</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 500, fontSize: '12px', color: '#6b7280' }}>Nom</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 500, fontSize: '12px', color: '#6b7280' }}>Client</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 500, fontSize: '12px', color: '#6b7280' }}>Statut</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 500, fontSize: '12px', color: '#6b7280' }}>Avancement</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 500, fontSize: '12px', color: '#6b7280' }}>Budget</th>
                <th style={{ padding: '12px 16px', textAlign: 'center', fontWeight: 500, fontSize: '12px', color: '#6b7280' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((affaire) => (
                <tr
                  key={affaire.id}
                  onClick={() => onSelect(affaire.id)}
                  style={{
                    borderTop: '1px solid #e5e7eb',
                    cursor: 'pointer',
                  }}
                  onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}
                  onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'white'}
                >
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontWeight: 500, color: '#3b82f6' }}>{affaire.reference}</span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ fontWeight: 500 }}>{affaire.name}</div>
                    {affaire.description && (
                      <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                        {affaire.description.substring(0, 50)}...
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px', color: '#6b7280' }}>
                    {affaire.customer_name || '-'}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <StatusBadge status={affaire.status} />
                  </td>
                  <td style={{ padding: '12px 16px', width: '120px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <ProgressBar value={affaire.progress || 0} />
                      <span style={{ fontSize: '12px', color: '#6b7280', minWidth: '35px' }}>
                        {affaire.progress || 0}%
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    {formatCurrency(affaire.budget_total)}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                    <ChevronRight size={16} style={{ color: '#9ca3af' }} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* Pagination */}
        {data && data.total > 25 && (
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 16px',
            borderTop: '1px solid #e5e7eb',
          }}>
            <span style={{ fontSize: '14px', color: '#6b7280' }}>
              {data.total} affaire(s)
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                style={{
                  padding: '6px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  backgroundColor: 'white',
                  cursor: page === 1 ? 'not-allowed' : 'pointer',
                  opacity: page === 1 ? 0.5 : 1,
                }}
              >
                Précédent
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page * 25 >= data.total}
                style={{
                  padding: '6px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  backgroundColor: 'white',
                  cursor: page * 25 >= data.total ? 'not-allowed' : 'pointer',
                  opacity: page * 25 >= data.total ? 0.5 : 1,
                }}
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

// Détail d'une affaire
const AffaireDetailInternal: React.FC<{
  affaireId: string;
  onBack: () => void;
  onEdit: () => void;
}> = ({ affaireId, onBack, onEdit }) => {
  const { data: affaire, isLoading } = useAffaire(affaireId);
  const updateAffaire = useUpdateAffaire();

  const handleStatusChange = async (newStatus: AffaireStatus) => {
    if (!affaire) return;
    await updateAffaire.mutateAsync({ id: affaireId, data: { status: newStatus } });
  };

  const handleCreateInvoice = () => {
    navigateToModule('factures', {
      action: 'create',
      affaire_id: affaireId,
      affaire_reference: affaire?.reference || '',
    });
  };

  if (isLoading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: '#6b7280' }}>
        Chargement...
      </div>
    );
  }

  if (!affaire) {
    return (
      <div style={{ padding: '24px' }}>
        <button onClick={onBack} style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: '#6b7280',
          marginBottom: '16px'
        }}>
          <ArrowLeft size={16} />
          Retour
        </button>
        <div style={{
          textAlign: 'center',
          padding: '40px',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #e5e7eb',
        }}>
          <AlertTriangle size={48} style={{ color: '#f59e0b', marginBottom: '16px' }} />
          <p style={{ color: '#6b7280' }}>Affaire non trouvée</p>
        </div>
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[affaire.status] || STATUS_CONFIG.EN_COURS;

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '24px'
      }}>
        <div>
          <button onClick={onBack} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: '#6b7280',
            marginBottom: '8px',
            padding: 0,
          }}>
            <ArrowLeft size={16} />
            Retour à la liste
          </button>
          <h1 style={{ fontSize: '24px', fontWeight: 600, margin: 0 }}>
            {affaire.reference}
          </h1>
          <p style={{ color: '#6b7280', margin: '4px 0 0 0' }}>
            {affaire.name}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={onEdit}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 16px',
              backgroundColor: 'white',
              color: '#374151',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            <Edit size={16} />
            Modifier
          </button>
          {affaire.status === 'TERMINE' && (
            <button
              onClick={handleCreateInvoice}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 16px',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              <FileText size={16} />
              Créer facture
            </button>
          )}
        </div>
      </div>

      {/* Info cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '16px',
          border: '1px solid #e5e7eb',
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px' }}>Statut</div>
          <StatusBadge status={affaire.status} />
        </div>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '16px',
          border: '1px solid #e5e7eb',
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px' }}>Client</div>
          <div style={{ fontWeight: 500 }}>{affaire.customer_name || '-'}</div>
        </div>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '16px',
          border: '1px solid #e5e7eb',
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px' }}>Avancement</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ProgressBar value={affaire.progress || 0} color={statusConfig.color} />
            <span style={{ fontWeight: 500 }}>{affaire.progress || 0}%</span>
          </div>
        </div>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '16px',
          border: '1px solid #e5e7eb',
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px' }}>Budget</div>
          <div style={{ fontWeight: 500 }}>{formatCurrency(affaire.budget_total)}</div>
        </div>
      </div>

      {/* Contenu principal */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Détails */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          border: '1px solid #e5e7eb',
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
            Détails de l'affaire
          </h3>

          <dl style={{
            display: 'grid',
            gridTemplateColumns: '1fr 2fr',
            gap: '12px',
            margin: 0,
          }}>
            <dt style={{ color: '#6b7280' }}>Référence</dt>
            <dd style={{ margin: 0, fontWeight: 500 }}>{affaire.reference}</dd>

            <dt style={{ color: '#6b7280' }}>Description</dt>
            <dd style={{ margin: 0 }}>{affaire.description || '-'}</dd>

            <dt style={{ color: '#6b7280' }}>Date début</dt>
            <dd style={{ margin: 0 }}>{formatDate(affaire.start_date)}</dd>

            <dt style={{ color: '#6b7280' }}>Date fin prévue</dt>
            <dd style={{ margin: 0 }}>{formatDate(affaire.end_date)}</dd>

            <dt style={{ color: '#6b7280' }}>Chef de projet</dt>
            <dd style={{ margin: 0 }}>{affaire.project_manager_name || '-'}</dd>
          </dl>

          {/* Origine */}
          {(affaire.commande_reference || affaire.ods_reference) && (
            <>
              <h4 style={{ fontSize: '14px', fontWeight: 600, marginTop: '24px', marginBottom: '12px' }}>
                Origine
              </h4>
              <div style={{ display: 'flex', gap: '8px' }}>
                {affaire.commande_reference && affaire.commande_id && (
                  <button
                    onClick={() => navigateToModule('commandes', { id: affaire.commande_id! })}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 12px',
                      backgroundColor: '#dbeafe',
                      color: '#1d4ed8',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                    }}
                  >
                    <Package size={14} />
                    {affaire.commande_reference}
                  </button>
                )}
                {affaire.ods_reference && affaire.ods_id && (
                  <button
                    onClick={() => navigateToModule('ordres-service', { id: affaire.ods_id! })}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 12px',
                      backgroundColor: '#fef3c7',
                      color: '#b45309',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                    }}
                  >
                    <Wrench size={14} />
                    {affaire.ods_reference}
                  </button>
                )}
              </div>
            </>
          )}
        </div>

        {/* Actions & Budget */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Actions rapides */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '16px',
            border: '1px solid #e5e7eb',
          }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>
              Changer le statut
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {Object.entries(STATUS_CONFIG)
                .filter(([key]) => key !== affaire.status)
                .map(([key, config]) => (
                  <button
                    key={key}
                    onClick={() => handleStatusChange(key as AffaireStatus)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 12px',
                      backgroundColor: `${config.color}10`,
                      color: config.color,
                      border: `1px solid ${config.color}40`,
                      borderRadius: '6px',
                      cursor: 'pointer',
                      width: '100%',
                      justifyContent: 'flex-start',
                    }}
                  >
                    {config.icon}
                    Passer à "{config.label}"
                  </button>
                ))}
            </div>
          </div>

          {/* Budget */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '16px',
            border: '1px solid #e5e7eb',
          }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>
              <Euro size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              Budget
            </h4>
            <dl style={{ margin: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <dt style={{ color: '#6b7280' }}>Total</dt>
                <dd style={{ margin: 0, fontWeight: 500 }}>{formatCurrency(affaire.budget_total)}</dd>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <dt style={{ color: '#6b7280' }}>Dépensé</dt>
                <dd style={{ margin: 0, color: '#ef4444' }}>{formatCurrency(affaire.budget_spent)}</dd>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '8px', borderTop: '1px solid #e5e7eb' }}>
                <dt style={{ fontWeight: 500 }}>Restant</dt>
                <dd style={{ margin: 0, fontWeight: 600, color: '#10b981' }}>
                  {formatCurrency(affaire.budget_remaining)}
                </dd>
              </div>
            </dl>
          </div>

          {/* Facturation */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '16px',
            border: '1px solid #e5e7eb',
          }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>
              <FileText size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              Facturation
            </h4>
            <dl style={{ margin: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <dt style={{ color: '#6b7280' }}>Facturé</dt>
                <dd style={{ margin: 0 }}>{formatCurrency(affaire.total_invoiced)}</dd>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <dt style={{ color: '#6b7280' }}>Encaissé</dt>
                <dd style={{ margin: 0, color: '#10b981' }}>{formatCurrency(affaire.total_paid)}</dd>
              </div>
            </dl>
            <button
              onClick={() => navigateToModule('factures', { affaire_id: affaireId })}
              style={{
                width: '100%',
                marginTop: '12px',
                padding: '8px',
                backgroundColor: '#f3f4f6',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                color: '#374151',
              }}
            >
              Voir les factures
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Formulaire affaire
const AffaireFormInternal: React.FC<{
  affaireId?: string;
  fromCommande?: string;
  fromODS?: string;
  onBack: () => void;
  onSaved: (id: string) => void;
}> = ({ affaireId, fromCommande, fromODS, onBack, onSaved }) => {
  const { data: existingAffaire } = useAffaire(affaireId);
  const createAffaire = useCreateAffaire();
  const updateAffaire = useUpdateAffaire();

  const [formData, setFormData] = useState<Partial<Affaire>>({
    name: '',
    description: '',
    status: 'PLANIFIE',
    priority: 'NORMALE',
    progress: 0,
    commande_id: fromCommande,
    ods_id: fromODS,
  });

  // Charger les données existantes
  React.useEffect(() => {
    if (existingAffaire) {
      setFormData(existingAffaire);
    }
  }, [existingAffaire]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (affaireId) {
        await updateAffaire.mutateAsync({ id: affaireId, data: formData });
        onSaved(affaireId);
      } else {
        const result = await createAffaire.mutateAsync(formData);
        onSaved(result.id);
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };

  const isLoading = createAffaire.isPending || updateAffaire.isPending;

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <button onClick={onBack} style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: '#6b7280',
          marginBottom: '8px',
          padding: 0,
        }}>
          <ArrowLeft size={16} />
          Retour
        </button>
        <h1 style={{ fontSize: '24px', fontWeight: 600, margin: 0 }}>
          {affaireId ? 'Modifier l\'affaire' : 'Nouvelle affaire'}
        </h1>
      </div>

      {/* Formulaire */}
      <form onSubmit={handleSubmit}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          border: '1px solid #e5e7eb',
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Nom */}
            <div style={{ gridColumn: 'span 2' }}>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>
                Nom de l'affaire *
              </label>
              <input
                type="text"
                required
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              />
            </div>

            {/* Description */}
            <div style={{ gridColumn: 'span 2' }}>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>
                Description
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  resize: 'vertical',
                }}
              />
            </div>

            {/* Statut */}
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>
                Statut
              </label>
              <select
                value={formData.status || 'PLANIFIE'}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as AffaireStatus })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              >
                {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>

            {/* Priorité */}
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>
                Priorité
              </label>
              <select
                value={formData.priority || 'NORMALE'}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as AffairePriority })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              >
                {Object.entries(PRIORITY_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>

            {/* Date début */}
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>
                Date de début
              </label>
              <input
                type="date"
                value={formData.start_date || ''}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              />
            </div>

            {/* Date fin */}
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>
                Date de fin prévue
              </label>
              <input
                type="date"
                value={formData.end_date || ''}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              />
            </div>

            {/* Budget */}
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>
                Budget total (€)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formData.budget_total || ''}
                onChange={(e) => setFormData({ ...formData, budget_total: parseFloat(e.target.value) || 0 })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              />
            </div>

            {/* Avancement */}
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>
                Avancement (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.progress || 0}
                onChange={(e) => setFormData({ ...formData, progress: parseInt(e.target.value) || 0 })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              />
            </div>
          </div>

          {/* Origine (affichage si depuis commande/ODS) */}
          {(fromCommande || fromODS) && (
            <div style={{
              marginTop: '16px',
              padding: '12px',
              backgroundColor: '#f0f9ff',
              borderRadius: '6px',
            }}>
              <span style={{ fontSize: '12px', color: '#0369a1' }}>
                {fromCommande && `Créée depuis la commande: ${fromCommande}`}
                {fromODS && `Créée depuis l'OS: ${fromODS}`}
              </span>
            </div>
          )}

          {/* Actions */}
          <div style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '12px',
            marginTop: '24px',
            paddingTop: '16px',
            borderTop: '1px solid #e5e7eb',
          }}>
            <button
              type="button"
              onClick={onBack}
              style={{
                padding: '10px 16px',
                backgroundColor: 'white',
                color: '#374151',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isLoading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 16px',
                backgroundColor: isLoading ? '#9ca3af' : '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
              }}
            >
              <Save size={16} />
              {isLoading ? 'Enregistrement...' : 'Enregistrer'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

// ============================================================
// MODULE PRINCIPAL
// ============================================================

export const AffairesModule: React.FC = () => {
  const [navState, setNavState] = useState<NavState>({ view: 'list' });

  // Écouter les événements de navigation cross-module
  React.useEffect(() => {
    const handleNavEvent = (event: CustomEvent) => {
      const { view, params } = event.detail || {};
      if (view === 'affaires' && params) {
        if (params.action === 'create') {
          setNavState({
            view: 'form',
            isNew: true,
            fromCommande: params.commande_id,
            fromODS: params.ods_id,
          });
        } else if (params.id) {
          setNavState({ view: 'detail', affaireId: params.id });
        }
      }
    };

    window.addEventListener('azals:navigate', handleNavEvent as EventListener);
    return () => window.removeEventListener('azals:navigate', handleNavEvent as EventListener);
  }, []);

  // Navigation callbacks
  const goToList = useCallback(() => setNavState({ view: 'list' }), []);
  const goToDetail = useCallback((id: string) => setNavState({ view: 'detail', affaireId: id }), []);
  const goToForm = useCallback((id?: string) => setNavState({ view: 'form', affaireId: id, isNew: !id }), []);
  const goToNewForm = useCallback(() => setNavState({ view: 'form', isNew: true }), []);

  // Rendu basé sur la navigation
  switch (navState.view) {
    case 'detail':
      return navState.affaireId ? (
        <AffaireDetailInternal
          affaireId={navState.affaireId}
          onBack={goToList}
          onEdit={() => goToForm(navState.affaireId)}
        />
      ) : (
        <AffairesListInternal onSelect={goToDetail} onCreate={goToNewForm} />
      );

    case 'form':
      return (
        <AffaireFormInternal
          affaireId={navState.isNew ? undefined : navState.affaireId}
          fromCommande={navState.fromCommande}
          fromODS={navState.fromODS}
          onBack={navState.affaireId ? () => goToDetail(navState.affaireId!) : goToList}
          onSaved={goToDetail}
        />
      );

    default:
      return <AffairesListInternal onSelect={goToDetail} onCreate={goToNewForm} />;
  }
};

export default AffairesModule;
