/**
 * AZALSCORE - Theo AI Panel
 * ==========================
 * Panneau de chat flottant pour l'assistant IA Theo
 * Interface unique pour toute l'assistance IA dans l'ERP
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
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
import { clsx } from 'clsx';
import { useTheo, type TheoMessage, type TheoState } from '@core/theo';

// ============================================================
// STYLES (inline pour éviter les conflits)
// ============================================================

const styles = {
  panel: {
    position: 'fixed' as const,
    bottom: '20px',
    right: '20px',
    width: '400px',
    maxHeight: '600px',
    backgroundColor: '#ffffff',
    borderRadius: '16px',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05)',
    display: 'flex',
    flexDirection: 'column' as const,
    zIndex: 9998,
    overflow: 'hidden',
    transition: 'all 0.3s ease',
  },
  panelMinimized: {
    height: '60px',
    maxHeight: '60px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    color: '#ffffff',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  headerIcon: {
    width: '32px',
    height: '32px',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontWeight: 600,
    fontSize: '16px',
    margin: 0,
  },
  headerSubtitle: {
    fontSize: '12px',
    opacity: 0.8,
    margin: 0,
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  headerBtn: {
    width: '32px',
    height: '32px',
    border: 'none',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: '8px',
    color: '#ffffff',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s',
  },
  messages: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '16px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
    maxHeight: '400px',
    minHeight: '200px',
  },
  messageWrapper: {
    display: 'flex',
    gap: '10px',
    maxWidth: '90%',
  },
  messageUser: {
    alignSelf: 'flex-end' as const,
    flexDirection: 'row-reverse' as const,
  },
  messageTheo: {
    alignSelf: 'flex-start' as const,
  },
  messageAvatar: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  avatarUser: {
    backgroundColor: '#e0e7ff',
    color: '#4f46e5',
  },
  avatarTheo: {
    backgroundColor: '#f3e8ff',
    color: '#9333ea',
  },
  avatarSystem: {
    backgroundColor: '#fee2e2',
    color: '#dc2626',
  },
  messageBubble: {
    padding: '12px 16px',
    borderRadius: '16px',
    fontSize: '14px',
    lineHeight: '1.5',
  },
  bubbleUser: {
    backgroundColor: '#4f46e5',
    color: '#ffffff',
    borderBottomRightRadius: '4px',
  },
  bubbleTheo: {
    backgroundColor: '#f3f4f6',
    color: '#1f2937',
    borderBottomLeftRadius: '4px',
  },
  bubbleSystem: {
    backgroundColor: '#fef2f2',
    color: '#991b1b',
    borderBottomLeftRadius: '4px',
  },
  timestamp: {
    fontSize: '11px',
    color: '#9ca3af',
    marginTop: '4px',
  },
  inputArea: {
    padding: '16px',
    borderTop: '1px solid #e5e7eb',
    backgroundColor: '#fafafa',
  },
  inputWrapper: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '10px',
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    border: '2px solid #e5e7eb',
    padding: '8px 12px',
    transition: 'border-color 0.2s',
  },
  inputWrapperFocused: {
    borderColor: '#6366f1',
  },
  input: {
    flex: 1,
    border: 'none',
    outline: 'none',
    fontSize: '14px',
    resize: 'none' as const,
    maxHeight: '100px',
    minHeight: '24px',
    fontFamily: 'inherit',
    backgroundColor: 'transparent',
  },
  sendBtn: {
    width: '36px',
    height: '36px',
    border: 'none',
    backgroundColor: '#4f46e5',
    borderRadius: '10px',
    color: '#ffffff',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s',
    flexShrink: 0,
  },
  sendBtnDisabled: {
    backgroundColor: '#d1d5db',
    cursor: 'not-allowed',
  },
  stateIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    fontSize: '13px',
    color: '#6b7280',
  },
  confirmationBox: {
    display: 'flex',
    gap: '8px',
    marginTop: '8px',
  },
  confirmBtn: {
    padding: '8px 16px',
    border: 'none',
    borderRadius: '8px',
    fontSize: '13px',
    fontWeight: 500,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    transition: 'all 0.2s',
  },
  confirmBtnYes: {
    backgroundColor: '#10b981',
    color: '#ffffff',
  },
  confirmBtnNo: {
    backgroundColor: '#ef4444',
    color: '#ffffff',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 20px',
    textAlign: 'center' as const,
    color: '#6b7280',
  },
  emptyIcon: {
    width: '64px',
    height: '64px',
    backgroundColor: '#f3e8ff',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '16px',
    color: '#9333ea',
  },
};

// ============================================================
// STATE INDICATOR
// ============================================================

const StateIndicator: React.FC<{ state: TheoState }> = ({ state }) => {
  if (state === 'idle') return null;

  const indicators: Record<TheoState, { icon: React.ReactNode; text: string }> = {
    idle: { icon: null, text: '' },
    listening: { icon: <MessageSquare size={14} />, text: 'En écoute...' },
    thinking: { icon: <Loader2 size={14} className="animate-spin" />, text: 'Theo réfléchit...' },
    responding: { icon: <Bot size={14} />, text: 'Theo répond...' },
    clarifying: { icon: <AlertCircle size={14} />, text: 'Clarification requise' },
    error: { icon: <AlertCircle size={14} />, text: 'Erreur' },
  };

  const { icon, text } = indicators[state];

  return (
    <div style={styles.stateIndicator}>
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

  const wrapperStyle = {
    ...styles.messageWrapper,
    ...(isUser ? styles.messageUser : styles.messageTheo),
  };

  const avatarStyle = {
    ...styles.messageAvatar,
    ...(isUser ? styles.avatarUser : isSystem ? styles.avatarSystem : styles.avatarTheo),
  };

  const bubbleStyle = {
    ...styles.messageBubble,
    ...(isUser ? styles.bubbleUser : isSystem ? styles.bubbleSystem : styles.bubbleTheo),
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div style={wrapperStyle}>
      <div style={avatarStyle}>
        {isUser ? <User size={16} /> : isSystem ? <AlertCircle size={16} /> : <Bot size={16} />}
      </div>
      <div>
        <div style={bubbleStyle}>
          {message.content}
        </div>
        {showConfirmation && message.metadata?.requires_confirmation && onConfirm && (
          <div style={styles.confirmationBox}>
            <button
              style={{ ...styles.confirmBtn, ...styles.confirmBtnYes }}
              onClick={() => onConfirm(true)}
            >
              <CheckCircle size={14} />
              Confirmer
            </button>
            <button
              style={{ ...styles.confirmBtn, ...styles.confirmBtnNo }}
              onClick={() => onConfirm(false)}
            >
              <XCircle size={14} />
              Annuler
            </button>
          </div>
        )}
        <div style={styles.timestamp}>{formatTime(message.timestamp)}</div>
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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

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

  const panelStyle = {
    ...styles.panel,
    ...(isMinimized ? styles.panelMinimized : {}),
  };

  return (
    <div style={panelStyle} role="dialog" aria-label="Assistant IA Theo">
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.headerIcon}>
            <Sparkles size={18} />
          </div>
          <div>
            <h3 style={styles.headerTitle}>Theo</h3>
            {!isMinimized && (
              <p style={styles.headerSubtitle}>Assistant IA AZALSCORE</p>
            )}
          </div>
        </div>
        <div style={styles.headerActions}>
          {!isMinimized && (
            <>
              <button
                style={styles.headerBtn}
                onClick={handleNewSession}
                title="Nouvelle conversation"
              >
                <RefreshCw size={16} />
              </button>
              <button
                style={styles.headerBtn}
                onClick={clearMessages}
                title="Effacer les messages"
              >
                <Trash2 size={16} />
              </button>
            </>
          )}
          <button
            style={styles.headerBtn}
            onClick={isMinimized ? maximize : minimize}
            title={isMinimized ? 'Agrandir' : 'Réduire'}
          >
            {isMinimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
          </button>
          <button
            style={styles.headerBtn}
            onClick={close}
            title="Fermer"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Content (hidden when minimized) */}
      {!isMinimized && (
        <>
          {/* Messages */}
          <div style={styles.messages}>
            {messages.length === 0 ? (
              <div style={styles.emptyState}>
                <div style={styles.emptyIcon}>
                  <Bot size={32} />
                </div>
                <p style={{ margin: 0, fontWeight: 500 }}>Bienvenue !</p>
                <p style={{ margin: '8px 0 0', fontSize: '13px' }}>
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
          <div style={styles.inputArea}>
            <div
              style={{
                ...styles.inputWrapper,
                ...(inputFocused ? styles.inputWrapperFocused : {}),
              }}
            >
              <textarea
                ref={inputRef}
                style={styles.input}
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
                style={{
                  ...styles.sendBtn,
                  ...((!input.trim() || state === 'thinking') ? styles.sendBtnDisabled : {}),
                }}
                onClick={handleSend}
                disabled={!input.trim() || state === 'thinking'}
                title="Envoyer"
              >
                {state === 'thinking' ? (
                  <Loader2 size={18} className="animate-spin" />
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
