/**
 * AZALSCORE Module - Vehicles Types
 * Types et utilitaires pour la gestion de la flotte vehicules
 */

// ============================================================
// TYPES DE BASE
// ============================================================

export type FuelType = 'diesel' | 'essence' | 'electrique' | 'hybride' | 'gpl';

export type VehicleStatus = 'active' | 'inactive' | 'maintenance' | 'scrapped';

export interface Vehicule {
  id: string;
  immatriculation: string;
  marque: string;
  modele: string;
  type_carburant: FuelType;

  // Consommation
  conso_100km: number;          // L/100km ou kWh/100km
  prix_carburant: number;       // Euro/L ou Euro/kWh

  // Entretien
  cout_entretien_km: number;    // Euro/km
  assurance_mois: number;       // Euro/mois
  km_mois_estime: number;       // km/mois

  // Amortissement (optionnel)
  prix_achat?: number;
  duree_amort_km?: number;

  // Emissions
  co2_km?: number;              // kg/km (si vide -> defaut selon type)
  norme_euro?: string;

  // Etat
  kilometrage_actuel: number;
  date_mise_service?: string;
  date_derniere_revision?: string;
  prochaine_revision?: string;

  // Affectation
  employe_id?: string;
  employe_nom?: string;

  // Statut
  is_active: boolean;
  created_at: string;
  updated_at: string;

  // Relations
  fuel_logs?: FuelLog[];
  maintenance_logs?: MaintenanceLog[];
  mileage_logs?: MileageLog[];
  documents?: VehicleDocument[];
  history?: VehicleHistoryEntry[];
}

export interface FuelLog {
  id: string;
  vehicle_id: string;
  date: string;
  liters: number;
  price_per_liter: number;
  total_cost: number;
  mileage_at_fill: number;
  station?: string;
  full_tank: boolean;
  created_by?: string;
  created_at: string;
}

export interface MaintenanceLog {
  id: string;
  vehicle_id: string;
  date: string;
  type: 'revision' | 'repair' | 'tire_change' | 'inspection' | 'other';
  description: string;
  mileage_at_service: number;
  cost: number;
  provider?: string;
  next_service_mileage?: number;
  next_service_date?: string;
  created_at: string;
}

export interface MileageLog {
  id: string;
  vehicle_id: string;
  date: string;
  km_start: number;
  km_end: number;
  km_total: number;
  motif: string;
  affaire_id?: string;
  affaire_numero?: string;
  employe_id?: string;
  employe_nom?: string;
  cost_total: number;
  co2_total: number;
  created_at: string;
}

export interface VehicleDocument {
  id: string;
  vehicle_id: string;
  type: 'registration' | 'insurance' | 'inspection' | 'manual' | 'other';
  name: string;
  file_url?: string;
  file_size?: number;
  expiry_date?: string;
  created_at: string;
}

export interface VehicleHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

export interface CoutKmDetail {
  carburant: number;
  entretien: number;
  assurance: number;
  amortissement: number;
  total: number;
}

// ============================================================
// CONSTANTES & CONFIGURATIONS
// ============================================================

export const FUEL_TYPE_LABELS: Record<FuelType, string> = {
  diesel: 'Diesel',
  essence: 'Essence',
  electrique: 'Electrique',
  hybride: 'Hybride',
  gpl: 'GPL',
};

export const FUEL_TYPE_ICONS: Record<FuelType, string> = {
  diesel: '⛽',
  essence: '⛽',
  electrique: '⚡',
  hybride: '🔋',
  gpl: '🔵',
};

export const FUEL_TYPE_CONFIG: Record<FuelType, { label: string; icon: string; color: string }> = {
  diesel: { label: 'Diesel', icon: '⛽', color: 'gray' },
  essence: { label: 'Essence', icon: '⛽', color: 'orange' },
  electrique: { label: 'Electrique', icon: '⚡', color: 'green' },
  hybride: { label: 'Hybride', icon: '🔋', color: 'blue' },
  gpl: { label: 'GPL', icon: '🔵', color: 'cyan' },
};

export const VEHICLE_STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  active: { label: 'Actif', color: 'green' },
  inactive: { label: 'Inactif', color: 'gray' },
  maintenance: { label: 'En maintenance', color: 'orange' },
  scrapped: { label: 'Reforme', color: 'red' },
};

export const MAINTENANCE_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  revision: { label: 'Revision', color: 'blue' },
  repair: { label: 'Reparation', color: 'orange' },
  tire_change: { label: 'Pneumatiques', color: 'gray' },
  inspection: { label: 'Controle technique', color: 'purple' },
  other: { label: 'Autre', color: 'gray' },
};

export const DOCUMENT_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  registration: { label: 'Carte grise', color: 'blue' },
  insurance: { label: 'Assurance', color: 'green' },
  inspection: { label: 'Controle technique', color: 'purple' },
  manual: { label: 'Manuel', color: 'gray' },
  other: { label: 'Autre', color: 'gray' },
};

// Valeurs par defaut si non renseignees
export const DEFAULT_CO2_KM: Record<FuelType, number> = {
  diesel: 0.21,
  essence: 0.19,
  electrique: 0.05,
  hybride: 0.12,
  gpl: 0.16,
};

export const DEFAULT_PRIX_KM: Record<FuelType, number> = {
  diesel: 0.45,
  essence: 0.40,
  electrique: 0.25,
  hybride: 0.35,
  gpl: 0.30,
};

