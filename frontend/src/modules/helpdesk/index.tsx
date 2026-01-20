import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input, TextArea } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import { Inbox, Settings, AlertTriangle, CheckCircle, Clock, Target, Star } from 'lucide-react';
import type { TableColumn } from '@/types';

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
// TYPES
// ============================================================================

interface TicketCategory {
  id: string;
  code: string;
  name: string;
  description?: string;
  sla_hours?: number;
  is_active: boolean;
}

interface Ticket {
  id: string;
  number: string;
  subject: string;
  description: string;
  category_id?: string;
  category_name?: string;
  customer_id?: string;
  customer_name?: string;
  customer_email?: string;
  contact_id?: string;
  contact_name?: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  status: 'OPEN' | 'IN_PROGRESS' | 'WAITING' | 'RESOLVED' | 'CLOSED';
  assigned_to_id?: string;
  assigned_to_name?: string;
  source: 'EMAIL' | 'PHONE' | 'WEB' | 'CHAT' | 'OTHER';
  sla_due_date?: string;
  first_response_at?: string;
  resolved_at?: string;
  closed_at?: string;
  messages: TicketMessage[];
  created_at: string;
}

interface TicketMessage {
  id: string;
  content: string;
  is_internal: boolean;
  author_id: string;
  author_name?: string;
  created_at: string;
}

interface KnowledgeArticle {
  id: string;
  title: string;
  content: string;
  category_id?: string;
  category_name?: string;
  tags: string[];
  views: number;
  is_published: boolean;
  created_at: string;
}

interface HelpdeskDashboard {
  open_tickets: number;
  in_progress_tickets: number;
  overdue_tickets: number;
  resolved_today: number;
  avg_response_time: number;
  avg_resolution_time: number;
  satisfaction_rate: number;
  tickets_by_priority: { priority: string; count: number }[];
  tickets_by_category: { category_name: string; count: number }[];
}

// ============================================================================
// CONSTANTES
// ============================================================================

const PRIORITIES = [
  { value: 'LOW', label: 'Basse', color: 'gray' },
  { value: 'MEDIUM', label: 'Moyenne', color: 'blue' },
  { value: 'HIGH', label: 'Haute', color: 'orange' },
  { value: 'URGENT', label: 'Urgente', color: 'red' }
];

const STATUSES = [
  { value: 'OPEN', label: 'Ouvert', color: 'blue' },
  { value: 'IN_PROGRESS', label: 'En cours', color: 'orange' },
  { value: 'WAITING', label: 'En attente', color: 'yellow' },
  { value: 'RESOLVED', label: 'Résolu', color: 'green' },
  { value: 'CLOSED', label: 'Fermé', color: 'gray' }
];

const SOURCES = [
  { value: 'EMAIL', label: 'Email' },
  { value: 'PHONE', label: 'Téléphone' },
  { value: 'WEB', label: 'Web' },
  { value: 'CHAT', label: 'Chat' },
  { value: 'OTHER', label: 'Autre' }
];

// ============================================================================
// HELPERS
// ============================================================================

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

const getStatusInfo = (statuses: any[], status: string) => {
  return statuses.find(s => s.value === status) || { label: status, color: 'gray' };
};

const formatDuration = (hours: number): string => {
  if (hours < 1) return `${Math.round(hours * 60)}min`;
  if (hours < 24) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}j`;
};

const navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

// ============================================================================
// API HOOKS
// ============================================================================

const useHelpdeskDashboard = () => {
  return useQuery({
    queryKey: ['helpdesk', 'dashboard'],
    queryFn: async () => {
      return api.get<HelpdeskDashboard>('/v1/helpdesk/dashboard').then(r => r.data);
    }
  });
};

const useTicketCategories = () => {
  return useQuery({
    queryKey: ['helpdesk', 'categories'],
    queryFn: async () => {
      return api.get<TicketCategory[]>('/v1/helpdesk/categories').then(r => r.data);
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
      const url = queryString ? `/v1/helpdesk/tickets?${queryString}` : '/v1/helpdesk/tickets';
      return api.get<Ticket[]>(url).then(r => r.data);
    }
  });
};

const useTicket = (id: string) => {
  return useQuery({
    queryKey: ['helpdesk', 'tickets', id],
    queryFn: async () => {
      return api.get<Ticket>(`/v1/helpdesk/tickets/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

