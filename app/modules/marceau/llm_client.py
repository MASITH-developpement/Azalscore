"""
AZALS MODULE - Marceau LLM Client Multi-Provider
=================================================

Client LLM unifie supportant plusieurs providers avec fallback automatique.
Ordre de priorite: Ollama (local) > Anthropic > OpenAI > Mock

Usage:
    from app.modules.marceau.llm_client import get_llm_client

    llm = get_llm_client()
    response = await llm.generate("Ton prompt ici")
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# INTERFACE DE BASE
# ============================================================================

class BaseLLMClient(ABC):
    """Interface de base pour tous les clients LLM."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        system_prompt: str | None = None,
    ) -> str:
        """
        Genere une reponse a partir d'un prompt.

        Args:
            prompt: Le prompt utilisateur
            model: Modele specifique (optionnel, utilise le defaut)
            temperature: Temperature de generation (0-1)
            max_tokens: Nombre max de tokens en sortie
            system_prompt: Prompt systeme optionnel

        Returns:
            La reponse generee
        """
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


# ============================================================================
# OLLAMA CLIENT (PRIORITAIRE)
# ============================================================================

class OllamaClient(BaseLLMClient):
    """
    Client pour Ollama (LLM local).
    Prioritaire car gratuit et sans latence reseau externe.
    """

    DEFAULT_MODEL = "llama3:8b-instruct-q4_0"
    FALLBACK_MODELS = ["mistral:7b-instruct", "llama2:7b", "phi3:mini"]

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._available_models: list[str] | None = None

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def is_available(self) -> bool:
        """Verifie si Ollama est en cours d'execution."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    self._available_models = [m["name"] for m in data.get("models", [])]
                    return len(self._available_models) > 0
                return False
        except Exception as e:
            logger.debug(f"[LLM] Ollama non disponible: {e}")
            return False

    async def _get_best_model(self, requested: str | None) -> str:
        """Trouve le meilleur modele disponible."""
        if self._available_models is None:
            await self.is_available()

        if not self._available_models:
            return self.DEFAULT_MODEL

        # Si le modele demande est disponible
        if requested and requested in self._available_models:
            return requested

        # Essayer les modeles par ordre de preference
        for model in [self.DEFAULT_MODEL] + self.FALLBACK_MODELS:
            if model in self._available_models:
                return model

        # Sinon prendre le premier disponible
        return self._available_models[0]

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        system_prompt: str | None = None,
    ) -> str:
        """Genere une reponse via Ollama."""
        import httpx

        best_model = await self._get_best_model(model)

        # Construire le prompt complet
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": best_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

            logger.debug(f"[LLM] Ollama ({best_model}): {len(data.get('response', ''))} chars")
            return data.get("response", "")


# ============================================================================
# ANTHROPIC CLIENT
# ============================================================================

class AnthropicClient(BaseLLMClient):
    """
    Client pour Anthropic Claude.
    Fallback si Ollama non disponible.
    """

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def is_available(self) -> bool:
        """Verifie si la cle API est configuree."""
        return bool(self.api_key)

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        system_prompt: str | None = None,
    ) -> str:
        """Genere une reponse via Anthropic Claude."""
        import httpx

        if not self.api_key:
            raise ValueError("Cle API Anthropic non configuree")

        messages = [{"role": "user", "content": prompt}]

        payload: dict[str, Any] = {
            "model": model or self.DEFAULT_MODEL,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Anthropic n'accepte pas temperature=0
        if temperature > 0:
            payload["temperature"] = temperature

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Extraire le contenu de la reponse
            content = data.get("content", [])
            if content and isinstance(content, list):
                text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                result = "".join(text_parts)
                logger.debug(f"[LLM] Anthropic: {len(result)} chars")
                return result

            return ""


# ============================================================================
# OPENAI CLIENT
# ============================================================================

class OpenAIClient(BaseLLMClient):
    """
    Client pour OpenAI GPT.
    Fallback secondaire.
    """

    DEFAULT_MODEL = "gpt-4-turbo-preview"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"

    @property
    def provider_name(self) -> str:
        return "openai"

    async def is_available(self) -> bool:
        """Verifie si la cle API est configuree."""
        return bool(self.api_key)

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        system_prompt: str | None = None,
    ) -> str:
        """Genere une reponse via OpenAI."""
        import httpx

        if not self.api_key:
            raise ValueError("Cle API OpenAI non configuree")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model or self.DEFAULT_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
            )
            response.raise_for_status()
            data = response.json()

            choices = data.get("choices", [])
            if choices:
                result = choices[0].get("message", {}).get("content", "")
                logger.debug(f"[LLM] OpenAI: {len(result)} chars")
                return result

            return ""


# ============================================================================
# MOCK CLIENT (FALLBACK ULTIME)
# ============================================================================

class MockLLMClient(BaseLLMClient):
    """
    Client LLM de fallback pour tests et mode degrade.
    Retourne des reponses JSON valides pour le systeme.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    async def is_available(self) -> bool:
        """Toujours disponible."""
        return True

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        system_prompt: str | None = None,
    ) -> str:
        """Retourne une reponse mock."""
        logger.warning("[LLM] Mode degrade: utilisation du client Mock")

        # Detecter le type de requete pour retourner une reponse appropriee
        prompt_lower = prompt.lower()

        # Detection d'intention
        if "module" in prompt_lower and "action" in prompt_lower:
            # Essayer de detecter le module depuis le prompt
            module = "telephonie"
            action = "unknown"

            if "devis" in prompt_lower or "quote" in prompt_lower:
                module = "commercial"
                action = "create_quote"
            elif "ticket" in prompt_lower or "support" in prompt_lower:
                module = "support"
                action = "create_ticket"
            elif "article" in prompt_lower or "seo" in prompt_lower:
                module = "seo"
                action = "generate_article"
            elif "campagne" in prompt_lower or "marketing" in prompt_lower:
                module = "marketing"
                action = "create_campaign"
            elif "facture" in prompt_lower or "comptab" in prompt_lower:
                module = "comptabilite"
                action = "process_invoice"

            return json.dumps({
                "module": module,
                "action": action,
                "confidence": 0.5,
                "reasoning": "Mode degrade - detection basique par mots-cles"
            })

        # Reponse generique
        return json.dumps({
            "response": "Mode degrade actif. Aucun LLM disponible.",
            "success": False,
            "warning": "Configurez Ollama, Anthropic ou OpenAI pour des reponses completes."
        })


