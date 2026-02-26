"""
AZALS MODULE - Odoo Import History Service
============================================

Service de gestion de l'historique et des statistiques d'import.
"""
from __future__ import annotations


import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func

from app.modules.odoo_import.models import (
    OdooConnectionConfig,
    OdooImportHistory,
    OdooSyncType,
)

from .base import BaseOdooService

logger = logging.getLogger(__name__)


class HistoryService(BaseOdooService[OdooImportHistory]):
    """Service de gestion de l'historique d'import."""

    model = OdooImportHistory

    def list(
        self,
        config_id: Optional[UUID] = None,
        sync_type: Optional[OdooSyncType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[OdooImportHistory]:
        """
        Récupère l'historique des imports.

        Args:
            config_id: Filtrer par configuration (optionnel)
            sync_type: Filtrer par type de sync (optionnel)
            limit: Nombre max de résultats
            offset: Décalage pour pagination

        Returns:
            Liste des historiques triés par date décroissante
        """
        query = self.db.query(OdooImportHistory).filter(
            OdooImportHistory.tenant_id == self.tenant_id,
        )

        if config_id:
            query = query.filter(OdooImportHistory.config_id == config_id)

        if sync_type:
            query = query.filter(OdooImportHistory.sync_type == sync_type)

        return (
            query.order_by(OdooImportHistory.started_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get(self, history_id: UUID) -> Optional[OdooImportHistory]:
        """
        Récupère un historique par ID.

        Args:
            history_id: ID de l'historique

        Returns:
            Historique ou None
        """
        return (
            self.db.query(OdooImportHistory)
            .filter(
                OdooImportHistory.tenant_id == self.tenant_id,
                OdooImportHistory.id == history_id,
            )
            .first()
        )

    def get_last_by_type(
        self,
        config_id: UUID,
        sync_type: OdooSyncType,
    ) -> Optional[OdooImportHistory]:
        """
        Récupère le dernier import d'un type donné.

        Args:
            config_id: ID de la configuration
            sync_type: Type de synchronisation

        Returns:
            Dernier historique ou None
        """
        return (
            self.db.query(OdooImportHistory)
            .filter(
                OdooImportHistory.tenant_id == self.tenant_id,
                OdooImportHistory.config_id == config_id,
                OdooImportHistory.sync_type == sync_type,
            )
            .order_by(OdooImportHistory.started_at.desc())
            .first()
        )

    def get_stats(self, config_id: UUID) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une configuration.

        Args:
            config_id: ID de la configuration

        Returns:
            Dictionnaire de statistiques comprenant:
            - Informations de la configuration
            - Compteurs par statut
            - Dernier import par type
        """
        config = self.get_config(config_id)
        if not config:
            return {}

        # Compter les imports par statut
        status_counts = self._get_status_counts(config_id)

        # Dernier import par type
        last_imports = self._get_last_imports_by_type(config_id)

        return {
            "config_id": str(config_id),
            "config_name": config.name,
            "total_imports": config.total_imports,
            "total_products": config.total_products_imported,
            "total_contacts": config.total_contacts_imported,
            "total_suppliers": config.total_suppliers_imported,
            "is_connected": config.is_connected,
            "last_connection_test": config.last_connection_test_at,
            "status_counts": status_counts,
            "last_imports": last_imports,
        }

    def _get_status_counts(self, config_id: UUID) -> Dict[str, int]:
        """
        Compte les imports par statut.

        Args:
            config_id: ID de la configuration

        Returns:
            Dictionnaire {status: count}
        """
        results = (
            self.db.query(
                OdooImportHistory.status,
                func.count(OdooImportHistory.id),
            )
            .filter(
                OdooImportHistory.tenant_id == self.tenant_id,
                OdooImportHistory.config_id == config_id,
            )
            .group_by(OdooImportHistory.status)
            .all()
        )

        return {status.value: count for status, count in results}

    def _get_last_imports_by_type(self, config_id: UUID) -> Dict[str, Dict[str, Any]]:
        """
        Récupère le dernier import pour chaque type.

        Args:
            config_id: ID de la configuration

        Returns:
            Dictionnaire {sync_type: {started_at, status, records}}
        """
        last_imports = {}

        for sync_type in OdooSyncType:
            last = self.get_last_by_type(config_id, sync_type)
            if last:
                last_imports[sync_type.value] = {
                    "started_at": last.started_at,
                    "status": last.status.value,
                    "records": last.total_records,
                    "created": last.created_count,
                    "updated": last.updated_count,
                    "errors": last.error_count,
                }

        return last_imports

    def get_summary(self, config_id: UUID) -> Dict[str, Any]:
        """
        Récupère un résumé des imports récents.

        Args:
            config_id: ID de la configuration

        Returns:
            Résumé avec imports récents et tendances
        """
        # 10 derniers imports
        recent = self.list(config_id=config_id, limit=10)

        # Calculer les tendances
        success_count = sum(1 for h in recent if h.status.value == "success")
        error_count = sum(1 for h in recent if h.status.value == "error")
        partial_count = sum(1 for h in recent if h.status.value == "partial")

        total_records = sum(h.total_records or 0 for h in recent)
        total_created = sum(h.created_count or 0 for h in recent)
        total_updated = sum(h.updated_count or 0 for h in recent)
        total_errors = sum(h.error_count or 0 for h in recent)

        return {
            "recent_imports": [
                {
                    "id": str(h.id),
                    "sync_type": h.sync_type.value,
                    "status": h.status.value,
                    "started_at": h.started_at,
                    "duration_seconds": h.duration_seconds,
                    "total_records": h.total_records,
                    "created": h.created_count,
                    "updated": h.updated_count,
                    "errors": h.error_count,
                }
                for h in recent
            ],
            "trends": {
                "success_rate": (
                    success_count / len(recent) * 100
                    if recent
                    else 0
                ),
                "total_records": total_records,
                "total_created": total_created,
                "total_updated": total_updated,
                "total_errors": total_errors,
            },
            "health": {
                "success": success_count,
                "partial": partial_count,
                "error": error_count,
            },
        }

    def cleanup_old(
        self,
        config_id: Optional[UUID] = None,
        days_to_keep: int = 90,
    ) -> int:
        """
        Supprime les anciens historiques.

        Args:
            config_id: Filtrer par configuration (optionnel)
            days_to_keep: Nombre de jours à conserver

        Returns:
            Nombre d'historiques supprimés
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        query = self.db.query(OdooImportHistory).filter(
            OdooImportHistory.tenant_id == self.tenant_id,
            OdooImportHistory.started_at < cutoff_date,
        )

        if config_id:
            query = query.filter(OdooImportHistory.config_id == config_id)

        count = query.delete()
        self.db.commit()

        logger.info(
            "Nettoyage historique | tenant=%s deleted=%d cutoff=%s",
            self.tenant_id,
            count,
            cutoff_date,
        )
        return count
