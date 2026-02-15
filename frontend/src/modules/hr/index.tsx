/**
 * AZALSCORE Module - HR
 * Gestion des Ressources Humaines
 */

import React, { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
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
  User, FileText, Euro, History, Sparkles, ArrowLeft, Edit, Eye, Briefcase, Trash2
} from 'lucide-react';

import type {
  Department, Position, Employee, LeaveRequest, Timesheet, TimeEntry, HRDashboard
} from './types';
import {
  getFullName, getSeniorityFormatted, getSeniority,
  CONTRACT_TYPE_CONFIG, EMPLOYEE_STATUS_CONFIG, LEAVE_TYPE_CONFIG, LEAVE_STATUS_CONFIG,
  TIMESHEET_STATUS_CONFIG,
  isActive, isOnLeave, isContractExpiringSoon, isOnProbation,
  getRemainingLeave, getTotalRemainingLeave
} from './types';
import { formatDate, formatCurrency } from '@/utils/formatters';
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
  return useQuery<HRDashboard | null, Error>({
    queryKey: ['hr', 'dashboard'],
    queryFn: async (): Promise<HRDashboard | null> => {
      const response: any = await api.get('/hr/dashboard');
      // Handle both direct response and wrapped { data: {...} }
      if (response?.pending_leave_requests !== undefined) {
        return response as HRDashboard;
      }
      if (response?.data?.pending_leave_requests !== undefined) {
        return response.data as HRDashboard;
      }
      return response || null;
    }
  });
};

const useDepartments = () => {
  return useQuery({
    queryKey: ['hr', 'departments'],
    queryFn: async () => {
      const response = await api.get<{ data: Department[] } | Department[]>('/hr/departments');
      // Handle both wrapped { data: [...] } and direct [...] responses
      if (Array.isArray(response)) {
        return response;
      }
      if (response && typeof response === 'object' && 'data' in response) {
        return Array.isArray(response.data) ? response.data : [];
      }
      return [];
    }
  });
};

const usePositions = () => {
  return useQuery({
    queryKey: ['hr', 'positions'],
    queryFn: async () => {
      const response = await api.get<{ data: Position[] } | Position[]>('/hr/positions');
      // Handle both wrapped { data: [...] } and direct [...] responses
      if (Array.isArray(response)) {
        return response;
      }
      if (response && typeof response === 'object' && 'data' in response) {
        return Array.isArray(response.data) ? response.data : [];
      }
      return [];
    }
  });
};

const useEmployees = (filters?: { department_id?: string; status?: string; contract_type?: string }) => {
  return useQuery<Employee[], Error>({
    queryKey: ['hr', 'employees', serializeFilters(filters)],
    queryFn: async (): Promise<Employee[]> => {
      const url = buildUrlWithParams('/hr/employees', filters);
      const response: any = await api.get(url);
      // Handle both direct { items: [...] } and wrapped { data: { items: [...] } }
      if (response?.items) {
        return response.items as Employee[];
      }
      if (response?.data?.items) {
        return response.data.items as Employee[];
      }
      return [];
    }
  });
};

const useEmployee = (id: string) => {
  return useQuery<Employee | null, Error>({
    queryKey: ['hr', 'employee', id],
    queryFn: async (): Promise<Employee | null> => {
      const response: any = await api.get(`/hr/employees/${id}`);
      if (response?.data) {
        return response.data as Employee;
      }
      if (response?.id) {
        return response as Employee;
      }
      return null;
    },
    enabled: !!id
  });
};

const useLeaveRequests = (filters?: { status?: string; type?: string }) => {
  return useQuery<LeaveRequest[], Error>({
    queryKey: ['hr', 'leave-requests', serializeFilters(filters)],
    queryFn: async (): Promise<LeaveRequest[]> => {
      const url = buildUrlWithParams('/hr/leave-requests', filters);
      const response: any = await api.get(url);
      // Handle both direct { items: [...] } and wrapped { data: { items: [...] } }
      if (response?.items) {
        return response.items as LeaveRequest[];
      }
      if (response?.data?.items) {
        return response.data.items as LeaveRequest[];
      }
      return [];
    }
  });
};

const useTimeEntries = (filters?: { employee_id?: string; from_date?: string; to_date?: string }) => {
  return useQuery({
    queryKey: ['hr', 'time-entries', serializeFilters(filters)],
    queryFn: async () => {
      const url = buildUrlWithParams('/hr/time-entries', filters);
      const response = await api.get<TimeEntry[] | { items: TimeEntry[] }>(url).then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

// Alias pour compatibilite
const useTimesheets = useTimeEntries;

interface TimeEntryCreateData {
  date: string;
  start_time?: string;
  end_time?: string;
  break_duration?: number;
  worked_hours: number;
  overtime_hours?: number;
  project_id?: string;
  task_description?: string;
}

const useCreateTimeEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ employee_id, data }: { employee_id: string; data: TimeEntryCreateData }) => {
      return api.post<TimeEntry>(`/hr/employees/${employee_id}/time-entries`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'time-entries'] })
  });
};

const useCreateEmployee = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Employee>) => {
      return api.post<Employee>('/hr/employees', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

interface LeaveRequestCreateData {
  employee_id: string;
  type: string;
  start_date: string;
  end_date: string;
  reason?: string;
}

const useCreateLeaveRequest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: LeaveRequestCreateData) => {
      const response = await api.post<LeaveRequest>('/hr/leave-requests', data);
      // Handle both wrapped and direct response
      return (response as { data?: LeaveRequest }).data || response;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'leave-requests'] })
  });
};

const useApproveLeave = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response: any = await api.post(`/hr/leave-requests/${id}/approve`);
      return response?.data || response;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

const useRejectLeave = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      const response: any = await api.post(`/hr/leave-requests/${id}/reject?rejection_reason=${encodeURIComponent(reason)}`);
      return response?.data || response;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

interface LeaveRequestUpdateData {
  type?: string;
  start_date?: string;
  end_date?: string;
  half_day_start?: boolean;
  half_day_end?: boolean;
  reason?: string;
  resubmit?: boolean;
}

