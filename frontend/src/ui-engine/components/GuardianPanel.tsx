/**
 * AZALSCORE GUARDIAN - Panneau d'Incidents Type ERP/Odoo
 * =======================================================
 *
 * Caracteristiques:
 * - Visible immediatement
 * - Non intrusif
 * - Empilable (plusieurs erreurs)
 * - Repliable / depliable
 * - Contenu entierement copiable
 * - Visible meme en cas d'erreur bloquante
 */

import React, { useState, useCallback, useMemo } from 'react';
import { clsx } from 'clsx';
import {
  AlertCircle,
  AlertTriangle,
  Info,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  X,
  Copy,
  Check,
  RefreshCw,
  LogOut,
  Home,
  ArrowLeft,
  Maximize2,
  Minimize2,
  Camera,
  Clock,
  Server,
  User,
  MapPin,
  Activity,
  type LucideIcon,
} from 'lucide-react';
import '@/styles/guardian-panel.css';

// ============================================================
// TYPES
// ============================================================

export type IncidentType = 'auth' | 'api' | 'business' | 'js' | 'network' | 'validation';
export type IncidentSeverity = 'info' | 'warning' | 'error' | 'critical';

export interface GuardianAction {
  id: string;
  action_type: string;
  description: string;
  timestamp: Date;
  success: boolean;
  result: string | null;
}

export interface GuardianIncident {
  id: string;
  type: IncidentType;
  severity: IncidentSeverity;
  tenant_id: string | null;
  user_id: string | null;
  page: string;
  route: string;
  endpoint: string | null;
  method: string | null;
  http_status: number | null;
  message: string;
  details: string | null;
  stack_trace: string | null;
  timestamp: Date;
  screenshot_data: string | null;
  guardian_actions: GuardianAction[];
  is_expanded: boolean;
  is_acknowledged: boolean;
  is_sent_to_backend: boolean;
}

interface GuardianPanelProps {
  incidents: GuardianIncident[];
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onRemoveIncident: (id: string) => void;
  onAcknowledgeIncident: (id: string) => void;
  onToggleExpanded: (id: string) => void;
  onClearAll: () => void;
  onGuardianAction: (incidentId: string, action: string) => void;
}

// ============================================================
// HELPERS
// ============================================================

const SEVERITY_ICONS: Record<IncidentSeverity, LucideIcon> = {
  info: Info,
  warning: AlertTriangle,
  error: AlertCircle,
  critical: ShieldAlert,
};

const SEVERITY_LABELS: Record<IncidentSeverity, string> = {
  info: 'Info',
  warning: 'Attention',
  error: 'Erreur',
  critical: 'Critique',
};

const TYPE_LABELS: Record<IncidentType, string> = {
  auth: 'Authentification',
  api: 'API',
  business: 'Metier',
  js: 'JavaScript',
  network: 'Reseau',
  validation: 'Validation',
};

const formatTimestamp = (date: Date): string => {
  return date.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

/** Keyboard handler for clickable non-button elements */
const handleKeyActivate = (callback: () => void) => (e: React.KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    callback();
  }
};

// ============================================================
// COMPOSANT: INCIDENT CARD
// ============================================================

interface IncidentCardProps {
  incident: GuardianIncident;
  onRemove: () => void;
  onAcknowledge: () => void;
  onToggleExpanded: () => void;
  onGuardianAction: (action: string) => void;
}

