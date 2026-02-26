"""
AZALS MODULE - Marceau Voice Client
====================================

Client vocal unifie pour reconnaissance vocale (STT) et synthese vocale (TTS).
Supporte plusieurs providers avec fallback automatique.

STT (Speech-to-Text):
    - Whisper (local via faster-whisper ou API OpenAI)
    - Google Speech-to-Text
    - Azure Speech Services
    - Mock (fallback)

TTS (Text-to-Speech):
    - Piper (local, haute qualite)
    - Google Text-to-Speech
    - Azure Speech Services
    - ElevenLabs (voix naturelles)
    - Mock (fallback)

Usage:
    from app.modules.marceau.voice_client import get_voice_client

    voice = await get_voice_client(tenant_id, db)

    # Reconnaissance vocale
    text = await voice.transcribe(audio_data, language="fr")

    # Synthese vocale
    audio = await voice.synthesize("Bonjour, comment puis-je vous aider?")
"""
from __future__ import annotations


import asyncio
import base64
import io
import json
import logging
import os
import tempfile
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO

logger = logging.getLogger(__name__)


# ============================================================================
# TYPES ET CONFIGURATIONS
# ============================================================================

class AudioFormat(str, Enum):
    """Formats audio supportes."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    WEBM = "webm"
    PCM = "pcm"


@dataclass
class TranscriptionResult:
    """Resultat d'une transcription."""
    text: str
    language: str
    confidence: float
    duration_seconds: float
    segments: list[dict] | None = None  # Segments avec timestamps
    words: list[dict] | None = None  # Mots avec timestamps


@dataclass
class SynthesisResult:
    """Resultat d'une synthese vocale."""
    audio_data: bytes
    format: AudioFormat
    sample_rate: int
    duration_seconds: float


@dataclass
class VoiceConfig:
    """Configuration vocale."""
    # STT
    stt_provider: str = "whisper"
    stt_model: str = "small"
    stt_language: str = "fr"

    # TTS
    tts_provider: str = "piper"
    tts_voice: str = "fr_FR-siwis-medium"
    tts_speed: float = 1.0
    tts_pitch: float = 1.0

    # Audio
    sample_rate: int = 16000
    channels: int = 1


# ============================================================================
# INTERFACE STT
# ============================================================================

class BaseSTTClient(ABC):
    """Interface de base pour les clients STT."""

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "fr",
        **kwargs
    ) -> TranscriptionResult:
        """Transcrit un fichier audio en texte."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Verifie si le provider est disponible."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nom du provider."""
        pass


class WhisperSTTClient(BaseSTTClient):
    """
    Client Whisper pour STT.
    Utilise faster-whisper (local) ou API OpenAI.
    """

    def __init__(
        self,
        model: str = "small",
        use_api: bool = False,
        api_key: str | None = None,
        device: str = "auto"
    ):
        self.model_name = model
        self.use_api = use_api
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.device = device
        self._model = None

    @property
    def provider_name(self) -> str:
        return "whisper_api" if self.use_api else "whisper_local"

    async def is_available(self) -> bool:
        """Verifie disponibilite."""
        if self.use_api:
            return bool(self.api_key)

        try:
            # Verifier si faster-whisper est installe
            import faster_whisper
            return True
        except ImportError:
            return False

    def _load_model(self):
        """Charge le modele Whisper local."""
        if self._model is None and not self.use_api:
            try:
                from faster_whisper import WhisperModel

                # Detecter le device
                device = self.device
                if device == "auto":
                    try:
                        import torch
                        device = "cuda" if torch.cuda.is_available() else "cpu"
                    except ImportError:
                        device = "cpu"

                compute_type = "float16" if device == "cuda" else "int8"

                self._model = WhisperModel(
                    self.model_name,
                    device=device,
                    compute_type=compute_type
                )
                logger.info(f"[Voice] Modele Whisper {self.model_name} charge sur {device}")

            except Exception as e:
                logger.error(f"[Voice] Erreur chargement Whisper: {e}")
                raise

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "fr",
        **kwargs
    ) -> TranscriptionResult:
        """Transcrit l'audio via Whisper."""

        if self.use_api:
            return await self._transcribe_api(audio_data, language, **kwargs)
        else:
            return await self._transcribe_local(audio_data, language, **kwargs)

    async def _transcribe_api(
        self,
        audio_data: bytes,
        language: str,
        **kwargs
    ) -> TranscriptionResult:
        """Transcription via API OpenAI."""
        import httpx

        # Sauvegarder temporairement l'audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(temp_path, "rb") as audio_file:
                    response = await client.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files={"file": ("audio.wav", audio_file, "audio/wav")},
                        data={
                            "model": "whisper-1",
                            "language": language,
                            "response_format": "verbose_json",
                        }
                    )
                    response.raise_for_status()
                    data = response.json()

            return TranscriptionResult(
                text=data.get("text", ""),
                language=data.get("language", language),
                confidence=1.0,  # API ne retourne pas de confidence
                duration_seconds=data.get("duration", 0),
                segments=data.get("segments"),
                words=data.get("words"),
            )

        finally:
            os.unlink(temp_path)

    async def _transcribe_local(
        self,
        audio_data: bytes,
        language: str,
        **kwargs
    ) -> TranscriptionResult:
        """Transcription via faster-whisper local."""

        # Charger le modele si necessaire
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model)

        # Sauvegarder temporairement l'audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            # Transcription
            segments, info = await loop.run_in_executor(
                None,
                lambda: self._model.transcribe(
                    temp_path,
                    language=language,
                    beam_size=5,
                    word_timestamps=True,
                    vad_filter=True,
                )
            )

            # Collecter les segments
            text_parts = []
            segment_list = []

            for segment in segments:
                text_parts.append(segment.text)
                segment_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "confidence": segment.avg_logprob,
                })

            return TranscriptionResult(
                text=" ".join(text_parts).strip(),
                language=info.language,
                confidence=info.language_probability,
                duration_seconds=info.duration,
                segments=segment_list,
            )

        finally:
            os.unlink(temp_path)


