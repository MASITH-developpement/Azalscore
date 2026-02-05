"""
AZALS MODULE T6 - Service Diffusion Périodique
==============================================

Service métier pour la gestion des diffusions automatiques.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from .models import (
    BroadcastExecution,
    BroadcastFrequency,
    BroadcastMetric,
    BroadcastPreference,
    BroadcastStatus,
    BroadcastTemplate,
    ContentType,
    DeliveryChannel,
    DeliveryDetail,
    DeliveryStatus,
    RecipientList,
    RecipientMember,
    RecipientType,
    ScheduledBroadcast,
)


class BroadcastService:
    """Service de gestion des diffusions périodiques."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    def create_template(
        self,
        code: str,
        name: str,
        content_type: ContentType,
        subject_template: str | None = None,
        body_template: str | None = None,
        html_template: str | None = None,
        default_channel: DeliveryChannel = DeliveryChannel.EMAIL,
        available_channels: list[str] | None = None,
        variables: dict | None = None,
        styling: dict | None = None,
        data_sources: list[dict] | None = None,
        language: str = "fr",
        created_by: int | None = None,
        **kwargs
    ) -> BroadcastTemplate:
        """Créer un template de diffusion."""
        template = BroadcastTemplate(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            content_type=content_type,
            subject_template=subject_template,
            body_template=body_template,
            html_template=html_template,
            default_channel=default_channel,
            available_channels=json.dumps(available_channels) if available_channels else None,
            variables=json.dumps(variables) if variables else None,
            styling=json.dumps(styling) if styling else None,
            data_sources=json.dumps(data_sources) if data_sources else None,
            language=language,
            created_by=created_by
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_template(self, template_id: int) -> BroadcastTemplate | None:
        """Récupérer un template par ID."""
        return self.db.query(BroadcastTemplate).filter(
            and_(
                BroadcastTemplate.tenant_id == self.tenant_id,
                BroadcastTemplate.id == template_id
            )
        ).first()

    def get_template_by_code(self, code: str) -> BroadcastTemplate | None:
        """Récupérer un template par code."""
        return self.db.query(BroadcastTemplate).filter(
            and_(
                BroadcastTemplate.tenant_id == self.tenant_id,
                BroadcastTemplate.code == code
            )
        ).first()

    def list_templates(
        self,
        content_type: ContentType | None = None,
        is_active: bool | None = True,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[BroadcastTemplate], int]:
        """Lister les templates avec filtres."""
        query = self.db.query(BroadcastTemplate).filter(
            BroadcastTemplate.tenant_id == self.tenant_id
        )

        if content_type:
            query = query.filter(BroadcastTemplate.content_type == content_type)
        if is_active is not None:
            query = query.filter(BroadcastTemplate.is_active == is_active)

        total = query.count()
        items = query.order_by(desc(BroadcastTemplate.created_at)).offset(skip).limit(limit).all()
        return items, total

    def update_template(self, template_id: int, **updates) -> BroadcastTemplate | None:
        """Mettre à jour un template."""
        template = self.get_template(template_id)
        if not template:
            return None

        json_fields = ["available_channels", "variables", "styling", "data_sources"]
        for key, value in updates.items():
            if hasattr(template, key):
                if key in json_fields and value is not None:
                    setattr(template, key, json.dumps(value))
                else:
                    setattr(template, key, value)

        template.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete_template(self, template_id: int) -> bool:
        """Supprimer un template."""
        template = self.get_template(template_id)
        if not template or template.is_system:
            return False

        self.db.delete(template)
        self.db.commit()
        return True

    # ========================================================================
    # LISTES DE DESTINATAIRES
    # ========================================================================

    def create_recipient_list(
        self,
        code: str,
        name: str,
        description: str | None = None,
        is_dynamic: bool = False,
        query_config: dict | None = None,
        created_by: int | None = None
    ) -> RecipientList:
        """Créer une liste de destinataires."""
        recipient_list = RecipientList(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            is_dynamic=is_dynamic,
            query_config=json.dumps(query_config) if query_config else None,
            created_by=created_by
        )
        self.db.add(recipient_list)
        self.db.commit()
        self.db.refresh(recipient_list)
        return recipient_list

    def get_recipient_list(self, list_id: int) -> RecipientList | None:
        """Récupérer une liste par ID."""
        return self.db.query(RecipientList).filter(
            and_(
                RecipientList.tenant_id == self.tenant_id,
                RecipientList.id == list_id
            )
        ).first()

    def list_recipient_lists(
        self,
        is_active: bool | None = True,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[RecipientList], int]:
        """Lister les listes de destinataires."""
        query = self.db.query(RecipientList).filter(
            RecipientList.tenant_id == self.tenant_id
        )

        if is_active is not None:
            query = query.filter(RecipientList.is_active == is_active)

        total = query.count()
        items = query.order_by(RecipientList.name).offset(skip).limit(limit).all()
        return items, total

    def add_member_to_list(
        self,
        list_id: int,
        recipient_type: RecipientType,
        user_id: int | None = None,
        group_id: int | None = None,
        role_code: str | None = None,
        external_email: str | None = None,
        external_name: str | None = None,
        preferred_channel: DeliveryChannel | None = None,
        added_by: int | None = None
    ) -> RecipientMember:
        """Ajouter un membre à une liste."""
        member = RecipientMember(
            tenant_id=self.tenant_id,
            list_id=list_id,
            recipient_type=recipient_type,
            user_id=user_id,
            group_id=group_id,
            role_code=role_code,
            external_email=external_email,
            external_name=external_name,
            preferred_channel=preferred_channel,
            added_by=added_by
        )
        self.db.add(member)

        # Mettre à jour le compteur
        recipient_list = self.get_recipient_list(list_id)
        if recipient_list:
            recipient_list.total_recipients += 1
            recipient_list.active_recipients += 1

        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member_from_list(self, member_id: int) -> bool:
        """Retirer un membre d'une liste."""
        member = self.db.query(RecipientMember).filter(
            and_(
                RecipientMember.tenant_id == self.tenant_id,
                RecipientMember.id == member_id
            )
        ).first()

        if not member:
            return False

        # Mettre à jour le compteur
        recipient_list = self.get_recipient_list(member.list_id)
        if recipient_list:
            recipient_list.total_recipients -= 1
            if member.is_active:
                recipient_list.active_recipients -= 1

        self.db.delete(member)
        self.db.commit()
        return True

    def get_list_members(
        self,
        list_id: int,
        is_active: bool | None = True,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[RecipientMember], int]:
        """Récupérer les membres d'une liste."""
        query = self.db.query(RecipientMember).filter(
            and_(
                RecipientMember.tenant_id == self.tenant_id,
                RecipientMember.list_id == list_id
            )
        )

        if is_active is not None:
            query = query.filter(RecipientMember.is_active == is_active)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    # ========================================================================
    # DIFFUSIONS PROGRAMMÉES
    # ========================================================================

    def create_scheduled_broadcast(
        self,
        code: str,
        name: str,
        content_type: ContentType,
        frequency: BroadcastFrequency,
        delivery_channel: DeliveryChannel = DeliveryChannel.EMAIL,
        template_id: int | None = None,
        recipient_list_id: int | None = None,
        subject: str | None = None,
        body_content: str | None = None,
        html_content: str | None = None,
        cron_expression: str | None = None,
        timezone: str = "Europe/Paris",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        send_time: str | None = None,
        day_of_week: int | None = None,
        day_of_month: int | None = None,
        data_query: dict | None = None,
        created_by: int | None = None,
        **kwargs
    ) -> ScheduledBroadcast:
        """Créer une diffusion programmée."""
        broadcast = ScheduledBroadcast(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            content_type=content_type,
            frequency=frequency,
            delivery_channel=delivery_channel,
            template_id=template_id,
            recipient_list_id=recipient_list_id,
            subject=subject,
            body_content=body_content,
            html_content=html_content,
            cron_expression=cron_expression,
            timezone=timezone,
            start_date=start_date,
            end_date=end_date,
            send_time=send_time,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            data_query=json.dumps(data_query) if data_query else None,
            status=BroadcastStatus.DRAFT,
            created_by=created_by
        )

        # Calculer la prochaine exécution
        broadcast.next_run_at = self._calculate_next_run(broadcast)

        self.db.add(broadcast)
        self.db.commit()
        self.db.refresh(broadcast)
        return broadcast

    def get_scheduled_broadcast(self, broadcast_id: int) -> ScheduledBroadcast | None:
        """Récupérer une diffusion programmée par ID."""
        return self.db.query(ScheduledBroadcast).filter(
            and_(
                ScheduledBroadcast.tenant_id == self.tenant_id,
                ScheduledBroadcast.id == broadcast_id
            )
        ).first()

    def list_scheduled_broadcasts(
        self,
        status: BroadcastStatus | None = None,
        content_type: ContentType | None = None,
        is_active: bool | None = True,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[ScheduledBroadcast], int]:
        """Lister les diffusions programmées."""
        query = self.db.query(ScheduledBroadcast).filter(
            ScheduledBroadcast.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(ScheduledBroadcast.status == status)
        if content_type:
            query = query.filter(ScheduledBroadcast.content_type == content_type)
        if is_active is not None:
            query = query.filter(ScheduledBroadcast.is_active == is_active)

        total = query.count()
        items = query.order_by(desc(ScheduledBroadcast.created_at)).offset(skip).limit(limit).all()
        return items, total

    def update_scheduled_broadcast(self, broadcast_id: int, **updates) -> ScheduledBroadcast | None:
        """Mettre à jour une diffusion programmée."""
        broadcast = self.get_scheduled_broadcast(broadcast_id)
        if not broadcast:
            return None

        json_fields = ["data_query", "data_filters", "additional_channels"]
        for key, value in updates.items():
            if hasattr(broadcast, key):
                if key in json_fields and value is not None:
                    setattr(broadcast, key, json.dumps(value))
                else:
                    setattr(broadcast, key, value)

        # Recalculer prochaine exécution si paramètres de planification changés
        schedule_fields = ["frequency", "cron_expression", "send_time", "day_of_week", "day_of_month"]
        if any(f in updates for f in schedule_fields):
            broadcast.next_run_at = self._calculate_next_run(broadcast)

        broadcast.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(broadcast)
        return broadcast

    def activate_broadcast(self, broadcast_id: int) -> ScheduledBroadcast | None:
        """Activer une diffusion (passer en SCHEDULED ou ACTIVE)."""
        broadcast = self.get_scheduled_broadcast(broadcast_id)
        if not broadcast:
            return None

        if broadcast.frequency == BroadcastFrequency.ONCE:
            broadcast.status = BroadcastStatus.SCHEDULED
        else:
            broadcast.status = BroadcastStatus.ACTIVE

        broadcast.next_run_at = self._calculate_next_run(broadcast)
        broadcast.is_active = True
        broadcast.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(broadcast)
        return broadcast

    def pause_broadcast(self, broadcast_id: int) -> ScheduledBroadcast | None:
        """Mettre en pause une diffusion."""
        broadcast = self.get_scheduled_broadcast(broadcast_id)
        if not broadcast:
            return None

        broadcast.status = BroadcastStatus.PAUSED
        broadcast.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(broadcast)
        return broadcast

    def cancel_broadcast(self, broadcast_id: int) -> ScheduledBroadcast | None:
        """Annuler une diffusion."""
        broadcast = self.get_scheduled_broadcast(broadcast_id)
        if not broadcast:
            return None

        broadcast.status = BroadcastStatus.CANCELLED
        broadcast.is_active = False
        broadcast.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(broadcast)
        return broadcast

    def get_broadcasts_due(self) -> list[ScheduledBroadcast]:
        """Récupérer les diffusions à exécuter maintenant."""
        now = datetime.utcnow()
        return self.db.query(ScheduledBroadcast).filter(
            and_(
                ScheduledBroadcast.tenant_id == self.tenant_id,
                ScheduledBroadcast.is_active,
                ScheduledBroadcast.status.in_([BroadcastStatus.ACTIVE, BroadcastStatus.SCHEDULED]),
                ScheduledBroadcast.next_run_at <= now,
                or_(
                    ScheduledBroadcast.start_date is None,
                    ScheduledBroadcast.start_date <= now
                ),
                or_(
                    ScheduledBroadcast.end_date is None,
                    ScheduledBroadcast.end_date >= now
                )
            )
        ).all()

    # ========================================================================
    # EXÉCUTION DE DIFFUSION
    # ========================================================================

    def execute_broadcast(
        self,
        broadcast_id: int,
        triggered_by: str = "scheduler",
        triggered_user: int | None = None
    ) -> BroadcastExecution:
        """Exécuter une diffusion."""
        broadcast = self.get_scheduled_broadcast(broadcast_id)
        if not broadcast:
            raise ValueError(f"Broadcast {broadcast_id} not found")

        # Créer l'exécution
        execution = BroadcastExecution(
            tenant_id=self.tenant_id,
            scheduled_broadcast_id=broadcast_id,
            execution_number=broadcast.total_sent + 1,
            started_at=datetime.utcnow(),
            status=DeliveryStatus.SENDING,
            triggered_by=triggered_by,
            triggered_user=triggered_user
        )
        self.db.add(execution)
        self.db.commit()

        try:
            # Récupérer les destinataires
            recipients = self._get_recipients(broadcast)
            execution.total_recipients = len(recipients)

            # Générer le contenu
            content = self._generate_content(broadcast)
            execution.generated_subject = content.get("subject")
            execution.generated_content = content.get("body")

            # Créer les détails de livraison
            for recipient in recipients:
                detail = DeliveryDetail(
                    tenant_id=self.tenant_id,
                    execution_id=execution.id,
                    recipient_type=recipient["type"],
                    user_id=recipient.get("user_id"),
                    email=recipient.get("email"),
                    channel=broadcast.delivery_channel,
                    status=DeliveryStatus.PENDING,
                    tracking_id=str(uuid.uuid4())
                )
                self.db.add(detail)

            # Simuler l'envoi (dans un vrai système, appeler le service d'envoi)
            execution.sent_count = len(recipients)
            execution.delivered_count = len(recipients)  # Simulé
            execution.status = DeliveryStatus.DELIVERED
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()

            # Mettre à jour les stats de la diffusion
            broadcast.total_sent += 1
            broadcast.total_delivered += len(recipients)
            broadcast.last_run_at = datetime.utcnow()

            # Calculer prochaine exécution
            if broadcast.frequency != BroadcastFrequency.ONCE:
                broadcast.next_run_at = self._calculate_next_run(broadcast)
            else:
                broadcast.status = BroadcastStatus.COMPLETED

            self.db.commit()
            self.db.refresh(execution)

        except Exception as e:
            execution.status = DeliveryStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            broadcast.last_error = str(e)
            broadcast.status = BroadcastStatus.ERROR
            self.db.commit()
            self.db.refresh(execution)

        return execution

    def get_execution(self, execution_id: int) -> BroadcastExecution | None:
        """Récupérer une exécution par ID."""
        return self.db.query(BroadcastExecution).filter(
            and_(
                BroadcastExecution.tenant_id == self.tenant_id,
                BroadcastExecution.id == execution_id
            )
        ).first()

    def list_executions(
        self,
        broadcast_id: int | None = None,
        status: DeliveryStatus | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[BroadcastExecution], int]:
        """Lister les exécutions."""
        query = self.db.query(BroadcastExecution).filter(
            BroadcastExecution.tenant_id == self.tenant_id
        )

        if broadcast_id:
            query = query.filter(BroadcastExecution.scheduled_broadcast_id == broadcast_id)
        if status:
            query = query.filter(BroadcastExecution.status == status)

        total = query.count()
        items = query.order_by(desc(BroadcastExecution.started_at)).offset(skip).limit(limit).all()
        return items, total

    def get_delivery_details(
        self,
        execution_id: int,
        status: DeliveryStatus | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[DeliveryDetail], int]:
        """Récupérer les détails de livraison d'une exécution."""
        query = self.db.query(DeliveryDetail).filter(
            and_(
                DeliveryDetail.tenant_id == self.tenant_id,
                DeliveryDetail.execution_id == execution_id
            )
        )

        if status:
            query = query.filter(DeliveryDetail.status == status)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    # ========================================================================
    # PRÉFÉRENCES UTILISATEUR
    # ========================================================================

    def get_user_preferences(self, user_id: int) -> BroadcastPreference | None:
        """Récupérer les préférences d'un utilisateur."""
        return self.db.query(BroadcastPreference).filter(
            and_(
                BroadcastPreference.tenant_id == self.tenant_id,
                BroadcastPreference.user_id == user_id
            )
        ).first()

    def set_user_preferences(
        self,
        user_id: int,
        **preferences
    ) -> BroadcastPreference:
        """Définir les préférences d'un utilisateur."""
        pref = self.get_user_preferences(user_id)

        if not pref:
            pref = BroadcastPreference(
                tenant_id=self.tenant_id,
                user_id=user_id
            )
            self.db.add(pref)

        json_fields = ["excluded_content_types", "excluded_broadcasts"]
        for key, value in preferences.items():
            if hasattr(pref, key):
                if key in json_fields and value is not None:
                    setattr(pref, key, json.dumps(value))
                else:
                    setattr(pref, key, value)

        pref.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(pref)
        return pref

    def unsubscribe_user(self, user_id: int, broadcast_id: int | None = None) -> bool:
        """Désabonner un utilisateur."""
        pref = self.get_user_preferences(user_id)

        if not pref:
            pref = BroadcastPreference(
                tenant_id=self.tenant_id,
                user_id=user_id
            )
            self.db.add(pref)

        if broadcast_id:
            # Désabonner d'une diffusion spécifique
            excluded = json.loads(pref.excluded_broadcasts or "[]")
            if broadcast_id not in excluded:
                excluded.append(broadcast_id)
                pref.excluded_broadcasts = json.dumps(excluded)
        else:
            # Désabonner de tout
            pref.is_unsubscribed_all = True
            pref.unsubscribed_at = datetime.utcnow()

        self.db.commit()
        return True

    # ========================================================================
    # MÉTRIQUES
    # ========================================================================

    def record_metrics(
        self,
        metric_date: datetime | None = None,
        period_type: str = "DAILY"
    ) -> BroadcastMetric:
        """Enregistrer les métriques de diffusion."""
        if not metric_date:
            metric_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculer les métriques
        start_date = metric_date
        if period_type == "WEEKLY":
            end_date = start_date + timedelta(days=7)
        elif period_type == "MONTHLY":
            end_date = start_date + timedelta(days=30)
        else:
            end_date = start_date + timedelta(days=1)

        # Compter les exécutions
        executions = self.db.query(BroadcastExecution).filter(
            and_(
                BroadcastExecution.tenant_id == self.tenant_id,
                BroadcastExecution.started_at >= start_date,
                BroadcastExecution.started_at < end_date
            )
        ).all()

        total_messages = sum(e.total_recipients or 0 for e in executions)
        delivered = sum(e.delivered_count or 0 for e in executions)
        failed = sum(e.failed_count or 0 for e in executions)
        opened = sum(e.opened_count or 0 for e in executions)
        clicked = sum(e.clicked_count or 0 for e in executions)

        metric = BroadcastMetric(
            tenant_id=self.tenant_id,
            metric_date=metric_date,
            period_type=period_type,
            total_broadcasts=self.db.query(ScheduledBroadcast).filter(
                ScheduledBroadcast.tenant_id == self.tenant_id
            ).count(),
            total_executions=len(executions),
            total_messages=total_messages,
            delivered_count=delivered,
            failed_count=failed,
            opened_count=opened,
            clicked_count=clicked,
            delivery_rate=(delivered / total_messages * 100) if total_messages > 0 else 0,
            open_rate=(opened / delivered * 100) if delivered > 0 else 0,
            click_rate=(clicked / opened * 100) if opened > 0 else 0
        )

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def get_metrics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        period_type: str = "DAILY",
        limit: int = 30
    ) -> list[BroadcastMetric]:
        """Récupérer les métriques."""
        query = self.db.query(BroadcastMetric).filter(
            and_(
                BroadcastMetric.tenant_id == self.tenant_id,
                BroadcastMetric.period_type == period_type
            )
        )

        if start_date:
            query = query.filter(BroadcastMetric.metric_date >= start_date)
        if end_date:
            query = query.filter(BroadcastMetric.metric_date <= end_date)

        return query.order_by(desc(BroadcastMetric.metric_date)).limit(limit).all()

    def get_dashboard_stats(self) -> dict[str, Any]:
        """Récupérer les statistiques pour le dashboard."""
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)

        # Stats globales
        total_broadcasts = self.db.query(ScheduledBroadcast).filter(
            ScheduledBroadcast.tenant_id == self.tenant_id
        ).count()

        active_broadcasts = self.db.query(ScheduledBroadcast).filter(
            and_(
                ScheduledBroadcast.tenant_id == self.tenant_id,
                ScheduledBroadcast.status == BroadcastStatus.ACTIVE
            )
        ).count()

        # Exécutions récentes
        recent_executions = self.db.query(BroadcastExecution).filter(
            and_(
                BroadcastExecution.tenant_id == self.tenant_id,
                BroadcastExecution.started_at >= week_ago
            )
        ).all()

        total_sent = sum(e.sent_count or 0 for e in recent_executions)
        total_delivered = sum(e.delivered_count or 0 for e in recent_executions)
        total_opened = sum(e.opened_count or 0 for e in recent_executions)

        # Prochaines exécutions
        upcoming = self.db.query(ScheduledBroadcast).filter(
            and_(
                ScheduledBroadcast.tenant_id == self.tenant_id,
                ScheduledBroadcast.is_active,
                ScheduledBroadcast.next_run_at >= now
            )
        ).order_by(ScheduledBroadcast.next_run_at).limit(5).all()

        return {
            "total_broadcasts": total_broadcasts,
            "active_broadcasts": active_broadcasts,
            "executions_this_week": len(recent_executions),
            "messages_sent_this_week": total_sent,
            "delivery_rate": (total_delivered / total_sent * 100) if total_sent > 0 else 0,
            "open_rate": (total_opened / total_delivered * 100) if total_delivered > 0 else 0,
            "upcoming_broadcasts": [
                {
                    "id": b.id,
                    "name": b.name,
                    "next_run_at": b.next_run_at.isoformat() if b.next_run_at else None
                }
                for b in upcoming
            ]
        }

    # ========================================================================
    # HELPERS INTERNES
    # ========================================================================

    def _calculate_next_run(self, broadcast: ScheduledBroadcast) -> datetime | None:
        """Calculer la prochaine date d'exécution."""
        now = datetime.utcnow()
        base_date = broadcast.last_run_at or now

        if broadcast.frequency == BroadcastFrequency.ONCE:
            if broadcast.start_date and broadcast.start_date > now:
                return broadcast.start_date
            return now

        elif broadcast.frequency == BroadcastFrequency.DAILY:
            next_run = base_date + timedelta(days=1)

        elif broadcast.frequency == BroadcastFrequency.WEEKLY:
            next_run = base_date + timedelta(weeks=1)
            if broadcast.day_of_week is not None:
                days_ahead = broadcast.day_of_week - next_run.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                next_run = next_run + timedelta(days=days_ahead)

        elif broadcast.frequency == BroadcastFrequency.BIWEEKLY:
            next_run = base_date + timedelta(weeks=2)

        elif broadcast.frequency == BroadcastFrequency.MONTHLY:
            next_month = base_date.month + 1
            next_year = base_date.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            day = broadcast.day_of_month or base_date.day
            day = min(day, 28)  # Éviter les problèmes de fin de mois
            next_run = base_date.replace(year=next_year, month=next_month, day=day)

        elif broadcast.frequency == BroadcastFrequency.QUARTERLY:
            next_month = ((base_date.month - 1) // 3 + 1) * 3 + 1
            next_year = base_date.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            next_run = base_date.replace(year=next_year, month=next_month, day=1)

        elif broadcast.frequency == BroadcastFrequency.YEARLY:
            next_run = base_date.replace(year=base_date.year + 1)

        else:
            next_run = base_date + timedelta(days=1)

        # Appliquer l'heure d'envoi
        if broadcast.send_time:
            try:
                hour, minute = map(int, broadcast.send_time.split(":"))
                next_run = next_run.replace(hour=hour, minute=minute, second=0)
            except Exception as e:
                logger.warning(
                    "[BROADCAST_SCHEDULE] Format send_time invalide",
                    extra={
                        "send_time": str(broadcast.send_time),
                        "error": str(e)[:200],
                        "consequence": "default_time_used"
                    }
                )

        # S'assurer que c'est dans le futur
        if next_run <= now:
            next_run = now + timedelta(hours=1)

        return next_run

    def _get_recipients(self, broadcast: ScheduledBroadcast) -> list[dict]:
        """Récupérer les destinataires d'une diffusion."""
        recipients = []

        if broadcast.recipient_list_id:
            members, _ = self.get_list_members(
                broadcast.recipient_list_id,
                is_active=True,
                limit=10000
            )

            for member in members:
                if member.is_unsubscribed:
                    continue

                recipient = {
                    "type": member.recipient_type,
                    "user_id": member.user_id,
                    "email": member.external_email,
                    "name": member.external_name,
                    "channel": member.preferred_channel or broadcast.delivery_channel
                }
                recipients.append(recipient)

        return recipients

    def _generate_content(self, broadcast: ScheduledBroadcast) -> dict[str, str]:
        """Générer le contenu d'une diffusion."""
        content = {
            "subject": broadcast.subject or "",
            "body": broadcast.body_content or "",
            "html": broadcast.html_content or ""
        }

        # Si un template est utilisé
        if broadcast.template_id:
            template = self.get_template(broadcast.template_id)
            if template:
                content["subject"] = template.subject_template or content["subject"]
                content["body"] = template.body_template or content["body"]
                content["html"] = template.html_template or content["html"]

        # TODO: Remplacer les variables dynamiques

        return content


def get_broadcast_service(db: Session, tenant_id: str) -> BroadcastService:
    """Factory pour créer une instance du service."""
    return BroadcastService(db, tenant_id)
