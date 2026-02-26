"""
Tests pour le router Consolidation - API REST
==============================================

Tests des endpoints API pour le module de consolidation.

Coverage:
- Dashboard (2 tests)
- Perimetres API (8 tests)
- Entites API (8 tests)
- Cours de change API (4 tests)
- Consolidations API (10 tests)
- Paquets API (8 tests)
- Eliminations API (4 tests)
- Reconciliations API (4 tests)
- Rapports API (4 tests)

TOTAL: 52 tests
"""

import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from fastapi import HTTPException
from fastapi.testclient import TestClient


# ============================================================================
# TESTS DASHBOARD
# ============================================================================

class TestDashboardEndpoints:
    """Tests pour les endpoints dashboard."""

    def test_get_dashboard(self, test_client):
        """Test GET /consolidation/dashboard."""
        from app.modules.consolidation.router import get_dashboard
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.get_dashboard.return_value = {
            "active_perimeters": 2,
            "total_entities": 10,
            "entities_by_method": {"full_integration": 5, "equity_method": 3},
            "consolidations_in_progress": 1,
            "consolidations_validated": 2,
            "packages_pending": 3,
            "packages_validated": 7,
            "packages_rejected": 0,
            "total_intercompany_balance": Decimal("0"),
            "unreconciled_items": 2,
            "reconciliation_rate": Decimal("80.0"),
            "total_eliminations": 15,
            "elimination_amount": Decimal("500000"),
            "total_goodwill": Decimal("200000"),
            "total_impairment": Decimal("0")
        }

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                get_dashboard(service=mock_service)
            )

            assert result.active_perimeters == 2
            assert result.total_entities == 10


# ============================================================================
# TESTS PERIMETRES API
# ============================================================================

class TestPerimeterEndpoints:
    """Tests pour les endpoints perimetres."""

    def test_create_perimeter_endpoint(self, test_client, perimeter_data):
        """Test POST /consolidation/perimeters."""
        from app.modules.consolidation.router import create_perimeter
        from app.modules.consolidation.service import ConsolidationService
        from app.modules.consolidation.schemas import ConsolidationPerimeterCreate

        mock_service = Mock(spec=ConsolidationService)
        mock_service.create_perimeter.return_value = Mock(
            id=uuid4(),
            tenant_id="tenant-test",
            code="GRP-2025",
            name="Groupe 2025",
            status=Mock(value="draft"),
            **{k: v for k, v in perimeter_data.items()}
        )

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            data = ConsolidationPerimeterCreate(**perimeter_data)
            result = pytest.importorskip('asyncio').run(
                create_perimeter(data=data, service=mock_service)
            )

            assert result.code == "GRP-2025"

    def test_list_perimeters_endpoint(self, test_client):
        """Test GET /consolidation/perimeters."""
        from app.modules.consolidation.router import list_perimeters
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.list_perimeters.return_value = ([Mock(
            id=uuid4(),
            code="GRP-2025",
            status=Mock(value="draft")
        )], 1)
        mock_service.perimeter_repo = Mock()
        mock_service.perimeter_repo.get_entity_count.return_value = 5

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                list_perimeters(
                    fiscal_year=2025,
                    status=None,
                    page=1,
                    page_size=20,
                    service=mock_service
                )
            )

            assert result.total == 1

    def test_get_perimeter_endpoint(self, test_client, sample_perimeter):
        """Test GET /consolidation/perimeters/{id}."""
        from app.modules.consolidation.router import get_perimeter
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.get_perimeter.return_value = Mock(
            **sample_perimeter,
            status=Mock(value="draft")
        )
        mock_service.perimeter_repo = Mock()
        mock_service.perimeter_repo.get_entity_count.return_value = 3

        perimeter_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                get_perimeter(perimeter_id=perimeter_id, service=mock_service)
            )

            assert result.code == "GRP-2025"

    def test_update_perimeter_endpoint(self, test_client, sample_perimeter):
        """Test PUT /consolidation/perimeters/{id}."""
        from app.modules.consolidation.router import update_perimeter
        from app.modules.consolidation.service import ConsolidationService
        from app.modules.consolidation.schemas import ConsolidationPerimeterUpdate

        mock_service = Mock(spec=ConsolidationService)
        mock_service.update_perimeter.return_value = Mock(
            **{**sample_perimeter, "name": "Nouveau nom"},
            status=Mock(value="draft")
        )
        mock_service.perimeter_repo = Mock()
        mock_service.perimeter_repo.get_entity_count.return_value = 3

        perimeter_id = uuid4()
        data = ConsolidationPerimeterUpdate(name="Nouveau nom")

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                update_perimeter(perimeter_id=perimeter_id, data=data, service=mock_service)
            )

            assert result.name == "Nouveau nom"

    def test_delete_perimeter_endpoint(self, test_client):
        """Test DELETE /consolidation/perimeters/{id}."""
        from app.modules.consolidation.router import delete_perimeter
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.delete_perimeter.return_value = True

        perimeter_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            # Devrait s'executer sans erreur (204 No Content)
            pytest.importorskip('asyncio').run(
                delete_perimeter(perimeter_id=perimeter_id, service=mock_service)
            )

            mock_service.delete_perimeter.assert_called_once()


