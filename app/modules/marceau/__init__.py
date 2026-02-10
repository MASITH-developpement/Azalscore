"""
AZALS MODULE - Marceau AI Assistant
====================================

Agent IA polyvalent pour la gestion autonome de 9 domaines metiers.
Chaque tenant dispose de son propre Marceau independant avec memoire isolee.

Modules disponibles:
- telephonie: Reception d'appels, devis, planification interventions
- marketing: Campagnes automatiques, reseaux sociaux
- seo: Generation contenu, publication WordPress
- commercial: Gestion CRM, devis automatiques
- comptabilite: Traitement factures, rapprochement
- juridique: Analyse contrats, conformite
- recrutement: Sourcing LinkedIn, scoring candidats
- support: Gestion tickets, base de connaissances
- orchestration: Coordination inter-modules, workflows
"""

from .models import (
    MarceauConfig,
    MarceauAction,
    MarceauMemory,
    MarceauConversation,
    ActionStatus,
    MemoryType,
    ConversationOutcome,
)
from .router import router

__all__ = [
    "router",
    "MarceauConfig",
    "MarceauAction",
    "MarceauMemory",
    "MarceauConversation",
    "ActionStatus",
    "MemoryType",
    "ConversationOutcome",
]
