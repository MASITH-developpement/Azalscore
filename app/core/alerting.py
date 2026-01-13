"""
AZALS - Systeme d'Alertes et Observabilite
==========================================
Alertes critiques, warnings et monitoring.

NIVEAUX D'ALERTE:
- INFO: Information, pas d'action requise
- WARNING: Attention requise, pas critique
- CRITICAL: Action immediate requise
- EMERGENCY: Systeme en danger

CANAUX DE NOTIFICATION:
- Logs structures (toujours actif)
- Webhook (Slack, Discord, Teams)
- Email (SMTP)
- Prometheus metrics

ALERTES SUPPORTEES:
- Crash application
- Backup absent/echoue
- Corruption detectee
- Dechiffrement impossible
- Lenteurs
- Echecs repetes
- Espace disque faible
- Memoire elevee
"""

import os
import json
import logging
import smtplib
import threading
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict
import requests

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Niveaux d'alerte."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(str, Enum):
    """Types d'alertes predefinies."""
    # Systeme
    APP_CRASH = "app_crash"
    APP_SLOW = "app_slow"
    MEMORY_HIGH = "memory_high"
    DISK_LOW = "disk_low"
    CPU_HIGH = "cpu_high"

    # Backup
    BACKUP_MISSING = "backup_missing"
    BACKUP_FAILED = "backup_failed"
    BACKUP_DELAYED = "backup_delayed"

    # Donnees
    CORRUPTION_DETECTED = "corruption_detected"
    DECRYPTION_FAILED = "decryption_failed"
    DATA_INTEGRITY_ERROR = "data_integrity_error"

    # Securite
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    BRUTE_FORCE_DETECTED = "brute_force_detected"
    SECRET_EXPOSED = "secret_exposed"

    # Performance
    SLOW_QUERY = "slow_query"
    HIGH_LATENCY = "high_latency"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Tenant
    TENANT_ISOLATED = "tenant_isolated"
    TENANT_QUOTA_EXCEEDED = "tenant_quota_exceeded"

    # Custom
    CUSTOM = "custom"


@dataclass
class Alert:
    """Alerte structuree."""
    alert_type: AlertType
    level: AlertLevel
    message: str
    tenant_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    alert_id: str = field(default_factory=lambda: f"alert-{datetime.now().strftime('%Y%m%d%H%M%S%f')}")
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class AlertConfig:
    """Configuration du systeme d'alertes."""
    # Logs
    log_all_alerts: bool = True

    # Webhook (Slack, Discord, etc.)
    webhook_url: Optional[str] = None
    webhook_enabled: bool = False

    # Email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_to: List[str] = field(default_factory=list)
    email_enabled: bool = False

    # Prometheus
    prometheus_enabled: bool = True

    # Seuils
    memory_warning_percent: int = 80
    memory_critical_percent: int = 95
    disk_warning_percent: int = 80
    disk_critical_percent: int = 95
    backup_max_age_hours: int = 25  # Alert si backup > 25h

    # Rate limiting des alertes (evite le spam)
    alert_cooldown_minutes: int = 5


