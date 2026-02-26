/**
 * AZALSCORE - Table des points
 * =============================
 */

import React from 'react';
import { Zap } from 'lucide-react';
import type { PointsAction } from '../types';

interface PointsTableProps {
  actions: PointsAction[];
}

const CATEGORY_LABELS: Record<string, string> = {
  apprentissage: 'Apprentissage',
  pratique: 'Pratique',
  social: 'Social',
  examen: 'Examens',
};

const CATEGORY_COLORS: Record<string, string> = {
  apprentissage: 'bg-blue-100 text-blue-700',
  pratique: 'bg-green-100 text-green-700',
  social: 'bg-purple-100 text-purple-700',
  examen: 'bg-amber-100 text-amber-700',
};

/**
 * Table affichant toutes les actions et leurs points associés
 */
export function PointsTable({ actions }: PointsTableProps) {
  // Grouper par catégorie
  const groupedActions = actions.reduce((acc, action) => {
    if (!acc[action.category]) {
      acc[action.category] = [];
    }
    acc[action.category].push(action);
    return acc;
  }, {} as Record<string, PointsAction[]>);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Zap className="w-5 h-5 text-yellow-500" />
        <h3 className="text-lg font-bold text-gray-900">Comment gagner des points</h3>
      </div>

      {Object.entries(groupedActions).map(([category, categoryActions]) => (
        <div key={category} className="bg-white rounded-xl border overflow-hidden">
          <div className={`px-4 py-2 font-medium ${CATEGORY_COLORS[category]}`}>
            {CATEGORY_LABELS[category] || category}
          </div>
          <div className="divide-y">
            {categoryActions.map(action => (
              <div
                key={action.id}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">{action.icon}</span>
                  <span className="text-gray-700">{action.action}</span>
                </div>
                <div className="flex items-center gap-1 font-bold text-amber-600">
                  <Zap className="w-4 h-4" />
                  +{action.points}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default PointsTable;
