"""
Tests de sécurité et d'isolation multi-tenant - Risk Management - GAP-075
=========================================================================
"""
import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date, timedelta

from app.modules.risk.models import (
    RiskMatrix, Risk, Control, MitigationAction,
    RiskIndicator, RiskAssessment, RiskIncident
)
from app.modules.risk.exceptions import (
    RiskMatrixNotFoundError, RiskNotFoundError, ControlNotFoundError,
    ActionNotFoundError, IndicatorNotFoundError, AssessmentNotFoundError,
    IncidentNotFoundError
)
from app.modules.risk.service import RiskService
from app.modules.risk.schemas import (
    RiskMatrixCreate, RiskCreate, ControlCreate, ActionCreate,
    IndicatorCreate, AssessmentCreate, IncidentCreate
)


class TestRiskMatrixTenantIsolation:
    """Tests d'isolation multi-tenant pour les matrices de risques."""

    def test_cannot_read_other_tenant_matrix(
        self,
        risk_service: RiskService,
        other_tenant_matrix: RiskMatrix
    ):
        """Impossible de lire une matrice d'un autre tenant."""
        with pytest.raises(RiskMatrixNotFoundError):
            risk_service.get_matrix(other_tenant_matrix.id)

    def test_cannot_list_other_tenant_matrices(
        self,
        risk_service: RiskService,
        sample_matrix: RiskMatrix,
        other_tenant_matrix: RiskMatrix
    ):
        """Liste uniquement les matrices du tenant courant."""
        items, total, _ = risk_service.list_matrices()

        matrix_ids = [m.id for m in items]
        assert sample_matrix.id in matrix_ids
        assert other_tenant_matrix.id not in matrix_ids

    def test_cannot_update_other_tenant_matrix(
        self,
        risk_service: RiskService,
        other_tenant_matrix: RiskMatrix
    ):
        """Impossible de mettre à jour une matrice d'un autre tenant."""
        from app.modules.risk.schemas import RiskMatrixUpdate
        with pytest.raises(RiskMatrixNotFoundError):
            risk_service.update_matrix(
                other_tenant_matrix.id,
                RiskMatrixUpdate(name="Hacked")
            )

    def test_cannot_delete_other_tenant_matrix(
        self,
        risk_service: RiskService,
        other_tenant_matrix: RiskMatrix
    ):
        """Impossible de supprimer une matrice d'un autre tenant."""
        with pytest.raises(RiskMatrixNotFoundError):
            risk_service.delete_matrix(other_tenant_matrix.id)


class TestRiskTenantIsolation:
    """Tests d'isolation multi-tenant pour les risques."""

    def test_cannot_read_other_tenant_risk(
        self,
        risk_service: RiskService,
        other_tenant_risk: Risk
    ):
        """Impossible de lire un risque d'un autre tenant."""
        with pytest.raises(RiskNotFoundError):
            risk_service.get_risk(other_tenant_risk.id)

    def test_cannot_list_other_tenant_risks(
        self,
        risk_service: RiskService,
        sample_risk: Risk,
        other_tenant_risk: Risk
    ):
        """Liste uniquement les risques du tenant courant."""
        items, total, _ = risk_service.list_risks()

        risk_ids = [r.id for r in items]
        assert sample_risk.id in risk_ids
        assert other_tenant_risk.id not in risk_ids

    def test_cannot_update_other_tenant_risk(
        self,
        risk_service: RiskService,
        other_tenant_risk: Risk
    ):
        """Impossible de mettre à jour un risque d'un autre tenant."""
        from app.modules.risk.schemas import RiskUpdate
        with pytest.raises(RiskNotFoundError):
            risk_service.update_risk(
                other_tenant_risk.id,
                RiskUpdate(title="Hacked")
            )

    def test_cannot_delete_other_tenant_risk(
        self,
        risk_service: RiskService,
        other_tenant_risk: Risk
    ):
        """Impossible de supprimer un risque d'un autre tenant."""
        with pytest.raises(RiskNotFoundError):
            risk_service.delete_risk(other_tenant_risk.id)

    def test_cannot_close_other_tenant_risk(
        self,
        risk_service: RiskService,
        other_tenant_risk: Risk
    ):
        """Impossible de clôturer un risque d'un autre tenant."""
        with pytest.raises(RiskNotFoundError):
            risk_service.close_risk(other_tenant_risk.id, "Test")

    def test_cannot_change_status_other_tenant_risk(
        self,
        risk_service: RiskService,
        other_tenant_risk: Risk
    ):
        """Impossible de changer le statut d'un risque d'un autre tenant."""
        with pytest.raises(RiskNotFoundError):
            risk_service.change_risk_status(other_tenant_risk.id, "assessed")


