"""
Repository - Module Expenses (GAP-084)

CRITIQUE: Toutes les requêtes filtrées par tenant_id.
"""
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload

from .models import (
    ExpenseReport, ExpenseLine, ExpensePolicy, MileageRate, EmployeeVehicle,
    ExpenseStatus, ExpenseCategory, PaymentMethod, VehicleType
)
from .schemas import ExpenseReportFilters


class ExpenseReportRepository:
    """Repository ExpenseReport avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(ExpenseReport).filter(ExpenseReport.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(ExpenseReport.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ExpenseReport]:
        return self._base_query().options(
            joinedload(ExpenseReport.lines)
        ).filter(ExpenseReport.id == id).first()

    def get_by_code(self, code: str) -> Optional[ExpenseReport]:
        return self._base_query().filter(ExpenseReport.code == code.upper()).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(ExpenseReport.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(ExpenseReport.code == code.upper())
        if exclude_id:
            query = query.filter(ExpenseReport.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: ExpenseReportFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[ExpenseReport], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    ExpenseReport.title.ilike(term),
                    ExpenseReport.code.ilike(term),
                    ExpenseReport.employee_name.ilike(term)
                ))
            if filters.status:
                query = query.filter(ExpenseReport.status.in_([s.value for s in filters.status]))
            if filters.employee_id:
                query = query.filter(ExpenseReport.employee_id == filters.employee_id)
            if filters.department_id:
                query = query.filter(ExpenseReport.department_id == filters.department_id)
            if filters.date_from:
                query = query.filter(ExpenseReport.period_start >= filters.date_from)
            if filters.date_to:
                query = query.filter(ExpenseReport.period_end <= filters.date_to)
            if filters.min_amount is not None:
                query = query.filter(ExpenseReport.total_amount >= filters.min_amount)
            if filters.max_amount is not None:
                query = query.filter(ExpenseReport.total_amount <= filters.max_amount)

        total = query.count()
        sort_col = getattr(ExpenseReport, sort_by, ExpenseReport.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_employee(self, employee_id: UUID, year: int = None) -> List[ExpenseReport]:
        query = self._base_query().filter(ExpenseReport.employee_id == employee_id)
        if year:
            query = query.filter(func.extract('year', ExpenseReport.created_at) == year)
        return query.order_by(desc(ExpenseReport.created_at)).all()

    def get_pending_approval(self, approver_id: UUID) -> List[ExpenseReport]:
        return self._base_query().filter(
            ExpenseReport.status.in_([ExpenseStatus.SUBMITTED.value, ExpenseStatus.PENDING_APPROVAL.value]),
            ExpenseReport.current_approver_id == approver_id
        ).order_by(ExpenseReport.submitted_at).all()

    def get_next_code(self) -> str:
        """Générer le prochain code."""
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        prefix = f"NF-{year}{month:02d}-"

        last = self.db.query(ExpenseReport).filter(
            ExpenseReport.tenant_id == self.tenant_id,
            ExpenseReport.code.like(f"{prefix}%")
        ).order_by(desc(ExpenseReport.code)).first()

        if last:
            try:
                last_num = int(last.code.split("-")[-1])
                return f"{prefix}{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}0001"

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(or_(
            ExpenseReport.title.ilike(f"{prefix}%"),
            ExpenseReport.code.ilike(f"{prefix}%")
        ))
        results = query.order_by(ExpenseReport.created_at.desc()).limit(limit).all()
        return [
            {"id": str(r.id), "code": r.code, "name": r.title, "label": f"[{r.code}] {r.title}"}
            for r in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ExpenseReport:
        lines_data = data.pop("lines", [])

        if "code" not in data or not data["code"]:
            data["code"] = self.get_next_code()

        entity = ExpenseReport(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.flush()

        for line_data in lines_data:
            self._add_line(entity, line_data, created_by)

        self._recalculate_totals(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: ExpenseReport, data: Dict[str, Any], updated_by: UUID = None) -> ExpenseReport:
        for key, value in data.items():
            if hasattr(entity, key) and key != "lines":
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def add_line(self, report: ExpenseReport, line_data: Dict[str, Any], created_by: UUID = None) -> ExpenseLine:
        if report.status != ExpenseStatus.DRAFT.value:
            raise ValueError("Cannot modify submitted report")

        line = self._add_line(report, line_data, created_by)
        self._recalculate_totals(report)
        self.db.commit()
        self.db.refresh(line)
        return line

    def _add_line(self, report: ExpenseReport, line_data: Dict[str, Any], created_by: UUID = None) -> ExpenseLine:
        # Calculer TVA si taux fourni
        vat_rate = line_data.get("vat_rate")
        amount = Decimal(str(line_data.get("amount", 0)))

        if vat_rate:
            vat_rate = Decimal(str(vat_rate))
            vat_amount = (amount * vat_rate / (100 + vat_rate)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            amount_excl_vat = amount - vat_amount
            line_data["vat_amount"] = vat_amount
            line_data["amount_excl_vat"] = amount_excl_vat

        # Guest count
        guests = line_data.get("guests", [])
        line_data["guest_count"] = len(guests)

        line = ExpenseLine(
            tenant_id=self.tenant_id,
            report_id=report.id,
            created_by=created_by,
            **line_data
        )
        self.db.add(line)
        return line

    def update_line(self, line: ExpenseLine, data: Dict[str, Any]) -> ExpenseLine:
        report = line.report
        if report.status != ExpenseStatus.DRAFT.value:
            raise ValueError("Cannot modify submitted report")

        for key, value in data.items():
            if hasattr(line, key):
                setattr(line, key, value)

        # Recalculer TVA si amount ou vat_rate change
        if "amount" in data or "vat_rate" in data:
            if line.vat_rate:
                vat_amount = (line.amount * line.vat_rate / (100 + line.vat_rate)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                line.vat_amount = vat_amount
                line.amount_excl_vat = line.amount - vat_amount

        if "guests" in data:
            line.guest_count = len(data["guests"])

        self._recalculate_totals(report)
        self.db.commit()
        self.db.refresh(line)
        return line

    def remove_line(self, line: ExpenseLine) -> bool:
        report = line.report
        if report.status != ExpenseStatus.DRAFT.value:
            raise ValueError("Cannot modify submitted report")

        self.db.delete(line)
        self._recalculate_totals(report)
        self.db.commit()
        return True

    def _recalculate_totals(self, report: ExpenseReport):
        """Recalculer les totaux de la note."""
        lines = self.db.query(ExpenseLine).filter(ExpenseLine.report_id == report.id).all()

        report.total_amount = sum(line.amount or Decimal("0") for line in lines)
        report.total_vat = sum(
            line.vat_amount or Decimal("0")
            for line in lines
            if line.vat_recoverable
        )
        report.total_reimbursable = sum(
            line.amount or Decimal("0")
            for line in lines
            if line.payment_method not in [PaymentMethod.COMPANY_CARD.value, PaymentMethod.COMPANY_ACCOUNT.value]
        )

    def submit(self, report: ExpenseReport, approver_id: UUID = None) -> ExpenseReport:
        if report.status != ExpenseStatus.DRAFT.value:
            raise ValueError("Report already submitted")

        report.status = ExpenseStatus.SUBMITTED.value
        report.submitted_at = datetime.utcnow()
        report.current_approver_id = approver_id

        self.db.commit()
        self.db.refresh(report)
        return report

    def approve(self, report: ExpenseReport, approver_id: UUID, comments: str = None) -> ExpenseReport:
        if report.status not in [ExpenseStatus.SUBMITTED.value, ExpenseStatus.PENDING_APPROVAL.value]:
            raise ValueError("Report not pending approval")

        history = list(report.approval_history or [])
        history.append({
            "approver_id": str(approver_id),
            "action": "approved",
            "comments": comments,
            "timestamp": datetime.utcnow().isoformat()
        })
        report.approval_history = history

        report.status = ExpenseStatus.APPROVED.value
        report.approved_at = datetime.utcnow()
        report.current_approver_id = None

        self.db.commit()
        self.db.refresh(report)
        return report

    def reject(self, report: ExpenseReport, approver_id: UUID, reason: str) -> ExpenseReport:
        if report.status not in [ExpenseStatus.SUBMITTED.value, ExpenseStatus.PENDING_APPROVAL.value]:
            raise ValueError("Report not pending approval")

        history = list(report.approval_history or [])
        history.append({
            "approver_id": str(approver_id),
            "action": "rejected",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        report.approval_history = history

        report.status = ExpenseStatus.REJECTED.value
        report.current_approver_id = None

        self.db.commit()
        self.db.refresh(report)
        return report

    def mark_paid(self, report: ExpenseReport, updated_by: UUID = None) -> ExpenseReport:
        if report.status != ExpenseStatus.APPROVED.value:
            raise ValueError("Report not approved")

        report.status = ExpenseStatus.PAID.value
        report.paid_at = datetime.utcnow()
        report.updated_by = updated_by

        self.db.commit()
        self.db.refresh(report)
        return report

    def soft_delete(self, entity: ExpenseReport, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: ExpenseReport) -> ExpenseReport:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity


class ExpensePolicyRepository:
    """Repository ExpensePolicy avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(ExpensePolicy).filter(ExpensePolicy.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(ExpensePolicy.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ExpensePolicy]:
        return self._base_query().filter(ExpensePolicy.id == id).first()

    def get_by_code(self, code: str) -> Optional[ExpensePolicy]:
        return self._base_query().filter(ExpensePolicy.code == code.upper()).first()

    def get_default(self) -> Optional[ExpensePolicy]:
        return self._base_query().filter(
            ExpensePolicy.is_default == True,
            ExpensePolicy.is_active == True
        ).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(ExpensePolicy.code == code.upper())
        if exclude_id:
            query = query.filter(ExpensePolicy.id != exclude_id)
        return query.count() > 0

    def list_active(self) -> List[ExpensePolicy]:
        return self._base_query().filter(ExpensePolicy.is_active == True).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ExpensePolicy:
        # Si is_default, désactiver les autres
        if data.get("is_default"):
            self._base_query().filter(ExpensePolicy.is_default == True).update(
                {"is_default": False}
            )

        entity = ExpensePolicy(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: ExpensePolicy, data: Dict[str, Any], updated_by: UUID = None) -> ExpensePolicy:
        if data.get("is_default") and not entity.is_default:
            self._base_query().filter(
                ExpensePolicy.is_default == True,
                ExpensePolicy.id != entity.id
            ).update({"is_default": False})

        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: ExpensePolicy, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class MileageRateRepository:
    """Repository MileageRate avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(MileageRate).filter(MileageRate.tenant_id == self.tenant_id)

    def get_rate(self, year: int, vehicle_type: VehicleType) -> Optional[MileageRate]:
        return self._base_query().filter(
            MileageRate.year == year,
            MileageRate.vehicle_type == vehicle_type.value,
            MileageRate.is_active == True
        ).first()

    def get_rates_for_year(self, year: int) -> List[MileageRate]:
        return self._base_query().filter(
            MileageRate.year == year,
            MileageRate.is_active == True
        ).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> MileageRate:
        entity = MileageRate(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity


class EmployeeVehicleRepository:
    """Repository EmployeeVehicle avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(EmployeeVehicle).filter(EmployeeVehicle.tenant_id == self.tenant_id)

    def get_by_employee(self, employee_id: UUID) -> List[EmployeeVehicle]:
        return self._base_query().filter(
            EmployeeVehicle.employee_id == employee_id,
            EmployeeVehicle.is_active == True
        ).all()

    def get_default_vehicle(self, employee_id: UUID) -> Optional[EmployeeVehicle]:
        return self._base_query().filter(
            EmployeeVehicle.employee_id == employee_id,
            EmployeeVehicle.is_default == True,
            EmployeeVehicle.is_active == True
        ).first()

    def get_annual_mileage(self, employee_id: UUID, year: int) -> Decimal:
        vehicles = self.get_by_employee(employee_id)
        total = Decimal("0")
        for v in vehicles:
            mileage = v.annual_mileage or {}
            total += Decimal(str(mileage.get(str(year), 0)))
        return total

    def update_annual_mileage(self, vehicle: EmployeeVehicle, year: int, additional_km: Decimal):
        mileage = dict(vehicle.annual_mileage or {})
        current = Decimal(str(mileage.get(str(year), 0)))
        mileage[str(year)] = float(current + additional_km)
        vehicle.annual_mileage = mileage
        self.db.commit()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> EmployeeVehicle:
        entity = EmployeeVehicle(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