const useUpdateLeaveRequest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: LeaveRequestUpdateData }) => {
      const response: any = await api.put(`/hr/leave-requests/${id}`, data);
      return response?.data || response;
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
  const { data: employee, isLoading, error, refetch } = useEmployee(employeeId);

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
      error={error ? (error as Error) : null}
      onRetry={() => refetch()}
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
  const { data: employees = [], isLoading, error, refetch } = useEmployees({
    department_id: filterDepartment || undefined,
    status: filterStatus || undefined,
    contract_type: filterContract || undefined
  });
  const { data: departments = [], refetch: refetchDepartments } = useDepartments();
  const { data: positions = [], refetch: refetchPositions } = usePositions();
  const createEmployee = useCreateEmployee();
  const updateEmployee = useUpdateEmployee();
  const deleteEmployee = useDeleteEmployee();
  const createDepartment = useCreateDepartment();
  const createPosition = useCreatePosition();
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [showPosModal, setShowPosModal] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const editFormRef = useRef<HTMLFormElement>(null);
  const [formKey, setFormKey] = useState(0); // Pour réinitialiser le formulaire
  const [newDeptData, setNewDeptData] = useState<{ code: string; name: string }>({ code: '', name: '' });
  const [newPosData, setNewPosData] = useState<{ code: string; title: string }>({ code: '', title: '' });
  const [deptError, setDeptError] = useState<string>('');
  const [posError, setPosError] = useState<string>('');
  const [deleteError, setDeleteError] = useState<string>('');

  const handleDeleteEmployee = async (emp: Employee) => {
    const fullName = `${emp.first_name} ${emp.last_name}`;
    if (!window.confirm(`Supprimer l'employé "${fullName}" ?`)) return;
    setDeleteError('');
    try {
      await deleteEmployee.mutateAsync(emp.id);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Erreur lors de la suppression';
      setDeleteError(msg);
    }
  };

  const handleEditEmployee = (emp: Employee) => {
    setEditingEmployee(emp);
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editFormRef.current || !editingEmployee) return;

    const form = new FormData(editFormRef.current);
    const dataToSubmit: Record<string, unknown> = {
      // Informations personnelles
      first_name: form.get('first_name') as string,
      last_name: form.get('last_name') as string,
      maiden_name: form.get('maiden_name') as string || undefined,
      gender: form.get('gender') as string || undefined,
      birth_date: form.get('birth_date') as string || undefined,
      birth_place: form.get('birth_place') as string || undefined,
      nationality: form.get('nationality') as string || undefined,
      // Contact
      email: form.get('email') as string || undefined,
      personal_email: form.get('personal_email') as string || undefined,
      phone: form.get('phone') as string || undefined,
      mobile: form.get('mobile') as string || undefined,
      // Adresse
      address_line1: form.get('address_line1') as string || undefined,
      address_line2: form.get('address_line2') as string || undefined,
      postal_code: form.get('postal_code') as string || undefined,
      city: form.get('city') as string || undefined,
      country: form.get('country') as string || undefined,
      // Organisation
      department_id: form.get('department_id') as string || undefined,
      position_id: form.get('position_id') as string || undefined,
      manager_id: form.get('manager_id') as string || undefined,
      work_location: form.get('work_location') as string || undefined,
      // Contrat
      contract_type: form.get('contract_type') as string || 'CDI',
      hire_date: form.get('hire_date') as string,
      contract_end_date: form.get('contract_end_date') as string || undefined,
      status: form.get('status') as string || 'ACTIVE',
      // Banque
      bank_name: form.get('bank_name') as string || undefined,
      iban: form.get('iban') as string || undefined,
      bic: form.get('bic') as string || undefined,
      // Autres
      notes: form.get('notes') as string || undefined,
      is_active: form.get('is_active') === 'on',
    };

    const salaryValue = form.get('gross_salary') as string;
    if (salaryValue) {
      dataToSubmit.gross_salary = parseFloat(salaryValue.replace(',', '.'));
    }
    const weeklyHours = form.get('weekly_hours') as string;
    if (weeklyHours) {
      dataToSubmit.weekly_hours = parseFloat(weeklyHours.replace(',', '.'));
    }

    try {
      await updateEmployee.mutateAsync({ id: editingEmployee.id, data: dataToSubmit as Partial<Employee> });
      setShowEditModal(false);
      setEditingEmployee(null);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Erreur lors de la modification';
      alert(`Erreur: ${msg}`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formRef.current) return;

    const form = new FormData(formRef.current);
    const dataToSubmit: Record<string, unknown> = {
      first_name: form.get('first_name') as string,
      last_name: form.get('last_name') as string,
      email: form.get('email') as string || undefined,
      phone: form.get('phone') as string || undefined,
      department_id: form.get('department_id') as string || undefined,
      position_id: form.get('position_id') as string || undefined,
      contract_type: form.get('contract_type') as string || 'CDI',
      hire_date: form.get('hire_date') as string,
      contract_end_date: form.get('contract_end_date') as string || undefined,
    };

    const salaryValue = form.get('gross_salary') as string;
    if (salaryValue) {
      dataToSubmit.gross_salary = parseFloat(salaryValue.replace(',', '.'));
    }

    // Générer employee_number automatiquement
    dataToSubmit.employee_number = `EMP-${Date.now().toString(36).toUpperCase()}`;

    await createEmployee.mutateAsync(dataToSubmit as Partial<Employee>);
    setShowModal(false);
    setFormKey(k => k + 1); // Réinitialiser le formulaire
  };

  const handleCreateDepartment = async () => {
    if (!newDeptData.code || !newDeptData.name) {
      setDeptError('Code et nom requis');
      return;
    }
    setDeptError('');
    try {
      const created = await createDepartment.mutateAsync(newDeptData);
      // Fermer le modal et rafraîchir la liste
      setShowDeptModal(false);
      setNewDeptData({ code: '', name: '' });
      await refetchDepartments();
      // Sélectionner le nouveau département dans le formulaire
      if (created?.id && formRef.current) {
        const select = formRef.current.querySelector<HTMLSelectElement>('select[name="department_id"]');
        if (select) select.value = created.id;
      }
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 409) {
        setDeptError(`Le code "${newDeptData.code}" existe deja. Choisissez un autre code.`);
      } else {
        const msg = err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'Erreur lors de la creation';
        setDeptError(msg);
      }
    }
  };

  const handleCreatePosition = async () => {
    if (!newPosData.code || !newPosData.title) {
      setPosError('Code et intitule requis');
      return;
    }
    setPosError('');
    try {
      const created = await createPosition.mutateAsync(newPosData);
      // Fermer le modal et rafraîchir la liste
      setShowPosModal(false);
      setNewPosData({ code: '', title: '' });
      await refetchPositions();
      // Sélectionner le nouveau poste dans le formulaire
      if (created?.id && formRef.current) {
        const select = formRef.current.querySelector<HTMLSelectElement>('select[name="position_id"]');
        if (select) select.value = created.id;
      }
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 409) {
        setPosError(`Le code "${newPosData.code}" existe deja. Choisissez un autre code.`);
      } else {
        const msg = err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'Erreur lors de la creation';
        setPosError(msg);
      }
    }
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
      <div className="flex gap-1">
        <Button size="sm" variant="ghost" onClick={() => onSelectEmployee(row.id)}>
          <Eye size={14} />
        </Button>
        <button
          className="azals-btn azals-btn--sm azals-btn--secondary"
          onClick={() => handleEditEmployee(row as Employee)}
          title="Modifier"
        >
          <Edit size={14} />
        </button>
        <Button size="sm" variant="ghost" onClick={() => handleDeleteEmployee(row as Employee)}>
          <Trash2 size={14} className="text-red-500" />
        </Button>
      </div>
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
      {deleteError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {deleteError}
        </div>
      )}
      <DataTable columns={columns} data={employees} isLoading={isLoading} keyField="id" filterable error={error && typeof error === 'object' && 'message' in error ? error as Error : null} onRetry={() => refetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvel employe" size="lg">
        <form key={formKey} ref={formRef} onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="emp-first-name">Prenom *</label>
              <input
                id="emp-first-name"
                name="first_name"
                type="text"
                className="azals-input"
                required
                autoComplete="off"
              />
            </div>
            <div className="azals-field">
              <label htmlFor="emp-last-name">Nom *</label>
              <input
                id="emp-last-name"
                name="last_name"
                type="text"
                className="azals-input"
                required
                autoComplete="off"
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="emp-email">Email</label>
              <input
                id="emp-email"
                name="email"
                type="email"
                className="azals-input"
                autoComplete="off"
              />
            </div>
            <div className="azals-field">
              <label htmlFor="emp-phone">Telephone</label>
              <input
                id="emp-phone"
                name="phone"
                type="text"
                className="azals-input"
                autoComplete="off"
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Departement {departments.length > 0 && <span className="text-xs text-gray-500">({departments.length})</span>}</label>
              <div className="flex gap-2">
                <div className="flex-1">
                  <select name="department_id" className="azals-select w-full">
                    <option value="">Selectionner...</option>
                    {departments.map(d => (
                      <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
                    ))}
                  </select>
                </div>
                <Button type="button" variant="secondary" onClick={() => setShowDeptModal(true)}>+</Button>
              </div>
            </div>
            <div className="azals-field">
              <label>Poste {positions.length > 0 && <span className="text-xs text-gray-500">({positions.length})</span>}</label>
              <div className="flex gap-2">
                <div className="flex-1">
                  <select name="position_id" className="azals-select w-full">
                    <option value="">Selectionner...</option>
                    {positions.map(p => (
                      <option key={p.id} value={p.id}>{p.title} ({p.code})</option>
                    ))}
                  </select>
                </div>
                <Button type="button" variant="secondary" onClick={() => setShowPosModal(true)}>+</Button>
              </div>
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="emp-contract-type">Type de contrat</label>
              <select id="emp-contract-type" name="contract_type" className="azals-select w-full">
                {CONTRACT_TYPES.map(ct => (
                  <option key={ct.value} value={ct.value}>{ct.label}</option>
                ))}
              </select>
            </div>
            <div className="azals-field">
              <label htmlFor="emp-hire-date">Date d'embauche *</label>
              <input
                id="emp-hire-date"
                name="hire_date"
                type="date"
                className="azals-input"
                required
              />
            </div>
          </Grid>
          <div className="azals-field">
            <label htmlFor="emp-contract-end">Date de fin de contrat (CDD/Interim)</label>
            <input
              id="emp-contract-end"
              name="contract_end_date"
              type="date"
              className="azals-input"
            />
          </div>
          <div className="azals-field">
            <label htmlFor="emp-salary">Salaire mensuel brut (EUR)</label>
            <input
              id="emp-salary"
              name="gross_salary"
              type="text"
              inputMode="decimal"
              className="azals-input"
              placeholder="Ex: 3500.00"
              autoComplete="off"
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createEmployee.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>

      {/* Modal édition employé */}
      <Modal isOpen={showEditModal} onClose={() => { setShowEditModal(false); setEditingEmployee(null); }} title="Modifier l'employe" size="xl">
        {editingEmployee && (
          <form ref={editFormRef} onSubmit={handleEditSubmit} className="max-h-[70vh] overflow-y-auto pr-2">
            {/* Section: Informations personnelles */}
            <h4 className="text-sm font-semibold text-gray-600 mb-2 mt-0">Informations personnelles</h4>
            <Grid cols={3}>
              <div className="azals-field">
                <label htmlFor="edit-emp-first-name">Prenom *</label>
                <input id="edit-emp-first-name" name="first_name" type="text" className="azals-input" defaultValue={editingEmployee.first_name} required autoComplete="off" />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-last-name">Nom *</label>
                <input id="edit-emp-last-name" name="last_name" type="text" className="azals-input" defaultValue={editingEmployee.last_name} required autoComplete="off" />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-maiden">Nom de jeune fille</label>
                <input id="edit-emp-maiden" name="maiden_name" type="text" className="azals-input" defaultValue={editingEmployee.maiden_name || ''} autoComplete="off" />
              </div>
            </Grid>
            <Grid cols={4}>
              <div className="azals-field">
                <label htmlFor="edit-emp-gender">Genre</label>
                <select id="edit-emp-gender" name="gender" className="azals-select w-full" defaultValue={editingEmployee.gender || ''}>
                  <option value="">-</option>
                  <option value="M">Homme</option>
                  <option value="F">Femme</option>
                  <option value="OTHER">Autre</option>
                </select>
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-birth">Date de naissance</label>
                <input id="edit-emp-birth" name="birth_date" type="date" className="azals-input" defaultValue={editingEmployee.birth_date || ''} />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-birthplace">Lieu de naissance</label>
                <input id="edit-emp-birthplace" name="birth_place" type="text" className="azals-input" defaultValue={editingEmployee.birth_place || ''} autoComplete="off" />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-nationality">Nationalite</label>
                <input id="edit-emp-nationality" name="nationality" type="text" className="azals-input" defaultValue={editingEmployee.nationality || ''} placeholder="Ex: Francaise" autoComplete="off" />
              </div>
            </Grid>

            {/* Section: Contact */}
            <h4 className="text-sm font-semibold text-gray-600 mb-2 mt-4">Contact</h4>
            <Grid cols={2}>
              <div className="azals-field">
                <label htmlFor="edit-emp-email">Email professionnel</label>
                <input id="edit-emp-email" name="email" type="email" className="azals-input" defaultValue={editingEmployee.email || ''} autoComplete="off" />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-persemail">Email personnel</label>
                <input id="edit-emp-persemail" name="personal_email" type="email" className="azals-input" defaultValue={editingEmployee.personal_email || ''} autoComplete="off" />
              </div>
            </Grid>
            <Grid cols={2}>
              <div className="azals-field">
                <label htmlFor="edit-emp-phone">Telephone fixe</label>
                <input id="edit-emp-phone" name="phone" type="tel" className="azals-input" defaultValue={editingEmployee.phone || ''} autoComplete="off" />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-mobile">Mobile</label>
                <input id="edit-emp-mobile" name="mobile" type="tel" className="azals-input" defaultValue={editingEmployee.mobile || ''} autoComplete="off" />
              </div>
            </Grid>

            {/* Section: Adresse */}
            <h4 className="text-sm font-semibold text-gray-600 mb-2 mt-4">Adresse</h4>
            <div className="azals-field">
              <label htmlFor="edit-emp-addr1">Adresse ligne 1</label>
              <input id="edit-emp-addr1" name="address_line1" type="text" className="azals-input" defaultValue={editingEmployee.address_line1 || ''} placeholder="Numero et rue" autoComplete="off" />
            </div>
            <div className="azals-field">
              <label htmlFor="edit-emp-addr2">Adresse ligne 2</label>
              <input id="edit-emp-addr2" name="address_line2" type="text" className="azals-input" defaultValue={editingEmployee.address_line2 || ''} placeholder="Complement d'adresse" autoComplete="off" />
            </div>
            <Grid cols={3}>
              <div className="azals-field">
                <label htmlFor="edit-emp-postal">Code postal</label>
                <input id="edit-emp-postal" name="postal_code" type="text" className="azals-input" defaultValue={editingEmployee.postal_code || ''} autoComplete="off" />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-city">Ville</label>
                <input id="edit-emp-city" name="city" type="text" className="azals-input" defaultValue={editingEmployee.city || ''} autoComplete="off" />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-country">Pays</label>
                <input id="edit-emp-country" name="country" type="text" className="azals-input" defaultValue={editingEmployee.country || 'France'} autoComplete="off" />
              </div>
            </Grid>

            {/* Section: Organisation */}
            <h4 className="text-sm font-semibold text-gray-600 mb-2 mt-4">Organisation</h4>
            <Grid cols={2}>
              <div className="azals-field">
                <label htmlFor="edit-emp-dept">Departement</label>
                <select id="edit-emp-dept" name="department_id" className="azals-select w-full" defaultValue={editingEmployee.department_id || ''}>
                  <option value="">Aucun</option>
                  {departments.map((d: Department) => (<option key={d.id} value={d.id}>{d.name}</option>))}
                </select>
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-pos">Poste</label>
                <select id="edit-emp-pos" name="position_id" className="azals-select w-full" defaultValue={editingEmployee.position_id || ''}>
                  <option value="">Aucun</option>
                  {positions.map((p: Position) => (<option key={p.id} value={p.id}>{p.title}</option>))}
                </select>
              </div>
            </Grid>
            <Grid cols={2}>
              <div className="azals-field">
                <label htmlFor="edit-emp-manager">Manager</label>
                <select id="edit-emp-manager" name="manager_id" className="azals-select w-full" defaultValue={editingEmployee.manager_id || ''}>
                  <option value="">Aucun</option>
                  {employees.filter((e: Employee) => e.id !== editingEmployee.id).map((e: Employee) => (
                    <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>
                  ))}
                </select>
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-location">Lieu de travail</label>
                <input id="edit-emp-location" name="work_location" type="text" className="azals-input" defaultValue={editingEmployee.work_location || ''} placeholder="Ex: Paris, Teletravail" autoComplete="off" />
              </div>
            </Grid>

            {/* Section: Contrat */}
            <h4 className="text-sm font-semibold text-gray-600 mb-2 mt-4">Contrat</h4>
            <Grid cols={2}>
              <div className="azals-field">
                <label htmlFor="edit-emp-contract">Type de contrat</label>
                <select id="edit-emp-contract" name="contract_type" className="azals-select w-full" defaultValue={editingEmployee.contract_type || 'CDI'}>
                  {CONTRACT_TYPES.map(ct => (<option key={ct.value} value={ct.value}>{ct.label}</option>))}
                </select>
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-status">Statut</label>
                <select id="edit-emp-status" name="status" className="azals-select w-full" defaultValue={editingEmployee.status || 'ACTIVE'}>
                  {EMPLOYEE_STATUSES.map(s => (<option key={s.value} value={s.value}>{s.label}</option>))}
                </select>
              </div>
            </Grid>
            <Grid cols={2}>
              <div className="azals-field">
                <label htmlFor="edit-emp-hire-date">Date d'embauche *</label>
                <input id="edit-emp-hire-date" name="hire_date" type="date" className="azals-input" defaultValue={editingEmployee.hire_date} required />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-contract-end">Date de fin de contrat</label>
                <input id="edit-emp-contract-end" name="contract_end_date" type="date" className="azals-input" defaultValue={editingEmployee.contract_end_date || ''} />
              </div>
            </Grid>

            {/* Section: Rémunération */}
            <h4 className="text-sm font-semibold text-gray-600 mb-2 mt-4">Remuneration</h4>
            <Grid cols={2}>
              <div className="azals-field">
                <label htmlFor="edit-emp-salary">Salaire mensuel brut (EUR)</label>
                <input id="edit-emp-salary" name="gross_salary" type="text" inputMode="decimal" className="azals-input" defaultValue={editingEmployee.gross_salary || ''} placeholder="Ex: 3500.00" autoComplete="off" />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-hours">Heures hebdomadaires</label>
                <input id="edit-emp-hours" name="weekly_hours" type="text" inputMode="decimal" className="azals-input" defaultValue={editingEmployee.weekly_hours || '35'} placeholder="Ex: 35" autoComplete="off" />
              </div>
            </Grid>

            {/* Section: Informations bancaires */}
            <h4 className="text-sm font-semibold text-gray-600 mb-2 mt-4">Informations bancaires</h4>
            <Grid cols={3}>
              <div className="azals-field">
                <label htmlFor="edit-emp-bank">Banque</label>
                <input id="edit-emp-bank" name="bank_name" type="text" className="azals-input" defaultValue={editingEmployee.bank_name || ''} placeholder="Ex: BNP Paribas" autoComplete="off" />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-iban">IBAN</label>
                <input id="edit-emp-iban" name="iban" type="text" className="azals-input" defaultValue={editingEmployee.iban || editingEmployee.bank_iban || ''} placeholder="FR76..." autoComplete="off" />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-bic">BIC</label>
                <input id="edit-emp-bic" name="bic" type="text" className="azals-input" defaultValue={editingEmployee.bic || editingEmployee.bank_bic || ''} placeholder="BNPAFRPP" autoComplete="off" />
              </div>
            </Grid>

            {/* Section: Autres */}
            <h4 className="text-sm font-semibold text-gray-600 mb-2 mt-4">Autres informations</h4>
            <div className="azals-field">
              <label htmlFor="edit-emp-notes">Notes</label>
              <textarea id="edit-emp-notes" name="notes" className="azals-input" rows={3} defaultValue={editingEmployee.notes || ''} placeholder="Notes internes sur l'employe..." />
            </div>
            <div className="azals-field">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="is_active" className="azals-checkbox" defaultChecked={editingEmployee.is_active !== false} />
                <span>Employe actif dans le systeme</span>
              </label>
            </div>

            <div className="flex justify-end gap-2 mt-4 pt-4 border-t">
              <Button type="button" variant="secondary" onClick={() => { setShowEditModal(false); setEditingEmployee(null); }}>Annuler</Button>
              <Button type="submit" isLoading={updateEmployee.isPending}>Enregistrer</Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Modal création département */}
      <Modal isOpen={showDeptModal} onClose={() => { setShowDeptModal(false); setDeptError(''); }} title="Nouveau departement" size="sm">
        <div className="space-y-4">
          {deptError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {deptError}
            </div>
          )}
          <div className="azals-field">
            <label>Code</label>
            <input
              type="text"
              className="azals-input"
              value={newDeptData.code}
              onChange={(e) => setNewDeptData({ ...newDeptData, code: e.target.value.toUpperCase() })}
              placeholder="Ex: IT, RH, COMPTA"
            />
          </div>
          <div className="azals-field">
            <label>Nom</label>
            <input
              type="text"
              className="azals-input"
              value={newDeptData.name}
              onChange={(e) => setNewDeptData({ ...newDeptData, name: e.target.value })}
              placeholder="Ex: Informatique"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => { setShowDeptModal(false); setDeptError(''); }}>Annuler</Button>
            <Button onClick={handleCreateDepartment} isLoading={createDepartment.isPending}>Creer</Button>
          </div>
        </div>
      </Modal>

      {/* Modal création poste */}
      <Modal isOpen={showPosModal} onClose={() => { setShowPosModal(false); setPosError(''); }} title="Nouveau poste" size="sm">
        <div className="space-y-4">
          {posError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {posError}
            </div>
          )}
          <div className="azals-field">
            <label>Code</label>
            <input
              type="text"
              className="azals-input"
              value={newPosData.code}
              onChange={(e) => setNewPosData({ ...newPosData, code: e.target.value.toUpperCase() })}
              placeholder="Ex: DEV, MGR, ASST"
            />
          </div>
          <div className="azals-field">
            <label>Intitule</label>
            <input
              type="text"
              className="azals-input"
              value={newPosData.title}
              onChange={(e) => setNewPosData({ ...newPosData, title: e.target.value })}
              placeholder="Ex: Developpeur Senior"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => { setShowPosModal(false); setPosError(''); }}>Annuler</Button>
            <Button onClick={handleCreatePosition} isLoading={createPosition.isPending}>Creer</Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
};

const LeaveRequestsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('');
  const { data: requests = [], isLoading, error: leaveError, refetch: leaveRefetch } = useLeaveRequests({
    status: filterStatus || undefined,
    type: filterType || undefined
  });
  const { data: employees = [] } = useEmployees();
  const createRequest = useCreateLeaveRequest();
  const updateRequest = useUpdateLeaveRequest();
  const approveLeave = useApproveLeave();
  const rejectLeave = useRejectLeave();
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingLeave, setEditingLeave] = useState<LeaveRequest | null>(null);
  const leaveFormRef = useRef<HTMLFormElement>(null);
  const editFormRef = useRef<HTMLFormElement>(null);
  const [leaveFormKey, setLeaveFormKey] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leaveFormRef.current) return;

    const form = new FormData(leaveFormRef.current);
    const dataToSubmit = {
      employee_id: form.get('employee_id') as string,
      type: form.get('type') as string,
      start_date: form.get('start_date') as string,
      end_date: form.get('end_date') as string,
      half_day_start: form.get('half_day_start') === 'on',
      half_day_end: form.get('half_day_end') === 'on',
      replacement_id: form.get('replacement_id') as string || undefined,
      reason: form.get('reason') as string || undefined,
    };

    try {
      await createRequest.mutateAsync(dataToSubmit);
      alert('Demande de conge creee avec succes');
      setShowModal(false);
      setLeaveFormKey(k => k + 1);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Erreur lors de la creation';
      alert(`Erreur: ${errorMsg}`);
      console.error('Leave request error:', err);
    }
  };

  const handleEdit = (leave: LeaveRequest) => {
    setEditingLeave(leave);
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editFormRef.current || !editingLeave) return;

    const form = new FormData(editFormRef.current);
    const resubmit = editingLeave.status === 'REJECTED' && form.get('resubmit') === 'on';

    const dataToSubmit: LeaveRequestUpdateData = {
      type: form.get('type') as string,
      start_date: form.get('start_date') as string,
      end_date: form.get('end_date') as string,
      half_day_start: form.get('half_day_start') === 'on',
      half_day_end: form.get('half_day_end') === 'on',
      reason: form.get('reason') as string || undefined,
      resubmit: resubmit
    };

    try {
      await updateRequest.mutateAsync({ id: editingLeave.id, data: dataToSubmit });
      alert(resubmit ? 'Demande modifiee et resoumise avec succes' : 'Demande modifiee avec succes');
      setShowEditModal(false);
      setEditingLeave(null);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Erreur lors de la modification';
      alert(`Erreur: ${errorMsg}`);
      console.error('Leave request update error:', err);
    }
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
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => {
      const leave = row as LeaveRequest;
      const canEdit = leave.status === 'PENDING' || leave.status === 'REJECTED';
      const canApprove = leave.status === 'PENDING';

      return (
        <div className="flex gap-1">
          {canEdit && (
            <button
              className="azals-btn azals-btn--sm azals-btn--secondary"
              onClick={() => handleEdit(leave)}
              title="Modifier"
            >
              <Edit size={14} />
            </button>
          )}
          {canApprove && (
            <>
              <Button size="sm" onClick={() => approveLeave.mutate(leave.id)}>Approuver</Button>
              <Button size="sm" variant="secondary" onClick={() => {
                const reason = prompt('Motif du refus:');
                if (reason) {
                  rejectLeave.mutate({ id: leave.id, reason });
                }
              }}>Refuser</Button>
            </>
          )}
        </div>
      );
    }}
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
      <DataTable columns={columns} data={requests} isLoading={isLoading} keyField="id" filterable error={leaveError instanceof Error ? leaveError : null} onRetry={() => leaveRefetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvelle demande de conge">
        <form key={leaveFormKey} ref={leaveFormRef} onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="leave-employee">Employe *</label>
              <select id="leave-employee" name="employee_id" className="azals-select w-full" required>
                <option value="">Selectionner...</option>
                {employees.map((e: Employee) => (
                  <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>
                ))}
              </select>
            </div>
            <div className="azals-field">
              <label htmlFor="leave-type">Type de conge *</label>
              <select id="leave-type" name="type" className="azals-select w-full" required>
                {LEAVE_TYPES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="leave-start">Date de debut *</label>
              <input id="leave-start" name="start_date" type="date" className="azals-input" required />
              <label className="flex items-center gap-2 mt-1 text-sm cursor-pointer">
                <input type="checkbox" name="half_day_start" className="azals-checkbox" />
                <span>Demi-journee (apres-midi)</span>
              </label>
            </div>
            <div className="azals-field">
              <label htmlFor="leave-end">Date de fin *</label>
              <input id="leave-end" name="end_date" type="date" className="azals-input" required />
              <label className="flex items-center gap-2 mt-1 text-sm cursor-pointer">
                <input type="checkbox" name="half_day_end" className="azals-checkbox" />
                <span>Demi-journee (matin)</span>
              </label>
            </div>
          </Grid>
          <div className="azals-field">
            <label htmlFor="leave-replacement">Remplacant (optionnel)</label>
            <select id="leave-replacement" name="replacement_id" className="azals-select w-full">
              <option value="">Aucun</option>
              {employees.map((e: Employee) => (
                <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>
              ))}
            </select>
          </div>
          <div className="azals-field">
            <label htmlFor="leave-reason">Motif (optionnel)</label>
            <textarea
              id="leave-reason"
              name="reason"
              className="azals-input"
              placeholder="Ex: Vacances famille, rendez-vous medical..."
              rows={2}
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createRequest.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>

      {/* Modal d'edition */}
      <Modal
        isOpen={showEditModal}
        onClose={() => { setShowEditModal(false); setEditingLeave(null); }}
        title={editingLeave?.status === 'REJECTED' ? "Modifier et resoumettre la demande" : "Modifier la demande de conge"}
      >
        {editingLeave && (
          <form ref={editFormRef} onSubmit={handleEditSubmit}>
            <div className="azals-field">
              <label>Employe</label>
              <p className="text-gray-600">{editingLeave.employee_name || 'N/A'}</p>
            </div>
            <div className="azals-field">
              <label htmlFor="edit-leave-type">Type de conge *</label>
              <select
                id="edit-leave-type"
                name="type"
                className="azals-select w-full"
                defaultValue={editingLeave.type}
                required
              >
                {LEAVE_TYPES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <Grid cols={2}>
              <div className="azals-field">
                <label htmlFor="edit-leave-start">Date de debut *</label>
                <input id="edit-leave-start" name="start_date" type="date" className="azals-input" defaultValue={editingLeave.start_date} required />
                <label className="flex items-center gap-2 mt-1 text-sm cursor-pointer">
                  <input type="checkbox" name="half_day_start" className="azals-checkbox" defaultChecked={editingLeave.half_day_start} />
                  <span>Demi-journee (apres-midi)</span>
                </label>
              </div>
              <div className="azals-field">
                <label htmlFor="edit-leave-end">Date de fin *</label>
                <input id="edit-leave-end" name="end_date" type="date" className="azals-input" defaultValue={editingLeave.end_date} required />
                <label className="flex items-center gap-2 mt-1 text-sm cursor-pointer">
                  <input type="checkbox" name="half_day_end" className="azals-checkbox" defaultChecked={editingLeave.half_day_end} />
                  <span>Demi-journee (matin)</span>
                </label>
              </div>
            </Grid>
            <div className="azals-field">
              <label htmlFor="edit-leave-reason">Motif (optionnel)</label>
              <textarea
                id="edit-leave-reason"
                name="reason"
                className="azals-input"
                defaultValue={editingLeave.reason || ''}
                placeholder="Ex: Vacances famille"
                rows={2}
              />
            </div>
            {editingLeave.status === 'REJECTED' && (
              <div className="azals-field">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    name="resubmit"
                    className="azals-checkbox"
                    defaultChecked={true}
                  />
                  <span>Resoumettre la demande (remettre en attente)</span>
                </label>
                {editingLeave.rejection_reason && (
                  <p className="text-sm text-red-600 mt-1">
                    Motif du refus precedent: {editingLeave.rejection_reason}
                  </p>
                )}
              </div>
            )}
            <div className="flex justify-end gap-2 mt-4">
              <Button type="button" variant="secondary" onClick={() => { setShowEditModal(false); setEditingLeave(null); }}>
                Annuler
              </Button>
              <Button type="submit" isLoading={updateRequest.isPending}>
                {editingLeave.status === 'REJECTED' ? 'Modifier et resoumettre' : 'Enregistrer'}
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </Card>
  );
};

// Hook pour créer un département
const useCreateDepartment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Department>) => {
      return api.post<Department>('/hr/departments', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'departments'] })
  });
};

