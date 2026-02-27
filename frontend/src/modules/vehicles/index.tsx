/**
 * AZALSCORE Module - Vehicules
 * ============================
 *
 * Gestion de la flotte de vehicules avec:
 * - Calcul automatique du cout/km (carburant + entretien + assurance + amortissement)
 * - Suivi des emissions CO2
 * - Affectation aux employes
 * - Frais kilometriques lies aux affaires
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  Plus, Car, Fuel, Wrench, Shield, TrendingDown, Leaf,
  Edit, Save, Calculator, AlertCircle,
  ChevronDown, X, FileText, Clock, Sparkles
} from 'lucide-react';
import { useHasCapability } from '@core/capabilities';
import { Button, ConfirmDialog } from '@ui/actions';
import { LoadingState } from '@ui/components/StateViews';
import { KPICard } from '@ui/dashboards';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { BaseViewStandard } from '@ui/standards';
import { DataTable } from '@ui/tables';
import type { TableColumn, TableAction, DashboardKPI } from '@/types';
import { formatCurrency } from '@/utils/formatters';

// Internal imports
import {
  VehicleInfoTab, VehicleCostsTab, VehicleFuelTab,
  VehicleDocsTab, VehicleHistoryTab, VehicleIATab
} from './components';
import {
  calculCoutKm, getCO2Km, formatCurrencyKm, formatKilometers,
  FUEL_TYPE_LABELS, FUEL_TYPE_ICONS, FUEL_TYPE_CONFIG
} from './types';
import { useVehicules, useVehicule, useDeleteVehicule } from './hooks';
import type { Vehicule, FuelType } from './types';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition, SemanticColor } from '@ui/standards';
import './vehicles.css';

// ============================================================
// COMPOSANTS UTILITAIRES (Exportes)
// ============================================================

interface VehicleSelectorProps {
  value?: string;
  onChange: (vehiculeId: string | undefined, vehicule?: Vehicule) => void;
  placeholder?: string;
  disabled?: boolean;
}

export const VehicleSelector: React.FC<VehicleSelectorProps> = ({
  value,
  onChange,
  placeholder = 'Selectionner un vehicule',
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const { data } = useVehicules(1, 100);

  const vehicles = data?.items || [];
  const selectedVehicle = vehicles.find(v => v.id === value);

  const filteredVehicles = useMemo(() => {
    if (!search) return vehicles;
    const lowerSearch = search.toLowerCase();
    return vehicles.filter(v =>
      v.immatriculation.toLowerCase().includes(lowerSearch) ||
      v.marque.toLowerCase().includes(lowerSearch) ||
      v.modele.toLowerCase().includes(lowerSearch)
    );
  }, [vehicles, search]);

  const handleSelect = useCallback((vehicule: Vehicule) => {
    onChange(vehicule.id, vehicule);
    setIsOpen(false);
    setSearch('');
  }, [onChange]);

  const handleClear = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(undefined);
  }, [onChange]);

  return (
    <div className="azals-vehicle-selector">
      <button
        type="button"
        className="azals-vehicle-selector__trigger"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
      >
        {selectedVehicle ? (
          <>
            <span>{FUEL_TYPE_ICONS[selectedVehicle.type_carburant]}</span>
            <span style={{ flex: 1 }}>
              {selectedVehicle.marque} {selectedVehicle.modele} ({selectedVehicle.immatriculation})
            </span>
            <span style={{ color: 'var(--azals-primary)', fontWeight: 500 }}>
              {formatCurrencyKm(calculCoutKm(selectedVehicle).total)}/km
            </span>
            <button type="button" onClick={handleClear} style={{ padding: 4 }}>
              <X size={14} />
            </button>
          </>
        ) : (
          <>
            <Car size={16} />
            <span className="azals-vehicle-selector__placeholder">{placeholder}</span>
            <ChevronDown size={16} />
          </>
        )}
      </button>

      {isOpen && (
        <div className="azals-vehicle-selector__dropdown">
          <div className="azals-vehicle-selector__search">
            <input
              type="text"
              placeholder="Rechercher..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>
          <div className="azals-vehicle-selector__list">
            {filteredVehicles.length === 0 ? (
              <div style={{ padding: '12px', textAlign: 'center', color: 'var(--azals-text-muted)' }}>
                Aucun vehicule trouve
              </div>
            ) : (
              filteredVehicles.map((v) => (
                <div
                  key={v.id}
                  className={`azals-vehicle-selector__item ${value === v.id ? 'azals-vehicle-selector__item--selected' : ''}`}
                  onClick={() => handleSelect(v)}
                >
                  <span style={{ marginRight: 8 }}>{FUEL_TYPE_ICONS[v.type_carburant]}</span>
                  <span style={{ flex: 1 }}>
                    <strong>{v.marque} {v.modele}</strong>
                    <span style={{ marginLeft: 8, color: 'var(--azals-text-muted)' }}>{v.immatriculation}</span>
                  </span>
                  <span style={{ color: 'var(--azals-primary)' }}>
                    {formatCurrencyKm(calculCoutKm(v).total)}/km
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Formulaire de saisie frais kilometriques
export interface FraisKmData {
  vehicule_id: string;
  vehicule_immat: string;
  km_parcourus: number;
  date: string;
  motif: string;
  cout_total: number;
  co2_total: number;
  affaire_id?: string;
}

interface FraisKmFormProps {
  affaireId?: string;
  affaireNumero?: string;
  onSubmit: (data: FraisKmData) => void;
  onCancel?: () => void;
}

export const FraisKmForm: React.FC<FraisKmFormProps> = ({
  affaireId,
  affaireNumero,
  onSubmit,
  onCancel,
}) => {
  const [vehiculeId, setVehiculeId] = useState<string>();
  const [selectedVehicule, setSelectedVehicule] = useState<Vehicule>();
  const [kmParcourus, setKmParcourus] = useState<number>(0);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [motif, setMotif] = useState('');

  const handleVehiculeChange = useCallback((id: string | undefined, vehicule?: Vehicule) => {
    setVehiculeId(id);
    setSelectedVehicule(vehicule);
  }, []);

  const coutKm = selectedVehicule ? calculCoutKm(selectedVehicule).total : 0;
  const co2Km = selectedVehicule ? getCO2Km(selectedVehicule) : 0;
  const coutTotal = kmParcourus * coutKm;
  const co2Total = kmParcourus * co2Km;

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!vehiculeId || !selectedVehicule || kmParcourus <= 0) return;

    onSubmit({
      vehicule_id: vehiculeId,
      vehicule_immat: selectedVehicule.immatriculation,
      km_parcourus: kmParcourus,
      date,
      motif: motif || `Deplacement${affaireNumero ? ` - ${affaireNumero}` : ''}`,
      cout_total: coutTotal,
      co2_total: co2Total,
      affaire_id: affaireId,
    });
  }, [vehiculeId, selectedVehicule, kmParcourus, date, motif, coutTotal, co2Total, affaireId, affaireNumero, onSubmit]);

  return (
    <form className="azals-frais-km-form" onSubmit={handleSubmit}>
      <div className="azals-frais-km-form__header">
        <div className="azals-frais-km-form__title">
          <Car size={18} />
          <span>Frais kilometriques</span>
        </div>
        {affaireNumero && (
          <span style={{ fontSize: 12, color: 'var(--azals-text-muted)' }}>
            Affaire: {affaireNumero}
          </span>
        )}
      </div>

      <div className="azals-frais-km-form__grid">
        <div className="azals-form-field">
          <label>Vehicule *</label>
          <VehicleSelector value={vehiculeId} onChange={handleVehiculeChange} />
        </div>

        <div className="azals-form-field">
          <label>Kilometres parcourus *</label>
          <div className="azals-input-group">
            <input
              type="number"
              className="azals-input"
              value={kmParcourus || ''}
              onChange={(e) => setKmParcourus(parseInt(e.target.value) || 0)}
              min="1"
              required
            />
            <span className="azals-input-group__suffix">km</span>
          </div>
        </div>

        <div className="azals-form-field">
          <label>Date</label>
          <input
            type="date"
            className="azals-input"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>

        <div className="azals-form-field">
          <label>Motif / Description</label>
          <input
            type="text"
            className="azals-input"
            value={motif}
            onChange={(e) => setMotif(e.target.value)}
            placeholder="Deplacement chantier..."
          />
        </div>
      </div>

      {selectedVehicule && kmParcourus > 0 && (
        <div className="azals-frais-km-form__summary">
          <div className="azals-frais-km-form__summary-item">
            <div className="azals-frais-km-form__summary-label">Cout/km</div>
            <div className="azals-frais-km-form__summary-value">{formatCurrencyKm(coutKm)}</div>
          </div>
          <div className="azals-frais-km-form__summary-item">
            <div className="azals-frais-km-form__summary-label">Cout total</div>
            <div className="azals-frais-km-form__summary-value">{formatCurrency(coutTotal)}</div>
          </div>
          <div className="azals-frais-km-form__summary-item">
            <div className="azals-frais-km-form__summary-label">CO2 emis</div>
            <div className="azals-frais-km-form__summary-value" style={{ color: 'var(--azals-success)' }}>
              {co2Total.toFixed(2)} kg
            </div>
          </div>
        </div>
      )}

      <div className="azals-frais-km-form__actions">
        {onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel}>
            Annuler
          </Button>
        )}
        <Button
          type="submit"
          disabled={!vehiculeId || kmParcourus <= 0}
          leftIcon={<Save size={16} />}
        >
          Enregistrer
        </Button>
      </div>
    </form>
  );
};

// ============================================================
// VEHICLE DETAIL VIEW
// ============================================================

interface VehicleDetailViewProps {
  vehicleId: string;
  onBack: () => void;
  onEdit: (id: string) => void;
}

const VehicleDetailView: React.FC<VehicleDetailViewProps> = ({ vehicleId, onBack, onEdit }) => {
  const { data: vehicle, isLoading, error, refetch } = useVehicule(vehicleId);
  const canEdit = useHasCapability('fleet.edit');

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <LoadingState onRetry={() => refetch()} message="Chargement du vehicule..." />
      </PageWrapper>
    );
  }

  if (error || !vehicle) {
    return (
      <PageWrapper title="Vehicule non trouve">
        <Card>
          <div className="azals-empty">
            <AlertCircle size={48} />
            <p>Ce vehicule n'existe pas ou a ete supprime.</p>
            <Button onClick={onBack}>Retour a la liste</Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  const coutKm = calculCoutKm(vehicle);
  const co2Km = getCO2Km(vehicle);
  const fuelConfig = FUEL_TYPE_CONFIG[vehicle.type_carburant];

  const tabs: TabDefinition<Vehicule>[] = [
    { id: 'info', label: 'Informations', icon: <Car size={16} />, component: VehicleInfoTab },
    { id: 'costs', label: 'Couts', icon: <Calculator size={16} />, component: VehicleCostsTab },
    { id: 'fuel', label: 'Carburant', icon: <Fuel size={16} />, badge: vehicle.fuel_logs?.length, component: VehicleFuelTab },
    { id: 'docs', label: 'Documents', icon: <FileText size={16} />, badge: vehicle.documents?.length, component: VehicleDocsTab },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: VehicleHistoryTab },
    { id: 'ia', label: 'IA', icon: <Sparkles size={16} />, component: VehicleIATab },
  ];

  const infoBarItems: InfoBarItem[] = [
    { id: 'cost-km', label: 'Cout/km', value: formatCurrencyKm(coutKm.total), valueColor: coutKm.total < 0.40 ? 'green' : coutKm.total < 0.55 ? 'orange' : 'red' },
    { id: 'mileage', label: 'Kilometrage', value: formatKilometers(vehicle.kilometrage_actuel), valueColor: 'blue' as SemanticColor },
    { id: 'co2', label: 'CO2/km', value: `${co2Km.toFixed(2)} kg`, valueColor: co2Km < 0.10 ? 'green' : co2Km < 0.18 ? 'orange' : 'red' },
    { id: 'fuel-type', label: 'Carburant', value: `${FUEL_TYPE_ICONS[vehicle.type_carburant]} ${fuelConfig.label}`, valueColor: fuelConfig.color as SemanticColor },
  ];

  const sidebarSections: SidebarSection[] = [
    {
      id: 'identification', title: 'Identification',
      items: [
        { id: 'immat', label: 'Immatriculation', value: vehicle.immatriculation },
        { id: 'marque', label: 'Marque', value: vehicle.marque },
        { id: 'modele', label: 'Modele', value: vehicle.modele },
        { id: 'norme', label: 'Norme Euro', value: vehicle.norme_euro || '-' },
      ],
    },
    {
      id: 'costs', title: 'Couts detailles',
      items: [
        { id: 'fuel-cost', label: 'Carburant', value: formatCurrencyKm(coutKm.carburant) + '/km' },
        { id: 'maintenance-cost', label: 'Entretien', value: formatCurrencyKm(coutKm.entretien) + '/km' },
        { id: 'insurance-cost', label: 'Assurance', value: formatCurrencyKm(coutKm.assurance) + '/km' },
        { id: 'amort-cost', label: 'Amortissement', value: formatCurrencyKm(coutKm.amortissement) + '/km' },
        { id: 'total-cost', label: 'Total', value: formatCurrencyKm(coutKm.total) + '/km', highlight: true },
      ],
    },
    {
      id: 'assignment', title: 'Affectation',
      items: [
        { id: 'driver', label: 'Conducteur', value: vehicle.employe_nom || 'Pool' },
        { id: 'km-month', label: 'Km/mois estime', value: formatKilometers(vehicle.km_mois_estime) },
      ],
    },
  ];

  const headerActions: ActionDefinition[] = [
    { id: 'back', label: 'Retour', variant: 'ghost', onClick: onBack },
    ...(canEdit ? [{ id: 'edit', label: 'Modifier', icon: <Edit size={16} />, onClick: () => onEdit(vehicleId) }] : []),
  ];

  return (
    <BaseViewStandard<Vehicule>
      title={`${vehicle.marque} ${vehicle.modele}`}
      subtitle={vehicle.immatriculation}
      status={{ label: vehicle.is_active ? 'Actif' : 'Inactif', color: vehicle.is_active ? 'green' : 'gray' }}
      data={vehicle}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
    />
  );
};

// ============================================================
// DASHBOARD
// ============================================================

const VehiculesDashboard: React.FC<{
  onNavigateToList: () => void;
  onSelectVehicule: (id: string) => void;
  onNewVehicule: () => void;
}> = ({ onNavigateToList, onSelectVehicule, onNewVehicule }) => {
  const { data } = useVehicules(1, 100);
  const canCreate = useHasCapability('fleet.create');

  const stats = useMemo(() => {
    const items = data?.items || [];
    const actifs = items.filter(v => v.is_active);
    const coutMoyen = items.length > 0
      ? items.reduce((sum, v) => sum + calculCoutKm(v).total, 0) / items.length
      : 0;
    const co2Moyen = items.length > 0
      ? items.reduce((sum, v) => sum + getCO2Km(v), 0) / items.length
      : 0;
    return { total: items.length, actifs: actifs.length, coutMoyen, co2Moyen };
  }, [data]);

  const kpis: DashboardKPI[] = [
    { id: 'total', label: 'Vehicules', value: stats.total, icon: <Car size={20} /> },
    { id: 'actifs', label: 'Actifs', value: stats.actifs, icon: <Car size={20} /> },
    { id: 'cout', label: 'Cout moyen/km', value: `${stats.coutMoyen.toFixed(3)} Euro`, icon: <Calculator size={20} /> },
    { id: 'co2', label: 'CO2 moyen/km', value: `${stats.co2Moyen.toFixed(2)} kg`, icon: <Leaf size={20} /> },
  ];

  return (
    <PageWrapper
      title="Flotte Vehicules"
      subtitle="Gestion des vehicules et frais kilometriques"
      actions={canCreate && <Button leftIcon={<Plus size={16} />} onClick={onNewVehicule}>Nouveau vehicule</Button>}
    >
      <section className="azals-section">
        <Grid cols={4} gap="md">
          {kpis.map((kpi) => <KPICard key={kpi.id} kpi={kpi} />)}
        </Grid>
      </section>
      <section className="azals-section">
        <Card title="Vehicules recents" actions={<Button variant="ghost" size="sm" onClick={onNavigateToList}>Voir tout</Button>}>
          {data?.items && data.items.length > 0 ? (
            <ul className="azals-simple-list">
              {data.items.slice(0, 5).map((v) => (
                <li key={v.id} onClick={() => onSelectVehicule(v.id)}>
                  <span>{FUEL_TYPE_ICONS[v.type_carburant]} {v.marque} {v.modele}</span>
                  <span className="text-muted">{v.immatriculation}</span>
                  <span>{formatCurrencyKm(calculCoutKm(v).total)}/km</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted text-center py-4">Aucun vehicule enregistre</p>
          )}
        </Card>
      </section>
    </PageWrapper>
  );
};

// ============================================================
// LIST PAGE
// ============================================================

const VehiculesListPage: React.FC<{
  onSelectVehicule: (id: string) => void;
  onNewVehicule: () => void;
}> = ({ onSelectVehicule, onNewVehicule }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [deleteTarget, setDeleteTarget] = useState<Vehicule | null>(null);

  const { data, isLoading, error, refetch } = useVehicules(page, pageSize);
  const deleteVehicule = useDeleteVehicule();
  const canCreate = useHasCapability('fleet.create');
  const canDelete = useHasCapability('fleet.delete');

  const columns: TableColumn<Vehicule>[] = [
    {
      id: 'immatriculation', header: 'Immatriculation', accessor: 'immatriculation', sortable: true,
      render: (value, row) => (
        <span className="azals-link" onClick={() => onSelectVehicule(row.id)}>
          {FUEL_TYPE_ICONS[row.type_carburant]} {value as string}
        </span>
      ),
    },
    { id: 'vehicule', header: 'Vehicule', accessor: 'marque', render: (_, row) => `${row.marque} ${row.modele}` },
    { id: 'type', header: 'Type', accessor: 'type_carburant', render: (value) => FUEL_TYPE_LABELS[value as FuelType] },
    { id: 'kilometrage', header: 'Kilometrage', accessor: 'kilometrage_actuel', align: 'right', render: (value) => formatKilometers(value as number) },
    { id: 'cout_km', header: 'Cout/km', accessor: 'id', align: 'right', render: (_, row) => formatCurrencyKm(calculCoutKm(row).total) },
    { id: 'co2_km', header: 'CO2/km', accessor: 'id', align: 'right', render: (_, row) => `${getCO2Km(row).toFixed(2)} kg` },
    { id: 'affecte', header: 'Affecte a', accessor: 'employe_nom', render: (value) => value ? String(value) : <span className="text-muted">Pool</span> },
    {
      id: 'statut', header: 'Statut', accessor: 'is_active',
      render: (value) => <span className={`azals-badge azals-badge--${value ? 'green' : 'gray'}`}>{value ? 'Actif' : 'Inactif'}</span>,
    },
  ];

  const actions: TableAction<Vehicule>[] = [
    { id: 'edit', label: 'Modifier', icon: 'edit', onClick: (row) => onSelectVehicule(row.id) },
    { id: 'delete', label: 'Supprimer', icon: 'trash', variant: 'danger', onClick: (row) => setDeleteTarget(row), isHidden: () => !canDelete },
  ];

  return (
    <PageWrapper
      title="Liste des vehicules"
      actions={canCreate && <Button leftIcon={<Plus size={16} />} onClick={onNewVehicule}>Nouveau vehicule</Button>}
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          actions={actions}
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
          pagination={{ page, pageSize, total: data?.total || 0, onPageChange: setPage, onPageSizeChange: setPageSize }}
          onRefresh={refetch}
          onRetry={() => refetch()}
          emptyMessage="Aucun vehicule enregistre"
        />
      </Card>

      {deleteTarget && (
        <ConfirmDialog
          title="Supprimer le vehicule"
          message={`Voulez-vous supprimer ${deleteTarget.marque} ${deleteTarget.modele} (${deleteTarget.immatriculation}) ?`}
          variant="danger"
          onConfirm={async () => {
            await deleteVehicule.mutateAsync(deleteTarget.id);
            setDeleteTarget(null);
          }}
          onCancel={() => setDeleteTarget(null)}
          isLoading={deleteVehicule.isPending}
        />
      )}
    </PageWrapper>
  );
};

// ============================================================
// FORM PAGE (Placeholder)
// ============================================================

const VehiculeFormPage: React.FC<{
  vehiculeId?: string;
  isEdit: boolean;
  onBack: () => void;
  onSuccess: () => void;
}> = ({ vehiculeId: _vehiculeId, isEdit, onBack, onSuccess: _onSuccess }) => {
  return (
    <PageWrapper title={isEdit ? 'Modifier le vehicule' : 'Nouveau vehicule'} backAction={{ label: 'Retour', onClick: onBack }}>
      <Card>
        <div className="azals-empty">
          <Car size={48} />
          <p>Formulaire en cours de migration</p>
          <Button onClick={onBack}>Retour</Button>
        </div>
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// MODULE PRINCIPAL
// ============================================================

type VehiculeView = 'dashboard' | 'list' | 'detail' | 'form';

interface VehiculeNavState {
  view: VehiculeView;
  vehiculeId?: string;
  isEdit?: boolean;
}

export const VehiculesModule: React.FC = () => {
  const [navState, setNavState] = useState<VehiculeNavState>({ view: 'dashboard' });

  const navigateTo = useCallback((view: VehiculeView, vehiculeId?: string, isEdit?: boolean) => {
    setNavState({ view, vehiculeId, isEdit });
  }, []);

  const goToList = useCallback(() => navigateTo('list'), [navigateTo]);
  const goToDetail = useCallback((id: string) => navigateTo('detail', id), [navigateTo]);
  const goToNew = useCallback(() => navigateTo('form', undefined, false), [navigateTo]);
  const goToEdit = useCallback((id: string) => navigateTo('form', id, true), [navigateTo]);

  switch (navState.view) {
    case 'list':
      return <VehiculesListPage onSelectVehicule={goToDetail} onNewVehicule={goToNew} />;
    case 'detail':
      return navState.vehiculeId ? (
        <VehicleDetailView vehicleId={navState.vehiculeId} onBack={goToList} onEdit={goToEdit} />
      ) : (
        <VehiculesDashboard onNavigateToList={goToList} onSelectVehicule={goToDetail} onNewVehicule={goToNew} />
      );
    case 'form':
      return <VehiculeFormPage vehiculeId={navState.vehiculeId} isEdit={navState.isEdit || false} onBack={goToList} onSuccess={goToList} />;
    default:
      return <VehiculesDashboard onNavigateToList={goToList} onSelectVehicule={goToDetail} onNewVehicule={goToNew} />;
  }
};

// ============================================================
// RE-EXPORTS
// ============================================================

export { calculCoutKm, getCO2Km } from './types';
export type { Vehicule, FuelType, CoutKmDetail } from './types';
export * from './hooks';
export default VehiculesModule;
