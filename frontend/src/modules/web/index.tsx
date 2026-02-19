/**
 * AZALSCORE Module - Site Web / Configuration UI
 * Gestion des thèmes, widgets, dashboards, pages personnalisées
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText, Palette, LayoutGrid,
  Plus, Edit, Trash2, Eye, Menu, Layers
} from 'lucide-react';
import { Routes, Route } from 'react-router-dom';
import { api } from '@core/api-client';
import { Button, Modal } from '@ui/actions';
import { StatCard } from '@ui/dashboards';
import { Input, TextArea } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';

// ============================================================================
// TYPES
// ============================================================================

interface Theme {
  id: string;
  name: string;
  description?: string;
  is_default: boolean;
  is_active: boolean;
  primary_color: string;
  secondary_color: string;
  created_at: string;
}

interface Widget {
  id: string;
  name: string;
  widget_type: string;
  config: Record<string, unknown>;
  is_active: boolean;
  position: number;
}

interface Dashboard {
  id: string;
  name: string;
  description?: string;
  is_default: boolean;
  is_public: boolean;
  layout: string;
  widgets: string[];
}

interface CustomPage {
  id: string;
  slug: string;
  title: string;
  content?: string;
  is_published: boolean;
  created_at: string;
}

interface MenuItem {
  id: string;
  label: string;
  icon?: string;
  path?: string;
  parent_id?: string;
  position: number;
  is_visible: boolean;
}

// ============================================================================
// API HOOKS
// ============================================================================

const useThemes = () => useQuery({
  queryKey: ['web', 'themes'],
  queryFn: () => api.get<{ items: Theme[] }>('/web/themes').then(r => r.data.items || [])
});

const useWidgets = () => useQuery({
  queryKey: ['web', 'widgets'],
  queryFn: () => api.get<{ items: Widget[] }>('/web/widgets').then(r => r.data.items || [])
});

const useDashboards = () => useQuery({
  queryKey: ['web', 'dashboards'],
  queryFn: () => api.get<{ items: Dashboard[] }>('/web/dashboards').then(r => r.data.items || [])
});

const usePages = () => useQuery({
  queryKey: ['web', 'pages'],
  queryFn: () => api.get<{ items: CustomPage[] }>('/web/pages').then(r => r.data.items || [])
});

const useMenuItems = () => useQuery({
  queryKey: ['web', 'menu-items'],
  queryFn: () => api.get<MenuItem[]>('/web/menu-items').then(r => r.data || [])
});

const useCreateTheme = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Theme>) => api.post('/web/themes', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['web', 'themes'] })
  });
};

const useCreatePage = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<CustomPage>) => api.post('/web/pages', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['web', 'pages'] })
  });
};

const useDeletePage = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/web/pages/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['web', 'pages'] })
  });
};

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavProps {
  tabs: { id: string; label: string; icon?: React.ReactNode }[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <div className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.icon && <span className="mr-2">{tab.icon}</span>}
        {tab.label}
      </button>
    ))}
  </div>
);

// ============================================================================
// THEMES VIEW
// ============================================================================

const ThemesView: React.FC = () => {
  const { data: themes = [], isLoading } = useThemes();
  const createTheme = useCreateTheme();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', primary_color: '#3B82F6', secondary_color: '#10B981' });

  const handleCreate = useCallback(() => {
    createTheme.mutate(formData, { onSuccess: () => { setShowModal(false); setFormData({ name: '', primary_color: '#3B82F6', secondary_color: '#10B981' }); } });
  }, [createTheme, formData]);

  const handleCloseModal = useCallback(() => setShowModal(false), []);

  const columns: TableColumn<Theme>[] = [
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'primary_color', header: 'Couleur primaire', accessor: 'primary_color', render: (v) => (
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded" style={{ backgroundColor: v as string }} />
        <code>{v as string}</code>
      </div>
    )},
    { id: 'is_default', header: 'Défaut', accessor: 'is_default', render: (v) => v ? <Badge color="blue">Défaut</Badge> : null },
    { id: 'is_active', header: 'Statut', accessor: 'is_active', render: (v) => <Badge color={v ? 'green' : 'gray'}>{v ? 'Actif' : 'Inactif'}</Badge> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2"><Palette size={20} /> Thèmes</h3>
        <Button onClick={() => setShowModal(true)}><Plus size={16} className="mr-2" />Nouveau thème</Button>
      </div>
      <DataTable columns={columns} data={themes} isLoading={isLoading} keyField="id" filterable />
      <Modal isOpen={showModal} onClose={handleCloseModal} title="Nouveau thème">
        <div className="space-y-4">
          <div className="azals-field">
            <label>Nom du thème</label>
            <Input value={formData.name} onChange={(v: string) => setFormData(p => ({ ...p, name: v }))} placeholder="Mon thème" />
          </div>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Couleur primaire</label>
              <input type="color" value={formData.primary_color} onChange={(e) => setFormData(p => ({ ...p, primary_color: e.target.value }))} className="w-full h-10" />
            </div>
            <div className="azals-field">
              <label>Couleur secondaire</label>
              <input type="color" value={formData.secondary_color} onChange={(e) => setFormData(p => ({ ...p, secondary_color: e.target.value }))} className="w-full h-10" />
            </div>
          </Grid>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="secondary" onClick={handleCloseModal}>Annuler</Button>
            <Button onClick={handleCreate} isLoading={createTheme.isPending}>Créer</Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
};

// ============================================================================
// WIDGETS VIEW
// ============================================================================

const WidgetsView: React.FC = () => {
  const { data: widgets = [], isLoading } = useWidgets();

  const columns: TableColumn<Widget>[] = [
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'widget_type', header: 'Type', accessor: 'widget_type', render: (v) => <Badge color="purple">{v as string}</Badge> },
    { id: 'position', header: 'Position', accessor: 'position' },
    { id: 'is_active', header: 'Statut', accessor: 'is_active', render: (v) => <Badge color={v ? 'green' : 'gray'}>{v ? 'Actif' : 'Inactif'}</Badge> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2"><Layers size={20} /> Widgets</h3>
        <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'web', type: 'widget' } })); }}><Plus size={16} className="mr-2" />Nouveau widget</Button>
      </div>
      <DataTable columns={columns} data={widgets} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

// ============================================================================
// DASHBOARDS VIEW
// ============================================================================

const DashboardsView: React.FC = () => {
  const { data: dashboards = [], isLoading } = useDashboards();

  const columns: TableColumn<Dashboard>[] = [
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'description', header: 'Description', accessor: 'description' },
    { id: 'is_default', header: 'Défaut', accessor: 'is_default', render: (v) => v ? <Badge color="blue">Défaut</Badge> : null },
    { id: 'is_public', header: 'Public', accessor: 'is_public', render: (v) => <Badge color={v ? 'green' : 'gray'}>{v ? 'Public' : 'Privé'}</Badge> },
    { id: 'widgets', header: 'Widgets', accessor: 'widgets', render: (v) => <span>{(v as string[])?.length || 0} widgets</span> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2"><LayoutGrid size={20} /> Tableaux de bord</h3>
        <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'web', type: 'dashboard' } })); }}><Plus size={16} className="mr-2" />Nouveau dashboard</Button>
      </div>
      <DataTable columns={columns} data={dashboards} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

// ============================================================================
// PAGES VIEW
// ============================================================================

const PagesView: React.FC = () => {
  const { data: pages = [], isLoading } = usePages();
  const createPage = useCreatePage();
  const deletePage = useDeletePage();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ title: '', slug: '', content: '' });

  const handleCreate = useCallback(() => {
    createPage.mutate(formData, { onSuccess: () => { setShowModal(false); setFormData({ title: '', slug: '', content: '' }); } });
  }, [createPage, formData]);

  const handleDelete = useCallback((id: string) => {
    if (window.confirm('Supprimer cette page ?')) deletePage.mutate(id);
  }, [deletePage]);

  const handleCloseModal = useCallback(() => setShowModal(false), []);

  const columns: TableColumn<CustomPage>[] = [
    { id: 'title', header: 'Titre', accessor: 'title' },
    { id: 'slug', header: 'URL', accessor: 'slug', render: (v) => <code>/{v as string}</code> },
    { id: 'is_published', header: 'Statut', accessor: 'is_published', render: (v) => <Badge color={v ? 'green' : 'yellow'}>{v ? 'Publié' : 'Brouillon'}</Badge> },
    { id: 'created_at', header: 'Créé le', accessor: 'created_at', render: (v) => new Date(v as string).toLocaleDateString('fr-FR') },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-2">
        <Button size="sm" variant="ghost" onClick={() => { window.open(`/web/pages/${(row as CustomPage).id}/preview`, '_blank'); }}><Eye size={14} /></Button>
        <Button size="sm" variant="ghost" onClick={() => { window.dispatchEvent(new CustomEvent('azals:edit', { detail: { module: 'web', type: 'page', id: (row as CustomPage).id } })); }}><Edit size={14} /></Button>
        <Button size="sm" variant="ghost" onClick={() => handleDelete((row as CustomPage).id)}><Trash2 size={14} /></Button>
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2"><FileText size={20} /> Pages personnalisées</h3>
        <Button onClick={() => setShowModal(true)}><Plus size={16} className="mr-2" />Nouvelle page</Button>
      </div>
      <DataTable columns={columns} data={pages} isLoading={isLoading} keyField="id" filterable />
      <Modal isOpen={showModal} onClose={handleCloseModal} title="Nouvelle page">
        <div className="space-y-4">
          <div className="azals-field">
            <label>Titre</label>
            <Input value={formData.title} onChange={(v: string) => setFormData(p => ({ ...p, title: v }))} placeholder="Ma page" />
          </div>
          <div className="azals-field">
            <label>Slug (URL)</label>
            <Input value={formData.slug} onChange={(v: string) => setFormData(p => ({ ...p, slug: v }))} placeholder="ma-page" />
          </div>
          <div className="azals-field">
            <label>Contenu</label>
            <TextArea value={formData.content} onChange={(v: string) => setFormData(p => ({ ...p, content: v }))} rows={6} placeholder="Contenu de la page..." />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="secondary" onClick={handleCloseModal}>Annuler</Button>
            <Button onClick={handleCreate} isLoading={createPage.isPending}>Créer</Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
};

// ============================================================================
// MENU VIEW
// ============================================================================

const MenuView: React.FC = () => {
  const { data: menuItems = [], isLoading } = useMenuItems();

  const columns: TableColumn<MenuItem>[] = [
    { id: 'label', header: 'Label', accessor: 'label' },
    { id: 'icon', header: 'Icône', accessor: 'icon', render: (v) => v ? <code>{v as string}</code> : '-' },
    { id: 'path', header: 'Chemin', accessor: 'path', render: (v) => v ? <code>{v as string}</code> : '-' },
    { id: 'position', header: 'Position', accessor: 'position' },
    { id: 'is_visible', header: 'Visible', accessor: 'is_visible', render: (v) => <Badge color={v ? 'green' : 'gray'}>{v ? 'Oui' : 'Non'}</Badge> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2"><Menu size={20} /> Menu de navigation</h3>
        <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'web', type: 'menu' } })); }}><Plus size={16} className="mr-2" />Nouveau menu</Button>
      </div>
      <DataTable columns={columns} data={menuItems} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

// ============================================================================
// MAIN DASHBOARD
// ============================================================================

const WebDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('themes');
  const { data: themes = [] } = useThemes();
  const { data: widgets = [] } = useWidgets();
  const { data: dashboards = [] } = useDashboards();
  const { data: pages = [] } = usePages();

  const tabs = [
    { id: 'themes', label: 'Thèmes', icon: <Palette size={16} /> },
    { id: 'widgets', label: 'Widgets', icon: <Layers size={16} /> },
    { id: 'dashboards', label: 'Dashboards', icon: <LayoutGrid size={16} /> },
    { id: 'pages', label: 'Pages', icon: <FileText size={16} /> },
    { id: 'menu', label: 'Menu', icon: <Menu size={16} /> }
  ];

  return (
    <PageWrapper title="Configuration Web" subtitle="Thèmes, widgets, pages et navigation">
      <section className="azals-section">
        <Grid cols={4} gap="md">
          <StatCard title="Thèmes" value={themes.length} icon={<Palette />} />
          <StatCard title="Widgets" value={widgets.length} icon={<Layers />} />
          <StatCard title="Dashboards" value={dashboards.length} icon={<LayoutGrid />} />
          <StatCard title="Pages" value={pages.length} icon={<FileText />} />
        </Grid>
      </section>

      <section className="azals-section">
        <TabNav tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        <div className="mt-4">
          {activeTab === 'themes' && <ThemesView />}
          {activeTab === 'widgets' && <WidgetsView />}
          {activeTab === 'dashboards' && <DashboardsView />}
          {activeTab === 'pages' && <PagesView />}
          {activeTab === 'menu' && <MenuView />}
        </div>
      </section>
    </PageWrapper>
  );
};

// ============================================================================
// ROUTES
// ============================================================================

export const WebRoutes: React.FC = () => (
  <Routes>
    <Route index element={<WebDashboard />} />
    <Route path="themes" element={<WebDashboard />} />
    <Route path="widgets" element={<WebDashboard />} />
    <Route path="pages" element={<WebDashboard />} />
  </Routes>
);

export default WebRoutes;
