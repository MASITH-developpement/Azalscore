/**
 * AZALSCORE Module - APPROVAL
 * ============================
 * Interface de gestion des approbations
 */

import React, { useState } from 'react';
import {
  CheckSquare, Clock, GitBranch, History,
  Check, X, UserPlus, AlertTriangle,
  ChevronRight, MessageSquare, RefreshCw
} from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { KPICard } from '@ui/dashboards';
import { DataTable } from '@ui/tables';
import { Badge } from '@ui/simple';
import { Modal, TextArea } from '@ui/forms';
import { formatDate, formatCurrency } from '@/utils/formatters';
import type { TableColumn, DashboardKPI } from '@/types';

import {
  usePendingApprovals,
  useApprovalRequests,
  useApprovalStats,
  useWorkflows,
  useSubmitAction,
  usePendingCount,
} from './hooks';
import type {
  ApprovalRequest, ApprovalWorkflow, PendingApproval,
  RequestStatus, WorkflowStatus, ApprovalType,
} from './types';
import {
  APPROVAL_TYPE_CONFIG,
  REQUEST_STATUS_CONFIG,
  WORKFLOW_STATUS_CONFIG,
} from './types';

// ============================================================================
// BADGES
// ============================================================================

const TypeBadge: React.FC<{ type: ApprovalType }> = ({ type }) => {
  const config = APPROVAL_TYPE_CONFIG[type];
  return <Badge variant="default">{config?.label || type}</Badge>;
};

const StatusBadge: React.FC<{ status: RequestStatus }> = ({ status }) => {
  const config = REQUEST_STATUS_CONFIG[status];
  const variant = config?.color === 'green' ? 'success' :
    config?.color === 'red' ? 'destructive' :
    config?.color === 'orange' ? 'warning' : 'default';
  return <Badge variant={variant}>{config?.label || status}</Badge>;
};

