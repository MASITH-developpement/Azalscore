/**
 * AZALSCORE - Module Onboarding
 * ==============================
 * Systeme de formation integre au logiciel.
 * Comprend: Wizard d'accueil, Tours guides, Aide contextuelle.
 */

import React, { useState, useEffect, createContext, useContext, useCallback } from 'react';
import {
  X,
  ChevronRight,
  ChevronLeft,
  Check,
  Play,
  HelpCircle,
  BookOpen,
  Video,
  Target,
  Lightbulb,
  Sparkles,
  GraduationCap,
  Trophy,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  target?: string; // CSS selector for highlight
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  action?: () => void;
  video?: string;
  image?: string;
}

export interface OnboardingTour {
  id: string;
  name: string;
  description: string;
  steps: OnboardingStep[];
  module?: string;
  duration?: string;
  level?: 'debutant' | 'intermediaire' | 'avance';
}

export interface UserProgress {
  completedTours: string[];
  currentTour?: string;
  currentStep?: number;
  achievements: string[];
  totalProgress: number;
}

interface OnboardingContextType {
  isActive: boolean;
  currentTour: OnboardingTour | null;
  currentStepIndex: number;
  progress: UserProgress;
  startTour: (tourId: string) => void;
  nextStep: () => void;
  prevStep: () => void;
  endTour: () => void;
  skipTour: () => void;
  showHelp: (context: string) => void;
}

// ============================================================================
// CONTEXT
// ============================================================================

const OnboardingContext = createContext<OnboardingContextType | null>(null);

export const useOnboarding = () => {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error('useOnboarding must be used within OnboardingProvider');
  }
  return context;
};

// ============================================================================
// TOURS PREDEFINIES
// ============================================================================

