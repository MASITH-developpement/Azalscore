/**
 * AZALSCORE Module - Cockpit
 * ==========================
 *
 * Vue globale du flux commercial avec suivi en temps réel.
 * Tableau de bord exécutif montrant le pipeline commercial.
 *
 * Flux: CRM → DEV → COM/ODS → AFF → FAC/AVO → CPT
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Users, FileText, Package, Wrench, Briefcase, Receipt, Calculator,
  TrendingUp, TrendingDown, ArrowRight, RefreshCw, Eye, AlertTriangle,
  Clock, CheckCircle2, XCircle, Euro, Calendar, ChevronRight, Activity
} from 'lucide-react';
import { api } from '@core/api-client';

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

// ============================================================
// CONSTANTES
// ============================================================

const FLUX_STEPS = [
  { id: 'crm', label: 'CRM', icon: Users, color: '#8b5cf6', description: 'Prospects & Clients' },
  { id: 'devis', label: 'Devis', icon: FileText, color: '#3b82f6', description: 'Propositions' },
  { id: 'commandes', label: 'Commandes', icon: Package, color: '#10b981', description: 'Commandes client' },
  { id: 'ordres-service', label: 'ODS', icon: Wrench, color: '#f59e0b', description: 'Interventions' },
  { id: 'affaires', label: 'Affaires', icon: Briefcase, color: '#6366f1', description: 'Projets' },
  { id: 'factures', label: 'Factures', icon: Receipt, color: '#ec4899', description: 'Facturation' },
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

// ============================================================
// API HOOKS
// ============================================================

const useCockpitStats = () => {
  return useQuery({
    queryKey: ['cockpit-stats'],
    queryFn: async () => {
      // Récupérer les stats de chaque module
      const [
        customersRes,
        opportunitiesRes,
        devisRes,
        commandesRes,
        interventionsRes,
        projectsRes,
        facturesRes,
      ] = await Promise.all([
        api.get('/v1/commercial/customers?page_size=1').catch(() => ({ total: 0, items: [] })),
        api.get('/v1/commercial/opportunities?page_size=100').catch(() => ({ total: 0, items: [] })),
        api.get('/v1/commercial/documents?type=QUOTE&page_size=100').catch(() => ({ total: 0, items: [] })),
        api.get('/v1/commercial/documents?type=ORDER&page_size=100').catch(() => ({ total: 0, items: [] })),
        api.get('/v1/interventions?page_size=100').catch(() => ({ total: 0, items: [] })),
        api.get('/v1/projects?limit=200').catch(() => ({ total: 0, items: [] })),
        api.get('/v1/commercial/documents?type=INVOICE&page_size=100').catch(() => ({ total: 0, items: [] })),
      ]);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const opportunities = ((opportunitiesRes as any).items || []) as any[];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const devis = ((devisRes as any).items || []) as any[];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const commandes = ((commandesRes as any).items || []) as any[];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const interventions = ((interventionsRes as any).items || []) as any[];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const projects = ((projectsRes as any).items || []) as any[];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const factures = ((facturesRes as any).items || []) as any[];

      // Calculer les stats
      const stats: FluxStats = {
        crm: {
          prospects: ((customersRes as { total?: number }).total || 0),
          clients: ((customersRes as { total?: number }).total || 0),
          opportunites: opportunities.length,
        },
        devis: {
          total: devis.length,
          en_attente: devis.filter((d) => d.status === 'DRAFT' || d.status === 'SENT').length,
          acceptes: devis.filter((d) => d.status === 'ACCEPTED').length,
          refuses: devis.filter((d) => d.status === 'REJECTED').length,
          montant_total: devis.reduce((sum, d) => sum + (d.total_ht || 0), 0),
        },
        commandes: {
          total: commandes.length,
          en_cours: commandes.filter((c) => c.status === 'CONFIRMED' || c.status === 'IN_PROGRESS').length,
          livrees: commandes.filter((c) => c.status === 'DELIVERED').length,
          montant_total: commandes.reduce((sum, c) => sum + (c.total_ht || 0), 0),
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
          ca_total: projects.reduce((sum, p) => sum + (p.budget_total || 0), 0),
        },
        factures: {
          total: factures.length,
          en_attente: factures.filter((f) => f.status === 'DRAFT' || f.status === 'SENT').length,
          payees: factures.filter((f) => f.status === 'PAID').length,
          montant_total: factures.reduce((sum, f) => sum + (f.total_ht || 0), 0),
          montant_encaisse: factures
            .filter((f) => f.status === 'PAID')
            .reduce((sum: number, f) => sum + (f.total_ht || 0), 0),
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
      // Récupérer les items récents de chaque module
      const [devisRes, commandesRes, interventionsRes, facturesRes] = await Promise.all([
        api.get('/v1/commercial/documents?type=QUOTE&limit=5').catch(() => ({ items: [] })),
        api.get('/v1/commercial/documents?type=ORDER&limit=5').catch(() => ({ items: [] })),
        api.get('/v1/interventions?limit=5').catch(() => ({ items: [] })),
        api.get('/v1/commercial/documents?type=INVOICE&limit=5').catch(() => ({ items: [] })),
      ]);

      const items: RecentItem[] = [];

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const devisList = ((devisRes as any).items || []) as any[];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const commandesList = ((commandesRes as any).items || []) as any[];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const interventionsList = ((interventionsRes as any).items || []) as any[];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const facturesList = ((facturesRes as any).items || []) as any[];

      // Ajouter les devis
      devisList.forEach((d) => {
        items.push({
          id: d.id || '',
          reference: d.reference || '',
          label: d.customer_name || 'Client',
          type: 'devis',
          status: d.status || '',
          date: d.created_at || '',
          montant: d.total_ht,
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
          montant: c.total_ht,
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
          montant: f.total_ht,
        });
      });

      // Trier par date
      items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

      return items.slice(0, 10);
    },
  });
};

// ============================================================
// COMPOSANTS
// ============================================================

// Card d'étape du flux
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
          subLabel: 'Opportunités',
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
          subLabel: 'À payer',
          montant: stats.factures.montant_total,
        };
      default:
        return { main: 0, mainLabel: '', sub: 0, subLabel: '' };
    }
  };

  const stepStats = getStepStats();

  return (
    <div
      onClick={onNavigate}
      style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '20px',
        border: '1px solid #e5e7eb',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        minWidth: '160px',
        flex: 1,
      }}
      onMouseOver={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
      }}
      onMouseOut={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      {/* Icône et label */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <div style={{
          width: '44px',
          height: '44px',
          borderRadius: '10px',
          backgroundColor: `${step.color}15`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <Icon size={22} style={{ color: step.color }} />
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: '16px', color: '#111827' }}>{step.label}</div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>{step.description}</div>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: step.color }}>{stepStats.main}</div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>{stepStats.mainLabel}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '18px', fontWeight: 600, color: '#374151' }}>{stepStats.sub}</div>
          <div style={{ fontSize: '11px', color: '#9ca3af' }}>{stepStats.subLabel}</div>
        </div>
      </div>

      {/* Montant si applicable */}
      {stepStats.montant !== undefined && (
        <div style={{
          marginTop: '12px',
          paddingTop: '12px',
          borderTop: '1px solid #f3f4f6',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}>
          <Euro size={14} style={{ color: '#6b7280' }} />
          <span style={{ fontSize: '14px', fontWeight: 500, color: '#374151' }}>
            {formatCurrency(stepStats.montant)}
          </span>
        </div>
      )}

      {/* Bouton voir */}
      <div style={{
        marginTop: '12px',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        color: step.color,
        fontSize: '13px',
        fontWeight: 500,
      }}>
        <Eye size={14} />
        <span>Voir détails</span>
        <ChevronRight size={14} />
      </div>
    </div>
  );
};

