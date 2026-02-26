/**
 * AZALSCORE - Collection de badges
 * =================================
 */

import React from 'react';
import { Lock } from 'lucide-react';
import type { Badge } from '../types';

interface BadgeCollectionProps {
  badges: Badge[];
  allBadges: Badge[];
}

const RARITY_COLORS = {
  common: 'from-gray-400 to-gray-500',
  rare: 'from-blue-400 to-blue-600',
  epic: 'from-purple-400 to-purple-600',
  legendary: 'from-yellow-400 to-orange-500',
};

const RARITY_BORDERS = {
  common: 'border-gray-300',
  rare: 'border-blue-400',
  epic: 'border-purple-400',
  legendary: 'border-yellow-400',
};

const RARITY_LABELS = {
  common: 'Commun',
  rare: 'Rare',
  epic: 'Épique',
  legendary: 'Légendaire',
};

/**
 * Affiche la collection de badges avec ceux débloqués et verrouillés
 */
export function BadgeCollection({ badges, allBadges }: BadgeCollectionProps) {
  const unlockedIds = new Set(badges.map(b => b.id));

  return (
    <div className="grid grid-cols-5 gap-3">
      {allBadges.map(badge => {
        const isUnlocked = unlockedIds.has(badge.id);
        const unlockedBadge = badges.find(b => b.id === badge.id);

        return (
          <BadgeItem
            key={badge.id}
            badge={badge}
            isUnlocked={isUnlocked}
            unlockedAt={unlockedBadge?.unlockedAt}
          />
        );
      })}
    </div>
  );
}

interface BadgeItemProps {
  badge: Badge;
  isUnlocked: boolean;
  unlockedAt?: string;
}

function BadgeItem({ badge, isUnlocked, unlockedAt }: BadgeItemProps) {
  return (
    <div
      className={`relative group cursor-pointer transition-all duration-300 ${
        isUnlocked ? 'hover:scale-110' : 'opacity-50 grayscale'
      }`}
      title={isUnlocked ? badge.description : `🔒 ${badge.description}`}
    >
      <div
        className={`w-14 h-14 rounded-xl flex items-center justify-center text-2xl border-2 ${
          isUnlocked
            ? `bg-gradient-to-br ${RARITY_COLORS[badge.rarity]} ${RARITY_BORDERS[badge.rarity]} shadow-lg`
            : 'bg-gray-200 border-gray-300'
        }`}
      >
        {isUnlocked ? (
          badge.icon
        ) : (
          <Lock className="w-5 h-5 text-gray-400" />
        )}
      </div>

      {/* Tooltip au survol */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
        <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-xl">
          <div className="font-bold">{badge.name}</div>
          <div className="text-gray-300">{badge.description}</div>
          <div className={`text-xs mt-1 ${getRarityTextColor(badge.rarity)}`}>
            {RARITY_LABELS[badge.rarity]}
          </div>
          {unlockedAt && (
            <div className="text-gray-400 text-xs mt-1">
              Obtenu le {new Date(unlockedAt).toLocaleDateString('fr-FR')}
            </div>
          )}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
        </div>
      </div>

      {/* Indicateur de rareté */}
      {isUnlocked && badge.rarity !== 'common' && (
        <div
          className={`absolute -top-1 -right-1 w-3 h-3 rounded-full bg-gradient-to-br ${RARITY_COLORS[badge.rarity]} border border-white`}
        />
      )}
    </div>
  );
}

function getRarityTextColor(rarity: Badge['rarity']): string {
  switch (rarity) {
    case 'legendary':
      return 'text-yellow-400';
    case 'epic':
      return 'text-purple-400';
    case 'rare':
      return 'text-blue-400';
    default:
      return 'text-gray-400';
  }
}

export default BadgeCollection;
