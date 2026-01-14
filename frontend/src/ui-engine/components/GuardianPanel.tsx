/**
 * AZALSCORE GUARDIAN - Panneau d'Incidents Type ERP/Odoo
 * =======================================================
 *
 * Caractéristiques:
 * - Visible immédiatement
 * - Non intrusif
 * - Empilable (plusieurs erreurs)
 * - Repliable / dépliable
 * - Contenu entièrement copiable
 * - Visible même en cas d'erreur bloquante
 */

import React, { useState, useCallback, useMemo } from 'react';
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
} from 'lucide-react';
import { clsx } from 'clsx';

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

const SEVERITY_CONFIG = {
  info: {
    icon: Info,
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    badge: 'bg-blue-100 text-blue-800',
    label: 'Info',
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-yellow-600',
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    badge: 'bg-yellow-100 text-yellow-800',
    label: 'Attention',
  },
  error: {
    icon: AlertCircle,
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
    badge: 'bg-red-100 text-red-800',
    label: 'Erreur',
  },
  critical: {
    icon: ShieldAlert,
    color: 'text-red-700',
    bg: 'bg-red-100',
    border: 'border-red-300',
    badge: 'bg-red-200 text-red-900',
    label: 'Critique',
  },
};

const TYPE_LABELS: Record<IncidentType, string> = {
  auth: 'Authentification',
  api: 'API',
  business: 'Métier',
  js: 'JavaScript',
  network: 'Réseau',
  validation: 'Validation',
};

