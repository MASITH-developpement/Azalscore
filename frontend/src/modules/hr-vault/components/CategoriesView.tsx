/**
 * AZALSCORE Module - HR Vault - Categories View
 * Gestion des categories de documents
 */

import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { FolderOpen, Trash2, RefreshCw } from 'lucide-react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { hrVaultApi } from '../api';
import { useCategories, hrVaultKeys } from '../hooks';
import type { VaultCategory } from '../types';

export const CategoriesView: React.FC = () => {
  const { data: categories = [], isLoading, refetch } = useCategories();
  const queryClient = useQueryClient();

  const deleteCategoryMutation = useMutation({
    mutationFn: async (categoryId: string) => {
      await hrVaultApi.deleteCategory(categoryId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: hrVaultKeys.categories() });
    },
  });

  const columns: TableColumn<VaultCategory>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      render: (v) => <code className="font-mono">{v as string}</code>,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
    },
    {
      id: 'description',
      header: 'Description',
      accessor: 'description',
      render: (v) => String(v || '-'),
    },
    {
      id: 'documents',
      header: 'Documents',
      accessor: 'documents_count',
    },
    {
      id: 'retention',
      header: 'Conservation',
      accessor: 'default_retention',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, cat) => (
        <Button
          size="sm"
          variant="danger"
          disabled={cat.documents_count > 0}
          onClick={() => deleteCategoryMutation.mutate(cat.id)}
        >
          <Trash2 size={14} />
        </Button>
      ),
    },
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <FolderOpen size={20} />
          Categories de documents
        </h3>
        <Button variant="secondary" onClick={() => { void refetch(); }}>
          <RefreshCw size={16} />
        </Button>
      </div>
      <DataTable
        columns={columns}
        data={categories}
        isLoading={isLoading}
        keyField="id"
      />
    </Card>
  );
};

export default CategoriesView;
