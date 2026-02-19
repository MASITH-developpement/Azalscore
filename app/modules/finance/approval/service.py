"""
AZALSCORE Finance Approval Workflow Service
=============================================

Service de gestion des workflows d'approbation.

Fonctionnalités:
- Règles d'approbation par type de document et montant
- Niveaux d'approbation multiples
- Délégation temporaire
- Escalade automatique
- Historique complet des actions
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class DocumentType(str, Enum):
    """Type de document à approuver."""
    INVOICE = "invoice"
    PAYMENT = "payment"
    EXPENSE = "expense"
    PURCHASE_ORDER = "purchase_order"
    CREDIT_NOTE = "credit_note"
    BUDGET_REQUEST = "budget_request"
    CONTRACT = "contract"
    REFUND = "refund"


class ApprovalStatus(str, Enum):
    """Statut d'une demande d'approbation."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class ActionType(str, Enum):
    """Type d'action d'approbation."""
    APPROVE = "approve"
    REJECT = "reject"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    COMMENT = "comment"
    REQUEST_INFO = "request_info"


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class ApprovalLevel:
    """Niveau d'approbation."""
    level: int
    name: str
    approvers: list[str]           # Liste des user_ids autorisés
    min_approvers: int = 1         # Nombre minimum d'approbations requises
    timeout_hours: int = 48        # Délai avant escalade
    can_delegate: bool = True
    can_escalate: bool = True


@dataclass
class ApprovalRule:
    """Règle d'approbation."""
    id: str
    tenant_id: str
    name: str
    document_type: DocumentType
    min_amount: Optional[Decimal] = None   # Montant minimum pour appliquer la règle
    max_amount: Optional[Decimal] = None   # Montant maximum
    levels: list[ApprovalLevel] = field(default_factory=list)
    is_active: bool = True
    priority: int = 0                      # Plus élevé = plus prioritaire
    conditions: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ApprovalAction:
    """Action d'approbation."""
    id: str
    request_id: str
    action_type: ActionType
    user_id: str
    user_name: Optional[str] = None
    comment: Optional[str] = None
    level: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class ApprovalRequest:
    """Demande d'approbation."""
    id: str
    tenant_id: str
    document_type: DocumentType
    document_id: str
    document_reference: str
    amount: Decimal
    currency: str
    description: str
    requestor_id: str
    requestor_name: Optional[str] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    current_level: int = 1
    total_levels: int = 1
    rule_id: Optional[str] = None
    actions: list[ApprovalAction] = field(default_factory=list)
    pending_approvers: list[str] = field(default_factory=list)
    approved_by: list[str] = field(default_factory=list)
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)

    @property
    def is_pending(self) -> bool:
        """Vérifie si la demande est en attente."""
        return self.status == ApprovalStatus.PENDING

    @property
    def approval_progress(self) -> str:
        """Progression de l'approbation."""
        return f"{self.current_level}/{self.total_levels}"


@dataclass
class Delegation:
    """Délégation de pouvoir."""
    id: str
    tenant_id: str
    delegator_id: str
    delegator_name: str
    delegate_id: str
    delegate_name: str
    document_types: list[DocumentType]
    max_amount: Optional[Decimal] = None
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    is_active: bool = True
    reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ApprovalStats:
    """Statistiques d'approbation."""
    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    average_approval_time_hours: float
    approval_rate: float
    by_document_type: dict
    by_level: dict


# =============================================================================
# DEFAULT RULES
# =============================================================================