// ============================================================
// FONCTIONS UTILITAIRES
// ============================================================

/**
 * Calcul du cout au kilometre detaille
 */
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

/**
 * Obtenir les emissions CO2 par km
 */
export const getCO2Km = (v: Partial<Vehicule>): number => {
  if (v.co2_km) return v.co2_km;
  return DEFAULT_CO2_KM[v.type_carburant || 'diesel'];
};

/**
 * Formatage monnaie (3 decimales pour cout/km)
 */
export const formatCurrencyKm = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(amount);
};

/**
 * Formatage kilometrage
 */
export const formatKilometers = (km: number): string => {
  return `${km.toLocaleString('fr-FR')} km`;
};

/**
 * Calculer la consommation moyenne depuis les logs de carburant
 */
export const calculateAverageConsumption = (vehicle: Vehicule): number | null => {
  const logs = vehicle.fuel_logs?.filter(l => l.full_tank) || [];
  if (logs.length < 2) return null;

  const sorted = [...logs].sort((a, b) => a.mileage_at_fill - b.mileage_at_fill);
  let totalLiters = 0;
  let totalKm = 0;

  for (let i = 1; i < sorted.length; i++) {
    totalLiters += sorted[i].liters;
    totalKm += sorted[i].mileage_at_fill - sorted[i - 1].mileage_at_fill;
  }

  if (totalKm === 0) return null;
  return (totalLiters / totalKm) * 100;
};

/**
 * Calculer le cout total de maintenance
 */
export const getTotalMaintenanceCost = (vehicle: Vehicule): number => {
  return (vehicle.maintenance_logs || []).reduce((sum, log) => sum + log.cost, 0);
};

/**
 * Calculer le total des frais kilometriques
 */
export const getTotalMileageCost = (vehicle: Vehicule): number => {
  return (vehicle.mileage_logs || []).reduce((sum, log) => sum + log.cost_total, 0);
};

/**
 * Calculer les emissions CO2 totales
 */
export const getTotalCO2Emissions = (vehicle: Vehicule): number => {
  return (vehicle.mileage_logs || []).reduce((sum, log) => sum + log.co2_total, 0);
};

/**
 * Verifier si le controle technique expire bientot (30 jours)
 */
export const isInspectionDueSoon = (vehicle: Vehicule): boolean => {
  const inspectionDoc = vehicle.documents?.find(d => d.type === 'inspection');
  if (!inspectionDoc?.expiry_date) return false;

  const expiry = new Date(inspectionDoc.expiry_date);
  const now = new Date();
  const daysUntil = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  return daysUntil <= 30 && daysUntil > 0;
};

/**
 * Verifier si le controle technique est expire
 */
export const isInspectionExpired = (vehicle: Vehicule): boolean => {
  const inspectionDoc = vehicle.documents?.find(d => d.type === 'inspection');
  if (!inspectionDoc?.expiry_date) return false;
  return new Date(inspectionDoc.expiry_date) < new Date();
};

/**
 * Verifier si l'assurance expire bientot (30 jours)
 */
export const isInsuranceDueSoon = (vehicle: Vehicule): boolean => {
  const insuranceDoc = vehicle.documents?.find(d => d.type === 'insurance');
  if (!insuranceDoc?.expiry_date) return false;

  const expiry = new Date(insuranceDoc.expiry_date);
  const now = new Date();
  const daysUntil = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  return daysUntil <= 30 && daysUntil > 0;
};

/**
 * Verifier si la revision est proche
 */
export const isRevisionDueSoon = (vehicle: Vehicule): boolean => {
  // Par date
  if (vehicle.prochaine_revision) {
    const next = new Date(vehicle.prochaine_revision);
    const now = new Date();
    const daysUntil = (next.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
    if (daysUntil <= 30 && daysUntil > 0) return true;
  }

  // Par kilometrage
  const lastMaintenance = vehicle.maintenance_logs?.find(l => l.type === 'revision');
  if (lastMaintenance?.next_service_mileage) {
    const kmUntil = lastMaintenance.next_service_mileage - vehicle.kilometrage_actuel;
    if (kmUntil <= 1000 && kmUntil > 0) return true;
  }

  return false;
};

/**
 * Obtenir les documents expirant bientot
 */
export const getExpiringDocuments = (vehicle: Vehicule): VehicleDocument[] => {
  const now = new Date();
  const thirtyDaysFromNow = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);

  return (vehicle.documents || []).filter(doc => {
    if (!doc.expiry_date) return false;
    const expiry = new Date(doc.expiry_date);
    return expiry <= thirtyDaysFromNow;
  });
};

/**
 * Calculer l'age du vehicule en annees
 */
export const getVehicleAge = (vehicle: Vehicule): number | null => {
  if (!vehicle.date_mise_service) return null;
  const serviceDate = new Date(vehicle.date_mise_service);
  const now = new Date();
  return Math.floor((now.getTime() - serviceDate.getTime()) / (1000 * 60 * 60 * 24 * 365));
};

/**
 * Calculer le kilometrage annuel moyen
 */
export const getAverageYearlyMileage = (vehicle: Vehicule): number | null => {
  const age = getVehicleAge(vehicle);
  if (!age || age === 0) return null;
  return Math.round(vehicle.kilometrage_actuel / age);
};