// Hook pour créer un poste
const useCreatePosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Position>) => {
      return api.post<Position>('/hr/positions', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'positions'] })
  });
};

// Hook pour modifier un département
const useUpdateDepartment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Department> }) => {
      const response: any = await api.put(`/hr/departments/${id}`, data);
      return response?.data || response;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'departments'] })
  });
};

// Hook pour modifier un poste
const useUpdatePosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Position> }) => {
      const response: any = await api.put(`/hr/positions/${id}`, data);
      return response?.data || response;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'positions'] })
  });
};

// Hook pour modifier un employé
const useUpdateEmployee = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Employee> }) => {
      const response: any = await api.put(`/hr/employees/${id}`, data);
      return response?.data || response;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

// Hook pour supprimer un département
const useDeleteDepartment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/hr/departments/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'departments'] })
  });
};

// Hook pour supprimer un poste
const useDeletePosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/hr/positions/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'positions'] })
  });
};

// Hook pour supprimer un employé
const useDeleteEmployee = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/hr/employees/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

// Formulaire de création de département (composant isolé pour éviter les re-renders)
interface DepartmentFormProps {
  onSubmit: (data: Partial<Department>) => Promise<void>;
  onCancel: () => void;
  isLoading: boolean;
  employees: Employee[];
  departments: Department[];
  initialData?: Department;
}

