/**
 * AZALSCORE - Module Import de Donnees
 * =====================================
 * Import depuis Odoo, Axonaut, Pennylane, Sage, Chorus
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import { Input } from '@ui/forms';
import { Download, Settings, Play, CheckCircle, AlertCircle, Clock, Save, Trash2 } from 'lucide-react';
import { api } from '@core/api-client';

// ============================================================
// TYPES
// ============================================================

// Direction de synchronisation
interface SyncDirection {
  import: boolean;  // Odoo → AZALSCORE
  export: boolean;  // AZALSCORE → Odoo
}

interface OdooConfig {
  id?: string;
  name: string;
  odoo_url: string;
  database: string;
  username: string;
  api_key: string;
  odoo_version?: number;
  // Données de base avec direction
  sync_products: boolean;
  sync_products_direction: SyncDirection;
  sync_contacts: boolean;
  sync_contacts_direction: SyncDirection;
  sync_suppliers: boolean;
  sync_suppliers_direction: SyncDirection;
  // Commandes
  sync_purchase_orders: boolean;
  sync_purchase_orders_direction: SyncDirection;
  sync_sale_orders: boolean;
  sync_sale_orders_direction: SyncDirection;
  // Documents commerciaux
  sync_invoices: boolean;
  sync_invoices_direction: SyncDirection;
  sync_quotes: boolean;
  sync_quotes_direction: SyncDirection;
  // Finance
  sync_accounting: boolean;
  sync_accounting_direction: SyncDirection;
  sync_bank: boolean;
  sync_bank_direction: SyncDirection;
  // Services
  sync_interventions: boolean;
  sync_interventions_direction: SyncDirection;
}

// Direction par defaut
const DEFAULT_DIRECTION: SyncDirection = { import: true, export: false };

interface ImportResult {
  id: string;
  status: string;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_failed: number;
  error_message?: string;
}

type ImportSource = 'odoo' | 'axonaut' | 'pennylane' | 'sage' | 'chorus';

interface ImportModuleProps {
  source: ImportSource;
}

// ============================================================
// CONFIGURATION PAR SOURCE
// ============================================================

const SOURCE_CONFIG: Record<ImportSource, { name: string; description: string; apiPrefix: string; fields: string[] }> = {
  odoo: {
    name: 'Odoo',
    description: 'Import depuis Odoo (versions 8-18) via XML-RPC',
    apiPrefix: '/v3/odoo',
    fields: ['url', 'database', 'username', 'apiKey'],
  },
  axonaut: {
    name: 'Axonaut',
    description: 'Import depuis Axonaut via API REST',
    apiPrefix: '/v3/axonaut',
    fields: ['apiKey'],
  },
  pennylane: {
    name: 'Pennylane',
    description: 'Import depuis Pennylane via API REST',
    apiPrefix: '/v3/pennylane',
    fields: ['apiKey'],
  },
  sage: {
    name: 'Sage',
    description: 'Import depuis Sage via fichiers export',
    apiPrefix: '/v3/sage',
    fields: ['url', 'username', 'apiKey'],
  },
  chorus: {
    name: 'Chorus Pro',
    description: 'Import depuis Chorus Pro (factures publiques)',
    apiPrefix: '/v3/chorus',
    fields: ['username', 'apiKey'],
  },
};

// ============================================================
// COMPOSANT ODOO IMPORT (avec vraie API)
// ============================================================

export const OdooImportModule: React.FC = () => {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<OdooConfig>({
    name: 'Configuration Odoo',
    odoo_url: '',
    database: '',
    username: '',
    api_key: '',
    sync_products: true,
    sync_products_direction: { import: true, export: false },
    sync_contacts: true,
    sync_contacts_direction: { import: true, export: false },
    sync_suppliers: true,
    sync_suppliers_direction: { import: true, export: false },
    sync_purchase_orders: false,
    sync_purchase_orders_direction: { import: true, export: false },
    sync_sale_orders: false,
    sync_sale_orders_direction: { import: true, export: false },
    sync_invoices: true,
    sync_invoices_direction: { import: true, export: false },
    sync_quotes: true,
    sync_quotes_direction: { import: true, export: false },
    sync_accounting: false,
    sync_accounting_direction: { import: true, export: false },
    sync_bank: false,
    sync_bank_direction: { import: true, export: false },
    sync_interventions: false,
    sync_interventions_direction: { import: true, export: false },
  });
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testMessage, setTestMessage] = useState('');

  // Charger la configuration existante
  const { data: configs } = useQuery({
    queryKey: ['odoo', 'configs'],
    queryFn: async () => {
      try {
        const response = await api.get('/v3/odoo/config');
        return Array.isArray(response) ? response : [];
      } catch {
        return [];
      }
    },
  });

  // Charger la première config si elle existe
  useEffect(() => {
    if (configs && configs.length > 0) {
      const existing = configs[0];
      setConfig({
        id: existing.id,
        name: existing.name || 'Configuration Odoo',
        odoo_url: existing.odoo_url || '',
        database: existing.odoo_database || '',
        username: existing.username || '',
        api_key: '', // Ne pas afficher l'ancienne clé
        sync_products: existing.sync_products ?? true,
        sync_products_direction: existing.sync_products_direction ?? { import: true, export: false },
        sync_contacts: existing.sync_contacts ?? true,
        sync_contacts_direction: existing.sync_contacts_direction ?? { import: true, export: false },
        sync_suppliers: existing.sync_suppliers ?? true,
        sync_suppliers_direction: existing.sync_suppliers_direction ?? { import: true, export: false },
        sync_purchase_orders: existing.sync_purchase_orders ?? false,
        sync_purchase_orders_direction: existing.sync_purchase_orders_direction ?? { import: true, export: false },
        sync_sale_orders: existing.sync_sale_orders ?? false,
        sync_sale_orders_direction: existing.sync_sale_orders_direction ?? { import: true, export: false },
        sync_invoices: existing.sync_invoices ?? true,
        sync_invoices_direction: existing.sync_invoices_direction ?? { import: true, export: false },
        sync_quotes: existing.sync_quotes ?? true,
        sync_quotes_direction: existing.sync_quotes_direction ?? { import: true, export: false },
        sync_accounting: existing.sync_accounting ?? false,
        sync_accounting_direction: existing.sync_accounting_direction ?? { import: true, export: false },
        sync_bank: existing.sync_bank ?? false,
        sync_bank_direction: existing.sync_bank_direction ?? { import: true, export: false },
        sync_interventions: existing.sync_interventions ?? false,
        sync_interventions_direction: existing.sync_interventions_direction ?? { import: true, export: false },
      });
    }
  }, [configs]);

  // Mutation pour sauvegarder
  const saveMutation = useMutation({
    mutationFn: async (data: OdooConfig) => {
      const payload = {
        name: data.name,
        odoo_url: data.odoo_url,
        odoo_database: data.database,
        auth_method: 'api_key',
        username: data.username,
        credential: data.api_key,
        sync_products: data.sync_products,
        sync_contacts: data.sync_contacts,
        sync_suppliers: data.sync_suppliers,
        sync_purchase_orders: data.sync_purchase_orders,
        sync_sale_orders: data.sync_sale_orders,
        sync_invoices: data.sync_invoices,
        sync_quotes: data.sync_quotes,
        sync_accounting: data.sync_accounting,
        sync_bank: data.sync_bank,
        sync_interventions: data.sync_interventions,
      };
      if (data.id) {
        return api.put(`/v3/odoo/config/${data.id}`, payload);
      } else {
        return api.post('/v3/odoo/config', payload);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['odoo', 'configs'] });
    },
  });

  // Mutation pour tester la connexion
  const testMutation = useMutation({
    mutationFn: async () => {
      if (config.id) {
        return api.post(`/v3/odoo/config/${config.id}/test`);
      } else {
        return api.post('/v3/odoo/test', {
          odoo_url: config.odoo_url,
          odoo_database: config.database,
          username: config.username,
          credential: config.api_key,
          auth_method: 'api_key',
        });
      }
    },
    onSuccess: (data: any) => {
      setTestStatus(data?.success ? 'success' : 'error');
      setTestMessage(data?.message || (data?.success ? 'Connexion reussie' : 'Echec de connexion'));
    },
    onError: (error: any) => {
      setTestStatus('error');
      setTestMessage(error?.message || 'Erreur de connexion');
    },
  });

  // Types d'import disponibles
  type ImportType = 'products' | 'contacts' | 'suppliers' | 'purchase_orders' | 'sale_orders' | 'invoices' | 'quotes' | 'accounting' | 'bank' | 'interventions' | 'full';

  // Mutation pour lancer l'import
  const importMutation = useMutation({
    mutationFn: async (type: ImportType) => {
      return api.post(`/v3/odoo/import/${type}?config_id=${config.id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['odoo', 'history'] });
    },
  });

  // Historique des imports
  const { data: history } = useQuery({
    queryKey: ['odoo', 'history'],
    queryFn: async () => {
      try {
        const response = await api.get('/v3/odoo/history');
        return Array.isArray(response) ? response : [];
      } catch {
        return [];
      }
    },
  });

  const handleTest = () => {
    setTestStatus('testing');
    testMutation.mutate();
  };

  const handleSave = () => {
    saveMutation.mutate(config);
  };

  const handleImport = (type: ImportType) => {
    if (!config.id) {
      alert('Veuillez d\'abord enregistrer la configuration');
      return;
    }
    importMutation.mutate(type);
  };

  // Mutation pour supprimer
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/v3/odoo/config/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['odoo', 'configs'] });
      setConfig({
        name: 'Configuration Odoo',
        odoo_url: '',
        database: '',
        username: '',
        api_key: '',
        sync_products: true,
        sync_products_direction: { import: true, export: false },
        sync_contacts: true,
        sync_contacts_direction: { import: true, export: false },
        sync_suppliers: true,
        sync_suppliers_direction: { import: true, export: false },
        sync_purchase_orders: false,
        sync_purchase_orders_direction: { import: true, export: false },
        sync_sale_orders: false,
        sync_sale_orders_direction: { import: true, export: false },
        sync_invoices: true,
        sync_invoices_direction: { import: true, export: false },
        sync_quotes: true,
        sync_quotes_direction: { import: true, export: false },
        sync_accounting: false,
        sync_accounting_direction: { import: true, export: false },
        sync_bank: false,
        sync_bank_direction: { import: true, export: false },
        sync_interventions: false,
        sync_interventions_direction: { import: true, export: false },
      });
      setTestStatus('idle');
      setTestMessage('');
    },
  });

  const handleDelete = () => {
    if (!config.id) return;
    if (confirm('Supprimer cette configuration ?')) {
      deleteMutation.mutate(config.id);
    }
  };

  return (
    <PageWrapper
      title="Import Odoo"
      subtitle="Import depuis Odoo (versions 8-18) via XML-RPC"
    >
      <Grid cols={2} gap="lg">
        {/* Configuration */}
        <Card title="Configuration" icon={<Settings size={20} />}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">URL du serveur Odoo</label>
              <Input
                placeholder="https://mon-instance.odoo.com"
                value={config.odoo_url}
                onChange={(value) => setConfig({ ...config, odoo_url: value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Base de donnees</label>
              <Input
                placeholder="nom_base"
                value={config.database}
                onChange={(value) => setConfig({ ...config, database: value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Nom d'utilisateur (email)</label>
              <Input
                placeholder="admin@example.com"
                value={config.username}
                onChange={(value) => setConfig({ ...config, username: value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Cle API (ou mot de passe)</label>
              <Input
                type="password"
                placeholder="Votre cle API Odoo"
                value={config.api_key}
                onChange={(value) => setConfig({ ...config, api_key: value })}
              />
              <p className="text-xs text-muted mt-1">
                Pour Odoo 14+, utilisez une cle API. Pour les versions anterieures, utilisez le mot de passe.
              </p>
            </div>

            {testMessage && (
              <div className={`p-3 rounded text-sm ${testStatus === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                {testMessage}
              </div>
            )}

            <div className="flex gap-2 pt-4">
              <Button
                variant="secondary"
                onClick={handleTest}
                disabled={testMutation.isPending || !config.odoo_url || !config.username}
              >
                {testMutation.isPending ? (
                  <><Clock size={16} className="animate-spin" /> Test...</>
                ) : testStatus === 'success' ? (
                  <><CheckCircle size={16} /> OK</>
                ) : testStatus === 'error' ? (
                  <><AlertCircle size={16} /> Echec</>
                ) : (
                  'Tester'
                )}
              </Button>
              <Button
                onClick={handleSave}
                disabled={saveMutation.isPending || !config.odoo_url}
              >
                {saveMutation.isPending ? (
                  <><Clock size={16} className="animate-spin" /> ...</>
                ) : (
                  <><Save size={16} /> Enregistrer</>
                )}
              </Button>
              {config.id && (
                <Button
                  variant="danger"
                  onClick={handleDelete}
                  disabled={deleteMutation.isPending}
                >
                  {deleteMutation.isPending ? (
                    <Clock size={16} className="animate-spin" />
                  ) : (
                    <Trash2 size={16} />
                  )}
                </Button>
              )}
            </div>
          </div>
        </Card>

        {/* Import */}
        <Card title="Lancer l'import" icon={<Download size={20} />}>
          <div className="space-y-4">
            <p className="text-sm text-muted">
              Selectionnez les donnees a importer depuis Odoo.
            </p>

            {/* Tableau de synchronisation avec Import/Export */}
            <div className="border rounded overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left p-2 font-medium">Donnees</th>
                    <th className="text-center p-2 font-medium w-20">Import</th>
                    <th className="text-center p-2 font-medium w-20">Export</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {[
                    { key: 'products', label: 'Produits / Articles' },
                    { key: 'contacts', label: 'Clients' },
                    { key: 'suppliers', label: 'Fournisseurs' },
                    { key: 'purchase_orders', label: 'Commandes Achat' },
                    { key: 'sale_orders', label: 'Commandes Vente' },
                    { key: 'invoices', label: 'Factures' },
                    { key: 'quotes', label: 'Devis' },
                    { key: 'accounting', label: 'Comptabilite' },
                    { key: 'bank', label: 'Banque' },
                    { key: 'interventions', label: 'Interventions' },
                  ].map(({ key, label }) => {
                    const syncKey = `sync_${key}` as keyof OdooConfig;
                    const dirKey = `sync_${key}_direction` as keyof OdooConfig;
                    const isEnabled = config[syncKey] as boolean;
                    const direction = (config[dirKey] as SyncDirection) || DEFAULT_DIRECTION;

                    return (
                      <tr key={key} className={isEnabled ? '' : 'opacity-50'}>
                        <td className="p-2">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={isEnabled}
                              onChange={(e) => setConfig({ ...config, [syncKey]: e.target.checked })}
                              className="rounded"
                            />
                            <span>{label}</span>
                          </label>
                        </td>
                        <td className="text-center p-2">
                          <input
                            type="checkbox"
                            checked={direction.import}
                            disabled={!isEnabled}
                            onChange={(e) => setConfig({
                              ...config,
                              [dirKey]: { ...direction, import: e.target.checked }
                            })}
                            className="rounded"
                            title="Odoo → AZALSCORE"
                          />
                        </td>
                        <td className="text-center p-2">
                          <input
                            type="checkbox"
                            checked={direction.export}
                            disabled={!isEnabled}
                            onChange={(e) => setConfig({
                              ...config,
                              [dirKey]: { ...direction, export: e.target.checked }
                            })}
                            className="rounded"
                            title="AZALSCORE → Odoo"
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-muted">
              <strong>Import</strong>: Odoo → AZALSCORE | <strong>Export</strong>: AZALSCORE → Odoo
            </p>

            <div className="flex flex-col gap-3 pt-4">
              <Button
                onClick={() => handleImport('full')}
                disabled={!config.id || importMutation.isPending}
                className="w-full"
              >
                {importMutation.isPending ? (
                  <><Clock size={16} className="animate-spin" /> Import en cours...</>
                ) : (
                  <><Play size={16} /> Lancer l'import complet</>
                )}
              </Button>

              <div className="border-t pt-3">
                <p className="text-xs text-muted mb-2">Ou importer individuellement :</p>
                <div className="grid grid-cols-2 gap-2">
                  <Button variant="secondary" size="sm" onClick={() => handleImport('products')} disabled={!config.id || importMutation.isPending}>
                    Produits
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleImport('contacts')} disabled={!config.id || importMutation.isPending}>
                    Clients
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleImport('suppliers')} disabled={!config.id || importMutation.isPending}>
                    Fournisseurs
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleImport('purchase_orders')} disabled={!config.id || importMutation.isPending}>
                    Cmd Achat
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleImport('sale_orders')} disabled={!config.id || importMutation.isPending}>
                    Cmd Vente
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleImport('invoices')} disabled={!config.id || importMutation.isPending}>
                    Factures
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleImport('quotes')} disabled={!config.id || importMutation.isPending}>
                    Devis
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleImport('accounting')} disabled={!config.id || importMutation.isPending}>
                    Comptabilite
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleImport('bank')} disabled={!config.id || importMutation.isPending}>
                    Banque
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleImport('interventions')} disabled={!config.id || importMutation.isPending}>
                    Interventions
                  </Button>
                </div>
              </div>
            </div>

            {!config.id && (
              <p className="text-xs text-amber-600">
                Enregistrez d'abord la configuration avant de lancer l'import.
              </p>
            )}
          </div>
        </Card>

        {/* Historique */}
        <Card title="Historique des imports" className="col-span-2">
          {history && history.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Date</th>
                    <th className="text-left p-2">Type</th>
                    <th className="text-left p-2">Statut</th>
                    <th className="text-right p-2">Traites</th>
                    <th className="text-right p-2">Crees</th>
                    <th className="text-right p-2">Maj</th>
                    <th className="text-right p-2">Erreurs</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(0, 10).map((item: any) => (
                    <tr key={item.id} className="border-b">
                      <td className="p-2">{new Date(item.started_at).toLocaleString('fr-FR')}</td>
                      <td className="p-2">{item.import_type}</td>
                      <td className="p-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          item.status === 'completed' ? 'bg-green-100 text-green-700' :
                          item.status === 'failed' ? 'bg-red-100 text-red-700' :
                          'bg-yellow-100 text-yellow-700'
                        }`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="p-2 text-right">{item.records_processed}</td>
                      <td className="p-2 text-right">{item.records_created}</td>
                      <td className="p-2 text-right">{item.records_updated}</td>
                      <td className="p-2 text-right">{item.records_failed}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-muted py-4 text-center">Aucun import effectue</p>
          )}
        </Card>
      </Grid>
    </PageWrapper>
  );
};

// ============================================================
// COMPOSANTS PLACEHOLDER POUR AUTRES SOURCES
// ============================================================

const PlaceholderImport: React.FC<{ source: ImportSource }> = ({ source }) => {
  const sourceConfig = SOURCE_CONFIG[source];

  return (
    <PageWrapper
      title={`Import ${sourceConfig.name}`}
      subtitle={sourceConfig.description}
    >
      <Card>
        <div className="text-center py-8">
          <Download size={48} className="mx-auto mb-4 text-muted" />
          <h3 className="text-lg font-medium mb-2">Module en cours de developpement</h3>
          <p className="text-sm text-muted">
            L'import depuis {sourceConfig.name} sera disponible prochainement.
          </p>
        </div>
      </Card>
    </PageWrapper>
  );
};

export const AxonautImportModule: React.FC = () => <PlaceholderImport source="axonaut" />;
export const PennylaneImportModule: React.FC = () => <PlaceholderImport source="pennylane" />;
export const SageImportModule: React.FC = () => <PlaceholderImport source="sage" />;
export const ChorusImportModule: React.FC = () => <PlaceholderImport source="chorus" />;

export default OdooImportModule;
