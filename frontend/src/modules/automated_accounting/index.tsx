/**
 * AZALSCORE Module - Automated Accounting (M2A)
 * Interface principale du module de comptabilite automatisee
 */

import React, { useState, useRef } from 'react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { LoadingState, EmptyState } from '@ui/components/StateViews';

// Local UI components
const Badge: React.FC<{ variant?: string; className?: string; children: React.ReactNode }> = ({ className = '', children }) => (
  <span className={`azals-badge ${className}`}>{children}</span>
);

const CardHeader: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="azals-card__header">{children}</div>
);

const CardTitle: React.FC<{ className?: string; children: React.ReactNode }> = ({ className = '', children }) => (
  <h3 className={`azals-card__title ${className}`}>{children}</h3>
);

const CardContent: React.FC<{ className?: string; children: React.ReactNode }> = ({ className = '', children }) => (
  <div className={`azals-card__body ${className}`}>{children}</div>
);

const Tabs: React.FC<{ defaultValue: string; children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = React.useState('');
  return (
    <div className="azals-tabs" data-active={activeTab}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<{ activeTab?: string; setActiveTab?: (v: string) => void }>, { activeTab, setActiveTab });
        }
        return child;
      })}
    </div>
  );
};

const TabsList: React.FC<{ children: React.ReactNode; activeTab?: string; setActiveTab?: (v: string) => void }> = ({ children, activeTab, setActiveTab }) => (
  <div className="azals-tabs__list flex gap-2 border-b mb-4" role="tablist">
    {React.Children.map(children, (child) => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child as React.ReactElement<{ activeTab?: string; setActiveTab?: (v: string) => void }>, { activeTab, setActiveTab });
      }
      return child;
    })}
  </div>
);

