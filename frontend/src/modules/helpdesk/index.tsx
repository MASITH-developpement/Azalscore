/**
 * AZALSCORE Module - Helpdesk
 * Gestion des tickets de support client
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input, TextArea } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import { BaseViewStandard } from '@ui/standards';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition, SemanticColor } from '@ui/standards';
import {
  Inbox, Settings, AlertTriangle, CheckCircle, Clock, Target, Star,
  MessageSquare, FileText, BookOpen, Sparkles, User, Edit
} from 'lucide-react';
import { LoadingState, ErrorState } from '@ui/components/StateViews';
import type { TableColumn } from '@/types';
import type { Ticket, TicketCategory, KnowledgeArticle, HelpdeskDashboard, TicketPriority, TicketStatus, TicketSource } from './types';
import {
  PRIORITIES, STATUSES, SOURCES,
  PRIORITY_CONFIG, STATUS_CONFIG, SOURCE_CONFIG,
  isTicketOverdue, isSlaDueSoon, getTimeUntilSla,
  getTicketAge, getPublicMessageCount
} from './types';
import { formatDate, formatDateTime, formatDuration } from '@/utils/formatters';
import {
  TicketInfoTab,
  TicketMessagesTab,
  TicketDocsTab,
  TicketHistoryTab,
  TicketKnowledgeTab,
  TicketIATab
} from './components';

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
  <nav className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </nav>
);

// ============================================================================
// HELPERS
// ============================================================================

const getStatusInfo = (statuses: typeof STATUSES, status: string) => {
  return statuses.find(s => s.value === status) || { label: status, color: 'gray' };
};

// ============================================================================
// API HOOKS
// ============================================================================

const useHelpdeskDashboard = () => {
  return useQuery({
    queryKey: ['helpdesk', 'dashboard'],
    queryFn: async () => {
      return api.get<HelpdeskDashboard>('/helpdesk/dashboard').then(r => r.data);
    }
  });
};

const useTicketCategories = () => {
  return useQuery({
    queryKey: ['helpdesk', 'categories'],
    queryFn: async () => {
      return api.get<TicketCategory[]>('/helpdesk/categories').then(r => r.data);
    }
  });
};

const useTickets = (filters?: { status?: string; priority?: string; category_id?: string }) => {
  return useQuery({
    queryKey: ['helpdesk', 'tickets', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.priority) params.append('priority', filters.priority);
      if (filters?.category_id) params.append('category_id', filters.category_id);
      const queryString = params.toString();
      const url = queryString ? `/helpdesk/tickets?${queryString}` : '/helpdesk/tickets';
      return api.get<Ticket[]>(url).then(r => r.data);
    }
  });
};

const useTicket = (id: string) => {
  return useQuery({
    queryKey: ['helpdesk', 'tickets', id],
    queryFn: async () => {
      return api.get<Ticket>(`/helpdesk/tickets/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

const useKnowledgeArticles = () => {
  return useQuery({
    queryKey: ['helpdesk', 'articles'],
    queryFn: async () => {
      return api.get<KnowledgeArticle[]>('/helpdesk/articles').then(r => r.data);
    }
  });
};

const useCreateTicket = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Ticket>) => {
      return api.post('/helpdesk/tickets', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['helpdesk'] })
  });
};

const useUpdateTicketStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/helpdesk/tickets/${id}`, { status }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['helpdesk'] })
  });
};

// ============================================================================
// TICKET DETAIL VIEW (BaseViewStandard)
// ============================================================================

interface TicketDetailViewProps {
  ticketId: string;
  onBack: () => void;
}

const TicketDetailView: React.FC<TicketDetailViewProps> = ({ ticketId, onBack }) => {
  const { data: ticket, isLoading, error, refetch } = useTicket(ticketId);

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <LoadingState onRetry={() => refetch()} message="Chargement du ticket..." />
      </PageWrapper>
    );
  }

  if (error || !ticket) {
    return (
      <PageWrapper title="Ticket non trouve">
        <ErrorState
          message="Ce ticket n'existe pas ou a ete supprime."
          onRetry={() => refetch()}
          onBack={onBack}
        />
      </PageWrapper>
    );
  }

  const priorityConfig = PRIORITY_CONFIG[ticket.priority];
  const statusConfig = STATUS_CONFIG[ticket.status];
  const isOverdue = isTicketOverdue(ticket);
  const slaDueSoon = isSlaDueSoon(ticket);
  const timeUntilSla = getTimeUntilSla(ticket);

  // Tabs definition
  const tabs: TabDefinition<Ticket>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <Inbox size={16} />,
      component: TicketInfoTab,
    },
    {
      id: 'messages',
      label: 'Messages',
      icon: <MessageSquare size={16} />,
      badge: getPublicMessageCount(ticket),
      component: TicketMessagesTab,
    },
    {
      id: 'docs',
      label: 'Documents',
      icon: <FileText size={16} />,
      badge: ticket.attachments?.length,
      component: TicketDocsTab,
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <Clock size={16} />,
      component: TicketHistoryTab,
    },
    {
      id: 'knowledge',
      label: 'Articles',
      icon: <BookOpen size={16} />,
      component: TicketKnowledgeTab,
    },
    {
      id: 'ia',
      label: 'IA',
      icon: <Sparkles size={16} />,
      component: TicketIATab,
    },
  ];

  // Info bar items
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'status',
      label: 'Statut',
      value: statusConfig.label,
      valueColor: statusConfig.color as SemanticColor,
    },
    {
      id: 'priority',
      label: 'Priorite',
      value: priorityConfig.label,
      valueColor: priorityConfig.color as SemanticColor,
    },
    {
      id: 'sla',
      label: 'SLA',
      value: isOverdue ? 'Depasse' : slaDueSoon ? 'Proche' : timeUntilSla || 'N/A',
      valueColor: isOverdue ? 'red' : slaDueSoon ? 'orange' : 'green',
    },
    {
      id: 'age',
      label: 'Age',
      value: getTicketAge(ticket),
      valueColor: 'gray' as SemanticColor,
    },
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'ticket',
      title: 'Ticket',
      items: [
        { id: 'number', label: 'Numero', value: ticket.number },
        { id: 'category', label: 'Categorie', value: ticket.category_name || '-' },
        { id: 'source', label: 'Source', value: SOURCE_CONFIG[ticket.source]?.label || ticket.source },
      ],
    },
    {
      id: 'client',
      title: 'Client',
      items: [
        { id: 'customer', label: 'Nom', value: ticket.customer_name || '-' },
        { id: 'email', label: 'Email', value: ticket.customer_email || '-' },
        { id: 'contact', label: 'Contact', value: ticket.contact_name || '-' },
      ],
    },
    {
      id: 'assignment',
      title: 'Assignation',
      items: [
        { id: 'assigned', label: 'Assigne a', value: ticket.assigned_to_name || 'Non assigne', highlight: !ticket.assigned_to_name },
        { id: 'created', label: 'Cree le', value: formatDate(ticket.created_at) },
      ],
    },
  ];

  // Header actions
  const headerActions: ActionDefinition[] = [
    {
      id: 'back',
      label: 'Retour',
      variant: 'ghost',
      onClick: onBack,
    },
    {
      id: 'edit',
      label: 'Modifier',
      icon: <Edit size={16} />,
      onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'editTicket', ticketId: ticket.id } })); },
    },
  ];

  return (
    <BaseViewStandard<Ticket>
      title={ticket.subject}
      subtitle={`Ticket ${ticket.number}`}
      status={{
        label: statusConfig.label,
        color: statusConfig.color as SemanticColor,
      }}
      data={ticket}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
    />
  );
};

// ============================================================================
// COMPOSANTS DE LISTE
// ============================================================================

const TicketsView: React.FC<{ onSelectTicket: (id: string) => void }> = ({ onSelectTicket }) => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterPriority, setFilterPriority] = useState<string>('');
  const [filterCategory, setFilterCategory] = useState<string>('');
  const { data: tickets = [], isLoading } = useTickets({
    status: filterStatus || undefined,
    priority: filterPriority || undefined,
    category_id: filterCategory || undefined
  });
  const { data: categories = [] } = useTicketCategories();
  const createTicket = useCreateTicket();
  const updateStatus = useUpdateTicketStatus();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<Ticket>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createTicket.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<Ticket>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'subject', header: 'Sujet', accessor: 'subject', render: (v, row: Ticket) => (
      <button
        className="text-blue-600 hover:underline text-left"
        onClick={() => onSelectTicket(row.id)}
      >
        {v as string}
      </button>
    )},
    { id: 'customer_name', header: 'Client', accessor: 'customer_name', render: (v) => (v as string) || '-' },
    { id: 'category_name', header: 'Categorie', accessor: 'category_name', render: (v) => (v as string) || '-' },
    { id: 'priority', header: 'Priorite', accessor: 'priority', render: (v) => {
      const info = getStatusInfo(PRIORITIES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'assigned_to_name', header: 'Assigne a', accessor: 'assigned_to_name', render: (v) => (v as string) || '-' },
    { id: 'created_at', header: 'Cree le', accessor: 'created_at', render: (v) => formatDate(v as string) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v, row: Ticket) => (
      <Select
        value={v as string}
        onChange={(val) => updateStatus.mutate({ id: row.id, status: val })}
        options={STATUSES}
        className="w-36"
      />
    )}
  ];

  return (
    <>
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Tickets</h3>
          <div className="flex gap-2">
            <Select
              value={filterCategory}
              onChange={(val) => setFilterCategory(val)}
              options={[{ value: '', label: 'Toutes categories' }, ...categories.map(c => ({ value: c.id, label: c.name }))]}
              className="w-40"
            />
            <Select
              value={filterPriority}
              onChange={(val) => setFilterPriority(val)}
              options={[{ value: '', label: 'Toutes priorites' }, ...PRIORITIES]}
              className="w-36"
            />
            <Select
              value={filterStatus}
              onChange={(val) => setFilterStatus(val)}
              options={[{ value: '', label: 'Tous statuts' }, ...STATUSES]}
              className="w-36"
            />
            <Button onClick={() => setShowModal(true)}>Nouveau ticket</Button>
          </div>
        </div>
        <DataTable columns={columns} data={tickets} isLoading={isLoading} keyField="id" filterable />
      </Card>

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouveau ticket" size="lg">
        <form onSubmit={handleSubmit}>
          <div className="azals-field">
            <label className="azals-field__label">Sujet</label>
            <Input
              value={formData.subject || ''}
              onChange={(v) => setFormData({ ...formData, subject: v })}
            />
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Description</label>
            <TextArea
              value={formData.description || ''}
              onChange={(v) => setFormData({ ...formData, description: v })}
              rows={4}
            />
          </div>
          <Grid cols={2}>
            <div className="azals-field">
              <label className="azals-field__label">Categorie</label>
              <Select
                value={formData.category_id || ''}
                onChange={(val) => setFormData({ ...formData, category_id: val })}
                options={[{ value: '', label: 'Selectionner...' }, ...categories.map(c => ({ value: c.id, label: c.name }))]}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Priorite</label>
              <Select
                value={formData.priority || 'MEDIUM'}
                onChange={(val) => setFormData({ ...formData, priority: val as TicketPriority })}
                options={PRIORITIES}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label className="azals-field__label">Source</label>
              <Select
                value={formData.source || 'WEB'}
                onChange={(val) => setFormData({ ...formData, source: val as TicketSource })}
                options={SOURCES}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Email client</label>
              <Input
                type="email"
                value={formData.customer_email || ''}
                onChange={(v) => setFormData({ ...formData, customer_email: v })}
              />
            </div>
          </Grid>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createTicket.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </>
  );
};

const CategoriesView: React.FC = () => {
  const { data: categories = [], isLoading } = useTicketCategories();

  const columns: TableColumn<TicketCategory>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'description', header: 'Description', accessor: 'description', render: (v) => (v as string) || '-' },
    { id: 'sla_hours', header: 'SLA', accessor: 'sla_hours', render: (v) => (v as number) ? `${v as number}h` : '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Categories</h3>
        <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createCategory' } })); }}>Nouvelle categorie</Button>
      </div>
      <DataTable columns={columns} data={categories} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

const KnowledgeBaseView: React.FC = () => {
  const { data: articles = [], isLoading } = useKnowledgeArticles();
  const [filterPublished, setFilterPublished] = useState<string>('');

  const filteredData = filterPublished
    ? articles.filter(a => filterPublished === 'true' ? a.is_published : !a.is_published)
    : articles;

  const columns: TableColumn<KnowledgeArticle>[] = [
    { id: 'title', header: 'Titre', accessor: 'title' },
    { id: 'category_name', header: 'Categorie', accessor: 'category_name', render: (v) => (v as string) || '-' },
    { id: 'tags', header: 'Tags', accessor: 'tags', render: (v) => (
      <div className="flex gap-1 flex-wrap">
        {((v as string[]) || []).slice(0, 3).map((tag, i) => (
          <Badge key={i} color="blue">{tag}</Badge>
        ))}
      </div>
    )},
    { id: 'views', header: 'Vues', accessor: 'views' },
    { id: 'is_published', header: 'Publie', accessor: 'is_published', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Base de connaissances</h3>
        <div className="flex gap-2">
          <Select
            value={filterPublished}
            onChange={(val) => setFilterPublished(val)}
            options={[
              { value: '', label: 'Tous' },
              { value: 'true', label: 'Publies' },
              { value: 'false', label: 'Brouillons' }
            ]}
            className="w-32"
          />
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createArticle' } })); }}>Nouvel article</Button>
        </div>
      </div>
      <DataTable columns={columns} data={filteredData} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'tickets' | 'categories' | 'knowledge' | 'ticket-detail';

interface NavState {
  view: View;
  ticketId?: string;
}

const HelpdeskModule: React.FC = () => {
  const [navState, setNavState] = useState<NavState>({ view: 'dashboard' });
  const { data: dashboard } = useHelpdeskDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'tickets', label: 'Tickets' },
    { id: 'categories', label: 'Categories' },
    { id: 'knowledge', label: 'Base de connaissances' }
  ];

  const handleSelectTicket = (ticketId: string) => {
    setNavState({ view: 'ticket-detail', ticketId });
  };

  const handleBackToList = () => {
    setNavState({ view: 'tickets' });
  };

  // Afficher la vue detail du ticket
  if (navState.view === 'ticket-detail' && navState.ticketId) {
    return (
      <TicketDetailView
        ticketId={navState.ticketId}
        onBack={handleBackToList}
      />
    );
  }

  const renderContent = () => {
    switch (navState.view) {
      case 'tickets':
        return <TicketsView onSelectTicket={handleSelectTicket} />;
      case 'categories':
        return <CategoriesView />;
      case 'knowledge':
        return <KnowledgeBaseView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Tickets ouverts"
                value={String(dashboard?.open_tickets || 0)}
                icon={<Inbox />}
                variant="default"
                onClick={() => setNavState({ view: 'tickets' })}
              />
              <StatCard
                title="En cours"
                value={String(dashboard?.in_progress_tickets || 0)}
                icon={<Settings />}
                variant="warning"
                onClick={() => setNavState({ view: 'tickets' })}
              />
              <StatCard
                title="En retard"
                value={String(dashboard?.overdue_tickets || 0)}
                icon={<AlertTriangle />}
                variant="danger"
                onClick={() => setNavState({ view: 'tickets' })}
              />
              <StatCard
                title="Resolus aujourd'hui"
                value={String(dashboard?.resolved_today || 0)}
                icon={<CheckCircle />}
                variant="success"
              />
            </Grid>
            <Grid cols={3}>
              <StatCard
                title="Temps moyen 1ere reponse"
                value={formatDuration(dashboard?.avg_response_time || 0)}
                icon={<Clock />}
                variant="default"
              />
              <StatCard
                title="Temps moyen resolution"
                value={formatDuration(dashboard?.avg_resolution_time || 0)}
                icon={<Target />}
                variant="default"
              />
              <StatCard
                title="Satisfaction client"
                value={`${((dashboard?.satisfaction_rate || 0) * 100).toFixed(0)}%`}
                icon={<Star />}
                variant="success"
              />
            </Grid>
            <Grid cols={2}>
              {dashboard?.tickets_by_priority && dashboard.tickets_by_priority.length > 0 && (
                <Card>
                  <h3 className="text-lg font-semibold mb-4">Tickets par priorite</h3>
                  <div className="space-y-2">
                    {dashboard.tickets_by_priority.map((item, i) => {
                      const info = getStatusInfo(PRIORITIES, item.priority);
                      return (
                        <div key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <Badge color={info.color}>{info.label}</Badge>
                          <span className="font-semibold">{item.count}</span>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}
              {dashboard?.tickets_by_category && dashboard.tickets_by_category.length > 0 && (
                <Card>
                  <h3 className="text-lg font-semibold mb-4">Tickets par categorie</h3>
                  <div className="space-y-2">
                    {dashboard.tickets_by_category.map((item, i) => (
                      <div key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>{item.category_name}</span>
                        <Badge color="blue">{item.count}</Badge>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Support" subtitle="Gestion des tickets et support client">
      <TabNav
        tabs={tabs}
        activeTab={navState.view === 'ticket-detail' ? 'tickets' : navState.view}
        onChange={(id) => setNavState({ view: id as View })}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default HelpdeskModule;
