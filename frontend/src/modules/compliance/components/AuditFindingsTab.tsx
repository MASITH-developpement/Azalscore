/**
 * AZALSCORE Module - Compliance - Audit Findings Tab
 * Onglet constats de l'audit
 */

import React from 'react';
import { AlertTriangle, CheckCircle2, XCircle, Clock, AlertCircle } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Audit, AuditFinding } from '../types';
import {
  formatDate,
  FINDING_SEVERITY_CONFIG, FINDING_STATUS_CONFIG,
  isFindingOpen, isFindingCritical
} from '../types';

/**
 * AuditFindingsTab - Constats de l'audit
 */
export const AuditFindingsTab: React.FC<TabContentProps<Audit>> = ({ data: audit }) => {
  const findings = audit.findings || [];

  const criticalCount = findings.filter(f => f.severity === 'CRITICAL').length;
  const majorCount = findings.filter(f => f.severity === 'MAJOR').length;
  const minorCount = findings.filter(f => f.severity === 'MINOR').length;
  const observationCount = findings.filter(f => f.severity === 'OBSERVATION').length;
  const openCount = findings.filter(isFindingOpen).length;
  const closedCount = findings.length - openCount;

  return (
    <div className="azals-std-tab-content">
      {/* Resume */}
      <Card title="Resume des constats" icon={<AlertTriangle size={18} />}>
        <Grid cols={3} gap="md">
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-2xl font-bold text-primary">{findings.length}</div>
            <div className="text-sm text-muted">Total</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded">
            <div className="text-2xl font-bold text-red-600">{criticalCount}</div>
            <div className="text-sm text-muted">Critiques</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded">
            <div className="text-2xl font-bold text-orange-600">{majorCount}</div>
            <div className="text-sm text-muted">Majeurs</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded">
            <div className="text-2xl font-bold text-yellow-600">{minorCount}</div>
            <div className="text-sm text-muted">Mineurs</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">{observationCount}</div>
            <div className="text-sm text-muted">Observations</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">{closedCount}</div>
            <div className="text-sm text-muted">Clotures</div>
          </div>
        </Grid>
      </Card>

      {/* Alertes */}
      {criticalCount > 0 && (
        <Card className="mt-4 border-red-200 bg-red-50">
          <div className="flex items-center gap-2 text-red-700">
            <AlertTriangle size={18} />
            <span className="font-medium">
              {criticalCount} constat(s) critique(s) identifie(s)
            </span>
          </div>
        </Card>
      )}

      {openCount > 0 && (
        <Card className="mt-4 border-orange-200 bg-orange-50">
          <div className="flex items-center gap-2 text-orange-700">
            <Clock size={18} />
            <span className="font-medium">
              {openCount} constat(s) en attente de traitement
            </span>
          </div>
        </Card>
      )}

      {/* Liste des constats */}
      <Card title={`Constats (${findings.length})`} icon={<AlertTriangle size={18} />} className="mt-4">
        {findings.length > 0 ? (
          <div className="space-y-3">
            {findings.map((finding) => (
              <FindingCard key={finding.id} finding={finding} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <CheckCircle2 size={32} className="text-green-500" />
            <p className="text-green-600 font-medium">Aucun constat enregistre</p>
          </div>
        )}
      </Card>

      {/* Stats detaillees (ERP only) */}
      <Card title="Repartition par statut" icon={<AlertTriangle size={18} />} className="mt-4 azals-std-field--secondary">
        <div className="grid grid-cols-5 gap-2">
          {Object.entries(FINDING_STATUS_CONFIG).map(([status, config]) => {
            const count = findings.filter(f => f.status === status).length;
            return (
              <div key={status} className="text-center p-2 bg-gray-50 rounded">
                <span className={`azals-badge azals-badge--${config.color} mb-1`}>
                  {config.label}
                </span>
                <div className="text-lg font-bold">{count}</div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant carte de constat
 */
const FindingCard: React.FC<{ finding: AuditFinding }> = ({ finding }) => {
  const severityConfig = FINDING_SEVERITY_CONFIG[finding.severity];
  const statusConfig = FINDING_STATUS_CONFIG[finding.status];
  const isOpen = isFindingOpen(finding);
  const isCritical = isFindingCritical(finding);

  const getSeverityIcon = () => {
    switch (finding.severity) {
      case 'CRITICAL':
        return <XCircle size={18} className="text-red-600" />;
      case 'MAJOR':
        return <AlertTriangle size={18} className="text-orange-600" />;
      case 'MINOR':
        return <AlertCircle size={18} className="text-yellow-600" />;
      default:
        return <AlertCircle size={18} className="text-blue-600" />;
    }
  };

  return (
    <div className={`p-4 rounded border ${isCritical ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-gray-50'}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          {getSeverityIcon()}
          <div>
            <div className="flex items-center gap-2 mb-1">
              <code className="font-mono text-sm text-muted">{finding.code}</code>
              <span className={`azals-badge azals-badge--${severityConfig.color}`}>
                {severityConfig.label}
              </span>
              <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
            <h4 className="font-medium">{finding.title}</h4>
            {finding.description && (
              <p className="text-muted text-sm mt-1">{finding.description}</p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-4 gap-4 text-sm">
        {finding.category && (
          <div>
            <span className="text-muted">Categorie:</span>
            <span className="ml-1">{finding.category}</span>
          </div>
        )}
        {finding.affected_area && (
          <div>
            <span className="text-muted">Zone:</span>
            <span className="ml-1">{finding.affected_area}</span>
          </div>
        )}
        {finding.assigned_to && (
          <div>
            <span className="text-muted">Assigne a:</span>
            <span className="ml-1">{finding.assigned_to}</span>
          </div>
        )}
        {finding.due_date && (
          <div>
            <span className="text-muted">Echeance:</span>
            <span className={`ml-1 ${isOpen && new Date(finding.due_date) < new Date() ? 'text-red-600 font-bold' : ''}`}>
              {formatDate(finding.due_date)}
            </span>
          </div>
        )}
      </div>

      {finding.recommendation && (
        <div className="mt-3 p-2 bg-blue-50 rounded text-sm azals-std-field--secondary">
          <span className="text-muted">Recommandation:</span>
          <p className="mt-1">{finding.recommendation}</p>
        </div>
      )}
    </div>
  );
};

export default AuditFindingsTab;
