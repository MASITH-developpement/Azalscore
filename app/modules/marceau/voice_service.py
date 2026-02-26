"""
AZALS MODULE - Marceau Voice Service
=====================================

Service de dialogue vocal complet.
Combine reconnaissance vocale, synthese vocale et gestion de dialogue fluide.

Fonctionnalites:
    - Conversation vocale en temps reel
    - Reconnaissance vocale continue (streaming)
    - Synthese vocale naturelle
    - Gestion de dialogue multi-tour
    - Detection d'interruptions
    - Adaptation au bruit ambiant
    - Historique et transcription

Usage:
    from app.modules.marceau.voice_service import VoiceService

    service = VoiceService(tenant_id, db)
    await service.initialize()

    # Demarrer une conversation
    session = await service.start_session(caller_phone="+33612345678")

    # Traiter l'audio entrant
    response = await service.process_audio(session.id, audio_chunk)

    # Obtenir l'audio de reponse
    audio_response = response.audio_data
"""
from __future__ import annotations


import asyncio
import base64
import io
import json
import logging
import uuid
import wave
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, BinaryIO, Callable

from sqlalchemy.orm import Session

from .dialogue_manager import (
    DialogueManager,
    DialogueResponse,
    DialogueState,
    DialogueContext,
    IntentType,
)
from .voice_client import (
    VoiceClient,
    VoiceConfig,
    VoiceClientFactory,
    TranscriptionResult,
    SynthesisResult,
    AudioFormat,
    get_voice_client,
)
from .models import MarceauConversation, ConversationOutcome

logger = logging.getLogger(__name__)


# ============================================================================
# TYPES ET CONFIGURATIONS
# ============================================================================

class SessionState(str, Enum):
    """Etats de session vocale."""
    INITIALIZING = "initializing"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    PAUSED = "paused"
    ENDED = "ended"


class AudioStreamState(str, Enum):
    """Etats du flux audio."""
    SILENCE = "silence"
    SPEECH = "speech"
    END_OF_SPEECH = "end_of_speech"


@dataclass
class VoiceSessionConfig:
    """Configuration de session vocale."""
    # Audio
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_ms: int = 100  # Duree d'un chunk audio

    # VAD (Voice Activity Detection)
    vad_enabled: bool = True
    vad_threshold: float = 0.5
    silence_timeout_ms: int = 1500  # Delai avant fin de parole
    min_speech_duration_ms: int = 250  # Duree minimum pour considerer comme parole

    # Interruptions
    allow_interruptions: bool = True
    interrupt_threshold_ms: int = 500  # Duree de parole pour interrompre

    # Timeouts
    session_timeout_minutes: int = 30
    inactivity_timeout_seconds: int = 60


@dataclass
class VoiceSession:
    """Session de dialogue vocal."""
    id: str
    tenant_id: str
    conversation_id: str
    state: SessionState
    config: VoiceSessionConfig

    # Caller info
    caller_phone: str
    customer_id: str | None = None
    customer_name: str | None = None

    # Audio state
    audio_buffer: bytes = b""
    is_speaking: bool = False
    speech_start_time: datetime | None = None
    last_speech_time: datetime | None = None

    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

    # Stats
    total_speech_duration: float = 0.0
    total_silence_duration: float = 0.0
    utterance_count: int = 0
    response_count: int = 0


@dataclass
class VoiceResponse:
    """Reponse vocale complete."""
    text: str
    audio_data: bytes | None
    audio_format: AudioFormat
    audio_duration: float
    dialogue_response: DialogueResponse
    session_state: SessionState
    should_end: bool = False
    transfer_to: str | None = None


# ============================================================================
# VOICE ACTIVITY DETECTION (VAD)
# ============================================================================

