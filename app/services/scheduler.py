"""
AZALS - Service de tâches planifiées
Réinitialise les alertes RED tous les jours à 23h59
"""

import logging
import uuid

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# UUID système pour les opérations automatiques
SYSTEM_USER_UUID = "00000000-0000-0000-0000-000000000001"


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
            logger.info("[OK] Scheduler demarre - Reinitialisation RED a 23h59")

    def shutdown(self):
        """Arrete le scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("[STOP] Scheduler arrete")

    @staticmethod
    def reset_red_alerts():
        """
        Réinitialise les alertes RED.

        Règle:
        - Marquer toutes les décisions RED de la veille comme "réinitialisées"
        - Réactiver le workflow (remet completed_steps à vide)
        - Les tresoreries en deficit redeviennent RED
        """
        db = SessionLocal()
        try:
            logger.info("[...] Reinitialisation des alertes RED...")

            # Vérifier les décisions RED complétées
            # Note: reason est la colonne principale, is_fully_validated=1 signifie validé
            result = db.execute(text("""
                SELECT d.id, d.reason
                FROM decisions d
                WHERE d.level = 'RED'
                AND d.is_fully_validated = 1
                AND DATE(d.created_at) < CURRENT_DATE
            """))

            old_reds = result.fetchall()

            if old_reds:
                # Réinitialiser les étapes du workflow
                for red_id, _reason in old_reds:
                    # Supprimer les étapes complétées (table correcte: red_decision_workflows)
                    db.execute(text("""
                        DELETE FROM red_decision_workflows
                        WHERE decision_id = :decision_id
                    """), {"decision_id": str(red_id)})

                    # Réinitialiser is_fully_validated (0 = False)
                    db.execute(text("""
                        UPDATE decisions
                        SET is_fully_validated = 0
                        WHERE id = :decision_id AND level = 'RED'
                    """), {"decision_id": str(red_id)})

                db.commit()
                logger.info(f"[OK] {len(old_reds)} alerte(s) RED reinitialisee(s)")

                # Journaliser l'action avec UUID système valide
                for red_id, _reason in old_reds:
                    journal_id = str(uuid.uuid4())
                    db.execute(text("""
                        INSERT INTO core_audit_journal
                        (id, tenant_id, user_id, action, details, created_at)
                        VALUES (:id, :tenant_id, :user_id, :action, :details, CURRENT_TIMESTAMP)
                    """), {
                        "id": journal_id,
                        "tenant_id": "system",
                        "user_id": SYSTEM_USER_UUID,
                        "action": "RED_RESET_DAILY",
                        "details": f"Réinitialisation RED quotidienne - ID: {red_id}"
                    })

                db.commit()
            else:
                logger.info("[INFO] Aucune alerte RED a reinitialiser")

        except Exception as e:
            logger.error(f"[ERROR] Erreur reinitialisation RED: {e}")
            db.rollback()
        finally:
            db.close()


# Instance globale
scheduler_service = SchedulerService()
