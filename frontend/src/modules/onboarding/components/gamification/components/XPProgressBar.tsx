/**
 * AZALSCORE - Barre de progression XP
 * ====================================
 */

import React from 'react';
import { LEVELS } from '../constants';

interface XPProgressBarProps {
  xp: number;
  xpToNext: number;
  level: number;
}

/**
 * Barre de progression XP animée
 */
export function XPProgressBar({ xp, xpToNext, level }: XPProgressBarProps) {
  const percentage = Math.min((xp / xpToNext) * 100, 100);
  const levelData = LEVELS[level - 1];

  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded-full bg-gradient-to-br from-${levelData?.color || 'blue'}-400 to-${levelData?.color || 'blue'}-600 flex items-center justify-center text-white font-bold text-sm shadow-lg`}
          >
            {level}
          </div>
          <span className="text-sm font-medium text-gray-700">
            {levelData?.title}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {xp} / {xpToNext} XP
        </span>
      </div>
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full transition-all duration-500 ease-out relative"
          style={{ width: `${percentage}%` }}
        >
          <div className="absolute inset-0 bg-white/20 animate-pulse" />
        </div>
      </div>
    </div>
  );
}

export default XPProgressBar;
