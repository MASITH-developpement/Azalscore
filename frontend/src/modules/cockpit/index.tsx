/**
 * AZALSCORE Module - Cockpit
 * Vue globale du flux commercial avec suivi en temps reel.
 * Flux: CRM -> DEV -> COM/ODS -> AFF -> FAC/AVO -> CPT
 */

import React, { useMemo } from 'react';
import { clsx } from 'clsx';
import {
  Users, FileText, Package, Wrench, Briefcase, Receipt, Calculator,
  TrendingUp, TrendingDown, ArrowRight, RefreshCw, Eye,
  Clock, CheckCircle2, Euro, Calendar, ChevronRight, Activity, ShieldAlert
} from 'lucide-react';
import { COLORS } from '@core/design-tokens';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { ErrorState } from '../../ui-engine/components/StateViews';
import '../../styles/cockpit.css';

// Hooks & Types
import {
  useCockpitStats, useRecentActivity, useRiskAlerts, useStrategicKPIs,
  DEFAULT_STATS,
  type FluxStats, type RecentItem, type StrategicKPIData
} from './hooks';

// Re-exports
export * from './hooks';

// ============================================================================
// CONSTANTES
// ============================================================================

const FLUX_STEPS = [
  { id: 'crm', label: 'CRM', icon: Users, color: COLORS.crm, description: 'Prospects & Clients' },
  { id: 'devis', label: 'Devis', icon: FileText, color: COLORS.devis, description: 'Propositions' },
  { id: 'commandes', label: 'Commandes', icon: Package, color: COLORS.commandes, description: 'Commandes client' },
  { id: 'ordres-service', label: 'ODS', icon: Wrench, color: COLORS.ods, description: 'Interventions' },
  { id: 'affaires', label: 'Affaires', icon: Briefcase, color: COLORS.affaires, description: 'Projets' },
  { id: 'factures', label: 'Factures', icon: Receipt, color: COLORS.factures, description: 'Facturation' },
] as const;

// ============================================================================
// HELPERS
// ============================================================================

const formatCurrency = (amount?: number): string => {
  if (amount === undefined || amount === null) return '-';
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
};

const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

const navigateToModule = (module: string, params?: Record<string, string>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view: module, params } }));
};

const handleKeyActivate = (callback: () => void) => (e: React.KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); callback(); }
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const FluxStepCard: React.FC<{
  step: typeof FLUX_STEPS[number];
  stats: FluxStats;
  onNavigate: () => void;
}> = ({ step, stats, onNavigate }) => {
  const Icon = step.icon;

  const getStepStats = () => {
    switch (step.id) {
      case 'crm': return { main: stats.crm.clients, mainLabel: 'Clients', sub: stats.crm.opportunites, subLabel: 'Opportunites' };
      case 'devis': return { main: stats.devis.total, mainLabel: 'Devis', sub: stats.devis.en_attente, subLabel: 'En attente', montant: stats.devis.montant_total };
      case 'commandes': return { main: stats.commandes.total, mainLabel: 'Commandes', sub: stats.commandes.en_cours, subLabel: 'En cours', montant: stats.commandes.montant_total };
      case 'ordres-service': return { main: stats.ods.total, mainLabel: 'Interventions', sub: stats.ods.en_cours, subLabel: 'En cours' };
      case 'affaires': return { main: stats.affaires.total, mainLabel: 'Affaires', sub: stats.affaires.en_cours, subLabel: 'En cours', montant: stats.affaires.ca_total };
      case 'factures': return { main: stats.factures.total, mainLabel: 'Factures', sub: stats.factures.en_attente, subLabel: 'A payer', montant: stats.factures.montant_total };
      default: return { main: 0, mainLabel: '', sub: 0, subLabel: '' };
    }
  };

  const stepStats = getStepStats();

  return (
    <div className={clsx('azals-cockpit-step', `azals-cockpit-step--${step.id}`)} onClick={onNavigate} onKeyDown={handleKeyActivate(onNavigate)} role="button" tabIndex={0} aria-label={`${step.label} - ${stepStats.main} ${stepStats.mainLabel}`}>
      <div className="azals-cockpit-step__header">
        <div className="azals-cockpit-step__icon"><Icon size={22} /></div>
        <div>
          <div className="azals-cockpit-step__label">{step.label}</div>
          <div className="azals-cockpit-step__desc">{step.description}</div>
        </div>
      </div>
      <div className="azals-cockpit-step__stats">
        <div><div className="azals-cockpit-step__main-value">{stepStats.main}</div><div className="azals-cockpit-step__main-label">{stepStats.mainLabel}</div></div>
        <div className="azals-cockpit-step__sub"><div className="azals-cockpit-step__sub-value">{stepStats.sub}</div><div className="azals-cockpit-step__sub-label">{stepStats.subLabel}</div></div>
      </div>
      {stepStats.montant !== undefined && (
        <div className="azals-cockpit-step__montant"><Euro size={14} className="azals-cockpit-step__montant-icon" /><span className="azals-cockpit-step__montant-value">{formatCurrency(stepStats.montant)}</span></div>
      )}
      <div className="azals-cockpit-step__cta"><Eye size={14} /><span>Voir details</span><ChevronRight size={14} /></div>
    </div>
  );
};

