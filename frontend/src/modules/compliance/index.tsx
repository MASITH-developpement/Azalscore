import React, { useState } from 'react';
import { Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input, TextArea } from '@ui/forms';
import { StatCard, ProgressBar } from '@ui/dashboards';
import { BaseViewStandard } from '@ui/standards';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition, SemanticColor } from '@ui/standards';
import type { TableColumn } from '@/types';
import {
  ClipboardCheck, AlertTriangle, FileText, Clock, Sparkles,
  Play, CheckCircle2, ArrowLeft, Edit, Printer
} from 'lucide-react';
import type {
  Audit as AuditType, AuditFinding, AuditDocument, AuditHistoryEntry
} from './types';
import {
  AUDIT_TYPE_CONFIG, AUDIT_STATUS_CONFIG,
  isAuditCompleted, isAuditInProgress, hasCriticalFindings,
  hasOpenFindings, getAuditScoreColor
} from './types';
import { formatDate, formatPercent } from '@/utils/formatters';
import {
  AuditInfoTab, AuditFindingsTab, AuditDocumentsTab,
  AuditHistoryTab, AuditIATab
} from './components';

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

interface Policy {
  id: string;
  code: string;
  name: string;
  description?: string;
  type: 'SECURITY' | 'PRIVACY' | 'DATA_RETENTION' | 'ACCESS_CONTROL' | 'OTHER';
  version: string;
  status: 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
  effective_date?: string;
  review_date?: string;
  content?: string;
  is_mandatory: boolean;
  created_at: string;
  updated_at: string;
}

interface Audit {
  id: string;
  code: string;
  name: string;
  type: 'INTERNAL' | 'EXTERNAL' | 'REGULATORY';
  status: 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  auditor?: string;
  planned_date?: string;
  completed_date?: string;
  findings_count: number;
  critical_findings: number;
  score?: number;
  report_url?: string;
  created_at: string;
}

interface GDPRRequest {
  id: string;
  reference: string;
  type: 'ACCESS' | 'RECTIFICATION' | 'ERASURE' | 'PORTABILITY' | 'OBJECTION' | 'RESTRICTION';
  requester_name: string;
  requester_email: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED';
  request_date: string;
  due_date: string;
  completed_date?: string;
  notes?: string;
  created_at: string;
}

interface Consent {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  consent_type: 'MARKETING' | 'ANALYTICS' | 'THIRD_PARTY' | 'NEWSLETTER' | 'TERMS';
  status: boolean;
  given_at?: string;
  withdrawn_at?: string;
  source: string;
  version: string;
}

interface ComplianceStats {
  active_policies: number;
  pending_reviews: number;
  audits_year: number;
  open_findings: number;
  gdpr_requests_pending: number;
  gdpr_requests_completed: number;
  compliance_score: number;
  consent_rate: number;
}

// ============================================================================
// CONSTANTES
// ============================================================================

const POLICY_TYPES = [
  { value: 'SECURITY', label: 'Securite' },
  { value: 'PRIVACY', label: 'Confidentialite' },
  { value: 'DATA_RETENTION', label: 'Conservation donnees' },
  { value: 'ACCESS_CONTROL', label: 'Controle d\'acces' },
  { value: 'OTHER', label: 'Autre' }
];

const POLICY_STATUS = [
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'ARCHIVED', label: 'Archivee' }
];

const AUDIT_TYPES = [
  { value: 'INTERNAL', label: 'Interne' },
  { value: 'EXTERNAL', label: 'Externe' },
  { value: 'REGULATORY', label: 'Reglementaire' }
];

const AUDIT_STATUS = [
  { value: 'PLANNED', label: 'Planifie' },
  { value: 'IN_PROGRESS', label: 'En cours' },
  { value: 'COMPLETED', label: 'Termine' },
  { value: 'CANCELLED', label: 'Annule' }
];

const GDPR_TYPES = [
  { value: 'ACCESS', label: 'Acces' },
  { value: 'RECTIFICATION', label: 'Rectification' },
  { value: 'ERASURE', label: 'Effacement' },
  { value: 'PORTABILITY', label: 'Portabilite' },
  { value: 'OBJECTION', label: 'Opposition' },
  { value: 'RESTRICTION', label: 'Limitation' }
];

const GDPR_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'IN_PROGRESS', label: 'En cours' },
  { value: 'COMPLETED', label: 'Traitee' },
  { value: 'REJECTED', label: 'Rejetee' }
];

