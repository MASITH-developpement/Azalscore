/**
 * AZALSCORE Module - HR Vault - Access Logs View
 * Historique des acces aux documents
 */

import React, { useState } from 'react';
import { Eye, CheckCircle, XCircle } from 'lucide-react';
import { Input } from '@ui/forms';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDateTime } from '@/utils/formatters';
import { useAccessLogs } from '../hooks';
import type { VaultAccessLog } from '../types';

export const AccessLogsView: React.FC = () => {
  const [documentId, setDocumentId] = useState<string>('');
  const { data, isLoading } = useAccessLogs(documentId || undefined);

  const columns: TableColumn<VaultAccessLog>[] = [
    {
      id: 'date',
      header: 'Date',
      accessor: 'access_date',
      render: (date) => formatDateTime(date as string),
    },
    {
      id: 'document',
      header: 'Document',
      accessor: 'document_title',
      render: (title) => String(title || '-'),
    },
    {
      id: 'user',
      header: 'Utilisateur',
      accessor: 'accessed_by_name',
      render: (name) => String(name || '-'),
    },
    {
      id: 'role',
      header: 'Role',
      accessor: 'access_role',
    },
    {
      id: 'action',
      header: 'Action',
      accessor: 'access_type',
    },
    {
      id: 'ip',
      header: 'IP',
      accessor: 'ip_address',
      render: (ip) => String(ip || '-'),
    },
    {
      id: 'success',
      header: 'Resultat',
      accessor: 'success',
      render: (success) =>
        success ? (
          <CheckCircle size={16} className="text-green-500" />
        ) : (
          <XCircle size={16} className="text-red-500" />
        ),
    },
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Eye size={20} />
          Historique des acces
        </h3>
        <div className="w-64">
          <Input
            placeholder="Filtrer par ID document"
            value={documentId}
            onChange={setDocumentId}
          />
        </div>
      </div>
      <DataTable
        columns={columns}
        data={data?.items || []}
        isLoading={isLoading}
        keyField="id"
        filterable
      />
    </Card>
  );
};

export default AccessLogsView;