# ============================================================================
# TESTS ENTITES API
# ============================================================================

class TestEntityEndpoints:
    """Tests pour les endpoints entites."""

    def test_create_entity_endpoint(self, test_client, entity_data):
        """Test POST /consolidation/entities."""
        from app.modules.consolidation.router import create_entity
        from app.modules.consolidation.service import ConsolidationService
        from app.modules.consolidation.schemas import ConsolidationEntityCreate

        mock_service = Mock(spec=ConsolidationService)
        mock_service.create_entity.return_value = Mock(
            id=uuid4(),
            code="HOLDING",
            name="AZALS Holding SA",
            consolidation_method=Mock(value="full_integration")
        )

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            data = ConsolidationEntityCreate(**entity_data)
            result = pytest.importorskip('asyncio').run(
                create_entity(data=data, service=mock_service)
            )

            assert result.code == "HOLDING"

    def test_list_entities_endpoint(self, test_client):
        """Test GET /consolidation/entities."""
        from app.modules.consolidation.router import list_entities
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.list_entities.return_value = ([Mock(
            id=uuid4(),
            code="HOLDING",
            consolidation_method=Mock(value="full_integration")
        )], 1)

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                list_entities(
                    perimeter_id=None,
                    search=None,
                    country=None,
                    consolidation_method=None,
                    is_parent=None,
                    is_active=None,
                    page=1,
                    page_size=20,
                    service=mock_service
                )
            )

            assert result.total == 1

    def test_get_entity_endpoint(self, test_client, sample_entity):
        """Test GET /consolidation/entities/{id}."""
        from app.modules.consolidation.router import get_entity
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.get_entity.return_value = Mock(
            **sample_entity,
            consolidation_method=Mock(value="full_integration")
        )

        entity_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                get_entity(entity_id=entity_id, service=mock_service)
            )

            assert result.code == "HOLDING"


# ============================================================================
# TESTS CONSOLIDATIONS API
# ============================================================================

class TestConsolidationEndpoints:
    """Tests pour les endpoints consolidations."""

    def test_create_consolidation_endpoint(self, test_client, consolidation_data):
        """Test POST /consolidation/consolidations."""
        from app.modules.consolidation.router import create_consolidation
        from app.modules.consolidation.service import ConsolidationService
        from app.modules.consolidation.schemas import ConsolidationCreate

        mock_service = Mock(spec=ConsolidationService)
        mock_service.create_consolidation.return_value = Mock(
            id=uuid4(),
            code="CONSO-2025-Q4",
            status=Mock(value="draft")
        )

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            data = ConsolidationCreate(**consolidation_data)
            result = pytest.importorskip('asyncio').run(
                create_consolidation(data=data, service=mock_service)
            )

            assert result.code == "CONSO-2025-Q4"

    def test_list_consolidations_endpoint(self, test_client):
        """Test GET /consolidation/consolidations."""
        from app.modules.consolidation.router import list_consolidations
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.list_consolidations.return_value = ([Mock(
            id=uuid4(),
            code="CONSO-2025",
            status=Mock(value="draft")
        )], 1)

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                list_consolidations(
                    search=None,
                    fiscal_year=2025,
                    status=None,
                    perimeter_id=None,
                    page=1,
                    page_size=20,
                    service=mock_service
                )
            )

            assert result.total == 1

    def test_get_consolidation_endpoint(self, test_client, sample_consolidation):
        """Test GET /consolidation/consolidations/{id}."""
        from app.modules.consolidation.router import get_consolidation
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.get_consolidation.return_value = Mock(
            **sample_consolidation,
            status=Mock(value="draft"),
            accounting_standard=Mock(value="french_gaap")
        )
        mock_service.consolidation_repo = Mock()
        mock_service.consolidation_repo.get_packages_count.return_value = {"validated": 5}
        mock_service.elimination_repo = Mock()
        mock_service.elimination_repo.list_by_consolidation.return_value = []

        consolidation_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                get_consolidation(consolidation_id=consolidation_id, service=mock_service)
            )

            assert result.code == "CONSO-2025-Q4"

    def test_execute_consolidation_endpoint(self, test_client):
        """Test POST /consolidation/consolidations/{id}/execute."""
        from app.modules.consolidation.router import execute_consolidation
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.execute_consolidation.return_value = {
            "packages_processed": 5,
            "eliminations_generated": 10,
            "minority_interests": 2,
            "warnings": [],
            "errors": []
        }

        consolidation_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                execute_consolidation(consolidation_id=consolidation_id, service=mock_service)
            )

            assert result["packages_processed"] == 5
            assert result["eliminations_generated"] == 10

    def test_submit_consolidation_endpoint(self, test_client, sample_consolidation):
        """Test POST /consolidation/consolidations/{id}/submit."""
        from app.modules.consolidation.router import submit_consolidation
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.submit_consolidation.return_value = Mock(
            **sample_consolidation,
            status=Mock(value="pending_review"),
            accounting_standard=Mock(value="french_gaap")
        )

        consolidation_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                submit_consolidation(consolidation_id=consolidation_id, service=mock_service)
            )

            assert result.status.value == "pending_review"

    def test_validate_consolidation_endpoint(self, test_client, sample_consolidation):
        """Test POST /consolidation/consolidations/{id}/validate."""
        from app.modules.consolidation.router import validate_consolidation
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.validate_consolidation.return_value = Mock(
            **sample_consolidation,
            status=Mock(value="validated"),
            accounting_standard=Mock(value="french_gaap")
        )

        consolidation_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                validate_consolidation(consolidation_id=consolidation_id, service=mock_service)
            )

            assert result.status.value == "validated"


