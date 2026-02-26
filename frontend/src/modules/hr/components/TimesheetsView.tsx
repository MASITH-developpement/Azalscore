/**
 * AZALSCORE Module - HR - TimesheetsView
 * Vue des saisies de temps
 */

import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import type { TimeEntry } from '../types';
import { getFullName } from '../types';
import { useEmployees, useTimeEntries, useCreateTimeEntry, type TimeEntryCreateData } from '../hooks';
import TimeEntryForm from './TimeEntryForm';

// Badge local
const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

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
          <label htmlFor="ts-filter-employee" className="block text-sm font-medium mb-1">Employe</label>
          <select
            id="ts-filter-employee"
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
          <label htmlFor="ts-filter-from" className="block text-sm font-medium mb-1">Du</label>
          <input
            id="ts-filter-from"
            type="date"
            value={filterFromDate}
            onChange={(e) => setFilterFromDate(e.target.value)}
            className="border rounded px-3 py-2"
          />
        </div>
        <div>
          <label htmlFor="ts-filter-to" className="block text-sm font-medium mb-1">Au</label>
          <input
            id="ts-filter-to"
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

export default TimesheetsView;