const IncidentCard: React.FC<IncidentCardProps> = ({
  incident,
  onRemove,
  onAcknowledge,
  onToggleExpanded,
  onGuardianAction,
}) => {
  const [copied, setCopied] = useState(false);
  const severity = incident.severity;
  const Icon = SEVERITY_ICONS[severity];

  const handleCopy = useCallback(async () => {
    const textContent = `
INCIDENT AZALSCORE
==================
Type: ${TYPE_LABELS[incident.type]}
Severite: ${SEVERITY_LABELS[severity]}
Timestamp: ${incident.timestamp.toISOString()}

Tenant ID: ${incident.tenant_id || 'N/A'}
User ID: ${incident.user_id || 'N/A'}
Page: ${incident.page}
Route: ${incident.route}

${incident.endpoint ? `Endpoint: ${incident.method || 'GET'} ${incident.endpoint}` : ''}
${incident.http_status ? `Status HTTP: ${incident.http_status}` : ''}

Message: ${incident.message}
${incident.details ? `Details: ${incident.details}` : ''}
${incident.stack_trace ? `\nStack Trace:\n${incident.stack_trace}` : ''}

Actions Guardian:
${incident.guardian_actions.map(a => `- [${a.success ? 'OK' : 'FAIL'}] ${a.action_type}: ${a.description}`).join('\n')}
    `.trim();

    try {
      await navigator.clipboard.writeText(textContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      console.error('Failed to copy');
    }
  }, [incident, severity]);

  return (
    <div
      className={clsx(
        'azals-guardian-card',
        `azals-guardian-card--${severity}`,
        incident.is_acknowledged && 'azals-guardian-card--acknowledged'
      )}
    >
      {/* Header */}
      <button
        className="azals-guardian-card__header"
        onClick={onToggleExpanded}
        aria-expanded={incident.is_expanded}
        aria-label={`${SEVERITY_LABELS[severity]}: ${incident.message}`}
      >
        <Icon
          className={clsx('azals-guardian-card__icon', `azals-guardian-card__icon--${severity}`)}
          size={20}
        />

        <div className="azals-guardian-card__summary">
          <div className="azals-guardian-card__meta">
            <span className={clsx('azals-guardian-card__type-badge', `azals-guardian-card__type-badge--${severity}`)}>
              {TYPE_LABELS[incident.type]}
            </span>
            <span className="azals-guardian-card__timestamp">
              {formatTimestamp(incident.timestamp)}
            </span>
            {!incident.is_sent_to_backend && (
              <span className="azals-guardian-card__unsent">
                Non envoye
              </span>
            )}
          </div>
          <p className="azals-guardian-card__message">
            {incident.message}
          </p>
        </div>

        <div className="azals-guardian-card__chevron">
          {incident.is_expanded ? (
            <ChevronUp size={16} />
          ) : (
            <ChevronDown size={16} />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {incident.is_expanded && (
        <div className="azals-guardian-card__body">
          {/* Metadonnees */}
          <div className="azals-guardian-card__metadata">
            <div className="azals-guardian-card__meta-item">
              <User size={12} />
              <span>Tenant: {incident.tenant_id || 'N/A'}</span>
            </div>
            <div className="azals-guardian-card__meta-item">
              <MapPin size={12} />
              <span>Route: {incident.route}</span>
            </div>
            {incident.endpoint && (
              <div className="azals-guardian-card__meta-item azals-guardian-card__meta-item--full">
                <Server size={12} />
                <span>
                  {incident.method || 'GET'} {incident.endpoint}
                  {incident.http_status && ` \u2192 ${incident.http_status}`}
                </span>
              </div>
            )}
          </div>

          {/* Details */}
          {incident.details && (
            <div className="azals-guardian-card__details">
              <p className="azals-guardian-card__details-label">Details:</p>
              <p className="azals-guardian-card__details-text">
                {incident.details}
              </p>
            </div>
          )}

          {/* Stack Trace */}
          {incident.stack_trace && (
            <div className="azals-guardian-card__stack">
              <p className="azals-guardian-card__stack-label">Stack Trace:</p>
              <pre className="azals-guardian-card__stack-pre">
                {incident.stack_trace}
              </pre>
            </div>
          )}

          {/* Screenshot */}
          {incident.screenshot_data && (
            <div className="azals-guardian-card__screenshot">
              <p className="azals-guardian-card__screenshot-label">
                <Camera size={12} />
                Capture d'ecran:
              </p>
              <img
                src={incident.screenshot_data}
                alt="Capture ecran incident"
                className="azals-guardian-card__screenshot-img"
              />
            </div>
          )}

          {/* Guardian Actions */}
          {incident.guardian_actions.length > 0 && (
            <div className="azals-guardian-card__actions-log">
              <p className="azals-guardian-card__actions-log-label">
                <Activity size={12} />
                Actions Guardian:
              </p>
              <div className="azals-guardian-card__actions-log-list">
                {incident.guardian_actions.map((action) => (
                  <div
                    key={action.id}
                    className={clsx(
                      'azals-guardian-card__action-entry',
                      action.success
                        ? 'azals-guardian-card__action-entry--success'
                        : 'azals-guardian-card__action-entry--failure'
                    )}
                  >
                    <span className="azals-guardian-card__action-status">[{action.success ? 'OK' : 'FAIL'}]</span>
                    <div>
                      <span className="azals-guardian-card__action-type">{action.action_type}</span>
                      <span className="azals-guardian-card__action-separator">-</span>
                      <span>{action.description}</span>
                      {action.result && (
                        <p className="azals-guardian-card__action-detail-text">{action.result}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions utilisateur */}
          <div className="azals-guardian-card__user-actions">
            <button
              onClick={handleCopy}
              className="azals-guardian-action-btn azals-guardian-action-btn--gray"
              aria-label="Copier l'incident"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? 'Copie!' : 'Copier'}
            </button>

            {/* Actions Guardian disponibles selon le type */}
            {(incident.type === 'auth' || incident.http_status === 401) && (
              <>
                <button
                  onClick={() => onGuardianAction('refresh_token')}
                  className="azals-guardian-action-btn azals-guardian-action-btn--blue"
                  aria-label="Rafraichir le token"
                >
                  <RefreshCw size={12} />
                  Rafraichir token
                </button>
                <button
                  onClick={() => onGuardianAction('force_logout')}
                  className="azals-guardian-action-btn azals-guardian-action-btn--orange"
                  aria-label="Forcer la deconnexion"
                >
                  <LogOut size={12} />
                  Deconnexion
                </button>
              </>
            )}

            {incident.severity === 'critical' && (
              <button
                onClick={() => onGuardianAction('reload')}
                className="azals-guardian-action-btn azals-guardian-action-btn--purple"
                aria-label="Recharger la page"
              >
                <RefreshCw size={12} />
                Recharger page
              </button>
            )}

            <button
              onClick={() => onGuardianAction('go_back')}
              className="azals-guardian-action-btn azals-guardian-action-btn--gray"
              aria-label="Retour"
            >
              <ArrowLeft size={12} />
              Retour
            </button>

            <button
              onClick={() => onGuardianAction('go_cockpit')}
              className="azals-guardian-action-btn azals-guardian-action-btn--gray"
              aria-label="Aller au cockpit"
            >
              <Home size={12} />
              Cockpit
            </button>

            {!incident.is_acknowledged && (
              <button
                onClick={onAcknowledge}
                className="azals-guardian-action-btn azals-guardian-action-btn--green azals-guardian-action-btn--ml-auto"
                aria-label="Acquitter l'incident"
              >
                <Check size={12} />
                Acquitter
              </button>
            )}

            <button
              onClick={onRemove}
              className="azals-guardian-action-btn azals-guardian-action-btn--red"
              aria-label="Fermer l'incident"
            >
              <X size={12} />
              Fermer
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================
// COMPOSANT PRINCIPAL: GUARDIAN PANEL
// ============================================================

export const GuardianPanel: React.FC<GuardianPanelProps> = ({
  incidents,
  isCollapsed,
  onToggleCollapse,
  onRemoveIncident,
  onAcknowledgeIncident,
  onToggleExpanded,
  onClearAll,
  onGuardianAction,
}) => {
  const [isMinimized, setIsMinimized] = useState(false);

  // Statistiques
  const stats = useMemo(() => {
    return {
      total: incidents.length,
      critical: incidents.filter((i) => i.severity === 'critical').length,
      error: incidents.filter((i) => i.severity === 'error').length,
      warning: incidents.filter((i) => i.severity === 'warning').length,
      unacknowledged: incidents.filter((i) => !i.is_acknowledged).length,
    };
  }, [incidents]);

  if (incidents.length === 0) return null;

  // Mode minimise (badge seulement)
  if (isMinimized) {
    return (
      <div className="azals-guardian-minimized">
        <button
          className={clsx(
            'azals-guardian-minimized__pill',
            stats.critical > 0
              ? 'azals-guardian-minimized__pill--critical'
              : stats.error > 0
              ? 'azals-guardian-minimized__pill--error'
              : 'azals-guardian-minimized__pill--default'
          )}
          onClick={() => setIsMinimized(false)}
          aria-label={`${stats.total} incident${stats.total > 1 ? 's' : ''} - Cliquer pour agrandir`}
        >
          <ShieldAlert size={20} />
          <span className="azals-guardian-minimized__count">{stats.total}</span>
          <span className="azals-guardian-minimized__label">incident{stats.total > 1 ? 's' : ''}</span>
          <Maximize2 className="azals-guardian-minimized__expand-icon" size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className="azals-guardian-panel">
      {/* Header */}
      <div
        className="azals-guardian-header"
        role="button"
        tabIndex={0}
        onClick={onToggleCollapse}
        onKeyDown={handleKeyActivate(onToggleCollapse)}
        aria-expanded={!isCollapsed}
        aria-label="Basculer le panneau Guardian"
      >
        <div className="azals-guardian-header__left">
          <ShieldAlert size={20} />
          <span className="azals-guardian-header__title">GUARDIAN</span>

          {/* Badges de comptage */}
          <div className="azals-guardian-header__badges">
            {stats.critical > 0 && (
              <span className="azals-guardian-header__badge azals-guardian-header__badge--critical">
                {stats.critical} crit
              </span>
            )}
            {stats.error > 0 && (
              <span className="azals-guardian-header__badge azals-guardian-header__badge--error">
                {stats.error} err
              </span>
            )}
            {stats.warning > 0 && (
              <span className="azals-guardian-header__badge azals-guardian-header__badge--warning">
                {stats.warning} warn
              </span>
            )}
          </div>
        </div>

        <div className="azals-guardian-header__right">
          <span className="azals-guardian-header__unack">
            {stats.unacknowledged} non acquitte{stats.unacknowledged > 1 ? 's' : ''}
          </span>

          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsMinimized(true);
            }}
            className="azals-guardian-header__minimize-btn"
            title="Minimiser"
            aria-label="Minimiser le panneau Guardian"
          >
            <Minimize2 size={16} />
          </button>

          {isCollapsed ? (
            <ChevronUp size={20} />
          ) : (
            <ChevronDown size={20} />
          )}
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <>
          {/* Toolbar */}
          <div className="azals-guardian-toolbar">
            <span className="azals-guardian-toolbar__info">
              <Clock className="azals-guardian-toolbar__info-icon" size={12} />
              {incidents.length} incident{incidents.length > 1 ? 's' : ''} actif{incidents.length > 1 ? 's' : ''}
            </span>
            <button
              onClick={onClearAll}
              className="azals-guardian-toolbar__clear-btn"
              aria-label="Effacer tous les incidents"
            >
              Tout effacer
            </button>
          </div>

          {/* Liste des incidents */}
          <div className="azals-guardian-list">
            {incidents.map((incident) => (
              <IncidentCard
                key={incident.id}
                incident={incident}
                onRemove={() => onRemoveIncident(incident.id)}
                onAcknowledge={() => onAcknowledgeIncident(incident.id)}
                onToggleExpanded={() => onToggleExpanded(incident.id)}
                onGuardianAction={(action) => onGuardianAction(incident.id, action)}
              />
            ))}
          </div>

          {/* Footer */}
          <div className="azals-guardian-footer">
            AZALSCORE V1 - Systeme GUARDIAN actif
          </div>
        </>
      )}
    </div>
  );
};

export default GuardianPanel;
