"""
Implémentation du sous-programme : send_alert

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Side effects déclarés (envoi d'alerte)
- Non idempotent (chaque appel crée une nouvelle alerte)
"""

import uuid
from typing import Dict, Any
from datetime import datetime


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envoie une alerte système.

    Note: Cette implémentation est un stub.
    En production, elle devrait :
    - Enregistrer l'alerte en base de données
    - Envoyer un email si configuré
    - Appeler un webhook si configuré
    - Envoyer une notification push si configuré

    Args:
        inputs: {
            "alert_type": str,
            "severity": str (défaut: "warning"),
            "title": str,
            "message": str,
            "data": dict (optionnel),
            "recipients": list (optionnel)
        }

    Returns:
        {
            "alert_id": str (UUID),
            "sent_at": str (ISO 8601),
            "channels": list,
            "status": str
        }
    """
    alert_type = inputs["alert_type"]
    severity = inputs.get("severity", "warning")
    title = inputs["title"]
    message = inputs["message"]
    data = inputs.get("data", {})
    recipients = inputs.get("recipients", [])

    # Génération d'un ID unique pour l'alerte
    alert_id = str(uuid.uuid4())

    # Timestamp d'envoi
    sent_at = datetime.utcnow().isoformat() + "Z"

    # Détermination des canaux selon la sévérité
    channels = []
    if severity == "critical":
        channels = ["email", "notification", "webhook"]
    elif severity == "warning":
        channels = ["email", "notification"]
    else:  # info
        channels = ["notification"]

    # TODO: Implémenter l'envoi réel
    # - Enregistrer en base via le module notification
    # - Envoyer email via le module email
    # - Appeler webhook si configuré
    # - Envoyer notification push

    # Pour l'instant, on simule l'envoi
    status = "sent"

    return {
        "alert_id": alert_id,
        "sent_at": sent_at,
        "channels": channels,
        "status": status
    }
