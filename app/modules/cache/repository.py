"""
AZALS MODULE - Cache - Repository
==================================

Repository pour la gestion du cache applicatif.
Herite de BaseRepository avec methodes metier specifiques.
"""
from __future__ import annotations


import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.repository import BaseRepository

from .models import (
    CacheAlert,
    CacheAuditLog,
    CacheConfig,
    CacheEntry,
    CacheLevel,
    CacheRegion,
    CacheStatistics,
    CacheStatus,
    InvalidationEvent,
    InvalidationType,
    PreloadTask,
    AlertStatus,
    AlertSeverity,
)

logger = logging.getLogger(__name__)


class CacheConfigRepository(BaseRepository[CacheConfig]):
    """Repository pour CacheConfig."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, CacheConfig, tenant_id)

    def get_config(self) -> Optional[CacheConfig]:
        """Recupere la configuration du tenant."""
        return self.db.query(CacheConfig).filter(
            CacheConfig.tenant_id == self.tenant_id
        ).first()

    def config_exists(self) -> bool:
        """Verifie si une configuration existe."""
        return self.db.query(CacheConfig).filter(
            CacheConfig.tenant_id == self.tenant_id
        ).count() > 0


class CacheRegionRepository(BaseRepository[CacheRegion]):
    """Repository pour CacheRegion."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, CacheRegion, tenant_id)

    def find_by_code(self, code: str) -> Optional[CacheRegion]:
        """Recherche region par code."""
        return self.db.query(CacheRegion).filter(
            CacheRegion.tenant_id == self.tenant_id,
            CacheRegion.code == code
        ).first()

    def list_active(self, skip: int = 0, limit: int = 100) -> Tuple[List[CacheRegion], int]:
        """Liste les regions actives."""
        query = self.db.query(CacheRegion).filter(
            CacheRegion.tenant_id == self.tenant_id,
            CacheRegion.is_active == True
        ).order_by(CacheRegion.code)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_by_entity_type(self, entity_type: str) -> Optional[CacheRegion]:
        """Recherche region par type d'entite."""
        return self.db.query(CacheRegion).filter(
            CacheRegion.tenant_id == self.tenant_id,
            CacheRegion.is_active == True,
            CacheRegion.entity_types.contains([entity_type])
        ).first()

    def count_active(self) -> int:
        """Compte les regions actives."""
        return self.db.query(CacheRegion).filter(
            CacheRegion.tenant_id == self.tenant_id,
            CacheRegion.is_active == True
        ).count()


