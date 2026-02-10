"""
AZALS MODULE - Marceau Orchestrator
=====================================

Orchestrateur central de l'agent Marceau.
Gere le routage des requetes, la detection d'intention et la coordination des modules.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from .config import (
    MARCEAU_SYSTEM_PROMPT,
    get_or_create_marceau_config,
    is_module_enabled,
    requires_validation,
)
from .memory import MarceauMemoryService
from .models import (
    ActionStatus,
    MarceauAction,
    MarceauConfig,
    MemoryType,
    ModuleName,
)

logger = logging.getLogger(__name__)


# ============================================================================
# LLM CLIENT (LAZY INITIALIZATION)
# ============================================================================

_llm_client = None


def get_llm_client():
    """
    Initialise et retourne le client LLM.
    Support llama.cpp, Ollama, ou API compatible OpenAI.
    """
    global _llm_client

    if _llm_client is None:
        try:
            # Essayer d'utiliser Ollama en local
            import httpx

            _llm_client = OllamaClient()
            logger.info("[MARCEAU] Client LLM Ollama initialise")
        except Exception as e:
            logger.warning(f"[MARCEAU] LLM non disponible: {e}")
            _llm_client = MockLLMClient()

    return _llm_client


class OllamaClient:
    """Client pour Ollama (LLM local)."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def generate(
        self,
        prompt: str,
        model: str = "llama3:8b-instruct-q4_0",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """Genere une reponse via Ollama."""
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")


