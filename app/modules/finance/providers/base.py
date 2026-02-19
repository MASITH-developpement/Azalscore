"""
AZALSCORE Finance Providers - Base Classes
==========================================

Classes de base pour tous les providers finance.
Implémente les patterns communs: retry, timeout, logging, cache, multi-tenant.

Architecture:
    BaseFinanceProvider (ABC)
    ├── SwanProvider (Banking/Open Banking)
    ├── NMIProvider (Paiements)
    ├── DefactoProvider (Affacturage)
    └── SolarisProvider (Crédit)
"""

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class FinanceProviderType(str, Enum):
    """Types de providers finance."""
    SWAN = "swan"
    NMI = "nmi"
    DEFACTO = "defacto"
    SOLARIS = "solaris"


class FinanceErrorCode(str, Enum):
    """Codes d'erreur standardisés."""
    # Réseau
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    SSL_ERROR = "SSL_ERROR"

    # Authentification
    INVALID_API_KEY = "INVALID_API_KEY"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Validation
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Métier
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    TRANSACTION_REJECTED = "TRANSACTION_REJECTED"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"

    # Système
    RATE_LIMITED = "RATE_LIMITED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class WebhookEventType(str, Enum):
    """Types d'événements webhook."""
    # Comptes
    ACCOUNT_CREATED = "account.created"
    ACCOUNT_UPDATED = "account.updated"
    ACCOUNT_CLOSED = "account.closed"

    # Transactions
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_PENDING = "transaction.pending"
    TRANSACTION_COMPLETED = "transaction.completed"
    TRANSACTION_FAILED = "transaction.failed"
    TRANSACTION_REVERSED = "transaction.reversed"

    # Paiements
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_AUTHORIZED = "payment.authorized"
    PAYMENT_CAPTURED = "payment.captured"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_DISPUTED = "payment.disputed"

    # Affacturage
    INVOICE_SUBMITTED = "invoice.submitted"
    INVOICE_APPROVED = "invoice.approved"
    INVOICE_FUNDED = "invoice.funded"
    INVOICE_REJECTED = "invoice.rejected"

    # Crédit
    CREDIT_APPLICATION_RECEIVED = "credit.application_received"
    CREDIT_APPROVED = "credit.approved"
    CREDIT_DISBURSED = "credit.disbursed"
    CREDIT_REPAYMENT_RECEIVED = "credit.repayment_received"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FinanceError:
    """Erreur structurée d'un provider finance."""
    code: FinanceErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    provider_error_code: Optional[str] = None
    provider_error_message: Optional[str] = None
    retryable: bool = False

    def to_dict(self) -> dict:
        """Conversion en dictionnaire."""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "provider_error_code": self.provider_error_code,
            "provider_error_message": self.provider_error_message,
            "retryable": self.retryable,
        }


T = TypeVar("T")


