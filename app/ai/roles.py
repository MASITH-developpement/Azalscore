"""
AZALSCORE AI Roles Definition

Chaque IA a un rôle unique et des responsabilités claires.
Aucune IA ne peut agir en dehors de son rôle.

Conformité: AZA-IA-001, AZA-NF-003
"""
from __future__ import annotations


from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class AIRole(Enum):
    """
    Rôles IA officiels AZALSCORE

    Principe: 1 appel = 1 rôle
    Aucune IA ne peut être sollicitée sans rôle explicite
    """

    # THEO - Interface humaine souveraine (IA-R5)
    THEO_DIALOGUE = "theo_dialogue"           # Dialogue avec l'humain
    THEO_CLARIFICATION = "theo_clarification" # Questions de clarification
    THEO_REFORMULATION = "theo_reformulation" # Reformulation d'intention
    THEO_ORCHESTRATION = "theo_orchestration" # Orchestration des autres IA
    THEO_SYNTHESIS = "theo_synthesis"         # Synthèse des réponses

    # CHATGPT - Architecte cognitif (IA-R7)
    GPT_STRUCTURE = "gpt_structure"           # Structuration d'intention
    GPT_DECOMPOSE = "gpt_decompose"           # Découpage cognitif
    GPT_REFORMULATE = "gpt_reformulate"       # Reformulation neutre

    # CLAUDE - Expert technique (IA-R6)
    CLAUDE_REASONING = "claude_reasoning"     # Raisonnement technique
    CLAUDE_DEBUG = "claude_debug"             # Débogage
    CLAUDE_CODE_ANALYSIS = "claude_code"      # Analyse de code
    CLAUDE_PEDAGOGY = "claude_pedagogy"       # Production pédagogique

    # GUARDIAN - Sécurité & conformité (IA-R8)
    GUARDIAN_VALIDATE = "guardian_validate"   # Validation de conformité
    GUARDIAN_AUDIT = "guardian_audit"         # Audit de flux
    GUARDIAN_BLOCK = "guardian_block"         # Blocage de dérive
    GUARDIAN_ALERT = "guardian_alert"         # Alerte cockpit


@dataclass
class AIRoleConfig:
    """Configuration d'un rôle IA"""
    role: AIRole
    description: str
    allowed_actions: List[str]
    forbidden_actions: List[str]
    requires_validation: bool = False
    timeout_ms: int = 30000
    max_retries: int = 2


# Configuration officielle des rôles
ROLE_CONFIGS = {
    # THEO Roles
    AIRole.THEO_DIALOGUE: AIRoleConfig(
        role=AIRole.THEO_DIALOGUE,
        description="Interface de dialogue avec l'utilisateur humain",
        allowed_actions=["listen", "ask", "respond", "clarify"],
        forbidden_actions=["decide", "execute", "modify_system"],
        requires_validation=False,
        timeout_ms=60000
    ),
    AIRole.THEO_CLARIFICATION: AIRoleConfig(
        role=AIRole.THEO_CLARIFICATION,
        description="Poser des questions de clarification",
        allowed_actions=["ask", "validate_understanding"],
        forbidden_actions=["assume", "interpret_norm"],
        requires_validation=False
    ),
    AIRole.THEO_ORCHESTRATION: AIRoleConfig(
        role=AIRole.THEO_ORCHESTRATION,
        description="Orchestrer les appels aux autres IA",
        allowed_actions=["route", "dispatch", "consolidate"],
        forbidden_actions=["bypass_guardian", "direct_execution"],
        requires_validation=False
    ),
    AIRole.THEO_SYNTHESIS: AIRoleConfig(
        role=AIRole.THEO_SYNTHESIS,
        description="Consolider et synthétiser les réponses",
        allowed_actions=["aggregate", "summarize", "format"],
        forbidden_actions=["add_content", "modify_meaning"],
        requires_validation=False
    ),

    # GPT Roles
    AIRole.GPT_STRUCTURE: AIRoleConfig(
        role=AIRole.GPT_STRUCTURE,
        description="Structuration d'intention utilisateur",
        allowed_actions=["analyze", "structure", "categorize"],
        forbidden_actions=["respond_to_user", "decide", "conclude"],
        requires_validation=False
    ),
    AIRole.GPT_DECOMPOSE: AIRoleConfig(
        role=AIRole.GPT_DECOMPOSE,
        description="Découpage cognitif des demandes complexes",
        allowed_actions=["decompose", "identify_subtasks"],
        forbidden_actions=["execute", "route"],
        requires_validation=False
    ),

    # CLAUDE Roles
    AIRole.CLAUDE_REASONING: AIRoleConfig(
        role=AIRole.CLAUDE_REASONING,
        description="Raisonnement technique profond",
        allowed_actions=["analyze", "reason", "explain"],
        forbidden_actions=["respond_to_user", "modify_code"],
        requires_validation=False
    ),
    AIRole.CLAUDE_DEBUG: AIRoleConfig(
        role=AIRole.CLAUDE_DEBUG,
        description="Débogage et diagnostic technique",
        allowed_actions=["diagnose", "identify_issue", "suggest_fix"],
        forbidden_actions=["apply_fix", "modify_production"],
        requires_validation=True
    ),
    AIRole.CLAUDE_CODE_ANALYSIS: AIRoleConfig(
        role=AIRole.CLAUDE_CODE_ANALYSIS,
        description="Analyse de code source",
        allowed_actions=["read_code", "analyze", "document"],
        forbidden_actions=["write_code", "execute"],
        requires_validation=False
    ),

    # GUARDIAN Roles
    AIRole.GUARDIAN_VALIDATE: AIRoleConfig(
        role=AIRole.GUARDIAN_VALIDATE,
        description="Validation de conformité des actions",
        allowed_actions=["validate", "reject", "log"],
        forbidden_actions=["execute", "bypass"],
        requires_validation=False,
        timeout_ms=5000
    ),
    AIRole.GUARDIAN_AUDIT: AIRoleConfig(
        role=AIRole.GUARDIAN_AUDIT,
        description="Audit des flux système",
        allowed_actions=["audit", "trace", "report"],
        forbidden_actions=["modify", "delete_logs"],
        requires_validation=False
    ),
    AIRole.GUARDIAN_BLOCK: AIRoleConfig(
        role=AIRole.GUARDIAN_BLOCK,
        description="Blocage des dérives détectées",
        allowed_actions=["block", "alert", "escalate"],
        forbidden_actions=["unblock_without_auth"],
        requires_validation=False,
        timeout_ms=1000  # Fast response required
    ),
    AIRole.GUARDIAN_ALERT: AIRoleConfig(
        role=AIRole.GUARDIAN_ALERT,
        description="Alerter le cockpit humain",
        allowed_actions=["alert", "notify", "log"],
        forbidden_actions=["auto_resolve"],
        requires_validation=False
    ),
}


def get_role_config(role: AIRole) -> AIRoleConfig:
    """Récupère la configuration d'un rôle"""
    return ROLE_CONFIGS.get(role)


def validate_role_action(role: AIRole, action: str) -> bool:
    """Vérifie si une action est autorisée pour un rôle"""
    config = get_role_config(role)
    if not config:
        return False

    if action in config.forbidden_actions:
        return False

    if action in config.allowed_actions:
        return True

    # Par défaut, actions non listées sont interdites
    return False
