"""
AZALS MODULE M7 - Claim Service
================================

Gestion des réclamations clients.
"""

import logging
from datetime import date, datetime
from typing import Optional, Tuple, List

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from app.modules.quality.models import (
    CustomerClaim,
    ClaimAction,
    ClaimStatus,
)
from app.modules.quality.schemas import (
    ClaimCreate,
    ClaimUpdate,
    ClaimRespond,
    ClaimResolve,
    ClaimClose,
    ClaimActionCreate,
)
from .base import BaseQualityService

logger = logging.getLogger(__name__)


class ClaimService(BaseQualityService[CustomerClaim]):
    """Service de gestion des réclamations clients."""

    model = CustomerClaim

    def _generate_claim_number(self) -> str:
        """Génère un numéro de réclamation."""
        year = datetime.now().year
        count = self.db.query(func.count(CustomerClaim.id)).filter(
            CustomerClaim.tenant_id == self.tenant_id,
            func.extract("year", CustomerClaim.created_at) == year
        ).scalar() or 0
        return f"REC-{year}-{count + 1:05d}"

    def create(self, data: ClaimCreate) -> CustomerClaim:
        """Crée une réclamation client."""
        claim_number = self._generate_claim_number()
        logger.info(
            "Creating customer claim | tenant=%s user=%s customer_id=%s type=%s claim_number=%s",
            self.tenant_id, self.user_id, data.customer_id, data.claim_type, claim_number
        )

        claim = CustomerClaim(
            tenant_id=self.tenant_id,
            claim_number=claim_number,
            title=data.title,
            description=data.description,
            customer_id=data.customer_id,
            customer_contact=data.customer_contact,
            customer_reference=data.customer_reference,
            received_date=data.received_date,
            received_via=data.received_via,
            received_by_id=self.user_id,
            product_id=data.product_id,
            order_reference=data.order_reference,
            invoice_reference=data.invoice_reference,
            lot_number=data.lot_number,
            quantity_affected=data.quantity_affected,
            claim_type=data.claim_type,
            severity=data.severity,
            priority=data.priority,
            status=ClaimStatus.RECEIVED,
            owner_id=data.owner_id,
            response_due_date=data.response_due_date,
            claim_amount=data.claim_amount,
            created_by=self.user_id,
        )
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)

        logger.info("Customer claim created | claim_id=%s claim_number=%s", claim.id, claim.claim_number)
        return claim

    def get(self, claim_id: int) -> Optional[CustomerClaim]:
        """Récupère une réclamation par ID."""
        return self._get_by_id(claim_id, options=[
            joinedload(CustomerClaim.actions)
        ])

    def get_by_number(self, claim_number: str) -> Optional[CustomerClaim]:
        """Récupère une réclamation par numéro."""
        return self._base_query().options(
            joinedload(CustomerClaim.actions)
        ).filter(CustomerClaim.claim_number == claim_number).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[ClaimStatus] = None,
        customer_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[CustomerClaim], int]:
        """Liste les réclamations."""
        query = self._base_query()

        if status:
            query = query.filter(CustomerClaim.status == status)
        if customer_id:
            query = query.filter(CustomerClaim.customer_id == customer_id)
        if date_from:
            query = query.filter(CustomerClaim.received_date >= date_from)
        if date_to:
            query = query.filter(CustomerClaim.received_date <= date_to)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    CustomerClaim.claim_number.ilike(search_filter),
                    CustomerClaim.title.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(
            joinedload(CustomerClaim.actions)
        ).order_by(
            CustomerClaim.received_date.desc()
        ).offset(skip).limit(limit).all()

        return items, total

    def update(self, claim_id: int, data: ClaimUpdate) -> Optional[CustomerClaim]:
        """Met à jour une réclamation."""
        claim = self.get(claim_id)
        if not claim:
            return None

        update_data = data.model_dump(exclude_unset=True)
        return self._update(claim, update_data)

    # ========================================================================
    # WORKFLOW
    # ========================================================================

    def acknowledge(self, claim_id: int) -> Optional[CustomerClaim]:
        """Accuse réception d'une réclamation."""
        claim = self.get(claim_id)
        if not claim:
            return None

        claim.status = ClaimStatus.ACKNOWLEDGED
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def respond(self, claim_id: int, data: ClaimRespond) -> Optional[CustomerClaim]:
        """Répond à une réclamation."""
        claim = self.get(claim_id)
        if not claim:
            return None

        claim.response_content = data.response_content
        claim.response_date = date.today()
        claim.response_by_id = self.user_id
        claim.status = ClaimStatus.RESPONSE_SENT

        self.db.commit()
        self.db.refresh(claim)
        return claim

    def resolve(self, claim_id: int, data: ClaimResolve) -> Optional[CustomerClaim]:
        """Résout une réclamation."""
        claim = self.get(claim_id)
        if not claim:
            return None

        claim.resolution_type = data.resolution_type
        claim.resolution_description = data.resolution_description
        claim.accepted_amount = data.accepted_amount
        claim.resolution_date = date.today()
        claim.status = ClaimStatus.RESOLVED

        self.db.commit()
        self.db.refresh(claim)
        return claim

    def close(self, claim_id: int, data: ClaimClose) -> Optional[CustomerClaim]:
        """Clôture une réclamation."""
        claim = self.get(claim_id)
        if not claim:
            return None

        claim.customer_satisfied = data.customer_satisfied
        claim.satisfaction_feedback = data.satisfaction_feedback
        claim.closed_date = date.today()
        claim.closed_by_id = self.user_id
        claim.status = ClaimStatus.CLOSED

        self.db.commit()
        self.db.refresh(claim)
        return claim

    # ========================================================================
    # ACTIONS
    # ========================================================================

    def add_action(self, claim_id: int, data: ClaimActionCreate) -> Optional[ClaimAction]:
        """Ajoute une action à une réclamation."""
        claim = self.get(claim_id)
        if not claim:
            return None

        action_count = self.db.query(func.count(ClaimAction.id)).filter(
            ClaimAction.claim_id == claim_id
        ).scalar() or 0

        action = ClaimAction(
            tenant_id=self.tenant_id,
            claim_id=claim_id,
            action_number=action_count + 1,
            action_type=data.action_type,
            description=data.description,
            responsible_id=data.responsible_id,
            due_date=data.due_date,
            status="PLANNED",
            created_by=self.user_id,
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def complete_action(self, action_id: int) -> Optional[ClaimAction]:
        """Marque une action comme terminée."""
        action = self.db.query(ClaimAction).filter(
            ClaimAction.id == action_id,
            ClaimAction.tenant_id == self.tenant_id
        ).first()
        if not action:
            return None

        action.status = "COMPLETED"
        action.completed_date = date.today()
        action.completed_by_id = self.user_id
        self.db.commit()
        self.db.refresh(action)
        return action
