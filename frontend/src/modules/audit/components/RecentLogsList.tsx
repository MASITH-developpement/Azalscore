/**
 * AZALSCORE Module - Audit - Recent Logs List
 * Liste des logs recents
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle } from 'lucide-react';
import { formatDate } from '@/utils/formatters';
import { AUDIT_ACTION_LABELS, AUDIT_LEVEL_CONFIG } from '../types';
import type { AuditLog } from '../types';

export interface RecentLogsListProps {
  logs: AuditLog[];
}

export const RecentLogsList: React.FC<RecentLogsListProps> = ({ logs }) => {
  const navigate = useNavigate();

  if (logs.length === 0) {
    return <p className="azals-text--muted">Aucun log recent</p>;
  }

  return (
    <div className="azals-list">
      {logs.map((log) => {
        const levelConfig = AUDIT_LEVEL_CONFIG[log.level];
        return (
          <div
            key={log.id}
            className="azals-list-item azals-list-item--clickable"
            onClick={() => navigate(`/audit/logs/${log.id}`)}
          >
            <div className="azals-list-item__icon">
              {log.success ? (
                <CheckCircle size={16} className="azals-text--success" />
              ) : (
                <XCircle size={16} className="azals-text--danger" />
              )}
            </div>
            <div className="azals-list-item__content">
              <div className="azals-list-item__header">
                <span className={`azals-badge azals-badge--${levelConfig.color}`}>
                  {AUDIT_ACTION_LABELS[log.action] || log.action}
                </span>
                <span className="azals-text--muted">{log.module}</span>
              </div>
              <p className="azals-list-item__description">
                {log.description || `${log.entity_type || ''} ${log.entity_id || ''}`}
              </p>
            </div>
            <div className="azals-list-item__meta">
              <span className="azals-text--muted">{formatDate(log.created_at)}</span>
              {log.user_email && <span className="azals-text--muted">{log.user_email}</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RecentLogsList;
