/**
 * AZALSCORE Module - HR Vault - Dashboard View
 * Vue d'ensemble avec statistiques
 */

import React from 'react';
import {
  FileText, AlertTriangle, PenTool, Shield, Clock,
  HardDrive, Bell, FileCheck, FolderOpen
} from 'lucide-react';
import { StatCard } from '@ui/dashboards';
import { Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import {
  useDashboardStats,
  useExpiringDocuments,
  usePendingSignatures,
  useAlerts,
} from '../hooks';
import {
  SIGNATURE_STATUS_CONFIG,
  formatFileSize,
  getDocumentTypeLabel,
} from '../types';
import type { VaultDocumentType } from '../types';
import { Badge } from './LocalComponents';

export const DashboardView: React.FC = () => {
  const { data: stats, isLoading } = useDashboardStats();
  const { data: expiringDocs = [] } = useExpiringDocuments();
  const { data: pendingSignatures = [] } = usePendingSignatures();
  const { data: alerts = [] } = useAlerts(true);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="azals-spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <Grid cols={4}>
        <StatCard
          title="Documents totaux"
          value={String(stats?.total_documents || 0)}
          icon={<FileText size={24} />}
          variant="default"
        />
        <StatCard
          title="Stockage utilise"
          value={formatFileSize(stats?.total_storage_bytes || 0)}
          icon={<HardDrive size={24} />}
          variant="default"
        />
        <StatCard
          title="Signatures en attente"
          value={String(stats?.pending_signatures || 0)}
          icon={<PenTool size={24} />}
          variant={stats?.pending_signatures ? 'warning' : 'success'}
        />
        <StatCard
          title="Demandes RGPD"
          value={String(stats?.gdpr_requests_pending || 0)}
          icon={<Shield size={24} />}
          variant={stats?.gdpr_requests_pending ? 'warning' : 'success'}
        />
      </Grid>

      <Grid cols={2}>
        {/* Documents expirant */}
        <Card title="Documents expirant prochainement" icon={<Clock size={18} />}>
          {expiringDocs.length === 0 ? (
            <p className="text-gray-500 text-center py-4">Aucun document expirant dans les 30 jours</p>
          ) : (
            <div className="space-y-2">
              {expiringDocs.slice(0, 5).map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-2 bg-orange-50 rounded">
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={16} className="text-orange-500" />
                    <span className="font-medium">{doc.title}</span>
                  </div>
                  <span className="text-sm text-gray-500">
                    Expire le {formatDate(doc.expiry_date || '')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Signatures en attente */}
        <Card title="Signatures en attente" icon={<PenTool size={18} />}>
          {pendingSignatures.length === 0 ? (
            <p className="text-gray-500 text-center py-4">Aucune signature en attente</p>
          ) : (
            <div className="space-y-2">
              {pendingSignatures.slice(0, 5).map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-2 bg-blue-50 rounded">
                  <div className="flex items-center gap-2">
                    <FileCheck size={16} className="text-blue-500" />
                    <span className="font-medium">{doc.title}</span>
                  </div>
                  <Badge color={SIGNATURE_STATUS_CONFIG[doc.signature_status].color}>
                    {SIGNATURE_STATUS_CONFIG[doc.signature_status].label}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </Grid>

      {/* Alertes */}
      {alerts.length > 0 && (
        <Card title="Alertes non lues" icon={<Bell size={18} />}>
          <div className="space-y-2">
            {alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className={`flex items-center justify-between p-3 rounded ${
                  alert.severity === 'CRITICAL' ? 'bg-red-50' :
                  alert.severity === 'WARNING' ? 'bg-orange-50' : 'bg-blue-50'
                }`}
              >
                <div className="flex items-center gap-2">
                  <AlertTriangle
                    size={16}
                    className={
                      alert.severity === 'CRITICAL' ? 'text-red-500' :
                      alert.severity === 'WARNING' ? 'text-orange-500' : 'text-blue-500'
                    }
                  />
                  <div>
                    <div className="font-medium">{alert.title}</div>
                    {alert.description && (
                      <div className="text-sm text-gray-500">{alert.description}</div>
                    )}
                  </div>
                </div>
                <span className="text-sm text-gray-500">{formatDate(alert.created_at)}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Repartition par type */}
      {stats?.documents_by_type && Object.keys(stats.documents_by_type).length > 0 && (
        <Card title="Repartition par type de document" icon={<FolderOpen size={18} />}>
          <div className="grid grid-cols-4 gap-4">
            {Object.entries(stats.documents_by_type).map(([type, count]) => (
              <div key={type} className="p-3 bg-gray-50 rounded">
                <div className="text-sm text-gray-500">
                  {getDocumentTypeLabel(type as VaultDocumentType)}
                </div>
                <div className="text-2xl font-bold">{count}</div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default DashboardView;