export const ONBOARDING_TOURS: OnboardingTour[] = [
  {
    id: 'welcome',
    name: 'Bienvenue sur AZALSCORE',
    description: 'Decouvrez les bases de votre nouvel ERP',
    duration: '5 min',
    level: 'debutant',
    steps: [
      {
        id: 'welcome-1',
        title: 'Bienvenue sur AZALSCORE ! 🎉',
        description: 'Felicitations pour votre premiere connexion. Ce guide rapide va vous presenter les fonctionnalites essentielles de votre nouvel ERP.',
        position: 'center',
      },
      {
        id: 'welcome-2',
        title: 'La barre de recherche',
        description: 'Appuyez sur "/" pour rechercher instantanement clients, documents ou produits. Utilisez @ pour les clients, # pour les documents.',
        target: '[data-tour="search-bar"]',
        position: 'bottom',
      },
      {
        id: 'welcome-3',
        title: 'Le menu principal',
        description: 'Accedez a tous les modules depuis ce menu. Les sections sont organisees par domaine : Gestion, Finance, Operations...',
        target: '[data-tour="main-menu"]',
        position: 'right',
      },
      {
        id: 'welcome-4',
        title: 'Vos notifications',
        description: 'La cloche vous alerte des evenements importants : nouveaux messages, validations en attente, alertes systeme.',
        target: '[data-tour="notifications"]',
        position: 'bottom',
      },
      {
        id: 'welcome-5',
        title: 'Votre assistant Theo',
        description: 'Cliquez ici pour parler a Theo, votre assistant IA. Il peut repondre a vos questions et effectuer des actions pour vous.',
        target: '[data-tour="theo-button"]',
        position: 'top',
      },
      {
        id: 'welcome-6',
        title: 'Vous etes pret !',
        description: 'Explorez AZALSCORE a votre rythme. D\'autres formations sont disponibles dans le Centre d\'aide. Bonne decouverte !',
        position: 'center',
      },
    ],
  },
  {
    id: 'crm-basics',
    name: 'Gestion des Clients',
    description: 'Apprenez a gerer vos clients dans le CRM',
    module: 'crm',
    duration: '8 min',
    level: 'debutant',
    steps: [
      {
        id: 'crm-1',
        title: 'Le module CRM',
        description: 'Bienvenue dans le CRM AZALSCORE. C\'est ici que vous gerez toutes les informations de vos clients et prospects.',
        position: 'center',
      },
      {
        id: 'crm-2',
        title: 'Liste des clients',
        description: 'Tous vos clients apparaissent ici. Utilisez les filtres pour trouver rapidement ce que vous cherchez.',
        target: '[data-tour="client-list"]',
        position: 'top',
      },
      {
        id: 'crm-3',
        title: 'Creer un client',
        description: 'Cliquez sur ce bouton pour ajouter un nouveau client. Les champs obligatoires sont marques d\'un asterisque.',
        target: '[data-tour="new-client-btn"]',
        position: 'left',
      },
      {
        id: 'crm-4',
        title: 'Fiche client',
        description: 'Chaque client a sa fiche detaillee avec onglets : informations, documents, historique, notes.',
        target: '[data-tour="client-card"]',
        position: 'right',
      },
      {
        id: 'crm-5',
        title: 'Recherche rapide',
        description: 'Tapez @NomClient dans la recherche globale pour trouver instantanement un client.',
        target: '[data-tour="search-bar"]',
        position: 'bottom',
      },
    ],
  },
  {
    id: 'invoicing-basics',
    name: 'Devis et Factures',
    description: 'Creez et gerez vos documents commerciaux',
    module: 'invoicing',
    duration: '10 min',
    level: 'debutant',
    steps: [
      {
        id: 'inv-1',
        title: 'La facturation dans AZALSCORE',
        description: 'Ce module gere tout le cycle commercial : devis, commandes, factures, avoirs.',
        position: 'center',
      },
      {
        id: 'inv-2',
        title: 'Creer un devis',
        description: 'Cliquez ici pour creer un nouveau devis. Selectionnez le client, ajoutez les lignes, et c\'est pret !',
        target: '[data-tour="new-quote-btn"]',
        position: 'left',
      },
      {
        id: 'inv-3',
        title: 'Ajouter des lignes',
        description: 'Chaque ligne correspond a un produit ou service. Le prix et la TVA se calculent automatiquement.',
        target: '[data-tour="quote-lines"]',
        position: 'top',
      },
      {
        id: 'inv-4',
        title: 'Envoyer le devis',
        description: 'Une fois pret, envoyez le devis par email directement depuis AZALSCORE.',
        target: '[data-tour="send-btn"]',
        position: 'bottom',
      },
      {
        id: 'inv-5',
        title: 'Convertir en facture',
        description: 'Quand le client accepte, convertissez le devis en commande puis en facture en quelques clics.',
        target: '[data-tour="convert-btn"]',
        position: 'left',
      },
    ],
  },
  {
    id: 'cockpit-tour',
    name: 'Tableau de Bord',
    description: 'Maitrisez le Cockpit dirigeant',
    module: 'cockpit',
    duration: '5 min',
    level: 'intermediaire',
    steps: [
      {
        id: 'cockpit-1',
        title: 'Le Cockpit Dirigeant',
        description: 'Vue d\'ensemble de votre activite en temps reel. Tous les indicateurs cles sont ici.',
        position: 'center',
      },
      {
        id: 'cockpit-2',
        title: 'Indicateurs cles',
        description: 'CA, pipeline, tresorerie, tendances... Cliquez sur un chiffre pour voir le detail.',
        target: '[data-tour="kpi-cards"]',
        position: 'bottom',
      },
      {
        id: 'cockpit-3',
        title: 'Graphiques',
        description: 'Visualisez l\'evolution de vos performances. Survolez pour les details.',
        target: '[data-tour="charts"]',
        position: 'top',
      },
      {
        id: 'cockpit-4',
        title: 'Personnalisation',
        description: 'Configurez votre tableau de bord selon vos besoins. Ajoutez, supprimez ou reorganisez les widgets.',
        target: '[data-tour="customize-btn"]',
        position: 'left',
      },
    ],
  },
];

