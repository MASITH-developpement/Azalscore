/**
 * AZALSCORE Module - HR - LeaveRequestsView
 * Vue des demandes de conges
 */

import React, { useState, useRef } from 'react';
import { Edit } from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { Select } from '@ui/forms';
import { Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import type { Employee, LeaveRequest } from '../types';
import { LEAVE_TYPES, LEAVE_STATUSES, getStatusInfo } from '../constants';
import {
  useEmployees, useLeaveRequests,
  useCreateLeaveRequest, useUpdateLeaveRequest,
  useApproveLeave, useRejectLeave,
  type LeaveRequestUpdateData
} from '../hooks';

// Badge local
const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

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
            options={[{ value: '', label: 'Tous types' }, ...LEAVE_TYPES.map(t => ({ value: t.value, label: t.label }))]}
            className="w-36"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...LEAVE_STATUSES.map(s => ({ value: s.value, label: s.label }))]}
            className="w-36"
          />
          <Button onClick={() => setShowModal(true)}>Nouvelle demande</Button>
        </div>
      </div>
      <DataTable columns={columns} data={requests} isLoading={isLoading} keyField="id" filterable error={leaveError instanceof Error ? leaveError : null} onRetry={() => leaveRefetch()} />

      {/* Modal creation */}
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

      {/* Modal edition */}
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

export default LeaveRequestsView;
