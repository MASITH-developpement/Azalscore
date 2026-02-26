"""
Router API - Module Expenses (GAP-084)

Endpoints REST pour la gestion des notes de frais.
"""
from __future__ import annotations

import math
from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import ExpenseStatus, ExpenseCategory, PaymentMethod, VehicleType
from .schemas import (
    ExpenseReportCreate, ExpenseReportUpdate, ExpenseReportResponse,
    ExpenseReportList, ExpenseReportListItem,
    ExpenseLineCreate, ExpenseLineUpdate, ExpenseLineResponse,
    ExpensePolicyCreate, ExpensePolicyUpdate, ExpensePolicyResponse,
    MileageCalculationRequest, MileageCalculationResponse,
    ExpenseStatsResponse, EmployeeExpenseStats, ValidationResult,
    ExpenseReportFilters,
    AutocompleteResponse, AutocompleteItem
)
from .repository import (
    ExpenseReportRepository, ExpensePolicyRepository,
    MileageRateRepository, EmployeeVehicleRepository
)
from .exceptions import (
    ExpenseReportNotFoundError, ExpenseReportStateError,
    PolicyNotFoundError, PolicyViolationError
)

router = APIRouter(prefix="/expenses", tags=["Expenses"])


# ============== Expense Reports ==============

@router.get("/reports", response_model=ExpenseReportList)
async def list_reports(
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[ExpenseStatus]] = Query(None),
    employee_id: Optional[UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.read")
):
    """Lister les notes de frais."""
    filters = ExpenseReportFilters(
        search=search, status=status, employee_id=employee_id,
        date_from=date_from, date_to=date_to
    )
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)

    return ExpenseReportList(
        items=[ExpenseReportListItem(
            id=r.id,
            code=r.code,
            title=r.title,
            employee_name=r.employee_name,
            status=r.status,
            total_amount=r.total_amount or Decimal("0"),
            total_reimbursable=r.total_reimbursable or Decimal("0"),
            period_start=r.period_start,
            period_end=r.period_end,
            submitted_at=r.submitted_at,
            line_count=len(r.lines) if r.lines else 0
        ) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/reports/my", response_model=ExpenseReportList)
async def list_my_reports(
    status: Optional[List[ExpenseStatus]] = Query(None),
    year: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.read")
):
    """Lister mes notes de frais."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    reports = repo.get_by_employee(current_user.id, year)

    if status:
        reports = [r for r in reports if r.status in [s.value for s in status]]

    total = len(reports)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = reports[start:end]

    return ExpenseReportList(
        items=[ExpenseReportListItem(
            id=r.id,
            code=r.code,
            title=r.title,
            employee_name=r.employee_name,
            status=r.status,
            total_amount=r.total_amount or Decimal("0"),
            total_reimbursable=r.total_reimbursable or Decimal("0"),
            period_start=r.period_start,
            period_end=r.period_end,
            submitted_at=r.submitted_at,
            line_count=len(r.lines) if r.lines else 0
        ) for r in page_items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/reports/pending-approval", response_model=ExpenseReportList)
async def list_pending_approval(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.approve")
):
    """Lister les notes en attente d'approbation."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    reports = repo.get_pending_approval(current_user.id)

    total = len(reports)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = reports[start:end]

    return ExpenseReportList(
        items=[ExpenseReportListItem(
            id=r.id,
            code=r.code,
            title=r.title,
            employee_name=r.employee_name,
            status=r.status,
            total_amount=r.total_amount or Decimal("0"),
            total_reimbursable=r.total_reimbursable or Decimal("0"),
            period_start=r.period_start,
            period_end=r.period_end,
            submitted_at=r.submitted_at,
            line_count=len(r.lines) if r.lines else 0
        ) for r in page_items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/reports/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_reports(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.read")
):
    """Autocomplete notes de frais."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    results = repo.autocomplete(q, limit)
    return AutocompleteResponse(items=[AutocompleteItem(**r) for r in results])


@router.get("/reports/{report_id}", response_model=ExpenseReportResponse)
async def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.read")
):
    """Obtenir une note de frais."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")
    return report


@router.post("/reports", response_model=ExpenseReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    data: ExpenseReportCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.create")
):
    """Créer une note de frais."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)

    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code note de frais déjà existant")

    report_data = data.model_dump()
    report_data["employee_id"] = current_user.id
    report_data["employee_name"] = current_user.full_name if hasattr(current_user, "full_name") else str(current_user.id)

    report = repo.create(report_data, current_user.id)
    return report


@router.put("/reports/{report_id}", response_model=ExpenseReportResponse)
async def update_report(
    report_id: UUID,
    data: ExpenseReportUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.update")
):
    """Mettre à jour une note de frais."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")

    if report.status != ExpenseStatus.DRAFT.value:
        raise HTTPException(status_code=400, detail="Note de frais non modifiable")

    if data.code and repo.code_exists(data.code, report_id):
        raise HTTPException(status_code=409, detail="Code déjà existant")

    update_data = data.model_dump(exclude_unset=True)
    report = repo.update(report, update_data, current_user.id)
    return report


@router.post("/reports/{report_id}/validate", response_model=ValidationResult)
async def validate_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.read")
):
    """Valider une note de frais avant soumission."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")

    policy_repo = ExpensePolicyRepository(db, current_user.tenant_id)
    policy = policy_repo.get_default()

    errors = []
    warnings = []

    # Vérifier les lignes
    for line in report.lines:
        if line.receipt_required and not line.receipt_file_path:
            if policy and line.amount > policy.receipt_required_above:
                errors.append(f"Justificatif manquant: {line.description}")

        if not line.is_policy_compliant:
            warnings.append(f"Non-conformité: {line.policy_violation_reason}")

    # Vérifier les totaux
    if policy:
        if report.total_amount > policy.monthly_limit:
            warnings.append(f"Dépassement limite mensuelle: {report.total_amount} > {policy.monthly_limit}")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        total_amount=report.total_amount or Decimal("0"),
        line_count=len(report.lines)
    )


@router.post("/reports/{report_id}/submit", response_model=ExpenseReportResponse)
async def submit_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.submit")
):
    """Soumettre une note de frais."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")

    if report.status != ExpenseStatus.DRAFT.value:
        raise HTTPException(status_code=400, detail="Note déjà soumise")

    # Déterminer l'approbateur (simplifié)
    approver_id = None  # En production: lookup dans org chart

    try:
        report = repo.submit(report, approver_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return report


@router.post("/reports/{report_id}/approve", response_model=ExpenseReportResponse)
async def approve_report(
    report_id: UUID,
    comments: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.approve")
):
    """Approuver une note de frais."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")

    try:
        report = repo.approve(report, current_user.id, comments)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return report


@router.post("/reports/{report_id}/reject", response_model=ExpenseReportResponse)
async def reject_report(
    report_id: UUID,
    reason: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.approve")
):
    """Rejeter une note de frais."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")

    try:
        report = repo.reject(report, current_user.id, reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return report


@router.post("/reports/{report_id}/mark-paid", response_model=ExpenseReportResponse)
async def mark_report_paid(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.pay")
):
    """Marquer une note comme remboursée."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")

    try:
        report = repo.mark_paid(report, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return report


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.delete")
):
    """Supprimer une note de frais (soft delete)."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")

    if report.status not in [ExpenseStatus.DRAFT.value, ExpenseStatus.REJECTED.value]:
        raise HTTPException(status_code=400, detail="Impossible de supprimer une note soumise")

    repo.soft_delete(report, current_user.id)


