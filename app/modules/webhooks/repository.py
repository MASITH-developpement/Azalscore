"""
AZALS MODULE WEBHOOKS - Repository
===================================

Repositories SQLAlchemy pour le module Webhooks (GAP-053).
Conforme aux normes AZALSCORE (isolation tenant, type hints).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session

from .models import (
    WebhookEndpoint,
    WebhookPayload,
    DeliveryAttempt,
    WebhookLog,
    WebhookSecret,
    WebhookHealthCheck,
    WebhookEvent,
    WebhookStatus,
    DeliveryStatus,
    SignatureVersion,
)


class WebhookEndpointRepository:
    """Repository pour les endpoints webhook."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WebhookEndpoint).filter(
            WebhookEndpoint.tenant_id == self.tenant_id
        )

    def get_by_id(self, endpoint_id: UUID) -> Optional[WebhookEndpoint]:
        """Recupere un endpoint par ID."""
        return self._base_query().filter(
            WebhookEndpoint.id == endpoint_id
        ).first()

    def get_by_name(self, name: str) -> Optional[WebhookEndpoint]:
        """Recupere un endpoint par nom."""
        return self._base_query().filter(
            WebhookEndpoint.name == name
        ).first()

    def list(
        self,
        status: Optional[WebhookStatus] = None,
        event: Optional[WebhookEvent] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WebhookEndpoint], int]:
        """Liste les endpoints avec filtres."""
        query = self._base_query()

        if status:
            query = query.filter(WebhookEndpoint.status == status)
        if event:
            query = query.filter(WebhookEndpoint.events.contains([event.value]))

        total = query.count()
        items = query.order_by(desc(WebhookEndpoint.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def get_active_for_event(self, event: WebhookEvent) -> List[WebhookEndpoint]:
        """Recupere les endpoints actifs pour un evenement."""
        return self._base_query().filter(
            WebhookEndpoint.status == WebhookStatus.ACTIVE,
            WebhookEndpoint.events.contains([event.value])
        ).all()

    def get_failing(self, min_failures: int = 5) -> List[WebhookEndpoint]:
        """Recupere les endpoints en echec."""
        return self._base_query().filter(
            WebhookEndpoint.consecutive_failures >= min_failures
        ).all()

    def create(self, data: Dict[str, Any]) -> WebhookEndpoint:
        """Cree un nouveau endpoint."""
        endpoint = WebhookEndpoint(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(endpoint)
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint

    def update(
        self,
        endpoint: WebhookEndpoint,
        data: Dict[str, Any]
    ) -> WebhookEndpoint:
        """Met a jour un endpoint."""
        for key, value in data.items():
            if hasattr(endpoint, key) and value is not None:
                setattr(endpoint, key, value)
        endpoint.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint

    def delete(self, endpoint: WebhookEndpoint) -> None:
        """Supprime un endpoint."""
        self.db.delete(endpoint)
        self.db.commit()

    def pause(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        """Met en pause un endpoint."""
        endpoint.status = WebhookStatus.PAUSED
        endpoint.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint

    def activate(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        """Active un endpoint."""
        endpoint.status = WebhookStatus.ACTIVE
        endpoint.consecutive_failures = 0
        endpoint.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint

    def disable(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        """Desactive un endpoint."""
        endpoint.status = WebhookStatus.DISABLED
        endpoint.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint

    def record_success(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        """Enregistre un succes de livraison."""
        endpoint.total_deliveries += 1
        endpoint.successful_deliveries += 1
        endpoint.last_delivery_at = datetime.utcnow()
        endpoint.last_success_at = datetime.utcnow()
        endpoint.consecutive_failures = 0
        if endpoint.status == WebhookStatus.FAILING:
            endpoint.status = WebhookStatus.ACTIVE
        endpoint.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint

    def record_failure(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        """Enregistre un echec de livraison."""
        endpoint.total_deliveries += 1
        endpoint.failed_deliveries += 1
        endpoint.last_delivery_at = datetime.utcnow()
        endpoint.last_failure_at = datetime.utcnow()
        endpoint.consecutive_failures += 1

        # Passer en statut FAILING apres 5 echecs consecutifs
        if endpoint.consecutive_failures >= 5:
            endpoint.status = WebhookStatus.FAILING

        endpoint.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint


class WebhookPayloadRepository:
    """Repository pour les payloads webhook."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WebhookPayload).filter(
            WebhookPayload.tenant_id == self.tenant_id
        )

    def get_by_id(self, payload_id: UUID) -> Optional[WebhookPayload]:
        """Recupere un payload par ID."""
        return self._base_query().filter(
            WebhookPayload.id == payload_id
        ).first()

    def list(
        self,
        event: Optional[WebhookEvent] = None,
        source_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WebhookPayload], int]:
        """Liste les payloads avec filtres."""
        query = self._base_query()

        if event:
            query = query.filter(WebhookPayload.event == event)
        if source_type:
            query = query.filter(WebhookPayload.source_type == source_type)
        if date_from:
            query = query.filter(WebhookPayload.timestamp >= date_from)
        if date_to:
            query = query.filter(WebhookPayload.timestamp <= date_to)

        total = query.count()
        items = query.order_by(desc(WebhookPayload.timestamp)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any]) -> WebhookPayload:
        """Cree un nouveau payload."""
        payload = WebhookPayload(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(payload)
        self.db.commit()
        self.db.refresh(payload)
        return payload

    def delete_old(self, days: int = 30) -> int:
        """Supprime les anciens payloads."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = self._base_query().filter(
            WebhookPayload.timestamp < cutoff
        ).delete(synchronize_session=False)
        self.db.commit()
        return result


class DeliveryAttemptRepository:
    """Repository pour les tentatives de livraison."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(DeliveryAttempt).filter(
            DeliveryAttempt.tenant_id == self.tenant_id
        )

    def get_by_id(self, attempt_id: UUID) -> Optional[DeliveryAttempt]:
        """Recupere une tentative par ID."""
        return self._base_query().filter(
            DeliveryAttempt.id == attempt_id
        ).first()

    def get_by_payload(self, payload_id: UUID) -> List[DeliveryAttempt]:
        """Recupere les tentatives pour un payload."""
        return self._base_query().filter(
            DeliveryAttempt.payload_id == payload_id
        ).order_by(DeliveryAttempt.attempt_number).all()

    def get_by_endpoint(
        self,
        endpoint_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DeliveryAttempt], int]:
        """Recupere les tentatives pour un endpoint."""
        query = self._base_query().filter(
            DeliveryAttempt.endpoint_id == endpoint_id
        )
        total = query.count()
        items = query.order_by(desc(DeliveryAttempt.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def get_pending_retries(self, limit: int = 100) -> List[DeliveryAttempt]:
        """Recupere les tentatives a reessayer."""
        now = datetime.utcnow()
        return self._base_query().filter(
            DeliveryAttempt.status == DeliveryStatus.RETRYING,
            DeliveryAttempt.next_retry_at <= now
        ).order_by(DeliveryAttempt.next_retry_at).limit(limit).all()

    def create(self, data: Dict[str, Any]) -> DeliveryAttempt:
        """Cree une nouvelle tentative."""
        attempt = DeliveryAttempt(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def start(self, attempt: DeliveryAttempt) -> DeliveryAttempt:
        """Demarre une tentative."""
        attempt.started_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def complete_success(
        self,
        attempt: DeliveryAttempt,
        response_status: int,
        response_headers: Dict[str, str],
        response_body: str,
        response_time_ms: int
    ) -> DeliveryAttempt:
        """Complete une tentative avec succes."""
        attempt.status = DeliveryStatus.DELIVERED
        attempt.response_status_code = response_status
        attempt.response_headers = response_headers
        attempt.response_body = response_body
        attempt.response_time_ms = response_time_ms
        attempt.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def complete_failure(
        self,
        attempt: DeliveryAttempt,
        error_message: str,
        error_code: Optional[str] = None,
        response_status: Optional[int] = None,
        schedule_retry: bool = True,
        retry_at: Optional[datetime] = None
    ) -> DeliveryAttempt:
        """Complete une tentative avec echec."""
        if schedule_retry:
            attempt.status = DeliveryStatus.RETRYING
            if retry_at:
                attempt.next_retry_at = retry_at
            else:
                # Backoff exponentiel
                delay = min(60 * (2 ** (attempt.attempt_number - 1)), 3600)
                attempt.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
        else:
            attempt.status = DeliveryStatus.FAILED

        attempt.error_message = error_message
        attempt.error_code = error_code
        if response_status:
            attempt.response_status_code = response_status
        attempt.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def create_retry(self, original: DeliveryAttempt) -> DeliveryAttempt:
        """Cree une nouvelle tentative de retry."""
        retry = DeliveryAttempt(
            tenant_id=self.tenant_id,
            endpoint_id=original.endpoint_id,
            payload_id=original.payload_id,
            attempt_number=original.attempt_number + 1,
            request_url=original.request_url,
            request_headers=original.request_headers,
            request_body=original.request_body
        )
        self.db.add(retry)
        self.db.commit()
        self.db.refresh(retry)
        return retry


class WebhookLogRepository:
    """Repository pour les logs webhook."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WebhookLog).filter(
            WebhookLog.tenant_id == self.tenant_id
        )

    def list(
        self,
        endpoint_id: Optional[UUID] = None,
        event: Optional[WebhookEvent] = None,
        success: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WebhookLog], int]:
        """Liste les logs avec filtres."""
        query = self._base_query()

        if endpoint_id:
            query = query.filter(WebhookLog.endpoint_id == endpoint_id)
        if event:
            query = query.filter(WebhookLog.event == event)
        if success is not None:
            query = query.filter(WebhookLog.success == success)
        if date_from:
            query = query.filter(WebhookLog.created_at >= date_from)
        if date_to:
            query = query.filter(WebhookLog.created_at <= date_to)

        total = query.count()
        items = query.order_by(desc(WebhookLog.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any]) -> WebhookLog:
        """Cree un nouveau log."""
        log = WebhookLog(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_statistics(
        self,
        endpoint_id: Optional[UUID] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Calcule les statistiques de livraison."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = self._base_query().filter(WebhookLog.created_at >= cutoff)

        if endpoint_id:
            query = query.filter(WebhookLog.endpoint_id == endpoint_id)

        total = query.count()
        successes = query.filter(WebhookLog.success == True).count()

        return {
            "total": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": (successes / total * 100) if total > 0 else 0,
            "period_days": days
        }

    def delete_old(self, days: int = 30) -> int:
        """Supprime les anciens logs."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = self._base_query().filter(
            WebhookLog.created_at < cutoff
        ).delete(synchronize_session=False)
        self.db.commit()
        return result


class WebhookSecretRepository:
    """Repository pour les secrets webhook."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WebhookSecret).filter(
            WebhookSecret.tenant_id == self.tenant_id
        )

    def get_active(self, endpoint_id: UUID) -> Optional[WebhookSecret]:
        """Recupere le secret actif d'un endpoint."""
        return self._base_query().filter(
            WebhookSecret.endpoint_id == endpoint_id,
            WebhookSecret.is_active == True,
            or_(
                WebhookSecret.expires_at.is_(None),
                WebhookSecret.expires_at > datetime.utcnow()
            )
        ).order_by(desc(WebhookSecret.version)).first()

    def get_all_for_endpoint(self, endpoint_id: UUID) -> List[WebhookSecret]:
        """Recupere tous les secrets d'un endpoint."""
        return self._base_query().filter(
            WebhookSecret.endpoint_id == endpoint_id
        ).order_by(desc(WebhookSecret.version)).all()

    def create(self, data: Dict[str, Any]) -> WebhookSecret:
        """Cree un nouveau secret."""
        secret = WebhookSecret(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(secret)
        self.db.commit()
        self.db.refresh(secret)
        return secret

    def rotate(
        self,
        endpoint_id: UUID,
        new_secret: str,
        grace_period_hours: int = 24
    ) -> WebhookSecret:
        """Effectue une rotation de secret."""
        # Expirer l'ancien secret avec periode de grace
        old_secret = self.get_active(endpoint_id)
        if old_secret:
            old_secret.expires_at = datetime.utcnow() + timedelta(hours=grace_period_hours)
            old_secret.rotated_at = datetime.utcnow()

        # Creer le nouveau secret
        new_version = (old_secret.version + 1) if old_secret else 1
        secret = WebhookSecret(
            tenant_id=self.tenant_id,
            endpoint_id=endpoint_id,
            secret=new_secret,
            version=new_version,
            is_active=True
        )
        self.db.add(secret)
        self.db.commit()
        self.db.refresh(secret)
        return secret

    def deactivate(self, secret: WebhookSecret) -> WebhookSecret:
        """Desactive un secret."""
        secret.is_active = False
        self.db.commit()
        self.db.refresh(secret)
        return secret


class WebhookHealthCheckRepository:
    """Repository pour les health checks webhook."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WebhookHealthCheck).filter(
            WebhookHealthCheck.tenant_id == self.tenant_id
        )

    def get_latest(self, endpoint_id: UUID) -> Optional[WebhookHealthCheck]:
        """Recupere le dernier health check."""
        return self._base_query().filter(
            WebhookHealthCheck.endpoint_id == endpoint_id
        ).order_by(desc(WebhookHealthCheck.checked_at)).first()

    def get_history(
        self,
        endpoint_id: UUID,
        hours: int = 24
    ) -> List[WebhookHealthCheck]:
        """Recupere l'historique des health checks."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self._base_query().filter(
            WebhookHealthCheck.endpoint_id == endpoint_id,
            WebhookHealthCheck.checked_at >= cutoff
        ).order_by(WebhookHealthCheck.checked_at).all()

    def create(self, data: Dict[str, Any]) -> WebhookHealthCheck:
        """Cree un nouveau health check."""
        check = WebhookHealthCheck(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(check)
        self.db.commit()
        self.db.refresh(check)
        return check

    def delete_old(self, days: int = 7) -> int:
        """Supprime les anciens health checks."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = self._base_query().filter(
            WebhookHealthCheck.checked_at < cutoff
        ).delete(synchronize_session=False)
        self.db.commit()
        return result