const CONSENT_TYPES = [
  { value: 'MARKETING', label: 'Marketing' },
  { value: 'ANALYTICS', label: 'Analytics' },
  { value: 'THIRD_PARTY', label: 'Tiers' },
  { value: 'NEWSLETTER', label: 'Newsletter' },
  { value: 'TERMS', label: 'CGU' }
];

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'gray',
  ACTIVE: 'green',
  ARCHIVED: 'gray',
  PLANNED: 'blue',
  IN_PROGRESS: 'orange',
  COMPLETED: 'green',
  CANCELLED: 'red',
  PENDING: 'orange',
  REJECTED: 'red'
};

// ============================================================================
// HELPERS
// ============================================================================

// formatDate and formatPercent are imported from ./types

// ============================================================================
// API HOOKS
// ============================================================================

const useComplianceStats = () => {
  return useQuery({
    queryKey: ['compliance', 'stats'],
    queryFn: async () => {
      return api.get<ComplianceStats>('/compliance/stats').then(r => r.data);
    }
  });
};

const usePolicies = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: ['compliance', 'policies', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/compliance/policies?${queryString}` : '/compliance/policies';
      return api.get<Policy[]>(url).then(r => r.data);
    }
  });
};

const useAudits = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: ['compliance', 'audits', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/compliance/audits?${queryString}` : '/compliance/audits';
      return api.get<Audit[]>(url).then(r => r.data);
    }
  });
};

const useGDPRRequests = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: ['compliance', 'gdpr', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/compliance/gdpr-requests?${queryString}` : '/compliance/gdpr-requests';
      return api.get<GDPRRequest[]>(url).then(r => r.data);
    }
  });
};

const useConsents = (filters?: { consent_type?: string }) => {
  return useQuery({
    queryKey: ['compliance', 'consents', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.consent_type) params.append('consent_type', filters.consent_type);
      const queryString = params.toString();
      const url = queryString ? `/compliance/consents?${queryString}` : '/compliance/consents';
      return api.get<Consent[]>(url).then(r => r.data);
    }
  });
};

const useUpdateGDPRStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch<void>(`/compliance/gdpr-requests/${id}/status`, { status }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance', 'gdpr'] });
      queryClient.invalidateQueries({ queryKey: ['compliance', 'stats'] });
    }
  });
};

const useAudit = (id: string) => {
  return useQuery({
    queryKey: ['compliance', 'audits', id],
    queryFn: async () => {
      return api.get<AuditType>(`/compliance/audits/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const PoliciesView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: policies = [], isLoading, error, refetch } = usePolicies({
    type: filterType || undefined,
    status: filterStatus || undefined
  });

  const columns: TableColumn<Policy>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Politique', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = POLICY_TYPES.find(t => t.value === (v as string));
      return info?.label || (v as string);
    }},
    { id: 'version', header: 'Version', accessor: 'version', render: (v) => <Badge color="blue">{v as string}</Badge> },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const statusValue = v as string;
      const info = POLICY_STATUS.find(s => s.value === statusValue);
      return <Badge color={STATUS_COLORS[statusValue] || 'gray'}>{info?.label || statusValue}</Badge>;
    }},
    { id: 'is_mandatory', header: 'Obligatoire', accessor: 'is_mandatory', render: (v) => (v as boolean) ? <Badge color="red">Oui</Badge> : '-' },
    { id: 'effective_date', header: 'Effective', accessor: 'effective_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'review_date', header: 'Revision', accessor: 'review_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (v) => <Button size="sm" variant="secondary" onClick={() => { window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view: 'compliance', params: { policyId: v } } })); }}>Voir</Button> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Politiques de conformite</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous types' }, ...POLICY_TYPES]}
            className="w-40"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...POLICY_STATUS]}
            className="w-32"
          />
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createPolicy' } })); }}>Nouvelle politique</Button>
        </div>
      </div>
      <DataTable columns={columns} data={policies} isLoading={isLoading} keyField="id" filterable error={error && typeof error === 'object' && 'message' in error ? error as Error : null} onRetry={() => refetch()} />
    </Card>
  );
};

