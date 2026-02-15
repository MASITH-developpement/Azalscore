/**
 * AZALSCORE Module - Mobile PWA
 * Configuration et fonctionnalités mobiles
 * Appareils, sessions, notifications, synchronisation
 */

import React, { useState, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import { useUIStore } from '@ui/states';
import {
  Smartphone, Bell, Wifi, Settings, Download, QrCode, RefreshCw,
  Trash2, Eye, Monitor, Tablet, Watch, Power, Activity, Clock,
  CheckCircle, XCircle, AlertTriangle, Send
} from 'lucide-react';
import type { TableColumn } from '@/types';

// ============================================================================
// TYPES
// ============================================================================

interface Device {
  id: string;
  device_type: 'mobile' | 'tablet' | 'desktop' | 'watch';
  device_name: string;
  platform: string;
  os_version?: string;
  app_version?: string;
  push_token?: string;
  is_active: boolean;
  last_seen_at?: string;
  created_at: string;
}

interface MobileSession {
  id: string;
  device_id: string;
  is_active: boolean;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  expires_at?: string;
}

interface Notification {
  id: string;
  title: string;
  body: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  data?: Record<string, unknown>;
}

interface MobileStats {
  total_devices: number;
  active_devices: number;
  total_sessions: number;
  active_sessions: number;
  unread_notifications: number;
  last_sync_at?: string;
}

interface Preferences {
  notifications_enabled: boolean;
  dark_mode: boolean;
  offline_mode: boolean;
  auto_sync: boolean;
  sync_interval_minutes: number;
  language: string;
}

// ============================================================================
// API HOOKS
// ============================================================================

const useMobileStats = () => useQuery({
  queryKey: ['mobile', 'stats'],
  queryFn: () => api.get<MobileStats>('/v3/mobile/stats').then(r => r.data)
});

const useDevices = () => useQuery({
  queryKey: ['mobile', 'devices'],
  queryFn: () => api.get<Device[]>('/v3/mobile/devices').then(r => r.data || [])
});

const useSessions = () => useQuery({
  queryKey: ['mobile', 'sessions'],
  queryFn: () => api.get<MobileSession[]>('/v3/mobile/sessions').then(r => r.data || [])
});

const useNotifications = () => useQuery({
  queryKey: ['mobile', 'notifications'],
  queryFn: () => api.get<Notification[]>('/v3/mobile/notifications').then(r => r.data || [])
});

const usePreferences = () => useQuery({
  queryKey: ['mobile', 'preferences'],
  queryFn: () => api.get<Preferences>('/v3/mobile/preferences').then(r => r.data)
});

const useDeleteDevice = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/v3/mobile/devices/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mobile', 'devices'] })
  });
};

const useDeleteSession = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/v3/mobile/sessions/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mobile', 'sessions'] })
  });
};

const useMarkNotificationRead = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.put(`/v3/mobile/notifications/${id}/read`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mobile', 'notifications'] })
  });
};

const useMarkAllNotificationsRead = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.put('/v3/mobile/notifications/read-all'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mobile', 'notifications'] })
  });
};

const useUpdatePreferences = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Preferences>) => api.put('/v3/mobile/preferences', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mobile', 'preferences'] })
  });
};

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

const DeviceIcon: React.FC<{ type: string }> = ({ type }) => {
  switch (type) {
    case 'mobile': return <Smartphone size={20} />;
    case 'tablet': return <Tablet size={20} />;
    case 'watch': return <Watch size={20} />;
    default: return <Monitor size={20} />;
  }
};

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
// DEVICES VIEW
// ============================================================================

