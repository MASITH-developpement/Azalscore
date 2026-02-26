/**
 * AZALS MODULE GAP-086 - Integration Hub - Connectors List
 * Liste des connecteurs disponibles
 */

import React, { useState } from 'react';
import { Search, Plug, Webhook as WebhookIcon } from 'lucide-react';
import { PageWrapper, Card, Grid } from '@ui/layout';
import type { ConnectorDefinition } from '../types';
import { CONNECTOR_CATEGORIES } from '../types';
import { useConnectors } from '../hooks';
import { getCategoryIcon } from './StatusBadges';

export interface ConnectorsListProps {
  onSelectConnector: (connectorType: string) => void;
  onBack: () => void;
}

export const ConnectorsList: React.FC<ConnectorsListProps> = ({ onSelectConnector, onBack }) => {
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  const { data, isLoading } = useConnectors(categoryFilter || undefined);

  const filteredConnectors = data?.items.filter(c =>
    !searchQuery ||
    c.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const connectorsByCategory = filteredConnectors.reduce((acc, connector) => {
    const cat = connector.category || 'custom';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(connector);
    return acc;
  }, {} as Record<string, ConnectorDefinition[]>);

  return (
    <PageWrapper
      title="Connecteurs disponibles"
      subtitle="Explorez les integrations disponibles"
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <section className="azals-section">
        <Card noPadding>
          <div className="azals-filter-bar">
            <div className="azals-filter-bar__search">
              <Search size={16} />
              <input
                type="text"
                placeholder="Rechercher un connecteur..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="azals-input"
              />
            </div>
            <select
              className="azals-select"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="">Toutes les categories</option>
              {Object.entries(CONNECTOR_CATEGORIES).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </Card>
      </section>

      {isLoading ? (
        <div className="azals-loading-container">
          <div className="azals-spinner" />
          <p>Chargement des connecteurs...</p>
        </div>
      ) : (
        Object.entries(connectorsByCategory).map(([category, connectors]) => (
          <section key={category} className="azals-section">
            <h3 className="azals-section-title">
              {getCategoryIcon(category)}
              <span className="ml-2">{CONNECTOR_CATEGORIES[category] || category}</span>
              <span className="azals-badge azals-badge--gray ml-2">{connectors.length}</span>
            </h3>
            <Grid cols={3} gap="md">
              {connectors.map(connector => (
                <Card
                  key={connector.id}
                  className="azals-connector-card azals-clickable"
                  onClick={() => onSelectConnector(connector.connector_type)}
                >
                  <div className="azals-connector-card__header">
                    {connector.logo_url ? (
                      <img
                        src={connector.logo_url}
                        alt={connector.display_name}
                        className="azals-connector-card__logo"
                      />
                    ) : (
                      <div
                        className="azals-connector-card__icon"
                        style={{ backgroundColor: connector.color || '#6b7280' }}
                      >
                        <Plug size={24} />
                      </div>
                    )}
                    <div className="azals-connector-card__info">
                      <h4>{connector.display_name}</h4>
                      {connector.is_beta && (
                        <span className="azals-badge azals-badge--purple">Beta</span>
                      )}
                      {connector.is_premium && (
                        <span className="azals-badge azals-badge--yellow">Premium</span>
                      )}
                    </div>
                  </div>
                  <p className="azals-connector-card__description">
                    {connector.description || 'Integration avec ' + connector.display_name}
                  </p>
                  <div className="azals-connector-card__footer">
                    <span className="text-muted">
                      {connector.supported_entities.length} entites supportees
                    </span>
                    {connector.supports_webhooks && (
                      <WebhookIcon size={14} className="text-primary" />
                    )}
                  </div>
                </Card>
              ))}
            </Grid>
          </section>
        ))
      )}

      {!isLoading && filteredConnectors.length === 0 && (
        <div className="azals-empty-state">
          <Plug size={48} className="text-muted" />
          <p>Aucun connecteur trouve</p>
        </div>
      )}
    </PageWrapper>
  );
};

export default ConnectorsList;
