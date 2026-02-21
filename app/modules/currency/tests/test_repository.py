"""
Tests unitaires pour les repositories Currency.
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from sqlalchemy.orm import Session

from app.modules.currency.repository import (
    CurrencyRepository, ExchangeRateRepository, CurrencyConfigRepository,
    ExchangeGainLossRepository, CurrencyRevaluationRepository,
    RateAlertRepository
)
from app.modules.currency.models import (
    Currency, ExchangeRate, CurrencyConfig, ExchangeGainLoss,
    CurrencyRevaluation, RateAlert,
    CurrencyStatus, RateSource, RateType, GainLossType, RevaluationStatus
)
from app.modules.currency.schemas import (
    CurrencyFilters, ExchangeRateFilters, GainLossFilters
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Session de base de donnees mockee."""
    db = Mock(spec=Session)
    return db


@pytest.fixture
def tenant_id():
    """Tenant ID de test."""
    return str(uuid4())


# ============================================================================
# TESTS CURRENCY REPOSITORY
# ============================================================================

class TestCurrencyRepository:
    """Tests pour CurrencyRepository."""

    def test_base_query_filters_tenant(self, mock_db, tenant_id):
        """_base_query filtre par tenant_id."""
        repo = CurrencyRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        repo._base_query()

        mock_db.query.assert_called_once_with(Currency)
        # Verifie que filter est appele avec tenant_id
        assert mock_query.filter.called

    def test_base_query_excludes_deleted(self, mock_db, tenant_id):
        """_base_query exclut les supprimes par defaut."""
        repo = CurrencyRepository(mock_db, tenant_id, include_deleted=False)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        repo._base_query()

        # filter doit etre appele 2 fois (tenant + is_deleted)
        assert mock_query.filter.call_count == 2

    def test_base_query_includes_deleted(self, mock_db, tenant_id):
        """_base_query inclut les supprimes si demande."""
        repo = CurrencyRepository(mock_db, tenant_id, include_deleted=True)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        repo._base_query()

        # filter doit etre appele 1 seule fois (tenant uniquement)
        assert mock_query.filter.call_count == 1

    def test_get_by_code(self, mock_db, tenant_id):
        """Recuperation par code."""
        repo = CurrencyRepository(mock_db, tenant_id)

        mock_currency = Mock(spec=Currency)
        mock_currency.code = "EUR"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_currency

        result = repo.get_by_code("eur")  # Minuscules

        # Verifie que le code est mis en majuscules
        assert result == mock_currency

    def test_exists(self, mock_db, tenant_id):
        """Verification d'existence."""
        repo = CurrencyRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1

        result = repo.exists("EUR")

        assert result == True

    def test_not_exists(self, mock_db, tenant_id):
        """Code non existant."""
        repo = CurrencyRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0

        result = repo.exists("XYZ")

        assert result == False

    def test_create(self, mock_db, tenant_id):
        """Creation d'une devise."""
        repo = CurrencyRepository(mock_db, tenant_id)
        user_id = uuid4()

        data = {
            "code": "EUR",
            "name": "Euro",
            "symbol": "\u20ac",
            "decimals": 2
        }

        repo.create(data, user_id)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_increments_version(self, mock_db, tenant_id):
        """La mise a jour incremente la version."""
        repo = CurrencyRepository(mock_db, tenant_id)

        mock_currency = Mock(spec=Currency)
        mock_currency.version = 1
        mock_currency.updated_by = None

        user_id = uuid4()
        data = {"name": "Euro Updated"}

        repo.update(mock_currency, data, user_id)

        assert mock_currency.version == 2
        assert mock_currency.updated_by == user_id
        mock_db.commit.assert_called_once()

    def test_soft_delete(self, mock_db, tenant_id):
        """Suppression logique."""
        repo = CurrencyRepository(mock_db, tenant_id)

        mock_currency = Mock(spec=Currency)
        mock_currency.is_deleted = False
        mock_currency.is_enabled = True

        user_id = uuid4()
        result = repo.soft_delete(mock_currency, user_id)

        assert result == True
        assert mock_currency.is_deleted == True
        assert mock_currency.is_enabled == False
        assert mock_currency.deleted_by == user_id
        assert mock_currency.deleted_at is not None
        mock_db.commit.assert_called_once()

    def test_restore(self, mock_db, tenant_id):
        """Restauration."""
        repo = CurrencyRepository(mock_db, tenant_id)

        mock_currency = Mock(spec=Currency)
        mock_currency.is_deleted = True
        mock_currency.deleted_at = datetime.utcnow()
        mock_currency.deleted_by = uuid4()

        repo.restore(mock_currency)

        assert mock_currency.is_deleted == False
        assert mock_currency.deleted_at is None
        assert mock_currency.deleted_by is None
        mock_db.commit.assert_called_once()

    def test_set_default(self, mock_db, tenant_id):
        """Definition devise par defaut."""
        repo = CurrencyRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 1

        mock_currency = Mock(spec=Currency)
        mock_currency.is_default = False
        mock_currency.is_enabled = False

        user_id = uuid4()
        repo.set_default(mock_currency, user_id)

        assert mock_currency.is_default == True
        assert mock_currency.is_enabled == True
        mock_db.commit.assert_called()

    def test_autocomplete(self, mock_db, tenant_id):
        """Autocomplete."""
        repo = CurrencyRepository(mock_db, tenant_id)

        mock_currencies = [
            Mock(id=uuid4(), code="EUR", name="Euro", symbol="\u20ac"),
            Mock(id=uuid4(), code="USD", name="Dollar", symbol="$")
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_currencies

        results = repo.autocomplete("E", 10)

        assert len(results) == 2
        assert results[0]["code"] == "EUR"


# ============================================================================
# TESTS EXCHANGE RATE REPOSITORY
# ============================================================================

class TestExchangeRateRepository:
    """Tests pour ExchangeRateRepository."""

    def test_get_rate(self, mock_db, tenant_id):
        """Recuperation d'un taux."""
        repo = ExchangeRateRepository(mock_db, tenant_id)

        mock_rate = Mock(spec=ExchangeRate)
        mock_rate.rate = Decimal("1.0850")

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_rate

        result = repo.get_rate("EUR", "USD", date.today())

        assert result == mock_rate

    def test_get_rate_exact_date(self, mock_db, tenant_id):
        """Recuperation taux date exacte."""
        repo = ExchangeRateRepository(mock_db, tenant_id)

        mock_rate = Mock(spec=ExchangeRate)
        mock_rate.rate_date = date.today()

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_rate

        result = repo.get_rate_exact_date("EUR", "USD", date.today())

        assert result == mock_rate

    def test_upsert_creates(self, mock_db, tenant_id):
        """Upsert cree si n'existe pas."""
        repo = ExchangeRateRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # N'existe pas

        user_id = uuid4()
        result = repo.upsert(
            "EUR", "USD", date.today(),
            Decimal("1.0850"), RateSource.ECB, RateType.SPOT, user_id
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_upsert_updates(self, mock_db, tenant_id):
        """Upsert met a jour si existe."""
        repo = ExchangeRateRepository(mock_db, tenant_id)

        existing_rate = Mock(spec=ExchangeRate)
        existing_rate.rate = Decimal("1.0800")
        existing_rate.is_locked = False
        existing_rate.version = 1

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_rate

        user_id = uuid4()
        result = repo.upsert(
            "EUR", "USD", date.today(),
            Decimal("1.0850"), RateSource.ECB, RateType.SPOT, user_id
        )

        assert result.rate == Decimal("1.0850")

    def test_lock_rate(self, mock_db, tenant_id):
        """Verrouillage d'un taux."""
        repo = ExchangeRateRepository(mock_db, tenant_id)

        mock_rate = Mock(spec=ExchangeRate)
        mock_rate.is_locked = False

        user_id = uuid4()
        repo.lock(mock_rate, user_id)

        assert mock_rate.is_locked == True
        mock_db.commit.assert_called_once()

    def test_get_average_rate(self, mock_db, tenant_id):
        """Calcul taux moyen."""
        repo = ExchangeRateRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = 1.0850

        start = date.today() - timedelta(days=30)
        end = date.today()

        result = repo.get_average_rate("EUR", "USD", start, end)

        assert result == Decimal("1.085")


# ============================================================================
# TESTS CONFIG REPOSITORY
# ============================================================================

class TestCurrencyConfigRepository:
    """Tests pour CurrencyConfigRepository."""

    def test_get_or_create_creates(self, mock_db, tenant_id):
        """get_or_create cree si n'existe pas."""
        repo = CurrencyConfigRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        user_id = uuid4()
        result = repo.get_or_create(user_id)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_get_or_create_returns_existing(self, mock_db, tenant_id):
        """get_or_create retourne l'existant."""
        repo = CurrencyConfigRepository(mock_db, tenant_id)

        existing_config = Mock(spec=CurrencyConfig)
        existing_config.tenant_id = tenant_id

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_config

        result = repo.get_or_create()

        assert result == existing_config
        mock_db.add.assert_not_called()


# ============================================================================
# TESTS GAIN LOSS REPOSITORY
# ============================================================================

class TestExchangeGainLossRepository:
    """Tests pour ExchangeGainLossRepository."""

    def test_get_by_document(self, mock_db, tenant_id):
        """Recuperation par document."""
        repo = ExchangeGainLossRepository(mock_db, tenant_id)

        mock_entries = [
            Mock(spec=ExchangeGainLoss, gain_loss_amount=Decimal("50.00")),
            Mock(spec=ExchangeGainLoss, gain_loss_amount=Decimal("-30.00"))
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_entries

        doc_id = uuid4()
        result = repo.get_by_document("invoice", doc_id)

        assert len(result) == 2

    def test_get_summary(self, mock_db, tenant_id):
        """Resume des gains/pertes."""
        repo = ExchangeGainLossRepository(mock_db, tenant_id)

        mock_entries = [
            Mock(
                gain_loss_type=GainLossType.REALIZED.value,
                gain_loss_amount=Decimal("100.00")
            ),
            Mock(
                gain_loss_type=GainLossType.REALIZED.value,
                gain_loss_amount=Decimal("-50.00")
            ),
            Mock(
                gain_loss_type=GainLossType.UNREALIZED.value,
                gain_loss_amount=Decimal("30.00")
            )
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_entries

        start = date.today() - timedelta(days=30)
        end = date.today()

        result = repo.get_summary(start, end)

        assert result["realized_gains"] == Decimal("100.00")
        assert result["realized_losses"] == Decimal("-50.00")
        assert result["realized_net"] == Decimal("50.00")
        assert result["unrealized_gains"] == Decimal("30.00")


# ============================================================================
# TESTS REVALUATION REPOSITORY
# ============================================================================

class TestCurrencyRevaluationRepository:
    """Tests pour CurrencyRevaluationRepository."""

    def test_get_next_code(self, mock_db, tenant_id):
        """Generation du prochain code."""
        repo = CurrencyRevaluationRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        code = repo.get_next_code()

        year = datetime.utcnow().year
        assert code == f"REVAL-{year}-0001"

    def test_get_next_code_increments(self, mock_db, tenant_id):
        """Le code s'incremente."""
        repo = CurrencyRevaluationRepository(mock_db, tenant_id)

        year = datetime.utcnow().year
        existing = Mock(code=f"REVAL-{year}-0005")

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = existing

        code = repo.get_next_code()

        assert code == f"REVAL-{year}-0006"

    def test_post(self, mock_db, tenant_id):
        """Comptabilisation."""
        repo = CurrencyRevaluationRepository(mock_db, tenant_id)

        mock_revaluation = Mock(spec=CurrencyRevaluation)
        mock_revaluation.status = RevaluationStatus.DRAFT.value

        journal_id = uuid4()
        user_id = uuid4()

        repo.post(mock_revaluation, journal_id, user_id)

        assert mock_revaluation.status == RevaluationStatus.POSTED.value
        assert mock_revaluation.journal_entry_id == journal_id
        assert mock_revaluation.posted_by == user_id
        mock_db.commit.assert_called_once()

    def test_cancel(self, mock_db, tenant_id):
        """Annulation."""
        repo = CurrencyRevaluationRepository(mock_db, tenant_id)

        mock_revaluation = Mock(spec=CurrencyRevaluation)
        mock_revaluation.status = RevaluationStatus.DRAFT.value

        user_id = uuid4()
        repo.cancel(mock_revaluation, user_id)

        assert mock_revaluation.status == RevaluationStatus.CANCELLED.value
        mock_db.commit.assert_called_once()


# ============================================================================
# TESTS ALERT REPOSITORY
# ============================================================================

class TestRateAlertRepository:
    """Tests pour RateAlertRepository."""

    def test_list_unread(self, mock_db, tenant_id):
        """Liste alertes non lues."""
        repo = RateAlertRepository(mock_db, tenant_id)

        mock_alerts = [
            Mock(spec=RateAlert, is_read=False),
            Mock(spec=RateAlert, is_read=False)
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_alerts

        result = repo.list_unread()

        assert len(result) == 2

    def test_mark_read(self, mock_db, tenant_id):
        """Marquer comme lue."""
        repo = RateAlertRepository(mock_db, tenant_id)

        mock_alert = Mock(spec=RateAlert)
        mock_alert.is_read = False

        repo.mark_read(mock_alert)

        assert mock_alert.is_read == True
        mock_db.commit.assert_called_once()

    def test_acknowledge(self, mock_db, tenant_id):
        """Acquittement."""
        repo = RateAlertRepository(mock_db, tenant_id)

        mock_alert = Mock(spec=RateAlert)
        mock_alert.is_acknowledged = False

        user_id = uuid4()
        repo.acknowledge(mock_alert, user_id)

        assert mock_alert.is_acknowledged == True
        assert mock_alert.acknowledged_by == user_id
        assert mock_alert.acknowledged_at is not None
        mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
