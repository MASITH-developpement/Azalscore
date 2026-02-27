/**
 * AZALSCORE Module - INTERVENTIONS - Detail View
 * Vue détaillée d'une intervention avec BaseViewStandard
 */

import React, { useState } from 'react';
import {
  ClipboardList, Calendar, Wrench, CheckCircle, Clock,
  User, FileText, History, Sparkles, Package, Euro, AlertTriangle, Play, X,
  Lock, Unlock, CheckSquare
} from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { BaseViewStandard } from '@ui/standards';
import type { Intervenant, ApiMutationError } from '@/types';
import { formatDate, formatDuration, formatCurrency } from '@/utils/formatters';
import {
  useIntervenants,
} from '../api';
import { usePlanifierIntervention } from '../hooks/usePlanningActions';
import {
  useValiderIntervention, useDemarrerIntervention, useTerminerIntervention,
  useBloquerIntervention, useDebloquerIntervention, useAnnulerIntervention
} from '../hooks/useWorkflowActions';
import {
  STATUT_CONFIG, PRIORITE_CONFIG, TYPE_CONFIG,
  isLate, canValidate, canUnblock
} from '../types';
import type { Intervention } from '../types';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition } from '@ui/standards';
import {
  InterventionInfoTab,
  InterventionLinesTab,
  InterventionFinancialTab,
  InterventionDocsTab,
  InterventionHistoryTab,
  InterventionIATab,
} from './index';

export interface InterventionDetailViewProps {
  intervention: Intervention;
  onClose: () => void;
}

