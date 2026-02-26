/**
 * AZALSCORE - Affichage des résultats d'examen
 * ==============================================
 */

import React, { useState } from 'react';
import {
  Trophy,
  Target,
  Star,
  X,
  CheckCircle,
  AlertTriangle,
  Lightbulb,
  BookOpen,
  BarChart3,
  Rocket,
  Brain,
} from 'lucide-react';
import type { ExamQuestion, ExamGrade } from '../types';
import { GRADE_THRESHOLDS } from '../constants';

interface ExamResultsDisplayProps {
  result: {
    passed: boolean;
    grade: ExamGrade;
    percentage: number;
    correctAnswers: number;
    totalQuestions: number;
    xpEarned: number;
    examLevel?: number;
  };
  questions: ExamQuestion[];
  answers: (number | null)[];
  onClose: () => void;
}

type ActiveTab = 'summary' | 'errors' | 'all';

/**
 * Affichage détaillé des résultats d'examen avec analyse des erreurs
 */
export function ExamResultsDisplay({
  result,
  questions,
  answers,
  onClose,
}: ExamResultsDisplayProps) {
  const [activeTab, setActiveTab] = useState<ActiveTab>('errors');
  const gradeInfo = GRADE_THRESHOLDS.find(g => g.grade === result.grade)!;

  // Séparer les réponses correctes et incorrectes
  const incorrectAnswers = questions
    .map((q, i) => ({ question: q, index: i, userAnswer: answers[i] }))
    .filter(item => item.userAnswer !== item.question.correctAnswer);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header avec note */}
        <div
          className={`relative p-6 text-center text-white bg-gradient-to-br ${gradeInfo.color} flex-shrink-0`}
        >
          {result.passed && <ConfettiEffect />}

          <div className="relative flex items-center justify-center gap-8">
            <div>
              {result.passed ? (
                <Trophy className="w-12 h-12 mx-auto mb-2" />
              ) : (
                <Target className="w-12 h-12 mx-auto mb-2" />
              )}
              <div className="text-6xl font-black drop-shadow-lg">{result.grade}</div>
              <div className="text-xl font-bold">{gradeInfo.label}</div>
            </div>

            <div className="text-left">
              <div className="text-white/90 mb-2">
                <span className="text-3xl font-bold">{result.percentage}%</span>
                <span className="text-lg ml-2">de réussite</span>
              </div>
              <div className="flex gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`w-6 h-6 ${
                      i < gradeInfo.stars
                        ? 'text-yellow-300 fill-yellow-300'
                        : 'text-white/30'
                    }`}
                  />
                ))}
              </div>
              <div className="mt-2 text-white/80 text-sm">
                {result.correctAnswers} / {result.totalQuestions} réponses correctes
              </div>
            </div>
          </div>
        </div>

        {/* Statistiques rapides */}
        <div className="grid grid-cols-4 gap-2 p-4 bg-gray-50 border-b flex-shrink-0">
          <StatBlock value={result.correctAnswers} label="Correctes" color="text-green-600" />
          <StatBlock value={incorrectAnswers.length} label="Incorrectes" color="text-red-600" />
          <StatBlock
            value={answers.filter(a => a === null).length}
            label="Sans réponse"
            color="text-gray-600"
          />
          <StatBlock value={`+${result.xpEarned}`} label="XP gagnés" color="text-amber-600" />
        </div>

        {/* Tabs */}
        <div className="flex border-b flex-shrink-0">
          <TabButton
            active={activeTab === 'errors'}
            onClick={() => setActiveTab('errors')}
            icon={<X className="w-4 h-4" />}
            label={`Erreurs (${incorrectAnswers.length})`}
            color="red"
          />
          <TabButton
            active={activeTab === 'all'}
            onClick={() => setActiveTab('all')}
            icon={<BookOpen className="w-4 h-4" />}
            label={`Toutes (${questions.length})`}
            color="blue"
          />
          <TabButton
            active={activeTab === 'summary'}
            onClick={() => setActiveTab('summary')}
            icon={<BarChart3 className="w-4 h-4" />}
            label="Résumé"
            color="green"
          />
        </div>

        {/* Contenu scrollable */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'summary' && (
            <SummaryTab result={result} questions={questions} answers={answers} incorrectAnswers={incorrectAnswers} />
          )}
          {activeTab === 'errors' && (
            <ErrorsTab incorrectAnswers={incorrectAnswers} />
          )}
          {activeTab === 'all' && (
            <AllAnswersTab questions={questions} answers={answers} />
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 p-4 border-t flex-shrink-0">
          <button
            onClick={onClose}
            className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
          >
            {result.passed ? 'Continuer' : 'Fermer et réviser'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// SOUS-COMPOSANTS
// ============================================================================

function ConfettiEffect() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {[...Array(30)].map((_, i) => (
        <div
          key={i}
          className="absolute w-2 h-2 animate-confetti rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 2}s`,
            backgroundColor: ['#FFD700', '#FFF', '#87CEEB', '#98FB98'][
              Math.floor(Math.random() * 4)
            ],
          }}
        />
      ))}
    </div>
  );
}