// Flèche entre les étapes
const FluxArrow: React.FC = () => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0 8px',
  }}>
    <ArrowRight size={24} style={{ color: '#d1d5db' }} />
  </div>
);

// Activité récente
const RecentActivityItem: React.FC<{ item: RecentItem }> = ({ item }) => {
  const typeConfig: Record<string, { color: string; icon: React.ReactNode; module: string }> = {
    devis: { color: '#3b82f6', icon: <FileText size={14} />, module: 'devis' },
    commande: { color: '#10b981', icon: <Package size={14} />, module: 'commandes' },
    ods: { color: '#f59e0b', icon: <Wrench size={14} />, module: 'ordres-service' },
    affaire: { color: '#6366f1', icon: <Briefcase size={14} />, module: 'affaires' },
    facture: { color: '#ec4899', icon: <Receipt size={14} />, module: 'factures' },
  };

  const config = typeConfig[item.type] || typeConfig.devis;

  return (
    <div
      onClick={() => navigateToModule(config.module, { id: item.id })}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px',
        borderRadius: '8px',
        cursor: 'pointer',
        transition: 'background-color 0.2s',
      }}
      onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}
      onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
    >
      <div style={{
        width: '32px',
        height: '32px',
        borderRadius: '8px',
        backgroundColor: `${config.color}15`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: config.color,
      }}>
        {config.icon}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: 500, color: config.color }}>{item.reference}</span>
          <span style={{ fontSize: '12px', color: '#6b7280' }}>{item.label}</span>
        </div>
        <div style={{ fontSize: '12px', color: '#9ca3af' }}>
          {formatDate(item.date)}
          {item.montant && ` • ${formatCurrency(item.montant)}`}
        </div>
      </div>
      <ChevronRight size={16} style={{ color: '#d1d5db' }} />
    </div>
  );
};

