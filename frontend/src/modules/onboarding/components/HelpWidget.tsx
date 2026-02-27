/**
 * AZALSCORE Module - Onboarding - Widget d'Aide Flottant
 * Bouton d'aide flottant avec menu rapide
 */

import React, { useState, useEffect } from 'react';
import { X, HelpCircle, Play, BookOpen, Video, GraduationCap } from 'lucide-react';
import { useOnboarding } from '../context';

// ============================================================================
// COMPONENT
// ============================================================================

export function HelpWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const { startTour, progress } = useOnboarding();

  // Afficher automatiquement pour les nouveaux utilisateurs
  useEffect(() => {
    if (progress.completedTours.length === 0) {
      const hasSeenWelcome = localStorage.getItem('azalscore_welcome_shown');
      if (!hasSeenWelcome) {
        setTimeout(() => {
          startTour('welcome');
          localStorage.setItem('azalscore_welcome_shown', 'true');
        }, 1000);
      }
    }
  }, [progress.completedTours.length, startTour]);

  return (
    <div className="fixed bottom-20 right-6 z-40">
      {isOpen && (
        <div className="absolute bottom-16 right-0 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
          <div className="bg-blue-600 text-white p-4">
            <h3 className="font-semibold flex items-center gap-2">
              <GraduationCap className="w-5 h-5" />
              Besoin d'aide ?
            </h3>
          </div>
          <div className="p-4 space-y-3">
            <button
              onClick={() => {
                startTour('welcome');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left"
            >
              <Play className="w-5 h-5 text-blue-600" />
              <div>
                <p className="font-medium text-gray-900">Tour guide</p>
                <p className="text-xs text-gray-500">Decouvrez l'interface</p>
              </div>
            </button>
            <button
              onClick={() => window.open('/formation', '_blank')}
              className="w-full flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left"
            >
              <BookOpen className="w-5 h-5 text-green-600" />
              <div>
                <p className="font-medium text-gray-900">Documentation</p>
                <p className="text-xs text-gray-500">Guides complets</p>
              </div>
            </button>
            <button
              onClick={() => window.open('/videos', '_blank')}
              className="w-full flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left"
            >
              <Video className="w-5 h-5 text-purple-600" />
              <div>
                <p className="font-medium text-gray-900">Videos</p>
                <p className="text-xs text-gray-500">Tutoriels pas a pas</p>
              </div>
            </button>
          </div>
        </div>
      )}

      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all ${
          isOpen
            ? 'bg-gray-200 text-gray-600'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        {isOpen ? <X className="w-6 h-6" /> : <HelpCircle className="w-6 h-6" />}
      </button>
    </div>
  );
}

export default HelpWidget;