class DefaultApprovalRules:
    """Règles d'approbation par défaut."""

    @staticmethod
    def get_default_rules(tenant_id: str) -> list[ApprovalRule]:
        """Retourne les règles par défaut."""
        return [
            # Factures < 1000€ - Auto-approuvé
            ApprovalRule(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name="Factures petits montants",
                document_type=DocumentType.INVOICE,
                max_amount=Decimal("1000"),
                levels=[
                    ApprovalLevel(level=1, name="Manager", approvers=[], min_approvers=1),
                ],
                priority=10,
            ),
            # Factures 1000€ - 10000€
            ApprovalRule(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name="Factures montants moyens",
                document_type=DocumentType.INVOICE,
                min_amount=Decimal("1000"),
                max_amount=Decimal("10000"),
                levels=[
                    ApprovalLevel(level=1, name="Manager", approvers=[], min_approvers=1),
                    ApprovalLevel(level=2, name="Directeur", approvers=[], min_approvers=1),
                ],
                priority=20,
            ),
            # Factures > 10000€
            ApprovalRule(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name="Factures gros montants",
                document_type=DocumentType.INVOICE,
                min_amount=Decimal("10000"),
                levels=[
                    ApprovalLevel(level=1, name="Manager", approvers=[], min_approvers=1),
                    ApprovalLevel(level=2, name="Directeur", approvers=[], min_approvers=1),
                    ApprovalLevel(level=3, name="DG", approvers=[], min_approvers=1),
                ],
                priority=30,
            ),
            # Notes de frais
            ApprovalRule(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name="Notes de frais",
                document_type=DocumentType.EXPENSE,
                levels=[
                    ApprovalLevel(level=1, name="Manager direct", approvers=[], min_approvers=1),
                ],
                priority=10,
            ),
            # Bons de commande
            ApprovalRule(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name="Bons de commande",
                document_type=DocumentType.PURCHASE_ORDER,
                levels=[
                    ApprovalLevel(level=1, name="Responsable achats", approvers=[], min_approvers=1),
                ],
                priority=10,
            ),
        ]


# =============================================================================
# SERVICE
# =============================================================================


