/**
 * AZALSCORE - Theo AI Store
 * ==========================
 * Gestion du chat avec Theo (LLM souverain)
 * Interface unique pour l'assistance IA
 */

import { create } from 'zustand';
import { api } from '@core/api-client';

// ============================================================
// TYPES
// ============================================================

export type TheoMessageRole = 'user' | 'theo' | 'system';
export type TheoState = 'idle' | 'listening' | 'thinking' | 'responding' | 'clarifying' | 'error';

export interface TheoMessage {
  id: string;
  role: TheoMessageRole;
  content: string;
  timestamp: Date;
  metadata?: {
    intent?: string;
    confidence?: number;
    requires_confirmation?: boolean;
    clarification_options?: string[];
  };
}

export interface TheoSession {
  session_id: string;
  started_at: Date;
  last_activity: Date;
  message_count: number;
}

interface TheoStore {
  // State
  isOpen: boolean;
  isMinimized: boolean;
  session: TheoSession | null;
  messages: TheoMessage[];
  state: TheoState;
  error: string | null;
  pendingConfirmation: TheoMessage | null;

  // Actions
  open: () => void;
  close: () => void;
  minimize: () => void;
  maximize: () => void;
  toggle: () => void;

  startSession: () => Promise<void>;
  endSession: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  confirmIntent: (confirmed: boolean) => Promise<void>;
  clearMessages: () => void;
  clearError: () => void;
}

// ============================================================
// HELPERS
// ============================================================

