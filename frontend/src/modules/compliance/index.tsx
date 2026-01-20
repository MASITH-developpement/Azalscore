import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input, TextArea } from '@ui/forms';
import { StatCard, ProgressBar } from '@ui/dashboards';
import type { TableColumn } from '@/types';

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

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const formatPercent = (value: number): string => {
  return `${value.toFixed(0)}%`;
};

// ============================================================================
// API HOOKS
// ============================================================================

const useComplianceStats = () => {
  return useQuery({
    queryKey: ['compliance', 'stats'],
    queryFn: async () => {
      return api.get<ComplianceStats>('/v1/compliance/stats').then(r => r.data);
    }
  });
};

const usePolicies = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: ['compliance', 'policies', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/v1/compliance/policies?${queryString}` : '/v1/compliance/policies';
      return api.get<Policy[]>(url).then(r => r.data);
    }
  });
};

const useAudits = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: ['compliance', 'audits', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/v1/compliance/audits?${queryString}` : '/v1/compliance/audits';
      return api.get<Audit[]>(url).then(r => r.data);
    }
  });
};

const useGDPRRequests = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: ['compliance', 'gdpr', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/v1/compliance/gdpr-requests?${queryString}` : '/v1/compliance/gdpr-requests';
      return api.get<GDPRRequest[]>(url).then(r => r.data);
    }
  });
};

const useConsents = (filters?: { consent_type?: string }) => {
  return useQuery({
    queryKey: ['compliance', 'consents', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.consent_type) params.append('consent_type', filters.consent_type);
      const queryString = params.toString();
      const url = queryString ? `/v1/compliance/consents?${queryString}` : '/v1/compliance/consents';
      return api.get<Consent[]>(url).then(r => r.data);
    }
  });
};

const useUpdateGDPRStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch<void>(`/v1/compliance/gdpr-requests/${id}/status`, { status }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance', 'gdpr'] });
      queryClient.invalidateQueries({ queryKey: ['compliance', 'stats'] });
    }
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const PoliciesView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: policies = [], isLoading } = usePolicies({
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
    { id: 'actions', header: 'Actions', accessor: 'id', render: () => <Button size="sm" variant="secondary">Voir</Button> }
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
          <Button>Nouvelle politique</Button>
        </div>
      </div>
      <DataTable columns={columns} data={policies} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const AuditsView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: audits = [], isLoading } = useAudits({
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
    { id: 'actions', header: 'Actions', accessor: 'id', render: () => <Button size="sm" variant="secondary">Detail</Button> }
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
          <Button>Planifier audit</Button>
        </div>
      </div>
      <DataTable columns={columns} data={audits} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const GDPRView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: requests = [], isLoading } = useGDPRRequests({
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
      <DataTable columns={columns} data={requests} isLoading={isLoading} keyField="id" />
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
      <DataTable columns={columns} data={consents} isLoading={isLoading} keyField="id" />
    </Card>
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

export default ComplianceModule;
