/**
 * AZALSCORE Module - Admin - TenantsView
 * Vue de gestion des tenants
 */

import React, { useState } from 'react';
import { Building, Edit3, Lock, Unlock, AlertTriangle, Package } from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { Select, Input } from '@ui/forms';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import {
  useTenants, useAvailableModules,
  useSuspendTenant, useActivateTenant, useCancelTenant, useUpdateTenant
} from '../hooks';

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface Tenant {
  id: string;
  tenant_id: string;
  name: string;
  email: string;
  status: 'ACTIVE' | 'INACTIVE' | 'TRIAL' | 'SUSPENDED' | 'PENDING';
  plan: 'STARTER' | 'PROFESSIONAL' | 'ENTERPRISE' | 'CUSTOM';
  modules_enabled: string[];
  max_users: number;
  max_storage_gb: number;
  storage_used_gb: number;
  created_at: string;
}

const TENANT_STATUSES = [
  { value: 'ACTIVE', label: 'Actif', color: 'green' },
  { value: 'INACTIVE', label: 'Inactif', color: 'gray' },
  { value: 'TRIAL', label: 'Essai', color: 'blue' },
  { value: 'SUSPENDED', label: 'Suspendu', color: 'red' }
];

const TENANT_PLANS = [
  { value: 'FREE', label: 'Gratuit' },
  { value: 'STARTER', label: 'Starter' },
  { value: 'PROFESSIONAL', label: 'Professionnel' },
  { value: 'ENTERPRISE', label: 'Enterprise' }
];

interface StatusInfo {
  value: string;
  label: string;
  color: string;
}

const getStatusInfo = (statuses: StatusInfo[], status: string): StatusInfo => {
  return statuses.find(s => s.value === status) || { value: status, label: status, color: 'gray' };
};

const TenantsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterPlan, setFilterPlan] = useState<string>('');
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editData, setEditData] = useState<Partial<Tenant>>({});

  const { data: modulesData } = useAvailableModules();
  const availableModules = modulesData?.modules || [];
  const modulesByCategory = modulesData?.modules_by_category || {};

  const { data: tenants = [], isLoading } = useTenants({
    status: filterStatus || undefined,
    plan: filterPlan || undefined
  });

  const suspendTenant = useSuspendTenant();
  const activateTenant = useActivateTenant();
  const cancelTenant = useCancelTenant();
  const updateTenant = useUpdateTenant();

  const handleEdit = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setEditData({
      name: tenant.name,
      max_users: tenant.max_users || 0,
      max_storage_gb: tenant.max_storage_gb || 0,
      modules_enabled: tenant.modules_enabled || [],
    });
    setShowEditModal(true);
  };

  const toggleModule = (moduleCode: string) => {
    const current = editData.modules_enabled || [];
    if (current.includes(moduleCode)) {
      setEditData({ ...editData, modules_enabled: current.filter(m => m !== moduleCode) });
    } else {
      setEditData({ ...editData, modules_enabled: [...current, moduleCode] });
    }
  };

  const handleSaveEdit = async () => {
    if (selectedTenant) {
      try {
        await updateTenant.mutateAsync({
          tenantId: selectedTenant.tenant_id,
          data: editData
        });
        setShowEditModal(false);
        setSelectedTenant(null);
      } catch (err: unknown) {
        alert('Erreur: ' + (err instanceof Error ? err.message : String(err)));
      }
    }
  };

  const handleSuspend = async (tenant: Tenant) => {
    if (confirm(`Suspendre le tenant "${tenant.name}" ?`)) {
      await suspendTenant.mutateAsync(tenant.tenant_id);
    }
  };

  const handleActivate = async (tenant: Tenant) => {
    await activateTenant.mutateAsync(tenant.tenant_id);
  };

  const handleCancel = async (tenant: Tenant) => {
    if (confirm(`ATTENTION: Annuler definitivement le tenant "${tenant.name}" ? Cette action est irreversible.`)) {
      await cancelTenant.mutateAsync(tenant.tenant_id);
    }
  };

  const columns: TableColumn<Tenant>[] = [
    { id: 'tenant_id', header: 'Code', accessor: 'tenant_id', render: (v) => <code className="font-mono text-xs">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'plan', header: 'Plan', accessor: 'plan', render: (v) => {
      const info = TENANT_PLANS.find(p => p.value === (v as string));
      return <Badge color="blue">{info?.label || (v as string)}</Badge>;
    }},
    { id: 'max_users', header: 'Utilisateurs max', accessor: 'max_users', render: (v) => (
      <span className="text-sm">{v as number}</span>
    )},
    { id: 'storage_used_gb', header: 'Stockage', accessor: 'storage_used_gb', render: (v, row) => {
      const tenant = row as Tenant;
      const used = (v as number) || 0;
      const max = tenant.max_storage_gb || 0;
      const percent = max > 0 ? Math.round((used / max) * 100) : 0;
      return (
        <div className="text-sm">
          <span className={percent > 90 ? 'text-red-600 font-semibold' : ''}>{used} Go</span>
          {max > 0 && <span className="text-gray-400">/{max} Go</span>}
        </div>
      );
    }},
    { id: 'modules', header: 'Modules', accessor: 'modules_enabled', render: (v) => {
      const modules = v as string[];
      return <span className="text-sm text-gray-600">{modules?.length || 0} actifs</span>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(TENANT_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => {
      const tenant = row as Tenant;
      return (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <Button size="sm" variant="secondary" onClick={() => handleEdit(tenant)}>
            <Edit3 size={14} />
          </Button>
          {tenant.status === 'ACTIVE' ? (
            <Button size="sm" variant="warning" onClick={() => handleSuspend(tenant)}>
              <Lock size={14} />
            </Button>
          ) : tenant.status === 'SUSPENDED' ? (
            <Button size="sm" variant="success" onClick={() => handleActivate(tenant)}>
              <Unlock size={14} />
            </Button>
          ) : null}
        </div>
      );
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Tenants</h3>
        <div className="flex gap-2">
          <Select
            value={filterPlan}
            onChange={(val) => setFilterPlan(val)}
            options={[{ value: '', label: 'Tous les plans' }, ...TENANT_PLANS]}
            className="w-36"
          />
          <Select
            value={filterStatus}
            onChange={(val) => setFilterStatus(val)}
            options={[{ value: '', label: 'Tous statuts' }, ...TENANT_STATUSES]}
            className="w-32"
          />
        </div>
      </div>
      <DataTable columns={columns} data={tenants} isLoading={isLoading} keyField="id" filterable />

      <Modal isOpen={showEditModal} onClose={() => setShowEditModal(false)} title={`Modifier: ${selectedTenant?.name}`} size="lg">
        <div className="space-y-6">
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Building size={16} />
              Informations generales
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="azals-field">
                <label htmlFor="tenant-edit-name">Nom</label>
                <Input
                  id="tenant-edit-name"
                  value={editData.name || ''}
                  onChange={(v) => setEditData({ ...editData, name: v })}
                />
              </div>
              <div className="azals-field">
                <label htmlFor="tenant-edit-max-users">Utilisateurs max</label>
                <Input
                  id="tenant-edit-max-users"
                  type="number"
                  value={String(editData.max_users || 0)}
                  onChange={(v) => setEditData({ ...editData, max_users: parseInt(v) || 0 })}
                />
              </div>
              <div className="azals-field">
                <label htmlFor="tenant-edit-storage">Stockage max (Go)</label>
                <Input
                  id="tenant-edit-storage"
                  type="number"
                  value={String(editData.max_storage_gb || 0)}
                  onChange={(v) => setEditData({ ...editData, max_storage_gb: parseInt(v) || 0 })}
                />
                <span className="text-xs text-gray-500">Utilise: {selectedTenant?.storage_used_gb || 0} Go</span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Package size={16} />
              Modules actives ({(editData.modules_enabled || []).length}/{availableModules.length})
            </h4>
            <div className="max-h-64 overflow-y-auto border rounded bg-gray-50 p-2 space-y-4">
              {Object.entries(modulesByCategory).map(([category, mods]) => (
                <div key={category}>
                  <h5 className="text-xs font-bold text-gray-600 uppercase mb-2 sticky top-0 bg-gray-50 py-1">
                    {category}
                  </h5>
                  <div className="grid grid-cols-2 gap-2">
                    {mods.map((mod) => {
                      const isEnabled = (editData.modules_enabled || []).includes(mod.code);
                      return (
                        <label
                          key={mod.code}
                          aria-label={mod.name}
                          className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                            isEnabled ? 'bg-blue-50 border border-blue-200' : 'bg-white border border-gray-200 hover:bg-gray-100'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isEnabled}
                            onChange={() => toggleModule(mod.code)}
                            className="rounded text-blue-600"
                          />
                          <div>
                            <div className="text-sm font-medium">{mod.name}</div>
                            <div className="text-xs text-gray-500">{mod.description}</div>
                          </div>
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex gap-2 mt-2">
              <button
                type="button"
                onClick={() => setEditData({ ...editData, modules_enabled: availableModules.map(m => m.code) })}
                className="text-xs text-blue-600 hover:underline"
              >
                Tout selectionner
              </button>
              <button
                type="button"
                onClick={() => setEditData({ ...editData, modules_enabled: [] })}
                className="text-xs text-gray-600 hover:underline"
              >
                Tout deselectionner
              </button>
            </div>
          </div>

          {selectedTenant && selectedTenant.status !== 'SUSPENDED' && (
            <div className="pt-4 border-t border-red-200 bg-red-50 -mx-6 px-6 pb-4 rounded-b">
              <h4 className="text-sm font-semibold text-red-700 mb-2 flex items-center gap-2">
                <AlertTriangle size={16} />
                Zone de danger
              </h4>
              <Button
                variant="danger"
                size="sm"
                onClick={() => {
                  handleCancel(selectedTenant);
                  setShowEditModal(false);
                }}
              >
                Annuler ce tenant definitivement
              </Button>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>Annuler</Button>
            <Button onClick={handleSaveEdit} isLoading={updateTenant.isPending}>Enregistrer</Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
};

export default TenantsView;