const DepartmentForm: React.FC<DepartmentFormProps> = ({ onSubmit, onCancel, isLoading, employees, departments, initialData }) => {
  const [code, setCode] = useState(initialData?.code || '');
  const [name, setName] = useState(initialData?.name || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [parentId, setParentId] = useState(initialData?.parent_id || '');
  const [managerId, setManagerId] = useState(initialData?.manager_id || '');
  const [costCenter, setCostCenter] = useState(initialData?.cost_center || '');
  const [isActive, setIsActive] = useState(initialData?.is_active ?? true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      code,
      name,
      description: description || undefined,
      parent_id: parentId || undefined,
      manager_id: managerId || undefined,
      cost_center: costCenter || undefined,
      is_active: isActive,
    });
  };

  // Filtrer les départements pour éviter les références circulaires
  const availableParents = departments.filter(d => !initialData || d.id !== initialData.id);

  return (
    <form onSubmit={handleSubmit}>
      <Grid cols={2}>
        <div className="azals-field">
          <label>Code *</label>
          <input
            type="text"
            className="azals-input"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="Ex: IT, RH, COMPTA"
            required
          />
        </div>
        <div className="azals-field">
          <label>Nom *</label>
          <input
            type="text"
            className="azals-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ex: Informatique"
            required
          />
        </div>
      </Grid>
      <div className="azals-field">
        <label>Description</label>
        <textarea
          className="azals-input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description du departement"
          rows={2}
        />
      </div>
      <div className="azals-field">
        <label>Departement parent (hierarchie)</label>
        <Select
          value={parentId}
          onChange={(v) => setParentId(v)}
          options={[{ value: '', label: 'Aucun (departement racine)' }, ...availableParents.map(d => ({ value: d.id, label: `${d.code} - ${d.name}` }))]}
        />
      </div>
      <Grid cols={2}>
        <div className="azals-field">
          <label>Responsable</label>
          <Select
            value={managerId}
            onChange={(v) => setManagerId(v)}
            options={[{ value: '', label: 'Aucun (a definir plus tard)' }, ...employees.map(e => ({ value: e.id, label: `${e.first_name} ${e.last_name}` }))]}
          />
        </div>
        <div className="azals-field">
          <label>Centre de cout</label>
          <input
            type="text"
            className="azals-input"
            value={costCenter}
            onChange={(e) => setCostCenter(e.target.value)}
            placeholder="Ex: CC-001"
          />
        </div>
      </Grid>
      {initialData && (
        <div className="azals-field">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="azals-checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            <span>Departement actif</span>
          </label>
        </div>
      )}
      <div className="flex justify-end gap-2 mt-4">
        <Button variant="secondary" type="button" onClick={onCancel}>Annuler</Button>
        <Button type="submit" isLoading={isLoading}>{initialData ? 'Enregistrer' : 'Creer'}</Button>
      </div>
    </form>
  );
};