class GoogleSTTClient(BaseSTTClient):
    """Client Google Speech-to-Text."""

    def __init__(self, credentials_path: str | None = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    @property
    def provider_name(self) -> str:
        return "google_stt"

    async def is_available(self) -> bool:
        """Verifie si les credentials sont configures."""
        if self.credentials_path and os.path.exists(self.credentials_path):
            return True
        return bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "fr",
        **kwargs
    ) -> TranscriptionResult:
        """Transcription via Google Speech API."""
        try:
            from google.cloud import speech

            client = speech.SpeechClient()

            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=kwargs.get("sample_rate", 16000),
                language_code=f"{language}-FR" if language == "fr" else language,
                enable_word_time_offsets=True,
                enable_automatic_punctuation=True,
            )

            response = client.recognize(config=config, audio=audio)

            text_parts = []
            confidence_sum = 0
            word_count = 0

            for result in response.results:
                alternative = result.alternatives[0]
                text_parts.append(alternative.transcript)
                confidence_sum += alternative.confidence
                word_count += 1

            return TranscriptionResult(
                text=" ".join(text_parts),
                language=language,
                confidence=confidence_sum / max(word_count, 1),
                duration_seconds=0,  # Non fourni par l'API
            )

        except Exception as e:
            logger.error(f"[Voice] Erreur Google STT: {e}")
            raise


class MockSTTClient(BaseSTTClient):
    """Client STT mock pour tests."""

    @property
    def provider_name(self) -> str:
        return "mock_stt"

    async def is_available(self) -> bool:
        return True

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "fr",
        **kwargs
    ) -> TranscriptionResult:
        """Retourne une transcription mock."""
        logger.warning("[Voice] Utilisation du STT mock")
        return TranscriptionResult(
            text="[Transcription mock - STT non configure]",
            language=language,
            confidence=0.0,
            duration_seconds=len(audio_data) / 32000,  # Estimation
        )


# ============================================================================
# INTERFACE TTS
# ============================================================================

class BaseTTSClient(ABC):
    """Interface de base pour les clients TTS."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        **kwargs
    ) -> SynthesisResult:
        """Synthetise du texte en audio."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Verifie si le provider est disponible."""
        pass

    @abstractmethod
    async def list_voices(self, language: str = "fr") -> list[dict]:
        """Liste les voix disponibles."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nom du provider."""
        pass


