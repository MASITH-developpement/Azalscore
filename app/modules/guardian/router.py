"""
AZALS MODULE GUARDIAN - Router API
==================================

Endpoints API pour le système de correction automatique gouvernée.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User

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
# CONFIGURATION
# ============================================================================

@router.get("/config", response_model=GuardianConfigResponse)
async def get_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupère la configuration GUARDIAN du tenant."""
    service = get_guardian_service(db, tenant_id)
    return service.get_config()


@router.put("/config", response_model=GuardianConfigResponse)
async def update_config(
    data: GuardianConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Met à jour la configuration GUARDIAN.
    Réservé aux rôles DIRIGEANT et ADMIN.
    """
    if current_user.role.value not in ["DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent modifier la configuration GUARDIAN"
        )

    service = get_guardian_service(db, tenant_id)
    return service.update_config(data)


# ============================================================================
# DÉTECTION D'ERREURS
# ============================================================================

@router.post("/errors", response_model=ErrorDetectionResponse, status_code=status.HTTP_201_CREATED)
async def report_error(
    data: ErrorDetectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Signale une erreur au système GUARDIAN.
    L'erreur est enregistrée et analysée pour correction automatique potentielle.
    """
    service = get_guardian_service(db, tenant_id)
    try:
        error = service.detect_error(data)
        return error
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/errors/frontend", response_model=ErrorDetectionResponse, status_code=status.HTTP_201_CREATED)
async def report_frontend_error(
    data: FrontendErrorReport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Signale une erreur frontend.
    Les données utilisateur sont automatiquement pseudonymisées.
    """
    service = get_guardian_service(db, tenant_id)
    try:
        error = service.report_frontend_error(data, user_id=current_user.id)
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Liste les erreurs détectées avec filtres et pagination."""
    service = get_guardian_service(db, tenant_id)
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupère une erreur par son ID."""
    from .models import ErrorDetection
    error = db.query(ErrorDetection).filter(
        ErrorDetection.id == error_id,
        ErrorDetection.tenant_id == tenant_id
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Acquitte une erreur (marque comme vue)."""
    from .models import ErrorDetection
    error = db.query(ErrorDetection).filter(
        ErrorDetection.id == error_id,
        ErrorDetection.tenant_id == tenant_id
    ).first()

    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Erreur {error_id} non trouvée"
        )

    error.is_acknowledged = True
    error.acknowledged_by = current_user.id
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Crée une entrée dans le registre des corrections.

    IMPORTANT: Cette entrée est obligatoire AVANT toute action corrective.
    Le registre est append-only et constitue une preuve d'audit.
    """
    service = get_guardian_service(db, tenant_id)
    try:
        correction = service.create_correction_registry(
            data,
            executed_by=f"user:{current_user.id}"
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Liste les corrections avec filtres et pagination."""
    service = get_guardian_service(db, tenant_id)
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Liste les corrections en attente de validation humaine."""
    service = get_guardian_service(db, tenant_id)
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupère une correction par son ID."""
    from .models import CorrectionRegistry
    correction = db.query(CorrectionRegistry).filter(
        CorrectionRegistry.id == correction_id,
        CorrectionRegistry.tenant_id == tenant_id
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Valide ou rejette une correction en attente.
    Réservé aux rôles DIRIGEANT et ADMIN.
    """
    if current_user.role.value not in ["DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent valider les corrections"
        )

    service = get_guardian_service(db, tenant_id)
    try:
        correction = service.validate_correction(
            correction_id=correction_id,
            approved=data.approved,
            user_id=current_user.id,
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Effectue un rollback d'une correction.
    Réservé aux rôles DIRIGEANT et ADMIN.
    """
    if current_user.role.value not in ["DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent effectuer un rollback"
        )

    service = get_guardian_service(db, tenant_id)
    try:
        correction = service.request_rollback(
            correction_id=correction_id,
            reason=data.reason,
            user_id=current_user.id
        )
        return correction
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/corrections/{correction_id}/tests", response_model=CorrectionTestListResponse)
async def get_correction_tests(
    correction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupère les tests exécutés pour une correction."""
    service = get_guardian_service(db, tenant_id)
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Crée une nouvelle règle de correction automatique.
    Réservé aux rôles DIRIGEANT et ADMIN.
    """
    if current_user.role.value not in ["DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent créer des règles"
        )

    service = get_guardian_service(db, tenant_id)
    rule = service.create_correction_rule(data, user_id=current_user.id)
    return rule


@router.get("/rules", response_model=CorrectionRuleListResponse)
async def list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Liste les règles de correction."""
    service = get_guardian_service(db, tenant_id)
    items, total = service.list_rules(
        page=page,
        page_size=page_size,
        is_active=is_active
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupère une règle par son ID."""
    from .models import CorrectionRule
    rule = db.query(CorrectionRule).filter(
        CorrectionRule.id == rule_id,
        CorrectionRule.tenant_id == tenant_id
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Met à jour une règle de correction.
    Réservé aux rôles DIRIGEANT et ADMIN.
    """
    if current_user.role.value not in ["DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent modifier les règles"
        )

    service = get_guardian_service(db, tenant_id)
    try:
        rule = service.update_correction_rule(rule_id, data)
        return rule
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Désactive une règle de correction (soft delete).
    Réservé aux rôles DIRIGEANT et ADMIN.
    """
    if current_user.role.value not in ["DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent supprimer les règles"
        )

    service = get_guardian_service(db, tenant_id)
    try:
        service.delete_correction_rule(rule_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Liste les alertes GUARDIAN."""
    service = get_guardian_service(db, tenant_id)
    items, total, unread_count = service.list_alerts(
        page=page,
        page_size=page_size,
        is_resolved=is_resolved,
        severity=severity
    )

    return GuardianAlertListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        unread_count=unread_count
    )


@router.get("/alerts/{alert_id}", response_model=GuardianAlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupère une alerte par son ID."""
    from .models import GuardianAlert
    alert = db.query(GuardianAlert).filter(
        GuardianAlert.id == alert_id,
        GuardianAlert.tenant_id == tenant_id
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
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Acquitte une alerte."""
    service = get_guardian_service(db, tenant_id)
    try:
        alert = service.acknowledge_alert(alert_id, current_user.id)
        return alert
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/alerts/{alert_id}/resolve", response_model=GuardianAlertResponse)
async def resolve_alert(
    alert_id: int,
    data: AlertResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Résout une alerte."""
    service = get_guardian_service(db, tenant_id)
    try:
        alert = service.resolve_alert(alert_id, current_user.id, data.comment)
        return alert
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# STATISTIQUES & DASHBOARD
# ============================================================================

@router.get("/statistics", response_model=GuardianStatistics)
async def get_statistics(
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupère les statistiques GUARDIAN."""
    service = get_guardian_service(db, tenant_id)
    return service.get_statistics(period_days)


@router.get("/dashboard", response_model=GuardianDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Récupère le tableau de bord GUARDIAN complet.
    Inclut statistiques, erreurs récentes, corrections en attente, alertes actives.
    """
    service = get_guardian_service(db, tenant_id)

    # Statistiques
    stats = service.get_statistics(period_days=30)

    # Erreurs récentes (top 10)
    recent_errors, _ = service.list_errors(page=1, page_size=10, is_processed=False)

    # Corrections en attente de validation
    pending_validations, _ = service.list_corrections(
        page=1, page_size=10,
        status=CorrectionStatus.BLOCKED,
        requires_validation=True
    )

    # Corrections récentes
    recent_corrections, _ = service.list_corrections(page=1, page_size=10)

    # Alertes actives (non résolues)
    active_alerts, _, _ = service.list_alerts(page=1, page_size=10, is_resolved=False)

    # Santé du système
    config = service.get_config()
    system_health = {
        "guardian_enabled": config.is_enabled,
        "auto_correction_enabled": config.auto_correction_enabled,
        "auto_correction_environments": config.auto_correction_environments,
        "corrections_today": stats.total_corrections,
        "success_rate": (
            stats.successful_corrections / stats.total_corrections * 100
            if stats.total_corrections > 0 else 100
        ),
        "unresolved_alerts": stats.unresolved_alerts,
        "critical_errors_24h": stats.errors_by_severity.get("CRITICAL", 0),
    }

    return GuardianDashboard(
        statistics=stats,
        recent_errors=recent_errors,
        pending_validations=pending_validations,
        recent_corrections=recent_corrections,
        active_alerts=active_alerts,
        system_health=system_health
    )


# ============================================================================
# AUDIT EXPORT
# ============================================================================

@router.get("/audit/export")
async def export_audit_data(
    date_from: datetime,
    date_to: datetime,
    include_errors: bool = True,
    include_corrections: bool = True,
    include_alerts: bool = True,
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Exporte les données d'audit pour une période donnée.
    Réservé aux rôles DIRIGEANT et ADMIN.

    Utilisable pour les audits externes et la conformité.
    """
    if current_user.role.value not in ["DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les rôles DIRIGEANT et ADMIN peuvent exporter les données d'audit"
        )

    service = get_guardian_service(db, tenant_id)

    export_data = {
        "tenant_id": tenant_id,
        "export_date": datetime.utcnow().isoformat(),
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        },
        "exported_by": current_user.id
    }

    if include_errors:
        errors, _ = service.list_errors(
            page=1, page_size=10000,
            date_from=date_from, date_to=date_to
        )
        export_data["errors"] = [
            {
                "error_uid": e.error_uid,
                "detected_at": e.detected_at.isoformat(),
                "severity": e.severity.value,
                "error_type": e.error_type.value,
                "module": e.module,
                "error_message": e.error_message,
                "is_processed": e.is_processed,
                "correction_id": e.correction_id
            }
            for e in errors
        ]

    if include_corrections:
        corrections, _ = service.list_corrections(
            page=1, page_size=10000,
            date_from=date_from, date_to=date_to
        )
        export_data["corrections"] = [
            {
                "correction_uid": c.correction_uid,
                "created_at": c.created_at.isoformat(),
                "environment": c.environment.value,
                "severity": c.severity.value,
                "module": c.module,
                "probable_cause": c.probable_cause,
                "correction_action": c.correction_action.value,
                "correction_description": c.correction_description,
                "estimated_impact": c.estimated_impact,
                "is_reversible": c.is_reversible,
                "reversibility_justification": c.reversibility_justification,
                "status": c.status.value,
                "correction_successful": c.correction_successful,
                "executed_by": c.executed_by,
                "executed_at": c.executed_at.isoformat() if c.executed_at else None,
                "rolled_back": c.rolled_back,
                "decision_trail": c.decision_trail
            }
            for c in corrections
        ]

    if include_alerts:
        alerts, _, _ = service.list_alerts(page=1, page_size=10000)
        # Filtrer par date manuellement
        export_data["alerts"] = [
            {
                "alert_uid": a.alert_uid,
                "created_at": a.created_at.isoformat(),
                "alert_type": a.alert_type,
                "severity": a.severity.value,
                "title": a.title,
                "message": a.message,
                "is_resolved": a.is_resolved,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None
            }
            for a in alerts
            if date_from <= a.created_at <= date_to
        ]

    return export_data