const formatTimestamp = (date: Date): string => {
  return date.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
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
  const config = SEVERITY_CONFIG[incident.severity];
  const Icon = config.icon;

  const handleCopy = useCallback(async () => {
    const textContent = `
INCIDENT AZALSCORE
==================
Type: ${TYPE_LABELS[incident.type]}
Sévérité: ${config.label}
Timestamp: ${incident.timestamp.toISOString()}

Tenant ID: ${incident.tenant_id || 'N/A'}
User ID: ${incident.user_id || 'N/A'}
Page: ${incident.page}
Route: ${incident.route}

${incident.endpoint ? `Endpoint: ${incident.method || 'GET'} ${incident.endpoint}` : ''}
${incident.http_status ? `Status HTTP: ${incident.http_status}` : ''}

Message: ${incident.message}
${incident.details ? `Détails: ${incident.details}` : ''}
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
  }, [incident, config.label]);

  return (
    <div
      className={clsx(
        'guardian-incident-card border rounded-lg mb-2 overflow-hidden transition-all',
        config.bg,
        config.border,
        incident.is_acknowledged && 'opacity-60'
      )}
    >
      {/* Header */}
      <div
        className={clsx(
          'flex items-center gap-2 px-3 py-2 cursor-pointer',
          config.bg
        )}
        onClick={onToggleExpanded}
      >
        <Icon className={clsx('w-5 h-5 flex-shrink-0', config.color)} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={clsx('text-xs px-2 py-0.5 rounded font-medium', config.badge)}>
              {TYPE_LABELS[incident.type]}
            </span>
            <span className="text-xs text-gray-500">
              {formatTimestamp(incident.timestamp)}
            </span>
            {!incident.is_sent_to_backend && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-orange-100 text-orange-700">
                Non envoyé
              </span>
            )}
          </div>
          <p className="text-sm font-medium text-gray-900 truncate mt-1">
            {incident.message}
          </p>
        </div>

        <div className="flex items-center gap-1">
          {incident.is_expanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {incident.is_expanded && (
        <div className="px-3 py-2 border-t border-gray-200 bg-white">
          {/* Métadonnées */}
          <div className="grid grid-cols-2 gap-2 text-xs mb-3">
            <div className="flex items-center gap-1 text-gray-600">
              <User className="w-3 h-3" />
              <span>Tenant: {incident.tenant_id || 'N/A'}</span>
            </div>
            <div className="flex items-center gap-1 text-gray-600">
              <MapPin className="w-3 h-3" />
              <span>Route: {incident.route}</span>
            </div>
            {incident.endpoint && (
              <div className="flex items-center gap-1 text-gray-600 col-span-2">
                <Server className="w-3 h-3" />
                <span>
                  {incident.method || 'GET'} {incident.endpoint}
                  {incident.http_status && ` → ${incident.http_status}`}
                </span>
              </div>
            )}
          </div>

          {/* Détails */}
          {incident.details && (
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-700 mb-1">Détails:</p>
              <p className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                {incident.details}
              </p>
            </div>
          )}

          {/* Stack Trace */}
          {incident.stack_trace && (
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-700 mb-1">Stack Trace:</p>
              <pre className="text-xs text-gray-600 bg-gray-900 text-gray-100 p-2 rounded overflow-x-auto max-h-32">
                {incident.stack_trace}
              </pre>
            </div>
          )}

          {/* Screenshot */}
          {incident.screenshot_data && (
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
                <Camera className="w-3 h-3" />
                Capture d'écran:
              </p>
              <img
                src={incident.screenshot_data}
                alt="Capture écran incident"
                className="max-w-full h-auto rounded border border-gray-200 max-h-40 object-contain"
              />
            </div>
          )}

          {/* Guardian Actions */}
          {incident.guardian_actions.length > 0 && (
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
                <Activity className="w-3 h-3" />
                Actions Guardian:
              </p>
              <div className="space-y-1">
                {incident.guardian_actions.map((action) => (
                  <div
                    key={action.id}
                    className={clsx(
                      'text-xs p-2 rounded flex items-start gap-2',
                      action.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                    )}
                  >
                    <span className="font-mono">[{action.success ? 'OK' : 'FAIL'}]</span>
                    <div>
                      <span className="font-medium">{action.action_type}</span>
                      <span className="mx-1">-</span>
                      <span>{action.description}</span>
                      {action.result && (
                        <p className="text-xs opacity-75 mt-0.5">{action.result}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions utilisateur */}
          <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
            >
              {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
              {copied ? 'Copié!' : 'Copier'}
            </button>

            {/* Actions Guardian disponibles selon le type */}
            {(incident.type === 'auth' || incident.http_status === 401) && (
              <>
                <button
                  onClick={() => onGuardianAction('refresh_token')}
                  className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 rounded transition-colors"
                >
                  <RefreshCw className="w-3 h-3" />
                  Rafraîchir token
                </button>
                <button
                  onClick={() => onGuardianAction('force_logout')}
                  className="flex items-center gap-1 px-2 py-1 text-xs bg-orange-100 hover:bg-orange-200 text-orange-800 rounded transition-colors"
                >
                  <LogOut className="w-3 h-3" />
                  Déconnexion
                </button>
              </>
            )}

            {incident.severity === 'critical' && (
              <button
                onClick={() => onGuardianAction('reload')}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-purple-100 hover:bg-purple-200 text-purple-800 rounded transition-colors"
              >
                <RefreshCw className="w-3 h-3" />
                Recharger page
              </button>
            )}

            <button
              onClick={() => onGuardianAction('go_back')}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
            >
              <ArrowLeft className="w-3 h-3" />
              Retour
            </button>

            <button
              onClick={() => onGuardianAction('go_cockpit')}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
            >
              <Home className="w-3 h-3" />
              Cockpit
            </button>

            {!incident.is_acknowledged && (
              <button
                onClick={onAcknowledge}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-green-100 hover:bg-green-200 text-green-800 rounded transition-colors ml-auto"
              >
                <Check className="w-3 h-3" />
                Acquitter
              </button>
            )}

            <button
              onClick={onRemove}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-red-100 hover:bg-red-200 text-red-800 rounded transition-colors"
            >
              <X className="w-3 h-3" />
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

  // Mode minimisé (badge seulement)
  if (isMinimized) {
    return (
      <div
        className="guardian-panel-minimized fixed bottom-4 right-4 z-[9999]"
        onClick={() => setIsMinimized(false)}
      >
        <div
          className={clsx(
            'flex items-center gap-2 px-3 py-2 rounded-full shadow-lg cursor-pointer',
            'transition-all hover:scale-105',
            stats.critical > 0
              ? 'bg-red-600 text-white'
              : stats.error > 0
              ? 'bg-red-500 text-white'
              : 'bg-yellow-500 text-white'
          )}
        >
          <ShieldAlert className="w-5 h-5" />
          <span className="font-bold">{stats.total}</span>
          <span className="text-sm opacity-90">incident{stats.total > 1 ? 's' : ''}</span>
          <Maximize2 className="w-4 h-4 ml-1 opacity-75" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'guardian-panel fixed bottom-0 right-0 z-[9999]',
        'w-full md:w-[480px] max-h-[70vh]',
        'bg-white shadow-2xl border-l border-t border-gray-200 rounded-tl-lg',
        'flex flex-col',
        'transition-all duration-300'
      )}
    >
      {/* Header */}
      <div
        className={clsx(
          'flex items-center justify-between px-4 py-2',
          'bg-gray-800 text-white rounded-tl-lg cursor-pointer'
        )}
        onClick={onToggleCollapse}
      >
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-5 h-5" />
          <span className="font-semibold">GUARDIAN</span>

          {/* Badges de comptage */}
          <div className="flex items-center gap-1.5">
            {stats.critical > 0 && (
              <span className="px-2 py-0.5 text-xs font-bold bg-red-600 rounded-full">
                {stats.critical} crit
              </span>
            )}
            {stats.error > 0 && (
              <span className="px-2 py-0.5 text-xs font-bold bg-red-500 rounded-full">
                {stats.error} err
              </span>
            )}
            {stats.warning > 0 && (
              <span className="px-2 py-0.5 text-xs font-bold bg-yellow-500 text-yellow-900 rounded-full">
                {stats.warning} warn
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-300">
            {stats.unacknowledged} non acquitté{stats.unacknowledged > 1 ? 's' : ''}
          </span>

          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsMinimized(true);
            }}
            className="p-1 hover:bg-gray-700 rounded"
            title="Minimiser"
          >
            <Minimize2 className="w-4 h-4" />
          </button>

          {isCollapsed ? (
            <ChevronUp className="w-5 h-5" />
          ) : (
            <ChevronDown className="w-5 h-5" />
          )}
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <>
          {/* Toolbar */}
          <div className="flex items-center justify-between px-3 py-1.5 bg-gray-100 border-b">
            <span className="text-xs text-gray-600">
              <Clock className="w-3 h-3 inline mr-1" />
              {incidents.length} incident{incidents.length > 1 ? 's' : ''} actif{incidents.length > 1 ? 's' : ''}
            </span>
            <button
              onClick={onClearAll}
              className="text-xs text-red-600 hover:text-red-800 hover:underline"
            >
              Tout effacer
            </button>
          </div>

          {/* Liste des incidents */}
          <div className="flex-1 overflow-y-auto p-2">
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
          <div className="px-3 py-2 bg-gray-50 border-t text-xs text-gray-500 text-center">
            AZALSCORE V1 - Système GUARDIAN actif
          </div>
        </>
      )}
    </div>
  );
};

export default GuardianPanel;