@dataclass
class FinanceResult(Generic[T]):
    """
    Résultat standardisé d'une opération provider.

    Pattern Result pour éviter les exceptions dans le flux normal.
    """
    success: bool
    data: Optional[T] = None
    error: Optional[FinanceError] = None

    # Métadonnées
    provider: str = ""
    request_id: Optional[str] = None
    response_time_ms: int = 0
    cached: bool = False

    # Pagination (si applicable)
    total_count: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    has_more: bool = False

    @staticmethod
    def ok(
        data: T,
        provider: str = "",
        request_id: Optional[str] = None,
        response_time_ms: int = 0,
        cached: bool = False,
        total_count: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        has_more: bool = False,
    ) -> "FinanceResult[T]":
        """Crée un résultat succès."""
        return FinanceResult(
            success=True,
            data=data,
            provider=provider,
            request_id=request_id,
            response_time_ms=response_time_ms,
            cached=cached,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    @staticmethod
    def fail(
        error: FinanceError,
        provider: str = "",
        request_id: Optional[str] = None,
        response_time_ms: int = 0,
    ) -> "FinanceResult[T]":
        """Crée un résultat échec."""
        return FinanceResult(
            success=False,
            error=error,
            provider=provider,
            request_id=request_id,
            response_time_ms=response_time_ms,
        )

    def to_dict(self) -> dict:
        """Conversion en dictionnaire."""
        result = {
            "success": self.success,
            "provider": self.provider,
            "request_id": self.request_id,
            "response_time_ms": self.response_time_ms,
            "cached": self.cached,
        }

        if self.success and self.data is not None:
            if hasattr(self.data, "to_dict"):
                result["data"] = self.data.to_dict()
            elif isinstance(self.data, list):
                result["data"] = [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in self.data
                ]
            else:
                result["data"] = self.data

        if self.error:
            result["error"] = self.error.to_dict()

        if self.total_count is not None:
            result["pagination"] = {
                "total_count": self.total_count,
                "page": self.page,
                "page_size": self.page_size,
                "has_more": self.has_more,
            }

        return result


@dataclass
class WebhookEvent:
    """Événement webhook reçu d'un provider."""
    id: str
    type: WebhookEventType
    provider: FinanceProviderType
    tenant_id: str

    # Données
    payload: dict[str, Any]
    raw_payload: str

    # Métadonnées
    timestamp: datetime
    signature: Optional[str] = None
    signature_valid: bool = False

    # Traitement
    processed: bool = False
    processed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0


# =============================================================================
# BASE PROVIDER
# =============================================================================

class BaseFinanceProvider(ABC):
    """
    Classe de base abstraite pour tous les providers finance.

    Fournit:
    - Gestion du client HTTP (httpx async)
    - Retry automatique avec backoff exponentiel
    - Timeout configurable
    - Logging structuré
    - Cache optionnel
    - Isolation multi-tenant

    Usage:
        class SwanProvider(BaseFinanceProvider):
            PROVIDER_NAME = "swan"
            BASE_URL = "https://api.swan.io"

            async def get_accounts(self) -> FinanceResult[list[SwanAccount]]:
                return await self._request("GET", "/accounts")
    """

    # Configuration à surcharger
    PROVIDER_NAME: str = "base"
    PROVIDER_TYPE: FinanceProviderType = FinanceProviderType.SWAN
    BASE_URL: str = ""
    API_VERSION: str = "v1"

    # Timeouts (secondes)
    DEFAULT_TIMEOUT: float = 30.0
    CONNECT_TIMEOUT: float = 10.0

    # Retry
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 1.5
    RETRY_STATUS_CODES: set[int] = {429, 500, 502, 503, 504}

    # Cache
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_ENABLED: bool = True

    def __init__(
        self,
        tenant_id: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        sandbox: bool = False,
        timeout: Optional[float] = None,
    ):
        """
        Initialise le provider.

        Args:
            tenant_id: ID du tenant (OBLIGATOIRE - isolation multi-tenant)
            api_key: Clé API (si non fournie, récupérée depuis config DB)
            api_secret: Secret API (optionnel)
            sandbox: Mode sandbox/test
            timeout: Timeout custom (optionnel)
        """
        if not tenant_id:
            raise ValueError("tenant_id est obligatoire pour l'isolation multi-tenant")

        self.tenant_id = tenant_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        self.timeout = timeout or self.DEFAULT_TIMEOUT

        # Client HTTP (lazy init)
        self._client: Optional[httpx.AsyncClient] = None

        # Logger avec contexte
        self._logger = logging.LoggerAdapter(
            logger,
            extra={
                "provider": self.PROVIDER_NAME,
                "tenant_id": self.tenant_id,
            }
        )

    # =========================================================================
    # HTTP CLIENT
    # =========================================================================

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Retourne le client HTTP (lazy init avec connection pooling).
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._get_base_url(),
                timeout=httpx.Timeout(
                    timeout=self.timeout,
                    connect=self.CONNECT_TIMEOUT,
                ),
                headers=self._get_default_headers(),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Ferme le client HTTP."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BaseFinanceProvider":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        await self.close()

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    def _get_base_url(self) -> str:
        """Retourne l'URL de base (sandbox ou production)."""
        return self.BASE_URL

    def _get_default_headers(self) -> dict[str, str]:
        """Retourne les headers par défaut."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"AZALSCORE/{self.PROVIDER_NAME}",
            "X-Tenant-ID": self.tenant_id,
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    # =========================================================================
    # REQUÊTES HTTP
    # =========================================================================

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
        retry: bool = True,
    ) -> FinanceResult[dict]:
        """
        Effectue une requête HTTP avec retry et gestion d'erreurs.

        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE, PATCH)
            endpoint: Endpoint relatif (/accounts, /transactions)
            params: Query parameters
            json_data: Corps JSON
            headers: Headers additionnels
            timeout: Timeout custom
            retry: Activer le retry automatique

        Returns:
            FinanceResult avec les données ou l'erreur
        """
        start_time = time.time()
        request_id = self._generate_request_id()

        # Préparer les headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)
        request_headers["X-Request-ID"] = request_id

        # Log de début
        self._logger.info(
            f"[{self.PROVIDER_NAME.upper()}] {method} {endpoint}",
            extra={
                "request_id": request_id,
                "method": method,
                "endpoint": endpoint,
                "has_body": json_data is not None,
            }
        )

        # Tentatives avec retry
        last_error: Optional[FinanceError] = None
        retries = self.MAX_RETRIES if retry else 1

        for attempt in range(retries):
            try:
                client = await self._get_client()

                response = await client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                    timeout=timeout or self.timeout,
                )

                response_time_ms = int((time.time() - start_time) * 1000)

                # Succès
                if response.is_success:
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        data = {"raw": response.text}

                    self._logger.info(
                        f"[{self.PROVIDER_NAME.upper()}] {method} {endpoint} -> {response.status_code} ({response_time_ms}ms)",
                        extra={
                            "request_id": request_id,
                            "status_code": response.status_code,
                            "response_time_ms": response_time_ms,
                        }
                    )

                    return FinanceResult.ok(
                        data=data,
                        provider=self.PROVIDER_NAME,
                        request_id=request_id,
                        response_time_ms=response_time_ms,
                    )

                # Erreur HTTP
                last_error = self._parse_error_response(response, request_id)

                # Retry si status code éligible
                if response.status_code in self.RETRY_STATUS_CODES and attempt < retries - 1:
                    wait_time = self.RETRY_BACKOFF_FACTOR ** attempt
                    self._logger.warning(
                        f"[{self.PROVIDER_NAME.upper()}] Retry {attempt + 1}/{retries} après {wait_time:.1f}s",
                        extra={
                            "request_id": request_id,
                            "status_code": response.status_code,
                            "wait_time": wait_time,
                        }
                    )
                    await self._sleep(wait_time)
                    continue

                break

            except httpx.TimeoutException as e:
                response_time_ms = int((time.time() - start_time) * 1000)
                last_error = FinanceError(
                    code=FinanceErrorCode.TIMEOUT,
                    message=f"Timeout après {response_time_ms}ms",
                    details={"timeout": self.timeout},
                    retryable=True,
                )

                if attempt < retries - 1:
                    wait_time = self.RETRY_BACKOFF_FACTOR ** attempt
                    self._logger.warning(
                        f"[{self.PROVIDER_NAME.upper()}] Timeout, retry {attempt + 1}/{retries}",
                        extra={"request_id": request_id}
                    )
                    await self._sleep(wait_time)
                    continue

            except httpx.ConnectError as e:
                last_error = FinanceError(
                    code=FinanceErrorCode.CONNECTION_ERROR,
                    message=f"Erreur de connexion: {str(e)}",
                    retryable=True,
                )

                if attempt < retries - 1:
                    wait_time = self.RETRY_BACKOFF_FACTOR ** attempt
                    await self._sleep(wait_time)
                    continue

            except Exception as e:
                last_error = FinanceError(
                    code=FinanceErrorCode.UNKNOWN_ERROR,
                    message=f"Erreur inattendue: {str(e)}",
                    details={"exception_type": type(e).__name__},
                    retryable=False,
                )
                break

        # Échec final
        response_time_ms = int((time.time() - start_time) * 1000)

        self._logger.error(
            f"[{self.PROVIDER_NAME.upper()}] {method} {endpoint} -> FAILED ({response_time_ms}ms)",
            extra={
                "request_id": request_id,
                "error_code": last_error.code.value if last_error else "UNKNOWN",
                "response_time_ms": response_time_ms,
            }
        )

        return FinanceResult.fail(
            error=last_error or FinanceError(
                code=FinanceErrorCode.UNKNOWN_ERROR,
                message="Erreur inconnue",
            ),
            provider=self.PROVIDER_NAME,
            request_id=request_id,
            response_time_ms=response_time_ms,
        )

    def _parse_error_response(
        self,
        response: httpx.Response,
        request_id: str
    ) -> FinanceError:
        """
        Parse une réponse d'erreur HTTP.

        À surcharger par les providers pour parser leurs formats d'erreur spécifiques.
        """
        status_code = response.status_code

        # Mapping status code -> error code
        error_code_map = {
            400: FinanceErrorCode.INVALID_REQUEST,
            401: FinanceErrorCode.INVALID_API_KEY,
            403: FinanceErrorCode.INSUFFICIENT_PERMISSIONS,
            404: FinanceErrorCode.ACCOUNT_NOT_FOUND,
            429: FinanceErrorCode.RATE_LIMITED,
            500: FinanceErrorCode.INTERNAL_ERROR,
            502: FinanceErrorCode.SERVICE_UNAVAILABLE,
            503: FinanceErrorCode.SERVICE_UNAVAILABLE,
            504: FinanceErrorCode.TIMEOUT,
        }

        error_code = error_code_map.get(status_code, FinanceErrorCode.UNKNOWN_ERROR)

        # Essayer de parser le body JSON
        try:
            body = response.json()
            provider_message = body.get("message") or body.get("error") or str(body)
            provider_code = body.get("code") or body.get("error_code")
        except (json.JSONDecodeError, KeyError):
            provider_message = response.text[:500] if response.text else "No response body"
            provider_code = None

        return FinanceError(
            code=error_code,
            message=f"HTTP {status_code}: {provider_message}",
            details={"status_code": status_code, "request_id": request_id},
            provider_error_code=provider_code,
            provider_error_message=provider_message,
            retryable=status_code in self.RETRY_STATUS_CODES,
        )

    # =========================================================================
    # CACHE
    # =========================================================================

    def _cache_key(self, operation: str, *args) -> str:
        """Génère une clé de cache unique."""
        key_parts = [
            "azals",
            "finance",
            self.tenant_id,
            self.PROVIDER_NAME,
            operation,
            *[str(a) for a in args],
        ]
        key_string = ":".join(key_parts)
        # MD5 utilisé pour génération de clé cache, pas pour sécurité
        return hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()

    async def _get_cached(self, cache_key: str) -> Optional[dict]:
        """Récupère une valeur du cache."""
        if not self.CACHE_ENABLED:
            return None

        try:
            from app.core.cache import get_cache
            cache = get_cache()
            data = cache.get(cache_key)
            if data:
                return json.loads(data)
        except Exception as e:
            self._logger.warning(f"Cache read error: {e}")

        return None

    async def _set_cached(self, cache_key: str, data: dict, ttl: Optional[int] = None) -> None:
        """Stocke une valeur dans le cache."""
        if not self.CACHE_ENABLED:
            return

        try:
            from app.core.cache import get_cache
            cache = get_cache()
            cache.set(cache_key, json.dumps(data), ttl or self.CACHE_TTL)
        except Exception as e:
            self._logger.warning(f"Cache write error: {e}")

    # =========================================================================
    # WEBHOOKS
    # =========================================================================

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Vérifie la signature d'un webhook.

        À implémenter par chaque provider avec son algorithme spécifique.
        """
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: dict) -> WebhookEvent:
        """
        Parse un payload webhook en WebhookEvent.

        À implémenter par chaque provider.
        """
        pass

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _generate_request_id(self) -> str:
        """Génère un ID de requête unique."""
        import uuid
        return f"{self.PROVIDER_NAME}-{uuid.uuid4().hex[:12]}"

    async def _sleep(self, seconds: float) -> None:
        """Sleep asynchrone (pour tests mockables)."""
        import asyncio
        await asyncio.sleep(seconds)

    # =========================================================================
    # MÉTHODES ABSTRAITES
    # =========================================================================

    @abstractmethod
    async def health_check(self) -> FinanceResult[dict]:
        """
        Vérifie la connectivité avec le provider.

        Returns:
            FinanceResult avec status de santé
        """
        pass

    @abstractmethod
    async def get_account_info(self) -> FinanceResult[dict]:
        """
        Récupère les informations du compte principal.

        Returns:
            FinanceResult avec infos compte
        """
        pass
