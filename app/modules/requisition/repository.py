"""
Repository Requisition / Demandes d'achat
=========================================
Pattern Repository avec tenant isolation obligatoire.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from .models import (
    CatalogCategory, CatalogItem, CatalogItemStatus,
    PreferredVendor, BudgetAllocation,
    Requisition, RequisitionStatus, RequisitionLine, LineStatus,
    ApprovalStep, ApprovalStatus, RequisitionComment,
    RequisitionTemplate
)


class CatalogCategoryRepository:
    """Repository pour CatalogCategory avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base TOUJOURS filtrée par tenant."""
        return self.db.query(CatalogCategory).filter(
            CatalogCategory.tenant_id == self.tenant_id,
            CatalogCategory.is_deleted == False
        )

    def get_by_id(self, category_id: UUID) -> Optional[CatalogCategory]:
        return self._base_query().filter(CatalogCategory.id == category_id).first()

    def get_by_code(self, code: str) -> Optional[CatalogCategory]:
        return self._base_query().filter(CatalogCategory.code == code).first()

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        parent_id: Optional[UUID] = None
    ) -> Tuple[List[CatalogCategory], int, int]:
        query = self._base_query()

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    CatalogCategory.code.ilike(search_filter),
                    CatalogCategory.name.ilike(search_filter)
                )
            )

        if is_active is not None:
            query = query.filter(CatalogCategory.is_active == is_active)

        if parent_id:
            query = query.filter(CatalogCategory.parent_id == parent_id)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(CatalogCategory.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, category: CatalogCategory) -> CatalogCategory:
        category.tenant_id = self.tenant_id
        self.db.add(category)
        self.db.flush()
        return category

    def update(self, category: CatalogCategory) -> CatalogCategory:
        category.version += 1
        self.db.flush()
        return category

    def soft_delete(self, category_id: UUID, deleted_by: UUID) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False
        category.is_deleted = True
        category.deleted_at = datetime.utcnow()
        category.deleted_by = deleted_by
        self.db.flush()
        return True

    def restore(self, category_id: UUID) -> Optional[CatalogCategory]:
        category = self.db.query(CatalogCategory).filter(
            CatalogCategory.tenant_id == self.tenant_id,
            CatalogCategory.id == category_id,
            CatalogCategory.is_deleted == True
        ).first()
        if category:
            category.is_deleted = False
            category.deleted_at = None
            category.deleted_by = None
            self.db.flush()
        return category

    def autocomplete(self, search: str, limit: int = 10) -> List[dict]:
        categories = self._base_query().filter(
            CatalogCategory.is_active == True,
            or_(
                CatalogCategory.code.ilike(f"%{search}%"),
                CatalogCategory.name.ilike(f"%{search}%")
            )
        ).limit(limit).all()
        return [{"id": c.id, "code": c.code, "name": c.name} for c in categories]


class CatalogItemRepository:
    """Repository pour CatalogItem avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(CatalogItem).filter(
            CatalogItem.tenant_id == self.tenant_id,
            CatalogItem.is_deleted == False
        )

    def get_by_id(self, item_id: UUID) -> Optional[CatalogItem]:
        return self._base_query().filter(CatalogItem.id == item_id).first()

    def get_by_code(self, code: str) -> Optional[CatalogItem]:
        return self._base_query().filter(CatalogItem.code == code).first()

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[CatalogItemStatus] = None,
        category_id: Optional[UUID] = None,
        vendor_id: Optional[UUID] = None
    ) -> Tuple[List[CatalogItem], int, int]:
        query = self._base_query()

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    CatalogItem.code.ilike(search_filter),
                    CatalogItem.name.ilike(search_filter),
                    CatalogItem.description.ilike(search_filter)
                )
            )

        if status:
            query = query.filter(CatalogItem.status == status)

        if category_id:
            query = query.filter(CatalogItem.category_id == category_id)

        if vendor_id:
            query = query.filter(CatalogItem.preferred_vendor_id == vendor_id)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(CatalogItem.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, item: CatalogItem) -> CatalogItem:
        item.tenant_id = self.tenant_id
        self.db.add(item)
        self.db.flush()
        return item

    def update(self, item: CatalogItem) -> CatalogItem:
        item.version += 1
        self.db.flush()
        return item

    def soft_delete(self, item_id: UUID, deleted_by: UUID) -> bool:
        item = self.get_by_id(item_id)
        if not item:
            return False
        item.is_deleted = True
        item.deleted_at = datetime.utcnow()
        item.deleted_by = deleted_by
        self.db.flush()
        return True

    def restore(self, item_id: UUID) -> Optional[CatalogItem]:
        item = self.db.query(CatalogItem).filter(
            CatalogItem.tenant_id == self.tenant_id,
            CatalogItem.id == item_id,
            CatalogItem.is_deleted == True
        ).first()
        if item:
            item.is_deleted = False
            item.deleted_at = None
            item.deleted_by = None
            self.db.flush()
        return item

    def autocomplete(self, search: str, limit: int = 10) -> List[dict]:
        items = self._base_query().filter(
            CatalogItem.status == CatalogItemStatus.ACTIVE,
            or_(
                CatalogItem.code.ilike(f"%{search}%"),
                CatalogItem.name.ilike(f"%{search}%")
            )
        ).limit(limit).all()
        return [{"id": i.id, "code": i.code, "name": i.name, "unit_price": float(i.unit_price)} for i in items]