const DevicesView: React.FC = () => {
  const { data: devices = [], isLoading } = useDevices();
  const deleteDevice = useDeleteDevice();

  const handleDelete = useCallback((id: string) => {
    if (window.confirm('Supprimer cet appareil ?')) deleteDevice.mutate(id);
  }, [deleteDevice]);

  const columns: TableColumn<Device>[] = [
    { id: 'device_type', header: 'Type', accessor: 'device_type', render: (v) => <DeviceIcon type={v as string} /> },
    { id: 'device_name', header: 'Nom', accessor: 'device_name' },
    { id: 'platform', header: 'Plateforme', accessor: 'platform', render: (v, row) => (
      <div>
        <div>{v as string}</div>
        <div className="text-xs text-gray-500">{(row as Device).os_version}</div>
      </div>
    )},
    { id: 'app_version', header: 'Version App', accessor: 'app_version' },
    { id: 'is_active', header: 'Statut', accessor: 'is_active', render: (v) => (
      <Badge color={v ? 'green' : 'gray'}>{v ? 'Actif' : 'Inactif'}</Badge>
    )},
    { id: 'last_seen_at', header: 'Dernière activité', accessor: 'last_seen_at', render: (v) => (
      v ? new Date(v as string).toLocaleString('fr-FR') : '-'
    )},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <Button size="sm" variant="ghost" onClick={() => handleDelete((row as Device).id)}>
        <Trash2 size={14} />
      </Button>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2"><Smartphone size={20} /> Appareils enregistrés</h3>
      </div>
      <DataTable columns={columns} data={devices} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

// ============================================================================
// SESSIONS VIEW
// ============================================================================

const SessionsView: React.FC = () => {
  const { data: sessions = [], isLoading } = useSessions();
  const deleteSession = useDeleteSession();

  const handleDelete = useCallback((id: string) => {
    if (window.confirm('Terminer cette session ?')) deleteSession.mutate(id);
  }, [deleteSession]);

  const columns: TableColumn<MobileSession>[] = [
    { id: 'device_id', header: 'Appareil', accessor: 'device_id', render: (v) => <code className="text-xs">{(v as string).slice(0, 8)}...</code> },
    { id: 'ip_address', header: 'Adresse IP', accessor: 'ip_address' },
    { id: 'is_active', header: 'Statut', accessor: 'is_active', render: (v) => (
      <Badge color={v ? 'green' : 'gray'}>{v ? 'Active' : 'Expirée'}</Badge>
    )},
    { id: 'created_at', header: 'Créée le', accessor: 'created_at', render: (v) => new Date(v as string).toLocaleString('fr-FR') },
    { id: 'expires_at', header: 'Expire le', accessor: 'expires_at', render: (v) => v ? new Date(v as string).toLocaleString('fr-FR') : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <Button size="sm" variant="ghost" onClick={() => handleDelete((row as MobileSession).id)}>
        <Power size={14} />
      </Button>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2"><Activity size={20} /> Sessions actives</h3>
      </div>
      <DataTable columns={columns} data={sessions} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

// ============================================================================
// NOTIFICATIONS VIEW
// ============================================================================

const NotificationsView: React.FC = () => {
  const { data: notifications = [], isLoading } = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const columns: TableColumn<Notification>[] = [
    { id: 'is_read', header: '', accessor: 'is_read', render: (v) => v ? <CheckCircle size={16} className="text-gray-400" /> : <Bell size={16} className="text-blue-500" /> },
    { id: 'title', header: 'Titre', accessor: 'title', render: (v, row) => (
      <div className={(row as Notification).is_read ? 'text-gray-500' : 'font-medium'}>
        {v as string}
      </div>
    )},
    { id: 'body', header: 'Message', accessor: 'body', render: (v) => (
      <div className="text-sm text-gray-600 truncate max-w-xs">{v as string}</div>
    )},
    { id: 'notification_type', header: 'Type', accessor: 'notification_type', render: (v) => <Badge color="purple">{v as string}</Badge> },
    { id: 'created_at', header: 'Date', accessor: 'created_at', render: (v) => new Date(v as string).toLocaleString('fr-FR') },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      !((row as Notification).is_read) && (
        <Button size="sm" variant="ghost" onClick={() => markRead.mutate((row as Notification).id)}>
          <Eye size={14} />
        </Button>
      )
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Bell size={20} /> Notifications
          {unreadCount > 0 && <Badge color="red">{unreadCount}</Badge>}
        </h3>
        {unreadCount > 0 && (
          <Button variant="secondary" onClick={() => markAllRead.mutate()} isLoading={markAllRead.isPending}>
            <CheckCircle size={16} className="mr-2" /> Tout marquer comme lu
          </Button>
        )}
      </div>
      <DataTable columns={columns} data={notifications} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

// ============================================================================
// PREFERENCES VIEW
// ============================================================================

const PreferencesView: React.FC = () => {
  const { data: preferences, isLoading } = usePreferences();
  const updatePreferences = useUpdatePreferences();

  const handleToggle = useCallback((key: keyof Preferences) => {
    if (preferences) {
      updatePreferences.mutate({ [key]: !preferences[key] });
    }
  }, [preferences, updatePreferences]);

  if (isLoading || !preferences) {
    return <Card><div className="p-8 text-center">Chargement...</div></Card>;
  }

  return (
    <Card>
      <h3 className="text-lg font-semibold flex items-center gap-2 mb-4"><Settings size={20} /> Préférences</h3>
      <div className="space-y-4">
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div>
            <div className="font-medium">Notifications push</div>
            <div className="text-sm text-gray-500">Recevoir des notifications sur cet appareil</div>
          </div>
          <button
            onClick={() => handleToggle('notifications_enabled')}
            className={`w-12 h-6 rounded-full transition-colors ${preferences.notifications_enabled ? 'bg-blue-500' : 'bg-gray-300'}`}
          >
            <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${preferences.notifications_enabled ? 'translate-x-6' : 'translate-x-0.5'}`} />
          </button>
        </div>
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div>
            <div className="font-medium">Mode hors-ligne</div>
            <div className="text-sm text-gray-500">Accéder aux données récentes sans connexion</div>
          </div>
          <button
            onClick={() => handleToggle('offline_mode')}
            className={`w-12 h-6 rounded-full transition-colors ${preferences.offline_mode ? 'bg-blue-500' : 'bg-gray-300'}`}
          >
            <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${preferences.offline_mode ? 'translate-x-6' : 'translate-x-0.5'}`} />
          </button>
        </div>
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div>
            <div className="font-medium">Synchronisation automatique</div>
            <div className="text-sm text-gray-500">Synchroniser les données en arrière-plan</div>
          </div>
          <button
            onClick={() => handleToggle('auto_sync')}
            className={`w-12 h-6 rounded-full transition-colors ${preferences.auto_sync ? 'bg-blue-500' : 'bg-gray-300'}`}
          >
            <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${preferences.auto_sync ? 'translate-x-6' : 'translate-x-0.5'}`} />
          </button>
        </div>
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div>
            <div className="font-medium">Mode sombre</div>
            <div className="text-sm text-gray-500">Utiliser le thème sombre sur mobile</div>
          </div>
          <button
            onClick={() => handleToggle('dark_mode')}
            className={`w-12 h-6 rounded-full transition-colors ${preferences.dark_mode ? 'bg-blue-500' : 'bg-gray-300'}`}
          >
            <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${preferences.dark_mode ? 'translate-x-6' : 'translate-x-0.5'}`} />
          </button>
        </div>
      </div>
    </Card>
  );
};

// ============================================================================
// MAIN DASHBOARD
// ============================================================================

const MobileDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('devices');
  const isMobile = useUIStore((state) => state.isMobile);
  const { data: stats } = useMobileStats();

  const tabs = [
    { id: 'devices', label: 'Appareils', icon: <Smartphone size={16} /> },
    { id: 'sessions', label: 'Sessions', icon: <Activity size={16} /> },
    { id: 'notifications', label: 'Notifications', icon: <Bell size={16} /> },
    { id: 'preferences', label: 'Préférences', icon: <Settings size={16} /> }
  ];

  return (
    <PageWrapper title="Application Mobile" subtitle="Configuration PWA et fonctionnalités mobiles">
      {/* Status Banner */}
      <section className="azals-section">
        <Card>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Smartphone size={24} className="text-blue-600" />
              </div>
              <div>
                <div className="font-medium">Mode d'affichage: {isMobile ? 'Mobile' : 'Desktop'}</div>
                <div className="text-sm text-gray-500">Service Worker actif - Mode PWA disponible</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge color="green">PWA Ready</Badge>
              <Badge color="blue">Hors-ligne actif</Badge>
            </div>
          </div>
        </Card>
      </section>

      {/* Stats */}
      <section className="azals-section">
        <Grid cols={4} gap="md">
          <StatCard title="Appareils" value={stats?.total_devices || 0} subtitle={`${stats?.active_devices || 0} actifs`} icon={<Smartphone />} />
          <StatCard title="Sessions" value={stats?.total_sessions || 0} subtitle={`${stats?.active_sessions || 0} actives`} icon={<Activity />} />
          <StatCard title="Notifications" value={stats?.unread_notifications || 0} subtitle="non lues" icon={<Bell />} />
          <StatCard title="Dernière sync" value={stats?.last_sync_at ? new Date(stats.last_sync_at).toLocaleTimeString('fr-FR') : '-'} icon={<RefreshCw />} />
        </Grid>
      </section>

      {/* Tabs */}
      <section className="azals-section">
        <TabNav tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        <div className="mt-4">
          {activeTab === 'devices' && <DevicesView />}
          {activeTab === 'sessions' && <SessionsView />}
          {activeTab === 'notifications' && <NotificationsView />}
          {activeTab === 'preferences' && <PreferencesView />}
        </div>
      </section>
    </PageWrapper>
  );
};

// ============================================================================
// ROUTES
// ============================================================================

export const MobileRoutes: React.FC = () => (
  <Routes>
    <Route index element={<MobileDashboard />} />
    <Route path="devices" element={<MobileDashboard />} />
    <Route path="notifications" element={<MobileDashboard />} />
    <Route path="qr" element={<MobileDashboard />} />
  </Routes>
);

export default MobileRoutes;
