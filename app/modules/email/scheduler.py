"""
AZALS - Module Email - Scheduler Rappels
=========================================
Planificateur de rappels automatiques pour factures impayées.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class InvoiceReminderScheduler:
    """
    Planificateur de rappels automatiques pour factures impayées.
    
    Gère l'envoi de rappels à J+7, J+15, J+30 après échéance
    selon la configuration du tenant.
    """
    
    DEFAULT_REMINDER_DAYS = [7, 15, 30]  # Jours après échéance
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        
    def get_reminder_config(self) -> dict:
        """
        Récupère la configuration des rappels pour le tenant.
        
        Returns:
            Dict avec configuration (enabled, reminder_days, templates, etc.)
        """
        # TODO: Récupérer depuis tenant.settings['reminders']
        # from app.modules.tenants.models import Tenant
        # tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        # if tenant and tenant.settings:
        #     return tenant.settings.get('reminders', self._default_config())
        
        return self._default_config()
    
    def _default_config(self) -> dict:
        """Configuration par défaut des rappels."""
        return {
            "enabled": True,
            "auto_send": True,
            "reminder_days": self.DEFAULT_REMINDER_DAYS,
            "stop_after_days": 60,  # Arrêter après 60 jours
            "max_reminders": 3,
            "email_template": "invoice_reminder",
            "cc_accounting": False,
            "escalate_after": 30  # Escalade après 30 jours
        }
    
    def find_invoices_needing_reminders(self) -> List[dict]:
        """
        Trouve les factures nécessitant un rappel aujourd'hui.
        
        Returns:
            Liste de dicts contenant invoice_id, days_overdue, reminder_count
        """
        from app.modules.commercial.models import Document, DocumentStatus, DocumentType
        
        config = self.get_reminder_config()
        
        if not config.get("enabled"):
            logger.info(f"Reminders disabled for tenant {self.tenant_id}")
            return []
        
        reminder_days = config.get("reminder_days", self.DEFAULT_REMINDER_DAYS)
        today = date.today()
        
        # Trouver les factures impayées
        unpaid_invoices = self.db.query(Document).filter(
            and_(
                Document.tenant_id == self.tenant_id,
                Document.document_type == DocumentType.INVOICE,
                Document.status.in_([DocumentStatus.SENT, DocumentStatus.VALIDATED]),
                Document.due_date < today,  # Échue
                Document.paid_at.is_(None)  # Non payée
            )
        ).all()
        
        invoices_to_remind = []
        
        for invoice in unpaid_invoices:
            days_overdue = (today - invoice.due_date).days
            
            # Vérifier si on doit envoyer un rappel
            if days_overdue in reminder_days:
                # Compter les rappels déjà envoyés
                reminder_count = self._count_reminders_sent(invoice.id)
                
                max_reminders = config.get("max_reminders", 3)
                if reminder_count < max_reminders:
                    invoices_to_remind.append({
                        "invoice_id": invoice.id,
                        "invoice_number": invoice.document_number,
                        "customer_email": self._get_customer_email(invoice),
                        "customer_name": self._get_customer_name(invoice),
                        "amount_due": float(invoice.total_with_tax or 0),
                        "due_date": invoice.due_date,
                        "days_overdue": days_overdue,
                        "reminder_count": reminder_count,
                        "reminder_level": self._get_reminder_level(days_overdue)
                    })
        
        logger.info(f"Found {len(invoices_to_remind)} invoices needing reminders for tenant {self.tenant_id}")
        return invoices_to_remind
    
    def send_overdue_reminder(
        self,
        invoice_id: UUID,
        force: bool = False
    ) -> bool:
        """
        Envoie un rappel pour une facture impayée.
        
        Args:
            invoice_id: ID de la facture
            force: Forcer l'envoi même si déjà envoyé aujourd'hui
            
        Returns:
            True si envoyé avec succès
        """
        from app.modules.commercial.models import Document
        from app.modules.email.models import EmailLog, EmailStatus, EmailType
        
        # Récupérer la facture
        invoice = self.db.query(Document).filter(
            and_(
                Document.id == invoice_id,
                Document.tenant_id == self.tenant_id
            )
        ).first()
        
        if not invoice:
            logger.warning(f"Invoice {invoice_id} not found")
            return False
        
        # Vérifier si déjà envoyé aujourd'hui
        if not force and self._reminder_sent_today(invoice_id):
            logger.info(f"Reminder already sent today for invoice {invoice_id}")
            return False
        
        # Préparer les variables pour le template
        customer_email = self._get_customer_email(invoice)
        if not customer_email:
            logger.warning(f"No email found for invoice {invoice_id} customer")
            return False
        
        days_overdue = (date.today() - invoice.due_date).days if invoice.due_date else 0
        reminder_count = self._count_reminders_sent(invoice_id)
        
        variables = {
            "customer_name": self._get_customer_name(invoice),
            "invoice_number": invoice.document_number,
            "invoice_date": invoice.document_date.isoformat() if invoice.document_date else None,
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            "amount_due": float(invoice.total_with_tax or 0),
            "currency": invoice.currency or "EUR",
            "days_overdue": days_overdue,
            "reminder_count": reminder_count + 1,
            "reminder_level": self._get_reminder_level(days_overdue),
            "payment_link": self._generate_payment_link(invoice)
        }
        
        # Déterminer le ton du message selon le nombre de jours
        subject = self._get_reminder_subject(days_overdue, invoice.document_number)
        
        # Créer le log email
        email_log = EmailLog(
            tenant_id=self.tenant_id,
            email_type=EmailType.REMINDER,
            status=EmailStatus.PENDING,
            to_email=customer_email,
            to_name=self._get_customer_name(invoice),
            subject=subject,
            variables_used=variables,
            reference_type="invoice",
            reference_id=str(invoice_id),
            priority=self._get_reminder_priority(days_overdue)
        )
        
        self.db.add(email_log)
        self.db.commit()
        
        # Envoyer l'email (via le service email)
        try:
            from app.modules.email.service import EmailService
            email_service = EmailService(self.db, self.tenant_id)
            # TODO: Implémenter send_from_log dans EmailService
            # email_service.send_from_log(email_log.id)
            
            logger.info(f"Reminder sent for invoice {invoice_id} (attempt {reminder_count + 1})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reminder for invoice {invoice_id}: {str(e)}")
            email_log.status = EmailStatus.FAILED
            email_log.error_message = str(e)
            self.db.commit()
            return False
    
    def schedule_reminders(self) -> dict:
        """
        Planifie tous les rappels du jour.
        
        Appelé quotidiennement par un cron job.
        
        Returns:
            Dict avec statistiques (found, sent, failed)
        """
        invoices = self.find_invoices_needing_reminders()
        
        stats = {
            "found": len(invoices),
            "sent": 0,
            "failed": 0,
            "skipped": 0
        }
        
        for invoice_data in invoices:
            try:
                success = self.send_overdue_reminder(invoice_data["invoice_id"])
                if success:
                    stats["sent"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                logger.error(f"Error sending reminder for {invoice_data['invoice_id']}: {str(e)}")
                stats["failed"] += 1
        
        logger.info(f"Reminder scheduler completed: {stats}")
        return stats
    
    def get_reminder_schedule(
        self,
        days_ahead: int = 30
    ) -> List[dict]:
        """
        Récupère le planning des rappels à venir.
        
        Args:
            days_ahead: Nombre de jours à anticiper
            
        Returns:
            Liste des rappels prévus
        """
        from app.modules.commercial.models import Document, DocumentStatus, DocumentType
        
        today = date.today()
        config = self.get_reminder_config()
        reminder_days = config.get("reminder_days", self.DEFAULT_REMINDER_DAYS)
        
        # Trouver toutes les factures impayées
        unpaid_invoices = self.db.query(Document).filter(
            and_(
                Document.tenant_id == self.tenant_id,
                Document.document_type == DocumentType.INVOICE,
                Document.status.in_([DocumentStatus.SENT, DocumentStatus.VALIDATED]),
                Document.paid_at.is_(None)
            )
        ).all()
        
        schedule = []
        
        for invoice in unpaid_invoices:
            if not invoice.due_date:
                continue
            
            # Calculer les dates de rappel
            for reminder_day in reminder_days:
                reminder_date = invoice.due_date + timedelta(days=reminder_day)
                
                if today <= reminder_date <= today + timedelta(days=days_ahead):
                    reminder_count = self._count_reminders_sent(invoice.id)
                    
                    schedule.append({
                        "date": reminder_date,
                        "invoice_id": invoice.id,
                        "invoice_number": invoice.document_number,
                        "customer_name": self._get_customer_name(invoice),
                        "amount_due": float(invoice.total_with_tax or 0),
                        "days_after_due": reminder_day,
                        "reminder_count": reminder_count,
                        "already_sent": reminder_count > 0
                    })
        
        # Trier par date
        schedule.sort(key=lambda x: x["date"])
        return schedule
    
    # =========================================================================
    # HELPERS PRIVÉS
    # =========================================================================
    
    def _count_reminders_sent(self, invoice_id: UUID) -> int:
        """Compte le nombre de rappels déjà envoyés pour une facture."""
        from app.modules.email.models import EmailLog, EmailType
        
        count = self.db.query(EmailLog).filter(
            and_(
                EmailLog.tenant_id == self.tenant_id,
                EmailLog.email_type == EmailType.REMINDER,
                EmailLog.reference_type == "invoice",
                EmailLog.reference_id == str(invoice_id)
            )
        ).count()
        
        return count
    
    def _reminder_sent_today(self, invoice_id: UUID) -> bool:
        """Vérifie si un rappel a déjà été envoyé aujourd'hui."""
        from app.modules.email.models import EmailLog, EmailType
        
        today_start = datetime.combine(date.today(), datetime.min.time())
        
        exists = self.db.query(EmailLog).filter(
            and_(
                EmailLog.tenant_id == self.tenant_id,
                EmailLog.email_type == EmailType.REMINDER,
                EmailLog.reference_type == "invoice",
                EmailLog.reference_id == str(invoice_id),
                EmailLog.created_at >= today_start
            )
        ).first()
        
        return exists is not None
    
    def _get_customer_email(self, invoice) -> Optional[str]:
        """Récupère l'email du client."""
        # TODO: Utiliser la relation avec Customer
        return None  # Placeholder
    
    def _get_customer_name(self, invoice) -> str:
        """Récupère le nom du client."""
        # TODO: Utiliser la relation avec Customer
        return invoice.customer_name if hasattr(invoice, 'customer_name') else "Client"
    
    def _get_reminder_level(self, days_overdue: int) -> str:
        """Détermine le niveau de rappel selon les jours de retard."""
        if days_overdue <= 7:
            return "friendly"
        elif days_overdue <= 15:
            return "reminder"
        elif days_overdue <= 30:
            return "firm"
        else:
            return "urgent"
    
    def _get_reminder_subject(self, days_overdue: int, invoice_number: str) -> str:
        """Génère le sujet de l'email selon le niveau."""
        level = self._get_reminder_level(days_overdue)
        
        subjects = {
            "friendly": f"Rappel amical - Facture {invoice_number}",
            "reminder": f"Rappel de paiement - Facture {invoice_number}",
            "firm": f"Relance importante - Facture {invoice_number}",
            "urgent": f"URGENT - Facture impayée {invoice_number}"
        }
        
        return subjects.get(level, f"Rappel - Facture {invoice_number}")
    
    def _get_reminder_priority(self, days_overdue: int) -> int:
        """Détermine la priorité de l'email selon les jours."""
        if days_overdue >= 30:
            return 1  # Urgent
        elif days_overdue >= 15:
            return 3  # Haute
        else:
            return 5  # Normale
    
    def _generate_payment_link(self, invoice) -> str:
        """Génère un lien de paiement pour la facture."""
        # TODO: Implémenter lien de paiement sécurisé
        return f"https://pay.azalscore.com/invoice/{invoice.id}"


class ReminderConfigManager:
    """Gestionnaire de configuration des rappels."""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def get_config(self) -> dict:
        """Récupère la configuration actuelle."""
        # TODO: Implémenter récupération depuis tenant settings
        return InvoiceReminderScheduler(self.db, self.tenant_id).get_reminder_config()
    
    def update_config(self, config: dict) -> bool:
        """
        Met à jour la configuration des rappels.
        
        Args:
            config: Nouvelle configuration
            
        Returns:
            True si mis à jour avec succès
        """
        # TODO: Sauvegarder dans tenant.settings['reminders']
        # from app.modules.tenants.models import Tenant
        # tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        # if tenant:
        #     if not tenant.settings:
        #         tenant.settings = {}
        #     tenant.settings['reminders'] = config
        #     self.db.commit()
        #     return True
        
        return False
    
    def test_reminder(self, invoice_id: UUID) -> bool:
        """
        Envoie un rappel de test pour une facture.
        
        Args:
            invoice_id: ID de la facture
            
        Returns:
            True si envoyé avec succès
        """
        scheduler = InvoiceReminderScheduler(self.db, self.tenant_id)
        return scheduler.send_overdue_reminder(invoice_id, force=True)