const useKnowledgeArticles = () => {
  return useQuery({
    queryKey: ['helpdesk', 'articles'],
    queryFn: async () => {
      return api.get<KnowledgeArticle[]>('/v1/helpdesk/articles').then(r => r.data);
    }
  });
};

const useCreateTicket = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Ticket>) => {
      return api.post('/v1/helpdesk/tickets', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['helpdesk'] })
  });
};

const useUpdateTicketStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/v1/helpdesk/tickets/${id}`, { status }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['helpdesk'] })
  });
};

const useAssignTicket = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, assignedToId }: { id: string; assignedToId: string }) => {
      return api.post(`/v1/helpdesk/tickets/${id}/assign`, { assigned_to_id: assignedToId }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['helpdesk'] })
  });
};

const useAddMessage = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ ticketId, content, isInternal }: { ticketId: string; content: string; isInternal: boolean }) => {
      return api.post(`/v1/helpdesk/tickets/${ticketId}/messages`, { content, is_internal: isInternal }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['helpdesk'] })
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const TicketsView: React.FC = () => {
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
  const [selectedTicket, setSelectedTicket] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createTicket.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<Ticket>[] = [
    { id: 'number', header: 'N°', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'subject', header: 'Sujet', accessor: 'subject', render: (v, row: Ticket) => (
      <button
        className="text-blue-600 hover:underline text-left"
        onClick={() => setSelectedTicket(row.id)}
      >
        {v as string}
      </button>
    )},
    { id: 'customer_name', header: 'Client', accessor: 'customer_name', render: (v, row: Ticket) => (v as string) ? (
      <button
        className="text-blue-600 hover:underline"
        onClick={() => navigateTo('crm', { view: 'customers', id: row.customer_id })}
      >
        {v as string}
      </button>
    ) : '-' },
    { id: 'category_name', header: 'Catégorie', accessor: 'category_name', render: (v) => (v as string) || '-' },
    { id: 'priority', header: 'Priorité', accessor: 'priority', render: (v) => {
      const info = getStatusInfo(PRIORITIES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'assigned_to_name', header: 'Assigné à', accessor: 'assigned_to_name', render: (v) => (v as string) || '-' },
    { id: 'created_at', header: 'Créé le', accessor: 'created_at', render: (v) => formatDate(v as string) },
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
              options={[{ value: '', label: 'Toutes catégories' }, ...categories.map(c => ({ value: c.id, label: c.name }))]}
              className="w-40"
            />
            <Select
              value={filterPriority}
              onChange={(val) => setFilterPriority(val)}
              options={[{ value: '', label: 'Toutes priorités' }, ...PRIORITIES]}
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
        <DataTable columns={columns} data={tickets} isLoading={isLoading} keyField="id" />
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
              <label className="azals-field__label">Catégorie</label>
              <Select
                value={formData.category_id || ''}
                onChange={(val) => setFormData({ ...formData, category_id: val })}
                options={[{ value: '', label: 'Sélectionner...' }, ...categories.map(c => ({ value: c.id, label: c.name }))]}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Priorité</label>
              <Select
                value={formData.priority || 'MEDIUM'}
                onChange={(val) => setFormData({ ...formData, priority: val as Ticket['priority'] })}
                options={PRIORITIES}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label className="azals-field__label">Source</label>
              <Select
                value={formData.source || 'WEB'}
                onChange={(val) => setFormData({ ...formData, source: val as Ticket['source'] })}
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
            <Button type="submit" isLoading={createTicket.isPending}>Créer</Button>
          </div>
        </form>
      </Modal>

      {selectedTicket && (
        <TicketDetailModal ticketId={selectedTicket} onClose={() => setSelectedTicket(null)} />
      )}
    </>
  );
};

const TicketDetailModal: React.FC<{ ticketId: string; onClose: () => void }> = ({ ticketId, onClose }) => {
  const { data: ticket, isLoading } = useTicket(ticketId);
  const addMessage = useAddMessage();
  const [newMessage, setNewMessage] = useState('');
  const [isInternal, setIsInternal] = useState(false);

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;
    await addMessage.mutateAsync({ ticketId, content: newMessage, isInternal });
    setNewMessage('');
  };

  if (isLoading || !ticket) return null;

  return (
    <Modal isOpen={true} onClose={onClose} title={`Ticket ${ticket.number}`} size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-500">Sujet</span>
            <p className="font-medium">{ticket.subject}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Client</span>
            <p className="font-medium">{ticket.customer_name || ticket.customer_email || '-'}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Statut</span>
            <Badge color={getStatusInfo(STATUSES, ticket.status).color}>
              {getStatusInfo(STATUSES, ticket.status).label}
            </Badge>
          </div>
          <div>
            <span className="text-sm text-gray-500">Priorité</span>
            <Badge color={getStatusInfo(PRIORITIES, ticket.priority).color}>
              {getStatusInfo(PRIORITIES, ticket.priority).label}
            </Badge>
          </div>
        </div>

        <div>
          <span className="text-sm text-gray-500">Description</span>
          <p className="mt-1">{ticket.description}</p>
        </div>

        <div>
          <h4 className="font-medium mb-2">Messages</h4>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {(ticket.messages || []).map((msg) => (
              <div
                key={msg.id}
                className={`p-3 rounded ${msg.is_internal ? 'bg-yellow-50 border border-yellow-200' : 'bg-gray-50'}`}
              >
                <div className="flex justify-between text-sm text-gray-500">
                  <span>{msg.author_name}</span>
                  <span>{formatDateTime(msg.created_at)}</span>
                </div>
                <p className="mt-1">{msg.content}</p>
                {msg.is_internal && <Badge color="yellow">Note interne</Badge>}
              </div>
            ))}
          </div>
        </div>

        <div className="border-t pt-4">
          <div className="azals-field">
            <label className="azals-field__label">Nouvelle réponse</label>
            <TextArea
              value={newMessage}
              onChange={(v) => setNewMessage(v)}
              rows={3}
            />
          </div>
          <div className="flex items-center justify-between mt-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isInternal}
                onChange={(e) => setIsInternal(e.target.checked)}
              />
              <span className="text-sm">Note interne</span>
            </label>
            <Button onClick={handleSendMessage} isLoading={addMessage.isPending}>
              Envoyer
            </Button>
          </div>
        </div>
      </div>
    </Modal>
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
        <h3 className="text-lg font-semibold">Catégories</h3>
        <Button>Nouvelle catégorie</Button>
      </div>
      <DataTable columns={columns} data={categories} isLoading={isLoading} keyField="id" />
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
    { id: 'category_name', header: 'Catégorie', accessor: 'category_name', render: (v) => (v as string) || '-' },
    { id: 'tags', header: 'Tags', accessor: 'tags', render: (v) => (
      <div className="flex gap-1 flex-wrap">
        {((v as string[]) || []).slice(0, 3).map((tag, i) => (
          <Badge key={i} color="blue">{tag}</Badge>
        ))}
      </div>
    )},
    { id: 'views', header: 'Vues', accessor: 'views' },
    { id: 'is_published', header: 'Publié', accessor: 'is_published', render: (v) => (
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
              { value: 'true', label: 'Publiés' },
              { value: 'false', label: 'Brouillons' }
            ]}
            className="w-32"
          />
          <Button>Nouvel article</Button>
        </div>
      </div>
      <DataTable columns={columns} data={filteredData} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'tickets' | 'categories' | 'knowledge';

const HelpdeskModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: dashboard } = useHelpdeskDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'tickets', label: 'Tickets' },
    { id: 'categories', label: 'Catégories' },
    { id: 'knowledge', label: 'Base de connaissances' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'tickets':
        return <TicketsView />;
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
                onClick={() => setCurrentView('tickets')}
              />
              <StatCard
                title="En cours"
                value={String(dashboard?.in_progress_tickets || 0)}
                icon={<Settings />}
                variant="warning"
                onClick={() => setCurrentView('tickets')}
              />
              <StatCard
                title="En retard"
                value={String(dashboard?.overdue_tickets || 0)}
                icon={<AlertTriangle />}
                variant="danger"
                onClick={() => setCurrentView('tickets')}
              />
              <StatCard
                title="Résolus aujourd'hui"
                value={String(dashboard?.resolved_today || 0)}
                icon={<CheckCircle />}
                variant="success"
              />
            </Grid>
            <Grid cols={3}>
              <StatCard
                title="Temps moyen 1ère réponse"
                value={formatDuration(dashboard?.avg_response_time || 0)}
                icon={<Clock />}
                variant="default"
              />
              <StatCard
                title="Temps moyen résolution"
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
                  <h3 className="text-lg font-semibold mb-4">Tickets par priorité</h3>
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
                  <h3 className="text-lg font-semibold mb-4">Tickets par catégorie</h3>
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
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default HelpdeskModule;
