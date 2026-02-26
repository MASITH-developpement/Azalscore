/**
 * AZALSCORE - Logo Component
 * Réutilisable sur toutes les pages publiques
 */

import React from 'react';

const COLORS = {
  primary: '#2563eb',
};

export const AzalscoreLogo: React.FC<{ size?: number }> = ({ size = 40 }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" fill="none">
    <rect width="100" height="100" rx="20" fill={COLORS.primary} />
    <path
      d="M25 70L50 25L75 70H60L50 50L40 70H25Z"
      fill="white"
      stroke="white"
      strokeWidth="2"
      strokeLinejoin="round"
    />
    <circle cx="50" cy="65" r="8" fill="white" />
  </svg>
);

export const LogoWithText: React.FC<{ size?: number; className?: string }> = ({
  size = 32,
  className = ''
}) => (
  <div className={`flex items-center gap-2 ${className}`}>
    <AzalscoreLogo size={size} />
    <span className="font-bold text-xl text-gray-900">
      <span className="text-blue-600">AZAL</span>
      <span>SCORE</span>
    </span>
  </div>
);

export default AzalscoreLogo;
