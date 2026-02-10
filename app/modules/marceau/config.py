"""
AZALS MODULE - Marceau Configuration
=====================================

Configuration par defaut et gestion de la config par tenant.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from .models import MarceauConfig


# ============================================================================
# CONFIGURATION PAR DEFAUT
# ============================================================================

DEFAULT_ENABLED_MODULES = {
    "telephonie": True,
    "marketing": False,
    "seo": False,
    "commercial": False,
    "comptabilite": False,
    "juridique": False,
    "recrutement": False,
    "support": False,
    "orchestration": False,
}

DEFAULT_AUTONOMY_LEVELS = {
    "telephonie": 100,
    "marketing": 100,
    "seo": 100,
    "commercial": 100,
    "comptabilite": 100,
    "juridique": 100,
    "recrutement": 100,
    "support": 100,
    "orchestration": 100,
}

DEFAULT_TELEPHONY_CONFIG = {
    "asterisk_ami_host": "localhost",
    "asterisk_ami_port": 5038,
    "asterisk_ami_username": "",
    "asterisk_ami_password": "",
    "working_hours": {"start": "09:00", "end": "18:00"},
    "overflow_threshold": 2,
    "overflow_number": "",
    "appointment_duration_minutes": 60,
    "max_wait_days": 14,
    "use_travel_time": True,
    "travel_buffer_minutes": 15,
}

DEFAULT_INTEGRATIONS = {
    "ors_api_key": None,
    "gmail_credentials": None,
    "google_calendar_id": None,
    "linkedin_token": None,
    "facebook_token": None,
    "instagram_token": None,
    "slack_webhook": None,
    "hubspot_api_key": None,
    "wordpress_url": None,
    "wordpress_token": None,
}


# ============================================================================
# PROMPT SYSTEME MARCEAU
# ============================================================================

MARCEAU_SYSTEM_PROMPT = """
Tu es Marceau, l'assistant IA d'Azalscore, logiciel de gestion pour entreprises.

TON ROLE:
- Gerer les appels telephoniques avec professionnalisme et empathie
- Creer des devis en collectant: nom, adresse, telephone, email, description
- Planifier des interventions en verifiant disponibilite techniciens
- Respecter les horaires 9h-18h, duree standard 1h + temps de trajet
- Alerter si aucun creneau sous 14 jours

TON TON:
- Professionnel mais chaleureux
- Concis et efficace
- Jamais d'improvisation sur les prix
- Toujours confirmer les informations critiques

PROCESSUS DEVIS:
1. Saluer et identifier le besoin
2. Collecter TOUS les champs obligatoires (nom, adresse, telephone, email, description)
3. Proposer articles du catalogue
4. Recapituler avant validation
5. Envoyer par email en PDF

PROCESSUS INTERVENTION:
1. Collecter adresse complete et type de besoin
2. Identifier la zone de service (geocodage)
3. Chercher techniciens disponibles avec temps de trajet
4. Proposer 3 meilleurs creneaux sous 14 jours
5. Confirmer par email + SMS
6. Si pas de creneau: alerter le manager immediatement