class SimpleVAD:
    """
    Detection d'activite vocale simple.
    Utilise l'energie RMS pour detecter la parole.
    """

    def __init__(
        self,
        threshold: float = 0.02,
        min_speech_frames: int = 3,
        min_silence_frames: int = 10
    ):
        self.threshold = threshold
        self.min_speech_frames = min_speech_frames
        self.min_silence_frames = min_silence_frames
        self.speech_frames = 0
        self.silence_frames = 0
        self.is_speech = False

    def process(self, audio_chunk: bytes) -> AudioStreamState:
        """
        Analyse un chunk audio et retourne l'etat.

        Args:
            audio_chunk: Chunk audio PCM 16-bit

        Returns:
            Etat du flux audio
        """
        # Calculer l'energie RMS
        import struct
        samples = struct.unpack(f"{len(audio_chunk)//2}h", audio_chunk)
        rms = (sum(s**2 for s in samples) / len(samples)) ** 0.5
        normalized_rms = rms / 32768.0

        if normalized_rms > self.threshold:
            self.speech_frames += 1
            self.silence_frames = 0

            if self.speech_frames >= self.min_speech_frames:
                self.is_speech = True
                return AudioStreamState.SPEECH

        else:
            self.silence_frames += 1

            if self.is_speech and self.silence_frames >= self.min_silence_frames:
                self.is_speech = False
                self.speech_frames = 0
                return AudioStreamState.END_OF_SPEECH

        return AudioStreamState.SPEECH if self.is_speech else AudioStreamState.SILENCE

    def reset(self):
        """Reset le VAD."""
        self.speech_frames = 0
        self.silence_frames = 0
        self.is_speech = False


# ============================================================================
# SERVICE VOCAL
# ============================================================================