// KPI Global
const GlobalKPICard: React.FC<{
  label: string;
  value: string | number;
  trend?: number;
  icon: React.ReactNode;
  color: string;
}> = ({ label, value, trend, icon, color }) => (
  <div style={{
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '20px',
    border: '1px solid #e5e7eb',
  }}>
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
      <div style={{
        width: '48px',
        height: '48px',
        borderRadius: '12px',
        backgroundColor: `${color}15`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: color,
      }}>
        {icon}
      </div>
      {trend !== undefined && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          color: trend >= 0 ? '#10b981' : '#ef4444',
          fontSize: '13px',
          fontWeight: 500,
        }}>
          {trend >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {Math.abs(trend)}%
        </div>
      )}
    </div>
    <div style={{ marginTop: '16px' }}>
      <div style={{ fontSize: '28px', fontWeight: 700, color: '#111827' }}>{value}</div>
      <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '4px' }}>{label}</div>
    </div>
  </div>
);

// ============================================================
// MODULE PRINCIPAL
// ============================================================

export const CockpitModule: React.FC = () => {
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useCockpitStats();
  const { data: recentItems, isLoading: recentLoading } = useRecentActivity();

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
    return {
      caTotal: currentStats.affaires.ca_total + currentStats.commandes.montant_total,
      facturesEnAttente: currentStats.factures.montant_total - currentStats.factures.montant_encaisse,
      tauxConversion: currentStats.devis.total > 0
        ? Math.round((currentStats.devis.acceptes / currentStats.devis.total) * 100)
        : 0,
      affairesEnCours: currentStats.affaires.en_cours + currentStats.ods.en_cours,
    };
  }, [currentStats]);

  return (
    <div style={{ padding: '24px', backgroundColor: '#f9fafb', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
      }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, margin: 0, color: '#111827' }}>
            Cockpit
          </h1>
          <p style={{ color: '#6b7280', margin: '4px 0 0 0' }}>
            Vue globale du flux commercial
          </p>
        </div>
        <button
          onClick={() => refetchStats()}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 16px',
            backgroundColor: 'white',
            color: '#374151',
            border: '1px solid #d1d5db',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          <RefreshCw size={16} />
          Actualiser
        </button>
      </div>

      {/* KPIs Globaux */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px',
        marginBottom: '24px',
      }}>
        <GlobalKPICard
          label="CA Total"
          value={formatCurrency(globalKPIs.caTotal)}
          trend={12}
          icon={<Euro size={24} />}
          color="#10b981"
        />
        <GlobalKPICard
          label="À encaisser"
          value={formatCurrency(globalKPIs.facturesEnAttente)}
          icon={<Receipt size={24} />}
          color="#f59e0b"
        />
        <GlobalKPICard
          label="Taux conversion devis"
          value={`${globalKPIs.tauxConversion}%`}
          trend={5}
          icon={<TrendingUp size={24} />}
          color="#3b82f6"
        />
        <GlobalKPICard
          label="Affaires en cours"
          value={globalKPIs.affairesEnCours}
          icon={<Activity size={24} />}
          color="#8b5cf6"
        />
      </div>

      {/* Pipeline du flux */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '24px',
        border: '1px solid #e5e7eb',
      }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '20px', color: '#111827' }}>
          Pipeline Commercial
        </h2>

        {statsLoading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
            Chargement...
          </div>
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'stretch',
            gap: '0',
            overflowX: 'auto',
            paddingBottom: '8px',
          }}>
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
      </div>

      {/* Contenu principal */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Alertes et actions */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          padding: '24px',
          border: '1px solid #e5e7eb',
        }}>
          <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '20px', color: '#111827' }}>
            Actions prioritaires
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Devis en attente */}
            {currentStats.devis.en_attente > 0 && (
              <div
                onClick={() => navigateToModule('devis', { status: 'SENT' })}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '16px',
                  backgroundColor: '#fef3c7',
                  borderRadius: '10px',
                  cursor: 'pointer',
                }}
              >
                <Clock size={20} style={{ color: '#d97706' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, color: '#92400e' }}>
                    {currentStats.devis.en_attente} devis en attente de réponse
                  </div>
                  <div style={{ fontSize: '13px', color: '#b45309' }}>
                    Relancer les clients
                  </div>
                </div>
                <ChevronRight size={18} style={{ color: '#d97706' }} />
              </div>
            )}

            {/* Interventions à planifier */}
            {currentStats.ods.a_planifier > 0 && (
              <div
                onClick={() => navigateToModule('ordres-service', { status: 'A_PLANIFIER' })}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '16px',
                  backgroundColor: '#dbeafe',
                  borderRadius: '10px',
                  cursor: 'pointer',
                }}
              >
                <Calendar size={20} style={{ color: '#2563eb' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, color: '#1e40af' }}>
                    {currentStats.ods.a_planifier} intervention(s) à planifier
                  </div>
                  <div style={{ fontSize: '13px', color: '#3b82f6' }}>
                    Assigner les techniciens
                  </div>
                </div>
                <ChevronRight size={18} style={{ color: '#2563eb' }} />
              </div>
            )}

            {/* Factures à encaisser */}
            {currentStats.factures.en_attente > 0 && (
              <div
                onClick={() => navigateToModule('factures', { status: 'SENT' })}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '16px',
                  backgroundColor: '#fce7f3',
                  borderRadius: '10px',
                  cursor: 'pointer',
                }}
              >
                <Receipt size={20} style={{ color: '#db2777' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, color: '#9d174d' }}>
                    {currentStats.factures.en_attente} facture(s) en attente de paiement
                  </div>
                  <div style={{ fontSize: '13px', color: '#ec4899' }}>
                    {formatCurrency(currentStats.factures.montant_total - currentStats.factures.montant_encaisse)} à encaisser
                  </div>
                </div>
                <ChevronRight size={18} style={{ color: '#db2777' }} />
              </div>
            )}

            {/* Aucune alerte */}
            {currentStats.devis.en_attente === 0 &&
             currentStats.ods.a_planifier === 0 &&
             currentStats.factures.en_attente === 0 && (
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '32px',
                color: '#6b7280',
              }}>
                <CheckCircle2 size={48} style={{ color: '#10b981', marginBottom: '12px' }} />
                <div style={{ fontWeight: 500 }}>Aucune action prioritaire</div>
                <div style={{ fontSize: '13px' }}>Tout est sous contrôle</div>
              </div>
            )}
          </div>
        </div>

        {/* Activité récente */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          padding: '24px',
          border: '1px solid #e5e7eb',
        }}>
          <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px', color: '#111827' }}>
            Activité récente
          </h2>

          {recentLoading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
              Chargement...
            </div>
          ) : recentItems && recentItems.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {recentItems.map((item) => (
                <RecentActivityItem key={`${item.type}-${item.id}`} item={item} />
              ))}
            </div>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '32px',
              color: '#9ca3af',
            }}>
              Aucune activité récente
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Export pour la compatibilité avec l'ancien code
export const CockpitPage = CockpitModule;
export default CockpitModule;
