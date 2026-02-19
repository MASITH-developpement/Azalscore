/**
 * AZALSCORE Module - Compliance - Audit Info Tab
 * Onglet informations generales de l'audit
 */

import React from 'react';
import {
  ClipboardCheck, User, Calendar, Target, Building2,
  CheckCircle2, AlertTriangle, Users
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatPercent } from '@/utils/formatters';
import {
  AUDIT_TYPE_CONFIG, AUDIT_STATUS_CONFIG, getAuditScoreColor
} from '../types';
import type { Audit } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * AuditInfoTab - Informations generales
 */
export const AuditInfoTab: React.FC<TabContentProps<Audit>> = ({ data: audit }) => {
  return (
    <div className="azals-std-tab-content">
      {/* Identification */}
      <Card title="Identification" icon={<ClipboardCheck size={18} />}>
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Code audit</span>
            <div className="azals-field__value font-mono">{audit.code}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Nom</span>
            <div className="azals-field__value">{audit.name}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Statut</span>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${AUDIT_STATUS_CONFIG[audit.status].color}`}>
                {AUDIT_STATUS_CONFIG[audit.status].label}
              </span>
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Type d'audit</span>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${AUDIT_TYPE_CONFIG[audit.type].color}`}>
                {AUDIT_TYPE_CONFIG[audit.type].label}
              </span>
            </div>
          </div>
          {audit.description && (
            <div className="azals-field col-span-2">
              <span className="azals-field__label">Description</span>
              <div className="azals-field__value">{audit.description}</div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Perimetre et objectifs */}
      <Card title="Perimetre et objectifs" icon={<Target size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          {audit.scope && (
            <div className="azals-field">
              <span className="azals-field__label">Perimetre</span>
              <div className="azals-field__value">{audit.scope}</div>
            </div>
          )}
          {audit.objectives && (
            <div className="azals-field">
              <span className="azals-field__label">Objectifs</span>
              <div className="azals-field__value">{audit.objectives}</div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Equipe d'audit */}
      <Card title="Equipe d'audit" icon={<Users size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Auditeur principal</span>
            <div className="azals-field__value flex items-center gap-1">
              <User size={14} className="text-muted" />
              {audit.auditor || audit.lead_auditor || '-'}
            </div>
          </div>
          {audit.auditor_company && (
            <div className="azals-field">
              <span className="azals-field__label">Cabinet / Societe</span>
              <div className="azals-field__value flex items-center gap-1">
                <Building2 size={14} className="text-muted" />
                {audit.auditor_company}
              </div>
            </div>
          )}
          {audit.audit_team && audit.audit_team.length > 0 && (
            <div className="azals-field azals-std-field--secondary">
              <span className="azals-field__label">Equipe</span>
              <div className="azals-field__value">
                {audit.audit_team.join(', ')}
              </div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Calendrier */}
      <Card title="Calendrier" icon={<Calendar size={18} />} className="mt-4">
        <Grid cols={4} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Date prevue</span>
            <div className="azals-field__value">
              {audit.planned_date ? formatDate(audit.planned_date) : '-'}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Date de debut</span>
            <div className="azals-field__value">
              {audit.start_date ? formatDate(audit.start_date) : '-'}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Date de fin</span>
            <div className="azals-field__value">
              {audit.end_date ? formatDate(audit.end_date) : '-'}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Date cloture</span>
            <div className="azals-field__value">
              {audit.completed_date ? (
                <span className="text-green-600 flex items-center gap-1">
                  <CheckCircle2 size={14} />
                  {formatDate(audit.completed_date)}
                </span>
              ) : '-'}
            </div>
          </div>
          {audit.next_audit_date && (
            <div className="azals-field azals-std-field--secondary">
              <span className="azals-field__label">Prochain audit</span>
              <div className="azals-field__value">
                {formatDate(audit.next_audit_date)}
              </div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Resultats */}
      {audit.status === 'COMPLETED' && (
        <Card title="Resultats" icon={<ClipboardCheck size={18} />} className="mt-4">
          <Grid cols={4} gap="md">
            <div className="azals-field">
              <span className="azals-field__label">Score global</span>
              <div className="azals-field__value">
                {audit.score !== undefined ? (
                  <span className={`text-2xl font-bold text-${getAuditScoreColor(audit.score)}-600`}>
                    {formatPercent(audit.score)}
                  </span>
                ) : '-'}
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Total constats</span>
              <div className="azals-field__value text-xl font-medium">
                {audit.findings_count}
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Critiques</span>
              <div className="azals-field__value">
                {audit.critical_findings > 0 ? (
                  <span className="text-red-600 font-bold flex items-center gap-1">
                    <AlertTriangle size={16} />
                    {audit.critical_findings}
                  </span>
                ) : (
                  <span className="text-green-600">0</span>
                )}
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Majeurs</span>
              <div className="azals-field__value">
                {(audit.major_findings || 0) > 0 ? (
                  <span className="text-orange-600 font-medium">{audit.major_findings}</span>
                ) : (
                  <span className="text-green-600">0</span>
                )}
              </div>
            </div>
          </Grid>

          {/* Plan d'action */}
          {audit.action_plan_status && (
            <div className="mt-4 pt-4 border-t">
              <Grid cols={2} gap="md">
                <div className="azals-field">
                  <span className="azals-field__label">Plan d'action</span>
                  <div className="azals-field__value">
                    <span className={`azals-badge azals-badge--${
                      audit.action_plan_status === 'COMPLETED' ? 'green' :
                      audit.action_plan_status === 'IN_PROGRESS' ? 'orange' : 'gray'
                    }`}>
                      {audit.action_plan_status === 'COMPLETED' ? 'Termine' :
                       audit.action_plan_status === 'IN_PROGRESS' ? 'En cours' : 'En attente'}
                    </span>
                  </div>
                </div>
                {audit.action_plan_progress !== undefined && (
                  <div className="azals-field">
                    <span className="azals-field__label">Progression</span>
                    <div className="azals-field__value">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-primary-500 h-2 rounded-full"
                            style={{ width: `${audit.action_plan_progress}%` }}
                          />
                        </div>
                        <span className="font-medium">{formatPercent(audit.action_plan_progress)}</span>
                      </div>
                    </div>
                  </div>
                )}
              </Grid>
            </div>
          )}
        </Card>
      )}

      {/* Notes (ERP only) */}
      {audit.notes && (
        <Card title="Notes internes" className="mt-4 azals-std-field--secondary">
          <p className="text-muted whitespace-pre-wrap">{audit.notes}</p>
        </Card>
      )}
    </div>
  );
};

export default AuditInfoTab;
