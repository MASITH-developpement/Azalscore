"""
AZALS - Service de tâches planifiées
Réinitialise les alertes RED tous les jours à 23h59
"""

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service de gestion des tâches planifiées."""
    
    def __init__(self):
        self.scheduler = None
    
    def start(self):
        """Démarre le scheduler."""
        if self.scheduler is None:
            self.scheduler = BackgroundScheduler(daemon=True)
            
            # Tâche quotidienne : réinitialiser les RED à 23h59
            self.scheduler.add_job(
                self.reset_red_alerts,
                trigger=CronTrigger(hour=23, minute=59),
                id='reset_red_alerts_daily',
                name='Reset RED alerts daily',
                misfire_grace_time=600,  # Tolérance 10 minutes
                coalesce=True,
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("✅ Scheduler démarré - Réinitialisation RED à 23h59")
    
    def shutdown(self):
        """Arrête le scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("⏹️  Scheduler arrêté")
    
    @staticmethod
    def reset_red_alerts():
        """
        Réinitialise les alertes RED.
        
        Règle: 
        - Marquer toutes les décisions RED de la veille comme "réinitialisées"
        - Réactiver le workflow (remet completed_steps à vide)
        - Les trésoreries en déficit redeviennent 🔴
        """
        db = SessionLocal()
        try:
            logger.info("🔄 Réinitialisation des alertes RED...")
            
            # Vérifier les décisions RED complétées
            result = db.execute(text("""
                SELECT d.id, d.decision_reason
                FROM decisions d
                WHERE d.level = 'RED'
                AND d.is_fully_validated = TRUE
                AND DATE(d.created_at) < CURRENT_DATE
            """))
            
            old_reds = result.fetchall()
            
            if old_reds:
                # Réinitialiser les étapes du workflow
                for red_id, reason in old_reds:
                    # Supprimer les étapes complétées
                    db.execute(text("""
                        DELETE FROM red_workflow_steps 
                        WHERE decision_id = :decision_id
                    """), {"decision_id": red_id})
                    
                    # Réinitialiser is_fully_validated
                    db.execute(text("""
                        UPDATE decisions 
                        SET is_fully_validated = FALSE
                        WHERE id = :decision_id AND level = 'RED'
                    """), {"decision_id": red_id})
                
                db.commit()
                logger.info(f"✅ {len(old_reds)} alerte(s) RED réinitialisée(s)")
                
                # Journaliser l'action
                for red_id, reason in old_reds:
                    db.execute(text("""
                        INSERT INTO core_audit_journal
                        (tenant_id, user_id, action, details, created_at)
                        VALUES (:tenant_id, :user_id, :action, :details, CURRENT_TIMESTAMP)
                    """), {
                        "tenant_id": "system",
                        "user_id": 1,  # Utilisateur système
                        "action": "RED_RESET_DAILY",
                        "details": f"Réinitialisation RED quotidienne - ID: {red_id}"
                    })
                
                db.commit()
            else:
                logger.info("ℹ️  Aucune alerte RED à réinitialiser")
        
        except Exception as e:
            logger.error(f"❌ Erreur réinitialisation RED: {e}")
            db.rollback()
        finally:
            db.close()


# Instance globale
scheduler_service = SchedulerService()