interface StatBlockProps {
  value: number | string;
  label: string;
  color: string;
}

function StatBlock({ value, label, color }: StatBlockProps) {
  return (
    <div className="text-center">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  color: string;
}

function TabButton({ active, onClick, icon, label, color }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 ${
        active
          ? `text-${color}-600 border-b-2 border-${color}-600 bg-${color}-50`
          : 'text-gray-500'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

interface SummaryTabProps {
  result: ExamResultsDisplayProps['result'];
  questions: ExamQuestion[];
  answers: (number | null)[];
  incorrectAnswers: Array<{ question: ExamQuestion; index: number; userAnswer: number | null }>;
}

function SummaryTab({ result, questions, answers, incorrectAnswers }: SummaryTabProps) {
  return (
    <div className="space-y-4">
      {/* Message principal */}
      <div
        className={`p-4 rounded-xl ${
          result.passed
            ? 'bg-green-50 border border-green-200'
            : 'bg-amber-50 border border-amber-200'
        }`}
      >
        {result.passed ? (
          <div className="flex items-center gap-3">
            <Rocket className="w-10 h-10 text-green-600" />
            <div>
              <h4 className="font-bold text-green-800">Félicitations !</h4>
              <p className="text-green-700">
                {result.examLevel
                  ? `Vous avez réussi l'examen et passez au niveau ${result.examLevel} !`
                  : 'Excellent travail ! Vous maîtrisez bien ce sujet.'}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <Brain className="w-10 h-10 text-amber-600" />
            <div>
              <h4 className="font-bold text-amber-800">Continuez vos efforts !</h4>
              <p className="text-amber-700">
                Consultez les erreurs ci-dessous pour comprendre vos points faibles.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Répartition par difficulté */}
      <div className="bg-white rounded-xl border p-4">
        <h4 className="font-semibold text-gray-900 mb-3">Répartition par difficulté</h4>
        {(['facile', 'moyen', 'difficile'] as const).map(diff => {
          const diffQuestions = questions.filter(q => q.difficulty === diff);
          const diffCorrect = diffQuestions.filter((q) => {
            const idx = questions.indexOf(q);
            return answers[idx] === q.correctAnswer;
          }).length;
          const percentage =
            diffQuestions.length > 0
              ? Math.round((diffCorrect / diffQuestions.length) * 100)
              : 0;

          return (
            <div key={diff} className="mb-3 last:mb-0">
              <div className="flex justify-between text-sm mb-1">
                <span
                  className={`font-medium ${
                    diff === 'facile'
                      ? 'text-green-700'
                      : diff === 'moyen'
                      ? 'text-amber-700'
                      : 'text-red-700'
                  }`}
                >
                  {diff.charAt(0).toUpperCase() + diff.slice(1)}
                </span>
                <span className="text-gray-600">
                  {diffCorrect}/{diffQuestions.length} ({percentage}%)
                </span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    diff === 'facile'
                      ? 'bg-green-500'
                      : diff === 'moyen'
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Points à réviser */}
      {incorrectAnswers.length > 0 && (
        <div className="bg-red-50 rounded-xl border border-red-200 p-4">
          <h4 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Points à réviser
          </h4>
          <ul className="space-y-2">
            {incorrectAnswers.slice(0, 5).map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-red-700">
                <span className="text-red-400">•</span>
                {item.question.question.substring(0, 60)}...
              </li>
            ))}
            {incorrectAnswers.length > 5 && (
              <li className="text-sm text-red-600 font-medium">
                + {incorrectAnswers.length - 5} autres erreurs
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

interface ErrorsTabProps {
  incorrectAnswers: Array<{ question: ExamQuestion; index: number; userAnswer: number | null }>;
}

function ErrorsTab({ incorrectAnswers }: ErrorsTabProps) {
  if (incorrectAnswers.length === 0) {
    return (
      <div className="text-center py-12">
        <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
        <h3 className="text-xl font-bold text-gray-900">Parfait !</h3>
        <p className="text-gray-600">Aucune erreur - Vous avez tout juste !</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4">
        <h3 className="font-bold text-red-800 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          {incorrectAnswers.length} erreur{incorrectAnswers.length > 1 ? 's' : ''} à comprendre
        </h3>
        <p className="text-red-700 text-sm mt-1">
          Lisez attentivement les explications pour chaque erreur afin de progresser.
        </p>
      </div>

      {incorrectAnswers.map((item, idx) => (
        <QuestionErrorCard key={item.question.id} item={item} idx={idx} />
      ))}
    </div>
  );
}

interface QuestionErrorCardProps {
  item: { question: ExamQuestion; index: number; userAnswer: number | null };
  idx: number;
}

function QuestionErrorCard({ item, idx }: QuestionErrorCardProps) {
  return (
    <div className="bg-white rounded-xl border-2 border-red-200 overflow-hidden">
      {/* Question header */}
      <div className="bg-red-50 p-4 border-b border-red-200">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center font-bold text-sm">
              {idx + 1}
            </span>
            <span
              className={`text-xs px-2 py-1 rounded-full ${
                item.question.difficulty === 'facile'
                  ? 'bg-green-100 text-green-700'
                  : item.question.difficulty === 'moyen'
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-red-100 text-red-700'
              }`}
            >
              {item.question.difficulty}
            </span>
          </div>
          <span className="text-sm text-red-600 font-medium">
            {item.question.points} pts perdus
          </span>
        </div>
        <h4 className="font-semibold text-gray-900 mt-2">{item.question.question}</h4>
      </div>

      {/* Réponses */}
      <div className="p-4 space-y-2">
        {item.question.options.map((option, optIdx) => {
          const isUserAnswer = item.userAnswer === optIdx;
          const isCorrect = item.question.correctAnswer === optIdx;

          return (
            <div
              key={optIdx}
              className={`p-3 rounded-lg flex items-center gap-3 ${
                isCorrect
                  ? 'bg-green-100 border-2 border-green-500'
                  : isUserAnswer
                  ? 'bg-red-100 border-2 border-red-500'
                  : 'bg-gray-50 border border-gray-200'
              }`}
            >
              <span
                className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold ${
                  isCorrect
                    ? 'bg-green-500 text-white'
                    : isUserAnswer
                    ? 'bg-red-500 text-white'
                    : 'bg-gray-300 text-gray-600'
                }`}
              >
                {String.fromCharCode(65 + optIdx)}
              </span>
              <span
                className={`flex-1 ${
                  isCorrect
                    ? 'text-green-800 font-medium'
                    : isUserAnswer
                    ? 'text-red-800'
                    : 'text-gray-700'
                }`}
              >
                {option}
              </span>
              {isCorrect && <CheckCircle className="w-5 h-5 text-green-600" />}
              {isUserAnswer && !isCorrect && <X className="w-5 h-5 text-red-600" />}
            </div>
          );
        })}
      </div>

      {/* Explication */}
      <div className="bg-blue-50 p-4 border-t border-blue-200">
        <div className="flex items-start gap-3">
          <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h5 className="font-semibold text-blue-800 mb-1">Explication</h5>
            <p className="text-blue-700 text-sm">{item.question.explanation}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

interface AllAnswersTabProps {
  questions: ExamQuestion[];
  answers: (number | null)[];
}

function AllAnswersTab({ questions, answers }: AllAnswersTabProps) {
  return (
    <div className="space-y-3">
      {questions.map((q, index) => {
        const isCorrect = answers[index] === q.correctAnswer;
        const userAnswer = answers[index];

        return (
          <div
            key={q.id}
            className={`rounded-xl border-2 overflow-hidden ${
              isCorrect ? 'border-green-300 bg-green-50' : 'border-red-300 bg-red-50'
            }`}
          >
            <div className="p-3 flex items-start gap-3">
              <div
                className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                  isCorrect ? 'bg-green-500' : 'bg-red-500'
                }`}
              >
                {isCorrect ? (
                  <CheckCircle className="w-5 h-5 text-white" />
                ) : (
                  <X className="w-5 h-5 text-white" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 text-sm">{q.question}</p>
                <div className="mt-2 text-sm">
                  <p className={isCorrect ? 'text-green-700' : 'text-red-700'}>
                    <span className="text-gray-500">Votre réponse: </span>
                    {userAnswer !== null ? q.options[userAnswer] : 'Non répondu'}
                  </p>
                  {!isCorrect && (
                    <p className="text-green-700 mt-1">
                      <span className="text-gray-500">Bonne réponse: </span>
                      {q.options[q.correctAnswer]}
                    </p>
                  )}
                </div>
                {!isCorrect && (
                  <p className="mt-2 text-xs text-blue-600 bg-blue-100 p-2 rounded">
                    <Lightbulb className="w-3 h-3 inline mr-1" />
                    {q.explanation}
                  </p>
                )}
              </div>
              <span className="text-xs text-gray-500">{q.points} pts</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default ExamResultsDisplay;
