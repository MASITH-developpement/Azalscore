"""
AZALS MODULE - Marceau Default Knowledge Initialization
=========================================================

Pre-charge la base de connaissances par defaut pour un nouveau tenant.
"""
from __future__ import annotations


import logging
import uuid

from sqlalchemy.orm import Session

from app.modules.marceau.memory import MarceauMemoryService
from app.modules.marceau.models import MemoryType

logger = logging.getLogger(__name__)


# Base de connaissances par defaut
DEFAULT_KNOWLEDGE_BASE = [
    # Processus devis
    {
        "content": "Pour creer un devis: 1) Identifier le client 2) Selectionner articles 3) Calculer total 4) Generer PDF 5) Envoyer par email",
        "tags": ["devis", "processus", "commercial"],
        "importance": 1.0
    },
    {
        "content": "Champs obligatoires pour un devis: nom du client, adresse, telephone, email, description du besoin. Ne jamais creer de devis sans ces informations.",
        "tags": ["devis", "validation", "obligatoire"],
        "importance": 1.0
    },
    {
        "content": "Les prix des articles doivent toujours provenir du catalogue. Ne jamais inventer ou estimer un prix.",
        "tags": ["devis", "prix", "catalogue"],
        "importance": 1.0
    },

    # Processus intervention
    {
        "content": "Pour planifier une intervention: 1) Verifier zone de service 2) Chercher technicien disponible 3) Calculer trajet 4) Bloquer creneau 5) Confirmer",
        "tags": ["intervention", "processus", "field_service"],
        "importance": 1.0
    },
    {
        "content": "Duree standard d'une intervention: 1 heure. Ajouter le temps de trajet entre les interventions (buffer de 15 minutes minimum).",
        "tags": ["intervention", "duree", "planning"],
        "importance": 0.9
    },
    {
        "content": "Horaires de travail: 9h-18h du lundi au vendredi. Ne pas proposer de creneaux en dehors de ces horaires sauf urgence explicite.",
        "tags": ["intervention", "horaires", "planning"],
        "importance": 0.9
    },

    # Alertes et escalade
    {
        "content": "Si aucun technicien disponible sous 14 jours: alerter immediatement le manager et proposer de rappeler le client. C'est une situation urgente.",
        "tags": ["intervention", "urgence", "escalade", "manager"],
        "importance": 1.0
    },
    {
        "content": "Si le client est mecontent ou fait une reclamation: noter precisement la reclamation, proposer un rappel par un responsable, ne pas s'engager sur une resolution.",
        "tags": ["reclamation", "escalade", "client"],
        "importance": 1.0
    },

    # FAQ Telephonie
    {
        "content": "Q: Client demande devis sans articles specifiques. R: Proposer RDV diagnostic gratuit pour evaluer le besoin sur place.",
        "tags": ["faq", "devis", "diagnostic"],
        "importance": 0.8
    },
    {
        "content": "Q: Client demande prix au telephone. R: Expliquer que les prix dependent du diagnostic et proposer un devis gratuit.",
        "tags": ["faq", "prix", "telephone"],
        "importance": 0.8
    },
    {
        "content": "Q: Client veut annuler un RDV. R: Confirmer l'annulation, proposer un nouveau creneau, noter la raison de l'annulation.",
        "tags": ["faq", "annulation", "rdv"],
        "importance": 0.8
    },

    # Bonnes pratiques telephoniques
    {
        "content": "Toujours epeler l'adresse email: 'jean POINT dupont AROBASE exemple POINT com'. Cela evite les erreurs de transcription.",
        "tags": ["telephonie", "bonnes_pratiques", "email"],
        "importance": 0.9
    },
    {
        "content": "Si client change de sujet, reformuler: 'D'accord, donc vous souhaitez...' pour confirmer comprehension avant de continuer.",
        "tags": ["telephonie", "bonnes_pratiques", "reformulation"],
        "importance": 0.8
    },
    {
        "content": "Toujours recapituler les informations importantes avant de terminer l'appel: date, heure, adresse, technicien si connu.",
        "tags": ["telephonie", "bonnes_pratiques", "recapitulatif"],
        "importance": 0.9
    },
    {
        "content": "En cas de bruit ou mauvaise qualite d'appel, demander poliment au client de repeter. Ne jamais deviner une information importante.",
        "tags": ["telephonie", "bonnes_pratiques", "qualite"],
        "importance": 0.8
    },

    # Vocabulaire metier
    {
        "content": "Termes courants: intervention = RDV technique, devis = proposition commerciale, facture = document de paiement, bon de commande = validation client.",
        "tags": ["vocabulaire", "metier", "definitions"],
        "importance": 0.7
    },

    # Politesse et ton
    {
        "content": "Ton a adopter: professionnel mais chaleureux. Eviter le tutoiement. Utiliser 'Bonjour', 'Je vous remercie', 'Bonne journee'.",
        "tags": ["ton", "politesse", "communication"],
        "importance": 0.8
    },
    {
        "content": "En cas d'attente: 'Je verifie cela pour vous, merci de patienter un instant.' Ne jamais laisser le silence s'installer.",
        "tags": ["ton", "attente", "communication"],
        "importance": 0.8
    },
]


async def initialize_default_knowledge(tenant_id: str, db: Session) -> int:
    """
    Pre-charge la base de connaissances par defaut pour un nouveau tenant.

    Args:
        tenant_id: ID du tenant
        db: Session SQLAlchemy

    Returns:
        Nombre de memoires creees
    """
    logger.info(f"[MARCEAU] Initialisation base de connaissances pour tenant {tenant_id}")

    memory_service = MarceauMemoryService(tenant_id, db)
    count = 0

    for item in DEFAULT_KNOWLEDGE_BASE:
        try:
            await memory_service.store_memory(
                content=item["content"],
                memory_type=MemoryType.KNOWLEDGE,
                tags=item["tags"],
                importance_score=item["importance"],
                is_permanent=True,
                source="default_knowledge"
            )
            count += 1
        except Exception as e:
            logger.error(f"[MARCEAU] Erreur stockage connaissance: {e}")

    logger.info(f"[MARCEAU] {count} connaissances initialisees pour tenant {tenant_id}")
    return count


async def add_custom_knowledge(
    tenant_id: str,
    db: Session,
    content: str,
    tags: list[str],
    importance: float = 0.7,
    source: str = "custom"
) -> bool:
    """
    Ajoute une connaissance personnalisee.

    Args:
        tenant_id: ID du tenant
        db: Session SQLAlchemy
        content: Contenu de la connaissance
        tags: Tags de classification
        importance: Score d'importance (0-1)
        source: Source de la connaissance

    Returns:
        True si succes
    """
    try:
        memory_service = MarceauMemoryService(tenant_id, db)

        await memory_service.store_memory(
            content=content,
            memory_type=MemoryType.KNOWLEDGE,
            tags=tags,
            importance_score=importance,
            is_permanent=True,
            source=source
        )

        return True

    except Exception as e:
        logger.error(f"[MARCEAU] Erreur ajout connaissance: {e}")
        return False
