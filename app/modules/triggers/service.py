"""
AZALS MODULE T2 - Service Déclencheurs & Diffusion
===================================================

Logique métier pour le système de déclencheurs.
"""

import json
import logging

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.encryption import decrypt_value, encrypt_value

from .models import (
    AlertSeverity,
    ConditionOperator,
    EscalationLevel,
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationTemplate,
    ReportFrequency,
    ReportHistory,
    ScheduledReport,
    Trigger,
    TriggerEvent,
    TriggerLog,
    TriggerStatus,
    TriggerSubscription,
    TriggerType,
    WebhookEndpoint,
)


class TriggerService:
    """Service principal pour les déclencheurs."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2

    # ========================================================================
    # GESTION DES TRIGGERS
    # ========================================================================

    def create_trigger(
        self,
        code: str,
        name: str,
        trigger_type: TriggerType,
        source_module: str,
        condition: dict[str, Any],
        created_by: int | None = None,
        description: str | None = None,
        source_entity: str | None = None,
        source_field: str | None = None,
        threshold_value: str | None = None,
        threshold_operator: ConditionOperator | None = None,
        schedule_cron: str | None = None,
        severity: AlertSeverity = AlertSeverity.WARNING,
        escalation_enabled: bool = False,
        escalation_delay_minutes: int = 60,
        cooldown_minutes: int = 60,
        action_template_id: int | None = None
    ) -> Trigger:
        """Crée un nouveau trigger."""
        # Vérifier code unique
        existing = self.get_trigger_by_code(code)
        if existing:
            raise ValueError(f"Trigger {code} existe déjà")

        trigger = Trigger(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            trigger_type=trigger_type,
            source_module=source_module,
            source_entity=source_entity,
            source_field=source_field,
            condition=json.dumps(condition),
            threshold_value=threshold_value,
            threshold_operator=threshold_operator,
            schedule_cron=schedule_cron,
            severity=severity,
            escalation_enabled=escalation_enabled,
            escalation_delay_minutes=escalation_delay_minutes,
            cooldown_minutes=cooldown_minutes,
            action_template_id=action_template_id,
            created_by=created_by
        )

        self.db.add(trigger)

        self._log("TRIGGER_CREATED", "TRIGGER", trigger.id,
                 details={"code": code, "type": trigger_type.value})

        self.db.commit()
        return trigger

    def get_trigger(self, trigger_id: int) -> Trigger | None:
        """Récupère un trigger par ID."""
        return self.db.query(Trigger).filter(
            Trigger.tenant_id == self.tenant_id,
            Trigger.id == trigger_id
        ).first()

    def get_trigger_by_code(self, code: str) -> Trigger | None:
        """Récupère un trigger par code."""
        return self.db.query(Trigger).filter(
            Trigger.tenant_id == self.tenant_id,
            Trigger.code == code
        ).first()

    def list_triggers(
        self,
        source_module: str | None = None,
        trigger_type: TriggerType | None = None,
        include_inactive: bool = False
    ) -> list[Trigger]:
        """Liste les triggers."""
        query = self.db.query(Trigger).filter(
            Trigger.tenant_id == self.tenant_id
        )

        if source_module:
            query = query.filter(Trigger.source_module == source_module)

        if trigger_type:
            query = query.filter(Trigger.trigger_type == trigger_type)

        if not include_inactive:
            query = query.filter(Trigger.status == TriggerStatus.ACTIVE)

        return query.order_by(Trigger.severity.desc(), Trigger.name).all()

    def update_trigger(
        self,
        trigger_id: int,
        **kwargs
    ) -> Trigger:
        """Met à jour un trigger."""
        trigger = self.get_trigger(trigger_id)
        if not trigger:
            raise ValueError("Trigger non trouvé")

        for key, value in kwargs.items():
            if hasattr(trigger, key):
                if key == 'condition' and isinstance(value, dict):
                    value = json.dumps(value)
                setattr(trigger, key, value)

        self._log("TRIGGER_UPDATED", "TRIGGER", trigger_id)
        self.db.commit()
        return trigger

    def delete_trigger(self, trigger_id: int, deleted_by: int | None = None) -> bool:
        """Supprime un trigger."""
        trigger = self.get_trigger(trigger_id)
        if not trigger:
            return False

        self._log("TRIGGER_DELETED", "TRIGGER", trigger_id,
                 details={"code": trigger.code})

        self.db.delete(trigger)
        self.db.commit()
        return True

    def pause_trigger(self, trigger_id: int) -> Trigger:
        """Met en pause un trigger."""
        trigger = self.get_trigger(trigger_id)
        if not trigger:
            raise ValueError("Trigger non trouvé")

        trigger.status = TriggerStatus.PAUSED
        self._log("TRIGGER_PAUSED", "TRIGGER", trigger_id)
        self.db.commit()
        return trigger

    def resume_trigger(self, trigger_id: int) -> Trigger:
        """Reprend un trigger en pause."""
        trigger = self.get_trigger(trigger_id)
        if not trigger:
            raise ValueError("Trigger non trouvé")

        trigger.status = TriggerStatus.ACTIVE
        self._log("TRIGGER_RESUMED", "TRIGGER", trigger_id)
        self.db.commit()
        return trigger

    # ========================================================================
    # ABONNEMENTS
    # ========================================================================

    def subscribe_user(
        self,
        trigger_id: int,
        user_id: int,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        escalation_level: EscalationLevel = EscalationLevel.L1,
        created_by: int | None = None
    ) -> TriggerSubscription:
        """Abonne un utilisateur à un trigger."""
        subscription = TriggerSubscription(
            tenant_id=self.tenant_id,
            trigger_id=trigger_id,
            user_id=user_id,
            channel=channel,
            escalation_level=escalation_level,
            created_by=created_by
        )

        self.db.add(subscription)
        self.db.commit()
        return subscription

    def subscribe_role(
        self,
        trigger_id: int,
        role_code: str,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        escalation_level: EscalationLevel = EscalationLevel.L1,
        created_by: int | None = None
    ) -> TriggerSubscription:
        """Abonne tous les utilisateurs d'un rôle à un trigger."""
        subscription = TriggerSubscription(
            tenant_id=self.tenant_id,
            trigger_id=trigger_id,
            role_code=role_code,
            channel=channel,
            escalation_level=escalation_level,
            created_by=created_by
        )

        self.db.add(subscription)
        self.db.commit()
        return subscription

    def unsubscribe(self, subscription_id: int) -> bool:
        """Désabonne d'un trigger."""
        subscription = self.db.query(TriggerSubscription).filter(
            TriggerSubscription.id == subscription_id,
            TriggerSubscription.tenant_id == self.tenant_id
        ).first()

        if subscription:
            self.db.delete(subscription)
            self.db.commit()
            return True
        return False

    def get_trigger_subscriptions(self, trigger_id: int) -> list[TriggerSubscription]:
        """Liste les abonnements d'un trigger."""
        return self.db.query(TriggerSubscription).filter(
            TriggerSubscription.trigger_id == trigger_id,
            TriggerSubscription.tenant_id == self.tenant_id,
            TriggerSubscription.is_active
        ).all()

    # ========================================================================
    # ÉVALUATION ET DÉCLENCHEMENT
    # ========================================================================

    def evaluate_trigger(self, trigger: Trigger, data: dict[str, Any]) -> bool:
        """
        Évalue si un trigger doit se déclencher.
        Retourne True si la condition est remplie.
        """
        if trigger.status != TriggerStatus.ACTIVE:
            return False

        # Vérifier cooldown
        if trigger.last_triggered_at:
            cooldown_end = trigger.last_triggered_at + timedelta(minutes=trigger.cooldown_minutes)
            if datetime.utcnow() < cooldown_end:
                return False

        condition = json.loads(trigger.condition)
        return self._evaluate_condition(condition, data)

    def _evaluate_condition(self, condition: dict[str, Any], data: dict[str, Any]) -> bool:
        """Évalue une condition."""
        # Condition AND
        if 'and' in condition:
            return all(self._evaluate_condition(c, data) for c in condition['and'])

        # Condition OR
        if 'or' in condition:
            return any(self._evaluate_condition(c, data) for c in condition['or'])

        # Condition NOT
        if 'not' in condition:
            return not self._evaluate_condition(condition['not'], data)

        # Condition simple
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')

        if not field or not operator:
            return False

        # Récupérer la valeur du champ
        field_value = self._get_field_value(data, field)
        if field_value is None and operator not in ['is_null', 'is_not_null']:
            return False

        return self._compare(field_value, operator, value)

    def _get_field_value(self, data: dict[str, Any], field: str) -> Any:
        """Récupère la valeur d'un champ (support notation pointée)."""
        keys = field.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def _compare(self, field_value: Any, operator: str, target_value: Any) -> bool:
        """Compare une valeur selon l'opérateur."""
        try:
            if operator == 'eq':
                return field_value == target_value
            elif operator == 'ne':
                return field_value != target_value
            elif operator == 'gt':
                return float(field_value) > float(target_value)
            elif operator == 'ge':
                return float(field_value) >= float(target_value)
            elif operator == 'lt':
                return float(field_value) < float(target_value)
            elif operator == 'le':
                return float(field_value) <= float(target_value)
            elif operator == 'in':
                return field_value in target_value
            elif operator == 'not_in':
                return field_value not in target_value
            elif operator == 'contains':
                return target_value in str(field_value)
            elif operator == 'starts_with':
                return str(field_value).startswith(str(target_value))
            elif operator == 'ends_with':
                return str(field_value).endswith(str(target_value))
            elif operator == 'between':
                return target_value[0] <= field_value <= target_value[1]
            elif operator == 'is_null':
                return field_value is None
            elif operator == 'is_not_null':
                return field_value is not None
            else:
                return False
        except (ValueError, TypeError):
            return False

    def fire_trigger(
        self,
        trigger: Trigger,
        triggered_value: Any = None,
        condition_details: dict[str, Any] = None
    ) -> TriggerEvent:
        """
        Déclenche un trigger et crée les notifications.
        """
        # Créer l'événement
        event = TriggerEvent(
            tenant_id=self.tenant_id,
            trigger_id=trigger.id,
            triggered_value=str(triggered_value) if triggered_value else None,
            condition_details=json.dumps(condition_details) if condition_details else None,
            severity=trigger.severity,
            escalation_level=EscalationLevel.L1
        )

        self.db.add(event)

        # Mettre à jour le trigger
        trigger.last_triggered_at = datetime.utcnow()
        trigger.trigger_count += 1

        self.db.flush()

        # Créer les notifications
        subscriptions = self.get_trigger_subscriptions(trigger.id)
        self._create_notifications(event, trigger, subscriptions)

        self._log("TRIGGER_FIRED", "EVENT", event.id,
                 details={
                     "trigger_code": trigger.code,
                     "severity": trigger.severity.value,
                     "value": str(triggered_value)
                 })

        self.db.commit()
        return event

    def _create_notifications(
        self,
        event: TriggerEvent,
        trigger: Trigger,
        subscriptions: list[TriggerSubscription]
    ):
        """Crée les notifications pour un événement."""
        template = trigger.template

        for sub in subscriptions:
            # Déterminer les destinataires
            recipients = self._resolve_subscription_recipients(sub)

            for recipient in recipients:
                # Générer le contenu
                subject, body = self._render_notification(
                    trigger, event, template, recipient
                )

                notification = Notification(
                    tenant_id=self.tenant_id,
                    event_id=event.id,
                    user_id=recipient.get('user_id'),
                    email=recipient.get('email'),
                    channel=sub.channel,
                    subject=subject,
                    body=body,
                    status=NotificationStatus.PENDING
                )

                self.db.add(notification)

    def _resolve_subscription_recipients(self, subscription: TriggerSubscription) -> list[dict[str, Any]]:
        """Résout les destinataires d'un abonnement."""
        recipients = []

        if subscription.user_id:
            # NOTE: Phase 2 - Récupérer email via IAMService.get_user(user_id)
            recipients.append({
                'user_id': subscription.user_id,
                'email': None  # Résolu par IAM en Phase 2
            })

        if subscription.role_code:
            # NOTE: Phase 2 - Récupérer utilisateurs du rôle via IAMService
            pass

        if subscription.group_code:
            # NOTE: Phase 2 - Récupérer utilisateurs du groupe via IAMService
            pass

        if subscription.email_external:
            recipients.append({
                'user_id': None,
                'email': subscription.email_external
            })

        return recipients

    def _render_notification(
        self,
        trigger: Trigger,
        event: TriggerEvent,
        template: NotificationTemplate | None,
        recipient: dict[str, Any]
    ) -> tuple[str, str]:
        """Génère le contenu de la notification."""
        # Variables disponibles
        variables = {
            'trigger_name': trigger.name,
            'trigger_code': trigger.code,
            'severity': event.severity.value,
            'triggered_at': event.triggered_at.isoformat(),
            'triggered_value': event.triggered_value,
            'source_module': trigger.source_module,
        }

        if template:
            subject = self._render_template(template.subject_template or "", variables)
            body = self._render_template(template.body_template, variables)
        else:
            # Template par défaut
            subject = f"[{event.severity.value}] Alerte: {trigger.name}"
            body = f"""
Alerte AZALS

Trigger: {trigger.name}
Sévérité: {event.severity.value}
Module: {trigger.source_module}
Valeur: {event.triggered_value}
Date: {event.triggered_at.isoformat()}

---
Message automatique AZALS
"""

        return subject, body

    def _render_template(self, template: str, variables: dict[str, Any]) -> str:
        """Remplace les variables dans un template."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value) if value else "")
        return result

    # ========================================================================
    # ÉVÉNEMENTS
    # ========================================================================

    def get_event(self, event_id: int) -> TriggerEvent | None:
        """Récupère un événement par ID."""
        return self.db.query(TriggerEvent).filter(
            TriggerEvent.tenant_id == self.tenant_id,
            TriggerEvent.id == event_id
        ).first()

    def list_events(
        self,
        trigger_id: int | None = None,
        resolved: bool | None = None,
        severity: AlertSeverity | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 100
    ) -> list[TriggerEvent]:
        """Liste les événements."""
        query = self.db.query(TriggerEvent).filter(
            TriggerEvent.tenant_id == self.tenant_id
        )

        if trigger_id:
            query = query.filter(TriggerEvent.trigger_id == trigger_id)

        if resolved is not None:
            query = query.filter(TriggerEvent.resolved == resolved)

        if severity:
            query = query.filter(TriggerEvent.severity == severity)

        if from_date:
            query = query.filter(TriggerEvent.triggered_at >= from_date)

        if to_date:
            query = query.filter(TriggerEvent.triggered_at <= to_date)

        return query.order_by(TriggerEvent.triggered_at.desc()).limit(limit).all()

    def resolve_event(
        self,
        event_id: int,
        resolved_by: int,
        resolution_notes: str | None = None
    ) -> TriggerEvent:
        """Marque un événement comme résolu."""
        event = self.get_event(event_id)
        if not event:
            raise ValueError("Événement non trouvé")

        if event.resolved:
            raise ValueError("Événement déjà résolu")

        event.resolved = True
        event.resolved_at = datetime.utcnow()
        event.resolved_by = resolved_by
        event.resolution_notes = resolution_notes

        self._log("EVENT_RESOLVED", "EVENT", event_id,
                 details={"trigger_id": event.trigger_id})

        self.db.commit()
        return event

    def escalate_event(self, event_id: int) -> TriggerEvent:
        """Escalade un événement au niveau supérieur."""
        event = self.get_event(event_id)
        if not event:
            raise ValueError("Événement non trouvé")

        if event.resolved:
            raise ValueError("Événement déjà résolu")

        # Passer au niveau supérieur
        level_order = [EscalationLevel.L1, EscalationLevel.L2, EscalationLevel.L3, EscalationLevel.L4]
        current_idx = level_order.index(event.escalation_level)

        if current_idx >= len(level_order) - 1:
            raise ValueError("Niveau d'escalade maximum atteint")

        event.escalation_level = level_order[current_idx + 1]
        event.escalated_at = datetime.utcnow()

        # SÉCURITÉ: Notifier le niveau supérieur (filtrer par tenant_id)
        trigger = event.trigger
        subscriptions = self.db.query(TriggerSubscription).filter(
            TriggerSubscription.tenant_id == self.tenant_id,
            TriggerSubscription.trigger_id == trigger.id,
            TriggerSubscription.escalation_level == event.escalation_level,
            TriggerSubscription.is_active
        ).all()

        self._create_notifications(event, trigger, subscriptions)

        self._log("EVENT_ESCALATED", "EVENT", event_id,
                 details={"new_level": event.escalation_level.value})

        self.db.commit()
        return event

    # ========================================================================
    # NOTIFICATIONS
    # ========================================================================

    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> list[Notification]:
        """Liste les notifications d'un utilisateur."""
        query = self.db.query(Notification).filter(
            Notification.tenant_id == self.tenant_id,
            Notification.user_id == user_id
        )

        if unread_only:
            query = query.filter(Notification.read_at.is_(None))

        return query.order_by(Notification.sent_at.desc()).limit(limit).all()

    def mark_notification_read(self, notification_id: int) -> Notification:
        """Marque une notification comme lue."""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.tenant_id == self.tenant_id
        ).first()

        if notification:
            notification.read_at = datetime.utcnow()
            notification.status = NotificationStatus.READ
            self.db.commit()

        return notification

    def send_pending_notifications(self) -> int:
        """Envoie les notifications en attente."""
        pending = self.db.query(Notification).filter(
            Notification.tenant_id == self.tenant_id,
            Notification.status == NotificationStatus.PENDING
        ).limit(100).all()

        sent_count = 0
        for notification in pending:
            try:
                self._send_notification(notification)
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                sent_count += 1
            except Exception as e:
                notification.status = NotificationStatus.FAILED
                notification.failed_at = datetime.utcnow()
                notification.failure_reason = str(e)
                notification.retry_count += 1

        self.db.commit()
        return sent_count

    def _send_notification(self, notification: Notification):
        """Envoie une notification via le canal approprié."""
        if notification.channel == NotificationChannel.EMAIL:
            # NOTE: Phase 2 - Intégration avec email_service
            pass
        elif notification.channel == NotificationChannel.WEBHOOK:
            # NOTE: Phase 2 - Intégration webhook_service
            pass
        elif notification.channel == NotificationChannel.IN_APP:
            # Notification in-app, pas d'envoi externe nécessaire
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.utcnow()
        # Autres canaux...

    # ========================================================================
    # RAPPORTS PÉRIODIQUES
    # ========================================================================

    def create_scheduled_report(
        self,
        code: str,
        name: str,
        report_type: str,
        frequency: ReportFrequency,
        recipients: dict[str, Any],
        created_by: int | None = None,
        description: str | None = None,
        report_config: dict | None = None,
        schedule_day: int | None = None,
        schedule_time: str | None = None,
        output_format: str = 'PDF'
    ) -> ScheduledReport:
        """Crée un rapport périodique."""
        report = ScheduledReport(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            report_type=report_type,
            report_config=json.dumps(report_config) if report_config else None,
            frequency=frequency,
            schedule_day=schedule_day,
            schedule_time=schedule_time,
            recipients=json.dumps(recipients),
            output_format=output_format,
            created_by=created_by
        )

        # Calculer la prochaine génération
        report.next_generation_at = self._calculate_next_generation(report)

        self.db.add(report)

        self._log("REPORT_CREATED", "REPORT", report.id,
                 details={"code": code, "frequency": frequency.value})

        self.db.commit()
        return report

    def _calculate_next_generation(self, report: ScheduledReport) -> datetime:
        """Calcule la prochaine date de génération."""
        now = datetime.utcnow()

        if report.frequency == ReportFrequency.DAILY:
            next_gen = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        elif report.frequency == ReportFrequency.WEEKLY:
            days_ahead = report.schedule_day or 1  # Lundi par défaut
            days_ahead = days_ahead - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_gen = now.replace(hour=0, minute=0, second=0) + timedelta(days=days_ahead)
        elif report.frequency == ReportFrequency.MONTHLY:
            day = report.schedule_day or 1
            if now.day >= day:
                # Mois suivant
                if now.month == 12:
                    next_gen = now.replace(year=now.year + 1, month=1, day=day, hour=0, minute=0, second=0)
                else:
                    next_gen = now.replace(month=now.month + 1, day=day, hour=0, minute=0, second=0)
            else:
                next_gen = now.replace(day=day, hour=0, minute=0, second=0)
        else:
            next_gen = now + timedelta(days=1)

        # Appliquer l'heure si spécifiée
        if report.schedule_time:
            try:
                hour, minute = map(int, report.schedule_time.split(':'))
                next_gen = next_gen.replace(hour=hour, minute=minute)
            except (ValueError, TypeError) as e:
                logger.warning(
                    "[TRIGGERS] Format schedule_time invalide",
                    extra={"schedule_time": report.schedule_time, "error": str(e)[:200], "consequence": "default_time_kept"}
                )

        return next_gen

    def list_scheduled_reports(self, include_inactive: bool = False) -> list[ScheduledReport]:
        """Liste les rapports planifiés."""
        query = self.db.query(ScheduledReport).filter(
            ScheduledReport.tenant_id == self.tenant_id
        )

        if not include_inactive:
            query = query.filter(ScheduledReport.is_active)

        return query.order_by(ScheduledReport.next_generation_at).all()

    def generate_report(self, report_id: int, generated_by: int | None = None) -> ReportHistory:
        """Génère un rapport."""
        report = self.db.query(ScheduledReport).filter(
            ScheduledReport.id == report_id,
            ScheduledReport.tenant_id == self.tenant_id
        ).first()

        if not report:
            raise ValueError("Rapport non trouvé")

        # NOTE: Phase 2 - Intégrer avec report_service pour génération PDF/Excel
        file_name = f"{report.code}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{report.output_format.lower()}"

        history = ReportHistory(
            tenant_id=self.tenant_id,
            report_id=report.id,
            generated_by=generated_by,
            file_name=file_name,
            file_format=report.output_format,
            success=True
        )

        self.db.add(history)

        # Mettre à jour le rapport
        report.last_generated_at = datetime.utcnow()
        report.next_generation_at = self._calculate_next_generation(report)
        report.generation_count += 1

        self._log("REPORT_GENERATED", "REPORT", report.id,
                 details={"file_name": file_name})

        self.db.commit()
        return history

    def generate_due_reports(self) -> int:
        """Génère les rapports dont la date est passée."""
        due_reports = self.db.query(ScheduledReport).filter(
            ScheduledReport.tenant_id == self.tenant_id,
            ScheduledReport.is_active,
            ScheduledReport.next_generation_at <= datetime.utcnow()
        ).all()

        count = 0
        for report in due_reports:
            try:
                self.generate_report(report.id)
                count += 1
            except Exception as e:
                self._log("REPORT_GENERATION_FAILED", "REPORT", report.id,
                         success=False, error_message=str(e))

        return count

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    def create_template(
        self,
        code: str,
        name: str,
        body_template: str,
        created_by: int | None = None,
        description: str | None = None,
        subject_template: str | None = None,
        body_html: str | None = None,
        available_variables: list[str] | None = None
    ) -> NotificationTemplate:
        """Crée un template de notification."""
        template = NotificationTemplate(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            subject_template=subject_template,
            body_template=body_template,
            body_html=body_html,
            available_variables=json.dumps(available_variables) if available_variables else None,
            created_by=created_by
        )

        self.db.add(template)
        self.db.commit()
        return template

    def list_templates(self) -> list[NotificationTemplate]:
        """Liste les templates."""
        return self.db.query(NotificationTemplate).filter(
            NotificationTemplate.tenant_id == self.tenant_id,
            NotificationTemplate.is_active
        ).all()

    # ========================================================================
    # WEBHOOKS
    # ========================================================================

    def create_webhook(
        self,
        code: str,
        name: str,
        url: str,
        created_by: int | None = None,
        description: str | None = None,
        method: str = 'POST',
        headers: dict | None = None,
        auth_type: str | None = None,
        auth_config: dict | None = None
    ) -> WebhookEndpoint:
        """Crée un endpoint webhook."""
        # Chiffrer auth_config si présent (contient credentials sensibles)
        encrypted_auth_config = None
        if auth_config:
            encrypted_auth_config = encrypt_value(json.dumps(auth_config))

        webhook = WebhookEndpoint(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            url=url,
            method=method,
            headers=json.dumps(headers) if headers else None,
            auth_type=auth_type,
            auth_config=encrypted_auth_config,
            created_by=created_by
        )

        self.db.add(webhook)
        self.db.commit()
        return webhook

    def get_webhook_decrypted_config(self, webhook_id: int) -> dict | None:
        """Récupère la config auth déchiffrée d'un webhook."""
        webhook = self.db.query(WebhookEndpoint).filter(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.tenant_id == self.tenant_id
        ).first()

        if not webhook or not webhook.auth_config:
            return None

        try:
            decrypted = decrypt_value(webhook.auth_config)
            return json.loads(decrypted)
        except (ValueError, TypeError) as e:
            # Peut-être données anciennes non chiffrées
            logger.debug("Decryption failed for webhook %s, trying unencrypted: %s", webhook_id, e)
            try:
                return json.loads(webhook.auth_config)
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse auth_config for webhook %s: %s", webhook_id, e)
                return None

    def list_webhooks(self) -> list[WebhookEndpoint]:
        """Liste les webhooks."""
        return self.db.query(WebhookEndpoint).filter(
            WebhookEndpoint.tenant_id == self.tenant_id,
            WebhookEndpoint.is_active
        ).all()

    # ========================================================================
    # LOGGING
    # ========================================================================

    def _log(
        self,
        action: str,
        entity_type: str,
        entity_id: int | None,
        details: dict = None,
        success: bool = True,
        error_message: str = None
    ) -> None:
        """Crée une entrée de log."""
        log = TriggerLog(
            tenant_id=self.tenant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details) if details else None,
            success=success,
            error_message=error_message
        )
        self.db.add(log)


# ============================================================================
# FACTORY
# ============================================================================

def get_trigger_service(db: Session, tenant_id: str) -> TriggerService:
    """Factory pour créer un service de triggers."""
    return TriggerService(db, tenant_id)
