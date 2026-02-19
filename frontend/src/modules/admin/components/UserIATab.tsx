/**
 * AZALSCORE Module - Admin - User IA Tab
 * Onglet Assistant IA pour l'utilisateur
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  AlertTriangle, ThumbsUp, Shield, Key, Activity, Lock
} from 'lucide-react';
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';
import { Card, Grid } from '@ui/layout';
import {
  isUserActive, isUserLocked, mustChangePassword,
  hasTwoFactorEnabled, isPasswordOld, getPasswordAgeDays
} from '../types';
import type { AdminUser } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * UserIATab - Assistant IA
 */
export const UserIATab: React.FC<TabContentProps<AdminUser>> = ({ data: user }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(user);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(user);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const securityScore = calculateSecurityScore(user);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce profil utilisateur et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de sécurité - Composant partagé */}
      <Card title="Score de sécurité" icon={<Shield size={18} />} className="mb-4">
        <IAScoreCircle
          score={securityScore}
          label="Sécurité"
          details={`${positiveCount} points positifs, ${warningCount} alertes, ${suggestionCount} suggestions`}
        />
      </Card>

      <Grid cols={2} gap="lg">
        {/* Insights - Composant partagé */}
        <Card title="Insights IA">
          <InsightList insights={sharedInsights} />
        </Card>

        {/* Actions suggérées - Composant partagé */}
        <Card title="Actions suggérées">
          <SuggestedActionList
            actions={suggestedActions}
            emptyMessage="Aucune action suggérée pour le moment"
          />
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur l'utilisateur
 */
function generateSuggestedActions(user: AdminUser): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (mustChangePassword(user)) {
    actions.push({
      id: 'force-pwd',
      title: 'Forcer changement MDP',
      description: "L'utilisateur doit changer son mot de passe.",
      confidence: 100,
      icon: <Key size={16} />,
      actionLabel: 'Forcer',
    });
  }

  if (!hasTwoFactorEnabled(user)) {
    actions.push({
      id: '2fa',
      title: 'Activer 2FA',
      description: 'Renforcer la sécurité du compte.',
      confidence: 90,
      icon: <Shield size={16} />,
      actionLabel: 'Activer',
    });
  }

  if (isPasswordOld(user)) {
    actions.push({
      id: 'renew-pwd',
      title: 'Renouveler mot de passe',
      description: `Mot de passe âgé de ${getPasswordAgeDays(user)} jours.`,
      confidence: 85,
      icon: <Key size={16} />,
      actionLabel: 'Renouveler',
    });
  }

  if (isUserLocked(user)) {
    actions.push({
      id: 'unlock',
      title: 'Débloquer le compte',
      description: 'Le compte est actuellement bloqué.',
      confidence: 80,
      icon: <Lock size={16} />,
      actionLabel: 'Débloquer',
    });
  }

  if (user.failed_login_count > 5) {
    actions.push({
      id: 'check-failures',
      title: 'Vérifier les tentatives',
      description: `${user.failed_login_count} échecs de connexion.`,
      confidence: 75,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (isUserActive(user) && hasTwoFactorEnabled(user) && !isPasswordOld(user)) {
    actions.push({
      id: 'ok',
      title: 'Compte conforme',
      description: 'Aucune action requise.',
      confidence: 100,
      icon: <ThumbsUp size={16} />,
    });
  }

  return actions;
}

/**
 * Calculer le score de sécurité
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
