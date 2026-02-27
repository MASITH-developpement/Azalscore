// @ts-nocheck
/**
 * AZALSCORE Module - Shipping
 * Interface principale du module d'expedition
 */

import React, { useState } from 'react';
import { Button } from '@ui/actions';
import { Card, PageWrapper, Grid } from '@ui/layout';
import { Input, Select } from '@ui/forms';
import { DataTable } from '@ui/tables';
import { LoadingState, EmptyState } from '@ui/components/StateViews';
import type { TableColumn } from '@/types';
import {
  Truck,
  Package,
  DollarSign,
  RotateCcw,
  MapPin,
  Plus,
  Search,
  Eye,
  Printer,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  FileText,
  ExternalLink,
} from 'lucide-react';
import {
  useShippingDashboard,
  useShipmentList,
  useCarriers,
  useRates,
  useReturnList,
  usePickupPoints,
  useGenerateLabel,
  useCancelShipment,
  useApproveReturn,
  useRejectReturn,
} from './hooks';
import type {
  Shipment,
  Carrier,
  ShippingRate,
  Return,
  PickupPoint,
  ShipmentStatus,
  CarrierType,
  ReturnStatus,
} from './types';
import {
  SHIPMENT_STATUS_CONFIG,
  CARRIER_TYPE_CONFIG,
  RETURN_STATUS_CONFIG,
  SHIPPING_METHOD_CONFIG,
} from './types';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ variant?: string; className?: string; children: React.ReactNode }> = ({ variant = 'default', className = '', children }) => (
  <span className={`azals-badge azals-badge--${variant} ${className}`}>{children}</span>
);

const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
);

// Simple Tabs components
const Tabs: React.FC<{ defaultValue: string; children: React.ReactNode }> = ({ defaultValue, children }) => {
  const [activeTab, setActiveTab] = useState(defaultValue);
  return (
    <div className="azals-tabs">
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

// ============================================================================
// HELPERS
// ============================================================================

function toNum(value: number | string | undefined): number {
  if (value === undefined || value === null) return 0;
  if (typeof value === 'number') return value;
  return parseFloat(value) || 0;
}

function formatDate(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
}

// ============================================================================
// STATUS BADGES
// ============================================================================

interface ShipmentStatusBadgeProps {
  status: ShipmentStatus;
}

function ShipmentStatusBadge({ status }: ShipmentStatusBadgeProps) {
  const config = SHIPMENT_STATUS_CONFIG[status];
  const colorMap: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-800',
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-red-100 text-red-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    purple: 'bg-purple-100 text-purple-800',
  };

  return (
    <Badge className={colorMap[config.color] || colorMap.gray}>
      {config.label}
    </Badge>
  );
}

interface ReturnStatusBadgeProps {
  status: ReturnStatus;
}

function ReturnStatusBadge({ status }: ReturnStatusBadgeProps) {
  const config = RETURN_STATUS_CONFIG[status];
  const colorMap: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-800',
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-red-100 text-red-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    purple: 'bg-purple-100 text-purple-800',
  };

  return (
    <Badge className={colorMap[config.color] || colorMap.gray}>
      {config.label}
    </Badge>
  );
}

// ============================================================================
// STATS CARDS
// ============================================================================

interface StatsCardsProps {
  stats: {
    total_shipments: number;
    in_transit: number;
    delivered_today: number;
    pending_returns: number;
  };
}

function StatsCards({ stats }: StatsCardsProps) {
  return (
    <Grid cols={4} gap="md">
      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Package className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Expeditions</p>
            <p className="text-2xl font-bold">{stats.total_shipments}</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-orange-100 rounded-lg">
            <Truck className="h-5 w-5 text-orange-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">En transit</p>
            <p className="text-2xl font-bold">{stats.in_transit}</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Livrees</p>
            <p className="text-2xl font-bold">{stats.delivered_today}</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <RotateCcw className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Retours</p>
            <p className="text-2xl font-bold">{stats.pending_returns}</p>
          </div>
        </div>
      </Card>
    </Grid>
  );
}

// ============================================================================
// SHIPMENTS TAB
// ============================================================================