const DepartmentsView: React.FC = () => {
  const { data: departments = [], isLoading, error: deptError, refetch: deptRefetch } = useDepartments();
  const { data: employees = [] } = useEmployees();
  const createDepartment = useCreateDepartment();
  const updateDepartment = useUpdateDepartment();
  const deleteDepartment = useDeleteDepartment();
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null);
  const [deleteError, setDeleteError] = useState<string>('');

  const handleSubmit = async (data: Partial<Department>) => {
    await createDepartment.mutateAsync(data);
    setShowModal(false);
  };

  const handleEdit = (dept: Department) => {
    setEditingDepartment(dept);
    setShowEditModal(true);
  };

  const handleEditSubmit = async (data: Partial<Department>) => {
    if (!editingDepartment) return;
    await updateDepartment.mutateAsync({ id: editingDepartment.id, data });
    setShowEditModal(false);
    setEditingDepartment(null);
  };

  const handleDelete = async (dept: Department) => {
    if (!window.confirm(`Supprimer le département "${dept.name}" ?`)) return;
    setDeleteError('');
    try {
      await deleteDepartment.mutateAsync(dept.id);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Erreur lors de la suppression';
      setDeleteError(msg);
    }
  };

  const columns: TableColumn<Department>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'description', header: 'Description', accessor: 'description', render: (v) => (v as string) || '-' },
    { id: 'manager_name', header: 'Responsable', accessor: 'manager_name', render: (v) => (v as string) || '-' },
    { id: 'cost_center', header: 'Centre de coût', accessor: 'cost_center', render: (v) => (v as string) || '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )},
    { id: 'actions', header: '', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        <button
          className="azals-btn azals-btn--sm azals-btn--secondary"
          onClick={() => handleEdit(row as Department)}
          title="Modifier"
        >
          <Edit size={14} />
        </button>
        <Button size="sm" variant="ghost" onClick={() => handleDelete(row as Department)}>
          <Trash2 size={14} className="text-red-500" />
        </Button>
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Departements</h3>
        <Button onClick={() => setShowModal(true)}>Nouveau departement</Button>
      </div>
      {deleteError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {deleteError}
        </div>
      )}
      <DataTable columns={columns} data={departments} isLoading={isLoading} keyField="id" filterable error={deptError instanceof Error ? deptError : null} onRetry={() => deptRefetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouveau departement" size="md">
        <DepartmentForm
          onSubmit={handleSubmit}
          onCancel={() => setShowModal(false)}
          isLoading={createDepartment.isPending}
          employees={employees}
          departments={departments}
        />
      </Modal>

      <Modal isOpen={showEditModal} onClose={() => { setShowEditModal(false); setEditingDepartment(null); }} title="Modifier le departement" size="md">
        {editingDepartment && (
          <DepartmentForm
            onSubmit={handleEditSubmit}
            onCancel={() => { setShowEditModal(false); setEditingDepartment(null); }}
            isLoading={updateDepartment.isPending}
            employees={employees}
            departments={departments}
            initialData={editingDepartment}
          />
        )}
      </Modal>
    </Card>
  );
};

