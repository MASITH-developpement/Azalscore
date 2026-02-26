/**
 * AZALSCORE - Micro-Learning
 * ===========================
 * Lecons courtes, visuelles et faciles a assimiler.
 */

import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  ChevronLeft,
  ChevronRight,
  Volume2,
  VolumeX,
  Maximize,
  CheckCircle,
  Clock,
  Bookmark,
  BookmarkCheck,
  ThumbsUp,
  Share,
  RotateCcw,
  Sparkles,
  Lightbulb,
  AlertCircle,
  Info,
  ArrowRight,
  GraduationCap,
} from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

interface MicroLesson {
  id: string;
  title: string;
  duration: string;
  category: string;
  difficulty: 'facile' | 'moyen' | 'avance';
  slides: Slide[];
  completed?: boolean;
  bookmarked?: boolean;
}

interface Slide {
  id: string;
  type: 'text' | 'image' | 'video' | 'interaction' | 'tip' | 'quiz';
  title?: string;
  content: string;
  image?: string;
  video?: string;
  highlight?: boolean;
  animation?: 'fade' | 'slide' | 'zoom' | 'bounce';
  quiz?: {
    question: string;
    options: string[];
    correctIndex: number;
  };
}

// ============================================================================
// DONNEES DE DEMO
// ============================================================================

const MICRO_LESSONS: MicroLesson[] = [
  {
    id: 'search-101',
    title: 'La recherche en 60 secondes',
    duration: '1 min',
    category: 'Bases',
    difficulty: 'facile',
    slides: [
      {
        id: '1',
        type: 'text',
        title: 'La recherche ultra-rapide ⚡',
        content: 'Trouvez n\'importe quoi en quelques secondes avec la recherche globale AZALSCORE.',
        animation: 'fade',
      },
      {
        id: '2',
        type: 'tip',
        title: 'Le raccourci magique',
        content: 'Appuyez sur la touche "/" pour ouvrir instantanement la recherche. Essayez maintenant !',
        animation: 'bounce',
      },
      {
        id: '3',
        type: 'text',
        title: 'Les prefixes secrets 🔍',
        content: '@ → Clients\n# → Documents\n$ → Produits\n\nExemple: @Dupont trouve tous les clients Dupont',
        animation: 'slide',
      },
      {
        id: '4',
        type: 'quiz',
        content: '',
        quiz: {
          question: 'Pour chercher un client, j\'utilise le prefixe :',
          options: ['#', '@', '$', '&'],
          correctIndex: 1,
        },
      },
      {
        id: '5',
        type: 'text',
        title: 'Bravo ! 🎉',
        content: 'Vous maitrisez maintenant la recherche AZALSCORE.\n\nVous gagnerez des heures chaque semaine !',
        highlight: true,
        animation: 'zoom',
      },
    ],
  },
  {
    id: 'devis-quick',
    title: 'Creer un devis en 2 minutes',
    duration: '2 min',
    category: 'Commercial',
    difficulty: 'facile',
    slides: [
      {
        id: '1',
        type: 'text',
        title: 'Un devis, vite fait bien fait 📄',
        content: 'Apprenez a creer un devis professionnel en quelques clics seulement.',
        animation: 'fade',
      },
      {
        id: '2',
        type: 'text',
        title: 'Etape 1 : Le client',
        content: '1. Cliquez sur "+ Nouveau devis"\n2. Tapez le nom du client\n3. Selectionnez-le dans la liste',
        animation: 'slide',
      },
      {
        id: '3',
        type: 'tip',
        title: 'Astuce Pro 💡',
        content: 'Si le client n\'existe pas, cliquez sur "+ Creer" pour l\'ajouter sans quitter le devis !',
        animation: 'bounce',
      },
      {
        id: '4',
        type: 'text',
        title: 'Etape 2 : Les produits',
        content: '1. Cliquez sur "+ Ajouter une ligne"\n2. Recherchez le produit\n3. Ajustez la quantite\n\nLe prix se calcule automatiquement !',
        animation: 'slide',
      },
      {
        id: '5',
        type: 'text',
        title: 'Etape 3 : Envoyer',
        content: 'Cliquez sur "Envoyer" et le devis part directement par email avec le PDF en piece jointe.\n\nC\'est aussi simple que ca !',
        animation: 'slide',
      },
      {
        id: '6',
        type: 'quiz',
        content: '',
        quiz: {
          question: 'Pour ajouter un produit au devis, je clique sur :',
          options: ['Enregistrer', '+ Ajouter une ligne', 'Nouveau client', 'Imprimer'],
          correctIndex: 1,
        },
      },
    ],
  },
  {
    id: 'theo-intro',
    title: 'Theo, votre assistant IA',
    duration: '1 min 30',
    category: 'IA',
    difficulty: 'facile',
    slides: [
      {
        id: '1',
        type: 'text',
        title: 'Rencontrez Theo 🤖',
        content: 'Theo est votre assistant intelligent. Il peut repondre a vos questions et effectuer des actions pour vous.',
        animation: 'fade',
      },
      {
        id: '2',
        type: 'text',
        title: 'Comment l\'appeler ?',
        content: 'Cliquez sur l\'icone 💬 en bas a droite de votre ecran. Theo est disponible 24h/24 !',
        animation: 'slide',
      },
      {
        id: '3',
        type: 'text',
        title: 'Que peut-il faire ?',
        content: '✅ Repondre a vos questions\n✅ Afficher des rapports\n✅ Envoyer des emails\n✅ Creer des documents\n✅ Analyser des donnees',
        animation: 'slide',
      },
      {
        id: '4',
        type: 'tip',
        title: 'Exemples de questions',
        content: '"Quel est mon CA du mois ?"\n"Liste les factures en retard"\n"Envoie une relance a Dupont"',
        animation: 'bounce',
      },
    ],
  },
];