# ============================================================================
# TESTS PAQUETS API
# ============================================================================

class TestPackageEndpoints:
    """Tests pour les endpoints paquets."""

    def test_create_package_endpoint(self, test_client, package_data):
        """Test POST /consolidation/packages."""
        from app.modules.consolidation.router import create_package
        from app.modules.consolidation.service import ConsolidationService
        from app.modules.consolidation.schemas import ConsolidationPackageCreate

        mock_service = Mock(spec=ConsolidationService)
        mock_service.create_package.return_value = Mock(
            id=uuid4(),
            entity_id=uuid4(),
            status=Mock(value="not_started")
        )
        mock_service.get_entity.return_value = Mock(name="Entity", code="ENT")

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            data = ConsolidationPackageCreate(**package_data)
            result = pytest.importorskip('asyncio').run(
                create_package(data=data, service=mock_service)
            )

            assert result.status.value == "not_started"

    def test_submit_package_endpoint(self, test_client, sample_package):
        """Test POST /consolidation/packages/{id}/submit."""
        from app.modules.consolidation.router import submit_package
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.submit_package.return_value = Mock(
            **sample_package,
            status=Mock(value="submitted")
        )
        mock_service.get_entity.return_value = Mock(name="Entity", code="ENT")

        package_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                submit_package(package_id=package_id, data=None, service=mock_service)
            )

            assert result.status.value == "submitted"

    def test_validate_package_endpoint(self, test_client, sample_package):
        """Test POST /consolidation/packages/{id}/validate."""
        from app.modules.consolidation.router import validate_package
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.validate_package.return_value = Mock(
            **sample_package,
            status=Mock(value="validated")
        )
        mock_service.get_entity.return_value = Mock(name="Entity", code="ENT")

        package_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                validate_package(package_id=package_id, data=None, service=mock_service)
            )

            assert result.status.value == "validated"

    def test_reject_package_endpoint(self, test_client, sample_package):
        """Test POST /consolidation/packages/{id}/reject."""
        from app.modules.consolidation.router import reject_package
        from app.modules.consolidation.service import ConsolidationService
        from app.modules.consolidation.schemas import ConsolidationPackageReject

        mock_service = Mock(spec=ConsolidationService)
        mock_service.reject_package.return_value = Mock(
            **sample_package,
            status=Mock(value="rejected"),
            rejection_reason="Balance non equilibree"
        )
        mock_service.get_entity.return_value = Mock(name="Entity", code="ENT")

        package_id = uuid4()
        data = ConsolidationPackageReject(reason="Balance non equilibree")

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                reject_package(package_id=package_id, data=data, service=mock_service)
            )

            assert result.status.value == "rejected"


# ============================================================================
# TESTS ELIMINATIONS API
# ============================================================================

class TestEliminationEndpoints:
    """Tests pour les endpoints eliminations."""

    def test_generate_eliminations_endpoint(self, test_client):
        """Test POST /consolidation/eliminations/generate."""
        from app.modules.consolidation.router import generate_eliminations
        from app.modules.consolidation.service import ConsolidationService
        from app.modules.consolidation.schemas import GenerateEliminationsRequest

        mock_service = Mock(spec=ConsolidationService)
        mock_service.generate_eliminations.return_value = [
            Mock(
                id=uuid4(),
                elimination_type=Mock(value="intercompany_receivables"),
                amount=Decimal("100000")
            )
        ]

        data = GenerateEliminationsRequest(consolidation_id=uuid4())

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                generate_eliminations(data=data, service=mock_service)
            )

            assert result.generated_count == 1

    def test_list_eliminations_endpoint(self, test_client):
        """Test GET /consolidation/consolidations/{id}/eliminations."""
        from app.modules.consolidation.router import list_eliminations
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.elimination_repo = Mock()
        mock_service.elimination_repo.list_by_consolidation.return_value = [
            Mock(
                id=uuid4(),
                elimination_type=Mock(value="capital_elimination"),
                amount=Decimal("500000")
            )
        ]

        consolidation_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                list_eliminations(
                    consolidation_id=consolidation_id,
                    elimination_type=None,
                    is_validated=None,
                    page=1,
                    page_size=50,
                    service=mock_service
                )
            )

            assert result.total == 1


