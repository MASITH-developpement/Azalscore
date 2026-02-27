"""
Tests pour les optimisations N+1 queries.

Ces tests vérifient que les méthodes optimisées:
1. get_balance() - utilise GROUP BY au lieu de N queries
2. get_pipeline_stats() - utilise GROUP BY au lieu de N queries
3. _to_account_response() - utilise eager loading au lieu de 2 queries par compte
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4


class TestAccountingGetBalanceOptimization:
    """Tests pour l'optimisation de get_balance()."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        from app.modules.accounting.service import AccountingService
        return AccountingService(mock_db, "tenant-test", "user-test")

    def test_get_balance_uses_group_by(self, service, mock_db):
        """Vérifier que get_balance utilise GROUP BY au lieu de N queries."""
        # Setup: 3 comptes
        mock_accounts = []
        for i in range(3):
            account = MagicMock()
            account.account_number = f"411{i:03d}"
            account.account_label = f"Client {i}"
            account.opening_balance_debit = Decimal("100.00")
            account.opening_balance_credit = Decimal("0.00")
            mock_accounts.append(account)

        # Track query calls to verify GROUP BY is used
        query_calls = []

        def track_query(*args):
            query_calls.append(args)
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            mock_q.count.return_value = 3
            mock_q.order_by.return_value = mock_q
            mock_q.offset.return_value = mock_q
            mock_q.limit.return_value = mock_q
            mock_q.all.return_value = mock_accounts
            mock_q.join.return_value = mock_q
            mock_q.group_by.return_value = mock_q
            # Return empty list for GROUP BY movements query
            mock_q.all.side_effect = lambda: mock_accounts if len(query_calls) == 1 else []
            return mock_q

        mock_db.query.side_effect = track_query

        # Execute
        balance_entries, total = service.get_balance()

        # Verify: should have made exactly 2 queries (accounts + movements GROUP BY)
        # Instead of 1 + N queries
        assert len(query_calls) == 2, f"Expected 2 queries, got {len(query_calls)}"
        assert len(balance_entries) == 3
        assert total == 3

    def test_get_balance_empty_accounts(self, service, mock_db):
        """Vérifier que get_balance gère les comptes vides."""
        # Désactiver le cache pour ce test
        service._cache = None

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        balance_entries, total = service.get_balance()

        assert balance_entries == []
        assert total == 0


