/**
 * AZALSCORE - Mini-Jeux Interactifs de Formation
 * ===============================================
 * Simulations, quiz dynamiques et exercices pratiques ludiques.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  CheckCircle,
  XCircle,
  HelpCircle,
  Lightbulb,
  Timer,
  Zap,
  Star,
  Trophy,
  ArrowRight,
  Target,
  Shuffle,
  MousePointer,
  Sparkles,
  Volume2,
  VolumeX,
} from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
  hint?: string;
  points: number;
  timeLimit?: number;
}

interface DragDropItem {
  id: string;
  content: string;
  category: string;
}

interface MatchPair {
  id: string;
  left: string;
  right: string;
}

interface SimulationStep {
  id: string;
  instruction: string;
  targetElement: string;
  action: 'click' | 'type' | 'select' | 'drag';
  expectedValue?: string;
  hint: string;
  validation: (value: any) => boolean;
}

// ============================================================================
// QUIZ INTERACTIF ANIME
// ============================================================================

interface AnimatedQuizProps {
  questions: QuizQuestion[];
  onComplete: (score: number, total: number) => void;
  showTimer?: boolean;
}

export function AnimatedQuiz({ questions, onComplete, showTimer = true }: AnimatedQuizProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [score, setScore] = useState(0);
  const [streak, setStreak] = useState(0);
  const [timeLeft, setTimeLeft] = useState(questions[0]?.timeLimit || 30);
  const [showHint, setShowHint] = useState(false);
  const [animations, setAnimations] = useState({ shake: false, pulse: false });

  const currentQuestion = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;

  // Timer
  useEffect(() => {
    if (!showTimer || isAnswered || timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          handleTimeout();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [showTimer, isAnswered, currentIndex]);

  const handleTimeout = () => {
    setIsAnswered(true);
    setStreak(0);
    setAnimations({ shake: true, pulse: false });
    setTimeout(() => setAnimations({ shake: false, pulse: false }), 500);
  };

  const handleAnswer = (index: number) => {
    if (isAnswered) return;

    setSelectedAnswer(index);
    setIsAnswered(true);

    const isCorrect = index === currentQuestion.correctIndex;

    if (isCorrect) {
      const bonusPoints = streak >= 3 ? 10 : streak >= 2 ? 5 : 0;
      setScore(prev => prev + currentQuestion.points + bonusPoints);
      setStreak(prev => prev + 1);
      setAnimations({ shake: false, pulse: true });
    } else {
      setStreak(0);
      setAnimations({ shake: true, pulse: false });
    }

    setTimeout(() => setAnimations({ shake: false, pulse: false }), 500);
  };

  const nextQuestion = () => {
    if (isLastQuestion) {
      onComplete(score, questions.reduce((acc, q) => acc + q.points, 0));
    } else {
      setCurrentIndex(prev => prev + 1);
      setSelectedAnswer(null);
      setIsAnswered(false);
      setShowHint(false);
      setTimeLeft(questions[currentIndex + 1]?.timeLimit || 30);
    }
  };

  const getOptionStyle = (index: number) => {
    if (!isAnswered) {
      return selectedAnswer === index
        ? 'border-blue-500 bg-blue-50'
        : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50';
    }

    if (index === currentQuestion.correctIndex) {
      return 'border-green-500 bg-green-50';
    }

    if (selectedAnswer === index) {
      return 'border-red-500 bg-red-50';
    }

    return 'border-gray-200 opacity-50';
  };

  return (
    <div className={`max-w-2xl mx-auto ${animations.shake ? 'animate-shake' : ''}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="text-sm font-medium text-gray-500">
            Question {currentIndex + 1}/{questions.length}
          </div>
          {streak >= 2 && (
            <div className="flex items-center gap-1 bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm animate-pulse">
              <Zap className="w-4 h-4" />
              Serie x{streak}
            </div>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 text-yellow-600 font-bold">
            <Star className="w-5 h-5" />
            {score}
          </div>
          {showTimer && (
            <div className={`flex items-center gap-1 font-mono ${
              timeLeft <= 10 ? 'text-red-600 animate-pulse' : 'text-gray-600'
            }`}>
              <Timer className="w-5 h-5" />
              {timeLeft}s
            </div>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-gray-200 rounded-full mb-6 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
          style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
        />
      </div>

      {/* Question */}
      <div className={`bg-white rounded-2xl shadow-lg p-6 mb-6 ${animations.pulse ? 'animate-pulse-green' : ''}`}>
        <h3 className="text-xl font-bold text-gray-900 mb-6">{currentQuestion.question}</h3>

        {/* Options */}
        <div className="space-y-3">
          {currentQuestion.options.map((option, index) => (
            <button
              key={index}
              onClick={() => handleAnswer(index)}
              disabled={isAnswered}
              className={`w-full p-4 rounded-xl border-2 transition-all text-left flex items-center gap-4 ${getOptionStyle(index)}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                isAnswered && index === currentQuestion.correctIndex
                  ? 'bg-green-500 text-white'
                  : isAnswered && selectedAnswer === index
                  ? 'bg-red-500 text-white'
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {String.fromCharCode(65 + index)}
              </div>
              <span className="flex-1">{option}</span>
              {isAnswered && index === currentQuestion.correctIndex && (
                <CheckCircle className="w-6 h-6 text-green-500" />
              )}
              {isAnswered && selectedAnswer === index && index !== currentQuestion.correctIndex && (
                <XCircle className="w-6 h-6 text-red-500" />
              )}
            </button>
          ))}
        </div>

        {/* Hint button */}
        {!isAnswered && currentQuestion.hint && !showHint && (
          <button
            onClick={() => setShowHint(true)}
            className="mt-4 flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm"
          >
            <Lightbulb className="w-4 h-4" />
            Voir un indice (-5 points)
          </button>
        )}

        {showHint && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-yellow-800">{currentQuestion.hint}</p>
          </div>
        )}

        {/* Explanation */}
        {isAnswered && (
          <div className={`mt-6 p-4 rounded-xl ${
            selectedAnswer === currentQuestion.correctIndex
              ? 'bg-green-50 border border-green-200'
              : 'bg-blue-50 border border-blue-200'
          }`}>
            <p className="text-sm text-gray-700">{currentQuestion.explanation}</p>
          </div>
        )}
      </div>

      {/* Next button */}
      {isAnswered && (
        <button
          onClick={nextQuestion}
          className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-bold text-lg hover:shadow-lg transition-all flex items-center justify-center gap-2"
        >
          {isLastQuestion ? 'Voir mes resultats' : 'Question suivante'}
          <ArrowRight className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}

// ============================================================================
// DRAG & DROP CATEGORISATION
// ============================================================================

interface DragDropCategoryProps {
  items: DragDropItem[];
  categories: string[];
  onComplete: (correct: number, total: number) => void;
}

export function DragDropCategory({ items, categories, onComplete }: DragDropCategoryProps) {
  const [availableItems, setAvailableItems] = useState(items);
  const [categoryItems, setCategoryItems] = useState<Record<string, DragDropItem[]>>(() =>
    categories.reduce((acc, cat) => ({ ...acc, [cat]: [] }), {})
  );
  const [draggedItem, setDraggedItem] = useState<DragDropItem | null>(null);
  const [showResults, setShowResults] = useState(false);

  const handleDragStart = (item: DragDropItem) => {
    setDraggedItem(item);
  };

  const handleDrop = (category: string) => {
    if (!draggedItem) return;

    setAvailableItems(prev => prev.filter(i => i.id !== draggedItem.id));
    setCategoryItems(prev => ({
      ...prev,
      [category]: [...prev[category], draggedItem],
    }));
    setDraggedItem(null);
  };

  const handleRemove = (category: string, item: DragDropItem) => {
    setCategoryItems(prev => ({
      ...prev,
      [category]: prev[category].filter(i => i.id !== item.id),
    }));
    setAvailableItems(prev => [...prev, item]);
  };

  const checkAnswers = () => {
    let correct = 0;
    Object.entries(categoryItems).forEach(([category, catItems]) => {
      catItems.forEach(item => {
        if (item.category === category) correct++;
      });
    });
    setShowResults(true);
    onComplete(correct, items.length);
  };

  const reset = () => {
    setAvailableItems(items);
    setCategoryItems(categories.reduce((acc, cat) => ({ ...acc, [cat]: [] }), {}));
    setShowResults(false);
  };

  const isCorrect = (category: string, item: DragDropItem) => item.category === category;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          Classez les elements dans la bonne categorie
        </h3>
        <p className="text-gray-600">Glissez et deposez chaque element</p>
      </div>

      {/* Items a classer */}
      <div className="bg-gray-100 rounded-2xl p-4 mb-6 min-h-[100px]">
        <p className="text-sm text-gray-500 mb-3">Elements a classer :</p>
        <div className="flex flex-wrap gap-2">
          {availableItems.map(item => (
            <div
              key={item.id}
              draggable
              onDragStart={() => handleDragStart(item)}
              className="px-4 py-2 bg-white rounded-xl shadow cursor-grab active:cursor-grabbing border-2 border-transparent hover:border-blue-300 transition-all"
            >
              {item.content}
            </div>
          ))}
          {availableItems.length === 0 && (
            <p className="text-gray-400 italic">Tous les elements ont ete classes</p>
          )}
        </div>
      </div>

      {/* Categories */}
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        {categories.map(category => (
          <div
            key={category}
            onDragOver={e => e.preventDefault()}
            onDrop={() => handleDrop(category)}
            className={`border-2 border-dashed rounded-2xl p-4 min-h-[150px] transition-colors ${
              draggedItem ? 'border-blue-400 bg-blue-50' : 'border-gray-300'
            }`}
          >
            <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-600" />
              {category}
            </h4>
            <div className="space-y-2">
              {categoryItems[category].map(item => (
                <div
                  key={item.id}
                  className={`px-4 py-2 rounded-xl flex items-center justify-between ${
                    showResults
                      ? isCorrect(category, item)
                        ? 'bg-green-100 border border-green-300'
                        : 'bg-red-100 border border-red-300'
                      : 'bg-white border border-gray-200'
                  }`}
                >
                  <span>{item.content}</span>
                  {showResults ? (
                    isCorrect(category, item) ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-600" />
                    )
                  ) : (
                    <button
                      onClick={() => handleRemove(category, item)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <XCircle className="w-5 h-5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex justify-center gap-4">
        {!showResults ? (
          <button
            onClick={checkAnswers}
            disabled={availableItems.length > 0}
            className={`px-8 py-3 rounded-xl font-bold transition-all ${
              availableItems.length > 0
                ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:shadow-lg'
            }`}
          >
            Verifier mes reponses
          </button>
        ) : (
          <button
            onClick={reset}
            className="px-8 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-all flex items-center gap-2"
          >
            <RotateCcw className="w-5 h-5" />
            Recommencer
          </button>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// JEU D'ASSOCIATION (MATCHING)
// ============================================================================

interface MatchingGameProps {
  pairs: MatchPair[];
  onComplete: (time: number, errors: number) => void;
}

export function MatchingGame({ pairs, onComplete }: MatchingGameProps) {
  const [leftSelected, setLeftSelected] = useState<string | null>(null);
  const [rightSelected, setRightSelected] = useState<string | null>(null);
  const [matched, setMatched] = useState<string[]>([]);
  const [errors, setErrors] = useState(0);
  const [startTime] = useState(Date.now());
  const [shuffledRight, setShuffledRight] = useState<MatchPair[]>([]);

  useEffect(() => {
    setShuffledRight([...pairs].sort(() => Math.random() - 0.5));
  }, [pairs]);

  useEffect(() => {
    if (leftSelected && rightSelected) {
      const leftPair = pairs.find(p => p.id === leftSelected);
      const isMatch = leftPair?.right === pairs.find(p => p.id === rightSelected)?.right;

      if (isMatch) {
        setMatched(prev => [...prev, leftSelected, rightSelected]);
        if (matched.length + 2 === pairs.length * 2) {
          onComplete(Math.round((Date.now() - startTime) / 1000), errors);
        }
      } else {
        setErrors(prev => prev + 1);
      }

      setTimeout(() => {
        setLeftSelected(null);
        setRightSelected(null);
      }, 500);
    }
  }, [leftSelected, rightSelected]);

  const isMatched = (id: string) => matched.includes(id);

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          Associez les elements correspondants
        </h3>
        <div className="flex justify-center gap-6 text-sm">
          <span className="text-gray-600">
            Erreurs: <span className="font-bold text-red-600">{errors}</span>
          </span>
          <span className="text-gray-600">
            Trouves: <span className="font-bold text-green-600">{matched.length / 2}/{pairs.length}</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Colonne gauche */}
        <div className="space-y-3">
          {pairs.map(pair => (
            <button
              key={pair.id}
              onClick={() => !isMatched(pair.id) && setLeftSelected(pair.id)}
              disabled={isMatched(pair.id)}
              className={`w-full p-4 rounded-xl text-left transition-all ${
                isMatched(pair.id)
                  ? 'bg-green-100 border-2 border-green-300 text-green-700'
                  : leftSelected === pair.id
                  ? 'bg-blue-100 border-2 border-blue-500 shadow-lg'
                  : 'bg-white border-2 border-gray-200 hover:border-blue-300'
              }`}
            >
              {pair.left}
            </button>
          ))}
        </div>

        {/* Colonne droite */}
        <div className="space-y-3">
          {shuffledRight.map(pair => (
            <button
              key={pair.id + '-right'}
              onClick={() => !isMatched(pair.id) && setRightSelected(pair.id)}
              disabled={isMatched(pair.id)}
              className={`w-full p-4 rounded-xl text-left transition-all ${
                isMatched(pair.id)
                  ? 'bg-green-100 border-2 border-green-300 text-green-700'
                  : rightSelected === pair.id
                  ? 'bg-purple-100 border-2 border-purple-500 shadow-lg'
                  : 'bg-white border-2 border-gray-200 hover:border-purple-300'
              }`}
            >
              {pair.right}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// SIMULATION INTERACTIVE
// ============================================================================

interface SimulationProps {
  title: string;
  description: string;
  steps: SimulationStep[];
  onComplete: () => void;
}

export function InteractiveSimulation({ title, description, steps, onComplete }: SimulationProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [completed, setCompleted] = useState<boolean[]>(new Array(steps.length).fill(false));
  const [showHint, setShowHint] = useState(false);
  const [inputValue, setInputValue] = useState('');

  const step = steps[currentStep];
  const progress = (completed.filter(Boolean).length / steps.length) * 100;

  const handleAction = (value?: any) => {
    if (step.validation(value || inputValue)) {
      const newCompleted = [...completed];
      newCompleted[currentStep] = true;
      setCompleted(newCompleted);

      if (currentStep < steps.length - 1) {
        setTimeout(() => {
          setCurrentStep(prev => prev + 1);
          setInputValue('');
          setShowHint(false);
        }, 500);
      } else {
        onComplete();
      }
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 text-white mb-6">
        <h3 className="text-xl font-bold mb-2">{title}</h3>
        <p className="text-white/80">{description}</p>
      </div>

      {/* Progress */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progression</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Steps indicator */}
      <div className="flex items-center justify-center gap-2 mb-8">
        {steps.map((_, index) => (
          <div
            key={index}
            className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all ${
              completed[index]
                ? 'bg-green-500 text-white'
                : index === currentStep
                ? 'bg-blue-600 text-white ring-4 ring-blue-200'
                : 'bg-gray-200 text-gray-500'
            }`}
          >
            {completed[index] ? <CheckCircle className="w-5 h-5" /> : index + 1}
          </div>
        ))}
      </div>

      {/* Current step */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <MousePointer className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h4 className="font-bold text-gray-900 mb-1">Etape {currentStep + 1}</h4>
            <p className="text-gray-600">{step.instruction}</p>
          </div>
        </div>

        {/* Interactive area based on action type */}
        {step.action === 'type' && (
          <div className="mb-4">
            <input
              type="text"
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              placeholder="Tapez votre reponse..."
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              onKeyPress={e => e.key === 'Enter' && handleAction()}
            />
          </div>
        )}

        {step.action === 'click' && (
          <div className="flex justify-center mb-4">
            <button
              onClick={() => handleAction(true)}
              className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-bold hover:shadow-lg transition-all animate-pulse"
            >
              {step.targetElement}
            </button>
          </div>
        )}

        {step.action === 'select' && (
          <div className="grid grid-cols-2 gap-3 mb-4">
            {['Option A', 'Option B', 'Option C', 'Option D'].map((opt, i) => (
              <button
                key={i}
                onClick={() => handleAction(opt)}
                className="p-3 bg-gray-100 rounded-xl hover:bg-blue-100 hover:border-blue-300 border-2 border-transparent transition-all"
              >
                {opt}
              </button>
            ))}
          </div>
        )}

        {/* Hint */}
        {!showHint ? (
          <button
            onClick={() => setShowHint(true)}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm"
          >
            <HelpCircle className="w-4 h-4" />
            Besoin d'aide ?
          </button>
        ) : (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-xl flex items-start gap-3">
            <Lightbulb className="w-5 h-5 text-yellow-600 flex-shrink-0" />
            <p className="text-sm text-yellow-800">{step.hint}</p>
          </div>
        )}
      </div>

      {/* Action button for type action */}
      {step.action === 'type' && (
        <button
          onClick={() => handleAction()}
          className="w-full mt-4 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-bold hover:shadow-lg transition-all"
        >
          Valider
        </button>
      )}
    </div>
  );
}