// ============================================================================
// PROVIDER
// ============================================================================

interface OnboardingProviderProps {
  children: React.ReactNode;
}

export function OnboardingProvider({ children }: OnboardingProviderProps) {
  const [isActive, setIsActive] = useState(false);
  const [currentTour, setCurrentTour] = useState<OnboardingTour | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [progress, setProgress] = useState<UserProgress>({
    completedTours: [],
    achievements: [],
    totalProgress: 0,
  });

  // Charger la progression depuis localStorage
  useEffect(() => {
    const saved = localStorage.getItem('azalscore_onboarding_progress');
    if (saved) {
      setProgress(JSON.parse(saved));
    }
  }, []);

  // Sauvegarder la progression
  const saveProgress = useCallback((newProgress: UserProgress) => {
    setProgress(newProgress);
    localStorage.setItem('azalscore_onboarding_progress', JSON.stringify(newProgress));
  }, []);

  const startTour = useCallback((tourId: string) => {
    const tour = ONBOARDING_TOURS.find(t => t.id === tourId);
    if (tour) {
      setCurrentTour(tour);
      setCurrentStepIndex(0);
      setIsActive(true);
      saveProgress({
        ...progress,
        currentTour: tourId,
        currentStep: 0,
      });
    }
  }, [progress, saveProgress]);

  const nextStep = useCallback(() => {
    if (!currentTour) return;

    if (currentStepIndex < currentTour.steps.length - 1) {
      const newIndex = currentStepIndex + 1;
      setCurrentStepIndex(newIndex);
      saveProgress({
        ...progress,
        currentStep: newIndex,
      });
    } else {
      // Tour termine
      const newCompleted = [...progress.completedTours, currentTour.id];
      const newProgress = Math.round((newCompleted.length / ONBOARDING_TOURS.length) * 100);
      saveProgress({
        ...progress,
        completedTours: newCompleted,
        currentTour: undefined,
        currentStep: undefined,
        totalProgress: newProgress,
      });
      setIsActive(false);
      setCurrentTour(null);
    }
  }, [currentTour, currentStepIndex, progress, saveProgress]);

  const prevStep = useCallback(() => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
    }
  }, [currentStepIndex]);

  const endTour = useCallback(() => {
    if (currentTour) {
      const newCompleted = [...progress.completedTours, currentTour.id];
      saveProgress({
        ...progress,
        completedTours: newCompleted,
        currentTour: undefined,
        currentStep: undefined,
        totalProgress: Math.round((newCompleted.length / ONBOARDING_TOURS.length) * 100),
      });
    }
    setIsActive(false);
    setCurrentTour(null);
  }, [currentTour, progress, saveProgress]);

  const skipTour = useCallback(() => {
    setIsActive(false);
    setCurrentTour(null);
    saveProgress({
      ...progress,
      currentTour: undefined,
      currentStep: undefined,
    });
  }, [progress, saveProgress]);

  const showHelp = useCallback((context: string) => {
    // Ouvrir l'aide contextuelle
    console.log('Show help for:', context);
  }, []);

  return (
    <OnboardingContext.Provider
      value={{
        isActive,
        currentTour,
        currentStepIndex,
        progress,
        startTour,
        nextStep,
        prevStep,
        endTour,
        skipTour,
        showHelp,
      }}
    >
      {children}
      {isActive && currentTour && (
        <TourOverlay
          tour={currentTour}
          stepIndex={currentStepIndex}
          onNext={nextStep}
          onPrev={prevStep}
          onSkip={skipTour}
          onEnd={endTour}
        />
      )}
    </OnboardingContext.Provider>
  );
}

// ============================================================================
// TOUR OVERLAY
// ============================================================================

interface TourOverlayProps {
  tour: OnboardingTour;
  stepIndex: number;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
  onEnd: () => void;
}

