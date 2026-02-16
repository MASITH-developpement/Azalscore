"""
AZALSCORE - Service de Sécurité API Avancé
==========================================
WAF (Web Application Firewall), détection d'intrusion, et threat intelligence.

Fonctionnalités:
- WAF avec règles OWASP CRS
- Détection d'injection SQL/XSS/Command
- Détection de bots et scanners
- Analyse comportementale
- Threat Intelligence (IP reputation)
- Honeypots et deception
- Alerting temps réel

OWASP Top 10 2021 Coverage:
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable Components
- A07: Authentication Failures
- A08: Software and Data Integrity
- A09: Security Logging
- A10: SSRF
"""

import hashlib
import ipaddress
import json
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS ET CONSTANTES
# ============================================================================

class ThreatType(str, Enum):
    """Types de menaces détectées."""
    SQL_INJECTION = "SQL_INJECTION"
    XSS = "XSS"
    COMMAND_INJECTION = "COMMAND_INJECTION"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    LDAP_INJECTION = "LDAP_INJECTION"
    XML_INJECTION = "XML_INJECTION"
    SSRF = "SSRF"
    SCANNER = "SCANNER"
    BOT = "BOT"
    BRUTE_FORCE = "BRUTE_FORCE"
    CREDENTIAL_STUFFING = "CREDENTIAL_STUFFING"
    ANOMALY = "ANOMALY"
    RATE_ABUSE = "RATE_ABUSE"
    HONEYPOT_TRIGGER = "HONEYPOT_TRIGGER"


