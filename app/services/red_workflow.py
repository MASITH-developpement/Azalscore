"""
AZALS - Service de validation workflow RED
Gestion stricte du workflow de validation DIRIGEANT pour décisions RED
"""

import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.models import (
    CoreAuditJournal,
    Decision,
    DecisionLevel,
    RedDecisionReport,
    RedDecisionWorkflow,
    RedWorkflowStep,
    TreasuryForecast,
    User,
    UserRole,
)


class RedWorkflowService:
    """
    Service de gestion du workflow de validation RED.
    Assure l'ordre strict des étapes et la traçabilité complète.
    """

    STEP_ORDER = [
        RedWorkflowStep.ACKNOWLEDGE,
        RedWorkflowStep.COMPLETENESS,
        RedWorkflowStep.FINAL
    ]

    def __init__(self, db: Session):
        self.db = db

    def _verify_dirigeant(self, user_id: int, tenant_id: str) -> None:
        """Vérifie que l'utilisateur est DIRIGEANT."""
        user = self.db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id
        ).first()

        if not user or user.role != UserRole.DIRIGEANT:
            raise HTTPException(
                status_code=403,
                detail="FORBIDDEN: Only DIRIGEANT role can validate RED decisions"
            )

    def _verify_red_decision(self, decision_id: int, tenant_id: str) -> Decision:
        """Vérifie que la décision existe et est RED."""
        decision = self.db.query(Decision).filter(
            Decision.id == decision_id,
            Decision.tenant_id == tenant_id
        ).first()

        if not decision:
            raise HTTPException(
                status_code=404,
                detail="Decision not found"
            )

        if decision.level != DecisionLevel.RED:
            raise HTTPException(
                status_code=400,
                detail="INVALID: Only RED decisions require validation workflow"
            )

        return decision

    def _get_completed_steps(self, decision_id: int) -> list[RedWorkflowStep]:
        """Récupère les étapes déjà validées pour une décision."""
        workflows = self.db.query(RedDecisionWorkflow).filter(
            RedDecisionWorkflow.decision_id == decision_id
        ).order_by(RedDecisionWorkflow.confirmed_at).all()

        return [w.step for w in workflows]

    def _verify_step_order(self, decision_id: int, step: RedWorkflowStep) -> None:
        """Vérifie que l'étape demandée respecte l'ordre strict."""
        completed = self._get_completed_steps(decision_id)

        # Vérifier si l'étape a déjà été validée
        if step in completed:
            raise HTTPException(
                status_code=409,
                detail=f"DUPLICATE: Step {step.value} already completed"
            )

        # Vérifier l'ordre des étapes
        step_index = self.STEP_ORDER.index(step)

        # Toutes les étapes précédentes doivent être complètes
        for i in range(step_index):
            if self.STEP_ORDER[i] not in completed:
                raise HTTPException(
                    status_code=400,
                    detail=f"INVALID_ORDER: Step {self.STEP_ORDER[i].value} must be completed first"
                )

    def _create_journal_entry(
        self,
        tenant_id: str,
        user_id: int,
        decision_id: int,
        step: RedWorkflowStep
    ) -> None:
        """Enregistre la validation dans le journal append-only."""
        entry = CoreAuditJournal(
            tenant_id=tenant_id,
            user_id=user_id,
            action=f"RED_WORKFLOW_{step.value}",
            details=f"Decision ID: {decision_id}, Step: {step.value}"
        )
        self.db.add(entry)

    def _generate_red_report(
        self,
        decision: Decision,
        user_id: int,
        tenant_id: str,
        validated_at: datetime
    ) -> RedDecisionReport:
        """
        Génère un rapport RED IMMUTABLE lors de la validation finale.

        Le rapport contient :
        - Snapshot des données décisionnelles
        - Identité du validateur
        - Références aux entrées journal
        - Données déclenchantes (ex: trésorerie négative)

        Règle : Un rapport par décision RED, créé UNIQUEMENT à la validation finale.
        """
        # Récupérer les entrées journal liées à cette décision
        journal_entries = self.db.query(CoreAuditJournal).filter(
            CoreAuditJournal.tenant_id == tenant_id,
            CoreAuditJournal.details.like(f"%Decision ID: {decision.id}%")
        ).all()

        journal_refs = [str(entry.id) for entry in journal_entries]

        # Récupérer les données déclenchantes si disponibles
        trigger_data = {
            "entity_type": decision.entity_type,
            "entity_id": decision.entity_id,
            "reason": decision.reason
        }

        # Si décision liée à trésorerie, inclure snapshot
        if decision.entity_type == "treasury_forecast":
            forecast = self.db.query(TreasuryForecast).filter(
                TreasuryForecast.id == int(decision.entity_id),
                TreasuryForecast.tenant_id == tenant_id
            ).first()

            if forecast:
                trigger_data["treasury_snapshot"] = {
                    "opening_balance": forecast.opening_balance,
                    "inflows": forecast.inflows,
                    "outflows": forecast.outflows,
                    "forecast_balance": forecast.forecast_balance,
                    "created_at": forecast.created_at.isoformat()
                }

        # Créer le rapport IMMUTABLE
        report = RedDecisionReport(
            tenant_id=tenant_id,
            decision_id=decision.id,
            decision_reason=decision.reason,
            trigger_data=json.dumps(trigger_data, ensure_ascii=False),
            validated_at=validated_at,
            validator_id=user_id,
            journal_references=json.dumps(journal_refs)
        )

        self.db.add(report)

        # Journaliser la création du rapport
        report_journal = CoreAuditJournal(
            tenant_id=tenant_id,
            user_id=user_id,
            action="RED_REPORT_GENERATED",
            details=f"Decision ID: {decision.id}, Report immutable created"
        )
        self.db.add(report_journal)

        return report

    def validate_step(
        self,
        decision_id: int,
        step: RedWorkflowStep,
        user_id: int,
        tenant_id: str
    ) -> RedDecisionWorkflow:
        """
        Valide une étape du workflow RED.

        Vérifie :
        - Utilisateur est DIRIGEANT
        - Décision existe et est RED
        - Étape pas déjà validée
        - Étapes précédentes complètes

        Crée :
        - Enregistrement workflow
        - Entrée journal
        """
        # Vérifications
        self._verify_dirigeant(user_id, tenant_id)
        self._verify_red_decision(decision_id, tenant_id)
        self._verify_step_order(decision_id, step)

        # Récupérer la décision pour le rapport
        decision = self._verify_red_decision(decision_id, tenant_id)

        # Création de l'enregistrement workflow
        workflow = RedDecisionWorkflow(
            tenant_id=tenant_id,
            decision_id=decision_id,
            step=step,
            user_id=user_id
        )
        self.db.add(workflow)

        # Journalisation
        self._create_journal_entry(tenant_id, user_id, decision_id, step)

        # Génération du rapport IMMUTABLE si étape FINAL
        if step == RedWorkflowStep.FINAL:
            self._generate_red_report(
                decision=decision,
                user_id=user_id,
                tenant_id=tenant_id,
                validated_at=datetime.utcnow()
            )
            # Marquer la décision comme entièrement validée
            decision.is_fully_validated = 1

        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    def get_workflow_status(self, decision_id: int, tenant_id: str) -> dict:
        """Retourne l'état du workflow pour une décision RED."""
        decision = self._verify_red_decision(decision_id, tenant_id)
        completed = self._get_completed_steps(decision_id)

        is_fully_validated = all(step in completed for step in self.STEP_ORDER)

        return {
            "decision_id": decision_id,
            "level": decision.level.value,
            "completed_steps": [s.value for s in completed],
            "pending_steps": [s.value for s in self.STEP_ORDER if s not in completed],
            "is_fully_validated": is_fully_validated
        }

    def get_red_report(self, decision_id: int, tenant_id: str) -> RedDecisionReport:
        """
        Récupère le rapport RED IMMUTABLE pour une décision.

        Règles :
        - Rapport accessible uniquement après validation complète (step FINAL)
        - Isolation stricte par tenant
        - Rapport en lecture seule
        """
        # Vérifier que la décision existe et est RED
        self._verify_red_decision(decision_id, tenant_id)

        # Vérifier que le workflow est complet
        status = self.get_workflow_status(decision_id, tenant_id)
        if not status["is_fully_validated"]:
            raise HTTPException(
                status_code=403,
                detail="FORBIDDEN: Report only accessible after complete validation (FINAL step)"
            )

        # Récupérer le rapport
        report = self.db.query(RedDecisionReport).filter(
            RedDecisionReport.decision_id == decision_id,
            RedDecisionReport.tenant_id == tenant_id
        ).first()

        if not report:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )

        return report