REGLES IMPORTANTES:
- Ne jamais inventer de prix - toujours utiliser le catalogue
- Toujours confirmer les informations importantes en les repetant
- En cas de doute, proposer de rappeler ou transferer a un humain
- Etre patient et reformuler si necessaire
- Epeler les adresses email: "jean POINT dupont AROBASE exemple POINT com"
"""


# ============================================================================
# FONCTIONS DE GESTION DE CONFIGURATION
# ============================================================================

def get_marceau_config(tenant_id: str, db: Session) -> MarceauConfig | None:
    """
    Recupere la configuration Marceau pour un tenant.

    Args:
        tenant_id: ID du tenant
        db: Session SQLAlchemy

    Returns:
        MarceauConfig ou None si non trouve
    """
    return db.query(MarceauConfig).filter(
        MarceauConfig.tenant_id == tenant_id
    ).first()


def get_or_create_marceau_config(tenant_id: str, db: Session) -> MarceauConfig:
    """
    Recupere ou cree la configuration Marceau pour un tenant.

    Args:
        tenant_id: ID du tenant
        db: Session SQLAlchemy

    Returns:
        MarceauConfig (existante ou nouvellement creee)
    """
    config = get_marceau_config(tenant_id, db)

    if not config:
        config = MarceauConfig(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            enabled_modules=DEFAULT_ENABLED_MODULES.copy(),
            autonomy_levels=DEFAULT_AUTONOMY_LEVELS.copy(),
            llm_temperature=0.2,
            llm_model="llama3-8b-instruct",
            stt_model="whisper-small",
            tts_voice="fr_FR-sise-medium",
            telephony_config=DEFAULT_TELEPHONY_CONFIG.copy(),
            integrations=DEFAULT_INTEGRATIONS.copy(),
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return config


def update_marceau_config(
    tenant_id: str,
    db: Session,
    **updates
) -> MarceauConfig | None:
    """
    Met a jour la configuration Marceau.

    Args:
        tenant_id: ID du tenant
        db: Session SQLAlchemy
        **updates: Champs a mettre a jour

    Returns:
        MarceauConfig mise a jour ou None
    """
    config = get_marceau_config(tenant_id, db)

    if not config:
        return None

    for key, value in updates.items():
        if hasattr(config, key) and value is not None:
            # Pour les champs JSON, faire un merge
            if key in ('enabled_modules', 'autonomy_levels', 'telephony_config', 'integrations'):
                current_value = getattr(config, key) or {}
                if isinstance(value, dict):
                    merged = {**current_value, **value}
                    setattr(config, key, merged)
                else:
                    setattr(config, key, value)
            else:
                setattr(config, key, value)

    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)

    return config


def reset_marceau_config(tenant_id: str, db: Session) -> MarceauConfig:
    """
    Reinitialise la configuration Marceau aux valeurs par defaut.

    Args:
        tenant_id: ID du tenant
        db: Session SQLAlchemy

    Returns:
        MarceauConfig reinitialisee
    """
    config = get_marceau_config(tenant_id, db)

    if config:
        config.enabled_modules = DEFAULT_ENABLED_MODULES.copy()
        config.autonomy_levels = DEFAULT_AUTONOMY_LEVELS.copy()
        config.llm_temperature = 0.2
        config.llm_model = "llama3-8b-instruct"
        config.stt_model = "whisper-small"
        config.tts_voice = "fr_FR-sise-medium"
        config.telephony_config = DEFAULT_TELEPHONY_CONFIG.copy()
        config.integrations = DEFAULT_INTEGRATIONS.copy()
        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
    else:
        config = get_or_create_marceau_config(tenant_id, db)

    return config


def is_module_enabled(config: MarceauConfig, module_name: str) -> bool:
    """
    Verifie si un module est active.

    Args:
        config: Configuration Marceau
        module_name: Nom du module

    Returns:
        True si le module est active
    """
    if not config or not config.enabled_modules:
        return False
    return config.enabled_modules.get(module_name, False)


def get_autonomy_level(config: MarceauConfig, module_name: str) -> int:
    """
    Recupere le niveau d'autonomie d'un module.

    Args:
        config: Configuration Marceau
        module_name: Nom du module

    Returns:
        Niveau d'autonomie (0-100)
    """
    if not config or not config.autonomy_levels:
        return 100
    return config.autonomy_levels.get(module_name, 100)


def requires_validation(config: MarceauConfig, module_name: str, confidence: float) -> bool:
    """
    Determine si une action necessite validation humaine.

    Args:
        config: Configuration Marceau
        module_name: Nom du module
        confidence: Score de confiance de l'action (0-1)

    Returns:
        True si validation humaine requise
    """
    autonomy = get_autonomy_level(config, module_name)

    # Si autonomie a 100%, jamais de validation
    if autonomy >= 100:
        return False

    # Si autonomie a 0%, toujours validation
    if autonomy <= 0:
        return True

    # Sinon, comparer confiance et seuil d'autonomie
    confidence_percent = confidence * 100
    return confidence_percent < autonomy
