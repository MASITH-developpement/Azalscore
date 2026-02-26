"""
AZALS MODULE CONTRACTS - Router
================================

Endpoints API REST pour la gestion des contrats (CLM).
"""
from __future__ import annotations


from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User

from .models import ContractStatus, AlertType
from .schemas import (
    # Contract
    ContractCreate, ContractUpdate, ContractResponse, ContractSummaryResponse,
    ContractListResponse, ContractFilters, ContractStatsResponse,
    ContractDashboardResponse, ContractHistoryResponse,
    # Party
    ContractPartyCreate, ContractPartyUpdate, ContractPartyResponse,
    # Line
    ContractLineCreate, ContractLineUpdate, ContractLineResponse,
    # Clause
    ContractClauseCreate, ContractClauseUpdate, ContractClauseResponse,
    # Obligation
    ContractObligationCreate, ContractObligationUpdate, ContractObligationResponse,
    ObligationCompleteRequest,
    # Milestone
    ContractMilestoneCreate, ContractMilestoneUpdate, ContractMilestoneResponse,
    MilestoneCompleteRequest,
    # Amendment
    ContractAmendmentCreate, ContractAmendmentUpdate, ContractAmendmentResponse,
    # Alert
    ContractAlertCreate, ContractAlertUpdate, ContractAlertResponse,
    AlertAcknowledgeRequest,
    # Approval
    ContractApprovalCreate, ContractApprovalResponse, ApprovalDecisionRequest,
    ApprovalDelegateRequest,
    # Category
    ContractCategoryCreate, ContractCategoryUpdate, ContractCategoryResponse,
    # Template
    ContractTemplateCreate, ContractTemplateUpdate, ContractTemplateResponse,
    ClauseTemplateCreate, ClauseTemplateUpdate, ClauseTemplateResponse,
    # Workflow
    ContractSubmitForApprovalRequest, ContractRecordSignatureRequest,
    ContractTerminateRequest, ContractRenewRequest,
    # Enums
    ContractTypeEnum, ContractStatusEnum
)
from .service import ContractService
from .exceptions import (
    ContractNotFoundError, ContractDuplicateError, ContractValidationError,
    ContractStateError, ContractNotEditableError, PartyNotFoundError,
    ContractLineNotFoundError, ObligationNotFoundError, MilestoneNotFoundError,
    AmendmentNotFoundError, ApprovalNotFoundError, ApprovalNotAuthorizedError,
    TemplateNotFoundError, CategoryNotFoundError, AlertNotFoundError,
    ContractVersionConflictError
)

router = APIRouter(prefix="/contracts", tags=["Contracts - Gestion des Contrats"])


def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> ContractService:
    """Service avec authentification obligatoire."""
    return ContractService(db, tenant_id)


