/**
 * AZALSCORE Module - Ordres de Service - Detail View
 * Vue detail d'une intervention avec BaseViewStandard
 */

import React, { useState } from 'react';
import {
  Wrench, Edit, Download, FileText, Calendar,
  Clock, Play, CheckCircle2, Sparkles
} from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { BaseViewStandard } from '@ui/standards';
import { formatDateTime, formatCurrency, formatDuration } from '@/utils/formatters';
import {
  STATUT_CONFIG, PRIORITE_CONFIG, TYPE_INTERVENTION_CONFIG,
  canEditIntervention, canStartIntervention, canCompleteIntervention, canInvoiceIntervention,
  getInterventionAge, getActualDuration, getPhotoCount, getFullAddress
} from '../types';
import type { Intervention } from '../types';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition, SemanticColor } from '@ui/standards';
import { useIntervention, useDemarrerIntervention, useTerminerIntervention } from '../hooks';
import {
  InterventionInfoTab, InterventionPlanningTab, InterventionPhotosTab,
  InterventionReportTab, InterventionHistoryTab, InterventionIATab
} from './index';

export interface InterventionDetailViewProps {
  interventionId: string;
  onBack: () => void;
  onEdit: (id: string) => void;
}

export const InterventionDetailView: React.FC<InterventionDetailViewProps> = ({
  interventionId,
  onBack,
  onEdit,
}) => {
  const { data: intervention, isLoading } = useIntervention(interventionId);
  const demarrer = useDemarrerIntervention();
  const terminer = useTerminerIntervention();
  const [showTerminer, setShowTerminer] = useState(false);
  const [commentaire, setCommentaire] = useState('');

  if (isLoading) {
    return <PageWrapper title="Chargement..."><div className="azals-loading">Chargement...</div></PageWrapper>;
  }

  if (!intervention) {
    return (
      <PageWrapper title="Intervention non trouvee">
        <Card><p>Cette intervention n'existe pas.</p><Button onClick={onBack}>Retour</Button></Card>
      </PageWrapper>
    );
  }

  const statutConfig = STATUT_CONFIG[intervention.statut];
  const prioriteConfig = PRIORITE_CONFIG[intervention.priorite];
  const canEdit = canEditIntervention(intervention);
  const canStart = canStartIntervention(intervention);
  const canComplete = canCompleteIntervention(intervention);
  const canInvoice = canInvoiceIntervention(intervention);

  const handleDemarrer = async () => {
    if (window.confirm('Demarrer l\'intervention ?')) {
      await demarrer.mutateAsync(interventionId);
    }
  };

  const handleTerminer = async () => {
    await terminer.mutateAsync({ id: interventionId, data: { commentaire_cloture: commentaire } });
    setShowTerminer(false);
  };

  const handleCreateFacture = () => {
    window.dispatchEvent(new CustomEvent('azals:navigate', {
      detail: { view: 'factures', params: { interventionId, action: 'new' } }
    }));
  };

  // Tab definitions
  const tabs: TabDefinition<Intervention>[] = [
    { id: 'info', label: 'Informations', icon: <Wrench size={16} />, component: InterventionInfoTab },
    { id: 'planning', label: 'Planning', icon: <Calendar size={16} />, component: InterventionPlanningTab },
    { id: 'photos', label: 'Photos', icon: <FileText size={16} />, badge: getPhotoCount(intervention), component: InterventionPhotosTab },
    { id: 'report', label: 'Compte-rendu', icon: <CheckCircle2 size={16} />, component: InterventionReportTab },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: InterventionHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: InterventionIATab },
  ];

  // InfoBar items
  const infoBarItems: InfoBarItem[] = [
    { id: 'statut', label: 'Statut', value: statutConfig.label, valueColor: statutConfig.color as SemanticColor },
    { id: 'priorite', label: 'Priorite', value: prioriteConfig.label, valueColor: prioriteConfig.color as SemanticColor },
    { id: 'date', label: 'Date prevue', value: intervention.date_prevue_debut ? formatDateTime(intervention.date_prevue_debut) : '-' },
    { id: 'duree', label: 'Duree', value: getActualDuration(intervention) || (intervention.duree_prevue_minutes ? `~${formatDuration(intervention.duree_prevue_minutes)}` : '-') },
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'intervention',
      title: 'Intervention',
      items: [
        { id: 'reference', label: 'Reference', value: intervention.reference },
        { id: 'type', label: 'Type', value: TYPE_INTERVENTION_CONFIG[intervention.type_intervention]?.label || intervention.type_intervention },
        { id: 'age', label: 'Age', value: getInterventionAge(intervention) },
        { id: 'photos', label: 'Photos', value: `${getPhotoCount(intervention)} photo(s)` },
      ],
    },
    {
      id: 'client',
      title: 'Client',
      items: [
        { id: 'client', label: 'Client', value: intervention.client_name || '-' },
        { id: 'donneur', label: 'Donneur ordre', value: intervention.donneur_ordre_name || '-' },
        { id: 'lieu', label: 'Lieu', value: getFullAddress(intervention) || '-' },
        { id: 'contact', label: 'Contact', value: intervention.contact_sur_place || '-' },
      ],
    },
    {
      id: 'planning',
      title: 'Planning',
      items: [
        { id: 'intervenant', label: 'Intervenant', value: intervention.intervenant_name || 'Non assigne', highlight: !intervention.intervenant_name },
        { id: 'date', label: 'Date', value: intervention.date_prevue_debut ? formatDateTime(intervention.date_prevue_debut) : '-' },
        { id: 'duree', label: 'Duree prevue', value: intervention.duree_prevue_minutes ? formatDuration(intervention.duree_prevue_minutes) : '-' },
      ],
    },
    {
      id: 'facturation',
      title: 'Facturation',
      items: [
        { id: 'facturable', label: 'Facturable', value: intervention.facturable !== false ? 'Oui' : 'Non' },
        { id: 'montant', label: 'Montant HT', value: intervention.montant_ht ? formatCurrency(intervention.montant_ht) : '-' },
        { id: 'facture', label: 'Facture', value: intervention.facture_reference || '-' },
      ],
    },
  ];

  // Header actions
  const headerActions: ActionDefinition[] = [
    { id: 'back', label: 'Retour', variant: 'ghost', onClick: onBack },
    ...(canInvoice ? [{ id: 'invoice', label: 'Creer facture', icon: <FileText size={16} />, onClick: handleCreateFacture }] : []),
    ...(canComplete ? [{ id: 'complete', label: 'Terminer', icon: <CheckCircle2 size={16} />, onClick: () => setShowTerminer(true) }] : []),
    ...(canStart ? [{ id: 'start', label: 'Demarrer', variant: 'secondary' as const, icon: <Play size={16} />, onClick: handleDemarrer }] : []),
    ...(canEdit ? [{ id: 'edit', label: 'Modifier', variant: 'ghost' as const, icon: <Edit size={16} />, onClick: () => onEdit(interventionId) }] : []),
    { id: 'pdf', label: 'PDF', variant: 'ghost', icon: <Download size={16} />, onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'downloadPDF', interventionId } })); } },
  ];

  return (
    <>
      <BaseViewStandard<Intervention>
        title={intervention.reference}
        subtitle={intervention.titre}
        status={{ label: statutConfig.label, color: statutConfig.color as SemanticColor }}
        data={intervention}
        view="detail"
        tabs={tabs}
        infoBarItems={infoBarItems}
        sidebarSections={sidebarSections}
        headerActions={headerActions}
      />

      {/* Modal Terminer */}
      {showTerminer && (
        <div className="azals-modal-overlay">
          <div className="azals-modal">
            <h3>Terminer l'intervention</h3>
            <div className="azals-form-field">
              <label>Commentaire de cloture</label>
              <textarea
                className="azals-textarea"
                value={commentaire}
                onChange={(e) => setCommentaire(e.target.value)}
                rows={4}
                placeholder="Travaux effectues, remarques..."
              />
            </div>
            <div className="azals-modal__actions">
              <Button variant="ghost" onClick={() => setShowTerminer(false)}>Annuler</Button>
              <Button onClick={handleTerminer} isLoading={terminer.isPending}>Terminer</Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default InterventionDetailView;