class AlertingService:
    """
    Service centralize d'alertes.

    Gere la creation, l'envoi et le suivi des alertes.
    """

    _instance: Optional['AlertingService'] = None
    _lock = threading.Lock()

    def __init__(self, config: Optional[AlertConfig] = None):
        """
        Initialise le service d'alertes.

        Args:
            config: Configuration personnalisee.
                   Si None, lit depuis l'environnement.
        """
        self.config = config or self._load_config_from_env()
        self._alerts: List[Alert] = []
        self._alert_counts: Dict[str, int] = defaultdict(int)
        self._last_alert_time: Dict[str, datetime] = {}
        self._callbacks: List[Callable[[Alert], None]] = []

        # Initialise les metriques Prometheus si disponible
        self._init_prometheus_metrics()

    @classmethod
    def get_instance(cls) -> 'AlertingService':
        """Obtient l'instance singleton."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset le singleton (tests)."""
        with cls._lock:
            cls._instance = None

    def _load_config_from_env(self) -> AlertConfig:
        """Charge la configuration depuis l'environnement."""
        smtp_to = os.environ.get("ALERT_EMAIL_TO", "")

        return AlertConfig(
            log_all_alerts=os.environ.get("ALERT_LOG_ALL", "true").lower() == "true",
            webhook_url=os.environ.get("ALERT_WEBHOOK_URL"),
            webhook_enabled=bool(os.environ.get("ALERT_WEBHOOK_URL")),
            smtp_host=os.environ.get("SMTP_HOST"),
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            smtp_user=os.environ.get("SMTP_USER"),
            smtp_password=os.environ.get("SMTP_PASSWORD"),
            smtp_from=os.environ.get("SMTP_FROM", "alerts@azalscore.com"),
            smtp_to=smtp_to.split(",") if smtp_to else [],
            email_enabled=bool(os.environ.get("SMTP_HOST")),
            prometheus_enabled=os.environ.get("PROMETHEUS_ENABLED", "true").lower() == "true",
            memory_warning_percent=int(os.environ.get("ALERT_MEMORY_WARNING", "80")),
            memory_critical_percent=int(os.environ.get("ALERT_MEMORY_CRITICAL", "95")),
            disk_warning_percent=int(os.environ.get("ALERT_DISK_WARNING", "80")),
            disk_critical_percent=int(os.environ.get("ALERT_DISK_CRITICAL", "95")),
            backup_max_age_hours=int(os.environ.get("ALERT_BACKUP_MAX_AGE", "25")),
            alert_cooldown_minutes=int(os.environ.get("ALERT_COOLDOWN", "5")),
        )

    def _init_prometheus_metrics(self) -> None:
        """Initialise les metriques Prometheus."""
        if not self.config.prometheus_enabled:
            return

        try:
            from prometheus_client import Counter, Gauge, Histogram

            self.alerts_total = Counter(
                'azals_alerts_total',
                'Total number of alerts',
                ['type', 'level', 'tenant_id']
            )

            self.active_alerts = Gauge(
                'azals_active_alerts',
                'Number of active (unresolved) alerts',
                ['type', 'level']
            )

            self.alert_latency = Histogram(
                'azals_alert_notification_latency_seconds',
                'Time to send alert notifications',
                ['channel']
            )

        except ImportError:
            logger.debug("prometheus_client non disponible")

    def alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        message: str,
        tenant_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        Cree et envoie une alerte.

        Args:
            alert_type: Type d'alerte
            level: Niveau de severite
            message: Message descriptif
            tenant_id: ID du tenant concerne (optionnel)
            details: Details supplementaires

        Returns:
            L'alerte creee
        """
        # Verifie le cooldown
        cooldown_key = f"{alert_type.value}:{tenant_id or 'global'}"
        if self._is_in_cooldown(cooldown_key):
            logger.debug(f"Alerte en cooldown: {cooldown_key}")
            return None

        alert = Alert(
            alert_type=alert_type,
            level=level,
            message=message,
            tenant_id=tenant_id,
            details=details or {}
        )

        # Stocke l'alerte
        self._alerts.append(alert)
        self._alert_counts[alert_type.value] += 1
        self._last_alert_time[cooldown_key] = datetime.now(timezone.utc)

        # Log
        if self.config.log_all_alerts:
            self._log_alert(alert)

        # Envoie les notifications
        self._send_notifications(alert)

        # Metriques Prometheus
        self._record_prometheus_metrics(alert)

        # Callbacks personnalises
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Callback d'alerte echoue: {e}")

        return alert

    def _is_in_cooldown(self, key: str) -> bool:
        """Verifie si une alerte est en periode de cooldown."""
        last_time = self._last_alert_time.get(key)
        if not last_time:
            return False

        cooldown = timedelta(minutes=self.config.alert_cooldown_minutes)
        return datetime.now(timezone.utc) - last_time < cooldown

    def _log_alert(self, alert: Alert) -> None:
        """Log une alerte."""
        log_data = {
            "alert_id": alert.alert_id,
            "type": alert.alert_type.value,
            "level": alert.level.value,
            "message": alert.message,
            "tenant_id": alert.tenant_id,
            "timestamp": alert.timestamp.isoformat(),
        }

        if alert.level == AlertLevel.EMERGENCY:
            logger.critical(f"[ALERT] {json.dumps(log_data)}")
        elif alert.level == AlertLevel.CRITICAL:
            logger.error(f"[ALERT] {json.dumps(log_data)}")
        elif alert.level == AlertLevel.WARNING:
            logger.warning(f"[ALERT] {json.dumps(log_data)}")
        else:
            logger.info(f"[ALERT] {json.dumps(log_data)}")

    def _send_notifications(self, alert: Alert) -> None:
        """Envoie les notifications pour une alerte."""
        # Webhook (async pour ne pas bloquer)
        if self.config.webhook_enabled and alert.level in (AlertLevel.CRITICAL, AlertLevel.EMERGENCY):
            threading.Thread(
                target=self._send_webhook,
                args=(alert,),
                daemon=True
            ).start()

        # Email
        if self.config.email_enabled and alert.level == AlertLevel.EMERGENCY:
            threading.Thread(
                target=self._send_email,
                args=(alert,),
                daemon=True
            ).start()

    def _send_webhook(self, alert: Alert) -> None:
        """Envoie une alerte via webhook."""
        if not self.config.webhook_url:
            return

        try:
            # Format pour Slack/Discord/Teams
            payload = {
                "text": f"**[{alert.level.value.upper()}]** {alert.message}",
                "attachments": [{
                    "color": self._get_alert_color(alert.level),
                    "fields": [
                        {"title": "Type", "value": alert.alert_type.value, "short": True},
                        {"title": "Tenant", "value": alert.tenant_id or "Global", "short": True},
                        {"title": "Time", "value": alert.timestamp.isoformat(), "short": True},
                    ]
                }]
            }

            response = requests.post(
                self.config.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            logger.debug(f"Webhook envoye: {alert.alert_id}")

        except Exception as e:
            logger.error(f"Webhook echoue: {e}")

    def _send_email(self, alert: Alert) -> None:
        """Envoie une alerte par email."""
        if not self.config.smtp_host or not self.config.smtp_to:
            return

        try:
            msg = MIMEMultipart()
            msg['Subject'] = f"[AZALS {alert.level.value.upper()}] {alert.alert_type.value}"
            msg['From'] = self.config.smtp_from
            msg['To'] = ", ".join(self.config.smtp_to)

            body = f"""
