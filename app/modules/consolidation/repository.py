"""
AZALS MODULE - CONSOLIDATION: Repository
==========================================

Repositories avec isolation tenant stricte pour le module
de consolidation comptable multi-entites.

REGLES CRITIQUES:
- Toutes les requetes filtrees par tenant_id via _base_query()
- Soft delete par defaut
- Gestion de version (optimistic locking)

Auteur: AZALSCORE Team
Version: 1.0.0
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload

from .models import (
    ConsolidationPerimeter,
    ConsolidationEntity,
    Participation,
    ExchangeRate,
    Consolidation,
    ConsolidationPackage,
    EliminationEntry,
    Restatement,
    IntercompanyReconciliation,
    GoodwillCalculation,
    MinorityInterest,
    ConsolidatedReport,
    AccountMapping,
    ConsolidationAuditLog,
    ConsolidationStatus,
    ConsolidationMethod,
    PackageStatus,
    EliminationType,
    RestatementType,
    ReportType,
)
from .schemas import (
    ConsolidationFilters,
    EntityFilters,
    PackageFilters,
    ReconciliationFilters,
)


# ============================================================================
# REPOSITORY: PERIMETRE DE CONSOLIDATION
# ============================================================================

class ConsolidationPerimeterRepository:
    """Repository pour les perimetres de consolidation avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base filtree par tenant_id."""
        query = self.db.query(ConsolidationPerimeter).filter(
            ConsolidationPerimeter.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(ConsolidationPerimeter.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ConsolidationPerimeter]:
        """Recuperer un perimetre par ID."""
        return self._base_query().filter(ConsolidationPerimeter.id == id).first()

    def get_by_code(self, code: str, fiscal_year: int) -> Optional[ConsolidationPerimeter]:
        """Recuperer un perimetre par code et annee."""
        return self._base_query().filter(
            ConsolidationPerimeter.code == code.upper(),
            ConsolidationPerimeter.fiscal_year == fiscal_year
        ).first()

    def exists(self, id: UUID) -> bool:
        """Verifier si un perimetre existe."""
        return self._base_query().filter(ConsolidationPerimeter.id == id).count() > 0

    def code_exists(self, code: str, fiscal_year: int, exclude_id: UUID = None) -> bool:
        """Verifier si un code existe pour une annee."""
        query = self._base_query().filter(
            ConsolidationPerimeter.code == code.upper(),
            ConsolidationPerimeter.fiscal_year == fiscal_year
        )
        if exclude_id:
            query = query.filter(ConsolidationPerimeter.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        fiscal_year: int = None,
        status: List[ConsolidationStatus] = None,
        is_active: bool = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[ConsolidationPerimeter], int]:
        """Lister les perimetres avec filtres et pagination."""
        query = self._base_query()

        if fiscal_year:
            query = query.filter(ConsolidationPerimeter.fiscal_year == fiscal_year)
        if status:
            query = query.filter(ConsolidationPerimeter.status.in_([s.value for s in status]))
        if is_active is not None:
            query = query.filter(ConsolidationPerimeter.is_active == is_active)

        total = query.count()
        sort_col = getattr(ConsolidationPerimeter, sort_by, ConsolidationPerimeter.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_active_by_year(self, fiscal_year: int) -> List[ConsolidationPerimeter]:
        """Recuperer les perimetres actifs pour une annee."""
        return self._base_query().filter(
            ConsolidationPerimeter.fiscal_year == fiscal_year,
            ConsolidationPerimeter.is_active == True
        ).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ConsolidationPerimeter:
        """Creer un nouveau perimetre."""
        if "code" in data:
            data["code"] = data["code"].upper()

        entity = ConsolidationPerimeter(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: ConsolidationPerimeter,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ConsolidationPerimeter:
        """Mettre a jour un perimetre."""
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: ConsolidationPerimeter, deleted_by: UUID = None) -> bool:
        """Supprimer logiquement un perimetre."""
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: ConsolidationPerimeter) -> ConsolidationPerimeter:
        """Restaurer un perimetre supprime."""
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_entity_count(self, perimeter_id: UUID) -> int:
        """Compter les entites d'un perimetre."""
        return self.db.query(ConsolidationEntity).filter(
            ConsolidationEntity.tenant_id == self.tenant_id,
            ConsolidationEntity.perimeter_id == perimeter_id,
            ConsolidationEntity.is_deleted == False
        ).count()