const TabsTrigger: React.FC<{ value: string; children: React.ReactNode; activeTab?: string; setActiveTab?: (v: string) => void }> = ({ value, children, activeTab, setActiveTab }) => (
  <button
    type="button"
    role="tab"
    className={`px-4 py-2 border-b-2 transition-colors ${activeTab === value ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
    aria-selected={activeTab === value}
    onClick={() => setActiveTab?.(value)}
  >
    <span className="flex items-center gap-2">{children}</span>
  </button>
);

const TabsContent: React.FC<{ value: string; children: React.ReactNode; className?: string; activeTab?: string }> = ({ value, children, className = '', activeTab }) => {
  if (activeTab !== value) return null;
  return <div className={className} role="tabpanel">{children}</div>;
};
import {
  Sparkles,
  FileText,
  Landmark,
  GitMerge,
  Bell,
  Upload,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Eye,
  Zap,
  TrendingUp,
  TrendingDown,
  Plus,
  Link2,
} from 'lucide-react';
import {
  useM2ADashboard,
  useDocumentList,
  useBankConnections,
  useBankTransactionList,
  useAlertList,
  useUploadDocument,
  useValidateDocument,
  useRejectDocument,
  useSyncBankConnection,
  useResolveAlert,
  useAutoReconcile,
} from './hooks';
import type {
  Document,
  BankConnection,
  BankTransaction,
  Alert,
  DocumentStatus,
  DocumentType,
  AlertSeverity,
  ConfidenceLevel,
} from './types';

// ============================================================================
// CONFIG
// ============================================================================

const DOCUMENT_STATUS_CONFIG: Record<DocumentStatus, { label: string; color: string }> = {
  RECEIVED: { label: 'Recu', color: 'gray' },
  PROCESSING: { label: 'En cours', color: 'blue' },
  ANALYZED: { label: 'Analyse', color: 'purple' },
  PENDING_VALIDATION: { label: 'A valider', color: 'orange' },
  VALIDATED: { label: 'Valide', color: 'green' },
  ACCOUNTED: { label: 'Comptabilise', color: 'green' },
  REJECTED: { label: 'Rejete', color: 'red' },
  ERROR: { label: 'Erreur', color: 'red' },
};

const DOCUMENT_TYPE_CONFIG: Record<DocumentType, { label: string }> = {
  INVOICE_RECEIVED: { label: 'Facture recue' },
  INVOICE_SENT: { label: 'Facture emise' },
  EXPENSE_NOTE: { label: 'Note de frais' },
  CREDIT_NOTE_RECEIVED: { label: 'Avoir recu' },
  CREDIT_NOTE_SENT: { label: 'Avoir emis' },
  QUOTE: { label: 'Devis' },
  PURCHASE_ORDER: { label: 'Bon de commande' },
  DELIVERY_NOTE: { label: 'Bon de livraison' },
  BANK_STATEMENT: { label: 'Releve bancaire' },
  OTHER: { label: 'Autre' },
};

const ALERT_SEVERITY_CONFIG: Record<AlertSeverity, { label: string; color: string }> = {
  INFO: { label: 'Info', color: 'blue' },
  WARNING: { label: 'Attention', color: 'yellow' },
  ERROR: { label: 'Erreur', color: 'orange' },
  CRITICAL: { label: 'Critique', color: 'red' },
};

const CONFIDENCE_CONFIG: Record<ConfidenceLevel, { label: string; color: string }> = {
  HIGH: { label: 'Haute', color: 'green' },
  MEDIUM: { label: 'Moyenne', color: 'yellow' },
  LOW: { label: 'Basse', color: 'orange' },
  VERY_LOW: { label: 'Tres basse', color: 'red' },
};

// ============================================================================
// HELPERS
// ============================================================================

function toNum(value: number | string | undefined): number {
  if (value === undefined || value === null) return 0;
  if (typeof value === 'number') return value;
  return parseFloat(value) || 0;
}

function formatCurrency(value: number | string | undefined): string {
  return `${toNum(value).toFixed(2)} EUR`;
}

function formatDate(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
}

function formatDateTime(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleString('fr-FR');
}

// ============================================================================
// STATUS BADGES
// ============================================================================

function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  const config = DOCUMENT_STATUS_CONFIG[status];
  const colorMap: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-800',
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800',
    purple: 'bg-purple-100 text-purple-800',
    red: 'bg-red-100 text-red-800',
  };

  return (
    <Badge className={colorMap[config.color] || colorMap.gray}>
      {config.label}
    </Badge>
  );
}

function ConfidenceBadge({ level, score }: { level?: ConfidenceLevel; score?: number }) {
  if (!level) return <span>-</span>;
  const config = CONFIDENCE_CONFIG[level];
  const colorMap: Record<string, string> = {
    green: 'bg-green-100 text-green-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-red-100 text-red-800',
  };

  return (
    <Badge className={colorMap[config.color] || 'bg-gray-100 text-gray-800'}>
      {score !== undefined ? `${(score * 100).toFixed(0)}%` : config.label}
    </Badge>
  );
}

function AlertSeverityBadge({ severity }: { severity: AlertSeverity }) {
  const config = ALERT_SEVERITY_CONFIG[severity];
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-red-100 text-red-800',
  };

  return (
    <Badge className={colorMap[config.color] || 'bg-gray-100 text-gray-800'}>
      {config.label}
    </Badge>
  );
}

// ============================================================================
// STATS CARDS
// ============================================================================

interface StatsCardsProps {
  stats: {
    documents_total: number;
    documents_pending: number;
    unreconciled_transactions: number;
    alerts_unread: number;
    alerts_critical: number;
    processing_rate: number;
    confidence_average: number;
  };
}

function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Documents</p>
              <p className="text-2xl font-bold">{stats.documents_total}</p>
              <p className="text-xs text-muted-foreground">
                {stats.documents_pending} a traiter
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <GitMerge className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Rapprochement</p>
              <p className="text-2xl font-bold">{stats.unreconciled_transactions}</p>
              <p className="text-xs text-muted-foreground">a rapprocher</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Bell className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Alertes</p>
              <p className="text-2xl font-bold">{stats.alerts_unread}</p>
              {stats.alerts_critical > 0 && (
                <p className="text-xs text-red-600 font-medium">
                  {stats.alerts_critical} critiques
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Sparkles className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Confiance IA</p>
              <p className="text-2xl font-bold">
                {(stats.confidence_average * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-muted-foreground">
                {(stats.processing_rate * 100).toFixed(0)}% auto
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// DOCUMENTS TAB
// ============================================================================

function DocumentsTab() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [statusFilter, setStatusFilter] = useState<DocumentStatus | ''>('');
  const [typeFilter, setTypeFilter] = useState<DocumentType | ''>('');

  const { data, isLoading } = useDocumentList({
    status: statusFilter || undefined,
    document_type: typeFilter || undefined,
  });

  const uploadDocument = useUploadDocument();
  const validateDocument = useValidateDocument();
  const rejectDocument = useRejectDocument();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadDocument.mutate({ file });
    }
  };

  const columns: import('@/types').TableColumn<Document>[] = [
    {
      id: 'original_filename',
      header: 'Document',
      accessor: 'original_filename',
      render: (_value, row) => (
        <div>
          <p className="font-medium">{row.original_filename || 'Sans nom'}</p>
          <p className="text-sm text-muted-foreground">
            {DOCUMENT_TYPE_CONFIG[row.document_type]?.label || row.document_type}
          </p>
        </div>
      ),
    },
    {
      id: 'vendor_name',
      header: 'Fournisseur',
      accessor: 'vendor_name',
      render: (_value, row) => row.vendor_name || '-',
    },
    {
      id: 'total_ttc',
      header: 'Montant TTC',
      accessor: 'total_ttc',
      render: (_value, row) => formatCurrency(row.total_ttc),
    },
    {
      id: 'invoice_date',
      header: 'Date',
      accessor: 'invoice_date',
      render: (_value, row) => formatDate(row.invoice_date),
    },
    {
      id: 'confidence_level',
      header: 'Confiance',
      accessor: 'confidence_level',
      render: (_value, row) => (
        <ConfidenceBadge level={row.confidence_level} score={row.confidence_score} />
      ),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (_value, row) => <DocumentStatusBadge status={row.status} />,
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_value, row) => (
        <div className="flex gap-1">
          <Button variant="ghost" size="sm">
            <Eye className="h-4 w-4" />
          </Button>
          {row.status === 'PENDING_VALIDATION' && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => validateDocument.mutate({ id: row.id })}
              >
                <CheckCircle className="h-4 w-4 text-green-500" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => rejectDocument.mutate({ id: row.id })}
              >
                <XCircle className="h-4 w-4 text-red-500" />
              </Button>
            </>
          )}
        </div>
      ),
    },
  ];

  if (isLoading) {
    return <LoadingState message="Chargement des documents..." />;
  }

  const items = (data as unknown as { items: Document[] } | undefined)?.items || [];

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as DocumentStatus | '')}
          className="border rounded-md px-3 py-2"
        >
          <option value="">Tous statuts</option>
          {Object.entries(DOCUMENT_STATUS_CONFIG).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as DocumentType | '')}
          className="border rounded-md px-3 py-2"
        >
          <option value="">Tous types</option>
          {Object.entries(DOCUMENT_TYPE_CONFIG).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        <div className="ml-auto">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.tiff,.tif"
            onChange={handleFileSelect}
            className="hidden"
          />
          <Button onClick={() => fileInputRef.current?.click()}>
            <Upload className="h-4 w-4 mr-2" />
            Importer
          </Button>
        </div>
      </div>

      {items.length > 0 ? (
        <DataTable
          data={items}
          columns={columns}
          keyField="id"
        />
      ) : (
        <EmptyState
          icon={<FileText className="h-12 w-12" />}
          title="Aucun document"
          message="Importez vos factures et justificatifs pour demarrer."
          action={{
            label: "Importer un document",
            onClick: () => fileInputRef.current?.click(),
            icon: <Upload className="h-4 w-4 mr-2" />,
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// BANK TAB
// ============================================================================

function BankTab() {
  const { data: connectionsData, isLoading: loadingConnections } = useBankConnections();
  const { data: transactionsData, isLoading: loadingTransactions } = useBankTransactionList({
    reconciliation_status: 'PENDING',
  });

  const syncBank = useSyncBankConnection();
  const autoReconcile = useAutoReconcile();

  if (loadingConnections) {
    return <LoadingState message="Chargement des connexions bancaires..." />;
  }

  const connections = (connectionsData as unknown as BankConnection[]) || [];
  const transactions = (transactionsData as unknown as { items: BankTransaction[] } | undefined)?.items || [];

  return (
    <div className="space-y-6">
      {/* Bank Connections */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Landmark className="h-5 w-5" />
              Connexions bancaires
            </CardTitle>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Connecter une banque
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {connections.length > 0 ? (
            <div className="space-y-4">
              {connections.map((conn: BankConnection) => (
                <div
                  key={conn.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-gray-100 rounded-lg">
                      <Landmark className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-medium">{conn.bank_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {conn.account_name} - {conn.iban_masked}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <Badge variant={conn.status === 'ACTIVE' ? 'default' : 'outline'}>
                        {conn.status === 'ACTIVE' ? 'Connecte' : conn.status}
                      </Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        Sync: {formatDateTime(conn.last_sync_at)}
                      </p>
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => syncBank.mutate(conn.id)}
                      disabled={syncBank.isPending}
                    >
                      <RefreshCw className={`h-4 w-4 ${syncBank.isPending ? 'animate-spin' : ''}`} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<Landmark className="h-12 w-12" />}
              title="Aucune banque connectee"
              message="Connectez votre banque pour synchroniser automatiquement vos transactions."
              action={{
                label: "Connecter une banque",
                onClick: () => {},
                icon: <Link2 className="h-4 w-4 mr-2" />,
              }}
            />
          )}
        </CardContent>
      </Card>

      {/* Pending Transactions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <GitMerge className="h-5 w-5" />
              Transactions a rapprocher
            </CardTitle>
            <Button
              variant="secondary"
              onClick={() => autoReconcile.mutate()}
              disabled={autoReconcile.isPending}
            >
              <Zap className="h-4 w-4 mr-2" />
              Rapprochement auto
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loadingTransactions ? (
            <LoadingState message="Chargement..." />
          ) : transactions.length > 0 ? (
            <div className="space-y-2">
              {transactions.slice(0, 10).map((tx: BankTransaction) => (
                <div
                  key={tx.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    {toNum(tx.amount) >= 0 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                    <div>
                      <p className="font-medium">{tx.counterparty_name || 'Inconnu'}</p>
                      <p className="text-sm text-muted-foreground">{tx.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-medium ${toNum(tx.amount) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(tx.amount)}
                    </p>
                    <p className="text-xs text-muted-foreground">{formatDate(tx.booking_date)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              Toutes les transactions sont rapprochees
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// ALERTS TAB
// ============================================================================

function AlertsTab() {
  const { data, isLoading } = useAlertList({ is_resolved: false });
  const resolveAlert = useResolveAlert();

  const columns: import('@/types').TableColumn<Alert>[] = [
    {
      id: 'title',
      header: 'Alerte',
      accessor: 'title',
      render: (_value, row) => (
        <div>
          <p className="font-medium">{row.title}</p>
          <p className="text-sm text-muted-foreground line-clamp-1">{row.message}</p>
        </div>
      ),
    },
    {
      id: 'severity',
      header: 'Severite',
      accessor: 'severity',
      render: (_value, row) => <AlertSeverityBadge severity={row.severity} />,
    },
    {
      id: 'created_at',
      header: 'Date',
      accessor: 'created_at',
      render: (_value, row) => formatDateTime(row.created_at),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_value, row) => (
        <div className="flex gap-1">
          {row.document_id && (
            <Button variant="ghost" size="sm">
              <Eye className="h-4 w-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => resolveAlert.mutate({ id: row.id })}
          >
            <CheckCircle className="h-4 w-4 text-green-500" />
          </Button>
        </div>
      ),
    },
  ];

  if (isLoading) {
    return <LoadingState message="Chargement des alertes..." />;
  }

  const items = (data as unknown as { items: Alert[] } | undefined)?.items || [];

  if (items.length === 0) {
    return (
      <EmptyState
        icon={<Bell className="h-12 w-12" />}
        title="Aucune alerte"
        message="Tout est en ordre, aucune alerte a traiter."
      />
    );
  }

  return (
    <DataTable
      data={items}
      columns={columns}
      keyField="id"
    />
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function AutomatedAccountingModule() {
  const { data: dashboard, isLoading } = useM2ADashboard();

  if (isLoading) {
    return (
      <div className="p-6">
        <LoadingState message="Chargement du module..." />
      </div>
    );
  }

  const dashboardData = dashboard as unknown as { stats: StatsCardsProps['stats'] } | undefined;
  const stats = dashboardData?.stats || {
    documents_total: 0,
    documents_pending: 0,
    documents_processed: 0,
    documents_error: 0,
    bank_connections: 0,
    unreconciled_transactions: 0,
    alerts_unread: 0,
    alerts_critical: 0,
    processing_rate: 0,
    confidence_average: 0,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Sparkles className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Comptabilite Automatisee</h1>
            <p className="text-muted-foreground">
              OCR, classification IA et rapprochement bancaire
            </p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <StatsCards stats={stats} />

      {/* Critical Alerts Banner */}
      {stats.alerts_critical > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <span className="font-medium text-red-800">
                {stats.alerts_critical} alerte(s) critique(s) necessite(nt) votre attention
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <Tabs defaultValue="documents">
        <TabsList>
          <TabsTrigger value="documents">
            <FileText className="h-4 w-4 mr-2" />
            Documents
            {stats.documents_pending > 0 && (
              <Badge className="ml-2 bg-orange-100 text-orange-800">{stats.documents_pending}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="bank">
            <Landmark className="h-4 w-4 mr-2" />
            Banque
            {stats.unreconciled_transactions > 0 && (
              <Badge className="ml-2 bg-blue-100 text-blue-800">{stats.unreconciled_transactions}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="alerts">
            <Bell className="h-4 w-4 mr-2" />
            Alertes
            {stats.alerts_unread > 0 && (
              <Badge className="ml-2 bg-red-100 text-red-800">{stats.alerts_unread}</Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="documents" className="mt-6">
          <DocumentsTab />
        </TabsContent>

        <TabsContent value="bank" className="mt-6">
          <BankTab />
        </TabsContent>

        <TabsContent value="alerts" className="mt-6">
          <AlertsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Named exports
export { AutomatedAccountingModule };
export * from './types';
export * from './hooks';
export * from './api';
export { automatedAccountingMeta } from './meta';
