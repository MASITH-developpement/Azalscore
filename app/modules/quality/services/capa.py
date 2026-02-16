"""
AZALS MODULE M7 - CAPA Service
===============================

Gestion des CAPA (Corrective and Preventive Actions).
"""

import logging
from datetime import date, datetime
from typing import Optional, Tuple, List

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from app.modules.quality.models import (
    CAPA,
    CAPAAction,
    CAPAType,
    CAPAStatus,
)
from app.modules.quality.schemas import (
    CAPACreate,
    CAPAUpdate,
    CAPAClose,
    CAPAActionCreate,
    CAPAActionUpdate,
)
from .base import BaseQualityService

logger = logging.getLogger(__name__)


class CAPAService(BaseQualityService[CAPA]):
    """Service de gestion des CAPA."""

    model = CAPA

    def _generate_capa_number(self) -> str:
        """Génère un numéro CAPA."""
        year = datetime.now().year
        count = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id,
            func.extract("year", CAPA.created_at) == year
        ).scalar() or 0
        return f"CAPA-{year}-{count + 1:04d}"

    def create(self, data: CAPACreate) -> CAPA:
        """Crée un CAPA."""
        capa_number = self._generate_capa_number()
        logger.info(
            "Creating CAPA | tenant=%s user=%s type=%s priority=%s capa_number=%s",
            self.tenant_id, self.user_id, data.capa_type, data.priority, capa_number
        )

        capa = CAPA(
            tenant_id=self.tenant_id,
            capa_number=capa_number,
            title=data.title,
            description=data.description,
            capa_type=data.capa_type,
            source_type=data.source_type,
            source_reference=data.source_reference,
            source_id=data.source_id,
            status=CAPAStatus.DRAFT,
            priority=data.priority,
            open_date=data.open_date,
            target_close_date=data.target_close_date,
            owner_id=data.owner_id,
            department=data.department,
            problem_statement=data.problem_statement,
            immediate_containment=data.immediate_containment,
            effectiveness_criteria=data.effectiveness_criteria,
            created_by=self.user_id,
        )
        self.db.add(capa)
        self.db.commit()
        self.db.refresh(capa)

        logger.info("CAPA created | capa_id=%s capa_number=%s", capa.id, capa.capa_number)
        return capa

    def get(self, capa_id: int) -> Optional[CAPA]:
        """Récupère un CAPA par ID."""
        return self._get_by_id(capa_id, options=[
            joinedload(CAPA.actions)
        ])

    def get_by_number(self, capa_number: str) -> Optional[CAPA]:
        """Récupère un CAPA par numéro."""
        return self._base_query().options(
            joinedload(CAPA.actions)
        ).filter(CAPA.capa_number == capa_number).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        capa_type: Optional[CAPAType] = None,
        status: Optional[CAPAStatus] = None,
        priority: Optional[str] = None,
        owner_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[CAPA], int]:
        """Liste les CAPA."""
        query = self._base_query()

        if capa_type:
            query = query.filter(CAPA.capa_type == capa_type)
        if status:
            query = query.filter(CAPA.status == status)
        if priority:
            query = query.filter(CAPA.priority == priority)
        if owner_id:
            query = query.filter(CAPA.owner_id == owner_id)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    CAPA.capa_number.ilike(search_filter),
                    CAPA.title.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(
            joinedload(CAPA.actions)
        ).order_by(CAPA.open_date.desc()).offset(skip).limit(limit).all()

        return items, total

    def update(self, capa_id: int, data: CAPAUpdate) -> Optional[CAPA]:
        """Met à jour un CAPA."""
        capa = self.get(capa_id)
        if not capa:
            return None

        update_data = data.model_dump(exclude_unset=True)
        return self._update(capa, update_data)

    # ========================================================================
    # WORKFLOW
    # ========================================================================

    def open(self, capa_id: int) -> Optional[CAPA]:
        """Ouvre un CAPA."""
        capa = self.get(capa_id)
        if not capa or capa.status != CAPAStatus.DRAFT:
            return None

        capa.status = CAPAStatus.OPEN
        self.db.commit()
        self.db.refresh(capa)
        return capa

    def start_analysis(self, capa_id: int) -> Optional[CAPA]:
        """Démarre l'analyse d'un CAPA."""
        capa = self.get(capa_id)
        if not capa:
            return None

        capa.status = CAPAStatus.ANALYSIS
        self.db.commit()
        self.db.refresh(capa)
        return capa

    def close(self, capa_id: int, data: CAPAClose) -> Optional[CAPA]:
        """Clôture un CAPA."""
        capa = self.get(capa_id)
        if not capa:
            return None

        capa.effectiveness_verified = data.effectiveness_verified
        capa.effectiveness_result = data.effectiveness_result
        capa.effectiveness_date = date.today()
        capa.verified_by_id = self.user_id
        capa.closure_comments = data.closure_comments
        capa.actual_close_date = date.today()
        capa.closed_by_id = self.user_id

        if data.effectiveness_verified:
            capa.status = CAPAStatus.CLOSED_EFFECTIVE
        else:
            capa.status = CAPAStatus.CLOSED_INEFFECTIVE

        self.db.commit()
        self.db.refresh(capa)
        return capa

    # ========================================================================
    # ACTIONS CAPA
    # ========================================================================

    def add_action(self, capa_id: int, data: CAPAActionCreate) -> Optional[CAPAAction]:
        """Ajoute une action à un CAPA."""
        capa = self.get(capa_id)
        if not capa:
            return None

        action_count = self.db.query(func.count(CAPAAction.id)).filter(
            CAPAAction.capa_id == capa_id
        ).scalar() or 0

        action = CAPAAction(
            tenant_id=self.tenant_id,
            capa_id=capa_id,
            action_number=action_count + 1,
            action_type=data.action_type,
            description=data.description,
            responsible_id=data.responsible_id,
            planned_date=data.planned_date,
            due_date=data.due_date,
            status="PLANNED",
            verification_required=data.verification_required,
            estimated_cost=data.estimated_cost,
            created_by=self.user_id,
        )
        self.db.add(action)

        # Mettre à jour statut CAPA
        if capa.status in [CAPAStatus.DRAFT, CAPAStatus.OPEN, CAPAStatus.ANALYSIS]:
            capa.status = CAPAStatus.ACTION_PLANNING

        self.db.commit()
        self.db.refresh(action)
        return action

    def update_action(self, action_id: int, data: CAPAActionUpdate) -> Optional[CAPAAction]:
        """Met à jour une action CAPA."""
        action = self.db.query(CAPAAction).filter(
            CAPAAction.id == action_id,
            CAPAAction.tenant_id == self.tenant_id
        ).first()
        if not action:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(action, field):
                setattr(action, field, value)

        self.db.commit()
        self.db.refresh(action)
        return action

    def complete_action(self, action_id: int) -> Optional[CAPAAction]:
        """Marque une action CAPA comme terminée."""
        action = self.db.query(CAPAAction).filter(
            CAPAAction.id == action_id,
            CAPAAction.tenant_id == self.tenant_id
        ).first()
        if not action:
            return None

        action.status = "COMPLETED"
        action.actual_date = date.today()
        action.completed_by_id = self.user_id
        self.db.commit()
        self.db.refresh(action)
        return action
