"""
AZALS - Service de tâches planifiées
Réinitialise les alertes RED tous les jours à 23h59
"""

import logging
import uuid

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from app.core.database import get_db_for_scheduler, get_db_for_platform_operation

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
            # P1 SÉCURITÉ: Configuration avec limites pour éviter DoS
            # - max_instances: évite l'accumulation de jobs si un job prend trop de temps
            # - job_defaults: timeout implicite via coalesce
            self.scheduler = BackgroundScheduler(
                daemon=True,
                timezone='Europe/Paris',
                job_defaults={
                    'coalesce': True,  # P1: Fusionne les jobs manqués en un seul
                    'max_instances': 1,  # P1: Un seul job du même type à la fois
                    'misfire_grace_time': 600  # P1: Tolérance 10 minutes
                }
            )

            # Tâche quotidienne : réinitialiser les RED à 23h59
            # P1: misfire_grace_time et coalesce sont maintenant dans job_defaults
            self.scheduler.add_job(
                self.reset_red_alerts,
                trigger=CronTrigger(hour=23, minute=59, timezone='Europe/Paris'),
                id='reset_red_alerts_daily',
                name='Reset RED alerts daily',
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

        SÉCURITÉ P0: Traitement PAR TENANT avec RLS context pour garantir l'isolation multi-tenant.
        """
        # P0 SÉCURITÉ: Utiliser get_db_for_platform_operation pour la requête cross-tenant
        platform_db = get_db_for_platform_operation(caller="scheduler.reset_red_alerts")
        try:
            logger.info("[...] Reinitialisation des alertes RED...")

            # P0 SÉCURITÉ: Requête plateforme pour lister les RED de tous les tenants
            # Note: reason est la colonne principale, is_fully_validated=1 signifie validé
            result = platform_db.execute(text("""
                SELECT d.id, d.tenant_id, d.reason
                FROM decisions d
                WHERE d.level = 'RED'
                AND d.is_fully_validated = 1
                AND DATE(d.created_at) < CURRENT_DATE
            """))

            old_reds = result.fetchall()
            platform_db.close()  # Fermer la session plateforme dès que possible

            if old_reds:
                # P0 SÉCURITÉ: Grouper par tenant pour traitement avec RLS context
                from collections import defaultdict
                reds_by_tenant: dict[str, list] = defaultdict(list)
                for red_id, tenant_id, reason in old_reds:
                    reds_by_tenant[tenant_id].append((red_id, reason))

                total_reset = 0
                for tenant_id, tenant_reds in reds_by_tenant.items():
                    # P0 SÉCURITÉ: Session avec RLS context pour ce tenant
                    tenant_db = get_db_for_scheduler(tenant_id)
                    try:
                        for red_id, _reason in tenant_reds:
                            # Supprimer les étapes complétées (RLS assure l'isolation)
                            tenant_db.execute(text("""
                                DELETE FROM red_decision_workflows
                                WHERE decision_id = :decision_id
                            """), {"decision_id": str(red_id)})

                            # Réinitialiser is_fully_validated (0 = False)
                            tenant_db.execute(text("""
                                UPDATE decisions
                                SET is_fully_validated = 0
                                WHERE id = :decision_id
                                AND level = 'RED'
                            """), {"decision_id": str(red_id)})

                            # Journal dans le contexte tenant (RLS assure l'isolation)
                            journal_id = str(uuid.uuid4())
                            tenant_db.execute(text("""
                                INSERT INTO core_audit_journal
                                (id, tenant_id, user_id, action, details, created_at)
                                VALUES (:id, :tenant_id, :user_id, :action, :details, CURRENT_TIMESTAMP)
                            """), {
                                "id": journal_id,
                                "tenant_id": tenant_id,
                                "user_id": SYSTEM_USER_UUID,
                                "action": "RED_RESET_DAILY",
                                "details": f"Réinitialisation RED quotidienne - ID: {red_id}"
                            })

                        tenant_db.commit()
                        total_reset += len(tenant_reds)
                        logger.debug("[OK] Tenant %s: %d RED réinitialisées", tenant_id, len(tenant_reds))
                    except Exception as e:
                        logger.error("[ERROR] Tenant %s: erreur reset RED: %s", tenant_id, e)
                        tenant_db.rollback()
                    finally:
                        tenant_db.close()

                logger.info("[OK] %s alerte(s) RED reinitialisee(s) sur %d tenants", total_reset, len(reds_by_tenant))
            else:
                logger.info("[INFO] Aucune alerte RED a reinitialiser")

        except Exception as e:
            logger.error("[ERROR] Erreur reinitialisation RED: %s", e)
        finally:
            # S'assurer que la session plateforme est fermée
            try:
                platform_db.close()
            except Exception:
                pass


# Instance globale
scheduler_service = SchedulerService()