class PiperTTSClient(BaseTTSClient):
    """
    Client Piper pour TTS local.
    Voix naturelles en local, rapide et gratuit.
    """

    # Voix francaises Piper disponibles
    FRENCH_VOICES = {
        "fr_FR-siwis-medium": "Siwis (femme, naturel)",
        "fr_FR-upmc-medium": "UPMC (homme)",
        "fr_FR-gilles-low": "Gilles (homme, economique)",
        "fr_FR-mls-medium": "MLS (mixte)",
    }

    def __init__(
        self,
        models_dir: str | None = None,
        default_voice: str = "fr_FR-siwis-medium"
    ):
        self.models_dir = models_dir or os.path.expanduser("~/.local/share/piper/models")
        self.default_voice = default_voice
        self._piper_path = None

    @property
    def provider_name(self) -> str:
        return "piper"

    async def is_available(self) -> bool:
        """Verifie si Piper est installe."""
        import shutil

        # Chercher l'executable piper
        self._piper_path = shutil.which("piper")
        if self._piper_path:
            return True

        # Chercher dans les chemins communs
        common_paths = [
            "/usr/bin/piper",
            "/usr/local/bin/piper",
            os.path.expanduser("~/.local/bin/piper"),
        ]
        for path in common_paths:
            if os.path.exists(path):
                self._piper_path = path
                return True

        return False

    async def list_voices(self, language: str = "fr") -> list[dict]:
        """Liste les voix disponibles."""
        voices = []
        for voice_id, description in self.FRENCH_VOICES.items():
            if language in voice_id:
                voices.append({
                    "id": voice_id,
                    "name": description,
                    "language": language,
                    "gender": "female" if "femme" in description.lower() else "male",
                })
        return voices

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        **kwargs
    ) -> SynthesisResult:
        """Synthetise via Piper."""
        voice = voice or self.default_voice

        if not self._piper_path:
            await self.is_available()

        if not self._piper_path:
            raise RuntimeError("Piper non disponible")

        # Chemin du modele
        model_path = os.path.join(self.models_dir, f"{voice}.onnx")

        # Verifier si le modele existe
        if not os.path.exists(model_path):
            logger.warning(f"[Voice] Modele {voice} non trouve, telechargement necessaire")
            # Fallback vers un modele disponible ou erreur
            raise FileNotFoundError(f"Modele Piper {voice} non trouve dans {self.models_dir}")

        # Fichier de sortie temporaire
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name

        try:
            # Executer Piper
            process = await asyncio.create_subprocess_exec(
                self._piper_path,
                "--model", model_path,
                "--output_file", output_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate(text.encode("utf-8"))

            if process.returncode != 0:
                raise RuntimeError(f"Piper erreur: {stderr.decode()}")

            # Lire le fichier audio
            with open(output_path, "rb") as f:
                audio_data = f.read()

            # Obtenir la duree
            with wave.open(output_path, "rb") as wav:
                frames = wav.getnframes()
                sample_rate = wav.getframerate()
                duration = frames / sample_rate

            return SynthesisResult(
                audio_data=audio_data,
                format=AudioFormat.WAV,
                sample_rate=sample_rate,
                duration_seconds=duration,
            )

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class ElevenLabsTTSClient(BaseTTSClient):
    """Client ElevenLabs pour TTS haute qualite."""

    DEFAULT_VOICES = {
        "Rachel": "21m00Tcm4TlvDq8ikWAM",
        "Domi": "AZnzlk1XvdvUeBnXmlld",
        "Bella": "EXAVITQu4vr4xnSDxMaL",
        "Antoni": "ErXwobaYiN019PkySvjV",
        "Thomas": "GBv7mTt0atIp3Br8iCZE",
    }

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"

    @property
    def provider_name(self) -> str:
        return "elevenlabs"

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def list_voices(self, language: str = "fr") -> list[dict]:
        """Liste les voix ElevenLabs."""
        if not self.api_key:
            return []

        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()

                return [
                    {
                        "id": v["voice_id"],
                        "name": v["name"],
                        "language": "multi",
                        "preview_url": v.get("preview_url"),
                    }
                    for v in data.get("voices", [])
                ]
        except Exception as e:
            logger.error(f"[Voice] Erreur liste voix ElevenLabs: {e}")
            return []

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        **kwargs
    ) -> SynthesisResult:
        """Synthetise via ElevenLabs."""
        import httpx

        if not self.api_key:
            raise ValueError("Cle API ElevenLabs non configuree")

        voice_id = voice or self.DEFAULT_VOICES.get("Rachel", list(self.DEFAULT_VOICES.values())[0])

        # Si c'est un nom de voix, convertir en ID
        if voice in self.DEFAULT_VOICES:
            voice_id = self.DEFAULT_VOICES[voice]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": kwargs.get("model_id", "eleven_multilingual_v2"),
                    "voice_settings": {
                        "stability": kwargs.get("stability", 0.5),
                        "similarity_boost": kwargs.get("similarity_boost", 0.75),
                    }
                }
            )
            response.raise_for_status()
            audio_data = response.content

        return SynthesisResult(
            audio_data=audio_data,
            format=AudioFormat.MP3,
            sample_rate=44100,
            duration_seconds=len(audio_data) / 20000,  # Estimation
        )