class ThreatSeverity(str, Enum):
    """Niveaux de sévérité."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ActionType(str, Enum):
    """Actions à prendre."""
    BLOCK = "BLOCK"
    CHALLENGE = "CHALLENGE"
    LOG = "LOG"
    ALERT = "ALERT"
    RATE_LIMIT = "RATE_LIMIT"


# ============================================================================
# RÈGLES WAF (OWASP CRS)
# ============================================================================

WAF_RULES = {
    # SQL Injection
    "SQL_INJECTION": {
        "patterns": [
            r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b.*\b(FROM|INTO|WHERE|SET|TABLE)\b)",
            r"(?i)(--|\#|/\*|\*/)",
            r"(?i)(\bOR\b\s+\d+\s*=\s*\d+)",
            r"(?i)(\bAND\b\s+\d+\s*=\s*\d+)",
            r"(?i)(SLEEP\s*\(\s*\d+\s*\))",
            r"(?i)(WAITFOR\s+DELAY)",
            r"(?i)(BENCHMARK\s*\()",
            r"(?i)('|\");\s*(DROP|DELETE|UPDATE|INSERT)",
            r"(?i)(CHAR\s*\(\s*\d+\s*\))",
            r"(?i)(0x[0-9a-fA-F]+)",
            r"(?i)(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)",
            r"(?i)(information_schema|sys\.tables|sysobjects)",
        ],
        "severity": ThreatSeverity.CRITICAL,
        "action": ActionType.BLOCK
    },

    # Cross-Site Scripting (XSS)
    "XSS": {
        "patterns": [
            r"(?i)<script[^>]*>.*?</script>",
            r"(?i)<script[^>]*>",
            r"(?i)javascript\s*:",
            r"(?i)on(load|error|click|mouse|focus|blur|submit|change|key)\s*=",
            r"(?i)<iframe[^>]*>",
            r"(?i)<object[^>]*>",
            r"(?i)<embed[^>]*>",
            r"(?i)<img[^>]+onerror\s*=",
            r"(?i)<svg[^>]+onload\s*=",
            r"(?i)expression\s*\(",
            r"(?i)vbscript\s*:",
            r"(?i)data\s*:\s*text/html",
        ],
        "severity": ThreatSeverity.HIGH,
        "action": ActionType.BLOCK
    },

    # Command Injection
    "COMMAND_INJECTION": {
        "patterns": [
            r"[;&|`$]",
            r"\$\([^)]+\)",
            r"`[^`]+`",
            r"(?i)(;|\||&)\s*(ls|cat|wget|curl|nc|bash|sh|python|perl|ruby|php)\b",
            r"(?i)/etc/(passwd|shadow|hosts)",
            r"(?i)\.\./\.\./",
            r"(?i)(rm|mv|cp|chmod|chown)\s+-[rf]",
            r"(?i)>(>)?.*\.(sh|php|py|pl|rb)",
        ],
        "severity": ThreatSeverity.CRITICAL,
        "action": ActionType.BLOCK
    },

    # Path Traversal
    "PATH_TRAVERSAL": {
        "patterns": [
            r"\.\.[/\\]",
            r"(?i)%2e%2e[%2f%5c]",
            r"(?i)\.\.%c0%af",
            r"(?i)\.\.%c1%9c",
            r"(?i)/etc/passwd",
            r"(?i)c:\\windows\\system32",
            r"(?i)\\\\[a-z0-9]+\\[a-z]+\$",
        ],
        "severity": ThreatSeverity.HIGH,
        "action": ActionType.BLOCK
    },

    # LDAP Injection
    "LDAP_INJECTION": {
        "patterns": [
            r"[)(|*\\]",
            r"(?i)\(\|",
            r"(?i)\(&",
            r"(?i)\(\!",
        ],
        "severity": ThreatSeverity.HIGH,
        "action": ActionType.BLOCK
    },

    # XML/XXE Injection
    "XML_INJECTION": {
        "patterns": [
            r"(?i)<!ENTITY",
            r"(?i)<!DOCTYPE[^>]*\[",
            r"(?i)SYSTEM\s+['\"]",
            r"(?i)PUBLIC\s+['\"]",
            r"(?i)file://",
            r"(?i)expect://",
        ],
        "severity": ThreatSeverity.CRITICAL,
        "action": ActionType.BLOCK
    },

    # SSRF
    "SSRF": {
        "patterns": [
            r"(?i)(localhost|127\.0\.0\.1|0\.0\.0\.0)",
            r"(?i)(169\.254\.\d+\.\d+)",  # AWS metadata
            r"(?i)(192\.168\.\d+\.\d+)",
            r"(?i)(10\.\d+\.\d+\.\d+)",
            r"(?i)(172\.(1[6-9]|2[0-9]|3[01])\.\d+\.\d+)",
            r"(?i)file://",
            r"(?i)gopher://",
            r"(?i)dict://",
        ],
        "severity": ThreatSeverity.HIGH,
        "action": ActionType.BLOCK
    },

    # Scanner/Bot Detection
    "SCANNER": {
        "patterns": [
            r"(?i)(nikto|sqlmap|nmap|dirb|gobuster|wfuzz|hydra|burp|zap)",
            r"(?i)(acunetix|nessus|qualys|rapid7|tenable)",
            r"(?i)masscan",
            r"(?i)nuclei",
        ],
        "severity": ThreatSeverity.MEDIUM,
        "action": ActionType.RATE_LIMIT
    },
}

# User-Agents suspects
SUSPICIOUS_USER_AGENTS = [
    r"(?i)^$",  # Vide
    r"(?i)^-$",
    r"(?i)bot",
    r"(?i)crawler",
    r"(?i)spider",
    r"(?i)scraper",
    r"(?i)python-requests",
    r"(?i)python-urllib",
    r"(?i)curl",
    r"(?i)wget",
    r"(?i)httpie",
    r"(?i)postman",
    r"(?i)insomnia",
]

# Honeypots (URLs qui n'existent pas mais attirent les attaquants)
HONEYPOT_PATHS = [
    "/admin.php",
    "/wp-admin",
    "/wp-login.php",
    "/phpmyadmin",
    "/.env",
    "/.git/config",
    "/config.php",
    "/backup.sql",
    "/db.sql",
    "/.aws/credentials",
    "/server-status",
    "/.htaccess",
    "/web.config",
    "/xmlrpc.php",
]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ThreatEvent:
    """Événement de menace détectée."""
    timestamp: datetime
    threat_type: ThreatType
    severity: ThreatSeverity
    action_taken: ActionType
    client_ip: str
    path: str
    method: str
    user_agent: str
    payload: str | None = None
    rule_id: str | None = None
    details: dict = field(default_factory=dict)


@dataclass
class IPReputation:
    """Réputation d'une IP."""
    ip: str
    score: int  # 0-100, 100 = totalement fiable
    threat_count: int = 0
    last_threat: datetime | None = None
    is_blocked: bool = False
    blocked_until: datetime | None = None
    categories: list[str] = field(default_factory=list)
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SecurityAlert:
    """Alerte de sécurité."""
    id: str
    timestamp: datetime
    severity: ThreatSeverity
    title: str
    description: str
    source_ip: str
    affected_endpoints: list[str]
    event_count: int
    is_acknowledged: bool = False
    acknowledged_by: str | None = None


# ============================================================================
# THREAT INTELLIGENCE
# ============================================================================

