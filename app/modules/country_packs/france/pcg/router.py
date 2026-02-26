"""
AZALS MODULE - PCG 2025: Router API
====================================

Endpoints REST pour la gestion du Plan Comptable Général 2025.
"""
from __future__ import annotations


import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.dependencies import get_tenant_id
from app.core.models import User

from .service import PCG2025Service
from .schemas import (
    PCGAccountCreate,
    PCGAccountUpdate,
    PCGAccountResponse,
    PCGAccountListResponse,
    PCGInitRequest,
    PCGInitResult,
    PCGMigrateRequest,
    PCGMigrationResult,
    PCGStatisticsResponse,
    PCGStatusResponse,
    PCGValidationResult,
    PCGHierarchyResponse,
    PCG_CLASSES,
    PCGClassInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pcg", tags=["PCG - Plan Comptable Général 2025"])


# ============================================================================
# ENDPOINTS INITIALISATION
# ============================================================================

@router.post(
    "/initialize",
    response_model=PCGInitResult,
    status_code=status.HTTP_201_CREATED,
    summary="Initialiser le PCG 2025",
    description="""
    Initialise le Plan Comptable Général 2025 pour le tenant.

    **Important:**
    - Crée environ 400 comptes standards PCG 2025
    - Ne supprime pas les comptes personnalisés existants
    - Utilisez `force=true` pour réinitialiser les comptes standards
    """,
)
def initialize_pcg(
    request: PCGInitRequest = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGInitResult:
    """Initialiser le PCG 2025."""
    service = PCG2025Service(db, tenant_id)
    force = request.force if request else False

    try:
        return service.initialize_pcg2025(force=force)
    except Exception as e:
        logger.error(f"[PCG] Erreur initialisation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'initialisation du PCG: {str(e)}",
        )


@router.get(
    "/status",
    response_model=PCGStatusResponse,
    summary="État d'initialisation du PCG",
    description="Vérifie si le PCG est initialisé et complet.",
)
def get_status(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGStatusResponse:
    """Récupérer l'état d'initialisation du PCG."""
    service = PCG2025Service(db, tenant_id)
    status_data = service.get_initialization_status()
    return PCGStatusResponse(**status_data)


@router.post(
    "/migrate",
    response_model=PCGMigrationResult,
    summary="Migrer le PCG",
    description="Migre le plan comptable de PCG 2024 vers PCG 2025.",
)
def migrate_pcg(
    request: PCGMigrateRequest = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGMigrationResult:
    """Migrer le PCG vers une nouvelle version."""
    service = PCG2025Service(db, tenant_id)

    try:
        return service.migrate_from_2024()
    except Exception as e:
        logger.error(f"[PCG] Erreur migration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la migration du PCG: {str(e)}",
        )


# ============================================================================
# ENDPOINTS COMPTES
# ============================================================================

@router.get(
    "/accounts",
    response_model=PCGAccountListResponse,
    summary="Lister les comptes PCG",
    description="Liste paginée des comptes du plan comptable.",
)
def list_accounts(
    pcg_class: Optional[str] = Query(None, description="Filtrer par classe (1-8)"),
    active_only: bool = Query(True, description="Uniquement les comptes actifs"),
    custom_only: bool = Query(False, description="Uniquement les comptes personnalisés"),
    summary_only: bool = Query(False, description="Uniquement les comptes de regroupement"),
    search: Optional[str] = Query(None, description="Recherche par numéro ou libellé"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(50, ge=1, le=500, description="Taille de page"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGAccountListResponse:
    """Lister les comptes PCG."""
    service = PCG2025Service(db, tenant_id)
    skip = (page - 1) * page_size

    accounts, total = service.list_accounts(
        pcg_class=pcg_class,
        active_only=active_only,
        custom_only=custom_only,
        summary_only=summary_only,
        search=search,
        skip=skip,
        limit=page_size,
    )

    total_pages = (total + page_size - 1) // page_size

    return PCGAccountListResponse(
        items=[
            PCGAccountResponse(
                id=a.id,
                tenant_id=a.tenant_id,
                account_number=a.account_number,
                account_label=a.account_label,
                pcg_class=a.pcg_class.value if hasattr(a.pcg_class, 'value') else str(a.pcg_class),
                parent_account=a.parent_account,
                is_summary=a.is_summary,
                is_active=a.is_active,
                is_custom=a.is_custom,
                normal_balance=a.normal_balance,
                description=a.description,
                default_vat_code=a.default_vat_code,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in accounts
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/accounts/{account_number}",
    response_model=PCGAccountResponse,
    summary="Récupérer un compte",
    description="Récupère les détails d'un compte par son numéro.",
)
def get_account(
    account_number: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGAccountResponse:
    """Récupérer un compte PCG."""
    service = PCG2025Service(db, tenant_id)
    account = service.get_account(account_number)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compte {account_number} introuvable",
        )

    return PCGAccountResponse(
        id=account.id,
        tenant_id=account.tenant_id,
        account_number=account.account_number,
        account_label=account.account_label,
        pcg_class=account.pcg_class.value if hasattr(account.pcg_class, 'value') else str(account.pcg_class),
        parent_account=account.parent_account,
        is_summary=account.is_summary,
        is_active=account.is_active,
        is_custom=account.is_custom,
        normal_balance=account.normal_balance,
        description=account.description,
        default_vat_code=account.default_vat_code,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


@router.post(
    "/accounts",
    response_model=PCGAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte personnalisé",
    description="""
    Crée un compte PCG personnalisé.

    **Règles:**
    - Le numéro doit commencer par un chiffre de classe (1-8)
    - Le numéro ne doit pas déjà exister
    - Le compte parent doit exister si le numéro a plus de 2 chiffres
    """,
)
def create_account(
    data: PCGAccountCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGAccountResponse:
    """Créer un compte PCG personnalisé."""
    service = PCG2025Service(db, tenant_id)

    try:
        account = service.create_custom_account(data)
        return PCGAccountResponse(
            id=account.id,
            tenant_id=account.tenant_id,
            account_number=account.account_number,
            account_label=account.account_label,
            pcg_class=account.pcg_class.value if hasattr(account.pcg_class, 'value') else str(account.pcg_class),
            parent_account=account.parent_account,
            is_summary=account.is_summary,
            is_active=account.is_active,
            is_custom=account.is_custom,
            normal_balance=account.normal_balance,
            description=account.description,
            default_vat_code=account.default_vat_code,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/accounts/{account_id}",
    response_model=PCGAccountResponse,
    summary="Mettre à jour un compte",
    description="Met à jour un compte personnalisé (les comptes standards ne peuvent pas être modifiés).",
)
def update_account(
    account_id: UUID,
    data: PCGAccountUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGAccountResponse:
    """Mettre à jour un compte PCG personnalisé."""
    service = PCG2025Service(db, tenant_id)

    try:
        account = service.update_account(
            account_id,
            **data.model_dump(exclude_unset=True),
        )
        return PCGAccountResponse(
            id=account.id,
            tenant_id=account.tenant_id,
            account_number=account.account_number,
            account_label=account.account_label,
            pcg_class=account.pcg_class.value if hasattr(account.pcg_class, 'value') else str(account.pcg_class),
            parent_account=account.parent_account,
            is_summary=account.is_summary,
            is_active=account.is_active,
            is_custom=account.is_custom,
            normal_balance=account.normal_balance,
            description=account.description,
            default_vat_code=account.default_vat_code,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/accounts/{account_number}/deactivate",
    response_model=PCGAccountResponse,
    summary="Désactiver un compte",
    description="Désactive un compte (les comptes avec des écritures ne peuvent pas être supprimés).",
)
def deactivate_account(
    account_number: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGAccountResponse:
    """Désactiver un compte PCG."""
    service = PCG2025Service(db, tenant_id)

    try:
        account = service.deactivate_account(account_number)
        return PCGAccountResponse(
            id=account.id,
            tenant_id=account.tenant_id,
            account_number=account.account_number,
            account_label=account.account_label,
            pcg_class=account.pcg_class.value if hasattr(account.pcg_class, 'value') else str(account.pcg_class),
            parent_account=account.parent_account,
            is_summary=account.is_summary,
            is_active=account.is_active,
            is_custom=account.is_custom,
            normal_balance=account.normal_balance,
            description=account.description,
            default_vat_code=account.default_vat_code,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# ENDPOINTS VALIDATION
# ============================================================================

@router.get(
    "/validate/{account_number}",
    response_model=PCGValidationResult,
    summary="Valider un numéro de compte",
    description="Valide un numéro de compte selon les règles PCG 2025.",
)
def validate_account(
    account_number: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGValidationResult:
    """Valider un numéro de compte PCG."""
    service = PCG2025Service(db, tenant_id)
    return service.validate_account_number(account_number)


@router.get(
    "/validate",
    summary="Valider le plan comptable complet",
    description="Vérifie la cohérence complète du plan comptable du tenant.",
)
def validate_chart_of_accounts(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Valider le plan comptable complet."""
    service = PCG2025Service(db, tenant_id)
    return service.validate_chart_of_accounts()


# ============================================================================
# ENDPOINTS HIÉRARCHIE
# ============================================================================

@router.get(
    "/accounts/{account_number}/hierarchy",
    response_model=PCGHierarchyResponse,
    summary="Hiérarchie d'un compte",
    description="Récupère la hiérarchie complète d'un compte (parents et enfants).",
)
def get_hierarchy(
    account_number: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGHierarchyResponse:
    """Récupérer la hiérarchie d'un compte."""
    service = PCG2025Service(db, tenant_id)

    hierarchy = service.get_account_hierarchy(account_number)
    children = service.get_child_accounts(account_number)

    return PCGHierarchyResponse(
        account_number=account_number,
        hierarchy=[
            PCGAccountResponse(
                id=a.id,
                tenant_id=a.tenant_id,
                account_number=a.account_number,
                account_label=a.account_label,
                pcg_class=a.pcg_class.value if hasattr(a.pcg_class, 'value') else str(a.pcg_class),
                parent_account=a.parent_account,
                is_summary=a.is_summary,
                is_active=a.is_active,
                is_custom=a.is_custom,
                normal_balance=a.normal_balance,
                description=a.description,
                default_vat_code=a.default_vat_code,
            )
            for a in hierarchy
        ],
        children=[
            PCGAccountResponse(
                id=a.id,
                tenant_id=a.tenant_id,
                account_number=a.account_number,
                account_label=a.account_label,
                pcg_class=a.pcg_class.value if hasattr(a.pcg_class, 'value') else str(a.pcg_class),
                parent_account=a.parent_account,
                is_summary=a.is_summary,
                is_active=a.is_active,
                is_custom=a.is_custom,
                normal_balance=a.normal_balance,
                description=a.description,
                default_vat_code=a.default_vat_code,
            )
            for a in children
        ],
    )


# ============================================================================
# ENDPOINTS STATISTIQUES
# ============================================================================

@router.get(
    "/statistics",
    response_model=PCGStatisticsResponse,
    summary="Statistiques du PCG",
    description="Retourne les statistiques du plan comptable.",
)
def get_statistics(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PCGStatisticsResponse:
    """Récupérer les statistiques du PCG."""
    service = PCG2025Service(db, tenant_id)
    stats = service.get_statistics()
    return PCGStatisticsResponse(**stats)


# ============================================================================
# ENDPOINTS RÉFÉRENCE
# ============================================================================

@router.get(
    "/classes",
    response_model=list[PCGClassInfo],
    summary="Liste des classes PCG",
    description="Retourne la définition des 8 classes du PCG.",
)
def get_pcg_classes() -> list[PCGClassInfo]:
    """Retourne la liste des classes PCG."""
    return PCG_CLASSES


@router.get(
    "/search",
    response_model=list[PCGAccountResponse],
    summary="Rechercher des comptes",
    description="Recherche rapide de comptes par numéro ou libellé.",
)
def search_accounts(
    q: str = Query(..., min_length=1, description="Terme de recherche"),
    limit: int = Query(20, ge=1, le=100, description="Nombre max de résultats"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> list[PCGAccountResponse]:
    """Rechercher des comptes PCG."""
    service = PCG2025Service(db, tenant_id)
    accounts = service.search_accounts(q, limit=limit)

    return [
        PCGAccountResponse(
            id=a.id,
            tenant_id=a.tenant_id,
            account_number=a.account_number,
            account_label=a.account_label,
            pcg_class=a.pcg_class.value if hasattr(a.pcg_class, 'value') else str(a.pcg_class),
            parent_account=a.parent_account,
            is_summary=a.is_summary,
            is_active=a.is_active,
            is_custom=a.is_custom,
            normal_balance=a.normal_balance,
            description=a.description,
            default_vat_code=a.default_vat_code,
        )
        for a in accounts
    ]