// ============================================================================
// MEMORY GAME (CONCENTRATION)
// ============================================================================

interface MemoryCard {
  id: number;
  content: string;
  pairId: number;
}

interface MemoryGameProps {
  cards: { id: number; content: string }[];
  onComplete: (moves: number, time: number) => void;
}

export function MemoryGame({ cards, onComplete }: MemoryGameProps) {
  const [gameCards, setGameCards] = useState<MemoryCard[]>([]);
  const [flipped, setFlipped] = useState<number[]>([]);
  const [matched, setMatched] = useState<number[]>([]);
  const [moves, setMoves] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [gameComplete, setGameComplete] = useState(false);

  useEffect(() => {
    // Create pairs and shuffle
    const pairs: MemoryCard[] = [];
    cards.forEach((card, index) => {
      pairs.push({ ...card, pairId: index, id: index * 2 });
      pairs.push({ ...card, pairId: index, id: index * 2 + 1 });
    });
    setGameCards(pairs.sort(() => Math.random() - 0.5));
  }, [cards]);

  const handleCardClick = (id: number) => {
    if (!startTime) setStartTime(Date.now());
    if (flipped.length === 2 || flipped.includes(id) || matched.includes(id)) return;

    const newFlipped = [...flipped, id];
    setFlipped(newFlipped);

    if (newFlipped.length === 2) {
      setMoves(prev => prev + 1);
      const [first, second] = newFlipped;
      const firstCard = gameCards.find(c => c.id === first);
      const secondCard = gameCards.find(c => c.id === second);

      if (firstCard?.pairId === secondCard?.pairId) {
        setMatched(prev => [...prev, first, second]);
        setFlipped([]);

        if (matched.length + 2 === gameCards.length) {
          setGameComplete(true);
          onComplete(moves + 1, Math.round((Date.now() - (startTime || Date.now())) / 1000));
        }
      } else {
        setTimeout(() => setFlipped([]), 1000);
      }
    }
  };

  const resetGame = () => {
    setGameCards(prev => [...prev].sort(() => Math.random() - 0.5));
    setFlipped([]);
    setMatched([]);
    setMoves(0);
    setStartTime(null);
    setGameComplete(false);
  };

  return (
    <div className="max-w-lg mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-gray-900">Jeu de Memoire</h3>
        <div className="flex gap-4 text-sm">
          <span className="text-gray-600">
            Coups: <span className="font-bold">{moves}</span>
          </span>
          <button
            onClick={resetGame}
            className="flex items-center gap-1 text-blue-600 hover:text-blue-700"
          >
            <RotateCcw className="w-4 h-4" />
            Recommencer
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3">
        {gameCards.map(card => {
          const isFlipped = flipped.includes(card.id) || matched.includes(card.id);
          const isMatched = matched.includes(card.id);

          return (
            <button
              key={card.id}
              onClick={() => handleCardClick(card.id)}
              className={`aspect-square rounded-xl text-2xl font-bold transition-all transform ${
                isFlipped
                  ? isMatched
                    ? 'bg-green-100 border-2 border-green-400 scale-95'
                    : 'bg-blue-100 border-2 border-blue-400'
                  : 'bg-gradient-to-br from-purple-500 to-pink-500 hover:scale-105 hover:shadow-lg'
              }`}
              style={{
                perspective: '1000px',
              }}
            >
              {isFlipped ? (
                <span>{card.content}</span>
              ) : (
                <span className="text-white">?</span>
              )}
            </button>
          );
        })}
      </div>

      {gameComplete && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-xl text-center">
          <Trophy className="w-12 h-12 text-yellow-500 mx-auto mb-2" />
          <p className="font-bold text-green-700">Bravo ! Termine en {moves} coups !</p>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  AnimatedQuiz,
  DragDropCategory,
  MatchingGame,
  InteractiveSimulation,
  MemoryGame,
};