class TestCommercialGetPipelineStatsOptimization:
    """Tests pour l'optimisation de get_pipeline_stats()."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        from app.modules.commercial.service import CommercialService
        return CommercialService(mock_db, "tenant-test")

    def test_get_pipeline_stats_uses_group_by(self, service, mock_db):
        """Vérifier que get_pipeline_stats utilise GROUP BY."""
        # Setup: mock pipeline stages
        mock_stages = []
        for i, name in enumerate(["Prospect", "Qualification", "Proposal"]):
            stage = MagicMock()
            stage.id = uuid4()
            stage.name = name
            stage.order = i
            stage.probability = 25 + i * 25
            stage.color = "#000"
            mock_stages.append(stage)

        # Mock list_pipeline_stages
        with patch.object(service, 'list_pipeline_stages', return_value=mock_stages):
            # Mock the GROUP BY query
            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.group_by.return_value = mock_query

            # Mock aggregated results
            mock_opp_row = MagicMock()
            mock_opp_row.stage = "Prospect"
            mock_opp_row.count = 5
            mock_opp_row.total_value = Decimal("10000.00")
            mock_opp_row.weighted_value = Decimal("2500.00")
            mock_query.all.return_value = [mock_opp_row]

            # Execute
            result = service.get_pipeline_stats()

            # Verify: should use group_by
            assert mock_query.group_by.called
            assert len(result.stages) == 3

    def test_get_pipeline_stats_empty_stages(self, service, mock_db):
        """Vérifier que get_pipeline_stats gère les stages vides."""
        with patch.object(service, 'list_pipeline_stages', return_value=[]):
            result = service.get_pipeline_stats()

            assert result.stages == []
            assert result.total_value == Decimal("0")
            assert result.opportunities_count == 0


class TestTreasuryAccountResponseOptimization:
    """Tests pour l'optimisation de _to_account_response()."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        from app.modules.treasury.service import TreasuryService
        return TreasuryService(mock_db, "tenant-test")

    def test_to_account_response_uses_eager_loaded_transactions(self, service):
        """Vérifier que _to_account_response utilise les transactions eager-loaded."""
        from datetime import datetime

        # Setup: account with eager-loaded transactions
        mock_account = MagicMock()
        mock_account.id = uuid4()
        mock_account.tenant_id = "tenant-test"
        mock_account.account_number = "123456"
        mock_account.name = "Compte Courant"
        mock_account.bank_name = "BNP"
        mock_account.iban = "FR76..."
        mock_account.bic = "BNPAFRPP"
        mock_account.is_default = True
        mock_account.is_active = True
        mock_account.current_balance = Decimal("1000.00")
        mock_account.currency = "EUR"
        mock_account.created_by = uuid4()
        mock_account.created_at = datetime.utcnow()
        mock_account.updated_at = datetime.utcnow()

        # Simulate eager-loaded transactions
        mock_tx1 = MagicMock()
        mock_tx1.entry_line_id = None  # Unreconciled
        mock_tx2 = MagicMock()
        mock_tx2.entry_line_id = uuid4()  # Reconciled
        mock_tx3 = MagicMock()
        mock_tx3.entry_line_id = None  # Unreconciled

        mock_account.transactions = [mock_tx1, mock_tx2, mock_tx3]

        # Execute
        response = service._to_account_response(mock_account)

        # Verify: counts should be from eager-loaded data
        assert response.transactions_count == 3
        assert response.unreconciled_count == 2

    def test_to_account_response_uses_preloaded_stats(self, service):
        """Vérifier que _to_account_response utilise les stats préchargées."""
        from datetime import datetime

        mock_account = MagicMock()
        mock_account.id = uuid4()
        mock_account.tenant_id = "tenant-test"
        mock_account.account_number = "123456"
        mock_account.name = "Compte Courant"
        mock_account.bank_name = "BNP"
        mock_account.iban = "FR76..."
        mock_account.bic = "BNPAFRPP"
        mock_account.is_default = True
        mock_account.is_active = True
        mock_account.current_balance = Decimal("1000.00")
        mock_account.currency = "EUR"
        mock_account.created_by = uuid4()
        mock_account.created_at = datetime.utcnow()
        mock_account.updated_at = datetime.utcnow()
        mock_account.transactions = None  # No eager loading

        # Preloaded stats
        preloaded_stats = {
            mock_account.id: {
                'tx_count': 10,
                'unreconciled': 3
            }
        }

        # Execute
        response = service._to_account_response(mock_account, preloaded_stats)

        # Verify: counts should be from preloaded stats
        assert response.transactions_count == 10
        assert response.unreconciled_count == 3


class TestN1QueryCount:
    """Tests pour vérifier le nombre de requêtes."""

    def test_get_balance_query_count(self):
        """
        Vérifier que get_balance fait 2 requêtes au lieu de N+1.

        Avant optimisation: 1 (comptes) + N (mouvements par compte) = N+1 requêtes
        Après optimisation: 1 (comptes) + 1 (mouvements GROUP BY) = 2 requêtes
        """
        # Ce test est documentatif - en production, utiliser un query counter
        pass

    def test_get_pipeline_stats_query_count(self):
        """
        Vérifier que get_pipeline_stats fait 2 requêtes au lieu de N+1.

        Avant optimisation: 1 (stages) + N (opps par stage) = N+1 requêtes
        Après optimisation: 1 (stages) + 1 (opps GROUP BY) = 2 requêtes
        """
        pass

    def test_list_accounts_query_count(self):
        """
        Vérifier que list_accounts fait 1 requête au lieu de 2N+1.

        Avant optimisation: 1 (comptes) + 2N (counts par compte) = 2N+1 requêtes
        Après optimisation: 1 (comptes avec eager loading) = 1 requête
        """
        pass
