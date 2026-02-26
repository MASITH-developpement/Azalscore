"""
AZALS MODULE M7 - Audit Service
================================

Gestion des audits qualité.
"""
from __future__ import annotations


import logging
from datetime import date, datetime
from typing import Optional, Tuple, List

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from app.modules.quality.models import (
    QualityAudit,
    AuditFinding,
    AuditType,
    AuditStatus,
    FindingSeverity,
)
from app.modules.quality.schemas import (
    AuditCreate,
    AuditUpdate,
    AuditClose,
    AuditFindingCreate,
    AuditFindingUpdate,
)
from .base import BaseQualityService

logger = logging.getLogger(__name__)


class AuditService(BaseQualityService[QualityAudit]):
    """Service de gestion des audits qualité."""

    model = QualityAudit

    def _generate_audit_number(self) -> str:
        """Génère un numéro d'audit."""
        year = datetime.now().year
        count = self.db.query(func.count(QualityAudit.id)).filter(
            QualityAudit.tenant_id == self.tenant_id,
            func.extract("year", QualityAudit.created_at) == year
        ).scalar() or 0
        return f"AUD-{year}-{count + 1:04d}"

    def create(self, data: AuditCreate) -> QualityAudit:
        """Crée un audit."""
        audit = QualityAudit(
            tenant_id=self.tenant_id,
            audit_number=self._generate_audit_number(),
            title=data.title,
            description=data.description,
            audit_type=data.audit_type,
            reference_standard=data.reference_standard,
            reference_version=data.reference_version,
            audit_scope=data.audit_scope,
            planned_date=data.planned_date,
            planned_end_date=data.planned_end_date,
            status=AuditStatus.PLANNED,
            lead_auditor_id=data.lead_auditor_id,
            auditors=data.auditors,
            audited_entity=data.audited_entity,
            audited_department=data.audited_department,
            auditee_contact_id=data.auditee_contact_id,
            supplier_id=data.supplier_id,
            created_by=self.user_id,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def get(self, audit_id: int) -> Optional[QualityAudit]:
        """Récupère un audit par ID."""
        return self._get_by_id(audit_id, options=[
            joinedload(QualityAudit.findings)
        ])

    def get_by_number(self, audit_number: str) -> Optional[QualityAudit]:
        """Récupère un audit par numéro."""
        return self._base_query().options(
            joinedload(QualityAudit.findings)
        ).filter(QualityAudit.audit_number == audit_number).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        audit_type: Optional[AuditType] = None,
        status: Optional[AuditStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[QualityAudit], int]:
        """Liste les audits."""
        query = self._base_query()

        if audit_type:
            query = query.filter(QualityAudit.audit_type == audit_type)
        if status:
            query = query.filter(QualityAudit.status == status)
        if date_from:
            query = query.filter(QualityAudit.planned_date >= date_from)
        if date_to:
            query = query.filter(QualityAudit.planned_date <= date_to)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    QualityAudit.audit_number.ilike(search_filter),
                    QualityAudit.title.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(
            joinedload(QualityAudit.findings)
        ).order_by(
            QualityAudit.planned_date.desc()
        ).offset(skip).limit(limit).all()

        return items, total

    def update(self, audit_id: int, data: AuditUpdate) -> Optional[QualityAudit]:
        """Met à jour un audit."""
        audit = self.get(audit_id)
        if not audit:
            return None

        update_data = data.model_dump(exclude_unset=True)
        return self._update(audit, update_data)

    # ========================================================================
    # WORKFLOW
    # ========================================================================

    def start(self, audit_id: int) -> Optional[QualityAudit]:
        """Démarre un audit."""
        audit = self.get(audit_id)
        if not audit:
            return None

        audit.status = AuditStatus.IN_PROGRESS
        audit.actual_date = date.today()
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def close(self, audit_id: int, data: AuditClose) -> Optional[QualityAudit]:
        """Clôture un audit."""
        audit = self.get(audit_id)
        if not audit:
            return None

        audit.status = AuditStatus.CLOSED
        audit.actual_end_date = date.today()
        audit.closed_date = date.today()
        audit.closed_by_id = self.user_id
        audit.audit_conclusion = data.audit_conclusion
        audit.recommendation = data.recommendation
        audit.report_date = date.today()

        self.db.commit()
        self.db.refresh(audit)
        return audit

    # ========================================================================
    # CONSTATS (FINDINGS)
    # ========================================================================

    def add_finding(self, audit_id: int, data: AuditFindingCreate) -> Optional[AuditFinding]:
        """Ajoute un constat à un audit."""
        audit = self.get(audit_id)
        if not audit:
            return None

        finding_count = self.db.query(func.count(AuditFinding.id)).filter(
            AuditFinding.audit_id == audit_id
        ).scalar() or 0

        finding = AuditFinding(
            tenant_id=self.tenant_id,
            audit_id=audit_id,
            finding_number=finding_count + 1,
            title=data.title,
            description=data.description,
            severity=data.severity,
            category=data.category,
            clause_reference=data.clause_reference,
            process_reference=data.process_reference,
            evidence=data.evidence,
            risk_description=data.risk_description,
            capa_required=data.capa_required,
            action_due_date=data.action_due_date,
            status="OPEN",
            created_by=self.user_id,
        )
        self.db.add(finding)

        # Mettre à jour les compteurs de l'audit
        audit.total_findings = (audit.total_findings or 0) + 1
        if data.severity == FindingSeverity.CRITICAL:
            audit.critical_findings = (audit.critical_findings or 0) + 1
        elif data.severity == FindingSeverity.MAJOR:
            audit.major_findings = (audit.major_findings or 0) + 1
        elif data.severity == FindingSeverity.MINOR:
            audit.minor_findings = (audit.minor_findings or 0) + 1
        else:
            audit.observations = (audit.observations or 0) + 1

        self.db.commit()
        self.db.refresh(finding)
        return finding

    def update_finding(self, finding_id: int, data: AuditFindingUpdate) -> Optional[AuditFinding]:
        """Met à jour un constat."""
        finding = self.db.query(AuditFinding).filter(
            AuditFinding.id == finding_id,
            AuditFinding.tenant_id == self.tenant_id
        ).first()
        if not finding:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(finding, field):
                setattr(finding, field, value)

        self.db.commit()
        self.db.refresh(finding)
        return finding

    def close_finding(self, finding_id: int, resolution: str = None) -> Optional[AuditFinding]:
        """Clôture un constat."""
        finding = self.db.query(AuditFinding).filter(
            AuditFinding.id == finding_id,
            AuditFinding.tenant_id == self.tenant_id
        ).first()
        if not finding:
            return None

        finding.status = "CLOSED"
        finding.closed_date = date.today()
        finding.closed_by_id = self.user_id
        if resolution:
            finding.resolution = resolution

        self.db.commit()
        self.db.refresh(finding)
        return finding
