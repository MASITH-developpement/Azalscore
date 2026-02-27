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
    QualityControlTemplate, QualityControlTemplateItem,
    QualityControl, QualityControlLine,
    NonConformance, NonConformanceAction,
    CAPA, CAPAAction,
    QualityAudit, AuditFinding, Certification,
    ControlType, ControlStatus, ControlResult,
    NonConformanceStatus, NonConformanceSeverity, NonConformanceType,
    CAPAStatus, CAPAType,
    AuditType, AuditStatus, FindingSeverity,
    CertificationStatus
)

# Import des schémas
from app.modules.quality.schemas import (
    ControlTemplateCreate, ControlTemplateItemCreate,
    ControlCreate, ControlLineUpdate,
    NonConformanceCreate, NonConformanceActionCreate,
    CAPACreate, CAPAActionCreate,
    AuditCreate, AuditFindingCreate,
    CertificationCreate, CertificationAuditCreate,
    QualityDashboard
)

# Import du service
from app.modules.quality.service import QualityService, get_quality_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_control_type_values(self):
        """Tester les types de contrôle."""
        assert ControlType.INCOMING.value == "INCOMING"
        assert ControlType.IN_PROCESS.value == "IN_PROCESS"
        assert ControlType.FINAL.value == "FINAL"
        assert len(ControlType) >= 4

    def test_control_status_values(self):
        """Tester les statuts de contrôle."""
        assert ControlStatus.PLANNED.value == "PLANNED"
        assert ControlStatus.PENDING.value == "PENDING"
        assert ControlStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert ControlStatus.COMPLETED.value == "COMPLETED"
        assert len(ControlStatus) >= 4

    def test_control_result_values(self):
        """Tester les résultats de contrôle."""
        assert ControlResult.PASSED.value == "PASSED"
        assert ControlResult.FAILED.value == "FAILED"
        assert ControlResult.CONDITIONAL.value == "CONDITIONAL"
        assert len(ControlResult) >= 3

    def test_nc_status_values(self):
        """Tester les statuts de non-conformité."""
        assert NonConformanceStatus.DRAFT.value == "DRAFT"
        assert NonConformanceStatus.OPEN.value == "OPEN"
        assert NonConformanceStatus.UNDER_ANALYSIS.value == "UNDER_ANALYSIS"
        assert NonConformanceStatus.ACTION_REQUIRED.value == "ACTION_REQUIRED"
        assert NonConformanceStatus.CLOSED.value == "CLOSED"
        assert len(NonConformanceStatus) >= 5

    def test_nc_severity_values(self):
        """Tester les niveaux de sévérité."""
        assert NonConformanceSeverity.MINOR.value == "MINOR"
        assert NonConformanceSeverity.MAJOR.value == "MAJOR"
        assert NonConformanceSeverity.CRITICAL.value == "CRITICAL"
        assert len(NonConformanceSeverity) >= 3

    def test_capa_type_values(self):
        """Tester les types de CAPA."""
        assert CAPAType.CORRECTIVE.value == "CORRECTIVE"
        assert CAPAType.PREVENTIVE.value == "PREVENTIVE"
        assert CAPAType.IMPROVEMENT.value == "IMPROVEMENT"
        assert len(CAPAType) == 3

    def test_capa_status_values(self):
        """Tester les statuts CAPA."""
        assert CAPAStatus.DRAFT.value == "DRAFT"
        assert CAPAStatus.OPEN.value == "OPEN"
        assert CAPAStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert CAPAStatus.VERIFICATION.value == "VERIFICATION"
        assert len(CAPAStatus) >= 5

    def test_audit_type_values(self):
        """Tester les types d'audit."""
        assert AuditType.INTERNAL.value == "INTERNAL"
        assert AuditType.EXTERNAL.value == "EXTERNAL"
        assert AuditType.SUPPLIER.value == "SUPPLIER"
        assert len(AuditType) >= 3

    def test_audit_status_values(self):
        """Tester les statuts d'audit."""
        assert AuditStatus.PLANNED.value == "PLANNED"
        assert AuditStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert AuditStatus.COMPLETED.value == "COMPLETED"
        assert AuditStatus.CLOSED.value == "CLOSED"
        assert len(AuditStatus) >= 4


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_quality_control_template_model(self):
        """Tester le modèle QualityControlTemplate."""
        template = QualityControlTemplate(
            tenant_id=1,
            code="QCT001",
            name="Template Contrôle Réception",
            control_type=ControlType.INCOMING,
            is_active=True
        )
        assert template.code == "QCT001"
        assert template.control_type == ControlType.INCOMING
        assert template.is_active is True

    def test_quality_control_model(self):
        """Tester le modèle QualityControl."""
        control = QualityControl(
            tenant_id=1,
            control_number="QC-2026-001",
            control_type=ControlType.INCOMING,
            control_date=date.today(),
            status=ControlStatus.PLANNED
        )
        assert control.control_number == "QC-2026-001"
        assert control.control_type == ControlType.INCOMING
        assert control.status == ControlStatus.PLANNED

    def test_non_conformance_model(self):
        """Tester le modèle NonConformance."""
        nc = NonConformance(
            tenant_id=1,
            nc_number="NC-2026-001",
            title="Défaut dimensionnel",
            nc_type=NonConformanceType.PRODUCT,
            severity=NonConformanceSeverity.MAJOR,
            status=NonConformanceStatus.DRAFT,
            detected_date=date.today()
        )
        assert nc.nc_number == "NC-2026-001"
        assert nc.severity == NonConformanceSeverity.MAJOR
        assert nc.status == NonConformanceStatus.DRAFT

    def test_capa_model(self):
        """Tester le modèle CAPA."""
        capa = CAPA(
            tenant_id=1,
            capa_number="CAPA-2026-001",
            title="Action corrective défaut",
            description="Description de l'action",
            capa_type=CAPAType.CORRECTIVE,
            status=CAPAStatus.DRAFT,
            open_date=date.today(),
            owner_id=1
        )
        assert capa.capa_number == "CAPA-2026-001"
        assert capa.capa_type == CAPAType.CORRECTIVE
        assert capa.status == CAPAStatus.DRAFT

    def test_audit_model(self):
        """Tester le modèle QualityAudit."""
        audit = QualityAudit(
            tenant_id=1,
            audit_number="AUD-2026-001",
            title="Audit ISO 9001",
            audit_type=AuditType.INTERNAL,
            planned_date=date.today(),
            status=AuditStatus.PLANNED
        )
        assert audit.audit_number == "AUD-2026-001"
        assert audit.audit_type == AuditType.INTERNAL
        assert audit.status == AuditStatus.PLANNED

    def test_certification_model(self):
        """Tester le modèle Certification."""
        cert = Certification(
            tenant_id=1,
            code="CERT001",
            name="ISO 9001:2015",
            standard="ISO 9001",
            status=CertificationStatus.PLANNED
        )
        assert cert.code == "CERT001"
        assert cert.standard == "ISO 9001"
        assert cert.status == CertificationStatus.PLANNED


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_control_template_create_schema(self):
        """Tester le schéma ControlTemplateCreate."""
        data = ControlTemplateCreate(
            code="QCT001",
            name="Template Contrôle",
            control_type=ControlType.INCOMING
        )
        assert data.code == "QCT001"
        assert data.control_type.value == "INCOMING"

    def test_non_conformance_create_schema(self):
        """Tester le schéma NonConformanceCreate."""
        data = NonConformanceCreate(
            title="Défaut de surface",
            description="Rayures visibles sur la surface",
            nc_type=NonConformanceType.PRODUCT,
            severity=NonConformanceSeverity.MINOR,
            detected_date=date.today()
        )
        assert data.severity.value == "MINOR"
        assert data.nc_type.value == "PRODUCT"

    def test_capa_create_schema(self):
        """Tester le schéma CAPACreate."""
        data = CAPACreate(
            title="Amélioration processus",
            capa_type=CAPAType.PREVENTIVE,
            description="Mise en place contrôle supplémentaire",
            open_date=date.today(),
            owner_id=1
        )
        assert data.capa_type.value == "PREVENTIVE"

    def test_audit_create_schema(self):
        """Tester le schéma AuditCreate."""
        data = AuditCreate(
            title="Audit annuel",
            audit_type=AuditType.INTERNAL,
            planned_date=date.today() + timedelta(days=30)
        )
        assert data.audit_type.value == "INTERNAL"


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
        return QualityService(mock_db, tenant_id=1, user_id=1)

    def test_create_non_conformance(self, service, mock_db):
        """Tester la création d'une non-conformité."""
        data = NonConformanceCreate(
            title="Défaut dimensionnel",
            nc_type=NonConformanceType.PRODUCT,
            severity=NonConformanceSeverity.MAJOR,
            detected_date=date.today()
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        # Mock the sequence config query - returns None to trigger default config creation
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None

        # Mock the created NC object
        mock_nc = MagicMock()
        mock_nc.nc_number = "NC-2026-0001"

        # Patch the _generate_nc_number to return a mock value
        with patch.object(service, '_generate_nc_number', return_value="NC-2026-0001"):
            result = service.create_non_conformance(data)

        mock_db.add.assert_called()

    def test_get_non_conformance(self, service, mock_db):
        """Tester la récupération d'une NC."""
        mock_nc = MagicMock(spec=NonConformance)
        mock_nc.id = 1
        mock_nc.nc_number = "NC-2026-001"

        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_nc

        result = service.get_non_conformance(1)

        assert result.nc_number == "NC-2026-001"


# =============================================================================
# TESTS DU SERVICE - CONTRÔLES
# =============================================================================

class TestQualityServiceControls:
    """Tests du service Quality - Contrôles."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return QualityService(mock_db, tenant_id=1, user_id=1)

    def test_create_control_template(self, service, mock_db):
        """Tester la création d'un template de contrôle."""
        data = ControlTemplateCreate(
            code="QCT001",
            name="Template Réception",
            control_type=ControlType.INCOMING
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_control_template(data)

        mock_db.add.assert_called()


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
        return QualityService(mock_db, tenant_id=1, user_id=1)

    def test_create_capa(self, service, mock_db):
        """Tester la création d'un CAPA."""
        data = CAPACreate(
            title="Action corrective",
            capa_type=CAPAType.CORRECTIVE,
            description="Description détaillée",
            open_date=date.today(),
            owner_id=1
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        result = service.create_capa(data)

        mock_db.add.assert_called()

    def test_get_capa(self, service, mock_db):
        """Tester la récupération d'un CAPA."""
        mock_capa = MagicMock(spec=CAPA)
        mock_capa.id = 1
        mock_capa.capa_number = "CAPA-2026-001"

        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_capa

        result = service.get_capa(1)

        assert result.capa_number == "CAPA-2026-001"


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
        return QualityService(mock_db, tenant_id=1, user_id=1)

    def test_create_audit(self, service, mock_db):
        """Tester la création d'un audit."""
        data = AuditCreate(
            title="Audit ISO",
            audit_type=AuditType.INTERNAL,
            planned_date=date.today()
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        result = service.create_audit(data)

        mock_db.add.assert_called()

    def test_get_audit(self, service, mock_db):
        """Tester la récupération d'un audit."""
        mock_audit = MagicMock(spec=QualityAudit)
        mock_audit.id = 1
        mock_audit.audit_number = "AUD-2026-001"

        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_audit

        result = service.get_audit(1)

        assert result.audit_number == "AUD-2026-001"


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_quality_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        service = get_quality_service(mock_db, tenant_id="1", user_id=1)

        assert isinstance(service, QualityService)
        assert service.tenant_id == "1"


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

    def test_control_pass_rate(self):
        """Tester le calcul du taux de conformité."""
        total_controls = Decimal("50")
        passed = Decimal("45")

        pass_rate = (passed / total_controls) * 100

        assert pass_rate == Decimal("90")

    def test_capa_closure_rate(self):
        """Tester le calcul du taux de clôture CAPA."""
        total_capas = 20
        closed_capas = 15

        closure_rate = (closed_capas / total_capas) * 100

        assert closure_rate == 75.0


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
