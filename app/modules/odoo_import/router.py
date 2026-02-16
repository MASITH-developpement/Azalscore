"""
AZALS MODULE - Odoo Import - Router
====================================

Endpoints API pour l'import de donnees Odoo.
Module activable depuis Administration > Acces Modules > Import de donnees.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.models import User

from .models import OdooSyncType
from .schemas import (
    OdooConnectionConfigCreate,
    OdooConnectionConfigUpdate,
    OdooConnectionConfigResponse,
    OdooTestConnectionRequest,
    OdooTestConnectionResponse,
    OdooImportRequest,
    OdooImportHistoryResponse,
    OdooDataPreviewRequest,
    OdooDataPreviewResponse,
    OdooSyncStats,
    OdooScheduleConfigRequest,
    OdooScheduleConfigResponse,
    OdooNextRunsResponse,
    OdooSelectiveImportRequest,
    OdooHistorySearchRequest,
    OdooHistorySearchResponse,
    OdooHistoryDetailResponse,
)
from .service import OdooImportService
from app.services.scheduler import scheduler_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/odoo", tags=["Import Odoo"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_service(request: Request, db: Session = Depends(get_db)) -> OdooImportService:
    """Factory pour OdooImportService avec tenant isolation."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant non identifie")

    user_id = None
    if hasattr(request.state, "user") and request.state.user:
        user_id = str(request.state.user.id)

    return OdooImportService(db, tenant_id, user_id)


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@router.post("/config", response_model=OdooConnectionConfigResponse)
async def create_config(
    data: OdooConnectionConfigCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cree une nouvelle configuration de connexion Odoo.

    Permet de configurer:
    - URL et base de donnees Odoo
    - Authentification (API key recommandee pour Odoo 14+)
    - Types de donnees a synchroniser
    """
    service = get_service(request, db)

    try:
        config = service.create_config(
            name=data.name,
            description=data.description,
            odoo_url=data.odoo_url,
            odoo_database=data.odoo_database,
            username=data.username,
            credential=data.credential,
            auth_method=data.auth_method,
            sync_products=data.sync_products,
            sync_contacts=data.sync_contacts,
            sync_suppliers=data.sync_suppliers,
            sync_purchase_orders=data.sync_purchase_orders,
        )
        return OdooConnectionConfigResponse.model_validate(config)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur creation config: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la creation")


@router.get("/config", response_model=List[OdooConnectionConfigResponse])
async def list_configs(
    active_only: bool = Query(False, description="Uniquement les configurations actives"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste les configurations de connexion Odoo du tenant.
    """
    service = get_service(request, db)
    configs = service.list_configs(active_only=active_only)
    return [OdooConnectionConfigResponse.model_validate(c) for c in configs]


@router.get("/config/{config_id}", response_model=OdooConnectionConfigResponse)
async def get_config(
    config_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere une configuration de connexion par ID.
    """
    service = get_service(request, db)
    config = service.get_config(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    return OdooConnectionConfigResponse.model_validate(config)


@router.put("/config/{config_id}", response_model=OdooConnectionConfigResponse)
async def update_config(
    config_id: UUID,
    data: OdooConnectionConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Met a jour une configuration de connexion.
    """
    service = get_service(request, db)

    config = service.update_config(
        config_id,
        **data.model_dump(exclude_unset=True),
    )

    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    return OdooConnectionConfigResponse.model_validate(config)


@router.delete("/config/{config_id}")
async def delete_config(
    config_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Supprime une configuration de connexion.
    """
    service = get_service(request, db)

    if not service.delete_config(config_id):
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    return {"message": "Configuration supprimee"}


# ============================================================================
# TEST CONNECTION
# ============================================================================

@router.post("/test", response_model=OdooTestConnectionResponse)
async def test_connection(
    data: OdooTestConnectionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Teste une connexion Odoo (sans sauvegarder la configuration).

    Utile pour valider les parametres avant de creer une configuration.
    """
    service = get_service(request, db)

    result = service.test_connection(
        odoo_url=data.odoo_url,
        odoo_database=data.odoo_database,
        username=data.username,
        credential=data.credential,
        auth_method=data.auth_method,
    )

    return OdooTestConnectionResponse(**result)


@router.post("/config/{config_id}/test", response_model=OdooTestConnectionResponse)
async def test_config_connection(
    config_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Teste la connexion d'une configuration existante.

    Met a jour le statut de connexion de la configuration.
    """
    service = get_service(request, db)
    result = service.test_config_connection(config_id)

    if result.get("error_type") == "not_found":
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    return OdooTestConnectionResponse(**result)


# ============================================================================
# IMPORT ENDPOINTS
# ============================================================================

@router.post("/import/products", response_model=OdooImportHistoryResponse)
async def import_products(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer le delta et reimporter tout"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lance l'import des produits depuis Odoo.

    Par defaut, effectue un delta sync (uniquement les modifications).
    Utilisez full_sync=true pour reimporter tous les produits.
    """
    service = get_service(request, db)

    try:
        history = service.import_products(config_id, full_sync=full_sync)
        return OdooImportHistoryResponse.model_validate(history)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur import produits: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")


@router.post("/import/contacts", response_model=OdooImportHistoryResponse)
async def import_contacts(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer le delta et reimporter tout"),
    include_suppliers: bool = Query(False, description="Inclure les fournisseurs"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lance l'import des contacts/clients depuis Odoo.

    Par defaut, importe uniquement les clients (customer_rank > 0).
    Utilisez include_suppliers=true pour inclure les fournisseurs.
    """
    service = get_service(request, db)

    try:
        history = service.import_contacts(
            config_id,
            full_sync=full_sync,
            include_suppliers=include_suppliers,
        )
        return OdooImportHistoryResponse.model_validate(history)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur import contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")


@router.post("/import/suppliers", response_model=OdooImportHistoryResponse)
async def import_suppliers(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer le delta et reimporter tout"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lance l'import des fournisseurs depuis Odoo.

    Importe les contacts avec supplier_rank > 0.
    """
    service = get_service(request, db)

    try:
        history = service.import_suppliers(config_id, full_sync=full_sync)
        return OdooImportHistoryResponse.model_validate(history)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur import fournisseurs: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")


@router.post("/import/purchase_orders", response_model=OdooImportHistoryResponse)
async def import_purchase_orders(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer le delta et reimporter tout"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lance l'import des commandes d'achat depuis Odoo."""
    service = get_service(request, db)
    try:
        history = service.import_purchase_orders(config_id, full_sync=full_sync)
        return OdooImportHistoryResponse.model_validate(history)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur import commandes achat: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")


@router.post("/import/sale_orders", response_model=OdooImportHistoryResponse)
async def import_sale_orders(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer le delta et reimporter tout"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lance l'import des commandes de vente depuis Odoo (sale.order)."""
    service = get_service(request, db)
    try:
        history = service.import_sale_orders(config_id, full_sync=full_sync)
        return OdooImportHistoryResponse.model_validate(history)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur import commandes vente: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")


@router.post("/import/invoices", response_model=OdooImportHistoryResponse)
async def import_invoices(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer le delta et reimporter tout"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lance l'import des factures depuis Odoo (account.move type=out_invoice)."""
    service = get_service(request, db)
    try:
        history = service.import_invoices(config_id, full_sync=full_sync)
        return OdooImportHistoryResponse.model_validate(history)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur import factures: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")


@router.post("/import/quotes", response_model=OdooImportHistoryResponse)
async def import_quotes(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer le delta et reimporter tout"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lance l'import des devis depuis Odoo (sale.order state=draft/sent)."""
    service = get_service(request, db)
    try:
        history = service.import_quotes(config_id, full_sync=full_sync)
        return OdooImportHistoryResponse.model_validate(history)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur import devis: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")


@router.post("/import/accounting", response_model=OdooImportHistoryResponse)
async def import_accounting(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer le delta et reimporter tout"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lance l'import des ecritures comptables depuis Odoo (account.move.line)."""
    service = get_service(request, db)
    try:
        history = service.import_accounting(config_id, full_sync=full_sync)
        return OdooImportHistoryResponse.model_validate(history)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur import comptabilite: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")


@router.post("/import/bank", response_model=OdooImportHistoryResponse)
async def import_bank(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer le delta et reimporter tout"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lance l'import des releves bancaires depuis Odoo (account.bank.statement)."""
    service = get_service(request, db)
    try:
        history = service.import_bank_statements(config_id, full_sync=full_sync)
        return OdooImportHistoryResponse.model_validate(history)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur import banque: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")


@router.post("/import/interventions", response_model=OdooImportHistoryResponse)
async def import_interventions(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer le delta et reimporter tout"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lance l'import des interventions depuis Odoo (project.task ou helpdesk.ticket)."""
    service = get_service(request, db)
    try:
        history = service.import_interventions(config_id, full_sync=full_sync)
        return OdooImportHistoryResponse.model_validate(history)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur import interventions: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")


@router.post("/import/full", response_model=List[OdooImportHistoryResponse])
async def full_sync(
    config_id: UUID = Query(..., description="ID de la configuration"),
    full_sync: bool = Query(False, description="Ignorer les deltas et tout reimporter"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lance une synchronisation complete (tous les types actives).

    Execute les imports dans l'ordre:
    1. Produits (si sync_products active)
    2. Contacts (si sync_contacts active)
    3. Fournisseurs (si sync_suppliers active)
    4. Commandes vente/achat
    5. Factures et devis
    6. Comptabilite et banque
    7. Interventions
    """
    service = get_service(request, db)

    try:
        histories = service.full_sync(config_id, full_sync=full_sync)
        return [OdooImportHistoryResponse.model_validate(h) for h in histories]

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur sync complete: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur sync: {str(e)}")


# ============================================================================
# HISTORY & STATS
# ============================================================================

@router.get("/history", response_model=List[OdooImportHistoryResponse])
async def get_import_history(
    config_id: Optional[UUID] = Query(None, description="Filtrer par configuration"),
    limit: int = Query(50, ge=1, le=200, description="Nombre max de resultats"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere l'historique des imports.
    """
    service = get_service(request, db)
    histories = service.get_import_history(config_id=config_id, limit=limit)
    return [OdooImportHistoryResponse.model_validate(h) for h in histories]


@router.get("/config/{config_id}/stats")
async def get_config_stats(
    config_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere les statistiques d'une configuration.
    """
    service = get_service(request, db)
    stats = service.get_stats(config_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    return stats


# ============================================================================
# PREVIEW
# ============================================================================

@router.post("/preview", response_model=OdooDataPreviewResponse)
async def preview_data(
    data: OdooDataPreviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Previsualise les donnees Odoo avant import.

    Permet de voir les donnees brutes Odoo et leur mapping vers AZALSCORE.
    Utile pour verifier le mapping avant un import.
    """
    service = get_service(request, db)

    try:
        result = service.preview_data(
            config_id=data.config_id,
            model=data.model,
            limit=data.limit,
        )

        return OdooDataPreviewResponse(
            model=result["model"],
            total_count=result["total_count"],
            preview_count=result["preview_count"],
            fields=result["fields"],
            records=result["odoo_records"],
            mapping_preview=result["mapped_records"],
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[ODOO] Erreur preview: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur preview: {str(e)}")


# ============================================================================
# ODOO MODELS INFO
# ============================================================================

@router.get("/models")
async def get_available_models(
    config_id: UUID = Query(..., description="ID de la configuration"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste les modeles Odoo disponibles pour l'import.

    Retourne les modeles supportes avec leur comptage.
    """
    service = get_service(request, db)
    config = service.get_config(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    try:
        from .connector import OdooConnector

        credential = service._decrypt_credential(config.encrypted_credential)
        connector = OdooConnector(
            url=config.odoo_url,
            database=config.odoo_database,
            username=config.username,
            credential=credential,
            auth_method=config.auth_method.value,
        )
        connector.connect()

        # Modeles supportes
        supported_models = [
            {
                "model": "product.product",
                "name": "Produits",
                "azals_target": "Product",
                "count": connector.search_count("product.product", []),
            },
            {
                "model": "res.partner",
                "name": "Contacts / Partenaires",
                "azals_target": "UnifiedContact",
                "count": connector.search_count("res.partner", [("is_company", "=", True)]),
            },
            {
                "model": "res.partner (clients)",
                "name": "Clients",
                "azals_target": "UnifiedContact",
                "count": connector.search_count("res.partner", [("customer_rank", ">", 0)]),
            },
            {
                "model": "res.partner (fournisseurs)",
                "name": "Fournisseurs",
                "azals_target": "UnifiedContact",
                "count": connector.search_count("res.partner", [("supplier_rank", ">", 0)]),
            },
        ]

        # Verifier si purchase.order existe
        try:
            po_count = connector.search_count("purchase.order", [])
            supported_models.append({
                "model": "purchase.order",
                "name": "Commandes d'achat",
                "azals_target": "LegacyPurchaseOrder",
                "count": po_count,
            })
        except Exception:
            pass  # Module purchase non installe

        return {"models": supported_models}

    except Exception as e:
        logger.exception(f"[ODOO] Erreur liste modeles: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ============================================================================
# SCHEDULING ENDPOINTS
# ============================================================================

@router.put("/config/{config_id}/schedule", response_model=OdooScheduleConfigResponse)
async def configure_schedule(
    config_id: UUID,
    data: OdooScheduleConfigRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Configure la planification d'une connexion Odoo.

    Modes disponibles:
    - disabled: Pas de planification automatique
    - cron: Expression cron (ex: "0 8 * * 1-5" = 8h du lun au ven)
    - interval: Intervalle en minutes (5-1440)
    """
    service = get_service(request, db)
    config = service.get_config(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    # Valider les parametres selon le mode
    if data.mode == 'cron' and not data.cron_expression:
        raise HTTPException(
            status_code=400,
            detail="cron_expression requis pour mode='cron'"
        )
    if data.mode == 'interval' and not data.interval_minutes:
        raise HTTPException(
            status_code=400,
            detail="interval_minutes requis pour mode='interval'"
        )

    try:
        # Mettre a jour la config en base
        from .models import OdooScheduleMode
        from sqlalchemy import update

        mode_enum = OdooScheduleMode(data.mode)

        db.execute(
            update(service.config_model).where(
                service.config_model.id == config_id
            ).values(
                schedule_mode=mode_enum,
                schedule_cron_expression=data.cron_expression if data.mode == 'cron' else None,
                schedule_interval_minutes=data.interval_minutes if data.mode == 'interval' else None,
                schedule_timezone=data.timezone,
            )
        )
        db.commit()

        # Mettre a jour le scheduler
        if data.mode == 'disabled':
            scheduler_service.remove_odoo_job(config_id)
            next_run = None
        else:
            scheduler_service.add_odoo_job(
                config_id=config_id,
                tenant_id=config.tenant_id,
                mode=data.mode,
                cron_expression=data.cron_expression,
                interval_minutes=data.interval_minutes,
                timezone=data.timezone,
            )
            next_run = scheduler_service.get_next_run_time(config_id)

        # Sauvegarder next_scheduled_run
        if next_run:
            from sqlalchemy import text
            db.execute(text("""
                UPDATE odoo_connection_configs
                SET next_scheduled_run = :next_run
                WHERE id = :config_id
            """), {"next_run": next_run, "config_id": str(config_id)})
            db.commit()

        return OdooScheduleConfigResponse(
            config_id=config_id,
            mode=data.mode,
            cron_expression=data.cron_expression,
            interval_minutes=data.interval_minutes,
            timezone=data.timezone,
            is_paused=False,
            next_scheduled_run=next_run,
            last_scheduled_run=config.last_scheduled_run,
            message=f"Planification configuree: {data.mode}"
        )

    except Exception as e:
        logger.exception(f"[ODOO] Erreur configuration schedule: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/config/{config_id}/schedule/pause")
async def pause_schedule(
    config_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Met en pause la planification d'une connexion."""
    service = get_service(request, db)
    config = service.get_config(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    from sqlalchemy import text
    db.execute(text("""
        UPDATE odoo_connection_configs
        SET schedule_paused = true, next_scheduled_run = null
        WHERE id = :config_id
    """), {"config_id": str(config_id)})
    db.commit()

    scheduler_service.pause_odoo_job(config_id)

    return {"message": "Planification mise en pause", "config_id": str(config_id)}


@router.post("/config/{config_id}/schedule/resume")
async def resume_schedule(
    config_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reprend la planification d'une connexion."""
    service = get_service(request, db)
    config = service.get_config(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    # Reactiver le job
    scheduler_service.resume_odoo_job(config_id)
    next_run = scheduler_service.get_next_run_time(config_id)

    from sqlalchemy import text
    db.execute(text("""
        UPDATE odoo_connection_configs
        SET schedule_paused = false, next_scheduled_run = :next_run
        WHERE id = :config_id
    """), {"next_run": next_run, "config_id": str(config_id)})
    db.commit()

    return {
        "message": "Planification reprise",
        "config_id": str(config_id),
        "next_scheduled_run": next_run.isoformat() if next_run else None
    }


@router.get("/config/{config_id}/schedule/next-runs", response_model=OdooNextRunsResponse)
async def get_next_runs(
    config_id: UUID,
    count: int = Query(5, ge=1, le=20, description="Nombre de dates a retourner"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Previsualise les prochaines executions planifiees.

    Utile pour verifier la configuration avant de la sauvegarder.
    """
    service = get_service(request, db)
    config = service.get_config(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    next_runs = scheduler_service.get_next_run_times(
        config_id=config_id,
        count=count,
        mode=config.schedule_mode.value if hasattr(config.schedule_mode, 'value') else config.schedule_mode,
        cron_expression=config.schedule_cron_expression,
        interval_minutes=config.schedule_interval_minutes,
        timezone=config.schedule_timezone,
    )

    return OdooNextRunsResponse(
        config_id=config_id,
        mode=config.schedule_mode.value if hasattr(config.schedule_mode, 'value') else str(config.schedule_mode),
        next_runs=next_runs,
    )


# ============================================================================
# SELECTIVE IMPORT
# ============================================================================

@router.post("/config/{config_id}/import/selective", response_model=List[OdooImportHistoryResponse])
async def selective_import(
    config_id: UUID,
    data: OdooSelectiveImportRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lance un import selectif (types specifiques uniquement).

    Permet de choisir exactement quels types de donnees importer.
    """
    service = get_service(request, db)
    config = service.get_config(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")

    histories = []

    try:
        type_method_map = {
            'products': service.import_products,
            'contacts': service.import_contacts,
            'suppliers': service.import_suppliers,
            'purchase_orders': service.import_purchase_orders,
            'sale_orders': service.import_sale_orders,
            'invoices': service.import_invoices,
            'quotes': service.import_quotes,
            'accounting': service.import_accounting,
            'bank': service.import_bank_statements,
            'interventions': service.import_interventions,
        }

        for sync_type in data.types:
            if sync_type in type_method_map:
                history = type_method_map[sync_type](config_id, full_sync=data.full_sync)
                histories.append(OdooImportHistoryResponse.model_validate(history))

        return histories

    except Exception as e:
        logger.exception(f"[ODOO] Erreur import selectif: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ============================================================================
# ADVANCED HISTORY
# ============================================================================

@router.post("/history/search", response_model=OdooHistorySearchResponse)
async def search_history(
    data: OdooHistorySearchRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recherche avancee dans l'historique des imports.

    Supporte les filtres par config, type, statut, periode, declencheur.
    """
    service = get_service(request, db)

    from .models import OdooImportHistory

    query = db.query(OdooImportHistory).filter(
        OdooImportHistory.tenant_id == service.tenant_id
    )

    # Appliquer les filtres
    if data.config_id:
        query = query.filter(OdooImportHistory.config_id == data.config_id)
    if data.sync_type:
        query = query.filter(OdooImportHistory.sync_type == data.sync_type)
    if data.status:
        query = query.filter(OdooImportHistory.status == data.status)
    if data.trigger_method:
        query = query.filter(OdooImportHistory.trigger_method == data.trigger_method)
    if data.date_from:
        query = query.filter(OdooImportHistory.started_at >= data.date_from)
    if data.date_to:
        query = query.filter(OdooImportHistory.started_at <= data.date_to)

    # Compter le total
    total = query.count()

    # Pagination
    offset = (data.page - 1) * data.page_size
    items = query.order_by(OdooImportHistory.started_at.desc()).offset(offset).limit(data.page_size).all()

    total_pages = (total + data.page_size - 1) // data.page_size

    return OdooHistorySearchResponse(
        items=[OdooImportHistoryResponse.model_validate(h) for h in items],
        total=total,
        page=data.page,
        page_size=data.page_size,
        total_pages=total_pages,
    )


@router.get("/history/{history_id}", response_model=OdooHistoryDetailResponse)
async def get_history_detail(
    history_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere le detail complet d'un historique d'import.

    Inclut la liste complete des erreurs et le resume de l'import.
    """
    service = get_service(request, db)

    from .models import OdooImportHistory, OdooConnectionConfig

    history = db.query(OdooImportHistory).filter(
        OdooImportHistory.id == history_id,
        OdooImportHistory.tenant_id == service.tenant_id,
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="Historique non trouve")

    # Recuperer le nom de la config
    config = db.query(OdooConnectionConfig).filter(
        OdooConnectionConfig.id == history.config_id
    ).first()

    response = OdooHistoryDetailResponse.model_validate(history)
    response.config_name = config.name if config else None
    response.import_summary = history.import_summary

    return response
