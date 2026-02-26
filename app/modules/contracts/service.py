"""
AZALS MODULE CONTRACTS - Service
=================================

Service de gestion des contrats (CLM - Contract Lifecycle Management).
Logique metier complete integrant les meilleures pratiques de:
Sage, Odoo, Microsoft Dynamics 365, Axonaut, Pennylane.

Fonctionnalites:
- CRUD contrats client/fournisseur
- Types de contrats configurables
- Lignes avec facturation recurrente
- Avenants et modifications
- Renouvellements automatiques
- Workflow de validation multi-niveaux
- Alertes et echeances
- Dashboard et rapports
"""
from __future__ import annotations

import logging
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import uuid as uuid_lib

from sqlalchemy.orm import Session

from .models import (
    Contract, ContractParty, ContractLine, ContractClause,
    ContractObligation, ContractMilestone, ContractAmendment,
    ContractRenewal, ContractDocument, ContractAlert,
    ContractApproval, ContractHistory, ContractCategory,
    ContractTemplate, ClauseTemplate, ContractMetrics,
    ContractStatus, ContractType, PartyRole, RenewalType,
    BillingFrequency, AmendmentType, ObligationType,
    ObligationStatus, AlertType, AlertPriority, ApprovalStatus
)
from .repository import (
    ContractRepository, ContractPartyRepository, ContractLineRepository,
    ContractObligationRepository, ContractMilestoneRepository,
    ContractAmendmentRepository, ContractAlertRepository,
    ContractApprovalRepository, ContractCategoryRepository,
    ContractTemplateRepository, ContractMetricsRepository
)
from .schemas import (
    ContractCreate, ContractUpdate, ContractResponse, ContractSummaryResponse,
    ContractFilters, ContractListResponse, ContractStatsResponse,
    ContractDashboardResponse, ContractPartyCreate, ContractPartyUpdate,
    ContractLineCreate, ContractLineUpdate, ContractClauseCreate,
    ContractObligationCreate, ContractObligationUpdate,
    ContractMilestoneCreate, ContractMilestoneUpdate,
    ContractAmendmentCreate, ContractAmendmentUpdate,
    ContractAlertCreate, ContractAlertUpdate,
    ContractCategoryCreate, ContractCategoryUpdate,
    ContractTemplateCreate, ContractTemplateUpdate,
    ContractSubmitForApprovalRequest, ContractTerminateRequest,
    ContractRenewRequest, ApprovalDecisionRequest
)
from .exceptions import (
    ContractNotFoundError, ContractDuplicateError, ContractValidationError,
    ContractStateError, ContractNotEditableError, ContractExpiredError,
    PartyNotFoundError, PartyAlreadySignedError, MissingPartyError,
    ContractLineNotFoundError, ObligationNotFoundError,
    MilestoneNotFoundError, MilestoneDependencyError,
    AmendmentNotFoundError, AmendmentNotAllowedError,
    RenewalNotAllowedError, MaxRenewalsReachedError,
    ApprovalNotFoundError, ApprovalNotAuthorizedError,
    ApprovalAlreadyProcessedError, ApprovalRequiredError,
    TemplateNotFoundError, CategoryNotFoundError,
    AlertNotFoundError, ContractVersionConflictError
)


