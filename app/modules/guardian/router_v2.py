"""
AZALS MODULE GUARDIAN - Router API v2 (CORE SaaS)
=================================================

✅ MIGRÉ CORE SaaS Phase 2.2
- Utilise get_saas_context() au lieu de get_current_user()
- Isolation tenant automatique via context.tenant_id
- Audit trail automatique via context.user_id
- Vérifications permissions via context.role

Endpoints API pour le système de correction automatique gouvernée.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext, get_saas_context
from app.core.models import UserRole

from .models import (
    CorrectionStatus,
    Environment,
    ErrorSeverity,
    ErrorType,
)
from .schemas import (
    AlertResolveRequest,
    # Correction Registry
    CorrectionRegistryCreate,
    CorrectionRegistryListResponse,
    CorrectionRegistryResponse,
    CorrectionRollbackRequest,
    # Correction Rules
    CorrectionRuleCreate,
    CorrectionRuleListResponse,
    CorrectionRuleResponse,
    CorrectionRuleUpdate,
    CorrectionTestListResponse,
    # Correction Tests
    CorrectionValidationRequest,
    # Error Detection
    ErrorDetectionCreate,
    ErrorDetectionListResponse,
    ErrorDetectionResponse,
    FrontendErrorReport,
    GuardianAlertListResponse,
    # Alerts
    GuardianAlertResponse,
    GuardianConfigResponse,
    # Config
    GuardianConfigUpdate,
    GuardianDashboard,
    # Statistics
    GuardianStatistics,
)
from .service import get_guardian_service

router = APIRouter(prefix="/guardian", tags=["GUARDIAN"])


# ============================================================================
# SERVICE DEPENDENCY v2
# ============================================================================

def get_service_v2(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> object:
    """✅ MIGRÉ CORE SaaS: Utilise context.tenant_id"""
    return get_guardian_service(db, context.tenant_id)


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.get("/config", response_model=GuardianConfigResponse)
async def get_config(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère la configuration GUARDIAN du tenant.

    Changements:
    - current_user → context
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    return service.get_config()


@router.put("/config", response_model=GuardianConfigResponse)
async def update_config(
    data: GuardianConfigUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Met à jour la configuration GUARDIAN.

    Réservé aux rôles DIRIGEANT et ADMIN.

    Changements:
    - current_user.role.value → context.role
    - Vérification permission via context.role
    """
    if context.role not in [UserRole.DIRIGEANT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent modifier la configuration GUARDIAN"
        )

    service = get_guardian_service(db, context.tenant_id)
    return service.update_config(data)


# ============================================================================
# DÉTECTION D'ERREURS
# ============================================================================

