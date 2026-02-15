/**
 * AZALSCORE - Planning View
 * Vue planning hebdomadaire avec drag & drop.
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import { unwrapApiResponse } from '@/types';
import { LoadingState, ErrorState } from '@ui/components/StateViews';
import {
  ChevronLeft, ChevronRight, Calendar, User, X, AlertCircle
} from 'lucide-react';
import {
  startOfWeek, endOfWeek, addWeeks, subWeeks, eachDayOfInterval,
  format, isSameDay, parseISO, isWeekend
} from 'date-fns';
import { fr } from 'date-fns/locale';

import type { Intervention } from '../types';
import { PRIORITE_CONFIG, CORPS_ETAT_CONFIG, STATUT_CONFIG } from '../types';
import type { CorpsEtat } from '../types';
import { Badge } from '@ui/simple';
import {
  usePlanifierIntervention,
  useModifierPlanification,
  useAnnulerPlanification,
  buildPlanificationData,
} from '../hooks/usePlanningActions';

// ============================================================================
// HOOKS (inline, same pattern as index.tsx)
// ============================================================================

const useInterventions = (filters?: { statut?: string }) => {
  return useQuery({
    queryKey: ['interventions', 'list', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.statut) params.append('statut', filters.statut);
      params.append('page_size', '200');
      const queryString = params.toString();
      const url = `/interventions${queryString ? `?${queryString}` : ''}`;
      const response = await api.get<{ items: Intervention[]; total: number }>(url);
      const data = unwrapApiResponse<{ items: Intervention[]; total: number }>(response);
      return data?.items || [];
    },
  });
};

const useIntervenants = () => {
  return useQuery({
    queryKey: ['intervenants'],
    queryFn: async () => {
      const response = await api.get<{ items: { id: string; first_name: string; last_name: string }[] }>('/hr/employees');
      const data = unwrapApiResponse<{ items: { id: string; first_name: string; last_name: string }[] }>(response);
      return data?.items || [];
    },
  });
};

// ============================================================================
// PLANNING CARD
// ============================================================================

interface PlanningCardProps {
  intervention: Intervention;
  onDragStart: (e: React.DragEvent, intervention: Intervention) => void;
  compact?: boolean;
}

const PlanningCard: React.FC<PlanningCardProps> = ({ intervention, onDragStart, compact }) => {
  const prioriteConfig = PRIORITE_CONFIG[intervention.priorite];
  const corpsConfig = intervention.corps_etat ? CORPS_ETAT_CONFIG[intervention.corps_etat as CorpsEtat] : null;

  return (
    <div
      className={`azals-planning-card ${compact ? 'azals-planning-card--compact' : ''}`}
      draggable
      onDragStart={(e) => {
        onDragStart(e, intervention);
        e.currentTarget.classList.add('azals-planning-card--dragging');
      }}
      onDragEnd={(e) => {
        e.currentTarget.classList.remove('azals-planning-card--dragging');
      }}
    >
      <div className="azals-planning-card__header">
        <code className="azals-planning-card__ref">{intervention.reference}</code>
        <Badge variant={prioriteConfig?.color || 'gray'}>
          {prioriteConfig?.label || intervention.priorite}
        </Badge>
        {intervention.statut === 'BLOQUEE' && (
          <Badge variant="red">Bloquée</Badge>
        )}
      </div>
      <div className="azals-planning-card__title">
        {intervention.titre || 'Sans titre'}
      </div>
      <div className="azals-planning-card__meta">
        {intervention.client_name && <span>{intervention.client_name}</span>}
        {corpsConfig && (
          <Badge variant={corpsConfig.color}>{corpsConfig.label}</Badge>
        )}
      </div>
      {compact && intervention.intervenant_name && (
        <div className="azals-planning-card__intervenant">
          <User size={10} /> {intervention.intervenant_name}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// DAY COLUMN
// ============================================================================

interface DayColumnProps {
  day: Date;
  interventions: Intervention[];
  intervenants: { id: string; first_name: string; last_name: string }[];
  isToday: boolean;
  isWeekendDay: boolean;
  onDragStart: (e: React.DragEvent, int: Intervention) => void;
  onDrop: (day: Date) => void;
}

const DayColumn: React.FC<DayColumnProps> = ({
  day, interventions, intervenants, isToday, isWeekendDay, onDragStart, onDrop,
}) => {
  const [dragOver, setDragOver] = useState(false);

  const grouped = interventions.reduce((acc, int) => {
    const key = int.intervenant_id || '_unassigned';
    if (!acc[key]) acc[key] = [];
    acc[key].push(int);
    return acc;
  }, {} as Record<string, Intervention[]>);

  return (
    <div
      className={[
        'azals-planning__day',
        isToday && 'azals-planning__day--today',
        isWeekendDay && 'azals-planning__day--weekend',
        dragOver && 'azals-planning__day--drag-over',
      ].filter(Boolean).join(' ')}
      onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setDragOver(false); onDrop(day); }}
    >
      <div className="azals-planning__day-header">
        <span className="azals-planning__day-name">{format(day, 'EEE', { locale: fr })}</span>
        <span className="azals-planning__day-number">{format(day, 'd')}</span>
        {interventions.length > 0 && (
          <span className="azals-planning__day-count">
            <Badge variant="blue">{interventions.length}</Badge>
          </span>
        )}
      </div>
      <div className="azals-planning__day-body">
        {Object.keys(grouped).length > 0 ? (
          Object.entries(grouped).map(([intervenantId, ints]) => {
            const intervenantInfo = intervenants.find(i => i.id === intervenantId);
            return (
              <div key={intervenantId} className="azals-planning__intervenant-group">
                <div className="azals-planning__intervenant-label">
                  <User size={10} />
                  {intervenantInfo
                    ? `${intervenantInfo.first_name} ${intervenantInfo.last_name}`
                    : 'Non assigne'}
                </div>
                {ints.map(int => (
                  <PlanningCard
                    key={int.id}
                    intervention={int}
                    onDragStart={onDragStart}
                    compact
                  />
                ))}
              </div>
            );
          })
        ) : (
          <div className="azals-planning__day-empty">-</div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// PLANNING VIEW (MAIN)
// ============================================================================

const PlanningView: React.FC = () => {
  // State
  const [currentWeekStart, setCurrentWeekStart] = useState<Date>(() =>
    startOfWeek(new Date(), { weekStartsOn: 1 })
  );
  const [selectedIntervenantId, setSelectedIntervenantId] = useState('');
  const [draggedIntervention, setDraggedIntervention] = useState<Intervention | null>(null);
  const [pendingDrop, setPendingDrop] = useState<{
    interventionId: string;
    targetDate: Date;
    dureePrevueMinutes?: number;
  } | null>(null);
  const [modalIntervenantId, setModalIntervenantId] = useState('');
  const [dropError, setDropError] = useState<string | null>(null);
  const [dragOverSidebar, setDragOverSidebar] = useState(false);

  // Data
  const { data: unplanned = [], isLoading: loadingUnplanned, error: errorUnplanned, refetch: refetchUnplanned } =
    useInterventions({ statut: 'A_PLANIFIER' });
  const { data: planned = [], isLoading: loadingPlanned, error: errorPlanned, refetch: refetchPlanned } =
    useInterventions({ statut: 'PLANIFIEE' });
  const { data: intervenants = [], isLoading: loadingIntervenants } = useIntervenants();

  // Mutations
  const planifier = usePlanifierIntervention();
  const modifier = useModifierPlanification();
  const annuler = useAnnulerPlanification();

  const isMutating = planifier.isPending || modifier.isPending || annuler.isPending;

  // Week computation
  const weekEnd = endOfWeek(currentWeekStart, { weekStartsOn: 1 });
  const weekDays = eachDayOfInterval({ start: currentWeekStart, end: weekEnd });
  const today = new Date();

  // PLANIFIEE interventions without dates → show in sidebar (need to be placed on a day)
  const plannedWithoutDates = planned.filter((int: Intervention) => !int.date_prevue_debut);

  // All sidebar interventions: A_PLANIFIER + PLANIFIEE without dates
  const sidebarInterventions = [...unplanned, ...plannedWithoutDates];

  // Filter planned interventions to current week
  const weekInterventions = planned.filter((int: Intervention) => {
    if (!int.date_prevue_debut) return false;
    const d = parseISO(int.date_prevue_debut);
    return d >= currentWeekStart && d <= weekEnd;
  });

  // Further filter by intervenant
  const filteredWeekInterventions = selectedIntervenantId
    ? weekInterventions.filter((int: Intervention) => int.intervenant_id === selectedIntervenantId)
    : weekInterventions;

  // Auto-dismiss error toast
  useEffect(() => {
    if (dropError) {
      const timer = setTimeout(() => setDropError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [dropError]);

  // Drag handlers
  const handleDragStart = useCallback((e: React.DragEvent, intervention: Intervention) => {
    e.dataTransfer.setData('text/plain', intervention.id);
    e.dataTransfer.effectAllowed = 'move';
    setDraggedIntervention(intervention);
  }, []);

  const handleDayDrop = useCallback((targetDay: Date) => {
    if (!draggedIntervention) return;
    const intervention = draggedIntervention;
    setDraggedIntervention(null);

    if (intervention.statut === 'A_PLANIFIER') {
      // Scenario A: planifier
      const intervenantId = selectedIntervenantId;
      if (!intervenantId) {
        setPendingDrop({
          interventionId: intervention.id,
          targetDate: targetDay,
          dureePrevueMinutes: intervention.duree_prevue_minutes,
        });
        return;
      }
      const data = buildPlanificationData(targetDay, intervenantId, intervention.duree_prevue_minutes);
      planifier.mutate({ id: intervention.id, data }, {
        onError: (err: any) => setDropError(err?.response?.data?.detail || err?.message || 'Erreur planification'),
      });
    } else if (intervention.statut === 'PLANIFIEE') {
      // Scenario B: replanifier (or place for the first time if no dates)
      if (intervention.date_prevue_debut && isSameDay(parseISO(intervention.date_prevue_debut), targetDay)) {
        return; // no-op, meme jour
      }
      const intervenantId = intervention.intervenant_id || selectedIntervenantId;
      if (!intervenantId) {
        // Open modal to select intervenant
        setPendingDrop({
          interventionId: intervention.id,
          targetDate: targetDay,
          dureePrevueMinutes: intervention.duree_prevue_minutes,
        });
        return;
      }
      const data = buildPlanificationData(targetDay, intervenantId, intervention.duree_prevue_minutes);
      modifier.mutate({ id: intervention.id, data }, {
        onError: (err: any) => setDropError(err?.response?.data?.detail || err?.message || 'Erreur modification'),
      });
    }
  }, [draggedIntervention, selectedIntervenantId, planifier, modifier]);

  const handleSidebarDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOverSidebar(false);
    if (!draggedIntervention) return;
    const intervention = draggedIntervention;
    setDraggedIntervention(null);

    if (intervention.statut === 'PLANIFIEE') {
      // Scenario C: deplanifier
      annuler.mutate(intervention.id, {
        onError: (err: any) => setDropError(err?.response?.data?.detail || err?.message || 'Erreur annulation'),
      });
    }
  }, [draggedIntervention, annuler]);

  // Modal confirm
  const handleModalConfirm = () => {
    if (!pendingDrop || !modalIntervenantId) return;
    const data = buildPlanificationData(
      pendingDrop.targetDate,
      modalIntervenantId,
      pendingDrop.dureePrevueMinutes
    );
    // Find the intervention to determine which endpoint to use
    const intervention = [...unplanned, ...planned].find(i => i.id === pendingDrop.interventionId);
    const mutationFn = intervention?.statut === 'PLANIFIEE' ? modifier : planifier;
    mutationFn.mutate({ id: pendingDrop.interventionId, data }, {
      onError: (err: any) => setDropError(err?.response?.data?.detail || err?.message || 'Erreur planification'),
    });
    setPendingDrop(null);
    setModalIntervenantId('');
  };

  const handleModalCancel = () => {
    setPendingDrop(null);
    setModalIntervenantId('');
  };

  // Loading / Error
  const isLoading = loadingUnplanned || loadingPlanned || loadingIntervenants;
  const error = errorUnplanned || errorPlanned;

  if (isLoading) {
    return <LoadingState onRetry={() => { refetchUnplanned(); refetchPlanned(); }} message="Chargement du planning..." />;
  }

  if (error) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : 'Erreur lors du chargement'}
        onRetry={() => { refetchUnplanned(); refetchPlanned(); }}
      />
    );
  }

  return (
    <div className="azals-planning">
      {/* Toolbar */}
      <div className="azals-planning__toolbar">
        <div className="azals-planning__nav">
          <button
            className="azals-btn azals-btn--secondary azals-btn--sm"
            onClick={() => setCurrentWeekStart(s => subWeeks(s, 1))}
          >
            <ChevronLeft size={14} />
          </button>
          <button
            className="azals-btn azals-btn--secondary azals-btn--sm"
            onClick={() => setCurrentWeekStart(startOfWeek(new Date(), { weekStartsOn: 1 }))}
          >
            Aujourd'hui
          </button>
          <button
            className="azals-btn azals-btn--secondary azals-btn--sm"
            onClick={() => setCurrentWeekStart(s => addWeeks(s, 1))}
          >
            <ChevronRight size={14} />
          </button>
        </div>

        <span className="azals-planning__week-label">
          <Calendar size={16} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: 6 }} />
          {format(currentWeekStart, 'd MMM', { locale: fr })} – {format(weekEnd, 'd MMM yyyy', { locale: fr })}
        </span>

        <select
          className="azals-select"
          style={{ width: 220 }}
          value={selectedIntervenantId}
          onChange={(e) => setSelectedIntervenantId(e.target.value)}
        >
          <option value="">Tous les intervenants</option>
          {intervenants.map((i: any) => (
            <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>
          ))}
        </select>
      </div>

      {/* Main layout */}
      <div className={`azals-planning__layout ${isMutating ? 'azals-planning__loading-overlay' : ''}`}>
        {/* Sidebar */}
        <div
          className={`azals-planning__sidebar ${dragOverSidebar ? 'azals-planning__sidebar--drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; setDragOverSidebar(true); }}
          onDragLeave={() => setDragOverSidebar(false)}
          onDrop={handleSidebarDrop}
        >
          <div className="azals-planning__sidebar-title">
            À planifier
            <Badge variant="gray">{sidebarInterventions.length}</Badge>
          </div>
          {sidebarInterventions.length > 0 ? (
            <div className="azals-planning__sidebar-list">
              {sidebarInterventions.map((int: Intervention) => (
                <PlanningCard
                  key={int.id}
                  intervention={int}
                  onDragStart={handleDragStart}
                />
              ))}
            </div>
          ) : (
            <div className="azals-planning__sidebar-empty">
              Aucune intervention a planifier
            </div>
          )}
        </div>

        {/* Week grid */}
        <div className="azals-planning__grid">
          {weekDays.map(day => (
            <DayColumn
              key={day.toISOString()}
              day={day}
              interventions={filteredWeekInterventions.filter((int: Intervention) =>
                int.date_prevue_debut && isSameDay(parseISO(int.date_prevue_debut), day)
              )}
              intervenants={intervenants}
              isToday={isSameDay(day, today)}
              isWeekendDay={isWeekend(day)}
              onDragStart={handleDragStart}
              onDrop={handleDayDrop}
            />
          ))}
        </div>
      </div>

      {/* Error toast */}
      {dropError && (
        <div className="azals-planning__toast">
          <AlertCircle size={16} />
          <span>{dropError}</span>
          <button
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', marginLeft: 8 }}
            onClick={() => setDropError(null)}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Modal selection intervenant */}
      {pendingDrop && (
        <div className="azals-planning__modal-overlay" onClick={handleModalCancel}>
          <div className="azals-planning__modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="azals-planning__modal-title">
              Selectionner un intervenant
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--azals-text-secondary)', marginBottom: '1rem' }}>
              Planification pour le {format(pendingDrop.targetDate, 'd MMMM yyyy', { locale: fr })}
            </p>
            <select
              className="azals-select"
              value={modalIntervenantId}
              onChange={(e) => setModalIntervenantId(e.target.value)}
            >
              <option value="">Choisir...</option>
              {intervenants.map((i: any) => (
                <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>
              ))}
            </select>
            <div className="azals-planning__modal-actions">
              <button className="azals-btn azals-btn--secondary" onClick={handleModalCancel}>
                Annuler
              </button>
              <button
                className="azals-btn azals-btn--primary"
                disabled={!modalIntervenantId || planifier.isPending}
                onClick={handleModalConfirm}
              >
                Planifier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export { PlanningView };
