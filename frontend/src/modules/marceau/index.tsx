/**
 * AZALSCORE - Module Marceau AI Assistant
 * ========================================
 * Interface conversationnelle intuitive pour l'agent IA Marceau.
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Bot, Send, Phone, FileText, Calendar, Users, Headphones,
  TrendingUp, Settings, ChevronRight, Loader2, Sparkles,
  MessageSquare, Activity, Brain, CheckCircle2, AlertTriangle,
  Zap, Clock, BarChart3, RotateCcw
} from 'lucide-react';
import {
  marceauKeys,
  useMarceauDashboard,
  useSendMarceauMessage,
  type DashboardStats,
} from './hooks';

// Types
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  intent?: string;
  action?: {
    type: string;
    status: 'pending' | 'completed' | 'failed';
    details?: string;
  };
}

interface QuickAction {
  icon: React.ReactNode;
  label: string;
  prompt: string;
  color: string;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    icon: <FileText size={18} />,
    label: 'Creer un devis',
    prompt: 'Je voudrais creer un devis pour un client',
    color: 'bg-blue-500',
  },
  {
    icon: <Calendar size={18} />,
    label: 'Planifier un RDV',
    prompt: 'Je dois planifier un rendez-vous',
    color: 'bg-green-500',
  },
  {
    icon: <Headphones size={18} />,
    label: 'Creer un ticket',
    prompt: 'Je dois creer un ticket de support',
    color: 'bg-purple-500',
  },
  {
    icon: <Users size={18} />,
    label: 'Relancer un client',
    prompt: 'Je voudrais relancer un client pour un devis en attente',
    color: 'bg-orange-500',
  },
];

const CAPABILITIES = [
  { icon: <Phone size={16} />, label: 'Telephonie', desc: 'Gestion des appels et messages' },
  { icon: <FileText size={16} />, label: 'Commercial', desc: 'Devis, factures, relances' },
  { icon: <Headphones size={16} />, label: 'Support', desc: 'Tickets et assistance client' },
  { icon: <TrendingUp size={16} />, label: 'Marketing', desc: 'Campagnes et newsletters' },
  { icon: <BarChart3 size={16} />, label: 'Comptabilite', desc: 'Factures et rapprochements' },
  { icon: <Brain size={16} />, label: 'Et plus...', desc: 'SEO, RH, juridique' },
];

export default function MarceauModule() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [showStats, setShowStats] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // React Query hooks
  const { data: stats } = useMarceauDashboard();
  const sendMessageMutation = useSendMarceauMessage();
  const sending = sendMessageMutation.isPending;

  // Derive config status from stats
  const configStatus: 'loading' | 'configured' | 'needs_config' =
    stats === undefined ? 'loading' :
    stats?.llm_configured ? 'configured' : 'needs_config';

  // Update showStats when stats load
  useEffect(() => {
    if (stats?.total_actions_today && stats.total_actions_today > 0) {
      setShowStats(true);
    }
  }, [stats]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Add welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: 'welcome',
        role: 'system',
        content: 'welcome',
        timestamp: new Date(),
      }]);
    }
  }, []);

  const sendMessage = async (messageText?: string) => {
    const text = messageText || input.trim();
    if (!text || sending) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => prev.filter(m => m.role !== 'system').concat(userMessage));
    setInput('');

    try {
      const response = await sendMessageMutation.mutateAsync({
        message: text,
        conversation_id: conversationId,
      });

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response?.message || 'Je suis desole, je n\'ai pas pu traiter votre demande.',
        timestamp: new Date(),
        intent: response?.intent || undefined,
        action: response?.action_created ? {
          type: response.action_created.action_type,
          status: response.action_created.status as 'pending' | 'completed' | 'failed',
        } : undefined,
      };

      setMessages(prev => [...prev, assistantMessage]);
      setConversationId(response?.conversation_id || null);

    } catch {
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Desole, je rencontre une difficulte technique. Verifiez que les APIs sont configurees dans Administration > Marceau.',
        timestamp: new Date(),
      }]);
    } finally {
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleQuickAction = (action: QuickAction) => {
    sendMessage(action.prompt);
  };

  const resetConversation = () => {
    setMessages([{
      id: 'welcome',
      role: 'system',
      content: 'welcome',
      timestamp: new Date(),
    }]);
    setConversationId(null);
    setInput('');
  };

  // Check if we have an active conversation (more than just welcome message)
  const hasActiveConversation = messages.some(m => m.role === 'user' || (m.role === 'assistant' && m.id !== 'welcome'));

  return (
    <div className="azals-page">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
                <Bot className="text-white" size={28} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Marceau</h1>
                <p className="text-gray-500">Votre assistant IA pour automatiser vos taches metier</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {configStatus === 'needs_config' && (
                <a
                  href="/admin/marceau"
                  className="flex items-center gap-2 px-3 py-2 bg-amber-50 text-amber-700 rounded-lg border border-amber-200 text-sm hover:bg-amber-100 transition-colors"
                >
                  <AlertTriangle size={16} />
                  Configurer les APIs
                </a>
              )}
              {configStatus === 'configured' && (
                <span className="flex items-center gap-2 px-3 py-2 bg-green-50 text-green-700 rounded-lg text-sm">
                  <CheckCircle2 size={16} />
                  IA connectee {stats?.llm_provider && `(${stats.llm_provider})`}
                </span>
              )}
              <a
                href="/admin/marceau"
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                title="Configuration"
              >
                <Settings size={20} />
              </a>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Chat Area */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
              {/* Chat Messages */}
              <div className="h-[500px] overflow-y-auto p-6">
                {messages.map((msg) => (
                  <div key={msg.id} className="mb-4">
                    {msg.role === 'system' && msg.content === 'welcome' ? (
                      // Welcome Message
                      <div className="text-center py-8">
                        <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                          <Sparkles className="text-white" size={36} />
                        </div>
                        <h2 className="text-xl font-semibold text-gray-900 mb-2">
                          Bonjour ! Je suis Marceau
                        </h2>
                        <p className="text-gray-500 max-w-md mx-auto mb-6">
                          Votre assistant IA pour automatiser vos taches commerciales,
                          support client, marketing et plus encore.
                        </p>

                        {/* Quick Actions */}
                        <div className="grid grid-cols-2 gap-3 max-w-lg mx-auto">
                          {QUICK_ACTIONS.map((action, i) => (
                            <button
                              key={i}
                              onClick={() => handleQuickAction(action)}
                              className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-xl text-left transition-colors group"
                            >
                              <div className={`w-10 h-10 ${action.color} rounded-lg flex items-center justify-center text-white`}>
                                {action.icon}
                              </div>
                              <span className="font-medium text-gray-700 group-hover:text-gray-900">
                                {action.label}
                              </span>
                              <ChevronRight size={16} className="ml-auto text-gray-400 group-hover:text-gray-600" />
                            </button>
                          ))}
                        </div>

                        <p className="text-sm text-gray-400 mt-6">
                          Ou ecrivez votre demande ci-dessous
                        </p>
                      </div>
                    ) : msg.role === 'user' ? (
                      // User Message
                      <div className="flex justify-end">
                        <div className="max-w-[80%] bg-blue-600 text-white px-4 py-3 rounded-2xl rounded-br-md">
                          {msg.content}
                        </div>
                      </div>
                    ) : (
                      // Assistant Message
                      <div className="flex gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center flex-shrink-0">
                          <Bot size={16} className="text-white" />
                        </div>
                        <div className="flex-1">
                          <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-tl-md max-w-[90%]">
                            {msg.content}
                          </div>
                          {msg.action && (
                            <div className="mt-2 flex items-center gap-2 text-sm">
                              <Zap size={14} className="text-blue-500" />
                              <span className="text-gray-600">
                                Action: {msg.action.type}
                              </span>
                              <span className={`px-2 py-0.5 rounded-full text-xs ${
                                msg.action.status === 'completed'
                                  ? 'bg-green-100 text-green-700'
                                  : msg.action.status === 'failed'
                                  ? 'bg-red-100 text-red-700'
                                  : 'bg-amber-100 text-amber-700'
                              }`}>
                                {msg.action.status === 'completed' ? 'Termine' :
                                 msg.action.status === 'failed' ? 'Echec' : 'En attente'}
                              </span>
                            </div>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            {msg.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* Typing indicator */}
                {sending && (
                  <div className="flex gap-3 mb-4">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                      <Bot size={16} className="text-white" />
                    </div>
                    <div className="bg-gray-100 rounded-2xl rounded-tl-md px-4 py-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t p-4 bg-gray-50">
                <div className="flex gap-3">
                  {hasActiveConversation && (
                    <button
                      onClick={resetConversation}
                      className="px-3 py-3 bg-white border border-gray-300 text-gray-600 rounded-xl hover:bg-gray-100 hover:text-gray-900 transition-colors flex items-center gap-2"
                      title="Nouvelle conversation"
                    >
                      <RotateCcw size={20} />
                      <span className="hidden md:inline">Nouveau</span>
                    </button>
                  )}
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ecrivez votre message..."
                    disabled={sending}
                    className="flex-1 px-4 py-3 bg-white border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  />
                  <button
                    onClick={() => sendMessage()}
                    disabled={!input.trim() || sending}
                    className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    {sending ? (
                      <Loader2 size={20} className="animate-spin" />
                    ) : (
                      <>
                        <Send size={20} />
                        <span className="hidden sm:inline">Envoyer</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Stats Card */}
            {stats && (
              <div className="bg-white rounded-2xl shadow-sm border p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <Activity size={18} className="text-blue-500" />
                    Activite du jour
                  </h3>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded-xl">
                    <p className="text-2xl font-bold text-blue-600">{stats.total_actions_today}</p>
                    <p className="text-xs text-gray-500">Actions</p>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-xl">
                    <p className="text-2xl font-bold text-green-600">{stats.total_conversations_today}</p>
                    <p className="text-xs text-gray-500">Conversations</p>
                  </div>
                  <div className="text-center p-3 bg-amber-50 rounded-xl">
                    <p className="text-2xl font-bold text-amber-600">{stats.pending_validations}</p>
                    <p className="text-xs text-gray-500">A valider</p>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded-xl">
                    <p className="text-2xl font-bold text-purple-600">
                      {((stats.avg_confidence_score || 0) * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-gray-500">Confiance</p>
                  </div>
                </div>

                {stats.pending_validations > 0 && (
                  <a
                    href="/marceau/actions?status=needs_validation"
                    className="mt-4 flex items-center justify-center gap-2 w-full py-2 bg-amber-100 text-amber-700 rounded-lg text-sm font-medium hover:bg-amber-200 transition-colors"
                  >
                    <Clock size={14} />
                    Voir les actions a valider
                  </a>
                )}
              </div>
            )}

            {/* Capabilities */}
            <div className="bg-white rounded-2xl shadow-sm border p-5">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Sparkles size={18} className="text-purple-500" />
                Ce que je peux faire
              </h3>
              <div className="space-y-3">
                {CAPABILITIES.map((cap, i) => (
                  <div key={i} className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600">
                      {cap.icon}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 text-sm">{cap.label}</p>
                      <p className="text-xs text-gray-500">{cap.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Help */}
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-5 text-white">
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <MessageSquare size={18} />
                Besoin d'aide ?
              </h3>
              <p className="text-sm text-blue-100 mb-3">
                Posez vos questions en langage naturel, Marceau comprend le francais.
              </p>
              <div className="space-y-2 text-sm">
                <p className="text-blue-200">Exemples :</p>
                <ul className="space-y-1 text-blue-100">
                  <li>• "Cree un devis pour Martin SA"</li>
                  <li>• "Quels devis sont en attente ?"</li>
                  <li>• "Planifie un RDV demain 14h"</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Re-export hooks for external use
export {
  marceauKeys,
  useMarceauDashboard,
  useSendMarceauMessage,
} from './hooks';
