"""
AZALSCORE Finance Webhook Service
=================================

Service centralisé pour le traitement des webhooks de tous les providers finance.

Fonctionnalités:
- Vérification des signatures
- Parsing des événements
- Stockage en base
- Distribution aux handlers
- Retry automatique
- Audit trail complet
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Callable, Awaitable
from uuid import uuid4

from sqlalchemy.orm import Session

from app.modules.finance.models import FinanceWebhookEvent
from app.modules.finance.providers.base import (
    FinanceProviderType,
    WebhookEvent,
    WebhookEventType,
)
from app.modules.finance.providers.registry import FinanceProviderRegistry

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================


class WebhookProcessingStatus(str, Enum):
    """Statuts de traitement des webhooks."""

    RECEIVED = "received"
    SIGNATURE_VALID = "signature_valid"
    SIGNATURE_INVALID = "signature_invalid"
    PARSED = "parsed"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookResult:
    """Résultat du traitement d'un webhook."""

    success: bool
    event_id: str
    provider: str
    event_type: Optional[str] = None
    status: WebhookProcessingStatus = WebhookProcessingStatus.RECEIVED
    message: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


# Type pour les handlers
WebhookHandler = Callable[[WebhookEvent], Awaitable[bool]]


# =============================================================================
# WEBHOOK SERVICE
# =============================================================================