const AuditsView: React.FC = () => {
  const navigate = useNavigate();
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: audits = [], isLoading, error, refetch } = useAudits({
    type: filterType || undefined,
    status: filterStatus || undefined
  });

  const columns: TableColumn<Audit>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Audit', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = AUDIT_TYPES.find(t => t.value === (v as string));
      return <Badge color="blue">{info?.label || (v as string)}</Badge>;
    }},
    { id: 'auditor', header: 'Auditeur', accessor: 'auditor', render: (v) => (v as string) || '-' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const statusValue = v as string;
      const info = AUDIT_STATUS.find(s => s.value === statusValue);
      return <Badge color={STATUS_COLORS[statusValue] || 'gray'}>{info?.label || statusValue}</Badge>;
    }},
    { id: 'planned_date', header: 'Date prevue', accessor: 'planned_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'findings_count', header: 'Constats', accessor: 'findings_count', render: (v, row) => (
      <div>
        <span>{v as number}</span>
        {row.critical_findings > 0 && <Badge color="red">{row.critical_findings} critiques</Badge>}
      </div>
    )},
    { id: 'score', header: 'Score', accessor: 'score', render: (v) => {
      const scoreValue = v as number;
      return scoreValue ? (
        <Badge color={scoreValue >= 80 ? 'green' : scoreValue >= 60 ? 'orange' : 'red'}>{scoreValue}%</Badge>
      ) : '-';
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (v) => (
      <Button size="sm" variant="secondary" onClick={() => navigate(`/compliance/audits/${v}`)}>Detail</Button>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Audits de conformite</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous types' }, ...AUDIT_TYPES]}
            className="w-36"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...AUDIT_STATUS]}
            className="w-32"
          />
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'planAudit' } })); }}>Planifier audit</Button>
        </div>
      </div>
      <DataTable columns={columns} data={audits} isLoading={isLoading} keyField="id" filterable error={error && typeof error === 'object' && 'message' in error ? error as Error : null} onRetry={() => refetch()} />
    </Card>
  );
};

const GDPRView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: requests = [], isLoading, error, refetch } = useGDPRRequests({
    type: filterType || undefined,
    status: filterStatus || undefined
  });
  const updateStatus = useUpdateGDPRStatus();

  const columns: TableColumn<GDPRRequest>[] = [
    { id: 'reference', header: 'Reference', accessor: 'reference', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = GDPR_TYPES.find(t => t.value === (v as string));
      return <Badge color="blue">{info?.label || (v as string)}</Badge>;
    }},
    { id: 'requester_name', header: 'Demandeur', accessor: 'requester_name' },
    { id: 'requester_email', header: 'Email', accessor: 'requester_email', render: (v) => (
      <span className="text-sm">{v as string}</span>
    )},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const statusValue = v as string;
      const info = GDPR_STATUS.find(s => s.value === statusValue);
      return <Badge color={STATUS_COLORS[statusValue] || 'gray'}>{info?.label || statusValue}</Badge>;
    }},
    { id: 'request_date', header: 'Demande', accessor: 'request_date', render: (v) => formatDate(v as string) },
    { id: 'due_date', header: 'Echeance', accessor: 'due_date', render: (v, row) => {
      const dateValue = v as string;
      const isOverdue = new Date(dateValue) < new Date() && row.status !== 'COMPLETED';
      return <span className={isOverdue ? 'text-red-600 font-bold' : ''}>{formatDate(dateValue)}</span>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        {row.status === 'PENDING' && (
          <Button size="sm" variant="primary" onClick={() => updateStatus.mutate({ id: row.id, status: 'IN_PROGRESS' })}>Traiter</Button>
        )}
        {row.status === 'IN_PROGRESS' && (
          <Button size="sm" variant="success" onClick={() => updateStatus.mutate({ id: row.id, status: 'COMPLETED' })}>Terminer</Button>
        )}
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Demandes RGPD</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous types' }, ...GDPR_TYPES]}
            className="w-36"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...GDPR_STATUS]}
            className="w-32"
          />
        </div>
      </div>
      <DataTable columns={columns} data={requests} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

