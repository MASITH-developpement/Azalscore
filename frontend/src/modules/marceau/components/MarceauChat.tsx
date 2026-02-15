/**
 * AZALSCORE - Marceau Chat Component
 * ====================================
 * Widget de chat flottant pour interagir avec Marceau.
 */

import React, { useState, useRef, useEffect } from 'react';
import { api } from '@core/api-client';
import { MessageSquare, Send, X, Minimize2, Maximize2, Bot, User, Loader2, AlertCircle } from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  intent?: string;
  confidence?: number;
}

interface MarceauChatProps {
  /** Position du widget */
  position?: 'bottom-right' | 'bottom-left';
  /** Afficher par defaut */
  defaultOpen?: boolean;
}

export function MarceauChat({ position = 'bottom-right', defaultOpen = false }: MarceauChatProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  // Initial greeting
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{
        id: 'greeting',
        role: 'assistant',
        content: 'Bonjour ! Je suis Marceau, votre assistant IA. Comment puis-je vous aider ?',
        timestamp: new Date(),
      }]);
    }
  }, [isOpen]);

  const sendMessage = async () => {
    if (!input.trim() || sending) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setSending(true);
    setError(null);

    try {
      const response = await api.post<{
        message: string;
        conversation_id: string;
        intent: string | null;
        confidence: number;
      }>('/marceau/chat/message', {
        message: userMessage.content,
        conversation_id: conversationId,
      });

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date(),
        intent: response.data.intent || undefined,
        confidence: response.data.confidence,
      };

      setMessages(prev => [...prev, assistantMessage]);
      setConversationId(response.data.conversation_id);

    } catch (e: any) {
      setError(e.message || 'Erreur de communication');
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Desole, je rencontre une difficulte technique. Pouvez-vous reformuler ?',
        timestamp: new Date(),
      }]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const positionClasses = position === 'bottom-right'
    ? 'right-4 bottom-4'
    : 'left-4 bottom-4';

  // Closed state - show button only
  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed ${positionClasses} z-50 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all hover:scale-110 flex items-center justify-center`}
        title="Discuter avec Marceau"
      >
        <Bot size={24} />
      </button>
    );
  }

  return (
    <div
      className={`fixed ${positionClasses} z-50 flex flex-col bg-white rounded-lg shadow-2xl border overflow-hidden transition-all ${
        isMinimized ? 'w-80 h-14' : 'w-96 h-[500px]'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-blue-600 text-white">
        <div className="flex items-center gap-2">
          <Bot size={20} />
          <span className="font-medium">Marceau</span>
          <span className="text-xs bg-blue-500 px-2 py-0.5 rounded-full">IA</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 hover:bg-blue-500 rounded transition-colors"
            title={isMinimized ? 'Agrandir' : 'Reduire'}
          >
            {isMinimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-blue-500 rounded transition-colors"
            title="Fermer"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Chat area - hidden when minimized */}
      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.role === 'user' ? 'bg-gray-200' : 'bg-blue-100'
                }`}>
                  {msg.role === 'user' ? (
                    <User size={16} className="text-gray-600" />
                  ) : (
                    <Bot size={16} className="text-blue-600" />
                  )}
                </div>
                <div className={`max-w-[75%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                  <div className={`inline-block px-3 py-2 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {msg.content}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {msg.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                    {msg.intent && (
                      <span className="ml-2 text-blue-400">
                        {msg.intent}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {sending && (
              <div className="flex gap-2">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <Bot size={16} className="text-blue-600" />
                </div>
                <div className="bg-gray-100 rounded-lg px-4 py-2">
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

          {/* Error banner */}
          {error && (
            <div className="px-4 py-2 bg-red-50 border-t border-red-100 text-red-600 text-sm flex items-center gap-2">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          {/* Input */}
          <div className="p-4 border-t">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Posez votre question..."
                disabled={sending}
                className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || sending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {sending ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <Send size={18} />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2 text-center">
              Marceau peut vous aider avec les devis, RDV, et questions metiers.
            </p>
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Hook pour utiliser le chat Marceau depuis n'importe ou
 */
export function useMarceauChat() {
  const [isOpen, setIsOpen] = useState(false);

  const openChat = (initialMessage?: string) => {
    setIsOpen(true);
    if (initialMessage) {
      // Dispatch event to send initial message after chat opens
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('marceau:send', {
          detail: { message: initialMessage }
        }));
      }, 300);
    }
  };

  const closeChat = () => {
    setIsOpen(false);
  };

  return { isOpen, openChat, closeChat };
}