// ============================================================================
// COMPOSANTS
// ============================================================================

/**
 * Carte de micro-lecon
 */
export function MicroLessonCard({
  lesson,
  onStart,
  onBookmark,
}: {
  lesson: MicroLesson;
  onStart: () => void;
  onBookmark: () => void;
}) {
  const difficultyColors = {
    facile: 'bg-green-100 text-green-700',
    moyen: 'bg-amber-100 text-amber-700',
    avance: 'bg-purple-100 text-purple-700',
  };

  return (
    <div className="bg-white rounded-2xl shadow-md hover:shadow-xl transition-all overflow-hidden group">
      {/* Thumbnail */}
      <div className="relative h-32 bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
        <GraduationCap className="w-12 h-12 text-white/30" />
        <button
          onClick={onStart}
          className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/20 transition-all"
        >
          <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-lg transform scale-90 group-hover:scale-100 transition-transform">
            <Play className="w-8 h-8 text-indigo-600 ml-1" />
          </div>
        </button>

        {/* Duration badge */}
        <div className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {lesson.duration}
        </div>

        {/* Bookmark */}
        <button
          onClick={e => {
            e.stopPropagation();
            onBookmark();
          }}
          className="absolute top-2 right-2 p-2 rounded-full bg-white/20 hover:bg-white/40 transition-colors"
        >
          {lesson.bookmarked ? (
            <BookmarkCheck className="w-5 h-5 text-yellow-400" />
          ) : (
            <Bookmark className="w-5 h-5 text-white" />
          )}
        </button>

        {/* Completed badge */}
        {lesson.completed && (
          <div className="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            Complete
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className={`text-xs px-2 py-0.5 rounded-full ${difficultyColors[lesson.difficulty]}`}>
            {lesson.difficulty}
          </span>
          <span className="text-xs text-gray-500">{lesson.category}</span>
        </div>
        <h3 className="font-bold text-gray-900 mb-2 line-clamp-2">{lesson.title}</h3>
        <button
          onClick={onStart}
          className="w-full py-2 bg-indigo-50 text-indigo-600 rounded-lg font-medium hover:bg-indigo-100 transition-colors flex items-center justify-center gap-2"
        >
          {lesson.completed ? 'Revoir' : 'Commencer'}
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

/**
 * Lecteur de micro-lecon
 */
export function MicroLessonPlayer({
  lesson,
  onComplete,
  onClose,
}: {
  lesson: MicroLesson;
  onComplete: () => void;
  onClose: () => void;
}) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [quizAnswer, setQuizAnswer] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);

  const slide = lesson.slides[currentSlide];
  const isFirstSlide = currentSlide === 0;
  const isLastSlide = currentSlide === lesson.slides.length - 1;
  const progress = ((currentSlide + 1) / lesson.slides.length) * 100;

  const nextSlide = () => {
    if (slide.type === 'quiz' && !quizSubmitted) {
      if (quizAnswer !== null) {
        setQuizSubmitted(true);
      }
      return;
    }

    if (isLastSlide) {
      onComplete();
    } else {
      setCurrentSlide(prev => prev + 1);
      setQuizAnswer(null);
      setQuizSubmitted(false);
    }
  };

  const prevSlide = () => {
    if (!isFirstSlide) {
      setCurrentSlide(prev => prev - 1);
      setQuizAnswer(null);
      setQuizSubmitted(false);
    }
  };

  const getSlideIcon = () => {
    switch (slide.type) {
      case 'tip':
        return <Lightbulb className="w-8 h-8 text-yellow-500" />;
      case 'quiz':
        return <Sparkles className="w-8 h-8 text-purple-500" />;
      default:
        return <Info className="w-8 h-8 text-blue-500" />;
    }
  };

  const getSlideBackground = () => {
    switch (slide.type) {
      case 'tip':
        return 'from-yellow-400 to-orange-500';
      case 'quiz':
        return 'from-purple-500 to-pink-500';
      default:
        return slide.highlight
          ? 'from-green-500 to-emerald-600'
          : 'from-indigo-500 to-purple-600';
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between text-white mb-4">
          <div className="flex items-center gap-3">
            <span className="text-sm opacity-70">{lesson.title}</span>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg">
            ✕
          </button>
        </div>

        {/* Progress bar */}
        <div className="h-1 bg-white/20 rounded-full mb-6 overflow-hidden">
          <div
            className="h-full bg-white transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Slide content */}
        <div
          className={`bg-gradient-to-br ${getSlideBackground()} rounded-3xl p-8 text-white min-h-[400px] flex flex-col animate-slideIn`}
          key={slide.id}
        >
          <div className="flex-1">
            {/* Icon */}
            <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mb-6 backdrop-blur-sm">
              {getSlideIcon()}
            </div>

            {/* Title */}
            {slide.title && (
              <h2 className="text-2xl font-bold mb-4">{slide.title}</h2>
            )}

            {/* Content */}
            {slide.type === 'quiz' && slide.quiz ? (
              <div>
                <p className="text-lg mb-6">{slide.quiz.question}</p>
                <div className="space-y-3">
                  {slide.quiz.options.map((option, index) => (
                    <button
                      key={index}
                      onClick={() => !quizSubmitted && setQuizAnswer(index)}
                      disabled={quizSubmitted}
                      className={`w-full p-4 rounded-xl text-left transition-all ${
                        quizSubmitted
                          ? index === slide.quiz!.correctIndex
                            ? 'bg-green-500 text-white'
                            : quizAnswer === index
                            ? 'bg-red-500 text-white'
                            : 'bg-white/10 text-white/50'
                          : quizAnswer === index
                          ? 'bg-white text-gray-900'
                          : 'bg-white/20 hover:bg-white/30'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center font-bold">
                          {String.fromCharCode(65 + index)}
                        </span>
                        {option}
                        {quizSubmitted && index === slide.quiz!.correctIndex && (
                          <CheckCircle className="w-5 h-5 ml-auto" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
                {quizSubmitted && (
                  <div className="mt-4 p-3 bg-white/20 rounded-xl">
                    {quizAnswer === slide.quiz.correctIndex ? (
                      <p className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5" />
                        Parfait ! Bonne reponse.
                      </p>
                    ) : (
                      <p className="flex items-center gap-2">
                        <AlertCircle className="w-5 h-5" />
                        La bonne reponse etait : {slide.quiz.options[slide.quiz.correctIndex]}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-lg whitespace-pre-line opacity-90">{slide.content}</p>
            )}
          </div>

          {/* Slide indicator */}
          <div className="flex items-center justify-center gap-2 mt-6">
            {lesson.slides.map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full transition-all ${
                  index === currentSlide
                    ? 'w-6 bg-white'
                    : index < currentSlide
                    ? 'bg-white/70'
                    : 'bg-white/30'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-6">
          <button
            onClick={prevSlide}
            disabled={isFirstSlide}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
              isFirstSlide
                ? 'text-white/30 cursor-not-allowed'
                : 'text-white hover:bg-white/10'
            }`}
          >
            <ChevronLeft className="w-5 h-5" />
            Precedent
          </button>

          <button
            onClick={nextSlide}
            className="flex items-center gap-2 px-6 py-3 bg-white text-gray-900 rounded-xl font-bold hover:shadow-lg transition-all"
          >
            {isLastSlide ? (
              <>
                Terminer
                <CheckCircle className="w-5 h-5" />
              </>
            ) : slide.type === 'quiz' && !quizSubmitted ? (
              <>
                Valider
                <Sparkles className="w-5 h-5" />
              </>
            ) : (
              <>
                Suivant
                <ChevronRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Bibliotheque de micro-lecons
 */
export function MicroLearningLibrary() {
  const [lessons, setLessons] = useState<MicroLesson[]>(MICRO_LESSONS);
  const [selectedLesson, setSelectedLesson] = useState<MicroLesson | null>(null);
  const [filter, setFilter] = useState<string>('all');

  const categories = ['all', ...new Set(lessons.map(l => l.category))];

  const filteredLessons = filter === 'all'
    ? lessons
    : lessons.filter(l => l.category === filter);

  const handleComplete = (lessonId: string) => {
    setLessons(prev =>
      prev.map(l => (l.id === lessonId ? { ...l, completed: true } : l))
    );
    setSelectedLesson(null);
  };

  const handleBookmark = (lessonId: string) => {
    setLessons(prev =>
      prev.map(l => (l.id === lessonId ? { ...l, bookmarked: !l.bookmarked } : l))
    );
  };

  const completedCount = lessons.filter(l => l.completed).length;
  const totalDuration = lessons.reduce((acc, l) => {
    const mins = parseInt(l.duration);
    return acc + (isNaN(mins) ? 2 : mins);
  }, 0);

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <Sparkles className="w-7 h-7 text-purple-500" />
          Micro-Learning
        </h1>
        <p className="text-gray-600">
          Des lecons courtes et efficaces pour apprendre rapidement
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl p-4 text-white">
          <p className="text-white/70 text-sm mb-1">Completees</p>
          <p className="text-3xl font-bold">{completedCount}/{lessons.length}</p>
        </div>
        <div className="bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl p-4 text-white">
          <p className="text-white/70 text-sm mb-1">Duree totale</p>
          <p className="text-3xl font-bold">{totalDuration} min</p>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl p-4 text-white">
          <p className="text-white/70 text-sm mb-1">Progression</p>
          <p className="text-3xl font-bold">{Math.round((completedCount / lessons.length) * 100)}%</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
              filter === cat
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {cat === 'all' ? 'Toutes' : cat}
          </button>
        ))}
      </div>

      {/* Lessons grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredLessons.map(lesson => (
          <MicroLessonCard
            key={lesson.id}
            lesson={lesson}
            onStart={() => setSelectedLesson(lesson)}
            onBookmark={() => handleBookmark(lesson.id)}
          />
        ))}
      </div>

      {/* Player */}
      {selectedLesson && (
        <MicroLessonPlayer
          lesson={selectedLesson}
          onComplete={() => handleComplete(selectedLesson.id)}
          onClose={() => setSelectedLesson(null)}
        />
      )}
    </div>
  );
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  MicroLessonCard,
  MicroLessonPlayer,
  MicroLearningLibrary,
  MICRO_LESSONS,
};
