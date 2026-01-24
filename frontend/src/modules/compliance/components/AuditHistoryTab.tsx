/**
 * AZALSCORE Module - Compliance - Audit History Tab
 * Onglet historique de l'audit
 */

import React from 'react';
import {
  Clock, User, Play, CheckCircle2, XCircle,
  Calendar, FileText, ArrowRight
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Audit, AuditHistoryEntry } from '../types';
import { formatDateTime, AUDIT_STATUS_CONFIG } from '../types';

/**
 * AuditHistoryTab - Historique de l'audit
 */
export const AuditHistoryTab: React.FC<TabContentProps<Audit>> = ({ data: audit }) => {
  const history = generateHistoryFromAudit(audit);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique de l'audit" icon={<Clock size={18} />}>
        {history.length > 0 ? (
          <div className="azals-timeline">
            {history.map((item, index) => (
              <HistoryEntryComponent
                key={item.id}
                entry={item}
                isFirst={index === 0}
                isLast={index === history.length - 1}
              />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Clock size={32} className="text-muted" />
            <p className="text-muted">Aucun historique disponible</p>
          </div>
        )}
      </Card>

      {/* Journal d'audit (ERP only) */}
      <Card title="Journal d'audit" icon={<Clock size={18} />} className="mt-4 azals-std-field--secondary">
        <table className="azals-table azals-table--simple azals-table--compact">
          <thead>
            <tr>
              <th>Date/Heure</th>
              <th>Action</th>
              <th>Utilisateur</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item) => (
              <tr key={item.id}>
                <td className="text-muted text-sm">{formatDateTime(item.timestamp)}</td>
                <td>{item.action}</td>
                <td>{item.user_name || 'Systeme'}</td>
                <td className="text-muted text-sm">
                  {item.details || '-'}
                  {item.old_status && item.new_status && (
                    <span className="ml-2">
                      <span className={`azals-badge azals-badge--${AUDIT_STATUS_CONFIG[item.old_status as keyof typeof AUDIT_STATUS_CONFIG]?.color || 'gray'} text-xs`}>
                        {AUDIT_STATUS_CONFIG[item.old_status as keyof typeof AUDIT_STATUS_CONFIG]?.label || item.old_status}
                      </span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className={`azals-badge azals-badge--${AUDIT_STATUS_CONFIG[item.new_status as keyof typeof AUDIT_STATUS_CONFIG]?.color || 'gray'} text-xs`}>
                        {AUDIT_STATUS_CONFIG[item.new_status as keyof typeof AUDIT_STATUS_CONFIG]?.label || item.new_status}
                      </span>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

/**
 * Composant entree de timeline
 */
interface HistoryEntryComponentProps {
  entry: AuditHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntryComponent: React.FC<HistoryEntryComponentProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('planifi')) {
      return <Calendar size={16} className="text-blue-500" />;
    }
    if (action.includes('demarr') || action.includes('lance') || action.includes('debut')) {
      return <Play size={16} className="text-orange-500" />;
    }
    if (action.includes('termin') || action.includes('clotur') || action.includes('complet')) {
      return <CheckCircle2 size={16} className="text-green-500" />;
    }
    if (action.includes('annul')) {
      return <XCircle size={16} className="text-red-500" />;
    }
    if (action.includes('rapport')) {
      return <FileText size={16} className="text-purple-500" />;
    }
    return <Clock size={16} className="text-muted" />;
  };

  return (
    <div className={`azals-timeline__entry ${isFirst ? 'azals-timeline__entry--first' : ''} ${isLast ? 'azals-timeline__entry--last' : ''}`}>
      <div className="azals-timeline__icon">{getIcon()}</div>
      <div className="azals-timeline__content">
        <div className="azals-timeline__header">
          <span className="azals-timeline__action">{entry.action}</span>
          <span className="azals-timeline__time text-muted">{formatDateTime(entry.timestamp)}</span>
        </div>
        {entry.user_name && (
          <div className="azals-timeline__user text-sm">
            <User size={12} className="mr-1" />
            {entry.user_name}
          </div>
        )}
        {entry.details && (
          <p className="azals-timeline__details text-muted text-sm mt-1">{entry.details}</p>
        )}
        {entry.old_status && entry.new_status && (
          <div className="azals-timeline__change text-sm mt-1">
            <span className={`azals-badge azals-badge--${AUDIT_STATUS_CONFIG[entry.old_status as keyof typeof AUDIT_STATUS_CONFIG]?.color || 'gray'}`}>
              {AUDIT_STATUS_CONFIG[entry.old_status as keyof typeof AUDIT_STATUS_CONFIG]?.label || entry.old_status}
            </span>
            <ArrowRight size={12} className="mx-2" />
            <span className={`azals-badge azals-badge--${AUDIT_STATUS_CONFIG[entry.new_status as keyof typeof AUDIT_STATUS_CONFIG]?.color || 'gray'}`}>
              {AUDIT_STATUS_CONFIG[entry.new_status as keyof typeof AUDIT_STATUS_CONFIG]?.label || entry.new_status}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Generer l'historique a partir des donnees de l'audit
 */
function generateHistoryFromAudit(audit: Audit): AuditHistoryEntry[] {
  const history: AuditHistoryEntry[] = [];

  // Planification
  if (audit.planned_date) {
    history.push({
      id: 'planned',
      timestamp: audit.created_at,
      action: 'Audit planifie',
      user_name: audit.created_by_name,
      details: `Prevu pour le ${new Date(audit.planned_date).toLocaleDateString('fr-FR')}`,
    });
  } else {
    history.push({
      id: 'created',
      timestamp: audit.created_at,
      action: 'Audit cree',
      user_name: audit.created_by_name,
      details: `Code: ${audit.code}`,
    });
  }

  // Demarrage
  if (audit.start_date) {
    history.push({
      id: 'started',
      timestamp: audit.start_date,
      action: 'Audit demarre',
      old_status: 'PLANNED',
      new_status: 'IN_PROGRESS',
      details: audit.auditor ? `Par ${audit.auditor}` : undefined,
    });
  }

  // Fin sur site
  if (audit.end_date && audit.status !== 'PLANNED') {
    history.push({
      id: 'ended',
      timestamp: audit.end_date,
      action: 'Audit sur site termine',
      details: `${audit.findings_count} constat(s) identifie(s)`,
    });
  }

  // Rapport
  if (audit.report_date) {
    history.push({
      id: 'report',
      timestamp: audit.report_date,
      action: 'Rapport emis',
      details: audit.score !== undefined ? `Score: ${audit.score}%` : undefined,
    });
  }

  // Cloture
  if (audit.completed_date) {
    history.push({
      id: 'completed',
      timestamp: audit.completed_date,
      action: 'Audit cloture',
      old_status: 'IN_PROGRESS',
      new_status: 'COMPLETED',
    });
  }

  // Annulation
  if (audit.status === 'CANCELLED') {
    history.push({
      id: 'cancelled',
      timestamp: audit.updated_at,
      action: 'Audit annule',
      new_status: 'CANCELLED',
    });
  }

  // Historique fourni par l'API
  if (audit.history && audit.history.length > 0) {
    history.push(...audit.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

export default AuditHistoryTab;