class TestControlTenantIsolation:
    """Tests d'isolation multi-tenant pour les contrôles."""

    def test_cannot_read_other_tenant_control(
        self,
        risk_service: RiskService,
        other_tenant_control: Control
    ):
        """Impossible de lire un contrôle d'un autre tenant."""
        with pytest.raises(ControlNotFoundError):
            risk_service.get_control(other_tenant_control.id)

    def test_cannot_list_other_tenant_controls(
        self,
        risk_service: RiskService,
        sample_control: Control,
        other_tenant_control: Control
    ):
        """Liste uniquement les contrôles du tenant courant."""
        items, total, _ = risk_service.list_controls()

        control_ids = [c.id for c in items]
        assert sample_control.id in control_ids
        assert other_tenant_control.id not in control_ids

    def test_cannot_update_other_tenant_control(
        self,
        risk_service: RiskService,
        other_tenant_control: Control
    ):
        """Impossible de mettre à jour un contrôle d'un autre tenant."""
        from app.modules.risk.schemas import ControlUpdate
        with pytest.raises(ControlNotFoundError):
            risk_service.update_control(
                other_tenant_control.id,
                ControlUpdate(name="Hacked")
            )

    def test_cannot_delete_other_tenant_control(
        self,
        risk_service: RiskService,
        other_tenant_control: Control
    ):
        """Impossible de supprimer un contrôle d'un autre tenant."""
        with pytest.raises(ControlNotFoundError):
            risk_service.delete_control(other_tenant_control.id)

    def test_cannot_create_control_for_other_tenant_risk(
        self,
        risk_service: RiskService,
        other_tenant_risk: Risk
    ):
        """Impossible de créer un contrôle pour un risque d'un autre tenant."""
        with pytest.raises(RiskNotFoundError):
            risk_service.create_control(ControlCreate(
                risk_id=other_tenant_risk.id,
                name="Hacked Control",
                control_type="preventive"
            ))


class TestActionTenantIsolation:
    """Tests d'isolation multi-tenant pour les actions."""

    def test_cannot_read_other_tenant_action(
        self,
        risk_service: RiskService,
        other_tenant_action: MitigationAction
    ):
        """Impossible de lire une action d'un autre tenant."""
        with pytest.raises(ActionNotFoundError):
            risk_service.get_action(other_tenant_action.id)

    def test_cannot_list_other_tenant_actions(
        self,
        risk_service: RiskService,
        sample_action: MitigationAction,
        other_tenant_action: MitigationAction
    ):
        """Liste uniquement les actions du tenant courant."""
        items, total, _ = risk_service.list_actions()

        action_ids = [a.id for a in items]
        assert sample_action.id in action_ids
        assert other_tenant_action.id not in action_ids

    def test_cannot_update_other_tenant_action(
        self,
        risk_service: RiskService,
        other_tenant_action: MitigationAction
    ):
        """Impossible de mettre à jour une action d'un autre tenant."""
        from app.modules.risk.schemas import ActionUpdate
        with pytest.raises(ActionNotFoundError):
            risk_service.update_action(
                other_tenant_action.id,
                ActionUpdate(title="Hacked")
            )

    def test_cannot_delete_other_tenant_action(
        self,
        risk_service: RiskService,
        other_tenant_action: MitigationAction
    ):
        """Impossible de supprimer une action d'un autre tenant."""
        with pytest.raises(ActionNotFoundError):
            risk_service.delete_action(other_tenant_action.id)

    def test_cannot_start_other_tenant_action(
        self,
        risk_service: RiskService,
        other_tenant_action: MitigationAction
    ):
        """Impossible de démarrer une action d'un autre tenant."""
        with pytest.raises(ActionNotFoundError):
            risk_service.start_action(other_tenant_action.id)

    def test_cannot_complete_other_tenant_action(
        self,
        risk_service: RiskService,
        other_tenant_action: MitigationAction
    ):
        """Impossible de terminer une action d'un autre tenant."""
        with pytest.raises(ActionNotFoundError):
            risk_service.complete_action(other_tenant_action.id)

    def test_cannot_create_action_for_other_tenant_risk(
        self,
        risk_service: RiskService,
        other_tenant_risk: Risk
    ):
        """Impossible de créer une action pour un risque d'un autre tenant."""
        with pytest.raises(RiskNotFoundError):
            risk_service.create_action(ActionCreate(
                risk_id=other_tenant_risk.id,
                title="Hacked Action"
            ))


