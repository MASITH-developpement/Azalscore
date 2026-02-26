"""
Service Requisition / Demandes d'achat
======================================
Logique métier avec tenant isolation.
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from .models import (
    CatalogCategory, CatalogItem, CatalogItemStatus,
    PreferredVendor, BudgetAllocation,
    Requisition, RequisitionStatus, RequisitionType, Priority,
    RequisitionLine, LineStatus,
    ApprovalStep, ApprovalStatus,
    RequisitionComment, RequisitionTemplate
)
from .repository import (
    CatalogCategoryRepository, CatalogItemRepository,
    PreferredVendorRepository, BudgetAllocationRepository,
    RequisitionRepository, RequisitionLineRepository,
    ApprovalStepRepository, CommentRepository,
    TemplateRepository
)
from .schemas import (
    CatalogCategoryCreate, CatalogCategoryUpdate,
    CatalogItemCreate, CatalogItemUpdate,
    PreferredVendorCreate, PreferredVendorUpdate,
    BudgetAllocationCreate, BudgetAllocationUpdate,
    RequisitionCreate, RequisitionUpdate,
    RequisitionLineCreate, RequisitionLineUpdate,
    ApprovalStepCreate, ApprovalDecision,
    CommentCreate,
    TemplateCreate, TemplateUpdate,
    BudgetCheckResult
)
from .exceptions import (
    CatalogCategoryNotFoundError, CatalogCategoryDuplicateError,
    CatalogItemNotFoundError, CatalogItemDuplicateError, CatalogItemInactiveError,
    PreferredVendorNotFoundError, PreferredVendorDuplicateError,
    BudgetAllocationNotFoundError, BudgetAllocationDuplicateError,
    BudgetExceededError, InsufficientBudgetError,
    RequisitionNotFoundError, RequisitionDuplicateError,
    RequisitionValidationError, RequisitionStateError, RequisitionClosedError,
    RequisitionEmptyError, RequisitionLineNotFoundError,
    ApprovalStepNotFoundError, ApprovalNotAuthorizedError, ApprovalAlreadyProcessedError,
    NoApproverError,
    TemplateNotFoundError, TemplateDuplicateError
)


class RequisitionService:
    """Service de gestion des demandes d'achat."""

    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Repositories
        self.category_repo = CatalogCategoryRepository(db, tenant_id)
        self.item_repo = CatalogItemRepository(db, tenant_id)
        self.vendor_repo = PreferredVendorRepository(db, tenant_id)
        self.budget_repo = BudgetAllocationRepository(db, tenant_id)
        self.req_repo = RequisitionRepository(db, tenant_id)
        self.line_repo = RequisitionLineRepository(db, tenant_id)
        self.approval_repo = ApprovalStepRepository(db, tenant_id)
        self.comment_repo = CommentRepository(db, tenant_id)
        self.template_repo = TemplateRepository(db, tenant_id)

    # ============== Catalog Category ==============

    def get_category(self, category_id: UUID) -> CatalogCategory:
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise CatalogCategoryNotFoundError(f"Category {category_id} not found")
        return category

    def list_categories(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        parent_id: Optional[UUID] = None
    ) -> Tuple[List[CatalogCategory], int, int]:
        return self.category_repo.list_all(page, page_size, search, is_active, parent_id)

    def create_category(self, data: CatalogCategoryCreate) -> CatalogCategory:
        if self.category_repo.get_by_code(data.code):
            raise CatalogCategoryDuplicateError(f"Category code {data.code} already exists")

        category = CatalogCategory(
            code=data.code,
            name=data.name,
            description=data.description,
            parent_id=data.parent_id,
            gl_account=data.gl_account,
            requires_approval=data.requires_approval,
            approval_threshold=data.approval_threshold,
            is_active=data.is_active,
            created_by=self.user_id
        )
        return self.category_repo.create(category)

    def update_category(self, category_id: UUID, data: CatalogCategoryUpdate) -> CatalogCategory:
        category = self.get_category(category_id)

        if data.code and data.code != category.code:
            if self.category_repo.get_by_code(data.code):
                raise CatalogCategoryDuplicateError(f"Category code {data.code} already exists")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)

        category.updated_by = self.user_id
        return self.category_repo.update(category)

    def delete_category(self, category_id: UUID) -> bool:
        self.get_category(category_id)
        return self.category_repo.soft_delete(category_id, self.user_id)

    def restore_category(self, category_id: UUID) -> CatalogCategory:
        category = self.category_repo.restore(category_id)
        if not category:
            raise CatalogCategoryNotFoundError(f"Category {category_id} not found")
        return category

    def autocomplete_category(self, search: str) -> List[dict]:
        return self.category_repo.autocomplete(search)

    # ============== Catalog Item ==============

    def get_item(self, item_id: UUID) -> CatalogItem:
        item = self.item_repo.get_by_id(item_id)
        if not item:
            raise CatalogItemNotFoundError(f"Item {item_id} not found")
        return item

    def list_items(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        category_id: Optional[UUID] = None,
        vendor_id: Optional[UUID] = None
    ) -> Tuple[List[CatalogItem], int, int]:
        status_enum = CatalogItemStatus(status) if status else None
        return self.item_repo.list_all(page, page_size, search, status_enum, category_id, vendor_id)

    def create_item(self, data: CatalogItemCreate) -> CatalogItem:
        if self.item_repo.get_by_code(data.code):
            raise CatalogItemDuplicateError(f"Item code {data.code} already exists")

        category_name = ""
        if data.category_id:
            category = self.get_category(data.category_id)
            category_name = category.name

        item = CatalogItem(
            code=data.code,
            name=data.name,
            description=data.description,
            category_id=data.category_id,
            category_name=category_name,
            unit_price=data.unit_price,
            currency=data.currency,
            unit_of_measure=data.unit_of_measure,
            preferred_vendor_id=data.preferred_vendor_id,
            preferred_vendor_name=data.preferred_vendor_name,
            vendor_item_code=data.vendor_item_code,
            lead_time_days=data.lead_time_days,
            min_order_qty=data.min_order_qty,
            max_order_qty=data.max_order_qty,
            order_multiple=data.order_multiple,
            image_url=data.image_url,
            specifications=data.specifications,
            tags=data.tags,
            created_by=self.user_id
        )
        return self.item_repo.create(item)

    def update_item(self, item_id: UUID, data: CatalogItemUpdate) -> CatalogItem:
        item = self.get_item(item_id)

        if data.code and data.code != item.code:
            if self.item_repo.get_by_code(data.code):
                raise CatalogItemDuplicateError(f"Item code {data.code} already exists")

        if data.category_id:
            category = self.get_category(data.category_id)
            item.category_name = category.name

        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "status" and value:
                setattr(item, field, CatalogItemStatus(value))
            else:
                setattr(item, field, value)

        item.updated_by = self.user_id
        return self.item_repo.update(item)

    def delete_item(self, item_id: UUID) -> bool:
        self.get_item(item_id)
        return self.item_repo.soft_delete(item_id, self.user_id)

    def restore_item(self, item_id: UUID) -> CatalogItem:
        item = self.item_repo.restore(item_id)
        if not item:
            raise CatalogItemNotFoundError(f"Item {item_id} not found")
        return item

    def autocomplete_item(self, search: str) -> List[dict]:
        return self.item_repo.autocomplete(search)

    # ============== Preferred Vendor ==============

    def get_preferred_vendor(self, vendor_pref_id: UUID) -> PreferredVendor:
        vendor = self.vendor_repo.get_by_id(vendor_pref_id)
        if not vendor:
            raise PreferredVendorNotFoundError(f"Preferred vendor {vendor_pref_id} not found")
        return vendor

    def list_preferred_vendors(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        category_id: Optional[UUID] = None
    ) -> Tuple[List[PreferredVendor], int, int]:
        return self.vendor_repo.list_all(page, page_size, search, is_active, category_id)

    def get_vendors_for_category(self, category_id: UUID) -> List[PreferredVendor]:
        return self.vendor_repo.get_for_category(category_id)

    def create_preferred_vendor(self, data: PreferredVendorCreate) -> PreferredVendor:
        if self.vendor_repo.get_by_vendor_id(data.vendor_id):
            raise PreferredVendorDuplicateError(f"Vendor {data.vendor_id} already preferred")

        vendor = PreferredVendor(
            vendor_id=data.vendor_id,
            vendor_code=data.vendor_code,
            vendor_name=data.vendor_name,
            category_ids=data.category_ids,
            contract_id=data.contract_id,
            contract_end_date=data.contract_end_date,
            discount_percentage=data.discount_percentage,
            payment_terms=data.payment_terms,
            lead_time_days=data.lead_time_days,
            minimum_order=data.minimum_order,
            rating=data.rating,
            is_primary=data.is_primary,
            is_active=data.is_active,
            created_by=self.user_id
        )
        return self.vendor_repo.create(vendor)

    def update_preferred_vendor(self, vendor_pref_id: UUID, data: PreferredVendorUpdate) -> PreferredVendor:
        vendor = self.get_preferred_vendor(vendor_pref_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(vendor, field, value)

        vendor.updated_by = self.user_id
        return self.vendor_repo.update(vendor)

    def delete_preferred_vendor(self, vendor_pref_id: UUID) -> bool:
        self.get_preferred_vendor(vendor_pref_id)
        return self.vendor_repo.soft_delete(vendor_pref_id, self.user_id)

    # ============== Budget Allocation ==============

    def get_budget_allocation(self, allocation_id: UUID) -> BudgetAllocation:
        allocation = self.budget_repo.get_by_id(allocation_id)
        if not allocation:
            raise BudgetAllocationNotFoundError(f"Budget allocation {allocation_id} not found")
        return allocation

    def list_budget_allocations(
        self,
        page: int = 1,
        page_size: int = 20,
        fiscal_year: Optional[int] = None,
        department_id: Optional[UUID] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[BudgetAllocation], int, int]:
        return self.budget_repo.list_all(page, page_size, fiscal_year, department_id, is_active)

    def create_budget_allocation(self, data: BudgetAllocationCreate) -> BudgetAllocation:
        existing = self.budget_repo.get_for_department(data.department_id, data.fiscal_year)
        if existing:
            raise BudgetAllocationDuplicateError(
                f"Budget allocation already exists for department {data.department_id} in {data.fiscal_year}"
            )

        allocation = BudgetAllocation(
            budget_id=data.budget_id,
            budget_name=data.budget_name,
            department_id=data.department_id,
            department_name=data.department_name,
            cost_center_id=data.cost_center_id,
            fiscal_year=data.fiscal_year,
            total_amount=data.total_amount,
            category_allocations=data.category_allocations,
            is_active=data.is_active,
            created_by=self.user_id
        )
        return self.budget_repo.create(allocation)

    def update_budget_allocation(self, allocation_id: UUID, data: BudgetAllocationUpdate) -> BudgetAllocation:
        allocation = self.get_budget_allocation(allocation_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(allocation, field, value)

        if data.total_amount is not None:
            allocation.available_amount = (
                allocation.total_amount - allocation.committed_amount - allocation.spent_amount
            )

        allocation.updated_by = self.user_id
        return self.budget_repo.update(allocation)

    def check_budget(self, department_id: UUID, amount: Decimal) -> BudgetCheckResult:
        fiscal_year = datetime.utcnow().year
        allocation = self.budget_repo.get_for_department(department_id, fiscal_year)

        if not allocation:
            return BudgetCheckResult(
                passed=True,
                message="No budget constraint for this department",
                available_amount=Decimal("0"),
                required_amount=amount
            )

        if allocation.available_amount >= amount:
            return BudgetCheckResult(
                passed=True,
                message="Budget available",
                available_amount=allocation.available_amount,
                required_amount=amount
            )
        else:
            return BudgetCheckResult(
                passed=False,
                message="Insufficient budget",
                available_amount=allocation.available_amount,
                required_amount=amount,
                over_budget_amount=amount - allocation.available_amount
            )

    # ============== Requisition ==============

    def get_requisition(self, req_id: UUID) -> Requisition:
        requisition = self.req_repo.get_by_id(req_id)
        if not requisition:
            raise RequisitionNotFoundError(f"Requisition {req_id} not found")
        return requisition

    def list_requisitions(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
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
        status_enum = RequisitionStatus(status) if status else None
        return self.req_repo.list_all(
            page, page_size, search, status_enum, requisition_type, priority,
            requester_id, department_id, approver_id, date_from, date_to,
            min_amount, max_amount
        )

    def list_pending_approval(
        self,
        approver_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Requisition], int, int]:
        return self.req_repo.list_pending_approval(approver_id, page, page_size)

    def create_requisition(
        self,
        data: RequisitionCreate,
        requester_name: str,
        requester_email: str = ""
    ) -> Requisition:
        requisition = Requisition(
            requisition_number=self.req_repo.get_next_number(),
            requisition_type=RequisitionType(data.requisition_type),
            priority=Priority(data.priority),
            title=data.title,
            description=data.description,
            justification=data.justification,
            requester_id=self.user_id,
            requester_name=requester_name,
            requester_email=requester_email,
            department_id=data.department_id,
            department_name=data.department_name,
            required_date=data.required_date,
            budget_id=data.budget_id,
            budget_name=data.budget_name,
            currency=data.currency,
            tags=data.tags,
            created_by=self.user_id
        )
        requisition = self.req_repo.create(requisition)

        # Create lines
        total = Decimal("0")
        for i, line_data in enumerate(data.lines):
            line = self._create_line(requisition.id, i + 1, line_data)
            total += line.total_price

        requisition.total_amount = total
        self.req_repo.update(requisition)

        return requisition

    def _create_line(
        self,
        req_id: UUID,
        line_number: int,
        data: RequisitionLineCreate
    ) -> RequisitionLine:
        line = RequisitionLine(
            requisition_id=req_id,
            line_number=line_number,
            item_id=data.item_id,
            item_code=data.item_code,
            description=data.description,
            category_id=data.category_id,
            category_name=data.category_name,
            quantity=data.quantity,
            unit_of_measure=data.unit_of_measure,
            unit_price=data.unit_price,
            currency=data.currency,
            suggested_vendor_id=data.suggested_vendor_id,
            suggested_vendor_name=data.suggested_vendor_name,
            budget_id=data.budget_id,
            cost_center_id=data.cost_center_id,
            gl_account=data.gl_account,
            specifications=data.specifications,
            notes=data.notes
        )
        return self.line_repo.create(line)

    def update_requisition(self, req_id: UUID, data: RequisitionUpdate) -> Requisition:
        requisition = self.get_requisition(req_id)

        if requisition.status not in [RequisitionStatus.DRAFT, RequisitionStatus.REJECTED]:
            raise RequisitionStateError("Can only update draft or rejected requisitions")

        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "requisition_type" and value:
                setattr(requisition, field, RequisitionType(value))
            elif field == "priority" and value:
                setattr(requisition, field, Priority(value))
            else:
                setattr(requisition, field, value)

        requisition.updated_by = self.user_id
        return self.req_repo.update(requisition)

    def delete_requisition(self, req_id: UUID) -> bool:
        requisition = self.get_requisition(req_id)

        if requisition.status not in [RequisitionStatus.DRAFT, RequisitionStatus.CANCELLED]:
            raise RequisitionStateError("Can only delete draft or cancelled requisitions")

        return self.req_repo.soft_delete(req_id, self.user_id)

    def restore_requisition(self, req_id: UUID) -> Requisition:
        requisition = self.req_repo.restore(req_id)
        if not requisition:
            raise RequisitionNotFoundError(f"Requisition {req_id} not found")
        return requisition

    def autocomplete_requisition(self, search: str) -> List[dict]:
        return self.req_repo.autocomplete(search)

    # ============== Line Operations ==============

    def add_line(self, req_id: UUID, data: RequisitionLineCreate) -> RequisitionLine:
        requisition = self.get_requisition(req_id)

        if requisition.status not in [RequisitionStatus.DRAFT, RequisitionStatus.REJECTED]:
            raise RequisitionStateError("Can only add lines to draft or rejected requisitions")

        line_number = self.line_repo.get_next_line_number(req_id)
        line = self._create_line(req_id, line_number, data)

        requisition.total_amount += line.total_price
        requisition.updated_by = self.user_id
        self.req_repo.update(requisition)

        return line

    def update_line(self, line_id: UUID, data: RequisitionLineUpdate) -> RequisitionLine:
        line = self.line_repo.get_by_id(line_id)
        if not line:
            raise RequisitionLineNotFoundError(f"Line {line_id} not found")

        requisition = self.get_requisition(line.requisition_id)
        if requisition.status not in [RequisitionStatus.DRAFT, RequisitionStatus.REJECTED]:
            raise RequisitionStateError("Can only update lines in draft or rejected requisitions")

        old_total = line.total_price

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(line, field, value)

        line = self.line_repo.update(line)

        requisition.total_amount = requisition.total_amount - old_total + line.total_price
        self.req_repo.update(requisition)

        return line

    def remove_line(self, line_id: UUID) -> bool:
        line = self.line_repo.get_by_id(line_id)
        if not line:
            raise RequisitionLineNotFoundError(f"Line {line_id} not found")

        requisition = self.get_requisition(line.requisition_id)
        if requisition.status not in [RequisitionStatus.DRAFT, RequisitionStatus.REJECTED]:
            raise RequisitionStateError("Can only remove lines from draft or rejected requisitions")

        requisition.total_amount -= line.total_price
        self.req_repo.update(requisition)

        return self.line_repo.delete(line_id)

    def get_lines(self, req_id: UUID) -> List[RequisitionLine]:
        self.get_requisition(req_id)
        return self.line_repo.get_for_requisition(req_id)

    # ============== Workflow ==============

    def submit_requisition(self, req_id: UUID) -> Requisition:
        requisition = self.get_requisition(req_id)

        if requisition.status != RequisitionStatus.DRAFT:
            raise RequisitionStateError("Can only submit draft requisitions")

        lines = self.line_repo.get_for_requisition(req_id)
        if not lines:
            raise RequisitionEmptyError("Cannot submit requisition without lines")

        # Check budget
        if requisition.department_id:
            result = self.check_budget(requisition.department_id, requisition.total_amount)
            requisition.budget_check_passed = result.passed
            requisition.budget_check_message = result.message

        requisition.status = RequisitionStatus.SUBMITTED
        requisition.submitted_at = datetime.utcnow()
        requisition.updated_by = self.user_id

        return self.req_repo.update(requisition)

    def submit_for_approval(
        self,
        req_id: UUID,
        approvers: List[ApprovalStepCreate]
    ) -> Requisition:
        requisition = self.get_requisition(req_id)

        if requisition.status != RequisitionStatus.SUBMITTED:
            raise RequisitionStateError("Can only request approval for submitted requisitions")

        if not approvers:
            raise NoApproverError("At least one approver required")

        # Create approval steps
        for i, approver_data in enumerate(approvers):
            step = ApprovalStep(
                requisition_id=req_id,
                step_number=i + 1,
                approver_id=approver_data.approver_id,
                approver_name=approver_data.approver_name
            )
            self.approval_repo.create(step)

        # Set first approver as current
        requisition.status = RequisitionStatus.PENDING_APPROVAL
        requisition.current_approver_id = approvers[0].approver_id
        requisition.current_approver_name = approvers[0].approver_name
        requisition.updated_by = self.user_id

        return self.req_repo.update(requisition)

    def process_approval(
        self,
        req_id: UUID,
        decision: ApprovalDecision
    ) -> Requisition:
        requisition = self.get_requisition(req_id)

        if requisition.status != RequisitionStatus.PENDING_APPROVAL:
            raise RequisitionStateError("Requisition is not pending approval")

        step = self.approval_repo.get_pending_for_approver(self.user_id, req_id)
        if not step:
            raise ApprovalNotAuthorizedError("You are not authorized to approve this requisition")

        step.status = ApprovalStatus.APPROVED if decision.decision == "approved" else ApprovalStatus.REJECTED
        step.comments = decision.comments
        step.decided_at = datetime.utcnow()
        self.approval_repo.update(step)

        if decision.decision == "rejected":
            requisition.status = RequisitionStatus.REJECTED
            requisition.current_approver_id = None
            requisition.current_approver_name = ""
        else:
            # Check for next approver
            steps = self.approval_repo.get_for_requisition(req_id)
            next_step = None
            for s in steps:
                if s.status == ApprovalStatus.PENDING:
                    next_step = s
                    break

            if next_step:
                requisition.current_approver_id = next_step.approver_id
                requisition.current_approver_name = next_step.approver_name
            else:
                requisition.status = RequisitionStatus.APPROVED
                requisition.approved_at = datetime.utcnow()
                requisition.current_approver_id = None
                requisition.current_approver_name = ""

                # Commit budget
                if requisition.department_id:
                    allocation = self.budget_repo.get_for_department(
                        requisition.department_id,
                        datetime.utcnow().year
                    )
                    if allocation:
                        self.budget_repo.commit_amount(allocation.id, requisition.total_amount)

        requisition.updated_by = self.user_id
        return self.req_repo.update(requisition)

    def cancel_requisition(self, req_id: UUID, reason: str = "") -> Requisition:
        requisition = self.get_requisition(req_id)

        allowed = [
            RequisitionStatus.DRAFT,
            RequisitionStatus.SUBMITTED,
            RequisitionStatus.PENDING_APPROVAL,
            RequisitionStatus.APPROVED
        ]
        if requisition.status not in allowed:
            raise RequisitionStateError("Cannot cancel requisition in current status")

        # Release committed budget
        if requisition.status == RequisitionStatus.APPROVED and requisition.department_id:
            allocation = self.budget_repo.get_for_department(
                requisition.department_id,
                datetime.utcnow().year
            )
            if allocation:
                self.budget_repo.release_amount(allocation.id, requisition.total_amount)

        requisition.status = RequisitionStatus.CANCELLED
        requisition.updated_by = self.user_id

        if reason:
            self.add_comment(req_id, CommentCreate(content=f"Cancelled: {reason}", is_internal=True))

        return self.req_repo.update(requisition)

    def close_requisition(self, req_id: UUID) -> Requisition:
        requisition = self.get_requisition(req_id)

        if requisition.status != RequisitionStatus.RECEIVED:
            raise RequisitionStateError("Can only close received requisitions")

        requisition.status = RequisitionStatus.CLOSED
        requisition.closed_at = datetime.utcnow()
        requisition.updated_by = self.user_id

        return self.req_repo.update(requisition)

    # ============== Comments ==============

    def add_comment(self, req_id: UUID, data: CommentCreate) -> RequisitionComment:
        self.get_requisition(req_id)

        comment = RequisitionComment(
            requisition_id=req_id,
            author_id=self.user_id,
            author_name="",  # Should be filled by caller
            content=data.content,
            is_internal=data.is_internal
        )
        return self.comment_repo.create(comment)

    def get_comments(self, req_id: UUID, include_internal: bool = False) -> List[RequisitionComment]:
        self.get_requisition(req_id)
        return self.comment_repo.get_for_requisition(req_id, include_internal)

    # ============== Templates ==============

    def get_template(self, template_id: UUID) -> RequisitionTemplate:
        template = self.template_repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")
        return template

    def list_templates(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        requisition_type: Optional[str] = None
    ) -> Tuple[List[RequisitionTemplate], int, int]:
        return self.template_repo.list_all(page, page_size, search, is_active, requisition_type)

    def create_template(self, data: TemplateCreate) -> RequisitionTemplate:
        if self.template_repo.get_by_code(data.code):
            raise TemplateDuplicateError(f"Template code {data.code} already exists")

        template = RequisitionTemplate(
            code=data.code,
            name=data.name,
            description=data.description,
            requisition_type=RequisitionType(data.requisition_type),
            default_lines=data.default_lines,
            is_active=data.is_active,
            created_by=self.user_id
        )
        return self.template_repo.create(template)

    def update_template(self, template_id: UUID, data: TemplateUpdate) -> RequisitionTemplate:
        template = self.get_template(template_id)

        if data.code and data.code != template.code:
            if self.template_repo.get_by_code(data.code):
                raise TemplateDuplicateError(f"Template code {data.code} already exists")

        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "requisition_type" and value:
                setattr(template, field, RequisitionType(value))
            else:
                setattr(template, field, value)

        template.updated_by = self.user_id
        return self.template_repo.update(template)

    def delete_template(self, template_id: UUID) -> bool:
        self.get_template(template_id)
        return self.template_repo.soft_delete(template_id, self.user_id)

    def create_from_template(
        self,
        template_id: UUID,
        data: RequisitionCreate,
        requester_name: str,
        requester_email: str = ""
    ) -> Requisition:
        template = self.get_template(template_id)

        # Merge template lines with provided lines
        lines = list(data.lines)
        for tpl_line in template.default_lines:
            lines.append(RequisitionLineCreate(**tpl_line))

        data_dict = data.model_dump()
        data_dict["lines"] = lines
        data_dict["requisition_type"] = template.requisition_type.value

        return self.create_requisition(
            RequisitionCreate(**data_dict),
            requester_name,
            requester_email
        )

    def autocomplete_template(self, search: str) -> List[dict]:
        return self.template_repo.autocomplete(search)

    # ============== Stats ==============

    def get_stats(self, date_from=None, date_to=None) -> dict:
        return self.req_repo.get_stats(date_from, date_to)

    def get_approval_steps(self, req_id: UUID) -> List[ApprovalStep]:
        self.get_requisition(req_id)
        return self.approval_repo.get_for_requisition(req_id)
