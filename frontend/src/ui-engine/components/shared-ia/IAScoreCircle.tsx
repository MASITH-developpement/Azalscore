/**
 * AZALSCORE - Shared IA Component - IAScoreCircle
 * ================================================
 * Composant partagé pour afficher un score circulaire IA.
 * Réutilisable dans tous les onglets IA de l'application.
 */

import React from 'react';

/**
 * Props du composant IAScoreCircle
 */
export interface IAScoreCircleProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  details?: string;
  color?: string;
  className?: string;
}

/**
 * Tailles du cercle
 */
const SIZE_CONFIG = {
  sm: { container: 'w-16 h-16', text: 'text-lg' },
  md: { container: 'w-24 h-24', text: 'text-2xl' },
  lg: { container: 'w-32 h-32', text: 'text-3xl' },
};

/**
 * IAScoreCircle - Composant d'affichage du score IA en cercle
 */
export const IAScoreCircle: React.FC<IAScoreCircleProps> = ({
  score,
  size = 'md',
  label,
  details,
  color = 'var(--azals-primary-500)',
  className = '',
}) => {
  const normalizedScore = Math.max(0, Math.min(100, score));
  const sizeConfig = SIZE_CONFIG[size];

  return (
    <div className={`azals-score-display ${className}`}>
      <div className={`azals-score-display__circle ${sizeConfig.container}`}>
        <svg viewBox="0 0 36 36" className="azals-score-display__svg">
          <path
            className="azals-score-display__bg"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke="var(--azals-border, #e5e7eb)"
            strokeWidth="3"
          />
          <path
            className="azals-score-display__fg"
            strokeDasharray={`${normalizedScore}, 100`}
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
        <span className={`azals-score-display__value ${sizeConfig.text}`}>
          {normalizedScore}%
        </span>
      </div>
      {(label || details) && (
        <div className="azals-score-display__details">
          {label && <p className="font-medium">{label}</p>}
          {details && <p className="text-muted text-sm">{details}</p>}
        </div>
      )}
    </div>
  );
};

/**
 * Composant pour afficher plusieurs scores côte à côte
 */
export interface ScoreData {
  label: string;
  score: number;
  color?: string;
}

export interface IAScoreGridProps {
  scores: ScoreData[];
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const IAScoreGrid: React.FC<IAScoreGridProps> = ({
  scores,
  size = 'sm',
  className = '',
}) => {
  return (
    <div className={`flex gap-4 ${className}`}>
      {scores.map((item, index) => (
        <IAScoreCircle
          key={index}
          score={item.score}
          size={size}
          label={item.label}
          color={item.color}
        />
      ))}
    </div>
  );
};

export default IAScoreCircle;