class WebhookService:
    """
    Service centralisé pour le traitement des webhooks finance.

    Fonctionnalités:
    - Vérification des signatures de tous les providers
    - Parsing unifié des événements
    - Stockage en base pour audit
    - Distribution aux handlers enregistrés
    - Gestion des retries
    - Logging structuré

    Usage:
        service = WebhookService(db, tenant_id)

        # Enregistrer un handler
        service.register_handler(
            WebhookEventType.PAYMENT_CAPTURED,
            my_payment_handler,
        )

        # Traiter un webhook
        result = await service.process_webhook(
            provider="swan",
            payload=raw_body,
            signature=signature_header,
        )
    """

    # Mapping provider -> header de signature
    SIGNATURE_HEADERS = {
        FinanceProviderType.SWAN: "X-Swan-Signature",
        FinanceProviderType.NMI: "X-Nmi-Signature",
        FinanceProviderType.DEFACTO: "X-Defacto-Signature",
        FinanceProviderType.SOLARIS: "X-Solaris-Signature",
    }

    def __init__(
        self,
        db: Session,
        tenant_id: str,
    ):
        """
        Initialise le service de webhooks.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant
        """
        if not tenant_id:
            raise ValueError("tenant_id est obligatoire")

        self.db = db
        self.tenant_id = tenant_id

        # Registry pour accéder aux providers
        self._registry = FinanceProviderRegistry(tenant_id=tenant_id, db=db)

        # Handlers enregistrés par type d'événement
        self._handlers: dict[WebhookEventType, list[WebhookHandler]] = {}

        # Logger avec contexte
        self._logger = logging.LoggerAdapter(
            logger,
            extra={"tenant_id": tenant_id, "service": "WebhookService"},
        )

    # =========================================================================
    # HANDLERS
    # =========================================================================

    def register_handler(
        self,
        event_type: WebhookEventType,
        handler: WebhookHandler,
    ) -> None:
        """
        Enregistre un handler pour un type d'événement.

        Args:
            event_type: Type d'événement
            handler: Fonction async qui traite l'événement
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        self._logger.info(f"Handler enregistré pour {event_type.value}")

    def unregister_handler(
        self,
        event_type: WebhookEventType,
        handler: WebhookHandler,
    ) -> bool:
        """
        Supprime un handler pour un type d'événement.

        Args:
            event_type: Type d'événement
            handler: Handler à supprimer

        Returns:
            True si supprimé, False sinon
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            return True
        return False

    # =========================================================================
    # PROCESSING
    # =========================================================================

    async def process_webhook(
        self,
        provider: str,
        payload: bytes,
        signature: Optional[str] = None,
        headers: Optional[dict] = None,
    ) -> WebhookResult:
        """
        Traite un webhook entrant.

        Args:
            provider: Nom du provider (swan, nmi, defacto, solaris)
            payload: Corps brut de la requête
            signature: Signature du webhook (ou None pour extraire des headers)
            headers: Headers HTTP (pour extraire la signature si non fournie)

        Returns:
            WebhookResult avec le statut du traitement
        """
        event_id = str(uuid4())
        start_time = datetime.utcnow()

        self._logger.info(
            f"Webhook reçu de {provider}",
            extra={"event_id": event_id, "payload_size": len(payload)},
        )

        try:
            # 1. Identifier le provider
            provider_type = self._get_provider_type(provider)
            if not provider_type:
                return WebhookResult(
                    success=False,
                    event_id=event_id,
                    provider=provider,
                    status=WebhookProcessingStatus.FAILED,
                    error=f"Provider inconnu: {provider}",
                )

            # 2. Récupérer l'instance du provider
            provider_instance = await self._registry.get_provider(provider_type)
            if not provider_instance:
                return WebhookResult(
                    success=False,
                    event_id=event_id,
                    provider=provider,
                    status=WebhookProcessingStatus.FAILED,
                    error=f"Provider {provider} non configuré pour ce tenant",
                )

            # 3. Extraire la signature si nécessaire
            if not signature and headers:
                sig_header = self.SIGNATURE_HEADERS.get(provider_type, "")
                signature = headers.get(sig_header) or headers.get(sig_header.lower())

            # 4. Vérifier la signature
            signature_valid = False
            if signature:
                signature_valid = provider_instance.verify_webhook_signature(
                    payload=payload,
                    signature=signature,
                )

                if not signature_valid:
                    self._logger.warning(
                        f"Signature webhook invalide",
                        extra={"provider": provider, "event_id": event_id},
                    )
                    # On continue quand même pour loguer l'événement
                    # mais on marque comme non fiable

            # 5. Parser le payload
            try:
                payload_dict = json.loads(payload.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                return WebhookResult(
                    success=False,
                    event_id=event_id,
                    provider=provider,
                    status=WebhookProcessingStatus.FAILED,
                    error=f"Payload invalide: {e}",
                )

            # 6. Parser l'événement
            event = provider_instance.parse_webhook_event(payload_dict)
            event.signature = signature
            event.signature_valid = signature_valid

            # 7. Stocker en base
            db_event = await self._store_event(event, payload)

            # 8. Distribuer aux handlers
            if signature_valid:
                handlers_success = await self._dispatch_event(event)
            else:
                handlers_success = False
                self._logger.warning(
                    "Handlers non exécutés car signature invalide",
                    extra={"event_id": event_id},
                )

            # 9. Mettre à jour le statut
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            status = (
                WebhookProcessingStatus.PROCESSED
                if handlers_success
                else WebhookProcessingStatus.SIGNATURE_INVALID
                if not signature_valid
                else WebhookProcessingStatus.FAILED
            )

            if db_event:
                db_event.processed = handlers_success
                db_event.processed_at = datetime.utcnow()
                db_event.processing_time_ms = int(processing_time)
                self.db.commit()

            self._logger.info(
                f"Webhook traité",
                extra={
                    "event_id": event_id,
                    "provider": provider,
                    "event_type": event.type.value,
                    "status": status.value,
                    "processing_time_ms": processing_time,
                },
            )

            return WebhookResult(
                success=handlers_success,
                event_id=event_id,
                provider=provider,
                event_type=event.type.value,
                status=status,
                message="Webhook traité avec succès" if handlers_success else None,
            )

        except Exception as e:
            self._logger.error(
                f"Erreur traitement webhook: {e}",
                extra={"event_id": event_id, "provider": provider},
                exc_info=True,
            )
            return WebhookResult(
                success=False,
                event_id=event_id,
                provider=provider,
                status=WebhookProcessingStatus.FAILED,
                error=str(e),
            )

    async def _dispatch_event(self, event: WebhookEvent) -> bool:
        """
        Distribue un événement aux handlers enregistrés.

        Args:
            event: Événement à distribuer

        Returns:
            True si tous les handlers ont réussi
        """
        handlers = self._handlers.get(event.type, [])

        if not handlers:
            self._logger.debug(f"Pas de handler pour {event.type.value}")
            return True  # Pas d'erreur si pas de handler

        all_success = True
        for handler in handlers:
            try:
                success = await handler(event)
                if not success:
                    all_success = False
                    self._logger.warning(
                        f"Handler a retourné False",
                        extra={"event_type": event.type.value},
                    )
            except Exception as e:
                all_success = False
                self._logger.error(
                    f"Erreur dans handler: {e}",
                    extra={"event_type": event.type.value},
                    exc_info=True,
                )

        return all_success

    async def _store_event(
        self,
        event: WebhookEvent,
        raw_payload: bytes,
    ) -> Optional[FinanceWebhookEvent]:
        """
        Stocke l'événement en base pour audit.

        Args:
            event: Événement parsé
            raw_payload: Payload brut

        Returns:
            Instance du modèle créé
        """
        try:
            db_event = FinanceWebhookEvent(
                tenant_id=self.tenant_id,
                provider=event.provider.value,
                event_type=event.type.value,
                event_id=event.id,
                payload=event.payload,
                raw_payload=raw_payload.decode("utf-8", errors="replace"),
                signature=event.signature,
                signature_valid=event.signature_valid,
                received_at=datetime.utcnow(),
            )

            self.db.add(db_event)
            self.db.commit()
            self.db.refresh(db_event)

            return db_event

        except Exception as e:
            self._logger.error(f"Erreur stockage événement: {e}")
            self.db.rollback()
            return None

    def _get_provider_type(self, provider: str) -> Optional[FinanceProviderType]:
        """
        Convertit le nom du provider en enum.

        Args:
            provider: Nom du provider (swan, nmi, etc.)

        Returns:
            FinanceProviderType ou None
        """
        mapping = {
            "swan": FinanceProviderType.SWAN,
            "nmi": FinanceProviderType.NMI,
            "defacto": FinanceProviderType.DEFACTO,
            "solaris": FinanceProviderType.SOLARIS,
        }
        return mapping.get(provider.lower())

    # =========================================================================
    # RETRY
    # =========================================================================

    async def retry_failed_events(
        self,
        max_retries: int = 3,
        limit: int = 100,
    ) -> dict:
        """
        Retente le traitement des événements échoués.

        Args:
            max_retries: Nombre max de tentatives
            limit: Nombre max d'événements à traiter

        Returns:
            Statistiques de retry
        """
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        try:
            # Récupérer les événements échoués
            failed_events = self.db.query(FinanceWebhookEvent).filter(
                FinanceWebhookEvent.tenant_id == self.tenant_id,
                FinanceWebhookEvent.processed == False,
                FinanceWebhookEvent.retry_count < max_retries,
            ).limit(limit).all()

            stats["total"] = len(failed_events)

            for db_event in failed_events:
                # Récupérer le provider
                provider_type = self._get_provider_type(db_event.provider)
                if not provider_type:
                    stats["skipped"] += 1
                    continue

                provider = await self._registry.get_provider(provider_type)
                if not provider:
                    stats["skipped"] += 1
                    continue

                # Re-parser et distribuer
                try:
                    payload_dict = json.loads(db_event.raw_payload)
                    event = provider.parse_webhook_event(payload_dict)
                    event.signature_valid = db_event.signature_valid

                    if event.signature_valid:
                        success = await self._dispatch_event(event)
                        if success:
                            db_event.processed = True
                            db_event.processed_at = datetime.utcnow()
                            stats["success"] += 1
                        else:
                            db_event.retry_count += 1
                            stats["failed"] += 1
                    else:
                        stats["skipped"] += 1

                except Exception as e:
                    db_event.retry_count += 1
                    db_event.error = str(e)
                    stats["failed"] += 1

            self.db.commit()

        except Exception as e:
            self._logger.error(f"Erreur retry: {e}")
            self.db.rollback()

        return stats

    # =========================================================================
    # QUERIES
    # =========================================================================

    async def get_events(
        self,
        provider: Optional[str] = None,
        event_type: Optional[str] = None,
        processed: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """
        Récupère les événements webhook.

        Args:
            provider: Filtrer par provider
            event_type: Filtrer par type d'événement
            processed: Filtrer par statut de traitement
            limit: Nombre max de résultats
            offset: Décalage

        Returns:
            Liste des événements
        """
        query = self.db.query(FinanceWebhookEvent).filter(
            FinanceWebhookEvent.tenant_id == self.tenant_id
        )

        if provider:
            query = query.filter(FinanceWebhookEvent.provider == provider)
        if event_type:
            query = query.filter(FinanceWebhookEvent.event_type == event_type)
        if processed is not None:
            query = query.filter(FinanceWebhookEvent.processed == processed)

        events = query.order_by(
            FinanceWebhookEvent.received_at.desc()
        ).offset(offset).limit(limit).all()

        return [
            {
                "id": str(e.id),
                "provider": e.provider,
                "event_type": e.event_type,
                "event_id": e.event_id,
                "processed": e.processed,
                "signature_valid": e.signature_valid,
                "retry_count": e.retry_count,
                "received_at": e.received_at.isoformat() if e.received_at else None,
                "processed_at": e.processed_at.isoformat() if e.processed_at else None,
            }
            for e in events
        ]

    async def get_event(self, event_id: str) -> Optional[dict]:
        """
        Récupère un événement par son ID.

        Args:
            event_id: ID de l'événement (webhook event_id, pas DB id)

        Returns:
            Données de l'événement ou None
        """
        event = self.db.query(FinanceWebhookEvent).filter(
            FinanceWebhookEvent.tenant_id == self.tenant_id,
            FinanceWebhookEvent.event_id == event_id,
        ).first()

        if not event:
            return None

        return {
            "id": str(event.id),
            "provider": event.provider,
            "event_type": event.event_type,
            "event_id": event.event_id,
            "payload": event.payload,
            "processed": event.processed,
            "signature_valid": event.signature_valid,
            "retry_count": event.retry_count,
            "error": event.error,
            "received_at": event.received_at.isoformat() if event.received_at else None,
            "processed_at": event.processed_at.isoformat() if event.processed_at else None,
        }