# ============================================================================
# FACTORY ET CLIENT PRINCIPAL
# ============================================================================

class LLMClientFactory:
    """
    Factory pour creer le meilleur client LLM disponible.
    Teste les providers dans l'ordre de priorite.
    Supporte la configuration par tenant via integrations.
    """

    PROVIDER_ORDER = ["ollama", "openai", "anthropic", "mock"]

    _instance: BaseLLMClient | None = None
    _provider_cache: dict[str, BaseLLMClient] = {}

    @classmethod
    def _get_provider_instance(
        cls,
        provider: str,
        config: dict | None = None
    ) -> BaseLLMClient:
        """
        Recupere ou cree une instance de provider.

        Args:
            provider: Nom du provider
            config: Configuration optionnelle (integrations du tenant)
        """
        config = config or {}

        # Pour les configs tenant-specifiques, ne pas cacher
        cache_key = provider
        if config:
            # Creer une instance specifique sans cache
            if provider == "ollama":
                base_url = config.get("ollama_base_url", "http://localhost:11434")
                return OllamaClient(base_url=base_url)
            elif provider == "anthropic":
                api_key = config.get("anthropic_api_key")
                return AnthropicClient(api_key=api_key)
            elif provider == "openai":
                api_key = config.get("openai_api_key")
                return OpenAIClient(api_key=api_key)
            else:
                return MockLLMClient()

        # Cache pour les instances sans config specifique
        if cache_key not in cls._provider_cache:
            if provider == "ollama":
                cls._provider_cache[cache_key] = OllamaClient()
            elif provider == "anthropic":
                cls._provider_cache[cache_key] = AnthropicClient()
            elif provider == "openai":
                cls._provider_cache[cache_key] = OpenAIClient()
            else:
                cls._provider_cache[cache_key] = MockLLMClient()

        return cls._provider_cache[cache_key]

    @classmethod
    async def create(
        cls,
        provider: str = "auto",
        config: dict | None = None
    ) -> BaseLLMClient:
        """
        Cree le client LLM le plus adapte.

        Args:
            provider: "auto" pour detection automatique, ou nom specifique
            config: Configuration tenant (integrations dict)

        Returns:
            Instance de BaseLLMClient
        """
        if provider != "auto":
            client = cls._get_provider_instance(provider, config)
            if await client.is_available():
                logger.info(f"[LLM] Provider selectionne: {provider}")
                return client
            logger.warning(f"[LLM] Provider {provider} non disponible, fallback auto")

        # Detection automatique
        for prov in cls.PROVIDER_ORDER:
            client = cls._get_provider_instance(prov, config)
            if await client.is_available():
                logger.info(f"[LLM] Provider detecte: {prov}")
                return client

        # Fallback ultime
        logger.warning("[LLM] Aucun provider disponible, mode Mock")
        return MockLLMClient()

    @classmethod
    def reset(cls):
        """Reset le cache des providers."""
        cls._instance = None
        cls._provider_cache.clear()