class VoiceService:
    """
    Service de dialogue vocal complet.
    Orchestre reconnaissance, synthese et dialogue.
    """

    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db
        self.voice_client: VoiceClient | None = None
        self.dialogue_manager: DialogueManager | None = None
        self._sessions: dict[str, VoiceSession] = {}
        self._vads: dict[str, SimpleVAD] = {}
        self._initialized = False

    async def initialize(self):
        """Initialise le service vocal."""
        if self._initialized:
            return

        # Initialiser le client vocal
        self.voice_client = await get_voice_client(self.tenant_id, self.db)

        # Initialiser le gestionnaire de dialogue
        self.dialogue_manager = DialogueManager(self.tenant_id, self.db)

        self._initialized = True
        logger.info(f"[VoiceService] Initialise pour tenant {self.tenant_id}")
        logger.info(f"[VoiceService] STT: {self.voice_client.stt_provider}, TTS: {self.voice_client.tts_provider}")

    # ========================================================================
    # GESTION DES SESSIONS
    # ========================================================================

    async def start_session(
        self,
        caller_phone: str,
        customer_id: str | None = None,
        customer_name: str | None = None,
        config: VoiceSessionConfig | None = None
    ) -> VoiceSession:
        """
        Demarre une nouvelle session vocale.

        Args:
            caller_phone: Numero de telephone
            customer_id: ID client si connu
            customer_name: Nom du client si connu
            config: Configuration optionnelle

        Returns:
            Session vocale initialisee
        """
        if not self._initialized:
            await self.initialize()

        session_id = str(uuid.uuid4())
        config = config or VoiceSessionConfig()

        # Demarrer la conversation dans le dialogue manager
        dialogue_response = await self.dialogue_manager.start_conversation(
            caller_phone=caller_phone,
            customer_id=customer_id,
            customer_name=customer_name,
        )

        # Recuperer l'ID de conversation
        context = None
        for ctx in self.dialogue_manager._contexts.values():
            if ctx.caller_phone == caller_phone:
                context = ctx
                break

        conversation_id = context.conversation_id if context else session_id

        # Creer la session
        session = VoiceSession(
            id=session_id,
            tenant_id=self.tenant_id,
            conversation_id=conversation_id,
            state=SessionState.SPEAKING,  # On va parler le greeting
            config=config,
            caller_phone=caller_phone,
            customer_id=customer_id,
            customer_name=customer_name,
        )

        self._sessions[session_id] = session
        self._vads[session_id] = SimpleVAD(
            threshold=config.vad_threshold,
        )

        logger.info(f"[VoiceService] Session {session_id} demarree pour {caller_phone}")

        return session

    async def get_greeting_audio(self, session_id: str) -> VoiceResponse:
        """
        Obtient l'audio du message de bienvenue.

        Args:
            session_id: ID de la session

        Returns:
            Reponse vocale avec le greeting
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} non trouvee")

        context = self.dialogue_manager.get_context(session.conversation_id)
        if not context or not context.turns:
            greeting_text = "Bonjour, comment puis-je vous aider?"
        else:
            greeting_text = context.turns[0].text

        # Synthetiser le greeting
        synthesis = await self.voice_client.synthesize(greeting_text)

        session.state = SessionState.LISTENING
        session.response_count += 1

        return VoiceResponse(
            text=greeting_text,
            audio_data=synthesis.audio_data,
            audio_format=synthesis.format,
            audio_duration=synthesis.duration_seconds,
            dialogue_response=DialogueResponse(
                text=greeting_text,
                state=DialogueState.LISTENING,
                intent=None,
                entities={},
                actions=[],
                suggestions=["Demander un devis", "Prendre rendez-vous", "Support"],
            ),
            session_state=SessionState.LISTENING,
        )

    async def process_audio(
        self,
        session_id: str,
        audio_data: bytes,
        is_final: bool = False
    ) -> VoiceResponse | None:
        """
        Traite un chunk audio entrant.

        Args:
            session_id: ID de la session
            audio_data: Donnees audio (PCM 16-bit, mono, 16kHz)
            is_final: Indique si c'est le dernier chunk

        Returns:
            Reponse vocale si une reponse est prete, None sinon
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} non trouvee")

        vad = self._vads.get(session_id)
        if not vad:
            vad = SimpleVAD()
            self._vads[session_id] = vad

        session.last_activity = datetime.utcnow()

        # Analyser l'audio avec VAD
        stream_state = vad.process(audio_data)

        if stream_state == AudioStreamState.SPEECH:
            # Accumuler l'audio
            session.audio_buffer += audio_data
            session.is_speaking = True

            if session.speech_start_time is None:
                session.speech_start_time = datetime.utcnow()

            session.last_speech_time = datetime.utcnow()

            # Verifier si interruption pendant que Marceau parle
            if session.state == SessionState.SPEAKING and session.config.allow_interruptions:
                speech_duration = (datetime.utcnow() - session.speech_start_time).total_seconds() * 1000
                if speech_duration >= session.config.interrupt_threshold_ms:
                    logger.info(f"[VoiceService] Interruption detectee session {session_id}")
                    session.state = SessionState.LISTENING

            return None

        elif stream_state == AudioStreamState.END_OF_SPEECH or is_final:
            # Fin de parole detectee - traiter l'utterance
            if session.audio_buffer:
                return await self._process_utterance(session)

        elif stream_state == AudioStreamState.SILENCE:
            # Verifier timeout de silence
            if session.last_speech_time:
                silence_duration = (datetime.utcnow() - session.last_speech_time).total_seconds() * 1000
                if silence_duration >= session.config.silence_timeout_ms and session.audio_buffer:
                    return await self._process_utterance(session)

        return None

    async def process_text(
        self,
        session_id: str,
        text: str
    ) -> VoiceResponse:
        """
        Traite une entree texte directe.

        Args:
            session_id: ID de la session
            text: Texte a traiter

        Returns:
            Reponse vocale
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} non trouvee")

        session.last_activity = datetime.utcnow()
        session.utterance_count += 1

        # Traiter via dialogue manager
        dialogue_response = await self.dialogue_manager.process_utterance(
            session.conversation_id,
            text,
        )

        # Synthetiser la reponse
        synthesis = await self.voice_client.synthesize(dialogue_response.text)

        session.response_count += 1

        # Mettre a jour l'etat
        if dialogue_response.should_end:
            session.state = SessionState.ENDED
        elif dialogue_response.transfer_to:
            session.state = SessionState.PAUSED
        else:
            session.state = SessionState.LISTENING

        return VoiceResponse(
            text=dialogue_response.text,
            audio_data=synthesis.audio_data,
            audio_format=synthesis.format,
            audio_duration=synthesis.duration_seconds,
            dialogue_response=dialogue_response,
            session_state=session.state,
            should_end=dialogue_response.should_end,
            transfer_to=dialogue_response.transfer_to,
        )

    async def _process_utterance(self, session: VoiceSession) -> VoiceResponse:
        """Traite une utterance complete."""

        # Calculer la duree de parole
        if session.speech_start_time:
            speech_duration = (datetime.utcnow() - session.speech_start_time).total_seconds()
            session.total_speech_duration += speech_duration

        session.state = SessionState.PROCESSING

        try:
            # Transcrire l'audio
            transcription = await self.voice_client.transcribe(
                session.audio_buffer,
                language="fr",
            )

            text = transcription.text.strip()
            logger.info(f"[VoiceService] Transcription: {text}")

            if not text:
                # Pas de parole detectee
                session.audio_buffer = b""
                session.is_speaking = False
                session.speech_start_time = None
                session.state = SessionState.LISTENING
                return None

            session.utterance_count += 1

            # Traiter via dialogue manager
            dialogue_response = await self.dialogue_manager.process_utterance(
                session.conversation_id,
                text,
                audio_duration=transcription.duration_seconds,
            )

            # Synthetiser la reponse
            session.state = SessionState.SPEAKING
            synthesis = await self.voice_client.synthesize(dialogue_response.text)

            session.response_count += 1

            # Reset le buffer
            session.audio_buffer = b""
            session.is_speaking = False
            session.speech_start_time = None
            self._vads[session.id].reset()

            # Mettre a jour l'etat final
            if dialogue_response.should_end:
                session.state = SessionState.ENDED
            elif dialogue_response.transfer_to:
                session.state = SessionState.PAUSED
            else:
                session.state = SessionState.LISTENING

            return VoiceResponse(
                text=dialogue_response.text,
                audio_data=synthesis.audio_data,
                audio_format=synthesis.format,
                audio_duration=synthesis.duration_seconds,
                dialogue_response=dialogue_response,
                session_state=session.state,
                should_end=dialogue_response.should_end,
                transfer_to=dialogue_response.transfer_to,
            )

        except Exception as e:
            logger.error(f"[VoiceService] Erreur traitement utterance: {e}")
            session.state = SessionState.LISTENING
            session.audio_buffer = b""

            # Reponse d'erreur
            error_text = "Excusez-moi, je n'ai pas bien compris. Pouvez-vous repeter?"
            synthesis = await self.voice_client.synthesize(error_text)

            return VoiceResponse(
                text=error_text,
                audio_data=synthesis.audio_data,
                audio_format=synthesis.format,
                audio_duration=synthesis.duration_seconds,
                dialogue_response=DialogueResponse(
                    text=error_text,
                    state=DialogueState.LISTENING,
                    intent=None,
                    entities={},
                    actions=[],
                    suggestions=[],
                ),
                session_state=SessionState.LISTENING,
            )

    async def end_session(
        self,
        session_id: str,
        outcome: ConversationOutcome = ConversationOutcome.INFORMATION_PROVIDED
    ) -> dict:
        """
        Termine une session vocale.

        Args:
            session_id: ID de la session
            outcome: Resultat de la conversation

        Returns:
            Statistiques de la session
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} non trouvee")

        session.state = SessionState.ENDED

        # Terminer la conversation
        conversation_result = await self.dialogue_manager.end_conversation(
            session.conversation_id,
            outcome=outcome,
        )

        # Calculer les stats
        duration = (datetime.utcnow() - session.started_at).total_seconds()

        stats = {
            "session_id": session_id,
            "conversation_id": session.conversation_id,
            "duration_seconds": duration,
            "utterance_count": session.utterance_count,
            "response_count": session.response_count,
            "total_speech_duration": session.total_speech_duration,
            "outcome": outcome.value,
            "summary": conversation_result.get("summary"),
        }

        # Nettoyer
        del self._sessions[session_id]
        self._vads.pop(session_id, None)

        logger.info(f"[VoiceService] Session {session_id} terminee: {outcome.value}")

        return stats

    def get_session(self, session_id: str) -> VoiceSession | None:
        """Recupere une session."""
        return self._sessions.get(session_id)

    def get_active_sessions(self) -> list[VoiceSession]:
        """Liste les sessions actives."""
        return [
            s for s in self._sessions.values()
            if s.state not in [SessionState.ENDED]
        ]

    # ========================================================================
    # STREAMING
    # ========================================================================

    async def stream_response(
        self,
        session_id: str,
        text: str,
        chunk_size: int = 4096
    ) -> AsyncIterator[bytes]:
        """
        Stream la reponse audio par chunks.

        Args:
            session_id: ID de la session
            text: Texte a synthetiser
            chunk_size: Taille des chunks

        Yields:
            Chunks audio
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} non trouvee")

        session.state = SessionState.SPEAKING

        # Synthetiser
        synthesis = await self.voice_client.synthesize(text)

        # Streamer par chunks
        audio_data = synthesis.audio_data
        offset = 0

        while offset < len(audio_data):
            chunk = audio_data[offset:offset + chunk_size]
            yield chunk
            offset += chunk_size
            await asyncio.sleep(0.01)  # Petit delai pour le streaming

        session.state = SessionState.LISTENING
        session.response_count += 1

    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "fr"
    ) -> TranscriptionResult:
        """
        Transcrit de l'audio sans session.

        Args:
            audio_data: Donnees audio
            language: Langue

        Returns:
            Resultat de transcription
        """
        if not self._initialized:
            await self.initialize()

        return await self.voice_client.transcribe(audio_data, language)

    async def synthesize_text(
        self,
        text: str,
        voice: str | None = None
    ) -> SynthesisResult:
        """
        Synthetise du texte sans session.

        Args:
            text: Texte a synthetiser
            voice: Voix optionnelle

        Returns:
            Resultat de synthese
        """
        if not self._initialized:
            await self.initialize()

        return await self.voice_client.synthesize(text, voice)

    async def list_voices(self, language: str = "fr") -> list[dict]:
        """Liste les voix disponibles."""
        if not self._initialized:
            await self.initialize()

        return await self.voice_client.list_voices(language)

    def get_providers(self) -> dict:
        """Retourne les providers actifs."""
        if not self.voice_client:
            return {"stt": "not_initialized", "tts": "not_initialized"}

        return {
            "stt": self.voice_client.stt_provider,
            "tts": self.voice_client.tts_provider,
        }


# ============================================================================
# FACTORY ET SINGLETON
# ============================================================================

_voice_services: dict[str, VoiceService] = {}


async def get_voice_service(tenant_id: str, db: Session) -> VoiceService:
    """
    Recupere le service vocal pour un tenant.

    Args:
        tenant_id: ID du tenant
        db: Session SQLAlchemy

    Returns:
        Instance de VoiceService
    """
    global _voice_services

    if tenant_id not in _voice_services:
        service = VoiceService(tenant_id, db)
        await service.initialize()
        _voice_services[tenant_id] = service

    return _voice_services[tenant_id]


def reset_voice_service(tenant_id: str | None = None):
    """Reset le service vocal."""
    global _voice_services

    if tenant_id:
        _voice_services.pop(tenant_id, None)
    else:
        _voice_services.clear()