# ============================================================================
# REPOSITORY: ENTITES DU GROUPE
# ============================================================================

class ConsolidationEntityRepository:
    """Repository pour les entites du groupe avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base filtree par tenant_id."""
        query = self.db.query(ConsolidationEntity).filter(
            ConsolidationEntity.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(ConsolidationEntity.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ConsolidationEntity]:
        """Recuperer une entite par ID."""
        return self._base_query().filter(ConsolidationEntity.id == id).first()

    def get_by_code(self, code: str, perimeter_id: UUID) -> Optional[ConsolidationEntity]:
        """Recuperer une entite par code dans un perimetre."""
        return self._base_query().filter(
            ConsolidationEntity.code == code.upper(),
            ConsolidationEntity.perimeter_id == perimeter_id
        ).first()

    def code_exists(self, code: str, perimeter_id: UUID, exclude_id: UUID = None) -> bool:
        """Verifier si un code existe dans un perimetre."""
        query = self._base_query().filter(
            ConsolidationEntity.code == code.upper(),
            ConsolidationEntity.perimeter_id == perimeter_id
        )
        if exclude_id:
            query = query.filter(ConsolidationEntity.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: EntityFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "code",
        sort_dir: str = "asc"
    ) -> Tuple[List[ConsolidationEntity], int]:
        """Lister les entites avec filtres et pagination."""
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    ConsolidationEntity.code.ilike(term),
                    ConsolidationEntity.name.ilike(term),
                    ConsolidationEntity.legal_name.ilike(term)
                ))
            if filters.perimeter_id:
                query = query.filter(ConsolidationEntity.perimeter_id == filters.perimeter_id)
            if filters.country:
                query = query.filter(ConsolidationEntity.country == filters.country.upper())
            if filters.currency:
                query = query.filter(ConsolidationEntity.currency == filters.currency.upper())
            if filters.consolidation_method:
                query = query.filter(ConsolidationEntity.consolidation_method.in_(
                    [m.value for m in filters.consolidation_method]
                ))
            if filters.is_parent is not None:
                query = query.filter(ConsolidationEntity.is_parent == filters.is_parent)
            if filters.is_active is not None:
                query = query.filter(ConsolidationEntity.is_active == filters.is_active)

        total = query.count()
        sort_col = getattr(ConsolidationEntity, sort_by, ConsolidationEntity.code)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_perimeter(
        self,
        perimeter_id: UUID,
        include_inactive: bool = False
    ) -> List[ConsolidationEntity]:
        """Recuperer toutes les entites d'un perimetre."""
        query = self._base_query().filter(ConsolidationEntity.perimeter_id == perimeter_id)
        if not include_inactive:
            query = query.filter(ConsolidationEntity.is_active == True)
        return query.order_by(ConsolidationEntity.code).all()

    def get_parent_entity(self, perimeter_id: UUID) -> Optional[ConsolidationEntity]:
        """Recuperer la societe mere d'un perimetre."""
        return self._base_query().filter(
            ConsolidationEntity.perimeter_id == perimeter_id,
            ConsolidationEntity.is_parent == True,
            ConsolidationEntity.is_active == True
        ).first()

    def get_subsidiaries(self, parent_id: UUID) -> List[ConsolidationEntity]:
        """Recuperer les filiales directes d'une entite."""
        return self._base_query().filter(
            ConsolidationEntity.parent_entity_id == parent_id,
            ConsolidationEntity.is_active == True
        ).all()

    def get_entities_to_consolidate(
        self,
        perimeter_id: UUID,
        as_of_date: date
    ) -> List[ConsolidationEntity]:
        """Recuperer les entites a consolider a une date donnee."""
        query = self._base_query().filter(
            ConsolidationEntity.perimeter_id == perimeter_id,
            ConsolidationEntity.is_active == True,
            ConsolidationEntity.consolidation_method != ConsolidationMethod.NOT_CONSOLIDATED
        )

        # Filtre sur les dates d'acquisition/cession
        query = query.filter(
            or_(
                ConsolidationEntity.acquisition_date == None,
                ConsolidationEntity.acquisition_date <= as_of_date
            )
        ).filter(
            or_(
                ConsolidationEntity.disposal_date == None,
                ConsolidationEntity.disposal_date > as_of_date
            )
        )

        return query.all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ConsolidationEntity:
        """Creer une nouvelle entite."""
        if "code" in data:
            data["code"] = data["code"].upper()
        if "country" in data:
            data["country"] = data["country"].upper()
        if "currency" in data:
            data["currency"] = data["currency"].upper()

        # Calculer total_ownership_pct
        direct = Decimal(str(data.get("direct_ownership_pct", 0)))
        indirect = Decimal(str(data.get("indirect_ownership_pct", 0)))
        data["total_ownership_pct"] = direct + indirect

        entity = ConsolidationEntity(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: ConsolidationEntity,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ConsolidationEntity:
        """Mettre a jour une entite."""
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)

        # Recalculer total_ownership_pct si necessaire
        if "direct_ownership_pct" in data or "indirect_ownership_pct" in data:
            entity.total_ownership_pct = entity.direct_ownership_pct + entity.indirect_ownership_pct

        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: ConsolidationEntity, deleted_by: UUID = None) -> bool:
        """Supprimer logiquement une entite."""
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


