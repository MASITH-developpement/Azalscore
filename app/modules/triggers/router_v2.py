"""
AZALS MODULE TRIGGERS - Router v2 CORE SaaS
==========================================

Endpoints pour le système de déclencheurs et alertes.
Migration CORE SaaS v2 avec SaaSContext.
"""
from __future__ import annotations


from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.database import get_db

from .models import (
    AlertSeverity,
    EscalationLevel,
    NotificationChannel,
    ReportFrequency,
    TriggerStatus,
    TriggerType,
)
from .schemas import (
    EventListResponseSchema,
    EventResponseSchema,
    NotificationListResponseSchema,
    NotificationResponseSchema,
    ReportHistoryResponseSchema,
    ScheduledReportCreateSchema,
    ScheduledReportResponseSchema,
    ScheduledReportUpdateSchema,
    SubscriptionCreateSchema,
    SubscriptionResponseSchema,
    TemplateCreateSchema,
    TemplateResponseSchema,
    TemplateUpdateSchema,
    TriggerCreateSchema,
    TriggerDashboardSchema,
    TriggerListResponseSchema,
    TriggerLogListResponseSchema,
    TriggerResponseSchema,
    TriggerUpdateSchema,
    WebhookCreateSchema,
    WebhookResponseSchema,
    WebhookTestResponseSchema,
    WebhookUpdateSchema,
)
from .service import TriggerService

router = APIRouter(prefix="/v2/triggers", tags=["Triggers v2 - CORE SaaS"])


# ============================================================================
# FACTORY SERVICE
# ============================================================================

def get_trigger_service(db: Session, tenant_id: str, user_id: str) -> TriggerService:
    """Factory pour créer un service Triggers avec SaaSContext."""
    return TriggerService(db, tenant_id, user_id)


# ============================================================================
# TRIGGERS - Déclencheurs
# ============================================================================

