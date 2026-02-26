/**
 * AZALSCORE - Notification de niveau disponible
 * ===============================================
 */

import React from 'react';
import { Rocket, GraduationCap, X } from 'lucide-react';
import { LEVELS } from '../constants';

interface LevelUpNotificationProps {
  pendingLevel: number;
  onStartExam: () => void;
  onDismiss: () => void;
}

/**
 * Notification indiquant qu'un examen de niveau est disponible
 */
export function LevelUpNotification({
  pendingLevel,
  onStartExam,
  onDismiss,
}: LevelUpNotificationProps) {
  const levelData = LEVELS.find(l => l.level === pendingLevel);

  return (
    <div className="fixed bottom-4 right-4 max-w-sm animate-slideUp z-40">
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-5 text-white shadow-2xl relative">
        {/* Bouton fermer */}
        <button
          onClick={onDismiss}
          className="absolute top-2 right-2 p-1 hover:bg-white/20 rounded-full transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Contenu */}
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center">
            <Rocket className="w-8 h-8" />
          </div>
          <div className="flex-1">
            <h4 className="font-bold text-lg">Niveau {pendingLevel} disponible !</h4>
            <p className="text-white/80 text-sm">
              Vous avez assez d'XP pour devenir {levelData?.title}
            </p>
          </div>
        </div>

        {/* Bouton action */}
        <button
          onClick={onStartExam}
          className="mt-4 w-full py-2.5 bg-white text-purple-600 rounded-xl font-medium flex items-center justify-center gap-2 hover:bg-purple-50 transition-colors"
        >
          <GraduationCap className="w-5 h-5" />
          Passer l'examen
        </button>
      </div>
    </div>
  );
}

export default LevelUpNotification;
