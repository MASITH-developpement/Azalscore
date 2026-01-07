"""
AZALS MODULE M7 - Tests Qualité (Quality Management)
=====================================================

Tests unitaires pour la gestion de la qualité.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Import des modèles
from app.modules.quality.models import (
    QualityControlTemplate as QualityPlan, QualityControlTemplateItem as InspectionPoint,
    QualityControl as Inspection, QualityControlLine as InspectionResult,
    NonConformance as NonConformity, NonConformanceAction as NCAction,
    CAPA, CAPAAction,
    QualityAudit as Audit, AuditFinding, Certification,
    ControlType as InspectionType, ControlStatus as InspectionStatus,
    NonConformanceStatus as NCStatus, NonConformanceSeverity as NCSeverity,
    CAPAStatus as ActionStatus, CAPAType as ActionType, CAPAType, CAPAStatus,
    AuditType, AuditStatus, FindingSeverity,
    CertificationStatus
)

# Import des schémas
from app.modules.quality.schemas import (
    QualityPlanCreate, InspectionPointCreate,
    InspectionCreate, InspectionResultCreate,
    NonConformityCreate, NCActionCreate,
    CAPACreate, CAPAActionCreate,
    AuditCreate, AuditFindingCreate,
    DocumentCreate, DocumentRevisionCreate,
    CertificationCreate, CalibrationCreate,
    QualityDashboard, QualityMetrics
)

# Import du service
from app.modules.quality.service import QualityService, get_quality_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_inspection_type_values(self):
        """Tester les types d'inspection."""
        assert InspectionType.INCOMING.value == "INCOMING"
        assert InspectionType.IN_PROCESS.value == "IN_PROCESS"
        assert InspectionType.FINAL.value == "FINAL"
        assert InspectionType.PERIODIC.value == "PERIODIC"
        assert len(InspectionType) >= 4

    def test_inspection_status_values(self):
        """Tester les statuts d'inspection."""
        assert InspectionStatus.PENDING.value == "PENDING"
        assert InspectionStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert InspectionStatus.PASSED.value == "PASSED"
        assert InspectionStatus.FAILED.value == "FAILED"
        assert len(InspectionStatus) >= 4

    def test_nc_status_values(self):
        """Tester les statuts de non-conformité."""
        assert NCStatus.OPEN.value == "OPEN"
        assert NCStatus.UNDER_REVIEW.value == "UNDER_REVIEW"
        assert NCStatus.ACTION_REQUIRED.value == "ACTION_REQUIRED"
        assert NCStatus.CLOSED.value == "CLOSED"
        assert len(NCStatus) >= 4

    def test_nc_severity_values(self):
        """Tester les niveaux de sévérité."""
        assert NCSeverity.MINOR.value == "MINOR"
        assert NCSeverity.MAJOR.value == "MAJOR"
        assert NCSeverity.CRITICAL.value == "CRITICAL"
        assert len(NCSeverity) >= 3

    def test_capa_type_values(self):
        """Tester les types de CAPA."""
        assert CAPAType.CORRECTIVE.value == "CORRECTIVE"
        assert CAPAType.PREVENTIVE.value == "PREVENTIVE"
        assert len(CAPAType) == 2

    def test_audit_type_values(self):
        """Tester les types d'audit."""
        assert AuditType.INTERNAL.value == "INTERNAL"
        assert AuditType.EXTERNAL.value == "EXTERNAL"
        assert AuditType.SUPPLIER.value == "SUPPLIER"
        assert len(AuditType) >= 3


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_quality_plan_model(self):
        """Tester le modèle QualityPlan."""
        plan = QualityPlan(
            tenant_id="test-tenant",
            code="QP001",
            name="Plan Qualité Produit A"
        )
        assert plan.code == "QP001"
        assert plan.is_active == True

    def test_inspection_model(self):
        """Tester le modèle Inspection."""
        inspection = Inspection(
            tenant_id="test-tenant",
            number="INS-2026-001",
            type=InspectionType.INCOMING,
            planned_date=date.today()
        )
        assert inspection.number == "INS-2026-001"
        assert inspection.type == InspectionType.INCOMING
        assert inspection.status == InspectionStatus.PENDING

    def test_non_conformity_model(self):
        """Tester le modèle NonConformity."""
        nc = NonConformity(
            tenant_id="test-tenant",
            number="NC-2026-001",
            title="Défaut dimensionnel",
            severity=NCSeverity.MAJOR
        )
        assert nc.number == "NC-2026-001"
        assert nc.severity == NCSeverity.MAJOR
        assert nc.status == NCStatus.OPEN

    def test_capa_model(self):
        """Tester le modèle CAPA."""
        capa = CAPA(
            tenant_id="test-tenant",
            number="CAPA-2026-001",
            title="Action corrective défaut",
            type=CAPAType.CORRECTIVE
        )
        assert capa.number == "CAPA-2026-001"
        assert capa.type == CAPAType.CORRECTIVE
        assert capa.status == CAPAStatus.OPEN

    def test_audit_model(self):
        """Tester le modèle Audit."""
        audit = Audit(
            tenant_id="test-tenant",
            number="AUD-2026-001",
            name="Audit ISO 9001",
            type=AuditType.INTERNAL,
            planned_date=date.today()
        )
        assert audit.number == "AUD-2026-001"
        assert audit.type == AuditType.INTERNAL
        assert audit.status == AuditStatus.PLANNED

    def test_calibration_record_model(self):
        """Tester le modèle CalibrationRecord."""
        calibration = CalibrationRecord(
            tenant_id="test-tenant",
            equipment_code="CAL001",
            equipment_name="Pied à coulisse",
            calibration_date=date.today(),
            next_due_date=date.today() + timedelta(days=365)
        )
        assert calibration.equipment_code == "CAL001"
        assert calibration.status == CalibrationStatus.VALID


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_inspection_create_schema(self):
        """Tester le schéma InspectionCreate."""
        data = InspectionCreate(
            type=InspectionType.INCOMING,
            planned_date=date.today(),
            product_id=uuid4()
        )
        assert data.type == InspectionType.INCOMING

    def test_non_conformity_create_schema(self):
        """Tester le schéma NonConformityCreate."""
        data = NonConformityCreate(
            title="Défaut de surface",
            description="Rayures visibles sur la surface",
            severity=NCSeverity.MINOR
        )
        assert data.severity == NCSeverity.MINOR

    def test_capa_create_schema(self):
        """Tester le schéma CAPACreate."""
        data = CAPACreate(
            title="Amélioration processus",
            type=CAPAType.PREVENTIVE,
            description="Mise en place contrôle supplémentaire"
        )
        assert data.type == CAPAType.PREVENTIVE

    def test_audit_create_schema(self):
        """Tester le schéma AuditCreate."""
        data = AuditCreate(
            name="Audit annuel",
            type=AuditType.INTERNAL,
            planned_date=date.today() + timedelta(days=30),
            scope="Processus production"
        )
        assert data.type == AuditType.INTERNAL


