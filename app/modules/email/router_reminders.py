"""
AZALS - Module Email - Router Rappels
======================================
Endpoints API pour la gestion des rappels automatiques.
"""

import logging
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.saas_context import SaaSContext, get_saas_context
from app.db import get_db

from .scheduler import InvoiceReminderScheduler, ReminderConfigManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/notifications/reminders", tags=["Reminders"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ReminderConfig(BaseModel):
    """Configuration des rappels automatiques."""
    enabled: bool = True
    auto_send: bool = True
    reminder_days: List[int] = Field(default=[7, 15, 30])
    stop_after_days: int = Field(default=60, ge=1)
    max_reminders: int = Field(default=3, ge=1, le=10)
    email_template: str = "invoice_reminder"
    cc_accounting: bool = False
    escalate_after: int = Field(default=30, ge=0)


class ReminderConfigResponse(ReminderConfig):
    """Réponse de configuration."""
    pass


class InvoiceReminderInfo(BaseModel):
    """Informations sur une facture à rappeler."""
    invoice_id: UUID
    invoice_number: str
    customer_email: Optional[str] = None
    customer_name: str
    amount_due: float
    due_date: date
    days_overdue: int
    reminder_count: int
    reminder_level: str


class ReminderScheduleItem(BaseModel):
    """Item dans le planning des rappels."""
    date: date
    invoice_id: UUID
    invoice_number: str
    customer_name: str
    amount_due: float
    days_after_due: int
    reminder_count: int
    already_sent: bool


class ReminderStats(BaseModel):
    """Statistiques sur les rappels."""
    found: int = 0
    sent: int = 0
    failed: int = 0
    skipped: int = 0


class SendReminderRequest(BaseModel):
    """Requête d'envoi de rappel."""
    invoice_id: UUID
    force: bool = Field(default=False, description="Forcer l'envoi même si déjà envoyé aujourd'hui")


class SendReminderResponse(BaseModel):
    """Réponse d'envoi de rappel."""
    success: bool
    invoice_id: UUID
    message: str


class ScheduleRemindersResponse(BaseModel):
    """Réponse de planification des rappels."""
    stats: ReminderStats
    message: str


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.get("/config", response_model=ReminderConfigResponse)
def get_reminder_config(
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère la configuration des rappels automatiques du tenant.
    
    Retourne les paramètres configurés pour les rappels de factures impayées.
    """
    manager = ReminderConfigManager(db, ctx.tenant_id)
    config = manager.get_config()
    return ReminderConfigResponse(**config)


@router.post("/config", response_model=ReminderConfigResponse)
def update_reminder_config(
    config: ReminderConfig,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour la configuration des rappels automatiques.
    
    - **enabled**: Activer/désactiver les rappels
    - **auto_send**: Envoi automatique quotidien
    - **reminder_days**: Jours après échéance pour envoyer rappels [7, 15, 30]
    - **max_reminders**: Nombre maximum de rappels par facture
    """
    manager = ReminderConfigManager(db, ctx.tenant_id)
    success = manager.update_config(config.model_dump())
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Échec de la mise à jour de la configuration"
        )
    
    return ReminderConfigResponse(**config.model_dump())


# ============================================================================
# RECHERCHE FACTURES
# ============================================================================

@router.get("/invoices", response_model=List[InvoiceReminderInfo])
def list_invoices_needing_reminders(
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les factures nécessitant un rappel aujourd'hui.
    
    Retourne toutes les factures impayées qui atteignent une date de rappel
    configurée (J+7, J+15, J+30, etc.).
    """
    scheduler = InvoiceReminderScheduler(db, ctx.tenant_id)
    invoices = scheduler.find_invoices_needing_reminders()
    
    return [InvoiceReminderInfo(**inv) for inv in invoices]


@router.get("/schedule", response_model=List[ReminderScheduleItem])
def get_reminder_schedule(
    days_ahead: int = Query(default=30, ge=1, le=90, description="Nombre de jours à anticiper"),
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère le planning des rappels à venir.
    
    Affiche tous les rappels prévus dans les N prochains jours.
    """
    scheduler = InvoiceReminderScheduler(db, ctx.tenant_id)
    schedule = scheduler.get_reminder_schedule(days_ahead=days_ahead)
    
    return [ReminderScheduleItem(**item) for item in schedule]


# ============================================================================
# ENVOI RAPPELS
# ============================================================================

@router.post("/send", response_model=SendReminderResponse)
def send_reminder(
    request: SendReminderRequest,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Envoie un rappel pour une facture spécifique.
    
    - **invoice_id**: ID de la facture
    - **force**: Forcer l'envoi même si déjà envoyé aujourd'hui
    """
    scheduler = InvoiceReminderScheduler(db, ctx.tenant_id)
    
    success = scheduler.send_overdue_reminder(
        invoice_id=request.invoice_id,
        force=request.force
    )
    
    if success:
        return SendReminderResponse(
            success=True,
            invoice_id=request.invoice_id,
            message="Rappel envoyé avec succès"
        )
    else:
        return SendReminderResponse(
            success=False,
            invoice_id=request.invoice_id,
            message="Échec de l'envoi du rappel (vérifier logs)"
        )


@router.post("/schedule-all", response_model=ScheduleRemindersResponse)
def schedule_all_reminders(
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Planifie et envoie tous les rappels du jour.
    
    Cette endpoint est normalement appelée quotidiennement par un cron job.
    Peut être appelée manuellement pour forcer l'envoi des rappels.
    """
    scheduler = InvoiceReminderScheduler(db, ctx.tenant_id)
    stats = scheduler.schedule_reminders()
    
    message = f"{stats['sent']} rappels envoyés, {stats['failed']} échoués, {stats['skipped']} ignorés"
    
    return ScheduleRemindersResponse(
        stats=ReminderStats(**stats),
        message=message
    )


# ============================================================================
# TEST
# ============================================================================

@router.post("/test/{invoice_id}", response_model=SendReminderResponse)
def test_reminder(
    invoice_id: UUID,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Envoie un rappel de test pour une facture.
    
    Force l'envoi d'un rappel même si les conditions normales ne sont pas remplies.
    Utile pour tester les templates et la configuration.
    """
    manager = ReminderConfigManager(db, ctx.tenant_id)
    success = manager.test_reminder(invoice_id)
    
    if success:
        return SendReminderResponse(
            success=True,
            invoice_id=invoice_id,
            message="Rappel de test envoyé avec succès"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Échec de l'envoi du rappel de test"
        )
