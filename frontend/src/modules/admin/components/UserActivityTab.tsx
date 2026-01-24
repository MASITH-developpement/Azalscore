/**
 * AZALSCORE Module - Admin - User Activity Tab
 * Onglet activite utilisateur
 */

import React from 'react';
import {
  Activity, Monitor, Smartphone, Tablet, Globe,
  Clock, CheckCircle2, XCircle, MapPin
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { AdminUser, UserSession } from '../types';
import { formatDateTime, formatDate, formatTime } from '../types';

/**
 * UserActivityTab - Activite utilisateur
 */
export const UserActivityTab: React.FC<TabContentProps<AdminUser>> = ({ data: user }) => {
  const sessions = user.sessions || [];
  const activeSessions = sessions.filter(s => s.is_active);
  const pastSessions = sessions.filter(s => !s.is_active);

  return (
    <div className="azals-std-tab-content">
      {/* Resume activite */}
      <Card title="Resume de l'activite" icon={<Activity size={18} />}>
        <Grid cols={4} gap="md">
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">{user.login_count}</div>
            <div className="text-sm text-muted">Connexions totales</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">{activeSessions.length}</div>
            <div className="text-sm text-muted">Sessions actives</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded">
            <div className="text-2xl font-bold text-red-600">{user.failed_login_count}</div>
            <div className="text-sm text-muted">Echecs de connexion</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-lg font-bold text-gray-600">
              {user.last_login ? formatDate(user.last_login) : 'Jamais'}
            </div>
            <div className="text-sm text-muted">Derniere connexion</div>
          </div>
        </Grid>
      </Card>

      {/* Sessions actives */}
      <Card title={`Sessions actives (${activeSessions.length})`} icon={<CheckCircle2 size={18} />} className="mt-4">
        {activeSessions.length > 0 ? (
          <div className="space-y-3">
            {activeSessions.map((session) => (
              <SessionCard key={session.id} session={session} isActive />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Monitor size={32} className="text-muted" />
            <p className="text-muted">Aucune session active</p>
          </div>
        )}
      </Card>

      {/* Historique des sessions */}
      <Card title="Historique des sessions" icon={<Clock size={18} />} className="mt-4">
        {pastSessions.length > 0 ? (
          <div className="space-y-3">
            {pastSessions.slice(0, 10).map((session) => (
              <SessionCard key={session.id} session={session} isActive={false} />
            ))}
            {pastSessions.length > 10 && (
              <p className="text-center text-sm text-muted pt-2">
                + {pastSessions.length - 10} autres sessions
              </p>
            )}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Clock size={32} className="text-muted" />
            <p className="text-muted">Aucun historique de session</p>
          </div>
        )}
      </Card>

      {/* Statistiques detaillees (ERP only) */}
      <Card title="Statistiques par appareil" icon={<Monitor size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={3} gap="md">
          {(['DESKTOP', 'MOBILE', 'TABLET'] as const).map((deviceType) => {
            const count = sessions.filter(s => s.device_type === deviceType).length;
            const Icon = deviceType === 'DESKTOP' ? Monitor : deviceType === 'MOBILE' ? Smartphone : Tablet;
            const labels = { DESKTOP: 'Bureau', MOBILE: 'Mobile', TABLET: 'Tablette' };
            return (
              <div key={deviceType} className="p-3 bg-gray-50 rounded">
                <div className="flex items-center gap-2 mb-2">
                  <Icon size={18} className="text-muted" />
                  <span className="font-medium">{labels[deviceType]}</span>
                </div>
                <div className="text-xl font-bold">{count}</div>
                <div className="text-sm text-muted">sessions</div>
              </div>
            );
          })}
        </Grid>
      </Card>
    </div>
  );
};

/**
 * Composant carte de session
 */
const SessionCard: React.FC<{ session: UserSession; isActive: boolean }> = ({ session, isActive }) => {
  const getDeviceIcon = () => {
    switch (session.device_type) {
      case 'DESKTOP':
        return <Monitor size={18} />;
      case 'MOBILE':
        return <Smartphone size={18} />;
      case 'TABLET':
        return <Tablet size={18} />;
      default:
        return <Globe size={18} />;
    }
  };

  return (
    <div className={`flex items-center gap-3 p-3 rounded border ${isActive ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
      <div className={`p-2 rounded ${isActive ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'}`}>
        {getDeviceIcon()}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          {isActive ? (
            <span className="azals-badge azals-badge--green text-xs">Active</span>
          ) : (
            <span className="azals-badge azals-badge--gray text-xs">Terminee</span>
          )}
          <span className="text-sm font-mono">{session.ip_address}</span>
          {session.location && (
            <span className="text-sm text-muted flex items-center gap-1">
              <MapPin size={12} />
              {session.location}
            </span>
          )}
        </div>
        <div className="text-sm text-muted">
          Debut: {formatDateTime(session.started_at)}
          {session.ended_at && (
            <span className="ml-3">Fin: {formatDateTime(session.ended_at)}</span>
          )}
        </div>
        <div className="text-xs text-muted mt-1 truncate max-w-md">
          {session.user_agent}
        </div>
      </div>
      <div className="text-right text-sm">
        <div className="text-muted">Derniere activite</div>
        <div className="font-medium">{formatTime(session.last_activity)}</div>
      </div>
    </div>
  );
};

export default UserActivityTab;
