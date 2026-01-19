"""
AZALS MODULE M7 - Router Qualité
================================

Endpoints FastAPI pour le module de gestion de la qualité.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
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
    # Audits
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
    # CAPA
    CAPACreate,
    CAPAResponse,
    CAPAUpdate,
    CertificationAuditCreate,
    CertificationAuditResponse,
    CertificationAuditUpdate,
    # Certifications
    CertificationCreate,
    CertificationResponse,
    CertificationUpdate,
    ClaimActionCreate,
    ClaimActionResponse,
    ClaimClose,
    # Réclamations
    ClaimCreate,
    ClaimResolve,
    ClaimRespond,
    ClaimResponse,
    ClaimUpdate,
    # Contrôles
    ControlCreate,
    ControlLineUpdate,
    ControlResponse,
    # Templates
    ControlTemplateCreate,
    ControlTemplateItemCreate,
    ControlTemplateItemResponse,
    ControlTemplateResponse,
    ControlTemplateUpdate,
    ControlUpdate,
    # Indicateurs
    IndicatorCreate,
    IndicatorMeasurementCreate,
    IndicatorMeasurementResponse,
    IndicatorResponse,
    IndicatorUpdate,
    NonConformanceActionCreate,
    NonConformanceActionResponse,
    NonConformanceActionUpdate,
    NonConformanceClose,
    # Non-conformités
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
    # Dashboard
    QualityDashboard,
)
from app.modules.quality.service import get_quality_service

router = APIRouter(prefix="/quality", tags=["Quality Management"])


# ============================================================================
# NON-CONFORMITÉS
# ============================================================================

@router.post("/non-conformances", response_model=NonConformanceResponse)
def create_non_conformance(
    data: NonConformanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crée une nouvelle non-conformité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Liste les non-conformités"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Récupère une non-conformité par ID"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    nc = service.get_non_conformance(nc_id)
    if not nc:
        raise HTTPException(status_code=404, detail="Non-conformité non trouvée")
    return nc


@router.put("/non-conformances/{nc_id}", response_model=NonConformanceResponse)
def update_non_conformance(
    nc_id: int,
    data: NonConformanceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour une non-conformité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    nc = service.update_non_conformance(nc_id, data)
    if not nc:
        raise HTTPException(status_code=404, detail="Non-conformité non trouvée")
    return nc


@router.post("/non-conformances/{nc_id}/open", response_model=NonConformanceResponse)
def open_non_conformance(
    nc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ouvre une non-conformité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    nc = service.open_non_conformance(nc_id)
    if not nc:
        raise HTTPException(status_code=400, detail="Impossible d'ouvrir la non-conformité")
    return nc


@router.post("/non-conformances/{nc_id}/close", response_model=NonConformanceResponse)
def close_non_conformance(
    nc_id: int,
    data: NonConformanceClose,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Clôture une non-conformité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    nc = service.close_non_conformance(nc_id, data)
    if not nc:
        raise HTTPException(status_code=404, detail="Non-conformité non trouvée")
    return nc


@router.post("/non-conformances/{nc_id}/actions", response_model=NonConformanceActionResponse)
def add_nc_action(
    nc_id: int,
    data: NonConformanceActionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ajoute une action à une non-conformité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    action = service.add_nc_action(nc_id, data)
    if not action:
        raise HTTPException(status_code=404, detail="Non-conformité non trouvée")
    return action


@router.put("/nc-actions/{action_id}", response_model=NonConformanceActionResponse)
def update_nc_action(
    action_id: int,
    data: NonConformanceActionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour une action de non-conformité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    action = service.update_nc_action(action_id, data)
    if not action:
        raise HTTPException(status_code=404, detail="Action non trouvée")
    return action


# ============================================================================
# TEMPLATES DE CONTRÔLE
# ============================================================================

@router.post("/control-templates", response_model=ControlTemplateResponse)
def create_control_template(
    data: ControlTemplateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crée un template de contrôle qualité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    return service.create_control_template(data)


@router.get("/control-templates", response_model=PaginatedControlTemplateResponse)
def list_control_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    control_type: ControlType | None = None,
    active_only: bool = True,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Liste les templates de contrôle"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Récupère un template par ID"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    template = service.get_control_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@router.put("/control-templates/{template_id}", response_model=ControlTemplateResponse)
def update_control_template(
    template_id: int,
    data: ControlTemplateUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour un template"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    template = service.update_control_template(template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@router.post("/control-templates/{template_id}/items", response_model=ControlTemplateItemResponse)
def add_template_item(
    template_id: int,
    data: ControlTemplateItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ajoute un item à un template"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    item = service.add_template_item(template_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return item


# ============================================================================
# CONTRÔLES QUALITÉ
# ============================================================================

@router.post("/controls", response_model=ControlResponse)
def create_control(
    data: ControlCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crée un contrôle qualité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Liste les contrôles qualité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Récupère un contrôle par ID"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    control = service.get_control(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Contrôle non trouvé")
    return control


@router.put("/controls/{control_id}", response_model=ControlResponse)
def update_control(
    control_id: int,
    data: ControlUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour un contrôle"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    control = service.update_control(control_id, data)
    if not control:
        raise HTTPException(status_code=404, detail="Contrôle non trouvé")
    return control


@router.post("/controls/{control_id}/start", response_model=ControlResponse)
def start_control(
    control_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Démarre un contrôle"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    control = service.start_control(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Contrôle non trouvé")
    return control


@router.put("/control-lines/{line_id}", response_model=ControlResponse)
def update_control_line(
    line_id: int,
    data: ControlLineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour une ligne de contrôle"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    line = service.update_control_line(line_id, data)
    if not line:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    # Retourner le contrôle complet
    control = service.get_control(line.control_id)
    return control


@router.post("/controls/{control_id}/complete", response_model=ControlResponse)
def complete_control(
    control_id: int,
    decision: str = Query(..., description="ACCEPT, REJECT, CONDITIONAL, REWORK"),
    comments: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Termine un contrôle qualité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    control = service.complete_control(control_id, decision, comments)
    if not control:
        raise HTTPException(status_code=404, detail="Contrôle non trouvé")
    return control


# ============================================================================
# AUDITS
# ============================================================================

@router.post("/audits", response_model=AuditResponse)
def create_audit(
    data: AuditCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crée un audit"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Liste les audits"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Récupère un audit par ID"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    audit = service.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")
    return audit


@router.put("/audits/{audit_id}", response_model=AuditResponse)
def update_audit(
    audit_id: int,
    data: AuditUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour un audit"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    audit = service.update_audit(audit_id, data)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")
    return audit


@router.post("/audits/{audit_id}/start", response_model=AuditResponse)
def start_audit(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Démarre un audit"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    audit = service.start_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")
    return audit


@router.post("/audits/{audit_id}/findings", response_model=AuditFindingResponse)
def add_finding(
    audit_id: int,
    data: AuditFindingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ajoute un constat à un audit"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    finding = service.add_finding(audit_id, data)
    if not finding:
        raise HTTPException(status_code=404, detail="Audit non trouvé")
    return finding


@router.put("/audit-findings/{finding_id}", response_model=AuditFindingResponse)
def update_finding(
    finding_id: int,
    data: AuditFindingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour un constat"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    finding = service.update_finding(finding_id, data)
    if not finding:
        raise HTTPException(status_code=404, detail="Constat non trouvé")
    return finding


@router.post("/audits/{audit_id}/close", response_model=AuditResponse)
def close_audit(
    audit_id: int,
    data: AuditClose,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Clôture un audit"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    audit = service.close_audit(audit_id, data)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")
    return audit


# ============================================================================
# CAPA
# ============================================================================

@router.post("/capas", response_model=CAPAResponse)
def create_capa(
    data: CAPACreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crée un CAPA"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Liste les CAPA"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Récupère un CAPA par ID"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    capa = service.get_capa(capa_id)
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA non trouvé")
    return capa


@router.put("/capas/{capa_id}", response_model=CAPAResponse)
def update_capa(
    capa_id: int,
    data: CAPAUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour un CAPA"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    capa = service.update_capa(capa_id, data)
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA non trouvé")
    return capa


@router.post("/capas/{capa_id}/actions", response_model=CAPAActionResponse)
def add_capa_action(
    capa_id: int,
    data: CAPAActionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ajoute une action à un CAPA"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    action = service.add_capa_action(capa_id, data)
    if not action:
        raise HTTPException(status_code=404, detail="CAPA non trouvé")
    return action


@router.put("/capa-actions/{action_id}", response_model=CAPAActionResponse)
def update_capa_action(
    action_id: int,
    data: CAPAActionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour une action CAPA"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    action = service.update_capa_action(action_id, data)
    if not action:
        raise HTTPException(status_code=404, detail="Action non trouvée")
    return action


@router.post("/capas/{capa_id}/close", response_model=CAPAResponse)
def close_capa(
    capa_id: int,
    data: CAPAClose,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Clôture un CAPA"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    capa = service.close_capa(capa_id, data)
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA non trouvé")
    return capa


# ============================================================================
# RÉCLAMATIONS CLIENTS
# ============================================================================

@router.post("/claims", response_model=ClaimResponse)
def create_claim(
    data: ClaimCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crée une réclamation client"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Liste les réclamations"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Récupère une réclamation par ID"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    claim = service.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Réclamation non trouvée")
    return claim


@router.put("/claims/{claim_id}", response_model=ClaimResponse)
def update_claim(
    claim_id: int,
    data: ClaimUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour une réclamation"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    claim = service.update_claim(claim_id, data)
    if not claim:
        raise HTTPException(status_code=404, detail="Réclamation non trouvée")
    return claim


@router.post("/claims/{claim_id}/acknowledge", response_model=ClaimResponse)
def acknowledge_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Accuse réception d'une réclamation"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    claim = service.acknowledge_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Réclamation non trouvée")
    return claim


@router.post("/claims/{claim_id}/respond", response_model=ClaimResponse)
def respond_claim(
    claim_id: int,
    data: ClaimRespond,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Répond à une réclamation"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    claim = service.respond_claim(claim_id, data)
    if not claim:
        raise HTTPException(status_code=404, detail="Réclamation non trouvée")
    return claim


@router.post("/claims/{claim_id}/resolve", response_model=ClaimResponse)
def resolve_claim(
    claim_id: int,
    data: ClaimResolve,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Résout une réclamation"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    claim = service.resolve_claim(claim_id, data)
    if not claim:
        raise HTTPException(status_code=404, detail="Réclamation non trouvée")
    return claim


@router.post("/claims/{claim_id}/close", response_model=ClaimResponse)
def close_claim(
    claim_id: int,
    data: ClaimClose,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Clôture une réclamation"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    claim = service.close_claim(claim_id, data)
    if not claim:
        raise HTTPException(status_code=404, detail="Réclamation non trouvée")
    return claim


@router.post("/claims/{claim_id}/actions", response_model=ClaimActionResponse)
def add_claim_action(
    claim_id: int,
    data: ClaimActionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ajoute une action à une réclamation"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    action = service.add_claim_action(claim_id, data)
    if not action:
        raise HTTPException(status_code=404, detail="Réclamation non trouvée")
    return action


# ============================================================================
# INDICATEURS QUALITÉ
# ============================================================================

@router.post("/indicators", response_model=IndicatorResponse)
def create_indicator(
    data: IndicatorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crée un indicateur qualité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    return service.create_indicator(data)


@router.get("/indicators", response_model=PaginatedIndicatorResponse)
def list_indicators(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: str | None = None,
    active_only: bool = True,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Liste les indicateurs"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Récupère un indicateur par ID"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    indicator = service.get_indicator(indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicateur non trouvé")
    return indicator


@router.put("/indicators/{indicator_id}", response_model=IndicatorResponse)
def update_indicator(
    indicator_id: int,
    data: IndicatorUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour un indicateur"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    indicator = service.update_indicator(indicator_id, data)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicateur non trouvé")
    return indicator


@router.post("/indicators/{indicator_id}/measurements", response_model=IndicatorMeasurementResponse)
def add_measurement(
    indicator_id: int,
    data: IndicatorMeasurementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ajoute une mesure à un indicateur"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    measurement = service.add_measurement(indicator_id, data)
    if not measurement:
        raise HTTPException(status_code=404, detail="Indicateur non trouvé")
    return measurement


# ============================================================================
# CERTIFICATIONS
# ============================================================================

@router.post("/certifications", response_model=CertificationResponse)
def create_certification(
    data: CertificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crée une certification"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    return service.create_certification(data)


@router.get("/certifications", response_model=PaginatedCertificationResponse)
def list_certifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: CertificationStatus | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Liste les certifications"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
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
    current_user=Depends(get_current_user),
):
    """Récupère une certification par ID"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    certification = service.get_certification(cert_id)
    if not certification:
        raise HTTPException(status_code=404, detail="Certification non trouvée")
    return certification


@router.put("/certifications/{cert_id}", response_model=CertificationResponse)
def update_certification(
    cert_id: int,
    data: CertificationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour une certification"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    certification = service.update_certification(cert_id, data)
    if not certification:
        raise HTTPException(status_code=404, detail="Certification non trouvée")
    return certification


@router.post("/certifications/{cert_id}/audits", response_model=CertificationAuditResponse)
def add_certification_audit(
    cert_id: int,
    data: CertificationAuditCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ajoute un audit à une certification"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    audit = service.add_certification_audit(cert_id, data)
    if not audit:
        raise HTTPException(status_code=404, detail="Certification non trouvée")
    return audit


@router.put("/certification-audits/{audit_id}", response_model=CertificationAuditResponse)
def update_certification_audit(
    audit_id: int,
    data: CertificationAuditUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour un audit de certification"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    audit = service.update_certification_audit(audit_id, data)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")
    return audit


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=QualityDashboard)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Récupère les statistiques du dashboard qualité"""
    service = get_quality_service(db, current_user.tenant_id, current_user.id)
    return service.get_dashboard()
