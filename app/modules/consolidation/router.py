"""
AZALS MODULE - CONSOLIDATION: Router API
==========================================

API REST pour le module de consolidation comptable multi-entites.

Endpoints:
- Perimetres de consolidation
- Entites du groupe
- Participations
- Cours de change
- Consolidations
- Paquets de consolidation
- Eliminations
- Reconciliations intercompany
- Rapports consolides
- Dashboard

Auteur: AZALSCORE Team
Version: 1.0.0
"""
from __future__ import annotations


from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User

from .models import (
    AccountingStandard,
    ConsolidationMethod,
    ConsolidationStatus,
    EliminationType,
    PackageStatus,
    ReportType,
)
from .schemas import (
    # Perimetres
    ConsolidationPerimeterCreate,
    ConsolidationPerimeterUpdate,
    ConsolidationPerimeterResponse,
    PaginatedPerimeters,
    # Entites
    ConsolidationEntityCreate,
    ConsolidationEntityUpdate,
    ConsolidationEntityResponse,
    PaginatedEntities,
    EntityFilters,
    # Participations
    ParticipationCreate,
    ParticipationUpdate,
    ParticipationResponse,
    # Cours de change
    ExchangeRateCreate,
    ExchangeRateBulkCreate,
    ExchangeRateResponse,
    PaginatedExchangeRates,
    # Consolidations
    ConsolidationCreate,
    ConsolidationUpdate,
    ConsolidationResponse,
    PaginatedConsolidations,
    ConsolidationFilters,
    # Paquets
    ConsolidationPackageCreate,
    ConsolidationPackageUpdate,
    ConsolidationPackageSubmit,
    ConsolidationPackageValidate,
    ConsolidationPackageReject,
    ConsolidationPackageResponse,
    PaginatedPackages,
    PackageFilters,
    # Eliminations
    EliminationEntryCreate,
    EliminationEntryUpdate,
    EliminationEntryResponse,
    PaginatedEliminations,
    GenerateEliminationsRequest,
    GenerateEliminationsResponse,
    # Reconciliations
    IntercompanyReconciliationCreate,
    IntercompanyReconciliationUpdate,
    IntercompanyReconciliationResponse,
    PaginatedReconciliations,
    ReconciliationSummary,
    ReconciliationFilters,
    # Rapports
    ConsolidatedReportResponse,
    PaginatedReports,
    GenerateReportRequest,
    # Dashboard
    ConsolidationDashboard,
    ConsolidationProgress,
)
from .service import ConsolidationService, create_consolidation_service
from .exceptions import (
    ConsolidationError,
    PerimeterNotFoundError,
    PerimeterDuplicateError,
    EntityNotFoundError,
    EntityDuplicateError,
    ConsolidationNotFoundError,
    ConsolidationDuplicateError,
    ConsolidationStatusError,
    PackageNotFoundError,
    PackageStatusError,
    ExchangeRateNotFoundError,
)


router = APIRouter(prefix="/consolidation", tags=["Consolidation - Consolidation Comptable"])


def get_consolidation_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ConsolidationService:
    """Factory pour creer le service Consolidation."""
    return create_consolidation_service(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=str(current_user.id)
    )


