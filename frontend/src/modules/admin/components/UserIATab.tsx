/**
 * AZALSCORE Module - Admin - User IA Tab
 * Onglet Assistant IA pour l'utilisateur
 */

import React, { useState } from 'react';
import {
  Sparkles, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ChevronRight, CheckCircle2,
  Shield, Key, Activity, Lock
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { AdminUser } from '../types';
import {
  isUserActive, isUserLocked, mustChangePassword,
  hasTwoFactorEnabled, isPasswordOld, getPasswordAgeDays,
  formatDate
} from '../types';

/**
 * UserIATab - Assistant IA
 */
export const UserIATab: React.FC<TabContentProps<AdminUser>> = ({ data: user }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(user);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  return (
    <div className="azals-std-tab-content">
      {/* En-tete IA (mode AZALSCORE) */}
      <div className="azals-std-ia-panel azals-std-azalscore-only">
        <div className="azals-std-ia-panel__header">
          <Sparkles size={24} className="azals-std-ia-panel__icon" />
          <h3 className="azals-std-ia-panel__title">Assistant AZALSCORE IA</h3>
        </div>
        <div className="azals-std-ia-panel__content">
          <p>
            J'ai analyse ce profil utilisateur et identifie{' '}
            <strong>{insights.length} points d'attention</strong>.
            {insights.filter(i => i.type === 'warning').length > 0 && (
              <span className="text-warning ml-1">
                ({insights.filter(i => i.type === 'warning').length} alertes)
              </span>
            )}
          </p>
        </div>
        <div className="azals-std-ia-panel__actions">
          <Button
            variant="secondary"
            leftIcon={<RefreshCw size={16} className={isAnalyzing ? 'azals-spin' : ''} />}
            onClick={handleRefreshAnalysis}
            disabled={isAnalyzing}
          >
            Relancer l'analyse
          </Button>
        </div>
      </div>

      {/* Score de securite */}
      <Card title="Score de securite" icon={<Shield size={18} />} className="mb-4">
        <div className="azals-score-display">
          <div className="azals-score-display__circle">
            <svg viewBox="0 0 36 36" className="azals-score-display__svg">
              <path
                className="azals-score-display__bg"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="3"
              />
              <path
                className="azals-score-display__fg"
                strokeDasharray={`${calculateSecurityScore(user)}, 100`}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke={calculateSecurityScore(user) >= 80 ? 'var(--azals-success-500)' : calculateSecurityScore(user) >= 50 ? 'var(--azals-warning-500)' : 'var(--azals-danger-500)'}
                strokeWidth="3"
                strokeLinecap="round"
              />
            </svg>
            <span className="azals-score-display__value">
              {calculateSecurityScore(user)}
            </span>
          </div>
          <div className="azals-score-display__details">
            <p>
              {insights.filter(i => i.type === 'success').length} points positifs,{' '}
              {insights.filter(i => i.type === 'warning').length} alertes,{' '}
              {insights.filter(i => i.type === 'suggestion').length} suggestions
            </p>
          </div>
        </div>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Insights */}
        <Card title="Insights IA" icon={<Lightbulb size={18} />}>
          <div className="azals-insights-list">
            {insights.map((insight) => (
              <InsightItem key={insight.id} insight={insight} />
            ))}
          </div>
        </Card>

        {/* Actions suggerees */}
        <Card title="Actions suggerees" icon={<ChevronRight size={18} />}>
          <div className="azals-suggested-actions">
            {mustChangePassword(user) && (
              <SuggestedAction
                title="Forcer changement MDP"
                description="L'utilisateur doit changer son mot de passe."
                confidence={100}
                icon={<Key size={16} />}
              />
            )}
            {!hasTwoFactorEnabled(user) && (
              <SuggestedAction
                title="Activer 2FA"
                description="Renforcer la securite du compte."
                confidence={90}
                icon={<Shield size={16} />}
              />
            )}
            {isPasswordOld(user) && (
              <SuggestedAction
                title="Renouveler mot de passe"
                description={`Mot de passe age de ${getPasswordAgeDays(user)} jours.`}
                confidence={85}
                icon={<Key size={16} />}
              />
            )}
            {isUserLocked(user) && (
              <SuggestedAction
                title="Debloquer le compte"
                description="Le compte est actuellement bloque."
                confidence={80}
                icon={<Lock size={16} />}
              />
            )}
            {user.failed_login_count > 5 && (
              <SuggestedAction
                title="Verifier les tentatives"
                description={`${user.failed_login_count} echecs de connexion.`}
                confidence={75}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {isUserActive(user) && hasTwoFactorEnabled(user) && !isPasswordOld(user) && (
              <SuggestedAction
                title="Compte conforme"
                description="Aucune action requise."
                confidence={100}
                icon={<ThumbsUp size={16} />}
              />
            )}
          </div>
        </Card>
      </Grid>

      {/* Analyse detaillee (ERP only) */}
      <Card
        title="Analyse detaillee"
        icon={<Activity size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-analysis-grid">
          <div className="azals-analysis-item">
            <h4>Connexions</h4>
            <p className="text-lg font-medium text-primary">{user.login_count}</p>
            <p className="text-sm text-muted">totales</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Echecs</h4>
            <p className={`text-lg font-medium ${user.failed_login_count > 3 ? 'text-red-600' : 'text-green-600'}`}>
              {user.failed_login_count}
            </p>
            <p className="text-sm text-muted">tentatives</p>
          </div>
          <div className="azals-analysis-item">
            <h4>MDP</h4>
            <p className={`text-lg font-medium ${isPasswordOld(user) ? 'text-orange-600' : 'text-green-600'}`}>
              {getPasswordAgeDays(user) >= 0 ? `${getPasswordAgeDays(user)}j` : '-'}
            </p>
            <p className="text-sm text-muted">d'anciennete</p>
          </div>
          <div className="azals-analysis-item">
            <h4>2FA</h4>
            <p className={`text-lg font-medium ${hasTwoFactorEnabled(user) ? 'text-green-600' : 'text-orange-600'}`}>
              {hasTwoFactorEnabled(user) ? 'Actif' : 'Inactif'}
            </p>
            <p className="text-sm text-muted">statut</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

/**
 * Types pour les insights
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Composant item d'insight
 */
const InsightItem: React.FC<{ insight: Insight }> = ({ insight }) => {
  const getIcon = () => {
    switch (insight.type) {
      case 'success':
        return <ThumbsUp size={16} className="text-success" />;
      case 'warning':
        return <AlertTriangle size={16} className="text-warning" />;
      case 'suggestion':
        return <Lightbulb size={16} className="text-primary" />;
    }
  };

  return (
    <div className={`azals-insight azals-insight--${insight.type}`}>
      <div className="azals-insight__icon">{getIcon()}</div>
      <div className="azals-insight__content">
        <h4 className="azals-insight__title">{insight.title}</h4>
        <p className="azals-insight__description">{insight.description}</p>
      </div>
    </div>
  );
};

/**
 * Composant action suggeree
 */
interface SuggestedActionProps {
  title: string;
  description: string;
  confidence: number;
  icon?: React.ReactNode;
}

const SuggestedAction: React.FC<SuggestedActionProps> = ({ title, description, confidence, icon }) => {
  return (
    <div className="azals-suggested-action">
      <div className="azals-suggested-action__content">
        <h4>
          {icon && <span className="mr-2">{icon}</span>}
          {title}
        </h4>
        <p className="text-muted text-sm">{description}</p>
      </div>
      <div className="azals-suggested-action__confidence">
        <span className={`azals-confidence azals-confidence--${confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low'}`}>
          {confidence}%
        </span>
      </div>
    </div>
  );
};

/**
 * Calculer le score de securite
 */
function calculateSecurityScore(user: AdminUser): number {
  let score = 50; // Base

  // 2FA active
  if (hasTwoFactorEnabled(user)) score += 20;

  // Mot de passe recent
  const passwordAge = getPasswordAgeDays(user);
  if (passwordAge >= 0 && passwordAge <= 30) score += 15;
  else if (passwordAge > 90) score -= 10;

  // Compte actif
  if (isUserActive(user)) score += 10;
  else if (isUserLocked(user)) score -= 20;

  // Pas d'echecs de connexion
  if (user.failed_login_count === 0) score += 5;
  else if (user.failed_login_count > 5) score -= 15;

  // Pas de changement requis
  if (!mustChangePassword(user)) score += 10;
  else score -= 10;

  return Math.max(0, Math.min(100, score));
}

/**
 * Generer les insights bases sur l'utilisateur
 */
function generateInsights(user: AdminUser): Insight[] {
  const insights: Insight[] = [];

  // Statut compte
  if (isUserActive(user)) {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Compte actif',
      description: 'Le compte est actif et operationnel.'
    });
  } else if (isUserLocked(user)) {
    insights.push({
      id: 'locked',
      type: 'warning',
      title: 'Compte bloque',
      description: 'Le compte est actuellement bloque ou suspendu.'
    });
  } else {
    insights.push({
      id: 'inactive',
      type: 'suggestion',
      title: 'Compte inactif',
      description: 'Le compte n\'est pas actif.'
    });
  }

  // 2FA
  if (hasTwoFactorEnabled(user)) {
    insights.push({
      id: '2fa-enabled',
      type: 'success',
      title: '2FA active',
      description: 'L\'authentification a deux facteurs est activee.'
    });
  } else {
    insights.push({
      id: '2fa-disabled',
      type: 'warning',
      title: '2FA desactivee',
      description: 'Recommande d\'activer l\'authentification a deux facteurs.'
    });
  }

  // Mot de passe
  if (mustChangePassword(user)) {
    insights.push({
      id: 'password-change-required',
      type: 'warning',
      title: 'Changement MDP requis',
      description: 'L\'utilisateur doit changer son mot de passe.'
    });
  } else if (isPasswordOld(user)) {
    insights.push({
      id: 'password-old',
      type: 'suggestion',
      title: 'Mot de passe ancien',
      description: `Le mot de passe a ${getPasswordAgeDays(user)} jours.`
    });
  } else {
    insights.push({
      id: 'password-ok',
      type: 'success',
      title: 'Mot de passe recent',
      description: 'Le mot de passe est a jour.'
    });
  }

  // Echecs de connexion
  if (user.failed_login_count > 5) {
    insights.push({
      id: 'many-failures',
      type: 'warning',
      title: 'Echecs multiples',
      description: `${user.failed_login_count} tentatives echouees detectees.`
    });
  } else if (user.failed_login_count > 0) {
    insights.push({
      id: 'some-failures',
      type: 'suggestion',
      title: 'Quelques echecs',
      description: `${user.failed_login_count} echec(s) de connexion.`
    });
  }

  // Activite
  if (user.login_count >= 100) {
    insights.push({
      id: 'high-activity',
      type: 'success',
      title: 'Utilisateur actif',
      description: `${user.login_count} connexions enregistrees.`
    });
  } else if (user.login_count < 5) {
    insights.push({
      id: 'low-activity',
      type: 'suggestion',
      title: 'Faible activite',
      description: 'Peu de connexions pour ce compte.'
    });
  }

  return insights;
}

export default UserIATab;
