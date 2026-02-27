/**
 * AZALSCORE Module - Audit - Log Detail Page
 * Vue detaillee d'un log d'audit
 */

import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import { useAuditLog } from '../hooks';
import { AUDIT_ACTION_LABELS, AUDIT_CATEGORY_LABELS, AUDIT_LEVEL_CONFIG } from '../types';

export const LogDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: log, isLoading, error } = useAuditLog(id!);

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">Chargement du log...</div>
      </PageWrapper>
    );
  }

  if (error || !log) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <p className="text-danger">Impossible de charger le log.</p>
          <Button variant="secondary" onClick={() => navigate('/audit/logs')} className="mt-4">
            Retour
          </Button>
        </Card>
      </PageWrapper>
    );
  }

  const levelConfig = AUDIT_LEVEL_CONFIG[log.level];

  return (
    <PageWrapper
      title={`Log ${log.id.slice(0, 8)}`}
      subtitle={`${AUDIT_ACTION_LABELS[log.action]} - ${log.module}`}
      backAction={{
        label: 'Retour',
        onClick: () => navigate('/audit/logs'),
      }}
    >
      {/* Statut */}
      <section className="azals-section">
        <div className="azals-status-bar">
          <span className={`azals-badge azals-badge--${levelConfig.color} azals-badge--lg`}>
            {levelConfig.label}
          </span>
          <span className={`azals-badge azals-badge--${log.success ? 'green' : 'red'}`}>
            {log.success ? 'Succes' : 'Echec'}
          </span>
          <span className="azals-text--muted">{formatDate(log.created_at)}</span>
        </div>
      </section>

      {/* Informations */}
      <section className="azals-section">
        <Grid cols={2} gap="md">
          <Card title="Details">
            <div className="azals-info-list">
              <div className="azals-info-item">
                <span>Action</span>
                <strong>{AUDIT_ACTION_LABELS[log.action]}</strong>
              </div>
              <div className="azals-info-item">
                <span>Categorie</span>
                <strong>{AUDIT_CATEGORY_LABELS[log.category]}</strong>
              </div>
              <div className="azals-info-item">
                <span>Module</span>
                <strong>{log.module}</strong>
              </div>
              {log.entity_type && (
                <div className="azals-info-item">
                  <span>Entite</span>
                  <strong>
                    {log.entity_type} {log.entity_id && `#${log.entity_id}`}
                  </strong>
                </div>
              )}
              {log.duration_ms && (
                <div className="azals-info-item">
                  <span>Duree</span>
                  <strong>{log.duration_ms.toFixed(2)} ms</strong>
                </div>
              )}
            </div>
          </Card>

          <Card title="Contexte">
            <div className="azals-info-list">
              {log.user_email && (
                <div className="azals-info-item">
                  <span>Utilisateur</span>
                  <strong>{log.user_email}</strong>
                </div>
              )}
              {log.user_role && (
                <div className="azals-info-item">
                  <span>Role</span>
                  <strong>{log.user_role}</strong>
                </div>
              )}
              {log.ip_address && (
                <div className="azals-info-item">
                  <span>Adresse IP</span>
                  <strong>{log.ip_address}</strong>
                </div>
              )}
              {log.session_id && (
                <div className="azals-info-item">
                  <span>Session</span>
                  <code>{log.session_id.slice(0, 12)}...</code>
                </div>
              )}
              {log.request_id && (
                <div className="azals-info-item">
                  <span>Request ID</span>
                  <code>{log.request_id.slice(0, 12)}...</code>
                </div>
              )}
            </div>
          </Card>
        </Grid>
      </section>

      {/* Description et erreur */}
      {(log.description || log.error_message) && (
        <section className="azals-section">
          <Grid cols={2} gap="md">
            {log.description && (
              <Card title="Description">
                <p>{log.description}</p>
              </Card>
            )}
            {log.error_message && (
              <Card title="Erreur">
                <p className="azals-text--danger">{log.error_message}</p>
                {log.error_code && (
                  <code className="azals-code">{log.error_code}</code>
                )}
              </Card>
            )}
          </Grid>
        </section>
      )}

      {/* Valeurs */}
      {(log.old_value || log.new_value || log.diff) && (
        <section className="azals-section">
          <Grid cols={log.diff ? 3 : 2} gap="md">
            {log.old_value && (
              <Card title="Ancienne valeur">
                <pre className="azals-code-block">{JSON.stringify(log.old_value, null, 2)}</pre>
              </Card>
            )}
            {log.new_value && (
              <Card title="Nouvelle valeur">
                <pre className="azals-code-block">{JSON.stringify(log.new_value, null, 2)}</pre>
              </Card>
            )}
            {log.diff && (
              <Card title="Differences">
                <pre className="azals-code-block">{JSON.stringify(log.diff, null, 2)}</pre>
              </Card>
            )}
          </Grid>
        </section>
      )}
    </PageWrapper>
  );
};

export default LogDetailPage;