# ============== Expense Lines ==============

@router.post("/reports/{report_id}/lines", response_model=ExpenseLineResponse, status_code=status.HTTP_201_CREATED)
async def add_line(
    report_id: UUID,
    data: ExpenseLineCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.update")
):
    """Ajouter une ligne de dépense."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")

    try:
        line = repo.add_line(report, data.model_dump(), current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return line


@router.put("/reports/{report_id}/lines/{line_id}", response_model=ExpenseLineResponse)
async def update_line(
    report_id: UUID,
    line_id: UUID,
    data: ExpenseLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.update")
):
    """Mettre à jour une ligne de dépense."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")

    line = next((l for l in report.lines if l.id == line_id), None)
    if not line:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")

    try:
        line = repo.update_line(line, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return line


@router.delete("/reports/{report_id}/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_line(
    report_id: UUID,
    line_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.update")
):
    """Supprimer une ligne de dépense."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Note de frais non trouvée")

    line = next((l for l in report.lines if l.id == line_id), None)
    if not line:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")

    try:
        repo.remove_line(line)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Mileage ==============

@router.post("/mileage/calculate", response_model=MileageCalculationResponse)
async def calculate_mileage(
    data: MileageCalculationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.read")
):
    """Calculer une indemnité kilométrique."""
    from .service import MILEAGE_RATES_CAR_2024, MILEAGE_RATE_BICYCLE

    # Obtenir le kilométrage annuel actuel
    vehicle_repo = EmployeeVehicleRepository(db, current_user.tenant_id)
    annual_before = vehicle_repo.get_annual_mileage(current_user.id, data.expense_date.year)

    # Calculer la distance totale
    distance = data.distance_km * 2 if data.is_round_trip else data.distance_km
    annual_after = annual_before + distance

    # Déterminer le taux
    if data.vehicle_type == VehicleType.BICYCLE:
        rate = MILEAGE_RATE_BICYCLE
    elif data.vehicle_type == VehicleType.ELECTRIC_BICYCLE:
        rate = MILEAGE_RATE_BICYCLE * Decimal("1.2")
    else:
        rates = MILEAGE_RATES_CAR_2024.get(data.vehicle_type)
        if not rates:
            rates = MILEAGE_RATES_CAR_2024[VehicleType.CAR_5CV]

        if annual_after <= 5000:
            rate = rates["up_to_5000"]
        elif annual_after <= 20000:
            rate = rates["5001_to_20000"]
        else:
            rate = rates["above_20000"]

    amount = (distance * rate).quantize(Decimal("0.01"))

    return MileageCalculationResponse(
        distance_km=distance,
        rate_applied=rate,
        amount=amount,
        vehicle_type=data.vehicle_type,
        annual_mileage_before=annual_before,
        annual_mileage_after=annual_after
    )


# ============== Policies ==============

@router.get("/policies", response_model=List[ExpensePolicyResponse])
async def list_policies(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.policy.read")
):
    """Lister les politiques de dépenses."""
    repo = ExpensePolicyRepository(db, current_user.tenant_id)
    return repo.list_active()


@router.get("/policies/default", response_model=ExpensePolicyResponse)
async def get_default_policy(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.policy.read")
):
    """Obtenir la politique par défaut."""
    repo = ExpensePolicyRepository(db, current_user.tenant_id)
    policy = repo.get_default()
    if not policy:
        raise HTTPException(status_code=404, detail="Aucune politique par défaut")
    return policy


@router.get("/policies/{policy_id}", response_model=ExpensePolicyResponse)
async def get_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.policy.read")
):
    """Obtenir une politique."""
    repo = ExpensePolicyRepository(db, current_user.tenant_id)
    policy = repo.get_by_id(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Politique non trouvée")
    return policy


@router.post("/policies", response_model=ExpensePolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    data: ExpensePolicyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.policy.create")
):
    """Créer une politique."""
    repo = ExpensePolicyRepository(db, current_user.tenant_id)

    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code politique déjà existant")

    policy = repo.create(data.model_dump(), current_user.id)
    return policy


@router.put("/policies/{policy_id}", response_model=ExpensePolicyResponse)
async def update_policy(
    policy_id: UUID,
    data: ExpensePolicyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.policy.update")
):
    """Mettre à jour une politique."""
    repo = ExpensePolicyRepository(db, current_user.tenant_id)
    policy = repo.get_by_id(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Politique non trouvée")

    policy = repo.update(policy, data.model_dump(exclude_unset=True), current_user.id)
    return policy


# ============== Stats ==============

@router.get("/stats", response_model=ExpenseStatsResponse)
async def get_stats(
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.stats.read")
):
    """Obtenir les statistiques de dépenses."""
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    filters = ExpenseReportFilters(date_from=period_start, date_to=period_end)
    items, total = repo.list(filters, page=1, page_size=10000)

    stats = {
        "tenant_id": current_user.tenant_id,
        "period_start": period_start,
        "period_end": period_end,
        "total_reports": total,
        "total_amount": sum(r.total_amount or Decimal("0") for r in items),
        "total_approved": sum(
            r.total_amount or Decimal("0") for r in items
            if r.status in [ExpenseStatus.APPROVED.value, ExpenseStatus.PAID.value]
        ),
        "total_pending": sum(
            r.total_amount or Decimal("0") for r in items
            if r.status in [ExpenseStatus.SUBMITTED.value, ExpenseStatus.PENDING_APPROVAL.value]
        ),
        "total_rejected": sum(
            r.total_amount or Decimal("0") for r in items
            if r.status == ExpenseStatus.REJECTED.value
        ),
        "by_category": {},
        "by_employee": {},
        "by_status": {}
    }

    if items:
        stats["average_per_report"] = stats["total_amount"] / len(items)

    # Par statut
    for r in items:
        stats["by_status"][r.status] = stats["by_status"].get(r.status, 0) + 1

    return ExpenseStatsResponse(**stats)


@router.get("/stats/my", response_model=EmployeeExpenseStats)
async def get_my_stats(
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("expenses.report.read")
):
    """Obtenir mes statistiques de dépenses."""
    year = year or date.today().year
    repo = ExpenseReportRepository(db, current_user.tenant_id)
    reports = repo.get_by_employee(current_user.id, year)

    stats = {
        "employee_id": current_user.id,
        "year": year,
        "report_count": len(reports),
        "total_submitted": sum(
            r.total_amount or Decimal("0") for r in reports
            if r.status not in [ExpenseStatus.DRAFT.value, ExpenseStatus.CANCELLED.value]
        ),
        "total_approved": sum(
            r.total_amount or Decimal("0") for r in reports
            if r.status in [ExpenseStatus.APPROVED.value, ExpenseStatus.PAID.value]
        ),
        "total_paid": sum(
            r.total_amount or Decimal("0") for r in reports
            if r.status == ExpenseStatus.PAID.value
        ),
        "by_category": {}
    }

    stats["total_pending"] = stats["total_submitted"] - stats["total_approved"]

    if reports:
        stats["average_per_report"] = stats["total_submitted"] / len([
            r for r in reports
            if r.status not in [ExpenseStatus.DRAFT.value, ExpenseStatus.CANCELLED.value]
        ]) if any(r.status not in [ExpenseStatus.DRAFT.value, ExpenseStatus.CANCELLED.value] for r in reports) else Decimal("0")

    return EmployeeExpenseStats(**stats)