class CacheEntryRepository(BaseRepository[CacheEntry]):
    """Repository pour CacheEntry."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, CacheEntry, tenant_id)

    def _compute_key_hash(self, key: str) -> str:
        """Calcule le hash d'une cle."""
        full_key = f"{self.tenant_id}:{key}"
        return hashlib.sha256(full_key.encode()).hexdigest()

    def find_by_key(self, key: str) -> Optional[CacheEntry]:
        """Recherche entree par cle."""
        key_hash = self._compute_key_hash(key)
        return self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.key_hash == key_hash,
            CacheEntry.status == CacheStatus.ACTIVE
        ).first()

    def find_by_pattern(self, pattern: str) -> List[CacheEntry]:
        """Recherche entrees par pattern."""
        # Convertit le pattern glob en pattern SQL
        sql_pattern = pattern.replace('*', '%').replace('?', '_')
        return self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.cache_key.like(sql_pattern),
            CacheEntry.status == CacheStatus.ACTIVE
        ).all()

    def find_by_tag(self, tag: str) -> List[CacheEntry]:
        """Recherche entrees par tag."""
        return self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.tags.contains([tag]),
            CacheEntry.status == CacheStatus.ACTIVE
        ).all()

    def find_by_entity(
        self,
        entity_type: str,
        entity_id: Optional[str] = None
    ) -> List[CacheEntry]:
        """Recherche entrees par entite."""
        query = self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.entity_type == entity_type,
            CacheEntry.status == CacheStatus.ACTIVE
        )
        if entity_id:
            query = query.filter(CacheEntry.entity_id == entity_id)
        return query.all()

    def find_by_region(self, region_code: str) -> List[CacheEntry]:
        """Recherche entrees par region."""
        return self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.region_code == region_code,
            CacheEntry.status == CacheStatus.ACTIVE
        ).all()

    def find_expired(self, limit: int = 1000) -> List[CacheEntry]:
        """Recherche les entrees expirees."""
        now = datetime.utcnow()
        return self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.expires_at <= now,
            CacheEntry.status == CacheStatus.ACTIVE
        ).limit(limit).all()

    def find_stale(self, limit: int = 1000) -> List[CacheEntry]:
        """Recherche les entrees stale."""
        now = datetime.utcnow()
        return self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.stale_at <= now,
            CacheEntry.expires_at > now,
            CacheEntry.status == CacheStatus.ACTIVE
        ).limit(limit).all()

    def get_top_keys(self, limit: int = 10) -> List[CacheEntry]:
        """Recupere les cles les plus utilisees."""
        return self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.status == CacheStatus.ACTIVE
        ).order_by(CacheEntry.hit_count.desc()).limit(limit).all()

    def count_active(self) -> int:
        """Compte les entrees actives."""
        return self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.status == CacheStatus.ACTIVE
        ).count()

    def get_total_size(self) -> int:
        """Calcule la taille totale du cache."""
        result = self.db.query(func.sum(CacheEntry.original_size_bytes)).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.status == CacheStatus.ACTIVE
        ).scalar()
        return result or 0

    def invalidate_key(self, key: str) -> int:
        """Invalide une entree par cle."""
        key_hash = self._compute_key_hash(key)
        count = self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.key_hash == key_hash
        ).update({"status": CacheStatus.INVALIDATED})
        self.db.flush()
        return count

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalide les entrees par pattern."""
        sql_pattern = pattern.replace('*', '%').replace('?', '_')
        count = self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.cache_key.like(sql_pattern)
        ).update({"status": CacheStatus.INVALIDATED}, synchronize_session=False)
        self.db.flush()
        return count

    def invalidate_tag(self, tag: str) -> int:
        """Invalide les entrees par tag."""
        entries = self.find_by_tag(tag)
        count = 0
        for entry in entries:
            entry.status = CacheStatus.INVALIDATED
            count += 1
        self.db.flush()
        return count

    def invalidate_entity(self, entity_type: str, entity_id: Optional[str] = None) -> int:
        """Invalide les entrees par entite."""
        query = self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            CacheEntry.entity_type == entity_type
        )
        if entity_id:
            query = query.filter(CacheEntry.entity_id == entity_id)
        count = query.update({"status": CacheStatus.INVALIDATED}, synchronize_session=False)
        self.db.flush()
        return count

    def invalidate_all(self) -> int:
        """Invalide toutes les entrees du tenant."""
        count = self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id
        ).update({"status": CacheStatus.INVALIDATED}, synchronize_session=False)
        self.db.flush()
        return count

    def purge_expired(self) -> int:
        """Supprime les entrees expirees."""
        count = self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id,
            or_(
                CacheEntry.status == CacheStatus.EXPIRED,
                CacheEntry.status == CacheStatus.INVALIDATED,
                and_(
                    CacheEntry.expires_at.isnot(None),
                    CacheEntry.expires_at <= datetime.utcnow()
                )
            )
        ).delete(synchronize_session=False)
        self.db.flush()
        return count

    def purge_all(self) -> int:
        """Supprime toutes les entrees du tenant."""
        count = self.db.query(CacheEntry).filter(
            CacheEntry.tenant_id == self.tenant_id
        ).delete(synchronize_session=False)
        self.db.flush()
        return count


class CacheStatisticsRepository(BaseRepository[CacheStatistics]):
    """Repository pour CacheStatistics."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, CacheStatistics, tenant_id)

    def get_current_stats(
        self,
        level: CacheLevel,
        period_type: str = 'HOUR'
    ) -> Optional[CacheStatistics]:
        """Recupere les stats de la periode actuelle."""
        now = datetime.utcnow()

        if period_type == 'MINUTE':
            period_start = now.replace(second=0, microsecond=0)
        elif period_type == 'HOUR':
            period_start = now.replace(minute=0, second=0, microsecond=0)
        else:  # DAY
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        return self.db.query(CacheStatistics).filter(
            CacheStatistics.tenant_id == self.tenant_id,
            CacheStatistics.cache_level == level,
            CacheStatistics.period_start == period_start,
            CacheStatistics.period_type == period_type
        ).first()

    def get_stats_range(
        self,
        level: Optional[CacheLevel],
        start_date: datetime,
        end_date: datetime,
        period_type: str = 'HOUR'
    ) -> List[CacheStatistics]:
        """Recupere les stats sur une periode."""
        query = self.db.query(CacheStatistics).filter(
            CacheStatistics.tenant_id == self.tenant_id,
            CacheStatistics.period_start >= start_date,
            CacheStatistics.period_end <= end_date,
            CacheStatistics.period_type == period_type
        )
        if level:
            query = query.filter(CacheStatistics.cache_level == level)
        return query.order_by(CacheStatistics.period_start).all()

    def get_aggregated_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calcule les statistiques agregees."""
        stats = self.db.query(
            CacheStatistics.cache_level,
            func.sum(CacheStatistics.hits).label('total_hits'),
            func.sum(CacheStatistics.misses).label('total_misses'),
            func.sum(CacheStatistics.stale_hits).label('total_stale_hits'),
            func.sum(CacheStatistics.evictions_ttl).label('total_evictions_ttl'),
            func.sum(CacheStatistics.evictions_capacity).label('total_evictions_capacity'),
            func.avg(CacheStatistics.avg_get_time_ms).label('avg_get_time'),
            func.avg(CacheStatistics.avg_set_time_ms).label('avg_set_time'),
        ).filter(
            CacheStatistics.tenant_id == self.tenant_id,
            CacheStatistics.period_start >= start_date,
            CacheStatistics.period_end <= end_date
        ).group_by(CacheStatistics.cache_level).all()

        return {
            str(s.cache_level.value): {
                'total_hits': int(s.total_hits or 0),
                'total_misses': int(s.total_misses or 0),
                'total_stale_hits': int(s.total_stale_hits or 0),
                'total_evictions': int((s.total_evictions_ttl or 0) + (s.total_evictions_capacity or 0)),
                'avg_get_time_ms': float(s.avg_get_time or 0),
                'avg_set_time_ms': float(s.avg_set_time or 0),
            }
            for s in stats
        }


class InvalidationEventRepository(BaseRepository[InvalidationEvent]):
    """Repository pour InvalidationEvent."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, InvalidationEvent, tenant_id)

    def get_recent(self, limit: int = 20) -> List[InvalidationEvent]:
        """Recupere les invalidations recentes."""
        return self.db.query(InvalidationEvent).filter(
            InvalidationEvent.tenant_id == self.tenant_id
        ).order_by(InvalidationEvent.created_at.desc()).limit(limit).all()

    def get_by_type(
        self,
        invalidation_type: InvalidationType,
        limit: int = 100
    ) -> List[InvalidationEvent]:
        """Recupere les invalidations par type."""
        return self.db.query(InvalidationEvent).filter(
            InvalidationEvent.tenant_id == self.tenant_id,
            InvalidationEvent.invalidation_type == invalidation_type
        ).order_by(InvalidationEvent.created_at.desc()).limit(limit).all()


