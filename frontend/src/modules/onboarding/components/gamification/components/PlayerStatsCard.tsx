/**
 * AZALSCORE - Carte des statistiques joueur
 * ==========================================
 */

import React from 'react';
import { Trophy, Flame, Star, TrendingUp } from 'lucide-react';
import type { UserGameProfile } from '../types';
import { XPProgressBar } from './XPProgressBar';

interface PlayerStatsCardProps {
  profile: UserGameProfile;
}

/**
 * Carte affichant les statistiques du joueur
 */
export function PlayerStatsCard({ profile }: PlayerStatsCardProps) {
  return (
    <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-6 text-white shadow-xl">
      {/* Header avec avatar et niveau */}
      <div className="flex items-center gap-4 mb-4">
        <div className="relative">
          <div className="w-16 h-16 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-3xl">
            {profile.avatar}
          </div>
          <div className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-yellow-400 flex items-center justify-center text-sm font-bold text-yellow-900 shadow-lg">
            {profile.level}
          </div>
        </div>
        <div>
          <h2 className="text-xl font-bold">{profile.displayName}</h2>
          <p className="text-white/80 text-sm flex items-center gap-1">
            <Trophy className="w-4 h-4" />
            {profile.title}
          </p>
        </div>
      </div>

      {/* Barre XP */}
      <div className="bg-white/10 backdrop-blur rounded-xl p-3 mb-4">
        <XPProgressBar
          xp={profile.xp}
          xpToNext={profile.xpToNextLevel}
          level={profile.level}
        />
      </div>

      {/* Stats rapides */}
      <div className="grid grid-cols-4 gap-3">
        <StatItem
          icon={<Star className="w-5 h-5 text-yellow-300" />}
          value={profile.totalPoints}
          label="Points"
        />
        <StatItem
          icon={<Flame className="w-5 h-5 text-orange-300" />}
          value={profile.streak}
          label="Série"
        />
        <StatItem
          icon={<Trophy className="w-5 h-5 text-amber-300" />}
          value={profile.badges.length}
          label="Badges"
        />
        <StatItem
          icon={<TrendingUp className="w-5 h-5 text-green-300" />}
          value={`#${profile.rank}`}
          label="Rang"
        />
      </div>
    </div>
  );
}

interface StatItemProps {
  icon: React.ReactNode;
  value: string | number;
  label: string;
}

function StatItem({ icon, value, label }: StatItemProps) {
  return (
    <div className="text-center">
      <div className="flex justify-center mb-1">{icon}</div>
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs text-white/70">{label}</div>
    </div>
  );
}

export default PlayerStatsCard;
