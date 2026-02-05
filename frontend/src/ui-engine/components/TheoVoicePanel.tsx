/**
 * THEO -- Voice Panel Component
 * =============================
 * Interface vocale pour Theo.
 * Micro, indicateur d'etat, transcript, reponses.
 */

import React, { useEffect, useCallback, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, X, Pause, Play, RefreshCw } from 'lucide-react';
import { useTheoVoice, VoiceState, CompanionId } from '@core/theo/voice';
import { COLORS } from '@core/design-tokens';
import { clsx } from 'clsx';
import { useFocusTrap } from '../hooks/useFocusTrap';
import '@/styles/theo-voice-panel.css';

// ============================================================
// COMPANION AVATARS
// ============================================================

const COMPANION_AVATARS: Record<CompanionId, { name: string; color: string; initial: string }> = {
  theo: { name: 'Theo', color: COLORS.affaires, initial: 'T' },
  lea: { name: 'Lea', color: COLORS.factures, initial: 'L' },
  alex: { name: 'Alex', color: COLORS.success, initial: 'A' },
};

// ============================================================
// VOICE STATE INDICATOR
// ============================================================

interface StateIndicatorProps {
  state: VoiceState;
  companionId: CompanionId;
}

const StateIndicator: React.FC<StateIndicatorProps> = ({ state, companionId }) => {
  const companion = COMPANION_AVATARS[companionId];

  const stateLabels: Record<VoiceState, string> = {
    idle: 'Pret',
    listening: 'J\'ecoute...',
    processing: 'Je reflechis...',
    speaking: 'Je parle...',
    awaiting: 'Tu confirmes ?',
    paused: 'En pause',
    error: 'Erreur',
  };

  const label = stateLabels[state];

  return (
    <div className="azals-theo-voice-indicator">
      {/* Avatar */}
      <div
        className={clsx(
          'azals-theo-voice-avatar',
          `azals-theo-voice-avatar--${state}`
        )}
        style={{ '--companion-color': companion.color } as React.CSSProperties}
      >
        <span className="azals-theo-voice-avatar__initial">
          {companion.initial}
        </span>

        {/* Pulse ring for listening */}
        {state === 'listening' && (
          <div
            className="azals-theo-voice-avatar__ping"
          />
        )}

        {/* Sound waves for speaking */}
        {state === 'speaking' && (
          <div className="azals-theo-voice-avatar__wave">
            <Volume2 size={24} />
          </div>
        )}
      </div>

      {/* Companion name and state */}
      <div className="azals-theo-voice-info">
        <div className="azals-theo-voice-info__name">{companion.name}</div>
        <div className="azals-theo-voice-info__state">{label}</div>
      </div>
    </div>
  );
};

// ============================================================
// VOICE BUTTON
// ============================================================

interface VoiceButtonProps {
  isListening: boolean;
  onStart: () => void;
  onStop: () => void;
  disabled?: boolean;
}

const VoiceButton: React.FC<VoiceButtonProps> = ({
  isListening,
  onStart,
  onStop,
  disabled,
}) => {
  return (
    <button
      onClick={isListening ? onStop : onStart}
      disabled={disabled}
      className={clsx(
        'azals-theo-voice-btn',
        isListening ? 'azals-theo-voice-btn--listening' : 'azals-theo-voice-btn--idle',
        disabled && 'azals-theo-voice-btn--disabled'
      )}
      title={isListening ? 'Arreter l\'ecoute' : 'Appuyer pour parler'}
      aria-label={isListening ? 'Arreter l\'ecoute' : 'Appuyer pour parler'}
    >
      {isListening ? (
        <MicOff className="azals-theo-voice-btn__icon" />
      ) : (
        <Mic className="azals-theo-voice-btn__icon" />
      )}
    </button>
  );
};

// ============================================================
// TRANSCRIPT DISPLAY
// ============================================================

interface TranscriptProps {
  text: string;
  isListening: boolean;
}

const TranscriptDisplay: React.FC<TranscriptProps> = ({ text, isListening }) => {
  if (!text && !isListening) return null;

  return (
    <div className="azals-theo-voice-transcript">
      <div className="azals-theo-voice-transcript__label">Tu dis :</div>
      <div className="azals-theo-voice-transcript__text">
        {text || (isListening ? <span className="azals-theo-voice-transcript__placeholder">En ecoute...</span> : '')}
      </div>
    </div>
  );
};

// ============================================================
// RESPONSE DISPLAY
// ============================================================

interface ResponseProps {
  text: string;
  isAwaiting: boolean;
  onConfirm: (yes: boolean) => void;
}

const ResponseDisplay: React.FC<ResponseProps> = ({ text, isAwaiting, onConfirm }) => {
  if (!text) return null;

  return (
    <div className="azals-theo-voice-response">
      <div className="azals-theo-voice-response__label">Theo :</div>
      <div className="azals-theo-voice-response__text">{text}</div>

      {/* Confirmation buttons */}
      {isAwaiting && (
        <div className="azals-theo-voice-confirm">
          <button
            onClick={() => onConfirm(true)}
            className="azals-theo-voice-confirm__btn azals-theo-voice-confirm__btn--yes"
          >
            Oui
          </button>
          <button
            onClick={() => onConfirm(false)}
            className="azals-theo-voice-confirm__btn azals-theo-voice-confirm__btn--no"
          >
            Non
          </button>
        </div>
      )}
    </div>
  );
};

