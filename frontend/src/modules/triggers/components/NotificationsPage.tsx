/**
 * AZALSCORE Module - Triggers - Notifications Page
 * Mes notifications
 */

import React, { useState } from 'react';
import { CheckCircle } from 'lucide-react';
import { Button, ButtonGroup } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import { NOTIFICATION_STATUS_CONFIG } from '../types';
import type { Notification } from '../types';
import { useMyNotifications, useMarkNotificationRead, useMarkAllNotificationsRead } from '../hooks';

export const NotificationsPage: React.FC = () => {
  const [unreadOnly, setUnreadOnly] = useState(false);
  const { data, isLoading, error, refetch } = useMyNotifications(unreadOnly);
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  const columns: TableColumn<Notification>[] = [
    {
      id: 'sent_at',
      header: 'Date',
      accessor: 'sent_at',
      sortable: true,
      render: (value) => (value ? formatDate(value as string) : '-'),
    },
    {
      id: 'channel',
      header: 'Canal',
      accessor: 'channel',
    },
    {
      id: 'subject',
      header: 'Sujet',
      accessor: 'subject',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => {
        const config = NOTIFICATION_STATUS_CONFIG[value as keyof typeof NOTIFICATION_STATUS_CONFIG];
        return <span className={`azals-badge azals-badge--${config.color}`}>{config.label}</span>;
      },
    },
    {
      id: 'read_at',
      header: 'Lu',
      accessor: 'read_at',
      render: (value) =>
        value ? (
          <CheckCircle size={16} className="azals-text--success" />
        ) : (
          <span className="azals-badge azals-badge--blue">Non lu</span>
        ),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <ButtonGroup>
          {!row.read_at && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => markRead.mutate(row.id)}
              disabled={markRead.isPending}
            >
              Marquer lu
            </Button>
          )}
        </ButtonGroup>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Mes notifications"
      subtitle={data ? `${data.unread_count} non lues` : ''}
      actions={
        <ButtonGroup>
          <Button
            variant={unreadOnly ? 'secondary' : 'ghost'}
            onClick={() => setUnreadOnly(!unreadOnly)}
          >
            {unreadOnly ? 'Toutes' : 'Non lues'}
          </Button>
          {data && data.unread_count > 0 && (
            <Button
              variant="secondary"
              onClick={() => markAllRead.mutate()}
              disabled={markAllRead.isPending}
            >
              Tout marquer lu
            </Button>
          )}
        </ButtonGroup>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.notifications || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucune notification"
        />
      </Card>
    </PageWrapper>
  );
};

export default NotificationsPage;
