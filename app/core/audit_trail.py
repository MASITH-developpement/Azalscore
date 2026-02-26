"""
AZALSCORE - Audit Trail & SIEM Service
=======================================

Service d'audit trail complet avec:
- Hash chain pour inaltérabilité (SHA-256)
- Intégration SIEM (Splunk, ELK, QRadar, Datadog)
- Alertes temps réel
- Analyse forensique
- Conformité RGPD et NIS2

Conforme aux exigences:
- ISO 27001 (A.12.4 - Logging and monitoring)
- SOC 2 Type II (CC7.2 - System monitoring)
- RGPD (Article 30 - Records of processing activities)
- NIS2 (Article 21 - Cybersecurity risk-management measures)
"""
from __future__ import annotations


import asyncio
import hashlib
import hmac
import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Callable
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class AuditEventCategory(str, Enum):
    """Catégories d'événements d'audit."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    DATA_EXPORT = "data_export"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    SYSTEM = "system"
    NETWORK = "network"
    APPLICATION = "application"
    USER_ACTIVITY = "user_activity"
    FINANCIAL = "financial"
    ADMIN = "admin"


class AuditEventSeverity(str, Enum):
    """Niveaux de sévérité des événements."""
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class AuditEventOutcome(str, Enum):
    """Résultat de l'événement."""
    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"
    IN_PROGRESS = "in_progress"


class AlertPriority(str, Enum):
    """Priorité des alertes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SIEMProvider(str, Enum):
    """Fournisseurs SIEM supportés."""
    SPLUNK = "splunk"
    ELASTICSEARCH = "elasticsearch"
    DATADOG = "datadog"
    QRADAR = "qradar"
    SENTINEL = "sentinel"
    SUMO_LOGIC = "sumo_logic"
    GRAYLOG = "graylog"
    SYSLOG = "syslog"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AuditActor:
    """Acteur de l'événement (qui a fait l'action)."""
    actor_type: str  # user, system, service, api_key, anonymous
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    auth_method: Optional[str] = None
    roles: list[str] = field(default_factory=list)
    tenant_id: Optional[str] = None


@dataclass
class AuditTarget:
    """Cible de l'action (sur quoi l'action a été effectuée)."""
    target_type: str  # resource, user, system, config
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    target_path: Optional[str] = None
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None


@dataclass
class AuditContext:
    """Contexte additionnel de l'événement."""
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    http_method: Optional[str] = None
    http_path: Optional[str] = None
    http_status: Optional[int] = None
    duration_ms: Optional[float] = None
    geo_location: Optional[dict] = None
    device_info: Optional[dict] = None
    custom_data: dict = field(default_factory=dict)


@dataclass
class AuditEvent:
    """Événement d'audit complet."""
    event_id: str
    timestamp: datetime
    category: AuditEventCategory
    action: str
    severity: AuditEventSeverity
    outcome: AuditEventOutcome
    actor: AuditActor
    target: Optional[AuditTarget]
    context: AuditContext
    description: str
    tenant_id: str

    # Hash chain
    sequence_number: int = 0
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None

    # Métadonnées
    source_system: str = "azalscore"
    version: str = "1.0"

    def to_dict(self) -> dict:
        """Convertit l'événement en dictionnaire."""
        # Handle both enum and string values
        cat_val = self.category.value if hasattr(self.category, 'value') else str(self.category)
        sev_val = self.severity.value if hasattr(self.severity, 'value') else str(self.severity)
        out_val = self.outcome.value if hasattr(self.outcome, 'value') else str(self.outcome)
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "category": cat_val,
            "action": self.action,
            "severity": sev_val,
            "outcome": out_val,
            "actor": asdict(self.actor),
            "target": asdict(self.target) if self.target else None,
            "context": asdict(self.context),
            "description": self.description,
            "tenant_id": self.tenant_id,
            "sequence_number": self.sequence_number,
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
            "source_system": self.source_system,
            "version": self.version,
        }

    def compute_hash(self, secret_key: bytes) -> str:
        """Calcule le hash HMAC-SHA256 de l'événement."""
        # Handle both enum and string values for category
        category_value = self.category.value if hasattr(self.category, 'value') else str(self.category)
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "category": category_value,
            "action": self.action,
            "actor": asdict(self.actor),
            "target": asdict(self.target) if self.target else None,
            "tenant_id": self.tenant_id,
            "sequence_number": self.sequence_number,
            "previous_hash": self.previous_hash or "",
        }

        canonical = json.dumps(data, sort_keys=True, default=str)
        return hmac.new(secret_key, canonical.encode(), hashlib.sha256).hexdigest()


@dataclass
class SecurityAlert:
    """Alerte de sécurité générée par l'analyse."""
    alert_id: str
    timestamp: datetime
    priority: AlertPriority
    title: str
    description: str
    category: str
    source_events: list[str]
    tenant_id: str
    indicators: dict = field(default_factory=dict)
    recommended_actions: list[str] = field(default_factory=list)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


@dataclass
class ThreatIndicator:
    """Indicateur de compromission (IoC)."""
    indicator_type: str  # ip, domain, hash, email, user_behavior
    value: str
    confidence: float
    threat_type: str
    first_seen: datetime
    last_seen: datetime
    occurrences: int
    related_events: list[str] = field(default_factory=list)


# =============================================================================
# SIEM EXPORTERS
# =============================================================================

class SIEMExporter(ABC):
    """Interface de base pour les exporters SIEM."""

    @abstractmethod
    async def export_event(self, event: AuditEvent) -> bool:
        """Exporte un événement vers le SIEM."""
        pass

    @abstractmethod
    async def export_alert(self, alert: SecurityAlert) -> bool:
        """Exporte une alerte vers le SIEM."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Vérifie la connectivité avec le SIEM."""
        pass


