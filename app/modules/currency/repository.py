"""
AZALS MODULE - CURRENCY: Repository
====================================

Repository avec isolation tenant stricte.
Toutes les requetes sont filtrees par tenant_id.
"""
from __future__ import annotations


from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.orm import Session, joinedload

from .models import (
    Currency, ExchangeRate, CurrencyConfig, ExchangeGainLoss,
    CurrencyRevaluation, CurrencyConversionLog, RateAlert,
    CurrencyStatus, RateSource, RateType, GainLossType, RevaluationStatus
)
from .schemas import CurrencyFilters, ExchangeRateFilters, GainLossFilters


class CurrencyRepository:
    """Repository Currency avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base filtree par tenant."""
        query = self.db.query(Currency).filter(Currency.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(Currency.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Currency]:
        """Recupere une devise par ID."""
        return self._base_query().filter(Currency.id == id).first()

    def get_by_code(self, code: str) -> Optional[Currency]:
        """Recupere une devise par code ISO."""
        return self._base_query().filter(Currency.code == code.upper()).first()

    def exists(self, code: str) -> bool:
        """Verifie si une devise existe."""
        return self._base_query().filter(Currency.code == code.upper()).count() > 0

    def get_default(self) -> Optional[Currency]:
        """Recupere la devise par defaut."""
        return self._base_query().filter(
            Currency.is_default == True,
            Currency.is_enabled == True
        ).first()

    def get_reporting(self) -> Optional[Currency]:
        """Recupere la devise de reporting."""
        return self._base_query().filter(
            Currency.is_reporting == True,
            Currency.is_enabled == True
        ).first()

    def list_enabled(self) -> List[Currency]:
        """Liste les devises actives."""
        return self._base_query().filter(
            Currency.is_enabled == True,
            Currency.status == CurrencyStatus.ACTIVE.value
        ).order_by(Currency.code).all()

    def list(
        self,
        filters: CurrencyFilters = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Currency], int]:
        """Liste les devises avec filtres."""
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    Currency.code.ilike(term),
                    Currency.name.ilike(term),
                    Currency.symbol.ilike(term)
                ))
            if filters.is_enabled is not None:
                query = query.filter(Currency.is_enabled == filters.is_enabled)
            if filters.is_major is not None:
                query = query.filter(Currency.is_major == filters.is_major)
            if filters.status:
                query = query.filter(Currency.status == filters.status.value)

        total = query.count()
        query = query.order_by(
            desc(Currency.is_default),
            desc(Currency.is_reporting),
            Currency.code
        )
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        """Autocomplete devises."""
        if len(prefix) < 1:
            return []
        query = self._base_query().filter(
            Currency.is_enabled == True,
            or_(
                Currency.code.ilike(f"{prefix}%"),
                Currency.name.ilike(f"%{prefix}%")
            )
        )
        results = query.order_by(Currency.code).limit(limit).all()
        return [
            {
                "id": str(c.id),
                "code": c.code,
                "name": c.name,
                "label": f"{c.code} - {c.name}",
                "symbol": c.symbol
            }
            for c in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Currency:
        """Cree une devise."""
        entity = Currency(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: Currency, data: Dict[str, Any], updated_by: UUID = None) -> Currency:
        """Met a jour une devise."""
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def set_default(self, currency: Currency, updated_by: UUID = None) -> Currency:
        """Definit une devise comme devise par defaut."""
        # Retirer le flag des autres
        self._base_query().filter(Currency.is_default == True).update(
            {"is_default": False, "updated_by": updated_by}
        )
        currency.is_default = True
        currency.is_enabled = True
        currency.updated_by = updated_by
        self.db.commit()
        self.db.refresh(currency)
        return currency

    def set_reporting(self, currency: Currency, updated_by: UUID = None) -> Currency:
        """Definit une devise comme devise de reporting."""
        self._base_query().filter(Currency.is_reporting == True).update(
            {"is_reporting": False, "updated_by": updated_by}
        )
        currency.is_reporting = True
        currency.is_enabled = True
        currency.updated_by = updated_by
        self.db.commit()
        self.db.refresh(currency)
        return currency

    def soft_delete(self, entity: Currency, deleted_by: UUID = None) -> bool:
        """Suppression logique."""
        entity.is_deleted = True
        entity.is_enabled = False
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: Currency) -> Currency:
        """Restaure une devise supprimee."""
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def bulk_create(self, currencies_data: List[Dict[str, Any]], created_by: UUID = None) -> int:
        """Creation en masse de devises."""
        created = 0
        for data in currencies_data:
            if not self.exists(data.get("code", "")):
                entity = Currency(
                    tenant_id=self.tenant_id,
                    created_by=created_by,
                    **data
                )
                self.db.add(entity)
                created += 1
        self.db.commit()
        return created


