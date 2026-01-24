/**
 * THÉO — Voice Interface
 * =======================
 * Gestion de l'interface vocale avec Théo.
 * WebSocket, micro, haut-parleur, états visuels.
 */

import { create } from 'zustand';

// ============================================================
// TYPES
// ============================================================

export type VoiceState =
  | 'idle'           // Prêt à écouter
  | 'listening'      // En écoute (micro actif)
  | 'processing'     // Traitement en cours
  | 'speaking'       // Théo parle
  | 'awaiting'       // Attend confirmation
  | 'paused'         // En pause
  | 'error';         // Erreur

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';

export type CompanionId = 'theo' | 'lea' | 'alex';

export interface VoiceMessage {
  type: 'user' | 'theo';
  text: string;
  timestamp: Date;
  audioUrl?: string;
}

interface TheoVoiceStore {
  // Connection
  connectionState: ConnectionState;
  sessionId: string | null;
  websocket: WebSocket | null;

  // Voice state
  voiceState: VoiceState;
  isListening: boolean;
  isSpeaking: boolean;

  // Companion
  companionId: CompanionId;

  // Audio
  mediaRecorder: MediaRecorder | null;
  audioContext: AudioContext | null;
  audioQueue: ArrayBuffer[];
  isPlayingAudio: boolean;

  // Transcript
  currentTranscript: string;
  lastResponse: string;
  messages: VoiceMessage[];

  // Web Speech API
  useBrowserSTT: boolean;
  speechRecognition: SpeechRecognition | null;

  // Actions
  connect: (token?: string) => Promise<void>;
  disconnect: () => void;
  startListening: () => Promise<void>;
  stopListening: () => void;
  sendText: (text: string) => void;
  confirm: (yes: boolean) => void;
  pause: () => void;
  resume: () => void;
  setCompanion: (id: CompanionId) => void;
  clearMessages: () => void;
}

// ============================================================
// WEBSOCKET MESSAGE TYPES
// ============================================================

interface WSMessage {
  type: string;
  payload: Record<string, unknown>;
  timestamp?: string;
}

// ============================================================
// STORE
// ============================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const useTheoVoiceStore = create<TheoVoiceStore>((set, get) => ({
  // Initial state
  connectionState: 'disconnected',
  sessionId: null,
  websocket: null,
  voiceState: 'idle',
  isListening: false,
  isSpeaking: false,
  companionId: 'theo',
  mediaRecorder: null,
  audioContext: null,
  audioQueue: [],
  isPlayingAudio: false,
  currentTranscript: '',
  lastResponse: '',
  messages: [],
  useBrowserSTT: true, // Use Web Speech API by default
  speechRecognition: null,

  // ----------------------------------------------------------------
  // CONNECTION
  // ----------------------------------------------------------------

  connect: async (token?: string) => {
    const { companionId, disconnect } = get();

    // Disconnect if already connected
    disconnect();

    set({ connectionState: 'connecting' });

    try {
      // Build WebSocket URL
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = API_BASE_URL.replace(/^https?:\/\//, '') || window.location.host;
      const wsUrl = `${wsProtocol}//${wsHost}/theo/ws?companion=${companionId}&mode=desktop${token ? `&token=${token}` : ''}`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[TheoVoice] Connected');
        set({ connectionState: 'connected' });
      };

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          handleWSMessage(message, set, get);
        } catch (e) {
          console.error('[TheoVoice] Invalid message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('[TheoVoice] WebSocket error:', error);
        set({ connectionState: 'error', voiceState: 'error' });
      };

      ws.onclose = () => {
        console.log('[TheoVoice] Disconnected');
        set({
          connectionState: 'disconnected',
          websocket: null,
          sessionId: null,
        });
      };

      set({ websocket: ws });

      // Initialize AudioContext
      const audioContext = new AudioContext();
      set({ audioContext });

    } catch (error) {
      console.error('[TheoVoice] Connection error:', error);
      set({ connectionState: 'error' });
    }
  },

  disconnect: () => {
    const { websocket, mediaRecorder, speechRecognition, audioContext } = get();

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }

    if (speechRecognition) {
      speechRecognition.stop();
    }

    if (websocket) {
      websocket.close();
    }

    if (audioContext) {
      audioContext.close();
    }

    set({
      websocket: null,
      mediaRecorder: null,
      speechRecognition: null,
      audioContext: null,
      connectionState: 'disconnected',
      sessionId: null,
      isListening: false,
      isSpeaking: false,
    });
  },

  // ----------------------------------------------------------------
  // VOICE RECORDING
  // ----------------------------------------------------------------

  startListening: async () => {
    const { websocket, useBrowserSTT } = get();

    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      console.error('[TheoVoice] Not connected');
      return;
    }

    set({ isListening: true, voiceState: 'listening', currentTranscript: '' });

    if (useBrowserSTT) {
      // Use Web Speech API
      startBrowserSTT(set, get);
    } else {
      // Use server-side STT via WebSocket
      await startMediaRecording(set, get);
    }
  },

  stopListening: () => {
    const { mediaRecorder, speechRecognition, useBrowserSTT } = get();

    set({ isListening: false });

    if (useBrowserSTT && speechRecognition) {
      speechRecognition.stop();
    } else if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
  },

  // ----------------------------------------------------------------
  // TEXT INPUT
  // ----------------------------------------------------------------

  sendText: (text: string) => {
    const { websocket } = get();

    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      console.error('[TheoVoice] Not connected');
      return;
    }

    // Add user message
    const userMessage: VoiceMessage = {
      type: 'user',
      text,
      timestamp: new Date(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      voiceState: 'processing',
    }));

    // Send via WebSocket
    websocket.send(JSON.stringify({
      type: 'text_input',
      payload: { text },
    }));
  },

  // ----------------------------------------------------------------
  // CONFIRMATION
  // ----------------------------------------------------------------

  confirm: (yes: boolean) => {
    const { sendText } = get();
    sendText(yes ? 'oui' : 'non');
  },

  // ----------------------------------------------------------------
  // CONTROL
  // ----------------------------------------------------------------

  pause: () => {
    const { websocket } = get();

    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'control',
        payload: { action: 'pause' },
      }));
    }

    set({ voiceState: 'paused' });
  },

  resume: () => {
    const { websocket } = get();

    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'control',
        payload: { action: 'resume' },
      }));
    }

    set({ voiceState: 'idle' });
  },

  setCompanion: (id: CompanionId) => {
    set({ companionId: id });
    // Reconnect with new companion
    const { connect } = get();
    connect();
  },

  clearMessages: () => {
    set({ messages: [], currentTranscript: '', lastResponse: '' });
  },
}));

