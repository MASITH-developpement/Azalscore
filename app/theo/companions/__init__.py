"""
THÉO Companions — Système de Compagnons
=======================================

Les compagnons sont des masques vocaux/visuels.
Ils incarnent Théo avec différentes identités mais
aucune logique propre. Tout est traduit vers Théo.
"""

from app.theo.companions.registry import CompanionRegistry, Companion, get_companion_registry
from app.theo.companions.translator import CompanionTranslator, get_translator

__all__ = [
    "CompanionRegistry",
    "Companion",
    "get_companion_registry",
    "CompanionTranslator",
    "get_translator",
]