class MockLLMClient:
    """Client LLM de fallback pour tests."""

    async def generate(
        self,
        prompt: str,
        model: str = "mock",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """Retourne une reponse mock."""
        logger.warning("[MARCEAU] Utilisation du LLM mock - pas de vrai traitement")
        return json.dumps({
            "module": "telephonie",
            "action": "unknown",
            "confidence": 0.5,
            "reasoning": "LLM non disponible - mode degrade"
        })


# ============================================================================
# ORCHESTRATEUR
# ============================================================================

class MarceauOrchestrator:
    """
    Orchestrateur central de Marceau.
    Coordonne les modules, detecte les intentions et gere le contexte.
    """

    def __init__(self, tenant_id: str, db: Session):
        """
        Initialise l'orchestrateur.

        Args:
            tenant_id: ID du tenant
            db: Session SQLAlchemy
        """
        self.tenant_id = tenant_id
        self.db = db
        self.config: MarceauConfig | None = None
        self.memory = MarceauMemoryService(tenant_id, db)
        self.services: dict[str, Any] = {}

    async def initialize(self):
        """Initialise l'orchestrateur et charge la configuration."""
        self.config = get_or_create_marceau_config(self.tenant_id, self.db)
        await self._load_services()
        logger.info(f"[MARCEAU] Orchestrateur initialise pour tenant {self.tenant_id}")

    async def _load_services(self):
        """Charge les services des modules actives."""
        service_imports = {
            "telephonie": ("app.modules.marceau.modules.telephonie.service", "TelephonyService"),
            "commercial": ("app.modules.marceau.modules.commercial.service", "CommercialService"),
            "marketing": ("app.modules.marceau.modules.marketing.service", "MarketingService"),
            "seo": ("app.modules.marceau.modules.seo.service", "SEOService"),
            "support": ("app.modules.marceau.modules.support.service", "SupportService"),
            "orchestration": ("app.modules.marceau.modules.orchestration.service", "OrchestrationService"),
        }

        for module_name, (module_path, class_name) in service_imports.items():
            if is_module_enabled(self.config, module_name):
                try:
                    # Import dynamique pour eviter erreurs si module non implemente
                    import importlib
                    module = importlib.import_module(module_path)
                    service_class = getattr(module, class_name)
                    self.services[module_name] = service_class(self.tenant_id, self.db)
                    logger.debug(f"[MARCEAU] Service {module_name} charge")
                except ImportError as e:
                    logger.warning(f"[MARCEAU] Module {module_name} non disponible: {e}")
                except Exception as e:
                    logger.error(f"[MARCEAU] Erreur chargement service {module_name}: {e}")

    async def handle_request(self, request: dict) -> dict:
        """
        Point d'entree principal pour traiter une requete.
        Utilise RAG pour enrichir le contexte avant traitement.

        Args:
            request: Requete a traiter (message, context, etc.)

        Returns:
            Resultat du traitement
        """
        start_time = time.time()

        try:
            # 1. Recuperer contexte pertinent via RAG
            message = request.get("message", "")
            context = await self.memory.retrieve_relevant_context(
                query=message,
                limit=10,
                memory_types=[MemoryType.KNOWLEDGE, MemoryType.LEARNING, MemoryType.DECISION]
            )

            # 2. Detecter l'intention avec contexte enrichi
            intent = await self.detect_intent(message, context)

            # 3. Verifier si le module est active
            module = intent.get("module", "telephonie")
            if not is_module_enabled(self.config, module):
                return {
                    "error": f"Module {module} non active",
                    "success": False,
                    "suggestion": "Activez ce module dans Administration > Marceau"
                }

            # 4. Executer l'action
            service = self.services.get(module)
            if not service:
                return {
                    "error": f"Service {module} non disponible",
                    "success": False
                }

            result = await service.execute_action(
                action=intent.get("action", "unknown"),
                data=request,
                context=context
            )

            # 5. Verifier si validation humaine requise
            confidence = intent.get("confidence", 1.0)
            if requires_validation(self.config, module, confidence):
                result["requires_validation"] = True
                action = await self._create_pending_action(
                    module=module,
                    action_type=intent.get("action", "unknown"),
                    input_data=request,
                    output_data=result,
                    confidence=confidence
                )
                result["action_id"] = str(action.id)
                result["message"] = "Action en attente de validation"

            # 6. Stocker en memoire si succes
            if result.get("success", True):
                await self.memory.store_memory(
                    content=f"Action {intent.get('action')}: {json.dumps(result, default=str)[:500]}",
                    memory_type=MemoryType.DECISION,
                    tags=[module, intent.get("action", "unknown")],
                    importance_score=confidence,
                )

            duration = time.time() - start_time
            result["duration_seconds"] = duration

            return result

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur traitement requete: {e}")
            return {
                "error": str(e),
                "success": False,
                "duration_seconds": time.time() - start_time
            }

    async def detect_intent(self, message: str, context: list[str]) -> dict:
        """
        Detecte l'intention d'un message avec contexte RAG.

        Args:
            message: Message de l'utilisateur
            context: Contexte recupere par RAG

        Returns:
            Dict avec module, action, confidence, reasoning
        """
        if not message.strip():
            return {
                "module": "telephonie",
                "action": "unknown",
                "confidence": 0.0,
                "reasoning": "Message vide"
            }

        # Construire le prompt avec contexte
        context_str = "\n\n".join([f"[Connaissance {i+1}]: {c}" for i, c in enumerate(context)])

        intent_prompt = f"""
{MARCEAU_SYSTEM_PROMPT}

CONTEXTE PERTINENT (base de connaissances):
{context_str if context else "Aucun contexte specifique"}

MESSAGE DE L'UTILISATEUR:
{message}

En utilisant ton role et le contexte, determine:
1. Le module concerne (telephonie, commercial, marketing, seo, support, etc.)
2. L'action precise a effectuer
3. Ton niveau de confiance (0-1)

Reponds UNIQUEMENT au format JSON valide:
{{
    "module": "nom_module",
    "action": "nom_action",
    "confidence": 0.95,
    "reasoning": "Breve explication"
}}
"""

        try:
            llm = get_llm_client()
            model = self.config.llm_model if self.config else "llama3:8b-instruct-q4_0"
            temperature = self.config.llm_temperature if self.config else 0.2

            response = await llm.generate(
                prompt=intent_prompt,
                model=model,
                temperature=temperature,
                max_tokens=256
            )

            # Parser la reponse JSON
            intent = self._parse_intent_response(response)
            return intent

        except Exception as e:
            logger.error(f"[MARCEAU] Erreur detection intention: {e}")
            return {
                "module": "telephonie",
                "action": "unknown",
                "confidence": 0.3,
                "reasoning": f"Erreur LLM: {str(e)}"
            }

    def _parse_intent_response(self, response: str) -> dict:
        """Parse la reponse JSON du LLM."""
        try:
            # Chercher le JSON dans la reponse
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                intent = json.loads(json_str)

                # Valider les champs
                return {
                    "module": intent.get("module", "telephonie"),
                    "action": intent.get("action", "unknown"),
                    "confidence": float(intent.get("confidence", 0.5)),
                    "reasoning": intent.get("reasoning", "")
                }
        except json.JSONDecodeError:
            pass

        # Fallback si parsing echoue
        return {
            "module": "telephonie",
            "action": "unknown",
            "confidence": 0.3,
            "reasoning": "Erreur parsing reponse LLM"
        }

    async def _create_pending_action(
        self,
        module: str,
        action_type: str,
        input_data: dict,
        output_data: dict,
        confidence: float
    ) -> MarceauAction:
        """Cree une action en attente de validation."""
        action = MarceauAction(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            module=ModuleName(module),
            action_type=action_type,
            status=ActionStatus.NEEDS_VALIDATION,
            input_data=input_data,
            output_data=output_data,
            confidence_score=confidence,
            required_human_validation=True,
        )

        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)

        logger.info(f"[MARCEAU] Action {action.id} creee en attente de validation")
        return action

    async def validate_action(
        self,
        action_id: uuid.UUID,
        approved: bool,
        validated_by: uuid.UUID,
        notes: str | None = None
    ) -> MarceauAction | None:
        """
        Valide ou rejette une action en attente.

        Args:
            action_id: ID de l'action
            approved: True pour approuver, False pour rejeter
            validated_by: ID de l'utilisateur qui valide
            notes: Notes optionnelles

        Returns:
            Action mise a jour ou None
        """
        action = self.db.query(MarceauAction).filter(
            MarceauAction.id == action_id,
            MarceauAction.tenant_id == self.tenant_id,
            MarceauAction.status == ActionStatus.NEEDS_VALIDATION
        ).first()

        if not action:
            return None

        action.validated_by = validated_by
        action.validated_at = datetime.utcnow()
        action.validation_notes = notes

        if approved:
            action.status = ActionStatus.VALIDATED
            # Executer l'action validee
            await self._execute_validated_action(action)
        else:
            action.status = ActionStatus.REJECTED

        self.db.commit()
        self.db.refresh(action)

        # Stocker feedback pour apprentissage
        await self.memory.store_memory(
            content=f"Action {action.action_type} {'approuvee' if approved else 'rejetee'}: {notes or 'pas de notes'}",
            memory_type=MemoryType.LEARNING,
            tags=[action.module.value, "validation", "approved" if approved else "rejected"],
            importance_score=0.8 if not approved else 0.5,  # Les rejets sont plus importants a retenir
        )

        return action

    async def _execute_validated_action(self, action: MarceauAction):
        """Execute une action apres validation."""
        module = action.module.value
        service = self.services.get(module)

        if not service:
            action.status = ActionStatus.FAILED
            action.error_message = f"Service {module} non disponible"
            return

        try:
            result = await service.execute_action(
                action=action.action_type,
                data=action.input_data,
                context=[]
            )

            action.output_data = result
            action.status = ActionStatus.COMPLETED

        except Exception as e:
            action.status = ActionStatus.FAILED
            action.error_message = str(e)
            logger.error(f"[MARCEAU] Erreur execution action validee {action.id}: {e}")

    async def chat(self, message: str, conversation_id: uuid.UUID | None = None) -> dict:
        """
        Interface de chat avec Marceau.

        Args:
            message: Message utilisateur
            conversation_id: ID conversation existante (optionnel)

        Returns:
            Reponse du chat
        """
        # Recuperer contexte
        context = await self.memory.retrieve_relevant_context(
            query=message,
            limit=5
        )

        # Generer reponse
        chat_prompt = f"""
{MARCEAU_SYSTEM_PROMPT}

CONTEXTE:
{chr(10).join(context) if context else 'Aucun contexte'}

UTILISATEUR: {message}

Reponds de maniere professionnelle et concise. Si une action est necessaire, indique-la clairement.

MARCEAU:"""

        try:
            llm = get_llm_client()
            response = await llm.generate(
                prompt=chat_prompt,
                model=self.config.llm_model if self.config else "llama3:8b-instruct-q4_0",
                temperature=0.7,  # Plus de creativite pour le chat
                max_tokens=512
            )

            # Detecter si une action est necessaire
            intent = await self.detect_intent(message, context)

            return {
                "message": response.strip(),
                "conversation_id": conversation_id or uuid.uuid4(),
                "intent": intent.get("action"),
                "actions_taken": [],
                "suggestions": [],
                "confidence": intent.get("confidence", 1.0)
            }

        except Exception as e:
            logger.error(f"[MARCEAU] Erreur chat: {e}")
            return {
                "message": "Desole, je rencontre une difficulte technique. Pouvez-vous reformuler votre demande?",
                "conversation_id": conversation_id or uuid.uuid4(),
                "intent": None,
                "actions_taken": [],
                "suggestions": ["Reformuler la demande", "Contacter le support"],
                "confidence": 0.0
            }

    async def get_dashboard_data(self) -> dict:
        """
        Recupere les donnees pour le dashboard Marceau.

        Returns:
            Donnees du dashboard
        """
        from sqlalchemy import func
        from datetime import date, timedelta

        today = date.today()
        yesterday = today - timedelta(days=1)

        # Actions aujourd'hui
        actions_today = self.db.query(func.count(MarceauAction.id)).filter(
            MarceauAction.tenant_id == self.tenant_id,
            func.date(MarceauAction.created_at) == today
        ).scalar() or 0

        actions_yesterday = self.db.query(func.count(MarceauAction.id)).filter(
            MarceauAction.tenant_id == self.tenant_id,
            func.date(MarceauAction.created_at) == yesterday
        ).scalar() or 0

        # Actions en attente de validation
        pending = self.db.query(func.count(MarceauAction.id)).filter(
            MarceauAction.tenant_id == self.tenant_id,
            MarceauAction.status == ActionStatus.NEEDS_VALIDATION
        ).scalar() or 0

        # Actions par module
        by_module = self.db.query(
            MarceauAction.module,
            func.count(MarceauAction.id)
        ).filter(
            MarceauAction.tenant_id == self.tenant_id,
            func.date(MarceauAction.created_at) == today
        ).group_by(MarceauAction.module).all()

        # Dernières actions
        recent = self.db.query(MarceauAction).filter(
            MarceauAction.tenant_id == self.tenant_id
        ).order_by(MarceauAction.created_at.desc()).limit(20).all()

        # Confiance moyenne
        avg_confidence = self.db.query(func.avg(MarceauAction.confidence_score)).filter(
            MarceauAction.tenant_id == self.tenant_id,
            func.date(MarceauAction.created_at) == today
        ).scalar()

        # Tendance
        trend = ((actions_today - actions_yesterday) / max(actions_yesterday, 1)) * 100

        return {
            "total_actions_today": actions_today,
            "total_conversations_today": 0,  # A implementer
            "total_quotes_today": 0,
            "total_appointments_today": 0,
            "actions_trend": trend,
            "conversations_trend": 0,
            "quotes_trend": 0,
            "appointments_trend": 0,
            "actions_by_module": {str(m): c for m, c in by_module},
            "pending_validations": pending,
            "recent_actions": recent,
            "alerts": [],
            "avg_confidence_score": float(avg_confidence) if avg_confidence else 1.0,
            "avg_response_time_seconds": 0,
            "tokens_used_today": 0,
        }