class ExchangeRateRepository:
    """Repository ExchangeRate avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base filtree par tenant."""
        query = self.db.query(ExchangeRate).filter(ExchangeRate.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(ExchangeRate.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ExchangeRate]:
        """Recupere un taux par ID."""
        return self._base_query().filter(ExchangeRate.id == id).first()

    def get_rate(
        self,
        base_code: str,
        quote_code: str,
        rate_date: date = None
    ) -> Optional[ExchangeRate]:
        """Recupere le taux pour une paire a une date."""
        base_code = base_code.upper()
        quote_code = quote_code.upper()
        rate_date = rate_date or date.today()

        # Taux direct
        rate = self._base_query().filter(
            ExchangeRate.base_currency_code == base_code,
            ExchangeRate.quote_currency_code == quote_code,
            ExchangeRate.rate_date <= rate_date
        ).order_by(desc(ExchangeRate.rate_date)).first()

        return rate

    def get_rate_exact_date(
        self,
        base_code: str,
        quote_code: str,
        rate_date: date
    ) -> Optional[ExchangeRate]:
        """Recupere le taux pour une date exacte."""
        return self._base_query().filter(
            ExchangeRate.base_currency_code == base_code.upper(),
            ExchangeRate.quote_currency_code == quote_code.upper(),
            ExchangeRate.rate_date == rate_date
        ).first()

    def get_latest_rate(self, base_code: str, quote_code: str) -> Optional[ExchangeRate]:
        """Recupere le dernier taux disponible."""
        return self._base_query().filter(
            ExchangeRate.base_currency_code == base_code.upper(),
            ExchangeRate.quote_currency_code == quote_code.upper()
        ).order_by(desc(ExchangeRate.rate_date)).first()

    def list_rates_for_date(self, rate_date: date, base_code: str = None) -> List[ExchangeRate]:
        """Liste les taux pour une date."""
        query = self._base_query().filter(ExchangeRate.rate_date == rate_date)
        if base_code:
            query = query.filter(ExchangeRate.base_currency_code == base_code.upper())
        return query.order_by(ExchangeRate.quote_currency_code).all()

    def list(
        self,
        filters: ExchangeRateFilters = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "rate_date",
        sort_dir: str = "desc"
    ) -> Tuple[List[ExchangeRate], int]:
        """Liste les taux avec filtres."""
        query = self._base_query()

        if filters:
            if filters.base_currency:
                query = query.filter(
                    ExchangeRate.base_currency_code == filters.base_currency.upper()
                )
            if filters.quote_currency:
                query = query.filter(
                    ExchangeRate.quote_currency_code == filters.quote_currency.upper()
                )
            if filters.date_from:
                query = query.filter(ExchangeRate.rate_date >= filters.date_from)
            if filters.date_to:
                query = query.filter(ExchangeRate.rate_date <= filters.date_to)
            if filters.rate_type:
                query = query.filter(ExchangeRate.rate_type == filters.rate_type.value)
            if filters.source:
                query = query.filter(ExchangeRate.source == filters.source.value)
            if filters.is_manual is not None:
                query = query.filter(ExchangeRate.is_manual == filters.is_manual)

        total = query.count()
        sort_col = getattr(ExchangeRate, sort_by, ExchangeRate.rate_date)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_history(
        self,
        base_code: str,
        quote_code: str,
        start_date: date,
        end_date: date,
        limit: int = 365
    ) -> List[ExchangeRate]:
        """Historique des taux."""
        return self._base_query().filter(
            ExchangeRate.base_currency_code == base_code.upper(),
            ExchangeRate.quote_currency_code == quote_code.upper(),
            ExchangeRate.rate_date >= start_date,
            ExchangeRate.rate_date <= end_date
        ).order_by(desc(ExchangeRate.rate_date)).limit(limit).all()

    def exists(self, base_code: str, quote_code: str, rate_date: date) -> bool:
        """Verifie si un taux existe."""
        return self._base_query().filter(
            ExchangeRate.base_currency_code == base_code.upper(),
            ExchangeRate.quote_currency_code == quote_code.upper(),
            ExchangeRate.rate_date == rate_date
        ).count() > 0

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ExchangeRate:
        """Cree un taux de change."""
        # Calculer le taux inverse si non fourni
        if "inverse_rate" not in data or not data["inverse_rate"]:
            if data.get("rate"):
                data["inverse_rate"] = (Decimal("1") / Decimal(str(data["rate"]))).quantize(
                    Decimal("0.000000000001")
                )

        entity = ExchangeRate(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: ExchangeRate, data: Dict[str, Any], updated_by: UUID = None) -> ExchangeRate:
        """Met a jour un taux."""
        if entity.is_locked:
            raise ValueError("Ce taux est verrouille")

        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        # Recalculer inverse si rate change
        if "rate" in data:
            entity.inverse_rate = (Decimal("1") / entity.rate).quantize(
                Decimal("0.000000000001")
            )

        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def upsert(
        self,
        base_code: str,
        quote_code: str,
        rate_date: date,
        rate: Decimal,
        source: RateSource = RateSource.MANUAL,
        rate_type: RateType = RateType.SPOT,
        created_by: UUID = None
    ) -> ExchangeRate:
        """Cree ou met a jour un taux."""
        existing = self.get_rate_exact_date(base_code, quote_code, rate_date)

        if existing:
            return self.update(existing, {
                "rate": rate,
                "source": source.value,
                "rate_type": rate_type.value,
                "fetched_at": datetime.utcnow()
            }, created_by)
        else:
            return self.create({
                "base_currency_code": base_code.upper(),
                "quote_currency_code": quote_code.upper(),
                "rate": rate,
                "rate_date": rate_date,
                "source": source.value,
                "rate_type": rate_type.value,
                "is_manual": source == RateSource.MANUAL,
                "fetched_at": datetime.utcnow()
            }, created_by)

    def soft_delete(self, entity: ExchangeRate, deleted_by: UUID = None) -> bool:
        """Suppression logique."""
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def lock(self, entity: ExchangeRate, updated_by: UUID = None) -> ExchangeRate:
        """Verrouille un taux."""
        entity.is_locked = True
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_average_rate(
        self,
        base_code: str,
        quote_code: str,
        start_date: date,
        end_date: date
    ) -> Optional[Decimal]:
        """Calcule le taux moyen sur une periode."""
        result = self._base_query().filter(
            ExchangeRate.base_currency_code == base_code.upper(),
            ExchangeRate.quote_currency_code == quote_code.upper(),
            ExchangeRate.rate_date >= start_date,
            ExchangeRate.rate_date <= end_date
        ).with_entities(func.avg(ExchangeRate.rate)).scalar()

        return Decimal(str(result)).quantize(Decimal("0.000001")) if result else None

    def delete_old_rates(self, days_to_keep: int = 365 * 5) -> int:
        """Supprime les anciens taux (hard delete)."""
        cutoff = date.today() - timedelta(days=days_to_keep)
        deleted = self._base_query().filter(
            ExchangeRate.rate_date < cutoff,
            ExchangeRate.is_locked == False
        ).delete()
        self.db.commit()
        return deleted


class CurrencyConfigRepository:
    """Repository CurrencyConfig avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def get(self) -> Optional[CurrencyConfig]:
        """Recupere la configuration du tenant."""
        return self.db.query(CurrencyConfig).filter(
            CurrencyConfig.tenant_id == self.tenant_id
        ).first()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> CurrencyConfig:
        """Cree la configuration."""
        entity = CurrencyConfig(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: CurrencyConfig, data: Dict[str, Any], updated_by: UUID = None) -> CurrencyConfig:
        """Met a jour la configuration."""
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_or_create(self, created_by: UUID = None) -> CurrencyConfig:
        """Recupere ou cree la configuration."""
        config = self.get()
        if not config:
            config = self.create({}, created_by)
        return config


class ExchangeGainLossRepository:
    """Repository ExchangeGainLoss avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base filtree par tenant."""
        query = self.db.query(ExchangeGainLoss).filter(
            ExchangeGainLoss.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(ExchangeGainLoss.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ExchangeGainLoss]:
        """Recupere un gain/perte par ID."""
        return self._base_query().filter(ExchangeGainLoss.id == id).first()

    def get_by_document(self, document_type: str, document_id: UUID) -> List[ExchangeGainLoss]:
        """Recupere les gains/pertes pour un document."""
        return self._base_query().filter(
            ExchangeGainLoss.document_type == document_type,
            ExchangeGainLoss.document_id == document_id
        ).order_by(ExchangeGainLoss.created_at).all()

    def list(
        self,
        filters: GainLossFilters = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ExchangeGainLoss], int]:
        """Liste les gains/pertes."""
        query = self._base_query()

        if filters:
            if filters.gain_loss_type:
                query = query.filter(
                    ExchangeGainLoss.gain_loss_type == filters.gain_loss_type.value
                )
            if filters.document_type:
                query = query.filter(
                    ExchangeGainLoss.document_type == filters.document_type
                )
            if filters.currency:
                query = query.filter(
                    ExchangeGainLoss.original_currency_code == filters.currency.upper()
                )
            if filters.date_from:
                query = query.filter(ExchangeGainLoss.booking_date >= filters.date_from)
            if filters.date_to:
                query = query.filter(ExchangeGainLoss.booking_date <= filters.date_to)
            if filters.is_posted is not None:
                query = query.filter(ExchangeGainLoss.is_posted == filters.is_posted)

        total = query.count()
        query = query.order_by(desc(ExchangeGainLoss.created_at))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_summary(
        self,
        start_date: date,
        end_date: date,
        currency: str = None
    ) -> Dict[str, Any]:
        """Resume des gains/pertes."""
        query = self._base_query().filter(
            ExchangeGainLoss.booking_date >= start_date,
            ExchangeGainLoss.booking_date <= end_date
        )

        if currency:
            query = query.filter(
                ExchangeGainLoss.reporting_currency_code == currency.upper()
            )

        entries = query.all()

        realized = [e for e in entries if e.gain_loss_type == GainLossType.REALIZED.value]
        unrealized = [e for e in entries if e.gain_loss_type == GainLossType.UNREALIZED.value]

        return {
            "period_start": start_date,
            "period_end": end_date,
            "realized_gains": sum(e.gain_loss_amount for e in realized if e.gain_loss_amount > 0),
            "realized_losses": sum(e.gain_loss_amount for e in realized if e.gain_loss_amount < 0),
            "realized_net": sum(e.gain_loss_amount for e in realized),
            "unrealized_gains": sum(e.gain_loss_amount for e in unrealized if e.gain_loss_amount > 0),
            "unrealized_losses": sum(e.gain_loss_amount for e in unrealized if e.gain_loss_amount < 0),
            "unrealized_net": sum(e.gain_loss_amount for e in unrealized),
            "total_net": sum(e.gain_loss_amount for e in entries),
            "entry_count": len(entries)
        }

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ExchangeGainLoss:
        """Cree un gain/perte."""
        entity = ExchangeGainLoss(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def mark_posted(
        self,
        entity: ExchangeGainLoss,
        journal_entry_id: UUID,
        posting_date: date,
        updated_by: UUID = None
    ) -> ExchangeGainLoss:
        """Marque comme comptabilise."""
        entity.is_posted = True
        entity.journal_entry_id = journal_entry_id
        entity.posting_date = posting_date
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: ExchangeGainLoss, deleted_by: UUID = None) -> bool:
        """Suppression logique."""
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class CurrencyRevaluationRepository:
    """Repository CurrencyRevaluation avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base filtree par tenant."""
        query = self.db.query(CurrencyRevaluation).filter(
            CurrencyRevaluation.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(CurrencyRevaluation.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[CurrencyRevaluation]:
        """Recupere une reevaluation par ID."""
        return self._base_query().filter(CurrencyRevaluation.id == id).first()

    def get_by_code(self, code: str) -> Optional[CurrencyRevaluation]:
        """Recupere une reevaluation par code."""
        return self._base_query().filter(CurrencyRevaluation.code == code.upper()).first()

    def get_for_period(self, period: str) -> Optional[CurrencyRevaluation]:
        """Recupere la reevaluation pour une periode."""
        return self._base_query().filter(
            CurrencyRevaluation.period == period,
            CurrencyRevaluation.status != RevaluationStatus.CANCELLED.value
        ).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: RevaluationStatus = None
    ) -> Tuple[List[CurrencyRevaluation], int]:
        """Liste les reevaluations."""
        query = self._base_query()

        if status:
            query = query.filter(CurrencyRevaluation.status == status.value)

        total = query.count()
        query = query.order_by(desc(CurrencyRevaluation.revaluation_date))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_next_code(self) -> str:
        """Genere le prochain code."""
        year = datetime.utcnow().year
        prefix = f"REVAL-{year}-"

        last = self.db.query(CurrencyRevaluation).filter(
            CurrencyRevaluation.tenant_id == self.tenant_id,
            CurrencyRevaluation.code.like(f"{prefix}%")
        ).order_by(desc(CurrencyRevaluation.code)).first()

        if last:
            try:
                last_num = int(last.code.split("-")[-1])
                return f"{prefix}{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}0001"

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> CurrencyRevaluation:
        """Cree une reevaluation."""
        if "code" not in data or not data["code"]:
            data["code"] = self.get_next_code()

        entity = CurrencyRevaluation(
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
        entity: CurrencyRevaluation,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> CurrencyRevaluation:
        """Met a jour une reevaluation."""
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def post(
        self,
        entity: CurrencyRevaluation,
        journal_entry_id: UUID,
        posted_by: UUID
    ) -> CurrencyRevaluation:
        """Comptabilise la reevaluation."""
        entity.status = RevaluationStatus.POSTED.value
        entity.journal_entry_id = journal_entry_id
        entity.posted_at = datetime.utcnow()
        entity.posted_by = posted_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def cancel(self, entity: CurrencyRevaluation, updated_by: UUID = None) -> CurrencyRevaluation:
        """Annule une reevaluation."""
        entity.status = RevaluationStatus.CANCELLED.value
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: CurrencyRevaluation, deleted_by: UUID = None) -> bool:
        """Suppression logique."""
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class CurrencyConversionLogRepository:
    """Repository pour les logs de conversion."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def create(self, data: Dict[str, Any]) -> CurrencyConversionLog:
        """Enregistre une conversion."""
        entity = CurrencyConversionLog(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        return entity

    def list_for_document(
        self,
        document_type: str,
        document_id: UUID
    ) -> List[CurrencyConversionLog]:
        """Liste les conversions pour un document."""
        return self.db.query(CurrencyConversionLog).filter(
            CurrencyConversionLog.tenant_id == self.tenant_id,
            CurrencyConversionLog.document_type == document_type,
            CurrencyConversionLog.document_id == document_id
        ).order_by(CurrencyConversionLog.converted_at).all()


class RateAlertRepository:
    """Repository pour les alertes de taux."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(RateAlert).filter(RateAlert.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Optional[RateAlert]:
        return self._base_query().filter(RateAlert.id == id).first()

    def list_unread(self) -> List[RateAlert]:
        """Liste les alertes non lues."""
        return self._base_query().filter(
            RateAlert.is_read == False
        ).order_by(desc(RateAlert.created_at)).all()

    def list_unacknowledged(self) -> List[RateAlert]:
        """Liste les alertes non acquittees."""
        return self._base_query().filter(
            RateAlert.is_acknowledged == False
        ).order_by(desc(RateAlert.created_at)).all()

    def create(self, data: Dict[str, Any]) -> RateAlert:
        """Cree une alerte."""
        entity = RateAlert(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def mark_read(self, entity: RateAlert) -> RateAlert:
        """Marque comme lue."""
        entity.is_read = True
        self.db.commit()
        return entity

    def acknowledge(self, entity: RateAlert, user_id: UUID) -> RateAlert:
        """Acquitte l'alerte."""
        entity.is_acknowledged = True
        entity.acknowledged_by = user_id
        entity.acknowledged_at = datetime.utcnow()
        self.db.commit()
        return entity

    def mark_all_read(self) -> int:
        """Marque toutes les alertes comme lues."""
        updated = self._base_query().filter(RateAlert.is_read == False).update(
            {"is_read": True}
        )
        self.db.commit()
        return updated