# ============================================================================
# SINGLETON GLOBAL
# ============================================================================

_global_client: BaseLLMClient | None = None
_tenant_clients: dict[str, BaseLLMClient] = {}


async def get_llm_client(
    provider: str = "auto",
    tenant_id: str | None = None,
    config: dict | None = None
) -> BaseLLMClient:
    """
    Recupere le client LLM.
    Si tenant_id et config sont fournis, utilise la configuration tenant.
    Sinon, utilise le client global (variables d'environnement).

    Args:
        provider: "auto" pour detection automatique
        tenant_id: ID du tenant (optionnel)
        config: Configuration integrations du tenant (optionnel)

    Returns:
        Instance de BaseLLMClient prete a l'emploi
    """
    global _global_client, _tenant_clients

    # Si config tenant fournie, creer un client specifique
    if tenant_id and config:
        # Verifier si on a deja un client pour ce tenant
        if tenant_id not in _tenant_clients:
            _tenant_clients[tenant_id] = await LLMClientFactory.create(provider, config)
        return _tenant_clients[tenant_id]

    # Sinon utiliser le client global
    if _global_client is None:
        _global_client = await LLMClientFactory.create(provider)

    return _global_client


async def get_llm_client_for_tenant(tenant_id: str, db) -> BaseLLMClient:
    """
    Recupere le client LLM avec la configuration du tenant.

    Args:
        tenant_id: ID du tenant
        db: Session SQLAlchemy

    Returns:
        Instance de BaseLLMClient configuree pour le tenant
    """
    from .config import get_or_create_marceau_config

    config = get_or_create_marceau_config(tenant_id, db)
    integrations = config.integrations or {}

    return await get_llm_client(
        provider="auto",
        tenant_id=tenant_id,
        config=integrations
    )


def reset_llm_client(tenant_id: str | None = None):
    """
    Reset le client LLM.

    Args:
        tenant_id: Si fourni, reset uniquement ce tenant. Sinon reset tout.
    """
    global _global_client, _tenant_clients

    if tenant_id:
        _tenant_clients.pop(tenant_id, None)
    else:
        _global_client = None
        _tenant_clients.clear()
        LLMClientFactory.reset()


# ============================================================================
# UTILITAIRES
# ============================================================================

async def generate_with_retry(
    prompt: str,
    max_retries: int = 2,
    **kwargs
) -> str:
    """
    Genere avec retry automatique sur plusieurs providers.

    Args:
        prompt: Le prompt
        max_retries: Nombre de retries
        **kwargs: Arguments supplementaires pour generate()

    Returns:
        Reponse generee
    """
    llm = await get_llm_client()
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return await llm.generate(prompt, **kwargs)
        except Exception as e:
            last_error = e
            logger.warning(f"[LLM] Tentative {attempt + 1} echouee: {e}")

            # Essayer un autre provider
            if attempt < max_retries:
                reset_llm_client()
                llm = await get_llm_client()

    raise last_error or Exception("Echec generation LLM")


async def extract_json_from_response(response: str) -> dict | None:
    """
    Extrait le JSON d'une reponse LLM.

    Args:
        response: Reponse brute du LLM

    Returns:
        Dict parse ou None si echec
    """
    try:
        # Chercher le JSON dans la reponse
        start = response.find("{")
        end = response.rfind("}") + 1

        if start >= 0 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)

        return None
    except json.JSONDecodeError:
        return None