def handle_contract_exception(e: Exception):
    """Gerer les exceptions du module contracts."""
    if isinstance(e, ContractNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, ContractDuplicateError):
        raise HTTPException(status_code=409, detail=str(e))
    elif isinstance(e, ContractValidationError):
        raise HTTPException(status_code=422, detail=str(e))
    elif isinstance(e, (ContractStateError, ContractNotEditableError)):
        raise HTTPException(status_code=400, detail=str(e))
    elif isinstance(e, ContractVersionConflictError):
        raise HTTPException(status_code=409, detail=str(e))
    elif isinstance(e, PartyNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, ContractLineNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, ObligationNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, MilestoneNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, AmendmentNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, ApprovalNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, ApprovalNotAuthorizedError):
        raise HTTPException(status_code=403, detail=str(e))
    elif isinstance(e, TemplateNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, CategoryNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, AlertNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    else:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONTRACTS - CRUD
# ============================================================================

@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    data: ContractCreate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Creer un nouveau contrat."""
    try:
        contract = service.create_contract(data, current_user.id)
        return contract
    except Exception as e:
        handle_contract_exception(e)


@router.get("", response_model=ContractListResponse)
def list_contracts(
    search: Optional[str] = None,
    status: Optional[List[ContractStatusEnum]] = Query(None),
    contract_type: Optional[List[ContractTypeEnum]] = Query(None),
    category_id: Optional[UUID] = None,
    owner_id: Optional[UUID] = None,
    party_name: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    expiring_within_days: Optional[int] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    service: ContractService = Depends(get_service)
):
    """Lister les contrats avec filtres et pagination."""
    from decimal import Decimal

    filters = ContractFilters(
        search=search,
        status=status,
        contract_type=contract_type,
        category_id=category_id,
        owner_id=owner_id,
        party_name=party_name,
        date_from=date_from,
        date_to=date_to,
        expiring_within_days=expiring_within_days,
        min_value=Decimal(str(min_value)) if min_value else None,
        max_value=Decimal(str(max_value)) if max_value else None
    )

    items, total = service.list_contracts(filters, page, page_size, sort_by, sort_dir)
    total_pages = (total + page_size - 1) // page_size

    # Convertir en summaries
    summaries = []
    for c in items:
        party_names = [p.name for p in (c.parties or [])]
        days_expiry = None
        days_renewal = None
        if c.end_date:
            days_expiry = (c.end_date - date.today()).days
        if c.next_renewal_date:
            days_renewal = (c.next_renewal_date - date.today()).days

        summaries.append(ContractSummaryResponse(
            id=c.id,
            contract_number=c.contract_number,
            title=c.title,
            contract_type=c.contract_type,
            status=c.status,
            total_value=c.total_value or 0,
            currency=c.currency,
            start_date=c.start_date,
            end_date=c.end_date,
            owner_name=c.owner_name,
            party_names=party_names,
            days_until_expiry=days_expiry,
            days_until_renewal=days_renewal,
            created_at=c.created_at
        ))

    return ContractListResponse(
        items=summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/search")
def search_contracts(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    service: ContractService = Depends(get_service)
):
    """Recherche rapide de contrats."""
    results = service.search_contracts(q, limit)
    return [
        {
            "id": str(c.id),
            "number": c.contract_number,
            "title": c.title,
            "label": f"[{c.contract_number}] {c.title}"
        }
        for c in results
    ]


@router.get("/stats", response_model=ContractStatsResponse)
def get_statistics(
    service: ContractService = Depends(get_service)
):
    """Statistiques des contrats."""
    return service.get_statistics()


@router.get("/dashboard", response_model=ContractDashboardResponse)
def get_dashboard(
    service: ContractService = Depends(get_service)
):
    """Dashboard des contrats."""
    return service.get_dashboard()


@router.get("/expiring")
def get_expiring_contracts(
    days: int = Query(30, ge=1, le=365),
    service: ContractService = Depends(get_service)
):
    """Contrats expirant bientot."""
    contracts = service.contracts.get_expiring_contracts(days)
    return [
        {
            "id": str(c.id),
            "contract_number": c.contract_number,
            "title": c.title,
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "days_remaining": (c.end_date - date.today()).days if c.end_date else None,
            "total_value": float(c.total_value) if c.total_value else 0
        }
        for c in contracts
    ]


@router.get("/pending-approval")
def get_pending_approvals(
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Contrats en attente d'approbation de l'utilisateur."""
    contracts = service.contracts.get_pending_approvals(current_user.id)
    return contracts


@router.get("/pending-signature")
def get_pending_signatures(
    service: ContractService = Depends(get_service)
):
    """Contrats en attente de signature."""
    return service.contracts.get_pending_signatures()


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: UUID,
    service: ContractService = Depends(get_service)
):
    """Recuperer un contrat par ID."""
    try:
        return service.get_contract(contract_id)
    except Exception as e:
        handle_contract_exception(e)


@router.get("/{contract_id}/history", response_model=List[ContractHistoryResponse])
def get_contract_history(
    contract_id: UUID,
    service: ContractService = Depends(get_service)
):
    """Historique des modifications du contrat."""
    contract = service.get_contract(contract_id)
    return contract.history