// ============================================================
// COMPANION SELECTOR
// ============================================================

interface CompanionSelectorProps {
  current: CompanionId;
  onSelect: (id: CompanionId) => void;
}

const CompanionSelector: React.FC<CompanionSelectorProps> = ({ current, onSelect }) => {
  const companions: CompanionId[] = ['theo', 'lea', 'alex'];

  return (
    <div className="azals-theo-voice-companions">
      {companions.map((id) => {
        const companion = COMPANION_AVATARS[id];
        const isSelected = id === current;

        return (
          <button
            key={id}
            onClick={() => onSelect(id)}
            className={clsx(
              'azals-theo-voice-companion-btn',
              isSelected
                ? 'azals-theo-voice-companion-btn--selected'
                : 'azals-theo-voice-companion-btn--unselected'
            )}
            style={{ '--companion-color': companion.color } as React.CSSProperties}
            title={companion.name}
            aria-label={`Choisir ${companion.name}`}
          >
            <span className="azals-theo-voice-companion-btn__initial">{companion.initial}</span>
          </button>
        );
      })}
    </div>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

interface TheoVoicePanelProps {
  onClose?: () => void;
}

export const TheoVoicePanel: React.FC<TheoVoicePanelProps> = ({ onClose }) => {
  const {
    connectionState,
    isConnected,
    voiceState,
    isListening,
    isSpeaking,
    isAwaiting,
    companionId,
    currentTranscript,
    lastResponse,
    connect,
    disconnect,
    startListening,
    stopListening,
    confirm,
    pause,
    resume,
    setCompanion,
  } = useTheoVoice();

  const overlayRef = useRef<HTMLDivElement>(null);
  useFocusTrap(overlayRef, { enabled: true, onEscape: onClose });

  // Auto-connect on mount
  useEffect(() => {
    if (connectionState === 'disconnected') {
      connect();
    }

    return () => {
      // Don't disconnect on unmount to preserve session
    };
  }, []);

  // Keyboard shortcut (Space to talk)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !e.repeat && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault();
        if (!isListening && isConnected) {
          startListening();
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space' && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault();
        if (isListening) {
          stopListening();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isListening, isConnected, startListening, stopListening]);

  const handleReconnect = useCallback(() => {
    disconnect();
    setTimeout(() => connect(), 500);
  }, [disconnect, connect]);

  return (
    <div ref={overlayRef} className="azals-theo-voice-overlay" role="dialog" aria-modal="true" aria-label="Assistant Vocal">
      <div className="azals-theo-voice-panel">
        {/* Header */}
        <div className="azals-theo-voice-header">
          <h2 className="azals-theo-voice-header__title">Assistant Vocal</h2>

          <div className="azals-theo-voice-header__actions">
            {/* Connection status */}
            <div
              className={clsx(
                'azals-theo-voice-status-dot',
                isConnected
                  ? 'azals-theo-voice-status-dot--connected'
                  : connectionState === 'connecting'
                  ? 'azals-theo-voice-status-dot--connecting'
                  : 'azals-theo-voice-status-dot--disconnected'
              )}
              title={connectionState}
            />

            {/* Reconnect button */}
            {connectionState === 'error' && (
              <button
                onClick={handleReconnect}
                className="azals-theo-voice-icon-btn"
                title="Reconnecter"
                aria-label="Reconnecter"
              >
                <RefreshCw size={16} />
              </button>
            )}

            {/* Close button */}
            {onClose && (
              <button
                onClick={onClose}
                className="azals-theo-voice-icon-btn"
                aria-label="Fermer"
              >
                <X size={20} />
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="azals-theo-voice-content">
          {/* State indicator */}
          <StateIndicator state={voiceState} companionId={companionId} />

          {/* Transcript */}
          <TranscriptDisplay text={currentTranscript} isListening={isListening} />

          {/* Response */}
          <ResponseDisplay
            text={lastResponse}
            isAwaiting={isAwaiting}
            onConfirm={confirm}
          />

          {/* Voice button */}
          <div className="azals-theo-voice-btn-wrapper">
            <VoiceButton
              isListening={isListening}
              onStart={startListening}
              onStop={stopListening}
              disabled={!isConnected || voiceState === 'processing' || isSpeaking}
            />
          </div>

          {/* Hint */}
          <div className="azals-theo-voice-hint">
            Maintiens <kbd className="azals-theo-voice-hint__kbd">Espace</kbd> pour parler
          </div>
        </div>

        {/* Footer */}
        <div className="azals-theo-voice-footer">
          {/* Companion selector */}
          <CompanionSelector current={companionId} onSelect={setCompanion} />

          {/* Pause/Resume */}
          <button
            onClick={voiceState === 'paused' ? resume : pause}
            className="azals-theo-voice-icon-btn"
            title={voiceState === 'paused' ? 'Reprendre' : 'Pause'}
            aria-label={voiceState === 'paused' ? 'Reprendre' : 'Pause'}
          >
            {voiceState === 'paused' ? (
              <Play size={20} />
            ) : (
              <Pause size={20} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TheoVoicePanel;