@router.post("/errors", response_model=ErrorDetectionResponse, status_code=status.HTTP_201_CREATED)
async def report_error(
    data: ErrorDetectionCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Signale une erreur au système GUARDIAN.

    L'erreur est enregistrée et analysée pour correction automatique potentielle.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    try:
        error = service.detect_error(data)
        return error
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/errors/frontend", response_model=ErrorDetectionResponse, status_code=status.HTTP_201_CREATED)
async def report_frontend_error(
    data: FrontendErrorReport,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Signale une erreur frontend.

    Les données utilisateur sont automatiquement pseudonymisées.

    Changements:
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    try:
        error = service.report_frontend_error(data, user_id=context.user_id)
        return error
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/errors", response_model=ErrorDetectionListResponse)
async def list_errors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: ErrorSeverity | None = None,
    error_type: ErrorType | None = None,
    module: str | None = None,
    is_processed: bool | None = None,
    environment: Environment | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les erreurs détectées avec filtres et pagination.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    items, total = service.list_errors(
        page=page,
        page_size=page_size,
        severity=severity,
        error_type=error_type,
        module=module,
        is_processed=is_processed,
        environment=environment,
        date_from=date_from,
        date_to=date_to
    )

    return ErrorDetectionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/errors/{error_id}", response_model=ErrorDetectionResponse)
async def get_error(
    error_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère une erreur par son ID.

    Changements:
    - tenant_id → context.tenant_id
    - Isolation automatique par tenant
    """
    from .models import ErrorDetection
    error = db.query(ErrorDetection).filter(
        ErrorDetection.id == error_id,
        ErrorDetection.tenant_id == context.tenant_id
    ).first()

    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Erreur {error_id} non trouvée"
        )

    return error


@router.post("/errors/{error_id}/acknowledge")
async def acknowledge_error(
    error_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Acquitte une erreur (marque comme vue).

    Changements:
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    - Audit trail automatique
    """
    from .models import ErrorDetection
    error = db.query(ErrorDetection).filter(
        ErrorDetection.id == error_id,
        ErrorDetection.tenant_id == context.tenant_id
    ).first()

    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Erreur {error_id} non trouvée"
        )

    error.is_acknowledged = True
    error.acknowledged_by = context.user_id
    error.acknowledged_at = datetime.utcnow()
    db.commit()

    return {"status": "acknowledged", "error_id": error_id}


# ============================================================================
# REGISTRE DES CORRECTIONS
# ============================================================================

@router.post("/corrections", response_model=CorrectionRegistryResponse, status_code=status.HTTP_201_CREATED)
async def create_correction(
    data: CorrectionRegistryCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Crée une entrée dans le registre des corrections.

    IMPORTANT: Cette entrée est obligatoire AVANT toute action corrective.
    Le registre est append-only et constitue une preuve d'audit.

    Changements:
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    try:
        correction = service.create_correction_registry(
            data,
            executed_by=f"user:{context.user_id}"
        )
        return correction
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/corrections", response_model=CorrectionRegistryListResponse)
async def list_corrections(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: CorrectionStatus | None = Query(None, alias="status"),
    environment: Environment | None = None,
    severity: ErrorSeverity | None = None,
    module: str | None = None,
    requires_validation: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les corrections avec filtres et pagination.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    items, total = service.list_corrections(
        page=page,
        page_size=page_size,
        status=status_filter,
        environment=environment,
        severity=severity,
        module=module,
        requires_validation=requires_validation,
        date_from=date_from,
        date_to=date_to
    )

    return CorrectionRegistryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/corrections/pending-validation", response_model=CorrectionRegistryListResponse)
async def list_pending_validations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les corrections en attente de validation humaine.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    items, total = service.list_corrections(
        page=page,
        page_size=page_size,
        status=CorrectionStatus.BLOCKED,
        requires_validation=True
    )

    return CorrectionRegistryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/corrections/{correction_id}", response_model=CorrectionRegistryResponse)
async def get_correction(
    correction_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère une correction par son ID.

    Changements:
    - tenant_id → context.tenant_id
    - Isolation automatique par tenant
    """
    from .models import CorrectionRegistry
    correction = db.query(CorrectionRegistry).filter(
        CorrectionRegistry.id == correction_id,
        CorrectionRegistry.tenant_id == context.tenant_id
    ).first()

    if not correction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Correction {correction_id} non trouvée"
        )

    return correction


@router.post("/corrections/{correction_id}/validate", response_model=CorrectionRegistryResponse)
async def validate_correction(
    correction_id: int,
    data: CorrectionValidationRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Valide ou rejette une correction en attente.

    Réservé aux rôles DIRIGEANT et ADMIN.

    Changements:
    - current_user.role.value → context.role
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    if context.role not in [UserRole.DIRIGEANT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent valider les corrections"
        )

    service = get_guardian_service(db, context.tenant_id)
    try:
        correction = service.validate_correction(
            correction_id=correction_id,
            approved=data.approved,
            user_id=context.user_id,
            comment=data.comment
        )
        return correction
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/corrections/{correction_id}/rollback", response_model=CorrectionRegistryResponse)
async def rollback_correction(
    correction_id: int,
    data: CorrectionRollbackRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Effectue un rollback d'une correction.

    Réservé aux rôles DIRIGEANT et ADMIN.

    Changements:
    - current_user.role.value → context.role
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    if context.role not in [UserRole.DIRIGEANT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent effectuer un rollback"
        )

    service = get_guardian_service(db, context.tenant_id)
    try:
        correction = service.request_rollback(
            correction_id=correction_id,
            reason=data.reason,
            user_id=context.user_id
        )
        return correction
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/corrections/{correction_id}/tests", response_model=CorrectionTestListResponse)
async def get_correction_tests(
    correction_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère les tests exécutés pour une correction.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    tests = service.get_correction_tests(correction_id)

    return CorrectionTestListResponse(
        items=tests,
        total=len(tests)
    )


# ============================================================================
# RÈGLES DE CORRECTION
# ============================================================================

@router.post("/rules", response_model=CorrectionRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: CorrectionRuleCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Crée une nouvelle règle de correction automatique.

    Réservé aux rôles DIRIGEANT et ADMIN.

    Changements:
    - current_user.role.value → context.role
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    if context.role not in [UserRole.DIRIGEANT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent créer des règles"
        )

    service = get_guardian_service(db, context.tenant_id)
    rule = service.create_correction_rule(data, user_id=context.user_id)
    return rule


@router.get("/rules", response_model=CorrectionRuleListResponse)
async def list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = True,
    module: str | None = None,
    error_type: ErrorType | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les règles de correction avec filtres.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    items, total = service.list_correction_rules(
        page=page,
        page_size=page_size,
        is_active=is_active,
        module=module,
        error_type=error_type
    )

    return CorrectionRuleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/rules/{rule_id}", response_model=CorrectionRuleResponse)
async def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère une règle par son ID.

    Changements:
    - tenant_id → context.tenant_id
    - Isolation automatique par tenant
    """
    from .models import CorrectionRule
    rule = db.query(CorrectionRule).filter(
        CorrectionRule.id == rule_id,
        CorrectionRule.tenant_id == context.tenant_id
    ).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Règle {rule_id} non trouvée"
        )

    return rule


@router.put("/rules/{rule_id}", response_model=CorrectionRuleResponse)
async def update_rule(
    rule_id: int,
    data: CorrectionRuleUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Met à jour une règle de correction.

    Réservé aux rôles DIRIGEANT et ADMIN.

    Changements:
    - current_user.role.value → context.role
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    if context.role not in [UserRole.DIRIGEANT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent modifier les règles"
        )

    service = get_guardian_service(db, context.tenant_id)
    try:
        rule = service.update_correction_rule(rule_id, data, user_id=context.user_id)
        return rule
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Supprime (désactive) une règle de correction.

    Réservé aux rôles DIRIGEANT et ADMIN.

    Changements:
    - current_user.role.value → context.role
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    if context.role not in [UserRole.DIRIGEANT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent supprimer les règles"
        )

    service = get_guardian_service(db, context.tenant_id)
    try:
        service.delete_correction_rule(rule_id, user_id=context.user_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# ALERTES
# ============================================================================

@router.get("/alerts", response_model=GuardianAlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_resolved: bool | None = None,
    severity: ErrorSeverity | None = None,
    module: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les alertes GUARDIAN avec filtres.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    items, total = service.list_alerts(
        page=page,
        page_size=page_size,
        is_resolved=is_resolved,
        severity=severity,
        module=module
    )

    return GuardianAlertListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/alerts/{alert_id}", response_model=GuardianAlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère une alerte par son ID.

    Changements:
    - tenant_id → context.tenant_id
    - Isolation automatique par tenant
    """
    from .models import GuardianAlert
    alert = db.query(GuardianAlert).filter(
        GuardianAlert.id == alert_id,
        GuardianAlert.tenant_id == context.tenant_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alerte {alert_id} non trouvée"
        )

    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=GuardianAlertResponse)
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Acquitte une alerte.

    Changements:
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    try:
        alert = service.acknowledge_alert(alert_id, user_id=context.user_id)
        return alert
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/alerts/{alert_id}/resolve", response_model=GuardianAlertResponse)
async def resolve_alert(
    alert_id: int,
    data: AlertResolveRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Résout une alerte.

    Changements:
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    try:
        alert = service.resolve_alert(
            alert_id=alert_id,
            resolution=data.resolution,
            user_id=context.user_id
        )
        return alert
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# STATISTIQUES & DASHBOARD
# ============================================================================

@router.get("/statistics", response_model=GuardianStatistics)
async def get_statistics(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère les statistiques GUARDIAN.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    return service.get_statistics(date_from=date_from, date_to=date_to)


@router.get("/dashboard", response_model=GuardianDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère le dashboard GUARDIAN complet.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    return service.get_dashboard()


# ============================================================================
# AUDIT & EXPORTS
# ============================================================================

@router.get("/audit/export")
async def export_audit(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    format: str = Query("csv", regex="^(csv|json)$"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Exporte l'historique d'audit GUARDIAN.

    Changements:
    - tenant_id → context.tenant_id
    - Ajout X-Tenant-ID pour traçabilité
    """
    from fastapi.responses import StreamingResponse

    service = get_guardian_service(db, context.tenant_id)

    if format == "csv":
        content = service.export_audit_csv(date_from=date_from, date_to=date_to)
        media_type = "text/csv; charset=utf-8"
        filename = f"guardian_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    else:
        content = service.export_audit_json(date_from=date_from, date_to=date_to)
        media_type = "application/json"
        filename = f"guardian_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Tenant-ID": context.tenant_id
        }
    )


# ============================================================================
# INCIDENTS (NOUVEAUX ENDPOINTS DÉCOUVERTS)
# ============================================================================

@router.post("/incidents", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: dict,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Crée un incident GUARDIAN.

    Changements:
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    incident = service.create_incident(data, user_id=context.user_id)
    return incident


@router.get("/incidents")
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les incidents GUARDIAN.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    items, total = service.list_incidents(page=page, page_size=page_size)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/incidents/{incident_id}/screenshot")
async def get_incident_screenshot(
    incident_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère le screenshot d'un incident.

    Changements:
    - tenant_id → context.tenant_id
    """
    from fastapi.responses import Response

    service = get_guardian_service(db, context.tenant_id)
    screenshot = service.get_incident_screenshot(incident_id)

    if not screenshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screenshot de l'incident {incident_id} non trouvé"
        )

    return Response(content=screenshot, media_type="image/png")


# ============================================================================
# REPORTS DAILY
# ============================================================================

@router.get("/reports/daily")
async def list_daily_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les rapports quotidiens GUARDIAN.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    reports, total = service.list_daily_reports(page=page, page_size=page_size)

    return {
        "items": reports,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/reports/daily/{report_date}")
async def get_daily_report(
    report_date: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère un rapport quotidien spécifique.

    Changements:
    - tenant_id → context.tenant_id
    """
    service = get_guardian_service(db, context.tenant_id)
    report = service.get_daily_report(report_date)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rapport du {report_date} non trouvé"
        )

    return report


@router.post("/reports/daily/generate")
async def generate_daily_report(
    report_date: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Génère un rapport quotidien GUARDIAN.

    Réservé aux rôles DIRIGEANT et ADMIN.

    Changements:
    - current_user.role.value → context.role
    - current_user.id → context.user_id
    - tenant_id → context.tenant_id
    """
    if context.role not in [UserRole.DIRIGEANT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent générer des rapports"
        )

    service = get_guardian_service(db, context.tenant_id)
    report = service.generate_daily_report(
        report_date=report_date,
        user_id=context.user_id
    )

    return report