function TourOverlay({ tour, stepIndex, onNext, onPrev, onSkip, onEnd }: TourOverlayProps) {
  const step = tour.steps[stepIndex];
  const isFirst = stepIndex === 0;
  const isLast = stepIndex === tour.steps.length - 1;

  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    if (step.target) {
      const element = document.querySelector(step.target);
      if (element) {
        const rect = element.getBoundingClientRect();
        setTargetRect(rect);
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        setTargetRect(null);
      }
    } else {
      setTargetRect(null);
    }
  }, [step.target]);

  const getTooltipPosition = () => {
    if (!targetRect || step.position === 'center') {
      return {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
    }

    const padding = 20;
    const positions: Record<string, React.CSSProperties> = {
      top: {
        bottom: `${window.innerHeight - targetRect.top + padding}px`,
        left: `${targetRect.left + targetRect.width / 2}px`,
        transform: 'translateX(-50%)',
      },
      bottom: {
        top: `${targetRect.bottom + padding}px`,
        left: `${targetRect.left + targetRect.width / 2}px`,
        transform: 'translateX(-50%)',
      },
      left: {
        top: `${targetRect.top + targetRect.height / 2}px`,
        right: `${window.innerWidth - targetRect.left + padding}px`,
        transform: 'translateY(-50%)',
      },
      right: {
        top: `${targetRect.top + targetRect.height / 2}px`,
        left: `${targetRect.right + padding}px`,
        transform: 'translateY(-50%)',
      },
    };

    return positions[step.position || 'bottom'];
  };

  return (
    <div className="fixed inset-0 z-[9999]">
      {/* Overlay avec decoupe pour le target */}
      <div className="absolute inset-0 bg-black/60">
        {targetRect && (
          <div
            className="absolute bg-transparent shadow-[0_0_0_9999px_rgba(0,0,0,0.6)] rounded-lg ring-4 ring-blue-500 ring-offset-2"
            style={{
              top: targetRect.top - 4,
              left: targetRect.left - 4,
              width: targetRect.width + 8,
              height: targetRect.height + 8,
            }}
          />
        )}
      </div>

      {/* Tooltip */}
      <div
        className="absolute bg-white rounded-xl shadow-2xl p-6 max-w-md z-10"
        style={getTooltipPosition()}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">{tour.name}</p>
              <p className="text-sm text-gray-400">
                Etape {stepIndex + 1} / {tour.steps.length}
              </p>
            </div>
          </div>
          <button
            onClick={onSkip}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {step.title}
        </h3>
        <p className="text-gray-600 mb-6">
          {step.description}
        </p>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-4">
          <div
            className="bg-blue-600 h-1.5 rounded-full transition-all"
            style={{ width: `${((stepIndex + 1) / tour.steps.length) * 100}%` }}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <button
            onClick={onPrev}
            disabled={isFirst}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
              isFirst
                ? 'text-gray-300 cursor-not-allowed'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            Precedent
          </button>

          <div className="flex gap-2">
            <button
              onClick={onSkip}
              className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700"
            >
              Passer
            </button>
            <button
              onClick={isLast ? onEnd : onNext}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
            >
              {isLast ? (
                <>
                  Terminer
                  <Check className="w-4 h-4" />
                </>
              ) : (
                <>
                  Suivant
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// CENTRE DE FORMATION
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

// ============================================================================
// AIDE CONTEXTUELLE
// ============================================================================

interface ContextualHelpProps {
  context: string;
  children: React.ReactNode;
}

export function ContextualHelp({ context, children }: ContextualHelpProps) {
  const [isOpen, setIsOpen] = useState(false);

  const helpContent: Record<string, { title: string; tips: string[] }> = {
    'client-form': {
      title: 'Creer un client',
      tips: [
        'Les champs marques * sont obligatoires',
        'Le SIRET doit contenir 14 chiffres',
        'Vous pouvez ajouter plusieurs contacts',
      ],
    },
    'quote-form': {
      title: 'Creer un devis',
      tips: [
        'Selectionnez d\'abord le client',
        'Les prix se calculent automatiquement',
        'La validite par defaut est de 30 jours',
      ],
    },
    // Ajouter d'autres contextes...
  };

  const help = helpContent[context];
  if (!help) return <>{children}</>;

  return (
    <div className="relative">
      {children}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="absolute -top-2 -right-2 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center hover:bg-blue-200 transition-colors"
      >
        <HelpCircle className="w-4 h-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-8 w-72 bg-white rounded-xl shadow-xl border border-gray-200 p-4 z-50">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-5 h-5 text-amber-500" />
            <h4 className="font-semibold text-gray-900">{help.title}</h4>
          </div>
          <ul className="space-y-2">
            {help.tips.map((tip, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <Sparkles className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                {tip}
              </li>
            ))}
          </ul>
          <button
            onClick={() => setIsOpen(false)}
            className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// WIDGET D'AIDE FLOTTANT
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

// ============================================================================
// RE-EXPORTS DES COMPOSANTS GAMIFIES
// ============================================================================

// Gamification
export {
  useGamification,
  GamificationProvider,
  XPProgressBar,
  PlayerStatsCard,
  DailyChallengeCard,
  BadgeCollection,
  Leaderboard,
  CelebrationOverlay,
  GamificationDashboard,
  // Systeme d'examen et notation
  LevelExamComponent,
  ExamResultsDisplay,
  ExamHistory,
  LevelUpNotification,
  PointsTable,
  // Quiz d'entrainement
  PracticeQuizCard,
  PracticeQuizPlayer,
  PracticeQuizLibrary,
} from './components/Gamification';

// Jeux Interactifs
export {
  AnimatedQuiz,
  DragDropCategory,
  MatchingGame,
  InteractiveSimulation,
  MemoryGame,
} from './components/InteractiveGames';

// Micro-Learning
export {
  MicroLessonCard,
  MicroLessonPlayer,
  MicroLearningLibrary,
} from './components/MicroLearning';

// Tooltips & Aide
export {
  Tooltip,
  FeatureHighlight,
  FieldHint,
  InlineHelp,
  StepIndicator,
  AchievementBadge,
} from './components/Tooltips';

// Base de Connaissances
export { KnowledgeBase } from './components/KnowledgeBase';

// Training Hub (composant principal unifie)
export { TrainingHub } from './components/TrainingHub';

// Internationalisation (i18n)
export {
  I18nProvider,
  useI18n,
  LanguageSelector,
  translations,
  languageNames,
  languageFlags,
  isRTL,
  FR,
} from './i18n';
export type { SupportedLanguage, TranslationStrings, I18nContextType } from './i18n';

// Questions d'examens multilingues
export {
  getLevelExams,
  getPracticeQuizzes,
  getExamByLevel,
  getQuizById,
} from './i18n/examQuestions';

// Systeme de formation modulaire
export {
  // Types
  type ModuleTrainingContent,
  type ModuleLesson,
  type ModuleQuiz,
  type ModuleQuestion,
  type ModuleExercise,
  type ModuleProgress,
  type UserTrainingProgress,
  type GlobalSynthesis,
  type ExamResult,
  // Registre
  registerTrainingModule,
  getRegisteredModules,
  isModuleRegistered,
  loadModuleTraining,
  loadUserTrainings,
  getAccessibleModules,
  generateGlobalSynthesis,
  calculateTrainingStats,
  generateGlobalExam,
  // Hooks
  useTraining,
  useModuleTraining,
  useLessonPlayer,
  useQuizPlayer,
} from './training';

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  // Core
  OnboardingProvider,
  TrainingCenter,
  ContextualHelp,
  HelpWidget,
  useOnboarding,
  ONBOARDING_TOURS,
};
