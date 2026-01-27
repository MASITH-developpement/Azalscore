/**
 * AZALSCORE Module - INTERVENTIONS
 * Gestion des interventions terrain - Migré vers BaseViewStandard
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import { BaseViewStandard } from '@ui/standards';
import type { TableColumn } from '@/types';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition } from '@ui/standards';
import {
  ClipboardList, Calendar, Wrench, CheckCircle, BarChart3, Clock, MapPin,
  User, FileText, History, Sparkles, Package, Euro, AlertTriangle, Play, X
} from 'lucide-react';
import { LoadingState, ErrorState } from '@ui/components/StateViews';

// Import tab components
import {
  InterventionInfoTab,
  InterventionLinesTab,
  InterventionFinancialTab,
  InterventionDocsTab,
  InterventionHistoryTab,
  InterventionIATab,
  InterventionFormView
} from './components';

// Import shared types
import type { Intervention, InterventionType, InterventionPriorite, DonneurOrdre, InterventionStats } from './types';
import {
  STATUT_CONFIG, PRIORITE_CONFIG, TYPE_CONFIG,
  formatDate, formatDuration, formatCurrency, isLate
} from './types';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavProps {
  tabs: { id: string; label: string }[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <div className="azals-tab-nav">
    {tabs.map(tab => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

// ============================================================================
// CONSTANTES
// ============================================================================

const STATUTS = [
  { value: 'A_PLANIFIER', label: 'A planifier' },
  { value: 'PLANIFIEE', label: 'Planifiée' },
  { value: 'EN_COURS', label: 'En cours' },
  { value: 'TERMINEE', label: 'Terminée' },
  { value: 'ANNULEE', label: 'Annulée' }
];

const PRIORITES = [
  { value: 'LOW', label: 'Basse' },
  { value: 'NORMAL', label: 'Normale' },
  { value: 'HIGH', label: 'Haute' },
  { value: 'URGENT', label: 'Urgente' }
];

const TYPES_INTERVENTION = [
  { value: 'INSTALLATION', label: 'Installation' },
  { value: 'MAINTENANCE', label: 'Maintenance' },
  { value: 'REPARATION', label: 'Réparation' },
  { value: 'INSPECTION', label: 'Inspection' },
  { value: 'FORMATION', label: 'Formation' },
  { value: 'CONSULTATION', label: 'Consultation' },
  { value: 'AUTRE', label: 'Autre' }
];

// ============================================================================
// API HOOKS
// ============================================================================

const useInterventionStats = () => {
  return useQuery({
    queryKey: ['interventions', 'stats'],
    queryFn: async () => {
      const response = await api.get<{ data: InterventionStats }>('/v2/interventions/stats').then(r => r.data);
      return response as unknown as InterventionStats;
    }
  });
};

const useInterventions = (filters?: { statut?: string; type_intervention?: string; priorite?: string; client_id?: string }) => {
  return useQuery({
    queryKey: ['interventions', 'list', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.statut) params.append('statut', filters.statut);
      if (filters?.type_intervention) params.append('type_intervention', filters.type_intervention);
      if (filters?.priorite) params.append('priorite', filters.priorite);
      if (filters?.client_id) params.append('client_id', filters.client_id);
      const queryString = params.toString();
      const url = `/v2/interventions${queryString ? `?${queryString}` : ''}`;
      const response = await api.get<{ data: { items?: Intervention[] } }>(url).then(r => r.data);
      return (response as any)?.items || response as unknown as Intervention[];
    }
  });
};

const useDonneursOrdre = () => {
  return useQuery({
    queryKey: ['interventions', 'donneurs-ordre'],
    queryFn: async () => {
      const response = await api.get<{ data: DonneurOrdre[] }>('/v2/interventions/donneurs-ordre').then(r => r.data);
      return response as unknown as DonneurOrdre[];
    }
  });
};

const useClients = () => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await api.get<{ items: { id: string; name: string }[] }>('/v1/commercial/customers').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useIntervenants = () => {
  return useQuery({
    queryKey: ['intervenants'],
    queryFn: async () => {
      const response = await api.get<{ items: { id: string; first_name: string; last_name: string }[] }>('/v1/hr/employees').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useCreateIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Intervention>) => {
      return api.post('/v2/interventions', data).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    }
  });
};

const useUpdateStatut = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, statut }: { id: string; statut: string }) => {
      return api.put(`/v2/interventions/${id}`, { statut }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    }
  });
};

// ============================================================================
// DETAIL VIEW (BaseViewStandard)
// ============================================================================

interface InterventionDetailViewProps {
  intervention: Intervention;
  onClose: () => void;
}

const InterventionDetailView: React.FC<InterventionDetailViewProps> = ({ intervention, onClose }) => {
  const updateStatut = useUpdateStatut();
  const statutConfig = STATUT_CONFIG[intervention.statut];
  const prioriteConfig = PRIORITE_CONFIG[intervention.priorite];
  const typeConfig = TYPE_CONFIG[intervention.type_intervention];

  // Tabs definition
  const tabs: TabDefinition<Intervention>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <ClipboardList size={16} />,
      component: InterventionInfoTab
    },
    {
      id: 'lignes',
      label: 'Détails',
      icon: <Package size={16} />,
      component: InterventionLinesTab
    },
    {
      id: 'financier',
      label: 'Financier',
      icon: <Euro size={16} />,
      component: InterventionFinancialTab
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={16} />,
      badge: intervention.rapport ? 1 : 0,
      component: InterventionDocsTab
    },
    {
      id: 'historique',
      label: 'Historique',
      icon: <History size={16} />,
      component: InterventionHistoryTab
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: InterventionIATab
    }
  ];

  // InfoBar items
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'client',
      label: 'Client',
      value: intervention.client_name || '-',
      icon: <User size={14} />
    },
    {
      id: 'type',
      label: 'Type',
      value: typeConfig?.label || intervention.type_intervention,
      icon: <Wrench size={14} />
    },
    {
      id: 'date_prevue',
      label: 'Date prévue',
      value: intervention.date_prevue ? formatDate(intervention.date_prevue) : 'Non planifiée',
      icon: <Calendar size={14} />,
      valueColor: isLate(intervention) ? 'red' : undefined
    },
    {
      id: 'duree',
      label: 'Durée',
      value: formatDuration(intervention.duree_reelle_minutes || intervention.duree_prevue_minutes),
      icon: <Clock size={14} />
    }
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'resume',
      title: 'Résumé',
      items: [
        { id: 'reference', label: 'Référence', value: intervention.reference },
        { id: 'priorite', label: 'Priorité', value: prioriteConfig?.label || intervention.priorite },
        { id: 'intervenant', label: 'Intervenant', value: intervention.intervenant_name || 'Non assigné' },
        { id: 'created_at', label: 'Créé le', value: formatDate(intervention.created_at) }
      ]
    },
    {
      id: 'localisation',
      title: 'Localisation',
      items: [
        { id: 'adresse', label: 'Adresse', value: intervention.adresse_intervention || intervention.adresse_ligne1 || '-' },
        { id: 'ville', label: 'Ville', value: intervention.ville || '-' },
        { id: 'contact', label: 'Contact', value: intervention.contact_sur_place || '-' }
      ]
    },
    {
      id: 'facturation',
      title: 'Facturation',
      items: [
        { id: 'facturable', label: 'Facturable', value: intervention.facturable !== false ? 'Oui' : 'Non' },
        { id: 'montant_ht', label: 'Montant HT', value: formatCurrency(intervention.montant_ht || 0) },
        { id: 'facture', label: 'Facture', value: intervention.facture_reference || '-' }
      ]
    }
  ];

  // Header actions
  const headerActions: ActionDefinition[] = [
    {
      id: 'close',
      label: 'Fermer',
      variant: 'secondary' as const,
      onClick: onClose
    }
  ];

  // Footer actions based on status
  const primaryActions: ActionDefinition[] = [];

  if (intervention.statut === 'A_PLANIFIER') {
    primaryActions.push({
      id: 'planifier',
      label: 'Planifier',
      icon: <Calendar size={16} />,
      variant: 'primary' as const,
      onClick: () => {
        updateStatut.mutate({ id: intervention.id, statut: 'PLANIFIEE' });
        onClose();
      }
    });
  }

  if (intervention.statut === 'PLANIFIEE') {
    primaryActions.push({
      id: 'demarrer',
      label: 'Démarrer',
      icon: <Play size={16} />,
      variant: 'warning' as const,
      onClick: () => {
        updateStatut.mutate({ id: intervention.id, statut: 'EN_COURS' });
        onClose();
      }
    });
  }

  if (intervention.statut === 'EN_COURS') {
    primaryActions.push({
      id: 'terminer',
      label: 'Terminer',
      icon: <CheckCircle size={16} />,
      variant: 'success' as const,
      onClick: () => {
        updateStatut.mutate({ id: intervention.id, statut: 'TERMINEE' });
        onClose();
      }
    });
  }

  if (intervention.statut !== 'TERMINEE' && intervention.statut !== 'ANNULEE') {
    primaryActions.push({
      id: 'annuler',
      label: 'Annuler',
      icon: <X size={16} />,
      variant: 'danger' as const,
      onClick: () => {
        updateStatut.mutate({ id: intervention.id, statut: 'ANNULEE' });
        onClose();
      }
    });
  }

  return (
    <Modal isOpen={true} onClose={onClose} title="" size="xl">
      <BaseViewStandard<Intervention>
        title={intervention.titre}
        subtitle={`Intervention ${intervention.reference}`}
        status={{
          label: statutConfig?.label || intervention.statut,
          color: (statutConfig?.color || 'gray') as 'gray' | 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'yellow' | 'cyan',
          icon: statutConfig?.icon
        }}
        data={intervention}
        view="detail"
        tabs={tabs}
        infoBarItems={infoBarItems}
        sidebarSections={sidebarSections}
        headerActions={headerActions}
        primaryActions={primaryActions}
      />
    </Modal>
  );
};

// ============================================================================
// LIST VIEW
// ============================================================================

const InterventionsListView: React.FC<{ onNewIntervention?: () => void }> = ({ onNewIntervention }) => {
  const [filterStatut, setFilterStatut] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('');
  const [filterPriorite, setFilterPriorite] = useState<string>('');
  const [selectedIntervention, setSelectedIntervention] = useState<Intervention | null>(null);

  const { data: interventions = [], isLoading, error: interventionsError, refetch: refetchInterventions } = useInterventions({
    statut: filterStatut || undefined,
    type_intervention: filterType || undefined,
    priorite: filterPriorite || undefined
  });
  const updateStatut = useUpdateStatut();

  const columns: TableColumn<Intervention>[] = [
    { id: 'reference', header: 'Référence', accessor: 'reference', render: (v) => (
      <code className="font-mono text-sm">{v as string}</code>
    )},
    { id: 'titre', header: 'Titre', accessor: 'titre' },
    { id: 'client_name', header: 'Client', accessor: 'client_name', render: (v) => (v as string) || '-' },
    { id: 'type_intervention', header: 'Type', accessor: 'type_intervention', render: (v) => {
      const config = TYPE_CONFIG[v as InterventionType];
      return config?.label || (v as string);
    }},
    { id: 'priorite', header: 'Priorité', accessor: 'priorite', render: (v) => {
      const config = PRIORITE_CONFIG[v as InterventionPriorite];
      return <Badge color={config?.color || 'gray'}>{config?.label || (v as string)}</Badge>;
    }},
    { id: 'date_prevue', header: 'Date prévue', accessor: 'date_prevue', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'intervenant_name', header: 'Intervenant', accessor: 'intervenant_name', render: (v) => (v as string) || '-' },
    { id: 'statut', header: 'Statut', accessor: 'statut', render: (v) => {
      const config = STATUT_CONFIG[v as keyof typeof STATUT_CONFIG];
      return <Badge color={config?.color || 'gray'}>{config?.label || (v as string)}</Badge>;
    }},
    { id: 'duree_prevue_minutes', header: 'Durée', accessor: 'duree_prevue_minutes', render: (v) => (v as number) ? formatDuration(v as number) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_v, row) => (
      <div className="flex gap-1">
        <Button size="sm" variant="secondary" onClick={() => setSelectedIntervention(row)}>Détail</Button>
        {row.statut === 'A_PLANIFIER' && (
          <Button size="sm" variant="primary" onClick={() => updateStatut.mutate({ id: row.id, statut: 'PLANIFIEE' })}>Planifier</Button>
        )}
        {row.statut === 'PLANIFIEE' && (
          <Button size="sm" variant="warning" onClick={() => updateStatut.mutate({ id: row.id, statut: 'EN_COURS' })}>Démarrer</Button>
        )}
        {row.statut === 'EN_COURS' && (
          <Button size="sm" variant="success" onClick={() => updateStatut.mutate({ id: row.id, statut: 'TERMINEE' })}>Terminer</Button>
        )}
      </div>
    )}
  ];

  return (
    <>
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Interventions</h3>
          <div className="flex gap-2">
            <Select
              value={filterStatut}
              onChange={(v) => setFilterStatut(v)}
              options={[{ value: '', label: 'Tous statuts' }, ...STATUTS]}
              className="w-32"
            />
            <Select
              value={filterType}
              onChange={(v) => setFilterType(v)}
              options={[{ value: '', label: 'Tous types' }, ...TYPES_INTERVENTION]}
              className="w-36"
            />
            <Select
              value={filterPriorite}
              onChange={(v) => setFilterPriorite(v)}
              options={[{ value: '', label: 'Toutes priorités' }, ...PRIORITES]}
              className="w-36"
            />
            <Button onClick={onNewIntervention}>Nouvelle intervention</Button>
          </div>
        </div>
        <DataTable columns={columns} data={interventions} isLoading={isLoading} keyField="id" error={interventionsError instanceof Error ? interventionsError : null} onRetry={() => refetchInterventions()} />
      </Card>

      {/* Detail View with BaseViewStandard */}
      {selectedIntervention && (
        <InterventionDetailView
          intervention={selectedIntervention}
          onClose={() => setSelectedIntervention(null)}
        />
      )}

    </>
  );
};