const generateMessageId = (): string => {
  return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// ============================================================
// STORE
// ============================================================

export const useTheoStore = create<TheoStore>((set, get) => ({
  // Initial state
  isOpen: false,
  isMinimized: false,
  session: null,
  messages: [],
  state: 'idle',
  error: null,
  pendingConfirmation: null,

  // UI Actions
  open: () => {
    set({ isOpen: true, isMinimized: false });
    // Auto-start session if not already active
    const { session, startSession } = get();
    if (!session) {
      startSession();
    }
  },

  close: () => {
    set({ isOpen: false });
  },

  minimize: () => {
    set({ isMinimized: true });
  },

  maximize: () => {
    set({ isMinimized: false });
  },

  toggle: () => {
    const { isOpen, open, close } = get();
    if (isOpen) {
      close();
    } else {
      open();
    }
  },

  // Session Actions
  startSession: async () => {
    set({ state: 'thinking', error: null });

    try {
      const response = await api.post<{
        session_id: string;
        message: string;
      }>('/ai/theo/start', {}) as unknown as {
        session_id: string;
        message: string;
      };

      // Le backend retourne directement {session_id, message}
      if (response) {
        const session: TheoSession = {
          session_id: response.session_id,
          started_at: new Date(),
          last_activity: new Date(),
          message_count: 0,
        };

        // Message de bienvenue de Theo
        const welcomeMessage: TheoMessage = {
          id: generateMessageId(),
          role: 'theo',
          content: response.message || 'Bonjour ! Je suis Theo, votre assistant IA AZALSCORE. Comment puis-je vous aider ?',
          timestamp: new Date(),
        };

        set({
          session,
          messages: [welcomeMessage],
          state: 'idle',
        });
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Erreur de connexion à Theo';
      set({
        state: 'error',
        error: errorMessage,
      });

      // Fallback message si l'API n'est pas disponible
      const fallbackMessage: TheoMessage = {
        id: generateMessageId(),
        role: 'system',
        content: 'Service Theo temporairement indisponible. Réessayez dans quelques instants.',
        timestamp: new Date(),
      };
      set((state) => ({
        messages: [...state.messages, fallbackMessage],
      }));
    }
  },

  endSession: async () => {
    const { session } = get();

    if (session) {
      try {
        await api.post(`/ai/theo/end/${session.session_id}`, {});
      } catch {
        // Ignore errors on session end
      }
    }

    set({
      session: null,
      messages: [],
      state: 'idle',
      pendingConfirmation: null,
    });
  },

  sendMessage: async (content: string) => {
    const { session, startSession } = get();

    // Start session if not active
    if (!session) {
      await startSession();
      // Re-get session after start
      const newSession = get().session;
      if (!newSession) {
        return; // Failed to start session
      }
    }

    const currentSession = get().session;
    if (!currentSession) return;

    // Add user message
    const userMessage: TheoMessage = {
      id: generateMessageId(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      state: 'thinking',
      error: null,
    }));

    try {
      const response = await api.post<{
        message: string;
        intent?: string;
        confidence?: number;
        requires_confirmation?: boolean;
        clarification_options?: string[];
        action_result?: unknown;
      }>('/ai/theo/chat', {
        session_id: currentSession.session_id,
        message: content,
        context: {
          page: window.location.pathname,
          timestamp: new Date().toISOString(),
        },
      }) as unknown as {
        message: string;
        intent?: string;
        confidence?: number;
        requires_confirmation?: boolean;
        clarification_options?: string[];
        action_result?: unknown;
      };

      // Le backend retourne directement les données
      if (response) {
        const theoResponse: TheoMessage = {
          id: generateMessageId(),
          role: 'theo',
          content: response.message,
          timestamp: new Date(),
          metadata: {
            intent: response.intent,
            confidence: response.confidence,
            requires_confirmation: response.requires_confirmation,
            clarification_options: response.clarification_options,
          },
        };

        set((state) => ({
          messages: [...state.messages, theoResponse],
          state: response.requires_confirmation ? 'clarifying' : 'idle',
          pendingConfirmation: response.requires_confirmation ? theoResponse : null,
          session: state.session ? {
            ...state.session,
            last_activity: new Date(),
            message_count: state.session.message_count + 1,
          } : null,
        }));
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Erreur de communication avec Theo';

      const errorResponse: TheoMessage = {
        id: generateMessageId(),
        role: 'system',
        content: `Erreur: ${errorMessage}`,
        timestamp: new Date(),
      };

      set((state) => ({
        messages: [...state.messages, errorResponse],
        state: 'error',
        error: errorMessage,
      }));
    }
  },

  confirmIntent: async (confirmed: boolean) => {
    const { session, pendingConfirmation } = get();

    if (!session || !pendingConfirmation) return;

    set({ state: 'thinking' });

    try {
      const response = await api.post<{
        message: string;
        action_result?: unknown;
      }>('/ai/theo/confirm', {
        session_id: session.session_id,
        confirmed,
        intent: pendingConfirmation.metadata?.intent,
      }) as unknown as {
        message: string;
        action_result?: unknown;
      };

      // Le backend retourne directement les données
      if (response) {
        const confirmResponse: TheoMessage = {
          id: generateMessageId(),
          role: 'theo',
          content: response.message,
          timestamp: new Date(),
        };

        set((state) => ({
          messages: [...state.messages, confirmResponse],
          state: 'idle',
          pendingConfirmation: null,
        }));
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Erreur de confirmation';
      set({
        state: 'error',
        error: errorMessage,
        pendingConfirmation: null,
      });
    }
  },

  clearMessages: () => {
    set({ messages: [], pendingConfirmation: null });
  },

  clearError: () => {
    set({ error: null, state: 'idle' });
  },
}));

// ============================================================
// HOOKS
// ============================================================

export const useTheo = () => {
  const store = useTheoStore();
  return {
    isOpen: store.isOpen,
    isMinimized: store.isMinimized,
    messages: store.messages,
    state: store.state,
    error: store.error,
    hasSession: !!store.session,
    pendingConfirmation: store.pendingConfirmation,
    open: store.open,
    close: store.close,
    toggle: store.toggle,
    minimize: store.minimize,
    maximize: store.maximize,
    sendMessage: store.sendMessage,
    confirmIntent: store.confirmIntent,
    clearMessages: store.clearMessages,
    clearError: store.clearError,
    endSession: store.endSession,
  };
};

export const useTheoOpen = () => useTheoStore((state) => state.isOpen);
export const useTheoState = () => useTheoStore((state) => state.state);
export const useTheoMessages = () => useTheoStore((state) => state.messages);

// ============================================================
// RE-EXPORT VOICE MODULE
// ============================================================

export {
  useTheoVoice,
  useTheoVoiceStore,
  useVoiceState,
  useIsListening,
  useIsSpeaking,
  useCurrentTranscript,
} from './voice';

export type { VoiceState, CompanionId, VoiceMessage } from './voice';
