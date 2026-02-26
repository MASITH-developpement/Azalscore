"""
AZALS - Module Email - Service
==============================
Service d'envoi d'emails transactionnels avec file d'attente et retry.
"""
from __future__ import annotations


import logging
import re
import smtplib
import ssl
import uuid
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_value, encrypt_value

from .models import EmailConfig, EmailLog, EmailQueue, EmailStatus, EmailTemplate, EmailType
from .schemas import (
    BulkSendRequest,
    BulkSendResponse,
    EmailConfigCreate,
    EmailConfigResponse,
    EmailConfigUpdate,
    EmailDashboard,
    EmailLogResponse,
    EmailStats,
    EmailStatsByType,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    SendEmailRequest,
    SendEmailResponse,
)

logger = logging.getLogger(__name__)


class EmailService:
    """Service pour la gestion des emails transactionnels."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    def get_config(self) -> EmailConfig | None:
        """Récupère la configuration email du tenant."""
        return self.db.query(EmailConfig).filter(
            EmailConfig.tenant_id == self.tenant_id
        ).first()

    def create_config(self, data: EmailConfigCreate) -> EmailConfig:
        """Crée la configuration email."""
        config = EmailConfig(
            tenant_id=self.tenant_id,
            smtp_host=data.smtp_host,
            smtp_port=data.smtp_port,
            smtp_username=data.smtp_username,
            smtp_password_encrypted=encrypt_value(data.smtp_password) if data.smtp_password else None,
            smtp_use_tls=data.smtp_use_tls,
            smtp_use_ssl=data.smtp_use_ssl,
            provider=data.provider,
            api_key_encrypted=encrypt_value(data.api_key) if data.api_key else None,
            api_endpoint=data.api_endpoint,
            from_email=data.from_email,
            from_name=data.from_name,
            reply_to_email=data.reply_to_email,
            max_emails_per_hour=data.max_emails_per_hour,
            max_emails_per_day=data.max_emails_per_day,
            track_opens=data.track_opens,
            track_clicks=data.track_clicks
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update_config(self, data: EmailConfigUpdate) -> EmailConfig | None:
        """Met à jour la configuration email."""
        config = self.get_config()
        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if 'smtp_password' in update_data and update_data['smtp_password']:
            update_data['smtp_password_encrypted'] = encrypt_value(update_data.pop('smtp_password'))
        elif 'smtp_password' in update_data:
            del update_data['smtp_password']

        if 'api_key' in update_data and update_data['api_key']:
            update_data['api_key_encrypted'] = encrypt_value(update_data.pop('api_key'))
        elif 'api_key' in update_data:
            del update_data['api_key']

        for key, value in update_data.items():
            setattr(config, key, value)

        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        return config

    def verify_config(self) -> tuple[bool, str]:
        """Vérifie la configuration email en envoyant un email test."""
        config = self.get_config()
        if not config:
            return False, "Configuration non trouvée"

        if config.provider == "smtp":
            return self._verify_smtp(config)
        else:
            return False, f"Provider {config.provider} non supporté pour la vérification"

    def _verify_smtp(self, config: EmailConfig) -> tuple[bool, str]:
        """Vérifie la connexion SMTP."""
        if config.smtp_use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, context=context)
        else:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port)
            if config.smtp_use_tls:
                server.starttls()

        if config.smtp_username and config.smtp_password_encrypted:
            password = decrypt_value(config.smtp_password_encrypted)
            server.login(config.smtp_username, password)

        server.quit()

        config.is_verified = True
        config.last_verified_at = datetime.utcnow()
        self.db.commit()

        return True, "Configuration SMTP valide"

    # =========================================================================
    # TEMPLATES
    # =========================================================================

    def get_template(self, template_id: str) -> EmailTemplate | None:
        """Récupère un template par ID."""
        return self.db.query(EmailTemplate).filter(
            EmailTemplate.id == template_id,
            or_(EmailTemplate.tenant_id == self.tenant_id, EmailTemplate.tenant_id.is_(None))
        ).first()

    def get_template_by_code(self, code: str, language: str = "fr") -> EmailTemplate | None:
        """Récupère un template par code."""
        # D'abord chercher un template spécifique au tenant
        template = self.db.query(EmailTemplate).filter(
            EmailTemplate.code == code,
            EmailTemplate.tenant_id == self.tenant_id,
            EmailTemplate.language == language,
            EmailTemplate.is_active
        ).first()

        if not template:
            # Sinon chercher un template global
            template = self.db.query(EmailTemplate).filter(
                EmailTemplate.code == code,
                EmailTemplate.tenant_id.is_(None),
                EmailTemplate.language == language,
                EmailTemplate.is_active
            ).first()

        return template

    def create_template(self, data: EmailTemplateCreate) -> EmailTemplate:
        """Crée un template email."""
        template = EmailTemplate(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            email_type=data.email_type,
            subject=data.subject,
            body_html=data.body_html,
            body_text=data.body_text,
            variables=data.variables,
            language=data.language
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def update_template(self, template_id: str, data: EmailTemplateUpdate) -> EmailTemplate | None:
        """Met à jour un template."""
        template = self.get_template(template_id)
        if not template or (template.tenant_id and template.tenant_id != self.tenant_id):
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)

        template.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(template)
        return template

    def list_templates(self, email_type: EmailType | None = None) -> list[EmailTemplate]:
        """Liste les templates disponibles."""
        query = self.db.query(EmailTemplate).filter(
            or_(EmailTemplate.tenant_id == self.tenant_id, EmailTemplate.tenant_id.is_(None))
        )
        if email_type:
            query = query.filter(EmailTemplate.email_type == email_type)
        return query.order_by(EmailTemplate.code).all()

    # =========================================================================
    # ENVOI D'EMAILS
    # =========================================================================

    def send_email(self, data: SendEmailRequest, created_by: str | None = None) -> SendEmailResponse:
        """Envoie un email (mise en file d'attente)."""
        config = self.get_config()
        if not config or not config.is_active:
            raise ValueError("Configuration email non active")

        # Construire le contenu
        subject = data.subject
        body_html = data.body_html
        body_text = data.body_text

        if data.template_code:
            template = self.get_template_by_code(data.template_code)
            if template:
                subject = self._render_template(template.subject, data.variables)
                body_html = self._render_template(template.body_html, data.variables)
                body_text = self._render_template(template.body_text, data.variables) if template.body_text else None

        if not subject:
            raise ValueError("Sujet requis")

        # Créer le log
        email_log = EmailLog(
            tenant_id=self.tenant_id,
            email_type=data.email_type,
            to_email=data.to_email,
            to_name=data.to_name,
            cc_emails=data.cc_emails,
            bcc_emails=data.bcc_emails,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            variables_used=data.variables,
            attachments=data.attachments,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            priority=data.priority,
            created_by=created_by,
            status=EmailStatus.PENDING
        )
        self.db.add(email_log)
        self.db.flush()

        # Ajouter à la file d'attente
        schedule_at = data.schedule_at or datetime.utcnow()
        queue_item = EmailQueue(
            email_log_id=email_log.id,
            tenant_id=self.tenant_id,
            priority=data.priority,
            scheduled_at=schedule_at
        )
        self.db.add(queue_item)

        email_log.status = EmailStatus.QUEUED
        email_log.queued_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(email_log)

        return SendEmailResponse(
            id=str(email_log.id),
            status=email_log.status,
            to_email=email_log.to_email,
            subject=email_log.subject,
            queued_at=email_log.queued_at,
            message="Email mis en file d'attente"
        )

    def send_bulk(self, data: BulkSendRequest) -> BulkSendResponse:
        """Envoi en masse."""
        email_ids = []
        failed = 0

        for recipient in data.recipients:
            variables = {**data.base_variables, **recipient.get('variables', {})}
            request = SendEmailRequest(
                to_email=recipient['email'],
                to_name=recipient.get('name'),
                email_type=data.email_type,
                template_code=data.template_code,
                variables=variables,
                priority=data.priority
            )
            response = self.send_email(request)
            email_ids.append(response.id)

        return BulkSendResponse(
            total=len(data.recipients),
            queued=len(email_ids),
            failed=failed,
            email_ids=email_ids
        )

    def _render_template(self, template: str, variables: dict[str, Any]) -> str:
        """Rend un template avec les variables."""
        if not template:
            return ""

        result = template
        for key, value in variables.items():
            pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
            result = re.sub(pattern, str(value) if value is not None else '', result)

        return result

    # =========================================================================
    # TRAITEMENT FILE D'ATTENTE
    # =========================================================================

    def process_queue(self, batch_size: int = 10) -> int:
        """Traite la file d'attente d'emails."""
        now = datetime.utcnow()
        processed = 0

        # Récupérer les emails à envoyer
        queue_items = self.db.query(EmailQueue).filter(
            EmailQueue.tenant_id == self.tenant_id,
            EmailQueue.scheduled_at <= now,
            EmailQueue.locked_by.is_(None)
        ).order_by(
            EmailQueue.priority,
            EmailQueue.scheduled_at
        ).limit(batch_size).all()

        worker_id = str(uuid.uuid4())[:8]

        for item in queue_items:
            # Lock l'item
            item.locked_by = worker_id
            item.locked_at = now
            self.db.commit()

            # SÉCURITÉ: Filtrer par tenant_id
            email_log = self.db.query(EmailLog).filter(
                EmailLog.tenant_id == self.tenant_id,
                EmailLog.id == item.email_log_id
            ).first()
            if email_log:
                success = self._send_email_now(email_log)
                if success:
                    self.db.delete(item)
                    processed += 1
                else:
                    item.attempts += 1
                    item.last_attempt_at = now
                    item.next_attempt_at = now + timedelta(minutes=5 * item.attempts)
                    item.locked_by = None
                    item.locked_at = None

                    if item.attempts >= email_log.max_retries:
                        email_log.status = EmailStatus.FAILED
                        email_log.failed_at = now
                        self.db.delete(item)

            self.db.commit()

        return processed

    def _send_email_now(self, email_log: EmailLog) -> bool:
        """Envoie immédiatement un email."""
        config = self.get_config()
        if not config:
            return False

        email_log.status = EmailStatus.SENDING
        self.db.commit()

        if config.provider == "smtp":
            success = self._send_via_smtp(config, email_log)
        else:
            logger.warning("Provider %s non implémenté", config.provider)
            success = False

        if success:
            email_log.status = EmailStatus.SENT
            email_log.sent_at = datetime.utcnow()
            email_log.provider = config.provider
            self.db.commit()
            return True
        else:
            email_log.retry_count += 1
            self.db.commit()
            return False

    def _send_via_smtp(self, config: EmailConfig, email_log: EmailLog) -> bool:
        """Envoie via SMTP."""
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{config.from_name} <{config.from_email}>"
        msg['To'] = email_log.to_email
        msg['Subject'] = email_log.subject

        if config.reply_to_email:
            msg['Reply-To'] = config.reply_to_email

        if email_log.cc_emails:
            msg['Cc'] = ', '.join(email_log.cc_emails)

        if email_log.body_text:
            msg.attach(MIMEText(email_log.body_text, 'plain', 'utf-8'))

        if email_log.body_html:
            msg.attach(MIMEText(email_log.body_html, 'html', 'utf-8'))

        recipients = [email_log.to_email]
        if email_log.cc_emails:
            recipients.extend(email_log.cc_emails)
        if email_log.bcc_emails:
            recipients.extend(email_log.bcc_emails)

        if config.smtp_use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, context=context)
        else:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port)
            if config.smtp_use_tls:
                server.starttls()

        if config.smtp_username and config.smtp_password_encrypted:
            password = decrypt_value(config.smtp_password_encrypted)
            server.login(config.smtp_username, password)

        server.sendmail(config.from_email, recipients, msg.as_string())
        server.quit()

        return True

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_stats(self, start_date: datetime, end_date: datetime) -> EmailStats:
        """Récupère les statistiques d'emails."""
        base_query = self.db.query(EmailLog).filter(
            EmailLog.tenant_id == self.tenant_id,
            EmailLog.created_at >= start_date,
            EmailLog.created_at < end_date
        )

        total_sent = base_query.filter(EmailLog.status.in_([
            EmailStatus.SENT, EmailStatus.DELIVERED, EmailStatus.OPENED, EmailStatus.CLICKED
        ])).count()
        total_delivered = base_query.filter(EmailLog.status.in_([
            EmailStatus.DELIVERED, EmailStatus.OPENED, EmailStatus.CLICKED
        ])).count()
        total_opened = base_query.filter(EmailLog.status.in_([
            EmailStatus.OPENED, EmailStatus.CLICKED
        ])).count()
        total_clicked = base_query.filter(EmailLog.status == EmailStatus.CLICKED).count()
        total_bounced = base_query.filter(EmailLog.status == EmailStatus.BOUNCED).count()
        total_failed = base_query.filter(EmailLog.status == EmailStatus.FAILED).count()

        return EmailStats(
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_opened=total_opened,
            total_clicked=total_clicked,
            total_bounced=total_bounced,
            total_failed=total_failed,
            delivery_rate=round(total_delivered / total_sent * 100, 2) if total_sent > 0 else 0,
            open_rate=round(total_opened / total_delivered * 100, 2) if total_delivered > 0 else 0,
            click_rate=round(total_clicked / total_opened * 100, 2) if total_opened > 0 else 0,
            bounce_rate=round(total_bounced / total_sent * 100, 2) if total_sent > 0 else 0
        )

    def get_dashboard(self) -> EmailDashboard:
        """Dashboard email complet."""
        config = self.get_config()
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        stats_today = self.get_stats(today_start, now)
        stats_month = self.get_stats(month_start, now)

        # Stats par type
        by_type = []
        for email_type in EmailType:
            count = self.db.query(EmailLog).filter(
                EmailLog.tenant_id == self.tenant_id,
                EmailLog.email_type == email_type,
                EmailLog.created_at >= month_start
            ).count()
            if count > 0:
                delivered = self.db.query(EmailLog).filter(
                    EmailLog.tenant_id == self.tenant_id,
                    EmailLog.email_type == email_type,
                    EmailLog.created_at >= month_start,
                    EmailLog.status.in_([EmailStatus.DELIVERED, EmailStatus.OPENED, EmailStatus.CLICKED])
                ).count()
                by_type.append(EmailStatsByType(
                    email_type=email_type,
                    count=count,
                    delivered=delivered,
                    opened=0,
                    clicked=0,
                    bounced=0
                ))

        # Échecs récents
        recent_failures = self.db.query(EmailLog).filter(
            EmailLog.tenant_id == self.tenant_id,
            EmailLog.status == EmailStatus.FAILED
        ).order_by(EmailLog.failed_at.desc()).limit(10).all()

        # Taille file d'attente
        queue_size = self.db.query(EmailQueue).filter(
            EmailQueue.tenant_id == self.tenant_id
        ).count()

        return EmailDashboard(
            config=EmailConfigResponse.model_validate(config) if config else None,
            stats_today=stats_today,
            stats_month=stats_month,
            by_type=by_type,
            recent_failures=[EmailLogResponse.model_validate(f) for f in recent_failures],
            queue_size=queue_size
        )

    # =========================================================================
    # LOGS
    # =========================================================================

    def get_log(self, log_id: str) -> EmailLog | None:
        """Récupère un log email."""
        return self.db.query(EmailLog).filter(
            EmailLog.id == log_id,
            EmailLog.tenant_id == self.tenant_id
        ).first()

    def list_logs(
        self,
        email_type: EmailType | None = None,
        status: EmailStatus | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[EmailLog], int]:
        """Liste les logs emails."""
        query = self.db.query(EmailLog).filter(EmailLog.tenant_id == self.tenant_id)

        if email_type:
            query = query.filter(EmailLog.email_type == email_type)
        if status:
            query = query.filter(EmailLog.status == status)
        if start_date:
            query = query.filter(EmailLog.created_at >= start_date)
        if end_date:
            query = query.filter(EmailLog.created_at < end_date)

        total = query.count()
        items = query.order_by(EmailLog.created_at.desc()).offset(skip).limit(limit).all()

        return items, total


def get_email_service(db: Session, tenant_id: str, user_id: str = None) -> EmailService:
    """Factory pour le service email."""
    return EmailService(db, tenant_id, user_id)
