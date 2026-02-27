/**
 * AZALSCORE Module - Country Packs France - RGPD View
 * Vue RGPD (demandes, consentements, violations)
 */

import React, { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@ui/actions';
import { Select } from '@ui/forms';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate, formatDateTime } from '@/utils/formatters';
import { useRGPDConsents, useRGPDRequests, useRGPDBreaches, useProcessRGPDRequest } from '../hooks';
import { RGPD_REQUEST_TYPES, RGPD_REQUEST_STATUS, BREACH_SEVERITY } from '../constants';
import { Badge, TabNav } from './LocalComponents';
import type { RGPDConsent, RGPDRequest, RGPDBreach } from '../api';

export const RGPDView: React.FC = () => {
  const [activeSubView, setActiveSubView] = useState<'requests' | 'consents' | 'breaches'>('requests');
  const [filterRequestType, setFilterRequestType] = useState<string>('');
  const [filterRequestStatus, setFilterRequestStatus] = useState<string>('');

  const { data: requests = [], isLoading: loadingRequests, refetch: refetchRequests } = useRGPDRequests({
    type: filterRequestType || undefined,
    status: filterRequestStatus || undefined
  });
  const { data: consents = [], isLoading: loadingConsents } = useRGPDConsents();
  const { data: breaches = [], isLoading: loadingBreaches } = useRGPDBreaches();
  const processRequest = useProcessRGPDRequest();

  const requestColumns: TableColumn<RGPDRequest>[] = [
    { id: 'request_number', header: 'Reference', accessor: 'request_number', render: (v) => <code className="font-mono">{v as string}</code> },
    {
      id: 'request_type',
      header: 'Type',
      accessor: 'request_type',
      render: (v) => {
        const info = RGPD_REQUEST_TYPES.find(t => t.value === v);
        return <Badge color="blue">{info?.label || (v as string)}</Badge>;
      }
    },
    { id: 'contact_id', header: 'Contact ID', accessor: 'contact_id' },
    { id: 'description', header: 'Description', accessor: 'description', render: (v) => <span className="line-clamp-1">{v as string}</span> },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const info = RGPD_REQUEST_STATUS.find(s => s.value === v);
        return <Badge color={info?.color || 'gray'}>{info?.label || (v as string)}</Badge>;
      }
    },
    {
      id: 'due_date',
      header: 'Echeance',
      accessor: 'due_date',
      render: (v, row) => {
        const isOverdue = new Date(v as string) < new Date() && row.status !== 'COMPLETED';
        return <span className={isOverdue ? 'text-red-600 font-bold' : ''}>{formatDate(v as string)}</span>;
      }
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          {(row.status === 'PENDING' || row.status === 'IN_PROGRESS') && (
            <Button size="sm" variant="primary" onClick={() => processRequest.mutate({
              requestId: String(row.id),
              response: 'Demande traitee'
            })}>
              Traiter
            </Button>
          )}
        </div>
      )
    }
  ];

  const consentColumns: TableColumn<RGPDConsent>[] = [
    { id: 'contact_id', header: 'Contact ID', accessor: 'contact_id' },
    { id: 'purpose', header: 'Finalite', accessor: 'purpose' },
    {
      id: 'legal_basis',
      header: 'Base legale',
      accessor: 'legal_basis',
      render: (v) => <Badge color="blue">{v as string}</Badge>
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (v) => <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Actif' : 'Retire'}</Badge>
    },
    { id: 'consent_given_at', header: 'Donne le', accessor: 'consent_given_at', render: (v) => formatDate(v as string) },
    { id: 'consent_expires_at', header: 'Expire le', accessor: 'consent_expires_at', render: (v) => v ? formatDate(v as string) : '-' }
  ];

  const breachColumns: TableColumn<RGPDBreach>[] = [
    { id: 'breach_number', header: 'Reference', accessor: 'breach_number', render: (v) => <code className="font-mono">{v as string}</code> },
    {
      id: 'severity',
      header: 'Gravite',
      accessor: 'severity',
      render: (v) => {
        const info = BREACH_SEVERITY.find(s => s.value === v);
        return <Badge color={info?.color || 'gray'}>{info?.label || (v as string)}</Badge>;
      }
    },
    { id: 'description', header: 'Description', accessor: 'description', render: (v) => (
      <span className="line-clamp-2">{v as string}</span>
    )},
    { id: 'individuals_affected', header: 'Personnes affectees', accessor: 'individuals_affected', align: 'right' },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const colors: Record<string, string> = { DETECTED: 'red', INVESTIGATING: 'orange', CONTAINED: 'blue', RESOLVED: 'green' };
        return <Badge color={colors[v as string] || 'gray'}>{v as string}</Badge>;
      }
    },
    { id: 'breach_date', header: 'Date violation', accessor: 'breach_date', render: (v) => formatDateTime(v as string) },
    {
      id: 'notified_cnil',
      header: 'CNIL notifiee',
      accessor: 'notified_cnil',
      render: (v) => v ? <Badge color="green">Oui</Badge> : <Badge color="orange">Non</Badge>
    }
  ];

  const subTabs = [
    { id: 'requests', label: 'Demandes' },
    { id: 'consents', label: 'Consentements' },
    { id: 'breaches', label: 'Violations' }
  ];

  return (
    <div className="space-y-4">
      <TabNav tabs={subTabs} activeTab={activeSubView} onChange={(id) => setActiveSubView(id as typeof activeSubView)} />

      {activeSubView === 'requests' && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Demandes RGPD</h3>
            <div className="flex gap-2">
              <Select
                value={filterRequestType}
                onChange={(v) => setFilterRequestType(v)}
                options={[{ value: '', label: 'Tous types' }, ...RGPD_REQUEST_TYPES]}
                className="w-36"
              />
              <Select
                value={filterRequestStatus}
                onChange={(v) => setFilterRequestStatus(v)}
                options={[{ value: '', label: 'Tous statuts' }, ...RGPD_REQUEST_STATUS]}
                className="w-32"
              />
            </div>
          </div>
          <DataTable columns={requestColumns} data={requests} isLoading={loadingRequests} keyField="id" filterable onRetry={() => refetchRequests()} />
        </Card>
      )}

      {activeSubView === 'consents' && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Consentements</h3>
            <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createConsent' } })); }}>
              Nouveau consentement
            </Button>
          </div>
          <DataTable columns={consentColumns} data={consents} isLoading={loadingConsents} keyField="id" filterable />
        </Card>
      )}

      {activeSubView === 'breaches' && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Violations de donnees</h3>
            <Button variant="danger" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'reportBreach' } })); }}>
              <AlertTriangle size={16} className="mr-1" />
              Signaler une violation
            </Button>
          </div>
          <DataTable columns={breachColumns} data={breaches} isLoading={loadingBreaches} keyField="id" filterable />
        </Card>
      )}
    </div>
  );
};

export default RGPDView;
