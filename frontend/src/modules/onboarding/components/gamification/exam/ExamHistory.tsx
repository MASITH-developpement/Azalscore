/**
 * AZALSCORE - Historique des examens
 * ====================================
 */

import React from 'react';
import { Trophy, X, Clock, Target } from 'lucide-react';
import type { ExamResult } from '../types';
import { LEVELS, GRADE_THRESHOLDS } from '../constants';

interface ExamHistoryProps {
  results: ExamResult[];
}

/**
 * Affiche l'historique des examens passés
 */
export function ExamHistory({ results }: ExamHistoryProps) {
  if (results.length === 0) {
    return (
      <div className="bg-gray-50 rounded-xl p-8 text-center">
        <Target className="w-12 h-12 mx-auto text-gray-400 mb-3" />
        <h4 className="font-medium text-gray-600">Aucun examen passé</h4>
        <p className="text-sm text-gray-500 mt-1">
          Vos résultats d'examens apparaîtront ici
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
        <Clock className="w-5 h-5 text-gray-500" />
        Historique des examens
      </h3>

      <div className="space-y-3">
        {results.map((result, index) => (
          <ExamResultRow key={index} result={result} />
        ))}
      </div>
    </div>
  );
}

interface ExamResultRowProps {
  result: ExamResult;
}

function ExamResultRow({ result }: ExamResultRowProps) {
  const levelData = LEVELS.find(l => l.level === result.examLevel);
  const gradeInfo = GRADE_THRESHOLDS.find(g => g.grade === result.grade);

  return (
    <div
      className={`flex items-center gap-4 p-4 rounded-xl border-2 ${
        result.passed
          ? 'border-green-200 bg-green-50'
          : 'border-gray-200 bg-gray-50'
      }`}
    >
      {/* Icône résultat */}
      <div
        className={`w-12 h-12 rounded-xl flex items-center justify-center ${
          result.passed ? 'bg-green-500' : 'bg-gray-400'
        }`}
      >
        {result.passed ? (
          <Trophy className="w-6 h-6 text-white" />
        ) : (
          <X className="w-6 h-6 text-white" />
        )}
      </div>

      {/* Info examen */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="font-semibold text-gray-900 truncate">
            Niveau {result.examLevel} - {levelData?.title}
          </h4>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              result.passed
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {result.passed ? 'Réussi' : 'Échoué'}
          </span>
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
          <span>
            {result.correctAnswers}/{result.totalQuestions} réponses
          </span>
          <span>
            {Math.floor(result.timeSpent / 60)}:{(result.timeSpent % 60).toString().padStart(2, '0')}
          </span>
          <span>{new Date(result.completedAt).toLocaleDateString('fr-FR')}</span>
        </div>
      </div>

      {/* Note */}
      <div className="text-center">
        <div
          className={`text-2xl font-black bg-gradient-to-br ${gradeInfo?.color || 'from-gray-400 to-gray-500'} bg-clip-text text-transparent`}
        >
          {result.grade}
        </div>
        <div className="text-xs text-gray-500">{result.percentage}%</div>
      </div>

      {/* XP gagné */}
      {result.xpEarned > 0 && (
        <div className="text-right">
          <div className="font-bold text-amber-600">+{result.xpEarned}</div>
          <div className="text-xs text-gray-500">XP</div>
        </div>
      )}
    </div>
  );
}

export default ExamHistory;
