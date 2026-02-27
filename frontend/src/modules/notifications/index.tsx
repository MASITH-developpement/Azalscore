/**
 * AZALSCORE Module - NOTIFICATIONS
 * =================================
 * Interface de gestion des notifications
 */

import React, { useState } from 'react';
import {
  Bell, Mail, Smartphone, Layout, Settings,
  Check, CheckCheck, Trash2, Filter, RefreshCw,
  FileText, Eye, Clock, AlertTriangle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { KPICard } from '@ui/dashboards';
import { DataTable } from '@ui/tables';
import { Badge } from '@ui/simple';
import { Input, Modal } from '@ui/forms';
import { formatDate } from '@/utils/formatters';
import type { TableColumn, DashboardKPI } from '@/types';

import {
  useNotifications,
  useUnreadCount,
  useNotificationStats,
  useMarkAsRead,
  useMarkAllAsRead,
  useDeleteNotification,
  useNotificationPreferences,
  useUpdateNotificationPreferences,
  useNotificationTemplates,
} from './hooks';
import type {
  Notification,
  NotificationPreferences,
  NotificationTemplate,
  NotificationType,
  NotificationStatus,
} from './types';
import {
  NOTIFICATION_TYPE_CONFIG,
  NOTIFICATION_STATUS_CONFIG,
  NOTIFICATION_PRIORITY_CONFIG,
  NOTIFICATION_CHANNEL_CONFIG,
} from './types';

// ============================================================================
// BADGES
// ============================================================================

const TypeBadge: React.FC<{ type: NotificationType }> = ({ type }) => {
  const config = NOTIFICATION_TYPE_CONFIG[type];
  return <Badge variant={config?.color === 'blue' ? 'default' : 'default'}>{config?.label || type}</Badge>;
};

const StatusBadge: React.FC<{ status: NotificationStatus }> = ({ status }) => {
  const config = NOTIFICATION_STATUS_CONFIG[status];
  const variant = config?.color === 'green' ? 'success' : config?.color === 'red' ? 'destructive' : 'default';
  return <Badge variant={variant}>{config?.label || status}</Badge>;
};

// ============================================================================
// NOTIFICATIONS LIST
// ============================================================================

type View = 'list' | 'preferences' | 'templates';

const NotificationsList: React.FC<{
  onViewChange: (view: View) => void;
}> = ({ onViewChange }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [typeFilter, setTypeFilter] = useState<NotificationType | undefined>(undefined);
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  const { data, isLoading, refetch } = useNotifications({
    page,
    page_size: pageSize,
    type: typeFilter,
    is_read: showUnreadOnly ? false : undefined,
  });
  const { data: unreadCount } = useUnreadCount();
  const { data: stats } = useNotificationStats();
  const markAsRead = useMarkAsRead();
  const markAllAsRead = useMarkAllAsRead();
  const deleteNotification = useDeleteNotification();

  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);

  const kpis: DashboardKPI[] = [
    {
      id: 'unread',
      label: 'Non lues',
      value: unreadCount?.count || 0,
      icon: <Bell size={20} />,
      variant: 'warning',
    },
    {
      id: 'sent',
      label: 'Envoyees (30j)',
      value: stats?.total_sent || 0,
      icon: <Mail size={20} />,
      variant: 'info',
    },
    {
      id: 'delivered',
      label: 'Delivrees',
      value: stats?.total_delivered || 0,
      trend: stats?.delivery_rate && stats.delivery_rate > 90 ? 'up' : 'neutral',
      icon: <CheckCheck size={20} />,
      variant: 'success',
    },
    {
      id: 'failed',
      label: 'Echecs',
      value: stats?.total_failed || 0,
      icon: <AlertTriangle size={20} />,
      variant: 'danger',
    },
  ];

  const columns: TableColumn<Notification>[] = [
    {
      id: 'status_icon',
      header: '',
      accessor: 'status',
      width: 40,
      render: (_, row): React.ReactNode => (
        <div className={`w-2 h-2 rounded-full ${row.read_at ? 'bg-gray-300' : 'bg-primary'}`} />
      ),
    },
    {
      id: 'title',
      header: 'Notification',
      accessor: 'title',
      render: (_, row): React.ReactNode => (
        <div>
          <div className={`font-medium ${row.read_at ? 'text-gray-600' : 'text-gray-900'}`}>
            {row.title || row.subject || 'Sans titre'}
          </div>
          <div className="text-sm text-gray-500 truncate max-w-md">{row.body}</div>
        </div>
      ),
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'notification_type',
      render: (v): React.ReactNode => <TypeBadge type={v as NotificationType} />,
    },
    {
      id: 'channel',
      header: 'Canal',
      accessor: 'channel',
      render: (v): React.ReactNode => {
        const config = NOTIFICATION_CHANNEL_CONFIG[v as keyof typeof NOTIFICATION_CHANNEL_CONFIG];
        return <span className="text-sm">{config?.label || String(v)}</span>;
      },
    },
    {
      id: 'created_at',
      header: 'Date',
      accessor: 'created_at',
      render: (v): React.ReactNode => (
        <span className="text-sm text-gray-500">
          {formatDate(v as string)}
        </span>
      ),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v): React.ReactNode => <StatusBadge status={v as NotificationStatus} />,
    },
    {
      id: 'actions',
      header: '',
      accessor: 'id',
      width: 100,
      render: (_, row): React.ReactNode => (
        <div className="flex gap-1">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setSelectedNotification(row)}
          >
            <Eye size={14} />
          </Button>
          {!row.read_at && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => markAsRead.mutate(row.id)}
            >
              <Check size={14} />
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => deleteNotification.mutate(row.id)}
          >
            <Trash2 size={14} />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Notifications"
      subtitle={`${unreadCount?.count || 0} non lue(s)`}
      actions={
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => onViewChange('preferences')}>
            <Settings size={16} className="mr-2" />
            Preferences
          </Button>
          <Button variant="secondary" onClick={() => onViewChange('templates')}>
            <FileText size={16} className="mr-2" />
            Templates
          </Button>
          <Button onClick={() => markAllAsRead.mutate()} disabled={!unreadCount?.count}>
            <CheckCheck size={16} className="mr-2" />
            Tout marquer lu
          </Button>
        </div>
      }
    >
      <Grid cols={4} gap="md" className="mb-6">
        {kpis.map((kpi) => (
          <KPICard key={kpi.id} kpi={kpi} />
        ))}
      </Grid>

      <Card noPadding>
        <div className="p-4 border-b flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400" />
            <select
              className="azals-select text-sm"
              value={typeFilter || ''}
              onChange={(e) => setTypeFilter(e.target.value ? e.target.value as NotificationType : undefined)}
            >
              <option value="">Tous les types</option>
              {Object.entries(NOTIFICATION_TYPE_CONFIG).map(([key, config]) => (
                <option key={key} value={key}>{config.label}</option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showUnreadOnly}
              onChange={(e) => setShowUnreadOnly(e.target.checked)}
              className="rounded"
            />
            Non lues uniquement
          </label>
          <div className="flex-1" />
          <Button variant="ghost" size="sm" onClick={() => { refetch(); }}>
            <RefreshCw size={14} />
          </Button>
        </div>

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRowClick={(row) => setSelectedNotification(row)}
          emptyMessage="Aucune notification"
        />
      </Card>

      {/* Detail Modal */}
      <Modal
        isOpen={!!selectedNotification}
        onClose={() => setSelectedNotification(null)}
        title={selectedNotification?.title || selectedNotification?.subject || 'Notification'}
      >
        {selectedNotification && (
          <div className="space-y-4">
            <div className="flex gap-2">
              <TypeBadge type={selectedNotification.notification_type} />
              <StatusBadge status={selectedNotification.status} />
              <Badge variant={selectedNotification.priority === 'URGENT' ? 'destructive' : 'default'}>
                {NOTIFICATION_PRIORITY_CONFIG[selectedNotification.priority]?.label || selectedNotification.priority}
              </Badge>
            </div>

            <div className="prose prose-sm max-w-none">
              {selectedNotification.html_body ? (
                <div dangerouslySetInnerHTML={{ __html: selectedNotification.html_body }} />
              ) : (
                <p>{selectedNotification.body}</p>
              )}
            </div>

            <div className="text-sm text-gray-500 space-y-1">
              <div className="flex items-center gap-2">
                <Clock size={14} />
                Cree le {formatDate(selectedNotification.created_at)}
              </div>
              {selectedNotification.sent_at && (
                <div>Envoye le {formatDate(selectedNotification.sent_at)}</div>
              )}
              {selectedNotification.read_at && (
                <div>Lu le {formatDate(selectedNotification.read_at)}</div>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              {!selectedNotification.read_at && (
                <Button
                  onClick={() => {
                    markAsRead.mutate(selectedNotification.id);
                    setSelectedNotification(null);
                  }}
                >
                  <Check size={16} className="mr-2" />
                  Marquer comme lu
                </Button>
              )}
              <Button variant="secondary" onClick={() => setSelectedNotification(null)}>
                Fermer
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </PageWrapper>
  );
};

// ============================================================================
// PREFERENCES VIEW
// ============================================================================

const PreferencesView: React.FC<{ onBack: () => void }> = ({ onBack }) => {
  const { data: preferences, isLoading } = useNotificationPreferences();
  const updatePreferences = useUpdateNotificationPreferences();

  const handleToggle = (key: keyof NotificationPreferences, value: boolean) => {
    updatePreferences.mutate({ [key]: value });
  };

  if (isLoading) {
    return (
      <PageWrapper title="Preferences" backAction={{ label: 'Retour', onClick: onBack }}>
        <Card>Chargement...</Card>
      </PageWrapper>
    );
  }

  const ToggleRow: React.FC<{
    icon: React.ReactNode;
    title: string;
    description: string;
    checked: boolean;
    onChange: (v: boolean) => void;
  }> = ({ icon, title, description, checked, onChange }) => (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-3">
        {icon}
        <div>
          <div className="font-medium">{title}</div>
          <div className="text-sm text-gray-500">{description}</div>
        </div>
      </div>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="rounded h-5 w-5"
      />
    </div>
  );

  return (
    <PageWrapper
      title="Preferences de notification"
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <Grid cols={2} gap="lg">
        <Card title="Canaux de notification">
          <div className="space-y-2">
            <ToggleRow
              icon={<Mail size={20} className="text-gray-400" />}
              title="Email"
              description="Recevoir par email"
              checked={preferences?.email_enabled || false}
              onChange={(v) => handleToggle('email_enabled', v)}
            />
            <ToggleRow
              icon={<Smartphone size={20} className="text-gray-400" />}
              title="SMS"
              description="Recevoir par SMS"
              checked={preferences?.sms_enabled || false}
              onChange={(v) => handleToggle('sms_enabled', v)}
            />
            <ToggleRow
              icon={<Bell size={20} className="text-gray-400" />}
              title="Push"
              description="Notifications push mobile"
              checked={preferences?.push_enabled || false}
              onChange={(v) => handleToggle('push_enabled', v)}
            />
            <ToggleRow
              icon={<Layout size={20} className="text-gray-400" />}
              title="In-App"
              description="Notifications dans l application"
              checked={preferences?.in_app_enabled || false}
              onChange={(v) => handleToggle('in_app_enabled', v)}
            />
          </div>
        </Card>

        <Card title="Types de notifications">
          <div className="space-y-2">
            {Object.entries(NOTIFICATION_TYPE_CONFIG).map(([type, config]) => {
              const key = `${type.toLowerCase()}_enabled` as keyof NotificationPreferences;
              const isEnabled = preferences ? (preferences as unknown as Record<string, boolean>)[key] ?? true : true;
              return (
                <div key={type} className="flex items-center justify-between py-2">
                  <div className="font-medium">{config.label}</div>
                  <input
                    type="checkbox"
                    checked={isEnabled}
                    onChange={(e) => handleToggle(key, e.target.checked)}
                    className="rounded h-5 w-5"
                  />
                </div>
              );
            })}
          </div>
        </Card>

        <Card title="Heures silencieuses">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Activer les heures silencieuses</div>
                <div className="text-sm text-gray-500">Pas de notifications pendant ces heures</div>
              </div>
              <input
                type="checkbox"
                checked={preferences?.quiet_hours_enabled || false}
                onChange={(e) => handleToggle('quiet_hours_enabled', e.target.checked)}
                className="rounded h-5 w-5"
              />
            </div>

            {preferences?.quiet_hours_enabled && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-500">Debut</label>
                  <input
                    type="time"
                    className="azals-input w-full"
                    value={preferences.quiet_hours_start || '22:00'}
                    onChange={(e) => updatePreferences.mutate({ quiet_hours_start: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-500">Fin</label>
                  <input
                    type="time"
                    className="azals-input w-full"
                    value={preferences.quiet_hours_end || '08:00'}
                    onChange={(e) => updatePreferences.mutate({ quiet_hours_end: e.target.value })}
                  />
                </div>
              </div>
            )}
          </div>
        </Card>

        <Card title="Digest">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Recevoir un digest</div>
                <div className="text-sm text-gray-500">Resume periodique des notifications</div>
              </div>
              <input
                type="checkbox"
                checked={preferences?.digest_enabled || false}
                onChange={(e) => handleToggle('digest_enabled', e.target.checked)}
                className="rounded h-5 w-5"
              />
            </div>

            {preferences?.digest_enabled && (
              <div>
                <label className="text-sm text-gray-500">Frequence</label>
                <select
                  className="azals-select w-full"
                  value={preferences.digest_frequency || 'DAILY'}
                  onChange={(e) => updatePreferences.mutate({ digest_frequency: e.target.value as 'DAILY' | 'WEEKLY' })}
                >
                  <option value="DAILY">Quotidien</option>
                  <option value="WEEKLY">Hebdomadaire</option>
                </select>
              </div>
            )}
          </div>
        </Card>
      </Grid>
    </PageWrapper>
  );
};

// ============================================================================
// TEMPLATES VIEW
// ============================================================================

const TemplatesView: React.FC<{ onBack: () => void }> = ({ onBack }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const { data, isLoading, refetch } = useNotificationTemplates({ page, page_size: pageSize });

  const columns: TableColumn<NotificationTemplate>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v): React.ReactNode => <code className="text-sm">{String(v)}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'notification_type', render: (v): React.ReactNode => <TypeBadge type={v as NotificationType} /> },
    {
      id: 'channels',
      header: 'Canaux',
      accessor: 'channels',
      render: (v): React.ReactNode => (
        <div className="flex gap-1">
          {(v as string[])?.map((ch) => (
            <Badge key={ch} variant="secondary" size="sm">
              {NOTIFICATION_CHANNEL_CONFIG[ch as keyof typeof NOTIFICATION_CHANNEL_CONFIG]?.label || ch}
            </Badge>
          ))}
        </div>
      ),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v): React.ReactNode => (
        <Badge variant={v === 'ACTIVE' ? 'success' : v === 'DRAFT' ? 'secondary' : 'default'}>
          {v === 'ACTIVE' ? 'Actif' : v === 'DRAFT' ? 'Brouillon' : 'Archive'}
        </Badge>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Templates de notification"
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={<Button>Nouveau template</Button>}
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={() => { refetch(); }}
          emptyMessage="Aucun template"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const NotificationsModule: React.FC = () => {
  const [view, setView] = useState<View>('list');

  switch (view) {
    case 'preferences':
      return <PreferencesView onBack={() => setView('list')} />;
    case 'templates':
      return <TemplatesView onBack={() => setView('list')} />;
    default:
      return <NotificationsList onViewChange={setView} />;
  }
};

export default NotificationsModule;