// Formulaire de création de poste (composant isolé)
interface PositionFormProps {
  onSubmit: (data: Partial<Position>) => Promise<void>;
  onCancel: () => void;
  isLoading: boolean;
  departments: Department[];
  initialData?: Position;
}

const POSITION_CATEGORIES = [
  { value: 'CADRE', label: 'Cadre' },
  { value: 'NON_CADRE', label: 'Non-cadre' },
  { value: 'AGENT_MAITRISE', label: 'Agent de maîtrise' },
  { value: 'TECHNICIEN', label: 'Technicien' },
  { value: 'OUVRIER', label: 'Ouvrier' },
  { value: 'EMPLOYE', label: 'Employé' },
];

const PositionForm: React.FC<PositionFormProps> = ({ onSubmit, onCancel, isLoading, departments, initialData }) => {
  const [code, setCode] = useState(initialData?.code || '');
  const [title, setTitle] = useState(initialData?.title || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [departmentId, setDepartmentId] = useState(initialData?.department_id || '');
  const [category, setCategory] = useState(initialData?.category || '');
  const [level, setLevel] = useState(String(initialData?.level || 1));
  const [minSalary, setMinSalary] = useState(initialData?.min_salary ? String(initialData.min_salary) : '');
  const [maxSalary, setMaxSalary] = useState(initialData?.max_salary ? String(initialData.max_salary) : '');
  const [requirements, setRequirements] = useState(initialData?.requirements?.join('\n') || '');
  const [isActive, setIsActive] = useState(initialData?.is_active ?? true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const reqList = requirements.split('\n').map(r => r.trim()).filter(r => r.length > 0);
    onSubmit({
      code,
      title,
      description: description || undefined,
      department_id: departmentId || undefined,
      category: category || undefined,
      level: parseInt(level) || 1,
      min_salary: minSalary ? parseFloat(minSalary) : undefined,
      max_salary: maxSalary ? parseFloat(maxSalary) : undefined,
      requirements: reqList.length > 0 ? reqList : undefined,
      is_active: isActive,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <Grid cols={2}>
        <div className="azals-field">
          <label>Code *</label>
          <input
            type="text"
            className="azals-input"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="Ex: DEV, TECH, COMPTA"
            required
          />
        </div>
        <div className="azals-field">
          <label>Intitule du poste *</label>
          <input
            type="text"
            className="azals-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ex: Developpeur Senior"
            required
          />
        </div>
      </Grid>
      <div className="azals-field">
        <label>Description</label>
        <textarea
          className="azals-input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description du poste, missions principales..."
          rows={2}
        />
      </div>
      <Grid cols={3}>
        <div className="azals-field">
          <label>Departement</label>
          <Select
            value={departmentId}
            onChange={(v) => setDepartmentId(v)}
            options={[{ value: '', label: 'Aucun' }, ...departments.map(d => ({ value: d.id, label: d.name }))]}
          />
        </div>
        <div className="azals-field">
          <label>Categorie</label>
          <Select
            value={category}
            onChange={(v) => setCategory(v)}
            options={[{ value: '', label: 'Selectionner...' }, ...POSITION_CATEGORIES]}
          />
        </div>
        <div className="azals-field">
          <label>Niveau hierarchique</label>
          <input
            type="number"
            className="azals-input"
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            min={1}
            max={10}
          />
        </div>
      </Grid>
      <Grid cols={2}>
        <div className="azals-field">
          <label>Salaire minimum</label>
          <input
            type="number"
            className="azals-input"
            value={minSalary}
            onChange={(e) => setMinSalary(e.target.value)}
            placeholder="Ex: 2500"
          />
        </div>
        <div className="azals-field">
          <label>Salaire maximum</label>
          <input
            type="number"
            className="azals-input"
            value={maxSalary}
            onChange={(e) => setMaxSalary(e.target.value)}
            placeholder="Ex: 4500"
          />
        </div>
      </Grid>
      <div className="azals-field">
        <label>Competences requises (une par ligne)</label>
        <textarea
          className="azals-input"
          value={requirements}
          onChange={(e) => setRequirements(e.target.value)}
          placeholder="Ex:&#10;Diplome Bac+5&#10;3 ans d'experience&#10;Anglais courant"
          rows={3}
        />
      </div>
      {initialData && (
        <div className="azals-field">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="azals-checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            <span>Poste actif</span>
          </label>
        </div>
      )}
      <div className="flex justify-end gap-2 mt-4">
        <Button variant="secondary" type="button" onClick={onCancel}>Annuler</Button>
        <Button type="submit" isLoading={isLoading}>{initialData ? 'Enregistrer' : 'Creer'}</Button>
      </div>
    </form>
  );
};

const PositionsView: React.FC = () => {
  const { data: positions = [], isLoading, error: posError, refetch: posRefetch } = usePositions();
  const { data: departments = [] } = useDepartments();
  const createPosition = useCreatePosition();
  const updatePosition = useUpdatePosition();
  const deletePosition = useDeletePosition();
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingPosition, setEditingPosition] = useState<Position | null>(null);
  const [deleteError, setDeleteError] = useState<string>('');

  const handleSubmit = async (data: Partial<Position>) => {
    await createPosition.mutateAsync(data);
    setShowModal(false);
  };

  const handleEdit = (pos: Position) => {
    setEditingPosition(pos);
    setShowEditModal(true);
  };

  const handleEditSubmit = async (data: Partial<Position>) => {
    if (!editingPosition) return;
    await updatePosition.mutateAsync({ id: editingPosition.id, data });
    setShowEditModal(false);
    setEditingPosition(null);
  };

  const handleDelete = async (pos: Position) => {
    if (!window.confirm(`Supprimer le poste "${pos.title}" ?`)) return;
    setDeleteError('');
    try {
      await deletePosition.mutateAsync(pos.id);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Erreur lors de la suppression';
      setDeleteError(msg);
    }
  };

  const columns: TableColumn<Position>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'title', header: 'Intitule', accessor: 'title' },
    { id: 'department_name', header: 'Departement', accessor: 'department_name', render: (v) => (v as string) || '-' },
    { id: 'category', header: 'Categorie', accessor: 'category', render: (v) => {
      const cat = POSITION_CATEGORIES.find(c => c.value === v);
      return cat?.label || (v as string) || '-';
    }},
    { id: 'level', header: 'Niveau', accessor: 'level' },
    { id: 'min_salary', header: 'Salaire min', accessor: 'min_salary', render: (v) => v ? formatCurrency(v as number) : '-' },
    { id: 'max_salary', header: 'Salaire max', accessor: 'max_salary', render: (v) => v ? formatCurrency(v as number) : '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )},
    { id: 'actions', header: '', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        <button
          className="azals-btn azals-btn--sm azals-btn--secondary"
          onClick={() => handleEdit(row as Position)}
          title="Modifier"
        >
          <Edit size={14} />
        </button>
        <Button size="sm" variant="ghost" onClick={() => handleDelete(row as Position)}>
          <Trash2 size={14} className="text-red-500" />
        </Button>
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Postes / Fonctions</h3>
        <Button onClick={() => setShowModal(true)}>Nouveau poste</Button>
      </div>
      {deleteError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {deleteError}
        </div>
      )}
      <DataTable columns={columns} data={positions} isLoading={isLoading} keyField="id" filterable error={posError instanceof Error ? posError : null} onRetry={() => posRefetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouveau poste" size="lg">
        <PositionForm
          onSubmit={handleSubmit}
          onCancel={() => setShowModal(false)}
          isLoading={createPosition.isPending}
          departments={departments}
        />
      </Modal>

      <Modal isOpen={showEditModal} onClose={() => { setShowEditModal(false); setEditingPosition(null); }} title="Modifier le poste" size="lg">
        {editingPosition && (
          <PositionForm
            onSubmit={handleEditSubmit}
            onCancel={() => { setShowEditModal(false); setEditingPosition(null); }}
            isLoading={updatePosition.isPending}
            departments={departments}
            initialData={editingPosition}
          />
        )}
      </Modal>
    </Card>
  );
};

interface TimeEntryFormProps {
  onSubmit: (data: { employee_id: string; data: TimeEntryCreateData }) => Promise<void>;
  onCancel: () => void;
  isLoading: boolean;
  employees: Employee[];
}

const TimeEntryForm: React.FC<TimeEntryFormProps> = ({ onSubmit, onCancel, isLoading, employees }) => {
  const formRef = useRef<HTMLFormElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = formRef.current;
    if (!form) return;

    const formData = new FormData(form);
    const employee_id = formData.get('employee_id') as string;
    const data: TimeEntryCreateData = {
      date: formData.get('date') as string,
      worked_hours: parseFloat(formData.get('worked_hours') as string) || 0,
      overtime_hours: parseFloat(formData.get('overtime_hours') as string) || 0,
      break_duration: parseInt(formData.get('break_duration') as string) || 0,
      project_id: (formData.get('project_id') as string) || undefined,
      task_description: (formData.get('task_description') as string) || undefined
    };

    await onSubmit({ employee_id, data });
  };

  return (
    <form ref={formRef} onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Employe *</label>
        <select name="employee_id" required className="w-full border rounded px-3 py-2">
          <option value="">Selectionnez un employe</option>
          {employees.map(emp => (
            <option key={emp.id} value={emp.id}>{getFullName(emp)}</option>
          ))}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Date *</label>
          <input type="date" name="date" required defaultValue={new Date().toISOString().split('T')[0]} className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Heures travaillees *</label>
          <input type="number" name="worked_hours" required step={0.5} min={0} max={24} defaultValue={8} className="w-full border rounded px-3 py-2" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Heures supplementaires</label>
          <input type="number" name="overtime_hours" step={0.5} min={0} max={24} defaultValue={0} className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Pause (minutes)</label>
          <input type="number" name="break_duration" min={0} max={480} defaultValue={60} className="w-full border rounded px-3 py-2" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Description tache</label>
        <textarea name="task_description" className="w-full border rounded px-3 py-2" rows={3} placeholder="Description du travail effectue..." />
      </div>
      <div className="flex justify-end gap-2 pt-4">
        <Button variant="secondary" onClick={onCancel} disabled={isLoading}>Annuler</Button>
        <Button type="submit" disabled={isLoading}>{isLoading ? 'Enregistrement...' : 'Creer'}</Button>
      </div>
    </form>
  );
};

const TimesheetsView: React.FC = () => {
  const [filterEmployee, setFilterEmployee] = useState<string>('');
  const [filterFromDate, setFilterFromDate] = useState<string>('');
  const [filterToDate, setFilterToDate] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: timeEntries = [], isLoading, error: tsError, refetch: tsRefetch } = useTimeEntries({
    employee_id: filterEmployee || undefined,
    from_date: filterFromDate || undefined,
    to_date: filterToDate || undefined
  });
  const { data: employees = [] } = useEmployees({});
  const createTimeEntry = useCreateTimeEntry();

  const columns: TableColumn<TimeEntry>[] = [
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'employee_name', header: 'Employe', accessor: 'employee_name', render: (v, row) => {
      if (v) return v as string;
      const emp = employees.find(e => e.id === row.employee_id);
      return emp ? getFullName(emp) : row.employee_id;
    }},
    { id: 'worked_hours', header: 'Heures', accessor: 'worked_hours', render: (v) => `${v}h` },
    { id: 'overtime_hours', header: 'Heures sup.', accessor: 'overtime_hours', render: (v) => v ? `${v}h` : '-' },
    { id: 'break_duration', header: 'Pause', accessor: 'break_duration', render: (v) => v ? `${v} min` : '-' },
    { id: 'task_description', header: 'Description', accessor: 'task_description', render: (v) => (v as string) || '-' },
    { id: 'is_approved', header: 'Statut', accessor: 'is_approved', render: (v) => (
      <Badge color={v ? 'green' : 'orange'}>{v ? 'Approuve' : 'En attente'}</Badge>
    )}
  ];

  const handleCreate = async (payload: { employee_id: string; data: TimeEntryCreateData }) => {
    await createTimeEntry.mutateAsync(payload);
    setShowCreateModal(false);
  };

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Saisies de temps</h3>
        <Button onClick={() => setShowCreateModal(true)}><Plus className="h-4 w-4 mr-1" /> Nouvelle saisie</Button>
      </div>
      <div className="flex gap-4 mb-4">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">Employe</label>
          <select
            value={filterEmployee}
            onChange={(e) => setFilterEmployee(e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="">Tous les employes</option>
            {employees.map(emp => (
              <option key={emp.id} value={emp.id}>{getFullName(emp)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Du</label>
          <input
            type="date"
            value={filterFromDate}
            onChange={(e) => setFilterFromDate(e.target.value)}
            className="border rounded px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Au</label>
          <input
            type="date"
            value={filterToDate}
            onChange={(e) => setFilterToDate(e.target.value)}
            className="border rounded px-3 py-2"
          />
        </div>
      </div>
      <DataTable columns={columns} data={timeEntries} isLoading={isLoading} keyField="id" filterable error={tsError instanceof Error ? tsError : null} onRetry={() => tsRefetch()} />
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Nouvelle saisie de temps">
        <TimeEntryForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreateModal(false)}
          isLoading={createTimeEntry.isPending}
          employees={employees}
        />
      </Modal>
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'employees' | 'departments' | 'positions' | 'leave' | 'timesheets' | 'employee-detail';

const HRModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string | null>(null);
  const { data: dashboard } = useHRDashboard();
  const { data: departments = [] } = useDepartments();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'employees', label: 'Employes' },
    { id: 'departments', label: 'Departements' },
    { id: 'positions', label: 'Postes' },
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
      case 'positions':
        return <PositionsView />;
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
                value={String(dashboard?.on_leave_employees || dashboard?.employees_on_leave_today || 0)}
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
                value={String(dashboard?.contracts_ending_soon || 0)}
                icon={<AlertTriangle />}
                variant="danger"
                onClick={() => setCurrentView('employees')}
              />
            </Grid>
            <Grid cols={4}>
              <StatCard
                title="Embauches (mois)"
                value={String(dashboard?.new_hires_this_month || 0)}
                icon={<Plus />}
                variant="success"
              />
              <StatCard
                title="Departs (mois)"
                value={String(dashboard?.departures_this_month || 0)}
                icon={<Minus />}
                variant="danger"
              />
              <StatCard
                title="Departements"
                value={String(departments.length)}
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