const FluxArrow: React.FC = () => (<div className="azals-cockpit-arrow"><ArrowRight size={24} /></div>);

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
    <div className={clsx('azals-cockpit-recent-item', `azals-cockpit-recent-item--${item.type}`)} onClick={handleNavigate} onKeyDown={handleKeyActivate(handleNavigate)} role="button" tabIndex={0} aria-label={`${item.reference} - ${item.label}`}>
      <div className="azals-cockpit-recent-item__icon">{config.icon}</div>
      <div className="azals-cockpit-recent-item__body">
        <div className="azals-cockpit-recent-item__top"><span className="azals-cockpit-recent-item__ref">{item.reference}</span><span className="azals-cockpit-recent-item__label">{item.label}</span></div>
        <div className="azals-cockpit-recent-item__meta">{formatDate(item.date)}{item.montant && ` \u2022 ${formatCurrency(item.montant)}`}</div>
      </div>
      <ChevronRight size={16} className="azals-cockpit-recent-item__chevron" />
    </div>
  );
};

const StrategicKPICard: React.FC<{ title: string; kpi: StrategicKPIData; icon: React.ReactNode }> = ({ title, kpi, icon }) => {
  const colorMap: Record<string, string> = { red: 'danger', orange: 'warning', yellow: 'attention', green: 'success', blue: 'info', gray: 'neutral' };
  const badge = colorMap[kpi.color] || 'neutral';

  return (
    <div className={clsx('azals-cockpit-strategic-kpi', `azals-cockpit-strategic-kpi--${badge}`)}>
      <div className="azals-cockpit-strategic-kpi__header">
        <div className="azals-cockpit-strategic-kpi__icon">{icon}</div>
        <div className="azals-cockpit-strategic-kpi__title">{title}</div>
        <div className={clsx('azals-cockpit-strategic-kpi__badge', `azals-cockpit-strategic-kpi__badge--${badge}`)}>{kpi.status}</div>
      </div>
      <div className="azals-cockpit-strategic-kpi__value">
        {typeof kpi.value === 'number' ? (kpi.unit === 'EUR' || kpi.unit === 'EUR/employe/an' ? formatCurrency(kpi.value) : kpi.unit === '%' ? `${kpi.value}%` : `${kpi.value} ${kpi.unit}`) : kpi.value}
      </div>
      {kpi.recommendations && kpi.recommendations.length > 0 && kpi.recommendations[0] && (
        <div className="azals-cockpit-strategic-kpi__recommendation">{kpi.recommendations[0]}</div>
      )}
    </div>
  );
};

const GlobalKPICard: React.FC<{ label: string; value: string | number; trend?: number; icon: React.ReactNode; colorVariant: string }> = ({ label, value, trend, icon, colorVariant }) => (
  <div className="azals-cockpit-kpi">
    <div className="azals-cockpit-kpi__top">
      <div className={clsx('azals-cockpit-kpi__icon', `azals-cockpit-kpi__icon--${colorVariant}`)}>{icon}</div>
      {trend !== undefined && (
        <div className={clsx('azals-cockpit-kpi__trend', { 'azals-cockpit-kpi__trend--up': trend >= 0, 'azals-cockpit-kpi__trend--down': trend < 0 })}>
          {trend >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}{Math.abs(trend)}%
        </div>
      )}
    </div>
    <div className="azals-cockpit-kpi__body"><div className="azals-cockpit-kpi__value">{value}</div><div className="azals-cockpit-kpi__label">{label}</div></div>
  </div>
);

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