class TestIndicatorTenantIsolation:
    """Tests d'isolation multi-tenant pour les indicateurs."""

    def test_cannot_read_other_tenant_indicator(
        self,
        risk_service: RiskService,
        other_tenant_indicator: RiskIndicator
    ):
        """Impossible de lire un indicateur d'un autre tenant."""
        with pytest.raises(IndicatorNotFoundError):
            risk_service.get_indicator(other_tenant_indicator.id)

    def test_cannot_list_other_tenant_indicators(
        self,
        risk_service: RiskService,
        sample_indicator: RiskIndicator,
        other_tenant_indicator: RiskIndicator
    ):
        """Liste uniquement les indicateurs du tenant courant."""
        items, total, _ = risk_service.list_indicators()

        indicator_ids = [i.id for i in items]
        assert sample_indicator.id in indicator_ids
        assert other_tenant_indicator.id not in indicator_ids

    def test_cannot_update_other_tenant_indicator(
        self,
        risk_service: RiskService,
        other_tenant_indicator: RiskIndicator
    ):
        """Impossible de mettre à jour un indicateur d'un autre tenant."""
        from app.modules.risk.schemas import IndicatorUpdate
        with pytest.raises(IndicatorNotFoundError):
            risk_service.update_indicator(
                other_tenant_indicator.id,
                IndicatorUpdate(name="Hacked")
            )

    def test_cannot_delete_other_tenant_indicator(
        self,
        risk_service: RiskService,
        other_tenant_indicator: RiskIndicator
    ):
        """Impossible de supprimer un indicateur d'un autre tenant."""
        with pytest.raises(IndicatorNotFoundError):
            risk_service.delete_indicator(other_tenant_indicator.id)

    def test_cannot_record_value_other_tenant_indicator(
        self,
        risk_service: RiskService,
        other_tenant_indicator: RiskIndicator
    ):
        """Impossible d'enregistrer une valeur pour un indicateur d'un autre tenant."""
        from app.modules.risk.schemas import IndicatorValueRecord
        with pytest.raises(IndicatorNotFoundError):
            risk_service.record_indicator_value(
                other_tenant_indicator.id,
                IndicatorValueRecord(value=Decimal("100"))
            )

    def test_cannot_create_indicator_for_other_tenant_risk(
        self,
        risk_service: RiskService,
        other_tenant_risk: Risk
    ):
        """Impossible de créer un indicateur pour un risque d'un autre tenant."""
        with pytest.raises(RiskNotFoundError):
            risk_service.create_indicator(IndicatorCreate(
                risk_id=other_tenant_risk.id,
                name="Hacked Indicator",
                green_threshold=Decimal("5"),
                amber_threshold=Decimal("10"),
                red_threshold=Decimal("20")
            ))