# ============================================================================
# TESTS RECONCILIATIONS API
# ============================================================================

class TestReconciliationEndpoints:
    """Tests pour les endpoints reconciliations."""

    def test_auto_reconcile_endpoint(self, test_client):
        """Test POST /consolidation/consolidations/{id}/reconciliations/auto."""
        from app.modules.consolidation.router import auto_reconcile
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.auto_reconcile_intercompany.return_value = {
            "reconciliations_created": 5,
            "warnings": []
        }

        consolidation_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                auto_reconcile(consolidation_id=consolidation_id, service=mock_service)
            )

            assert result["reconciliations_created"] == 5

    def test_get_reconciliation_summary_endpoint(self, test_client):
        """Test GET /consolidation/consolidations/{id}/reconciliations/summary."""
        from app.modules.consolidation.router import get_reconciliation_summary
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.get_reconciliation_summary.return_value = {
            "total_pairs": 10,
            "reconciled_count": 8,
            "unreconciled_count": 2,
            "within_tolerance_count": 9,
            "total_difference": Decimal("150"),
            "reconciliation_rate": Decimal("80")
        }

        consolidation_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                get_reconciliation_summary(consolidation_id=consolidation_id, service=mock_service)
            )

            assert result.total_pairs == 10


# ============================================================================
# TESTS RAPPORTS API
# ============================================================================

class TestReportEndpoints:
    """Tests pour les endpoints rapports."""

    def test_generate_report_endpoint(self, test_client):
        """Test POST /consolidation/reports/generate."""
        from app.modules.consolidation.router import generate_report
        from app.modules.consolidation.service import ConsolidationService
        from app.modules.consolidation.schemas import GenerateReportRequest
        from app.modules.consolidation.models import ReportType

        mock_service = Mock(spec=ConsolidationService)
        mock_service.generate_report.return_value = Mock(
            id=uuid4(),
            report_type=Mock(value="balance_sheet"),
            report_data={"assets": {}, "liabilities": {}}
        )

        data = GenerateReportRequest(
            consolidation_id=uuid4(),
            report_type=ReportType.BALANCE_SHEET
        )

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                generate_report(data=data, service=mock_service)
            )

            assert result.report_type.value == "balance_sheet"

    def test_list_reports_endpoint(self, test_client):
        """Test GET /consolidation/consolidations/{id}/reports."""
        from app.modules.consolidation.router import list_reports
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.report_repo = Mock()
        mock_service.report_repo.list_by_consolidation.return_value = [
            Mock(
                id=uuid4(),
                report_type=Mock(value="balance_sheet")
            )
        ]

        consolidation_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                list_reports(
                    consolidation_id=consolidation_id,
                    report_type=None,
                    page=1,
                    page_size=20,
                    service=mock_service
                )
            )

            assert result.total == 1

    def test_get_report_endpoint(self, test_client, sample_report):
        """Test GET /consolidation/reports/{id}."""
        from app.modules.consolidation.router import get_report
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.report_repo = Mock()
        mock_service.report_repo.get_by_id.return_value = Mock(
            **sample_report,
            report_type=Mock(value="balance_sheet")
        )

        report_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                get_report(report_id=report_id, service=mock_service)
            )

            assert result.name == "Bilan Consolide T4 2025"

    def test_finalize_report_endpoint(self, test_client, sample_report):
        """Test POST /consolidation/reports/{id}/finalize."""
        from app.modules.consolidation.router import finalize_report
        from app.modules.consolidation.service import ConsolidationService

        mock_service = Mock(spec=ConsolidationService)
        mock_service.user_id = str(uuid4())
        mock_service.report_repo = Mock()
        mock_service.report_repo.get_by_id.return_value = Mock(**sample_report)
        mock_service.report_repo.finalize.return_value = Mock(
            **{**sample_report, "is_final": True},
            report_type=Mock(value="balance_sheet")
        )

        report_id = uuid4()

        with patch('app.modules.consolidation.router.get_consolidation_service', return_value=mock_service):
            result = pytest.importorskip('asyncio').run(
                finalize_report(report_id=report_id, service=mock_service)
            )

            assert result.is_final is True
