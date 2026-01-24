/**
 * AZALSCORE Module - HR
 * Gestion des Ressources Humaines
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import { BaseViewStandard } from '@ui/standards';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition, SemanticColor } from '@ui/standards';
import type { TableColumn } from '@/types';
import {
  Users, Calendar, Clock, AlertTriangle, Plus, Minus, Building, BarChart3,
  User, FileText, Euro, History, Sparkles, ArrowLeft, Edit, Eye, Briefcase
} from 'lucide-react';

import type {
  Department, Position, Employee, LeaveRequest, Timesheet, HRDashboard
} from './types';
import {
  formatDate, formatCurrency, getFullName, getSeniorityFormatted, getSeniority,
  CONTRACT_TYPE_CONFIG, EMPLOYEE_STATUS_CONFIG, LEAVE_TYPE_CONFIG, LEAVE_STATUS_CONFIG,
  TIMESHEET_STATUS_CONFIG,
  isActive, isOnLeave, isContractExpiringSoon, isOnProbation,
  getRemainingLeave, getTotalRemainingLeave
} from './types';
import {
  EmployeeInfoTab, EmployeeContractTab, EmployeeLeavesTab,
  EmployeeDocsTab, EmployeeHistoryTab, EmployeeIATab
} from './components';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavItem {
  id: string;
  label: string;
}

interface TabNavProps {
  tabs: TabNavItem[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <div className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

// ============================================================================
// CONSTANTES
// ============================================================================

const CONTRACT_TYPES = [
  { value: 'CDI', label: 'CDI' },
  { value: 'CDD', label: 'CDD' },
  { value: 'INTERIM', label: 'Interim' },
  { value: 'APPRENTICE', label: 'Apprenti' },
  { value: 'INTERN', label: 'Stagiaire' }
];

const EMPLOYEE_STATUSES = [
  { value: 'ACTIVE', label: 'Actif', color: 'green' },
  { value: 'ON_LEAVE', label: 'En conge', color: 'blue' },
  { value: 'SUSPENDED', label: 'Suspendu', color: 'orange' },
  { value: 'TERMINATED', label: 'Termine', color: 'red' }
];

const LEAVE_TYPES = [
  { value: 'PAID', label: 'Conges payes' },
  { value: 'UNPAID', label: 'Sans solde' },
  { value: 'SICK', label: 'Maladie' },
  { value: 'MATERNITY', label: 'Maternite' },
  { value: 'PATERNITY', label: 'Paternite' },
  { value: 'OTHER', label: 'Autre' }
];

const LEAVE_STATUSES = [
  { value: 'PENDING', label: 'En attente', color: 'orange' },
  { value: 'APPROVED', label: 'Approuve', color: 'green' },
  { value: 'REJECTED', label: 'Rejete', color: 'red' },
  { value: 'CANCELLED', label: 'Annule', color: 'gray' }
];

const TIMESHEET_STATUSES = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'SUBMITTED', label: 'Soumis', color: 'blue' },
  { value: 'APPROVED', label: 'Approuve', color: 'green' },
  { value: 'REJECTED', label: 'Rejete', color: 'red' }
];

// ============================================================================
// HELPERS
// ============================================================================

const getStatusInfo = (statuses: { value: string; label: string; color: string }[], status: string) => {
  return statuses.find(s => s.value === status) || { label: status, color: 'gray' };
};

const buildUrlWithParams = (baseUrl: string, params?: Record<string, string | undefined>): string => {
  if (!params) return baseUrl;
  const filteredParams = Object.entries(params).filter(([_, v]) => v !== undefined);
  if (filteredParams.length === 0) return baseUrl;
  const queryString = filteredParams.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v!)}`).join('&');
  return `${baseUrl}?${queryString}`;
};

// ============================================================================
// API HOOKS
// ============================================================================

const useHRDashboard = () => {
  return useQuery({
    queryKey: ['hr', 'dashboard'],
    queryFn: async () => {
      return api.get<HRDashboard>('/v1/hr/dashboard').then(r => r.data);
    }
  });
};

const useDepartments = () => {
  return useQuery({
    queryKey: ['hr', 'departments'],
    queryFn: async () => {
      const response = await api.get<Department[] | { items: Department[] }>('/v1/hr/departments').then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

const usePositions = () => {
  return useQuery({
    queryKey: ['hr', 'positions'],
    queryFn: async () => {
      const response = await api.get<Position[] | { items: Position[] }>('/v1/hr/positions').then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

const useEmployees = (filters?: { department_id?: string; status?: string; contract_type?: string }) => {
  return useQuery({
    queryKey: ['hr', 'employees', filters],
    queryFn: async () => {
      const url = buildUrlWithParams('/v1/hr/employees', filters);
      const response = await api.get<{ items: Employee[] }>(url).then(r => r.data);
      return response?.items || [];
    }
  });
};

const useEmployee = (id: string) => {
  return useQuery({
    queryKey: ['hr', 'employee', id],
    queryFn: async () => {
      return api.get<Employee>(`/v1/hr/employees/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

const useLeaveRequests = (filters?: { status?: string; type?: string }) => {
  return useQuery({
    queryKey: ['hr', 'leave-requests', filters],
    queryFn: async () => {
      const url = buildUrlWithParams('/v1/hr/leave-requests', filters);
      const response = await api.get<{ items: LeaveRequest[] }>(url).then(r => r.data);
      return response?.items || [];
    }
  });
};

const useTimesheets = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: ['hr', 'timesheets', filters],
    queryFn: async () => {
      const url = buildUrlWithParams('/v1/hr/timesheets', filters);
      const response = await api.get<Timesheet[] | { items: Timesheet[] }>(url).then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

const useCreateEmployee = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Employee>) => {
      return api.post<Employee>('/v1/hr/employees', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

const useCreateLeaveRequest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<LeaveRequest>) => {
      return api.post<LeaveRequest>('/v1/hr/leave-requests', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'leave-requests'] })
  });
};

const useApproveLeave = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<LeaveRequest>(`/v1/hr/leave-requests/${id}/approve`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

const useRejectLeave = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<LeaveRequest>(`/v1/hr/leave-requests/${id}/reject`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

// ============================================================================
// VUE DETAIL - EMPLOYEE
// ============================================================================

interface EmployeeDetailViewProps {
  employeeId: string;
  onBack: () => void;
  onEdit?: () => void;
}

const EmployeeDetailView: React.FC<EmployeeDetailViewProps> = ({ employeeId, onBack, onEdit }) => {
  const { data: employee, isLoading, error } = useEmployee(employeeId);

  if (isLoading) {
    return (
      <div className="azals-loading">
        <div className="azals-loading__spinner" />
        <p>Chargement du dossier employe...</p>
      </div>
    );
  }

  if (error || !employee) {
    return (
      <div className="azals-error">
        <p>Erreur lors du chargement du dossier.</p>
        <Button onClick={onBack} leftIcon={<ArrowLeft size={16} />}>Retour</Button>
      </div>
    );
  }

  // Configuration des onglets
  const tabs: TabDefinition<Employee>[] = [
    { id: 'info', label: 'Informations', icon: <User size={16} />, component: EmployeeInfoTab },
    { id: 'contract', label: 'Contrat', icon: <FileText size={16} />, component: EmployeeContractTab },
    { id: 'leaves', label: 'Conges', icon: <Calendar size={16} />, badge: employee.leave_requests?.filter(r => r.status === 'PENDING').length, component: EmployeeLeavesTab },
    { id: 'docs', label: 'Documents', icon: <FileText size={16} />, badge: employee.documents?.length, component: EmployeeDocsTab },
    { id: 'history', label: 'Historique', icon: <History size={16} />, component: EmployeeHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: EmployeeIATab }
  ];

  // Configuration InfoBar
  const statusConfig = EMPLOYEE_STATUS_CONFIG[employee.status];
  const contractConfig = CONTRACT_TYPE_CONFIG[employee.contract_type];

  const infoBarItems: InfoBarItem[] = [
    {
      id: 'department',
      label: 'Departement',
      value: employee.department_name || '-',
      icon: <Building size={16} />
    },
    {
      id: 'position',
      label: 'Poste',
      value: employee.position_title || '-',
      icon: <Briefcase size={16} />
    },
    {
      id: 'seniority',
      label: 'Anciennete',
      value: getSeniorityFormatted(employee),
      icon: <Clock size={16} />
    },
    {
      id: 'leave-balance',
      label: 'Conges restants',
      value: `${getTotalRemainingLeave(employee)}j`,
      valueColor: getTotalRemainingLeave(employee) > 20 ? 'orange' : 'green'
    }
  ];

  // Configuration Sidebar
  const sidebarSections: SidebarSection[] = [
    {
      id: 'status',
      title: 'Statut',
      items: [
        { id: 'status', label: 'Statut', value: statusConfig.label },
        { id: 'contract', label: 'Contrat', value: contractConfig.label },
        { id: 'hire-date', label: 'Embauche', value: formatDate(employee.hire_date) }
      ]
    },
    {
      id: 'leaves',
      title: 'Conges',
      items: [
        { id: 'cp', label: 'CP restants', value: `${getRemainingLeave(employee, 'PAID')}j`, highlight: getRemainingLeave(employee, 'PAID') > 20 },
        { id: 'total', label: 'Total restant', value: `${getTotalRemainingLeave(employee)}j` }
      ]
    },
    {
      id: 'salary',
      title: 'Remuneration',
      items: [
        { id: 'salary', label: 'Salaire mensuel', value: employee.salary ? formatCurrency(employee.salary) : '-', format: 'currency' }
      ]
    }
  ];

  // Actions header
  const headerActions: ActionDefinition[] = [
    { id: 'back', label: 'Retour', icon: <ArrowLeft size={16} />, variant: 'ghost', onClick: onBack },
    ...(onEdit ? [{ id: 'edit', label: 'Modifier', icon: <Edit size={16} />, variant: 'secondary' as const, onClick: onEdit }] : [])
  ];

  // Actions primaires
  const primaryActions: ActionDefinition[] = [
    {
      id: 'new-leave',
      label: 'Demande de conge',
      icon: <Calendar size={16} />,
      variant: 'secondary'
    }
  ];

  // Mapping couleurs
  const statusColorMap: Record<string, SemanticColor> = {
    gray: 'gray',
    blue: 'blue',
    orange: 'orange',
    green: 'green',
    red: 'red'
  };

  return (
    <BaseViewStandard<Employee>
      title={getFullName(employee)}
      subtitle={`${employee.employee_number} - ${employee.position_title || 'N/A'}`}
      status={{
        label: statusConfig.label,
        color: statusColorMap[statusConfig.color] || 'gray'
      }}
      data={employee}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      primaryActions={primaryActions}
    />
  );
};

// ============================================================================
// VUES LISTE
// ============================================================================

interface EmployeesViewProps {
  onSelectEmployee: (id: string) => void;
}

const EmployeesView: React.FC<EmployeesViewProps> = ({ onSelectEmployee }) => {
  const [filterDepartment, setFilterDepartment] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterContract, setFilterContract] = useState<string>('');
  const { data: employees = [], isLoading } = useEmployees({
    department_id: filterDepartment || undefined,
    status: filterStatus || undefined,
    contract_type: filterContract || undefined
  });
  const { data: departments = [] } = useDepartments();
  const { data: positions = [] } = usePositions();
  const createEmployee = useCreateEmployee();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<Employee>>({});

  const handleSubmit = async () => {
    await createEmployee.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<Employee>[] = [
    { id: 'employee_number', header: 'N', accessor: 'employee_number', render: (v, row) => (
      <button
        className="font-mono text-blue-600 hover:underline"
        onClick={() => onSelectEmployee(row.id)}
      >
        {v as string}
      </button>
    )},
    { id: 'last_name', header: 'Nom', accessor: 'last_name', render: (_, row) => getFullName(row as Employee) },
    { id: 'department_name', header: 'Departement', accessor: 'department_name', render: (v) => (v as string) || '-' },
    { id: 'position_title', header: 'Poste', accessor: 'position_title', render: (v) => (v as string) || '-' },
    { id: 'contract_type', header: 'Contrat', accessor: 'contract_type', render: (v) => {
      const info = CONTRACT_TYPES.find(t => t.value === v);
      return info?.label || (v as string);
    }},
    { id: 'hire_date', header: 'Embauche', accessor: 'hire_date', render: (v) => formatDate(v as string) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(EMPLOYEE_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'actions', header: '', accessor: 'id', render: (_, row) => (
      <Button size="sm" variant="ghost" onClick={() => onSelectEmployee(row.id)}>
        <Eye size={14} />
      </Button>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Employes</h3>
        <div className="flex gap-2">
          <Select
            value={filterDepartment}
            onChange={(v) => setFilterDepartment(v)}
            options={[{ value: '', label: 'Tous departements' }, ...departments.map(d => ({ value: d.id, label: d.name }))]}
            className="w-40"
          />
          <Select
            value={filterContract}
            onChange={(v) => setFilterContract(v)}
            options={[{ value: '', label: 'Tous contrats' }, ...CONTRACT_TYPES]}
            className="w-32"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...EMPLOYEE_STATUSES]}
            className="w-32"
          />
          <Button onClick={() => setShowModal(true)}>Nouvel employe</Button>
        </div>
      </div>
      <DataTable columns={columns} data={employees} isLoading={isLoading} keyField="id" />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvel employe" size="lg">
        <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Prenom</label>
              <Input
                value={formData.first_name || ''}
                onChange={(v) => setFormData({ ...formData, first_name: v })}
              />
            </div>
            <div className="azals-field">
              <label>Nom</label>
              <Input
                value={formData.last_name || ''}
                onChange={(v) => setFormData({ ...formData, last_name: v })}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Email</label>
              <Input
                type="email"
                value={formData.email || ''}
                onChange={(v) => setFormData({ ...formData, email: v })}
              />
            </div>
            <div className="azals-field">
              <label>Telephone</label>
              <Input
                value={formData.phone || ''}
                onChange={(v) => setFormData({ ...formData, phone: v })}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Departement</label>
              <Select
                value={formData.department_id || ''}
                onChange={(v) => setFormData({ ...formData, department_id: v })}
                options={[{ value: '', label: 'Selectionner...' }, ...departments.map(d => ({ value: d.id, label: d.name }))]}
              />
            </div>
            <div className="azals-field">
              <label>Poste</label>
              <Select
                value={formData.position_id || ''}
                onChange={(v) => setFormData({ ...formData, position_id: v })}
                options={[{ value: '', label: 'Selectionner...' }, ...positions.map(p => ({ value: p.id, label: p.title }))]}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Type de contrat</label>
              <Select
                value={formData.contract_type || ''}
                onChange={(v) => setFormData({ ...formData, contract_type: v as Employee['contract_type'] })}
                options={CONTRACT_TYPES}
              />
            </div>
            <div className="azals-field">
              <label>Date d'embauche</label>
              <input
                type="date"
                className="azals-input"
                value={formData.hire_date || ''}
                onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                required
              />
            </div>
          </Grid>
          {(formData.contract_type === 'CDD' || formData.contract_type === 'INTERIM') && (
            <div className="azals-field">
              <label>Date de fin de contrat</label>
              <input
                type="date"
                className="azals-input"
                value={formData.contract_end_date || ''}
                onChange={(e) => setFormData({ ...formData, contract_end_date: e.target.value })}
              />
            </div>
          )}
          <div className="azals-field">
            <label>Salaire mensuel</label>
            <Input
              type="number"
              value={formData.salary?.toString() || ''}
              onChange={(v) => setFormData({ ...formData, salary: parseFloat(v) })}
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createEmployee.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const LeaveRequestsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('');
  const { data: requests = [], isLoading } = useLeaveRequests({
    status: filterStatus || undefined,
    type: filterType || undefined
  });
  const { data: employees = [] } = useEmployees();
  const createRequest = useCreateLeaveRequest();
  const approveLeave = useApproveLeave();
  const rejectLeave = useRejectLeave();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<LeaveRequest>>({});

  const handleSubmit = async () => {
    await createRequest.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<LeaveRequest>[] = [
    { id: 'employee_name', header: 'Employe', accessor: 'employee_name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = LEAVE_TYPES.find(t => t.value === v);
      return info?.label || (v as string);
    }},
    { id: 'start_date', header: 'Debut', accessor: 'start_date', render: (v) => formatDate(v as string) },
    { id: 'end_date', header: 'Fin', accessor: 'end_date', render: (v) => formatDate(v as string) },
    { id: 'days', header: 'Jours', accessor: 'days' },
    { id: 'reason', header: 'Motif', accessor: 'reason', render: (v) => (v as string) || '-' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(LEAVE_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      (row as LeaveRequest).status === 'PENDING' ? (
        <div className="flex gap-1">
          <Button size="sm" onClick={() => approveLeave.mutate((row as LeaveRequest).id)}>Approuver</Button>
          <Button size="sm" variant="secondary" onClick={() => rejectLeave.mutate((row as LeaveRequest).id)}>Refuser</Button>
        </div>
      ) : null
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Demandes de conges</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous types' }, ...LEAVE_TYPES]}
            className="w-36"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...LEAVE_STATUSES]}
            className="w-36"
          />
          <Button onClick={() => setShowModal(true)}>Nouvelle demande</Button>
        </div>
      </div>
      <DataTable columns={columns} data={requests} isLoading={isLoading} keyField="id" />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvelle demande de conge">
        <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
          <div className="azals-field">
            <label>Employe</label>
            <Select
              value={formData.employee_id || ''}
              onChange={(v) => setFormData({ ...formData, employee_id: v })}
              options={employees.map(e => ({ value: e.id, label: `${e.first_name} ${e.last_name}` }))}
            />
          </div>
          <div className="azals-field">
            <label>Type de conge</label>
            <Select
              value={formData.type || ''}
              onChange={(v) => setFormData({ ...formData, type: v as LeaveRequest['type'] })}
              options={LEAVE_TYPES}
            />
          </div>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Date de debut</label>
              <input
                type="date"
                className="azals-input"
                value={formData.start_date || ''}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                required
              />
            </div>
            <div className="azals-field">
              <label>Date de fin</label>
              <input
                type="date"
                className="azals-input"
                value={formData.end_date || ''}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                required
              />
            </div>
          </Grid>
          <div className="azals-field">
            <label>Motif (optionnel)</label>
            <Input
              value={formData.reason || ''}
              onChange={(v) => setFormData({ ...formData, reason: v })}
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createRequest.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const DepartmentsView: React.FC = () => {
  const { data: departments = [], isLoading } = useDepartments();

  const columns: TableColumn<Department>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'manager_name', header: 'Responsable', accessor: 'manager_name', render: (v) => (v as string) || '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Departements</h3>
        <Button>Nouveau departement</Button>
      </div>
      <DataTable columns={columns} data={departments} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const TimesheetsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: timesheets = [], isLoading } = useTimesheets({
    status: filterStatus || undefined
  });

  const columns: TableColumn<Timesheet>[] = [
    { id: 'employee_name', header: 'Employe', accessor: 'employee_name' },
    { id: 'period_start', header: 'Debut periode', accessor: 'period_start', render: (v) => formatDate(v as string) },
    { id: 'period_end', header: 'Fin periode', accessor: 'period_end', render: (v) => formatDate(v as string) },
    { id: 'total_hours', header: 'Heures totales', accessor: 'total_hours' },
    { id: 'overtime_hours', header: 'Heures sup.', accessor: 'overtime_hours' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(TIMESHEET_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Feuilles de temps</h3>
        <Select
          value={filterStatus}
          onChange={(v) => setFilterStatus(v)}
          options={[{ value: '', label: 'Tous statuts' }, ...TIMESHEET_STATUSES]}
          className="w-40"
        />
      </div>
      <DataTable columns={columns} data={timesheets} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'employees' | 'departments' | 'leave' | 'timesheets' | 'employee-detail';

const HRModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string | null>(null);
  const { data: dashboard } = useHRDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'employees', label: 'Employes' },
    { id: 'departments', label: 'Departements' },
    { id: 'leave', label: 'Conges' },
    { id: 'timesheets', label: 'Temps' }
  ];

  const handleSelectEmployee = (id: string) => {
    setSelectedEmployeeId(id);
    setCurrentView('employee-detail');
  };

  const handleBackFromDetail = () => {
    setSelectedEmployeeId(null);
    setCurrentView('employees');
  };

  // Vue detail d'un employe
  if (currentView === 'employee-detail' && selectedEmployeeId) {
    return (
      <EmployeeDetailView
        employeeId={selectedEmployeeId}
        onBack={handleBackFromDetail}
      />
    );
  }

  const renderContent = () => {
    switch (currentView) {
      case 'employees':
        return <EmployeesView onSelectEmployee={handleSelectEmployee} />;
      case 'departments':
        return <DepartmentsView />;
      case 'leave':
        return <LeaveRequestsView />;
      case 'timesheets':
        return <TimesheetsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Employes actifs"
                value={String(dashboard?.active_employees || 0)}
                icon={<Users />}
                variant="default"
                onClick={() => setCurrentView('employees')}
              />
              <StatCard
                title="En conge"
                value={String(dashboard?.on_leave || 0)}
                icon={<Calendar />}
                variant="success"
                onClick={() => setCurrentView('leave')}
              />
              <StatCard
                title="Demandes en attente"
                value={String(dashboard?.pending_leave_requests || 0)}
                icon={<Clock />}
                variant="warning"
                onClick={() => setCurrentView('leave')}
              />
              <StatCard
                title="Contrats expirant"
                value={String(dashboard?.contracts_expiring_soon || 0)}
                icon={<AlertTriangle />}
                variant="danger"
                onClick={() => setCurrentView('employees')}
              />
            </Grid>
            <Grid cols={4}>
              <StatCard
                title="Embauches (mois)"
                value={String(dashboard?.new_hires_month || 0)}
                icon={<Plus />}
                variant="success"
              />
              <StatCard
                title="Departs (mois)"
                value={String(dashboard?.terminations_month || 0)}
                icon={<Minus />}
                variant="danger"
              />
              <StatCard
                title="Departements"
                value={String(dashboard?.departments_count || 0)}
                icon={<Building />}
                variant="default"
                onClick={() => setCurrentView('departments')}
              />
              <StatCard
                title="Total employes"
                value={String(dashboard?.total_employees || 0)}
                icon={<BarChart3 />}
                variant="default"
              />
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper
      title="Ressources Humaines"
      subtitle="Gestion du personnel et des conges"
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

export default HRModule;