class GoogleTTSClient(BaseTTSClient):
    """Client Google Text-to-Speech."""

    def __init__(self, credentials_path: str | None = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    @property
    def provider_name(self) -> str:
        return "google_tts"

    async def is_available(self) -> bool:
        if self.credentials_path and os.path.exists(self.credentials_path):
            return True
        return bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

    async def list_voices(self, language: str = "fr") -> list[dict]:
        """Liste les voix Google TTS."""
        try:
            from google.cloud import texttospeech

            client = texttospeech.TextToSpeechClient()
            response = client.list_voices(language_code=f"{language}-FR")

            return [
                {
                    "id": voice.name,
                    "name": voice.name,
                    "language": language,
                    "gender": voice.ssml_gender.name,
                }
                for voice in response.voices
            ]
        except Exception:
            return []

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        **kwargs
    ) -> SynthesisResult:
        """Synthetise via Google TTS."""
        from google.cloud import texttospeech

        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice_config = texttospeech.VoiceSelectionParams(
            language_code=kwargs.get("language", "fr-FR"),
            name=voice or "fr-FR-Neural2-A",
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=kwargs.get("sample_rate", 24000),
            speaking_rate=kwargs.get("speed", 1.0),
            pitch=kwargs.get("pitch", 0.0),
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_config,
            audio_config=audio_config,
        )

        return SynthesisResult(
            audio_data=response.audio_content,
            format=AudioFormat.WAV,
            sample_rate=24000,
            duration_seconds=len(response.audio_content) / 48000,
        )


class MockTTSClient(BaseTTSClient):
    """Client TTS mock pour tests."""

    @property
    def provider_name(self) -> str:
        return "mock_tts"

    async def is_available(self) -> bool:
        return True

    async def list_voices(self, language: str = "fr") -> list[dict]:
        return [{"id": "mock", "name": "Mock Voice", "language": language}]

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        **kwargs
    ) -> SynthesisResult:
        """Genere un fichier WAV vide."""
        logger.warning("[Voice] Utilisation du TTS mock")

        # Generer un WAV silencieux de 1 seconde
        sample_rate = 16000
        duration = 1.0
        num_samples = int(sample_rate * duration)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(b"\x00\x00" * num_samples)

        return SynthesisResult(
            audio_data=buffer.getvalue(),
            format=AudioFormat.WAV,
            sample_rate=sample_rate,
            duration_seconds=duration,
        )


# ============================================================================
# CLIENT UNIFIE
# ============================================================================

class VoiceClient:
    """
    Client vocal unifie.
    Combine STT et TTS avec detection automatique des providers.
    """

    def __init__(
        self,
        stt_client: BaseSTTClient,
        tts_client: BaseTTSClient,
        config: VoiceConfig | None = None
    ):
        self.stt = stt_client
        self.tts = tts_client
        self.config = config or VoiceConfig()

    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
        **kwargs
    ) -> TranscriptionResult:
        """Transcrit l'audio en texte."""
        lang = language or self.config.stt_language
        return await self.stt.transcribe(audio_data, language=lang, **kwargs)

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        **kwargs
    ) -> SynthesisResult:
        """Synthetise le texte en audio."""
        v = voice or self.config.tts_voice
        return await self.tts.synthesize(text, voice=v, **kwargs)

    async def list_voices(self, language: str = "fr") -> list[dict]:
        """Liste les voix TTS disponibles."""
        return await self.tts.list_voices(language)

    @property
    def stt_provider(self) -> str:
        return self.stt.provider_name

    @property
    def tts_provider(self) -> str:
        return self.tts.provider_name


# ============================================================================
# FACTORY
# ============================================================================

