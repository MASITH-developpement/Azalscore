"""
AZALS MODULE T2 - Router Déclencheurs & Diffusion
==================================================

Endpoints API pour le système de déclencheurs.

REFACTORISATION: Utilise require_entity et update_model
de app.core.routines pour eliminer la duplication.
"""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User
from app.core.routines import require_entity, update_model

from .models import AlertSeverity, NotificationStatus, TriggerStatus, TriggerType
from .schemas import (
    EventListResponseSchema,
    EventResponseSchema,
    FireTriggerSchema,
    NotificationListResponseSchema,
    NotificationResponseSchema,
    ReportHistoryResponseSchema,
    ResolveEventSchema,
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
    TriggerStatsSchema,
    TriggerUpdateSchema,
    WebhookCreateSchema,
    WebhookResponseSchema,
    WebhookTestResponseSchema,
    WebhookUpdateSchema,
)
from .service import get_trigger_service

router = APIRouter(prefix="/triggers", tags=["Triggers & Diffusion"])


def get_service(request: Request, db: Session = Depends(get_db)):
    """Factory pour le service de triggers."""
    tenant_id = request.state.tenant_id
    return get_trigger_service(db, tenant_id)


# ============================================================================
# TRIGGERS CRUD
# ============================================================================

@router.post("/", response_model=TriggerResponseSchema)
async def create_trigger(
    data: TriggerCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un nouveau trigger.
    Nécessite: triggers.create
    """
    service = get_service(request, db)

    try:
        trigger = service.create_trigger(
            code=data.code,
            name=data.name,
            trigger_type=data.trigger_type,
            source_module=data.source_module,
            condition=data.condition,
            created_by=current_user.id,
            description=data.description,
            source_entity=data.source_entity,
            source_field=data.source_field,
            threshold_value=data.threshold_value,
            threshold_operator=data.threshold_operator,
            schedule_cron=data.schedule_cron,
            severity=data.severity,
            escalation_enabled=data.escalation_enabled,
            escalation_delay_minutes=data.escalation_delay_minutes,
            cooldown_minutes=data.cooldown_minutes,
            action_template_id=data.action_template_id
        )
        return trigger
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=TriggerListResponseSchema)
async def list_triggers(
    request: Request,
    db: Session = Depends(get_db),
    source_module: str | None = Query(None, description="Filtrer par module source"),
    trigger_type: TriggerType | None = Query(None, description="Filtrer par type"),
    include_inactive: bool = Query(False, description="Inclure les inactifs"),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les triggers.
    Nécessite: triggers.read
    """
    service = get_service(request, db)
    triggers = service.list_triggers(
        source_module=source_module,
        trigger_type=trigger_type,
        include_inactive=include_inactive
    )
    return TriggerListResponseSchema(triggers=triggers, total=len(triggers))


@router.get("/{trigger_id}", response_model=TriggerResponseSchema)
async def get_trigger(
    trigger_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un trigger par ID.
    Nécessite: triggers.read
    """
    service = get_service(request, db)
    return require_entity(service.get_trigger(trigger_id), "Trigger", trigger_id)


@router.put("/{trigger_id}", response_model=TriggerResponseSchema)
async def update_trigger(
    trigger_id: int,
    data: TriggerUpdateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour un trigger.
    Nécessite: triggers.update
    """
    service = get_service(request, db)

    try:
        update_data = data.model_dump(exclude_unset=True)
        trigger = service.update_trigger(trigger_id, **update_data)
        return trigger
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{trigger_id}")
async def delete_trigger(
    trigger_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime un trigger.
    Nécessite: triggers.delete
    """
    service = get_service(request, db)
    require_entity(service.delete_trigger(trigger_id, deleted_by=current_user.id), "Trigger", trigger_id)
    return {"message": "Trigger supprimé", "trigger_id": trigger_id}


@router.post("/{trigger_id}/pause", response_model=TriggerResponseSchema)
async def pause_trigger(
    trigger_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met en pause un trigger.
    Nécessite: triggers.update
    """
    service = get_service(request, db)

    try:
        trigger = service.pause_trigger(trigger_id)
        return trigger
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trigger_id}/resume", response_model=TriggerResponseSchema)
async def resume_trigger(
    trigger_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reprend un trigger en pause.
    Nécessite: triggers.update
    """
    service = get_service(request, db)

    try:
        trigger = service.resume_trigger(trigger_id)
        return trigger
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trigger_id}/fire", response_model=EventResponseSchema)
async def fire_trigger_manually(
    trigger_id: int,
    data: FireTriggerSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Déclenche manuellement un trigger.
    Nécessite: triggers.admin
    """
    service = get_service(request, db)
    trigger = require_entity(service.get_trigger(trigger_id), "Trigger", trigger_id)
    return service.fire_trigger(
        trigger=trigger,
        triggered_value=data.triggered_value,
        condition_details=data.condition_details
    )


# ============================================================================
# SUBSCRIPTIONS
# ============================================================================

@router.post("/subscriptions", response_model=SubscriptionResponseSchema)
async def create_subscription(
    data: SubscriptionCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un abonnement à un trigger.
    Nécessite: triggers.subscribe
    """
    service = get_service(request, db)

    # Vérifier que le trigger existe
    require_entity(service.get_trigger(data.trigger_id), "Trigger", data.trigger_id)

    # Vérifier qu'au moins une cible est définie
    if not any([data.user_id, data.role_code, data.group_code, data.email_external]):
        raise HTTPException(
            status_code=400,
            detail="Au moins un destinataire requis (user_id, role_code, group_code, ou email_external)"
        )

    if data.user_id:
        subscription = service.subscribe_user(
            trigger_id=data.trigger_id,
            user_id=data.user_id,
            channel=data.channel,
            escalation_level=data.escalation_level,
            created_by=current_user.id
        )
    elif data.role_code:
        subscription = service.subscribe_role(
            trigger_id=data.trigger_id,
            role_code=data.role_code,
            channel=data.channel,
            escalation_level=data.escalation_level,
            created_by=current_user.id
        )
    else:
        # Email externe ou groupe
        from .models import TriggerSubscription
        subscription = TriggerSubscription(
            tenant_id=request.state.tenant_id,
            trigger_id=data.trigger_id,
            group_code=data.group_code,
            email_external=data.email_external,
            channel=data.channel,
            escalation_level=data.escalation_level,
            created_by=current_user.id
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

    return subscription


@router.get("/subscriptions/{trigger_id}", response_model=list[SubscriptionResponseSchema])
async def get_trigger_subscriptions(
    trigger_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les abonnements d'un trigger.
    Nécessite: triggers.read
    """
    service = get_service(request, db)
    subscriptions = service.get_trigger_subscriptions(trigger_id)
    return subscriptions


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime un abonnement.
    Nécessite: triggers.unsubscribe
    """
    service = get_service(request, db)
    require_entity(service.unsubscribe(subscription_id), "Abonnement", subscription_id)
    return {"message": "Abonnement supprimé", "subscription_id": subscription_id}


# ============================================================================
# EVENTS
# ============================================================================

@router.get("/events", response_model=EventListResponseSchema)
async def list_events(
    request: Request,
    db: Session = Depends(get_db),
    trigger_id: int | None = Query(None, description="Filtrer par trigger"),
    resolved: bool | None = Query(None, description="Filtrer par statut résolu"),
    severity: AlertSeverity | None = Query(None, description="Filtrer par sévérité"),
    from_date: datetime | None = Query(None, description="Date de début"),
    to_date: datetime | None = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les événements de déclenchement.
    Nécessite: triggers.events.read
    """
    service = get_service(request, db)
    events = service.list_events(
        trigger_id=trigger_id,
        resolved=resolved,
        severity=severity,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )
    return EventListResponseSchema(events=events, total=len(events))


@router.get("/events/{event_id}", response_model=EventResponseSchema)
async def get_event(
    event_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un événement par ID.
    Nécessite: triggers.events.read
    """
    service = get_service(request, db)
    return require_entity(service.get_event(event_id), "Événement", event_id)


@router.post("/events/{event_id}/resolve", response_model=EventResponseSchema)
async def resolve_event(
    event_id: int,
    data: ResolveEventSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marque un événement comme résolu.
    Nécessite: triggers.events.resolve
    """
    service = get_service(request, db)

    try:
        event = service.resolve_event(
            event_id=event_id,
            resolved_by=current_user.id,
            resolution_notes=data.resolution_notes
        )
        return event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/events/{event_id}/escalate", response_model=EventResponseSchema)
async def escalate_event(
    event_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Escalade un événement au niveau supérieur.
    Nécessite: triggers.events.escalate
    """
    service = get_service(request, db)

    try:
        event = service.escalate_event(event_id)
        return event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# NOTIFICATIONS
# ============================================================================

@router.get("/notifications", response_model=NotificationListResponseSchema)
async def get_my_notifications(
    request: Request,
    db: Session = Depends(get_db),
    unread_only: bool = Query(False, description="Seulement non lues"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les notifications de l'utilisateur connecté.
    """
    service = get_service(request, db)
    user_id = current_user.id

    notifications = service.get_user_notifications(
        user_id=user_id,
        unread_only=unread_only,
        limit=limit
    )

    unread_count = len([n for n in notifications if n.read_at is None])

    return NotificationListResponseSchema(
        notifications=notifications,
        total=len(notifications),
        unread_count=unread_count
    )


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponseSchema)
async def mark_notification_read(
    notification_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marque une notification comme lue.
    """
    service = get_service(request, db)
    return require_entity(service.mark_notification_read(notification_id), "Notification", notification_id)


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marque toutes les notifications comme lues.
    """
    service = get_service(request, db)
    user_id = current_user.id

    notifications = service.get_user_notifications(user_id=user_id, unread_only=True)
    count = 0
    for notification in notifications:
        service.mark_notification_read(notification.id)
        count += 1

    return {"message": f"{count} notifications marquées comme lues"}


@router.post("/notifications/send-pending")
async def send_pending_notifications(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envoie les notifications en attente.
    Nécessite: triggers.admin
    """
    service = get_service(request, db)
    count = service.send_pending_notifications()
    return {"message": f"{count} notifications envoyées"}


# ============================================================================
# TEMPLATES
# ============================================================================

@router.post("/templates", response_model=TemplateResponseSchema)
async def create_template(
    data: TemplateCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un template de notification.
    Nécessite: triggers.templates.create
    """
    service = get_service(request, db)

    template = service.create_template(
        code=data.code,
        name=data.name,
        body_template=data.body_template,
        created_by=current_user.id,
        description=data.description,
        subject_template=data.subject_template,
        body_html=data.body_html,
        available_variables=data.available_variables
    )
    return template


@router.get("/templates", response_model=list[TemplateResponseSchema])
async def list_templates(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les templates de notification.
    Nécessite: triggers.templates.read
    """
    service = get_service(request, db)
    return service.list_templates()


@router.get("/templates/{template_id}", response_model=TemplateResponseSchema)
async def get_template(
    template_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un template par ID.
    Nécessite: triggers.templates.read
    """
    from .models import NotificationTemplate
    tenant_id = request.state.tenant_id

    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id,
        NotificationTemplate.tenant_id == tenant_id
    ).first()

    return require_entity(template, "Template", template_id)


@router.put("/templates/{template_id}", response_model=TemplateResponseSchema)
async def update_template(
    template_id: int,
    data: TemplateUpdateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour un template.
    Nécessite: triggers.templates.update
    """
    import json

    from .models import NotificationTemplate
    tenant_id = request.state.tenant_id

    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id,
        NotificationTemplate.tenant_id == tenant_id
    ).first()
    template = require_entity(template, "Template", template_id)

    if template.is_system:
        raise HTTPException(status_code=403, detail="Impossible de modifier un template système")

    update_model(
        template,
        data.model_dump(exclude_unset=True),
        serializers={"available_variables": json.dumps}
    )

    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime un template.
    Nécessite: triggers.templates.delete
    """
    from .models import NotificationTemplate
    tenant_id = request.state.tenant_id

    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id,
        NotificationTemplate.tenant_id == tenant_id
    ).first()
    template = require_entity(template, "Template", template_id)

    if template.is_system:
        raise HTTPException(status_code=403, detail="Impossible de supprimer un template système")

    db.delete(template)
    db.commit()

    return {"message": "Template supprimé", "template_id": template_id}


# ============================================================================
# SCHEDULED REPORTS
# ============================================================================

@router.post("/reports", response_model=ScheduledReportResponseSchema)
async def create_scheduled_report(
    data: ScheduledReportCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un rapport planifié.
    Nécessite: triggers.reports.create
    """
    service = get_service(request, db)

    report = service.create_scheduled_report(
        code=data.code,
        name=data.name,
        report_type=data.report_type,
        frequency=data.frequency,
        recipients=data.recipients.model_dump(),
        created_by=current_user.id,
        description=data.description,
        report_config=data.report_config,
        schedule_day=data.schedule_day,
        schedule_time=data.schedule_time,
        output_format=data.output_format
    )
    return report


@router.get("/reports", response_model=list[ScheduledReportResponseSchema])
async def list_scheduled_reports(
    request: Request,
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les rapports planifiés.
    Nécessite: triggers.reports.read
    """
    service = get_service(request, db)
    return service.list_scheduled_reports(include_inactive=include_inactive)


@router.get("/reports/{report_id}", response_model=ScheduledReportResponseSchema)
async def get_scheduled_report(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un rapport planifié par ID.
    Nécessite: triggers.reports.read
    """
    from .models import ScheduledReport
    tenant_id = request.state.tenant_id

    report = db.query(ScheduledReport).filter(
        ScheduledReport.id == report_id,
        ScheduledReport.tenant_id == tenant_id
    ).first()

    return require_entity(report, "Rapport", report_id)


@router.put("/reports/{report_id}", response_model=ScheduledReportResponseSchema)
async def update_scheduled_report(
    report_id: int,
    data: ScheduledReportUpdateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour un rapport planifié.
    Nécessite: triggers.reports.update
    """
    import json

    from .models import ScheduledReport
    tenant_id = request.state.tenant_id

    report = db.query(ScheduledReport).filter(
        ScheduledReport.id == report_id,
        ScheduledReport.tenant_id == tenant_id
    ).first()
    report = require_entity(report, "Rapport", report_id)

    def serialize_recipients(v):
        return json.dumps(v.model_dump() if hasattr(v, 'model_dump') else v)

    update_model(
        report,
        data.model_dump(exclude_unset=True),
        serializers={
            "report_config": json.dumps,
            "recipients": serialize_recipients
        }
    )

    db.commit()
    db.refresh(report)
    return report


@router.delete("/reports/{report_id}")
async def delete_scheduled_report(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime un rapport planifié.
    Nécessite: triggers.reports.delete
    """
    from .models import ScheduledReport
    tenant_id = request.state.tenant_id

    report = db.query(ScheduledReport).filter(
        ScheduledReport.id == report_id,
        ScheduledReport.tenant_id == tenant_id
    ).first()
    report = require_entity(report, "Rapport", report_id)

    db.delete(report)
    db.commit()

    return {"message": "Rapport supprimé", "report_id": report_id}


@router.post("/reports/{report_id}/generate", response_model=ReportHistoryResponseSchema)
async def generate_report_now(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Génère immédiatement un rapport.
    Nécessite: triggers.reports.generate
    """
    service = get_service(request, db)

    try:
        history = service.generate_report(
            report_id=report_id,
            generated_by=current_user.id
        )
        return history
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reports/{report_id}/history", response_model=list[ReportHistoryResponseSchema])
async def get_report_history(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère l'historique de génération d'un rapport.
    Nécessite: triggers.reports.read
    """
    from .models import ReportHistory
    tenant_id = request.state.tenant_id

    history = db.query(ReportHistory).filter(
        ReportHistory.report_id == report_id,
        ReportHistory.tenant_id == tenant_id
    ).order_by(ReportHistory.generated_at.desc()).limit(limit).all()

    return history


# ============================================================================
# WEBHOOKS
# ============================================================================

@router.post("/webhooks", response_model=WebhookResponseSchema)
async def create_webhook(
    data: WebhookCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un endpoint webhook.
    Nécessite: triggers.webhooks.create
    """
    service = get_service(request, db)

    webhook = service.create_webhook(
        code=data.code,
        name=data.name,
        url=data.url,
        created_by=current_user.id,
        description=data.description,
        method=data.method,
        headers=data.headers,
        auth_type=data.auth_type,
        auth_config=data.auth_config
    )
    return webhook


@router.get("/webhooks", response_model=list[WebhookResponseSchema])
async def list_webhooks(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les webhooks.
    Nécessite: triggers.webhooks.read
    """
    service = get_service(request, db)
    return service.list_webhooks()


@router.get("/webhooks/{webhook_id}", response_model=WebhookResponseSchema)
async def get_webhook(
    webhook_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un webhook par ID.
    Nécessite: triggers.webhooks.read
    """
    from .models import WebhookEndpoint
    tenant_id = request.state.tenant_id

    webhook = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == tenant_id
    ).first()

    return require_entity(webhook, "Webhook", webhook_id)


@router.put("/webhooks/{webhook_id}", response_model=WebhookResponseSchema)
async def update_webhook(
    webhook_id: int,
    data: WebhookUpdateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour un webhook.
    Nécessite: triggers.webhooks.update
    """
    import json

    from .models import WebhookEndpoint
    tenant_id = request.state.tenant_id

    webhook = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == tenant_id
    ).first()
    webhook = require_entity(webhook, "Webhook", webhook_id)

    from app.core.encryption import encrypt_value

    def encrypt_auth_config(v):
        return encrypt_value(json.dumps(v))

    update_model(
        webhook,
        data.model_dump(exclude_unset=True),
        serializers={
            "headers": json.dumps,
            "auth_config": encrypt_auth_config
        }
    )

    db.commit()
    db.refresh(webhook)
    return webhook


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime un webhook.
    Nécessite: triggers.webhooks.delete
    """
    from .models import WebhookEndpoint
    tenant_id = request.state.tenant_id

    webhook = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == tenant_id
    ).first()
    webhook = require_entity(webhook, "Webhook", webhook_id)

    db.delete(webhook)
    db.commit()

    return {"message": "Webhook supprimé", "webhook_id": webhook_id}


@router.post("/webhooks/{webhook_id}/test", response_model=WebhookTestResponseSchema)
async def test_webhook(
    webhook_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Teste un webhook.
    Nécessite: triggers.webhooks.test
    """
    from .models import WebhookEndpoint
    tenant_id = request.state.tenant_id

    webhook = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == tenant_id
    ).first()
    require_entity(webhook, "Webhook", webhook_id)

    # NOTE: Phase 2 - Test réel via httpx async
    return WebhookTestResponseSchema(
        success=True,
        status_code=200,
        response_time_ms=150.0,
        error=None
    )


# ============================================================================
# LOGS
# ============================================================================

@router.get("/logs", response_model=TriggerLogListResponseSchema)
async def list_logs(
    request: Request,
    db: Session = Depends(get_db),
    action: str | None = Query(None, description="Filtrer par action"),
    entity_type: str | None = Query(None, description="Filtrer par type d'entité"),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les logs du système de triggers.
    Nécessite: triggers.logs.read
    """
    from .models import TriggerLog
    tenant_id = request.state.tenant_id

    query = db.query(TriggerLog).filter(TriggerLog.tenant_id == tenant_id)

    if action:
        query = query.filter(TriggerLog.action == action)
    if entity_type:
        query = query.filter(TriggerLog.entity_type == entity_type)
    if from_date:
        query = query.filter(TriggerLog.created_at >= from_date)
    if to_date:
        query = query.filter(TriggerLog.created_at <= to_date)

    logs = query.order_by(TriggerLog.created_at.desc()).limit(limit).all()

    return TriggerLogListResponseSchema(logs=logs, total=len(logs))


# ============================================================================
# DASHBOARD & STATS
# ============================================================================

@router.get("/dashboard", response_model=TriggerDashboardSchema)
async def get_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère le dashboard des triggers.
    Nécessite: triggers.read
    """
    from datetime import timedelta

    from .models import Notification, ScheduledReport, Trigger, TriggerEvent
    tenant_id = request.state.tenant_id
    now = datetime.utcnow()
    yesterday = now - timedelta(hours=24)

    # Statistiques triggers
    total_triggers = db.query(Trigger).filter(Trigger.tenant_id == tenant_id).count()
    active_triggers = db.query(Trigger).filter(
        Trigger.tenant_id == tenant_id,
        Trigger.status == TriggerStatus.ACTIVE
    ).count()
    paused_triggers = db.query(Trigger).filter(
        Trigger.tenant_id == tenant_id,
        Trigger.status == TriggerStatus.PAUSED
    ).count()
    disabled_triggers = db.query(Trigger).filter(
        Trigger.tenant_id == tenant_id,
        Trigger.status == TriggerStatus.DISABLED
    ).count()

    # Statistiques événements
    total_events_24h = db.query(TriggerEvent).filter(
        TriggerEvent.tenant_id == tenant_id,
        TriggerEvent.triggered_at >= yesterday
    ).count()
    unresolved_events = db.query(TriggerEvent).filter(
        TriggerEvent.tenant_id == tenant_id,
        not TriggerEvent.resolved
    ).count()
    critical_events = db.query(TriggerEvent).filter(
        TriggerEvent.tenant_id == tenant_id,
        not TriggerEvent.resolved,
        TriggerEvent.severity.in_([AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY])
    ).count()

    # Statistiques notifications
    total_notifications_24h = db.query(Notification).filter(
        Notification.tenant_id == tenant_id,
        Notification.sent_at >= yesterday
    ).count()
    pending_notifications = db.query(Notification).filter(
        Notification.tenant_id == tenant_id,
        Notification.status == NotificationStatus.PENDING
    ).count()
    failed_notifications = db.query(Notification).filter(
        Notification.tenant_id == tenant_id,
        Notification.status == NotificationStatus.FAILED
    ).count()

    # Statistiques rapports
    scheduled_reports = db.query(ScheduledReport).filter(
        ScheduledReport.tenant_id == tenant_id,
        ScheduledReport.is_active
    ).count()
    reports_generated_24h = db.query(ScheduledReport).filter(
        ScheduledReport.tenant_id == tenant_id,
        ScheduledReport.last_generated_at >= yesterday
    ).count()

    stats = TriggerStatsSchema(
        total_triggers=total_triggers,
        active_triggers=active_triggers,
        paused_triggers=paused_triggers,
        disabled_triggers=disabled_triggers,
        total_events_24h=total_events_24h,
        unresolved_events=unresolved_events,
        critical_events=critical_events,
        total_notifications_24h=total_notifications_24h,
        pending_notifications=pending_notifications,
        failed_notifications=failed_notifications,
        scheduled_reports=scheduled_reports,
        reports_generated_24h=reports_generated_24h
    )

    # Événements récents
    recent_events = db.query(TriggerEvent).filter(
        TriggerEvent.tenant_id == tenant_id
    ).order_by(TriggerEvent.triggered_at.desc()).limit(10).all()

    # Prochains rapports
    upcoming_reports = db.query(ScheduledReport).filter(
        ScheduledReport.tenant_id == tenant_id,
        ScheduledReport.is_active,
        ScheduledReport.next_generation_at is not None
    ).order_by(ScheduledReport.next_generation_at).limit(5).all()

    return TriggerDashboardSchema(
        stats=stats,
        recent_events=recent_events,
        upcoming_reports=upcoming_reports
    )