class PreloadTaskRepository(BaseRepository[PreloadTask]):
    """Repository pour PreloadTask."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, PreloadTask, tenant_id)

    def find_by_region(self, region_code: str) -> List[PreloadTask]:
        """Recherche taches par region."""
        return self.db.query(PreloadTask).filter(
            PreloadTask.tenant_id == self.tenant_id,
            PreloadTask.region_code == region_code
        ).all()

    def find_due_tasks(self, limit: int = 10) -> List[PreloadTask]:
        """Recherche les taches a executer."""
        now = datetime.utcnow()
        return self.db.query(PreloadTask).filter(
            PreloadTask.tenant_id == self.tenant_id,
            PreloadTask.is_active == True,
            PreloadTask.next_run_at <= now
        ).limit(limit).all()

    def count_active(self) -> int:
        """Compte les taches actives."""
        return self.db.query(PreloadTask).filter(
            PreloadTask.tenant_id == self.tenant_id,
            PreloadTask.is_active == True
        ).count()


class CacheAlertRepository(BaseRepository[CacheAlert]):
    """Repository pour CacheAlert."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, CacheAlert, tenant_id)

    def get_active_alerts(self, limit: int = 50) -> List[CacheAlert]:
        """Recupere les alertes actives."""
        return self.db.query(CacheAlert).filter(
            CacheAlert.tenant_id == self.tenant_id,
            CacheAlert.status == AlertStatus.ACTIVE
        ).order_by(CacheAlert.severity.desc(), CacheAlert.triggered_at.desc()).limit(limit).all()

    def get_by_type(
        self,
        alert_type: str,
        status: Optional[AlertStatus] = None,
        limit: int = 50
    ) -> List[CacheAlert]:
        """Recupere les alertes par type."""
        query = self.db.query(CacheAlert).filter(
            CacheAlert.tenant_id == self.tenant_id,
            CacheAlert.alert_type == alert_type
        )
        if status:
            query = query.filter(CacheAlert.status == status)
        return query.order_by(CacheAlert.triggered_at.desc()).limit(limit).all()

    def count_active(self) -> int:
        """Compte les alertes actives."""
        return self.db.query(CacheAlert).filter(
            CacheAlert.tenant_id == self.tenant_id,
            CacheAlert.status == AlertStatus.ACTIVE
        ).count()

    def count_by_severity(self, severity: AlertSeverity) -> int:
        """Compte les alertes par severite."""
        return self.db.query(CacheAlert).filter(
            CacheAlert.tenant_id == self.tenant_id,
            CacheAlert.status == AlertStatus.ACTIVE,
            CacheAlert.severity == severity
        ).count()


class CacheAuditLogRepository(BaseRepository[CacheAuditLog]):
    """Repository pour CacheAuditLog."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, CacheAuditLog, tenant_id)

    def get_recent(self, limit: int = 50) -> List[CacheAuditLog]:
        """Recupere les logs recents."""
        return self.db.query(CacheAuditLog).filter(
            CacheAuditLog.tenant_id == self.tenant_id
        ).order_by(CacheAuditLog.created_at.desc()).limit(limit).all()

    def get_by_action(self, action: str, limit: int = 50) -> List[CacheAuditLog]:
        """Recupere les logs par action."""
        return self.db.query(CacheAuditLog).filter(
            CacheAuditLog.tenant_id == self.tenant_id,
            CacheAuditLog.action == action
        ).order_by(CacheAuditLog.created_at.desc()).limit(limit).all()

    def get_by_user(self, user_id: UUID, limit: int = 50) -> List[CacheAuditLog]:
        """Recupere les logs par utilisateur."""
        return self.db.query(CacheAuditLog).filter(
            CacheAuditLog.tenant_id == self.tenant_id,
            CacheAuditLog.user_id == user_id
        ).order_by(CacheAuditLog.created_at.desc()).limit(limit).all()