class VoiceClientFactory:
    """Factory pour creer les clients vocaux."""

    STT_PROVIDERS = ["whisper_local", "whisper_api", "google_stt", "mock"]
    TTS_PROVIDERS = ["piper", "elevenlabs", "google_tts", "mock"]

    @classmethod
    async def create_stt(cls, provider: str = "auto", config: dict | None = None) -> BaseSTTClient:
        """Cree un client STT."""
        config = config or {}

        if provider != "auto":
            return cls._create_stt_provider(provider, config)

        # Detection automatique
        for prov in cls.STT_PROVIDERS:
            client = cls._create_stt_provider(prov, config)
            if await client.is_available():
                logger.info(f"[Voice] STT provider detecte: {prov}")
                return client

        return MockSTTClient()

    @classmethod
    async def create_tts(cls, provider: str = "auto", config: dict | None = None) -> BaseTTSClient:
        """Cree un client TTS."""
        config = config or {}

        if provider != "auto":
            return cls._create_tts_provider(provider, config)

        # Detection automatique
        for prov in cls.TTS_PROVIDERS:
            client = cls._create_tts_provider(prov, config)
            if await client.is_available():
                logger.info(f"[Voice] TTS provider detecte: {prov}")
                return client

        return MockTTSClient()

    @classmethod
    def _create_stt_provider(cls, provider: str, config: dict) -> BaseSTTClient:
        """Cree une instance de STT provider."""
        if provider == "whisper_local":
            return WhisperSTTClient(
                model=config.get("stt_model", "small"),
                use_api=False,
                device=config.get("whisper_device", "auto"),
            )
        elif provider == "whisper_api":
            return WhisperSTTClient(
                use_api=True,
                api_key=config.get("openai_api_key"),
            )
        elif provider == "google_stt":
            return GoogleSTTClient(
                credentials_path=config.get("google_credentials"),
            )
        else:
            return MockSTTClient()

    @classmethod
    def _create_tts_provider(cls, provider: str, config: dict) -> BaseTTSClient:
        """Cree une instance de TTS provider."""
        if provider == "piper":
            return PiperTTSClient(
                models_dir=config.get("piper_models_dir"),
                default_voice=config.get("tts_voice", "fr_FR-siwis-medium"),
            )
        elif provider == "elevenlabs":
            return ElevenLabsTTSClient(
                api_key=config.get("elevenlabs_api_key"),
            )
        elif provider == "google_tts":
            return GoogleTTSClient(
                credentials_path=config.get("google_credentials"),
            )
        else:
            return MockTTSClient()

    @classmethod
    async def create(
        cls,
        stt_provider: str = "auto",
        tts_provider: str = "auto",
        config: dict | None = None
    ) -> VoiceClient:
        """Cree un client vocal complet."""
        config = config or {}

        stt = await cls.create_stt(stt_provider, config)
        tts = await cls.create_tts(tts_provider, config)

        voice_config = VoiceConfig(
            stt_provider=stt.provider_name,
            stt_model=config.get("stt_model", "small"),
            stt_language=config.get("stt_language", "fr"),
            tts_provider=tts.provider_name,
            tts_voice=config.get("tts_voice", "fr_FR-siwis-medium"),
            tts_speed=config.get("tts_speed", 1.0),
        )

        return VoiceClient(stt, tts, voice_config)


# ============================================================================
# SINGLETON ET HELPERS
# ============================================================================

_voice_clients: dict[str, VoiceClient] = {}


async def get_voice_client(
    tenant_id: str | None = None,
    db=None,
) -> VoiceClient:
    """
    Recupere le client vocal pour un tenant.

    Args:
        tenant_id: ID du tenant
        db: Session SQLAlchemy

    Returns:
        Instance de VoiceClient
    """
    global _voice_clients

    cache_key = tenant_id or "default"

    if cache_key not in _voice_clients:
        config = {}

        # Charger la config tenant si disponible
        if tenant_id and db:
            try:
                from .config import get_or_create_marceau_config
                marceau_config = get_or_create_marceau_config(tenant_id, db)
                config = marceau_config.integrations or {}
                config["stt_model"] = marceau_config.stt_model
                config["tts_voice"] = marceau_config.tts_voice
            except Exception as e:
                logger.warning(f"[Voice] Erreur chargement config: {e}")

        _voice_clients[cache_key] = await VoiceClientFactory.create(config=config)

    return _voice_clients[cache_key]


def reset_voice_client(tenant_id: str | None = None):
    """Reset le client vocal."""
    global _voice_clients

    if tenant_id:
        _voice_clients.pop(tenant_id, None)
    else:
        _voice_clients.clear()