// ============================================================================
// DONNEURS D'ORDRE VIEW
// ============================================================================

const DonneursOrdreView: React.FC = () => {
  const { data: donneursOrdre = [], isLoading, error: donneursError, refetch: refetchDonneurs } = useDonneursOrdre();

  const columns: TableColumn<DonneurOrdre>[] = [
    { id: 'nom', header: 'Nom', accessor: 'nom' },
    { id: 'entreprise', header: 'Entreprise', accessor: 'entreprise', render: (v) => (v as string) || '-' },
    { id: 'email', header: 'Email', accessor: 'email', render: (v) => (v as string) || '-' },
    { id: 'telephone', header: 'Téléphone', accessor: 'telephone', render: (v) => (v as string) || '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Donneurs d'ordre</h3>
        <Button>Nouveau donneur d'ordre</Button>
      </div>
      <DataTable columns={columns} data={donneursOrdre} isLoading={isLoading} keyField="id" error={donneursError instanceof Error ? donneursError : null} onRetry={() => refetchDonneurs()} />
    </Card>
  );
};

// ============================================================================
// PLANNING VIEW
// ============================================================================

const PlanningView: React.FC = () => {
  const { data: interventions = [], isLoading, error, refetch } = useInterventions({ statut: 'PLANIFIEE' });

  if (isLoading) {
    return <LoadingState onRetry={() => refetch()} message="Chargement du planning..." />;
  }

  if (error) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : 'Erreur lors du chargement du planning'}
        onRetry={() => refetch()}
      />
    );
  }

  // Grouper par date
  const interventionsByDate = interventions.reduce((acc: Record<string, Intervention[]>, int: Intervention) => {
    const date = int.date_prevue || 'Non planifiée';
    if (!acc[date]) acc[date] = [];
    acc[date].push(int);
    return acc;
  }, {});

  const dates = Object.keys(interventionsByDate).sort();

  return (
    <div className="space-y-4">
      {dates.length === 0 ? (
        <Card>
          <div className="text-center py-8 text-gray-500">
            Aucune intervention planifiée
          </div>
        </Card>
      ) : (
        dates.map(date => (
          <Card key={date}>
            <h4 className="font-semibold mb-3">
              {date === 'Non planifiée' ? date : formatDate(date)}
              <Badge color="blue">{interventionsByDate[date].length}</Badge>
            </h4>
            <div className="space-y-2">
              {interventionsByDate[date].map((int: Intervention) => (
                <div key={int.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium">{int.titre}</div>
                    <div className="text-sm text-gray-500">
                      {int.heure_prevue || '-'} - {int.client_name} - {int.intervenant_name || 'Non assigné'}
                    </div>
                  </div>
                  <Badge color={PRIORITE_CONFIG[int.priorite]?.color || 'gray'}>
                    {PRIORITE_CONFIG[int.priorite]?.label || int.priorite}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        ))
      )}
    </div>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'interventions' | 'planning' | 'donneurs-ordre' | 'form';

const InterventionsModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [editInterventionId, setEditInterventionId] = useState<string | undefined>(undefined);
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useInterventionStats();

  const navigateToForm = (interventionId?: string) => {
    setEditInterventionId(interventionId);
    setCurrentView('form');
  };

  const navigateToList = () => {
    setEditInterventionId(undefined);
    setCurrentView('interventions');
  };

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'interventions', label: 'Interventions' },
    { id: 'planning', label: 'Planning' },
    { id: 'donneurs-ordre', label: 'Donneurs d\'ordre' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'form':
        return (
          <InterventionFormView
            interventionId={editInterventionId}
            onBack={navigateToList}
            onSaved={() => navigateToList()}
          />
        );
      case 'interventions':
        return <InterventionsListView onNewIntervention={() => navigateToForm()} />;
      case 'planning':
        return <PlanningView />;
      case 'donneurs-ordre':
        return <DonneursOrdreView />;
      default:
        if (statsLoading) {
          return <LoadingState onRetry={() => refetchStats()} message="Chargement des statistiques..." />;
        }
        if (statsError) {
          return (
            <ErrorState
              message="Impossible de charger les statistiques"
              onRetry={() => refetchStats()}
            />
          );
        }
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="A planifier"
                value={String(stats?.a_planifier || 0)}
                icon={<ClipboardList size={20} />}
                variant="default"
                onClick={() => setCurrentView('interventions')}
              />
              <StatCard
                title="Planifiées"
                value={String(stats?.planifiees || 0)}
                icon={<Calendar size={20} />}
                variant="default"
                onClick={() => setCurrentView('planning')}
              />
              <StatCard
                title="En cours"
                value={String(stats?.en_cours || 0)}
                icon={<Wrench size={20} />}
                variant="warning"
              />
              <StatCard
                title="Terminées (semaine)"
                value={String(stats?.terminees_semaine || 0)}
                icon={<CheckCircle size={20} />}
                variant="success"
              />
            </Grid>

            <Grid cols={3}>
              <StatCard
                title="Terminées (mois)"
                value={String(stats?.terminees_mois || 0)}
                icon={<BarChart3 size={20} />}
                variant="default"
              />
              <StatCard
                title="Durée moyenne"
                value={stats?.duree_moyenne_minutes ? formatDuration(stats.duree_moyenne_minutes) : '-'}
                icon={<Clock size={20} />}
                variant="default"
              />
              <StatCard
                title="Aujourd'hui"
                value={String(stats?.interventions_jour || 0)}
                icon={<MapPin size={20} />}
                variant="success"
              />
            </Grid>
          </div>
        );
    }
  };

  // Form view renders its own PageWrapper
  if (currentView === 'form') {
    return renderContent();
  }

  return (
    <PageWrapper title="Interventions" subtitle="Gestion des interventions terrain">
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default InterventionsModule;
