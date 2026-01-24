/**
 * AZALSCORE Module - HR - Employee IA Tab
 * Onglet Assistant IA pour l'employe
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Calendar, FileText, GraduationCap, Euro
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Employee } from '../types';
import {
  formatDate, formatCurrency, getSeniority, getSeniorityFormatted,
  EMPLOYEE_STATUS_CONFIG, CONTRACT_TYPE_CONFIG,
  isActive, isOnLeave, isContractExpiringSoon, isOnProbation,
  getRemainingLeave, getTotalRemainingLeave, getPendingLeaveRequests
} from '../types';

/**
 * EmployeeIATab - Assistant IA pour l'employe
 */
export const EmployeeIATab: React.FC<TabContentProps<Employee>> = ({ data: employee }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Generer les insights
  const insights = generateInsights(employee);

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
            J'ai analyse le dossier de cet employe et identifie{' '}
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
          <Button variant="ghost" leftIcon={<MessageSquare size={16} />}>
            Poser une question
          </Button>
        </div>
      </div>

      {/* Score engagement */}
      <Card title="Score d'engagement" icon={<TrendingUp size={18} />} className="mb-4">
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
                strokeDasharray={`${insights.filter(i => i.type !== 'warning').length * 20}, 100`}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="var(--azals-primary-500)"
                strokeWidth="3"
                strokeLinecap="round"
              />
            </svg>
            <span className="azals-score-display__value">
              {Math.round((insights.filter(i => i.type !== 'warning').length / Math.max(insights.length, 1)) * 100)}%
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
            {isContractExpiringSoon(employee) && (
              <SuggestedAction
                title="Renouveler le contrat"
                description="Le contrat arrive a echeance bientot."
                confidence={95}
                icon={<FileText size={16} />}
              />
            )}
            {isOnProbation(employee) && (
              <SuggestedAction
                title="Evaluer la periode d'essai"
                description="Planifier l'entretien de fin de periode d'essai."
                confidence={90}
                icon={<Calendar size={16} />}
              />
            )}
            {getPendingLeaveRequests(employee).length > 0 && (
              <SuggestedAction
                title="Traiter les demandes de conges"
                description={`${getPendingLeaveRequests(employee).length} demande(s) en attente.`}
                confidence={85}
                icon={<Calendar size={16} />}
              />
            )}
            {getSeniority(employee) >= 1 && !employee.salary && (
              <SuggestedAction
                title="Completer le dossier"
                description="Informations de remuneration manquantes."
                confidence={80}
                icon={<Euro size={16} />}
              />
            )}
            {(!employee.documents || employee.documents.length === 0) && (
              <SuggestedAction
                title="Ajouter des documents"
                description="Le dossier employe ne contient aucun document."
                confidence={75}
                icon={<FileText size={16} />}
              />
            )}
            {getSeniority(employee) >= 2 && (
              <SuggestedAction
                title="Proposer une formation"
                description="L'employe pourrait beneficier d'une montee en competences."
                confidence={70}
                icon={<GraduationCap size={16} />}
              />
            )}
          </div>
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
 * Generer les insights bases sur l'employe
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
