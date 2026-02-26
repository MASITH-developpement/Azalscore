/**
 * AZALSCORE - Classement des joueurs
 * ====================================
 */

import React from 'react';
import { Trophy, Medal, Award, TrendingUp } from 'lucide-react';
import type { LeaderboardEntry } from '../types';

interface LeaderboardProps {
  entries: LeaderboardEntry[];
  title?: string;
}

/**
 * Affiche le classement des meilleurs joueurs
 */
export function Leaderboard({ entries, title = 'Classement' }: LeaderboardProps) {
  // Trier par points décroissants
  const sortedEntries = [...entries].sort((a, b) => b.points - a.points);

  return (
    <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-4 py-3 flex items-center gap-2">
        <Trophy className="w-5 h-5 text-white" />
        <h3 className="font-bold text-white">{title}</h3>
      </div>

      <div className="divide-y">
        {sortedEntries.map((entry, index) => (
          <LeaderboardRow
            key={entry.userId}
            entry={entry}
            position={index + 1}
          />
        ))}
      </div>
    </div>
  );
}

interface LeaderboardRowProps {
  entry: LeaderboardEntry;
  position: number;
}

function LeaderboardRow({ entry, position }: LeaderboardRowProps) {
  const isCurrentUser = entry.isCurrentUser;

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 transition-colors ${
        isCurrentUser
          ? 'bg-indigo-50 border-l-4 border-indigo-500'
          : 'hover:bg-gray-50'
      }`}
    >
      {/* Position */}
      <div className="w-8 flex justify-center">
        {position === 1 ? (
          <Trophy className="w-6 h-6 text-yellow-500" />
        ) : position === 2 ? (
          <Medal className="w-6 h-6 text-gray-400" />
        ) : position === 3 ? (
          <Award className="w-6 h-6 text-amber-600" />
        ) : (
          <span className="text-gray-500 font-medium">{position}</span>
        )}
      </div>

      {/* Avatar */}
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-xl">
        {entry.avatar}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className={`font-medium truncate ${
              isCurrentUser ? 'text-indigo-700' : 'text-gray-900'
            }`}
          >
            {entry.displayName}
            {isCurrentUser && (
              <span className="text-xs text-indigo-500 ml-1">(vous)</span>
            )}
          </span>
        </div>
        <div className="text-xs text-gray-500">Niveau {entry.level}</div>
      </div>

      {/* Points */}
      <div className="text-right">
        <div className="font-bold text-gray-900 flex items-center gap-1">
          {entry.points.toLocaleString('fr-FR')}
          <TrendingUp className="w-3 h-3 text-green-500" />
        </div>
        <div className="text-xs text-gray-500">points</div>
      </div>
    </div>
  );
}

export default Leaderboard;