# =============================================================================
# TESTS DU SERVICE - INSPECTIONS
# =============================================================================

class TestQualityServiceInspections:
    """Tests du service Quality - Inspections."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return QualityService(mock_db, "test-tenant")

    def test_create_inspection(self, service, mock_db):
        """Tester la création d'une inspection."""
        data = InspectionCreate(
            type=InspectionType.INCOMING,
            planned_date=date.today()
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_inspection(data, uuid4())

        mock_db.add.assert_called()

    def test_start_inspection(self, service, mock_db):
        """Tester le démarrage d'une inspection."""
        insp_id = uuid4()
        mock_insp = MagicMock()
        mock_insp.status = InspectionStatus.PENDING

        mock_db.query.return_value.filter.return_value.first.return_value = mock_insp

        result = service.start_inspection(insp_id, uuid4())

        assert mock_insp.status == InspectionStatus.IN_PROGRESS

    def test_complete_inspection_passed(self, service, mock_db):
        """Tester la clôture d'une inspection (passée)."""
        insp_id = uuid4()
        mock_insp = MagicMock()
        mock_insp.status = InspectionStatus.IN_PROGRESS

        mock_db.query.return_value.filter.return_value.first.return_value = mock_insp

        result = service.complete_inspection(insp_id, passed=True)

        assert mock_insp.status == InspectionStatus.PASSED


# =============================================================================
# TESTS DU SERVICE - NON-CONFORMITÉS
# =============================================================================

class TestQualityServiceNC:
    """Tests du service Quality - Non-conformités."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return QualityService(mock_db, "test-tenant")

    def test_create_non_conformity(self, service, mock_db):
        """Tester la création d'une non-conformité."""
        data = NonConformityCreate(
            title="Défaut dimensionnel",
            severity=NCSeverity.MAJOR
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_non_conformity(data, uuid4())

        mock_db.add.assert_called()

    def test_assign_nc_for_review(self, service, mock_db):
        """Tester l'assignation pour revue."""
        nc_id = uuid4()
        reviewer_id = uuid4()
        mock_nc = MagicMock()
        mock_nc.status = NCStatus.OPEN

        mock_db.query.return_value.filter.return_value.first.return_value = mock_nc

        result = service.assign_nc_for_review(nc_id, reviewer_id)

        assert mock_nc.status == NCStatus.UNDER_REVIEW

    def test_close_non_conformity(self, service, mock_db):
        """Tester la clôture d'une non-conformité."""
        nc_id = uuid4()
        mock_nc = MagicMock()
        mock_nc.status = NCStatus.ACTION_REQUIRED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_nc

        result = service.close_non_conformity(nc_id, uuid4(), "Résolu")

        assert mock_nc.status == NCStatus.CLOSED


# =============================================================================
# TESTS DU SERVICE - CAPA
# =============================================================================

class TestQualityServiceCAPA:
    """Tests du service Quality - CAPA."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return QualityService(mock_db, "test-tenant")

    def test_create_capa(self, service, mock_db):
        """Tester la création d'un CAPA."""
        data = CAPACreate(
            title="Action corrective",
            type=CAPAType.CORRECTIVE
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_capa(data, uuid4())

        mock_db.add.assert_called()

    def test_start_capa(self, service, mock_db):
        """Tester le démarrage d'un CAPA."""
        capa_id = uuid4()
        mock_capa = MagicMock()
        mock_capa.status = CAPAStatus.OPEN

        mock_db.query.return_value.filter.return_value.first.return_value = mock_capa

        result = service.start_capa(capa_id)

        assert mock_capa.status == CAPAStatus.IN_PROGRESS


# =============================================================================
# TESTS DU SERVICE - AUDITS
# =============================================================================

class TestQualityServiceAudits:
    """Tests du service Quality - Audits."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return QualityService(mock_db, "test-tenant")

    def test_create_audit(self, service, mock_db):
        """Tester la création d'un audit."""
        data = AuditCreate(
            name="Audit ISO",
            type=AuditType.INTERNAL,
            planned_date=date.today()
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_audit(data, uuid4())

        mock_db.add.assert_called()

    def test_start_audit(self, service, mock_db):
        """Tester le démarrage d'un audit."""
        audit_id = uuid4()
        mock_audit = MagicMock()
        mock_audit.status = AuditStatus.PLANNED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_audit

        result = service.start_audit(audit_id)

        assert mock_audit.status == AuditStatus.IN_PROGRESS


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_quality_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        service = get_quality_service(mock_db, "test-tenant")

        assert isinstance(service, QualityService)
        assert service.tenant_id == "test-tenant"


# =============================================================================
# TESTS CALCULS QUALITÉ
# =============================================================================

class TestQualityCalculations:
    """Tests des calculs qualité."""

    def test_defect_rate_calculation(self):
        """Tester le calcul du taux de défauts."""
        total_inspected = Decimal("1000")
        defective = Decimal("15")

        defect_rate = (defective / total_inspected) * 100

        assert defect_rate == Decimal("1.5")

    def test_first_pass_yield(self):
        """Tester le calcul du rendement premier passage."""
        total_produced = Decimal("100")
        passed_first_time = Decimal("92")

        fpy = (passed_first_time / total_produced) * 100

        assert fpy == Decimal("92")

    def test_nc_resolution_time(self):
        """Tester le calcul du temps de résolution."""
        opened = datetime(2026, 1, 1, 10, 0)
        closed = datetime(2026, 1, 3, 15, 0)

        resolution_hours = (closed - opened).total_seconds() / 3600

        assert resolution_hours == 53.0


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