class ThreatIntelligence:
    """Service de Threat Intelligence avec réputation IP."""

    def __init__(self):
        self._ip_reputation: dict[str, IPReputation] = {}
        self._blocked_ranges: list[ipaddress.IPv4Network] = []
        self._lock = Lock()

        # Charger les ranges malveillants connus
        self._load_known_bad_ranges()

    def _load_known_bad_ranges(self):
        """Charger les plages IP connues comme malveillantes."""
        # Tor exit nodes, bulletproof hosting, etc.
        # (En production, utiliser des feeds externes)
        pass

    def get_reputation(self, ip: str) -> IPReputation:
        """Obtenir la réputation d'une IP."""
        with self._lock:
            if ip not in self._ip_reputation:
                self._ip_reputation[ip] = IPReputation(ip=ip, score=80)
            return self._ip_reputation[ip]

    def record_threat(self, ip: str, threat_type: ThreatType, severity: ThreatSeverity):
        """Enregistrer une menace et dégrader la réputation."""
        with self._lock:
            rep = self.get_reputation(ip)
            rep.threat_count += 1
            rep.last_threat = datetime.utcnow()
            rep.last_seen = datetime.utcnow()

            # Calcul de pénalité
            penalties = {
                ThreatSeverity.CRITICAL: 30,
                ThreatSeverity.HIGH: 20,
                ThreatSeverity.MEDIUM: 10,
                ThreatSeverity.LOW: 5,
                ThreatSeverity.INFO: 2,
            }
            penalty = penalties.get(severity, 10)
            rep.score = max(0, rep.score - penalty)

            if threat_type.value not in rep.categories:
                rep.categories.append(threat_type.value)

            # Auto-block si score trop bas
            if rep.score <= 20:
                rep.is_blocked = True
                rep.blocked_until = datetime.utcnow() + timedelta(hours=24)

            self._ip_reputation[ip] = rep

    def is_ip_allowed(self, ip: str) -> tuple[bool, str | None]:
        """Vérifier si une IP est autorisée."""
        rep = self.get_reputation(ip)

        if rep.is_blocked:
            if rep.blocked_until and datetime.utcnow() > rep.blocked_until:
                # Débloquer mais garder un score bas
                rep.is_blocked = False
                rep.blocked_until = None
                rep.score = min(rep.score + 10, 50)  # Restauration partielle
            else:
                return False, "IP blocked due to repeated threats"

        # Vérifier les plages bloquées
        try:
            ip_obj = ipaddress.ip_address(ip)
            for network in self._blocked_ranges:
                if ip_obj in network:
                    return False, f"IP in blocked range: {network}"
        except ValueError:
            pass

        return True, None

    def get_statistics(self) -> dict:
        """Obtenir les statistiques de threat intelligence."""
        with self._lock:
            blocked_count = sum(1 for r in self._ip_reputation.values() if r.is_blocked)
            low_rep_count = sum(1 for r in self._ip_reputation.values() if r.score < 50)

            return {
                "total_ips_tracked": len(self._ip_reputation),
                "blocked_ips": blocked_count,
                "low_reputation_ips": low_rep_count,
                "blocked_ranges": len(self._blocked_ranges)
            }


# ============================================================================
# WAF ENGINE
# ============================================================================

class WAFEngine:
    """Moteur WAF (Web Application Firewall)."""

    def __init__(self, rules: dict = None):
        self._rules = rules or WAF_RULES
        self._compiled_rules: dict[str, list[re.Pattern]] = {}
        self._compile_rules()

    def _compile_rules(self):
        """Pré-compiler les regex pour performance."""
        for rule_name, rule_data in self._rules.items():
            self._compiled_rules[rule_name] = [
                re.compile(pattern) for pattern in rule_data["patterns"]
            ]

    def scan(self, content: str, context: str = "body") -> list[tuple[str, ThreatType, ThreatSeverity]]:
        """
        Scanner du contenu pour détecter des menaces.

        Returns:
            Liste de (rule_name, threat_type, severity)
        """
        detections = []

        for rule_name, patterns in self._compiled_rules.items():
            rule_data = self._rules[rule_name]

            for pattern in patterns:
                if pattern.search(content):
                    threat_type = ThreatType[rule_name] if rule_name in ThreatType.__members__ else ThreatType.ANOMALY
                    detections.append((
                        rule_name,
                        threat_type,
                        rule_data["severity"]
                    ))
                    break  # Une détection par règle suffit

        return detections

    def get_action(self, rule_name: str) -> ActionType:
        """Obtenir l'action pour une règle."""
        if rule_name in self._rules:
            return self._rules[rule_name]["action"]
        return ActionType.LOG