// ============================================================
// WEBSOCKET MESSAGE HANDLER
// ============================================================

function handleWSMessage(
  message: WSMessage,
  set: (fn: (state: TheoVoiceStore) => Partial<TheoVoiceStore>) => void,
  get: () => TheoVoiceStore
) {
  const { type, payload } = message;

  switch (type) {
    case 'session_info':
      set(() => ({
        sessionId: payload.session_id as string,
      }));
      break;

    case 'listening':
      set(() => ({ voiceState: 'listening' }));
      break;

    case 'processing':
      set(() => ({ voiceState: 'processing' }));
      break;

    case 'transcription_result':
      set(() => ({
        currentTranscript: payload.text as string,
      }));
      break;

    case 'response':
      const responseText = payload.text as string;
      const theoMessage: VoiceMessage = {
        type: 'theo',
        text: responseText,
        timestamp: new Date(),
      };

      set((state) => ({
        lastResponse: responseText,
        messages: [...state.messages, theoMessage],
        voiceState: (payload.session_state === 'awaiting_confirmation')
          ? 'awaiting'
          : 'idle',
      }));
      break;

    case 'audio_response':
      // Receive audio chunk
      const audioData = payload.data as string;
      const audioBytes = base64ToArrayBuffer(audioData);
      const currentQueue = get().audioQueue;

      set(() => ({
        audioQueue: [...currentQueue, audioBytes],
      }));

      // Start playback if not already playing
      if (!get().isPlayingAudio) {
        playAudioQueue(set, get);
      }
      break;

    case 'audio_response_end':
      // Audio streaming complete
      break;

    case 'visual_state':
      const visualState = payload.state as string;
      const stateMap: Record<string, VoiceState> = {
        'idle': 'idle',
        'listening': 'listening',
        'processing': 'processing',
        'speaking': 'speaking',
        'awaiting': 'awaiting',
        'paused': 'paused',
        'error': 'error',
      };
      set(() => ({
        voiceState: stateMap[visualState] || 'idle',
        isSpeaking: visualState === 'speaking',
      }));
      break;

    case 'error':
      console.error('[TheoVoice] Error:', payload.message);
      set(() => ({
        voiceState: 'error',
      }));
      break;
  }
}

// ============================================================
// BROWSER STT (Web Speech API)
// ============================================================