# ============================================================================
# REPOSITORY: PARTICIPATIONS
# ============================================================================

class ParticipationRepository:
    """Repository pour les participations avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base filtree par tenant_id."""
        query = self.db.query(Participation).filter(
            Participation.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(Participation.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Participation]:
        return self._base_query().filter(Participation.id == id).first()

    def get_by_entities(self, parent_id: UUID, subsidiary_id: UUID) -> Optional[Participation]:
        return self._base_query().filter(
            Participation.parent_id == parent_id,
            Participation.subsidiary_id == subsidiary_id
        ).first()

    def exists(self, parent_id: UUID, subsidiary_id: UUID) -> bool:
        return self.get_by_entities(parent_id, subsidiary_id) is not None

    def get_by_parent(self, parent_id: UUID) -> List[Participation]:
        return self._base_query().filter(Participation.parent_id == parent_id).all()

    def get_by_subsidiary(self, subsidiary_id: UUID) -> List[Participation]:
        return self._base_query().filter(Participation.subsidiary_id == subsidiary_id).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Participation:
        # Calculer total_ownership
        direct = Decimal(str(data.get("direct_ownership", 0)))
        indirect = Decimal(str(data.get("indirect_ownership", 0)))
        data["total_ownership"] = direct + indirect

        entity = Participation(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: Participation, data: Dict[str, Any], updated_by: UUID = None) -> Participation:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)

        # Recalculer total si necessaire
        if "direct_ownership" in data or "indirect_ownership" in data:
            entity.total_ownership = entity.direct_ownership + entity.indirect_ownership

        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: Participation, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


# ============================================================================
# REPOSITORY: COURS DE CHANGE
# ============================================================================

