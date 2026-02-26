/**
 * AZALSCORE Module - HR - EmployeesView
 * Vue liste des employes avec formulaires de creation/edition
 */

import React, { useState, useRef } from 'react';
import { Eye, Edit, Trash2 } from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { Select } from '@ui/forms';
import { Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn, ApiMutationError } from '@/types';
import { formatDate } from '@/utils/formatters';
import type { Department, Position, Employee } from '../types';
import { getFullName } from '../types';
import { CONTRACT_TYPES, EMPLOYEE_STATUSES, getStatusInfo } from '../constants';
import {
  useEmployees, useDepartments, usePositions,
  useCreateEmployee, useUpdateEmployee, useDeleteEmployee,
  useCreateDepartment, useCreatePosition
} from '../hooks';

// Badge local
const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

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
  const [formKey, setFormKey] = useState(0);
  const [newDeptData, setNewDeptData] = useState<{ code: string; name: string }>({ code: '', name: '' });
  const [newPosData, setNewPosData] = useState<{ code: string; title: string }>({ code: '', title: '' });
  const [deptError, setDeptError] = useState<string>('');
  const [posError, setPosError] = useState<string>('');
  const [deleteError, setDeleteError] = useState<string>('');

  const handleDeleteEmployee = async (emp: Employee) => {
    const fullName = `${emp.first_name} ${emp.last_name}`;
    if (!window.confirm(`Supprimer l'employe "${fullName}" ?`)) return;
    setDeleteError('');
    try {
      await deleteEmployee.mutateAsync(emp.id);
    } catch (err: unknown) {
      const error = err as ApiMutationError;
      const msg = error?.response?.data?.detail || 'Erreur lors de la suppression';
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
      first_name: form.get('first_name') as string,
      last_name: form.get('last_name') as string,
      maiden_name: form.get('maiden_name') as string || undefined,
      gender: form.get('gender') as string || undefined,
      birth_date: form.get('birth_date') as string || undefined,
      birth_place: form.get('birth_place') as string || undefined,
      nationality: form.get('nationality') as string || undefined,
      email: form.get('email') as string || undefined,
      personal_email: form.get('personal_email') as string || undefined,
      phone: form.get('phone') as string || undefined,
      mobile: form.get('mobile') as string || undefined,
      address_line1: form.get('address_line1') as string || undefined,
      address_line2: form.get('address_line2') as string || undefined,
      postal_code: form.get('postal_code') as string || undefined,
      city: form.get('city') as string || undefined,
      country: form.get('country') as string || undefined,
      department_id: form.get('department_id') as string || undefined,
      position_id: form.get('position_id') as string || undefined,
      manager_id: form.get('manager_id') as string || undefined,
      work_location: form.get('work_location') as string || undefined,
      contract_type: form.get('contract_type') as string || 'CDI',
      hire_date: form.get('hire_date') as string,
      contract_end_date: form.get('contract_end_date') as string || undefined,
      status: form.get('status') as string || 'ACTIVE',
      bank_name: form.get('bank_name') as string || undefined,
      iban: form.get('iban') as string || undefined,
      bic: form.get('bic') as string || undefined,
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
    } catch (err: unknown) {
      const error = err as ApiMutationError;
      const msg = error?.response?.data?.detail || 'Erreur lors de la modification';
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

    dataToSubmit.employee_number = `EMP-${Date.now().toString(36).toUpperCase()}`;

    await createEmployee.mutateAsync(dataToSubmit as Partial<Employee>);
    setShowModal(false);
    setFormKey(k => k + 1);
  };

  const handleCreateDepartment = async () => {
    if (!newDeptData.code || !newDeptData.name) {
      setDeptError('Code et nom requis');
      return;
    }
    setDeptError('');
    try {
      const created = await createDepartment.mutateAsync(newDeptData);
      setShowDeptModal(false);
      setNewDeptData({ code: '', name: '' });
      await refetchDepartments();
      if (created?.id && formRef.current) {
        const select = formRef.current.querySelector<HTMLSelectElement>('select[name="department_id"]');
        if (select) select.value = created.id;
      }
    } catch (err: unknown) {
      const error = err as ApiMutationError & { response?: { status?: number } };
      const status = error?.response?.status;
      if (status === 409) {
        setDeptError(`Le code "${newDeptData.code}" existe deja. Choisissez un autre code.`);
      } else {
        const msg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || 'Erreur lors de la creation';
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
      setShowPosModal(false);
      setNewPosData({ code: '', title: '' });
      await refetchPositions();
      if (created?.id && formRef.current) {
        const select = formRef.current.querySelector<HTMLSelectElement>('select[name="position_id"]');
        if (select) select.value = created.id;
      }
    } catch (err: unknown) {
      const error = err as ApiMutationError & { response?: { status?: number } };
      const status = error?.response?.status;
      if (status === 409) {
        setPosError(`Le code "${newPosData.code}" existe deja. Choisissez un autre code.`);
      } else {
        const msg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || 'Erreur lors de la creation';
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
            options={[{ value: '', label: 'Tous contrats' }, ...CONTRACT_TYPES.map(ct => ({ value: ct.value, label: ct.label }))]}
            className="w-32"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...EMPLOYEE_STATUSES.map(s => ({ value: s.value, label: s.label }))]}
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

      {/* Modal creation employe */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvel employe" size="lg">
        <form key={formKey} ref={formRef} onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="emp-first-name">Prenom *</label>
              <input id="emp-first-name" name="first_name" type="text" className="azals-input" required autoComplete="off" />
            </div>
            <div className="azals-field">
              <label htmlFor="emp-last-name">Nom *</label>
              <input id="emp-last-name" name="last_name" type="text" className="azals-input" required autoComplete="off" />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="emp-email">Email</label>
              <input id="emp-email" name="email" type="email" className="azals-input" autoComplete="off" />
            </div>
            <div className="azals-field">
              <label htmlFor="emp-phone">Telephone</label>
              <input id="emp-phone" name="phone" type="text" className="azals-input" autoComplete="off" />
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
              <label htmlFor="emp-hire-date">Date d&apos;embauche *</label>
              <input id="emp-hire-date" name="hire_date" type="date" className="azals-input" required />
            </div>
          </Grid>
          <div className="azals-field">
            <label htmlFor="emp-contract-end">Date de fin de contrat (CDD/Interim)</label>
            <input id="emp-contract-end" name="contract_end_date" type="date" className="azals-input" />
          </div>
          <div className="azals-field">
            <label htmlFor="emp-salary">Salaire mensuel brut (EUR)</label>
            <input id="emp-salary" name="gross_salary" type="text" inputMode="decimal" className="azals-input" placeholder="Ex: 3500.00" autoComplete="off" />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createEmployee.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>

      {/* Modal edition employe */}
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
                <label htmlFor="edit-emp-hire-date">Date d&apos;embauche *</label>
                <input id="edit-emp-hire-date" name="hire_date" type="date" className="azals-input" defaultValue={editingEmployee.hire_date} required />
              </div>
              <div className="azals-field">
                <label htmlFor="edit-emp-contract-end">Date de fin de contrat</label>
                <input id="edit-emp-contract-end" name="contract_end_date" type="date" className="azals-input" defaultValue={editingEmployee.contract_end_date || ''} />
              </div>
            </Grid>

            {/* Section: Remuneration */}
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

      {/* Modal creation departement */}
      <Modal isOpen={showDeptModal} onClose={() => { setShowDeptModal(false); setDeptError(''); }} title="Nouveau departement" size="sm">
        <div className="space-y-4">
          {deptError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {deptError}
            </div>
          )}
          <div className="azals-field">
            <label htmlFor="new-dept-code">Code</label>
            <input
              id="new-dept-code"
              type="text"
              className="azals-input"
              value={newDeptData.code}
              onChange={(e) => setNewDeptData({ ...newDeptData, code: e.target.value.toUpperCase() })}
              placeholder="Ex: IT, RH, COMPTA"
            />
          </div>
          <div className="azals-field">
            <label htmlFor="new-dept-name">Nom</label>
            <input
              id="new-dept-name"
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

      {/* Modal creation poste */}
      <Modal isOpen={showPosModal} onClose={() => { setShowPosModal(false); setPosError(''); }} title="Nouveau poste" size="sm">
        <div className="space-y-4">
          {posError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {posError}
            </div>
          )}
          <div className="azals-field">
            <label htmlFor="new-pos-code">Code</label>
            <input
              id="new-pos-code"
              type="text"
              className="azals-input"
              value={newPosData.code}
              onChange={(e) => setNewPosData({ ...newPosData, code: e.target.value.toUpperCase() })}
              placeholder="Ex: DEV, MGR, ASST"
            />
          </div>
          <div className="azals-field">
            <label htmlFor="new-pos-title">Intitule</label>
            <input
              id="new-pos-title"
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

export default EmployeesView;
