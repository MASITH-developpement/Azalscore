/**
 * Bank Connections View - Comptabilité Automatisée
 *
 * Gestion des connexions bancaires en mode PULL uniquement.
 *
 * PRINCIPES:
 * - PULL mode: synchronisation déclenchée par l'utilisateur ou automatique
 * - JAMAIS de webhooks/PUSH depuis la banque
 * - L'utilisateur contrôle quand les données sont récupérées
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Building2,
  Plus,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  CreditCard,
  Wallet,
  TrendingUp,
  TrendingDown,
  Calendar,
  Link2,
  Unlink,
  Eye,
  Settings,
  ChevronRight,
  Shield,
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button, ButtonGroup } from '@ui/actions';
import { StatusBadge } from '@ui/dashboards';
import { Modal, Select, Input } from '@ui/forms';
import { ErrorState } from '../../../ui-engine/components/StateViews';
import { useAuth } from '@core/auth';

// ============================================================
// TYPES
// ============================================================

interface BankProvider {
  id: string;
  name: string;
  logo_url: string | null;
  country: string;
  supported_features: string[];
}

interface BankConnection {
  id: string;
  provider_id: string;
  provider_name: string;
  status: 'ACTIVE' | 'EXPIRED' | 'ERROR' | 'PENDING';
  consent_expires_at: string | null;
  last_sync_at: string | null;
  last_sync_status: string | null;
  accounts_count: number;
  created_at: string;
}

interface BankAccount {
  id: string;
  connection_id: string;
  provider_account_id: string;
  account_type: string;
  name: string;
  iban: string | null;
  currency: string;
  current_balance: number;
  available_balance: number | null;
  last_sync_at: string | null;
  is_active: boolean;
}

interface SyncSession {
  id: string;
  connection_id: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  transactions_fetched: number;
  transactions_new: number;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
}

interface BankConnectionsData {
  connections: BankConnection[];
  accounts: BankAccount[];
  recent_syncs: SyncSession[];
  total_balance: number;
  available_providers: BankProvider[];
}

// ============================================================
// API HOOKS
// ============================================================

const useBankConnections = () => {
  return useQuery({
    queryKey: ['accounting', 'bank', 'connections'],
    queryFn: async () => {
      const response = await api.get<BankConnectionsData>(
        '/accounting/bank/connections'
      );
      return response.data;
    },
    staleTime: 60000,
  });
};

const useCreateConnection = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ providerId }: { providerId: string }) => {
      const response = await api.post('/accounting/bank/connections', {
        provider_id: providerId,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'bank'] });
    },
  });
};

const useSyncConnection = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ connectionId }: { connectionId: string }) => {
      const response = await api.post(
        `/accounting/bank/connections/${connectionId}/sync`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'bank'] });
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

const useSyncAll = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/accounting/bank/sync-all');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'bank'] });
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

const useDisconnectBank = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ connectionId }: { connectionId: string }) => {
      const response = await api.delete(
        `/accounting/bank/connections/${connectionId}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'bank'] });
    },
  });
};

// ============================================================
// HELPER FUNCTIONS
// ============================================================

const formatCurrency = (value: number, currency = 'EUR') =>
  new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
  }).format(value);

const formatDate = (dateStr: string | null) =>
  dateStr ? new Date(dateStr).toLocaleDateString('fr-FR') : '-';

const formatDateTime = (dateStr: string | null) =>
  dateStr ? new Date(dateStr).toLocaleString('fr-FR') : '-';

const formatRelativeTime = (dateStr: string | null): string => {
  if (!dateStr) return 'Jamais';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "À l'instant";
  if (diffMins < 60) return `Il y a ${diffMins} min`;
  if (diffHours < 24) return `Il y a ${diffHours}h`;
  if (diffDays < 7) return `Il y a ${diffDays}j`;
  return formatDate(dateStr);
};

const getConnectionStatusVariant = (
  status: string
): 'success' | 'warning' | 'danger' | 'info' => {
  switch (status) {
    case 'ACTIVE':
      return 'success';
    case 'PENDING':
      return 'info';
    case 'EXPIRED':
      return 'warning';
    case 'ERROR':
      return 'danger';
    default:
      return 'info';
  }
};

const getConnectionStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    ACTIVE: 'Active',
    PENDING: 'En attente',
    EXPIRED: 'Expirée',
    ERROR: 'Erreur',
  };
  return labels[status] || status;
};

const getSyncStatusVariant = (
  status: string
): 'success' | 'warning' | 'danger' | 'info' => {
  switch (status) {
    case 'COMPLETED':
      return 'success';
    case 'IN_PROGRESS':
    case 'PENDING':
      return 'info';
    case 'FAILED':
      return 'danger';
    default:
      return 'info';
  }
};

const getAccountTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    CHECKING: 'Compte courant',
    SAVINGS: 'Compte épargne',
    CREDIT: 'Carte de crédit',
    LOAN: 'Prêt',
    OTHER: 'Autre',
  };
  return labels[type] || type;
};

// ============================================================
// SUB-COMPONENTS
// ============================================================

const TotalBalanceCard: React.FC<{
  totalBalance: number;
  accountsCount: number;
  lastSync: string | null;
  onSyncAll: () => void;
  isSyncing: boolean;
}> = ({ totalBalance, accountsCount, lastSync, onSyncAll, isSyncing }) => {
  return (
    <Card className="azals-auto-accounting__bank-total">
      <div className="azals-auto-accounting__bank-total-content">
        <div className="azals-auto-accounting__bank-total-main">
          <span className="azals-auto-accounting__bank-total-label">
            Solde total
          </span>
          <span
            className={`azals-auto-accounting__bank-total-value ${
              totalBalance >= 0 ? 'azals-text--success' : 'azals-text--danger'
            }`}
          >
            {formatCurrency(totalBalance)}
          </span>
          <span className="azals-auto-accounting__bank-total-accounts">
            sur {accountsCount} compte(s)
          </span>
        </div>

        <div className="azals-auto-accounting__bank-total-sync">
          <span className="azals-auto-accounting__bank-sync-time">
            Dernière synchro: {formatRelativeTime(lastSync)}
          </span>
          <Button
            variant="primary"
            leftIcon={<RefreshCw size={16} className={isSyncing ? 'azals-spin' : ''} />}
            onClick={onSyncAll}
            disabled={isSyncing}
          >
            {isSyncing ? 'Synchronisation...' : 'Synchroniser tout'}
          </Button>
        </div>
      </div>

      <div className="azals-auto-accounting__bank-total-info">
        <Shield size={14} />
        <span>
          Mode PULL sécurisé - Vos données ne sont récupérées que sur demande
        </span>
      </div>
    </Card>
  );
};

const ConnectionCard: React.FC<{
  connection: BankConnection;
  accounts: BankAccount[];
  onSync: () => void;
  onDisconnect: () => void;
  isSyncing: boolean;
}> = ({ connection, accounts, onSync, onDisconnect, isSyncing }) => {
  const navigate = useNavigate();
  const [showAccounts, setShowAccounts] = useState(false);

  const connectionAccounts = accounts.filter(
    (a) => a.connection_id === connection.id
  );
  const totalBalance = connectionAccounts.reduce(
    (sum, a) => sum + a.current_balance,
    0
  );

  const isExpiringSoon =
    connection.consent_expires_at &&
    new Date(connection.consent_expires_at).getTime() - Date.now() <
      7 * 24 * 60 * 60 * 1000;

  return (
    <Card className="azals-auto-accounting__bank-connection">
      <div className="azals-auto-accounting__bank-connection-header">
        <div className="azals-auto-accounting__bank-connection-info">
          <Building2 size={24} />
          <div>
            <span className="azals-auto-accounting__bank-connection-name">
              {connection.provider_name}
            </span>
            <span className="azals-auto-accounting__bank-connection-accounts">
              {connection.accounts_count} compte(s)
            </span>
          </div>
        </div>

        <div className="azals-auto-accounting__bank-connection-status">
          <StatusBadge
            variant={getConnectionStatusVariant(connection.status)}
            size="sm"
            status={getConnectionStatusLabel(connection.status)}
          />
          {isExpiringSoon && (
            <span className="azals-auto-accounting__bank-expiring">
              <AlertTriangle size={14} />
              Expire bientôt
            </span>
          )}
        </div>
      </div>

      <div className="azals-auto-accounting__bank-connection-balance">
        <span className="azals-auto-accounting__bank-balance-label">
          Solde total
        </span>
        <span
          className={`azals-auto-accounting__bank-balance-value ${
            totalBalance >= 0 ? 'azals-text--success' : 'azals-text--danger'
          }`}
        >
          {formatCurrency(totalBalance)}
        </span>
      </div>

      <div className="azals-auto-accounting__bank-connection-meta">
        <span>
          <Clock size={12} />
          Dernière synchro: {formatRelativeTime(connection.last_sync_at)}
        </span>
        {connection.consent_expires_at && (
          <span>
            <Calendar size={12} />
            Consentement expire: {formatDate(connection.consent_expires_at)}
          </span>
        )}
      </div>

      {showAccounts && connectionAccounts.length > 0 && (
        <div className="azals-auto-accounting__bank-accounts-list">
          {connectionAccounts.map((account) => (
            <div
              key={account.id}
              className="azals-auto-accounting__bank-account"
            >
              <div className="azals-auto-accounting__bank-account-info">
                <CreditCard size={16} />
                <div>
                  <span className="azals-auto-accounting__bank-account-name">
                    {account.name}
                  </span>
                  <span className="azals-auto-accounting__bank-account-type">
                    {getAccountTypeLabel(account.account_type)}
                    {account.iban && ` - ${account.iban.slice(-8)}`}
                  </span>
                </div>
              </div>
              <span
                className={`azals-auto-accounting__bank-account-balance ${
                  account.current_balance >= 0
                    ? 'azals-text--success'
                    : 'azals-text--danger'
                }`}
              >
                {formatCurrency(account.current_balance, account.currency)}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="azals-auto-accounting__bank-connection-actions">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowAccounts(!showAccounts)}
        >
          {showAccounts ? 'Masquer comptes' : 'Voir comptes'}
        </Button>
        <ButtonGroup>
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<RefreshCw size={14} className={isSyncing ? 'azals-spin' : ''} />}
            onClick={onSync}
            disabled={isSyncing || connection.status !== 'ACTIVE'}
          >
            Synchroniser
          </Button>
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<Eye size={14} />}
            onClick={() =>
              navigate(`/auto-accounting/bank/transactions?connection=${connection.id}`)
            }
          >
            Transactions
          </Button>
          <Button
            variant="danger"
            size="sm"
            leftIcon={<Unlink size={14} />}
            onClick={onDisconnect}
          >
            Déconnecter
          </Button>
        </ButtonGroup>
      </div>
    </Card>
  );
};

const RecentSyncsWidget: React.FC<{ syncs: SyncSession[] }> = ({ syncs }) => {
  if (syncs.length === 0) return null;

  return (
    <Card title="Synchronisations récentes" icon={<RefreshCw size={18} />}>
      <div className="azals-auto-accounting__sync-history">
        {syncs.map((sync) => (
          <div key={sync.id} className="azals-auto-accounting__sync-item">
            <StatusBadge
              variant={getSyncStatusVariant(sync.status)}
              size="sm"
              status={sync.status === 'COMPLETED'
                ? 'Terminé'
                : sync.status === 'FAILED'
                ? 'Échec'
                : sync.status === 'IN_PROGRESS'
                ? 'En cours'
                : 'En attente'}
            />

            <div className="azals-auto-accounting__sync-details">
              <span className="azals-auto-accounting__sync-time">
                {formatDateTime(sync.started_at)}
              </span>
              {sync.status === 'COMPLETED' && (
                <span className="azals-auto-accounting__sync-stats">
                  {sync.transactions_new} nouvelle(s) / {sync.transactions_fetched}{' '}
                  totale(s)
                </span>
              )}
              {sync.status === 'FAILED' && sync.error_message && (
                <span className="azals-auto-accounting__sync-error">
                  {sync.error_message}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

// ============================================================
// MODALS
// ============================================================

const AddConnectionModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  providers: BankProvider[];
  onCreate: (providerId: string) => void;
  isLoading: boolean;
}> = ({ isOpen, onClose, providers, onCreate, isLoading }) => {
  const [selectedProvider, setSelectedProvider] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredProviders = providers.filter(
    (p) =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.country.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreate = () => {
    if (selectedProvider) {
      onCreate(selectedProvider);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Connecter une banque"
      size="lg"
    >
      <div className="azals-auto-accounting__add-bank">
        <div className="azals-auto-accounting__add-bank-info">
          <Shield size={20} />
          <div>
            <strong>Connexion sécurisée Open Banking</strong>
            <p>
              Vos identifiants bancaires ne sont jamais stockés. La connexion
              utilise le protocole Open Banking réglementé par la DSP2.
            </p>
          </div>
        </div>

        <div className="azals-form-group">
          <label className="azals-form-label">Rechercher une banque</label>
          <Input
            value={searchTerm}
            onChange={(value) => setSearchTerm(value)}
            placeholder="Nom de la banque ou pays..."
            leftIcon={<Building2 size={16} />}
          />
        </div>

        <div className="azals-auto-accounting__bank-providers">
          {filteredProviders.map((provider) => (
            <div
              key={provider.id}
              className={`azals-auto-accounting__bank-provider ${
                selectedProvider === provider.id
                  ? 'azals-auto-accounting__bank-provider--selected'
                  : ''
              }`}
              onClick={() => setSelectedProvider(provider.id)}
            >
              {provider.logo_url ? (
                <img src={provider.logo_url} alt={provider.name} />
              ) : (
                <Building2 size={24} />
              )}
              <div className="azals-auto-accounting__bank-provider-info">
                <span className="azals-auto-accounting__bank-provider-name">
                  {provider.name}
                </span>
                <span className="azals-auto-accounting__bank-provider-country">
                  {provider.country}
                </span>
              </div>
              {selectedProvider === provider.id && (
                <CheckCircle size={20} className="azals-text--success" />
              )}
            </div>
          ))}

          {filteredProviders.length === 0 && (
            <div className="azals-auto-accounting__bank-providers-empty">
              <p>Aucune banque trouvée</p>
            </div>
          )}
        </div>

        <div className="azals-modal__actions">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!selectedProvider || isLoading}
          >
            {isLoading ? 'Connexion...' : 'Connecter'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

const DisconnectModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  connection: BankConnection | null;
  onConfirm: () => void;
  isLoading: boolean;
}> = ({ isOpen, onClose, connection, onConfirm, isLoading }) => {
  if (!connection) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Déconnecter la banque">
      <div className="azals-auto-accounting__disconnect-modal">
        <div className="azals-auto-accounting__disconnect-warning">
          <AlertTriangle size={24} className="azals-text--warning" />
          <div>
            <p>
              Êtes-vous sûr de vouloir déconnecter{' '}
              <strong>{connection.provider_name}</strong> ?
            </p>
            <p className="azals-text--muted">
              Les transactions déjà synchronisées seront conservées, mais vous ne
              pourrez plus récupérer de nouvelles transactions tant que vous ne
              reconnecterez pas cette banque.
            </p>
          </div>
        </div>

        <div className="azals-modal__actions">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={isLoading}>
            {isLoading ? 'Déconnexion...' : 'Déconnecter'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

export const BankConnections: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [showAddModal, setShowAddModal] = useState(false);
  const [disconnectTarget, setDisconnectTarget] =
    useState<BankConnection | null>(null);
  const [syncingConnectionId, setSyncingConnectionId] = useState<string | null>(
    null
  );

  const { data, isLoading, error: bankError, refetch: refetchBank } = useBankConnections();
  const createConnection = useCreateConnection();
  const syncConnection = useSyncConnection();
  const syncAll = useSyncAll();
  const disconnectBank = useDisconnectBank();

  // L'assistante n'a pas accès aux connexions bancaires
  const isAssistante = user?.roles?.includes('assistante') || false;
  if (isAssistante) {
    return (
      <PageWrapper title="Accès refusé">
        <Card>
          <div className="azals-empty-state">
            <XCircle size={48} className="azals-text--danger" />
            <p>Vous n'avez pas accès à cette section.</p>
            <Button onClick={() => navigate('/auto-accounting')}>Retour</Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  const handleCreateConnection = async (providerId: string) => {
    try {
      const result = await createConnection.mutateAsync({ providerId }) as { authorization_url?: string };
      // Si la banque retourne une URL d'autorisation, rediriger
      if (result?.authorization_url) {
        window.location.href = result.authorization_url;
      } else {
        setShowAddModal(false);
      }
    } catch (error) {
      console.error('Connection failed:', error);
    }
  };

  const handleSync = async (connectionId: string) => {
    setSyncingConnectionId(connectionId);
    try {
      await syncConnection.mutateAsync({ connectionId });
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setSyncingConnectionId(null);
    }
  };

  const handleSyncAll = async () => {
    try {
      await syncAll.mutateAsync();
    } catch (error) {
      console.error('Sync all failed:', error);
    }
  };

  const handleDisconnect = async () => {
    if (!disconnectTarget) return;
    try {
      await disconnectBank.mutateAsync({ connectionId: disconnectTarget.id });
      setDisconnectTarget(null);
    } catch (error) {
      console.error('Disconnect failed:', error);
    }
  };

  const lastSync =
    data?.connections
      .map((c) => c.last_sync_at)
      .filter((d) => d)
      .sort()
      .reverse()[0] || null;

  if (isLoading) {
    return (
      <PageWrapper title="Connexions bancaires">
        <div className="azals-loading">
          <div className="azals-spinner" />
          <p>Chargement...</p>
        </div>
      </PageWrapper>
    );
  }

  if (bankError) {
    return (
      <PageWrapper title="Connexions bancaires">
        <ErrorState
          message={bankError instanceof Error ? bankError.message : undefined}
          onRetry={() => { refetchBank(); }}
        />
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title="Connexions bancaires"
      subtitle="Gérez vos connexions Open Banking en mode PULL sécurisé"
      actions={
        <Button
          leftIcon={<Plus size={16} />}
          onClick={() => setShowAddModal(true)}
        >
          Connecter une banque
        </Button>
      }
    >
      {/* Solde total */}
      {data && (
        <section className="azals-section">
          <TotalBalanceCard
            totalBalance={data.total_balance}
            accountsCount={data.accounts.length}
            lastSync={lastSync}
            onSyncAll={handleSyncAll}
            isSyncing={syncAll.isPending}
          />
        </section>
      )}

      {/* Liste des connexions */}
      <section className="azals-section">
        {data && data.connections.length > 0 ? (
          <Grid columns={2}>
            {data.connections.map((connection) => (
              <ConnectionCard
                key={connection.id}
                connection={connection}
                accounts={data.accounts}
                onSync={() => handleSync(connection.id)}
                onDisconnect={() => setDisconnectTarget(connection)}
                isSyncing={syncingConnectionId === connection.id}
              />
            ))}
          </Grid>
        ) : (
          <Card>
            <div className="azals-empty-state">
              <Building2 size={48} />
              <h3>Aucune banque connectée</h3>
              <p>
                Connectez vos comptes bancaires pour automatiser le
                rapprochement comptable.
              </p>
              <Button
                leftIcon={<Plus size={16} />}
                onClick={() => setShowAddModal(true)}
              >
                Connecter une banque
              </Button>
            </div>
          </Card>
        )}
      </section>

      {/* Historique des synchronisations */}
      {data && data.recent_syncs.length > 0 && (
        <section className="azals-section">
          <RecentSyncsWidget syncs={data.recent_syncs} />
        </section>
      )}

      {/* Modal ajout connexion */}
      {showAddModal && data && (
        <AddConnectionModal
          isOpen={true}
          onClose={() => setShowAddModal(false)}
          providers={data.available_providers}
          onCreate={handleCreateConnection}
          isLoading={createConnection.isPending}
        />
      )}

      {/* Modal déconnexion */}
      <DisconnectModal
        isOpen={!!disconnectTarget}
        onClose={() => setDisconnectTarget(null)}
        connection={disconnectTarget}
        onConfirm={handleDisconnect}
        isLoading={disconnectBank.isPending}
      />
    </PageWrapper>
  );
};

export default BankConnections;
