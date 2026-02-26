/**
 * AZALSCORE - Overlay de célébration
 * ====================================
 */

import React from 'react';
import { Trophy, Award, Star, Flame, Zap } from 'lucide-react';
import type { CelebrationType } from '../types';

interface CelebrationOverlayProps {
  type: CelebrationType;
  message: string;
  reward?: number;
  onClose: () => void;
}

const CELEBRATION_CONFIG = {
  levelup: {
    icon: Trophy,
    color: 'from-yellow-400 to-orange-500',
    title: 'Niveau Supérieur !',
  },
  badge: {
    icon: Award,
    color: 'from-purple-400 to-pink-500',
    title: 'Nouveau Badge !',
  },
  achievement: {
    icon: Star,
    color: 'from-blue-400 to-cyan-500',
    title: 'Succès Débloqué !',
  },
  streak: {
    icon: Flame,
    color: 'from-orange-400 to-red-500',
    title: 'Série Continue !',
  },
};

/**
 * Overlay animé de célébration
 */
export function CelebrationOverlay({
  type,
  message,
  reward,
  onClose,
}: CelebrationOverlayProps) {
  const config = CELEBRATION_CONFIG[type];
  const Icon = config.icon;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      {/* Confettis */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(40)].map((_, i) => (
          <div
            key={i}
            className="absolute w-3 h-3 animate-confetti rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 2}s`,
              backgroundColor: [
                '#FFD700',
                '#FF6B6B',
                '#4ECDC4',
                '#45B7D1',
                '#96CEB4',
                '#FFEAA7',
                '#DDA0DD',
              ][Math.floor(Math.random() * 7)],
            }}
          />
        ))}
      </div>

      {/* Contenu */}
      <div className="relative bg-white rounded-3xl p-8 max-w-sm w-full text-center animate-bounceIn shadow-2xl">
        {/* Icône */}
        <div
          className={`w-24 h-24 mx-auto rounded-full bg-gradient-to-br ${config.color} flex items-center justify-center shadow-lg mb-4`}
        >
          <Icon className="w-12 h-12 text-white" />
        </div>

        {/* Titre */}
        <h2
          className={`text-2xl font-black bg-gradient-to-r ${config.color} bg-clip-text text-transparent mb-2`}
        >
          {config.title}
        </h2>

        {/* Message */}
        <p className="text-gray-600 mb-4">{message}</p>

        {/* Récompense */}
        {reward && (
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-yellow-100 to-orange-100 px-4 py-2 rounded-full mb-4">
            <Zap className="w-5 h-5 text-yellow-600" />
            <span className="font-bold text-yellow-700">+{reward} XP</span>
          </div>
        )}

        {/* Bouton */}
        <button
          onClick={onClose}
          className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
        >
          Génial !
        </button>
      </div>
    </div>
  );
}

export default CelebrationOverlay;