@router.patch("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: UUID,
    data: ContractUpdate,
    version: Optional[int] = Query(None, description="Version attendue pour optimistic locking"),
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour un contrat."""
    try:
        return service.update_contract(contract_id, data, current_user.id, version)
    except Exception as e:
        handle_contract_exception(e)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: UUID,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un contrat (soft delete)."""
    try:
        service.delete_contract(contract_id, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


# ============================================================================
# WORKFLOW
# ============================================================================

@router.post("/{contract_id}/submit-review", response_model=ContractResponse)
def submit_for_review(
    contract_id: UUID,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Soumettre pour revision interne."""
    try:
        return service.submit_for_review(contract_id, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/{contract_id}/start-negotiation", response_model=ContractResponse)
def start_negotiation(
    contract_id: UUID,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Passer en negociation."""
    try:
        return service.start_negotiation(contract_id, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/{contract_id}/submit-approval", response_model=ContractResponse)
def submit_for_approval(
    contract_id: UUID,
    data: ContractSubmitForApprovalRequest,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Soumettre pour approbation."""
    try:
        return service.submit_for_approval(contract_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/{contract_id}/approve", response_model=ContractResponse)
def approve_contract(
    contract_id: UUID,
    data: ApprovalDecisionRequest,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Approuver ou rejeter un contrat."""
    try:
        return service.approve_contract(contract_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/{contract_id}/record-signature", response_model=ContractPartyResponse)
def record_signature(
    contract_id: UUID,
    data: ContractRecordSignatureRequest,
    service: ContractService = Depends(get_service)
):
    """Enregistrer une signature."""
    try:
        return service.record_signature(
            contract_id,
            data.party_id,
            data.signature_id,
            data.signature_ip
        )
    except Exception as e:
        handle_contract_exception(e)


@router.post("/{contract_id}/activate", response_model=ContractResponse)
def activate_contract(
    contract_id: UUID,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Activer un contrat."""
    try:
        return service.activate_contract(contract_id, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/{contract_id}/suspend", response_model=ContractResponse)
def suspend_contract(
    contract_id: UUID,
    reason: str = Query(..., min_length=1),
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Suspendre un contrat."""
    try:
        return service.suspend_contract(contract_id, reason, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/{contract_id}/resume", response_model=ContractResponse)
def resume_contract(
    contract_id: UUID,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Reprendre un contrat suspendu."""
    try:
        return service.resume_contract(contract_id, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/{contract_id}/terminate", response_model=ContractResponse)
def terminate_contract(
    contract_id: UUID,
    data: ContractTerminateRequest,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Resilier un contrat."""
    try:
        return service.terminate_contract(contract_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/{contract_id}/renew", response_model=ContractResponse)
def renew_contract(
    contract_id: UUID,
    data: ContractRenewRequest,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Renouveler un contrat."""
    try:
        return service.renew_contract(contract_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


# ============================================================================
# PARTIES
# ============================================================================

@router.get("/{contract_id}/parties", response_model=List[ContractPartyResponse])
def list_parties(
    contract_id: UUID,
    service: ContractService = Depends(get_service)
):
    """Lister les parties d'un contrat."""
    return service.parties.get_by_contract(contract_id)


@router.post("/{contract_id}/parties", response_model=ContractPartyResponse, status_code=status.HTTP_201_CREATED)
def add_party(
    contract_id: UUID,
    data: ContractPartyCreate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Ajouter une partie au contrat."""
    try:
        return service.add_party(contract_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.patch("/parties/{party_id}", response_model=ContractPartyResponse)
def update_party(
    party_id: UUID,
    data: ContractPartyUpdate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une partie."""
    try:
        return service.update_party(party_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


# ============================================================================
# LINES
# ============================================================================

@router.get("/{contract_id}/lines", response_model=List[ContractLineResponse])
def list_lines(
    contract_id: UUID,
    service: ContractService = Depends(get_service)
):
    """Lister les lignes d'un contrat."""
    return service.lines.get_by_contract(contract_id)


@router.post("/{contract_id}/lines", response_model=ContractLineResponse, status_code=status.HTTP_201_CREATED)
def add_line(
    contract_id: UUID,
    data: ContractLineCreate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Ajouter une ligne au contrat."""
    try:
        return service.add_line(contract_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.patch("/lines/{line_id}", response_model=ContractLineResponse)
def update_line(
    line_id: UUID,
    data: ContractLineUpdate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une ligne."""
    try:
        return service.update_line(line_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line(
    line_id: UUID,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une ligne."""
    try:
        service.delete_line(line_id, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.get("/lines/recurring")
def get_recurring_lines(
    service: ContractService = Depends(get_service)
):
    """Lignes avec facturation recurrente."""
    return service.lines.get_recurring_lines()


@router.get("/lines/due-billing")
def get_lines_due_for_billing(
    before_date: Optional[date] = None,
    service: ContractService = Depends(get_service)
):
    """Lignes dues pour facturation."""
    return service.lines.get_lines_due_for_billing(before_date)


# ============================================================================
# OBLIGATIONS
# ============================================================================

@router.get("/{contract_id}/obligations", response_model=List[ContractObligationResponse])
def list_obligations(
    contract_id: UUID,
    service: ContractService = Depends(get_service)
):
    """Lister les obligations d'un contrat."""
    return service.obligations.get_by_contract(contract_id)


@router.post("/{contract_id}/obligations", response_model=ContractObligationResponse, status_code=status.HTTP_201_CREATED)
def add_obligation(
    contract_id: UUID,
    data: ContractObligationCreate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Ajouter une obligation."""
    try:
        return service.add_obligation(contract_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/obligations/{obligation_id}/complete", response_model=ContractObligationResponse)
def complete_obligation(
    obligation_id: UUID,
    data: ObligationCompleteRequest,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Completer une obligation."""
    try:
        return service.complete_obligation(
            obligation_id,
            current_user.id,
            data.completion_notes,
            data.evidence_document_id
        )
    except Exception as e:
        handle_contract_exception(e)


@router.get("/obligations/overdue", response_model=List[ContractObligationResponse])
def get_overdue_obligations(
    service: ContractService = Depends(get_service)
):
    """Obligations en retard."""
    return service.get_overdue_obligations()


@router.get("/obligations/upcoming", response_model=List[ContractObligationResponse])
def get_upcoming_obligations(
    days: int = Query(30, ge=1, le=365),
    service: ContractService = Depends(get_service)
):
    """Obligations a venir."""
    return service.get_upcoming_obligations(days)


# ============================================================================
# MILESTONES
# ============================================================================

@router.get("/{contract_id}/milestones", response_model=List[ContractMilestoneResponse])
def list_milestones(
    contract_id: UUID,
    service: ContractService = Depends(get_service)
):
    """Lister les jalons d'un contrat."""
    return service.milestones.get_by_contract(contract_id)


@router.post("/{contract_id}/milestones", response_model=ContractMilestoneResponse, status_code=status.HTTP_201_CREATED)
def add_milestone(
    contract_id: UUID,
    data: ContractMilestoneCreate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Ajouter un jalon."""
    try:
        return service.add_milestone(contract_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/milestones/{milestone_id}/complete", response_model=ContractMilestoneResponse)
def complete_milestone(
    milestone_id: UUID,
    data: MilestoneCompleteRequest,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Completer un jalon."""
    try:
        return service.complete_milestone(
            milestone_id,
            current_user.id,
            data.actual_date,
            data.notes,
            data.trigger_payment
        )
    except Exception as e:
        handle_contract_exception(e)


@router.get("/milestones/upcoming", response_model=List[ContractMilestoneResponse])
def get_upcoming_milestones(
    days: int = Query(30, ge=1, le=365),
    service: ContractService = Depends(get_service)
):
    """Jalons a venir."""
    return service.get_upcoming_milestones(days)


# ============================================================================
# AMENDMENTS
# ============================================================================

@router.get("/{contract_id}/amendments", response_model=List[ContractAmendmentResponse])
def list_amendments(
    contract_id: UUID,
    service: ContractService = Depends(get_service)
):
    """Lister les avenants d'un contrat."""
    return service.amendments.get_by_contract(contract_id)


@router.post("/{contract_id}/amendments", response_model=ContractAmendmentResponse, status_code=status.HTTP_201_CREATED)
def create_amendment(
    contract_id: UUID,
    data: ContractAmendmentCreate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Creer un avenant."""
    try:
        return service.create_amendment(contract_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.post("/amendments/{amendment_id}/apply", response_model=ContractResponse)
def apply_amendment(
    amendment_id: UUID,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Appliquer un avenant."""
    try:
        return service.apply_amendment(amendment_id, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


# ============================================================================
# ALERTS
# ============================================================================

@router.get("/{contract_id}/alerts", response_model=List[ContractAlertResponse])
def list_contract_alerts(
    contract_id: UUID,
    service: ContractService = Depends(get_service)
):
    """Lister les alertes d'un contrat."""
    return service.alerts.get_by_contract(contract_id)


@router.post("/{contract_id}/alerts", response_model=ContractAlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    contract_id: UUID,
    data: ContractAlertCreate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Creer une alerte manuelle."""
    try:
        return service.create_alert(contract_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.get("/alerts/active", response_model=List[ContractAlertResponse])
def get_active_alerts(
    service: ContractService = Depends(get_service)
):
    """Alertes actives."""
    return service.get_active_alerts()


@router.post("/alerts/{alert_id}/acknowledge", response_model=ContractAlertResponse)
def acknowledge_alert(
    alert_id: UUID,
    data: AlertAcknowledgeRequest,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Acquitter une alerte."""
    try:
        return service.acknowledge_alert(
            alert_id,
            current_user.id,
            data.notes,
            data.action_taken
        )
    except Exception as e:
        handle_contract_exception(e)


@router.post("/alerts/check-and-create")
def check_and_create_alerts(
    service: ContractService = Depends(get_service)
):
    """Verifier et creer les alertes automatiques."""
    alerts = service.check_and_create_alerts()
    return {"created_count": len(alerts), "alerts": alerts}


@router.post("/alerts/process-pending")
def process_pending_alerts(
    service: ContractService = Depends(get_service)
):
    """Traiter les alertes en attente."""
    sent = service.process_pending_alerts()
    return {"sent_count": len(sent)}


# ============================================================================
# CATEGORIES
# ============================================================================

@router.get("/config/categories", response_model=List[ContractCategoryResponse])
def list_categories(
    active_only: bool = True,
    service: ContractService = Depends(get_service)
):
    """Lister les categories."""
    return service.list_categories(active_only)


@router.post("/config/categories", response_model=ContractCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: ContractCategoryCreate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Creer une categorie."""
    try:
        return service.create_category(data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.patch("/config/categories/{category_id}", response_model=ContractCategoryResponse)
def update_category(
    category_id: UUID,
    data: ContractCategoryUpdate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une categorie."""
    try:
        category = service.categories.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError(str(category_id))
        update_data = data.model_dump(exclude_unset=True)
        return service.categories.update(category, update_data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


# ============================================================================
# TEMPLATES
# ============================================================================

@router.get("/config/templates", response_model=List[ContractTemplateResponse])
def list_templates(
    contract_type: Optional[str] = None,
    active_only: bool = True,
    service: ContractService = Depends(get_service)
):
    """Lister les templates."""
    return service.list_templates(contract_type, active_only)


@router.post("/config/templates", response_model=ContractTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    data: ContractTemplateCreate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Creer un template."""
    try:
        return service.create_template(data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


@router.get("/config/templates/{template_id}", response_model=ContractTemplateResponse)
def get_template(
    template_id: UUID,
    service: ContractService = Depends(get_service)
):
    """Recuperer un template."""
    template = service.templates.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouve")
    return template


@router.patch("/config/templates/{template_id}", response_model=ContractTemplateResponse)
def update_template(
    template_id: UUID,
    data: ContractTemplateUpdate,
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour un template."""
    try:
        return service.update_template(template_id, data, current_user.id)
    except Exception as e:
        handle_contract_exception(e)


# ============================================================================
# METRICS
# ============================================================================

@router.post("/metrics/calculate")
def calculate_metrics(
    metric_date: Optional[date] = None,
    service: ContractService = Depends(get_service)
):
    """Calculer et sauvegarder les metriques."""
    metrics = service.calculate_metrics(metric_date)
    return metrics


@router.get("/metrics/{metric_date}")
def get_metrics(
    metric_date: date,
    service: ContractService = Depends(get_service)
):
    """Recuperer les metriques d'une date."""
    metrics = service.metrics.get_by_date(metric_date)
    if not metrics:
        raise HTTPException(status_code=404, detail="Metriques non trouvees")
    return metrics


@router.get("/metrics/range")
def get_metrics_range(
    start_date: date,
    end_date: date,
    service: ContractService = Depends(get_service)
):
    """Recuperer les metriques sur une periode."""
    return service.metrics.get_range(start_date, end_date)


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

@router.post("/batch/process-renewals")
def process_automatic_renewals(
    service: ContractService = Depends(get_service)
):
    """Traiter les renouvellements automatiques."""
    renewed = service.process_automatic_renewals()
    return {
        "renewed_count": len(renewed),
        "contracts": [
            {"id": str(c.id), "number": c.contract_number}
            for c in renewed
        ]
    }


@router.post("/batch/expire-contracts")
def expire_contracts(
    service: ContractService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Marquer les contrats expires."""
    expired_contracts = service.contracts._base_query().filter(
        Contract.status == ContractStatus.ACTIVE.value,
        Contract.end_date < date.today()
    ).all()

    count = 0
    for contract in expired_contracts:
        service.expire_contract(contract.id, current_user.id)
        count += 1

    return {"expired_count": count}
