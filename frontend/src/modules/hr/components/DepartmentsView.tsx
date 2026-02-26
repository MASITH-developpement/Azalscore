/**
 * AZALSCORE Module - HR - DepartmentsView
 * Vue de gestion des departements
 */

import React, { useState } from 'react';
import { Edit, Trash2 } from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn, ApiMutationError } from '@/types';
import type { Department } from '../types';
import {
  useDepartments, useEmployees,
  useCreateDepartment, useUpdateDepartment, useDeleteDepartment
} from '../hooks';
import DepartmentForm from './DepartmentForm';

// Badge local
const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

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
    if (!window.confirm(`Supprimer le departement "${dept.name}" ?`)) return;
    setDeleteError('');
    try {
      await deleteDepartment.mutateAsync(dept.id);
    } catch (err: unknown) {
      const error = err as ApiMutationError;
      const msg = error?.response?.data?.detail || 'Erreur lors de la suppression';
      setDeleteError(msg);
    }
  };

  const columns: TableColumn<Department>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'description', header: 'Description', accessor: 'description', render: (v) => (v as string) || '-' },
    { id: 'manager_name', header: 'Responsable', accessor: 'manager_name', render: (v) => (v as string) || '-' },
    { id: 'cost_center', header: 'Centre de cout', accessor: 'cost_center', render: (v) => (v as string) || '-' },
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

export default DepartmentsView;
