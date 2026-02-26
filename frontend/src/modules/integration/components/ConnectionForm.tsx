/**
 * AZALS MODULE GAP-086 - Integration Hub - Connection Form
 * Formulaire de creation/modification de connexion
 */

import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import type { ConnectionCreate } from '../types';
import integrationApi from '../api';

export interface ConnectionFormProps {
  connectionId?: string;
  connectorType?: string;
  onBack: () => void;
  onSaved: (id: string) => void;
}

export const ConnectionForm: React.FC<ConnectionFormProps> = ({
  connectionId,
  connectorType,
  onBack,
  onSaved,
}) => {
  const isNew = !connectionId;
  const queryClient = useQueryClient();

  const [form, setForm] = useState({
    name: '',
    code: '',
    description: '',
    connector_type: connectorType || 'rest_api',
    auth_type: 'api_key',
    base_url: '',
    api_version: '',
    credentials: {} as Record<string, string>,
    settings: {} as Record<string, unknown>,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      if (isNew) {
        const result = await integrationApi.createConnection(form as ConnectionCreate);
        queryClient.invalidateQueries({ queryKey: ['integration', 'connections'] });
        onSaved(result.id);
      } else {
        await integrationApi.updateConnection(connectionId!, form);
        queryClient.invalidateQueries({ queryKey: ['integration', 'connections'] });
        onSaved(connectionId!);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageWrapper
      title={isNew ? 'Nouvelle connexion' : 'Modifier la connexion'}
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="azals-alert azals-alert--error mb-4">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        <Card title="Informations generales">
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>Nom *</label>
              <input
                type="text"
                className="azals-input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="azals-form-field">
              <label>Code</label>
              <input
                type="text"
                className="azals-input"
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                placeholder="Genere automatiquement"
              />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Description</label>
              <textarea
                className="azals-textarea"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={2}
              />
            </div>
            <div className="azals-form-field">
              <label>Type de connecteur *</label>
              <select
                className="azals-select"
                value={form.connector_type}
                onChange={(e) => setForm({ ...form, connector_type: e.target.value })}
                disabled={!!connectorType}
              >
                <option value="rest_api">API REST</option>
                <option value="graphql">GraphQL</option>
                <option value="webhook">Webhook</option>
                <option value="stripe">Stripe</option>
                <option value="hubspot">HubSpot</option>
                <option value="salesforce">Salesforce</option>
                <option value="slack">Slack</option>
                <option value="google_drive">Google Drive</option>
                <option value="shopify">Shopify</option>
              </select>
            </div>
            <div className="azals-form-field">
              <label>Type d'authentification *</label>
              <select
                className="azals-select"
                value={form.auth_type}
                onChange={(e) => setForm({ ...form, auth_type: e.target.value })}
              >
                <option value="none">Aucune</option>
                <option value="api_key">Cle API</option>
                <option value="oauth2">OAuth 2.0</option>
                <option value="basic">Basic Auth</option>
                <option value="bearer">Bearer Token</option>
              </select>
            </div>
          </Grid>
        </Card>

        <Card title="Configuration API">
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>URL de base</label>
              <input
                type="url"
                className="azals-input"
                value={form.base_url}
                onChange={(e) => setForm({ ...form, base_url: e.target.value })}
                placeholder="https://api.example.com"
              />
            </div>
            <div className="azals-form-field">
              <label>Version API</label>
              <input
                type="text"
                className="azals-input"
                value={form.api_version}
                onChange={(e) => setForm({ ...form, api_version: e.target.value })}
                placeholder="v1"
              />
            </div>
          </Grid>
        </Card>

        {form.auth_type === 'api_key' && (
          <Card title="Credentials">
            <div className="azals-form-field">
              <label>Cle API</label>
              <input
                type="password"
                className="azals-input"
                value={form.credentials.api_key || ''}
                onChange={(e) => setForm({
                  ...form,
                  credentials: { ...form.credentials, api_key: e.target.value }
                })}
                placeholder="sk_..."
              />
            </div>
          </Card>
        )}

        {form.auth_type === 'basic' && (
          <Card title="Credentials">
            <Grid cols={2} gap="md">
              <div className="azals-form-field">
                <label>Nom d'utilisateur</label>
                <input
                  type="text"
                  className="azals-input"
                  value={form.credentials.username || ''}
                  onChange={(e) => setForm({
                    ...form,
                    credentials: { ...form.credentials, username: e.target.value }
                  })}
                />
              </div>
              <div className="azals-form-field">
                <label>Mot de passe</label>
                <input
                  type="password"
                  className="azals-input"
                  value={form.credentials.password || ''}
                  onChange={(e) => setForm({
                    ...form,
                    credentials: { ...form.credentials, password: e.target.value }
                  })}
                />
              </div>
            </Grid>
          </Card>
        )}

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onBack}>
            Annuler
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            {isNew ? 'Creer' : 'Enregistrer'}
          </Button>
        </div>
      </form>
    </PageWrapper>
  );
};

export default ConnectionForm;
