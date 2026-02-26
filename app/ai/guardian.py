"""
AZALSCORE Guardian Module

Module de sécurité et conformité transversal.
Actif en permanence sur tous les flux.

Conformité: AZA-SEC, AZA-NF-009
"""
from __future__ import annotations


import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from app.ai.audit import get_audit_logger, AuditEventType, AuditEvent
from app.ai.roles import AIRole, validate_role_action

logger = logging.getLogger(__name__)


class GuardianDecision(Enum):
    """Décisions possibles de Guardian"""
    APPROVED = "approved"
    BLOCKED = "blocked"
    ESCALATE = "escalate"
    REVIEW_REQUIRED = "review_required"


class ThreatLevel(Enum):
    """Niveaux de menace détectés"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GuardianCheckResult:
    """Résultat d'une vérification Guardian"""
    decision: GuardianDecision
    threat_level: ThreatLevel
    reason: str
    violations: List[str]
    recommendations: List[str]
    requires_human_validation: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Guardian:
    """
    Module Guardian - Sécurité & Conformité AZALSCORE

    Responsabilités:
    - Valider toutes les actions avant exécution
    - Bloquer les dérives détectées
    - Alerter le cockpit humain
    - Journaliser toutes les anomalies

    Principe: Guardian est TRANSVERSAL à tous les flux.
    """

    # Patterns de contenu dangereux
    DANGEROUS_PATTERNS = [
        r"(?i)(drop|delete|truncate)\s+table",
        r"(?i)rm\s+-rf\s+/",
        r"(?i)sudo\s+.*password",
        r"(?i)exec\s*\(",
        r"(?i)eval\s*\(",
        r"(?i)__import__",
        r"(?i)os\.system",
        r"(?i)subprocess\..*shell\s*=\s*True",
    ]

    # Actions nécessitant une validation humaine
    HUMAN_VALIDATION_REQUIRED = [
        "delete_data",
        "modify_production",
        "change_permissions",
        "access_sensitive_data",
        "modify_security_config",
        "bulk_operation",
    ]

    # Limites de rate
    RATE_LIMITS = {
        "ai_calls_per_minute": 60,
        "ai_calls_per_hour": 500,
        "sensitive_operations_per_day": 10,
    }

    def __init__(self):
        self.audit = get_audit_logger()
        self._call_counts: Dict[str, List[datetime]] = {}
        self._blocked_sessions: Dict[str, datetime] = {}
        self._alerts: List[Dict[str, Any]] = []

    def validate_request(
        self,
        session_id: str,
        user_id: Optional[str],
        action: str,
        target_module: str,
        role: AIRole,
        input_data: Dict[str, Any]
    ) -> GuardianCheckResult:
        """
        Valide une requête avant exécution

        Args:
            session_id: ID de la session
            user_id: ID de l'utilisateur (si authentifié)
            action: Action demandée
            target_module: Module cible
            role: Rôle IA utilisé
            input_data: Données d'entrée

        Returns:
            GuardianCheckResult avec la décision
        """
        violations = []
        recommendations = []
        threat_level = ThreatLevel.NONE

        # 1. Vérifier si la session est bloquée
        if session_id in self._blocked_sessions:
            return GuardianCheckResult(
                decision=GuardianDecision.BLOCKED,
                threat_level=ThreatLevel.HIGH,
                reason="Session is blocked due to previous violations",
                violations=["session_blocked"],
                recommendations=["Contact administrator"]
            )

        # 2. Vérifier le rôle et l'action
        if not validate_role_action(role, action):
            violations.append(f"Action '{action}' not allowed for role '{role.value}'")
            threat_level = ThreatLevel.MEDIUM

        # 3. Scanner le contenu pour patterns dangereux
        content_check = self._scan_content(input_data)
        if content_check["dangerous"]:
            violations.extend(content_check["patterns_found"])
            threat_level = ThreatLevel.HIGH

        # 4. Vérifier les rate limits
        rate_check = self._check_rate_limits(session_id)
        if not rate_check["allowed"]:
            violations.append(f"Rate limit exceeded: {rate_check['reason']}")
            threat_level = max(threat_level, ThreatLevel.MEDIUM, key=lambda x: x.value)

        # 5. Vérifier si validation humaine requise
        requires_human = action in self.HUMAN_VALIDATION_REQUIRED

        # Déterminer la décision
        if violations:
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                decision = GuardianDecision.BLOCKED
                self._handle_block(session_id, violations)
            elif requires_human:
                decision = GuardianDecision.REVIEW_REQUIRED
            else:
                decision = GuardianDecision.ESCALATE
                recommendations.append("Review action with elevated privileges")
        else:
            decision = GuardianDecision.APPROVED

        # Journaliser la décision
        result = GuardianCheckResult(
            decision=decision,
            threat_level=threat_level,
            reason="; ".join(violations) if violations else "All checks passed",
            violations=violations,
            recommendations=recommendations,
            requires_human_validation=requires_human,
            metadata={
                "session_id": session_id,
                "user_id": user_id,
                "action": action,
                "target_module": target_module,
                "role": role.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        self.audit.log_guardian_decision(
            session_id=session_id,
            action=action,
            approved=(decision == GuardianDecision.APPROVED),
            reason=result.reason,
            metadata=result.metadata
        )

        return result

    def validate_ai_output(
        self,
        session_id: str,
        module: str,
        output: Any
    ) -> GuardianCheckResult:
        """
        Valide la sortie d'un module IA avant transmission

        Args:
            session_id: ID de la session
            module: Module source
            output: Sortie à valider

        Returns:
            GuardianCheckResult
        """
        violations = []
        threat_level = ThreatLevel.NONE

        # Convertir en dict si nécessaire pour le scan
        if isinstance(output, str):
            scan_data = {"content": output}
        elif isinstance(output, dict):
            scan_data = output
        else:
            scan_data = {"content": str(output)}

        # Scanner le contenu
        content_check = self._scan_content(scan_data)
        if content_check["dangerous"]:
            violations.extend(content_check["patterns_found"])
            threat_level = ThreatLevel.HIGH

        # Vérifier la taille de la réponse
        output_size = len(str(output))
        if output_size > 1_000_000:  # 1MB
            violations.append("Output size exceeds maximum allowed (1MB)")
            threat_level = ThreatLevel.MEDIUM

        decision = GuardianDecision.BLOCKED if violations else GuardianDecision.APPROVED

        return GuardianCheckResult(
            decision=decision,
            threat_level=threat_level,
            reason="; ".join(violations) if violations else "Output validated",
            violations=violations,
            recommendations=[],
            metadata={"module": module, "output_size": output_size}
        )

    def alert_cockpit(
        self,
        session_id: str,
        alert_type: str,
        message: str,
        severity: ThreatLevel,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Envoie une alerte au cockpit humain

        Args:
            session_id: ID de la session
            alert_type: Type d'alerte
            message: Message d'alerte
            severity: Niveau de sévérité
            details: Détails additionnels
        """
        alert = {
            "id": f"ALERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "type": alert_type,
            "message": message,
            "severity": severity.value,
            "details": details or {},
            "acknowledged": False
        }

        self._alerts.append(alert)

        # Log l'alerte
        self.audit.log_event(AuditEvent(
            event_type=AuditEventType.GUARDIAN_ALERT,
            session_id=session_id,
            source_module="guardian",
            action="alert",
            output_data=alert,
            success=True
        ))

        logger.warning("[GUARDIAN ALERT] %s: %s", severity.value, message)

    def get_pending_alerts(self) -> List[Dict[str, Any]]:
        """Récupère les alertes non acquittées"""
        return [a for a in self._alerts if not a["acknowledged"]]

    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acquitte une alerte"""
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_by"] = user_id
                alert["acknowledged_at"] = datetime.utcnow().isoformat()
                return True
        return False

    def _scan_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scanne le contenu pour détecter des patterns dangereux

        Args:
            data: Données à scanner

        Returns:
            Résultat du scan
        """
        patterns_found = []

        def scan_value(value: Any, path: str = ""):
            if isinstance(value, str):
                for pattern in self.DANGEROUS_PATTERNS:
                    if re.search(pattern, value):
                        patterns_found.append(
                            f"Dangerous pattern at '{path}': {pattern}"
                        )
            elif isinstance(value, dict):
                for k, v in value.items():
                    scan_value(v, f"{path}.{k}" if path else k)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    scan_value(item, f"{path}[{i}]")

        scan_value(data)

        return {
            "dangerous": len(patterns_found) > 0,
            "patterns_found": patterns_found
        }

    def _check_rate_limits(self, session_id: str) -> Dict[str, Any]:
        """
        Vérifie les limites de rate

        Args:
            session_id: ID de la session

        Returns:
            Résultat de la vérification
        """
        now = datetime.utcnow()

        # Initialiser le compteur si nécessaire
        if session_id not in self._call_counts:
            self._call_counts[session_id] = []

        # Nettoyer les anciennes entrées (plus d'une heure)
        self._call_counts[session_id] = [
            t for t in self._call_counts[session_id]
            if (now - t).total_seconds() < 3600
        ]

        # Ajouter l'appel actuel
        self._call_counts[session_id].append(now)

        # Compter les appels dans la dernière minute
        calls_last_minute = sum(
            1 for t in self._call_counts[session_id]
            if (now - t).total_seconds() < 60
        )

        # Compter les appels dans la dernière heure
        calls_last_hour = len(self._call_counts[session_id])

        if calls_last_minute > self.RATE_LIMITS["ai_calls_per_minute"]:
            return {
                "allowed": False,
                "reason": f"Exceeded {self.RATE_LIMITS['ai_calls_per_minute']} calls/minute"
            }

        if calls_last_hour > self.RATE_LIMITS["ai_calls_per_hour"]:
            return {
                "allowed": False,
                "reason": f"Exceeded {self.RATE_LIMITS['ai_calls_per_hour']} calls/hour"
            }

        return {"allowed": True, "reason": "Within rate limits"}

    def _handle_block(self, session_id: str, violations: List[str]):
        """Gère un blocage de session"""
        self._blocked_sessions[session_id] = datetime.utcnow()

        self.alert_cockpit(
            session_id=session_id,
            alert_type="session_blocked",
            message=f"Session blocked due to violations: {', '.join(violations)}",
            severity=ThreatLevel.HIGH,
            details={"violations": violations}
        )


# Instance singleton
_guardian_instance: Optional[Guardian] = None


def get_guardian() -> Guardian:
    """Récupère l'instance singleton de Guardian"""
    global _guardian_instance
    if _guardian_instance is None:
        _guardian_instance = Guardian()
    return _guardian_instance