const ConsentsView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const { data: consents = [], isLoading } = useConsents({
    consent_type: filterType || undefined
  });

  const columns: TableColumn<Consent>[] = [
    { id: 'user_name', header: 'Utilisateur', accessor: 'user_name' },
    { id: 'user_email', header: 'Email', accessor: 'user_email', render: (v) => <span className="text-sm">{v as string}</span> },
    { id: 'consent_type', header: 'Type', accessor: 'consent_type', render: (v) => {
      const info = CONSENT_TYPES.find(t => t.value === (v as string));
      return info?.label || (v as string);
    }},
    { id: 'status', header: 'Consentement', accessor: 'status', render: (v) => {
      const statusValue = v as boolean;
      return <Badge color={statusValue ? 'green' : 'red'}>{statusValue ? 'Accorde' : 'Refuse'}</Badge>;
    }},
    { id: 'given_at', header: 'Date', accessor: 'given_at', render: (v, row) => {
      if (row.status) return (v as string) ? formatDate(v as string) : '-';
      return row.withdrawn_at ? formatDate(row.withdrawn_at) : '-';
    }},
    { id: 'source', header: 'Source', accessor: 'source' },
    { id: 'version', header: 'Version', accessor: 'version', render: (v) => <Badge color="gray">{v as string}</Badge> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Gestion des consentements</h3>
        <Select
          value={filterType}
          onChange={(v) => setFilterType(v)}
          options={[{ value: '', label: 'Tous types' }, ...CONSENT_TYPES]}
          className="w-40"
        />
      </div>
      <DataTable columns={columns} data={consents} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

// ============================================================================
// AUDIT DETAIL VIEW
// ============================================================================

const AuditDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: audit, isLoading, error, refetch } = useAudit(id || '');

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="flex items-center justify-center h-64">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (error || !audit) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <div className="text-center py-8">
            <p className="text-red-600">Audit non trouve</p>
            <Button variant="secondary" onClick={() => navigate('/compliance')} className="mt-4">
              <ArrowLeft size={16} className="mr-2" />
              Retour
            </Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  // Tabs definition
  const tabs: TabDefinition<AuditType>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <ClipboardCheck size={16} />,
      component: AuditInfoTab
    },
    {
      id: 'findings',
      label: 'Constats',
      icon: <AlertTriangle size={16} />,
      badge: audit.findings_count > 0 ? audit.findings_count : undefined,
      component: AuditFindingsTab
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={16} />,
      component: AuditDocumentsTab
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <Clock size={16} />,
      component: AuditHistoryTab
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: AuditIATab
    }
  ];

  // Info bar items
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'type',
      label: 'Type',
      value: AUDIT_TYPE_CONFIG[audit.type]?.label || audit.type,
      valueColor: AUDIT_TYPE_CONFIG[audit.type]?.color as 'blue' | 'purple' | 'orange' || 'gray'
    },
    {
      id: 'score',
      label: 'Score',
      value: audit.score !== undefined ? formatPercent(audit.score) : '-',
      valueColor: audit.score !== undefined ? getAuditScoreColor(audit.score) as 'green' | 'orange' | 'red' : 'gray'
    },
    {
      id: 'findings',
      label: 'Constats',
      value: String(audit.findings_count),
      valueColor: audit.findings_count > 0 ? 'orange' : 'green'
    },
    {
      id: 'critical',
      label: 'Critiques',
      value: String(audit.critical_findings),
      valueColor: audit.critical_findings > 0 ? 'red' : 'green'
    }
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'dates',
      title: 'Calendrier',
      items: [
        { id: 'planned', label: 'Date prevue', value: audit.planned_date ? formatDate(audit.planned_date) : '-' },
        { id: 'start', label: 'Debut', value: audit.start_date ? formatDate(audit.start_date) : '-' },
        { id: 'end', label: 'Fin', value: audit.end_date ? formatDate(audit.end_date) : '-' },
        { id: 'completed', label: 'Cloture', value: audit.completed_date ? formatDate(audit.completed_date) : '-' }
      ]
    },
    {
      id: 'results',
      title: 'Resultats',
      items: [
        {
          id: 'score',
          label: 'Score global',
          value: audit.score !== undefined ? formatPercent(audit.score) : '-',
          highlight: audit.score !== undefined && audit.score >= 80
        },
        { id: 'total_findings', label: 'Total constats', value: String(audit.findings_count) },
        {
          id: 'critical_findings',
          label: 'Constats critiques',
          value: String(audit.critical_findings),
          highlight: audit.critical_findings === 0
        }
      ]
    },
    {
      id: 'team',
      title: 'Equipe',
      items: [
        { id: 'auditor', label: 'Auditeur', value: audit.auditor || audit.lead_auditor || '-' },
        { id: 'company', label: 'Cabinet', value: audit.auditor_company || '-' }
      ]
    }
  ];

  // Header actions
  const headerActions: ActionDefinition[] = [
    {
      id: 'back',
      label: 'Retour',
      icon: <ArrowLeft size={16} />,
      variant: 'secondary',
      onClick: () => navigate('/compliance')
    },
    {
      id: 'edit',
      label: 'Modifier',
      icon: <Edit size={16} />,
      variant: 'secondary',
      onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'editAudit', auditId: audit.id } })); }
    },
    {
      id: 'print',
      label: 'Imprimer',
      icon: <Printer size={16} />,
      variant: 'secondary',
      onClick: () => window.print()
    }
  ];

  // Primary actions (footer - right side)
  const primaryActions: ActionDefinition[] = [];

  if (audit.status === 'PLANNED') {
    primaryActions.push({
      id: 'start',
      label: 'Demarrer l\'audit',
      icon: <Play size={16} />,
      variant: 'primary',
      onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'startAudit', auditId: audit.id } })); }
    });
  }

  if (audit.status === 'IN_PROGRESS') {
    primaryActions.push({
      id: 'complete',
      label: 'Cloturer l\'audit',
      icon: <CheckCircle2 size={16} />,
      variant: 'success',
      onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'completeAudit', auditId: audit.id } })); }
    });
  }

  // Secondary actions (footer - left side)
  const secondaryActions: ActionDefinition[] = [];

  if (audit.report_url) {
    secondaryActions.push({
      id: 'report',
      label: 'Voir le rapport',
      icon: <FileText size={16} />,
      variant: 'secondary',
      onClick: () => { window.open(audit.report_url, '_blank'); }
    });
  }

  return (
    <BaseViewStandard<AuditType>
      title={audit.name}
      subtitle={audit.code}
      status={{
        label: AUDIT_STATUS_CONFIG[audit.status]?.label || audit.status,
        color: (AUDIT_STATUS_CONFIG[audit.status]?.color || 'gray') as SemanticColor
      }}
      data={audit}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      primaryActions={primaryActions}
      secondaryActions={secondaryActions}
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
    />
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'policies' | 'audits' | 'gdpr' | 'consents';

const ComplianceModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats } = useComplianceStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'policies', label: 'Politiques' },
    { id: 'audits', label: 'Audits' },
    { id: 'gdpr', label: 'RGPD' },
    { id: 'consents', label: 'Consentements' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'policies':
        return <PoliciesView />;
      case 'audits':
        return <AuditsView />;
      case 'gdpr':
        return <GDPRView />;
      case 'consents':
        return <ConsentsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Politiques actives"
                value={String(stats?.active_policies || 0)}
                icon={<span className="icon-scroll" />}
                variant="success"
                onClick={() => setCurrentView('policies')}
              />
              <StatCard
                title="Revisions en attente"
                value={String(stats?.pending_reviews || 0)}
                icon={<span className="icon-refresh" />}
                variant={stats?.pending_reviews ? 'warning' : 'success'}
              />
              <StatCard
                title="Audits (annee)"
                value={String(stats?.audits_year || 0)}
                icon={<span className="icon-clipboard" />}
                variant="default"
                onClick={() => setCurrentView('audits')}
              />
              <StatCard
                title="Constats ouverts"
                value={String(stats?.open_findings || 0)}
                icon={<span className="icon-alert" />}
                variant={stats?.open_findings ? 'danger' : 'success'}
              />
            </Grid>

            <Grid cols={4}>
              <StatCard
                title="Demandes RGPD en attente"
                value={String(stats?.gdpr_requests_pending || 0)}
                icon={<span className="icon-lock" />}
                variant={stats?.gdpr_requests_pending ? 'warning' : 'success'}
                onClick={() => setCurrentView('gdpr')}
              />
              <StatCard
                title="Demandes RGPD traitees"
                value={String(stats?.gdpr_requests_completed || 0)}
                icon={<span className="icon-check" />}
                variant="success"
              />
              <StatCard
                title="Score conformite"
                value={formatPercent(stats?.compliance_score || 0)}
                icon={<span className="icon-chart" />}
                variant={stats?.compliance_score && stats.compliance_score >= 80 ? 'success' : 'warning'}
              />
              <StatCard
                title="Taux consentement"
                value={formatPercent(stats?.consent_rate || 0)}
                icon={<span className="icon-users" />}
                variant="default"
                onClick={() => setCurrentView('consents')}
              />
            </Grid>

            <Card>
              <h3 className="text-lg font-semibold mb-4">Score de conformite global</h3>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <ProgressBar
                    value={stats?.compliance_score || 0}
                    max={100}
                    variant={(stats?.compliance_score || 0) >= 80 ? 'success' : (stats?.compliance_score || 0) >= 60 ? 'warning' : 'danger'}
                  />
                </div>
                <div className="text-3xl font-bold">
                  {formatPercent(stats?.compliance_score || 0)}
                </div>
              </div>
            </Card>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Conformite" subtitle="RGPD et conformite reglementaire">
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

// ============================================================================
// ROUTES WRAPPER
// ============================================================================

const ComplianceRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<ComplianceModule />} />
      <Route path="audits/:id" element={<AuditDetailView />} />
    </Routes>
  );
};

export default ComplianceRoutes;
