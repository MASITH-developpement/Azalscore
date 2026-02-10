"""
THÉO Voice — Services Vocaux
============================

STT (Speech-to-Text) et TTS (Text-to-Speech) avec abstractions
pour permettre le remplacement des providers à tout moment.
"""

from app.theo.voice.stt_service import STTService, STTResult, get_stt_service
from app.theo.voice.tts_service import TTSService, TTSResult, get_tts_service

__all__ = [
    "STTService",
    "STTResult",
    "get_stt_service",
    "TTSService",
    "TTSResult",
    "get_tts_service",
]
