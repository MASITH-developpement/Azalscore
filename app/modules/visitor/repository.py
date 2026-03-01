"""
AZALS MODULE VISITOR - Repository
==================================

Repositories SQLAlchemy pour le module Visitor Management (GAP-079).
Conforme aux normes AZALSCORE (isolation tenant, type hints).
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload

from .models import (
    VisitorLocation,
    Host,
    VisitorProfile,
    Visit,
    VisitorBadge,
    VisitGroup,
    WatchlistEntry,
    VisitorType,
    VisitStatus,
    BadgeType,
    AccessLevel,
    WatchlistType,
    WatchlistAction,
)


class VisitorLocationRepository:
    """Repository pour les lieux de visite."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(VisitorLocation).filter(
            VisitorLocation.tenant_id == self.tenant_id
        )

    def get_by_id(self, location_id: UUID) -> Optional[VisitorLocation]:
        """Recupere un lieu par ID."""
        return self._base_query().filter(
            VisitorLocation.id == location_id
        ).first()

    def get_by_code(self, code: str) -> Optional[VisitorLocation]:
        """Recupere un lieu par code."""
        return self._base_query().filter(
            VisitorLocation.code == code
        ).first()

    def list(
        self,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[VisitorLocation], int]:
        """Liste les lieux avec filtres."""
        query = self._base_query()

        if is_active is not None:
            query = query.filter(VisitorLocation.is_active == is_active)
        if search:
            query = query.filter(
                or_(
                    VisitorLocation.name.ilike(f"%{search}%"),
                    VisitorLocation.code.ilike(f"%{search}%"),
                    VisitorLocation.address.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(VisitorLocation.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any]) -> VisitorLocation:
        """Cree un nouveau lieu."""
        location = VisitorLocation(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def update(
        self,
        location: VisitorLocation,
        data: Dict[str, Any]
    ) -> VisitorLocation:
        """Met a jour un lieu."""
        for key, value in data.items():
            if hasattr(location, key) and value is not None:
                setattr(location, key, value)
        location.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(location)
        return location

    def increment_visitors(self, location: VisitorLocation) -> VisitorLocation:
        """Incremente le compteur de visiteurs."""
        location.current_visitors += 1
        location.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(location)
        return location

    def decrement_visitors(self, location: VisitorLocation) -> VisitorLocation:
        """Decremente le compteur de visiteurs."""
        if location.current_visitors > 0:
            location.current_visitors -= 1
        location.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(location)
        return location


class HostRepository:
    """Repository pour les hotes."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(Host).filter(
            Host.tenant_id == self.tenant_id
        )

    def get_by_id(self, host_id: UUID) -> Optional[Host]:
        """Recupere un hote par ID."""
        return self._base_query().filter(
            Host.id == host_id
        ).first()

    def get_by_user_id(self, user_id: UUID) -> Optional[Host]:
        """Recupere un hote par user_id."""
        return self._base_query().filter(
            Host.user_id == user_id
        ).first()

    def list(
        self,
        location_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Host], int]:
        """Liste les hotes avec filtres."""
        query = self._base_query()

        if location_id:
            query = query.filter(Host.location_id == location_id)
        if is_active is not None:
            query = query.filter(Host.is_active == is_active)
        if search:
            query = query.filter(
                or_(
                    Host.name.ilike(f"%{search}%"),
                    Host.email.ilike(f"%{search}%"),
                    Host.department.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(Host.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any]) -> Host:
        """Cree un nouvel hote."""
        host = Host(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(host)
        self.db.commit()
        self.db.refresh(host)
        return host

    def update(self, host: Host, data: Dict[str, Any]) -> Host:
        """Met a jour un hote."""
        for key, value in data.items():
            if hasattr(host, key) and value is not None:
                setattr(host, key, value)
        host.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(host)
        return host

    def delete(self, host: Host) -> None:
        """Supprime un hote (soft delete)."""
        host.is_active = False
        host.updated_at = datetime.utcnow()
        self.db.commit()


class VisitorProfileRepository:
    """Repository pour les profils visiteur."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(VisitorProfile).filter(
            VisitorProfile.tenant_id == self.tenant_id
        )

    def get_by_id(self, profile_id: UUID) -> Optional[VisitorProfile]:
        """Recupere un profil par ID."""
        return self._base_query().filter(
            VisitorProfile.id == profile_id
        ).first()

    def get_by_email(self, email: str) -> Optional[VisitorProfile]:
        """Recupere un profil par email."""
        return self._base_query().filter(
            VisitorProfile.email == email
        ).first()

    def list(
        self,
        is_blacklisted: Optional[bool] = None,
        is_vip: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[VisitorProfile], int]:
        """Liste les profils avec filtres."""
        query = self._base_query()

        if is_blacklisted is not None:
            query = query.filter(VisitorProfile.is_blacklisted == is_blacklisted)
        if is_vip is not None:
            query = query.filter(VisitorProfile.is_vip == is_vip)
        if search:
            query = query.filter(
                or_(
                    VisitorProfile.email.ilike(f"%{search}%"),
                    VisitorProfile.first_name.ilike(f"%{search}%"),
                    VisitorProfile.last_name.ilike(f"%{search}%"),
                    VisitorProfile.company.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(desc(VisitorProfile.last_visit)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def get_or_create(self, email: str, data: Dict[str, Any]) -> VisitorProfile:
        """Recupere ou cree un profil."""
        profile = self.get_by_email(email)
        if not profile:
            profile = VisitorProfile(
                tenant_id=self.tenant_id,
                email=email,
                **data
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def create(self, data: Dict[str, Any]) -> VisitorProfile:
        """Cree un nouveau profil."""
        profile = VisitorProfile(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update(
        self,
        profile: VisitorProfile,
        data: Dict[str, Any]
    ) -> VisitorProfile:
        """Met a jour un profil."""
        for key, value in data.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def record_visit(self, profile: VisitorProfile) -> VisitorProfile:
        """Enregistre une visite."""
        profile.total_visits += 1
        profile.last_visit = datetime.utcnow()
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def blacklist(
        self,
        profile: VisitorProfile,
        reason: str
    ) -> VisitorProfile:
        """Ajoute a la blacklist."""
        profile.is_blacklisted = True
        profile.blacklist_reason = reason
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def remove_from_blacklist(self, profile: VisitorProfile) -> VisitorProfile:
        """Retire de la blacklist."""
        profile.is_blacklisted = False
        profile.blacklist_reason = ""
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        return profile


class VisitRepository:
    """Repository pour les visites."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(Visit).filter(
            Visit.tenant_id == self.tenant_id
        )

    def get_by_id(
        self,
        visit_id: UUID,
        with_relations: bool = False
    ) -> Optional[Visit]:
        """Recupere une visite par ID."""
        query = self._base_query().filter(Visit.id == visit_id)
        if with_relations:
            query = query.options(
                joinedload(Visit.visitor_profile),
                joinedload(Visit.host),
                joinedload(Visit.location)
            )
        return query.first()

    def get_by_number(self, visit_number: str) -> Optional[Visit]:
        """Recupere une visite par numero."""
        return self._base_query().filter(
            Visit.visit_number == visit_number
        ).first()

    def get_by_qr_code(self, qr_code: str) -> Optional[Visit]:
        """Recupere une visite par QR code."""
        return self._base_query().filter(
            Visit.qr_code == qr_code
        ).first()

    def list(
        self,
        location_id: Optional[UUID] = None,
        host_id: Optional[UUID] = None,
        status: Optional[VisitStatus] = None,
        visitor_type: Optional[VisitorType] = None,
        scheduled_date: Optional[date] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Visit], int]:
        """Liste les visites avec filtres."""
        query = self._base_query()

        if location_id:
            query = query.filter(Visit.location_id == location_id)
        if host_id:
            query = query.filter(Visit.host_id == host_id)
        if status:
            query = query.filter(Visit.status == status)
        if visitor_type:
            query = query.filter(Visit.visitor_type == visitor_type)
        if scheduled_date:
            query = query.filter(Visit.scheduled_date == scheduled_date)
        if date_from:
            query = query.filter(Visit.scheduled_date >= date_from)
        if date_to:
            query = query.filter(Visit.scheduled_date <= date_to)
        if search:
            query = query.filter(
                or_(
                    Visit.visit_number.ilike(f"%{search}%"),
                    Visit.visitor_first_name.ilike(f"%{search}%"),
                    Visit.visitor_last_name.ilike(f"%{search}%"),
                    Visit.visitor_email.ilike(f"%{search}%"),
                    Visit.visitor_company.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(
            desc(Visit.scheduled_date),
            Visit.scheduled_start
        ).offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    def get_today(
        self,
        location_id: Optional[UUID] = None
    ) -> List[Visit]:
        """Recupere les visites du jour."""
        query = self._base_query().filter(
            Visit.scheduled_date == date.today()
        )
        if location_id:
            query = query.filter(Visit.location_id == location_id)
        return query.order_by(Visit.scheduled_start).all()

    def get_checked_in(
        self,
        location_id: Optional[UUID] = None
    ) -> List[Visit]:
        """Recupere les visiteurs actuellement sur site."""
        query = self._base_query().filter(
            Visit.status == VisitStatus.CHECKED_IN
        )
        if location_id:
            query = query.filter(Visit.location_id == location_id)
        return query.order_by(Visit.checked_in_at).all()

    def get_upcoming(
        self,
        hours: int = 24,
        location_id: Optional[UUID] = None
    ) -> List[Visit]:
        """Recupere les visites a venir."""
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=hours)
        query = self._base_query().filter(
            Visit.status.in_([VisitStatus.SCHEDULED, VisitStatus.PRE_REGISTERED]),
            Visit.scheduled_date >= now.date(),
            Visit.scheduled_date <= cutoff.date()
        )
        if location_id:
            query = query.filter(Visit.location_id == location_id)
        return query.order_by(Visit.scheduled_date, Visit.scheduled_start).all()

    def create(self, data: Dict[str, Any]) -> Visit:
        """Cree une nouvelle visite."""
        visit = Visit(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(visit)
        self.db.commit()
        self.db.refresh(visit)
        return visit

    def update(self, visit: Visit, data: Dict[str, Any]) -> Visit:
        """Met a jour une visite."""
        for key, value in data.items():
            if hasattr(visit, key) and value is not None:
                setattr(visit, key, value)
        visit.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(visit)
        return visit

    def check_in(
        self,
        visit: Visit,
        checked_in_by: str,
        badge_number: Optional[str] = None
    ) -> Visit:
        """Enregistre le check-in."""
        visit.status = VisitStatus.CHECKED_IN
        visit.checked_in_at = datetime.utcnow()
        visit.checked_in_by = checked_in_by
        if badge_number:
            visit.badge_number = badge_number
        visit.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(visit)
        return visit

    def check_out(
        self,
        visit: Visit,
        checked_out_by: str
    ) -> Visit:
        """Enregistre le check-out."""
        visit.status = VisitStatus.CHECKED_OUT
        visit.checked_out_at = datetime.utcnow()
        visit.checked_out_by = checked_out_by
        visit.badge_returned = True
        visit.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(visit)
        return visit

    def cancel(self, visit: Visit) -> Visit:
        """Annule une visite."""
        visit.status = VisitStatus.CANCELLED
        visit.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(visit)
        return visit

    def mark_no_show(self, visit: Visit) -> Visit:
        """Marque comme absent."""
        visit.status = VisitStatus.NO_SHOW
        visit.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(visit)
        return visit


class VisitorBadgeRepository:
    """Repository pour les badges visiteur."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(VisitorBadge).filter(
            VisitorBadge.tenant_id == self.tenant_id
        )

    def get_by_id(self, badge_id: UUID) -> Optional[VisitorBadge]:
        """Recupere un badge par ID."""
        return self._base_query().filter(
            VisitorBadge.id == badge_id
        ).first()

    def get_by_visit(self, visit_id: UUID) -> Optional[VisitorBadge]:
        """Recupere le badge d'une visite."""
        return self._base_query().filter(
            VisitorBadge.visit_id == visit_id
        ).first()

    def get_by_number(self, badge_number: str) -> Optional[VisitorBadge]:
        """Recupere un badge par numero."""
        return self._base_query().filter(
            VisitorBadge.badge_number == badge_number,
            VisitorBadge.is_active == True
        ).first()

    def create(self, data: Dict[str, Any]) -> VisitorBadge:
        """Cree un nouveau badge."""
        badge = VisitorBadge(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(badge)
        self.db.commit()
        self.db.refresh(badge)
        return badge

    def mark_printed(self, badge: VisitorBadge) -> VisitorBadge:
        """Marque le badge comme imprime."""
        badge.printed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(badge)
        return badge

    def mark_returned(self, badge: VisitorBadge) -> VisitorBadge:
        """Marque le badge comme retourne."""
        badge.returned_at = datetime.utcnow()
        badge.is_active = False
        self.db.commit()
        self.db.refresh(badge)
        return badge


class VisitGroupRepository:
    """Repository pour les groupes de visiteurs."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(VisitGroup).filter(
            VisitGroup.tenant_id == self.tenant_id
        )

    def get_by_id(
        self,
        group_id: UUID,
        with_visits: bool = False
    ) -> Optional[VisitGroup]:
        """Recupere un groupe par ID."""
        query = self._base_query().filter(VisitGroup.id == group_id)
        if with_visits:
            query = query.options(joinedload(VisitGroup.visits))
        return query.first()

    def list(
        self,
        location_id: Optional[UUID] = None,
        host_id: Optional[UUID] = None,
        visit_date: Optional[date] = None,
        status: Optional[VisitStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[VisitGroup], int]:
        """Liste les groupes avec filtres."""
        query = self._base_query()

        if location_id:
            query = query.filter(VisitGroup.location_id == location_id)
        if host_id:
            query = query.filter(VisitGroup.host_id == host_id)
        if visit_date:
            query = query.filter(VisitGroup.visit_date == visit_date)
        if status:
            query = query.filter(VisitGroup.status == status)

        total = query.count()
        items = query.order_by(
            desc(VisitGroup.visit_date),
            VisitGroup.start_time
        ).offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any]) -> VisitGroup:
        """Cree un nouveau groupe."""
        group = VisitGroup(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def update(
        self,
        group: VisitGroup,
        data: Dict[str, Any]
    ) -> VisitGroup:
        """Met a jour un groupe."""
        for key, value in data.items():
            if hasattr(group, key) and value is not None:
                setattr(group, key, value)
        group.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(group)
        return group

    def update_member_count(self, group: VisitGroup) -> VisitGroup:
        """Met a jour le nombre de membres."""
        count = self.db.query(Visit).filter(
            Visit.group_id == group.id
        ).count()
        group.member_count = count
        group.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(group)
        return group


class WatchlistRepository:
    """Repository pour la liste de surveillance."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WatchlistEntry).filter(
            WatchlistEntry.tenant_id == self.tenant_id
        )

    def get_by_id(self, entry_id: UUID) -> Optional[WatchlistEntry]:
        """Recupere une entree par ID."""
        return self._base_query().filter(
            WatchlistEntry.id == entry_id
        ).first()

    def check_email(self, email: str) -> Optional[WatchlistEntry]:
        """Verifie si un email est sur la liste."""
        today = date.today()
        return self._base_query().filter(
            WatchlistEntry.email == email,
            WatchlistEntry.is_active == True,
            WatchlistEntry.valid_from <= today,
            or_(
                WatchlistEntry.valid_until.is_(None),
                WatchlistEntry.valid_until >= today
            )
        ).first()

    def check_id_number(self, id_number: str) -> Optional[WatchlistEntry]:
        """Verifie si un numero d'identite est sur la liste."""
        today = date.today()
        return self._base_query().filter(
            WatchlistEntry.id_number == id_number,
            WatchlistEntry.is_active == True,
            WatchlistEntry.valid_from <= today,
            or_(
                WatchlistEntry.valid_until.is_(None),
                WatchlistEntry.valid_until >= today
            )
        ).first()

    def check_visitor(
        self,
        email: Optional[str] = None,
        id_number: Optional[str] = None
    ) -> Optional[WatchlistEntry]:
        """Verifie si un visiteur est sur la liste."""
        if email:
            result = self.check_email(email)
            if result:
                return result
        if id_number:
            result = self.check_id_number(id_number)
            if result:
                return result
        return None

    def list(
        self,
        list_type: Optional[WatchlistType] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WatchlistEntry], int]:
        """Liste les entrees avec filtres."""
        query = self._base_query()

        if list_type:
            query = query.filter(WatchlistEntry.list_type == list_type)
        if is_active is not None:
            query = query.filter(WatchlistEntry.is_active == is_active)
        if search:
            query = query.filter(
                or_(
                    WatchlistEntry.email.ilike(f"%{search}%"),
                    WatchlistEntry.name.ilike(f"%{search}%"),
                    WatchlistEntry.id_number.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(desc(WatchlistEntry.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any]) -> WatchlistEntry:
        """Cree une nouvelle entree."""
        entry = WatchlistEntry(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(
        self,
        entry: WatchlistEntry,
        data: Dict[str, Any]
    ) -> WatchlistEntry:
        """Met a jour une entree."""
        for key, value in data.items():
            if hasattr(entry, key) and value is not None:
                setattr(entry, key, value)
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def deactivate(self, entry: WatchlistEntry) -> WatchlistEntry:
        """Desactive une entree."""
        entry.is_active = False
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry: WatchlistEntry) -> None:
        """Supprime une entree."""
        self.db.delete(entry)
        self.db.commit()