const WorkflowStatusBadge: React.FC<{ status: WorkflowStatus }> = ({ status }) => {
  const config = WORKFLOW_STATUS_CONFIG[status];
  const variant = config?.color === 'green' ? 'success' : 'default';
  return <Badge variant={variant}>{config?.label || status}</Badge>;
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

type View = 'pending' | 'requests' | 'workflows';

const ApprovalModule: React.FC = () => {
  const [view, setView] = useState<View>('pending');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [selectedRequest, setSelectedRequest] = useState<ApprovalRequest | null>(null);
  const [actionModal, setActionModal] = useState<{ type: 'approve' | 'reject'; request: ApprovalRequest } | null>(null);
  const [comment, setComment] = useState('');

  const { data: stats } = useApprovalStats();
  const { data: pendingCount } = usePendingCount();
  const { data: pending, isLoading: pendingLoading, refetch: refetchPending } = usePendingApprovals();
  const { data: requests, isLoading: requestsLoading, refetch: refetchRequests } = useApprovalRequests({
    page,
    page_size: pageSize,
  });
  const { data: workflows, isLoading: workflowsLoading } = useWorkflows();
  const submitAction = useSubmitAction();

  const handleAction = async () => {
    if (!actionModal) return;
    await submitAction.mutateAsync({
      requestId: actionModal.request.id,
      data: {
        action_type: actionModal.type === 'approve' ? 'APPROVE' : 'REJECT',
        comment: comment || undefined,
      },
    });
    setActionModal(null);
    setComment('');
  };

  const kpis: DashboardKPI[] = [
    {
      id: 'pending',
      label: 'En attente',
      value: pendingCount?.count || stats?.pending_count || 0,
      icon: <Clock size={20} />,
      variant: 'warning',
    },
    {
      id: 'approved',
      label: 'Approuvees aujourd\'hui',
      value: stats?.approved_today || 0,
      icon: <Check size={20} />,
      variant: 'success',
    },
    {
      id: 'rejected',
      label: 'Rejetees aujourd\'hui',
      value: stats?.rejected_today || 0,
      icon: <X size={20} />,
      variant: 'danger',
    },
    {
      id: 'overdue',
      label: 'En retard',
      value: stats?.overdue_count || 0,
      icon: <AlertTriangle size={20} />,
      variant: stats?.overdue_count ? 'danger' : 'default',
    },
  ];

  const pendingColumns: TableColumn<PendingApproval>[] = [
    {
      id: 'reference',
      header: 'Reference',
      accessor: (row) => row.request.reference_name,
      render: (_, row): React.ReactNode => (
        <div>
          <div className="font-medium">{row.request.reference_name}</div>
          <div className="text-xs text-gray-500">{row.request.requester_name}</div>
        </div>
      ),
    },
    {
      id: 'type',
      header: 'Type',
      accessor: (row) => row.request.approval_type,
      render: (_, row): React.ReactNode => <TypeBadge type={row.request.approval_type} />,
    },
    {
      id: 'amount',
      header: 'Montant',
      accessor: (row) => row.request.amount,
      render: (_, row): React.ReactNode => row.request.amount
        ? formatCurrency(row.request.amount, row.request.currency)
        : '-',
    },
    {
      id: 'step',
      header: 'Etape',
      accessor: (row) => row.request.current_step,
      render: (_, row): React.ReactNode => (
        <span className="text-sm">
          {row.request.current_step}/{row.request.total_steps} - {row.step.name}
        </span>
      ),
    },
    {
      id: 'deadline',
      header: 'Echeance',
      accessor: (row) => row.deadline,
      render: (_, row): React.ReactNode => row.deadline
        ? <span className="text-sm">{formatDate(row.deadline)}</span>
        : '-',
    },
    {
      id: 'actions',
      header: '',
      accessor: (row) => row.request.id,
      width: 150,
      render: (_, row): React.ReactNode => (
        <div className="flex gap-2">
          {row.can_approve && (
            <>
              <Button
                size="sm"
                variant="primary"
                onClick={() => setActionModal({ type: 'approve', request: row.request })}
              >
                <Check size={14} className="mr-1" />
                Approuver
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setActionModal({ type: 'reject', request: row.request })}
              >
                <X size={14} />
              </Button>
            </>
          )}
          {row.can_delegate && (
            <Button size="sm" variant="ghost">
              <UserPlus size={14} />
            </Button>
          )}
        </div>
      ),
    },
  ];

  const requestColumns: TableColumn<ApprovalRequest>[] = [
    {
      id: 'reference',
      header: 'Reference',
      accessor: 'reference_name',
      render: (_, row): React.ReactNode => (
        <button
          className="text-left hover:text-primary"
          onClick={() => setSelectedRequest(row)}
        >
          <div className="font-medium">{row.reference_name}</div>
          <div className="text-xs text-gray-500">{row.requester_name}</div>
        </button>
      ),
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'approval_type',
      render: (v): React.ReactNode => <TypeBadge type={v as ApprovalType} />,
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v): React.ReactNode => <StatusBadge status={v as RequestStatus} />,
    },
    {
      id: 'progress',
      header: 'Progression',
      accessor: 'current_step',
      render: (_, row): React.ReactNode => (
        <div className="flex items-center gap-2">
          <div className="w-20 bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary rounded-full h-2"
              style={{ width: `${(row.current_step / row.total_steps) * 100}%` }}
            />
          </div>
          <span className="text-xs text-gray-500">{row.current_step}/{row.total_steps}</span>
        </div>
      ),
    },
    {
      id: 'amount',
      header: 'Montant',
      accessor: 'amount',
      render: (_, row): React.ReactNode => row.amount
        ? formatCurrency(row.amount, row.currency)
        : '-',
    },
    {
      id: 'created_at',
      header: 'Cree le',
      accessor: 'created_at',
      render: (v): React.ReactNode => formatDate(v as string),
    },
  ];

  const workflowColumns: TableColumn<ApprovalWorkflow>[] = [
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      render: (_, row): React.ReactNode => (
        <div>
          <div className="font-medium">{row.name}</div>
          {row.description && <div className="text-xs text-gray-500">{row.description}</div>}
        </div>
      ),
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'approval_type',
      render: (v): React.ReactNode => <TypeBadge type={v as ApprovalType} />,
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v): React.ReactNode => <WorkflowStatusBadge status={v as WorkflowStatus} />,
    },
    {
      id: 'steps',
      header: 'Etapes',
      accessor: 'steps',
      render: (_, row): React.ReactNode => (
        <span className="text-sm">{row.steps?.length || 0} etapes</span>
      ),
    },
    {
      id: 'default',
      header: 'Defaut',
      accessor: 'is_default',
      render: (v): React.ReactNode => v ? <Badge variant="success">Oui</Badge> : null,
    },
  ];

  return (
    <PageWrapper
      title="Approbations"
      subtitle={`${pendingCount?.count || 0} en attente`}
      actions={
        <Button variant="secondary" onClick={() => { view === 'pending' ? refetchPending() : refetchRequests(); }}>
          <RefreshCw size={16} className="mr-2" />
          Actualiser
        </Button>
      }
    >
      {/* KPIs */}
      <Grid cols={4} gap="md" className="mb-6">
        {kpis.map((kpi) => (
          <KPICard key={kpi.id} kpi={kpi} />
        ))}
      </Grid>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b">
        <button
          onClick={() => setView('pending')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${view === 'pending' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <Clock size={16} className="inline mr-1" />
          En attente ({pendingCount?.count || 0})
        </button>
        <button
          onClick={() => setView('requests')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${view === 'requests' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <History size={16} className="inline mr-1" />
          Toutes les demandes
        </button>
        <button
          onClick={() => setView('workflows')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${view === 'workflows' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <GitBranch size={16} className="inline mr-1" />
          Workflows
        </button>
      </div>

      {/* Content */}
      {view === 'pending' && (
        <Card noPadding>
          <DataTable
            columns={pendingColumns}
            data={(pending || []).map((p, idx) => ({ ...p, _key: p.request?.id || String(idx) }))}
            keyField="_key"
            isLoading={pendingLoading}
            emptyMessage="Aucune approbation en attente"
          />
        </Card>
      )}

      {view === 'requests' && (
        <Card noPadding>
          <DataTable
            columns={requestColumns}
            data={requests?.items || []}
            keyField="id"
            isLoading={requestsLoading}
            pagination={{
              page,
              pageSize,
              total: requests?.total || 0,
              onPageChange: setPage,
              onPageSizeChange: setPageSize,
            }}
            emptyMessage="Aucune demande d'approbation"
          />
        </Card>
      )}

      {view === 'workflows' && (
        <Card noPadding>
          <DataTable
            columns={workflowColumns}
            data={workflows?.items || []}
            keyField="id"
            isLoading={workflowsLoading}
            emptyMessage="Aucun workflow configure"
          />
        </Card>
      )}

      {/* Action Modal */}
      <Modal
        isOpen={!!actionModal}
        onClose={() => { setActionModal(null); setComment(''); }}
        title={actionModal?.type === 'approve' ? 'Approuver la demande' : 'Rejeter la demande'}
      >
        {actionModal && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded">
              <div className="font-medium">{actionModal.request.reference_name}</div>
              <div className="text-sm text-gray-500">{actionModal.request.requester_name}</div>
              {actionModal.request.amount && (
                <div className="text-lg font-semibold mt-2">
                  {formatCurrency(actionModal.request.amount, actionModal.request.currency)}
                </div>
              )}
            </div>

            <div className="space-y-1">
              <label className="block text-sm font-medium">Commentaire (optionnel)</label>
              <textarea
                className="azals-input w-full"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Ajouter un commentaire..."
                rows={3}
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => { setActionModal(null); setComment(''); }}>
                Annuler
              </Button>
              <Button
                variant={actionModal.type === 'approve' ? 'primary' : 'danger'}
                onClick={handleAction}
                disabled={submitAction.isPending}
              >
                {actionModal.type === 'approve' ? (
                  <>
                    <Check size={16} className="mr-2" />
                    Approuver
                  </>
                ) : (
                  <>
                    <X size={16} className="mr-2" />
                    Rejeter
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Request Detail Modal */}
      <Modal
        isOpen={!!selectedRequest}
        onClose={() => setSelectedRequest(null)}
        title={selectedRequest?.reference_name || 'Detail'}
      >
        {selectedRequest && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Type:</span>
                <span className="ml-2">{APPROVAL_TYPE_CONFIG[selectedRequest.approval_type]?.label}</span>
              </div>
              <div>
                <span className="text-gray-500">Statut:</span>
                <span className="ml-2"><StatusBadge status={selectedRequest.status} /></span>
              </div>
              <div>
                <span className="text-gray-500">Demandeur:</span>
                <span className="ml-2">{selectedRequest.requester_name}</span>
              </div>
              <div>
                <span className="text-gray-500">Workflow:</span>
                <span className="ml-2">{selectedRequest.workflow_name}</span>
              </div>
              {selectedRequest.amount && (
                <div>
                  <span className="text-gray-500">Montant:</span>
                  <span className="ml-2 font-semibold">
                    {formatCurrency(selectedRequest.amount, selectedRequest.currency)}
                  </span>
                </div>
              )}
              <div>
                <span className="text-gray-500">Progression:</span>
                <span className="ml-2">{selectedRequest.current_step}/{selectedRequest.total_steps} etapes</span>
              </div>
            </div>

            <div className="flex justify-end pt-4 border-t">
              <Button variant="secondary" onClick={() => setSelectedRequest(null)}>
                Fermer
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </PageWrapper>
  );
};

export default ApprovalModule;