function startBrowserSTT(
  set: (fn: (state: TheoVoiceStore) => Partial<TheoVoiceStore>) => void,
  get: () => TheoVoiceStore
) {
  // Check for browser support
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    console.error('[TheoVoice] Web Speech API not supported');
    set(() => ({ voiceState: 'error' }));
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'fr-FR';
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onresult = (event: SpeechRecognitionEvent) => {
    const { websocket } = get();

    let finalTranscript = '';
    let interimTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];
      if (result.isFinal) {
        finalTranscript += result[0].transcript;
      } else {
        interimTranscript += result[0].transcript;
      }
    }

    // Update current transcript
    set(() => ({
      currentTranscript: finalTranscript || interimTranscript,
    }));

    // Send final result to server
    if (finalTranscript && websocket && websocket.readyState === WebSocket.OPEN) {
      const userMessage: VoiceMessage = {
        type: 'user',
        text: finalTranscript,
        timestamp: new Date(),
      };

      set((state) => ({
        messages: [...state.messages, userMessage],
        isListening: false,
        voiceState: 'processing',
      }));

      websocket.send(JSON.stringify({
        type: 'transcription',
        payload: {
          text: finalTranscript,
          confidence: event.results[0][0].confidence || 0.9,
          is_final: true,
        },
      }));
    }
  };

  recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
    console.error('[TheoVoice] Speech recognition error:', event.error);
    set(() => ({
      isListening: false,
      voiceState: event.error === 'no-speech' ? 'idle' : 'error',
    }));
  };

  recognition.onend = () => {
    set(() => ({ isListening: false }));
  };

  recognition.start();
  set(() => ({ speechRecognition: recognition }));
}

// ============================================================
// MEDIA RECORDING (Server-side STT)
// ============================================================

async function startMediaRecording(
  set: (fn: (state: TheoVoiceStore) => Partial<TheoVoiceStore>) => void,
  get: () => TheoVoiceStore
) {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus',
    });

    const chunks: Blob[] = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data);

        // Send chunk to server
        const { websocket } = get();
        if (websocket && websocket.readyState === WebSocket.OPEN) {
          const reader = new FileReader();
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1];
            websocket.send(JSON.stringify({
              type: 'audio_chunk',
              payload: { data: base64, format: 'webm' },
            }));
          };
          reader.readAsDataURL(event.data);
        }
      }
    };

    mediaRecorder.onstop = () => {
      // Signal end of audio
      const { websocket } = get();
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          type: 'audio_end',
          payload: {},
        }));
      }

      // Stop all tracks
      stream.getTracks().forEach((track) => track.stop());

      set(() => ({
        mediaRecorder: null,
        voiceState: 'processing',
      }));
    };

    mediaRecorder.start(250); // Chunk every 250ms
    set(() => ({ mediaRecorder }));

  } catch (error) {
    console.error('[TheoVoice] Microphone error:', error);
    set(() => ({
      voiceState: 'error',
      isListening: false,
    }));
  }
}

// ============================================================
// AUDIO PLAYBACK
// ============================================================

async function playAudioQueue(
  set: (fn: (state: TheoVoiceStore) => Partial<TheoVoiceStore>) => void,
  get: () => TheoVoiceStore
) {
  const { audioContext, audioQueue } = get();

  if (!audioContext || audioQueue.length === 0) {
    set(() => ({ isPlayingAudio: false, isSpeaking: false }));
    return;
  }

  set(() => ({ isPlayingAudio: true, isSpeaking: true }));

  // Process queue
  while (get().audioQueue.length > 0) {
    const currentQueue = get().audioQueue;
    const buffer = currentQueue[0];

    // Remove from queue
    set(() => ({
      audioQueue: currentQueue.slice(1),
    }));

    try {
      // Decode and play
      const audioBuffer = await audioContext.decodeAudioData(buffer.slice(0));
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);

      await new Promise<void>((resolve) => {
        source.onended = () => resolve();
        source.start();
      });
    } catch (e) {
      console.error('[TheoVoice] Audio playback error:', e);
    }
  }

  set(() => ({ isPlayingAudio: false, isSpeaking: false, voiceState: 'idle' }));
}

// ============================================================
// UTILITIES
// ============================================================

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binaryString = window.atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

// ============================================================
// HOOKS
// ============================================================

export const useTheoVoice = () => {
  const store = useTheoVoiceStore();

  return {
    // Connection
    connectionState: store.connectionState,
    isConnected: store.connectionState === 'connected',
    sessionId: store.sessionId,

    // Voice state
    voiceState: store.voiceState,
    isListening: store.isListening,
    isSpeaking: store.isSpeaking,
    isProcessing: store.voiceState === 'processing',
    isAwaiting: store.voiceState === 'awaiting',

    // Companion
    companionId: store.companionId,

    // Transcript
    currentTranscript: store.currentTranscript,
    lastResponse: store.lastResponse,
    messages: store.messages,

    // Actions
    connect: store.connect,
    disconnect: store.disconnect,
    startListening: store.startListening,
    stopListening: store.stopListening,
    sendText: store.sendText,
    confirm: store.confirm,
    pause: store.pause,
    resume: store.resume,
    setCompanion: store.setCompanion,
    clearMessages: store.clearMessages,
  };
};

export const useVoiceState = () => useTheoVoiceStore((s) => s.voiceState);
export const useIsListening = () => useTheoVoiceStore((s) => s.isListening);
export const useIsSpeaking = () => useTheoVoiceStore((s) => s.isSpeaking);
export const useCurrentTranscript = () => useTheoVoiceStore((s) => s.currentTranscript);

// ============================================================
// TYPES FOR WEB SPEECH API
// ============================================================

declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}
