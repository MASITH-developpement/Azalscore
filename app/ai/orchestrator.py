"""
AZALSCORE AI Orchestrator

Orchestrateur central des modules IA.
Gère le routage, la coordination et la consolidation.

Conformité: AZA-NF-003, AZA-IA
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from app.ai.roles import AIRole, get_role_config, validate_role_action
from app.ai.audit import get_audit_logger, AuditEventType
from app.ai.guardian import get_guardian, GuardianDecision

logger = logging.getLogger(__name__)


class AIModule(Enum):
    """Modules IA disponibles"""
    THEO = "theo"
    GPT = "gpt"
    CLAUDE = "claude"
    GUARDIAN = "guardian"


@dataclass
class AICallRequest:
    """Requête d'appel IA"""
    session_id: str
    module: AIModule
    role: AIRole
    input_data: Dict[str, Any]
    timeout_ms: int = 30000
    require_validation: bool = False
    context: Optional[Dict[str, Any]] = None


@dataclass
class AICallResult:
    """Résultat d'un appel IA"""
    success: bool
    module: AIModule
    role: AIRole
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: int = 0
    validated_by_guardian: bool = False


class AIOrchestrator:
    """
    Orchestrateur Central AZALSCORE

    Responsabilités:
    - Router les requêtes vers les bons modules IA
    - Appliquer les règles: 1 appel = 1 rôle
    - Coordonner les validations croisées
    - Gérer les divergences et escalades
    - Garantir la traçabilité complète

    Principe: Aucun module IA ne s'appelle directement.
    Tout passe par l'orchestrateur.
    """

    def __init__(self):
        self.audit = get_audit_logger()
        self.guardian = get_guardian()
        self._module_clients: Dict[AIModule, Any] = {}
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialise les clients des modules IA"""
        # OpenAI (GPT)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from openai import OpenAI
                self._module_clients[AIModule.GPT] = OpenAI(api_key=openai_key)
                logger.info("[ORCHESTRATOR] GPT client initialized")
            except Exception as e:
                logger.warning("[ORCHESTRATOR] Failed to init GPT: %s", e)

        # Anthropic (Claude)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic
                self._module_clients[AIModule.CLAUDE] = anthropic.Anthropic(
                    api_key=anthropic_key
                )
                logger.info("[ORCHESTRATOR] Claude client initialized")
            except Exception as e:
                logger.warning("[ORCHESTRATOR] Failed to init Claude: %s", e)

    def call(self, request: AICallRequest) -> AICallResult:
        """
        Effectue un appel IA orchestré

        Args:
            request: Requête d'appel

        Returns:
            AICallResult
        """
        start_time = time.time()

        # 1. Validation Guardian
        guardian_check = self.guardian.validate_request(
            session_id=request.session_id,
            user_id=None,
            action=request.role.value,
            target_module=request.module.value,
            role=request.role,
            input_data=request.input_data
        )

        if guardian_check.decision == GuardianDecision.BLOCKED:
            return AICallResult(
                success=False,
                module=request.module,
                role=request.role,
                error=f"Blocked by Guardian: {guardian_check.reason}",
                validated_by_guardian=False
            )

        # 2. Vérifier le rôle
        role_config = get_role_config(request.role)
        if not role_config:
            return AICallResult(
                success=False,
                module=request.module,
                role=request.role,
                error=f"Invalid role: {request.role.value}"
            )

        # 3. Log le dispatch
        self.audit.log_theo_dispatch(
            session_id=request.session_id,
            target_module=request.module.value,
            role=request.role.value,
            input_data=request.input_data
        )

        # 4. Exécuter l'appel selon le module
        try:
            if request.module == AIModule.GPT:
                output = self._call_gpt(request)
            elif request.module == AIModule.CLAUDE:
                output = self._call_claude(request)
            else:
                return AICallResult(
                    success=False,
                    module=request.module,
                    role=request.role,
                    error=f"Module not supported: {request.module.value}"
                )

            duration_ms = int((time.time() - start_time) * 1000)

            # 5. Validation de la sortie par Guardian
            output_check = self.guardian.validate_ai_output(
                session_id=request.session_id,
                module=request.module.value,
                output=output
            )

            if output_check.decision == GuardianDecision.BLOCKED:
                return AICallResult(
                    success=False,
                    module=request.module,
                    role=request.role,
                    error=f"Output blocked by Guardian: {output_check.reason}",
                    duration_ms=duration_ms,
                    validated_by_guardian=False
                )

            # 6. Log le résultat
            self.audit.log_ai_call(
                session_id=request.session_id,
                module=request.module.value,
                role=request.role.value,
                input_data=request.input_data,
                output_data={"output": str(output)[:500]},  # Tronqué pour le log
                success=True,
                duration_ms=duration_ms
            )

            return AICallResult(
                success=True,
                module=request.module,
                role=request.role,
                output=output,
                duration_ms=duration_ms,
                validated_by_guardian=True
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            self.audit.log_ai_call(
                session_id=request.session_id,
                module=request.module.value,
                role=request.role.value,
                input_data=request.input_data,
                success=False,
                error_message=error_msg,
                duration_ms=duration_ms
            )

            return AICallResult(
                success=False,
                module=request.module,
                role=request.role,
                error=error_msg,
                duration_ms=duration_ms
            )

    def _call_gpt(self, request: AICallRequest) -> str:
        """
        Appelle le module GPT (architecte cognitif)

        Args:
            request: Requête

        Returns:
            Réponse texte
        """
        client = self._module_clients.get(AIModule.GPT)
        if not client:
            raise RuntimeError("GPT client not initialized")

        # Construire le prompt selon le rôle
        system_prompt = self._get_gpt_system_prompt(request.role)
        user_content = self._format_input(request.input_data)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=2000,
            temperature=0.3
        )

        return response.choices[0].message.content

    def _call_claude(self, request: AICallRequest) -> str:
        """
        Appelle le module Claude (expert technique)

        Args:
            request: Requête

        Returns:
            Réponse texte
        """
        client = self._module_clients.get(AIModule.CLAUDE)
        if not client:
            raise RuntimeError("Claude client not initialized")

        # Construire le prompt selon le rôle
        system_prompt = self._get_claude_system_prompt(request.role)
        user_content = self._format_input(request.input_data)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}]
        )

        return response.content[0].text

    def _get_gpt_system_prompt(self, role: AIRole) -> str:
        """Retourne le prompt système pour GPT selon le rôle"""
        prompts = {
            AIRole.GPT_STRUCTURE: """