class ContractService:
    """
    Service principal de gestion des contrats.

    Gere le cycle de vie complet des contrats:
    - Creation a partir de templates ou from scratch
    - Workflow d'approbation multi-niveaux
    - Signature electronique
    - Suivi des obligations et jalons
    - Renouvellements automatiques/manuels
    - Avenants et modifications
    - Alertes et notifications
    - Reporting et analytics
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        # Repositories
        self.contracts = ContractRepository(db, UUID(tenant_id))
        self.parties = ContractPartyRepository(db, UUID(tenant_id))
        self.lines = ContractLineRepository(db, UUID(tenant_id))
        self.obligations = ContractObligationRepository(db, UUID(tenant_id))
        self.milestones = ContractMilestoneRepository(db, UUID(tenant_id))
        self.amendments = ContractAmendmentRepository(db, UUID(tenant_id))
        self.alerts = ContractAlertRepository(db, UUID(tenant_id))
        self.approvals = ContractApprovalRepository(db, UUID(tenant_id))
        self.categories = ContractCategoryRepository(db, UUID(tenant_id))
        self.templates = ContractTemplateRepository(db, UUID(tenant_id))
        self.metrics = ContractMetricsRepository(db, UUID(tenant_id))

    # ========================================================================
    # CONTRACTS - CRUD
    # ========================================================================

    def create_contract(
        self,
        data: ContractCreate,
        created_by: UUID = None
    ) -> Contract:
        """Creer un nouveau contrat."""
        contract_data = data.model_dump(exclude_unset=True)

        # Verifier si numero existe deja
        if contract_data.get("contract_number"):
            if self.contracts.number_exists(contract_data["contract_number"]):
                raise ContractDuplicateError(contract_data["contract_number"])

        # Appliquer template si specifie
        if data.template_id:
            template = self.templates.get_by_id(data.template_id)
            if template:
                contract_data = self._apply_template(contract_data, template)

        contract = self.contracts.create(contract_data, created_by)

        # Creer alertes automatiques si dates definies
        self._create_automatic_alerts(contract, created_by)

        return contract

    def get_contract(
        self,
        contract_id: UUID,
        with_relations: bool = True
    ) -> Contract:
        """Recuperer un contrat par ID."""
        contract = self.contracts.get_by_id(contract_id, with_relations)
        if not contract:
            raise ContractNotFoundError(str(contract_id))
        return contract

    def get_contract_by_number(self, contract_number: str) -> Contract:
        """Recuperer un contrat par numero."""
        contract = self.contracts.get_by_number(contract_number)
        if not contract:
            raise ContractNotFoundError(message=f"Contrat {contract_number} non trouve")
        return contract

    def update_contract(
        self,
        contract_id: UUID,
        data: ContractUpdate,
        updated_by: UUID = None,
        expected_version: int = None
    ) -> Contract:
        """Mettre a jour un contrat."""
        contract = self.get_contract(contract_id, with_relations=False)

        # Verifier que le contrat est modifiable
        if contract.status not in [
            ContractStatus.DRAFT.value,
            ContractStatus.IN_REVIEW.value,
            ContractStatus.IN_NEGOTIATION.value
        ]:
            raise ContractNotEditableError(contract.status)

        # Optimistic locking
        if expected_version is not None and contract.version != expected_version:
            raise ContractVersionConflictError(expected_version, contract.version)

        update_data = data.model_dump(exclude_unset=True)
        contract = self.contracts.update(contract, update_data, updated_by)

        # Mettre a jour les alertes si dates changent
        if "end_date" in update_data or "renewal_notice_days" in update_data:
            self._update_automatic_alerts(contract, updated_by)

        return contract

    def delete_contract(
        self,
        contract_id: UUID,
        deleted_by: UUID = None
    ) -> bool:
        """Supprimer un contrat (soft delete)."""
        contract = self.get_contract(contract_id, with_relations=False)

        # Seuls les brouillons peuvent etre supprimes
        if contract.status not in [
            ContractStatus.DRAFT.value,
            ContractStatus.CANCELLED.value
        ]:
            raise ContractNotEditableError(
                contract.status,
                "Seuls les brouillons ou contrats annules peuvent etre supprimes"
            )

        return self.contracts.soft_delete(contract, deleted_by)

    def list_contracts(
        self,
        filters: ContractFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Contract], int]:
        """Lister les contrats avec filtres."""
        return self.contracts.list(filters, page, page_size, sort_by, sort_dir)

    def search_contracts(self, query: str, limit: int = 10) -> List[Contract]:
        """Recherche rapide de contrats."""
        return self.contracts.search_contracts(query, limit)

    # ========================================================================
    # WORKFLOW - Statuts
    # ========================================================================

    def submit_for_review(
        self,
        contract_id: UUID,
        submitted_by: UUID
    ) -> Contract:
        """Soumettre un contrat pour revision interne."""
        contract = self.get_contract(contract_id, with_relations=False)

        if contract.status != ContractStatus.DRAFT.value:
            raise ContractStateError(
                contract.status,
                ContractStatus.IN_REVIEW.value
            )

        return self.contracts.update_status(
            contract,
            ContractStatus.IN_REVIEW.value,
            submitted_by
        )

    def start_negotiation(
        self,
        contract_id: UUID,
        started_by: UUID
    ) -> Contract:
        """Passer un contrat en negociation."""
        contract = self.get_contract(contract_id, with_relations=False)

        allowed_from = [
            ContractStatus.DRAFT.value,
            ContractStatus.IN_REVIEW.value
        ]
        if contract.status not in allowed_from:
            raise ContractStateError(
                contract.status,
                ContractStatus.IN_NEGOTIATION.value
            )

        return self.contracts.update_status(
            contract,
            ContractStatus.IN_NEGOTIATION.value,
            started_by
        )

    def submit_for_approval(
        self,
        contract_id: UUID,
        request: ContractSubmitForApprovalRequest,
        submitted_by: UUID
    ) -> Contract:
        """Soumettre un contrat pour approbation."""
        contract = self.get_contract(contract_id, with_relations=True)

        # Valider que le contrat est pret
        self._validate_contract_for_approval(contract)

        # Verifier les parties
        if not contract.parties or len(contract.parties) < 2:
            raise MissingPartyError("Au moins 2 parties sont requises")

        # Creer la demande d'approbation
        approval = self.approvals.create(
            contract_id,
            {
                "level": 1,
                "level_name": "Niveau 1",
                "approver_id": request.approver_id,
                "due_date": datetime.utcnow() + timedelta(days=7)
            },
            submitted_by
        )

        # Mettre a jour le statut
        contract.current_approver_id = request.approver_id
        contract.approval_level = 1

        return self.contracts.update_status(
            contract,
            ContractStatus.PENDING_APPROVAL.value,
            submitted_by
        )

    def approve_contract(
        self,
        contract_id: UUID,
        decision: ApprovalDecisionRequest,
        approver_id: UUID
    ) -> Contract:
        """Approuver ou rejeter un contrat."""
        contract = self.get_contract(contract_id, with_relations=False)

        if contract.status != ContractStatus.PENDING_APPROVAL.value:
            raise ContractStateError(
                contract.status,
                "approval"
            )

        # Verifier que l'utilisateur est l'approbateur
        approval = self.approvals.get_current_approval(contract_id)
        if not approval or approval.approver_id != approver_id:
            raise ApprovalNotAuthorizedError(str(approver_id))

        if approval.status != ApprovalStatus.PENDING.value:
            raise ApprovalAlreadyProcessedError(approval.status)

        # Enregistrer la decision
        self.approvals.record_decision(
            approval,
            decision.decision,
            decision.comments,
            decision.rejection_reason,
            decision.conditions
        )

        if decision.decision == "approved":
            # Passer au niveau suivant ou finaliser
            contract.approved_at = datetime.utcnow()
            contract.approved_by = approver_id
            contract.current_approver_id = None

            new_status = ContractStatus.APPROVED.value
            if contract.requires_signature:
                new_status = ContractStatus.PENDING_SIGNATURE.value

            return self.contracts.update_status(
                contract, new_status, approver_id
            )
        else:
            # Rejete - retour en brouillon
            contract.current_approver_id = None
            return self.contracts.update_status(
                contract,
                ContractStatus.DRAFT.value,
                approver_id,
                reason=decision.rejection_reason
            )

    def activate_contract(
        self,
        contract_id: UUID,
        activated_by: UUID
    ) -> Contract:
        """Activer un contrat (apres signature complete)."""
        contract = self.get_contract(contract_id, with_relations=True)

        allowed_from = [
            ContractStatus.APPROVED.value,
            ContractStatus.PENDING_SIGNATURE.value,
            ContractStatus.PARTIALLY_SIGNED.value
        ]
        if contract.status not in allowed_from:
            raise ContractStateError(contract.status, ContractStatus.ACTIVE.value)

        # Verifier que toutes les parties ont signe si requis
        if contract.requires_signature:
            unsigned = [p for p in contract.parties if p.is_signatory and not p.has_signed]
            if unsigned:
                raise ContractStateError(
                    contract.status,
                    ContractStatus.ACTIVE.value,
                    f"{len(unsigned)} signature(s) manquante(s)"
                )

        contract.all_parties_signed = True
        contract.signed_date = datetime.utcnow()

        # Calculer la date de renouvellement
        if contract.end_date and contract.renewal_type != RenewalType.NONE.value:
            notice_days = contract.renewal_notice_days or 90
            contract.next_renewal_date = contract.end_date - timedelta(days=notice_days)

        contract = self.contracts.update_status(
            contract,
            ContractStatus.ACTIVE.value,
            activated_by
        )

        # Activer les lignes recurrentes
        self._activate_recurring_lines(contract)

        # Creer les alertes d'echeance
        self._create_automatic_alerts(contract, activated_by)

        return contract

    def suspend_contract(
        self,
        contract_id: UUID,
        reason: str,
        suspended_by: UUID
    ) -> Contract:
        """Suspendre un contrat actif."""
        contract = self.get_contract(contract_id, with_relations=False)

        if contract.status != ContractStatus.ACTIVE.value:
            raise ContractStateError(contract.status, ContractStatus.SUSPENDED.value)

        return self.contracts.update_status(
            contract,
            ContractStatus.SUSPENDED.value,
            suspended_by,
            reason=reason
        )

    def resume_contract(
        self,
        contract_id: UUID,
        resumed_by: UUID
    ) -> Contract:
        """Reprendre un contrat suspendu."""
        contract = self.get_contract(contract_id, with_relations=False)

        if contract.status not in [
            ContractStatus.SUSPENDED.value,
            ContractStatus.ON_HOLD.value
        ]:
            raise ContractStateError(contract.status, ContractStatus.ACTIVE.value)

        return self.contracts.update_status(
            contract,
            ContractStatus.ACTIVE.value,
            resumed_by
        )

    def terminate_contract(
        self,
        contract_id: UUID,
        request: ContractTerminateRequest,
        terminated_by: UUID
    ) -> Contract:
        """Resilier un contrat."""
        contract = self.get_contract(contract_id, with_relations=False)

        if contract.status not in [
            ContractStatus.ACTIVE.value,
            ContractStatus.SUSPENDED.value
        ]:
            raise ContractStateError(contract.status, ContractStatus.TERMINATED.value)

        contract.termination_date = request.termination_date
        contract.termination_reason = request.reason
        contract.termination_by = terminated_by

        if request.penalty_amount:
            contract.early_termination_penalty = request.penalty_amount

        return self.contracts.update_status(
            contract,
            ContractStatus.TERMINATED.value,
            terminated_by,
            reason=request.reason
        )

    def expire_contract(
        self,
        contract_id: UUID,
        expired_by: UUID = None
    ) -> Contract:
        """Marquer un contrat comme expire."""
        contract = self.get_contract(contract_id, with_relations=False)

        if contract.status != ContractStatus.ACTIVE.value:
            raise ContractStateError(contract.status, ContractStatus.EXPIRED.value)

        return self.contracts.update_status(
            contract,
            ContractStatus.EXPIRED.value,
            expired_by
        )

    # ========================================================================
    # PARTIES
    # ========================================================================

    def add_party(
        self,
        contract_id: UUID,
        data: ContractPartyCreate,
        created_by: UUID = None
    ) -> ContractParty:
        """Ajouter une partie au contrat."""
        contract = self.get_contract(contract_id, with_relations=False)

        if contract.status not in [
            ContractStatus.DRAFT.value,
            ContractStatus.IN_REVIEW.value,
            ContractStatus.IN_NEGOTIATION.value
        ]:
            raise ContractNotEditableError(contract.status)

        party_data = data.model_dump(exclude_unset=True)
        return self.parties.create(contract_id, party_data, created_by)

    def update_party(
        self,
        party_id: UUID,
        data: ContractPartyUpdate,
        updated_by: UUID = None
    ) -> ContractParty:
        """Mettre a jour une partie."""
        party = self.parties.get_by_id(party_id)
        if not party:
            raise PartyNotFoundError(str(party_id))

        # Verifier que le contrat est modifiable
        contract = self.contracts.get_by_id(party.contract_id)
        if contract.status not in [
            ContractStatus.DRAFT.value,
            ContractStatus.IN_REVIEW.value,
            ContractStatus.IN_NEGOTIATION.value
        ]:
            raise ContractNotEditableError(contract.status)

        update_data = data.model_dump(exclude_unset=True)
        return self.parties.update(party, update_data, updated_by)

    def record_signature(
        self,
        contract_id: UUID,
        party_id: UUID,
        signature_id: str,
        signature_ip: str = None
    ) -> ContractParty:
        """Enregistrer la signature d'une partie."""
        contract = self.get_contract(contract_id, with_relations=True)

        if contract.status not in [
            ContractStatus.PENDING_SIGNATURE.value,
            ContractStatus.PARTIALLY_SIGNED.value
        ]:
            raise ContractStateError(
                contract.status,
                "signature",
                "Le contrat n'est pas en attente de signature"
            )

        party = self.parties.get_by_id(party_id)
        if not party or party.contract_id != contract_id:
            raise PartyNotFoundError(str(party_id))

        if party.has_signed:
            raise PartyAlreadySignedError(str(party_id))

        party = self.parties.record_signature(party, signature_id, signature_ip)

        # Verifier si toutes les parties ont signe
        unsigned = self.parties.get_unsigned_parties(contract_id)
        if not unsigned:
            # Toutes les signatures obtenues - activer le contrat
            self.activate_contract(contract_id, party_id)
        elif contract.status == ContractStatus.PENDING_SIGNATURE.value:
            # Au moins une signature - passer en partiellement signe
            self.contracts.update_status(
                contract,
                ContractStatus.PARTIALLY_SIGNED.value,
                party_id
            )

        return party

    # ========================================================================
    # LINES
    # ========================================================================

    def add_line(
        self,
        contract_id: UUID,
        data: ContractLineCreate,
        created_by: UUID = None
    ) -> ContractLine:
        """Ajouter une ligne au contrat."""
        contract = self.get_contract(contract_id, with_relations=False)

        if contract.status not in [
            ContractStatus.DRAFT.value,
            ContractStatus.IN_REVIEW.value,
            ContractStatus.IN_NEGOTIATION.value
        ]:
            raise ContractNotEditableError(contract.status)

        line_data = data.model_dump(exclude_unset=True)
        line = self.lines.create(contract_id, line_data, created_by)

        # Recalculer la valeur totale du contrat
        self._recalculate_contract_total(contract_id)

        return line

    def update_line(
        self,
        line_id: UUID,
        data: ContractLineUpdate,
        updated_by: UUID = None
    ) -> ContractLine:
        """Mettre a jour une ligne de contrat."""
        line = self.lines.get_by_id(line_id)
        if not line:
            raise ContractLineNotFoundError(str(line_id))

        contract = self.contracts.get_by_id(line.contract_id)
        if contract.status not in [
            ContractStatus.DRAFT.value,
            ContractStatus.IN_REVIEW.value,
            ContractStatus.IN_NEGOTIATION.value
        ]:
            raise ContractNotEditableError(contract.status)

        update_data = data.model_dump(exclude_unset=True)
        line = self.lines.update(line, update_data, updated_by)

        # Recalculer la valeur totale
        self._recalculate_contract_total(line.contract_id)

        return line

    def delete_line(
        self,
        line_id: UUID,
        deleted_by: UUID = None
    ) -> bool:
        """Supprimer une ligne de contrat."""
        line = self.lines.get_by_id(line_id)
        if not line:
            raise ContractLineNotFoundError(str(line_id))

        contract = self.contracts.get_by_id(line.contract_id)
        if contract.status not in [
            ContractStatus.DRAFT.value,
            ContractStatus.IN_REVIEW.value,
            ContractStatus.IN_NEGOTIATION.value
        ]:
            raise ContractNotEditableError(contract.status)

        contract_id = line.contract_id
        result = self.lines.soft_delete(line, deleted_by)

        # Recalculer la valeur totale
        self._recalculate_contract_total(contract_id)

        return result

    # ========================================================================
    # OBLIGATIONS
    # ========================================================================

    def add_obligation(
        self,
        contract_id: UUID,
        data: ContractObligationCreate,
        created_by: UUID = None
    ) -> ContractObligation:
        """Ajouter une obligation contractuelle."""
        self.get_contract(contract_id, with_relations=False)

        obligation_data = data.model_dump(exclude_unset=True)
        obligation = self.obligations.create(contract_id, obligation_data, created_by)

        # Creer alerte si date d'echeance
        if obligation.due_date:
            self._create_obligation_alert(obligation, created_by)

        return obligation

    def complete_obligation(
        self,
        obligation_id: UUID,
        completed_by: UUID,
        notes: str = None,
        evidence_document_id: UUID = None
    ) -> ContractObligation:
        """Marquer une obligation comme completee."""
        obligation = self.obligations.get_by_id(obligation_id)
        if not obligation:
            raise ObligationNotFoundError(str(obligation_id))

        obligation = self.obligations.mark_completed(obligation, completed_by, notes)

        if evidence_document_id:
            obligation.evidence_document_id = evidence_document_id
            self.db.commit()

        return obligation

    def get_overdue_obligations(self) -> List[ContractObligation]:
        """Recuperer toutes les obligations en retard."""
        return self.obligations.get_overdue_obligations()

    def get_upcoming_obligations(self, days: int = 30) -> List[ContractObligation]:
        """Recuperer les obligations a venir."""
        return self.obligations.get_upcoming_obligations(days)

    # ========================================================================
    # MILESTONES
    # ========================================================================

    def add_milestone(
        self,
        contract_id: UUID,
        data: ContractMilestoneCreate,
        created_by: UUID = None
    ) -> ContractMilestone:
        """Ajouter un jalon au contrat."""
        self.get_contract(contract_id, with_relations=False)

        # Verifier dependance si specifiee
        if data.depends_on_milestone_id:
            depends_on = self.milestones.get_by_id(data.depends_on_milestone_id)
            if not depends_on:
                raise MilestoneNotFoundError(str(data.depends_on_milestone_id))

        milestone_data = data.model_dump(exclude_unset=True)
        return self.milestones.create(contract_id, milestone_data, created_by)

    def complete_milestone(
        self,
        milestone_id: UUID,
        completed_by: UUID,
        actual_date: date = None,
        notes: str = None,
        trigger_payment: bool = False
    ) -> ContractMilestone:
        """Marquer un jalon comme complete."""
        milestone = self.milestones.get_by_id(milestone_id)
        if not milestone:
            raise MilestoneNotFoundError(str(milestone_id))

        # Verifier dependances
        if milestone.depends_on_milestone_id:
            depends_on = self.milestones.get_by_id(milestone.depends_on_milestone_id)
            if depends_on and depends_on.status != "completed":
                raise MilestoneDependencyError(
                    str(milestone_id),
                    str(milestone.depends_on_milestone_id)
                )

        milestone = self.milestones.mark_completed(
            milestone, completed_by, actual_date, notes
        )

        if trigger_payment and milestone.payment_amount:
            milestone.payment_triggered = True
            self.db.commit()
            # Log pour integration future avec module facturation
            logger.info(
                "Milestone payment triggered: milestone=%s, contract=%s, amount=%s",
                milestone.id,
                milestone.contract_id,
                milestone.payment_amount
            )

        return milestone

    def get_upcoming_milestones(self, days: int = 30) -> List[ContractMilestone]:
        """Recuperer les jalons a venir."""
        return self.milestones.get_upcoming_milestones(days)

    # ========================================================================
    # AMENDMENTS
    # ========================================================================

    def create_amendment(
        self,
        contract_id: UUID,
        data: ContractAmendmentCreate,
        created_by: UUID = None
    ) -> ContractAmendment:
        """Creer un avenant au contrat."""
        contract = self.get_contract(contract_id, with_relations=False)

        # Verifier que le contrat peut avoir un avenant
        if contract.status not in [
            ContractStatus.ACTIVE.value,
            ContractStatus.SUSPENDED.value
        ]:
            raise AmendmentNotAllowedError(contract.status)

        amendment_data = data.model_dump(exclude_unset=True)
        amendment = self.amendments.create(contract_id, amendment_data, created_by)

        # Incrementer le compteur d'avenants
        contract.amendment_count += 1
        self.db.commit()

        return amendment

    def apply_amendment(
        self,
        amendment_id: UUID,
        applied_by: UUID
    ) -> Contract:
        """Appliquer un avenant signe au contrat."""
        amendment = self.amendments.get_by_id(amendment_id)
        if not amendment:
            raise AmendmentNotFoundError(str(amendment_id))

        if amendment.status != ContractStatus.ACTIVE.value:
            raise AmendmentNotAllowedError(
                f"L'avenant doit etre actif pour etre applique (statut: {amendment.status})"
            )

        contract = self.get_contract(amendment.contract_id, with_relations=False)

        # Appliquer les changements
        if amendment.value_change:
            contract.total_value += amendment.value_change

        if amendment.new_end_date:
            contract.end_date = amendment.new_end_date

        if amendment.new_duration_months:
            contract.duration_months = amendment.new_duration_months

        if amendment.amendment_type == AmendmentType.TERMINATION.value:
            return self.terminate_contract(
                contract.id,
                ContractTerminateRequest(
                    termination_date=amendment.effective_date,
                    reason=f"Resiliation par avenant #{amendment.amendment_number}"
                ),
                applied_by
            )

        contract.updated_by = applied_by
        contract.version += 1
        self.db.commit()
        self.db.refresh(contract)

        return contract

    # ========================================================================
    # RENEWALS
    # ========================================================================

    def renew_contract(
        self,
        contract_id: UUID,
        request: ContractRenewRequest,
        renewed_by: UUID
    ) -> Contract:
        """Renouveler un contrat."""
        contract = self.get_contract(contract_id, with_relations=False)

        # Verifier que le renouvellement est possible
        if contract.status not in [
            ContractStatus.ACTIVE.value,
            ContractStatus.EXPIRED.value
        ]:
            raise RenewalNotAllowedError(f"Statut invalide: {contract.status}")

        if contract.max_renewals and contract.renewal_count >= contract.max_renewals:
            raise MaxRenewalsReachedError(contract.max_renewals)

        # Creer l'enregistrement de renouvellement
        renewal = ContractRenewal(
            tenant_id=self.tenant_id,
            contract_id=contract_id,
            renewal_number=contract.renewal_count + 1,
            original_end_date=contract.end_date,
            new_end_date=request.new_end_date,
            renewal_date=date.today(),
            effective_date=contract.end_date or date.today(),
            renewal_type=contract.renewal_type,
            is_automatic=contract.renewal_type == RenewalType.AUTOMATIC.value,
            previous_value=contract.total_value,
            new_value=request.new_value or contract.total_value,
            status="confirmed",
            approved_by=renewed_by,
            approved_at=datetime.utcnow(),
            created_by=renewed_by
        )

        if request.price_increase_percent:
            renewal.price_increase_percent = request.price_increase_percent
            renewal.new_value = contract.total_value * (1 + request.price_increase_percent / 100)

        self.db.add(renewal)

        # Mettre a jour le contrat
        contract.end_date = request.new_end_date
        contract.renewal_count += 1

        if renewal.new_value:
            contract.total_value = renewal.new_value

        if request.new_terms:
            # Appliquer les nouvelles conditions
            for key, value in request.new_terms.items():
                if hasattr(contract, key):
                    setattr(contract, key, value)

        # Calculer la prochaine date de renouvellement
        if contract.renewal_type != RenewalType.NONE.value:
            notice_days = contract.renewal_notice_days or 90
            contract.next_renewal_date = contract.end_date - timedelta(days=notice_days)

        contract.updated_by = renewed_by
        contract.version += 1

        # Mettre a jour le statut si necessaire
        if contract.status == ContractStatus.EXPIRED.value:
            contract.status = ContractStatus.ACTIVE.value

        self.db.commit()
        self.db.refresh(contract)

        # Mettre a jour les alertes
        self._update_automatic_alerts(contract, renewed_by)

        return contract

    def process_automatic_renewals(self) -> List[Contract]:
        """Traiter les renouvellements automatiques."""
        # Trouver les contrats a renouveler automatiquement
        contracts_to_renew = self.contracts._base_query().filter(
            Contract.status == ContractStatus.ACTIVE.value,
            Contract.renewal_type == RenewalType.AUTOMATIC.value,
            Contract.end_date <= date.today() + timedelta(days=1)
        ).all()

        renewed = []
        for contract in contracts_to_renew:
            if contract.max_renewals and contract.renewal_count >= contract.max_renewals:
                continue

            new_duration = contract.auto_renewal_term_months or 12
            new_end_date = contract.end_date + timedelta(days=new_duration * 30)

            price_increase = contract.renewal_price_increase_percent

            self.renew_contract(
                contract.id,
                ContractRenewRequest(
                    new_end_date=new_end_date,
                    price_increase_percent=price_increase
                ),
                None  # Systeme
            )
            renewed.append(contract)

        return renewed

    # ========================================================================
    # ALERTS
    # ========================================================================

    def create_alert(
        self,
        contract_id: UUID,
        data: ContractAlertCreate,
        created_by: UUID = None
    ) -> ContractAlert:
        """Creer une alerte manuelle."""
        self.get_contract(contract_id, with_relations=False)

        alert_data = data.model_dump(exclude_unset=True)

        # Definir la date de declenchement
        if not alert_data.get("trigger_date"):
            days_before = 7 if alert_data.get("priority") == AlertPriority.CRITICAL.value else 14
            alert_data["trigger_date"] = alert_data["due_date"] - timedelta(days=days_before)

        return self.alerts.create(contract_id, alert_data, created_by)

    def acknowledge_alert(
        self,
        alert_id: UUID,
        acknowledged_by: UUID,
        notes: str = None,
        action_taken: str = None
    ) -> ContractAlert:
        """Acquitter une alerte."""
        alert = self.alerts.get_by_id(alert_id)
        if not alert:
            raise AlertNotFoundError(str(alert_id))

        return self.alerts.acknowledge(alert, acknowledged_by, notes, action_taken)

    def get_active_alerts(self, contract_id: UUID = None) -> List[ContractAlert]:
        """Recuperer les alertes actives."""
        return self.alerts.get_active_alerts(contract_id)

    def process_pending_alerts(self) -> List[ContractAlert]:
        """Traiter et envoyer les alertes en attente."""
        pending = self.alerts.get_pending_alerts(date.today())
        sent = []

        for alert in pending:
            # Log l'alerte pour traitement
            logger.info(
                "Contract alert triggered: type=%s, contract=%s, trigger_date=%s",
                alert.alert_type,
                alert.contract_id,
                alert.trigger_date
            )
            self.alerts.mark_sent(alert)
            sent.append(alert)

        return sent

    def check_and_create_alerts(self) -> List[ContractAlert]:
        """Verifier les contrats et creer les alertes necessaires."""
        created_alerts = []
        today = date.today()

        # Contrats actifs
        active_contracts = self.contracts.get_active_contracts()

        for contract in active_contracts:
            # Alerte expiration
            if contract.end_date:
                days_to_expiry = (contract.end_date - today).days
                if 0 < days_to_expiry <= 30:
                    existing = self._alert_exists(
                        contract.id, AlertType.EXPIRY.value, contract.end_date
                    )
                    if not existing:
                        alert = self.alerts.create(contract.id, {
                            "alert_type": AlertType.EXPIRY.value,
                            "priority": AlertPriority.HIGH.value if days_to_expiry <= 7 else AlertPriority.MEDIUM.value,
                            "title": f"Contrat {contract.contract_number} expire bientot",
                            "message": f"Le contrat expire dans {days_to_expiry} jours",
                            "due_date": contract.end_date,
                            "trigger_date": today
                        })
                        created_alerts.append(alert)

            # Alerte renouvellement
            if contract.next_renewal_date:
                days_to_renewal = (contract.next_renewal_date - today).days
                if 0 < days_to_renewal <= 30:
                    existing = self._alert_exists(
                        contract.id, AlertType.RENEWAL_NOTICE.value, contract.next_renewal_date
                    )
                    if not existing:
                        alert = self.alerts.create(contract.id, {
                            "alert_type": AlertType.RENEWAL_NOTICE.value,
                            "priority": AlertPriority.HIGH.value,
                            "title": f"Preavis renouvellement {contract.contract_number}",
                            "message": f"Date limite de preavis dans {days_to_renewal} jours",
                            "due_date": contract.next_renewal_date,
                            "trigger_date": today
                        })
                        created_alerts.append(alert)

        return created_alerts

    # ========================================================================
    # TEMPLATES & CATEGORIES
    # ========================================================================

    def create_template(
        self,
        data: ContractTemplateCreate,
        created_by: UUID = None
    ) -> ContractTemplate:
        """Creer un template de contrat."""
        template_data = data.model_dump(exclude_unset=True)
        return self.templates.create(template_data, created_by)

    def update_template(
        self,
        template_id: UUID,
        data: ContractTemplateUpdate,
        updated_by: UUID = None
    ) -> ContractTemplate:
        """Mettre a jour un template."""
        template = self.templates.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(str(template_id))

        update_data = data.model_dump(exclude_unset=True)
        return self.templates.update(template, update_data, updated_by)

    def list_templates(
        self,
        contract_type: str = None,
        active_only: bool = True
    ) -> List[ContractTemplate]:
        """Lister les templates disponibles."""
        return self.templates.list_all(contract_type, active_only)

    def create_category(
        self,
        data: ContractCategoryCreate,
        created_by: UUID = None
    ) -> ContractCategory:
        """Creer une categorie de contrat."""
        category_data = data.model_dump(exclude_unset=True)
        return self.categories.create(category_data, created_by)

    def list_categories(self, active_only: bool = True) -> List[ContractCategory]:
        """Lister les categories."""
        return self.categories.list_all(active_only)

    # ========================================================================
    # STATISTICS & DASHBOARD
    # ========================================================================

    def get_statistics(self) -> ContractStatsResponse:
        """Calculer les statistiques des contrats."""
        all_contracts = self.contracts._base_query().all()

        stats = {
            "total_contracts": len(all_contracts),
            "active_contracts": 0,
            "draft_contracts": 0,
            "pending_signature": 0,
            "pending_approval": 0,
            "expired_contracts": 0,
            "terminated_contracts": 0,
            "total_active_value": Decimal("0"),
            "expiring_30_days": 0,
            "expiring_60_days": 0,
            "expiring_90_days": 0,
            "by_type": {},
            "by_status": {},
            "overdue_obligations": 0,
            "pending_approvals": 0
        }

        today = date.today()
        mrr = Decimal("0")

        for contract in all_contracts:
            # Par statut
            status = contract.status
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            if status == ContractStatus.DRAFT.value:
                stats["draft_contracts"] += 1
            elif status == ContractStatus.ACTIVE.value:
                stats["active_contracts"] += 1
                stats["total_active_value"] += contract.total_value or Decimal("0")

                # Calcul MRR
                if contract.billing_frequency == BillingFrequency.MONTHLY.value:
                    mrr += contract.total_value or Decimal("0")
                elif contract.billing_frequency == BillingFrequency.ANNUAL.value:
                    mrr += (contract.total_value or Decimal("0")) / 12
                elif contract.billing_frequency == BillingFrequency.QUARTERLY.value:
                    mrr += (contract.total_value or Decimal("0")) / 3

                # Echeances
                if contract.end_date:
                    days = (contract.end_date - today).days
                    if 0 <= days <= 30:
                        stats["expiring_30_days"] += 1
                    if 0 <= days <= 60:
                        stats["expiring_60_days"] += 1
                    if 0 <= days <= 90:
                        stats["expiring_90_days"] += 1

            elif status == ContractStatus.PENDING_SIGNATURE.value:
                stats["pending_signature"] += 1
            elif status == ContractStatus.PENDING_APPROVAL.value:
                stats["pending_approval"] += 1
            elif status == ContractStatus.EXPIRED.value:
                stats["expired_contracts"] += 1
            elif status == ContractStatus.TERMINATED.value:
                stats["terminated_contracts"] += 1

            # Par type
            ctype = contract.contract_type
            stats["by_type"][ctype] = stats["by_type"].get(ctype, 0) + 1

        stats["mrr"] = mrr
        stats["arr"] = mrr * 12

        if stats["active_contracts"] > 0:
            stats["average_contract_value"] = (
                stats["total_active_value"] / stats["active_contracts"]
            ).quantize(Decimal("0.01"))

        # Obligations en retard
        stats["overdue_obligations"] = len(self.obligations.get_overdue_obligations())

        # Approbations en attente
        pending_approvals = self.approvals._base_query().filter(
            ContractApproval.status == ApprovalStatus.PENDING.value
        ).count()
        stats["pending_approvals"] = pending_approvals

        return ContractStatsResponse(**stats)

    def get_dashboard(self) -> ContractDashboardResponse:
        """Recuperer les donnees du dashboard."""
        stats = self.get_statistics()

        # Renouvellements a venir
        upcoming_renewals = self.contracts._base_query().filter(
            Contract.status == ContractStatus.ACTIVE.value,
            Contract.next_renewal_date != None,
            Contract.next_renewal_date <= date.today() + timedelta(days=30)
        ).order_by(Contract.next_renewal_date).limit(10).all()

        # Contrats expirant bientot
        expiring_soon = self.contracts.get_expiring_contracts(30)[:10]

        # Approbations en attente
        pending_approvals_contracts = self.contracts.get_pending_approvals()[:10]

        # Signatures en attente
        pending_signatures = self.contracts.get_pending_signatures()[:10]

        # Contrats recents
        recent = self.contracts._base_query().order_by(
            Contract.created_at.desc()
        ).limit(10).all()

        # Obligations en retard
        overdue = self.obligations.get_overdue_obligations()[:10]

        # Jalons a venir
        upcoming_milestones = self.milestones.get_upcoming_milestones(14)[:10]

        # Alertes actives
        active_alerts = self.alerts.get_active_alerts()[:10]

        def to_summary(c: Contract) -> ContractSummaryResponse:
            days_expiry = None
            days_renewal = None
            if c.end_date:
                days_expiry = (c.end_date - date.today()).days
            if c.next_renewal_date:
                days_renewal = (c.next_renewal_date - date.today()).days

            party_names = [p.name for p in (c.parties or [])]

            return ContractSummaryResponse(
                id=c.id,
                contract_number=c.contract_number,
                title=c.title,
                contract_type=c.contract_type,
                status=c.status,
                total_value=c.total_value or Decimal("0"),
                currency=c.currency,
                start_date=c.start_date,
                end_date=c.end_date,
                owner_name=c.owner_name,
                party_names=party_names,
                days_until_expiry=days_expiry,
                days_until_renewal=days_renewal,
                created_at=c.created_at
            )

        return ContractDashboardResponse(
            stats=stats,
            upcoming_renewals=[to_summary(c) for c in upcoming_renewals],
            expiring_soon=[to_summary(c) for c in expiring_soon],
            pending_approvals=[to_summary(c) for c in pending_approvals_contracts],
            pending_signatures=[to_summary(c) for c in pending_signatures],
            recent_contracts=[to_summary(c) for c in recent],
            overdue_obligations=overdue,
            upcoming_milestones=upcoming_milestones,
            active_alerts=active_alerts
        )

    def calculate_metrics(self, metric_date: date = None) -> ContractMetrics:
        """Calculer et sauvegarder les metriques."""
        if not metric_date:
            metric_date = date.today()

        stats = self.get_statistics()

        metrics_data = {
            "metric_date": metric_date,
            "total_contracts": stats.total_contracts,
            "active_contracts": stats.active_contracts,
            "draft_contracts": stats.draft_contracts,
            "pending_signature": stats.pending_signature,
            "expired_contracts": stats.expired_contracts,
            "terminated_contracts": stats.terminated_contracts,
            "total_active_value": stats.total_active_value,
            "average_contract_value": stats.average_contract_value,
            "mrr": stats.mrr,
            "arr": stats.arr,
            "expiring_30_days": stats.expiring_30_days,
            "expiring_60_days": stats.expiring_60_days,
            "expiring_90_days": stats.expiring_90_days,
            "by_type": stats.by_type,
            "by_status": stats.by_status,
            "overdue_obligations": stats.overdue_obligations,
            "pending_approvals": stats.pending_approvals
        }

        return self.metrics.save(metrics_data)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _validate_contract_for_approval(self, contract: Contract):
        """Valider qu'un contrat est pret pour approbation."""
        errors = []

        if not contract.title:
            errors.append("Le titre est requis")

        if not contract.contract_type:
            errors.append("Le type de contrat est requis")

        if contract.total_value and contract.total_value < 0:
            errors.append("La valeur ne peut pas etre negative")

        if errors:
            raise ContractValidationError(
                "Le contrat n'est pas valide pour approbation",
                errors=errors
            )

    def _apply_template(
        self,
        contract_data: Dict[str, Any],
        template: ContractTemplate
    ) -> Dict[str, Any]:
        """Appliquer un template a un contrat."""
        # Copier les valeurs par defaut du template
        if template.default_duration_months and "duration_months" not in contract_data:
            contract_data["duration_months"] = template.default_duration_months

        if template.default_renewal_type and "renewal_type" not in contract_data:
            contract_data["renewal_type"] = template.default_renewal_type

        if template.default_payment_terms_days and "payment_terms_days" not in contract_data:
            contract_data["payment_terms_days"] = template.default_payment_terms_days

        if template.content and "content" not in contract_data:
            contract_data["content"] = template.content

        # Ajouter les clauses par defaut
        if template.clause_templates and "clauses" not in contract_data:
            contract_data["clauses"] = [
                {
                    "title": ct.title,
                    "content": ct.content,
                    "clause_type": ct.clause_type,
                    "section": ct.section,
                    "is_from_template": True,
                    "template_id": ct.id,
                    "is_mandatory": ct.is_mandatory,
                    "is_negotiable": ct.is_negotiable,
                    "risk_level": ct.risk_level,
                    "sort_order": ct.sort_order
                }
                for ct in template.clause_templates
                if ct.is_active
            ]

        return contract_data

    def _recalculate_contract_total(self, contract_id: UUID):
        """Recalculer la valeur totale d'un contrat."""
        lines = self.lines.get_by_contract(contract_id)
        total = sum(line.total or Decimal("0") for line in lines if line.is_active)

        contract = self.contracts.get_by_id(contract_id)
        if contract:
            contract.total_value = total
            self.db.commit()

    def _activate_recurring_lines(self, contract: Contract):
        """Activer les lignes recurrentes apres activation du contrat."""
        lines = self.lines.get_recurring_lines(contract.id)
        today = date.today()

        for line in lines:
            if line.is_recurring and not line.next_billing_date:
                line.next_billing_date = line.billing_start_date or today
                line.original_price = line.unit_price

        self.db.commit()

    def _create_automatic_alerts(self, contract: Contract, created_by: UUID = None):
        """Creer les alertes automatiques pour un contrat."""
        # Alerte expiration
        if contract.end_date:
            alert_date = contract.end_date - timedelta(days=30)
            if alert_date > date.today():
                self.alerts.create(contract.id, {
                    "alert_type": AlertType.EXPIRY.value,
                    "priority": AlertPriority.HIGH.value,
                    "title": f"Contrat {contract.contract_number} arrive a echeance",
                    "message": f"Le contrat expire le {contract.end_date}",
                    "due_date": contract.end_date,
                    "trigger_date": alert_date,
                    "notify_owner": True
                }, created_by)

        # Alerte renouvellement
        if contract.next_renewal_date:
            alert_date = contract.next_renewal_date - timedelta(days=14)
            if alert_date > date.today():
                self.alerts.create(contract.id, {
                    "alert_type": AlertType.RENEWAL_NOTICE.value,
                    "priority": AlertPriority.HIGH.value,
                    "title": f"Preavis renouvellement {contract.contract_number}",
                    "message": f"Date limite de preavis: {contract.next_renewal_date}",
                    "due_date": contract.next_renewal_date,
                    "trigger_date": alert_date,
                    "notify_owner": True
                }, created_by)

    def _update_automatic_alerts(self, contract: Contract, updated_by: UUID = None):
        """Mettre a jour les alertes automatiques."""
        # Desactiver les anciennes alertes automatiques
        existing_alerts = self.alerts.get_by_contract(contract.id)
        for alert in existing_alerts:
            if alert.alert_type in [AlertType.EXPIRY.value, AlertType.RENEWAL_NOTICE.value]:
                if not alert.is_acknowledged:
                    self.alerts.dismiss(alert)

        # Recreer les alertes
        self._create_automatic_alerts(contract, updated_by)

    def _create_obligation_alert(
        self,
        obligation: ContractObligation,
        created_by: UUID = None
    ):
        """Creer une alerte pour une obligation."""
        if not obligation.due_date:
            return

        alert_date = obligation.due_date - timedelta(days=obligation.alert_days_before)
        if alert_date <= date.today():
            alert_date = date.today()

        self.alerts.create(obligation.contract_id, {
            "alert_type": AlertType.OBLIGATION_DUE.value,
            "priority": AlertPriority.HIGH.value if obligation.is_critical else AlertPriority.MEDIUM.value,
            "title": f"Obligation: {obligation.title}",
            "message": obligation.description,
            "reference_type": "obligation",
            "reference_id": obligation.id,
            "due_date": obligation.due_date,
            "trigger_date": alert_date,
            "notify_owner": True
        }, created_by)

    def _alert_exists(
        self,
        contract_id: UUID,
        alert_type: str,
        due_date: date
    ) -> bool:
        """Verifier si une alerte similaire existe deja."""
        existing = self.alerts._base_query().filter(
            ContractAlert.contract_id == contract_id,
            ContractAlert.alert_type == alert_type,
            ContractAlert.due_date == due_date,
            ContractAlert.is_active == True
        ).first()
        return existing is not None


# ============================================================================
# FACTORY
# ============================================================================

def create_contract_service(db: Session, tenant_id: str) -> ContractService:
    """Factory pour creer un service de gestion des contrats."""
    return ContractService(db, tenant_id)
