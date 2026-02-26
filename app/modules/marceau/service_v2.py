"""
AZALS - Marceau Service (v2 - CRUDRouter Compatible)
=====================================================

Service compatible avec BaseService et CRUDRouter.
Agent IA Marceau - Assistant telephonique intelligent.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.core.saas_context import Result, SaaSContext

from app.modules.marceau.models import (
    MarceauConfig,
    MarceauAction,
    MarceauMemory,
    MarceauConversation,
    MarceauKnowledgeDocument,
    MarceauFeedback,
    MarceauScheduledTask,
)
from app.modules.marceau.schemas import (
    MarceauConfigCreate,
    MarceauConfigUpdate,
    MarceauConfigResponse,
    MarceauActionCreate,
    MarceauActionResponse,
)

logger = logging.getLogger(__name__)


class MarceauConfigService(BaseService[MarceauConfig, Any, Any]):
    """Service CRUD pour la configuration Marceau."""

    model = MarceauConfig

    def get_or_create_config(self) -> MarceauConfig:
        """Recupere ou cree la configuration du tenant."""
        config = (
            self.db.query(MarceauConfig)
            .filter(MarceauConfig.tenant_id == self.tenant_id)
            .first()
        )
        if not config:
            config = MarceauConfig(
                tenant_id=self.tenant_id,
                enabled_modules={
                    "telephony": True,
                    "appointment": True,
                    "quote": True,
                    "crm": True,
                    "knowledge": True,
                },
                autonomy_levels={
                    "telephony": 3,
                    "appointment": 2,
                    "quote": 1,
                    "crm": 2,
                    "knowledge": 3,
                }
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        return config


class MarceauActionService(BaseService[MarceauAction, Any, Any]):
    """Service CRUD pour les actions Marceau."""

    model = MarceauAction

    def list_pending_validation(self) -> List[MarceauAction]:
        """Liste les actions en attente de validation humaine."""
        from app.modules.marceau.models import ActionStatus
        return (
            self.db.query(MarceauAction)
            .filter(
                MarceauAction.tenant_id == self.tenant_id,
                MarceauAction.status == ActionStatus.NEEDS_VALIDATION,
            )
            .order_by(MarceauAction.created_at.desc())
            .all()
        )

    def validate_action(self, action_id: UUID, approved: bool, validator_id: UUID, notes: str = None) -> Result[MarceauAction]:
        """Valide ou rejette une action."""
        result = self.get_or_fail(action_id)
        if not result.success:
            return result

        action = result.data
        from app.modules.marceau.models import ActionStatus
        action.status = ActionStatus.VALIDATED if approved else ActionStatus.REJECTED
        action.validated_by = validator_id
        action.validated_at = datetime.utcnow()
        if notes:
            action.validation_notes = notes

        self.db.commit()
        self.db.refresh(action)
        return Result.ok(action)


class MarceauConversationService(BaseService[MarceauConversation, Any, Any]):
    """Service CRUD pour les conversations Marceau."""

    model = MarceauConversation

    def list_recent(self, limit: int = 50) -> List[MarceauConversation]:
        """Liste les conversations recentes."""
        return (
            self.db.query(MarceauConversation)
            .filter(MarceauConversation.tenant_id == self.tenant_id)
            .order_by(MarceauConversation.started_at.desc())
            .limit(limit)
            .all()
        )

    def get_stats(self) -> Dict[str, Any]:
        """Calcule les statistiques des conversations."""
        from sqlalchemy import func

        conversations = (
            self.db.query(MarceauConversation)
            .filter(MarceauConversation.tenant_id == self.tenant_id)
            .all()
        )

        total = len(conversations)
        if total == 0:
            return {
                "total_conversations": 0,
                "avg_duration_seconds": 0,
                "avg_satisfaction_score": None,
                "outcomes_distribution": {},
                "intents_distribution": {},
            }

        durations = [c.duration_seconds for c in conversations if c.duration_seconds]
        scores = [c.satisfaction_score for c in conversations if c.satisfaction_score]

        outcomes = {}
        intents = {}
        for c in conversations:
            if c.outcome:
                outcomes[c.outcome] = outcomes.get(c.outcome, 0) + 1
            if c.intent:
                intents[c.intent] = intents.get(c.intent, 0) + 1

        return {
            "total_conversations": total,
            "avg_duration_seconds": sum(durations) / len(durations) if durations else 0,
            "avg_satisfaction_score": sum(scores) / len(scores) if scores else None,
            "outcomes_distribution": outcomes,
            "intents_distribution": intents,
        }


class MarceauKnowledgeService(BaseService[MarceauKnowledgeDocument, Any, Any]):
    """Service CRUD pour les documents de connaissance Marceau."""

    model = MarceauKnowledgeDocument

    def search(self, query: str, limit: int = 10) -> List[MarceauKnowledgeDocument]:
        """Recherche dans les documents de connaissance."""
        return (
            self.db.query(MarceauKnowledgeDocument)
            .filter(
                MarceauKnowledgeDocument.tenant_id == self.tenant_id,
                MarceauKnowledgeDocument.is_active == True,
                MarceauKnowledgeDocument.content.ilike(f"%{query}%"),
            )
            .limit(limit)
            .all()
        )


class MarceauScheduledTaskService(BaseService[MarceauScheduledTask, Any, Any]):
    """Service CRUD pour les taches planifiees Marceau."""

    model = MarceauScheduledTask

    def list_active(self) -> List[MarceauScheduledTask]:
        """Liste les taches planifiees actives."""
        return (
            self.db.query(MarceauScheduledTask)
            .filter(
                MarceauScheduledTask.tenant_id == self.tenant_id,
                MarceauScheduledTask.is_active == True,
            )
            .order_by(MarceauScheduledTask.next_run_at)
            .all()
        )