function ShipmentsTab() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading } = useShipmentList({
    search: search || undefined,
    status: (statusFilter || undefined) as ShipmentStatus | undefined,
  });

  const generateLabel = useGenerateLabel();
  const cancelShipment = useCancelShipment();

  const columns: TableColumn<Shipment>[] = [
    {
      id: 'shipment_number',
      header: 'N Expedition',
      accessor: 'shipment_number',
      render: (_, row) => (
        <span className="font-mono font-medium">{row.shipment_number}</span>
      ),
    },
    {
      id: 'carrier_name',
      header: 'Transporteur',
      accessor: 'carrier_name',
      render: (_, row) => (
        <div className="flex items-center gap-2">
          <Truck className="h-4 w-4" />
          {row.carrier_name}
        </div>
      ),
    },
    {
      id: 'recipient_name',
      header: 'Destinataire',
      accessor: 'recipient_name',
      render: (_, row) => (
        <div>
          <p className="font-medium">{row.recipient_name}</p>
          <p className="text-sm text-muted-foreground">{row.recipient_city}</p>
        </div>
      ),
    },
    {
      id: 'tracking_number',
      header: 'N Suivi',
      accessor: 'tracking_number',
      render: (_, row) => (
        <div className="flex items-center gap-1">
          <span className="font-mono text-sm">{row.tracking_number || '-'}</span>
          {row.tracking_url && (
            <a href={row.tracking_url} target="_blank" rel="noopener noreferrer" className="p-1 hover:bg-gray-100 rounded">
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      ),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (_, row) => <ShipmentStatusBadge status={row.status} />,
    },
    {
      id: 'shipping_cost',
      header: 'Cout',
      accessor: 'shipping_cost',
      render: (_, row) => `${toNum(row.shipping_cost).toFixed(2)} EUR`,
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          <Button variant="ghost" size="sm">
            <Eye className="h-4 w-4" />
          </Button>
          {row.status === 'confirmed' && !row.label_url && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => generateLabel.mutate(row.id)}
            >
              <Printer className="h-4 w-4" />
            </Button>
          )}
          {row.label_url && (
            <a href={row.label_url} target="_blank" rel="noopener noreferrer">
              <Button variant="ghost" size="sm">
                <FileText className="h-4 w-4" />
              </Button>
            </a>
          )}
          {['draft', 'confirmed'].includes(row.status) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => cancelShipment.mutate({ id: row.id })}
            >
              <XCircle className="h-4 w-4 text-red-500" />
            </Button>
          )}
        </div>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            
            placeholder="Rechercher une expedition..."
            value={search}
            onChange={(value) => setSearch(String(value))}
          />
        </div>
        <Select
          
          value={statusFilter}
          onChange={(value) => setStatusFilter(String(value))}
          options={[
            { value: '', label: 'Tous les statuts' },
            ...Object.entries(SHIPMENT_STATUS_CONFIG).map(([key, { label }]) => ({ value: key, label }))
          ]}
        />
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Nouvelle expedition
        </Button>
      </div>

      {data?.items && data.items.length > 0 ? (
        <DataTable
          data={data.items}
          columns={columns}
          keyField="id"
        />
      ) : (
        <EmptyState
          icon={<Package className="h-12 w-12" />}
          title="Aucune expedition"
          message="Creez votre premiere expedition pour commencer."
          action={{
            label: 'Creer une expedition',
            onClick: () => {},
            icon: <Plus className="h-4 w-4" />,
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// CARRIERS TAB
// ============================================================================

function CarriersTab() {
  const { data: carriers, isLoading } = useCarriers();

  const columns: TableColumn<Carrier>[] = [
    {
      id: 'name',
      header: 'Transporteur',
      accessor: 'name',
      render: (_, row) => (
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded bg-gray-100 flex items-center justify-center">
            <Truck className="h-5 w-5" />
          </div>
          <div>
            <p className="font-medium">{row.name}</p>
            <p className="text-sm text-muted-foreground">{row.code}</p>
          </div>
        </div>
      ),
    },
    {
      id: 'carrier_type',
      header: 'Type',
      accessor: 'carrier_type',
      render: (_, row) => (
        <Badge variant="secondary">
          {CARRIER_TYPE_CONFIG[row.carrier_type]?.label || row.carrier_type}
        </Badge>
      ),
    },
    {
      id: 'api_integration',
      header: 'API',
      accessor: 'api_integration',
      render: (_, row) => (
        <Badge variant={row.api_integration ? 'default' : 'secondary'}>
          {row.api_integration ? 'Connecte' : 'Manuel'}
        </Badge>
      ),
    },
    {
      id: 'tracking_integration',
      header: 'Tracking',
      accessor: 'tracking_integration',
      render: (_, row) => (
        <Badge variant={row.tracking_integration ? 'default' : 'secondary'}>
          {row.tracking_integration ? 'Oui' : 'Non'}
        </Badge>
      ),
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (_, row) => (
        <Badge variant={row.is_active ? 'default' : 'secondary'}>
          {row.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      ),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: () => (
        <Button variant="ghost" size="sm">
          <Eye className="h-4 w-4" />
        </Button>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!carriers || carriers.length === 0) {
    return (
      <EmptyState
        icon={<Truck className="h-12 w-12" />}
        title="Aucun transporteur"
        message="Configurez vos transporteurs pour commencer les expeditions."
        action={{
          label: 'Ajouter un transporteur',
          onClick: () => {},
          icon: <Plus className="h-4 w-4" />,
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Ajouter un transporteur
        </Button>
      </div>
      <DataTable
        data={carriers}
        columns={columns}
        keyField="id"
      />
    </div>
  );
}

// ============================================================================
// RATES TAB
// ============================================================================

function RatesTab() {
  const { data: rates, isLoading } = useRates();

  const columns: TableColumn<ShippingRate>[] = [
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      render: (_, row) => (
        <div>
          <p className="font-medium">{row.name}</p>
          <p className="text-sm text-muted-foreground">{row.carrier_name}</p>
        </div>
      ),
    },
    {
      id: 'zone_name',
      header: 'Zone',
      accessor: 'zone_name',
    },
    {
      id: 'shipping_method',
      header: 'Methode',
      accessor: 'shipping_method',
      render: (_, row) => (
        <Badge variant="secondary">
          {SHIPPING_METHOD_CONFIG[row.shipping_method]?.label || row.shipping_method}
        </Badge>
      ),
    },
    {
      id: 'base_price',
      header: 'Prix de base',
      accessor: 'base_price',
      render: (_, row) => `${toNum(row.base_price).toFixed(2)} EUR`,
    },
    {
      id: 'price_per_kg',
      header: 'Prix/kg',
      accessor: 'price_per_kg',
      render: (_, row) => `${toNum(row.price_per_kg).toFixed(2)} EUR`,
    },
    {
      id: 'free_shipping_threshold',
      header: 'Franco',
      accessor: 'free_shipping_threshold',
      render: (_, row) => row.free_shipping_threshold
        ? `${toNum(row.free_shipping_threshold).toFixed(0)} EUR`
        : '-',
    },
    {
      id: 'estimated_days',
      header: 'Delai',
      accessor: 'estimated_days_min',
      render: (_, row) => (
        <span>
          {row.estimated_days_min}-{row.estimated_days_max} jours
        </span>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!rates || rates.length === 0) {
    return (
      <EmptyState
        icon={<DollarSign className="h-12 w-12" />}
        title="Aucun tarif"
        message="Configurez vos tarifs d'expedition par zone et transporteur."
        action={{
          label: 'Creer un tarif',
          onClick: () => {},
          icon: <Plus className="h-4 w-4" />,
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Nouveau tarif
        </Button>
      </div>
      <DataTable
        data={rates}
        columns={columns}
        keyField="id"
      />
    </div>
  );
}

// ============================================================================
// RETURNS TAB
// ============================================================================

function ReturnsTab() {
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading } = useReturnList({
    status: (statusFilter || undefined) as ReturnStatus | undefined,
  });

  const approveReturn = useApproveReturn();
  const rejectReturn = useRejectReturn();

  const columns: TableColumn<Return>[] = [
    {
      id: 'return_number',
      header: 'N Retour',
      accessor: 'return_number',
      render: (_, row) => (
        <span className="font-mono font-medium">{row.return_number}</span>
      ),
    },
    {
      id: 'shipment_number',
      header: 'Expedition',
      accessor: 'shipment_number',
    },
    {
      id: 'customer_name',
      header: 'Client',
      accessor: 'customer_name',
    },
    {
      id: 'reason',
      header: 'Raison',
      accessor: 'reason',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (_, row) => <ReturnStatusBadge status={row.status} />,
    },
    {
      id: 'refund_amount',
      header: 'Remboursement',
      accessor: 'refund_amount',
      render: (_, row) => row.refund_amount
        ? `${toNum(row.refund_amount).toFixed(2)} EUR`
        : '-',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          <Button variant="ghost" size="sm">
            <Eye className="h-4 w-4" />
          </Button>
          {row.status === 'requested' && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => approveReturn.mutate({ id: row.id })}
              >
                <CheckCircle className="h-4 w-4 text-green-500" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => rejectReturn.mutate({ id: row.id, reason: 'Refuse' })}
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
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Select
          
          value={statusFilter}
          onChange={(value) => setStatusFilter(String(value))}
          options={[
            { value: '', label: 'Tous les statuts' },
            ...Object.entries(RETURN_STATUS_CONFIG).map(([key, { label }]) => ({ value: key, label }))
          ]}
        />
      </div>

      {data?.items && data.items.length > 0 ? (
        <DataTable
          data={data.items}
          columns={columns}
          keyField="id"
        />
      ) : (
        <EmptyState
          icon={<RotateCcw className="h-12 w-12" />}
          title="Aucun retour"
          message="Aucune demande de retour pour le moment."
        />
      )}
    </div>
  );
}

// ============================================================================
// PICKUP POINTS TAB
// ============================================================================

function PickupPointsTab() {
  const [search, setSearch] = useState('');
  const { data: pickupPoints, isLoading } = usePickupPoints();

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  const filteredPoints = pickupPoints?.filter(pp =>
    !search ||
    pp.name.toLowerCase().includes(search.toLowerCase()) ||
    pp.city?.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            
            placeholder="Rechercher un point relais..."
            value={search}
            onChange={(value) => setSearch(String(value))}
          />
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Ajouter un point
        </Button>
      </div>

      {filteredPoints.length > 0 ? (
        <Grid cols={3} gap="md">
          {filteredPoints.map((pp) => (
            <Card key={pp.id}>
              <div className="p-4 flex items-start gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <MapPin className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium">{pp.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {pp.address}, {pp.postal_code} {pp.city}
                  </p>
                  <div className="flex gap-2 mt-2">
                    <Badge variant="secondary">{pp.carrier_name}</Badge>
                    {pp.is_active && <Badge>Actif</Badge>}
                  </div>
                  {pp.opening_hours && (
                    <p className="text-xs text-muted-foreground mt-2">
                      <Clock className="h-3 w-3 inline mr-1" />
                      {pp.opening_hours}
                    </p>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </Grid>
      ) : (
        <EmptyState
          icon={<MapPin className="h-12 w-12" />}
          title="Aucun point relais"
          message="Ajoutez des points relais pour proposer plus d'options de livraison."
          action={{
            label: 'Ajouter un point relais',
            onClick: () => {},
            icon: <Plus className="h-4 w-4" />,
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function ShippingModule() {
  const { data: dashboard, isLoading } = useShippingDashboard();

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <Grid cols={4} gap="md">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </Grid>
        <Skeleton className="h-96" />
      </div>
    );
  }

  const stats = dashboard?.stats || {
    total_shipments: 0,
    in_transit: 0,
    delivered_today: 0,
    pending_returns: 0,
  };

  return (
    <PageWrapper
      title="Expeditions"
      subtitle="Gestion des expeditions, transporteurs et retours"
      actions={
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Nouvelle expedition
        </Button>
      }
    >
      <div className="space-y-6">
        <StatsCards stats={stats} />

        <Tabs defaultValue="shipments">
          <TabsList>
            <TabsTrigger value="shipments">
              <Package className="h-4 w-4 mr-2" />
              Expeditions
            </TabsTrigger>
            <TabsTrigger value="carriers">
              <Truck className="h-4 w-4 mr-2" />
              Transporteurs
            </TabsTrigger>
            <TabsTrigger value="rates">
              <DollarSign className="h-4 w-4 mr-2" />
              Tarifs
            </TabsTrigger>
            <TabsTrigger value="returns">
              <RotateCcw className="h-4 w-4 mr-2" />
              Retours
              {stats.pending_returns > 0 && (
                <Badge className="ml-2 bg-orange-100 text-orange-800">{stats.pending_returns}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="pickup-points">
              <MapPin className="h-4 w-4 mr-2" />
              Points relais
            </TabsTrigger>
          </TabsList>

          <TabsContent value="shipments" className="mt-6">
            <ShipmentsTab />
          </TabsContent>

          <TabsContent value="carriers" className="mt-6">
            <CarriersTab />
          </TabsContent>

          <TabsContent value="rates" className="mt-6">
            <RatesTab />
          </TabsContent>

          <TabsContent value="returns" className="mt-6">
            <ReturnsTab />
          </TabsContent>

          <TabsContent value="pickup-points" className="mt-6">
            <PickupPointsTab />
          </TabsContent>
        </Tabs>
      </div>
    </PageWrapper>
  );
}

// Named exports
export { ShippingModule };
export * from './types';
export * from './hooks';
export * from './api';
export { shippingMeta } from './meta';