export const InterventionDetailView: React.FC<InterventionDetailViewProps> = ({ intervention, onClose }) => {
  // Workflow hooks
  const valider = useValiderIntervention();
  const planifier = usePlanifierIntervention();
  const demarrer = useDemarrerIntervention();
  const terminer = useTerminerIntervention();
  const bloquer = useBloquerIntervention();
  const debloquer = useDebloquerIntervention();
  const annuler = useAnnulerIntervention();
  const { data: intervenants = [] } = useIntervenants();

  // Workflow modals state
  const [showPlanifierModal, setShowPlanifierModal] = useState(false);
  const [showBloquerModal, setShowBloquerModal] = useState(false);
  const [showConfirmAnnuler, setShowConfirmAnnuler] = useState(false);
  const [motifBlocage, setMotifBlocage] = useState('');
  const [planDate, setPlanDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [planHeureDebut, setPlanHeureDebut] = useState('08:00');
  const [planHeureFin, setPlanHeureFin] = useState('17:00');
  const [planIntervenantId, setPlanIntervenantId] = useState('');
  const [workflowError, setWorkflowError] = useState<string | null>(null);

  const statutConfig = STATUT_CONFIG[intervention.statut];
  const prioriteConfig = PRIORITE_CONFIG[intervention.priorite];
  const typeConfig = TYPE_CONFIG[intervention.type_intervention];

  // Tabs definition
  const tabs: TabDefinition<Intervention>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <ClipboardList size={16} />,
      component: InterventionInfoTab
    },
    {
      id: 'lignes',
      label: 'Détails',
      icon: <Package size={16} />,
      component: InterventionLinesTab
    },
    {
      id: 'financier',
      label: 'Financier',
      icon: <Euro size={16} />,
      component: InterventionFinancialTab
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={16} />,
      badge: intervention.rapport ? 1 : 0,
      component: InterventionDocsTab
    },
    {
      id: 'historique',
      label: 'Historique',
      icon: <History size={16} />,
      component: InterventionHistoryTab
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: InterventionIATab
    }
  ];

  // InfoBar items
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'client',
      label: 'Client',
      value: intervention.client_name || '-',
      icon: <User size={14} />
    },
    {
      id: 'type',
      label: 'Type',
      value: typeConfig?.label || intervention.type_intervention,
      icon: <Wrench size={14} />
    },
    {
      id: 'date_prevue',
      label: 'Date prévue',
      value: intervention.date_prevue ? formatDate(intervention.date_prevue) : 'Non planifiée',
      icon: <Calendar size={14} />,
      valueColor: isLate(intervention) ? 'red' : undefined
    },
    {
      id: 'duree',
      label: 'Durée',
      value: formatDuration(intervention.duree_reelle_minutes || intervention.duree_prevue_minutes),
      icon: <Clock size={14} />
    }
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'resume',
      title: 'Résumé',
      items: [
        { id: 'reference', label: 'Référence', value: intervention.reference },
        { id: 'priorite', label: 'Priorité', value: prioriteConfig?.label || intervention.priorite },
        { id: 'intervenant', label: 'Intervenant', value: intervention.intervenant_name || 'Non assigné' },
        { id: 'created_at', label: 'Créé le', value: formatDate(intervention.created_at) }
      ]
    },
    {
      id: 'localisation',
      title: 'Localisation',
      items: [
        { id: 'adresse', label: 'Adresse', value: intervention.adresse_intervention || intervention.adresse_ligne1 || '-' },
        { id: 'ville', label: 'Ville', value: intervention.ville || '-' },
        { id: 'contact', label: 'Contact', value: intervention.contact_sur_place || '-' }
      ]
    },
    {
      id: 'facturation',
      title: 'Facturation',
      items: [
        { id: 'facturable', label: 'Facturable', value: intervention.facturable !== false ? 'Oui' : 'Non' },
        { id: 'montant_ht', label: 'Montant HT', value: formatCurrency(intervention.montant_ht || 0) },
        { id: 'facture', label: 'Facture', value: intervention.facture_reference || '-' }
      ]
    }
  ];

  // Header actions
  const headerActions: ActionDefinition[] = [
    {
      id: 'close',
      label: 'Fermer',
      variant: 'secondary' as const,
      onClick: onClose
    }
  ];

  // Footer actions based on status (state machine 7 états)
  const primaryActions: ActionDefinition[] = [];

  if (canValidate(intervention)) {
    primaryActions.push({
      id: 'valider',
      label: 'Valider',
      icon: <CheckSquare size={16} />,
      variant: 'primary' as const,
      onClick: () => {
        valider.mutate(intervention.id, {
          onSuccess: () => onClose(),
          onError: (err: ApiMutationError) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur validation'),
        });
      }
    });
  }

  if (intervention.statut === 'A_PLANIFIER') {
    primaryActions.push({
      id: 'planifier',
      label: 'Planifier',
      icon: <Calendar size={16} />,
      variant: 'primary' as const,
      onClick: () => setShowPlanifierModal(true)
    });
  }

  if (intervention.statut === 'PLANIFIEE') {
    primaryActions.push({
      id: 'demarrer',
      label: 'Démarrer',
      icon: <Play size={16} />,
      variant: 'warning' as const,
      onClick: () => {
        demarrer.mutate(intervention.id, {
          onSuccess: () => onClose(),
          onError: (err: ApiMutationError) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur'),
        });
      }
    });
  }

  if (intervention.statut === 'EN_COURS') {
    primaryActions.push({
      id: 'terminer',
      label: 'Terminer',
      icon: <CheckCircle size={16} />,
      variant: 'success' as const,
      onClick: () => {
        terminer.mutate(intervention.id, {
          onSuccess: () => onClose(),
          onError: (err: ApiMutationError) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur'),
        });
      }
    });
    primaryActions.push({
      id: 'bloquer',
      label: 'Bloquer',
      icon: <Lock size={16} />,
      variant: 'danger' as const,
      onClick: () => setShowBloquerModal(true)
    });
  }

  if (canUnblock(intervention)) {
    primaryActions.push({
      id: 'debloquer',
      label: 'Débloquer',
      icon: <Unlock size={16} />,
      variant: 'warning' as const,
      onClick: () => {
        debloquer.mutate(intervention.id, {
          onSuccess: () => onClose(),
          onError: (err: ApiMutationError) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur déblocage'),
        });
      }
    });
  }

  if (!['TERMINEE', 'ANNULEE', 'DRAFT'].includes(intervention.statut)) {
    primaryActions.push({
      id: 'annuler',
      label: 'Annuler',
      icon: <X size={16} />,
      variant: 'danger' as const,
      onClick: () => setShowConfirmAnnuler(true)
    });
  }

  const handlePlanifierSubmit = () => {
    if (!planIntervenantId) {
      setWorkflowError('Veuillez sélectionner un intervenant');
      return;
    }
    const debut = new Date(`${planDate}T${planHeureDebut}:00`);
    const fin = new Date(`${planDate}T${planHeureFin}:00`);
    planifier.mutate({
      id: intervention.id,
      data: {
        date_prevue_debut: debut.toISOString(),
        date_prevue_fin: fin.toISOString(),
        intervenant_id: planIntervenantId,
      }
    }, {
      onSuccess: () => { setShowPlanifierModal(false); onClose(); },
      onError: (err: ApiMutationError) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur planification'),
    });
  };

  const handleAnnulerConfirm = () => {
    annuler.mutate(intervention.id, {
      onSuccess: () => { setShowConfirmAnnuler(false); onClose(); },
      onError: (err: ApiMutationError) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur annulation'),
    });
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="" size="xl">
      <BaseViewStandard<Intervention>
        title={intervention.titre}
        subtitle={`Intervention ${intervention.reference}`}
        status={{
          label: statutConfig?.label || intervention.statut,
          color: (statutConfig?.color || 'gray') as 'gray' | 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'yellow' | 'cyan',
          icon: statutConfig?.icon
        }}
        data={intervention}
        view="detail"
        tabs={tabs}
        infoBarItems={infoBarItems}
        sidebarSections={sidebarSections}
        headerActions={headerActions}
        primaryActions={primaryActions}
      />

      {/* Workflow error toast */}
      {workflowError && (
        <div className="azals-planning__toast">
          <AlertTriangle size={16} />
          <span>{workflowError}</span>
          <button className="azals-btn azals-btn--ghost azals-btn--icon-only" onClick={() => setWorkflowError(null)}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Modal Planifier */}
      {showPlanifierModal && (
        <Modal isOpen onClose={() => setShowPlanifierModal(false)} title="Planifier l'intervention">
          <div className="azals-modal__body">
            <p className="text-muted mb-4">
              {intervention.reference} — {intervention.titre || 'Sans titre'}
            </p>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="plan-date">Date <span className="azals-field__required">*</span></label>
              <input id="plan-date" className="azals-input" type="date" value={planDate} onChange={e => setPlanDate(e.target.value)} />
            </div>
            <div className="azals-grid azals-grid--cols-2">
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="plan-heure-debut">Heure début</label>
                <input id="plan-heure-debut" className="azals-input" type="time" value={planHeureDebut} onChange={e => setPlanHeureDebut(e.target.value)} />
              </div>
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="plan-heure-fin">Heure fin</label>
                <input id="plan-heure-fin" className="azals-input" type="time" value={planHeureFin} onChange={e => setPlanHeureFin(e.target.value)} />
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="plan-intervenant">Intervenant <span className="azals-field__required">*</span></label>
              <select id="plan-intervenant" className="azals-select" value={planIntervenantId} onChange={e => setPlanIntervenantId(e.target.value)}>
                <option value="">Choisir un intervenant...</option>
                {intervenants.map((i: Intervenant) => (
                  <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={() => setShowPlanifierModal(false)}>Annuler</Button>
            <Button onClick={handlePlanifierSubmit} disabled={planifier.isPending}>
              {planifier.isPending ? 'Planification...' : 'Planifier'}
            </Button>
          </div>
        </Modal>
      )}

      {/* Modal Bloquer */}
      {showBloquerModal && (
        <Modal isOpen onClose={() => { setShowBloquerModal(false); setMotifBlocage(''); }} title="Bloquer l'intervention">
          <div className="azals-modal__body">
            <p className="text-muted mb-4">
              {intervention.reference} — {intervention.titre || 'Sans titre'}
            </p>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="blocage-motif">Motif du blocage <span className="azals-field__required">*</span></label>
              <textarea
                id="blocage-motif"
                className="azals-input"
                rows={3}
                value={motifBlocage}
                onChange={e => setMotifBlocage(e.target.value)}
                placeholder="Décrivez le motif du blocage (min. 5 caractères)..."
              />
              {motifBlocage.length > 0 && motifBlocage.length < 5 && (
                <p className="text-danger text-sm mt-1">Le motif doit contenir au moins 5 caractères.</p>
              )}
            </div>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={() => { setShowBloquerModal(false); setMotifBlocage(''); }}>Annuler</Button>
            <Button
              variant="danger"
              onClick={() => {
                bloquer.mutate({ id: intervention.id, motif: motifBlocage }, {
                  onSuccess: () => { setShowBloquerModal(false); setMotifBlocage(''); onClose(); },
                  onError: (err: ApiMutationError) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur blocage'),
                });
              }}
              disabled={motifBlocage.length < 5 || bloquer.isPending}
            >
              {bloquer.isPending ? 'Blocage...' : 'Confirmer le blocage'}
            </Button>
          </div>
        </Modal>
      )}

      {/* Modal Confirmer annulation */}
      {showConfirmAnnuler && (
        <Modal isOpen onClose={() => setShowConfirmAnnuler(false)} title="Confirmer l'annulation">
          <div className="azals-modal__body">
            <p>
              Êtes-vous sûr de vouloir annuler l'intervention <strong>{intervention.reference}</strong> ?
            </p>
            <p className="text-muted mt-2">
              Cette action est irréversible.
            </p>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={() => setShowConfirmAnnuler(false)}>Non, garder</Button>
            <Button variant="danger" onClick={handleAnnulerConfirm} disabled={annuler.isPending}>
              {annuler.isPending ? 'Annulation...' : 'Oui, annuler'}
            </Button>
          </div>
        </Modal>
      )}
    </Modal>
  );
};

export default InterventionDetailView;
