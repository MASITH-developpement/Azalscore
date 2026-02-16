"""
AZALS MODULE M7 - Certification Service
========================================

Gestion des certifications qualité.
"""

import logging
from datetime import date
from typing import Optional, Tuple, List

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from app.modules.quality.models import (
    Certification,
    CertificationAudit,
    CertificationStatus,
)
from app.modules.quality.schemas import (
    CertificationCreate,
    CertificationUpdate,
    CertificationAuditCreate,
    CertificationAuditUpdate,
)
from .base import BaseQualityService

logger = logging.getLogger(__name__)


class CertificationService(BaseQualityService[Certification]):
    """Service de gestion des certifications."""

    model = Certification

    def create(self, data: CertificationCreate) -> Certification:
        """Crée une certification."""
        certification = Certification(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            standard=data.standard,
            standard_version=data.standard_version,
            scope=data.scope,
            certification_body=data.certification_body,
            certification_body_accreditation=data.certification_body_accreditation,
            initial_certification_date=data.initial_certification_date,
            status=CertificationStatus.PLANNED,
            manager_id=data.manager_id,
            annual_cost=data.annual_cost,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(certification)
        self.db.commit()
        self.db.refresh(certification)
        return certification

    def get(self, cert_id: int) -> Optional[Certification]:
        """Récupère une certification par ID."""
        return self._get_by_id(cert_id, options=[
            joinedload(Certification.audits)
        ])

    def get_by_code(self, code: str) -> Optional[Certification]:
        """Récupère une certification par code."""
        return self._base_query().options(
            joinedload(Certification.audits)
        ).filter(Certification.code == code).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[CertificationStatus] = None,
        active_only: bool = True,
        search: Optional[str] = None,
    ) -> Tuple[List[Certification], int]:
        """Liste les certifications."""
        query = self._base_query()

        if status:
            query = query.filter(Certification.status == status)
        if active_only:
            query = query.filter(
                Certification.status.in_([
                    CertificationStatus.ACTIVE,
                    CertificationStatus.PLANNED,
                    CertificationStatus.IN_PROGRESS
                ])
            )

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Certification.code.ilike(search_filter),
                    Certification.name.ilike(search_filter),
                    Certification.standard.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(
            joinedload(Certification.audits)
        ).order_by(Certification.code).offset(skip).limit(limit).all()

        return items, total

    def update(self, cert_id: int, data: CertificationUpdate) -> Optional[Certification]:
        """Met à jour une certification."""
        cert = self.get(cert_id)
        if not cert:
            return None

        update_data = data.model_dump(exclude_unset=True)
        return self._update(cert, update_data)

    # ========================================================================
    # WORKFLOW
    # ========================================================================

    def activate(self, cert_id: int, certificate_number: str, issue_date: date, expiry_date: date) -> Optional[Certification]:
        """Active une certification."""
        cert = self.get(cert_id)
        if not cert:
            return None

        cert.status = CertificationStatus.ACTIVE
        cert.certificate_number = certificate_number
        cert.certificate_issue_date = issue_date
        cert.certificate_expiry_date = expiry_date
        self.db.commit()
        self.db.refresh(cert)
        return cert

    def suspend(self, cert_id: int, reason: str = None) -> Optional[Certification]:
        """Suspend une certification."""
        cert = self.get(cert_id)
        if not cert:
            return None

        cert.status = CertificationStatus.SUSPENDED
        if reason:
            cert.notes = f"{cert.notes or ''}\n[Suspension] {reason}".strip()
        self.db.commit()
        self.db.refresh(cert)
        return cert

    def withdraw(self, cert_id: int, reason: str = None) -> Optional[Certification]:
        """Retire une certification."""
        cert = self.get(cert_id)
        if not cert:
            return None

        cert.status = CertificationStatus.WITHDRAWN
        if reason:
            cert.notes = f"{cert.notes or ''}\n[Retrait] {reason}".strip()
        self.db.commit()
        self.db.refresh(cert)
        return cert

    def renew(self, cert_id: int, new_expiry_date: date) -> Optional[Certification]:
        """Renouvelle une certification."""
        cert = self.get(cert_id)
        if not cert:
            return None

        cert.certificate_expiry_date = new_expiry_date
        cert.last_renewal_date = date.today()
        cert.status = CertificationStatus.ACTIVE
        self.db.commit()
        self.db.refresh(cert)
        return cert

    # ========================================================================
    # AUDITS DE CERTIFICATION
    # ========================================================================

    def add_audit(self, cert_id: int, data: CertificationAuditCreate) -> Optional[CertificationAudit]:
        """Ajoute un audit à une certification."""
        cert = self.get(cert_id)
        if not cert:
            return None

        audit = CertificationAudit(
            tenant_id=self.tenant_id,
            certification_id=cert_id,
            audit_type=data.audit_type,
            planned_date=data.planned_date,
            auditor_name=data.auditor_name,
            scope=data.scope,
            status="PLANNED",
            created_by=self.user_id,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def update_audit(self, audit_id: int, data: CertificationAuditUpdate) -> Optional[CertificationAudit]:
        """Met à jour un audit de certification."""
        audit = self.db.query(CertificationAudit).filter(
            CertificationAudit.id == audit_id,
            CertificationAudit.tenant_id == self.tenant_id
        ).first()
        if not audit:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(audit, field):
                setattr(audit, field, value)

        self.db.commit()
        self.db.refresh(audit)
        return audit

    def complete_audit(self, audit_id: int, result: str, findings_count: int = 0) -> Optional[CertificationAudit]:
        """Termine un audit de certification."""
        audit = self.db.query(CertificationAudit).filter(
            CertificationAudit.id == audit_id,
            CertificationAudit.tenant_id == self.tenant_id
        ).first()
        if not audit:
            return None

        audit.status = "COMPLETED"
        audit.actual_date = date.today()
        audit.result = result
        audit.findings_count = findings_count
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def get_expiring_certifications(self, days: int = 90) -> List[Certification]:
        """Récupère les certifications qui expirent bientôt."""
        from datetime import timedelta
        expiry_threshold = date.today() + timedelta(days=days)

        return self._base_query().filter(
            Certification.status == CertificationStatus.ACTIVE,
            Certification.certificate_expiry_date <= expiry_threshold
        ).order_by(Certification.certificate_expiry_date).all()
