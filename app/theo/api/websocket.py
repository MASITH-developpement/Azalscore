"""
THÉO — WebSocket API
=====================

WebSocket endpoint pour la communication temps réel avec Théo.
Gère le flux audio bidirectionnel et les messages de contrôle.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from dataclasses import dataclass
from enum import Enum
import json
import base64
import asyncio
import logging

from app.theo.core.orchestrator import get_theo_orchestrator, OrchestratorResult
from app.theo.core.session_manager import get_session_manager, AuthorityLevel
from app.theo.voice.stt_service import get_stt_service
from app.theo.voice.tts_service import get_tts_service
from app.theo.companions import get_companion_registry, get_translator

logger = logging.getLogger(__name__)

theo_router = APIRouter(prefix="/theo", tags=["Theo Voice Assistant"])


# ============================================================
# MESSAGE TYPES
# ============================================================

class MessageType(str, Enum):
    """Types de messages WebSocket."""

    # Client → Server
    AUDIO_CHUNK = "audio_chunk"           # Chunk audio à transcrire
    AUDIO_END = "audio_end"               # Fin de l'enregistrement audio
    TEXT_INPUT = "text_input"             # Entrée texte (fallback)
    TRANSCRIPTION = "transcription"       # Transcription du client (Web Speech API)
    CONTROL = "control"                   # Commande de contrôle

    # Server → Client
    LISTENING = "listening"               # Théo écoute
    PROCESSING = "processing"             # Traitement en cours
    TRANSCRIPTION_RESULT = "transcription_result"  # Résultat STT
    RESPONSE = "response"                 # Réponse de Théo
    AUDIO_RESPONSE = "audio_response"     # Chunk audio TTS
    AUDIO_RESPONSE_END = "audio_response_end"  # Fin audio TTS
    VISUAL_STATE = "visual_state"         # État visuel du compagnon
    ERROR = "error"                       # Erreur
    SESSION_INFO = "session_info"         # Info session


@dataclass
class WSMessage:
    """Message WebSocket structuré."""
    type: MessageType
    payload: Dict[str, Any]
    timestamp: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "payload": self.payload,
            "timestamp": self.timestamp
        })

    @classmethod
    def from_json(cls, data: str) -> "WSMessage":
        parsed = json.loads(data)
        return cls(
            type=MessageType(parsed["type"]),
            payload=parsed.get("payload", {}),
            timestamp=parsed.get("timestamp")
        )


# ============================================================
# CONNECTION MANAGER
# ============================================================

class TheoWebSocketManager:
    """Gestionnaire de connexions WebSocket Théo."""

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}  # session_id → websocket
        self._audio_buffers: Dict[str, bytes] = {}    # session_id → audio buffer

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str
    ) -> None:
        """Accepte une nouvelle connexion."""
        await websocket.accept()
        self._connections[session_id] = websocket
        self._audio_buffers[session_id] = b""
        logger.info(f"[TheoWS] Connected: {session_id}")

    def disconnect(self, session_id: str) -> None:
        """Déconnecte une session."""
        self._connections.pop(session_id, None)
        self._audio_buffers.pop(session_id, None)
        logger.info(f"[TheoWS] Disconnected: {session_id}")

    async def send(
        self,
        session_id: str,
        message: WSMessage
    ) -> None:
        """Envoie un message à une session."""
        websocket = self._connections.get(session_id)
        if websocket:
            await websocket.send_text(message.to_json())

    async def send_json(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Envoie un dict JSON à une session."""
        websocket = self._connections.get(session_id)
        if websocket:
            await websocket.send_json(data)

    def add_audio_chunk(self, session_id: str, chunk: bytes) -> None:
        """Ajoute un chunk audio au buffer."""
        if session_id in self._audio_buffers:
            self._audio_buffers[session_id] += chunk

    def get_audio_buffer(self, session_id: str) -> bytes:
        """Récupère le buffer audio."""
        return self._audio_buffers.get(session_id, b"")

    def clear_audio_buffer(self, session_id: str) -> None:
        """Vide le buffer audio."""
        if session_id in self._audio_buffers:
            self._audio_buffers[session_id] = b""

    def get_active_connections(self) -> List[str]:
        """Liste les sessions actives."""
        return list(self._connections.keys())


# Singleton
ws_manager = TheoWebSocketManager()


# ============================================================
# WEBSOCKET ENDPOINT
# ============================================================

