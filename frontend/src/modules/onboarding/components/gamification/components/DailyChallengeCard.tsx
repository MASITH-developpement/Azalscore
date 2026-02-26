/**
 * AZALSCORE - Carte de défi quotidien
 * =====================================
 */

import React from 'react';
import { Target, CheckCircle, Zap, Clock } from 'lucide-react';
import type { Challenge } from '../types';

interface DailyChallengeCardProps {
  challenge: Challenge;
  onComplete?: () => void;
}

const DIFFICULTY_COLORS = {
  easy: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-200' },
  medium: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-200' },
  hard: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-200' },
};

const DIFFICULTY_LABELS = {
  easy: 'Facile',
  medium: 'Moyen',
  hard: 'Difficile',
};

/**
 * Carte affichant un défi quotidien avec ses tâches
 */
export function DailyChallengeCard({ challenge, onComplete }: DailyChallengeCardProps) {
  const completedTasks = challenge.tasks.filter(t => t.completed).length;
  const totalTasks = challenge.tasks.length;
  const progress = (completedTasks / totalTasks) * 100;
  const diffColors = DIFFICULTY_COLORS[challenge.difficulty];

  const isCompleted = challenge.completed || completedTasks === totalTasks;

  return (
    <div
      className={`bg-white rounded-xl border-2 p-4 transition-all ${
        isCompleted ? 'border-green-300 bg-green-50' : 'border-gray-200 hover:border-purple-300'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              isCompleted ? 'bg-green-500' : 'bg-purple-100'
            }`}
          >
            {isCompleted ? (
              <CheckCircle className="w-5 h-5 text-white" />
            ) : (
              <Target className="w-5 h-5 text-purple-600" />
            )}
          </div>
          <div>
            <h4 className="font-semibold text-gray-900">{challenge.title}</h4>
            <p className="text-xs text-gray-500">{challenge.description}</p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${diffColors.bg} ${diffColors.text}`}
          >
            {DIFFICULTY_LABELS[challenge.difficulty]}
          </span>
          {challenge.timeLimit && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {Math.floor(challenge.timeLimit / 60)} min
            </span>
          )}
        </div>
      </div>

      {/* Tâches */}
      <div className="space-y-2 mb-3">
        {challenge.tasks.map(task => (
          <div
            key={task.id}
            className={`flex items-center gap-2 text-sm ${
              task.completed ? 'text-green-700' : 'text-gray-600'
            }`}
          >
            <div
              className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                task.completed
                  ? 'bg-green-500 border-green-500'
                  : 'border-gray-300'
              }`}
            >
              {task.completed && <CheckCircle className="w-3 h-3 text-white" />}
            </div>
            <span className={task.completed ? 'line-through' : ''}>
              {task.description}
            </span>
          </div>
        ))}
      </div>

      {/* Barre de progression */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs mb-1">
          <span className="text-gray-500">
            {completedTasks}/{totalTasks} tâches
          </span>
          <span className="font-medium text-purple-600">{Math.round(progress)}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isCompleted ? 'bg-green-500' : 'bg-purple-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Récompense */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-sm">
          <Zap className="w-4 h-4 text-yellow-500" />
          <span className="font-bold text-yellow-600">+{challenge.xpReward} XP</span>
        </div>

        {!isCompleted && onComplete && (
          <button
            onClick={onComplete}
            className="px-3 py-1.5 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors"
          >
            Valider
          </button>
        )}

        {isCompleted && (
          <span className="text-sm font-medium text-green-600 flex items-center gap-1">
            <CheckCircle className="w-4 h-4" />
            Terminé
          </span>
        )}
      </div>
    </div>
  );
}

export default DailyChallengeCard;
