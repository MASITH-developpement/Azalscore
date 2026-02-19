/**
 * AZALSCORE Module - Country Packs France
 * Pack France: PCG, TVA, FEC, DSN, RGPD
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BookOpen, FileText, Euro, Users, Shield, AlertTriangle, CheckCircle,
  Clock, Download, Upload, Play, FileSearch
} from 'lucide-react';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import { Button, Modal } from '@ui/actions';
import { LoadingState } from '@ui/components/StateViews';
import { StatCard } from '@ui/dashboards';
import { Select, Input } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate, formatDateTime, formatCurrency } from '@/utils/formatters';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavProps {
  tabs: { id: string; label: string }[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <nav className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </nav>
);

// ============================================================================
// TYPES
// ============================================================================

interface FrancePackStats {
  pcg_accounts: number;
  vat_rates: number;
  vat_declarations_pending: number;
  fec_exports: number;
  fec_exports_year: number;
  dsn_declarations: number;
  dsn_pending: number;
  rgpd_consents: number;
  rgpd_requests_pending: number;
  rgpd_breaches: number;
  contracts: number;
}

interface PCGAccount {
  id: number;
  account_number: string;
  label: string;
  pcg_class: string;
  pcg_category?: string;
  nature: 'DEBIT' | 'CREDIT';
  is_active: boolean;
  is_system: boolean;
  created_at: string;
}

interface VATRate {
  id: number;
  code: string;
  label: string;
  rate: number;
  type: 'NORMAL' | 'REDUCED' | 'SUPER_REDUCED' | 'ZERO';
  is_active: boolean;
}

interface VATDeclaration {
  id: number;
  reference: string;
  period_start: string;
  period_end: string;
  regime: 'CA3' | 'CA12';
  status: 'DRAFT' | 'CALCULATED' | 'VALIDATED' | 'SUBMITTED' | 'PAID';
  vat_collected: number;
  vat_deductible: number;
  vat_due: number;
  created_at: string;
  submitted_at?: string;
}

interface FECExport {
  id: number;
  reference: string;
  fiscal_year: number;
  period_start: string;
  period_end: string;
  status: 'PENDING' | 'GENERATING' | 'READY' | 'VALIDATED' | 'ERROR';
  entries_count: number;
  file_size?: number;
  validation_errors: string[];
  generated_at?: string;
  created_at: string;
}

interface DSNDeclaration {
  id: number;
  reference: string;
  period: string;
  type: 'MONTHLY' | 'EVENT';
  status: 'DRAFT' | 'VALIDATED' | 'SUBMITTED' | 'ACCEPTED' | 'REJECTED';
  employees_count: number;
  total_gross: number;
  total_contributions: number;
  submitted_at?: string;
  created_at: string;
}

interface RGPDConsent {
  id: number;
  data_subject_id: string;
  data_subject_email: string;
  purpose: string;
  legal_basis: 'CONSENT' | 'CONTRACT' | 'LEGAL_OBLIGATION' | 'VITAL_INTEREST' | 'PUBLIC_TASK' | 'LEGITIMATE_INTEREST';
  status: 'ACTIVE' | 'WITHDRAWN' | 'EXPIRED';
  given_at: string;
  withdrawn_at?: string;
  expires_at?: string;
}

interface RGPDRequest {
  id: number;
  reference: string;
  type: 'ACCESS' | 'RECTIFICATION' | 'ERASURE' | 'PORTABILITY' | 'OBJECTION' | 'RESTRICTION';
  data_subject_name: string;
  data_subject_email: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED';
  due_date: string;
  processed_at?: string;
  created_at: string;
}

interface RGPDBreach {
  id: number;
  reference: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  affected_subjects: number;
  status: 'DETECTED' | 'INVESTIGATING' | 'NOTIFIED' | 'RESOLVED';
  detected_at: string;
  cnil_notified_at?: string;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const PCG_CLASSES = [
  { value: '1', label: 'Classe 1 - Capitaux' },
  { value: '2', label: 'Classe 2 - Immobilisations' },
  { value: '3', label: 'Classe 3 - Stocks' },
  { value: '4', label: 'Classe 4 - Tiers' },
  { value: '5', label: 'Classe 5 - Financiers' },
  { value: '6', label: 'Classe 6 - Charges' },
  { value: '7', label: 'Classe 7 - Produits' }
];

const VAT_DECLARATION_STATUS = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'CALCULATED', label: 'Calcule', color: 'blue' },
  { value: 'VALIDATED', label: 'Valide', color: 'orange' },
  { value: 'SUBMITTED', label: 'Soumise', color: 'purple' },
  { value: 'PAID', label: 'Payee', color: 'green' }
];

const FEC_STATUS = [
  { value: 'PENDING', label: 'En attente', color: 'gray' },
  { value: 'GENERATING', label: 'Generation...', color: 'blue' },
  { value: 'READY', label: 'Pret', color: 'orange' },
  { value: 'VALIDATED', label: 'Valide', color: 'green' },
  { value: 'ERROR', label: 'Erreur', color: 'red' }
];

const DSN_STATUS = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'VALIDATED', label: 'Valide', color: 'orange' },
  { value: 'SUBMITTED', label: 'Soumise', color: 'blue' },
  { value: 'ACCEPTED', label: 'Acceptee', color: 'green' },
  { value: 'REJECTED', label: 'Rejetee', color: 'red' }
];

const RGPD_REQUEST_TYPES = [
  { value: 'ACCESS', label: 'Acces' },
  { value: 'RECTIFICATION', label: 'Rectification' },
  { value: 'ERASURE', label: 'Effacement' },
  { value: 'PORTABILITY', label: 'Portabilite' },
  { value: 'OBJECTION', label: 'Opposition' },
  { value: 'RESTRICTION', label: 'Limitation' }
];

const RGPD_REQUEST_STATUS = [
  { value: 'PENDING', label: 'En attente', color: 'orange' },
  { value: 'IN_PROGRESS', label: 'En cours', color: 'blue' },
  { value: 'COMPLETED', label: 'Traitee', color: 'green' },
  { value: 'REJECTED', label: 'Rejetee', color: 'red' }
];

const BREACH_SEVERITY = [
  { value: 'LOW', label: 'Faible', color: 'gray' },
  { value: 'MEDIUM', label: 'Moyenne', color: 'orange' },
  { value: 'HIGH', label: 'Elevee', color: 'red' },
  { value: 'CRITICAL', label: 'Critique', color: 'purple' }
];

// ============================================================================
// API HOOKS
// ============================================================================

const useFrancePackStats = () => {
  return useQuery({
    queryKey: ['france', 'stats'],
    queryFn: async () => {
      const response = await api.get<FrancePackStats>('/country-packs/france/stats');
      return response.data;
    }
  });
};

const usePCGAccounts = (filters?: { pcg_class?: string; active_only?: boolean }) => {
  return useQuery({
    queryKey: ['france', 'pcg', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.pcg_class) params.append('pcg_class', filters.pcg_class);
      if (filters?.active_only !== undefined) params.append('active_only', String(filters.active_only));
      const queryString = params.toString();
      const response = await api.get<PCGAccount[]>(`/country-packs/france/pcg/accounts${queryString ? `?${queryString}` : ''}`);
      return response.data;
    }
  });
};

const useVATRates = (active_only: boolean = true) => {
  return useQuery({
    queryKey: ['france', 'vat-rates', active_only],
    queryFn: async () => {
      const response = await api.get<VATRate[]>(`/country-packs/france/tva/rates?active_only=${active_only}`);
      return response.data;
    }
  });
};

const useVATDeclarations = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: ['france', 'vat-declarations', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const response = await api.get<VATDeclaration[]>(`/country-packs/france/tva/declarations${queryString ? `?${queryString}` : ''}`);
      return response.data;
    }
  });
};

const useFECExports = (filters?: { status?: string; fiscal_year?: number }) => {
  return useQuery({
    queryKey: ['france', 'fec', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.fiscal_year) params.append('fiscal_year', String(filters.fiscal_year));
      const queryString = params.toString();
      const response = await api.get<FECExport[]>(`/country-packs/france/fec${queryString ? `?${queryString}` : ''}`);
      return response.data;
    }
  });
};

const useDSNDeclarations = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: ['france', 'dsn', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const response = await api.get<DSNDeclaration[]>(`/country-packs/france/dsn${queryString ? `?${queryString}` : ''}`);
      return response.data;
    }
  });
};

const useRGPDConsents = () => {
  return useQuery({
    queryKey: ['france', 'rgpd', 'consents'],
    queryFn: async () => {
      const response = await api.get<RGPDConsent[]>('/country-packs/france/rgpd/consents');
      return response.data;
    }
  });
};

const useRGPDRequests = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: ['france', 'rgpd', 'requests', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const response = await api.get<RGPDRequest[]>(`/country-packs/france/rgpd/requests${queryString ? `?${queryString}` : ''}`);
      return response.data;
    }
  });
};

const useRGPDBreaches = () => {
  return useQuery({
    queryKey: ['france', 'rgpd', 'breaches'],
    queryFn: async () => {
      const response = await api.get<RGPDBreach[]>('/country-packs/france/rgpd/breaches');
      return response.data;
    }
  });
};

// Mutations
const useGenerateFEC = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { fiscal_year: number; period_start: string; period_end: string }) => {
      return api.post('/country-packs/france/fec/generate', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['france', 'fec'] });
      queryClient.invalidateQueries({ queryKey: ['france', 'stats'] });
    }
  });
};

const useValidateFEC = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (fecId: number) => {
      return api.post(`/country-packs/france/fec/${fecId}/validate`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['france', 'fec'] });
    }
  });
};

const useCalculateVATDeclaration = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (declarationId: number) => {
      return api.post(`/country-packs/france/tva/declarations/${declarationId}/calculate`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['france', 'vat-declarations'] });
    }
  });
};

const useSubmitDSN = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dsnId: number) => {
      return api.post(`/country-packs/france/dsn/${dsnId}/submit`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['france', 'dsn'] });
      queryClient.invalidateQueries({ queryKey: ['france', 'stats'] });
    }
  });
};

const useProcessRGPDRequest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ requestId, response, data_exported, data_deleted }: {
      requestId: number;
      response: string;
      data_exported?: boolean;
      data_deleted?: boolean;
    }) => {
      return api.post(`/country-packs/france/rgpd/requests/${requestId}/process`, {
        response,
        data_exported,
        data_deleted
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['france', 'rgpd'] });
      queryClient.invalidateQueries({ queryKey: ['france', 'stats'] });
    }
  });
};

// ============================================================================
// VIEWS
// ============================================================================

// PCG View
const PCGView: React.FC = () => {
  const [filterClass, setFilterClass] = useState<string>('');
  const { data: accounts = [], isLoading, error, refetch } = usePCGAccounts({
    pcg_class: filterClass || undefined
  });

  const columns: TableColumn<PCGAccount>[] = [
    {
      id: 'account_number',
      header: 'Numero',
      accessor: 'account_number',
      render: (v) => <code className="font-mono font-bold">{v as string}</code>
    },
    { id: 'label', header: 'Libelle', accessor: 'label' },
    {
      id: 'pcg_class',
      header: 'Classe',
      accessor: 'pcg_class',
      render: (v) => <Badge color="blue">Classe {v as string}</Badge>
    },
    { id: 'pcg_category', header: 'Categorie', accessor: 'pcg_category', render: (v) => (v as string) || '-' },
    {
      id: 'nature',
      header: 'Nature',
      accessor: 'nature',
      render: (v) => <Badge color={(v as string) === 'DEBIT' ? 'orange' : 'green'}>{v as string}</Badge>
    },
    {
      id: 'is_active',
      header: 'Actif',
      accessor: 'is_active',
      render: (v) => <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    },
    {
      id: 'is_system',
      header: 'Systeme',
      accessor: 'is_system',
      render: (v) => (v as boolean) ? <Badge color="purple">PCG</Badge> : '-'
    }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Plan Comptable General (PCG 2024)</h3>
        <div className="flex gap-2">
          <Select
            value={filterClass}
            onChange={(v) => setFilterClass(v)}
            options={[{ value: '', label: 'Toutes classes' }, ...PCG_CLASSES]}
            className="w-48"
          />
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createPCGAccount' } })); }}>
            Nouveau compte
          </Button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={accounts}
        isLoading={isLoading}
        keyField="id"
        filterable
        error={error instanceof Error ? error : null}
        onRetry={() => refetch()}
      />
    </Card>
  );
};

// TVA View
const TVAView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: rates = [] } = useVATRates();
  const { data: declarations = [], isLoading, error, refetch } = useVATDeclarations({
    status: filterStatus || undefined
  });
  const calculateDeclaration = useCalculateVATDeclaration();

  const ratesColumns: TableColumn<VATRate>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'label', header: 'Libelle', accessor: 'label' },
    {
      id: 'rate',
      header: 'Taux',
      accessor: 'rate',
      align: 'right',
      render: (v) => <span className="font-bold">{(v as number).toFixed(1)}%</span>
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'type',
      render: (v) => {
        const typeColors: Record<string, string> = {
          NORMAL: 'blue',
          REDUCED: 'green',
          SUPER_REDUCED: 'purple',
          ZERO: 'gray'
        };
        return <Badge color={typeColors[v as string] || 'gray'}>{v as string}</Badge>;
      }
    }
  ];

  const declarationsColumns: TableColumn<VATDeclaration>[] = [
    { id: 'reference', header: 'Reference', accessor: 'reference', render: (v) => <code className="font-mono">{v as string}</code> },
    {
      id: 'period',
      header: 'Periode',
      accessor: 'period_start',
      render: (_, row) => `${formatDate(row.period_start)} - ${formatDate(row.period_end)}`
    },
    { id: 'regime', header: 'Regime', accessor: 'regime', render: (v) => <Badge color="blue">{v as string}</Badge> },
    { id: 'vat_collected', header: 'TVA Collectee', accessor: 'vat_collected', align: 'right', render: (v) => formatCurrency(v as number) },
    { id: 'vat_deductible', header: 'TVA Deductible', accessor: 'vat_deductible', align: 'right', render: (v) => formatCurrency(v as number) },
    {
      id: 'vat_due',
      header: 'TVA Due',
      accessor: 'vat_due',
      align: 'right',
      render: (v) => <span className="font-bold">{formatCurrency(v as number)}</span>
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const info = VAT_DECLARATION_STATUS.find(s => s.value === v);
        return <Badge color={info?.color || 'gray'}>{info?.label || (v as string)}</Badge>;
      }
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          {row.status === 'DRAFT' && (
            <Button size="sm" onClick={() => calculateDeclaration.mutate(row.id)}>
              Calculer
            </Button>
          )}
          <Button size="sm" variant="secondary">Detail</Button>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Taux de TVA</h3>
        </div>
        <DataTable columns={ratesColumns} data={rates} keyField="id" />
      </Card>

      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Declarations de TVA</h3>
          <div className="flex gap-2">
            <Select
              value={filterStatus}
              onChange={(v) => setFilterStatus(v)}
              options={[{ value: '', label: 'Tous statuts' }, ...VAT_DECLARATION_STATUS]}
              className="w-36"
            />
            <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createVATDeclaration' } })); }}>
              Nouvelle declaration
            </Button>
          </div>
        </div>
        <DataTable
          columns={declarationsColumns}
          data={declarations}
          isLoading={isLoading}
          keyField="id"
          filterable
          error={error instanceof Error ? error : null}
          onRetry={() => refetch()}
        />
      </Card>
    </div>
  );
};

// FEC View
const FECView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [formData, setFormData] = useState({
    fiscal_year: new Date().getFullYear(),
    period_start: '',
    period_end: ''
  });

  const { data: exports = [], isLoading, error, refetch } = useFECExports({
    status: filterStatus || undefined
  });
  const generateFEC = useGenerateFEC();
  const validateFEC = useValidateFEC();

  const handleGenerate = async () => {
    await generateFEC.mutateAsync(formData);
    setShowGenerateModal(false);
  };

  const columns: TableColumn<FECExport>[] = [
    { id: 'reference', header: 'Reference', accessor: 'reference', render: (v) => <code className="font-mono font-bold">{v as string}</code> },
    { id: 'fiscal_year', header: 'Exercice', accessor: 'fiscal_year', render: (v) => <Badge color="blue">{v as number}</Badge> },
    {
      id: 'period',
      header: 'Periode',
      accessor: 'period_start',
      render: (_, row) => `${formatDate(row.period_start)} - ${formatDate(row.period_end)}`
    },
    { id: 'entries_count', header: 'Ecritures', accessor: 'entries_count', align: 'right' },
    {
      id: 'file_size',
      header: 'Taille',
      accessor: 'file_size',
      align: 'right',
      render: (v) => v ? `${((v as number) / 1024).toFixed(0)} Ko` : '-'
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const info = FEC_STATUS.find(s => s.value === v);
        return <Badge color={info?.color || 'gray'}>{info?.label || (v as string)}</Badge>;
      }
    },
    {
      id: 'validation_errors',
      header: 'Erreurs',
      accessor: 'validation_errors',
      render: (v) => {
        const errors = v as string[];
        return errors?.length > 0 ? (
          <Badge color="red">{errors.length} erreurs</Badge>
        ) : (
          <Badge color="green">OK</Badge>
        );
      }
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          {row.status === 'READY' && (
            <Button size="sm" variant="primary" onClick={() => validateFEC.mutate(row.id)}>
              <CheckCircle size={14} className="mr-1" />
              Valider
            </Button>
          )}
          {row.status === 'VALIDATED' && (
            <Button size="sm" variant="success">
              <Download size={14} className="mr-1" />
              Telecharger
            </Button>
          )}
        </div>
      )
    }
  ];

  return (
    <>
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Fichiers des Ecritures Comptables (FEC)</h3>
          <div className="flex gap-2">
            <Select
              value={filterStatus}
              onChange={(v) => setFilterStatus(v)}
              options={[{ value: '', label: 'Tous statuts' }, ...FEC_STATUS]}
              className="w-36"
            />
            <Button onClick={() => setShowGenerateModal(true)}>
              <FileText size={16} className="mr-1" />
              Generer FEC
            </Button>
          </div>
        </div>
        <DataTable
          columns={columns}
          data={exports}
          isLoading={isLoading}
          keyField="id"
          filterable
          error={error instanceof Error ? error : null}
          onRetry={() => refetch()}
        />
      </Card>

      <Modal isOpen={showGenerateModal} onClose={() => setShowGenerateModal(false)} title="Generer un FEC" size="md">
        <div className="space-y-4">
          <div className="azals-field">
            <label className="azals-field__label">Exercice fiscal</label>
            <Input
              type="number"
              value={String(formData.fiscal_year)}
              onChange={(v) => setFormData({ ...formData, fiscal_year: parseInt(v) })}
            />
          </div>
          <Grid cols={2}>
            <div className="azals-field">
              <label className="azals-field__label">Date debut</label>
              <input
                type="date"
                className="azals-input"
                value={formData.period_start}
                onChange={(e) => setFormData({ ...formData, period_start: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Date fin</label>
              <input
                type="date"
                className="azals-input"
                value={formData.period_end}
                onChange={(e) => setFormData({ ...formData, period_end: e.target.value })}
              />
            </div>
          </Grid>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowGenerateModal(false)}>Annuler</Button>
            <Button onClick={handleGenerate} isLoading={generateFEC.isPending}>
              <Play size={16} className="mr-1" />
              Generer
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};

// DSN View
const DSNView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: declarations = [], isLoading, error, refetch } = useDSNDeclarations({
    status: filterStatus || undefined
  });
  const submitDSN = useSubmitDSN();

  const columns: TableColumn<DSNDeclaration>[] = [
    { id: 'reference', header: 'Reference', accessor: 'reference', render: (v) => <code className="font-mono font-bold">{v as string}</code> },
    { id: 'period', header: 'Periode', accessor: 'period', render: (v) => <Badge color="blue">{v as string}</Badge> },
    {
      id: 'type',
      header: 'Type',
      accessor: 'type',
      render: (v) => <Badge color={(v as string) === 'MONTHLY' ? 'green' : 'orange'}>{(v as string) === 'MONTHLY' ? 'Mensuelle' : 'Evenement'}</Badge>
    },
    { id: 'employees_count', header: 'Salaries', accessor: 'employees_count', align: 'right' },
    { id: 'total_gross', header: 'Brut total', accessor: 'total_gross', align: 'right', render: (v) => formatCurrency(v as number) },
    { id: 'total_contributions', header: 'Cotisations', accessor: 'total_contributions', align: 'right', render: (v) => formatCurrency(v as number) },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const info = DSN_STATUS.find(s => s.value === v);
        return <Badge color={info?.color || 'gray'}>{info?.label || (v as string)}</Badge>;
      }
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          {row.status === 'VALIDATED' && (
            <Button size="sm" variant="primary" onClick={() => submitDSN.mutate(row.id)}>
              <Upload size={14} className="mr-1" />
              Soumettre
            </Button>
          )}
          <Button size="sm" variant="secondary">Detail</Button>
        </div>
      )
    }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Declarations Sociales Nominatives (DSN)</h3>
        <div className="flex gap-2">
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...DSN_STATUS]}
            className="w-36"
          />
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createDSN' } })); }}>
            Nouvelle DSN
          </Button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={declarations}
        isLoading={isLoading}
        keyField="id"
        filterable
        error={error instanceof Error ? error : null}
        onRetry={() => refetch()}
      />
    </Card>
  );
};

// RGPD View
const RGPDView: React.FC = () => {
  const [activeSubView, setActiveSubView] = useState<'requests' | 'consents' | 'breaches'>('requests');
  const [filterRequestType, setFilterRequestType] = useState<string>('');
  const [filterRequestStatus, setFilterRequestStatus] = useState<string>('');

  const { data: requests = [], isLoading: loadingRequests, refetch: refetchRequests } = useRGPDRequests({
    type: filterRequestType || undefined,
    status: filterRequestStatus || undefined
  });
  const { data: consents = [], isLoading: loadingConsents } = useRGPDConsents();
  const { data: breaches = [], isLoading: loadingBreaches } = useRGPDBreaches();
  const processRequest = useProcessRGPDRequest();

  const requestColumns: TableColumn<RGPDRequest>[] = [
    { id: 'reference', header: 'Reference', accessor: 'reference', render: (v) => <code className="font-mono">{v as string}</code> },
    {
      id: 'type',
      header: 'Type',
      accessor: 'type',
      render: (v) => {
        const info = RGPD_REQUEST_TYPES.find(t => t.value === v);
        return <Badge color="blue">{info?.label || (v as string)}</Badge>;
      }
    },
    { id: 'data_subject_name', header: 'Demandeur', accessor: 'data_subject_name' },
    { id: 'data_subject_email', header: 'Email', accessor: 'data_subject_email', render: (v) => <span className="text-sm">{v as string}</span> },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const info = RGPD_REQUEST_STATUS.find(s => s.value === v);
        return <Badge color={info?.color || 'gray'}>{info?.label || (v as string)}</Badge>;
      }
    },
    {
      id: 'due_date',
      header: 'Echeance',
      accessor: 'due_date',
      render: (v, row) => {
        const isOverdue = new Date(v as string) < new Date() && row.status !== 'COMPLETED';
        return <span className={isOverdue ? 'text-red-600 font-bold' : ''}>{formatDate(v as string)}</span>;
      }
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          {(row.status === 'PENDING' || row.status === 'IN_PROGRESS') && (
            <Button size="sm" variant="primary" onClick={() => processRequest.mutate({
              requestId: row.id,
              response: 'Demande traitee',
              data_exported: row.type === 'ACCESS' || row.type === 'PORTABILITY',
              data_deleted: row.type === 'ERASURE'
            })}>
              Traiter
            </Button>
          )}
        </div>
      )
    }
  ];

  const consentColumns: TableColumn<RGPDConsent>[] = [
    { id: 'data_subject_email', header: 'Email', accessor: 'data_subject_email' },
    { id: 'purpose', header: 'Finalite', accessor: 'purpose' },
    {
      id: 'legal_basis',
      header: 'Base legale',
      accessor: 'legal_basis',
      render: (v) => <Badge color="blue">{v as string}</Badge>
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const colors: Record<string, string> = { ACTIVE: 'green', WITHDRAWN: 'red', EXPIRED: 'gray' };
        return <Badge color={colors[v as string] || 'gray'}>{v as string}</Badge>;
      }
    },
    { id: 'given_at', header: 'Donne le', accessor: 'given_at', render: (v) => formatDate(v as string) },
    { id: 'expires_at', header: 'Expire le', accessor: 'expires_at', render: (v) => v ? formatDate(v as string) : '-' }
  ];

  const breachColumns: TableColumn<RGPDBreach>[] = [
    { id: 'reference', header: 'Reference', accessor: 'reference', render: (v) => <code className="font-mono">{v as string}</code> },
    {
      id: 'severity',
      header: 'Gravite',
      accessor: 'severity',
      render: (v) => {
        const info = BREACH_SEVERITY.find(s => s.value === v);
        return <Badge color={info?.color || 'gray'}>{info?.label || (v as string)}</Badge>;
      }
    },
    { id: 'description', header: 'Description', accessor: 'description', render: (v) => (
      <span className="line-clamp-2">{v as string}</span>
    )},
    { id: 'affected_subjects', header: 'Personnes affectees', accessor: 'affected_subjects', align: 'right' },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const colors: Record<string, string> = { DETECTED: 'red', INVESTIGATING: 'orange', NOTIFIED: 'blue', RESOLVED: 'green' };
        return <Badge color={colors[v as string] || 'gray'}>{v as string}</Badge>;
      }
    },
    { id: 'detected_at', header: 'Detecte le', accessor: 'detected_at', render: (v) => formatDateTime(v as string) },
    {
      id: 'cnil_notified_at',
      header: 'CNIL notifiee',
      accessor: 'cnil_notified_at',
      render: (v) => v ? formatDateTime(v as string) : <Badge color="orange">Non</Badge>
    }
  ];

  const subTabs = [
    { id: 'requests', label: 'Demandes' },
    { id: 'consents', label: 'Consentements' },
    { id: 'breaches', label: 'Violations' }
  ];

  return (
    <div className="space-y-4">
      <TabNav tabs={subTabs} activeTab={activeSubView} onChange={(id) => setActiveSubView(id as typeof activeSubView)} />

      {activeSubView === 'requests' && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Demandes RGPD</h3>
            <div className="flex gap-2">
              <Select
                value={filterRequestType}
                onChange={(v) => setFilterRequestType(v)}
                options={[{ value: '', label: 'Tous types' }, ...RGPD_REQUEST_TYPES]}
                className="w-36"
              />
              <Select
                value={filterRequestStatus}
                onChange={(v) => setFilterRequestStatus(v)}
                options={[{ value: '', label: 'Tous statuts' }, ...RGPD_REQUEST_STATUS]}
                className="w-32"
              />
            </div>
          </div>
          <DataTable columns={requestColumns} data={requests} isLoading={loadingRequests} keyField="id" filterable onRetry={() => refetchRequests()} />
        </Card>
      )}

      {activeSubView === 'consents' && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Consentements</h3>
            <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createConsent' } })); }}>
              Nouveau consentement
            </Button>
          </div>
          <DataTable columns={consentColumns} data={consents} isLoading={loadingConsents} keyField="id" filterable />
        </Card>
      )}

      {activeSubView === 'breaches' && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Violations de donnees</h3>
            <Button variant="danger" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'reportBreach' } })); }}>
              <AlertTriangle size={16} className="mr-1" />
              Signaler une violation
            </Button>
          </div>
          <DataTable columns={breachColumns} data={breaches} isLoading={loadingBreaches} keyField="id" filterable />
        </Card>
      )}
    </div>
  );
};

// ============================================================================
// MAIN MODULE
// ============================================================================

type View = 'dashboard' | 'pcg' | 'tva' | 'fec' | 'dsn' | 'rgpd';

const CountryPacksFranceModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats, isLoading: statsLoading } = useFrancePackStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'pcg', label: 'PCG' },
    { id: 'tva', label: 'TVA' },
    { id: 'fec', label: 'FEC' },
    { id: 'dsn', label: 'DSN' },
    { id: 'rgpd', label: 'RGPD' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'pcg':
        return <PCGView />;
      case 'tva':
        return <TVAView />;
      case 'fec':
        return <FECView />;
      case 'dsn':
        return <DSNView />;
      case 'rgpd':
        return <RGPDView />;
      default:
        if (statsLoading) {
          return <LoadingState message="Chargement des statistiques..." />;
        }
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Comptes PCG"
                value={String(stats?.pcg_accounts || 0)}
                icon={<BookOpen size={20} />}
                variant="default"
                onClick={() => setCurrentView('pcg')}
              />
              <StatCard
                title="Taux de TVA"
                value={String(stats?.vat_rates || 0)}
                icon={<Euro size={20} />}
                variant="default"
                onClick={() => setCurrentView('tva')}
              />
              <StatCard
                title="Declarations TVA en attente"
                value={String(stats?.vat_declarations_pending || 0)}
                icon={<Clock size={20} />}
                variant={stats?.vat_declarations_pending ? 'warning' : 'success'}
              />
              <StatCard
                title="FEC (exercice)"
                value={String(stats?.fec_exports_year || 0)}
                icon={<FileText size={20} />}
                variant="default"
                onClick={() => setCurrentView('fec')}
              />
            </Grid>

            <Grid cols={4}>
              <StatCard
                title="DSN en attente"
                value={String(stats?.dsn_pending || 0)}
                icon={<Users size={20} />}
                variant={stats?.dsn_pending ? 'warning' : 'success'}
                onClick={() => setCurrentView('dsn')}
              />
              <StatCard
                title="Consentements RGPD"
                value={String(stats?.rgpd_consents || 0)}
                icon={<Shield size={20} />}
                variant="default"
                onClick={() => setCurrentView('rgpd')}
              />
              <StatCard
                title="Demandes RGPD en attente"
                value={String(stats?.rgpd_requests_pending || 0)}
                icon={<FileSearch size={20} />}
                variant={stats?.rgpd_requests_pending ? 'warning' : 'success'}
              />
              <StatCard
                title="Violations de donnees"
                value={String(stats?.rgpd_breaches || 0)}
                icon={<AlertTriangle size={20} />}
                variant={stats?.rgpd_breaches ? 'danger' : 'success'}
              />
            </Grid>

            <Grid cols={2}>
              <Card>
                <h3 className="text-lg font-semibold mb-4">Conformite France</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>Plan Comptable General (PCG 2024)</span>
                    <Badge color="green">Active</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>TVA francaise</span>
                    <Badge color="green">5 taux configures</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>FEC (Article L47 A-I du LPF)</span>
                    <Badge color="green">Conforme</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>DSN (Declaration Sociale Nominative)</span>
                    <Badge color="green">Active</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>RGPD (Reglement General sur la Protection des Donnees)</span>
                    <Badge color="green">Conforme</Badge>
                  </div>
                </div>
              </Card>

              <Card>
                <h3 className="text-lg font-semibold mb-4">Actions rapides</h3>
                <div className="space-y-2">
                  <Button className="w-full justify-start" variant="secondary" onClick={() => setCurrentView('fec')}>
                    <FileText size={16} className="mr-2" />
                    Generer un FEC
                  </Button>
                  <Button className="w-full justify-start" variant="secondary" onClick={() => setCurrentView('tva')}>
                    <Euro size={16} className="mr-2" />
                    Nouvelle declaration TVA
                  </Button>
                  <Button className="w-full justify-start" variant="secondary" onClick={() => setCurrentView('dsn')}>
                    <Users size={16} className="mr-2" />
                    Preparer la DSN mensuelle
                  </Button>
                  <Button className="w-full justify-start" variant="secondary" onClick={() => setCurrentView('rgpd')}>
                    <Shield size={16} className="mr-2" />
                    Gerer les demandes RGPD
                  </Button>
                </div>
              </Card>
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper
      title="Pack France"
      subtitle="Conformite comptable et reglementaire France"
    >
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default CountryPacksFranceModule;
