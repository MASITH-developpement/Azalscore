"""
AZALSCORE AI Orchestration System

Architecture:
    Interface (azalscore.com)
           ↓
    THEO (LLM Souverain - Interface humaine)
           ↓
    Orchestrateur AZALSCORE
           ↓
    Modules IA internes:
    - ChatGPT (Architecte cognitif)
    - Claude (Expert technique)
    - Guardian (Sécurité & conformité)

Conformité: AZA-NF-008, AZA-IA
"""

from app.ai.orchestrator import AIOrchestrator, get_ai_orchestrator
from app.ai.theo import TheoInterface
from app.ai.guardian import Guardian
from app.ai.roles import AIRole

__all__ = [
    "AIOrchestrator",
    "get_ai_orchestrator",
    "TheoInterface",
    "Guardian",
    "AIRole",
]
