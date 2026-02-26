/**
 * AZALSCORE Module - Cockpit
 * ==========================
 *
 * Vue globale du flux commercial avec suivi en temps reel.
 * Tableau de bord executif montrant le pipeline commercial.
 *
 * Flux: CRM -> DEV -> COM/ODS -> AFF -> FAC/AVO -> CPT
 */

import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { clsx } from 'clsx';
import {
  Users, FileText, Package, Wrench, Briefcase, Receipt, Calculator,
  TrendingUp, TrendingDown, ArrowRight, RefreshCw, Eye,
  Clock, CheckCircle2, Euro, Calendar, ChevronRight, Activity,
  ShieldAlert
} from 'lucide-react';
import { api } from '@core/api-client';
import { COLORS } from '@core/design-tokens';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { ErrorState } from '../../ui-engine/components/StateViews';
import '../../styles/cockpit.css';

// ============================================================
// TYPES
// ============================================================

interface FluxStats {
  crm: { prospects: number; clients: number; opportunites: number };
  devis: { total: number; en_attente: number; acceptes: number; refuses: number; montant_total: number };
  commandes: { total: number; en_cours: number; livrees: number; montant_total: number };
  ods: { total: number; a_planifier: number; en_cours: number; terminees: number };
  affaires: { total: number; en_cours: number; terminees: number; ca_total: number };
  factures: { total: number; en_attente: number; payees: number; montant_total: number; montant_encaisse: number };
}

interface RecentItem {
  id: string;
  reference: string;
  label: string;
  type: 'devis' | 'commande' | 'ods' | 'affaire' | 'facture';
  status: string;
  date: string;
  montant?: number;
}

interface RiskAlert {
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

// Types pour les reponses API paginées
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

// ============================================================
// CONSTANTES
// ============================================================

const FLUX_STEPS = [
  { id: 'crm', label: 'CRM', icon: Users, color: COLORS.crm, description: 'Prospects & Clients' },
  { id: 'devis', label: 'Devis', icon: FileText, color: COLORS.devis, description: 'Propositions' },
  { id: 'commandes', label: 'Commandes', icon: Package, color: COLORS.commandes, description: 'Commandes client' },
  { id: 'ordres-service', label: 'ODS', icon: Wrench, color: COLORS.ods, description: 'Interventions' },
  { id: 'affaires', label: 'Affaires', icon: Briefcase, color: COLORS.affaires, description: 'Projets' },
  { id: 'factures', label: 'Factures', icon: Receipt, color: COLORS.factures, description: 'Facturation' },
] as const;

// ============================================================
// HELPERS
// ============================================================

const formatCurrency = (amount?: number): string => {
  if (amount === undefined || amount === null) return '-';
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
};

const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

// Navigation cross-module
const navigateToModule = (module: string, params?: Record<string, string>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', {
    detail: { view: module, params }
  }));
};

// Keyboard handler for interactive elements
const handleKeyActivate = (callback: () => void) => (e: React.KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    callback();
  }
};

// ============================================================
// API HOOKS
// ============================================================