class PreferredVendorRepository:
    """Repository pour PreferredVendor avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(PreferredVendor).filter(
            PreferredVendor.tenant_id == self.tenant_id,
            PreferredVendor.is_deleted == False
        )

    def get_by_id(self, vendor_pref_id: UUID) -> Optional[PreferredVendor]:
        return self._base_query().filter(PreferredVendor.id == vendor_pref_id).first()

    def get_by_vendor_id(self, vendor_id: UUID) -> Optional[PreferredVendor]:
        return self._base_query().filter(PreferredVendor.vendor_id == vendor_id).first()

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        category_id: Optional[UUID] = None
    ) -> Tuple[List[PreferredVendor], int, int]:
        query = self._base_query()

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    PreferredVendor.vendor_code.ilike(search_filter),
                    PreferredVendor.vendor_name.ilike(search_filter)
                )
            )

        if is_active is not None:
            query = query.filter(PreferredVendor.is_active == is_active)

        if category_id:
            query = query.filter(PreferredVendor.category_ids.contains([category_id]))

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(PreferredVendor.vendor_name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def get_for_category(self, category_id: UUID) -> List[PreferredVendor]:
        return self._base_query().filter(
            PreferredVendor.is_active == True,
            PreferredVendor.category_ids.contains([category_id])
        ).order_by(PreferredVendor.rating.desc()).all()

    def create(self, vendor: PreferredVendor) -> PreferredVendor:
        vendor.tenant_id = self.tenant_id
        self.db.add(vendor)
        self.db.flush()
        return vendor

    def update(self, vendor: PreferredVendor) -> PreferredVendor:
        vendor.version += 1
        self.db.flush()
        return vendor

    def soft_delete(self, vendor_pref_id: UUID, deleted_by: UUID) -> bool:
        vendor = self.get_by_id(vendor_pref_id)
        if not vendor:
            return False
        vendor.is_deleted = True
        vendor.deleted_at = datetime.utcnow()
        vendor.deleted_by = deleted_by
        self.db.flush()
        return True


class BudgetAllocationRepository:
    """Repository pour BudgetAllocation avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(BudgetAllocation).filter(
            BudgetAllocation.tenant_id == self.tenant_id,
            BudgetAllocation.is_deleted == False
        )

    def get_by_id(self, allocation_id: UUID) -> Optional[BudgetAllocation]:
        return self._base_query().filter(BudgetAllocation.id == allocation_id).first()

    def get_for_department(
        self,
        department_id: UUID,
        fiscal_year: int
    ) -> Optional[BudgetAllocation]:
        return self._base_query().filter(
            BudgetAllocation.department_id == department_id,
            BudgetAllocation.fiscal_year == fiscal_year,
            BudgetAllocation.is_active == True
        ).first()

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        fiscal_year: Optional[int] = None,
        department_id: Optional[UUID] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[BudgetAllocation], int, int]:
        query = self._base_query()

        if fiscal_year:
            query = query.filter(BudgetAllocation.fiscal_year == fiscal_year)

        if department_id:
            query = query.filter(BudgetAllocation.department_id == department_id)

        if is_active is not None:
            query = query.filter(BudgetAllocation.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(BudgetAllocation.department_name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, allocation: BudgetAllocation) -> BudgetAllocation:
        allocation.tenant_id = self.tenant_id
        allocation.available_amount = allocation.total_amount
        self.db.add(allocation)
        self.db.flush()
        return allocation

    def update(self, allocation: BudgetAllocation) -> BudgetAllocation:
        allocation.version += 1
        self.db.flush()
        return allocation

    def commit_amount(self, allocation_id: UUID, amount: Decimal) -> bool:
        allocation = self.get_by_id(allocation_id)
        if not allocation:
            return False
        allocation.committed_amount += amount
        allocation.available_amount = (
            allocation.total_amount - allocation.committed_amount - allocation.spent_amount
        )
        self.db.flush()
        return True

    def release_amount(self, allocation_id: UUID, amount: Decimal) -> bool:
        allocation = self.get_by_id(allocation_id)
        if not allocation:
            return False
        allocation.committed_amount = max(Decimal("0"), allocation.committed_amount - amount)
        allocation.available_amount = (
            allocation.total_amount - allocation.committed_amount - allocation.spent_amount
        )
        self.db.flush()
        return True

    def spend_amount(self, allocation_id: UUID, amount: Decimal) -> bool:
        allocation = self.get_by_id(allocation_id)
        if not allocation:
            return False
        allocation.committed_amount = max(Decimal("0"), allocation.committed_amount - amount)
        allocation.spent_amount += amount
        allocation.available_amount = (
            allocation.total_amount - allocation.committed_amount - allocation.spent_amount
        )
        self.db.flush()
        return True


class RequisitionRepository:
    """Repository pour Requisition avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Requisition).filter(
            Requisition.tenant_id == self.tenant_id,
            Requisition.is_deleted == False
        )

    def get_by_id(self, req_id: UUID) -> Optional[Requisition]:
        return self._base_query().filter(Requisition.id == req_id).first()

    def get_by_number(self, number: str) -> Optional[Requisition]:
        return self._base_query().filter(Requisition.requisition_number == number).first()

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[RequisitionStatus] = None,
        requisition_type: Optional[str] = None,
        priority: Optional[str] = None,
        requester_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        approver_id: Optional[UUID] = None,
        date_from=None,
        date_to=None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None
    ) -> Tuple[List[Requisition], int, int]:
        query = self._base_query()

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Requisition.requisition_number.ilike(search_filter),
                    Requisition.title.ilike(search_filter),
                    Requisition.requester_name.ilike(search_filter)
                )
            )

        if status:
            query = query.filter(Requisition.status == status)

        if requisition_type:
            query = query.filter(Requisition.requisition_type == requisition_type)

        if priority:
            query = query.filter(Requisition.priority == priority)

        if requester_id:
            query = query.filter(Requisition.requester_id == requester_id)

        if department_id:
            query = query.filter(Requisition.department_id == department_id)

        if approver_id:
            query = query.filter(Requisition.current_approver_id == approver_id)

        if date_from:
            query = query.filter(Requisition.created_at >= date_from)

        if date_to:
            query = query.filter(Requisition.created_at <= date_to)

        if min_amount is not None:
            query = query.filter(Requisition.total_amount >= min_amount)

        if max_amount is not None:
            query = query.filter(Requisition.total_amount <= max_amount)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Requisition.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def list_pending_approval(
        self,
        approver_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Requisition], int, int]:
        query = self._base_query().filter(
            Requisition.status == RequisitionStatus.PENDING_APPROVAL,
            Requisition.current_approver_id == approver_id
        )

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Requisition.created_at).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, requisition: Requisition) -> Requisition:
        requisition.tenant_id = self.tenant_id
        self.db.add(requisition)
        self.db.flush()
        return requisition

    def update(self, requisition: Requisition) -> Requisition:
        requisition.version += 1
        requisition.updated_at = datetime.utcnow()
        self.db.flush()
        return requisition

    def soft_delete(self, req_id: UUID, deleted_by: UUID) -> bool:
        requisition = self.get_by_id(req_id)
        if not requisition:
            return False
        requisition.is_deleted = True
        requisition.deleted_at = datetime.utcnow()
        requisition.deleted_by = deleted_by
        self.db.flush()
        return True

    def restore(self, req_id: UUID) -> Optional[Requisition]:
        requisition = self.db.query(Requisition).filter(
            Requisition.tenant_id == self.tenant_id,
            Requisition.id == req_id,
            Requisition.is_deleted == True
        ).first()
        if requisition:
            requisition.is_deleted = False
            requisition.deleted_at = None
            requisition.deleted_by = None
            self.db.flush()
        return requisition

    def bulk_delete(self, req_ids: List[UUID], deleted_by: UUID) -> int:
        count = 0
        for req_id in req_ids:
            if self.soft_delete(req_id, deleted_by):
                count += 1
        return count

    def get_next_number(self, prefix: str = "REQ") -> str:
        year = datetime.utcnow().year
        last_req = self._base_query().filter(
            Requisition.requisition_number.like(f"{prefix}-{year}-%")
        ).order_by(Requisition.requisition_number.desc()).first()

        if last_req:
            try:
                last_num = int(last_req.requisition_number.split("-")[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}-{year}-{next_num:06d}"

    def autocomplete(self, search: str, limit: int = 10) -> List[dict]:
        reqs = self._base_query().filter(
            or_(
                Requisition.requisition_number.ilike(f"%{search}%"),
                Requisition.title.ilike(f"%{search}%")
            )
        ).limit(limit).all()
        return [{"id": r.id, "number": r.requisition_number, "title": r.title} for r in reqs]

    def get_stats(self, date_from=None, date_to=None) -> dict:
        query = self._base_query()

        if date_from:
            query = query.filter(Requisition.created_at >= date_from)
        if date_to:
            query = query.filter(Requisition.created_at <= date_to)

        total = query.count()

        by_status = {}
        for status in RequisitionStatus:
            count = query.filter(Requisition.status == status).count()
            if count > 0:
                by_status[status.value] = count

        total_amount = query.with_entities(
            func.sum(Requisition.total_amount)
        ).scalar() or Decimal("0")

        approved_amount = query.filter(
            Requisition.status.in_([
                RequisitionStatus.APPROVED,
                RequisitionStatus.ORDERED,
                RequisitionStatus.RECEIVED,
                RequisitionStatus.CLOSED
            ])
        ).with_entities(func.sum(Requisition.total_amount)).scalar() or Decimal("0")

        return {
            "total": total,
            "by_status": by_status,
            "total_amount": total_amount,
            "approved_amount": approved_amount
        }


class RequisitionLineRepository:
    """Repository pour RequisitionLine avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(RequisitionLine).filter(
            RequisitionLine.tenant_id == self.tenant_id
        )

    def get_by_id(self, line_id: UUID) -> Optional[RequisitionLine]:
        return self._base_query().filter(RequisitionLine.id == line_id).first()

    def get_for_requisition(self, req_id: UUID) -> List[RequisitionLine]:
        return self._base_query().filter(
            RequisitionLine.requisition_id == req_id
        ).order_by(RequisitionLine.line_number).all()

    def create(self, line: RequisitionLine) -> RequisitionLine:
        line.tenant_id = self.tenant_id
        line.total_price = line.quantity * line.unit_price
        self.db.add(line)
        self.db.flush()
        return line

    def update(self, line: RequisitionLine) -> RequisitionLine:
        line.total_price = line.quantity * line.unit_price
        self.db.flush()
        return line

    def delete(self, line_id: UUID) -> bool:
        line = self.get_by_id(line_id)
        if not line:
            return False
        self.db.delete(line)
        self.db.flush()
        return True

    def get_next_line_number(self, req_id: UUID) -> int:
        max_num = self._base_query().filter(
            RequisitionLine.requisition_id == req_id
        ).with_entities(func.max(RequisitionLine.line_number)).scalar()
        return (max_num or 0) + 1


class ApprovalStepRepository:
    """Repository pour ApprovalStep avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(ApprovalStep).filter(
            ApprovalStep.tenant_id == self.tenant_id
        )

    def get_by_id(self, step_id: UUID) -> Optional[ApprovalStep]:
        return self._base_query().filter(ApprovalStep.id == step_id).first()

    def get_for_requisition(self, req_id: UUID) -> List[ApprovalStep]:
        return self._base_query().filter(
            ApprovalStep.requisition_id == req_id
        ).order_by(ApprovalStep.step_number).all()

    def get_pending_for_approver(
        self,
        approver_id: UUID,
        req_id: UUID
    ) -> Optional[ApprovalStep]:
        return self._base_query().filter(
            ApprovalStep.requisition_id == req_id,
            ApprovalStep.approver_id == approver_id,
            ApprovalStep.status == ApprovalStatus.PENDING
        ).first()

    def create(self, step: ApprovalStep) -> ApprovalStep:
        step.tenant_id = self.tenant_id
        self.db.add(step)
        self.db.flush()
        return step

    def update(self, step: ApprovalStep) -> ApprovalStep:
        self.db.flush()
        return step


class CommentRepository:
    """Repository pour RequisitionComment avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(RequisitionComment).filter(
            RequisitionComment.tenant_id == self.tenant_id
        )

    def get_for_requisition(
        self,
        req_id: UUID,
        include_internal: bool = False
    ) -> List[RequisitionComment]:
        query = self._base_query().filter(
            RequisitionComment.requisition_id == req_id
        )
        if not include_internal:
            query = query.filter(RequisitionComment.is_internal == False)
        return query.order_by(RequisitionComment.created_at).all()

    def create(self, comment: RequisitionComment) -> RequisitionComment:
        comment.tenant_id = self.tenant_id
        self.db.add(comment)
        self.db.flush()
        return comment


class TemplateRepository:
    """Repository pour RequisitionTemplate avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(RequisitionTemplate).filter(
            RequisitionTemplate.tenant_id == self.tenant_id,
            RequisitionTemplate.is_deleted == False
        )

    def get_by_id(self, template_id: UUID) -> Optional[RequisitionTemplate]:
        return self._base_query().filter(RequisitionTemplate.id == template_id).first()

    def get_by_code(self, code: str) -> Optional[RequisitionTemplate]:
        return self._base_query().filter(RequisitionTemplate.code == code).first()

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        requisition_type: Optional[str] = None
    ) -> Tuple[List[RequisitionTemplate], int, int]:
        query = self._base_query()

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    RequisitionTemplate.code.ilike(search_filter),
                    RequisitionTemplate.name.ilike(search_filter)
                )
            )

        if is_active is not None:
            query = query.filter(RequisitionTemplate.is_active == is_active)

        if requisition_type:
            query = query.filter(RequisitionTemplate.requisition_type == requisition_type)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(RequisitionTemplate.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, template: RequisitionTemplate) -> RequisitionTemplate:
        template.tenant_id = self.tenant_id
        self.db.add(template)
        self.db.flush()
        return template

    def update(self, template: RequisitionTemplate) -> RequisitionTemplate:
        template.version += 1
        self.db.flush()
        return template

    def soft_delete(self, template_id: UUID, deleted_by: UUID) -> bool:
        template = self.get_by_id(template_id)
        if not template:
            return False
        template.is_deleted = True
        template.deleted_at = datetime.utcnow()
        template.deleted_by = deleted_by
        self.db.flush()
        return True

    def autocomplete(self, search: str, limit: int = 10) -> List[dict]:
        templates = self._base_query().filter(
            RequisitionTemplate.is_active == True,
            or_(
                RequisitionTemplate.code.ilike(f"%{search}%"),
                RequisitionTemplate.name.ilike(f"%{search}%")
            )
        ).limit(limit).all()
        return [{"id": t.id, "code": t.code, "name": t.name} for t in templates]