class ApprovalWorkflowService:
    """
    Service de gestion des workflows d'approbation.

    Multi-tenant: OUI - Toutes les règles et demandes isolées par tenant
    Sécurité: Vérification des droits d'approbation
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
    ):
        if not tenant_id:
            raise ValueError("tenant_id est requis")

        self.db = db
        self.tenant_id = tenant_id
        self._rules: dict[str, ApprovalRule] = {}
        self._requests: dict[str, ApprovalRequest] = {}
        self._delegations: dict[str, Delegation] = {}

        # Initialiser les règles par défaut
        self._init_default_rules()

        logger.info(f"ApprovalWorkflowService initialisé pour tenant {tenant_id}")

    def _init_default_rules(self):
        """Initialise les règles par défaut."""
        for rule in DefaultApprovalRules.get_default_rules(self.tenant_id):
            self._rules[rule.id] = rule

    # =========================================================================
    # RULES MANAGEMENT
    # =========================================================================

    async def create_rule(
        self,
        name: str,
        document_type: DocumentType,
        levels: list[dict],
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        priority: int = 0,
        conditions: Optional[dict] = None,
    ) -> ApprovalRule:
        """Crée une règle d'approbation."""
        rule = ApprovalRule(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            document_type=document_type,
            min_amount=min_amount,
            max_amount=max_amount,
            levels=[
                ApprovalLevel(
                    level=i + 1,
                    name=lvl.get("name", f"Level {i + 1}"),
                    approvers=lvl.get("approvers", []),
                    min_approvers=lvl.get("min_approvers", 1),
                    timeout_hours=lvl.get("timeout_hours", 48),
                    can_delegate=lvl.get("can_delegate", True),
                    can_escalate=lvl.get("can_escalate", True),
                )
                for i, lvl in enumerate(levels)
            ],
            priority=priority,
            conditions=conditions or {},
        )

        self._rules[rule.id] = rule

        logger.info(f"Règle d'approbation créée: {name}")
        return rule

    async def get_rule(self, rule_id: str) -> Optional[ApprovalRule]:
        """Récupère une règle."""
        rule = self._rules.get(rule_id)
        if rule and rule.tenant_id == self.tenant_id:
            return rule
        return None

    async def list_rules(
        self,
        document_type: Optional[DocumentType] = None,
        active_only: bool = True,
    ) -> list[ApprovalRule]:
        """Liste les règles."""
        rules = [
            r for r in self._rules.values()
            if r.tenant_id == self.tenant_id
        ]

        if document_type:
            rules = [r for r in rules if r.document_type == document_type]

        if active_only:
            rules = [r for r in rules if r.is_active]

        return sorted(rules, key=lambda r: -r.priority)

    async def update_rule(
        self,
        rule_id: str,
        name: Optional[str] = None,
        levels: Optional[list[dict]] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        priority: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[ApprovalRule]:
        """Met à jour une règle."""
        rule = await self.get_rule(rule_id)
        if not rule:
            return None

        if name is not None:
            rule.name = name
        if min_amount is not None:
            rule.min_amount = min_amount
        if max_amount is not None:
            rule.max_amount = max_amount
        if priority is not None:
            rule.priority = priority
        if is_active is not None:
            rule.is_active = is_active
        if levels is not None:
            rule.levels = [
                ApprovalLevel(
                    level=i + 1,
                    name=lvl.get("name", f"Level {i + 1}"),
                    approvers=lvl.get("approvers", []),
                    min_approvers=lvl.get("min_approvers", 1),
                )
                for i, lvl in enumerate(levels)
            ]

        return rule

    async def delete_rule(self, rule_id: str) -> bool:
        """Supprime une règle."""
        rule = await self.get_rule(rule_id)
        if not rule:
            return False

        del self._rules[rule_id]
        logger.info(f"Règle supprimée: {rule_id}")
        return True

    def _find_applicable_rule(
        self,
        document_type: DocumentType,
        amount: Decimal,
    ) -> Optional[ApprovalRule]:
        """Trouve la règle applicable."""
        rules = [
            r for r in self._rules.values()
            if r.tenant_id == self.tenant_id
            and r.document_type == document_type
            and r.is_active
        ]

        for rule in sorted(rules, key=lambda r: -r.priority):
            if rule.min_amount and amount < rule.min_amount:
                continue
            if rule.max_amount and amount > rule.max_amount:
                continue
            return rule

        return None

    # =========================================================================
    # APPROVAL REQUESTS
    # =========================================================================

    async def create_approval_request(
        self,
        document_type: DocumentType,
        document_id: str,
        document_reference: str,
        amount: Decimal,
        description: str,
        requestor_id: str,
        requestor_name: Optional[str] = None,
        currency: str = "EUR",
        metadata: Optional[dict] = None,
    ) -> ApprovalRequest:
        """
        Crée une demande d'approbation.

        Trouve automatiquement la règle applicable selon le type et le montant.
        """
        # Trouver la règle applicable
        rule = self._find_applicable_rule(document_type, amount)

        total_levels = len(rule.levels) if rule else 1
        pending_approvers = rule.levels[0].approvers if rule and rule.levels else []

        request = ApprovalRequest(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            document_type=document_type,
            document_id=document_id,
            document_reference=document_reference,
            amount=amount,
            currency=currency,
            description=description,
            requestor_id=requestor_id,
            requestor_name=requestor_name,
            rule_id=rule.id if rule else None,
            total_levels=total_levels,
            pending_approvers=pending_approvers,
            expires_at=datetime.now() + timedelta(hours=48),
            metadata=metadata or {},
        )

        self._requests[request.id] = request

        logger.info(
            f"Demande d'approbation créée: {document_type.value} "
            f"{document_reference} ({amount} {currency})"
        )

        return request

    async def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Récupère une demande d'approbation."""
        request = self._requests.get(request_id)
        if request and request.tenant_id == self.tenant_id:
            return request
        return None

    async def list_requests(
        self,
        status: Optional[ApprovalStatus] = None,
        document_type: Optional[DocumentType] = None,
        requestor_id: Optional[str] = None,
        approver_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[ApprovalRequest]:
        """Liste les demandes d'approbation."""
        requests = [
            r for r in self._requests.values()
            if r.tenant_id == self.tenant_id
        ]

        if status:
            requests = [r for r in requests if r.status == status]

        if document_type:
            requests = [r for r in requests if r.document_type == document_type]

        if requestor_id:
            requests = [r for r in requests if r.requestor_id == requestor_id]

        if approver_id:
            requests = [
                r for r in requests
                if approver_id in r.pending_approvers or approver_id in r.approved_by
            ]

        return sorted(
            requests,
            key=lambda r: r.created_at,
            reverse=True
        )[:limit]

    async def get_pending_for_user(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[ApprovalRequest]:
        """Récupère les demandes en attente pour un utilisateur."""
        # Vérifier les délégations
        delegate_for = await self._get_delegation_principals(user_id)
        all_approvers = [user_id] + delegate_for

        requests = [
            r for r in self._requests.values()
            if r.tenant_id == self.tenant_id
            and r.status == ApprovalStatus.PENDING
            and any(approver in r.pending_approvers for approver in all_approvers)
        ]

        return sorted(
            requests,
            key=lambda r: r.created_at,
            reverse=True
        )[:limit]

    # =========================================================================
    # APPROVAL ACTIONS
    # =========================================================================

    async def approve(
        self,
        request_id: str,
        approver_id: str,
        approver_name: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Optional[ApprovalRequest]:
        """Approuve une demande."""
        request = await self.get_request(request_id)
        if not request or request.status != ApprovalStatus.PENDING:
            return None

        # Vérifier que l'utilisateur peut approuver
        can_approve = await self._can_user_approve(request, approver_id)
        if not can_approve:
            logger.warning(f"Utilisateur {approver_id} non autorisé à approuver {request_id}")
            return None

        # Enregistrer l'action
        action = ApprovalAction(
            id=str(uuid.uuid4()),
            request_id=request_id,
            action_type=ActionType.APPROVE,
            user_id=approver_id,
            user_name=approver_name,
            comment=comment,
            level=request.current_level,
        )
        request.actions.append(action)
        request.approved_by.append(approver_id)

        # Retirer des approbateurs en attente
        if approver_id in request.pending_approvers:
            request.pending_approvers.remove(approver_id)

        # Vérifier si le niveau est complété
        rule = await self.get_rule(request.rule_id) if request.rule_id else None
        level_completed = self._is_level_completed(request, rule)

        if level_completed:
            if request.current_level >= request.total_levels:
                # Toutes les approbations obtenues
                request.status = ApprovalStatus.APPROVED
                request.completed_at = datetime.now()
                logger.info(f"Demande {request_id} approuvée")
            else:
                # Passer au niveau suivant
                request.current_level += 1
                if rule and len(rule.levels) >= request.current_level:
                    next_level = rule.levels[request.current_level - 1]
                    request.pending_approvers = next_level.approvers.copy()

        request.updated_at = datetime.now()
        return request

    async def reject(
        self,
        request_id: str,
        rejector_id: str,
        rejector_name: Optional[str] = None,
        reason: str = "",
    ) -> Optional[ApprovalRequest]:
        """Rejette une demande."""
        request = await self.get_request(request_id)
        if not request or request.status != ApprovalStatus.PENDING:
            return None

        # Vérifier que l'utilisateur peut rejeter
        can_approve = await self._can_user_approve(request, rejector_id)
        if not can_approve:
            return None

        action = ApprovalAction(
            id=str(uuid.uuid4()),
            request_id=request_id,
            action_type=ActionType.REJECT,
            user_id=rejector_id,
            user_name=rejector_name,
            comment=reason,
            level=request.current_level,
        )
        request.actions.append(action)

        request.status = ApprovalStatus.REJECTED
        request.rejected_by = rejector_id
        request.rejection_reason = reason
        request.completed_at = datetime.now()
        request.updated_at = datetime.now()

        logger.info(f"Demande {request_id} rejetée par {rejector_id}: {reason}")
        return request

    async def add_comment(
        self,
        request_id: str,
        user_id: str,
        user_name: Optional[str] = None,
        comment: str = "",
    ) -> Optional[ApprovalRequest]:
        """Ajoute un commentaire."""
        request = await self.get_request(request_id)
        if not request:
            return None

        action = ApprovalAction(
            id=str(uuid.uuid4()),
            request_id=request_id,
            action_type=ActionType.COMMENT,
            user_id=user_id,
            user_name=user_name,
            comment=comment,
            level=request.current_level,
        )
        request.actions.append(action)
        request.updated_at = datetime.now()

        return request

    async def escalate(
        self,
        request_id: str,
        escalator_id: str,
        reason: Optional[str] = None,
    ) -> Optional[ApprovalRequest]:
        """Escalade une demande au niveau supérieur."""
        request = await self.get_request(request_id)
        if not request or request.status != ApprovalStatus.PENDING:
            return None

        if request.current_level >= request.total_levels:
            return request  # Déjà au niveau max

        action = ApprovalAction(
            id=str(uuid.uuid4()),
            request_id=request_id,
            action_type=ActionType.ESCALATE,
            user_id=escalator_id,
            comment=reason,
            level=request.current_level,
        )
        request.actions.append(action)

        # Passer au niveau suivant
        request.current_level += 1
        request.status = ApprovalStatus.ESCALATED

        rule = await self.get_rule(request.rule_id) if request.rule_id else None
        if rule and len(rule.levels) >= request.current_level:
            next_level = rule.levels[request.current_level - 1]
            request.pending_approvers = next_level.approvers.copy()

        request.status = ApprovalStatus.PENDING
        request.updated_at = datetime.now()

        logger.info(f"Demande {request_id} escaladée au niveau {request.current_level}")
        return request

    async def cancel(
        self,
        request_id: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> Optional[ApprovalRequest]:
        """Annule une demande."""
        request = await self.get_request(request_id)
        if not request or request.status != ApprovalStatus.PENDING:
            return None

        # Seul le demandeur peut annuler
        if request.requestor_id != user_id:
            return None

        request.status = ApprovalStatus.CANCELLED
        request.metadata["cancel_reason"] = reason
        request.completed_at = datetime.now()
        request.updated_at = datetime.now()

        logger.info(f"Demande {request_id} annulée")
        return request

    def _is_level_completed(
        self,
        request: ApprovalRequest,
        rule: Optional[ApprovalRule],
    ) -> bool:
        """Vérifie si le niveau actuel est complété."""
        if not rule or not rule.levels:
            return len(request.approved_by) >= 1

        current_level_config = next(
            (l for l in rule.levels if l.level == request.current_level),
            None
        )

        if not current_level_config:
            return True

        # Compter les approbations pour ce niveau
        level_approvals = sum(
            1 for a in request.actions
            if a.action_type == ActionType.APPROVE and a.level == request.current_level
        )

        return level_approvals >= current_level_config.min_approvers

    async def _can_user_approve(
        self,
        request: ApprovalRequest,
        user_id: str,
    ) -> bool:
        """Vérifie si un utilisateur peut approuver."""
        if user_id in request.pending_approvers:
            return True

        # Vérifier les délégations
        principals = await self._get_delegation_principals(user_id)
        return any(p in request.pending_approvers for p in principals)

    # =========================================================================
    # DELEGATIONS
    # =========================================================================

    async def create_delegation(
        self,
        delegator_id: str,
        delegator_name: str,
        delegate_id: str,
        delegate_name: str,
        document_types: list[DocumentType],
        max_amount: Optional[Decimal] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        reason: Optional[str] = None,
    ) -> Delegation:
        """Crée une délégation de pouvoir."""
        delegation = Delegation(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            delegator_id=delegator_id,
            delegator_name=delegator_name,
            delegate_id=delegate_id,
            delegate_name=delegate_name,
            document_types=document_types,
            max_amount=max_amount,
            start_date=start_date or datetime.now(),
            end_date=end_date,
            reason=reason,
        )

        self._delegations[delegation.id] = delegation

        logger.info(f"Délégation créée: {delegator_id} → {delegate_id}")
        return delegation

    async def list_delegations(
        self,
        delegator_id: Optional[str] = None,
        delegate_id: Optional[str] = None,
        active_only: bool = True,
    ) -> list[Delegation]:
        """Liste les délégations."""
        delegations = [
            d for d in self._delegations.values()
            if d.tenant_id == self.tenant_id
        ]

        if delegator_id:
            delegations = [d for d in delegations if d.delegator_id == delegator_id]

        if delegate_id:
            delegations = [d for d in delegations if d.delegate_id == delegate_id]

        if active_only:
            now = datetime.now()
            delegations = [
                d for d in delegations
                if d.is_active
                and d.start_date <= now
                and (d.end_date is None or d.end_date >= now)
            ]

        return delegations

    async def revoke_delegation(self, delegation_id: str) -> bool:
        """Révoque une délégation."""
        delegation = self._delegations.get(delegation_id)
        if not delegation or delegation.tenant_id != self.tenant_id:
            return False

        delegation.is_active = False
        delegation.end_date = datetime.now()

        logger.info(f"Délégation révoquée: {delegation_id}")
        return True

    async def _get_delegation_principals(self, user_id: str) -> list[str]:
        """Récupère les utilisateurs pour lesquels user_id a délégation."""
        delegations = await self.list_delegations(delegate_id=user_id, active_only=True)
        return [d.delegator_id for d in delegations]

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ApprovalStats:
        """Statistiques d'approbation."""
        requests = [
            r for r in self._requests.values()
            if r.tenant_id == self.tenant_id
        ]

        if start_date:
            requests = [r for r in requests if r.created_at >= start_date]
        if end_date:
            requests = [r for r in requests if r.created_at <= end_date]

        total = len(requests)
        pending = len([r for r in requests if r.status == ApprovalStatus.PENDING])
        approved = len([r for r in requests if r.status == ApprovalStatus.APPROVED])
        rejected = len([r for r in requests if r.status == ApprovalStatus.REJECTED])

        # Calcul du temps moyen d'approbation
        completed = [r for r in requests if r.completed_at and r.status == ApprovalStatus.APPROVED]
        if completed:
            avg_time = sum(
                (r.completed_at - r.created_at).total_seconds() / 3600
                for r in completed
            ) / len(completed)
        else:
            avg_time = 0

        # Par type de document
        by_type = {}
        for doc_type in DocumentType:
            by_type[doc_type.value] = len([
                r for r in requests if r.document_type == doc_type
            ])

        # Par niveau
        by_level = {}
        for r in requests:
            level = str(r.current_level)
            by_level[level] = by_level.get(level, 0) + 1

        return ApprovalStats(
            total_requests=total,
            pending_requests=pending,
            approved_requests=approved,
            rejected_requests=rejected,
            average_approval_time_hours=avg_time,
            approval_rate=approved / total * 100 if total > 0 else 0,
            by_document_type=by_type,
            by_level=by_level,
        )

    async def get_user_stats(self, user_id: str) -> dict:
        """Statistiques pour un utilisateur."""
        requests = [
            r for r in self._requests.values()
            if r.tenant_id == self.tenant_id
        ]

        approved_count = sum(
            1 for r in requests
            if user_id in r.approved_by
        )

        rejected_count = sum(
            1 for r in requests
            if r.rejected_by == user_id
        )

        pending_count = len(await self.get_pending_for_user(user_id))

        return {
            "user_id": user_id,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "pending_count": pending_count,
            "total_actions": approved_count + rejected_count,
        }