const useCockpitStats = () => {
  return useQuery({
    queryKey: ['cockpit-stats'],
    queryFn: async () => {
      // Recuperer les stats de chaque module
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

      // DEBUG: Log pour debugger les montants
      console.log('[COCKPIT DEBUG] facturesRes:', facturesRes);
      console.log('[COCKPIT DEBUG] factures count:', factures.length);
      if (factures.length > 0) {
        console.log('[COCKPIT DEBUG] first facture:', factures[0]);
        console.log('[COCKPIT DEBUG] first facture total:', factures[0]?.total, 'type:', typeof factures[0]?.total);
      }

      // Calculer les stats
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
    refetchInterval: 60000, // Refresh toutes les minutes
  });
};

const useRecentActivity = () => {
  return useQuery({
    queryKey: ['cockpit-recent'],
    queryFn: async () => {
      // Recuperer les items recents de chaque module
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

      // Ajouter les devis
      devisList.forEach((d) => {
        items.push({
          id: d.id || '',
          reference: d.reference || '',
          label: d.customer_name || 'Client',
          type: 'devis',
          status: d.status || '',
          date: d.created_at || '',
          montant: d.total || d.subtotal,
        });
      });

      // Ajouter les commandes
      commandesList.forEach((c) => {
        items.push({
          id: c.id || '',
          reference: c.reference || '',
          label: c.customer_name || 'Client',
          type: 'commande',
          status: c.status || '',
          date: c.created_at || '',
          montant: c.total || c.subtotal,
        });
      });

      // Ajouter les interventions
      interventionsList.forEach((i) => {
        items.push({
          id: i.id || '',
          reference: i.reference || '',
          label: i.title || 'Intervention',
          type: 'ods',
          status: i.status || '',
          date: i.created_at || '',
        });
      });

      // Ajouter les factures
      facturesList.forEach((f) => {
        items.push({
          id: f.id || '',
          reference: f.reference || '',
          label: f.customer_name || 'Client',
          type: 'facture',
          status: f.status || '',
          date: f.created_at || '',
          montant: f.total || f.subtotal,
        });
      });

      // Trier par date
      items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

      return items.slice(0, 10);
    },
  });
};

const useRiskAlerts = () => {
  return useQuery({
    queryKey: ['cockpit-risk-alerts'],
    queryFn: async (): Promise<RiskAlert[]> => {
      try {
        const response = await api.get('/enrichment/risk/alerts');
        return (response as unknown as RiskAlert[]) || [];
      } catch {
        // Silently fail if user doesn't have permission or module not available
        return [];
      }
    },
    refetchInterval: 300000, // Refresh toutes les 5 minutes
  });
};

// KPIs Strategiques (+15,000€ valeur)
interface StrategicKPIData {
  kpi: string;
  value: number;
  unit: string;
  status: string;
  color: string;
  details: Record<string, unknown>;
  recommendations: string[];
}

interface AllStrategicKPIs {
  cash_runway: StrategicKPIData;
  profit_margin: StrategicKPIData;
  customer_concentration: StrategicKPIData;
  working_capital: StrategicKPIData;
  employee_productivity: StrategicKPIData;
  generated_at: string;
}

const useStrategicKPIs = () => {
  return useQuery({
    queryKey: ['cockpit-strategic-kpis'],
    queryFn: async (): Promise<AllStrategicKPIs | null> => {
      try {
        const response = await api.get('/cockpit/helpers/all-strategic');
        return response as unknown as AllStrategicKPIs;
      } catch {
        return null;
      }
    },
    refetchInterval: 300000, // Refresh toutes les 5 minutes
  });
};

// ============================================================
// COMPOSANTS
// ============================================================

// Card d'etape du flux
const FluxStepCard: React.FC<{
  step: typeof FLUX_STEPS[number];
  stats: FluxStats;
  onNavigate: () => void;
}> = ({ step, stats, onNavigate }) => {
  const Icon = step.icon;

  const getStepStats = () => {
    switch (step.id) {
      case 'crm':
        return {
          main: stats.crm.clients,
          mainLabel: 'Clients',
          sub: stats.crm.opportunites,
          subLabel: 'Opportunites',
        };
      case 'devis':
        return {
          main: stats.devis.total,
          mainLabel: 'Devis',
          sub: stats.devis.en_attente,
          subLabel: 'En attente',
          montant: stats.devis.montant_total,
        };
      case 'commandes':
        return {
          main: stats.commandes.total,
          mainLabel: 'Commandes',
          sub: stats.commandes.en_cours,
          subLabel: 'En cours',
          montant: stats.commandes.montant_total,
        };
      case 'ordres-service':
        return {
          main: stats.ods.total,
          mainLabel: 'Interventions',
          sub: stats.ods.en_cours,
          subLabel: 'En cours',
        };
      case 'affaires':
        return {
          main: stats.affaires.total,
          mainLabel: 'Affaires',
          sub: stats.affaires.en_cours,
          subLabel: 'En cours',
          montant: stats.affaires.ca_total,
        };
      case 'factures':
        return {
          main: stats.factures.total,
          mainLabel: 'Factures',
          sub: stats.factures.en_attente,
          subLabel: 'A payer',
          montant: stats.factures.montant_total,
        };
      default:
        return { main: 0, mainLabel: '', sub: 0, subLabel: '' };
    }
  };

  const stepStats = getStepStats();

  return (
    <div
      className={clsx('azals-cockpit-step', `azals-cockpit-step--${step.id}`)}
      onClick={onNavigate}
      onKeyDown={handleKeyActivate(onNavigate)}
      role="button"
      tabIndex={0}
      aria-label={`${step.label} - ${stepStats.main} ${stepStats.mainLabel}`}
    >
      {/* Icone et label */}
      <div className="azals-cockpit-step__header">
        <div className="azals-cockpit-step__icon">
          <Icon size={22} />
        </div>
        <div>
          <div className="azals-cockpit-step__label">{step.label}</div>
          <div className="azals-cockpit-step__desc">{step.description}</div>
        </div>
      </div>

      {/* Stats */}
      <div className="azals-cockpit-step__stats">
        <div>
          <div className="azals-cockpit-step__main-value">{stepStats.main}</div>
          <div className="azals-cockpit-step__main-label">{stepStats.mainLabel}</div>
        </div>
        <div className="azals-cockpit-step__sub">
          <div className="azals-cockpit-step__sub-value">{stepStats.sub}</div>
          <div className="azals-cockpit-step__sub-label">{stepStats.subLabel}</div>
        </div>
      </div>

      {/* Montant si applicable */}
      {stepStats.montant !== undefined && (
        <div className="azals-cockpit-step__montant">
          <Euro size={14} className="azals-cockpit-step__montant-icon" />
          <span className="azals-cockpit-step__montant-value">
            {formatCurrency(stepStats.montant)}
          </span>
        </div>
      )}

      {/* Bouton voir */}
      <div className="azals-cockpit-step__cta">
        <Eye size={14} />
        <span>Voir details</span>
        <ChevronRight size={14} />
      </div>
    </div>
  );
};

// Fleche entre les etapes
const FluxArrow: React.FC = () => (
  <div className="azals-cockpit-arrow">
    <ArrowRight size={24} />
  </div>
);

// Activite recente
const RecentActivityItem: React.FC<{ item: RecentItem }> = ({ item }) => {
  const typeConfig: Record<string, { icon: React.ReactNode; module: string }> = {
    devis: { icon: <FileText size={14} />, module: 'devis' },
    commande: { icon: <Package size={14} />, module: 'commandes' },
    ods: { icon: <Wrench size={14} />, module: 'ordres-service' },
    affaire: { icon: <Briefcase size={14} />, module: 'affaires' },
    facture: { icon: <Receipt size={14} />, module: 'factures' },
  };

  const config = typeConfig[item.type] || typeConfig.devis;
  const handleNavigate = () => navigateToModule(config.module, { id: item.id });

  return (
    <div
      className={clsx('azals-cockpit-recent-item', `azals-cockpit-recent-item--${item.type}`)}
      onClick={handleNavigate}
      onKeyDown={handleKeyActivate(handleNavigate)}
      role="button"
      tabIndex={0}
      aria-label={`${item.reference} - ${item.label}`}
    >
      <div className="azals-cockpit-recent-item__icon">
        {config.icon}
      </div>
      <div className="azals-cockpit-recent-item__body">
        <div className="azals-cockpit-recent-item__top">
          <span className="azals-cockpit-recent-item__ref">{item.reference}</span>
          <span className="azals-cockpit-recent-item__label">{item.label}</span>
        </div>
        <div className="azals-cockpit-recent-item__meta">
          {formatDate(item.date)}
          {item.montant && ` \u2022 ${formatCurrency(item.montant)}`}
        </div>
      </div>
      <ChevronRight size={16} className="azals-cockpit-recent-item__chevron" />
    </div>
  );
};

// Strategic KPI Card (+15,000€ valeur)
const StrategicKPICard: React.FC<{
  title: string;
  kpi: StrategicKPIData;
  icon: React.ReactNode;
}> = ({ title, kpi, icon }) => {
  const getStatusBadge = () => {
    const colorMap: Record<string, string> = {
      red: 'danger',
      orange: 'warning',
      yellow: 'attention',
      green: 'success',
      blue: 'info',
      gray: 'neutral',
    };
    return colorMap[kpi.color] || 'neutral';
  };

  return (
    <div className={clsx('azals-cockpit-strategic-kpi', `azals-cockpit-strategic-kpi--${getStatusBadge()}`)}>
      <div className="azals-cockpit-strategic-kpi__header">
        <div className="azals-cockpit-strategic-kpi__icon">{icon}</div>
        <div className="azals-cockpit-strategic-kpi__title">{title}</div>
        <div className={clsx('azals-cockpit-strategic-kpi__badge', `azals-cockpit-strategic-kpi__badge--${getStatusBadge()}`)}>
          {kpi.status}
        </div>
      </div>
      <div className="azals-cockpit-strategic-kpi__value">
        {typeof kpi.value === 'number' ? (
          kpi.unit === 'EUR' || kpi.unit === 'EUR/employe/an' ? (
            formatCurrency(kpi.value)
          ) : kpi.unit === '%' ? (
            `${kpi.value}%`
          ) : (
            `${kpi.value} ${kpi.unit}`
          )
        ) : kpi.value}
      </div>
      {kpi.recommendations && kpi.recommendations.length > 0 && kpi.recommendations[0] && (
        <div className="azals-cockpit-strategic-kpi__recommendation">
          {kpi.recommendations[0]}
        </div>
      )}
    </div>
  );
};

// KPI Global
const GlobalKPICard: React.FC<{
  label: string;
  value: string | number;
  trend?: number;
  icon: React.ReactNode;
  colorVariant: string;
}> = ({ label, value, trend, icon, colorVariant }) => (
  <div className="azals-cockpit-kpi">
    <div className="azals-cockpit-kpi__top">
      <div className={clsx('azals-cockpit-kpi__icon', `azals-cockpit-kpi__icon--${colorVariant}`)}>
        {icon}
      </div>
      {trend !== undefined && (
        <div className={clsx('azals-cockpit-kpi__trend', {
          'azals-cockpit-kpi__trend--up': trend >= 0,
          'azals-cockpit-kpi__trend--down': trend < 0,
        })}>
          {trend >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {Math.abs(trend)}%
        </div>
      )}
    </div>
    <div className="azals-cockpit-kpi__body">
      <div className="azals-cockpit-kpi__value">{value}</div>
      <div className="azals-cockpit-kpi__label">{label}</div>
    </div>
  </div>
);

// ============================================================
// MODULE PRINCIPAL
// ============================================================

export const CockpitModule: React.FC = () => {
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useCockpitStats();
  const { data: recentItems, isLoading: recentLoading, error: recentError, refetch: refetchRecent } = useRecentActivity();
  const { data: riskAlerts, refetch: refetchRisk } = useRiskAlerts();
  const { data: strategicKPIs, isLoading: strategicLoading, refetch: refetchStrategic } = useStrategicKPIs();

  const defaultStats: FluxStats = {
    crm: { prospects: 0, clients: 0, opportunites: 0 },
    devis: { total: 0, en_attente: 0, acceptes: 0, refuses: 0, montant_total: 0 },
    commandes: { total: 0, en_cours: 0, livrees: 0, montant_total: 0 },
    ods: { total: 0, a_planifier: 0, en_cours: 0, terminees: 0 },
    affaires: { total: 0, en_cours: 0, terminees: 0, ca_total: 0 },
    factures: { total: 0, en_attente: 0, payees: 0, montant_total: 0, montant_encaisse: 0 },
  };

  const currentStats = stats || defaultStats;

  // Calculer les KPIs globaux
  const globalKPIs = useMemo(() => {
    // CA = montant total des factures (source principale de revenu)
    // Si pas de factures, fallback sur affaires + commandes
    const caFromInvoices = currentStats.factures.montant_total;
    const caFallback = currentStats.affaires.ca_total + currentStats.commandes.montant_total;
    return {
      caTotal: caFromInvoices > 0 ? caFromInvoices : caFallback,
      facturesEnAttente: currentStats.factures.montant_total - currentStats.factures.montant_encaisse,
      tauxConversion: currentStats.devis.total > 0
        ? Math.round((currentStats.devis.acceptes / currentStats.devis.total) * 100)
        : 0,
      affairesEnCours: currentStats.affaires.en_cours + currentStats.ods.en_cours,
    };
  }, [currentStats]);

  if (statsError) {
    return (
      <div className="azals-cockpit">
        <ErrorState
          message={statsError instanceof Error ? statsError.message : undefined}
          onRetry={() => { refetchStats(); }}
        />
      </div>
    );
  }

  return (
    <div className="azals-cockpit">
      {/* Header */}
      <div className="azals-cockpit-header">
        <div>
          <h1 className="azals-cockpit-header__title">
            Cockpit
          </h1>
          <p className="azals-cockpit-header__subtitle">
            Vue globale du flux commercial
          </p>
        </div>
        <Button
          variant="secondary"
          leftIcon={<RefreshCw size={16} />}
          onClick={() => { refetchStats(); refetchRecent(); refetchRisk(); refetchStrategic(); }}
        >
          Actualiser
        </Button>
      </div>

      {/* KPIs Globaux */}
      <div className="azals-cockpit-kpis">
        <GlobalKPICard
          label="CA Total"
          value={formatCurrency(globalKPIs.caTotal)}
          trend={12}
          icon={<Euro size={24} />}
          colorVariant="success"
        />
        <GlobalKPICard
          label="A encaisser"
          value={formatCurrency(globalKPIs.facturesEnAttente)}
          icon={<Receipt size={24} />}
          colorVariant="warning"
        />
        <GlobalKPICard
          label="Taux conversion devis"
          value={`${globalKPIs.tauxConversion}%`}
          trend={5}
          icon={<TrendingUp size={24} />}
          colorVariant="devis"
        />
        <GlobalKPICard
          label="Affaires en cours"
          value={globalKPIs.affairesEnCours}
          icon={<Activity size={24} />}
          colorVariant="crm"
        />
      </div>

      {/* KPIs Strategiques Dirigeant */}
      {strategicKPIs && !strategicLoading && (
        <Card title="KPIs Strategiques Dirigeant" className="azals-cockpit-strategic">
          <div className="azals-cockpit-strategic__grid">
            <StrategicKPICard
              title="Cash Runway"
              kpi={strategicKPIs.cash_runway}
              icon={<Euro size={20} />}
            />
            <StrategicKPICard
              title="Marge Beneficiaire"
              kpi={strategicKPIs.profit_margin}
              icon={<TrendingUp size={20} />}
            />
            <StrategicKPICard
              title="Concentration Clients"
              kpi={strategicKPIs.customer_concentration}
              icon={<Users size={20} />}
            />
            <StrategicKPICard
              title="BFR"
              kpi={strategicKPIs.working_capital}
              icon={<Calculator size={20} />}
            />
            <StrategicKPICard
              title="Productivite RH"
              kpi={strategicKPIs.employee_productivity}
              icon={<Activity size={20} />}
            />
          </div>
        </Card>
      )}

      {/* Pipeline du flux */}
      <Card
        title="Pipeline Commercial"
        className="azals-cockpit-pipeline"
      >
        {statsLoading ? (
          <div className="azals-cockpit-loading">
            Chargement...
          </div>
        ) : (
          <div className="azals-cockpit-pipeline__flow">
            {FLUX_STEPS.map((step, index) => (
              <React.Fragment key={step.id}>
                <FluxStepCard
                  step={step}
                  stats={currentStats}
                  onNavigate={() => navigateToModule(step.id)}
                />
                {index < FLUX_STEPS.length - 1 && <FluxArrow />}
              </React.Fragment>
            ))}
          </div>
        )}
      </Card>

      {/* Contenu principal */}
      <div className="azals-cockpit-content">
        {/* Alertes et actions */}
        <Card title="Actions prioritaires">
          <div className="azals-cockpit-actions__list">
            {/* Devis en attente */}
            {currentStats.devis.en_attente > 0 && (
              <div
                className="azals-cockpit-action azals-cockpit-action--warning"
                onClick={() => navigateToModule('devis', { status: 'SENT' })}
                onKeyDown={handleKeyActivate(() => navigateToModule('devis', { status: 'SENT' }))}
                role="button"
                tabIndex={0}
                aria-label={`${currentStats.devis.en_attente} devis en attente de reponse`}
              >
                <Clock size={20} className="azals-cockpit-action__icon" />
                <div className="azals-cockpit-action__body">
                  <div className="azals-cockpit-action__title">
                    {currentStats.devis.en_attente} devis en attente de reponse
                  </div>
                  <div className="azals-cockpit-action__subtitle">
                    Relancer les clients
                  </div>
                </div>
                <ChevronRight size={18} className="azals-cockpit-action__chevron" />
              </div>
            )}

            {/* Interventions a planifier */}
            {currentStats.ods.a_planifier > 0 && (
              <div
                className="azals-cockpit-action azals-cockpit-action--info"
                onClick={() => navigateToModule('ordres-service', { status: 'A_PLANIFIER' })}
                onKeyDown={handleKeyActivate(() => navigateToModule('ordres-service', { status: 'A_PLANIFIER' }))}
                role="button"
                tabIndex={0}
                aria-label={`${currentStats.ods.a_planifier} intervention(s) a planifier`}
              >
                <Calendar size={20} className="azals-cockpit-action__icon" />
                <div className="azals-cockpit-action__body">
                  <div className="azals-cockpit-action__title">
                    {currentStats.ods.a_planifier} intervention(s) a planifier
                  </div>
                  <div className="azals-cockpit-action__subtitle">
                    Assigner les techniciens
                  </div>
                </div>
                <ChevronRight size={18} className="azals-cockpit-action__chevron" />
              </div>
            )}

            {/* Factures a encaisser */}
            {currentStats.factures.en_attente > 0 && (
              <div
                className="azals-cockpit-action azals-cockpit-action--danger"
                onClick={() => navigateToModule('factures', { status: 'SENT' })}
                onKeyDown={handleKeyActivate(() => navigateToModule('factures', { status: 'SENT' }))}
                role="button"
                tabIndex={0}
                aria-label={`${currentStats.factures.en_attente} facture(s) en attente de paiement`}
              >
                <Receipt size={20} className="azals-cockpit-action__icon" />
                <div className="azals-cockpit-action__body">
                  <div className="azals-cockpit-action__title">
                    {currentStats.factures.en_attente} facture(s) en attente de paiement
                  </div>
                  <div className="azals-cockpit-action__subtitle">
                    {formatCurrency(currentStats.factures.montant_total - currentStats.factures.montant_encaisse)} a encaisser
                  </div>
                </div>
                <ChevronRight size={18} className="azals-cockpit-action__chevron" />
              </div>
            )}

            {/* Partenaires a risque eleve */}
            {riskAlerts && riskAlerts.length > 0 && (
              <div
                className={clsx(
                  'azals-cockpit-action',
                  riskAlerts.some(a => a.level === 'high')
                    ? 'azals-cockpit-action--danger'
                    : 'azals-cockpit-action--warning'
                )}
                onClick={() => navigateToModule('crm')}
                onKeyDown={handleKeyActivate(() => navigateToModule('crm'))}
                role="button"
                tabIndex={0}
                aria-label={`${riskAlerts.length} partenaire(s) a risque eleve`}
              >
                <ShieldAlert size={20} className="azals-cockpit-action__icon" />
                <div className="azals-cockpit-action__body">
                  <div className="azals-cockpit-action__title">
                    {riskAlerts.length} partenaire(s) a risque {riskAlerts.some(a => a.level === 'high') ? 'eleve' : 'modere'}
                  </div>
                  <div className="azals-cockpit-action__subtitle">
                    {riskAlerts.slice(0, 2).map(a => a.partner_name).join(', ')}
                    {riskAlerts.length > 2 && ` et ${riskAlerts.length - 2} autre(s)`}
                  </div>
                </div>
                <ChevronRight size={18} className="azals-cockpit-action__chevron" />
              </div>
            )}

            {/* Aucune alerte */}
            {currentStats.devis.en_attente === 0 &&
             currentStats.ods.a_planifier === 0 &&
             currentStats.factures.en_attente === 0 &&
             (!riskAlerts || riskAlerts.length === 0) && (
              <div className="azals-cockpit-actions__empty">
                <CheckCircle2 size={48} className="azals-cockpit-actions__empty-icon" />
                <div className="azals-cockpit-actions__empty-title">Aucune action prioritaire</div>
                <div className="azals-cockpit-actions__empty-subtitle">Tout est sous controle</div>
              </div>
            )}
          </div>
        </Card>

        {/* Activite recente */}
        <Card title="Activite recente">
          {recentError ? (
            <ErrorState
              message={recentError instanceof Error ? recentError.message : undefined}
              onRetry={() => { refetchRecent(); }}
            />
          ) : recentLoading ? (
            <div className="azals-cockpit-loading">
              Chargement...
            </div>
          ) : recentItems && recentItems.length > 0 ? (
            <div className="azals-cockpit-recent__list">
              {recentItems.map((item) => (
                <RecentActivityItem key={`${item.type}-${item.id}`} item={item} />
              ))}
            </div>
          ) : (
            <div className="azals-cockpit-empty">
              Aucune activite recente
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

// Export pour la compatibilite avec l'ancien code
export const CockpitPage = CockpitModule;
export default CockpitModule;
