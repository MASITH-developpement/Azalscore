/**
 * THÉO — Voice Panel Component
 * =============================
 * Interface vocale pour Théo.
 * Micro, indicateur d'état, transcript, réponses.
 */

import React, { useEffect, useCallback } from 'react';
import { Mic, MicOff, Volume2, VolumeX, X, Pause, Play, RefreshCw } from 'lucide-react';
import { useTheoVoice, VoiceState, CompanionId } from '@core/theo/voice';

// ============================================================
// COMPANION AVATARS
// ============================================================

const COMPANION_AVATARS: Record<CompanionId, { name: string; color: string; initial: string }> = {
  theo: { name: 'Théo', color: '#6366f1', initial: 'T' },
  lea: { name: 'Léa', color: '#ec4899', initial: 'L' },
  alex: { name: 'Alex', color: '#10b981', initial: 'A' },
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

  const stateStyles: Record<VoiceState, { ring: string; pulse: boolean; label: string }> = {
    idle: { ring: 'ring-gray-300', pulse: false, label: 'Prêt' },
    listening: { ring: 'ring-green-500', pulse: true, label: 'J\'écoute...' },
    processing: { ring: 'ring-blue-500', pulse: true, label: 'Je réfléchis...' },
    speaking: { ring: 'ring-purple-500', pulse: true, label: 'Je parle...' },
    awaiting: { ring: 'ring-amber-500', pulse: false, label: 'Tu confirmes ?' },
    paused: { ring: 'ring-gray-400', pulse: false, label: 'En pause' },
    error: { ring: 'ring-red-500', pulse: false, label: 'Erreur' },
  };

  const { ring, pulse, label } = stateStyles[state];

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Avatar */}
      <div
        className={`
          relative w-24 h-24 rounded-full ring-4 ${ring}
          transition-all duration-300 flex items-center justify-center
          ${pulse ? 'animate-pulse' : ''}
        `}
        style={{ backgroundColor: companion.color }}
      >
        <span className="text-4xl font-bold text-white">
          {companion.initial}
        </span>

        {/* Pulse ring for listening */}
        {state === 'listening' && (
          <div
            className="absolute inset-0 rounded-full animate-ping opacity-30"
            style={{ backgroundColor: companion.color }}
          />
        )}

        {/* Sound waves for speaking */}
        {state === 'speaking' && (
          <div className="absolute -right-1 -bottom-1">
            <Volume2 className="w-6 h-6 text-white animate-bounce" />
          </div>
        )}
      </div>

      {/* Companion name and state */}
      <div className="text-center">
        <div className="text-lg font-semibold text-gray-800">{companion.name}</div>
        <div className="text-sm text-gray-500">{label}</div>
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
      className={`
        w-20 h-20 rounded-full flex items-center justify-center
        transition-all duration-200 shadow-lg
        ${isListening
          ? 'bg-red-500 hover:bg-red-600 scale-110'
          : 'bg-indigo-600 hover:bg-indigo-700'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        active:scale-95
      `}
      title={isListening ? 'Arrêter l\'écoute' : 'Appuyer pour parler'}
    >
      {isListening ? (
        <MicOff className="w-10 h-10 text-white" />
      ) : (
        <Mic className="w-10 h-10 text-white" />
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
    <div className="bg-gray-100 rounded-lg p-4 min-h-[60px]">
      <div className="text-sm text-gray-500 mb-1">Tu dis :</div>
      <div className="text-gray-800">
        {text || (isListening ? <span className="text-gray-400 italic">En écoute...</span> : '')}
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
    <div className="bg-indigo-50 rounded-lg p-4">
      <div className="text-sm text-indigo-600 mb-1">Théo :</div>
      <div className="text-gray-800">{text}</div>

      {/* Confirmation buttons */}
      {isAwaiting && (
        <div className="flex gap-3 mt-4">
          <button
            onClick={() => onConfirm(true)}
            className="flex-1 py-2 px-4 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
          >
            Oui
          </button>
          <button
            onClick={() => onConfirm(false)}
            className="flex-1 py-2 px-4 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
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
    <div className="flex gap-2">
      {companions.map((id) => {
        const companion = COMPANION_AVATARS[id];
        const isSelected = id === current;

        return (
          <button
            key={id}
            onClick={() => onSelect(id)}
            className={`
              w-10 h-10 rounded-full flex items-center justify-center
              transition-all duration-200
              ${isSelected
                ? 'ring-2 ring-offset-2 ring-indigo-500 scale-110'
                : 'opacity-60 hover:opacity-100'
              }
            `}
            style={{ backgroundColor: companion.color }}
            title={companion.name}
          >
            <span className="text-white font-semibold">{companion.initial}</span>
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-800">Assistant Vocal</h2>

          <div className="flex items-center gap-2">
            {/* Connection status */}
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : connectionState === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              title={connectionState}
            />

            {/* Reconnect button */}
            {connectionState === 'error' && (
              <button
                onClick={handleReconnect}
                className="p-2 text-gray-400 hover:text-gray-600"
                title="Reconnecter"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            )}

            {/* Close button */}
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
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
          <div className="flex justify-center">
            <VoiceButton
              isListening={isListening}
              onStart={startListening}
              onStop={stopListening}
              disabled={!isConnected || voiceState === 'processing' || isSpeaking}
            />
          </div>

          {/* Hint */}
          <div className="text-center text-sm text-gray-400">
            Maintiens <kbd className="px-2 py-1 bg-gray-100 rounded">Espace</kbd> pour parler
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100 bg-gray-50">
          {/* Companion selector */}
          <CompanionSelector current={companionId} onSelect={setCompanion} />

          {/* Pause/Resume */}
          <button
            onClick={voiceState === 'paused' ? resume : pause}
            className="p-2 text-gray-400 hover:text-gray-600"
            title={voiceState === 'paused' ? 'Reprendre' : 'Pause'}
          >
            {voiceState === 'paused' ? (
              <Play className="w-5 h-5" />
            ) : (
              <Pause className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TheoVoicePanel;
