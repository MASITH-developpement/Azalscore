/**
 * AZALSCORE - Theo AI Panel
 * ==========================
 * Panneau de chat flottant pour l'assistant IA Theo
 * Interface unique pour toute l'assistance IA dans l'ERP
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { clsx } from 'clsx';
import {
  Sparkles,
  X,
  Minimize2,
  Maximize2,
  Send,
  Loader2,
  AlertCircle,
  CheckCircle,
  XCircle,
  MessageSquare,
  Bot,
  User,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import { useTheo, type TheoMessage, type TheoState } from '@core/theo';
import { useFocusTrap } from '../hooks/useFocusTrap';

// ============================================================
// STATE INDICATOR
// ============================================================

const StateIndicator: React.FC<{ state: TheoState }> = ({ state }) => {
  if (state === 'idle') return null;

  const indicators: Record<TheoState, { icon: React.ReactNode; text: string }> = {
    idle: { icon: null, text: '' },
    listening: { icon: <MessageSquare size={14} />, text: 'En écoute...' },
    thinking: { icon: <Loader2 size={14} className="azals-spin" />, text: 'Theo réfléchit...' },
    responding: { icon: <Bot size={14} />, text: 'Theo répond...' },
    clarifying: { icon: <AlertCircle size={14} />, text: 'Clarification requise' },
    error: { icon: <AlertCircle size={14} />, text: 'Erreur' },
  };

  const { icon, text } = indicators[state];

  return (
    <div className="azals-theo-state">
      {icon}
      <span>{text}</span>
    </div>
  );
};

// ============================================================
// MESSAGE COMPONENT
// ============================================================

interface MessageProps {
  message: TheoMessage;
  onConfirm?: (confirmed: boolean) => void;
  showConfirmation?: boolean;
}

const Message: React.FC<MessageProps> = ({ message, onConfirm, showConfirmation }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  const roleModifier = isUser ? 'user' : isSystem ? 'system' : 'theo';

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div
      className={clsx(
        'azals-theo-message',
        `azals-theo-message--${roleModifier}`
      )}
    >
      <div
        className={clsx(
          'azals-theo-message__avatar',
          `azals-theo-message__avatar--${roleModifier}`
        )}
      >
        {isUser ? <User size={16} /> : isSystem ? <AlertCircle size={16} /> : <Bot size={16} />}
      </div>
      <div>
        <div
          className={clsx(
            'azals-theo-message__bubble',
            `azals-theo-message__bubble--${roleModifier}`
          )}
        >
          {message.content}
        </div>
        {showConfirmation && message.metadata?.requires_confirmation && onConfirm && (
          <div className="azals-theo-confirmation">
            <button
              className="azals-theo-confirmation__btn azals-theo-confirmation__btn--yes"
              onClick={() => onConfirm(true)}
            >
              <CheckCircle size={14} />
              Confirmer
            </button>
            <button
              className="azals-theo-confirmation__btn azals-theo-confirmation__btn--no"
              onClick={() => onConfirm(false)}
            >
              <XCircle size={14} />
              Annuler
            </button>
          </div>
        )}
        <div className="azals-theo-message__timestamp">{formatTime(message.timestamp)}</div>
      </div>
    </div>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

export const TheoPanel: React.FC = () => {
  const {
    isOpen,
    isMinimized,
    messages,
    state,
    pendingConfirmation,
    close,
    minimize,
    maximize,
    sendMessage,
    confirmIntent,
    clearMessages,
    endSession,
  } = useTheo();

  const [input, setInput] = useState('');
  const [inputFocused, setInputFocused] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useFocusTrap(panelRef, { enabled: isOpen, onEscape: close });

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || state === 'thinking') return;

    const message = input.trim();
    setInput('');
    await sendMessage(message);
  }, [input, state, sendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewSession = () => {
    endSession();
    // Will auto-start when panel is opened
  };

  if (!isOpen) return null;

  return (
    <div
      ref={panelRef}
      className={clsx(
        'azals-theo-panel',
        isMinimized && 'azals-theo-panel--minimized'
      )}
      role="dialog"
      aria-modal="true"
      aria-label="Assistant IA Theo"
    >
      {/* Header */}
      <div className="azals-theo-header">
        <div className="azals-theo-header__left">
          <div className="azals-theo-header__icon">
            <Sparkles size={18} />
          </div>
          <div>
            <h3 className="azals-theo-header__title">Theo</h3>
            {!isMinimized && (
              <p className="azals-theo-header__subtitle">Assistant IA AZALSCORE</p>
            )}
          </div>
        </div>
        <div className="azals-theo-header__actions">
          {!isMinimized && (
            <>
              <button
                className="azals-theo-header__btn"
                onClick={handleNewSession}
                title="Nouvelle conversation"
                aria-label="Nouvelle conversation"
              >
                <RefreshCw size={16} />
              </button>
              <button
                className="azals-theo-header__btn"
                onClick={clearMessages}
                title="Effacer les messages"
                aria-label="Effacer les messages"
              >
                <Trash2 size={16} />
              </button>
            </>
          )}
          <button
            className="azals-theo-header__btn"
            onClick={isMinimized ? maximize : minimize}
            title={isMinimized ? 'Agrandir' : 'Réduire'}
            aria-label={isMinimized ? 'Agrandir' : 'Réduire'}
          >
            {isMinimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
          </button>
          <button
            className="azals-theo-header__btn"
            onClick={close}
            title="Fermer"
            aria-label="Fermer l'assistant"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Content (hidden when minimized) */}
      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="azals-theo-messages">
            {messages.length === 0 ? (
              <div className="azals-theo-empty">
                <div className="azals-theo-empty__icon">
                  <Bot size={32} />
                </div>
                <p className="azals-theo-empty__title">Bienvenue !</p>
                <p className="azals-theo-empty__description">
                  Posez votre question ou décrivez ce que vous souhaitez faire.
                </p>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <Message
                    key={msg.id}
                    message={msg}
                    onConfirm={confirmIntent}
                    showConfirmation={pendingConfirmation?.id === msg.id}
                  />
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* State Indicator */}
          <StateIndicator state={state} />

          {/* Input Area */}
          <div className="azals-theo-input-area">
            <div
              className={clsx(
                'azals-theo-input-wrapper',
                inputFocused && 'azals-theo-input-wrapper--focused'
              )}
            >
              <textarea
                ref={inputRef}
                className="azals-theo-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setInputFocused(true)}
                onBlur={() => setInputFocused(false)}
                placeholder="Tapez votre message..."
                rows={1}
                disabled={state === 'thinking'}
              />
              <button
                className="azals-theo-send-btn"
                onClick={handleSend}
                disabled={!input.trim() || state === 'thinking'}
                title="Envoyer"
                aria-label="Envoyer le message"
              >
                {state === 'thinking' ? (
                  <Loader2 size={18} className="azals-spin" />
                ) : (
                  <Send size={18} />
                )}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// ============================================================
// CONTAINER (avec store connection)
// ============================================================

export const TheoPanelContainer: React.FC = () => {
  return <TheoPanel />;
};

export default TheoPanel;
