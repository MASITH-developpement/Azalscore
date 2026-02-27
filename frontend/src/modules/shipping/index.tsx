/**
 * AZALSCORE Module - Shipping
 * Interface principale du module d'expedition
 */

import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  DataTable,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Input,
  Select,
  Skeleton,
  EmptyState,
} from '@/ui-engine';
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
  Navigation,
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

function formatDateTime(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleString('fr-FR');
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
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Package className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Expeditions</p>
              <p className="text-2xl font-bold">{stats.total_shipments}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Truck className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">En transit</p>
              <p className="text-2xl font-bold">{stats.in_transit}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Livrees</p>
              <p className="text-2xl font-bold">{stats.delivered_today}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <RotateCcw className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Retours</p>
              <p className="text-2xl font-bold">{stats.pending_returns}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// SHIPMENTS TAB
// ============================================================================

function ShipmentsTab() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ShipmentStatus | ''>('');

  const { data, isLoading } = useShipmentList({
    search: search || undefined,
    status: statusFilter || undefined,
  });

  const generateLabel = useGenerateLabel();
  const cancelShipment = useCancelShipment();

  const columns = [
    {
      header: 'N° Expedition',
      accessorKey: 'shipment_number' as const,
      cell: (row: Shipment) => (
        <span className="font-mono font-medium">{row.shipment_number}</span>
      ),
    },
    {
      header: 'Transporteur',
      accessorKey: 'carrier_name' as const,
      cell: (row: Shipment) => (
        <div className="flex items-center gap-2">
          <Truck className="h-4 w-4" />
          {row.carrier_name}
        </div>
      ),
    },
    {
      header: 'Destinataire',
      accessorKey: 'recipient_name' as const,
      cell: (row: Shipment) => (
        <div>
          <p className="font-medium">{row.recipient_name}</p>
          <p className="text-sm text-muted-foreground">{row.recipient_city}</p>
        </div>
      ),
    },
    {
      header: 'N° Suivi',
      accessorKey: 'tracking_number' as const,
      cell: (row: Shipment) => (
        <div className="flex items-center gap-1">
          <span className="font-mono text-sm">{row.tracking_number || '-'}</span>
          {row.tracking_url && (
            <Button variant="ghost" size="sm" className="p-1" asChild>
              <a href={row.tracking_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3 w-3" />
              </a>
            </Button>
          )}
        </div>
      ),
    },
    {
      header: 'Statut',
      accessorKey: 'status' as const,
      cell: (row: Shipment) => <ShipmentStatusBadge status={row.status} />,
    },
    {
      header: 'Cout',
      accessorKey: 'shipping_cost' as const,
      cell: (row: Shipment) => `${toNum(row.shipping_cost).toFixed(2)} EUR`,
    },
    {
      header: 'Actions',
      accessorKey: 'id' as const,
      cell: (row: Shipment) => (
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
            <Button variant="ghost" size="sm" asChild>
              <a href={row.label_url} target="_blank" rel="noopener noreferrer">
                <FileText className="h-4 w-4" />
              </a>
            </Button>
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
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select
          value={statusFilter}
          onValueChange={(value) => setStatusFilter(value as ShipmentStatus | '')}
        >
          <option value="">Tous les statuts</option>
          {Object.entries(SHIPMENT_STATUS_CONFIG).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </Select>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
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
          description="Creez votre premiere expedition pour commencer."
          action={
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Creer une expedition
            </Button>
          }
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

  const columns = [
    {
      header: 'Transporteur',
      accessorKey: 'name' as const,
      cell: (row: Carrier) => (
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
      header: 'Type',
      accessorKey: 'carrier_type' as const,
      cell: (row: Carrier) => (
        <Badge variant="outline">
          {CARRIER_TYPE_CONFIG[row.carrier_type]?.label || row.carrier_type}
        </Badge>
      ),
    },
    {
      header: 'API',
      accessorKey: 'api_integration' as const,
      cell: (row: Carrier) => (
        <Badge variant={row.api_integration ? 'default' : 'outline'}>
          {row.api_integration ? 'Connecte' : 'Manuel'}
        </Badge>
      ),
    },
    {
      header: 'Tracking',
      accessorKey: 'tracking_integration' as const,
      cell: (row: Carrier) => (
        <Badge variant={row.tracking_integration ? 'default' : 'outline'}>
          {row.tracking_integration ? 'Oui' : 'Non'}
        </Badge>
      ),
    },
    {
      header: 'Statut',
      accessorKey: 'is_active' as const,
      cell: (row: Carrier) => (
        <Badge variant={row.is_active ? 'default' : 'outline'}>
          {row.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      ),
    },
    {
      header: 'Actions',
      accessorKey: 'id' as const,
      cell: () => (
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
        description="Configurez vos transporteurs pour commencer les expeditions."
        action={
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Ajouter un transporteur
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button>
          <Plus className="h-4 w-4 mr-2" />
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

  const columns = [
    {
      header: 'Nom',
      accessorKey: 'name' as const,
      cell: (row: ShippingRate) => (
        <div>
          <p className="font-medium">{row.name}</p>
          <p className="text-sm text-muted-foreground">{row.carrier_name}</p>
        </div>
      ),
    },
    {
      header: 'Zone',
      accessorKey: 'zone_name' as const,
    },
    {
      header: 'Methode',
      accessorKey: 'shipping_method' as const,
      cell: (row: ShippingRate) => (
        <Badge variant="outline">
          {SHIPPING_METHOD_CONFIG[row.shipping_method]?.label || row.shipping_method}
        </Badge>
      ),
    },
    {
      header: 'Prix de base',
      accessorKey: 'base_price' as const,
      cell: (row: ShippingRate) => `${toNum(row.base_price).toFixed(2)} EUR`,
    },
    {
      header: 'Prix/kg',
      accessorKey: 'price_per_kg' as const,
      cell: (row: ShippingRate) => `${toNum(row.price_per_kg).toFixed(2)} EUR`,
    },
    {
      header: 'Franco',
      accessorKey: 'free_shipping_threshold' as const,
      cell: (row: ShippingRate) => row.free_shipping_threshold
        ? `${toNum(row.free_shipping_threshold).toFixed(0)} EUR`
        : '-',
    },
    {
      header: 'Delai',
      accessorKey: 'estimated_days_min' as const,
      cell: (row: ShippingRate) => (
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
        description="Configurez vos tarifs d'expedition par zone et transporteur."
        action={
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Creer un tarif
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button>
          <Plus className="h-4 w-4 mr-2" />
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
  const [statusFilter, setStatusFilter] = useState<ReturnStatus | ''>('');

  const { data, isLoading } = useReturnList({
    status: statusFilter || undefined,
  });

  const approveReturn = useApproveReturn();
  const rejectReturn = useRejectReturn();

  const columns = [
    {
      header: 'N° Retour',
      accessorKey: 'return_number' as const,
      cell: (row: Return) => (
        <span className="font-mono font-medium">{row.return_number}</span>
      ),
    },
    {
      header: 'Expedition',
      accessorKey: 'shipment_number' as const,
    },
    {
      header: 'Client',
      accessorKey: 'customer_name' as const,
    },
    {
      header: 'Raison',
      accessorKey: 'reason' as const,
    },
    {
      header: 'Statut',
      accessorKey: 'status' as const,
      cell: (row: Return) => <ReturnStatusBadge status={row.status} />,
    },
    {
      header: 'Remboursement',
      accessorKey: 'refund_amount' as const,
      cell: (row: Return) => row.refund_amount
        ? `${toNum(row.refund_amount).toFixed(2)} EUR`
        : '-',
    },
    {
      header: 'Actions',
      accessorKey: 'id' as const,
      cell: (row: Return) => (
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
          onValueChange={(value) => setStatusFilter(value as ReturnStatus | '')}
          className="w-48"
        >
          <option value="">Tous les statuts</option>
          {Object.entries(RETURN_STATUS_CONFIG).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </Select>
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
          description="Aucune demande de retour pour le moment."
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
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Ajouter un point
        </Button>
      </div>

      {filteredPoints.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPoints.map((pp) => (
            <Card key={pp.id}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <MapPin className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium">{pp.name}</h3>
                    <p className="text-sm text-muted-foreground">
                      {pp.address}, {pp.postal_code} {pp.city}
                    </p>
                    <div className="flex gap-2 mt-2">
                      <Badge variant="outline">{pp.carrier_name}</Badge>
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
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<MapPin className="h-12 w-12" />}
          title="Aucun point relais"
          description="Ajoutez des points relais pour proposer plus d'options de livraison."
          action={
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Ajouter un point relais
            </Button>
          }
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
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
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
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Truck className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Expeditions</h1>
            <p className="text-muted-foreground">
              Gestion des expeditions, transporteurs et retours
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nouvelle expedition
          </Button>
        </div>
      </div>

      {/* Stats */}
      <StatsCards stats={stats} />

      {/* Main Content */}
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
  );
}

// Named exports
export { ShippingModule };
export * from './types';
export * from './hooks';
export * from './api';
export { shippingMeta } from './meta';