AZALS Alert Notification
========================

Level: {alert.level.value.upper()}
Type: {alert.alert_type.value}
Message: {alert.message}
Tenant: {alert.tenant_id or 'Global'}
Time: {alert.timestamp.isoformat()}

Details:
{json.dumps(alert.details, indent=2)}

---
This is an automated alert from AZALS.
            """

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                if self.config.smtp_user and self.config.smtp_password:
                    server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)

            logger.debug(f"Email envoye: {alert.alert_id}")

        except Exception as e:
            logger.error(f"Email echoue: {e}")

    def _get_alert_color(self, level: AlertLevel) -> str:
        """Retourne la couleur pour un niveau d'alerte (format Slack)."""
        colors = {
            AlertLevel.INFO: "#36a64f",
            AlertLevel.WARNING: "#ffcc00",
            AlertLevel.CRITICAL: "#ff6600",
            AlertLevel.EMERGENCY: "#ff0000",
        }
        return colors.get(level, "#808080")

    def _record_prometheus_metrics(self, alert: Alert) -> None:
        """Enregistre les metriques Prometheus."""
        if not self.config.prometheus_enabled:
            return

        try:
            tenant = alert.tenant_id or "global"
            self.alerts_total.labels(
                type=alert.alert_type.value,
                level=alert.level.value,
                tenant_id=tenant
            ).inc()

            self.active_alerts.labels(
                type=alert.alert_type.value,
                level=alert.level.value
            ).inc()

        except Exception:
            pass

    def acknowledge(self, alert_id: str) -> bool:
        """Acquitte une alerte."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alerte acquittee: {alert_id}")
                return True
        return False

    def resolve(self, alert_id: str) -> bool:
        """Resout une alerte."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                # Decremente le compteur Prometheus
                if self.config.prometheus_enabled:
                    try:
                        self.active_alerts.labels(
                            type=alert.alert_type.value,
                            level=alert.level.value
                        ).dec()
                    except Exception:
                        pass
                logger.info(f"Alerte resolue: {alert_id}")
                return True
        return False

    def get_active_alerts(
        self,
        tenant_id: Optional[str] = None,
        level: Optional[AlertLevel] = None
    ) -> List[Alert]:
        """Retourne les alertes actives (non resolues)."""
        alerts = [a for a in self._alerts if not a.resolved]

        if tenant_id:
            alerts = [a for a in alerts if a.tenant_id == tenant_id]

        if level:
            alerts = [a for a in alerts if a.level == level]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur les alertes."""
        active = [a for a in self._alerts if not a.resolved]

        by_level = defaultdict(int)
        by_type = defaultdict(int)

        for alert in active:
            by_level[alert.level.value] += 1
            by_type[alert.alert_type.value] += 1

        return {
            "total_alerts": len(self._alerts),
            "active_alerts": len(active),
            "by_level": dict(by_level),
            "by_type": dict(by_type),
            "last_24h": len([
                a for a in self._alerts
                if a.timestamp > datetime.now(timezone.utc) - timedelta(hours=24)
            ])
        }

    def register_callback(self, callback: Callable[[Alert], None]) -> None:
        """Enregistre un callback pour les nouvelles alertes."""
        self._callbacks.append(callback)


# ============================================================================
# ALERTES PRE-DEFINIES
# ============================================================================

def alert_app_crash(error: str, details: Optional[Dict] = None) -> Alert:
    """Alerte crash application."""
    service = AlertingService.get_instance()
    return service.alert(
        AlertType.APP_CRASH,
        AlertLevel.EMERGENCY,
        f"Application crash: {error}",
        details=details
    )


def alert_backup_missing(tenant_id: str, last_backup_age_hours: int) -> Alert:
    """Alerte backup manquant."""
    service = AlertingService.get_instance()
    return service.alert(
        AlertType.BACKUP_MISSING,
        AlertLevel.CRITICAL,
        f"Backup manquant pour tenant {tenant_id[:8]}. Dernier backup: {last_backup_age_hours}h",
        tenant_id=tenant_id,
        details={"last_backup_age_hours": last_backup_age_hours}
    )


def alert_backup_failed(tenant_id: str, error: str) -> Alert:
    """Alerte backup echoue."""
    service = AlertingService.get_instance()
    return service.alert(
        AlertType.BACKUP_FAILED,
        AlertLevel.CRITICAL,
        f"Backup echoue pour tenant {tenant_id[:8]}: {error}",
        tenant_id=tenant_id,
        details={"error": error}
    )


def alert_corruption_detected(tenant_id: str, corruption_type: str, details: Dict) -> Alert:
    """Alerte corruption detectee."""
    service = AlertingService.get_instance()
    return service.alert(
        AlertType.CORRUPTION_DETECTED,
        AlertLevel.EMERGENCY,
        f"Corruption detectee pour tenant {tenant_id[:8]}: {corruption_type}",
        tenant_id=tenant_id,
        details=details
    )


def alert_decryption_failed(tenant_id: str, error: str) -> Alert:
    """Alerte dechiffrement impossible."""
    service = AlertingService.get_instance()
    return service.alert(
        AlertType.DECRYPTION_FAILED,
        AlertLevel.EMERGENCY,
        f"Dechiffrement impossible pour tenant {tenant_id[:8]}: {error}",
        tenant_id=tenant_id,
        details={"error": error}
    )


def alert_slow_query(query: str, duration_ms: int, tenant_id: Optional[str] = None) -> Alert:
    """Alerte requete lente."""
    service = AlertingService.get_instance()
    return service.alert(
        AlertType.SLOW_QUERY,
        AlertLevel.WARNING,
        f"Requete lente ({duration_ms}ms): {query[:100]}...",
        tenant_id=tenant_id,
        details={"query": query, "duration_ms": duration_ms}
    )


def alert_memory_high(percent: int) -> Alert:
    """Alerte memoire elevee."""
    service = AlertingService.get_instance()
    config = service.config

    level = AlertLevel.WARNING
    if percent >= config.memory_critical_percent:
        level = AlertLevel.CRITICAL

    return service.alert(
        AlertType.MEMORY_HIGH,
        level,
        f"Utilisation memoire elevee: {percent}%",
        details={"percent": percent}
    )


def alert_disk_low(percent: int, path: str = "/") -> Alert:
    """Alerte espace disque faible."""
    service = AlertingService.get_instance()
    config = service.config

    level = AlertLevel.WARNING
    if percent >= config.disk_critical_percent:
        level = AlertLevel.CRITICAL

    return service.alert(
        AlertType.DISK_LOW,
        level,
        f"Espace disque faible sur {path}: {percent}% utilise",
        details={"percent": percent, "path": path}
    )


def alert_unauthorized_access(tenant_id: str, attempted_tenant: str, user_id: str) -> Alert:
    """Alerte acces non autorise."""
    service = AlertingService.get_instance()
    return service.alert(
        AlertType.UNAUTHORIZED_ACCESS,
        AlertLevel.CRITICAL,
        f"Tentative d'acces non autorise: user {user_id[:8]} (tenant {tenant_id[:8]}) vers tenant {attempted_tenant[:8]}",
        tenant_id=tenant_id,
        details={"attempted_tenant": attempted_tenant, "user_id": user_id}
    )


def alert_tenant_isolated(tenant_id: str, reason: str) -> Alert:
    """Alerte tenant isole."""
    service = AlertingService.get_instance()
    return service.alert(
        AlertType.TENANT_ISOLATED,
        AlertLevel.CRITICAL,
        f"Tenant {tenant_id[:8]} isole: {reason}",
        tenant_id=tenant_id,
        details={"reason": reason}
    )


# ============================================================================
# MONITORING PROACTIF
# ============================================================================

class SystemMonitor:
    """
    Moniteur systeme proactif.

    Verifie periodiquement l'etat du systeme et declenche des alertes.
    """

    def __init__(self, check_interval_seconds: int = 60):
        """
        Args:
            check_interval_seconds: Intervalle entre les verifications
        """
        self.check_interval = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Demarre le monitoring."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("System monitor demarre")

    def stop(self) -> None:
        """Arrete le monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("System monitor arrete")

    def _monitor_loop(self) -> None:
        """Boucle principale de monitoring."""
        import time

        while self._running:
            try:
                self._check_memory()
                self._check_disk()
                self._check_backups()
            except Exception as e:
                logger.error(f"Erreur monitoring: {e}")

            time.sleep(self.check_interval)

    def _check_memory(self) -> None:
        """Verifie l'utilisation memoire."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent >= 80:
                alert_memory_high(int(memory.percent))
        except ImportError:
            pass

    def _check_disk(self) -> None:
        """Verifie l'espace disque."""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            if disk.percent >= 80:
                alert_disk_low(int(disk.percent), "/")
        except ImportError:
            pass

    def _check_backups(self) -> None:
        """Verifie l'age des backups."""
        # Implementation depend de la structure DB
        pass


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'AlertLevel',
    'AlertType',
    'Alert',
    'AlertConfig',
    'AlertingService',
    'SystemMonitor',
    'alert_app_crash',
    'alert_backup_missing',
    'alert_backup_failed',
    'alert_corruption_detected',
    'alert_decryption_failed',
    'alert_slow_query',
    'alert_memory_high',
    'alert_disk_low',
    'alert_unauthorized_access',
    'alert_tenant_isolated',
]
