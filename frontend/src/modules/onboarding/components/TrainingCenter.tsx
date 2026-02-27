/**
 * AZALSCORE Module - Onboarding - Centre de Formation
 * Interface principale de formation
 */

import React, { useState } from 'react';
import {
  Play,
  Target,
  Video,
  BookOpen,
  Trophy,
  Check,
  ArrowRight,
  ExternalLink,
  GraduationCap,
} from 'lucide-react';
import { useOnboarding } from '../context';
import { ONBOARDING_TOURS } from '../constants';

// ============================================================================
// COMPONENT
// ============================================================================

export function TrainingCenter() {
  const { progress, startTour } = useOnboarding();
  const [activeTab, setActiveTab] = useState<'tours' | 'videos' | 'docs'>('tours');

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <GraduationCap className="w-8 h-8 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">
            Centre de Formation
          </h1>
        </div>
        <p className="text-gray-600">
          Apprenez a maitriser AZALSCORE avec nos guides interactifs
        </p>
      </div>

      {/* Progress Card */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-6 text-white mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-blue-100 text-sm mb-1">Votre progression</p>
            <p className="text-3xl font-bold">{progress.totalProgress}%</p>
          </div>
          <Trophy className="w-12 h-12 text-blue-200" />
        </div>
        <div className="w-full bg-blue-500 rounded-full h-2">
          <div
            className="bg-white h-2 rounded-full transition-all"
            style={{ width: `${progress.totalProgress}%` }}
          />
        </div>
        <p className="text-blue-100 text-sm mt-2">
          {progress.completedTours.length} / {ONBOARDING_TOURS.length} formations completees
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-6">
          {[
            { id: 'tours', label: 'Tours Guides', icon: Target },
            { id: 'videos', label: 'Videos', icon: Video },
            { id: 'docs', label: 'Documentation', icon: BookOpen },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`flex items-center gap-2 pb-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'tours' && (
        <div className="grid gap-4">
          {ONBOARDING_TOURS.map(tour => {
            const isCompleted = progress.completedTours.includes(tour.id);

            return (
              <div
                key={tour.id}
                className={`border rounded-xl p-5 transition-all ${
                  isCompleted
                    ? 'border-green-200 bg-green-50'
                    : 'border-gray-200 hover:border-blue-300 hover:shadow-md'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      isCompleted ? 'bg-green-100' : 'bg-blue-100'
                    }`}>
                      {isCompleted ? (
                        <Check className="w-6 h-6 text-green-600" />
                      ) : (
                        <Play className="w-6 h-6 text-blue-600" />
                      )}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-1">
                        {tour.name}
                      </h3>
                      <p className="text-gray-600 text-sm mb-2">
                        {tour.description}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          {tour.steps.length} etapes
                        </span>
                        {tour.duration && (
                          <span className="flex items-center gap-1">
                            <Play className="w-3 h-3" />
                            {tour.duration}
                          </span>
                        )}
                        {tour.level && (
                          <span className={`px-2 py-0.5 rounded-full ${
                            tour.level === 'debutant'
                              ? 'bg-green-100 text-green-700'
                              : tour.level === 'intermediaire'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-purple-100 text-purple-700'
                          }`}>
                            {tour.level}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => startTour(tour.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isCompleted
                        ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {isCompleted ? 'Revoir' : 'Commencer'}
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {activeTab === 'videos' && (
        <div className="grid md:grid-cols-2 gap-4">
          {[
            { title: 'Premiere connexion', duration: '5:00', module: 'Decouverte' },
            { title: 'Creer un client', duration: '4:30', module: 'CRM' },
            { title: 'Votre premier devis', duration: '8:00', module: 'Facturation' },
            { title: 'Le Cockpit dirigeant', duration: '5:00', module: 'Cockpit' },
            { title: 'Gestion des stocks', duration: '7:00', module: 'Stock' },
            { title: 'Rapprochement bancaire', duration: '6:00', module: 'Compta' },
          ].map((video, i) => (
            <div
              key={i}
              className="border border-gray-200 rounded-xl p-4 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
            >
              <div className="aspect-video bg-gray-100 rounded-lg mb-3 flex items-center justify-center">
                <Play className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="font-medium text-gray-900 mb-1">{video.title}</h3>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span>{video.duration}</span>
                <span>-</span>
                <span>{video.module}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'docs' && (
        <div className="space-y-4">
          {[
            { title: 'Guide Utilisateur Complet', pages: '150+', type: 'PDF' },
            { title: 'Fiches Pratiques par Profil', pages: '80', type: 'PDF' },
            { title: 'Reference Rapide', pages: '2', type: 'PDF' },
            { title: 'Guide Administrateur', pages: '100', type: 'PDF' },
            { title: 'FAQ', pages: 'En ligne', type: 'Web' },
          ].map((doc, i) => (
            <div
              key={i}
              className="flex items-center justify-between border border-gray-200 rounded-xl p-4 hover:border-blue-300 transition-all"
            >
              <div className="flex items-center gap-4">
                <BookOpen className="w-8 h-8 text-blue-600" />
                <div>
                  <h3 className="font-medium text-gray-900">{doc.title}</h3>
                  <p className="text-sm text-gray-500">{doc.pages} pages - {doc.type}</p>
                </div>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg text-sm font-medium">
                Telecharger
                <ExternalLink className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TrainingCenter;