class ExchangeRateRepository:
    """Repository pour les cours de change avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(ExchangeRate).filter(ExchangeRate.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Optional[ExchangeRate]:
        return self._base_query().filter(ExchangeRate.id == id).first()

    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: date
    ) -> Optional[ExchangeRate]:
        """Recuperer un cours pour une paire de devises a une date."""
        if from_currency == to_currency:
            # Retourner un taux de 1 pour la meme devise
            return ExchangeRate(
                tenant_id=self.tenant_id,
                from_currency=from_currency,
                to_currency=to_currency,
                rate_date=rate_date,
                closing_rate=Decimal("1"),
                average_rate=Decimal("1"),
                historical_rate=Decimal("1")
            )

        return self._base_query().filter(
            ExchangeRate.from_currency == from_currency.upper(),
            ExchangeRate.to_currency == to_currency.upper(),
            ExchangeRate.rate_date == rate_date
        ).first()

    def get_rates_for_period(
        self,
        from_currency: str,
        to_currency: str,
        start_date: date,
        end_date: date
    ) -> List[ExchangeRate]:
        """Recuperer les cours pour une periode."""
        return self._base_query().filter(
            ExchangeRate.from_currency == from_currency.upper(),
            ExchangeRate.to_currency == to_currency.upper(),
            ExchangeRate.rate_date >= start_date,
            ExchangeRate.rate_date <= end_date
        ).order_by(ExchangeRate.rate_date).all()

    def list(
        self,
        from_currency: str = None,
        to_currency: str = None,
        date_from: date = None,
        date_to: date = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ExchangeRate], int]:
        query = self._base_query()

        if from_currency:
            query = query.filter(ExchangeRate.from_currency == from_currency.upper())
        if to_currency:
            query = query.filter(ExchangeRate.to_currency == to_currency.upper())
        if date_from:
            query = query.filter(ExchangeRate.rate_date >= date_from)
        if date_to:
            query = query.filter(ExchangeRate.rate_date <= date_to)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(ExchangeRate.rate_date)).offset(offset).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ExchangeRate:
        data["from_currency"] = data["from_currency"].upper()
        data["to_currency"] = data["to_currency"].upper()

        entity = ExchangeRate(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def create_bulk(self, rates: List[Dict[str, Any]], created_by: UUID = None) -> List[ExchangeRate]:
        """Creer plusieurs cours de change."""
        entities = []
        for data in rates:
            data["from_currency"] = data["from_currency"].upper()
            data["to_currency"] = data["to_currency"].upper()
            entity = ExchangeRate(tenant_id=self.tenant_id, created_by=created_by, **data)
            self.db.add(entity)
            entities.append(entity)

        self.db.commit()
        for e in entities:
            self.db.refresh(e)
        return entities

    def exists(self, from_currency: str, to_currency: str, rate_date: date) -> bool:
        return self._base_query().filter(
            ExchangeRate.from_currency == from_currency.upper(),
            ExchangeRate.to_currency == to_currency.upper(),
            ExchangeRate.rate_date == rate_date
        ).count() > 0


# ============================================================================
# REPOSITORY: CONSOLIDATION
# ============================================================================

class ConsolidationRepository:
    """Repository pour les consolidations avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(Consolidation).filter(
            Consolidation.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(Consolidation.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Consolidation]:
        return self._base_query().filter(Consolidation.id == id).first()

    def get_by_code(self, code: str) -> Optional[Consolidation]:
        return self._base_query().filter(Consolidation.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(Consolidation.code == code.upper())
        if exclude_id:
            query = query.filter(Consolidation.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: ConsolidationFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Consolidation], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    Consolidation.code.ilike(term),
                    Consolidation.name.ilike(term)
                ))
            if filters.fiscal_year:
                query = query.filter(Consolidation.fiscal_year == filters.fiscal_year)
            if filters.status:
                query = query.filter(Consolidation.status.in_([s.value for s in filters.status]))
            if filters.perimeter_id:
                query = query.filter(Consolidation.perimeter_id == filters.perimeter_id)
            if filters.accounting_standard:
                query = query.filter(Consolidation.accounting_standard == filters.accounting_standard)
            if filters.date_from:
                query = query.filter(Consolidation.period_start >= filters.date_from)
            if filters.date_to:
                query = query.filter(Consolidation.period_end <= filters.date_to)

        total = query.count()
        sort_col = getattr(Consolidation, sort_by, Consolidation.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_perimeter(
        self,
        perimeter_id: UUID,
        fiscal_year: int = None
    ) -> List[Consolidation]:
        query = self._base_query().filter(Consolidation.perimeter_id == perimeter_id)
        if fiscal_year:
            query = query.filter(Consolidation.fiscal_year == fiscal_year)
        return query.order_by(desc(Consolidation.period_end)).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Consolidation:
        if "code" in data:
            data["code"] = data["code"].upper()

        entity = Consolidation(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: Consolidation, data: Dict[str, Any], updated_by: UUID = None) -> Consolidation:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_totals(
        self,
        consolidation: Consolidation,
        totals: Dict[str, Decimal],
        updated_by: UUID = None
    ) -> Consolidation:
        """Mettre a jour les totaux de la consolidation."""
        for key, value in totals.items():
            if hasattr(consolidation, key):
                setattr(consolidation, key, value)
        consolidation.updated_by = updated_by
        consolidation.version += 1
        self.db.commit()
        self.db.refresh(consolidation)
        return consolidation

    def change_status(
        self,
        consolidation: Consolidation,
        new_status: ConsolidationStatus,
        user_id: UUID = None
    ) -> Consolidation:
        """Changer le statut d'une consolidation."""
        consolidation.status = new_status
        now = datetime.utcnow()

        if new_status == ConsolidationStatus.PENDING_REVIEW:
            consolidation.submitted_at = now
            consolidation.submitted_by = user_id
        elif new_status == ConsolidationStatus.VALIDATED:
            consolidation.validated_at = now
            consolidation.validated_by = user_id
        elif new_status == ConsolidationStatus.PUBLISHED:
            consolidation.published_at = now
            consolidation.published_by = user_id

        consolidation.version += 1
        self.db.commit()
        self.db.refresh(consolidation)
        return consolidation

    def soft_delete(self, entity: Consolidation, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def get_packages_count(self, consolidation_id: UUID) -> Dict[str, int]:
        """Compter les paquets par statut."""
        results = self.db.query(
            ConsolidationPackage.status,
            func.count(ConsolidationPackage.id)
        ).filter(
            ConsolidationPackage.tenant_id == self.tenant_id,
            ConsolidationPackage.consolidation_id == consolidation_id,
            ConsolidationPackage.is_deleted == False
        ).group_by(ConsolidationPackage.status).all()

        return {str(status): count for status, count in results}


# ============================================================================
# REPOSITORY: PAQUET DE CONSOLIDATION
# ============================================================================

class ConsolidationPackageRepository:
    """Repository pour les paquets de consolidation avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(ConsolidationPackage).filter(
            ConsolidationPackage.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(ConsolidationPackage.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ConsolidationPackage]:
        return self._base_query().filter(ConsolidationPackage.id == id).first()

    def get_by_consolidation_entity(
        self,
        consolidation_id: UUID,
        entity_id: UUID
    ) -> Optional[ConsolidationPackage]:
        return self._base_query().filter(
            ConsolidationPackage.consolidation_id == consolidation_id,
            ConsolidationPackage.entity_id == entity_id
        ).first()

    def exists(self, consolidation_id: UUID, entity_id: UUID) -> bool:
        return self.get_by_consolidation_entity(consolidation_id, entity_id) is not None

    def list(
        self,
        filters: PackageFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[ConsolidationPackage], int]:
        query = self._base_query()

        if filters:
            if filters.consolidation_id:
                query = query.filter(ConsolidationPackage.consolidation_id == filters.consolidation_id)
            if filters.entity_id:
                query = query.filter(ConsolidationPackage.entity_id == filters.entity_id)
            if filters.status:
                query = query.filter(ConsolidationPackage.status.in_([s.value for s in filters.status]))
            if filters.is_audited is not None:
                query = query.filter(ConsolidationPackage.is_audited == filters.is_audited)

        total = query.count()
        sort_col = getattr(ConsolidationPackage, sort_by, ConsolidationPackage.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_consolidation(
        self,
        consolidation_id: UUID,
        status: List[PackageStatus] = None
    ) -> List[ConsolidationPackage]:
        query = self._base_query().filter(
            ConsolidationPackage.consolidation_id == consolidation_id
        )
        if status:
            query = query.filter(ConsolidationPackage.status.in_([s.value for s in status]))
        return query.all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ConsolidationPackage:
        entity = ConsolidationPackage(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: ConsolidationPackage,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ConsolidationPackage:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def submit(self, package: ConsolidationPackage, submitted_by: UUID) -> ConsolidationPackage:
        package.status = PackageStatus.SUBMITTED
        package.submitted_at = datetime.utcnow()
        package.submitted_by = submitted_by
        package.version += 1
        self.db.commit()
        self.db.refresh(package)
        return package

    def validate(self, package: ConsolidationPackage, validated_by: UUID) -> ConsolidationPackage:
        package.status = PackageStatus.VALIDATED
        package.validated_at = datetime.utcnow()
        package.validated_by = validated_by
        package.version += 1
        self.db.commit()
        self.db.refresh(package)
        return package

    def reject(
        self,
        package: ConsolidationPackage,
        rejected_by: UUID,
        reason: str
    ) -> ConsolidationPackage:
        package.status = PackageStatus.REJECTED
        package.rejected_at = datetime.utcnow()
        package.rejected_by = rejected_by
        package.rejection_reason = reason
        package.version += 1
        self.db.commit()
        self.db.refresh(package)
        return package

    def soft_delete(self, entity: ConsolidationPackage, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


# ============================================================================
# REPOSITORY: ELIMINATIONS
# ============================================================================

class EliminationRepository:
    """Repository pour les eliminations avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(EliminationEntry).filter(
            EliminationEntry.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(EliminationEntry.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[EliminationEntry]:
        return self._base_query().filter(EliminationEntry.id == id).first()

    def list_by_consolidation(
        self,
        consolidation_id: UUID,
        elimination_type: EliminationType = None,
        is_validated: bool = None
    ) -> List[EliminationEntry]:
        query = self._base_query().filter(
            EliminationEntry.consolidation_id == consolidation_id
        )
        if elimination_type:
            query = query.filter(EliminationEntry.elimination_type == elimination_type)
        if is_validated is not None:
            query = query.filter(EliminationEntry.is_validated == is_validated)
        return query.order_by(EliminationEntry.created_at).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> EliminationEntry:
        entity = EliminationEntry(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def create_bulk(
        self,
        eliminations: List[Dict[str, Any]],
        created_by: UUID = None
    ) -> List[EliminationEntry]:
        entities = []
        for data in eliminations:
            entity = EliminationEntry(tenant_id=self.tenant_id, created_by=created_by, **data)
            self.db.add(entity)
            entities.append(entity)

        self.db.commit()
        for e in entities:
            self.db.refresh(e)
        return entities

    def update(
        self,
        entity: EliminationEntry,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> EliminationEntry:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def validate(self, entity: EliminationEntry, validated_by: UUID) -> EliminationEntry:
        entity.is_validated = True
        entity.validated_at = datetime.utcnow()
        entity.validated_by = validated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete_by_consolidation(self, consolidation_id: UUID, deleted_by: UUID = None) -> int:
        """Supprimer toutes les eliminations d'une consolidation."""
        count = self._base_query().filter(
            EliminationEntry.consolidation_id == consolidation_id
        ).update({
            "is_deleted": True,
            "deleted_at": datetime.utcnow(),
            "deleted_by": deleted_by
        })
        self.db.commit()
        return count

    def soft_delete(self, entity: EliminationEntry, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


# ============================================================================
# REPOSITORY: RECONCILIATION INTERCOMPANY
# ============================================================================

class IntercompanyReconciliationRepository:
    """Repository pour les reconciliations avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(IntercompanyReconciliation).filter(
            IntercompanyReconciliation.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(IntercompanyReconciliation.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[IntercompanyReconciliation]:
        return self._base_query().filter(IntercompanyReconciliation.id == id).first()

    def list(
        self,
        filters: ReconciliationFilters = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[IntercompanyReconciliation], int]:
        query = self._base_query()

        if filters:
            if filters.consolidation_id:
                query = query.filter(IntercompanyReconciliation.consolidation_id == filters.consolidation_id)
            if filters.entity_id:
                query = query.filter(or_(
                    IntercompanyReconciliation.entity1_id == filters.entity_id,
                    IntercompanyReconciliation.entity2_id == filters.entity_id
                ))
            if filters.transaction_type:
                query = query.filter(IntercompanyReconciliation.transaction_type == filters.transaction_type)
            if filters.is_reconciled is not None:
                query = query.filter(IntercompanyReconciliation.is_reconciled == filters.is_reconciled)
            if filters.is_within_tolerance is not None:
                query = query.filter(IntercompanyReconciliation.is_within_tolerance == filters.is_within_tolerance)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(IntercompanyReconciliation.created_at)).offset(offset).limit(page_size).all()

        return items, total

    def get_summary(self, consolidation_id: UUID) -> Dict[str, Any]:
        """Obtenir un resume des reconciliations."""
        query = self._base_query().filter(
            IntercompanyReconciliation.consolidation_id == consolidation_id
        )

        total = query.count()
        reconciled = query.filter(IntercompanyReconciliation.is_reconciled == True).count()
        within_tolerance = query.filter(IntercompanyReconciliation.is_within_tolerance == True).count()

        total_diff = self.db.query(func.sum(func.abs(IntercompanyReconciliation.difference))).filter(
            IntercompanyReconciliation.tenant_id == self.tenant_id,
            IntercompanyReconciliation.consolidation_id == consolidation_id,
            IntercompanyReconciliation.is_deleted == False
        ).scalar() or Decimal("0.00")

        return {
            "total_pairs": total,
            "reconciled_count": reconciled,
            "unreconciled_count": total - reconciled,
            "within_tolerance_count": within_tolerance,
            "total_difference": total_diff,
            "reconciliation_rate": Decimal(reconciled / total * 100) if total > 0 else Decimal("0")
        }

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> IntercompanyReconciliation:
        # Calculer l'ecart
        amount1 = Decimal(str(data.get("amount_entity1", 0)))
        amount2 = Decimal(str(data.get("amount_entity2", 0)))
        difference = abs(amount1 - amount2)
        data["difference"] = difference

        if amount1 != 0:
            data["difference_pct"] = (difference / abs(amount1)) * 100
        else:
            data["difference_pct"] = Decimal("0")

        # Verifier tolerance
        tolerance_amount = Decimal(str(data.get("tolerance_amount", 0)))
        tolerance_pct = Decimal(str(data.get("tolerance_pct", 0)))
        data["is_within_tolerance"] = (
            difference <= tolerance_amount or
            (data["difference_pct"] <= tolerance_pct if amount1 != 0 else True)
        )

        entity = IntercompanyReconciliation(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: IntercompanyReconciliation,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> IntercompanyReconciliation:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)

        # Recalculer si montants changent
        if "amount_entity1" in data or "amount_entity2" in data:
            entity.difference = abs(entity.amount_entity1 - entity.amount_entity2)
            if entity.amount_entity1 != 0:
                entity.difference_pct = (entity.difference / abs(entity.amount_entity1)) * 100
            entity.is_within_tolerance = (
                entity.difference <= entity.tolerance_amount or
                (entity.difference_pct <= entity.tolerance_pct if entity.amount_entity1 != 0 else True)
            )

        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def reconcile(
        self,
        entity: IntercompanyReconciliation,
        reconciled_by: UUID
    ) -> IntercompanyReconciliation:
        entity.is_reconciled = True
        entity.reconciled_at = datetime.utcnow()
        entity.reconciled_by = reconciled_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: IntercompanyReconciliation, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


# ============================================================================
# REPOSITORY: RAPPORTS
# ============================================================================

class ConsolidatedReportRepository:
    """Repository pour les rapports consolides avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(ConsolidatedReport).filter(
            ConsolidatedReport.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(ConsolidatedReport.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ConsolidatedReport]:
        return self._base_query().filter(ConsolidatedReport.id == id).first()

    def list_by_consolidation(
        self,
        consolidation_id: UUID,
        report_type: ReportType = None
    ) -> List[ConsolidatedReport]:
        query = self._base_query().filter(
            ConsolidatedReport.consolidation_id == consolidation_id
        )
        if report_type:
            query = query.filter(ConsolidatedReport.report_type == report_type)
        return query.order_by(ConsolidatedReport.created_at.desc()).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ConsolidatedReport:
        entity = ConsolidatedReport(
            tenant_id=self.tenant_id,
            created_by=created_by,
            generated_at=datetime.utcnow(),
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: ConsolidatedReport,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ConsolidatedReport:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def finalize(self, entity: ConsolidatedReport, finalized_by: UUID) -> ConsolidatedReport:
        entity.is_final = True
        entity.finalized_at = datetime.utcnow()
        entity.finalized_by = finalized_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: ConsolidatedReport, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


# ============================================================================
# REPOSITORY: AUDIT LOG
# ============================================================================

class ConsolidationAuditLogRepository:
    """Repository pour les logs d'audit avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(ConsolidationAuditLog).filter(
            ConsolidationAuditLog.tenant_id == self.tenant_id
        )

    def create(
        self,
        action: str,
        user_id: UUID,
        consolidation_id: UUID = None,
        entity_id: UUID = None,
        target_type: str = None,
        target_id: UUID = None,
        old_values: Dict = None,
        new_values: Dict = None,
        description: str = None,
        user_name: str = None,
        user_ip: str = None,
        action_category: str = None
    ) -> ConsolidationAuditLog:
        """Creer une entree de log d'audit."""
        log = ConsolidationAuditLog(
            tenant_id=self.tenant_id,
            consolidation_id=consolidation_id,
            entity_id=entity_id,
            action=action,
            action_category=action_category,
            target_type=target_type,
            target_id=target_id,
            old_values=old_values or {},
            new_values=new_values or {},
            description=description,
            user_id=user_id,
            user_name=user_name,
            user_ip=user_ip,
            timestamp=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list(
        self,
        consolidation_id: UUID = None,
        action: str = None,
        user_id: UUID = None,
        date_from: datetime = None,
        date_to: datetime = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ConsolidationAuditLog], int]:
        query = self._base_query()

        if consolidation_id:
            query = query.filter(ConsolidationAuditLog.consolidation_id == consolidation_id)
        if action:
            query = query.filter(ConsolidationAuditLog.action == action)
        if user_id:
            query = query.filter(ConsolidationAuditLog.user_id == user_id)
        if date_from:
            query = query.filter(ConsolidationAuditLog.timestamp >= date_from)
        if date_to:
            query = query.filter(ConsolidationAuditLog.timestamp <= date_to)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(ConsolidationAuditLog.timestamp)).offset(offset).limit(page_size).all()

        return items, total
