/**
 * AZALSCORE Module - HR - Employee IA Tab
 * Onglet Assistant IA pour l'employe
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  TrendingUp, Calendar, FileText, GraduationCap, Euro
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Employee } from '../types';
import {
  getSeniority, getSeniorityFormatted,
  EMPLOYEE_STATUS_CONFIG, CONTRACT_TYPE_CONFIG,
  isActive, isOnLeave, isContractExpiringSoon, isOnProbation,
  getRemainingLeave, getTotalRemainingLeave, getPendingLeaveRequests
} from '../types';
import { formatDate } from '@/utils/formatters';

// Composants partagés IA (AZA-NF-REUSE)
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';

/**
 * EmployeeIATab - Assistant IA pour l'employe
 */
export const EmployeeIATab: React.FC<TabContentProps<Employee>> = ({ data: employee }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights (conversion vers format partagé)
  const insights = generateInsights(employee);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(employee);

  // Calcul du score d'engagement
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const engagementScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={`J'ai analysé le dossier de cet employé et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score engagement - Composant partagé */}
      <Card title="Score d'engagement" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={engagementScore}
          label="Engagement"
          details={`${positiveCount} points positifs, ${warningCount} alertes, ${insights.filter(i => i.type === 'suggestion').length} suggestions`}
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
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-analysis-grid">
          <div className="azals-analysis-item">
            <h4>Statut</h4>
            <p className={`text-lg font-medium text-${EMPLOYEE_STATUS_CONFIG[employee.status].color}`}>
              {EMPLOYEE_STATUS_CONFIG[employee.status].label}
            </p>
            <p className="text-sm text-muted">
              {EMPLOYEE_STATUS_CONFIG[employee.status].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Anciennete</h4>
            <p className="text-lg font-medium text-primary">
              {getSeniorityFormatted(employee)}
            </p>
            <p className="text-sm text-muted">
              Embauche le {formatDate(employee.hire_date)}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Contrat</h4>
            <p className={`text-lg font-medium text-${CONTRACT_TYPE_CONFIG[employee.contract_type].color}`}>
              {CONTRACT_TYPE_CONFIG[employee.contract_type].label}
            </p>
            <p className="text-sm text-muted">
              {employee.contract_end_date
                ? `Fin: ${formatDate(employee.contract_end_date)}`
                : 'Duree indeterminee'}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Solde conges</h4>
            <p className="text-lg font-medium">
              {getTotalRemainingLeave(employee)} jours
            </p>
            <p className="text-sm text-muted">
              CP: {getRemainingLeave(employee, 'PAID')}j restants
            </p>
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
 * Générer les actions suggérées basées sur l'employé
 */
function generateSuggestedActions(employee: Employee): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isContractExpiringSoon(employee)) {
    actions.push({
      id: 'renew-contract',
      title: 'Renouveler le contrat',
      description: 'Le contrat arrive à échéance bientôt.',
      confidence: 95,
      icon: <FileText size={16} />,
      actionLabel: 'Traiter',
    });
  }

  if (isOnProbation(employee)) {
    actions.push({
      id: 'evaluate-probation',
      title: "Évaluer la période d'essai",
      description: "Planifier l'entretien de fin de période d'essai.",
      confidence: 90,
      icon: <Calendar size={16} />,
      actionLabel: 'Planifier',
    });
  }

  const pendingLeaves = getPendingLeaveRequests(employee);
  if (pendingLeaves.length > 0) {
    actions.push({
      id: 'process-leaves',
      title: 'Traiter les demandes de congés',
      description: `${pendingLeaves.length} demande(s) en attente.`,
      confidence: 85,
      icon: <Calendar size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (getSeniority(employee) >= 1 && !employee.salary) {
    actions.push({
      id: 'complete-file',
      title: 'Compléter le dossier',
      description: 'Informations de rémunération manquantes.',
      confidence: 80,
      icon: <Euro size={16} />,
      actionLabel: 'Modifier',
    });
  }

  if (!employee.documents || employee.documents.length === 0) {
    actions.push({
      id: 'add-documents',
      title: 'Ajouter des documents',
      description: 'Le dossier employé ne contient aucun document.',
      confidence: 75,
      icon: <FileText size={16} />,
      actionLabel: 'Ajouter',
    });
  }

  if (getSeniority(employee) >= 2) {
    actions.push({
      id: 'propose-training',
      title: 'Proposer une formation',
      description: "L'employé pourrait bénéficier d'une montée en compétences.",
      confidence: 70,
      icon: <GraduationCap size={16} />,
      actionLabel: 'Planifier',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur l'employé
 */
function generateInsights(employee: Employee): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (isActive(employee)) {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Employe actif',
      description: 'L\'employe est en poste et actif.',
    });
  } else if (isOnLeave(employee)) {
    insights.push({
      id: 'on-leave',
      type: 'suggestion',
      title: 'En conge',
      description: 'L\'employe est actuellement en conge.',
    });
  }

  // Anciennete
  const seniority = getSeniority(employee);
  if (seniority >= 5) {
    insights.push({
      id: 'senior',
      type: 'success',
      title: 'Employe senior',
      description: `${seniority} ans d'anciennete dans l'entreprise.`,
    });
  } else if (seniority < 1) {
    insights.push({
      id: 'new-hire',
      type: 'suggestion',
      title: 'Nouvel employe',
      description: 'Moins d\'un an dans l\'entreprise - suivi recommande.',
    });
  }

  // Contrat
  if (isContractExpiringSoon(employee)) {
    insights.push({
      id: 'contract-expiring',
      type: 'warning',
      title: 'Contrat expirant',
      description: `Le contrat se termine le ${formatDate(employee.contract_end_date!)}.`,
    });
  }

  // Periode d'essai
  if (isOnProbation(employee)) {
    insights.push({
      id: 'probation',
      type: 'warning',
      title: 'Periode d\'essai en cours',
      description: `Fin prevue le ${formatDate(employee.probation_end_date!)}.`,
    });
  }

  // Conges
  const pendingLeaves = getPendingLeaveRequests(employee);
  if (pendingLeaves.length > 0) {
    insights.push({
      id: 'pending-leaves',
      type: 'warning',
      title: 'Demandes en attente',
      description: `${pendingLeaves.length} demande(s) de conge a traiter.`,
    });
  }

  const remainingLeave = getRemainingLeave(employee, 'PAID');
  if (remainingLeave > 20) {
    insights.push({
      id: 'high-leave-balance',
      type: 'suggestion',
      title: 'Solde de conges eleve',
      description: `${remainingLeave} jours de CP restants - planifier des conges.`,
    });
  }

  // Documents
  if (!employee.documents || employee.documents.length === 0) {
    insights.push({
      id: 'no-documents',
      type: 'suggestion',
      title: 'Dossier incomplet',
      description: 'Aucun document dans le dossier employe.',
    });
  }

  // Coordonnees
  if (!employee.phone && !employee.mobile) {
    insights.push({
      id: 'no-phone',
      type: 'suggestion',
      title: 'Telephone manquant',
      description: 'Aucun numero de telephone renseigne.',
    });
  }

  // Salaire
  if (!employee.salary && seniority >= 1) {
    insights.push({
      id: 'no-salary',
      type: 'suggestion',
      title: 'Remuneration non renseignee',
      description: 'Le salaire n\'est pas indique dans le dossier.',
    });
  }

  return insights;
}

export default EmployeeIATab;
