/**
 * AZALSCORE Module - HR - PositionsView
 * Vue de gestion des postes
 */

import React, { useState } from 'react';
import { Edit, Trash2 } from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn, ApiMutationError } from '@/types';
import { formatCurrency } from '@/utils/formatters';
import type { Position } from '../types';
import { POSITION_CATEGORIES } from '../constants';
import {
  useDepartments, usePositions,
  useCreatePosition, useUpdatePosition, useDeletePosition
} from '../hooks';
import PositionForm from './PositionForm';

// Badge local
const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

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
    } catch (err: unknown) {
      const error = err as ApiMutationError;
      const msg = error?.response?.data?.detail || 'Erreur lors de la suppression';
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

export default PositionsView;