class TestIncidentTenantIsolation:
    """Tests d'isolation multi-tenant pour les incidents."""

    def test_cannot_read_other_tenant_incident(
        self,
        risk_service: RiskService,
        other_tenant_incident: RiskIncident
    ):
        """Impossible de lire un incident d'un autre tenant."""
        with pytest.raises(IncidentNotFoundError):
            risk_service.get_incident(other_tenant_incident.id)

    def test_cannot_list_other_tenant_incidents(
        self,
        risk_service: RiskService,
        sample_incident: RiskIncident,
        other_tenant_incident: RiskIncident
    ):
        """Liste uniquement les incidents du tenant courant."""
        items, total, _ = risk_service.list_incidents()

        incident_ids = [i.id for i in items]
        assert sample_incident.id in incident_ids
        assert other_tenant_incident.id not in incident_ids

    def test_cannot_update_other_tenant_incident(
        self,
        risk_service: RiskService,
        other_tenant_incident: RiskIncident
    ):
        """Impossible de mettre à jour un incident d'un autre tenant."""
        from app.modules.risk.schemas import IncidentUpdate
        with pytest.raises(IncidentNotFoundError):
            risk_service.update_incident(
                other_tenant_incident.id,
                IncidentUpdate(title="Hacked")
            )

    def test_cannot_delete_other_tenant_incident(
        self,
        risk_service: RiskService,
        other_tenant_incident: RiskIncident
    ):
        """Impossible de supprimer un incident d'un autre tenant."""
        with pytest.raises(IncidentNotFoundError):
            risk_service.delete_incident(other_tenant_incident.id)

    def test_cannot_start_investigation_other_tenant_incident(
        self,
        risk_service: RiskService,
        other_tenant_incident: RiskIncident
    ):
        """Impossible de démarrer une investigation sur un incident d'un autre tenant."""
        with pytest.raises(IncidentNotFoundError):
            risk_service.start_investigation(other_tenant_incident.id)

    def test_cannot_resolve_other_tenant_incident(
        self,
        risk_service: RiskService,
        other_tenant_incident: RiskIncident
    ):
        """Impossible de résoudre un incident d'un autre tenant."""
        from app.modules.risk.schemas import IncidentResolution
        with pytest.raises(IncidentNotFoundError):
            risk_service.resolve_incident(
                other_tenant_incident.id,
                IncidentResolution(lessons_learned="Hacked")
            )

    def test_cannot_close_other_tenant_incident(
        self,
        risk_service: RiskService,
        other_tenant_incident: RiskIncident
    ):
        """Impossible de clôturer un incident d'un autre tenant."""
        with pytest.raises(IncidentNotFoundError):
            risk_service.close_incident(other_tenant_incident.id)

    def test_cannot_create_incident_for_other_tenant_risk(
        self,
        risk_service: RiskService,
        other_tenant_risk: Risk
    ):
        """Impossible de créer un incident pour un risque d'un autre tenant."""
        with pytest.raises(RiskNotFoundError):
            risk_service.create_incident(IncidentCreate(
                risk_id=other_tenant_risk.id,
                title="Hacked Incident"
            ))


class TestCodeUniquenessPerTenant:
    """Tests d'unicité des codes par tenant."""

    def test_same_matrix_code_different_tenants(
        self,
        risk_service: RiskService,
        other_tenant_service: RiskService
    ):
        """Même code matrice autorisé dans différents tenants."""
        matrix1 = risk_service.create_matrix(RiskMatrixCreate(
            name="Matrix",
            code="MAT-SHARED"
        ))
        matrix2 = other_tenant_service.create_matrix(RiskMatrixCreate(
            name="Matrix",
            code="MAT-SHARED"
        ))

        assert matrix1.code == matrix2.code
        assert matrix1.tenant_id != matrix2.tenant_id

    def test_same_risk_code_different_tenants(
        self,
        risk_service: RiskService,
        other_tenant_service: RiskService,
        sample_matrix: RiskMatrix,
        other_tenant_matrix: RiskMatrix
    ):
        """Même code risque autorisé dans différents tenants."""
        risk1 = risk_service.create_risk(RiskCreate(
            code="RSK-SHARED",
            title="Risk 1",
            category="operational"
        ))
        risk2 = other_tenant_service.create_risk(RiskCreate(
            code="RSK-SHARED",
            title="Risk 2",
            category="operational"
        ))

        assert risk1.code == risk2.code
        assert risk1.tenant_id != risk2.tenant_id


class TestReportsTenantIsolation:
    """Tests d'isolation multi-tenant pour les rapports."""

    def test_report_only_includes_tenant_data(
        self,
        risk_service: RiskService,
        sample_risk: Risk,
        sample_control: Control,
        sample_action: MitigationAction,
        sample_indicator: RiskIndicator,
        sample_incident: RiskIncident,
        other_tenant_risk: Risk,
        other_tenant_control: Control,
        other_tenant_action: MitigationAction,
        other_tenant_indicator: RiskIndicator,
        other_tenant_incident: RiskIncident
    ):
        """Le rapport ne contient que les données du tenant courant."""
        report = risk_service.generate_report()

        assert report.total_risks == 1
        assert report.total_actions == 1
        assert report.total_kris == 1
        assert report.total_incidents == 1

    def test_heatmap_only_includes_tenant_data(
        self,
        risk_service: RiskService,
        sample_risk: Risk,
        other_tenant_risk: Risk
    ):
        """La heatmap ne contient que les données du tenant courant."""
        heatmap = risk_service.get_heatmap()

        total_count = sum(cell["count"] for cell in heatmap)
        assert total_count == 1
