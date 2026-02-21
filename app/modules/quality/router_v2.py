"""
AZALS MODULE M7 - Router Qualité v2 - CORE SaaS
================================================

Endpoints FastAPI pour le module de gestion de la qualité.
Version 2 avec support SaaSContext pour multi-tenancy.

Migration CORE SaaS v2: Utilise SaaSContext au lieu de get_current_user + get_tenant_id
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.routines import require_entity
from app.core.saas_context import SaaSContext
from app.modules.quality.models import (
    AuditStatus,
    AuditType,
    CAPAStatus,
    CAPAType,
    CertificationStatus,
    ClaimStatus,
    ControlResult,
    ControlStatus,
    ControlType,
    NonConformanceSeverity,
    NonConformanceStatus,
    NonConformanceType,
)
from app.modules.quality.schemas import (
    AuditClose,
    AuditCreate,
    AuditFindingCreate,
    AuditFindingResponse,
    AuditFindingUpdate,
    AuditResponse,
    AuditUpdate,
    CAPAActionCreate,
    CAPAActionResponse,
    CAPAActionUpdate,
    CAPAClose,
    CAPACreate,
    CAPAResponse,
    CAPAUpdate,
    CertificationAuditCreate,
    CertificationAuditResponse,
    CertificationAuditUpdate,
    CertificationCreate,
    CertificationResponse,
    CertificationUpdate,
    ClaimActionCreate,
    ClaimActionResponse,
    ClaimClose,
    ClaimCreate,
    ClaimResolve,
    ClaimRespond,
    ClaimResponse,
    ClaimUpdate,
    ControlCreate,
    ControlLineUpdate,
    ControlResponse,
    ControlTemplateCreate,
    ControlTemplateItemCreate,
    ControlTemplateItemResponse,
    ControlTemplateResponse,
    ControlTemplateUpdate,
    ControlUpdate,
    IndicatorCreate,
    IndicatorMeasurementCreate,
    IndicatorMeasurementResponse,
    IndicatorResponse,
    IndicatorUpdate,
    NonConformanceActionCreate,
    NonConformanceActionResponse,
    NonConformanceActionUpdate,
    NonConformanceClose,
    NonConformanceCreate,
    NonConformanceResponse,
    NonConformanceUpdate,
    PaginatedAuditResponse,
    PaginatedCAPAResponse,
    PaginatedCertificationResponse,
    PaginatedClaimResponse,
    PaginatedControlResponse,
    PaginatedControlTemplateResponse,
    PaginatedIndicatorResponse,
    PaginatedNCResponse,
    QualityDashboard,
)
from app.modules.quality.service import QualityService, get_quality_service


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def _get_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> QualityService:
    """
    Dépendance FastAPI pour obtenir le service Quality.

    Cette fonction wrapper permet de facilement remplacer le service
    dans les tests via app.dependency_overrides[_get_service].
    """
    return get_quality_service(db, context.tenant_id, str(context.user_id))


router = APIRouter(prefix="/v2/quality", tags=["Quality v2 - CORE SaaS"])


# ============================================================================
# NON-CONFORMITÉS
# ============================================================================

@router.post("/non-conformances", response_model=NonConformanceResponse)
def create_non_conformance(
    data: NonConformanceCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Crée une nouvelle non-conformité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return service.create_non_conformance(data)


@router.get("/non-conformances", response_model=PaginatedNCResponse)
def list_non_conformances(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    nc_type: NonConformanceType | None = None,
    status: NonConformanceStatus | None = None,
    severity: NonConformanceSeverity | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Liste les non-conformités"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    items, total = service.list_non_conformances(
        skip=skip,
        limit=limit,
        nc_type=nc_type,
        status=status,
        severity=severity,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
    return PaginatedNCResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/non-conformances/{nc_id}", response_model=NonConformanceResponse)
def get_non_conformance(
    nc_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère une non-conformité par ID"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.get_non_conformance(nc_id), "Non-conformité", nc_id)


@router.put("/non-conformances/{nc_id}", response_model=NonConformanceResponse)
def update_non_conformance(
    nc_id: int,
    data: NonConformanceUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour une non-conformité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_non_conformance(nc_id, data), "Non-conformité", nc_id)


@router.post("/non-conformances/{nc_id}/open", response_model=NonConformanceResponse)
def open_non_conformance(
    nc_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Ouvre une non-conformité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(
        service.open_non_conformance(nc_id), "Non-conformité", nc_id, status_code=400
    )


@router.post("/non-conformances/{nc_id}/close", response_model=NonConformanceResponse)
def close_non_conformance(
    nc_id: int,
    data: NonConformanceClose,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Clôture une non-conformité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.close_non_conformance(nc_id, data), "Non-conformité", nc_id)


@router.post("/non-conformances/{nc_id}/actions", response_model=NonConformanceActionResponse)
def add_nc_action(
    nc_id: int,
    data: NonConformanceActionCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Ajoute une action à une non-conformité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.add_nc_action(nc_id, data), "Non-conformité", nc_id)


@router.put("/nc-actions/{action_id}", response_model=NonConformanceActionResponse)
def update_nc_action(
    action_id: int,
    data: NonConformanceActionUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour une action de non-conformité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_nc_action(action_id, data), "Action NC", action_id)


# ============================================================================
# TEMPLATES DE CONTRÔLE
# ============================================================================

@router.post("/control-templates", response_model=ControlTemplateResponse)
def create_control_template(
    data: ControlTemplateCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Crée un template de contrôle qualité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return service.create_control_template(data)


@router.get("/control-templates", response_model=PaginatedControlTemplateResponse)
def list_control_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    control_type: ControlType | None = None,
    active_only: bool = True,
    search: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Liste les templates de contrôle"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    items, total = service.list_control_templates(
        skip=skip,
        limit=limit,
        control_type=control_type,
        active_only=active_only,
        search=search,
    )
    return PaginatedControlTemplateResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/control-templates/{template_id}", response_model=ControlTemplateResponse)
def get_control_template(
    template_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère un template par ID"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.get_control_template(template_id), "Template", template_id)


@router.put("/control-templates/{template_id}", response_model=ControlTemplateResponse)
def update_control_template(
    template_id: int,
    data: ControlTemplateUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour un template"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_control_template(template_id, data), "Template", template_id)


@router.post("/control-templates/{template_id}/items", response_model=ControlTemplateItemResponse)
def add_template_item(
    template_id: int,
    data: ControlTemplateItemCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Ajoute un item à un template"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.add_template_item(template_id, data), "Template", template_id)


# ============================================================================
# CONTRÔLES QUALITÉ
# ============================================================================

@router.post("/controls", response_model=ControlResponse)
def create_control(
    data: ControlCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Crée un contrôle qualité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return service.create_control(data)


@router.get("/controls", response_model=PaginatedControlResponse)
def list_controls(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    control_type: ControlType | None = None,
    status: ControlStatus | None = None,
    result: ControlResult | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Liste les contrôles qualité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    items, total = service.list_controls(
        skip=skip,
        limit=limit,
        control_type=control_type,
        status=status,
        result=result,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
    return PaginatedControlResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/controls/{control_id}", response_model=ControlResponse)
def get_control(
    control_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère un contrôle par ID"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.get_control(control_id), "Contrôle", control_id)


@router.put("/controls/{control_id}", response_model=ControlResponse)
def update_control(
    control_id: int,
    data: ControlUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour un contrôle"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_control(control_id, data), "Contrôle", control_id)


@router.post("/controls/{control_id}/start", response_model=ControlResponse)
def start_control(
    control_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Démarre un contrôle"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.start_control(control_id), "Contrôle", control_id)


@router.put("/control-lines/{line_id}", response_model=ControlResponse)
def update_control_line(
    line_id: int,
    data: ControlLineUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour une ligne de contrôle"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    line = require_entity(service.update_control_line(line_id, data), "Ligne contrôle", line_id)
    # Retourner le contrôle complet
    return service.get_control(line.control_id)


@router.post("/controls/{control_id}/complete", response_model=ControlResponse)
def complete_control(
    control_id: int,
    decision: str = Query(..., description="ACCEPT, REJECT, CONDITIONAL, REWORK"),
    comments: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Termine un contrôle qualité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.complete_control(control_id, decision, comments), "Contrôle", control_id)


# ============================================================================
# AUDITS
# ============================================================================

@router.post("/audits", response_model=AuditResponse)
def create_audit(
    data: AuditCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Crée un audit"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return service.create_audit(data)


@router.get("/audits", response_model=PaginatedAuditResponse)
def list_audits(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    audit_type: AuditType | None = None,
    status: AuditStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Liste les audits"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    items, total = service.list_audits(
        skip=skip,
        limit=limit,
        audit_type=audit_type,
        status=status,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
    return PaginatedAuditResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/audits/{audit_id}", response_model=AuditResponse)
def get_audit(
    audit_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère un audit par ID"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.get_audit(audit_id), "Audit", audit_id)


@router.put("/audits/{audit_id}", response_model=AuditResponse)
def update_audit(
    audit_id: int,
    data: AuditUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour un audit"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_audit(audit_id, data), "Audit", audit_id)


@router.post("/audits/{audit_id}/start", response_model=AuditResponse)
def start_audit(
    audit_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Démarre un audit"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.start_audit(audit_id), "Audit", audit_id)


@router.post("/audits/{audit_id}/findings", response_model=AuditFindingResponse)
def add_finding(
    audit_id: int,
    data: AuditFindingCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Ajoute un constat à un audit"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.add_finding(audit_id, data), "Audit", audit_id)


@router.put("/audit-findings/{finding_id}", response_model=AuditFindingResponse)
def update_finding(
    finding_id: int,
    data: AuditFindingUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour un constat"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_finding(finding_id, data), "Constat", finding_id)


@router.post("/audits/{audit_id}/close", response_model=AuditResponse)
def close_audit(
    audit_id: int,
    data: AuditClose,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Clôture un audit"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.close_audit(audit_id, data), "Audit", audit_id)


# ============================================================================
# CAPA
# ============================================================================

@router.post("/capas", response_model=CAPAResponse)
def create_capa(
    data: CAPACreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Crée un CAPA"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return service.create_capa(data)


@router.get("/capas", response_model=PaginatedCAPAResponse)
def list_capas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    capa_type: CAPAType | None = None,
    status: CAPAStatus | None = None,
    priority: str | None = None,
    owner_id: int | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Liste les CAPA"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    items, total = service.list_capas(
        skip=skip,
        limit=limit,
        capa_type=capa_type,
        status=status,
        priority=priority,
        owner_id=owner_id,
        search=search,
    )
    return PaginatedCAPAResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/capas/{capa_id}", response_model=CAPAResponse)
def get_capa(
    capa_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère un CAPA par ID"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.get_capa(capa_id), "CAPA", capa_id)


@router.put("/capas/{capa_id}", response_model=CAPAResponse)
def update_capa(
    capa_id: int,
    data: CAPAUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour un CAPA"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_capa(capa_id, data), "CAPA", capa_id)


@router.post("/capas/{capa_id}/actions", response_model=CAPAActionResponse)
def add_capa_action(
    capa_id: int,
    data: CAPAActionCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Ajoute une action à un CAPA"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.add_capa_action(capa_id, data), "CAPA", capa_id)


@router.put("/capa-actions/{action_id}", response_model=CAPAActionResponse)
def update_capa_action(
    action_id: int,
    data: CAPAActionUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour une action CAPA"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_capa_action(action_id, data), "Action CAPA", action_id)


@router.post("/capas/{capa_id}/close", response_model=CAPAResponse)
def close_capa(
    capa_id: int,
    data: CAPAClose,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Clôture un CAPA"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.close_capa(capa_id, data), "CAPA", capa_id)


# ============================================================================
# RÉCLAMATIONS CLIENTS
# ============================================================================

@router.post("/claims", response_model=ClaimResponse)
def create_claim(
    data: ClaimCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Crée une réclamation client"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return service.create_claim(data)


@router.get("/claims", response_model=PaginatedClaimResponse)
def list_claims(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: ClaimStatus | None = None,
    customer_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Liste les réclamations"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    items, total = service.list_claims(
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
    return PaginatedClaimResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/claims/{claim_id}", response_model=ClaimResponse)
def get_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère une réclamation par ID"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.get_claim(claim_id), "Réclamation", claim_id)


@router.put("/claims/{claim_id}", response_model=ClaimResponse)
def update_claim(
    claim_id: int,
    data: ClaimUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour une réclamation"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_claim(claim_id, data), "Réclamation", claim_id)


@router.post("/claims/{claim_id}/acknowledge", response_model=ClaimResponse)
def acknowledge_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Accuse réception d'une réclamation"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.acknowledge_claim(claim_id), "Réclamation", claim_id)


@router.post("/claims/{claim_id}/respond", response_model=ClaimResponse)
def respond_claim(
    claim_id: int,
    data: ClaimRespond,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Répond à une réclamation"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.respond_claim(claim_id, data), "Réclamation", claim_id)


@router.post("/claims/{claim_id}/resolve", response_model=ClaimResponse)
def resolve_claim(
    claim_id: int,
    data: ClaimResolve,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Résout une réclamation"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.resolve_claim(claim_id, data), "Réclamation", claim_id)


@router.post("/claims/{claim_id}/close", response_model=ClaimResponse)
def close_claim(
    claim_id: int,
    data: ClaimClose,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Clôture une réclamation"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.close_claim(claim_id, data), "Réclamation", claim_id)


@router.post("/claims/{claim_id}/actions", response_model=ClaimActionResponse)
def add_claim_action(
    claim_id: int,
    data: ClaimActionCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Ajoute une action à une réclamation"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.add_claim_action(claim_id, data), "Réclamation", claim_id)


# ============================================================================
# INDICATEURS QUALITÉ
# ============================================================================

@router.post("/indicators", response_model=IndicatorResponse)
def create_indicator(
    data: IndicatorCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Crée un indicateur qualité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return service.create_indicator(data)


@router.get("/indicators", response_model=PaginatedIndicatorResponse)
def list_indicators(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: str | None = None,
    active_only: bool = True,
    search: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Liste les indicateurs"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    items, total = service.list_indicators(
        skip=skip,
        limit=limit,
        category=category,
        active_only=active_only,
        search=search,
    )
    return PaginatedIndicatorResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/indicators/{indicator_id}", response_model=IndicatorResponse)
def get_indicator(
    indicator_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère un indicateur par ID"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.get_indicator(indicator_id), "Indicateur", indicator_id)


@router.put("/indicators/{indicator_id}", response_model=IndicatorResponse)
def update_indicator(
    indicator_id: int,
    data: IndicatorUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour un indicateur"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_indicator(indicator_id, data), "Indicateur", indicator_id)


@router.post("/indicators/{indicator_id}/measurements", response_model=IndicatorMeasurementResponse)
def add_measurement(
    indicator_id: int,
    data: IndicatorMeasurementCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Ajoute une mesure à un indicateur"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.add_measurement(indicator_id, data), "Indicateur", indicator_id)


# ============================================================================
# CERTIFICATIONS
# ============================================================================

@router.post("/certifications", response_model=CertificationResponse)
def create_certification(
    data: CertificationCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Crée une certification"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return service.create_certification(data)


@router.get("/certifications", response_model=PaginatedCertificationResponse)
def list_certifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: CertificationStatus | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Liste les certifications"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    items, total = service.list_certifications(
        skip=skip,
        limit=limit,
        status=status,
        search=search,
    )
    return PaginatedCertificationResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/certifications/{cert_id}", response_model=CertificationResponse)
def get_certification(
    cert_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère une certification par ID"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.get_certification(cert_id), "Certification", cert_id)


@router.put("/certifications/{cert_id}", response_model=CertificationResponse)
def update_certification(
    cert_id: int,
    data: CertificationUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour une certification"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_certification(cert_id, data), "Certification", cert_id)


@router.post("/certifications/{cert_id}/audits", response_model=CertificationAuditResponse)
def add_certification_audit(
    cert_id: int,
    data: CertificationAuditCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Ajoute un audit à une certification"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.add_certification_audit(cert_id, data), "Certification", cert_id)


@router.put("/certification-audits/{audit_id}", response_model=CertificationAuditResponse)
def update_certification_audit(
    audit_id: int,
    data: CertificationAuditUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour un audit de certification"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return require_entity(service.update_certification_audit(audit_id, data), "Audit certification", audit_id)


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=QualityDashboard)
def get_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère les statistiques du dashboard qualité"""
    service = get_quality_service(db, context.tenant_id, str(context.user_id))
    return service.get_dashboard()
