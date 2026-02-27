"""
AZALS MODULE - Réseaux Sociaux - Scheduler
==========================================
Tâches planifiées pour la synchronisation automatique des métriques
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import get_db_for_scheduler, get_db_for_platform_operation
from .models import MarketingPlatform, SocialNetworkConfig
from .config_service import ConfigService
from .service import SocialNetworksService

logger = logging.getLogger(__name__)

# Configuration du scheduler
SYNC_INTERVAL_HOURS = 6  # Synchronisation toutes les 6 heures
SYNC_DAYS_BACK = 7  # Synchroniser les 7 derniers jours


class SocialNetworkScheduler:
    """Scheduler pour la synchronisation automatique des métriques."""

    _instance: Optional["SocialNetworkScheduler"] = None
    _running: bool = False
    _task: Optional[asyncio.Task] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "SocialNetworkScheduler":
        """Retourne l'instance singleton du scheduler."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self):
        """Démarre le scheduler."""
        if self._running:
            logger.warning("[Scheduler] Déjà en cours d'exécution")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"[Scheduler] Démarré - Intervalle: {SYNC_INTERVAL_HOURS}h")

    async def stop(self):
        """Arrête le scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[Scheduler] Arrêté")

    async def _run_loop(self):
        """Boucle principale du scheduler."""
        while self._running:
            try:
                await self._sync_all_tenants()
            except Exception as e:
                logger.error(f"[Scheduler] Erreur dans la boucle: {e}")

            # Attendre avant la prochaine sync
            await asyncio.sleep(SYNC_INTERVAL_HOURS * 3600)

    async def _sync_all_tenants(self):
        """Synchronise toutes les plateformes pour tous les tenants."""
        logger.info("[Scheduler] Début de la synchronisation globale")

        # P0 SÉCURITÉ: Session plateforme pour lister les tenants (sans RLS intentionnel)
        db: Session = get_db_for_platform_operation()
        try:
            # Récupérer tous les tenants avec des configs actives
            tenant_ids = db.query(SocialNetworkConfig.tenant_id).filter(
                SocialNetworkConfig.is_enabled == True
            ).distinct().all()
        finally:
            db.close()

        # P1 SÉCURITÉ: Synchroniser chaque tenant avec session RLS isolée
        for (tenant_id,) in tenant_ids:
            tenant_db = get_db_for_scheduler(tenant_id)
            try:
                await self._sync_tenant(tenant_db, tenant_id)
            finally:
                tenant_db.close()

        logger.info("[Scheduler] Synchronisation globale terminée")

    async def _sync_tenant(self, db: Session, tenant_id: str):
        """Synchronise toutes les plateformes d'un tenant."""
        logger.info(f"[Scheduler] Sync tenant: {tenant_id}")

        config_service = ConfigService(db, tenant_id)
        metrics_service = SocialNetworksService(db, tenant_id)

        date_to = date.today() - timedelta(days=1)  # Hier
        date_from = date_to - timedelta(days=SYNC_DAYS_BACK - 1)

        results = await config_service.sync_all_platforms(date_from, date_to)

        # Sync vers Prometheus
        if results["total_records"] > 0:
            metrics_service.sync_to_prometheus(date_to)

        logger.info(
            f"[Scheduler] Tenant {tenant_id}: "
            f"{results['platforms_synced']} ok, "
            f"{results['platforms_failed']} erreurs, "
            f"{results['total_records']} enregistrements"
        )

    async def sync_now(self, tenant_id: Optional[str] = None):
        """Force une synchronisation immédiate."""
        logger.info(f"[Scheduler] Sync manuelle demandée (tenant: {tenant_id or 'tous'})")

        if tenant_id:
            # P1 SÉCURITÉ: Session avec contexte RLS pour ce tenant
            db: Session = get_db_for_scheduler(tenant_id)
            try:
                await self._sync_tenant(db, tenant_id)
            finally:
                db.close()
        else:
            # Synchroniser tous les tenants (chacun avec sa propre session RLS)
            await self._sync_all_tenants()


# Instance globale
scheduler = SocialNetworkScheduler.get_instance()


async def start_scheduler():
    """Démarre le scheduler (appelé au démarrage de l'app)."""
    await scheduler.start()


async def stop_scheduler():
    """Arrête le scheduler (appelé à l'arrêt de l'app)."""
    await scheduler.stop()