Tu es l'Architecte Cognitif d'AZALSCORE.
Ton rôle est de structurer les intentions utilisateur.

Règles:
- Tu analyses et structures, tu ne décides jamais
- Tu ne dialogues jamais directement avec l'utilisateur
- Tu produis une analyse structurée, pas une conclusion

Format de sortie attendu:
{
  "intention_principale": "...",
  "sous_intentions": [...],
  "entités_détectées": [...],
  "actions_suggérées": [...],
  "niveau_complexité": "simple|moyen|complexe",
  "modules_concernés": [...]
}
""",
            AIRole.GPT_DECOMPOSE: """
Tu es l'Architecte Cognitif d'AZALSCORE.
Ton rôle est de décomposer les demandes complexes en sous-tâches.

Règles:
- Décompose sans exécuter
- Identifie les dépendances entre sous-tâches
- Ne prends aucune décision

Format de sortie attendu:
{
  "tâches": [
    {"id": 1, "description": "...", "dépendances": []},
    ...
  ],
  "ordre_exécution": [1, 2, 3],
  "tâches_parallélisables": [[1, 2], [3]]
}
""",
            AIRole.GPT_REFORMULATE: """
Tu es l'Architecte Cognitif d'AZALSCORE.
Ton rôle est de reformuler les demandes de manière neutre et claire.

Règles:
- Reformule sans interpréter
- Reste factuel et neutre
- Ne suggère pas de solutions

Produis une reformulation claire et structurée.
"""
        }
        return prompts.get(role, "Tu es un assistant IA AZALSCORE.")

    def _get_claude_system_prompt(self, role: AIRole) -> str:
        """Retourne le prompt système pour Claude selon le rôle"""
        prompts = {
            AIRole.CLAUDE_REASONING: """
Tu es l'Expert Technique d'AZALSCORE.
Ton rôle est d'effectuer des raisonnements techniques approfondis.

Règles:
- Tu analyses en profondeur
- Tu ne modifies jamais directement le code ou les données
- Tu fournis des analyses détaillées et structurées

