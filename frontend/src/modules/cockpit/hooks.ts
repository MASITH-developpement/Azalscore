/**
 * AZALSCORE Module - Cockpit - React Query Hooks
 * Hooks pour le tableau de bord executif
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@core/api-client';

// ============================================================================
// TYPES
// ============================================================================

export interface FluxStats {
  crm: { prospects: number; clients: number; opportunites: number };
  devis: { total: number; en_attente: number; acceptes: number; refuses: number; montant_total: number };
  commandes: { total: number; en_cours: number; livrees: number; montant_total: number };
  ods: { total: number; a_planifier: number; en_cours: number; terminees: number };
  affaires: { total: number; en_cours: number; terminees: number; ca_total: number };
  factures: { total: number; en_attente: number; payees: number; montant_total: number; montant_encaisse: number };
}

export interface RecentItem {
  id: string;
  reference: string;
  label: string;
  type: 'devis' | 'commande' | 'ods' | 'affaire' | 'facture';
  status: string;
  date: string;
  montant?: number;
}

export interface RiskAlert {
  id: string;
  identifier: string;
  partner_name: string;
  score: number;
  level: 'elevated' | 'high';
  level_label: string;
  alerts: string[];
  recommendation: string;
  analyzed_at: string;
}

export interface StrategicKPIData {
  kpi: string;
  value: number;
  unit: string;
  status: string;
  color: string;
  details: Record<string, unknown>;
  recommendations: string[];
}

export interface AllStrategicKPIs {
  cash_runway: StrategicKPIData;
  profit_margin: StrategicKPIData;
  customer_concentration: StrategicKPIData;
  working_capital: StrategicKPIData;
  employee_productivity: StrategicKPIData;
  generated_at: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

interface DocumentItem {
  id: string;
  reference: string;
  customer_name?: string;
  status: string;
  created_at: string;
  total?: number;
  subtotal?: number;
}

interface InterventionItem {
  id: string;
  reference: string;
  title?: string;
  status: string;
  created_at: string;
}

interface ProjectItem {
  id: string;
  reference: string;
  name?: string;
  status: string;
  budget_total?: number;
}

interface OpportunityItem {
  id: string;
  name: string;
  status: string;
}

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const cockpitKeys = {
  all: ['cockpit'] as const,
  stats: () => [...cockpitKeys.all, 'stats'] as const,
  recent: () => [...cockpitKeys.all, 'recent'] as const,
  riskAlerts: () => [...cockpitKeys.all, 'risk-alerts'] as const,
  strategicKPIs: () => [...cockpitKeys.all, 'strategic-kpis'] as const,
};

// ============================================================================
// HOOKS
// ============================================================================

export const useCockpitStats = () => {
  return useQuery({
    queryKey: cockpitKeys.stats(),
    queryFn: async () => {
      const [
        customersRes,
        opportunitiesRes,
        devisRes,
        commandesRes,
        interventionsRes,
        projectsRes,
        facturesRes,
      ] = await Promise.all([
        api.get('/commercial/customers?page_size=1').catch(() => ({ total: 0, items: [] })) as Promise<PaginatedResponse<unknown>>,
        api.get('/commercial/opportunities?page_size=100').catch(() => ({ total: 0, items: [] })) as Promise<PaginatedResponse<OpportunityItem>>,
        api.get('/commercial/documents?type=QUOTE&page_size=100').catch(() => ({ total: 0, items: [] })) as Promise<PaginatedResponse<DocumentItem>>,
        api.get('/commercial/documents?type=ORDER&page_size=100').catch(() => ({ total: 0, items: [] })) as Promise<PaginatedResponse<DocumentItem>>,
        api.get('/interventions?page_size=100').catch(() => ({ total: 0, items: [] })) as Promise<PaginatedResponse<InterventionItem>>,
        api.get('/projects?limit=200').catch(() => ({ total: 0, items: [] })) as Promise<PaginatedResponse<ProjectItem>>,
        api.get('/commercial/documents?type=INVOICE&page_size=100').catch(() => ({ total: 0, items: [] })) as Promise<PaginatedResponse<DocumentItem>>,
      ]);

      const opportunities = opportunitiesRes.items || [];
      const devis = devisRes.items || [];
      const commandes = commandesRes.items || [];
      const interventions = interventionsRes.items || [];
      const projects = projectsRes.items || [];
      const factures = facturesRes.items || [];

      const stats: FluxStats = {
        crm: {
          prospects: customersRes.total || 0,
          clients: customersRes.total || 0,
          opportunites: opportunities.length,
        },
        devis: {
          total: devis.length,
          en_attente: devis.filter((d) => d.status === 'DRAFT' || d.status === 'SENT').length,
          acceptes: devis.filter((d) => d.status === 'ACCEPTED').length,
          refuses: devis.filter((d) => d.status === 'REJECTED').length,
          montant_total: devis.reduce((sum, d) => sum + Number(d.total || d.subtotal || 0), 0),
        },
        commandes: {
          total: commandes.length,
          en_cours: commandes.filter((c) => c.status === 'CONFIRMED' || c.status === 'IN_PROGRESS').length,
          livrees: commandes.filter((c) => c.status === 'DELIVERED').length,
          montant_total: commandes.reduce((sum, c) => sum + Number(c.total || c.subtotal || 0), 0),
        },
        ods: {
          total: interventions.length,
          a_planifier: interventions.filter((i) => i.status === 'A_PLANIFIER').length,
          en_cours: interventions.filter((i) => i.status === 'EN_COURS').length,
          terminees: interventions.filter((i) => i.status === 'TERMINEE').length,
        },
        affaires: {
          total: projects.length,
          en_cours: projects.filter((p) => p.status === 'EN_COURS').length,
          terminees: projects.filter((p) => p.status === 'TERMINE').length,
          ca_total: projects.reduce((sum, p) => sum + Number(p.budget_total || 0), 0),
        },
        factures: {
          total: factures.length,
          en_attente: factures.filter((f) => f.status === 'DRAFT' || f.status === 'SENT').length,
          payees: factures.filter((f) => f.status === 'PAID').length,
          montant_total: factures.reduce((sum, f) => sum + Number(f.total || f.subtotal || 0), 0),
          montant_encaisse: factures
            .filter((f) => f.status === 'PAID')
            .reduce((sum: number, f) => sum + Number(f.total || f.subtotal || 0), 0),
        },
      };

      return stats;
    },
    refetchInterval: 60000,
  });
};

export const useRecentActivity = () => {
  return useQuery({
    queryKey: cockpitKeys.recent(),
    queryFn: async () => {
      const [devisRes, commandesRes, interventionsRes, facturesRes] = await Promise.all([
        api.get('/commercial/documents?type=QUOTE&page_size=5').catch(() => ({ items: [], total: 0 })) as Promise<PaginatedResponse<DocumentItem>>,
        api.get('/commercial/documents?type=ORDER&page_size=5').catch(() => ({ items: [], total: 0 })) as Promise<PaginatedResponse<DocumentItem>>,
        api.get('/interventions?page_size=5').catch(() => ({ items: [], total: 0 })) as Promise<PaginatedResponse<InterventionItem>>,
        api.get('/commercial/documents?type=INVOICE&page_size=5').catch(() => ({ items: [], total: 0 })) as Promise<PaginatedResponse<DocumentItem>>,
      ]);

      const items: RecentItem[] = [];

      const devisList = devisRes.items || [];
      const commandesList = commandesRes.items || [];
      const interventionsList = interventionsRes.items || [];
      const facturesList = facturesRes.items || [];

      devisList.forEach((d) => {
        items.push({ id: d.id || '', reference: d.reference || '', label: d.customer_name || 'Client', type: 'devis', status: d.status || '', date: d.created_at || '', montant: d.total || d.subtotal });
      });

      commandesList.forEach((c) => {
        items.push({ id: c.id || '', reference: c.reference || '', label: c.customer_name || 'Client', type: 'commande', status: c.status || '', date: c.created_at || '', montant: c.total || c.subtotal });
      });

      interventionsList.forEach((i) => {
        items.push({ id: i.id || '', reference: i.reference || '', label: i.title || 'Intervention', type: 'ods', status: i.status || '', date: i.created_at || '' });
      });

      facturesList.forEach((f) => {
        items.push({ id: f.id || '', reference: f.reference || '', label: f.customer_name || 'Client', type: 'facture', status: f.status || '', date: f.created_at || '', montant: f.total || f.subtotal });
      });

      items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      return items.slice(0, 10);
    },
  });
};

export const useRiskAlerts = () => {
  return useQuery({
    queryKey: cockpitKeys.riskAlerts(),
    queryFn: async (): Promise<RiskAlert[]> => {
      try {
        const response = await api.get('/enrichment/risk/alerts');
        return (response as unknown as RiskAlert[]) || [];
      } catch {
        return [];
      }
    },
    refetchInterval: 300000,
  });
};

export const useStrategicKPIs = () => {
  return useQuery({
    queryKey: cockpitKeys.strategicKPIs(),
    queryFn: async (): Promise<AllStrategicKPIs | null> => {
      try {
        const response = await api.get('/cockpit/helpers/all-strategic');
        return response as unknown as AllStrategicKPIs;
      } catch {
        return null;
      }
    },
    refetchInterval: 300000,
  });
};

// ============================================================================
// DEFAULT STATS
// ============================================================================

export const DEFAULT_STATS: FluxStats = {
  crm: { prospects: 0, clients: 0, opportunites: 0 },
  devis: { total: 0, en_attente: 0, acceptes: 0, refuses: 0, montant_total: 0 },
  commandes: { total: 0, en_cours: 0, livrees: 0, montant_total: 0 },
  ods: { total: 0, a_planifier: 0, en_cours: 0, terminees: 0 },
  affaires: { total: 0, en_cours: 0, terminees: 0, ca_total: 0 },
  factures: { total: 0, en_attente: 0, payees: 0, montant_total: 0, montant_encaisse: 0 },
};