def handle_consolidation_error(e: ConsolidationError):
    """Convertir une exception metier en HTTPException."""
    status_code = 400
    if "not_found" in e.code.lower():
        status_code = 404
    elif "duplicate" in e.code.lower():
        status_code = 409
    elif "access_denied" in e.code.lower() or "isolation" in e.code.lower():
        status_code = 403

    raise HTTPException(
        status_code=status_code,
        detail={
            "code": e.code,
            "message": e.message,
            "details": e.details
        }
    )


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=ConsolidationDashboard)
async def get_dashboard(
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Obtenir le dashboard de consolidation."""
    try:
        data = service.get_dashboard()
        return ConsolidationDashboard(**data)
    except ConsolidationError as e:
        handle_consolidation_error(e)


# ============================================================================
# PERIMETRES DE CONSOLIDATION
# ============================================================================

@router.post("/perimeters", response_model=ConsolidationPerimeterResponse, status_code=status.HTTP_201_CREATED)
async def create_perimeter(
    data: ConsolidationPerimeterCreate,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Creer un nouveau perimetre de consolidation."""
    try:
        perimeter = service.create_perimeter(data)
        return ConsolidationPerimeterResponse(
            **perimeter.__dict__,
            entity_count=0,
            consolidation_count=0
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/perimeters", response_model=PaginatedPerimeters)
async def list_perimeters(
    fiscal_year: Optional[int] = Query(None, description="Annee fiscale"),
    status: Optional[List[ConsolidationStatus]] = Query(None, description="Statuts"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Lister les perimetres de consolidation."""
    items, total = service.list_perimeters(
        fiscal_year=fiscal_year,
        status=status,
        page=page,
        page_size=page_size
    )

    pages = (total + page_size - 1) // page_size

    return PaginatedPerimeters(
        items=[ConsolidationPerimeterResponse(
            **p.__dict__,
            entity_count=service.perimeter_repo.get_entity_count(p.id),
            consolidation_count=0
        ) for p in items],
        total=total,
        page=page,
        per_page=page_size,
        pages=pages
    )


@router.get("/perimeters/{perimeter_id}", response_model=ConsolidationPerimeterResponse)
async def get_perimeter(
    perimeter_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Recuperer un perimetre par ID."""
    try:
        perimeter = service.get_perimeter(perimeter_id)
        return ConsolidationPerimeterResponse(
            **perimeter.__dict__,
            entity_count=service.perimeter_repo.get_entity_count(perimeter.id),
            consolidation_count=0
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.put("/perimeters/{perimeter_id}", response_model=ConsolidationPerimeterResponse)
async def update_perimeter(
    perimeter_id: UUID,
    data: ConsolidationPerimeterUpdate,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Mettre a jour un perimetre."""
    try:
        perimeter = service.update_perimeter(perimeter_id, data)
        return ConsolidationPerimeterResponse(
            **perimeter.__dict__,
            entity_count=service.perimeter_repo.get_entity_count(perimeter.id),
            consolidation_count=0
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.delete("/perimeters/{perimeter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_perimeter(
    perimeter_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Supprimer un perimetre (soft delete)."""
    try:
        service.delete_perimeter(perimeter_id)
    except ConsolidationError as e:
        handle_consolidation_error(e)


# ============================================================================
# ENTITES DU GROUPE
# ============================================================================

@router.post("/entities", response_model=ConsolidationEntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    data: ConsolidationEntityCreate,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Creer une nouvelle entite dans le perimetre."""
    try:
        entity = service.create_entity(data)
        return ConsolidationEntityResponse(**entity.__dict__, subsidiaries_count=0)
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/entities", response_model=PaginatedEntities)
async def list_entities(
    perimeter_id: Optional[UUID] = Query(None, description="ID du perimetre"),
    search: Optional[str] = Query(None, description="Recherche"),
    country: Optional[str] = Query(None, description="Code pays"),
    consolidation_method: Optional[List[ConsolidationMethod]] = Query(None, description="Methodes"),
    is_parent: Optional[bool] = Query(None, description="Est societe mere"),
    is_active: Optional[bool] = Query(None, description="Est active"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Lister les entites."""
    filters = EntityFilters(
        perimeter_id=perimeter_id,
        search=search,
        country=country,
        consolidation_method=consolidation_method,
        is_parent=is_parent,
        is_active=is_active
    )

    items, total = service.list_entities(filters=filters, page=page, page_size=page_size)
    pages = (total + page_size - 1) // page_size

    return PaginatedEntities(
        items=[ConsolidationEntityResponse(**e.__dict__, subsidiaries_count=0) for e in items],
        total=total,
        page=page,
        per_page=page_size,
        pages=pages
    )


@router.get("/entities/{entity_id}", response_model=ConsolidationEntityResponse)
async def get_entity(
    entity_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Recuperer une entite par ID."""
    try:
        entity = service.get_entity(entity_id)
        return ConsolidationEntityResponse(**entity.__dict__, subsidiaries_count=0)
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.put("/entities/{entity_id}", response_model=ConsolidationEntityResponse)
async def update_entity(
    entity_id: UUID,
    data: ConsolidationEntityUpdate,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Mettre a jour une entite."""
    try:
        entity = service.update_entity(entity_id, data)
        return ConsolidationEntityResponse(**entity.__dict__, subsidiaries_count=0)
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/perimeters/{perimeter_id}/entities", response_model=List[ConsolidationEntityResponse])
async def get_entities_by_perimeter(
    perimeter_id: UUID,
    include_inactive: bool = Query(False, description="Inclure les inactives"),
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Recuperer les entites d'un perimetre."""
    try:
        entities = service.get_entities_by_perimeter(perimeter_id, include_inactive)
        return [ConsolidationEntityResponse(**e.__dict__, subsidiaries_count=0) for e in entities]
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/perimeters/{perimeter_id}/ownership", response_model=dict)
async def calculate_ownership(
    perimeter_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Calculer les pourcentages de detention indirecte."""
    try:
        return service.calculate_indirect_ownership(perimeter_id)
    except ConsolidationError as e:
        handle_consolidation_error(e)


# ============================================================================
# COURS DE CHANGE
# ============================================================================

@router.post("/exchange-rates", response_model=ExchangeRateResponse, status_code=status.HTTP_201_CREATED)
async def create_exchange_rate(
    data: ExchangeRateCreate,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Creer un nouveau cours de change."""
    try:
        rate = service.set_exchange_rate(
            from_currency=data.from_currency,
            to_currency=data.to_currency,
            rate_date=data.rate_date,
            closing_rate=data.closing_rate,
            average_rate=data.average_rate,
            historical_rate=data.historical_rate,
            source=data.source
        )
        return ExchangeRateResponse(**rate.__dict__)
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/exchange-rates/bulk", response_model=List[ExchangeRateResponse], status_code=status.HTTP_201_CREATED)
async def create_exchange_rates_bulk(
    data: ExchangeRateBulkCreate,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Creer plusieurs cours de change."""
    try:
        rates = service.exchange_rate_repo.create_bulk(
            [r.model_dump() for r in data.rates]
        )
        return [ExchangeRateResponse(**r.__dict__) for r in rates]
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/exchange-rates", response_model=PaginatedExchangeRates)
async def list_exchange_rates(
    from_currency: Optional[str] = Query(None, description="Devise source"),
    to_currency: Optional[str] = Query(None, description="Devise cible"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Lister les cours de change."""
    items, total = service.exchange_rate_repo.list(
        from_currency=from_currency,
        to_currency=to_currency,
        page=page,
        page_size=page_size
    )
    pages = (total + page_size - 1) // page_size

    return PaginatedExchangeRates(
        items=[ExchangeRateResponse(**r.__dict__) for r in items],
        total=total,
        page=page,
        per_page=page_size,
        pages=pages
    )


# ============================================================================
# CONSOLIDATIONS
# ============================================================================

@router.post("/consolidations", response_model=ConsolidationResponse, status_code=status.HTTP_201_CREATED)
async def create_consolidation(
    data: ConsolidationCreate,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Creer une nouvelle consolidation."""
    try:
        consolidation = service.create_consolidation(data)
        return ConsolidationResponse(
            **consolidation.__dict__,
            packages_count=0,
            packages_validated=0,
            eliminations_count=0
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/consolidations", response_model=PaginatedConsolidations)
async def list_consolidations(
    search: Optional[str] = Query(None, description="Recherche"),
    fiscal_year: Optional[int] = Query(None, description="Annee fiscale"),
    status: Optional[List[ConsolidationStatus]] = Query(None, description="Statuts"),
    perimeter_id: Optional[UUID] = Query(None, description="ID du perimetre"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Lister les consolidations."""
    filters = ConsolidationFilters(
        search=search,
        fiscal_year=fiscal_year,
        status=status,
        perimeter_id=perimeter_id
    )

    items, total = service.list_consolidations(filters=filters, page=page, page_size=page_size)
    pages = (total + page_size - 1) // page_size

    return PaginatedConsolidations(
        items=[ConsolidationResponse(
            **c.__dict__,
            packages_count=0,
            packages_validated=0,
            eliminations_count=0
        ) for c in items],
        total=total,
        page=page,
        per_page=page_size,
        pages=pages
    )


@router.get("/consolidations/{consolidation_id}", response_model=ConsolidationResponse)
async def get_consolidation(
    consolidation_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Recuperer une consolidation par ID."""
    try:
        consolidation = service.get_consolidation(consolidation_id)
        stats = service.consolidation_repo.get_packages_count(consolidation_id)

        return ConsolidationResponse(
            **consolidation.__dict__,
            packages_count=sum(stats.values()),
            packages_validated=stats.get(PackageStatus.VALIDATED.value, 0),
            eliminations_count=len(service.elimination_repo.list_by_consolidation(consolidation_id))
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.put("/consolidations/{consolidation_id}", response_model=ConsolidationResponse)
async def update_consolidation(
    consolidation_id: UUID,
    data: ConsolidationUpdate,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Mettre a jour une consolidation."""
    try:
        consolidation = service.update_consolidation(consolidation_id, data)
        return ConsolidationResponse(
            **consolidation.__dict__,
            packages_count=0,
            packages_validated=0,
            eliminations_count=0
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/consolidations/{consolidation_id}/execute", response_model=dict)
async def execute_consolidation(
    consolidation_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Executer le processus de consolidation complet."""
    try:
        return service.execute_consolidation(consolidation_id)
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/consolidations/{consolidation_id}/submit", response_model=ConsolidationResponse)
async def submit_consolidation(
    consolidation_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Soumettre une consolidation pour revue."""
    try:
        consolidation = service.submit_consolidation(consolidation_id)
        return ConsolidationResponse(
            **consolidation.__dict__,
            packages_count=0,
            packages_validated=0,
            eliminations_count=0
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/consolidations/{consolidation_id}/validate", response_model=ConsolidationResponse)
async def validate_consolidation(
    consolidation_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Valider une consolidation."""
    try:
        consolidation = service.validate_consolidation(consolidation_id)
        return ConsolidationResponse(
            **consolidation.__dict__,
            packages_count=0,
            packages_validated=0,
            eliminations_count=0
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/consolidations/{consolidation_id}/publish", response_model=ConsolidationResponse)
async def publish_consolidation(
    consolidation_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Publier une consolidation."""
    try:
        consolidation = service.publish_consolidation(consolidation_id)
        return ConsolidationResponse(
            **consolidation.__dict__,
            packages_count=0,
            packages_validated=0,
            eliminations_count=0
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/consolidations/{consolidation_id}/progress", response_model=ConsolidationProgress)
async def get_consolidation_progress(
    consolidation_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Obtenir la progression d'une consolidation."""
    try:
        consolidation = service.get_consolidation(consolidation_id)
        stats = service.consolidation_repo.get_packages_count(consolidation_id)
        entities = service.get_entities_by_perimeter(consolidation.perimeter_id)

        total_entities = len(entities)
        submitted = stats.get(PackageStatus.SUBMITTED.value, 0)
        validated = stats.get(PackageStatus.VALIDATED.value, 0)
        rejected = stats.get(PackageStatus.REJECTED.value, 0)
        completion = (validated / total_entities * 100) if total_entities > 0 else 0

        reports = service.report_repo.list_by_consolidation(consolidation_id)

        return ConsolidationProgress(
            consolidation_id=consolidation_id,
            total_entities=total_entities,
            packages_submitted=submitted,
            packages_validated=validated,
            packages_rejected=rejected,
            completion_pct=completion,
            eliminations_generated=len(service.elimination_repo.list_by_consolidation(consolidation_id)) > 0,
            restatements_validated=True,
            reports_generated=[r.report_type.value for r in reports]
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


# ============================================================================
# PAQUETS DE CONSOLIDATION
# ============================================================================

@router.post("/packages", response_model=ConsolidationPackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    data: ConsolidationPackageCreate,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Creer un paquet de consolidation."""
    try:
        package = service.create_package(data)
        entity = service.get_entity(package.entity_id)
        return ConsolidationPackageResponse(
            **package.__dict__,
            entity_name=entity.name,
            entity_code=entity.code
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/packages", response_model=PaginatedPackages)
async def list_packages(
    consolidation_id: Optional[UUID] = Query(None, description="ID consolidation"),
    entity_id: Optional[UUID] = Query(None, description="ID entite"),
    status: Optional[List[PackageStatus]] = Query(None, description="Statuts"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Lister les paquets de consolidation."""
    filters = PackageFilters(
        consolidation_id=consolidation_id,
        entity_id=entity_id,
        status=status
    )

    items, total = service.package_repo.list(filters=filters, page=page, page_size=page_size)
    pages = (total + page_size - 1) // page_size

    responses = []
    for p in items:
        entity = service.entity_repo.get_by_id(p.entity_id)
        responses.append(ConsolidationPackageResponse(
            **p.__dict__,
            entity_name=entity.name if entity else None,
            entity_code=entity.code if entity else None
        ))

    return PaginatedPackages(
        items=responses,
        total=total,
        page=page,
        per_page=page_size,
        pages=pages
    )


@router.get("/packages/{package_id}", response_model=ConsolidationPackageResponse)
async def get_package(
    package_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Recuperer un paquet par ID."""
    try:
        package = service.get_package(package_id)
        entity = service.get_entity(package.entity_id)
        return ConsolidationPackageResponse(
            **package.__dict__,
            entity_name=entity.name,
            entity_code=entity.code
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.put("/packages/{package_id}", response_model=ConsolidationPackageResponse)
async def update_package(
    package_id: UUID,
    data: ConsolidationPackageUpdate,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Mettre a jour un paquet."""
    try:
        package = service.update_package(package_id, data)
        entity = service.get_entity(package.entity_id)
        return ConsolidationPackageResponse(
            **package.__dict__,
            entity_name=entity.name,
            entity_code=entity.code
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/packages/{package_id}/submit", response_model=ConsolidationPackageResponse)
async def submit_package(
    package_id: UUID,
    data: ConsolidationPackageSubmit = None,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Soumettre un paquet pour validation."""
    try:
        package = service.submit_package(package_id)
        entity = service.get_entity(package.entity_id)
        return ConsolidationPackageResponse(
            **package.__dict__,
            entity_name=entity.name,
            entity_code=entity.code
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/packages/{package_id}/validate", response_model=ConsolidationPackageResponse)
async def validate_package(
    package_id: UUID,
    data: ConsolidationPackageValidate = None,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Valider un paquet."""
    try:
        package = service.validate_package(package_id)
        entity = service.get_entity(package.entity_id)
        return ConsolidationPackageResponse(
            **package.__dict__,
            entity_name=entity.name,
            entity_code=entity.code
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/packages/{package_id}/reject", response_model=ConsolidationPackageResponse)
async def reject_package(
    package_id: UUID,
    data: ConsolidationPackageReject,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Rejeter un paquet."""
    try:
        package = service.reject_package(package_id, data.reason)
        entity = service.get_entity(package.entity_id)
        return ConsolidationPackageResponse(
            **package.__dict__,
            entity_name=entity.name,
            entity_code=entity.code
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


# ============================================================================
# ELIMINATIONS
# ============================================================================

@router.post("/eliminations/generate", response_model=GenerateEliminationsResponse)
async def generate_eliminations(
    data: GenerateEliminationsRequest,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Generer les eliminations automatiques."""
    try:
        eliminations = service.generate_eliminations(
            consolidation_id=data.consolidation_id,
            elimination_types=data.elimination_types
        )

        return GenerateEliminationsResponse(
            generated_count=len(eliminations),
            eliminations=[EliminationEntryResponse(**e.__dict__) for e in eliminations],
            warnings=[]
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/consolidations/{consolidation_id}/eliminations", response_model=PaginatedEliminations)
async def list_eliminations(
    consolidation_id: UUID,
    elimination_type: Optional[EliminationType] = Query(None, description="Type d'elimination"),
    is_validated: Optional[bool] = Query(None, description="Est validee"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Lister les eliminations d'une consolidation."""
    try:
        eliminations = service.elimination_repo.list_by_consolidation(
            consolidation_id=consolidation_id,
            elimination_type=elimination_type,
            is_validated=is_validated
        )

        # Pagination manuelle
        total = len(eliminations)
        offset = (page - 1) * page_size
        items = eliminations[offset:offset + page_size]
        pages = (total + page_size - 1) // page_size

        return PaginatedEliminations(
            items=[EliminationEntryResponse(**e.__dict__) for e in items],
            total=total,
            page=page,
            per_page=page_size,
            pages=pages
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/eliminations/{elimination_id}/validate", response_model=EliminationEntryResponse)
async def validate_elimination(
    elimination_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Valider une elimination."""
    try:
        elimination = service.elimination_repo.get_by_id(elimination_id)
        if not elimination:
            raise HTTPException(status_code=404, detail="Elimination non trouvee")

        elimination = service.elimination_repo.validate(
            elimination,
            UUID(service.user_id) if service.user_id else None
        )
        return EliminationEntryResponse(**elimination.__dict__)
    except ConsolidationError as e:
        handle_consolidation_error(e)


# ============================================================================
# RECONCILIATIONS INTERCOMPANY
# ============================================================================

@router.post("/consolidations/{consolidation_id}/reconciliations/auto", response_model=dict)
async def auto_reconcile(
    consolidation_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Reconcilier automatiquement les soldes intercompany."""
    try:
        return service.auto_reconcile_intercompany(consolidation_id)
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/consolidations/{consolidation_id}/reconciliations", response_model=PaginatedReconciliations)
async def list_reconciliations(
    consolidation_id: UUID,
    entity_id: Optional[UUID] = Query(None, description="ID entite"),
    transaction_type: Optional[str] = Query(None, description="Type de transaction"),
    is_reconciled: Optional[bool] = Query(None, description="Est reconcilie"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Lister les reconciliations d'une consolidation."""
    try:
        filters = ReconciliationFilters(
            consolidation_id=consolidation_id,
            entity_id=entity_id,
            transaction_type=transaction_type,
            is_reconciled=is_reconciled
        )

        items, total = service.reconciliation_repo.list(filters=filters, page=page, page_size=page_size)
        pages = (total + page_size - 1) // page_size

        return PaginatedReconciliations(
            items=[IntercompanyReconciliationResponse(**r.__dict__) for r in items],
            total=total,
            page=page,
            per_page=page_size,
            pages=pages
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/consolidations/{consolidation_id}/reconciliations/summary", response_model=ReconciliationSummary)
async def get_reconciliation_summary(
    consolidation_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Obtenir le resume des reconciliations."""
    try:
        data = service.get_reconciliation_summary(consolidation_id)
        return ReconciliationSummary(**data, by_type={})
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/reconciliations/{reconciliation_id}/reconcile", response_model=IntercompanyReconciliationResponse)
async def mark_reconciled(
    reconciliation_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Marquer une reconciliation comme reconciliee."""
    try:
        recon = service.reconciliation_repo.get_by_id(reconciliation_id)
        if not recon:
            raise HTTPException(status_code=404, detail="Reconciliation non trouvee")

        recon = service.reconciliation_repo.reconcile(
            recon,
            UUID(service.user_id) if service.user_id else None
        )
        return IntercompanyReconciliationResponse(**recon.__dict__)
    except ConsolidationError as e:
        handle_consolidation_error(e)


# ============================================================================
# RAPPORTS
# ============================================================================

@router.post("/reports/generate", response_model=ConsolidatedReportResponse)
async def generate_report(
    data: GenerateReportRequest,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Generer un rapport consolide."""
    try:
        report = service.generate_report(data)
        return ConsolidatedReportResponse(**report.__dict__)
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/consolidations/{consolidation_id}/reports", response_model=PaginatedReports)
async def list_reports(
    consolidation_id: UUID,
    report_type: Optional[ReportType] = Query(None, description="Type de rapport"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Lister les rapports d'une consolidation."""
    try:
        reports = service.report_repo.list_by_consolidation(consolidation_id, report_type)

        # Pagination manuelle
        total = len(reports)
        offset = (page - 1) * page_size
        items = reports[offset:offset + page_size]
        pages = (total + page_size - 1) // page_size

        return PaginatedReports(
            items=[ConsolidatedReportResponse(**r.__dict__) for r in items],
            total=total,
            page=page,
            per_page=page_size,
            pages=pages
        )
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.get("/reports/{report_id}", response_model=ConsolidatedReportResponse)
async def get_report(
    report_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Recuperer un rapport par ID."""
    try:
        report = service.report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Rapport non trouve")
        return ConsolidatedReportResponse(**report.__dict__)
    except ConsolidationError as e:
        handle_consolidation_error(e)


@router.post("/reports/{report_id}/finalize", response_model=ConsolidatedReportResponse)
async def finalize_report(
    report_id: UUID,
    service: ConsolidationService = Depends(get_consolidation_service)
):
    """Finaliser un rapport."""
    try:
        report = service.report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Rapport non trouve")

        report = service.report_repo.finalize(
            report,
            UUID(service.user_id) if service.user_id else None
        )
        return ConsolidatedReportResponse(**report.__dict__)
    except ConsolidationError as e:
        handle_consolidation_error(e)