Fournis une analyse technique complète.
""",
            AIRole.CLAUDE_DEBUG: """
Tu es l'Expert Technique d'AZALSCORE, spécialisé en débogage.
Ton rôle est de diagnostiquer les problèmes techniques.

Règles:
- Identifie la cause racine
- Propose des solutions sans les appliquer
- Documente clairement le diagnostic

Format de sortie:
{
  "diagnostic": "...",
  "cause_probable": "...",
  "solutions_proposées": [...],
  "priorité": "P0|P1|P2|P3",
  "impact": "..."
}
""",
            AIRole.CLAUDE_CODE_ANALYSIS: """
Tu es l'Expert Technique d'AZALSCORE, spécialisé en analyse de code.
Ton rôle est d'analyser et documenter le code source.

Règles:
- Analyse sans modifier
- Documente clairement
- Identifie les patterns et anti-patterns

Fournis une analyse de code structurée.
""",
            AIRole.CLAUDE_PEDAGOGY: """
Tu es l'Expert Technique d'AZALSCORE, mode pédagogique.
Ton rôle est d'expliquer des concepts techniques.

Règles:
- Explique clairement, pas de jargon inutile
- Utilise des exemples concrets
- Structure tes explications (du simple au complexe)

Fournis une explication pédagogique.
"""
        }
        return prompts.get(role, "Tu es un expert technique AZALSCORE.")

    def _format_input(self, input_data: Dict[str, Any]) -> str:
        """Formate les données d'entrée en texte"""
        if isinstance(input_data, str):
            return input_data

        parts = []
        for key, value in input_data.items():
            parts.append(f"**{key}**: {value}")

        return "\n".join(parts)

    def call_with_validation(
        self,
        session_id: str,
        primary_request: AICallRequest,
        validation_request: AICallRequest
    ) -> Dict[str, Any]:
        """
        Appelle un module avec validation croisée

        Pour les tâches critiques, un second module valide le résultat.

        Args:
            session_id: ID de session
            primary_request: Requête principale
            validation_request: Requête de validation

        Returns:
            Résultat consolidé avec validation
        """
        # Appel principal
        primary_result = self.call(primary_request)

        if not primary_result.success:
            return {
                "success": False,
                "primary_result": primary_result,
                "validation_result": None,
                "consensus": False
            }

        # Appel de validation
        validation_request.input_data["to_validate"] = primary_result.output
        validation_result = self.call(validation_request)

        # Déterminer le consensus
        consensus = validation_result.success and "valid" in str(
            validation_result.output
        ).lower()

        # Si pas de consensus, escalade humaine
        if not consensus:
            self.guardian.alert_cockpit(
                session_id=session_id,
                alert_type="validation_divergence",
                message="Divergence détectée entre modules IA, validation humaine requise",
                severity=self.guardian.ThreatLevel.MEDIUM,
                details={
                    "primary_module": primary_request.module.value,
                    "validation_module": validation_request.module.value,
                    "primary_output": str(primary_result.output)[:200],
                    "validation_output": str(validation_result.output)[:200]
                }
            )

        return {
            "success": primary_result.success and validation_result.success,
            "primary_result": primary_result,
            "validation_result": validation_result,
            "consensus": consensus,
            "requires_human_validation": not consensus
        }

    def escalate_to_human(
        self,
        session_id: str,
        reason: str,
        context: Dict[str, Any]
    ):
        """
        Escalade une décision vers un humain

        Conformité: Toute décision finale est humaine.

        Args:
            session_id: ID de session
            reason: Raison de l'escalade
            context: Contexte complet
        """
        self.guardian.alert_cockpit(
            session_id=session_id,
            alert_type="human_escalation",
            message=f"Escalade humaine requise: {reason}",
            severity=self.guardian.ThreatLevel.MEDIUM,
            details=context
        )

        self.audit.log_event(
            self.audit.log_event.__self__.__class__(
                event_type=AuditEventType.SYSTEM_ESCALATION,
                session_id=session_id,
                source_module="orchestrator",
                action="escalate",
                output_data={"reason": reason, "context": context},
                success=True
            )
        )


# Instance singleton
_orchestrator_instance: Optional[AIOrchestrator] = None


def get_ai_orchestrator() -> AIOrchestrator:
    """Récupère l'instance singleton de l'orchestrateur"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AIOrchestrator()
    return _orchestrator_instance