# ============================================================================
# BEHAVIORAL ANALYSIS
# ============================================================================

class BehavioralAnalyzer:
    """Analyseur comportemental pour détecter les anomalies."""

    def __init__(self):
        self._request_history: dict[str, list[dict]] = defaultdict(list)
        self._lock = Lock()
        self._max_history = 100

    def record_request(
        self,
        client_ip: str,
        path: str,
        method: str,
        status_code: int,
        response_time: float
    ):
        """Enregistrer une requête pour analyse."""
        with self._lock:
            history = self._request_history[client_ip]
            history.append({
                "timestamp": time.time(),
                "path": path,
                "method": method,
                "status": status_code,
                "response_time": response_time
            })

            # Garder seulement les N dernières
            if len(history) > self._max_history:
                self._request_history[client_ip] = history[-self._max_history:]

    def analyze(self, client_ip: str) -> list[tuple[ThreatType, ThreatSeverity, str]]:
        """Analyser le comportement d'une IP."""
        anomalies = []

        with self._lock:
            history = self._request_history.get(client_ip, [])

        if len(history) < 10:
            return anomalies

        # Analyse des patterns
        recent = history[-50:]
        now = time.time()

        # 1. Taux de requêtes anormal
        recent_1min = [r for r in recent if now - r["timestamp"] < 60]
        if len(recent_1min) > 100:
            anomalies.append((
                ThreatType.RATE_ABUSE,
                ThreatSeverity.MEDIUM,
                f"High request rate: {len(recent_1min)}/min"
            ))

        # 2. Taux d'erreurs élevé (scanner)
        errors = [r for r in recent if r["status"] >= 400]
        error_rate = len(errors) / len(recent) if recent else 0
        if error_rate > 0.5:
            anomalies.append((
                ThreatType.SCANNER,
                ThreatSeverity.MEDIUM,
                f"High error rate: {error_rate:.1%}"
            ))

        # 3. Patterns de scan (paths séquentiels)
        paths = [r["path"] for r in recent]
        unique_paths = set(paths)
        if len(unique_paths) > 30 and len(unique_paths) / len(paths) > 0.8:
            anomalies.append((
                ThreatType.SCANNER,
                ThreatSeverity.HIGH,
                f"Path enumeration detected: {len(unique_paths)} unique paths"
            ))

        # 4. Credential stuffing (POST répétés sur /login)
        login_attempts = [r for r in recent if "/login" in r["path"] and r["method"] == "POST"]
        if len(login_attempts) > 10:
            failed = [r for r in login_attempts if r["status"] in (401, 403)]
            if len(failed) > 8:
                anomalies.append((
                    ThreatType.CREDENTIAL_STUFFING,
                    ThreatSeverity.HIGH,
                    f"Credential stuffing: {len(failed)} failed logins"
                ))

        return anomalies


# ============================================================================
# API SECURITY SERVICE
# ============================================================================