@router.post("/", response_model=TriggerResponseSchema, status_code=201)
async def create_trigger(
    data: TriggerCreateSchema,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau trigger.

    **Permissions requises:** triggers.create
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    try:
        trigger = service.create_trigger(
            code=data.code,
            name=data.name,
            trigger_type=data.trigger_type,
            source_module=data.source_module,
            condition=data.condition,
            created_by=UUID(context.user_id) if context.user_id else None,
            description=data.description,
            source_entity=data.source_entity,
            source_field=data.source_field,
            threshold_value=data.threshold_value,
            threshold_operator=data.threshold_operator,
            schedule_cron=data.schedule_cron,
            severity=data.severity or AlertSeverity.WARNING,
            escalation_enabled=data.escalation_enabled or False,
            escalation_delay_minutes=data.escalation_delay_minutes or 60,
            cooldown_minutes=data.cooldown_minutes or 60,
            action_template_id=UUID(data.action_template_id) if data.action_template_id else None
        )
        return trigger
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=TriggerListResponseSchema)
async def list_triggers(
    source_module: str | None = Query(None, description="Filtrer par module source"),
    trigger_type: TriggerType | None = Query(None, description="Filtrer par type"),
    include_inactive: bool = Query(False, description="Inclure inactifs"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les triggers.

    **Permissions requises:** triggers.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)
    triggers = service.list_triggers(
        source_module=source_module,
        trigger_type=trigger_type,
        include_inactive=include_inactive
    )

    return {
        "triggers": triggers,
        "total": len(triggers)
    }


@router.get("/{trigger_id}", response_model=TriggerResponseSchema)
async def get_trigger(
    trigger_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère un trigger par ID.

    **Permissions requises:** triggers.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)
    trigger = service.get_trigger(int(trigger_id))

    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger non trouvé")

    return trigger


@router.put("/{trigger_id}", response_model=TriggerResponseSchema)
async def update_trigger(
    trigger_id: UUID,
    data: TriggerUpdateSchema,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour un trigger.

    **Permissions requises:** triggers.update
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    try:
        # Préparer les données à mettre à jour
        update_data = data.model_dump(exclude_unset=True)

        # Convertir action_template_id en UUID si présent
        if 'action_template_id' in update_data and update_data['action_template_id']:
            update_data['action_template_id'] = UUID(update_data['action_template_id'])

        trigger = service.update_trigger(int(trigger_id), **update_data)
        return trigger
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{trigger_id}", status_code=204)
async def delete_trigger(
    trigger_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Supprime un trigger.

    **Permissions requises:** triggers.delete
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    success = service.delete_trigger(
        int(trigger_id),
        deleted_by=UUID(context.user_id) if context.user_id else None
    )

    if not success:
        raise HTTPException(status_code=404, detail="Trigger non trouvé")

    return None


@router.post("/{trigger_id}/pause", response_model=TriggerResponseSchema)
async def pause_trigger(
    trigger_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met en pause un trigger.

    **Permissions requises:** triggers.update
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    try:
        trigger = service.pause_trigger(int(trigger_id))
        return trigger
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{trigger_id}/resume", response_model=TriggerResponseSchema)
async def resume_trigger(
    trigger_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Reprend un trigger en pause.

    **Permissions requises:** triggers.update
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    try:
        trigger = service.resume_trigger(int(trigger_id))
        return trigger
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{trigger_id}/fire", response_model=EventResponseSchema)
async def fire_trigger(
    trigger_id: UUID,
    data: dict[str, Any] | None = None,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Déclenche manuellement un trigger.

    **Permissions requises:** triggers.execute
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    trigger = service.get_trigger(int(trigger_id))
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger non trouvé")

    # Évaluer et déclencher
    should_fire = service.evaluate_trigger(trigger, data or {})

    if should_fire:
        event = service.fire_trigger(
            trigger,
            triggered_value=data.get('value') if data else None,
            condition_details=data
        )
        return event
    else:
        raise HTTPException(status_code=400, detail="Condition non remplie")


# ============================================================================
# SUBSCRIPTIONS - Abonnements
# ============================================================================

@router.post("/subscriptions", response_model=SubscriptionResponseSchema, status_code=201)
async def create_subscription(
    data: SubscriptionCreateSchema,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Abonne un utilisateur ou rôle à un trigger.

    **Permissions requises:** triggers.subscribe
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    try:
        if data.user_id:
            subscription = service.subscribe_user(
                trigger_id=int(data.trigger_id),
                user_id=int(data.user_id),
                channel=data.channel or NotificationChannel.IN_APP,
                escalation_level=data.escalation_level or EscalationLevel.L1,
                created_by=UUID(context.user_id) if context.user_id else None
            )
        elif data.role_code:
            subscription = service.subscribe_role(
                trigger_id=int(data.trigger_id),
                role_code=data.role_code,
                channel=data.channel or NotificationChannel.IN_APP,
                escalation_level=data.escalation_level or EscalationLevel.L1,
                created_by=UUID(context.user_id) if context.user_id else None
            )
        else:
            raise HTTPException(status_code=400, detail="user_id ou role_code requis")

        return subscription
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions/{trigger_id}", response_model=list[SubscriptionResponseSchema])
async def list_trigger_subscriptions(
    trigger_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les abonnements d'un trigger.

    **Permissions requises:** triggers.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)
    subscriptions = service.get_trigger_subscriptions(int(trigger_id))

    return subscriptions


@router.delete("/subscriptions/{subscription_id}", status_code=204)
async def delete_subscription(
    subscription_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Supprime un abonnement.

    **Permissions requises:** triggers.subscribe
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    success = service.unsubscribe(int(subscription_id))

    if not success:
        raise HTTPException(status_code=404, detail="Abonnement non trouvé")

    return None


# ============================================================================
# EVENTS - Événements
# ============================================================================

@router.get("/events", response_model=EventListResponseSchema)
async def list_events(
    trigger_id: UUID | None = Query(None, description="Filtrer par trigger"),
    resolved: bool | None = Query(None, description="Filtrer par statut résolu"),
    severity: AlertSeverity | None = Query(None, description="Filtrer par sévérité"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les événements de déclenchement.

    **Permissions requises:** triggers.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    events = service.list_events(
        trigger_id=int(trigger_id) if trigger_id else None,
        resolved=resolved,
        severity=severity,
        limit=limit
    )

    return {
        "events": events,
        "total": len(events)
    }


@router.get("/events/{event_id}", response_model=EventResponseSchema)
async def get_event(
    event_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère un événement par ID.

    **Permissions requises:** triggers.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)
    event = service.get_event(int(event_id))

    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    return event


@router.post("/events/{event_id}/resolve", response_model=EventResponseSchema)
async def resolve_event(
    event_id: UUID,
    resolution_notes: str | None = None,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Marque un événement comme résolu.

    **Permissions requises:** triggers.resolve
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    try:
        event = service.resolve_event(
            int(event_id),
            resolved_by=int(context.user_id) if context.user_id else 0,
            resolution_notes=resolution_notes
        )
        return event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/events/{event_id}/escalate", response_model=EventResponseSchema)
async def escalate_event(
    event_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Escalade un événement au niveau supérieur.

    **Permissions requises:** triggers.escalate
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    try:
        event = service.escalate_event(int(event_id))
        return event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# NOTIFICATIONS
# ============================================================================

@router.get("/notifications", response_model=NotificationListResponseSchema)
async def list_user_notifications(
    unread_only: bool = Query(False, description="Seulement non lues"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les notifications de l'utilisateur courant.

    **Permissions requises:** triggers.notifications.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    if not context.user_id:
        raise HTTPException(status_code=401, detail="Utilisateur non authentifié")

    notifications = service.get_user_notifications(
        user_id=int(context.user_id),
        unread_only=unread_only,
        limit=limit
    )

    unread_count = len([n for n in notifications if not n.read_at])

    return {
        "notifications": notifications,
        "total": len(notifications),
        "unread_count": unread_count
    }


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponseSchema)
async def mark_notification_read(
    notification_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Marque une notification comme lue.

    **Permissions requises:** triggers.notifications.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    notification = service.mark_notification_read(int(notification_id))

    if not notification:
        raise HTTPException(status_code=404, detail="Notification non trouvée")

    return notification


@router.post("/notifications/read-all", status_code=204)
async def mark_all_read(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Marque toutes les notifications comme lues.

    **Permissions requises:** triggers.notifications.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    if not context.user_id:
        raise HTTPException(status_code=401, detail="Utilisateur non authentifié")

    notifications = service.get_user_notifications(
        user_id=int(context.user_id),
        unread_only=True,
        limit=500
    )

    for notification in notifications:
        service.mark_notification_read(int(notification.id))

    return None


@router.post("/notifications/send-pending")
async def send_pending_notifications(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Envoie les notifications en attente.

    **Permissions requises:** triggers.notifications.send
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    count = service.send_pending_notifications()

    return {
        "sent_count": count,
        "message": f"{count} notification(s) envoyée(s)"
    }


# ============================================================================
# TEMPLATES
# ============================================================================

@router.post("/templates", response_model=TemplateResponseSchema, status_code=201)
async def create_template(
    data: TemplateCreateSchema,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Crée un template de notification.

    **Permissions requises:** triggers.templates.create
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    template = service.create_template(
        code=data.code,
        name=data.name,
        body_template=data.body_template,
        created_by=UUID(context.user_id) if context.user_id else None,
        description=data.description,
        subject_template=data.subject_template,
        body_html=data.body_html,
        available_variables=data.available_variables
    )

    return template


@router.get("/templates", response_model=list[TemplateResponseSchema])
async def list_templates(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les templates de notification.

    **Permissions requises:** triggers.templates.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)
    templates = service.list_templates()

    return templates


@router.get("/templates/{template_id}", response_model=TemplateResponseSchema)
async def get_template(
    template_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère un template par ID.

    **Permissions requises:** triggers.templates.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    template = db.query(service.db.query(service.db.models.NotificationTemplate).filter(
        service.db.models.NotificationTemplate.id == template_id,
        service.db.models.NotificationTemplate.tenant_id == context.tenant_id
    ).first())

    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")

    return template


@router.put("/templates/{template_id}", response_model=TemplateResponseSchema)
async def update_template(
    template_id: UUID,
    data: TemplateUpdateSchema,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour un template.

    **Permissions requises:** triggers.templates.update
    """
    from .models import NotificationTemplate

    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id,
        NotificationTemplate.tenant_id == context.tenant_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")

    # Mettre à jour les champs
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)

    db.commit()
    db.refresh(template)

    return template


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Supprime un template.

    **Permissions requises:** triggers.templates.delete
    """
    from .models import NotificationTemplate

    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id,
        NotificationTemplate.tenant_id == context.tenant_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")

    db.delete(template)
    db.commit()

    return None


# ============================================================================
# SCHEDULED REPORTS
# ============================================================================

@router.post("/reports", response_model=ScheduledReportResponseSchema, status_code=201)
async def create_scheduled_report(
    data: ScheduledReportCreateSchema,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Crée un rapport planifié.

    **Permissions requises:** triggers.reports.create
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    report = service.create_scheduled_report(
        code=data.code,
        name=data.name,
        report_type=data.report_type,
        frequency=data.frequency,
        recipients=data.recipients,
        created_by=UUID(context.user_id) if context.user_id else None,
        description=data.description,
        report_config=data.report_config,
        schedule_day=data.schedule_day,
        schedule_time=data.schedule_time,
        output_format=data.output_format or 'PDF'
    )

    return report


@router.get("/reports", response_model=list[ScheduledReportResponseSchema])
async def list_scheduled_reports(
    include_inactive: bool = Query(False, description="Inclure inactifs"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les rapports planifiés.

    **Permissions requises:** triggers.reports.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)
    reports = service.list_scheduled_reports(include_inactive=include_inactive)

    return reports


@router.get("/reports/{report_id}", response_model=ScheduledReportResponseSchema)
async def get_scheduled_report(
    report_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère un rapport planifié par ID.

    **Permissions requises:** triggers.reports.read
    """
    from .models import ScheduledReport

    report = db.query(ScheduledReport).filter(
        ScheduledReport.id == report_id,
        ScheduledReport.tenant_id == context.tenant_id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")

    return report


@router.put("/reports/{report_id}", response_model=ScheduledReportResponseSchema)
async def update_scheduled_report(
    report_id: UUID,
    data: ScheduledReportUpdateSchema,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour un rapport planifié.

    **Permissions requises:** triggers.reports.update
    """
    from .models import ScheduledReport

    report = db.query(ScheduledReport).filter(
        ScheduledReport.id == report_id,
        ScheduledReport.tenant_id == context.tenant_id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")

    # Mettre à jour les champs
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(report, key, value)

    db.commit()
    db.refresh(report)

    return report


@router.delete("/reports/{report_id}", status_code=204)
async def delete_scheduled_report(
    report_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Supprime un rapport planifié.

    **Permissions requises:** triggers.reports.delete
    """
    from .models import ScheduledReport

    report = db.query(ScheduledReport).filter(
        ScheduledReport.id == report_id,
        ScheduledReport.tenant_id == context.tenant_id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")

    db.delete(report)
    db.commit()

    return None


@router.post("/reports/{report_id}/generate", response_model=ReportHistoryResponseSchema)
async def generate_report(
    report_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Génère un rapport manuellement.

    **Permissions requises:** triggers.reports.generate
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    try:
        history = service.generate_report(
            int(report_id),
            generated_by=UUID(context.user_id) if context.user_id else None
        )
        return history
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reports/{report_id}/history", response_model=list[ReportHistoryResponseSchema])
async def get_report_history(
    report_id: UUID,
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique d'un rapport.

    **Permissions requises:** triggers.reports.read
    """
    from .models import ReportHistory

    history = db.query(ReportHistory).filter(
        ReportHistory.report_id == report_id,
        ReportHistory.tenant_id == context.tenant_id
    ).order_by(ReportHistory.generated_at.desc()).limit(limit).all()

    return history


# ============================================================================
# WEBHOOKS
# ============================================================================

@router.post("/webhooks", response_model=WebhookResponseSchema, status_code=201)
async def create_webhook(
    data: WebhookCreateSchema,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Crée un endpoint webhook.

    **Permissions requises:** triggers.webhooks.create
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)

    webhook = service.create_webhook(
        code=data.code,
        name=data.name,
        url=data.url,
        created_by=UUID(context.user_id) if context.user_id else None,
        description=data.description,
        method=data.method or 'POST',
        headers=data.headers,
        auth_type=data.auth_type,
        auth_config=data.auth_config
    )

    return webhook


@router.get("/webhooks", response_model=list[WebhookResponseSchema])
async def list_webhooks(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les webhooks.

    **Permissions requises:** triggers.webhooks.read
    """
    service = get_trigger_service(db, context.tenant_id, context.user_id)
    webhooks = service.list_webhooks()

    return webhooks


@router.get("/webhooks/{webhook_id}", response_model=WebhookResponseSchema)
async def get_webhook(
    webhook_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère un webhook par ID.

    **Permissions requises:** triggers.webhooks.read
    """
    from .models import WebhookEndpoint

    webhook = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == context.tenant_id
    ).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook non trouvé")

    return webhook


@router.put("/webhooks/{webhook_id}", response_model=WebhookResponseSchema)
async def update_webhook(
    webhook_id: UUID,
    data: WebhookUpdateSchema,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour un webhook.

    **Permissions requises:** triggers.webhooks.update
    """
    from .models import WebhookEndpoint

    webhook = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == context.tenant_id
    ).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook non trouvé")

    # Mettre à jour les champs
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(webhook, key, value)

    db.commit()
    db.refresh(webhook)

    return webhook


@router.delete("/webhooks/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Supprime un webhook.

    **Permissions requises:** triggers.webhooks.delete
    """
    from .models import WebhookEndpoint

    webhook = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == context.tenant_id
    ).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook non trouvé")

    db.delete(webhook)
    db.commit()

    return None


@router.post("/webhooks/{webhook_id}/test", response_model=WebhookTestResponseSchema)
async def test_webhook(
    webhook_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Teste un webhook avec des données fictives.

    **Permissions requises:** triggers.webhooks.test
    """
    from .models import WebhookEndpoint

    webhook = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == context.tenant_id
    ).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook non trouvé")

    # NOTE: Phase 2 - Test réel via httpx async
    return {
        "success": True,
        "status_code": 200,
        "response_time_ms": 150,
        "message": "Test webhook OK (simulated)"
    }


# ============================================================================
# MONITORING & DASHBOARD
# ============================================================================

@router.get("/logs", response_model=TriggerLogListResponseSchema)
async def list_logs(
    action: str | None = Query(None, description="Filtrer par action"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les logs du système de triggers.

    **Permissions requises:** triggers.logs.read
    """
    from .models import TriggerLog

    query = db.query(TriggerLog).filter(
        TriggerLog.tenant_id == context.tenant_id
    )

    if action:
        query = query.filter(TriggerLog.action == action)

    logs = query.order_by(TriggerLog.created_at.desc()).limit(limit).all()

    return {
        "logs": logs,
        "total": len(logs)
    }


@router.get("/dashboard", response_model=TriggerDashboardSchema)
async def get_dashboard(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Dashboard récapitulatif du système de triggers.

    **Permissions requises:** triggers.read
    """
    from .models import Notification, Trigger, TriggerEvent

    # Statistiques
    total_triggers = db.query(Trigger).filter(
        Trigger.tenant_id == context.tenant_id
    ).count()

    active_triggers = db.query(Trigger).filter(
        Trigger.tenant_id == context.tenant_id,
        Trigger.status == TriggerStatus.ACTIVE
    ).count()

    total_events = db.query(TriggerEvent).filter(
        TriggerEvent.tenant_id == context.tenant_id
    ).count()

    unresolved_events = db.query(TriggerEvent).filter(
        TriggerEvent.tenant_id == context.tenant_id,
        TriggerEvent.resolved == False
    ).count()

    pending_notifications = db.query(Notification).filter(
        Notification.tenant_id == context.tenant_id,
        Notification.status == 'PENDING'
    ).count()

    # Top triggers
    top_triggers = db.query(Trigger).filter(
        Trigger.tenant_id == context.tenant_id
    ).order_by(Trigger.trigger_count.desc()).limit(5).all()

    return {
        "total_triggers": total_triggers,
        "active_triggers": active_triggers,
        "paused_triggers": total_triggers - active_triggers,
        "total_events": total_events,
        "unresolved_events": unresolved_events,
        "pending_notifications": pending_notifications,
        "top_triggers": [
            {
                "id": str(t.id),
                "code": t.code,
                "name": t.name,
                "trigger_count": t.trigger_count,
                "severity": t.severity.value
            }
            for t in top_triggers
        ]
    }