class SplunkExporter(SIEMExporter):
    """Exporter pour Splunk HEC (HTTP Event Collector)."""

    def __init__(
        self,
        hec_url: str,
        hec_token: str,
        index: str = "azalscore_audit",
        source: str = "azalscore",
        sourcetype: str = "_json",
        verify_ssl: bool = True
    ):
        self.hec_url = hec_url.rstrip("/")
        self.hec_token = hec_token
        self.index = index
        self.source = source
        self.sourcetype = sourcetype
        self.verify_ssl = verify_ssl
        self._session = None

    async def _get_session(self):
        """Retourne une session HTTP aiohttp."""
        if self._session is None:
            import aiohttp
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def export_event(self, event: AuditEvent) -> bool:
        """Exporte un événement vers Splunk."""
        try:
            session = await self._get_session()

            payload = {
                "time": event.timestamp.timestamp(),
                "host": os.environ.get("HOSTNAME", "azalscore"),
                "source": self.source,
                "sourcetype": self.sourcetype,
                "index": self.index,
                "event": event.to_dict()
            }

            headers = {
                "Authorization": f"Splunk {self.hec_token}",
                "Content-Type": "application/json"
            }

            async with session.post(
                f"{self.hec_url}/services/collector/event",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    logger.debug(f"Event {event.event_id} exported to Splunk")
                    return True
                else:
                    text = await resp.text()
                    logger.error(f"Splunk export failed: {resp.status} - {text}")
                    return False

        except Exception as e:
            logger.error(f"Splunk export error: {e}")
            return False

    async def export_alert(self, alert: SecurityAlert) -> bool:
        """Exporte une alerte vers Splunk."""
        try:
            session = await self._get_session()

            payload = {
                "time": alert.timestamp.timestamp(),
                "host": os.environ.get("HOSTNAME", "azalscore"),
                "source": self.source,
                "sourcetype": "azalscore_alert",
                "index": self.index,
                "event": {
                    "alert_id": alert.alert_id,
                    "timestamp": alert.timestamp.isoformat(),
                    "priority": alert.priority.value,
                    "title": alert.title,
                    "description": alert.description,
                    "category": alert.category,
                    "tenant_id": alert.tenant_id,
                    "indicators": alert.indicators,
                    "recommended_actions": alert.recommended_actions,
                }
            }

            headers = {
                "Authorization": f"Splunk {self.hec_token}",
                "Content-Type": "application/json"
            }

            async with session.post(
                f"{self.hec_url}/services/collector/event",
                json=payload,
                headers=headers
            ) as resp:
                return resp.status == 200

        except Exception as e:
            logger.error(f"Splunk alert export error: {e}")
            return False

    async def health_check(self) -> bool:
        """Vérifie la connectivité Splunk."""
        try:
            session = await self._get_session()
            headers = {"Authorization": f"Splunk {self.hec_token}"}
            async with session.get(
                f"{self.hec_url}/services/collector/health",
                headers=headers
            ) as resp:
                return resp.status == 200
        except Exception:
            return False


class ElasticsearchExporter(SIEMExporter):
    """Exporter pour Elasticsearch/OpenSearch."""

    def __init__(
        self,
        hosts: list[str],
        index_prefix: str = "azalscore-audit",
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        verify_ssl: bool = True
    ):
        self.hosts = hosts
        self.index_prefix = index_prefix
        self.username = username
        self.password = password
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self._client = None

    def _get_index_name(self, timestamp: datetime) -> str:
        """Génère le nom d'index avec date."""
        return f"{self.index_prefix}-{timestamp.strftime('%Y.%m.%d')}"

    async def _get_client(self):
        """Retourne un client Elasticsearch async."""
        if self._client is None:
            try:
                from elasticsearch import AsyncElasticsearch

                kwargs = {
                    "hosts": self.hosts,
                    "verify_certs": self.verify_ssl,
                }

                if self.api_key:
                    kwargs["api_key"] = self.api_key
                elif self.username and self.password:
                    kwargs["basic_auth"] = (self.username, self.password)

                self._client = AsyncElasticsearch(**kwargs)
            except ImportError:
                logger.error("elasticsearch-py not installed")
                return None
        return self._client

    async def export_event(self, event: AuditEvent) -> bool:
        """Exporte un événement vers Elasticsearch."""
        try:
            client = await self._get_client()
            if not client:
                return False

            doc = event.to_dict()
            doc["@timestamp"] = event.timestamp.isoformat()

            index_name = self._get_index_name(event.timestamp)

            await client.index(
                index=index_name,
                id=event.event_id,
                document=doc
            )

            logger.debug(f"Event {event.event_id} indexed in {index_name}")
            return True

        except Exception as e:
            logger.error(f"Elasticsearch export error: {e}")
            return False

    async def export_alert(self, alert: SecurityAlert) -> bool:
        """Exporte une alerte vers Elasticsearch."""
        try:
            client = await self._get_client()
            if not client:
                return False

            doc = {
                "alert_id": alert.alert_id,
                "@timestamp": alert.timestamp.isoformat(),
                "priority": alert.priority.value,
                "title": alert.title,
                "description": alert.description,
                "category": alert.category,
                "tenant_id": alert.tenant_id,
                "source_events": alert.source_events,
                "indicators": alert.indicators,
                "recommended_actions": alert.recommended_actions,
            }

            index_name = f"{self.index_prefix}-alerts-{alert.timestamp.strftime('%Y.%m')}"

            await client.index(
                index=index_name,
                id=alert.alert_id,
                document=doc
            )

            return True

        except Exception as e:
            logger.error(f"Elasticsearch alert export error: {e}")
            return False

    async def health_check(self) -> bool:
        """Vérifie la connectivité Elasticsearch."""
        try:
            client = await self._get_client()
            if not client:
                return False
            return await client.ping()
        except Exception:
            return False


class DatadogExporter(SIEMExporter):
    """Exporter pour Datadog."""

    def __init__(
        self,
        api_key: str,
        site: str = "datadoghq.com",
        service: str = "azalscore",
        env: str = "production"
    ):
        self.api_key = api_key
        self.site = site
        self.service = service
        self.env = env
        self._session = None

    async def _get_session(self):
        """Retourne une session HTTP."""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    async def export_event(self, event: AuditEvent) -> bool:
        """Exporte un événement vers Datadog."""
        try:
            session = await self._get_session()

            log_entry = {
                "ddsource": "azalscore",
                "ddtags": f"env:{self.env},service:{self.service},category:{event.category.value}",
                "hostname": os.environ.get("HOSTNAME", "azalscore"),
                "service": self.service,
                "status": event.severity.value,
                "message": event.description,
                **event.to_dict()
            }

            headers = {
                "DD-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            async with session.post(
                f"https://http-intake.logs.{self.site}/api/v2/logs",
                json=[log_entry],
                headers=headers
            ) as resp:
                return resp.status == 202

        except Exception as e:
            logger.error(f"Datadog export error: {e}")
            return False

    async def export_alert(self, alert: SecurityAlert) -> bool:
        """Exporte une alerte Datadog comme Event."""
        try:
            session = await self._get_session()

            # Map priority to Datadog alert type
            alert_type = {
                AlertPriority.LOW: "info",
                AlertPriority.MEDIUM: "warning",
                AlertPriority.HIGH: "error",
                AlertPriority.CRITICAL: "error"
            }.get(alert.priority, "info")

            event_data = {
                "title": alert.title,
                "text": alert.description,
                "alert_type": alert_type,
                "tags": [
                    f"tenant:{alert.tenant_id}",
                    f"category:{alert.category}",
                    f"priority:{alert.priority.value}"
                ],
                "aggregation_key": alert.category,
                "source_type_name": "azalscore"
            }

            headers = {
                "DD-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            async with session.post(
                f"https://api.{self.site}/api/v1/events",
                json=event_data,
                headers=headers
            ) as resp:
                return resp.status == 202

        except Exception as e:
            logger.error(f"Datadog alert export error: {e}")
            return False

    async def health_check(self) -> bool:
        """Vérifie la connectivité Datadog."""
        try:
            session = await self._get_session()
            headers = {"DD-API-KEY": self.api_key}
            async with session.get(
                f"https://api.{self.site}/api/v1/validate",
                headers=headers
            ) as resp:
                return resp.status == 200
        except Exception:
            return False


class SyslogExporter(SIEMExporter):
    """Exporter Syslog (RFC 5424) pour QRadar, etc."""

    def __init__(
        self,
        host: str,
        port: int = 514,
        protocol: str = "tcp",  # tcp, udp, tls
        facility: int = 1,  # user-level
        app_name: str = "azalscore",
        use_tls: bool = False,
        cert_file: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.facility = facility
        self.app_name = app_name
        self.use_tls = use_tls
        self.cert_file = cert_file
        self._socket = None

    def _severity_to_syslog(self, severity: AuditEventSeverity) -> int:
        """Convertit la sévérité en niveau syslog."""
        mapping = {
            AuditEventSeverity.EMERGENCY: 0,
            AuditEventSeverity.ALERT: 1,
            AuditEventSeverity.CRITICAL: 2,
            AuditEventSeverity.ERROR: 3,
            AuditEventSeverity.WARNING: 4,
            AuditEventSeverity.NOTICE: 5,
            AuditEventSeverity.INFO: 6,
            AuditEventSeverity.DEBUG: 7,
        }
        return mapping.get(severity, 6)

    def _format_syslog_message(self, event: AuditEvent) -> bytes:
        """Formate un message Syslog RFC 5424."""
        priority = self.facility * 8 + self._severity_to_syslog(event.severity)
        timestamp = event.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        hostname = os.environ.get("HOSTNAME", "-")

        # Structured data (SD-ID)
        sd = f'[azalscore@49152 tenant="{event.tenant_id}" action="{event.action}" ' \
             f'category="{event.category.value}" outcome="{event.outcome.value}"]'

        msg = f"<{priority}>1 {timestamp} {hostname} {self.app_name} " \
              f"{os.getpid()} {event.event_id} {sd} {event.description}"

        return msg.encode("utf-8")

    async def _send_message(self, message: bytes) -> bool:
        """Envoie un message via socket."""
        import socket
        import ssl

        try:
            if self.protocol == "udp":
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(message, (self.host, self.port))
                sock.close()
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                if self.use_tls:
                    context = ssl.create_default_context()
                    if self.cert_file:
                        context.load_verify_locations(self.cert_file)
                    sock = context.wrap_socket(sock, server_hostname=self.host)

                sock.connect((self.host, self.port))
                sock.sendall(message + b"\n")
                sock.close()

            return True

        except Exception as e:
            logger.error(f"Syslog send error: {e}")
            return False

    async def export_event(self, event: AuditEvent) -> bool:
        """Exporte un événement via Syslog."""
        message = self._format_syslog_message(event)
        return await self._send_message(message)

    async def export_alert(self, alert: SecurityAlert) -> bool:
        """Exporte une alerte via Syslog."""
        # Convertir l'alerte en événement pseudo
        severity_map = {
            AlertPriority.LOW: AuditEventSeverity.NOTICE,
            AlertPriority.MEDIUM: AuditEventSeverity.WARNING,
            AlertPriority.HIGH: AuditEventSeverity.ERROR,
            AlertPriority.CRITICAL: AuditEventSeverity.CRITICAL,
        }

        pseudo_event = AuditEvent(
            event_id=alert.alert_id,
            timestamp=alert.timestamp,
            category=AuditEventCategory.SECURITY,
            action="security_alert",
            severity=severity_map.get(alert.priority, AuditEventSeverity.WARNING),
            outcome=AuditEventOutcome.UNKNOWN,
            actor=AuditActor(actor_type="system", actor_id="siem"),
            target=None,
            context=AuditContext(),
            description=f"[ALERT:{alert.priority.value.upper()}] {alert.title} - {alert.description}",
            tenant_id=alert.tenant_id,
        )

        message = self._format_syslog_message(pseudo_event)
        return await self._send_message(message)

    async def health_check(self) -> bool:
        """Vérifie la connectivité Syslog."""
        import socket
        try:
            if self.protocol == "udp":
                return True  # UDP pas de vérification possible

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except Exception:
            return False


# =============================================================================
# THREAT DETECTION ENGINE
# =============================================================================

class ThreatDetectionEngine:
    """
    Moteur de détection des menaces en temps réel.
    Analyse les événements pour détecter les patterns suspects.
    """

    # Règles de détection
    DETECTION_RULES = {
        "brute_force_login": {
            "description": "Tentatives de connexion multiples échouées",
            "category": AuditEventCategory.AUTHENTICATION,
            "action_pattern": "login_failed",
            "threshold": 5,
            "window_seconds": 300,  # 5 minutes
            "priority": AlertPriority.HIGH,
            "group_by": "actor.ip_address"
        },
        "privilege_escalation": {
            "description": "Tentative d'escalade de privilèges",
            "category": AuditEventCategory.AUTHORIZATION,
            "action_pattern": "permission_denied",
            "threshold": 3,
            "window_seconds": 60,
            "priority": AlertPriority.CRITICAL,
            "group_by": "actor.actor_id"
        },
        "mass_data_export": {
            "description": "Export massif de données",
            "category": AuditEventCategory.DATA_EXPORT,
            "action_pattern": "export",
            "threshold": 10,
            "window_seconds": 600,
            "priority": AlertPriority.HIGH,
            "group_by": "actor.actor_id"
        },
        "mass_deletion": {
            "description": "Suppression massive de données",
            "category": AuditEventCategory.DATA_DELETION,
            "action_pattern": "delete",
            "threshold": 20,
            "window_seconds": 300,
            "priority": AlertPriority.CRITICAL,
            "group_by": "actor.actor_id"
        },
        "after_hours_activity": {
            "description": "Activité en dehors des heures ouvrées",
            "category": AuditEventCategory.DATA_ACCESS,
            "action_pattern": "*",
            "threshold": 1,
            "window_seconds": 0,  # Détection instantanée
            "priority": AlertPriority.MEDIUM,
            "time_condition": {"outside_hours": [8, 20]},  # 8h-20h
            "group_by": "actor.actor_id"
        },
        "impossible_travel": {
            "description": "Connexions depuis des lieux géographiquement impossibles",
            "category": AuditEventCategory.AUTHENTICATION,
            "action_pattern": "login_success",
            "threshold": 2,
            "window_seconds": 3600,  # 1 heure
            "priority": AlertPriority.CRITICAL,
            "group_by": "actor.actor_id",
            "geo_check": True
        },
        "credential_stuffing": {
            "description": "Tentatives avec différents comptes depuis même IP",
            "category": AuditEventCategory.AUTHENTICATION,
            "action_pattern": "login_failed",
            "threshold": 5,
            "window_seconds": 300,
            "priority": AlertPriority.HIGH,
            "group_by": "actor.ip_address",
            "count_distinct": "actor.actor_id"
        },
        "config_tampering": {
            "description": "Modification de configuration sensible",
            "category": AuditEventCategory.CONFIGURATION,
            "action_pattern": "config_change",
            "threshold": 1,
            "window_seconds": 0,
            "priority": AlertPriority.HIGH,
            "sensitive_targets": ["security", "auth", "permissions"]
        },
        "sql_injection_attempt": {
            "description": "Tentative d'injection SQL détectée",
            "category": AuditEventCategory.SECURITY,
            "action_pattern": "waf_blocked",
            "threshold": 1,
            "window_seconds": 0,
            "priority": AlertPriority.HIGH,
            "context_match": {"threat_type": "SQL_INJECTION"}
        },
        "api_abuse": {
            "description": "Abus d'API détecté",
            "category": AuditEventCategory.NETWORK,
            "action_pattern": "rate_limit_exceeded",
            "threshold": 3,
            "window_seconds": 300,
            "priority": AlertPriority.MEDIUM,
            "group_by": "actor.ip_address"
        }
    }

    def __init__(self):
        self._event_windows: dict[str, list[tuple[datetime, AuditEvent]]] = defaultdict(list)
        self._lock = threading.Lock()
        self._alert_handlers: list[Callable[[SecurityAlert], None]] = []
        self._indicators: dict[str, ThreatIndicator] = {}

    def register_alert_handler(self, handler: Callable[[SecurityAlert], None]) -> None:
        """Enregistre un handler pour les alertes."""
        self._alert_handlers.append(handler)

    async def analyze_event(self, event: AuditEvent) -> list[SecurityAlert]:
        """
        Analyse un événement et retourne les alertes générées.
        """
        alerts = []

        for rule_name, rule in self.DETECTION_RULES.items():
            alert = await self._check_rule(rule_name, rule, event)
            if alert:
                alerts.append(alert)

                # Notifier les handlers
                for handler in self._alert_handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        logger.error(f"Alert handler error: {e}")

        # Mettre à jour les indicateurs de menace
        self._update_indicators(event)

        return alerts

    async def _check_rule(
        self,
        rule_name: str,
        rule: dict,
        event: AuditEvent
    ) -> Optional[SecurityAlert]:
        """Vérifie si un événement déclenche une règle."""

        # Vérifier la catégorie
        if event.category != rule.get("category"):
            return None

        # Vérifier le pattern d'action
        action_pattern = rule.get("action_pattern", "*")
        if action_pattern != "*" and action_pattern not in event.action:
            return None

        # Vérifier les conditions de temps
        time_condition = rule.get("time_condition")
        if time_condition:
            outside_hours = time_condition.get("outside_hours")
            if outside_hours:
                current_hour = event.timestamp.hour
                start, end = outside_hours
                if start <= current_hour < end:
                    return None  # Dans les heures normales

        # Vérifier le match de contexte
        context_match = rule.get("context_match")
        if context_match:
            for key, value in context_match.items():
                if event.context.custom_data.get(key) != value:
                    return None

        # Vérifier les cibles sensibles
        sensitive_targets = rule.get("sensitive_targets")
        if sensitive_targets and event.target:
            if not any(s in (event.target.target_path or "") for s in sensitive_targets):
                return None

        # Comptage avec fenêtre temporelle
        window_seconds = rule.get("window_seconds", 0)
        threshold = rule.get("threshold", 1)

        if window_seconds > 0:
            group_by = rule.get("group_by", "actor.actor_id")
            group_key = self._get_group_key(event, group_by)
            window_key = f"{rule_name}:{group_key}"

            with self._lock:
                # Nettoyer les anciennes entrées
                cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
                self._event_windows[window_key] = [
                    (ts, e) for ts, e in self._event_windows[window_key]
                    if ts > cutoff
                ]

                # Ajouter l'événement courant
                self._event_windows[window_key].append((event.timestamp, event))

                # Vérifier le seuil
                count = len(self._event_windows[window_key])

                # Count distinct si nécessaire
                count_distinct = rule.get("count_distinct")
                if count_distinct:
                    distinct_values = set(
                        self._get_group_key(e, count_distinct)
                        for _, e in self._event_windows[window_key]
                    )
                    count = len(distinct_values)

                if count < threshold:
                    return None

                # Récupérer les IDs des événements déclencheurs
                source_events = [e.event_id for _, e in self._event_windows[window_key]]
        else:
            source_events = [event.event_id]

        # Générer l'alerte
        return SecurityAlert(
            alert_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            priority=rule.get("priority", AlertPriority.MEDIUM),
            title=f"[{rule_name.upper()}] {rule.get('description', 'Security Alert')}",
            description=self._generate_alert_description(rule_name, rule, event),
            category=rule_name,
            source_events=source_events,
            tenant_id=event.tenant_id,
            indicators={
                "rule": rule_name,
                "actor_ip": event.actor.ip_address,
                "actor_id": event.actor.actor_id,
                "action": event.action,
            },
            recommended_actions=self._get_recommended_actions(rule_name)
        )

    def _get_group_key(self, event: AuditEvent, path: str) -> str:
        """Extrait une valeur de l'événement par chemin."""
        parts = path.split(".")
        obj: Any = event

        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return "unknown"

        return str(obj) if obj else "unknown"

    def _generate_alert_description(
        self,
        rule_name: str,
        rule: dict,
        event: AuditEvent
    ) -> str:
        """Génère une description détaillée de l'alerte."""
        actor_info = f"Actor: {event.actor.actor_id or 'unknown'}"
        if event.actor.ip_address:
            actor_info += f" (IP: {event.actor.ip_address})"

        return (
            f"{rule.get('description', 'Security event detected')}\n\n"
            f"Trigger: {event.action}\n"
            f"{actor_info}\n"
            f"Tenant: {event.tenant_id}\n"
            f"Time: {event.timestamp.isoformat()}\n"
            f"Event ID: {event.event_id}"
        )

    def _get_recommended_actions(self, rule_name: str) -> list[str]:
        """Retourne les actions recommandées pour une règle."""
        actions_map = {
            "brute_force_login": [
                "Verify if user account is legitimate",
                "Consider blocking source IP temporarily",
                "Review recent successful logins from this IP",
                "Check for credential reuse across services"
            ],
            "privilege_escalation": [
                "Immediately review user permissions",
                "Check for unauthorized role changes",
                "Review recent admin activities",
                "Consider suspending user account pending investigation"
            ],
            "mass_data_export": [
                "Review exported data sensitivity",
                "Verify business justification",
                "Check if export complies with data policies",
                "Consider rate limiting user exports"
            ],
            "mass_deletion": [
                "Check backup availability",
                "Review deletion scope and impact",
                "Verify authorization for bulk operations",
                "Consider restoring deleted data if unauthorized"
            ],
            "after_hours_activity": [
                "Verify user identity",
                "Check if activity is authorized",
                "Review data accessed during session",
                "Contact user for confirmation"
            ],
            "impossible_travel": [
                "Immediately verify user identity",
                "Check for compromised credentials",
                "Review all recent sessions",
                "Consider forcing password reset"
            ],
            "credential_stuffing": [
                "Block source IP immediately",
                "Enable CAPTCHA for affected accounts",
                "Notify potentially affected users",
                "Review accounts for successful unauthorized access"
            ],
            "config_tampering": [
                "Review configuration change details",
                "Verify change authorization",
                "Check for other suspicious admin activities",
                "Consider rolling back changes"
            ],
            "sql_injection_attempt": [
                "Review WAF logs for attack patterns",
                "Check if any bypass was successful",
                "Update WAF rules if needed",
                "Report to security team"
            ],
            "api_abuse": [
                "Review API usage patterns",
                "Consider implementing stricter rate limits",
                "Check for data exfiltration",
                "Block abusive clients"
            ]
        }

        return actions_map.get(rule_name, ["Review event details", "Contact security team"])

    def _update_indicators(self, event: AuditEvent) -> None:
        """Met à jour les indicateurs de menace."""
        if event.outcome == AuditEventOutcome.FAILURE and event.actor.ip_address:
            # Tracker les IPs avec des échecs
            ip = event.actor.ip_address
            indicator_key = f"ip:{ip}"

            if indicator_key in self._indicators:
                ind = self._indicators[indicator_key]
                ind.last_seen = event.timestamp
                ind.occurrences += 1
                ind.related_events.append(event.event_id)
                if len(ind.related_events) > 100:
                    ind.related_events = ind.related_events[-100:]
            else:
                self._indicators[indicator_key] = ThreatIndicator(
                    indicator_type="ip",
                    value=ip,
                    confidence=0.3,
                    threat_type="suspicious_activity",
                    first_seen=event.timestamp,
                    last_seen=event.timestamp,
                    occurrences=1,
                    related_events=[event.event_id]
                )

    def get_indicators(self, min_confidence: float = 0.5) -> list[ThreatIndicator]:
        """Retourne les indicateurs avec un niveau de confiance minimum."""
        return [
            ind for ind in self._indicators.values()
            if ind.confidence >= min_confidence
        ]


# =============================================================================
# AUDIT TRAIL SERVICE
# =============================================================================

class AuditTrailService:
    """
    Service principal d'audit trail.

    Caractéristiques:
    - Hash chain pour inaltérabilité
    - Multi-tenant isolation
    - Intégration SIEM multiple
    - Détection de menaces temps réel
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        db_session_factory = None,
        enable_siem: bool = True,
        enable_threat_detection: bool = True
    ):
        self._secret_key = (secret_key or os.environ.get("AUDIT_SECRET_KEY", "")).encode()
        if not self._secret_key:
            # Générer une clé si non fournie (WARNING en production)
            self._secret_key = os.urandom(32)
            logger.warning("No AUDIT_SECRET_KEY provided, using random key")

        self._db_session_factory = db_session_factory
        self._sequence_counters: dict[str, int] = {}
        self._last_hashes: dict[str, str] = {}
        self._lock = threading.Lock()

        self._siem_exporters: list[SIEMExporter] = []
        self._enable_siem = enable_siem

        self._threat_engine = ThreatDetectionEngine() if enable_threat_detection else None

        # Buffer pour batch export
        self._event_buffer: list[AuditEvent] = []
        self._buffer_lock = threading.Lock()
        self._buffer_max_size = 100
        self._buffer_max_age = timedelta(seconds=5)
        self._buffer_last_flush = datetime.utcnow()

    def add_siem_exporter(self, exporter: SIEMExporter) -> None:
        """Ajoute un exporteur SIEM."""
        self._siem_exporters.append(exporter)
        logger.info(f"SIEM exporter added: {type(exporter).__name__}")

    async def log_event(
        self,
        category: AuditEventCategory,
        action: str,
        description: str,
        tenant_id: str,
        actor: Optional[AuditActor] = None,
        target: Optional[AuditTarget] = None,
        context: Optional[AuditContext] = None,
        severity: AuditEventSeverity = AuditEventSeverity.INFO,
        outcome: AuditEventOutcome = AuditEventOutcome.SUCCESS,
    ) -> AuditEvent:
        """
        Enregistre un événement d'audit.
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        # Valeurs par défaut
        if actor is None:
            actor = AuditActor(actor_type="system", actor_id="system")
        if context is None:
            context = AuditContext()

        # Obtenir le numéro de séquence et hash précédent
        with self._lock:
            # Handle both enum and string values for category
            category_value = category.value if hasattr(category, 'value') else str(category)
            chain_key = f"{tenant_id}:{category_value}"

            if chain_key not in self._sequence_counters:
                self._sequence_counters[chain_key] = 0
                self._last_hashes[chain_key] = hashlib.sha256(b"genesis").hexdigest()

            sequence_number = self._sequence_counters[chain_key] + 1
            previous_hash = self._last_hashes[chain_key]

        # Créer l'événement
        event = AuditEvent(
            event_id=event_id,
            timestamp=timestamp,
            category=category,
            action=action,
            severity=severity,
            outcome=outcome,
            actor=actor,
            target=target,
            context=context,
            description=description,
            tenant_id=tenant_id,
            sequence_number=sequence_number,
            previous_hash=previous_hash,
        )

        # Calculer et assigner le hash
        event.event_hash = event.compute_hash(self._secret_key)

        # Mettre à jour la chaîne
        with self._lock:
            self._sequence_counters[chain_key] = sequence_number
            self._last_hashes[chain_key] = event.event_hash

        # Logger localement
        logger.info(
            f"Audit: [{category.value}] {action}",
            extra={
                "event_id": event_id,
                "tenant_id": tenant_id,
                "category": category.value,
                "action": action,
                "severity": severity.value,
                "outcome": outcome.value,
                "actor_id": actor.actor_id,
            }
        )

        # Détection de menaces
        alerts = []
        if self._threat_engine:
            alerts = await self._threat_engine.analyze_event(event)

        # Export SIEM (async, non-bloquant)
        if self._enable_siem and self._siem_exporters:
            asyncio.create_task(self._export_to_siem(event, alerts))

        return event

    async def _export_to_siem(
        self,
        event: AuditEvent,
        alerts: list[SecurityAlert]
    ) -> None:
        """Exporte vers tous les SIEM configurés."""
        for exporter in self._siem_exporters:
            try:
                await exporter.export_event(event)

                for alert in alerts:
                    await exporter.export_alert(alert)

            except Exception as e:
                logger.error(f"SIEM export error: {e}")

    def verify_chain_integrity(
        self,
        tenant_id: str,
        category: AuditEventCategory,
        events: list[AuditEvent]
    ) -> tuple[bool, list[str]]:
        """
        Vérifie l'intégrité d'une chaîne d'événements.

        Returns:
            Tuple (is_valid, errors)
        """
        errors = []

        if not events:
            return True, []

        # Trier par numéro de séquence
        sorted_events = sorted(events, key=lambda e: e.sequence_number)

        previous_hash = hashlib.sha256(b"genesis").hexdigest()

        for i, event in enumerate(sorted_events):
            # Vérifier la séquence
            expected_seq = i + 1
            if event.sequence_number != expected_seq:
                errors.append(
                    f"Sequence gap: expected {expected_seq}, got {event.sequence_number}"
                )

            # Vérifier le hash précédent
            if event.previous_hash != previous_hash:
                errors.append(
                    f"Chain break at event {event.event_id}: "
                    f"previous_hash mismatch"
                )

            # Recalculer et vérifier le hash de l'événement
            computed_hash = event.compute_hash(self._secret_key)
            if event.event_hash != computed_hash:
                errors.append(
                    f"Hash mismatch for event {event.event_id}: "
                    f"stored={event.event_hash}, computed={computed_hash}"
                )

            previous_hash = event.event_hash

        return len(errors) == 0, errors

    # -------------------------------------------------------------------------
    # CONVENIENCE METHODS
    # -------------------------------------------------------------------------

    async def log_authentication(
        self,
        tenant_id: str,
        action: str,  # login_success, login_failed, logout, token_refresh
        user_id: Optional[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        auth_method: str = "password",
        outcome: AuditEventOutcome = AuditEventOutcome.SUCCESS,
        failure_reason: Optional[str] = None
    ) -> AuditEvent:
        """Log un événement d'authentification."""
        return await self.log_event(
            category=AuditEventCategory.AUTHENTICATION,
            action=action,
            description=f"Authentication: {action} for user {user_id or 'unknown'}",
            tenant_id=tenant_id,
            actor=AuditActor(
                actor_type="user" if user_id else "anonymous",
                actor_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                auth_method=auth_method,
            ),
            context=AuditContext(
                custom_data={"failure_reason": failure_reason} if failure_reason else {}
            ),
            severity=AuditEventSeverity.INFO if outcome == AuditEventOutcome.SUCCESS else AuditEventSeverity.WARNING,
            outcome=outcome,
        )

    async def log_data_access(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str = "read",
        fields_accessed: Optional[list[str]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log un accès aux données."""
        return await self.log_event(
            category=AuditEventCategory.DATA_ACCESS,
            action=f"data_{action}",
            description=f"Data access: {action} on {resource_type}/{resource_id}",
            tenant_id=tenant_id,
            actor=AuditActor(
                actor_type="user",
                actor_id=user_id,
                ip_address=ip_address,
            ),
            target=AuditTarget(
                target_type="resource",
                target_id=resource_id,
                target_name=resource_type,
            ),
            context=AuditContext(
                custom_data={"fields_accessed": fields_accessed} if fields_accessed else {}
            ),
            severity=AuditEventSeverity.INFO,
        )

    async def log_data_modification(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,  # create, update, delete
        before_state: Optional[dict] = None,
        after_state: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log une modification de données."""
        severity_map = {
            "create": AuditEventSeverity.INFO,
            "update": AuditEventSeverity.INFO,
            "delete": AuditEventSeverity.WARNING,
        }

        return await self.log_event(
            category=AuditEventCategory.DATA_MODIFICATION if action != "delete" else AuditEventCategory.DATA_DELETION,
            action=f"data_{action}",
            description=f"Data {action}: {resource_type}/{resource_id}",
            tenant_id=tenant_id,
            actor=AuditActor(
                actor_type="user",
                actor_id=user_id,
                ip_address=ip_address,
            ),
            target=AuditTarget(
                target_type="resource",
                target_id=resource_id,
                target_name=resource_type,
                before_state=before_state,
                after_state=after_state,
            ),
            severity=severity_map.get(action, AuditEventSeverity.INFO),
        )

    async def log_security_event(
        self,
        tenant_id: str,
        action: str,
        description: str,
        severity: AuditEventSeverity,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        threat_type: Optional[str] = None,
        blocked: bool = False,
    ) -> AuditEvent:
        """Log un événement de sécurité."""
        return await self.log_event(
            category=AuditEventCategory.SECURITY,
            action=action,
            description=description,
            tenant_id=tenant_id,
            actor=AuditActor(
                actor_type="user" if user_id else "external",
                actor_id=user_id,
                ip_address=ip_address,
            ),
            context=AuditContext(
                custom_data={
                    "threat_type": threat_type,
                    "blocked": blocked,
                }
            ),
            severity=severity,
            outcome=AuditEventOutcome.FAILURE if blocked else AuditEventOutcome.UNKNOWN,
        )

    async def log_compliance_event(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        compliance_type: str,  # rgpd, nf525, gdpr, soc2
        details: Optional[dict] = None,
    ) -> AuditEvent:
        """Log un événement de conformité."""
        return await self.log_event(
            category=AuditEventCategory.COMPLIANCE,
            action=f"compliance_{action}",
            description=f"Compliance ({compliance_type}): {action} on {resource_type}/{resource_id}",
            tenant_id=tenant_id,
            actor=AuditActor(
                actor_type="user",
                actor_id=user_id,
            ),
            target=AuditTarget(
                target_type="resource",
                target_id=resource_id,
                target_name=resource_type,
            ),
            context=AuditContext(
                custom_data={
                    "compliance_type": compliance_type,
                    **(details or {})
                }
            ),
            severity=AuditEventSeverity.NOTICE,
        )

    async def log_financial_event(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource_type: str,  # invoice, payment, refund
        resource_id: str,
        amount: Optional[Decimal] = None,
        currency: str = "EUR",
        details: Optional[dict] = None,
    ) -> AuditEvent:
        """Log un événement financier."""
        return await self.log_event(
            category=AuditEventCategory.FINANCIAL,
            action=f"financial_{action}",
            description=f"Financial: {action} {resource_type}/{resource_id}"
                        f"{f' ({amount} {currency})' if amount else ''}",
            tenant_id=tenant_id,
            actor=AuditActor(
                actor_type="user",
                actor_id=user_id,
            ),
            target=AuditTarget(
                target_type="resource",
                target_id=resource_id,
                target_name=resource_type,
            ),
            context=AuditContext(
                custom_data={
                    "amount": str(amount) if amount else None,
                    "currency": currency,
                    **(details or {})
                }
            ),
            severity=AuditEventSeverity.INFO,
        )

    # -------------------------------------------------------------------------
    # REPORTING & ANALYTICS
    # -------------------------------------------------------------------------

    def get_threat_indicators(self) -> list[ThreatIndicator]:
        """Retourne les indicateurs de menace actuels."""
        if self._threat_engine:
            return self._threat_engine.get_indicators()
        return []

    async def get_siem_health(self) -> dict[str, bool]:
        """Vérifie la santé de tous les connecteurs SIEM."""
        health = {}
        for exporter in self._siem_exporters:
            name = type(exporter).__name__
            try:
                health[name] = await exporter.health_check()
            except Exception:
                health[name] = False
        return health

    def get_statistics(self, tenant_id: Optional[str] = None) -> dict:
        """Retourne les statistiques d'audit."""
        stats = {
            "total_chains": len(self._sequence_counters),
            "total_events": sum(self._sequence_counters.values()),
            "siem_exporters": len(self._siem_exporters),
            "threat_indicators": len(self._threat_engine._indicators) if self._threat_engine else 0,
        }

        if tenant_id:
            tenant_chains = {
                k: v for k, v in self._sequence_counters.items()
                if k.startswith(f"{tenant_id}:")
            }
            stats["tenant_events"] = sum(tenant_chains.values())

        return stats


# =============================================================================
# MIDDLEWARE FASTAPI
# =============================================================================

class AuditMiddleware:
    """
    Middleware FastAPI pour audit automatique des requêtes.
    """

    def __init__(
        self,
        app,
        audit_service: AuditTrailService,
        exclude_paths: Optional[list[str]] = None,
        audit_request_body: bool = False,
        audit_response_body: bool = False,
    ):
        self.app = app
        self.audit_service = audit_service
        self.exclude_paths = exclude_paths or [
            "/health",
            "/ready",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ]
        self.audit_request_body = audit_request_body
        self.audit_response_body = audit_response_body

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request
        from starlette.responses import Response
        import time

        request = Request(scope, receive)
        path = request.url.path

        # Skip excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        response_status = 500

        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Déterminer le tenant_id
            tenant_id = getattr(request.state, "tenant_id", None)
            if not tenant_id:
                tenant_id = request.headers.get("X-Tenant-ID", "unknown")

            # Déterminer l'utilisateur
            user_id = getattr(request.state, "user_id", None)

            # Logger l'événement
            await self.audit_service.log_event(
                category=AuditEventCategory.NETWORK,
                action="http_request",
                description=f"{request.method} {path}",
                tenant_id=tenant_id,
                actor=AuditActor(
                    actor_type="user" if user_id else "anonymous",
                    actor_id=str(user_id) if user_id else None,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                ),
                context=AuditContext(
                    request_id=request.headers.get("X-Request-ID"),
                    http_method=request.method,
                    http_path=path,
                    http_status=response_status,
                    duration_ms=duration_ms,
                ),
                severity=AuditEventSeverity.DEBUG if response_status < 400 else AuditEventSeverity.WARNING,
                outcome=AuditEventOutcome.SUCCESS if response_status < 400 else AuditEventOutcome.FAILURE,
            )


# =============================================================================
# FACTORY & SINGLETON
# =============================================================================

_audit_service_instance: Optional[AuditTrailService] = None


def get_audit_service() -> AuditTrailService:
    """Retourne l'instance singleton du service d'audit."""
    global _audit_service_instance
    if _audit_service_instance is None:
        _audit_service_instance = AuditTrailService()
    return _audit_service_instance


def configure_audit_service(
    secret_key: Optional[str] = None,
    siem_config: Optional[dict] = None,
    enable_threat_detection: bool = True,
) -> AuditTrailService:
    """
    Configure le service d'audit avec les paramètres spécifiés.

    Args:
        secret_key: Clé secrète pour HMAC
        siem_config: Configuration des exporters SIEM
        enable_threat_detection: Activer la détection des menaces

    Returns:
        Instance configurée du service
    """
    global _audit_service_instance

    _audit_service_instance = AuditTrailService(
        secret_key=secret_key,
        enable_threat_detection=enable_threat_detection,
    )

    # Configurer les exporters SIEM
    if siem_config:
        if "splunk" in siem_config:
            cfg = siem_config["splunk"]
            exporter = SplunkExporter(
                hec_url=cfg["hec_url"],
                hec_token=cfg["hec_token"],
                index=cfg.get("index", "azalscore_audit"),
            )
            _audit_service_instance.add_siem_exporter(exporter)

        if "elasticsearch" in siem_config:
            cfg = siem_config["elasticsearch"]
            exporter = ElasticsearchExporter(
                hosts=cfg["hosts"],
                username=cfg.get("username"),
                password=cfg.get("password"),
                api_key=cfg.get("api_key"),
            )
            _audit_service_instance.add_siem_exporter(exporter)

        if "datadog" in siem_config:
            cfg = siem_config["datadog"]
            exporter = DatadogExporter(
                api_key=cfg["api_key"],
                site=cfg.get("site", "datadoghq.com"),
            )
            _audit_service_instance.add_siem_exporter(exporter)

        if "syslog" in siem_config:
            cfg = siem_config["syslog"]
            exporter = SyslogExporter(
                host=cfg["host"],
                port=cfg.get("port", 514),
                protocol=cfg.get("protocol", "tcp"),
                use_tls=cfg.get("use_tls", False),
            )
            _audit_service_instance.add_siem_exporter(exporter)

    logger.info(
        "Audit service configured",
        extra={
            "siem_exporters": len(_audit_service_instance._siem_exporters),
            "threat_detection": enable_threat_detection,
        }
    )

    return _audit_service_instance