class APISecurityService:
    """Service de sécurité API centralisé."""

    def __init__(self):
        self.waf = WAFEngine()
        self.threat_intel = ThreatIntelligence()
        self.behavioral = BehavioralAnalyzer()
        self._events: list[ThreatEvent] = []
        self._alerts: list[SecurityAlert] = []
        self._lock = Lock()
        self._event_handlers: list[Callable] = []

    def add_event_handler(self, handler: Callable[[ThreatEvent], None]):
        """Ajouter un handler pour les événements de sécurité."""
        self._event_handlers.append(handler)

    def _emit_event(self, event: ThreatEvent):
        """Émettre un événement aux handlers."""
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def check_request(
        self,
        client_ip: str,
        path: str,
        method: str,
        headers: dict,
        body: str | None = None,
        query_params: str | None = None
    ) -> tuple[bool, ActionType | None, str | None]:
        """
        Vérifier une requête entrante.

        Returns:
            (is_allowed, action, reason)
        """
        # 1. Vérifier réputation IP
        allowed, reason = self.threat_intel.is_ip_allowed(client_ip)
        if not allowed:
            self._record_event(
                ThreatType.ANOMALY,
                ThreatSeverity.HIGH,
                ActionType.BLOCK,
                client_ip, path, method,
                headers.get("user-agent", ""),
                details={"reason": reason}
            )
            return False, ActionType.BLOCK, reason

        # 2. Vérifier honeypots
        if path in HONEYPOT_PATHS:
            self.threat_intel.record_threat(client_ip, ThreatType.HONEYPOT_TRIGGER, ThreatSeverity.HIGH)
            self._record_event(
                ThreatType.HONEYPOT_TRIGGER,
                ThreatSeverity.HIGH,
                ActionType.BLOCK,
                client_ip, path, method,
                headers.get("user-agent", ""),
                details={"honeypot": path}
            )
            return False, ActionType.BLOCK, "Honeypot triggered"

        # 3. Vérifier User-Agent
        user_agent = headers.get("user-agent", "")
        for pattern in SUSPICIOUS_USER_AGENTS:
            if re.search(pattern, user_agent):
                # Log mais ne pas bloquer systématiquement
                logger.warning(
                    "[WAF] Suspicious user-agent detected",
                    extra={"ip": client_ip, "ua": user_agent[:100]}
                )
                break

        # 4. Scanner WAF sur URL + query
        scan_content = f"{path}?{query_params}" if query_params else path
        url_detections = self.waf.scan(scan_content, "url")

        for rule_name, threat_type, severity in url_detections:
            action = self.waf.get_action(rule_name)
            self.threat_intel.record_threat(client_ip, threat_type, severity)
            self._record_event(
                threat_type, severity, action,
                client_ip, path, method, user_agent,
                payload=scan_content[:500],
                rule_id=rule_name
            )

            if action == ActionType.BLOCK:
                return False, action, f"WAF rule triggered: {rule_name}"

        # 5. Scanner WAF sur body
        if body:
            body_detections = self.waf.scan(body, "body")

            for rule_name, threat_type, severity in body_detections:
                action = self.waf.get_action(rule_name)
                self.threat_intel.record_threat(client_ip, threat_type, severity)
                self._record_event(
                    threat_type, severity, action,
                    client_ip, path, method, user_agent,
                    payload=body[:500],
                    rule_id=rule_name
                )

                if action == ActionType.BLOCK:
                    return False, action, f"WAF rule triggered: {rule_name}"

        # 6. Scanner headers
        for header_name, header_value in headers.items():
            if header_name.lower() in ("authorization", "cookie"):
                continue  # Skip sensitive headers

            header_detections = self.waf.scan(header_value, "header")
            for rule_name, threat_type, severity in header_detections:
                action = self.waf.get_action(rule_name)
                if action == ActionType.BLOCK:
                    self._record_event(
                        threat_type, severity, action,
                        client_ip, path, method, user_agent,
                        payload=f"{header_name}: {header_value[:100]}",
                        rule_id=rule_name
                    )
                    return False, action, f"Malicious header: {header_name}"

        # 7. Analyse comportementale
        anomalies = self.behavioral.analyze(client_ip)
        for threat_type, severity, description in anomalies:
            self._record_event(
                threat_type, severity, ActionType.ALERT,
                client_ip, path, method, user_agent,
                details={"anomaly": description}
            )

            if severity in (ThreatSeverity.CRITICAL, ThreatSeverity.HIGH):
                self.threat_intel.record_threat(client_ip, threat_type, severity)

        return True, None, None

    def record_response(
        self,
        client_ip: str,
        path: str,
        method: str,
        status_code: int,
        response_time: float
    ):
        """Enregistrer une réponse pour analyse comportementale."""
        self.behavioral.record_request(
            client_ip, path, method, status_code, response_time
        )

    def _record_event(
        self,
        threat_type: ThreatType,
        severity: ThreatSeverity,
        action: ActionType,
        client_ip: str,
        path: str,
        method: str,
        user_agent: str,
        payload: str | None = None,
        rule_id: str | None = None,
        details: dict | None = None
    ):
        """Enregistrer un événement de sécurité."""
        event = ThreatEvent(
            timestamp=datetime.utcnow(),
            threat_type=threat_type,
            severity=severity,
            action_taken=action,
            client_ip=client_ip,
            path=path,
            method=method,
            user_agent=user_agent,
            payload=payload,
            rule_id=rule_id,
            details=details or {}
        )

        with self._lock:
            self._events.append(event)
            # Garder les 10000 derniers événements
            if len(self._events) > 10000:
                self._events = self._events[-10000:]

        # Logger
        logger.warning(
            "[WAF] Threat detected",
            extra={
                "threat_type": threat_type.value,
                "severity": severity.value,
                "action": action.value,
                "client_ip": client_ip,
                "path": path,
                "rule_id": rule_id
            }
        )

        # Émettre événement
        self._emit_event(event)

        # Créer alerte si critique
        if severity in (ThreatSeverity.CRITICAL, ThreatSeverity.HIGH):
            self._create_alert(event)

    def _create_alert(self, event: ThreatEvent):
        """Créer une alerte de sécurité."""
        alert_id = hashlib.sha256(
            f"{event.client_ip}:{event.threat_type.value}:{event.timestamp.isoformat()}".encode()
        ).hexdigest()[:16]

        alert = SecurityAlert(
            id=alert_id,
            timestamp=event.timestamp,
            severity=event.severity,
            title=f"{event.threat_type.value} detected from {event.client_ip}",
            description=f"Threat {event.threat_type.value} detected on {event.path}. "
                       f"Action taken: {event.action_taken.value}",
            source_ip=event.client_ip,
            affected_endpoints=[event.path],
            event_count=1
        )

        with self._lock:
            self._alerts.append(alert)

    def get_recent_events(self, limit: int = 100) -> list[ThreatEvent]:
        """Obtenir les événements récents."""
        with self._lock:
            return self._events[-limit:]

    def get_alerts(self, acknowledged: bool | None = None) -> list[SecurityAlert]:
        """Obtenir les alertes."""
        with self._lock:
            alerts = self._alerts.copy()

        if acknowledged is not None:
            alerts = [a for a in alerts if a.is_acknowledged == acknowledged]

        return alerts

    def get_dashboard_stats(self) -> dict:
        """Obtenir les statistiques pour le dashboard."""
        with self._lock:
            events = self._events.copy()

        now = datetime.utcnow()
        last_hour = [e for e in events if (now - e.timestamp).total_seconds() < 3600]
        last_24h = [e for e in events if (now - e.timestamp).total_seconds() < 86400]

        # Comptages par type
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        by_action = defaultdict(int)
        top_ips = defaultdict(int)

        for e in last_24h:
            by_type[e.threat_type.value] += 1
            by_severity[e.severity.value] += 1
            by_action[e.action_taken.value] += 1
            top_ips[e.client_ip] += 1

        return {
            "events_last_hour": len(last_hour),
            "events_last_24h": len(last_24h),
            "blocked_last_24h": by_action.get("BLOCK", 0),
            "threats_by_type": dict(by_type),
            "threats_by_severity": dict(by_severity),
            "top_threat_ips": sorted(top_ips.items(), key=lambda x: x[1], reverse=True)[:10],
            "threat_intel": self.threat_intel.get_statistics(),
            "pending_alerts": len([a for a in self._alerts if not a.is_acknowledged])
        }


