/**
 * AZALSCORE Module - Admin - Enrichment Providers View
 * Configuration des fournisseurs d'enrichissement de donnees
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { Card, Grid } from '@ui/layout';
import { Button, Modal } from '@ui/actions';
import { Input, Select } from '@ui/forms';
import {
  Database, Settings, Key, CheckCircle, XCircle, AlertTriangle,
  Globe, Play, Trash2, Edit3, Plus, ExternalLink, RefreshCw
} from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

interface ProviderInfo {
  provider: string;
  name: string;
  description: string;
  requires_api_key: boolean;
  is_free: boolean;
  country: string;
  capabilities: string[];
  documentation_url?: string;
}

interface ProviderConfig {
  id: string;
  provider: string;
  name: string;
  description: string;
  is_enabled: boolean;
  is_primary: boolean;
  priority: number;
  has_api_key: boolean;
  requires_api_key: boolean;
  is_free: boolean;
  country: string;
  capabilities: string[];
  custom_requests_per_minute?: number;
  custom_requests_per_day?: number;
  last_success_at?: string;
  last_error_at?: string;
  last_error_message?: string;
  total_requests: number;
  total_errors: number;
  created_at: string;
  updated_at: string;
}

interface ProvidersListResponse {
  providers: ProviderConfig[];
  available_providers: ProviderInfo[];
}

interface TestResult {
  provider: string;
  success: boolean;
  response_time_ms: number;
  error?: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// HOOKS
// ============================================================================

const useProviders = () => {
  return useQuery<ProvidersListResponse>({
    queryKey: ['enrichment', 'providers'],
    queryFn: async () => {
      const response = await api.get('/v3/enrichment/admin/providers');
      return (response as any)?.data ?? response;
    },
  });
};

const useCreateProvider = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const response = await api.post('/v3/enrichment/admin/providers', data);
      return (response as any)?.data ?? response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['enrichment', 'providers'] });
    },
  });
};

const useUpdateProvider = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ provider, data }: { provider: string; data: Record<string, unknown> }) => {
      const response = await api.patch(`/v3/enrichment/admin/providers/${provider}`, data);
      return (response as any)?.data ?? response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['enrichment', 'providers'] });
    },
  });
};

const useDeleteProvider = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (provider: string) => {
      const response = await api.delete(`/v3/enrichment/admin/providers/${provider}`);
      return (response as any)?.data ?? response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['enrichment', 'providers'] });
    },
  });
};

const useTestProvider = () => {
  return useMutation<TestResult, Error, string>({
    mutationFn: async (provider: string) => {
      const response = await api.post(`/v3/enrichment/admin/providers/${provider}/test`);
      return (response as any)?.data ?? response;
    },
  });
};

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

const CountryBadge: React.FC<{ country: string }> = ({ country }) => {
  const config: Record<string, { label: string; color: string }> = {
    FR: { label: 'France', color: 'blue' },
    EU: { label: 'Europe', color: 'purple' },
    WORLD: { label: 'Mondial', color: 'green' },
    UNKNOWN: { label: 'Inconnu', color: 'gray' },
  };
  const { label, color } = config[country] || config.UNKNOWN;
  return <span className={`azals-badge azals-badge--${color}`}>{label}</span>;
};

const StatusBadge: React.FC<{ enabled: boolean }> = ({ enabled }) => (
  <span className={`azals-badge azals-badge--${enabled ? 'green' : 'red'}`}>
    {enabled ? 'Actif' : 'Inactif'}
  </span>
);

const ApiKeyBadge: React.FC<{ hasKey: boolean; required: boolean }> = ({ hasKey, required }) => {
  if (!required) {
    return <span className="azals-badge azals-badge--gray">Non requis</span>;
  }
  return (
    <span className={`azals-badge azals-badge--${hasKey ? 'green' : 'orange'}`}>
      {hasKey ? 'Configure' : 'Manquante'}
    </span>
  );
};

// ============================================================================
// PROVIDER CARD
// ============================================================================

interface ProviderCardProps {
  config: ProviderConfig;
  onEdit: () => void;
  onTest: () => void;
  onDelete: () => void;
  isLoading?: boolean;
  testResult?: TestResult | null;
}

const ProviderCard: React.FC<ProviderCardProps> = ({
  config,
  onEdit,
  onTest,
  onDelete,
  isLoading,
  testResult,
}) => {
  return (
    <Card className="azals-provider-card">
      <div className="azals-provider-card__header">
        <div className="azals-provider-card__title">
          <Database size={20} />
          <span>{config.name}</span>
          {config.is_primary && (
            <span className="azals-badge azals-badge--blue">Principal</span>
          )}
        </div>
        <div className="azals-provider-card__actions">
          <button
            onClick={onTest}
            className="azals-btn azals-btn--ghost azals-btn--sm"
            disabled={isLoading}
            title="Tester la connexion"
          >
            {isLoading ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
          </button>
          <button
            onClick={onEdit}
            className="azals-btn azals-btn--ghost azals-btn--sm"
            title="Modifier"
          >
            <Edit3 size={16} />
          </button>
          <button
            onClick={onDelete}
            className="azals-btn azals-btn--ghost azals-btn--sm azals-btn--danger"
            title="Supprimer"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <p className="azals-provider-card__description">{config.description}</p>

      <div className="azals-provider-card__badges">
        <StatusBadge enabled={config.is_enabled} />
        <CountryBadge country={config.country} />
        <ApiKeyBadge hasKey={config.has_api_key} required={config.requires_api_key} />
        {!config.is_free && (
          <span className="azals-badge azals-badge--yellow">Payant</span>
        )}
      </div>

      <div className="azals-provider-card__capabilities">
        <span className="azals-provider-card__capabilities-label">Capacites:</span>
        {config.capabilities.map((cap) => (
          <span key={cap} className="azals-badge azals-badge--gray azals-badge--sm">
            {cap}
          </span>
        ))}
      </div>

      <div className="azals-provider-card__stats">
        <div className="azals-provider-card__stat">
          <span className="azals-provider-card__stat-value">{config.total_requests}</span>
          <span className="azals-provider-card__stat-label">Requetes</span>
        </div>
        <div className="azals-provider-card__stat">
          <span className="azals-provider-card__stat-value">{config.total_errors}</span>
          <span className="azals-provider-card__stat-label">Erreurs</span>
        </div>
        <div className="azals-provider-card__stat">
          <span className="azals-provider-card__stat-value">{config.priority}</span>
          <span className="azals-provider-card__stat-label">Priorite</span>
        </div>
      </div>

      {testResult && (
        <div className={`azals-provider-card__test-result azals-provider-card__test-result--${testResult.success ? 'success' : 'error'}`}>
          {testResult.success ? (
            <>
              <CheckCircle size={16} />
              <span>Test reussi ({testResult.response_time_ms}ms)</span>
            </>
          ) : (
            <>
              <XCircle size={16} />
              <span>{testResult.error || 'Test echoue'}</span>
            </>
          )}
        </div>
      )}

      {config.last_error_message && (
        <div className="azals-provider-card__error">
          <AlertTriangle size={14} />
          <span>{config.last_error_message}</span>
        </div>
      )}
    </Card>
  );
};

// ============================================================================
// AVAILABLE PROVIDER CARD
// ============================================================================

interface AvailableProviderCardProps {
  info: ProviderInfo;
  onAdd: () => void;
}

const AvailableProviderCard: React.FC<AvailableProviderCardProps> = ({ info, onAdd }) => {
  return (
    <Card className="azals-provider-card azals-provider-card--available">
      <div className="azals-provider-card__header">
        <div className="azals-provider-card__title">
          <Database size={20} />
          <span>{info.name}</span>
        </div>
        <button
          onClick={onAdd}
          className="azals-btn azals-btn--primary azals-btn--sm"
        >
          <Plus size={16} />
          Configurer
        </button>
      </div>

      <p className="azals-provider-card__description">{info.description}</p>

      <div className="azals-provider-card__badges">
        <CountryBadge country={info.country} />
        {info.requires_api_key ? (
          <span className="azals-badge azals-badge--orange">Cle API requise</span>
        ) : (
          <span className="azals-badge azals-badge--green">Gratuit</span>
        )}
        {!info.is_free && (
          <span className="azals-badge azals-badge--yellow">Payant</span>
        )}
      </div>

      <div className="azals-provider-card__capabilities">
        <span className="azals-provider-card__capabilities-label">Capacites:</span>
        {info.capabilities.map((cap) => (
          <span key={cap} className="azals-badge azals-badge--gray azals-badge--sm">
            {cap}
          </span>
        ))}
      </div>

      {info.documentation_url && (
        <a
          href={info.documentation_url}
          target="_blank"
          rel="noopener noreferrer"
          className="azals-provider-card__doc-link"
        >
          <ExternalLink size={14} />
          Documentation
        </a>
      )}
    </Card>
  );
};

// ============================================================================
// CONFIG MODAL
// ============================================================================

interface ConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  provider?: ProviderConfig | ProviderInfo | null;
  isNew?: boolean;
}

const ConfigModal: React.FC<ConfigModalProps> = ({ isOpen, onClose, provider, isNew }) => {
  const [formData, setFormData] = useState({
    provider: (provider as ProviderInfo)?.provider || '',
    is_enabled: true,
    is_primary: false,
    priority: 100,
    api_key: '',
    api_secret: '',
    custom_requests_per_minute: '',
    custom_requests_per_day: '',
  });

  const createMutation = useCreateProvider();
  const updateMutation = useUpdateProvider();

  const updateField = useCallback((field: string, value: string | boolean | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data: Record<string, unknown> = {
      is_enabled: formData.is_enabled,
      is_primary: formData.is_primary,
      priority: formData.priority,
    };

    if (formData.api_key) {
      data.api_key = formData.api_key;
    }
    if (formData.api_secret) {
      data.api_secret = formData.api_secret;
    }
    if (formData.custom_requests_per_minute) {
      data.custom_requests_per_minute = parseInt(formData.custom_requests_per_minute);
    }
    if (formData.custom_requests_per_day) {
      data.custom_requests_per_day = parseInt(formData.custom_requests_per_day);
    }

    try {
      if (isNew) {
        data.provider = formData.provider;
        await createMutation.mutateAsync(data);
      } else {
        await updateMutation.mutateAsync({
          provider: (provider as ProviderConfig).provider,
          data,
        });
      }
      onClose();
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    }
  };

  React.useEffect(() => {
    if (provider && !isNew) {
      const config = provider as ProviderConfig;
      setFormData({
        provider: config.provider,
        is_enabled: config.is_enabled,
        is_primary: config.is_primary,
        priority: config.priority,
        api_key: '',
        api_secret: '',
        custom_requests_per_minute: config.custom_requests_per_minute?.toString() || '',
        custom_requests_per_day: config.custom_requests_per_day?.toString() || '',
      });
    } else if (provider && isNew) {
      setFormData((prev) => ({
        ...prev,
        provider: (provider as ProviderInfo).provider,
      }));
    }
  }, [provider, isNew]);

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isNew ? 'Configurer un provider' : `Modifier ${(provider as ProviderConfig)?.name || ''}`}
    >
      <form onSubmit={handleSubmit} className="azals-form">
        <div className="azals-form__group">
          <label className="azals-form__label">Statut</label>
          <div className="azals-form__checkbox">
            <input
              type="checkbox"
              id="is_enabled"
              checked={formData.is_enabled}
              onChange={(e) => updateField('is_enabled', e.target.checked)}
            />
            <label htmlFor="is_enabled">Active</label>
          </div>
        </div>

        <div className="azals-form__group">
          <div className="azals-form__checkbox">
            <input
              type="checkbox"
              id="is_primary"
              checked={formData.is_primary}
              onChange={(e) => updateField('is_primary', e.target.checked)}
            />
            <label htmlFor="is_primary">Provider principal</label>
          </div>
        </div>

        <div className="azals-form__group">
          <label className="azals-form__label">
            Priorite (1-999, plus bas = plus prioritaire)
          </label>
          <Input
            type="number"
            value={formData.priority}
            onChange={(value) => updateField('priority', parseInt(value) || 100)}
            min={1}
            max={999}
          />
        </div>

        <div className="azals-form__group">
          <label className="azals-form__label">
            <Key size={14} /> Cle API
          </label>
          <Input
            type="password"
            value={formData.api_key}
            onChange={(value) => updateField('api_key', value)}
            placeholder={!isNew ? '(laisser vide pour conserver)' : 'Entrez la cle API'}
          />
        </div>

        <div className="azals-form__group">
          <label className="azals-form__label">
            Secret API (optionnel)
          </label>
          <Input
            type="password"
            value={formData.api_secret}
            onChange={(value) => updateField('api_secret', value)}
            placeholder={!isNew ? '(laisser vide pour conserver)' : 'Entrez le secret API'}
          />
        </div>

        <Grid cols={2} gap="md">
          <div className="azals-form__group">
            <label className="azals-form__label">
              Limite / minute
            </label>
            <Input
              type="number"
              value={formData.custom_requests_per_minute}
              onChange={(value) => updateField('custom_requests_per_minute', value)}
              placeholder="Par defaut"
            />
          </div>

          <div className="azals-form__group">
            <label className="azals-form__label">
              Limite / jour
            </label>
            <Input
              type="number"
              value={formData.custom_requests_per_day}
              onChange={(value) => updateField('custom_requests_per_day', value)}
              placeholder="Par defaut"
            />
          </div>
        </Grid>

        <div className="azals-form__actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" variant="primary" disabled={isLoading}>
            {isLoading ? 'Enregistrement...' : 'Enregistrer'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

// ============================================================================
// MAIN VIEW
// ============================================================================

export const EnrichmentProvidersView: React.FC = () => {
  const { data, isLoading, error } = useProviders();
  const testMutation = useTestProvider();
  const deleteMutation = useDeleteProvider();

  const [selectedProvider, setSelectedProvider] = useState<ProviderConfig | ProviderInfo | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isNewProvider, setIsNewProvider] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [testingProvider, setTestingProvider] = useState<string | null>(null);

  const handleEdit = useCallback((config: ProviderConfig) => {
    setSelectedProvider(config);
    setIsNewProvider(false);
    setIsModalOpen(true);
  }, []);

  const handleAdd = useCallback((info: ProviderInfo) => {
    setSelectedProvider(info);
    setIsNewProvider(true);
    setIsModalOpen(true);
  }, []);

  const handleTest = useCallback(async (provider: string) => {
    setTestingProvider(provider);
    try {
      const result = await testMutation.mutateAsync(provider);
      setTestResults((prev) => ({ ...prev, [provider]: result }));
    } catch (error) {
      setTestResults((prev) => ({
        ...prev,
        [provider]: {
          provider,
          success: false,
          response_time_ms: 0,
          error: (error as Error).message,
        },
      }));
    } finally {
      setTestingProvider(null);
    }
  }, [testMutation]);

  const handleDelete = useCallback(async (provider: string) => {
    if (window.confirm(`Supprimer la configuration de ${provider} ?`)) {
      await deleteMutation.mutateAsync(provider);
    }
  }, [deleteMutation]);

  const closeModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedProvider(null);
  }, []);

  if (isLoading) {
    return (
      <div className="azals-loading">
        <RefreshCw size={24} className="animate-spin" />
        Chargement des providers...
      </div>
    );
  }

  if (error) {
    return (
      <div className="azals-error">
        <AlertTriangle size={24} />
        Erreur lors du chargement des providers
      </div>
    );
  }

  const { providers = [], available_providers = [] } = data || {};

  return (
    <div className="azals-enrichment-providers">
      <div className="azals-section">
        <div className="azals-section__header">
          <h3 className="azals-section__title">
            <Settings size={20} />
            Providers Configures ({providers.length})
          </h3>
        </div>

        {providers.length === 0 ? (
          <Card>
            <div className="azals-empty-state">
              <Database size={48} />
              <p>Aucun provider configure</p>
              <p className="azals-empty-state__hint">
                Configurez un provider ci-dessous pour commencer
              </p>
            </div>
          </Card>
        ) : (
          <div className="azals-providers-grid">
            {providers.map((config) => (
              <ProviderCard
                key={config.id}
                config={config}
                onEdit={() => handleEdit(config)}
                onTest={() => handleTest(config.provider)}
                onDelete={() => handleDelete(config.provider)}
                isLoading={testingProvider === config.provider}
                testResult={testResults[config.provider]}
              />
            ))}
          </div>
        )}
      </div>

      {available_providers.length > 0 && (
        <div className="azals-section">
          <div className="azals-section__header">
            <h3 className="azals-section__title">
              <Globe size={20} />
              Providers Disponibles ({available_providers.length})
            </h3>
          </div>

          <div className="azals-providers-grid">
            {available_providers.map((info) => (
              <AvailableProviderCard
                key={info.provider}
                info={info}
                onAdd={() => handleAdd(info)}
              />
            ))}
          </div>
        </div>
      )}

      <ConfigModal
        isOpen={isModalOpen}
        onClose={closeModal}
        provider={selectedProvider}
        isNew={isNewProvider}
      />

      <style>{`
        .azals-enrichment-providers {
          padding: 1.5rem;
        }

        .azals-section {
          margin-bottom: 2rem;
        }

        .azals-section__header {
          margin-bottom: 1rem;
        }

        .azals-section__title {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 1.125rem;
          font-weight: 600;
          color: var(--color-text-primary);
        }

        .azals-providers-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
          gap: 1rem;
        }

        .azals-provider-card {
          padding: 1rem;
        }

        .azals-provider-card--available {
          border-style: dashed;
          background: var(--color-bg-subtle);
        }

        .azals-provider-card__header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 0.75rem;
        }

        .azals-provider-card__title {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 600;
          color: var(--color-text-primary);
        }

        .azals-provider-card__actions {
          display: flex;
          gap: 0.25rem;
        }

        .azals-provider-card__description {
          font-size: 0.875rem;
          color: var(--color-text-secondary);
          margin-bottom: 0.75rem;
          line-height: 1.4;
        }

        .azals-provider-card__badges {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-bottom: 0.75rem;
        }

        .azals-provider-card__capabilities {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 0.375rem;
          margin-bottom: 0.75rem;
        }

        .azals-provider-card__capabilities-label {
          font-size: 0.75rem;
          color: var(--color-text-muted);
        }

        .azals-provider-card__stats {
          display: flex;
          gap: 1.5rem;
          padding-top: 0.75rem;
          border-top: 1px solid var(--color-border);
        }

        .azals-provider-card__stat {
          display: flex;
          flex-direction: column;
        }

        .azals-provider-card__stat-value {
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--color-text-primary);
        }

        .azals-provider-card__stat-label {
          font-size: 0.75rem;
          color: var(--color-text-muted);
        }

        .azals-provider-card__test-result {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem;
          margin-top: 0.75rem;
          border-radius: 0.375rem;
          font-size: 0.875rem;
        }

        .azals-provider-card__test-result--success {
          background: var(--color-success-bg);
          color: var(--color-success);
        }

        .azals-provider-card__test-result--error {
          background: var(--color-danger-bg);
          color: var(--color-danger);
        }

        .azals-provider-card__error {
          display: flex;
          align-items: flex-start;
          gap: 0.375rem;
          padding: 0.5rem;
          margin-top: 0.75rem;
          background: var(--color-warning-bg);
          color: var(--color-warning);
          border-radius: 0.375rem;
          font-size: 0.75rem;
        }

        .azals-provider-card__doc-link {
          display: inline-flex;
          align-items: center;
          gap: 0.375rem;
          margin-top: 0.75rem;
          font-size: 0.875rem;
          color: var(--color-accent);
          text-decoration: none;
        }

        .azals-provider-card__doc-link:hover {
          text-decoration: underline;
        }

        .azals-empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 3rem;
          text-align: center;
          color: var(--color-text-muted);
        }

        .azals-empty-state__hint {
          font-size: 0.875rem;
          margin-top: 0.5rem;
        }

        .azals-loading,
        .azals-error {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          padding: 3rem;
          color: var(--color-text-secondary);
        }

        .azals-error {
          color: var(--color-danger);
        }

        .animate-spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .azals-form {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .azals-form__group {
          display: flex;
          flex-direction: column;
          gap: 0.375rem;
        }

        .azals-form__label {
          display: flex;
          align-items: center;
          gap: 0.375rem;
          font-size: 0.875rem;
          font-weight: 500;
          color: var(--color-text-primary);
        }

        .azals-form__checkbox {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .azals-form__checkbox input {
          width: 1rem;
          height: 1rem;
        }

        .azals-form__actions {
          display: flex;
          justify-content: flex-end;
          gap: 0.75rem;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid var(--color-border);
        }
      `}</style>
    </div>
  );
};

export default EnrichmentProvidersView;