export const CockpitModule: React.FC = () => {
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useCockpitStats();
  const { data: recentItems, isLoading: recentLoading, error: recentError, refetch: refetchRecent } = useRecentActivity();
  const { data: riskAlerts, refetch: refetchRisk } = useRiskAlerts();
  const { data: strategicKPIs, isLoading: strategicLoading, refetch: refetchStrategic } = useStrategicKPIs();

  const currentStats = stats || DEFAULT_STATS;

  const globalKPIs = useMemo(() => {
    const caFromInvoices = currentStats.factures.montant_total;
    const caFallback = currentStats.affaires.ca_total + currentStats.commandes.montant_total;
    return {
      caTotal: caFromInvoices > 0 ? caFromInvoices : caFallback,
      facturesEnAttente: currentStats.factures.montant_total - currentStats.factures.montant_encaisse,
      tauxConversion: currentStats.devis.total > 0 ? Math.round((currentStats.devis.acceptes / currentStats.devis.total) * 100) : 0,
      affairesEnCours: currentStats.affaires.en_cours + currentStats.ods.en_cours,
    };
  }, [currentStats]);

  if (statsError) {
    return (<div className="azals-cockpit"><ErrorState message={statsError instanceof Error ? statsError.message : undefined} onRetry={() => { refetchStats(); }} /></div>);
  }

  return (
    <div className="azals-cockpit">
      <div className="azals-cockpit-header">
        <div><h1 className="azals-cockpit-header__title">Cockpit</h1><p className="azals-cockpit-header__subtitle">Vue globale du flux commercial</p></div>
        <Button variant="secondary" leftIcon={<RefreshCw size={16} />} onClick={() => { refetchStats(); refetchRecent(); refetchRisk(); refetchStrategic(); }}>Actualiser</Button>
      </div>

      <div className="azals-cockpit-kpis">
        <GlobalKPICard label="CA Total" value={formatCurrency(globalKPIs.caTotal)} trend={12} icon={<Euro size={24} />} colorVariant="success" />
        <GlobalKPICard label="A encaisser" value={formatCurrency(globalKPIs.facturesEnAttente)} icon={<Receipt size={24} />} colorVariant="warning" />
        <GlobalKPICard label="Taux conversion devis" value={`${globalKPIs.tauxConversion}%`} trend={5} icon={<TrendingUp size={24} />} colorVariant="devis" />
        <GlobalKPICard label="Affaires en cours" value={globalKPIs.affairesEnCours} icon={<Activity size={24} />} colorVariant="crm" />
      </div>

      {strategicKPIs && !strategicLoading && (
        <Card title="KPIs Strategiques Dirigeant" className="azals-cockpit-strategic">
          <div className="azals-cockpit-strategic__grid">
            <StrategicKPICard title="Cash Runway" kpi={strategicKPIs.cash_runway} icon={<Euro size={20} />} />
            <StrategicKPICard title="Marge Beneficiaire" kpi={strategicKPIs.profit_margin} icon={<TrendingUp size={20} />} />
            <StrategicKPICard title="Concentration Clients" kpi={strategicKPIs.customer_concentration} icon={<Users size={20} />} />
            <StrategicKPICard title="BFR" kpi={strategicKPIs.working_capital} icon={<Calculator size={20} />} />
            <StrategicKPICard title="Productivite RH" kpi={strategicKPIs.employee_productivity} icon={<Activity size={20} />} />
          </div>
        </Card>
      )}

      <Card title="Pipeline Commercial" className="azals-cockpit-pipeline">
        {statsLoading ? (<div className="azals-cockpit-loading">Chargement...</div>) : (
          <div className="azals-cockpit-pipeline__flow">
            {FLUX_STEPS.map((step, index) => (
              <React.Fragment key={step.id}>
                <FluxStepCard step={step} stats={currentStats} onNavigate={() => navigateToModule(step.id)} />
                {index < FLUX_STEPS.length - 1 && <FluxArrow />}
              </React.Fragment>
            ))}
          </div>
        )}
      </Card>

      <div className="azals-cockpit-content">
        <Card title="Actions prioritaires">
          <div className="azals-cockpit-actions__list">
            {currentStats.devis.en_attente > 0 && (
              <div className="azals-cockpit-action azals-cockpit-action--warning" onClick={() => navigateToModule('devis', { status: 'SENT' })} onKeyDown={handleKeyActivate(() => navigateToModule('devis', { status: 'SENT' }))} role="button" tabIndex={0} aria-label={`${currentStats.devis.en_attente} devis en attente de reponse`}>
                <Clock size={20} className="azals-cockpit-action__icon" /><div className="azals-cockpit-action__body"><div className="azals-cockpit-action__title">{currentStats.devis.en_attente} devis en attente de reponse</div><div className="azals-cockpit-action__subtitle">Relancer les clients</div></div><ChevronRight size={18} className="azals-cockpit-action__chevron" />
              </div>
            )}
            {currentStats.ods.a_planifier > 0 && (
              <div className="azals-cockpit-action azals-cockpit-action--info" onClick={() => navigateToModule('ordres-service', { status: 'A_PLANIFIER' })} onKeyDown={handleKeyActivate(() => navigateToModule('ordres-service', { status: 'A_PLANIFIER' }))} role="button" tabIndex={0} aria-label={`${currentStats.ods.a_planifier} intervention(s) a planifier`}>
                <Calendar size={20} className="azals-cockpit-action__icon" /><div className="azals-cockpit-action__body"><div className="azals-cockpit-action__title">{currentStats.ods.a_planifier} intervention(s) a planifier</div><div className="azals-cockpit-action__subtitle">Assigner les techniciens</div></div><ChevronRight size={18} className="azals-cockpit-action__chevron" />
              </div>
            )}
            {currentStats.factures.en_attente > 0 && (
              <div className="azals-cockpit-action azals-cockpit-action--danger" onClick={() => navigateToModule('factures', { status: 'SENT' })} onKeyDown={handleKeyActivate(() => navigateToModule('factures', { status: 'SENT' }))} role="button" tabIndex={0} aria-label={`${currentStats.factures.en_attente} facture(s) en attente de paiement`}>
                <Receipt size={20} className="azals-cockpit-action__icon" /><div className="azals-cockpit-action__body"><div className="azals-cockpit-action__title">{currentStats.factures.en_attente} facture(s) en attente de paiement</div><div className="azals-cockpit-action__subtitle">{formatCurrency(currentStats.factures.montant_total - currentStats.factures.montant_encaisse)} a encaisser</div></div><ChevronRight size={18} className="azals-cockpit-action__chevron" />
              </div>
            )}
            {riskAlerts && riskAlerts.length > 0 && (
              <div className={clsx('azals-cockpit-action', riskAlerts.some(a => a.level === 'high') ? 'azals-cockpit-action--danger' : 'azals-cockpit-action--warning')} onClick={() => navigateToModule('crm')} onKeyDown={handleKeyActivate(() => navigateToModule('crm'))} role="button" tabIndex={0} aria-label={`${riskAlerts.length} partenaire(s) a risque eleve`}>
                <ShieldAlert size={20} className="azals-cockpit-action__icon" /><div className="azals-cockpit-action__body"><div className="azals-cockpit-action__title">{riskAlerts.length} partenaire(s) a risque {riskAlerts.some(a => a.level === 'high') ? 'eleve' : 'modere'}</div><div className="azals-cockpit-action__subtitle">{riskAlerts.slice(0, 2).map(a => a.partner_name).join(', ')}{riskAlerts.length > 2 && ` et ${riskAlerts.length - 2} autre(s)`}</div></div><ChevronRight size={18} className="azals-cockpit-action__chevron" />
              </div>
            )}
            {currentStats.devis.en_attente === 0 && currentStats.ods.a_planifier === 0 && currentStats.factures.en_attente === 0 && (!riskAlerts || riskAlerts.length === 0) && (
              <div className="azals-cockpit-actions__empty"><CheckCircle2 size={48} className="azals-cockpit-actions__empty-icon" /><div className="azals-cockpit-actions__empty-title">Aucune action prioritaire</div><div className="azals-cockpit-actions__empty-subtitle">Tout est sous controle</div></div>
            )}
          </div>
        </Card>

        <Card title="Activite recente">
          {recentError ? (<ErrorState message={recentError instanceof Error ? recentError.message : undefined} onRetry={() => { refetchRecent(); }} />) : recentLoading ? (<div className="azals-cockpit-loading">Chargement...</div>) : recentItems && recentItems.length > 0 ? (
            <div className="azals-cockpit-recent__list">{recentItems.map((item) => (<RecentActivityItem key={`${item.type}-${item.id}`} item={item} />))}</div>
          ) : (<div className="azals-cockpit-empty">Aucune activite recente</div>)}
        </Card>
      </div>
    </div>
  );
};

export const CockpitPage = CockpitModule;
export default CockpitModule;
