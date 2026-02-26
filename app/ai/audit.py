"""
AZALSCORE AI Audit System

Journalisation complète et traçable de toutes les interactions IA.
Objectif: Auditabilité juridique totale.

Conformité: AZA-NF-009, AZA-AUDIT-LEGAL
"""
from __future__ import annotations


import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types d'événements auditables"""
    # Interactions humaines
    HUMAN_REQUEST = "human_request"
    HUMAN_VALIDATION = "human_validation"
    HUMAN_REJECTION = "human_rejection"

    # Theo events
    THEO_RECEIVE = "theo_receive"
    THEO_CLARIFY = "theo_clarify"
    THEO_DISPATCH = "theo_dispatch"
    THEO_SYNTHESIZE = "theo_synthesize"
    THEO_RESPOND = "theo_respond"

    # AI Module events
    AI_CALL = "ai_call"
    AI_RESPONSE = "ai_response"
    AI_ERROR = "ai_error"
    AI_TIMEOUT = "ai_timeout"

    # Guardian events
    GUARDIAN_CHECK = "guardian_check"
    GUARDIAN_APPROVE = "guardian_approve"
    GUARDIAN_BLOCK = "guardian_block"
    GUARDIAN_ALERT = "guardian_alert"

    # Admin events
    ADMIN_ACTION = "admin_action"
    ADMIN_CONFIG_CHANGE = "admin_config_change"
    ADMIN_OVERRIDE = "admin_override"

    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_ESCALATION = "system_escalation"


@dataclass
class AuditEvent:
    """Événement d'audit complet"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    event_type: AuditEventType = AuditEventType.SYSTEM_ERROR
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None

    # Contexte
    source_module: str = "unknown"
    target_module: Optional[str] = None
    action: str = "unknown"

    # Contenu
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Résultat
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None

    # Intégrité
    checksum: Optional[str] = None

    def __post_init__(self):
        """Calcule le checksum pour garantir l'intégrité"""
        if self.checksum is None:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        """Calcule un hash SHA-256 de l'événement"""
        data = {
            "id": self.id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value if isinstance(self.event_type, Enum) else self.event_type,
            "session_id": self.session_id,
            "source_module": self.source_module,
            "action": self.action,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "success": self.success,
        }
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        result = asdict(self)
        if isinstance(result.get("event_type"), Enum):
            result["event_type"] = result["event_type"].value
        return result

    def to_json(self) -> str:
        """Convertit en JSON"""
        return json.dumps(self.to_dict(), default=str, indent=2)