@theo_router.websocket("/ws")
async def theo_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    companion: str = Query("theo"),
    mode: str = Query("driving")
):
    """
    WebSocket principal pour Théo.

    Query params:
        token: Token d'authentification (optionnel)
        companion: ID du compagnon (theo, lea, alex)
        mode: Mode d'interaction (driving, desktop, mobile)

    Message protocol:
        Client → Server:
            - audio_chunk: {data: base64, format: "webm"}
            - audio_end: {}
            - text_input: {text: "..."}
            - transcription: {text: "...", confidence: 0.9, is_final: true}
            - control: {action: "stop|pause|resume"}

        Server → Client:
            - listening: {}
            - processing: {}
            - transcription_result: {text: "...", confidence: 0.9}
            - response: {text: "...", intent: {...}}
            - audio_response: {data: base64, format: "mp3"}
            - audio_response_end: {}
            - visual_state: {state: "idle|listening|processing|speaking"}
            - error: {message: "...", code: "..."}
    """
    # Créer ou récupérer la session
    session_manager = get_session_manager()
    orchestrator = get_theo_orchestrator()
    translator = get_translator()
    companion_registry = get_companion_registry()

    # Extraire user_id et tenant_id du token si présent
    # TODO: Intégrer avec le système d'auth existant
    user_id = None
    tenant_id = None
    authority_level = AuthorityLevel.USER

    # Créer la session
    session = session_manager.create(
        user_id=user_id,
        tenant_id=tenant_id,
        companion_id=companion,
        authority_level=authority_level,
        mode=mode
    )
    session_id = session.session_id

    # Connexion WebSocket
    await ws_manager.connect(websocket, session_id)

    # Envoyer info session
    await ws_manager.send(
        session_id,
        WSMessage(
            type=MessageType.SESSION_INFO,
            payload={
                "session_id": session_id,
                "companion": companion,
                "mode": mode,
                "state": session.state.value
            }
        )
    )

    try:
        while True:
            # Recevoir message
            data = await websocket.receive_text()

            try:
                message = WSMessage.from_json(data)
            except Exception as e:
                await ws_manager.send(
                    session_id,
                    WSMessage(
                        type=MessageType.ERROR,
                        payload={"message": f"Invalid message format: {e}"}
                    )
                )
                continue

            # Router selon le type de message
            if message.type == MessageType.AUDIO_CHUNK:
                await handle_audio_chunk(session_id, message.payload)

            elif message.type == MessageType.AUDIO_END:
                await handle_audio_end(session_id, session, orchestrator)

            elif message.type == MessageType.TEXT_INPUT:
                await handle_text_input(
                    session_id, session, orchestrator,
                    message.payload.get("text", "")
                )

            elif message.type == MessageType.TRANSCRIPTION:
                # Transcription Web Speech API du client
                await handle_client_transcription(
                    session_id, session, orchestrator, translator,
                    message.payload
                )

            elif message.type == MessageType.CONTROL:
                await handle_control(session_id, session, message.payload)

    except WebSocketDisconnect:
        logger.info(f"[TheoWS] Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"[TheoWS] Error: {e}")
        await ws_manager.send(
            session_id,
            WSMessage(
                type=MessageType.ERROR,
                payload={"message": str(e)}
            )
        )
    finally:
        ws_manager.disconnect(session_id)
        session_manager.end(session_id)


# ============================================================
# MESSAGE HANDLERS
# ============================================================

async def handle_audio_chunk(session_id: str, payload: Dict[str, Any]) -> None:
    """Gère un chunk audio entrant."""
    audio_data = payload.get("data", "")
    if audio_data:
        chunk = base64.b64decode(audio_data)
        ws_manager.add_audio_chunk(session_id, chunk)


async def handle_audio_end(
    session_id: str,
    session: Any,
    orchestrator: Any
) -> None:
    """Gère la fin de l'enregistrement audio."""
    # Signaler le traitement
    await ws_manager.send(
        session_id,
        WSMessage(type=MessageType.PROCESSING, payload={})
    )

    # Récupérer le buffer audio
    audio_data = ws_manager.get_audio_buffer(session_id)
    ws_manager.clear_audio_buffer(session_id)

    if not audio_data:
        await ws_manager.send(
            session_id,
            WSMessage(
                type=MessageType.ERROR,
                payload={"message": "No audio data received"}
            )
        )
        return

    try:
        # Transcrire avec STT
        stt_service = get_stt_service()
        result = await stt_service.transcribe(audio_data, format="webm")

        # Envoyer le résultat de transcription
        await ws_manager.send(
            session_id,
            WSMessage(
                type=MessageType.TRANSCRIPTION_RESULT,
                payload={
                    "text": result.text,
                    "confidence": result.confidence,
                    "language": result.language
                }
            )
        )

        # Traiter avec l'orchestrateur
        await process_transcription(session_id, session, orchestrator, result.text)

    except Exception as e:
        logger.error(f"[TheoWS] STT error: {e}")
        await ws_manager.send(
            session_id,
            WSMessage(
                type=MessageType.ERROR,
                payload={"message": f"Transcription error: {e}"}
            )
        )


async def handle_text_input(
    session_id: str,
    session: Any,
    orchestrator: Any,
    text: str
) -> None:
    """Gère une entrée texte directe."""
    if not text.strip():
        return

    await ws_manager.send(
        session_id,
        WSMessage(type=MessageType.PROCESSING, payload={})
    )

    await process_transcription(session_id, session, orchestrator, text)


async def handle_client_transcription(
    session_id: str,
    session: Any,
    orchestrator: Any,
    translator: Any,
    payload: Dict[str, Any]
) -> None:
    """Gère une transcription Web Speech API du client."""
    text = payload.get("text", "")
    is_final = payload.get("is_final", True)
    confidence = payload.get("confidence", 0.9)

    if not text.strip() or not is_final:
        return

    await ws_manager.send(
        session_id,
        WSMessage(type=MessageType.PROCESSING, payload={})
    )

    # Traduire si c'est un compagnon
    translation = translator.translate(text)

    # Utiliser le texte traduit
    await process_transcription(
        session_id, session, orchestrator,
        translation.translated_text,
        companion_id=translation.companion_id
    )


async def handle_control(
    session_id: str,
    session: Any,
    payload: Dict[str, Any]
) -> None:
    """Gère les commandes de contrôle."""
    action = payload.get("action", "")

    if action == "stop":
        # Annuler l'action en cours
        session.clear_pending_action()
        await ws_manager.send(
            session_id,
            WSMessage(
                type=MessageType.VISUAL_STATE,
                payload={"state": "idle"}
            )
        )

    elif action == "pause":
        from app.theo.core.session_manager import SessionState
        session.state = SessionState.PAUSED
        await ws_manager.send(
            session_id,
            WSMessage(
                type=MessageType.VISUAL_STATE,
                payload={"state": "paused"}
            )
        )

    elif action == "resume":
        from app.theo.core.session_manager import SessionState
        session.state = SessionState.IDLE
        await ws_manager.send(
            session_id,
            WSMessage(
                type=MessageType.VISUAL_STATE,
                payload={"state": "idle"}
            )
        )


async def process_transcription(
    session_id: str,
    session: Any,
    orchestrator: Any,
    text: str,
    companion_id: Optional[str] = None
) -> None:
    """Traite une transcription et génère la réponse."""

    # Mettre à jour le compagnon si différent
    if companion_id and companion_id != session.companion_id:
        session.companion_id = companion_id

    # Traiter avec l'orchestrateur
    result: OrchestratorResult = await orchestrator.process(
        session.session_id,
        text,
        context={
            "current_page": session.current_page,
            "companion_id": session.companion_id
        }
    )

    # Envoyer l'état visuel
    await ws_manager.send(
        session_id,
        WSMessage(
            type=MessageType.VISUAL_STATE,
            payload={"state": result.visual_state}
        )
    )

    # Envoyer la réponse texte
    await ws_manager.send(
        session_id,
        WSMessage(
            type=MessageType.RESPONSE,
            payload={
                "text": result.speech_text,
                "type": result.type.value,
                "session_state": result.session_state.value,
                "intent": result.intent.to_dict() if result.intent else None,
                "action_result": result.action_result
            }
        )
    )

    # Générer et streamer l'audio TTS
    if result.speech_text:
        await stream_tts_response(session_id, session, result.speech_text)

    # Retour à l'état d'écoute
    await ws_manager.send(
        session_id,
        WSMessage(
            type=MessageType.VISUAL_STATE,
            payload={"state": "idle"}
        )
    )


async def stream_tts_response(
    session_id: str,
    session: Any,
    text: str
) -> None:
    """Génère et streame la réponse TTS."""
    try:
        # Récupérer la voix du compagnon
        companion_registry = get_companion_registry()
        companion = companion_registry.get(session.companion_id)
        voice_id = companion.voice.voice_id if companion else None

        # État visuel: speaking
        await ws_manager.send(
            session_id,
            WSMessage(
                type=MessageType.VISUAL_STATE,
                payload={"state": "speaking"}
            )
        )

        # Streamer l'audio
        tts_service = get_tts_service()

        async for chunk in tts_service.synthesize_stream(
            text,
            voice_id=voice_id,
            format="mp3"
        ):
            # Encoder en base64 et envoyer
            chunk_b64 = base64.b64encode(chunk).decode("utf-8")
            await ws_manager.send(
                session_id,
                WSMessage(
                    type=MessageType.AUDIO_RESPONSE,
                    payload={"data": chunk_b64, "format": "mp3"}
                )
            )

        # Fin de l'audio
        await ws_manager.send(
            session_id,
            WSMessage(
                type=MessageType.AUDIO_RESPONSE_END,
                payload={}
            )
        )

    except Exception as e:
        logger.error(f"[TheoWS] TTS error: {e}")
        # Pas d'erreur critique - le texte a déjà été envoyé


# ============================================================
# REST ENDPOINTS (pour debugging/admin)
# ============================================================

@theo_router.get("/sessions")
async def list_sessions():
    """Liste les sessions actives."""
    session_manager = get_session_manager()
    return {
        "active_websockets": ws_manager.get_active_connections(),
        "sessions": session_manager.status()
    }


@theo_router.get("/status")
async def theo_status():
    """Statut de Théo."""
    orchestrator = get_theo_orchestrator()
    return {
        "status": "operational",
        "orchestrator": orchestrator.status()
    }
