/**
 * AZALSCORE Module - Véhicules
 * ============================
 *
 * Gestion de la flotte de véhicules avec:
 * - Calcul automatique du coût/km (carburant + entretien + assurance + amortissement)
 * - Suivi des émissions CO2
 * - Affectation aux employés
 * - Frais kilométriques liés aux affaires
 *
 * Variables pour future intégration mobile (GPS, ODO auto)
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Car, Fuel, Wrench, Shield, TrendingDown, Leaf,
  Edit, Trash2, ArrowLeft, Save, Calculator, AlertCircle,
  MapPin, Calendar, ChevronDown, X
} from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard, useHasCapability } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ConfirmDialog } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, TableAction, DashboardKPI } from '@/types';
import { isDemoMode } from '../../utils/demoMode';
import './vehicles.css';

// ============================================================
// TYPES
// ============================================================

export type FuelType = 'diesel' | 'essence' | 'electrique' | 'hybride' | 'gpl';

export interface Vehicule {
  id: string;
  immatriculation: string;
  marque: string;
  modele: string;
  type_carburant: FuelType;

  // Consommation
  conso_100km: number;          // L/100km ou kWh/100km
  prix_carburant: number;       // €/L ou €/kWh

  // Entretien
  cout_entretien_km: number;    // €/km
  assurance_mois: number;       // €/mois
  km_mois_estime: number;       // km/mois

  // Amortissement (optionnel)
  prix_achat?: number;
  duree_amort_km?: number;

  // Émissions
  co2_km?: number;              // kg/km (si vide → défaut selon type)
  norme_euro?: string;

  // État
  kilometrage_actuel: number;
  date_mise_service?: string;
  date_derniere_revision?: string;

  // Affectation
  employe_id?: string;
  employe_nom?: string;

  // Statut
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface VehiculeFormData {
  immatriculation: string;
  marque: string;
  modele: string;
  type_carburant: FuelType;
  conso_100km: number;
  prix_carburant: number;
  cout_entretien_km: number;
  assurance_mois: number;
  km_mois_estime: number;
  prix_achat?: number;
  duree_amort_km?: number;
  co2_km?: number;
  norme_euro?: string;
  kilometrage_actuel: number;
  date_mise_service?: string;
  employe_id?: string;
  is_active: boolean;
}

export interface CoutKmDetail {
  carburant: number;
  entretien: number;
  assurance: number;
  amortissement: number;
  total: number;
}

// ============================================================
// CONSTANTES & VALEURS PAR DÉFAUT
// ============================================================

const FUEL_TYPE_LABELS: Record<FuelType, string> = {
  diesel: 'Diesel',
  essence: 'Essence',
  electrique: 'Électrique',
  hybride: 'Hybride',
  gpl: 'GPL',
};

const FUEL_TYPE_ICONS: Record<FuelType, string> = {
  diesel: '⛽',
  essence: '⛽',
  electrique: '⚡',
  hybride: '🔋',
  gpl: '🔵',
};

// Valeurs par défaut si non renseignées (configurables dans Admin)
const DEFAULT_CO2_KM: Record<FuelType, number> = {
  diesel: 0.21,
  essence: 0.19,
  electrique: 0.05,
  hybride: 0.12,
  gpl: 0.16,
};

const DEFAULT_PRIX_KM: Record<FuelType, number> = {
  diesel: 0.45,
  essence: 0.40,
  electrique: 0.25,
  hybride: 0.35,
  gpl: 0.30,
};

// Données de démonstration
const DEMO_VEHICLES: Vehicule[] = [
  {
    id: 'v1',
    immatriculation: 'AB-123-CD',
    marque: 'Renault',
    modele: 'Trafic L2H1',
    type_carburant: 'diesel',
    conso_100km: 8.5,
    prix_carburant: 1.65,
    cout_entretien_km: 0.04,
    assurance_mois: 95,
    km_mois_estime: 2500,
    prix_achat: 32000,
    duree_amort_km: 200000,
    co2_km: 0.195,
    norme_euro: 'Euro 6d',
    kilometrage_actuel: 45230,
    date_mise_service: '2023-03-15',
    date_derniere_revision: '2025-11-20',
    employe_id: 'e1',
    employe_nom: 'Jean Dupont',
    is_active: true,
    created_at: '2023-03-15T00:00:00Z',
    updated_at: '2026-01-15T00:00:00Z',
  },
  {
    id: 'v2',
    immatriculation: 'EF-456-GH',
    marque: 'Peugeot',
    modele: 'Expert',
    type_carburant: 'diesel',
    conso_100km: 7.8,
    prix_carburant: 1.65,
    cout_entretien_km: 0.05,
    assurance_mois: 85,
    km_mois_estime: 2000,
    prix_achat: 28000,
    duree_amort_km: 180000,
    norme_euro: 'Euro 6',
    kilometrage_actuel: 78450,
    date_mise_service: '2022-06-10',
    date_derniere_revision: '2025-09-15',
    employe_id: 'e2',
    employe_nom: 'Marie Martin',
    is_active: true,
    created_at: '2022-06-10T00:00:00Z',
    updated_at: '2026-01-10T00:00:00Z',
  },
  {
    id: 'v3',
    immatriculation: 'IJ-789-KL',
    marque: 'Citroën',
    modele: 'ë-Berlingo',
    type_carburant: 'electrique',
    conso_100km: 21,
    prix_carburant: 0.25,
    cout_entretien_km: 0.02,
    assurance_mois: 70,
    km_mois_estime: 1500,
    prix_achat: 38000,
    duree_amort_km: 250000,
    co2_km: 0.04,
    norme_euro: 'Euro 6d',
    kilometrage_actuel: 12300,
    date_mise_service: '2024-09-01',
    date_derniere_revision: '2025-12-01',
    is_active: true,
    created_at: '2024-09-01T00:00:00Z',
    updated_at: '2026-01-05T00:00:00Z',
  },
  {
    id: 'v4',
    immatriculation: 'MN-012-OP',
    marque: 'Ford',
    modele: 'Transit Custom',
    type_carburant: 'diesel',
    conso_100km: 9.2,
    prix_carburant: 1.65,
    cout_entretien_km: 0.06,
    assurance_mois: 110,
    km_mois_estime: 3000,
    prix_achat: 42000,
    duree_amort_km: 220000,
    norme_euro: 'Euro 6d',
    kilometrage_actuel: 125000,
    date_mise_service: '2021-02-20',
    date_derniere_revision: '2025-08-10',
    employe_id: 'e3',
    employe_nom: 'Pierre Durand',
    is_active: true,
    created_at: '2021-02-20T00:00:00Z',
    updated_at: '2025-12-20T00:00:00Z',
  },
  {
    id: 'v5',
    immatriculation: 'QR-345-ST',
    marque: 'Toyota',
    modele: 'Proace City',
    type_carburant: 'hybride',
    conso_100km: 5.5,
    prix_carburant: 1.75,
    cout_entretien_km: 0.03,
    assurance_mois: 75,
    km_mois_estime: 1800,
    prix_achat: 35000,
    duree_amort_km: 200000,
    co2_km: 0.11,
    norme_euro: 'Euro 6d',
    kilometrage_actuel: 28500,
    date_mise_service: '2024-01-10',
    is_active: true,
    created_at: '2024-01-10T00:00:00Z',
    updated_at: '2026-01-12T00:00:00Z',
  },
];

// ============================================================
// FONCTIONS UTILITAIRES (Exportées pour autres modules)
// ============================================================

export const calculCoutKm = (v: Partial<Vehicule>): CoutKmDetail => {
  const carburant = ((v.conso_100km || 0) / 100) * (v.prix_carburant || 0);
  const entretien = v.cout_entretien_km || 0;
  const assurance = v.km_mois_estime ? (v.assurance_mois || 0) / v.km_mois_estime : 0;
  const amortissement = (v.prix_achat && v.duree_amort_km)
    ? v.prix_achat / v.duree_amort_km
    : 0;

  return {
    carburant,
    entretien,
    assurance,
    amortissement,
    total: carburant + entretien + assurance + amortissement,
  };
};

export const getCO2Km = (v: Partial<Vehicule>): number => {
  if (v.co2_km) return v.co2_km;
  return DEFAULT_CO2_KM[v.type_carburant || 'diesel'];
};

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(amount);
};

// ============================================================
// API HOOKS
// ============================================================

const useVehicules = (page = 1, pageSize = 25) => {
  const demoMode = isDemoMode();

  return useQuery({
    queryKey: ['vehicles', page, pageSize, demoMode],
    queryFn: async () => {
      // En mode démo, retourner les données de démonstration
      if (demoMode) {
        const start = (page - 1) * pageSize;
        const items = DEMO_VEHICLES.slice(start, start + pageSize);
        return { items, total: DEMO_VEHICLES.length };
      }

      try {
        const response = await api.get<PaginatedResponse<Vehicule>>(
          `/v1/fleet/vehicles?page=${page}&page_size=${pageSize}`
        );
        return (response as unknown as PaginatedResponse<Vehicule>) || { items: [], total: 0 };
      } catch (error) {
        // Fallback sur données démo si API échoue
        console.warn('API véhicules non disponible, utilisation des données de démonstration');
        const start = (page - 1) * pageSize;
        const items = DEMO_VEHICLES.slice(start, start + pageSize);
        return { items, total: DEMO_VEHICLES.length };
      }
    },
  });
};

const useVehicule = (id: string) => {
  const demoMode = isDemoMode();

  return useQuery({
    queryKey: ['vehicle', id, demoMode],
    queryFn: async () => {
      // En mode démo, retourner les données de démonstration
      if (demoMode) {
        const vehicule = DEMO_VEHICLES.find(v => v.id === id);
        if (!vehicule) throw new Error('Véhicule non trouvé');
        return vehicule;
      }

      try {
        const response = await api.get<Vehicule>(`/v1/fleet/vehicles/${id}`);
        return response as unknown as Vehicule;
      } catch (error) {
        // Fallback sur données démo si API échoue
        const vehicule = DEMO_VEHICLES.find(v => v.id === id);
        if (vehicule) return vehicule;
        throw error;
      }
    },
    enabled: !!id && id !== 'new',
  });
};

const useCreateVehicule = () => {
  const queryClient = useQueryClient();
  const demoMode = isDemoMode();

  return useMutation({
    mutationFn: async (data: VehiculeFormData) => {
      if (demoMode) {
        // En mode démo, simuler la création
        const newVehicule: Vehicule = {
          ...data,
          id: `demo-${Date.now()}`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        // Ajouter au tableau local pour la session
        DEMO_VEHICLES.unshift(newVehicule);
        return newVehicule;
      }
      const response = await api.post<Vehicule>('/v1/fleet/vehicles', data);
      return response as unknown as Vehicule;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
    },
  });
};

const useUpdateVehicule = () => {
  const queryClient = useQueryClient();
  const demoMode = isDemoMode();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<VehiculeFormData> }) => {
      if (demoMode) {
        // En mode démo, simuler la mise à jour
        const index = DEMO_VEHICLES.findIndex(v => v.id === id);
        if (index >= 0) {
          DEMO_VEHICLES[index] = {
            ...DEMO_VEHICLES[index],
            ...data,
            updated_at: new Date().toISOString(),
          };
          return DEMO_VEHICLES[index];
        }
        throw new Error('Véhicule non trouvé');
      }
      const response = await api.put<Vehicule>(`/v1/fleet/vehicles/${id}`, data);
      return response as unknown as Vehicule;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['vehicle', variables.id] });
    },
  });
};

const useDeleteVehicule = () => {
  const queryClient = useQueryClient();
  const demoMode = isDemoMode();

  return useMutation({
    mutationFn: async (id: string) => {
      if (demoMode) {
        // En mode démo, simuler la suppression
        const index = DEMO_VEHICLES.findIndex(v => v.id === id);
        if (index >= 0) {
          DEMO_VEHICLES.splice(index, 1);
        }
        return id;
      }
      await api.delete(`/v1/fleet/vehicles/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
    },
  });
};

// ============================================================
// COMPOSANTS
// ============================================================

// Affichage du détail coût/km
const CoutKmBreakdown: React.FC<{ vehicule: Partial<Vehicule> }> = ({ vehicule }) => {
  const cout = calculCoutKm(vehicule);
  const total = cout.total || 0.001; // Éviter division par 0

  return (
    <div className="azals-cout-km-breakdown">
      <div className="azals-cout-km-breakdown__header">
        <Calculator size={16} />
        <span>Détail coût/km</span>
        <strong>{formatCurrency(cout.total)}/km</strong>
      </div>
      <div className="azals-cout-km-breakdown__items">
        <div className="azals-cout-km-breakdown__item">
          <Fuel size={14} />
          <span>Carburant</span>
          <span>{formatCurrency(cout.carburant)}</span>
          <span className="percent">{((cout.carburant / total) * 100).toFixed(0)}%</span>
        </div>
        <div className="azals-cout-km-breakdown__item">
          <Wrench size={14} />
          <span>Entretien</span>
          <span>{formatCurrency(cout.entretien)}</span>
          <span className="percent">{((cout.entretien / total) * 100).toFixed(0)}%</span>
        </div>
        <div className="azals-cout-km-breakdown__item">
          <Shield size={14} />
          <span>Assurance</span>
          <span>{formatCurrency(cout.assurance)}</span>
          <span className="percent">{((cout.assurance / total) * 100).toFixed(0)}%</span>
        </div>
        <div className="azals-cout-km-breakdown__item">
          <TrendingDown size={14} />
          <span>Amortissement</span>
          <span>{formatCurrency(cout.amortissement)}</span>
          <span className="percent">{((cout.amortissement / total) * 100).toFixed(0)}%</span>
        </div>
      </div>
      <div className="azals-cout-km-breakdown__co2">
        <Leaf size={14} />
        <span>Émissions CO₂</span>
        <strong>{getCO2Km(vehicule).toFixed(3)} kg/km</strong>
      </div>
    </div>
  );
};

// Sélecteur de véhicule (exportable pour autres modules)
interface VehicleSelectorProps {
  value?: string;
  onChange: (vehiculeId: string | undefined, vehicule?: Vehicule) => void;
  placeholder?: string;
  disabled?: boolean;
}

export const VehicleSelector: React.FC<VehicleSelectorProps> = ({
  value,
  onChange,
  placeholder = 'Sélectionner un véhicule',
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
              {formatCurrency(calculCoutKm(selectedVehicle).total)}/km
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
                Aucun véhicule trouvé
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
                    {formatCurrency(calculCoutKm(v).total)}/km
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

// Formulaire de saisie frais kilométriques (exportable pour Affaires)
interface FraisKmFormProps {
  affaireId?: string;
  affaireNumero?: string;
  onSubmit: (data: FraisKmData) => void;
  onCancel?: () => void;
}

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
      motif: motif || `Déplacement${affaireNumero ? ` - ${affaireNumero}` : ''}`,
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
          <span>Frais kilométriques</span>
        </div>
        {affaireNumero && (
          <span style={{ fontSize: 12, color: 'var(--azals-text-muted)' }}>
            Affaire: {affaireNumero}
          </span>
        )}
      </div>

      <div className="azals-frais-km-form__grid">
        <div className="azals-form-field">
          <label>Véhicule *</label>
          <VehicleSelector
            value={vehiculeId}
            onChange={handleVehiculeChange}
          />
        </div>

        <div className="azals-form-field">
          <label>Kilomètres parcourus *</label>
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
            placeholder="Déplacement chantier..."
          />
        </div>
      </div>

      {selectedVehicule && kmParcourus > 0 && (
        <div className="azals-frais-km-form__summary">
          <div className="azals-frais-km-form__summary-item">
            <div className="azals-frais-km-form__summary-label">Coût/km</div>
            <div className="azals-frais-km-form__summary-value">{formatCurrency(coutKm)}</div>
          </div>
          <div className="azals-frais-km-form__summary-item">
            <div className="azals-frais-km-form__summary-label">Coût total</div>
            <div className="azals-frais-km-form__summary-value">
              {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(coutTotal)}
            </div>
          </div>
          <div className="azals-frais-km-form__summary-item">
            <div className="azals-frais-km-form__summary-label">CO₂ émis</div>
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
// MODULE PRINCIPAL (Navigation interne)
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

  const goToDashboard = useCallback(() => navigateTo('dashboard'), [navigateTo]);
  const goToList = useCallback(() => navigateTo('list'), [navigateTo]);
  const goToDetail = useCallback((id: string) => navigateTo('detail', id), [navigateTo]);
  const goToNew = useCallback(() => navigateTo('form', undefined, false), [navigateTo]);
  const goToEdit = useCallback((id: string) => navigateTo('form', id, true), [navigateTo]);

  switch (navState.view) {
    case 'list':
      return (
        <VehiculesListPageInternal
          onSelectVehicule={goToDetail}
          onNewVehicule={goToNew}
        />
      );
    case 'detail':
      return navState.vehiculeId ? (
        <VehiculeDetailPageInternal
          vehiculeId={navState.vehiculeId}
          onBack={goToList}
          onEdit={goToEdit}
        />
      ) : (
        <VehiculesDashboardInternal onNavigateToList={goToList} onSelectVehicule={goToDetail} onNewVehicule={goToNew} />
      );
    case 'form':
      return (
        <VehiculeFormPageInternal
          vehiculeId={navState.vehiculeId}
          isEdit={navState.isEdit || false}
          onBack={goToList}
          onSuccess={goToList}
        />
      );
    default:
      return (
        <VehiculesDashboardInternal onNavigateToList={goToList} onSelectVehicule={goToDetail} onNewVehicule={goToNew} />
      );
  }
};

// Dashboard interne
const VehiculesDashboardInternal: React.FC<{
  onNavigateToList: () => void;
  onSelectVehicule: (id: string) => void;
  onNewVehicule: () => void;
}> = ({ onNavigateToList, onSelectVehicule, onNewVehicule }) => {
  const { data } = useVehicules(1, 100);
  const canCreate = useHasCapability('fleet.create');

  const stats = useMemo(() => {
    const items = data?.items || [];
    const actifs = items.filter(v => v.is_active);
    const totalKm = items.reduce((sum, v) => sum + (v.kilometrage_actuel || 0), 0);
    const coutMoyen = items.length > 0
      ? items.reduce((sum, v) => sum + calculCoutKm(v).total, 0) / items.length
      : 0;
    const co2Moyen = items.length > 0
      ? items.reduce((sum, v) => sum + getCO2Km(v), 0) / items.length
      : 0;
    return { total: items.length, actifs: actifs.length, totalKm, coutMoyen, co2Moyen };
  }, [data]);

  const kpis: DashboardKPI[] = [
    { id: 'total', label: 'Véhicules', value: stats.total, icon: <Car size={20} /> },
    { id: 'actifs', label: 'Actifs', value: stats.actifs, icon: <Car size={20} /> },
    { id: 'cout', label: 'Coût moyen/km', value: `${stats.coutMoyen.toFixed(3)} €`, icon: <Calculator size={20} /> },
    { id: 'co2', label: 'CO₂ moyen/km', value: `${stats.co2Moyen.toFixed(2)} kg`, icon: <Leaf size={20} /> },
  ];

  return (
    <PageWrapper
      title="Flotte Véhicules"
      subtitle="Gestion des véhicules et frais kilométriques"
      actions={
        canCreate && (
          <Button leftIcon={<Plus size={16} />} onClick={onNewVehicule}>
            Nouveau véhicule
          </Button>
        )
      }
    >
      <section className="azals-section">
        <Grid cols={4} gap="md">
          {kpis.map((kpi) => <KPICard key={kpi.id} kpi={kpi} />)}
        </Grid>
      </section>

      <section className="azals-section">
        <Card
          title="Véhicules récents"
          actions={
            <Button variant="ghost" size="sm" onClick={onNavigateToList}>
              Voir tout
            </Button>
          }
        >
          {data?.items && data.items.length > 0 ? (
            <ul className="azals-simple-list">
              {data.items.slice(0, 5).map((v) => (
                <li key={v.id} onClick={() => onSelectVehicule(v.id)}>
                  <span>{FUEL_TYPE_ICONS[v.type_carburant]} {v.marque} {v.modele}</span>
                  <span className="text-muted">{v.immatriculation}</span>
                  <span>{formatCurrency(calculCoutKm(v).total)}/km</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted text-center py-4">Aucun véhicule enregistré</p>
          )}
        </Card>
      </section>
    </PageWrapper>
  );
};

// Liste interne
const VehiculesListPageInternal: React.FC<{
  onSelectVehicule: (id: string) => void;
  onNewVehicule: () => void;
}> = ({ onSelectVehicule, onNewVehicule }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [deleteTarget, setDeleteTarget] = useState<Vehicule | null>(null);

  const { data, isLoading, refetch } = useVehicules(page, pageSize);
  const deleteVehicule = useDeleteVehicule();
  const canCreate = useHasCapability('fleet.create');
  const canDelete = useHasCapability('fleet.delete');

  const columns: TableColumn<Vehicule>[] = [
    {
      id: 'immatriculation',
      header: 'Immatriculation',
      accessor: 'immatriculation',
      sortable: true,
      render: (value, row) => (
        <span className="azals-link" onClick={() => onSelectVehicule(row.id)}>
          {FUEL_TYPE_ICONS[row.type_carburant]} {value as string}
        </span>
      ),
    },
    {
      id: 'vehicule',
      header: 'Véhicule',
      accessor: 'marque',
      render: (_, row) => `${row.marque} ${row.modele}`,
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'type_carburant',
      render: (value) => FUEL_TYPE_LABELS[value as FuelType],
    },
    {
      id: 'kilometrage',
      header: 'Kilométrage',
      accessor: 'kilometrage_actuel',
      align: 'right',
      render: (value) => `${(value as number).toLocaleString('fr-FR')} km`,
    },
    {
      id: 'cout_km',
      header: 'Coût/km',
      accessor: 'id',
      align: 'right',
      render: (_, row) => formatCurrency(calculCoutKm(row).total),
    },
    {
      id: 'co2_km',
      header: 'CO₂/km',
      accessor: 'id',
      align: 'right',
      render: (_, row) => `${getCO2Km(row).toFixed(2)} kg`,
    },
    {
      id: 'affecte',
      header: 'Affecté à',
      accessor: 'employe_nom',
      render: (value) => value ? String(value) : <span className="text-muted">Pool</span>,
    },
    {
      id: 'statut',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) => (
        <span className={`azals-badge azals-badge--${value ? 'green' : 'gray'}`}>
          {value ? 'Actif' : 'Inactif'}
        </span>
      ),
    },
  ];

  const actions: TableAction<Vehicule>[] = [
    {
      id: 'edit',
      label: 'Modifier',
      icon: 'edit',
      onClick: (row) => onSelectVehicule(row.id),
    },
    {
      id: 'delete',
      label: 'Supprimer',
      icon: 'trash',
      variant: 'danger',
      onClick: (row) => setDeleteTarget(row),
      isHidden: () => !canDelete,
    },
  ];

  return (
    <PageWrapper
      title="Liste des véhicules"
      actions={
        canCreate && (
          <Button leftIcon={<Plus size={16} />} onClick={onNewVehicule}>
            Nouveau véhicule
          </Button>
        )
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          actions={actions}
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage="Aucun véhicule enregistré"
        />
      </Card>

      {deleteTarget && (
        <ConfirmDialog
          title="Supprimer le véhicule"
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

// Formulaire interne
const VehiculeFormPageInternal: React.FC<{
  vehiculeId?: string;
  isEdit: boolean;
  onBack: () => void;
  onSuccess: () => void;
}> = ({ vehiculeId, isEdit, onBack, onSuccess }) => {
  const { data: vehicule, isLoading: loadingVehicule } = useVehicule(vehiculeId || '');
  const createVehicule = useCreateVehicule();
  const updateVehicule = useUpdateVehicule();

  const [formData, setFormData] = useState<VehiculeFormData>({
    immatriculation: '',
    marque: '',
    modele: '',
    type_carburant: 'diesel',
    conso_100km: 7,
    prix_carburant: 1.60,
    cout_entretien_km: 0.05,
    assurance_mois: 80,
    km_mois_estime: 2000,
    kilometrage_actuel: 0,
    is_active: true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  React.useEffect(() => {
    if (vehicule) {
      setFormData({
        immatriculation: vehicule.immatriculation,
        marque: vehicule.marque,
        modele: vehicule.modele,
        type_carburant: vehicule.type_carburant,
        conso_100km: vehicule.conso_100km,
        prix_carburant: vehicule.prix_carburant,
        cout_entretien_km: vehicule.cout_entretien_km,
        assurance_mois: vehicule.assurance_mois,
        km_mois_estime: vehicule.km_mois_estime,
        prix_achat: vehicule.prix_achat,
        duree_amort_km: vehicule.duree_amort_km,
        co2_km: vehicule.co2_km,
        norme_euro: vehicule.norme_euro,
        kilometrage_actuel: vehicule.kilometrage_actuel,
        date_mise_service: vehicule.date_mise_service,
        employe_id: vehicule.employe_id,
        is_active: vehicule.is_active,
      });
    }
  }, [vehicule]);

  const updateField = (field: keyof VehiculeFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!formData.immatriculation.trim()) newErrors.immatriculation = 'Immatriculation requise';
    if (!formData.marque.trim()) newErrors.marque = 'Marque requise';
    if (!formData.modele.trim()) newErrors.modele = 'Modèle requis';
    if (formData.conso_100km <= 0) newErrors.conso_100km = 'Consommation invalide';
    if (formData.prix_carburant <= 0) newErrors.prix_carburant = 'Prix carburant invalide';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      if (isEdit && vehiculeId) {
        await updateVehicule.mutateAsync({ id: vehiculeId, data: formData });
      } else {
        await createVehicule.mutateAsync(formData);
      }
      onSuccess();
    } catch (error) {
      console.error('Save error:', error);
    }
  };

  const isSubmitting = createVehicule.isPending || updateVehicule.isPending;

  if (isEdit && loadingVehicule) {
    return <PageWrapper title="Chargement..."><div className="azals-loading">Chargement...</div></PageWrapper>;
  }

  return (
    <PageWrapper
      title={isEdit ? 'Modifier le véhicule' : 'Nouveau véhicule'}
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <form onSubmit={handleSubmit}>
        <Grid cols={2} gap="lg">
          <div>
            <Card title="Informations générales" className="mb-4">
              <div className="azals-form-field">
                <label>Immatriculation *</label>
                <input
                  type="text"
                  className={`azals-input ${errors.immatriculation ? 'azals-input--error' : ''}`}
                  value={formData.immatriculation}
                  onChange={(e) => updateField('immatriculation', e.target.value.toUpperCase())}
                  placeholder="AB-123-CD"
                />
                {errors.immatriculation && <span className="azals-form-error">{errors.immatriculation}</span>}
              </div>

              <Grid cols={2} gap="md">
                <div className="azals-form-field">
                  <label>Marque *</label>
                  <input
                    type="text"
                    className={`azals-input ${errors.marque ? 'azals-input--error' : ''}`}
                    value={formData.marque}
                    onChange={(e) => updateField('marque', e.target.value)}
                    placeholder="Renault"
                  />
                </div>
                <div className="azals-form-field">
                  <label>Modèle *</label>
                  <input
                    type="text"
                    className={`azals-input ${errors.modele ? 'azals-input--error' : ''}`}
                    value={formData.modele}
                    onChange={(e) => updateField('modele', e.target.value)}
                    placeholder="Trafic"
                  />
                </div>
              </Grid>

              <Grid cols={2} gap="md">
                <div className="azals-form-field">
                  <label>Type de carburant</label>
                  <select
                    className="azals-select"
                    value={formData.type_carburant}
                    onChange={(e) => updateField('type_carburant', e.target.value)}
                  >
                    {Object.entries(FUEL_TYPE_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>{FUEL_TYPE_ICONS[key as FuelType]} {label}</option>
                    ))}
                  </select>
                </div>
                <div className="azals-form-field">
                  <label>Kilométrage actuel</label>
                  <input
                    type="number"
                    className="azals-input"
                    value={formData.kilometrage_actuel}
                    onChange={(e) => updateField('kilometrage_actuel', parseInt(e.target.value) || 0)}
                    min="0"
                  />
                </div>
              </Grid>

              <div className="azals-form-field">
                <label className="azals-checkbox">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => updateField('is_active', e.target.checked)}
                  />
                  <span>Véhicule actif</span>
                </label>
              </div>
            </Card>

            <Card title="Consommation & Carburant" className="mb-4">
              <Grid cols={2} gap="md">
                <div className="azals-form-field">
                  <label>Consommation moyenne *</label>
                  <div className="azals-input-group">
                    <input
                      type="number"
                      className={`azals-input ${errors.conso_100km ? 'azals-input--error' : ''}`}
                      value={formData.conso_100km}
                      onChange={(e) => updateField('conso_100km', parseFloat(e.target.value) || 0)}
                      step="0.1"
                      min="0"
                    />
                    <span className="azals-input-group__suffix">
                      {formData.type_carburant === 'electrique' ? 'kWh/100km' : 'L/100km'}
                    </span>
                  </div>
                </div>
                <div className="azals-form-field">
                  <label>Prix carburant *</label>
                  <div className="azals-input-group">
                    <input
                      type="number"
                      className={`azals-input ${errors.prix_carburant ? 'azals-input--error' : ''}`}
                      value={formData.prix_carburant}
                      onChange={(e) => updateField('prix_carburant', parseFloat(e.target.value) || 0)}
                      step="0.01"
                      min="0"
                    />
                    <span className="azals-input-group__suffix">
                      {formData.type_carburant === 'electrique' ? '€/kWh' : '€/L'}
                    </span>
                  </div>
                </div>
              </Grid>
            </Card>

            <Card title="Entretien & Assurance">
              <Grid cols={2} gap="md">
                <div className="azals-form-field">
                  <label>Coût entretien</label>
                  <div className="azals-input-group">
                    <input
                      type="number"
                      className="azals-input"
                      value={formData.cout_entretien_km}
                      onChange={(e) => updateField('cout_entretien_km', parseFloat(e.target.value) || 0)}
                      step="0.01"
                      min="0"
                    />
                    <span className="azals-input-group__suffix">€/km</span>
                  </div>
                </div>
                <div className="azals-form-field">
                  <label>Assurance mensuelle</label>
                  <div className="azals-input-group">
                    <input
                      type="number"
                      className="azals-input"
                      value={formData.assurance_mois}
                      onChange={(e) => updateField('assurance_mois', parseFloat(e.target.value) || 0)}
                      step="1"
                      min="0"
                    />
                    <span className="azals-input-group__suffix">€/mois</span>
                  </div>
                </div>
              </Grid>

              <div className="azals-form-field">
                <label>Km estimés par mois</label>
                <div className="azals-input-group">
                  <input
                    type="number"
                    className="azals-input"
                    value={formData.km_mois_estime}
                    onChange={(e) => updateField('km_mois_estime', parseInt(e.target.value) || 1)}
                    min="1"
                  />
                  <span className="azals-input-group__suffix">km/mois</span>
                </div>
              </div>
            </Card>
          </div>

          <div>
            <Card title="Calcul du coût kilométrique" className="azals-sticky-card">
              <CoutKmBreakdown vehicule={formData} />

              <div className="azals-form-actions mt-4">
                <Button type="button" variant="ghost" onClick={onBack}>
                  Annuler
                </Button>
                <Button type="submit" leftIcon={<Save size={16} />} isLoading={isSubmitting}>
                  {isEdit ? 'Enregistrer' : 'Créer le véhicule'}
                </Button>
              </div>
            </Card>
          </div>
        </Grid>
      </form>
    </PageWrapper>
  );
};

// Détail interne
const VehiculeDetailPageInternal: React.FC<{
  vehiculeId: string;
  onBack: () => void;
  onEdit: (id: string) => void;
}> = ({ vehiculeId, onBack, onEdit }) => {
  const { data: vehicule, isLoading } = useVehicule(vehiculeId);
  const canEdit = useHasCapability('fleet.edit');

  if (isLoading) {
    return <PageWrapper title="Chargement..."><div className="azals-loading">Chargement...</div></PageWrapper>;
  }

  if (!vehicule) {
    return (
      <PageWrapper title="Véhicule non trouvé">
        <Card>
          <div className="azals-empty">
            <AlertCircle size={48} />
            <p>Ce véhicule n'existe pas ou a été supprimé.</p>
            <Button onClick={onBack}>Retour à la liste</Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={`${vehicule.marque} ${vehicule.modele}`}
      subtitle={vehicule.immatriculation}
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={
        canEdit && (
          <Button leftIcon={<Edit size={16} />} onClick={() => onEdit(vehiculeId)}>
            Modifier
          </Button>
        )
      }
    >
      <Grid cols={3} gap="md" className="mb-4">
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Type</span>
            <span className="azals-stat__value">
              {FUEL_TYPE_ICONS[vehicule.type_carburant]} {FUEL_TYPE_LABELS[vehicule.type_carburant]}
            </span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Kilométrage</span>
            <span className="azals-stat__value">
              {vehicule.kilometrage_actuel.toLocaleString('fr-FR')} km
            </span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Statut</span>
            <span className={`azals-badge azals-badge--${vehicule.is_active ? 'green' : 'gray'}`}>
              {vehicule.is_active ? 'Actif' : 'Inactif'}
            </span>
          </div>
        </Card>
      </Grid>

      <Grid cols={2} gap="lg">
        <Card title="Détail des coûts">
          <CoutKmBreakdown vehicule={vehicule} />
        </Card>

        <Card title="Informations">
          <dl className="azals-dl">
            <dt>Affecté à</dt>
            <dd>{vehicule.employe_nom || 'Pool (non affecté)'}</dd>
            <dt>Mise en service</dt>
            <dd>{vehicule.date_mise_service || '-'}</dd>
            <dt>Norme Euro</dt>
            <dd>{vehicule.norme_euro || '-'}</dd>
            <dt>Dernière révision</dt>
            <dd>{vehicule.date_derniere_revision || '-'}</dd>
          </dl>
        </Card>
      </Grid>
    </PageWrapper>
  );
};

export default VehiculesModule;