class AIAuditLogger:
    """
    Logger d'audit pour le système IA

    Responsabilités:
    - Journaliser toutes les interactions
    - Garantir la traçabilité
    - Permettre l'export pour audit
    """

    def __init__(self, log_dir: str = None):
        import os
        if log_dir is None:
            # Use environment variable or fallback to local directory
            log_dir = os.getenv("AI_AUDIT_LOG_DIR", "./logs/ai_audit")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._events: List[AuditEvent] = []
        self._session_events: Dict[str, List[AuditEvent]] = {}

    def log_event(self, event: AuditEvent) -> str:
        """
        Enregistre un événement d'audit

        Returns:
            ID de l'événement
        """
        # Ajouter à la liste en mémoire
        self._events.append(event)

        # Ajouter à la session si applicable
        if event.session_id:
            if event.session_id not in self._session_events:
                self._session_events[event.session_id] = []
            self._session_events[event.session_id].append(event)

        # Écrire dans le fichier de log
        self._write_to_file(event)

        logger.info(
            "[AUDIT] %s: %s -> "
            "%s | %s | "
            "%s",
            event.event_type.value, event.source_module, event.target_module or 'N/A', event.action, 'SUCCESS' if event.success else 'FAILED'
        )

        return event.id

    def log_human_request(
        self,
        session_id: str,
        user_id: str,
        request: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Log une demande humaine"""
        return self.log_event(AuditEvent(
            event_type=AuditEventType.HUMAN_REQUEST,
            session_id=session_id,
            user_id=user_id,
            source_module="human",
            target_module="theo",
            action="request",
            input_data={"request": request},
            metadata=metadata or {}
        ))

    def log_theo_dispatch(
        self,
        session_id: str,
        target_module: str,
        role: str,
        input_data: Dict[str, Any]
    ) -> str:
        """Log un dispatch de Theo vers un module IA"""
        return self.log_event(AuditEvent(
            event_type=AuditEventType.THEO_DISPATCH,
            session_id=session_id,
            source_module="theo",
            target_module=target_module,
            role=role,
            action="dispatch",
            input_data=input_data
        ))

    def log_ai_call(
        self,
        session_id: str,
        module: str,
        role: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> str:
        """Log un appel IA"""
        return self.log_event(AuditEvent(
            event_type=AuditEventType.AI_RESPONSE if success else AuditEventType.AI_ERROR,
            session_id=session_id,
            source_module=module,
            role=role,
            action="execute",
            input_data=input_data,
            output_data=output_data,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms
        ))

    def log_guardian_decision(
        self,
        session_id: str,
        action: str,
        approved: bool,
        reason: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Log une décision Guardian"""
        event_type = AuditEventType.GUARDIAN_APPROVE if approved else AuditEventType.GUARDIAN_BLOCK
        return self.log_event(AuditEvent(
            event_type=event_type,
            session_id=session_id,
            source_module="guardian",
            action=action,
            success=approved,
            output_data={"approved": approved, "reason": reason},
            metadata=metadata or {}
        ))

    def log_admin_action(
        self,
        user_id: str,
        action: str,
        details: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """Log une action administrateur"""
        return self.log_event(AuditEvent(
            event_type=AuditEventType.ADMIN_ACTION,
            session_id=session_id,
            user_id=user_id,
            source_module="admin",
            action=action,
            input_data=details,
            metadata={"privilege_level": "admin"}
        ))

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Récupère l'historique d'une session"""
        events = self._session_events.get(session_id, [])
        return [e.to_dict() for e in events]

    def export_audit_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None
    ) -> Dict[str, Any]:
        """
        Exporte un rapport d'audit filtré

        Args:
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            event_types: Types d'événements à inclure (optionnel)

        Returns:
            Rapport d'audit structuré
        """
        filtered_events = self._events

        if start_date:
            filtered_events = [
                e for e in filtered_events
                if datetime.fromisoformat(e.timestamp) >= start_date
            ]

        if end_date:
            filtered_events = [
                e for e in filtered_events
                if datetime.fromisoformat(e.timestamp) <= end_date
            ]

        if event_types:
            filtered_events = [
                e for e in filtered_events
                if e.event_type in event_types
            ]

        return {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "total_events": len(filtered_events),
            "filters": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "event_types": [et.value for et in (event_types or [])]
            },
            "events": [e.to_dict() for e in filtered_events],
            "summary": self._generate_summary(filtered_events)
        }

    def _generate_summary(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Génère un résumé des événements"""
        summary = {
            "by_type": {},
            "by_module": {},
            "success_rate": 0,
            "total_errors": 0
        }

        for event in events:
            # Par type
            type_key = event.event_type.value
            summary["by_type"][type_key] = summary["by_type"].get(type_key, 0) + 1

            # Par module
            summary["by_module"][event.source_module] = \
                summary["by_module"].get(event.source_module, 0) + 1

            # Erreurs
            if not event.success:
                summary["total_errors"] += 1

        # Taux de succès
        if events:
            summary["success_rate"] = (
                (len(events) - summary["total_errors"]) / len(events) * 100
            )

        return summary

    def _write_to_file(self, event: AuditEvent):
        """Écrit un événement dans le fichier de log"""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"ai_audit_{date_str}.jsonl"

        with open(log_file, "a") as f:
            f.write(event.to_json().replace("\n", " ") + "\n")


# Instance singleton
_audit_logger: Optional[AIAuditLogger] = None


def get_audit_logger() -> AIAuditLogger:
    """Récupère l'instance singleton du logger d'audit"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AIAuditLogger()
    return _audit_logger
