/**
 * AZALSCORE - Module Passerelles d'Import
 * ========================================
 * Gestion des connexions d'import multi-sources (Odoo, etc.)
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button, Modal } from '@ui/actions';
import { Input, Select, TextArea } from '@ui/forms';
import {
  Plus, Settings, Play, Pause, Trash2,
  CheckCircle, AlertCircle, Clock, Calendar, History,
  Link2, Link2Off, Save, Loader2, ExternalLink
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { fr } from 'date-fns/locale';

import { odooApi } from './api';
import {
  OdooConnectionConfig, ImportHistory, ScheduleMode,
  STATUS_CONFIG, SYNC_TYPE_CONFIG, SCHEDULE_MODE_CONFIG,
  CRON_PRESETS, INTERVAL_PRESETS, SyncType
} from './types';

// ============================================================
// HELPER COMPONENTS
// ============================================================

const StatusBadge: React.FC<{ status: string; size?: 'sm' | 'md' }> = ({ status, size = 'md' }) => {
  const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] || { label: status, color: 'gray' };
  const sizeClass = size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-sm px-2 py-1';
  return (
    <span className={`inline-flex items-center rounded-full font-medium ${sizeClass} bg-${config.color}-100 text-${config.color}-800`}>
      {config.label}
    </span>
  );
};

const ConnectionStatusIcon: React.FC<{ connected: boolean; active: boolean }> = ({ connected, active }) => {
  if (!active) {
    return <span className="text-gray-400"><Link2Off size={16} /></span>;
  }
  return connected
    ? <span className="text-green-500"><Link2 size={16} /></span>
    : <span className="text-red-500"><AlertCircle size={16} /></span>;
};

const ScheduleStatusBadge: React.FC<{ config: OdooConnectionConfig }> = ({ config }) => {
  if (config.schedule_mode === 'disabled') {
    return <span className="text-xs text-gray-500">Pas de planification</span>;
  }
  if (config.schedule_paused) {
    return <span className="text-xs text-yellow-600 flex items-center gap-1"><Pause size={12} /> En pause</span>;
  }
  if (config.next_scheduled_run) {
    const nextRun = new Date(config.next_scheduled_run);
    return (
      <span className="text-xs text-blue-600 flex items-center gap-1">
        <Clock size={12} />
        {formatDistanceToNow(nextRun, { addSuffix: true, locale: fr })}
      </span>
    );
  }
  return <span className="text-xs text-gray-500">Planifie</span>;
};

// Field wrapper for labels
const Field: React.FC<{ label: string; required?: boolean; children: React.ReactNode }> = ({ label, required, children }) => (
  <div className="azals-field">
    <label className="azals-field__label">
      {label}
      {required && <span className="text-red-500 ml-1">*</span>}
    </label>
    {children}
  </div>
);

// ============================================================
// CONNECTION CARD
// ============================================================

interface ConnectionCardProps {
  config: OdooConnectionConfig;
  onEdit: () => void;
  onTest: () => void;
  onImport: () => void;
  onSchedule: () => void;
  onDelete: () => void;
}

const ConnectionCard: React.FC<ConnectionCardProps> = ({
  config, onEdit, onTest, onImport, onSchedule, onDelete
}) => {
  const enabledTypes = [
    config.sync_products && 'Produits',
    config.sync_contacts && 'Contacts',
    config.sync_suppliers && 'Fournisseurs',
    config.sync_invoices && 'Factures',
    config.sync_quotes && 'Devis',
  ].filter(Boolean);

  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <ConnectionStatusIcon connected={config.is_connected} active={config.is_active} />
          <h3 className="font-semibold text-gray-900">{config.name}</h3>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={onEdit}>
            <Settings size={16} />
          </Button>
          <Button variant="ghost" size="sm" onClick={onDelete} className="text-red-500">
            <Trash2 size={16} />
          </Button>
        </div>
      </div>

      <div className="text-sm text-gray-600 mb-2">
        <a href={config.odoo_url} target="_blank" rel="noopener noreferrer" className="hover:underline flex items-center gap-1">
          {config.odoo_url.replace(/^https?:\/\//, '')}
          <ExternalLink size={12} />
        </a>
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        {enabledTypes.map((type, i) => (
          <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
            {type}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
        <ScheduleStatusBadge config={config} />
        <span>{config.total_imports} imports</span>
      </div>

      <div className="flex gap-2">
        <Button variant="secondary" size="sm" onClick={onTest} className="flex-1">
          <CheckCircle size={14} className="mr-1" />
          Tester
        </Button>
        <Button variant="secondary" size="sm" onClick={onSchedule} className="flex-1">
          <Calendar size={14} className="mr-1" />
          Planifier
        </Button>
        <Button variant="primary" size="sm" onClick={onImport} className="flex-1">
          <Play size={14} className="mr-1" />
          Importer
        </Button>
      </div>
    </Card>
  );
};

// ============================================================
// CONFIG FORM MODAL
// ============================================================

interface ConfigFormModalProps {
  config?: OdooConnectionConfig | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: Record<string, unknown>) => void;
  isSaving: boolean;
}

const ConfigFormModal: React.FC<ConfigFormModalProps> = ({
  config, isOpen, onClose, onSave, isSaving
}) => {
  const [formData, setFormData] = useState({
    name: config?.name || '',
    description: config?.description || '',
    odoo_url: config?.odoo_url || '',
    odoo_database: config?.odoo_database || '',
    auth_method: config?.auth_method || 'api_key',
    username: config?.username || '',
    credential: '',
    sync_products: config?.sync_products ?? true,
    sync_contacts: config?.sync_contacts ?? true,
    sync_suppliers: config?.sync_suppliers ?? true,
    sync_purchase_orders: config?.sync_purchase_orders ?? false,
    sync_sale_orders: config?.sync_sale_orders ?? false,
    sync_invoices: config?.sync_invoices ?? true,
    sync_quotes: config?.sync_quotes ?? true,
    sync_accounting: config?.sync_accounting ?? false,
    sync_bank: config?.sync_bank ?? false,
    sync_interventions: config?.sync_interventions ?? false,
  });

  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testMessage, setTestMessage] = useState('');

  React.useEffect(() => {
    if (config) {
      setFormData({
        name: config.name,
        description: config.description || '',
        odoo_url: config.odoo_url,
        odoo_database: config.odoo_database,
        auth_method: config.auth_method,
        username: config.username,
        credential: '',
        sync_products: config.sync_products,
        sync_contacts: config.sync_contacts,
        sync_suppliers: config.sync_suppliers,
        sync_purchase_orders: config.sync_purchase_orders,
        sync_sale_orders: config.sync_sale_orders,
        sync_invoices: config.sync_invoices,
        sync_quotes: config.sync_quotes,
        sync_accounting: config.sync_accounting,
        sync_bank: config.sync_bank,
        sync_interventions: config.sync_interventions,
      });
    }
  }, [config]);

  const handleTest = async () => {
    if (!formData.odoo_url || !formData.username || !formData.credential) {
      setTestStatus('error');
      setTestMessage('URL, utilisateur et credential requis');
      return;
    }

    setTestStatus('testing');
    try {
      const result = await odooApi.connection.test({
        odoo_url: formData.odoo_url,
        odoo_database: formData.odoo_database,
        auth_method: formData.auth_method as 'password' | 'api_key',
        username: formData.username,
        credential: formData.credential,
      });

      if (result.success) {
        setTestStatus('success');
        setTestMessage(`Connecte a Odoo ${result.odoo_version || ''}`);
      } else {
        setTestStatus('error');
        setTestMessage(result.message);
      }
    } catch {
      setTestStatus('error');
      setTestMessage('Erreur de connexion');
    }
  };

  const handleSubmit = () => {
    const dataToSave = { ...formData };
    if (config && !dataToSave.credential) {
      delete (dataToSave as Record<string, unknown>).credential;
    }
    onSave(dataToSave);
  };

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={config ? 'Modifier la connexion' : 'Nouvelle connexion Odoo'} size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Nom de la connexion" required>
            <Input
              value={formData.name}
              onChange={(value: string) => setFormData({ ...formData, name: value })}
              placeholder="Ex: Odoo Production"
            />
          </Field>
          <Field label="URL Odoo" required>
            <Input
              value={formData.odoo_url}
              onChange={(value: string) => setFormData({ ...formData, odoo_url: value })}
              placeholder="https://mycompany.odoo.com"
            />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Base de donnees" required>
            <Input
              value={formData.odoo_database}
              onChange={(value: string) => setFormData({ ...formData, odoo_database: value })}
              placeholder="mycompany_prod"
            />
          </Field>
          <Field label="Methode d'authentification">
            <Select
              value={formData.auth_method}
              onChange={(value: string) => setFormData({ ...formData, auth_method: value as 'password' | 'api_key' })}
              options={[
                { value: 'api_key', label: 'Cle API (recommande)' },
                { value: 'password', label: 'Mot de passe' },
              ]}
            />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Utilisateur" required>
            <Input
              value={formData.username}
              onChange={(value: string) => setFormData({ ...formData, username: value })}
              placeholder="admin@company.com"
            />
          </Field>
          <Field label={formData.auth_method === 'api_key' ? 'Cle API' : 'Mot de passe'} required={!config}>
            <Input
              type="password"
              value={formData.credential}
              onChange={(value: string) => setFormData({ ...formData, credential: value })}
              placeholder={config ? '(laisser vide pour garder)' : ''}
            />
          </Field>
        </div>

        <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
          <Button variant="secondary" onClick={handleTest} disabled={testStatus === 'testing'}>
            {testStatus === 'testing' ? <Loader2 size={16} className="animate-spin mr-1" /> : <CheckCircle size={16} className="mr-1" />}
            Tester la connexion
          </Button>
          {testStatus === 'success' && (
            <span className="text-green-600 text-sm flex items-center gap-1">
              <CheckCircle size={14} /> {testMessage}
            </span>
          )}
          {testStatus === 'error' && (
            <span className="text-red-600 text-sm flex items-center gap-1">
              <AlertCircle size={14} /> {testMessage}
            </span>
          )}
        </div>

        <div>
          <h4 className="font-medium text-gray-900 mb-2">Donnees a synchroniser</h4>
          <div className="grid grid-cols-3 gap-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={formData.sync_products} onChange={(e) => setFormData({ ...formData, sync_products: e.target.checked })} className="rounded" />
              <span>Produits</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={formData.sync_contacts} onChange={(e) => setFormData({ ...formData, sync_contacts: e.target.checked })} className="rounded" />
              <span>Contacts</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={formData.sync_suppliers} onChange={(e) => setFormData({ ...formData, sync_suppliers: e.target.checked })} className="rounded" />
              <span>Fournisseurs</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={formData.sync_invoices} onChange={(e) => setFormData({ ...formData, sync_invoices: e.target.checked })} className="rounded" />
              <span>Factures</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={formData.sync_quotes} onChange={(e) => setFormData({ ...formData, sync_quotes: e.target.checked })} className="rounded" />
              <span>Devis</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={formData.sync_purchase_orders} onChange={(e) => setFormData({ ...formData, sync_purchase_orders: e.target.checked })} className="rounded" />
              <span>Commandes achat</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={formData.sync_sale_orders} onChange={(e) => setFormData({ ...formData, sync_sale_orders: e.target.checked })} className="rounded" />
              <span>Commandes vente</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={formData.sync_accounting} onChange={(e) => setFormData({ ...formData, sync_accounting: e.target.checked })} className="rounded" />
              <span>Comptabilite</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={formData.sync_interventions} onChange={(e) => setFormData({ ...formData, sync_interventions: e.target.checked })} className="rounded" />
              <span>Interventions</span>
            </label>
          </div>
        </div>

        <Field label="Description (optionnel)">
          <TextArea
            value={formData.description}
            onChange={(value: string) => setFormData({ ...formData, description: value })}
            rows={2}
          />
        </Field>
      </div>

      <div className="flex justify-end gap-2 mt-6">
        <Button variant="secondary" onClick={onClose}>Annuler</Button>
        <Button variant="primary" onClick={handleSubmit} disabled={isSaving}>
          {isSaving ? <Loader2 size={16} className="animate-spin mr-1" /> : <Save size={16} className="mr-1" />}
          {config ? 'Enregistrer' : 'Creer'}
        </Button>
      </div>
    </Modal>
  );
};

// ============================================================
// SCHEDULE MODAL
// ============================================================

interface ScheduleModalProps {
  config: OdooConnectionConfig | null;
  isOpen: boolean;
  onClose: () => void;
}

const ScheduleModal: React.FC<ScheduleModalProps> = ({ config, isOpen, onClose }) => {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<ScheduleMode>(config?.schedule_mode || 'disabled');
  const [cronExpression, setCronExpression] = useState(config?.schedule_cron_expression || '0 8 * * 1-5');
  const [intervalMinutes, setIntervalMinutes] = useState(config?.schedule_interval_minutes || 60);
  const [timezone] = useState(config?.schedule_timezone || 'Europe/Paris');

  const { data: nextRuns } = useQuery({
    queryKey: ['odoo-next-runs', config?.id, mode, cronExpression, intervalMinutes],
    queryFn: () => config?.id ? odooApi.schedule.getNextRuns(config.id, 5) : null,
    enabled: !!config?.id && mode !== 'disabled',
  });

  const scheduleMutation = useMutation({
    mutationFn: (data: { mode: ScheduleMode; cron_expression?: string; interval_minutes?: number; timezone: string }) =>
      odooApi.schedule.configure(config!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['odoo-configs'] });
      onClose();
    },
  });

  const pauseMutation = useMutation({
    mutationFn: () => odooApi.schedule.pause(config!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['odoo-configs'] }),
  });

  const resumeMutation = useMutation({
    mutationFn: () => odooApi.schedule.resume(config!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['odoo-configs'] }),
  });

  const handleSave = () => {
    scheduleMutation.mutate({
      mode,
      cron_expression: mode === 'cron' ? cronExpression : undefined,
      interval_minutes: mode === 'interval' ? intervalMinutes : undefined,
      timezone,
    });
  };

  if (!isOpen || !config) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Planification de l'import" size="md">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Mode de planification</label>
          <div className="space-y-2">
            {Object.entries(SCHEDULE_MODE_CONFIG).map(([key, { label, description }]) => (
              <label key={key} className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer border ${mode === key ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'}`}>
                <input
                  type="radio"
                  name="schedule_mode"
                  value={key}
                  checked={mode === key}
                  onChange={(e) => setMode(e.target.value as ScheduleMode)}
                  className="mt-1"
                />
                <div>
                  <div className="font-medium">{label}</div>
                  <div className="text-sm text-gray-500">{description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {mode === 'cron' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Expression Cron</label>
            <div className="flex gap-2 mb-2 flex-wrap">
              {CRON_PRESETS.map((preset) => (
                <button
                  key={preset.value}
                  type="button"
                  onClick={() => setCronExpression(preset.value)}
                  className={`px-2 py-1 text-xs rounded ${cronExpression === preset.value ? 'bg-blue-500 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            <Input
              value={cronExpression}
              onChange={(value: string) => setCronExpression(value)}
              placeholder="0 8 * * 1-5"
            />
          </div>
        )}

        {mode === 'interval' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Intervalle</label>
            <div className="flex gap-2 flex-wrap mb-2">
              {INTERVAL_PRESETS.map((preset) => (
                <button
                  key={preset.value}
                  type="button"
                  onClick={() => setIntervalMinutes(preset.value)}
                  className={`px-2 py-1 text-xs rounded ${intervalMinutes === preset.value ? 'bg-blue-500 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={intervalMinutes}
                onChange={(value: string) => setIntervalMinutes(parseInt(value) || 60)}
                min={5}
                max={1440}
                className="w-24"
              />
              <span className="text-sm text-gray-500">minutes</span>
            </div>
          </div>
        )}

        {mode !== 'disabled' && nextRuns?.next_runs && nextRuns.next_runs.length > 0 && (
          <div className="bg-gray-50 p-3 rounded-lg">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Prochaines executions</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              {nextRuns.next_runs.slice(0, 5).map((run, i) => (
                <li key={i} className="flex items-center gap-2">
                  <Clock size={12} />
                  {format(new Date(run), 'PPPp', { locale: fr })}
                </li>
              ))}
            </ul>
          </div>
        )}

        {config.schedule_mode !== 'disabled' && (
          <div className="flex gap-2">
            {config.schedule_paused ? (
              <Button variant="secondary" onClick={() => resumeMutation.mutate()} disabled={resumeMutation.isPending}>
                <Play size={14} className="mr-1" /> Reprendre
              </Button>
            ) : (
              <Button variant="secondary" onClick={() => pauseMutation.mutate()} disabled={pauseMutation.isPending}>
                <Pause size={14} className="mr-1" /> Mettre en pause
              </Button>
            )}
          </div>
        )}
      </div>

      <div className="flex justify-end gap-2 mt-6">
        <Button variant="secondary" onClick={onClose}>Annuler</Button>
        <Button variant="primary" onClick={handleSave} disabled={scheduleMutation.isPending}>
          {scheduleMutation.isPending ? <Loader2 size={16} className="animate-spin mr-1" /> : <Save size={16} className="mr-1" />}
          Enregistrer
        </Button>
      </div>
    </Modal>
  );
};

// ============================================================
// IMPORT MODAL
// ============================================================

interface ImportModalProps {
  config: OdooConnectionConfig | null;
  isOpen: boolean;
  onClose: () => void;
}

const ImportModal: React.FC<ImportModalProps> = ({ config, isOpen, onClose }) => {
  const queryClient = useQueryClient();
  const [selectedTypes, setSelectedTypes] = useState<SyncType[]>([]);
  const [fullSync, setFullSync] = useState(false);

  const availableTypes: SyncType[] = [
    config?.sync_products ? 'products' : null,
    config?.sync_contacts ? 'contacts' : null,
    config?.sync_suppliers ? 'suppliers' : null,
    config?.sync_invoices ? 'invoices' : null,
    config?.sync_quotes ? 'quotes' : null,
    config?.sync_purchase_orders ? 'purchase_orders' : null,
    config?.sync_sale_orders ? 'sale_orders' : null,
    config?.sync_accounting ? 'accounting' : null,
    config?.sync_bank ? 'bank' : null,
    config?.sync_interventions ? 'interventions' : null,
  ].filter((t): t is SyncType => t !== null);

  React.useEffect(() => {
    setSelectedTypes(availableTypes);
  }, [config]);

  const importMutation = useMutation({
    mutationFn: () => odooApi.import.selectiveImport(config!.id, { types: selectedTypes, full_sync: fullSync }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['odoo-configs'] });
      queryClient.invalidateQueries({ queryKey: ['odoo-history'] });
      onClose();
    },
  });

  const toggleType = (type: SyncType) => {
    setSelectedTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  if (!isOpen || !config) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Lancer un import" size="md">
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Types de donnees a importer</h4>
          <div className="grid grid-cols-2 gap-2">
            {availableTypes.map((type) => {
              const typeConfig = SYNC_TYPE_CONFIG[type];
              return (
                <label
                  key={type}
                  className={`flex items-center gap-2 p-2 rounded cursor-pointer border ${selectedTypes.includes(type) ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(type)}
                    onChange={() => toggleType(type)}
                  />
                  <span>{typeConfig.label}</span>
                </label>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={fullSync} onChange={(e) => setFullSync(e.target.checked)} className="rounded" />
            <span>Import complet (ignorer les deltas)</span>
          </label>
        </div>

        <div className="text-sm text-gray-500">
          <strong>Connexion:</strong> {config.name}
        </div>
      </div>

      <div className="flex justify-end gap-2 mt-6">
        <Button variant="secondary" onClick={onClose}>Annuler</Button>
        <Button
          variant="primary"
          onClick={() => importMutation.mutate()}
          disabled={importMutation.isPending || selectedTypes.length === 0}
        >
          {importMutation.isPending ? <Loader2 size={16} className="animate-spin mr-1" /> : <Play size={16} className="mr-1" />}
          Lancer l'import
        </Button>
      </div>
    </Modal>
  );
};

// ============================================================
// HISTORY TABLE
// ============================================================

interface HistoryTableProps {
  history: ImportHistory[];
  isLoading: boolean;
}

const HistoryTable: React.FC<HistoryTableProps> = ({ history, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="animate-spin text-gray-400" size={24} />
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        Aucun historique d'import
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Date</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Type</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Statut</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Crees</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Maj</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Erreurs</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Duree</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Declencheur</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {history.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-2 text-sm">
                {format(new Date(item.started_at), 'Pp', { locale: fr })}
              </td>
              <td className="px-4 py-2 text-sm">
                {SYNC_TYPE_CONFIG[item.sync_type]?.label || item.sync_type}
              </td>
              <td className="px-4 py-2">
                <StatusBadge status={item.status} size="sm" />
              </td>
              <td className="px-4 py-2 text-sm text-green-600">+{item.created_count}</td>
              <td className="px-4 py-2 text-sm text-blue-600">{item.updated_count}</td>
              <td className="px-4 py-2 text-sm text-red-600">{item.error_count}</td>
              <td className="px-4 py-2 text-sm text-gray-500">
                {item.duration_seconds ? `${item.duration_seconds}s` : '-'}
              </td>
              <td className="px-4 py-2 text-sm text-gray-500">
                {item.trigger_method === 'scheduled' ? (
                  <span className="flex items-center gap-1"><Clock size={12} /> Auto</span>
                ) : (
                  <span>Manuel</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

const ImportGatewaysModule: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'connections' | 'history'>('connections');
  const [editingConfig, setEditingConfig] = useState<OdooConnectionConfig | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [scheduleConfig, setScheduleConfig] = useState<OdooConnectionConfig | null>(null);
  const [importConfig, setImportConfig] = useState<OdooConnectionConfig | null>(null);

  const { data: configs = [], isLoading: configsLoading } = useQuery({
    queryKey: ['odoo-configs'],
    queryFn: () => odooApi.config.list(),
  });

  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ['odoo-history'],
    queryFn: () => odooApi.history.list(undefined, 50),
  });

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => odooApi.config.create(data as unknown as Parameters<typeof odooApi.config.create>[0]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['odoo-configs'] });
      setIsFormOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      odooApi.config.update(id, data as Parameters<typeof odooApi.config.update>[1]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['odoo-configs'] });
      setIsFormOpen(false);
      setEditingConfig(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => odooApi.config.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['odoo-configs'] }),
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => odooApi.connection.testConfig(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['odoo-configs'] }),
  });

  const handleSaveConfig = (data: Record<string, unknown>) => {
    if (editingConfig) {
      updateMutation.mutate({ id: editingConfig.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleDelete = (config: OdooConnectionConfig) => {
    if (window.confirm(`Supprimer la connexion "${config.name}" ?`)) {
      deleteMutation.mutate(config.id);
    }
  };

  return (
    <PageWrapper
      title="Passerelles d'Import"
      subtitle="Gerez vos connexions d'import depuis Odoo et autres sources"
      actions={
        <Button variant="primary" onClick={() => { setEditingConfig(null); setIsFormOpen(true); }}>
          <Plus size={16} className="mr-1" /> Nouvelle connexion
        </Button>
      }
    >
      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab('connections')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${activeTab === 'connections' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <Link2 size={16} className="inline mr-1" />
          Connexions ({configs.length})
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${activeTab === 'history' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <History size={16} className="inline mr-1" />
          Historique
        </button>
      </div>

      {activeTab === 'connections' && (
        <>
          {configsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin text-gray-400" size={32} />
            </div>
          ) : configs.length === 0 ? (
            <Card className="p-8 text-center">
              <Link2Off size={48} className="mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune connexion configuree</h3>
              <p className="text-gray-500 mb-4">Commencez par ajouter une connexion Odoo pour importer vos donnees.</p>
              <Button variant="primary" onClick={() => setIsFormOpen(true)}>
                <Plus size={16} className="mr-1" /> Ajouter une connexion
              </Button>
            </Card>
          ) : (
            <Grid cols={3} gap="md">
              {configs.map((config) => (
                <ConnectionCard
                  key={config.id}
                  config={config}
                  onEdit={() => { setEditingConfig(config); setIsFormOpen(true); }}
                  onTest={() => testMutation.mutate(config.id)}
                  onImport={() => setImportConfig(config)}
                  onSchedule={() => setScheduleConfig(config)}
                  onDelete={() => handleDelete(config)}
                />
              ))}
            </Grid>
          )}
        </>
      )}

      {activeTab === 'history' && (
        <Card>
          <HistoryTable history={history} isLoading={historyLoading} />
        </Card>
      )}

      <ConfigFormModal
        config={editingConfig}
        isOpen={isFormOpen}
        onClose={() => { setIsFormOpen(false); setEditingConfig(null); }}
        onSave={handleSaveConfig}
        isSaving={createMutation.isPending || updateMutation.isPending}
      />

      <ScheduleModal
        config={scheduleConfig}
        isOpen={!!scheduleConfig}
        onClose={() => setScheduleConfig(null)}
      />

      <ImportModal
        config={importConfig}
        isOpen={!!importConfig}
        onClose={() => setImportConfig(null)}
      />
    </PageWrapper>
  );
};

export default ImportGatewaysModule;