# ============================================================================
# MIDDLEWARE WAF
# ============================================================================

class WAFMiddleware(BaseHTTPMiddleware):
    """Middleware WAF pour FastAPI/Starlette."""

    def __init__(self, app, security_service: APISecurityService | None = None):
        super().__init__(app)
        self.security = security_service or APISecurityService()

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extraire informations
        client_ip = self._get_client_ip(request)
        path = request.url.path
        method = request.method
        headers = dict(request.headers)
        query_params = str(request.query_params)

        # Lire body si présent
        body = None
        if method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                body = body_bytes.decode("utf-8", errors="ignore")
            except Exception:
                pass

        # Vérification WAF
        allowed, action, reason = self.security.check_request(
            client_ip=client_ip,
            path=path,
            method=method,
            headers=headers,
            body=body,
            query_params=query_params
        )

        if not allowed:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "message": "Request blocked by security policy",
                    "code": "WAF_BLOCKED"
                }
            )

        # Exécuter la requête
        response = await call_next(request)

        # Enregistrer pour analyse comportementale
        response_time = time.time() - start_time
        self.security.record_response(
            client_ip, path, method, response.status_code, response_time
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extraire l'IP client."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        if request.client:
            return request.client.host
        return "unknown"


# ============================================================================
# INSTANCE GLOBALE
# ============================================================================

_security_service: APISecurityService | None = None


def get_security_service() -> APISecurityService:
    """Obtenir l'instance globale du service de sécurité."""
    global _security_service
    if _security_service is None:
        _security_service = APISecurityService()
    return _security_service


def setup_waf(app, security_service: APISecurityService | None = None):
    """Configurer le WAF sur l'application."""
    service = security_service or get_security_service()
    app.add_middleware(WAFMiddleware, security_service=service)
    logger.info("[WAF] Web Application Firewall enabled")
    return service
