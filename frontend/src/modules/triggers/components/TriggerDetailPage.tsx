/**
 * AZALSCORE Module - Triggers - Detail Page
 * Vue detail d'un trigger
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Pause, Play, Zap, Edit } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button, ButtonGroup } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import {
  TRIGGER_TYPE_LABELS,
  TRIGGER_STATUS_CONFIG,
  ALERT_SEVERITY_CONFIG,
} from '../types';
import { useTrigger, usePauseTrigger, useResumeTrigger, useFireTrigger } from '../hooks';

export const TriggerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: trigger, isLoading, error } = useTrigger(id!);
  const pauseTrigger = usePauseTrigger();
  const resumeTrigger = useResumeTrigger();
  const fireTrigger = useFireTrigger();

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">Chargement du trigger...</div>
      </PageWrapper>
    );
  }

  if (error || !trigger) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <p className="text-danger">Impossible de charger le trigger.</p>
          <Button variant="secondary" onClick={() => navigate('/triggers/list')} className="mt-4">
            Retour
          </Button>
        </Card>
      </PageWrapper>
    );
  }

  const statusConfig = TRIGGER_STATUS_CONFIG[trigger.status];
  const severityConfig = ALERT_SEVERITY_CONFIG[trigger.severity];

  return (
    <PageWrapper
      title={trigger.name}
      subtitle={`Code: ${trigger.code}`}
      backAction={{
        label: 'Retour',
        onClick: () => navigate('/triggers/list'),
      }}
      actions={
        <ButtonGroup>
          {trigger.status === 'ACTIVE' ? (
            <Button
              variant="secondary"
              leftIcon={<Pause size={16} />}
              onClick={() => pauseTrigger.mutate(trigger.id)}
              disabled={pauseTrigger.isPending}
            >
              Pause
            </Button>
          ) : trigger.status === 'PAUSED' ? (
            <Button
              variant="secondary"
              leftIcon={<Play size={16} />}
              onClick={() => resumeTrigger.mutate(trigger.id)}
              disabled={resumeTrigger.isPending}
            >
              Reprendre
            </Button>
          ) : null}
          <CapabilityGuard capability="triggers.admin">
            <Button
              variant="secondary"
              leftIcon={<Zap size={16} />}
              onClick={() => fireTrigger.mutate({ id: trigger.id })}
              disabled={fireTrigger.isPending}
            >
              Declencher
            </Button>
          </CapabilityGuard>
          <CapabilityGuard capability="triggers.update">
            <Button
              leftIcon={<Edit size={16} />}
              onClick={() => navigate(`/triggers/${trigger.id}/edit`)}
            >
              Modifier
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      }
    >
      {/* Statut */}
      <section className="azals-section">
        <div className="azals-status-bar">
          <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--lg`}>
            {statusConfig.label}
          </span>
          <span className={`azals-badge azals-badge--${severityConfig.color}`}>
            {severityConfig.label}
          </span>
          <span className="azals-text--muted">
            {trigger.trigger_count} declenchements
          </span>
          {trigger.last_triggered_at && (
            <span className="azals-text--muted">
              Dernier: {formatDate(trigger.last_triggered_at)}
            </span>
          )}
        </div>
      </section>

      {/* Informations */}
      <section className="azals-section">
        <Grid cols={2} gap="md">
          <Card title="Configuration">
            <div className="azals-info-list">
              <div className="azals-info-item">
                <span>Type</span>
                <strong>{TRIGGER_TYPE_LABELS[trigger.trigger_type]}</strong>
              </div>
              <div className="azals-info-item">
                <span>Module source</span>
                <strong>{trigger.source_module}</strong>
              </div>
              {trigger.source_entity && (
                <div className="azals-info-item">
                  <span>Entite</span>
                  <strong>{trigger.source_entity}</strong>
                </div>
              )}
              {trigger.source_field && (
                <div className="azals-info-item">
                  <span>Champ</span>
                  <strong>{trigger.source_field}</strong>
                </div>
              )}
              {trigger.threshold_value && (
                <div className="azals-info-item">
                  <span>Seuil</span>
                  <strong>
                    {trigger.threshold_operator} {trigger.threshold_value}
                  </strong>
                </div>
              )}
              {trigger.schedule_cron && (
                <div className="azals-info-item">
                  <span>Planification</span>
                  <code>{trigger.schedule_cron}</code>
                </div>
              )}
            </div>
          </Card>

          <Card title="Escalade">
            <div className="azals-info-list">
              <div className="azals-info-item">
                <span>Escalade activee</span>
                <strong>{trigger.escalation_enabled ? 'Oui' : 'Non'}</strong>
              </div>
              {trigger.escalation_enabled && (
                <>
                  <div className="azals-info-item">
                    <span>Delai d'escalade</span>
                    <strong>{trigger.escalation_delay_minutes} minutes</strong>
                  </div>
                  {trigger.escalation_level && (
                    <div className="azals-info-item">
                      <span>Niveau actuel</span>
                      <strong>{trigger.escalation_level}</strong>
                    </div>
                  )}
                </>
              )}
              <div className="azals-info-item">
                <span>Cooldown</span>
                <strong>{trigger.cooldown_minutes} minutes</strong>
              </div>
            </div>
          </Card>
        </Grid>
      </section>

      {/* Condition */}
      <section className="azals-section">
        <Card title="Condition">
          <pre className="azals-code-block">
            {JSON.stringify(trigger.condition, null, 2)}
          </pre>
        </Card>
      </section>

      {/* Description */}
      {trigger.description && (
        <section className="azals-section">
          <Card title="Description">
            <p>{trigger.description}</p>
          </Card>
        </section>
      )}

      {/* Metadonnees */}
      <section className="azals-section">
        <Card title="Informations">
          <div className="azals-info-list azals-info-list--horizontal">
            <div className="azals-info-item">
              <span>Cree le</span>
              <strong>{formatDate(trigger.created_at)}</strong>
            </div>
            <div className="azals-info-item">
              <span>Modifie le</span>
              <strong>{formatDate(trigger.updated_at)}</strong>
            </div>
          </div>
        </Card>
      </section>
    </PageWrapper>
  );
};

export default TriggerDetailPage;
