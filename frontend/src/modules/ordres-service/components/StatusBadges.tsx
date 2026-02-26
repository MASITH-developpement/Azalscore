/**
 * AZALSCORE Module - Ordres de Service - Status Badges
 * Badges de statut et priorite
 */

import React from 'react';
import { Calendar, Clock, Play, CheckCircle2, X } from 'lucide-react';
import { STATUT_CONFIG, PRIORITE_CONFIG } from '../types';
import type { InterventionStatut, InterventionPriorite } from '../types';

export const StatutBadge: React.FC<{ statut: InterventionStatut }> = ({ statut }) => {
  const config = STATUT_CONFIG[statut];
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {statut === 'A_PLANIFIER' && <Calendar size={14} />}
      {statut === 'PLANIFIEE' && <Clock size={14} />}
      {statut === 'EN_COURS' && <Play size={14} />}
      {statut === 'TERMINEE' && <CheckCircle2 size={14} />}
      {statut === 'ANNULEE' && <X size={14} />}
      <span className="ml-1">{config.label}</span>
    </span>
  );
};

export const PrioriteBadge: React.FC<{ priorite: InterventionPriorite }> = ({ priorite }) => {
  const config = PRIORITE_CONFIG[priorite];
  return (
    <span className={`azals-badge azals-badge--${config.color} azals-badge--outline`}>
      {config.label}
    </span>
  );
};
