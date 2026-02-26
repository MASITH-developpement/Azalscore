"""
AZALS MODULE - FEC: Router API
==============================

Endpoints REST pour la génération et validation du FEC.
"""
from __future__ import annotations


import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.dependencies import get_tenant_id
from app.core.models import User

from .service_sync import FECServiceSync
from .schemas import (
    FECExportRequest,
    FECExportResponse,
    FECValidationResponse,
    FECValidateRequest,
    FECListResponse,
    FECDownloadResponse,
    FECExportStatusEnum,
    FECStatistics,
    FEC_COLUMNS,
    FECColumn,
)
from .models import FECExportStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fec", tags=["FEC - Fichier des Écritures Comptables"])


# ============================================================================
# ENDPOINTS GÉNÉRATION
# ============================================================================

@router.post(
    "/exports",
    response_model=FECExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Générer un export FEC",
    description="""
    Génère un fichier FEC conforme à l'Article A.47 A-1 du LPF.

    **Paramètres obligatoires:**
    - `fiscal_year_id`: ID de l'exercice fiscal
    - `siren`: SIREN de l'entreprise (9 chiffres)
    - `company_name`: Raison sociale

    **Options:**
    - `format`: txt (défaut) ou xml
    - `encoding`: UTF-8 (défaut) ou ISO-8859-15
    - `separator`: TAB (défaut) ou PIPE

    **Conformité:**
    - 18 colonnes obligatoires
    - Format dates YYYYMMDD
    - Virgule décimale
    - Nommage: {SIREN}FEC{YYYYMMDD}.txt
    """,
)
def generate_fec(
    request: FECExportRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> FECExportResponse:
    """Génère un export FEC pour un exercice fiscal."""
    try:
        service = FECServiceSync(db, tenant_id)
        export = service.generate_fec(request)

        # Convertir en réponse
        return FECExportResponse(
            id=export.id,
            tenant_id=export.tenant_id,
            siren=export.siren,
            company_name=export.company_name,
            fiscal_year_code=export.fiscal_year_code,
            start_date=export.start_date.date() if hasattr(export.start_date, 'date') else export.start_date,
            end_date=export.end_date.date() if hasattr(export.end_date, 'date') else export.end_date,
            format=export.format.value,
            encoding=export.encoding.value,
            separator=export.separator.value,
            filename=export.filename,
            file_size=export.file_size,
            file_hash=export.file_hash,
            status=FECExportStatusEnum(export.status.value),
            is_valid=export.is_valid,
            validation_errors=export.validation_errors,
            validation_warnings=export.validation_warnings,
            statistics=FECStatistics(
                total_entries=export.total_entries,
                total_lines=export.total_lines,
                total_debit=export.total_debit,
                total_credit=export.total_credit,
                balance=export.total_debit - export.total_credit,
                is_balanced=abs(export.total_debit - export.total_credit) < 0.01,
                journals_count=0,
                accounts_count=0,
            ) if export.total_entries else None,
            error_message=export.error_message,
            requested_at=export.requested_at,
            completed_at=export.completed_at,
        )

    except ValueError as e:
        logger.warning(f"[FEC] Erreur validation: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[FEC] Erreur génération: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du FEC: {str(e)}",
        )


@router.get(
    "/exports",
    response_model=FECListResponse,
    summary="Lister les exports FEC",
    description="Liste les exports FEC du tenant avec filtres optionnels.",
)
def list_exports(
    fiscal_year_code: Optional[str] = Query(None, description="Filtrer par exercice fiscal"),
    fec_status: Optional[FECExportStatusEnum] = Query(None, alias="status", description="Filtrer par statut"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(20, ge=1, le=100, description="Taille de page"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> FECListResponse:
    """Liste les exports FEC."""
    service = FECServiceSync(db, tenant_id)

    status_filter = FECExportStatus(fec_status.value) if fec_status else None
    skip = (page - 1) * page_size

    exports, total = service.list_exports(
        fiscal_year_code=fiscal_year_code,
        status=status_filter,
        skip=skip,
        limit=page_size,
    )

    items = [
        FECExportResponse(
            id=e.id,
            tenant_id=e.tenant_id,
            siren=e.siren,
            company_name=e.company_name,
            fiscal_year_code=e.fiscal_year_code,
            start_date=e.start_date.date() if hasattr(e.start_date, 'date') else e.start_date,
            end_date=e.end_date.date() if hasattr(e.end_date, 'date') else e.end_date,
            format=e.format.value,
            encoding=e.encoding.value,
            separator=e.separator.value,
            filename=e.filename,
            file_size=e.file_size,
            file_hash=e.file_hash,
            status=FECExportStatusEnum(e.status.value),
            is_valid=e.is_valid,
            validation_errors=e.validation_errors,
            validation_warnings=e.validation_warnings,
            error_message=e.error_message,
            requested_at=e.requested_at,
            completed_at=e.completed_at,
        )
        for e in exports
    ]

    return FECListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/exports/{export_id}",
    response_model=FECExportResponse,
    summary="Récupérer un export FEC",
    description="Récupère les détails d'un export FEC par son ID.",
)
def get_export(
    export_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> FECExportResponse:
    """Récupère un export FEC."""
    service = FECServiceSync(db, tenant_id)
    export = service.get_export(export_id)

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export FEC non trouvé: {export_id}",
        )

    return FECExportResponse(
        id=export.id,
        tenant_id=export.tenant_id,
        siren=export.siren,
        company_name=export.company_name,
        fiscal_year_code=export.fiscal_year_code,
        start_date=export.start_date.date() if hasattr(export.start_date, 'date') else export.start_date,
        end_date=export.end_date.date() if hasattr(export.end_date, 'date') else export.end_date,
        format=export.format.value,
        encoding=export.encoding.value,
        separator=export.separator.value,
        filename=export.filename,
        file_size=export.file_size,
        file_hash=export.file_hash,
        status=FECExportStatusEnum(export.status.value),
        is_valid=export.is_valid,
        validation_errors=export.validation_errors,
        validation_warnings=export.validation_warnings,
        statistics=FECStatistics(
            total_entries=export.total_entries,
            total_lines=export.total_lines,
            total_debit=export.total_debit,
            total_credit=export.total_credit,
            balance=export.total_debit - export.total_credit,
            is_balanced=abs(export.total_debit - export.total_credit) < 0.01,
            journals_count=0,
            accounts_count=0,
        ) if export.total_entries else None,
        error_message=export.error_message,
        requested_at=export.requested_at,
        completed_at=export.completed_at,
    )


# ============================================================================
# ENDPOINTS VALIDATION
# ============================================================================

@router.post(
    "/validate",
    response_model=FECValidationResponse,
    summary="Valider un fichier FEC",
    description="""
    Valide un fichier FEC selon les règles DGFiP.

    **Règles de validation:**
    - Structure 18 colonnes obligatoires
    - Format des dates (YYYYMMDD)
    - Équilibre débit/crédit par écriture
    - Numérotation continue sans rupture
    - Montants positifs
    - Cohérence des dates (écriture >= pièce)
    """,
)
def validate_fec(
    request: FECValidateRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> FECValidationResponse:
    """Valide un fichier FEC."""
    service = FECServiceSync(db, tenant_id)

    try:
        if request.export_id:
            # Valider un export existant
            return service.validate_fec(request.export_id)
        elif request.file_content:
            # Valider un contenu brut (décodage base64)
            import base64
            content = base64.b64decode(request.file_content).decode("utf-8")
            return service.validate_fec_content(content)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="export_id ou file_content requis",
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))


@router.post(
    "/exports/{export_id}/validate",
    response_model=FECValidationResponse,
    summary="Revalider un export FEC",
    description="Relance la validation d'un export FEC existant.",
)
def revalidate_export(
    export_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> FECValidationResponse:
    """Revalide un export FEC existant."""
    service = FECServiceSync(db, tenant_id)

    try:
        return service.validate_fec(export_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))


# ============================================================================
# ENDPOINTS TÉLÉCHARGEMENT
# ============================================================================

@router.get(
    "/exports/{export_id}/download",
    response_model=FECDownloadResponse,
    summary="Télécharger un fichier FEC",
    description="Télécharge le fichier FEC généré (base64 encoded).",
)
def download_export(
    export_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> FECDownloadResponse:
    """Télécharge un fichier FEC."""
    service = FECServiceSync(db, tenant_id)

    try:
        filename, content = service.download_export(export_id)
        import base64
        import hashlib

        return FECDownloadResponse(
            filename=filename,
            content_type="text/plain; charset=utf-8",
            content=base64.b64encode(content).decode("ascii"),
            file_size=len(content),
            file_hash=hashlib.sha256(content).hexdigest(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))


# ============================================================================
# ENDPOINTS ARCHIVAGE
# ============================================================================

@router.post(
    "/exports/{export_id}/archive",
    status_code=status.HTTP_200_OK,
    summary="Archiver un export FEC",
    description="""
    Archive un export FEC pour conservation légale (10 ans).

    Seuls les exports valides et terminés peuvent être archivés.
    """,
)
def archive_export(
    export_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Archive un export FEC."""
    service = FECServiceSync(db, tenant_id)

    try:
        archive = service.archive_export(export_id)
        return {
            "message": "Export archivé avec succès",
            "archive_id": str(archive.id),
            "retention_until": archive.retention_until.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# ENDPOINTS RÉFÉRENCE
# ============================================================================

@router.get(
    "/columns",
    response_model=list[FECColumn],
    summary="Liste des colonnes FEC",
    description="Retourne la définition des 18 colonnes FEC obligatoires.",
)
def get_fec_columns() -> list[FECColumn]:
    """Retourne la définition des colonnes FEC."""
    return FEC_COLUMNS


@router.get(
    "/specification",
    summary="Spécification FEC",
    description="Retourne la spécification complète du format FEC.",
)
def get_fec_specification() -> dict:
    """Retourne la spécification FEC."""
    return {
        "name": "Fichier des Écritures Comptables",
        "abbreviation": "FEC",
        "legal_reference": "Article A.47 A-1 du Livre des Procédures Fiscales",
        "columns_count": 18,
        "columns": [col.model_dump() for col in FEC_COLUMNS],
        "file_naming": "{SIREN}FEC{YYYYMMDD}.txt",
        "supported_encodings": ["UTF-8", "ISO-8859-15"],
        "supported_separators": ["TAB", "PIPE"],
        "date_format": "YYYYMMDD",
        "decimal_separator": ",",
        "mandatory_rules": [
            "Équilibre débit/crédit par écriture",
            "Numérotation continue sans rupture",
            "Dates cohérentes (écriture >= pièce)",
            "Montants positifs ou nuls",
            "Pas de débit ET crédit positifs sur même ligne",
        ],
        "retention_period": "10 ans",
        "authority": "Direction Générale des Finances Publiques (DGFiP)",
    }
