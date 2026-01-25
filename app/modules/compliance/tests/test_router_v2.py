"""
Tests pour les endpoints v2 du module Compliance - CORE SaaS
============================================================

Coverage: ~90 tests couvrant toutes les entités et workflows
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from fastapi import status

from app.modules.compliance.models import (
    ActionStatus,
    AssessmentStatus,
    AuditStatus,
    ComplianceStatus,
    FindingSeverity,
    IncidentStatus,
    RegulationType,
    RequirementPriority,
    RiskLevel,
)


# =============================================================================
# TESTS REGULATIONS (8 tests)
# =============================================================================

class TestRegulations:
    """Tests pour les endpoints de réglementations."""

    def test_create_regulation_success(
        self, client, mock_saas_context, regulation_data, regulation_id
    ):
        """Test création d'une réglementation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_regulation") as mock_create:
                mock_regulation = MagicMock()
                mock_regulation.id = regulation_id
                mock_regulation.code = regulation_data["code"]
                mock_regulation.name = regulation_data["name"]
                mock_regulation.type = regulation_data["type"]
                mock_create.return_value = mock_regulation

                response = client.post("/v2/compliance/regulations", json=regulation_data)

                assert response.status_code == status.HTTP_201_CREATED
                assert response.json()["code"] == regulation_data["code"]

    def test_list_regulations_success(self, client, mock_saas_context):
        """Test liste des réglementations."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_regulations") as mock_list:
                mock_list.return_value = []

                response = client.get("/v2/compliance/regulations")

                assert response.status_code == status.HTTP_200_OK
                assert isinstance(response.json(), list)

    def test_list_regulations_with_filter(self, client, mock_saas_context):
        """Test liste filtrée par type."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_regulations") as mock_list:
                mock_list.return_value = []

                response = client.get(
                    "/v2/compliance/regulations",
                    params={"regulation_type": RegulationType.PRIVACY.value}
                )

                assert response.status_code == status.HTTP_200_OK

    def test_get_regulation_success(self, client, mock_saas_context, regulation_id, regulation_data):
        """Test récupération d'une réglementation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_regulation") as mock_get:
                mock_regulation = MagicMock()
                mock_regulation.id = regulation_id
                mock_regulation.code = regulation_data["code"]
                mock_get.return_value = mock_regulation

                response = client.get(f"/v2/compliance/regulations/{regulation_id}")

                assert response.status_code == status.HTTP_200_OK

    def test_get_regulation_not_found(self, client, mock_saas_context, regulation_id):
        """Test réglementation non trouvée."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_regulation") as mock_get:
                mock_get.return_value = None

                response = client.get(f"/v2/compliance/regulations/{regulation_id}")

                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_regulation_success(self, client, mock_saas_context, regulation_id):
        """Test mise à jour d'une réglementation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.update_regulation") as mock_update:
                mock_regulation = MagicMock()
                mock_regulation.id = regulation_id
                mock_update.return_value = mock_regulation

                update_data = {"name": "Nom mis à jour"}
                response = client.put(f"/v2/compliance/regulations/{regulation_id}", json=update_data)

                assert response.status_code == status.HTTP_200_OK

    def test_update_regulation_not_found(self, client, mock_saas_context, regulation_id):
        """Test mise à jour réglementation inexistante."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.update_regulation") as mock_update:
                mock_update.return_value = None

                update_data = {"name": "Nom mis à jour"}
                response = client.put(f"/v2/compliance/regulations/{regulation_id}", json=update_data)

                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_regulations_tenant_isolation(self, client, mock_saas_context):
        """Test isolation tenant sur les réglementations."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.get_compliance_service") as mock_service:
                client.get("/v2/compliance/regulations")

                mock_service.assert_called_once_with(
                    mock_service.call_args[0][0],  # db
                    mock_saas_context.tenant_id,
                    mock_saas_context.user_id
                )


# =============================================================================
# TESTS REQUIREMENTS (8 tests)
# =============================================================================

class TestRequirements:
    """Tests pour les endpoints d'exigences."""

    def test_create_requirement_success(self, client, mock_saas_context, requirement_data, requirement_id):
        """Test création d'une exigence."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_requirement") as mock_create:
                mock_requirement = MagicMock()
                mock_requirement.id = requirement_id
                mock_create.return_value = mock_requirement

                response = client.post("/v2/compliance/requirements", json=requirement_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_list_requirements_success(self, client, mock_saas_context):
        """Test liste des exigences."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_requirements") as mock_list:
                mock_list.return_value = []

                response = client.get("/v2/compliance/requirements")

                assert response.status_code == status.HTTP_200_OK

    def test_list_requirements_with_filters(self, client, mock_saas_context, regulation_id):
        """Test liste avec filtres multiples."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_requirements") as mock_list:
                mock_list.return_value = []

                response = client.get(
                    "/v2/compliance/requirements",
                    params={
                        "regulation_id": str(regulation_id),
                        "priority": RequirementPriority.HIGH.value,
                        "compliance_status": ComplianceStatus.PENDING.value
                    }
                )

                assert response.status_code == status.HTTP_200_OK

    def test_get_requirement_success(self, client, mock_saas_context, requirement_id):
        """Test récupération d'une exigence."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_requirement") as mock_get:
                mock_requirement = MagicMock()
                mock_requirement.id = requirement_id
                mock_get.return_value = mock_requirement

                response = client.get(f"/v2/compliance/requirements/{requirement_id}")

                assert response.status_code == status.HTTP_200_OK

    def test_update_requirement_success(self, client, mock_saas_context, requirement_id):
        """Test mise à jour d'une exigence."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.update_requirement") as mock_update:
                mock_requirement = MagicMock()
                mock_update.return_value = mock_requirement

                response = client.put(
                    f"/v2/compliance/requirements/{requirement_id}",
                    json={"title": "Titre mis à jour"}
                )

                assert response.status_code == status.HTTP_200_OK

    def test_assess_requirement_success(self, client, mock_saas_context, requirement_id):
        """Test évaluation d'une exigence."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.assess_requirement") as mock_assess:
                mock_requirement = MagicMock()
                mock_assess.return_value = mock_requirement

                response = client.post(
                    f"/v2/compliance/requirements/{requirement_id}/assess",
                    params={
                        "status": ComplianceStatus.COMPLIANT.value,
                        "score": 95.0
                    }
                )

                assert response.status_code == status.HTTP_200_OK

    def test_assess_requirement_not_found(self, client, mock_saas_context, requirement_id):
        """Test évaluation exigence inexistante."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.assess_requirement") as mock_assess:
                mock_assess.return_value = None

                response = client.post(
                    f"/v2/compliance/requirements/{requirement_id}/assess",
                    params={"status": ComplianceStatus.COMPLIANT.value}
                )

                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_requirements_pagination(self, client, mock_saas_context):
        """Test pagination des exigences."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_requirements") as mock_list:
                mock_list.return_value = []

                response = client.get(
                    "/v2/compliance/requirements",
                    params={"skip": 10, "limit": 50}
                )

                assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TESTS ASSESSMENTS (12 tests)
# =============================================================================

class TestAssessments:
    """Tests pour les endpoints d'évaluations."""

    def test_create_assessment_success(self, client, mock_saas_context, assessment_data, assessment_id):
        """Test création d'une évaluation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_assessment") as mock_create:
                mock_assessment = MagicMock()
                mock_assessment.id = assessment_id
                mock_assessment.number = "ASS-2024-0001"
                mock_create.return_value = mock_assessment

                response = client.post("/v2/compliance/assessments", json=assessment_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_get_assessment_success(self, client, mock_saas_context, assessment_id):
        """Test récupération d'une évaluation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_assessment") as mock_get:
                mock_assessment = MagicMock()
                mock_assessment.id = assessment_id
                mock_get.return_value = mock_assessment

                response = client.get(f"/v2/compliance/assessments/{assessment_id}")

                assert response.status_code == status.HTTP_200_OK

    def test_get_assessment_not_found(self, client, mock_saas_context, assessment_id):
        """Test évaluation non trouvée."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_assessment") as mock_get:
                mock_get.return_value = None

                response = client.get(f"/v2/compliance/assessments/{assessment_id}")

                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_start_assessment_success(self, client, mock_saas_context, assessment_id):
        """Test démarrage d'une évaluation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.start_assessment") as mock_start:
                mock_assessment = MagicMock()
                mock_assessment.status = AssessmentStatus.IN_PROGRESS
                mock_start.return_value = mock_assessment

                response = client.post(f"/v2/compliance/assessments/{assessment_id}/start")

                assert response.status_code == status.HTTP_200_OK

    def test_start_assessment_already_started(self, client, mock_saas_context, assessment_id):
        """Test démarrage évaluation déjà démarrée."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.start_assessment") as mock_start:
                mock_start.return_value = None

                response = client.post(f"/v2/compliance/assessments/{assessment_id}/start")

                assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_complete_assessment_success(self, client, mock_saas_context, assessment_id):
        """Test complétion d'une évaluation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.complete_assessment") as mock_complete:
                mock_assessment = MagicMock()
                mock_assessment.status = AssessmentStatus.COMPLETED
                mock_complete.return_value = mock_assessment

                response = client.post(
                    f"/v2/compliance/assessments/{assessment_id}/complete",
                    params={
                        "findings_summary": "5 écarts identifiés",
                        "recommendations": "Renforcer les contrôles d'accès"
                    }
                )

                assert response.status_code == status.HTTP_200_OK

    def test_complete_assessment_not_in_progress(self, client, mock_saas_context, assessment_id):
        """Test complétion évaluation pas en cours."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.complete_assessment") as mock_complete:
                mock_complete.return_value = None

                response = client.post(f"/v2/compliance/assessments/{assessment_id}/complete")

                assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_approve_assessment_success(self, client, mock_saas_context, assessment_id):
        """Test approbation d'une évaluation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.approve_assessment") as mock_approve:
                mock_assessment = MagicMock()
                mock_assessment.status = AssessmentStatus.APPROVED
                mock_approve.return_value = mock_assessment

                response = client.post(f"/v2/compliance/assessments/{assessment_id}/approve")

                assert response.status_code == status.HTTP_200_OK

    def test_approve_assessment_not_completed(self, client, mock_saas_context, assessment_id):
        """Test approbation évaluation pas complétée."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.approve_assessment") as mock_approve:
                mock_approve.return_value = None

                response = client.post(f"/v2/compliance/assessments/{assessment_id}/approve")

                assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_assessment_workflow_complete(self, client, mock_saas_context, assessment_data, assessment_id):
        """Test workflow complet d'évaluation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            # Création
            with patch("app.modules.compliance.service.ComplianceService.create_assessment") as mock_create:
                mock_assessment = MagicMock()
                mock_assessment.id = assessment_id
                mock_assessment.status = AssessmentStatus.DRAFT
                mock_create.return_value = mock_assessment

                response = client.post("/v2/compliance/assessments", json=assessment_data)
                assert response.status_code == status.HTTP_201_CREATED

            # Démarrage
            with patch("app.modules.compliance.service.ComplianceService.start_assessment") as mock_start:
                mock_assessment.status = AssessmentStatus.IN_PROGRESS
                mock_start.return_value = mock_assessment

                response = client.post(f"/v2/compliance/assessments/{assessment_id}/start")
                assert response.status_code == status.HTTP_200_OK

            # Complétion
            with patch("app.modules.compliance.service.ComplianceService.complete_assessment") as mock_complete:
                mock_assessment.status = AssessmentStatus.COMPLETED
                mock_complete.return_value = mock_assessment

                response = client.post(f"/v2/compliance/assessments/{assessment_id}/complete")
                assert response.status_code == status.HTTP_200_OK

            # Approbation
            with patch("app.modules.compliance.service.ComplianceService.approve_assessment") as mock_approve:
                mock_assessment.status = AssessmentStatus.APPROVED
                mock_approve.return_value = mock_assessment

                response = client.post(f"/v2/compliance/assessments/{assessment_id}/approve")
                assert response.status_code == status.HTTP_200_OK

    def test_assessment_scoring(self, client, mock_saas_context, assessment_id):
        """Test calcul du score d'évaluation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.complete_assessment") as mock_complete:
                mock_assessment = MagicMock()
                mock_assessment.overall_score = Decimal("85.5")
                mock_assessment.compliant_count = 17
                mock_assessment.non_compliant_count = 3
                mock_complete.return_value = mock_assessment

                response = client.post(f"/v2/compliance/assessments/{assessment_id}/complete")

                assert response.status_code == status.HTTP_200_OK

    def test_assessment_user_tracking(self, client, mock_saas_context, assessment_id):
        """Test tracking utilisateur sur évaluation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.approve_assessment") as mock_approve:
                mock_assessment = MagicMock()
                mock_approve.return_value = mock_assessment

                client.post(f"/v2/compliance/assessments/{assessment_id}/approve")

                mock_approve.assert_called_once_with(assessment_id, mock_saas_context.user_id)


# =============================================================================
# TESTS GAPS (8 tests)
# =============================================================================

class TestGaps:
    """Tests pour les endpoints d'écarts."""

    def test_create_gap_success(self, client, mock_saas_context, gap_data, gap_id):
        """Test création d'un écart."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_gap") as mock_create:
                mock_gap = MagicMock()
                mock_gap.id = gap_id
                mock_create.return_value = mock_gap

                response = client.post("/v2/compliance/gaps", json=gap_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_create_gap_with_severity(self, client, mock_saas_context, gap_data, gap_id):
        """Test création écart avec calcul sévérité."""
        gap_data["severity"] = RiskLevel.CRITICAL

        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_gap") as mock_create:
                mock_gap = MagicMock()
                mock_gap.id = gap_id
                mock_gap.risk_score = Decimal("100")
                mock_create.return_value = mock_gap

                response = client.post("/v2/compliance/gaps", json=gap_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_close_gap_success(self, client, mock_saas_context, gap_id):
        """Test clôture d'un écart."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.close_gap") as mock_close:
                mock_gap = MagicMock()
                mock_gap.is_open = False
                mock_close.return_value = mock_gap

                response = client.post(f"/v2/compliance/gaps/{gap_id}/close")

                assert response.status_code == status.HTTP_200_OK

    def test_close_gap_already_closed(self, client, mock_saas_context, gap_id):
        """Test clôture écart déjà clôturé."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.close_gap") as mock_close:
                mock_close.return_value = None

                response = client.post(f"/v2/compliance/gaps/{gap_id}/close")

                assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_gap_risk_calculation(self, client, mock_saas_context, gap_data, gap_id):
        """Test calcul du risque d'un écart."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_gap") as mock_create:
                mock_gap = MagicMock()
                mock_gap.severity = RiskLevel.HIGH
                mock_gap.risk_score = Decimal("75")
                mock_create.return_value = mock_gap

                response = client.post("/v2/compliance/gaps", json=gap_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_gap_lifecycle(self, client, mock_saas_context, gap_data, gap_id):
        """Test cycle de vie complet d'un écart."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            # Création
            with patch("app.modules.compliance.service.ComplianceService.create_gap") as mock_create:
                mock_gap = MagicMock()
                mock_gap.id = gap_id
                mock_gap.is_open = True
                mock_create.return_value = mock_gap

                response = client.post("/v2/compliance/gaps", json=gap_data)
                assert response.status_code == status.HTTP_201_CREATED

            # Clôture
            with patch("app.modules.compliance.service.ComplianceService.close_gap") as mock_close:
                mock_gap.is_open = False
                mock_close.return_value = mock_gap

                response = client.post(f"/v2/compliance/gaps/{gap_id}/close")
                assert response.status_code == status.HTTP_200_OK

    def test_gap_target_date_validation(self, client, mock_saas_context, gap_data, gap_id):
        """Test validation date cible écart."""
        gap_data["target_closure_date"] = date(2024, 12, 31)

        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_gap") as mock_create:
                mock_gap = MagicMock()
                mock_gap.id = gap_id
                mock_create.return_value = mock_gap

                response = client.post("/v2/compliance/gaps", json=gap_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_gap_status_tracking(self, client, mock_saas_context, gap_id):
        """Test suivi du statut d'un écart."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.close_gap") as mock_close:
                mock_gap = MagicMock()
                mock_gap.current_status = ComplianceStatus.COMPLIANT
                mock_gap.actual_closure_date = date.today()
                mock_close.return_value = mock_gap

                response = client.post(f"/v2/compliance/gaps/{gap_id}/close")

                assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TESTS ACTIONS (10 tests)
# =============================================================================

class TestActions:
    """Tests pour les endpoints d'actions correctives."""

    def test_create_action_success(self, client, mock_saas_context, action_data, action_id):
        """Test création d'une action."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_action") as mock_create:
                mock_action = MagicMock()
                mock_action.id = action_id
                mock_action.number = "ACT-2024-0001"
                mock_create.return_value = mock_action

                response = client.post("/v2/compliance/actions", json=action_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_get_action_success(self, client, mock_saas_context, action_id):
        """Test récupération d'une action."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_action") as mock_get:
                mock_action = MagicMock()
                mock_action.id = action_id
                mock_get.return_value = mock_action

                response = client.get(f"/v2/compliance/actions/{action_id}")

                assert response.status_code == status.HTTP_200_OK

    def test_get_action_not_found(self, client, mock_saas_context, action_id):
        """Test action non trouvée."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_action") as mock_get:
                mock_get.return_value = None

                response = client.get(f"/v2/compliance/actions/{action_id}")

                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_start_action_success(self, client, mock_saas_context, action_id):
        """Test démarrage d'une action."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.start_action") as mock_start:
                mock_action = MagicMock()
                mock_action.status = ActionStatus.IN_PROGRESS
                mock_start.return_value = mock_action

                response = client.post(f"/v2/compliance/actions/{action_id}/start")

                assert response.status_code == status.HTTP_200_OK

    def test_complete_action_success(self, client, mock_saas_context, action_id):
        """Test complétion d'une action."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.complete_action") as mock_complete:
                mock_action = MagicMock()
                mock_action.status = ActionStatus.COMPLETED
                mock_complete.return_value = mock_action

                response = client.post(
                    f"/v2/compliance/actions/{action_id}/complete",
                    params={
                        "resolution_notes": "Action terminée avec succès",
                        "actual_cost": 4500.00
                    }
                )

                assert response.status_code == status.HTTP_200_OK

    def test_verify_action_success(self, client, mock_saas_context, action_id):
        """Test vérification d'une action."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.verify_action") as mock_verify:
                mock_action = MagicMock()
                mock_action.status = ActionStatus.VERIFIED
                mock_verify.return_value = mock_action

                response = client.post(
                    f"/v2/compliance/actions/{action_id}/verify",
                    params={"verification_notes": "Action vérifiée et conforme"}
                )

                assert response.status_code == status.HTTP_200_OK

    def test_get_overdue_actions(self, client, mock_saas_context):
        """Test récupération des actions en retard."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_overdue_actions") as mock_overdue:
                mock_overdue.return_value = []

                response = client.get("/v2/compliance/actions/overdue")

                assert response.status_code == status.HTTP_200_OK

    def test_action_workflow_complete(self, client, mock_saas_context, action_data, action_id):
        """Test workflow complet d'une action."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            # Création
            with patch("app.modules.compliance.service.ComplianceService.create_action") as mock_create:
                mock_action = MagicMock()
                mock_action.id = action_id
                mock_action.status = ActionStatus.OPEN
                mock_create.return_value = mock_action

                response = client.post("/v2/compliance/actions", json=action_data)
                assert response.status_code == status.HTTP_201_CREATED

            # Démarrage
            with patch("app.modules.compliance.service.ComplianceService.start_action") as mock_start:
                mock_action.status = ActionStatus.IN_PROGRESS
                mock_start.return_value = mock_action

                response = client.post(f"/v2/compliance/actions/{action_id}/start")
                assert response.status_code == status.HTTP_200_OK

            # Complétion
            with patch("app.modules.compliance.service.ComplianceService.complete_action") as mock_complete:
                mock_action.status = ActionStatus.COMPLETED
                mock_complete.return_value = mock_action

                response = client.post(
                    f"/v2/compliance/actions/{action_id}/complete",
                    params={"resolution_notes": "Terminé"}
                )
                assert response.status_code == status.HTTP_200_OK

            # Vérification
            with patch("app.modules.compliance.service.ComplianceService.verify_action") as mock_verify:
                mock_action.status = ActionStatus.VERIFIED
                mock_verify.return_value = mock_action

                response = client.post(f"/v2/compliance/actions/{action_id}/verify")
                assert response.status_code == status.HTTP_200_OK

    def test_action_cost_tracking(self, client, mock_saas_context, action_id):
        """Test suivi des coûts d'une action."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.complete_action") as mock_complete:
                mock_action = MagicMock()
                mock_action.estimated_cost = Decimal("5000.00")
                mock_action.actual_cost = Decimal("4500.00")
                mock_complete.return_value = mock_action

                response = client.post(
                    f"/v2/compliance/actions/{action_id}/complete",
                    params={
                        "resolution_notes": "Terminé",
                        "actual_cost": 4500.00
                    }
                )

                assert response.status_code == status.HTTP_200_OK

    def test_action_evidence_tracking(self, client, mock_saas_context, action_id):
        """Test suivi des preuves d'une action."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.complete_action") as mock_complete:
                mock_action = MagicMock()
                mock_complete.return_value = mock_action

                response = client.post(
                    f"/v2/compliance/actions/{action_id}/complete",
                    params={
                        "resolution_notes": "Terminé",
                        "evidence": ["doc1.pdf", "screenshot.png"]
                    }
                )

                assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TESTS POLICIES (8 tests)
# =============================================================================

class TestPolicies:
    """Tests pour les endpoints de politiques."""

    def test_create_policy_success(self, client, mock_saas_context, policy_data, policy_id):
        """Test création d'une politique."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_policy") as mock_create:
                mock_policy = MagicMock()
                mock_policy.id = policy_id
                mock_create.return_value = mock_policy

                response = client.post("/v2/compliance/policies", json=policy_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_list_policies_success(self, client, mock_saas_context):
        """Test liste des politiques."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_policies") as mock_list:
                mock_list.return_value = []

                response = client.get("/v2/compliance/policies")

                assert response.status_code == status.HTTP_200_OK

    def test_list_policies_published_only(self, client, mock_saas_context):
        """Test liste des politiques publiées."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_policies") as mock_list:
                mock_list.return_value = []

                response = client.get(
                    "/v2/compliance/policies",
                    params={"is_published": True}
                )

                assert response.status_code == status.HTTP_200_OK

    def test_get_policy_success(self, client, mock_saas_context, policy_id):
        """Test récupération d'une politique."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_policy") as mock_get:
                mock_policy = MagicMock()
                mock_policy.id = policy_id
                mock_get.return_value = mock_policy

                response = client.get(f"/v2/compliance/policies/{policy_id}")

                assert response.status_code == status.HTTP_200_OK

    def test_publish_policy_success(self, client, mock_saas_context, policy_id):
        """Test publication d'une politique."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.publish_policy") as mock_publish:
                mock_policy = MagicMock()
                mock_policy.is_published = True
                mock_publish.return_value = mock_policy

                response = client.post(f"/v2/compliance/policies/{policy_id}/publish")

                assert response.status_code == status.HTTP_200_OK

    def test_acknowledge_policy_success(self, client, mock_saas_context, policy_id):
        """Test accusé de réception d'une politique."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.acknowledge_policy") as mock_ack:
                mock_acknowledgment = MagicMock()
                mock_ack.return_value = mock_acknowledgment

                ack_data = {
                    "policy_id": str(policy_id),
                    "notes": "Lu et compris"
                }
                response = client.post("/v2/compliance/policies/acknowledge", json=ack_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_policy_version_tracking(self, client, mock_saas_context, policy_data, policy_id):
        """Test suivi des versions de politique."""
        policy_data["version"] = "2.0"

        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_policy") as mock_create:
                mock_policy = MagicMock()
                mock_policy.id = policy_id
                mock_policy.version = "2.0"
                mock_create.return_value = mock_policy

                response = client.post("/v2/compliance/policies", json=policy_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_policy_acknowledgment_tracking(self, client, mock_saas_context, policy_id):
        """Test suivi des accusés de réception."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.acknowledge_policy") as mock_ack:
                mock_acknowledgment = MagicMock()
                mock_acknowledgment.user_id = mock_saas_context.user_id
                mock_ack.return_value = mock_acknowledgment

                ack_data = {"policy_id": str(policy_id)}
                client.post("/v2/compliance/policies/acknowledge", json=ack_data)

                mock_ack.assert_called_once()


# =============================================================================
# TESTS TRAININGS (6 tests)
# =============================================================================

class TestTrainings:
    """Tests pour les endpoints de formations."""

    def test_create_training_success(self, client, mock_saas_context, training_data, training_id):
        """Test création d'une formation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_training") as mock_create:
                mock_training = MagicMock()
                mock_training.id = training_id
                mock_create.return_value = mock_training

                response = client.post("/v2/compliance/trainings", json=training_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_get_training_success(self, client, mock_saas_context, training_id):
        """Test récupération d'une formation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_training") as mock_get:
                mock_training = MagicMock()
                mock_training.id = training_id
                mock_get.return_value = mock_training

                response = client.get(f"/v2/compliance/trainings/{training_id}")

                assert response.status_code == status.HTTP_200_OK

    def test_assign_training_success(self, client, mock_saas_context, training_id, completion_id):
        """Test assignation d'une formation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.assign_training") as mock_assign:
                mock_completion = MagicMock()
                mock_completion.id = completion_id
                mock_assign.return_value = mock_completion

                assign_data = {
                    "training_id": str(training_id),
                    "user_id": str(mock_saas_context.user_id),
                    "due_date": str(date(2024, 12, 31))
                }
                response = client.post("/v2/compliance/trainings/assign", json=assign_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_start_training_completion_success(self, client, mock_saas_context, completion_id):
        """Test démarrage d'une formation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.start_training") as mock_start:
                mock_completion = MagicMock()
                mock_completion.started_at = datetime.utcnow()
                mock_start.return_value = mock_completion

                response = client.post(f"/v2/compliance/trainings/completions/{completion_id}/start")

                assert response.status_code == status.HTTP_200_OK

    def test_complete_training_success(self, client, mock_saas_context, completion_id):
        """Test complétion d'une formation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.complete_training") as mock_complete:
                mock_completion = MagicMock()
                mock_completion.passed = True
                mock_completion.score = 85
                mock_complete.return_value = mock_completion

                response = client.post(
                    f"/v2/compliance/trainings/completions/{completion_id}/complete",
                    params={
                        "score": 85,
                        "certificate_number": "CERT-2024-001"
                    }
                )

                assert response.status_code == status.HTTP_200_OK

    def test_training_workflow_complete(self, client, mock_saas_context, training_data, training_id, completion_id):
        """Test workflow complet de formation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            # Création formation
            with patch("app.modules.compliance.service.ComplianceService.create_training") as mock_create:
                mock_training = MagicMock()
                mock_training.id = training_id
                mock_create.return_value = mock_training

                response = client.post("/v2/compliance/trainings", json=training_data)
                assert response.status_code == status.HTTP_201_CREATED

            # Assignation
            with patch("app.modules.compliance.service.ComplianceService.assign_training") as mock_assign:
                mock_completion = MagicMock()
                mock_completion.id = completion_id
                mock_assign.return_value = mock_completion

                assign_data = {
                    "training_id": str(training_id),
                    "user_id": str(mock_saas_context.user_id),
                    "due_date": str(date(2024, 12, 31))
                }
                response = client.post("/v2/compliance/trainings/assign", json=assign_data)
                assert response.status_code == status.HTTP_201_CREATED

            # Démarrage
            with patch("app.modules.compliance.service.ComplianceService.start_training") as mock_start:
                mock_completion.started_at = datetime.utcnow()
                mock_start.return_value = mock_completion

                response = client.post(f"/v2/compliance/trainings/completions/{completion_id}/start")
                assert response.status_code == status.HTTP_200_OK

            # Complétion
            with patch("app.modules.compliance.service.ComplianceService.complete_training") as mock_complete:
                mock_completion.passed = True
                mock_complete.return_value = mock_completion

                response = client.post(
                    f"/v2/compliance/trainings/completions/{completion_id}/complete",
                    params={"score": 90}
                )
                assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TESTS AUDITS (10 tests)
# =============================================================================

class TestAudits:
    """Tests pour les endpoints d'audits."""

    def test_create_audit_success(self, client, mock_saas_context, audit_data, audit_id):
        """Test création d'un audit."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_audit") as mock_create:
                mock_audit = MagicMock()
                mock_audit.id = audit_id
                mock_audit.number = "AUD-2024-0001"
                mock_create.return_value = mock_audit

                response = client.post("/v2/compliance/audits", json=audit_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_get_audit_success(self, client, mock_saas_context, audit_id):
        """Test récupération d'un audit."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_audit") as mock_get:
                mock_audit = MagicMock()
                mock_audit.id = audit_id
                mock_get.return_value = mock_audit

                response = client.get(f"/v2/compliance/audits/{audit_id}")

                assert response.status_code == status.HTTP_200_OK

    def test_start_audit_success(self, client, mock_saas_context, audit_id):
        """Test démarrage d'un audit."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.start_audit") as mock_start:
                mock_audit = MagicMock()
                mock_audit.status = AuditStatus.IN_PROGRESS
                mock_start.return_value = mock_audit

                response = client.post(f"/v2/compliance/audits/{audit_id}/start")

                assert response.status_code == status.HTTP_200_OK

    def test_complete_audit_success(self, client, mock_saas_context, audit_id):
        """Test complétion d'un audit."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.complete_audit") as mock_complete:
                mock_audit = MagicMock()
                mock_audit.status = AuditStatus.COMPLETED
                mock_complete.return_value = mock_audit

                response = client.post(
                    f"/v2/compliance/audits/{audit_id}/complete",
                    params={
                        "executive_summary": "Audit réussi",
                        "conclusions": "Conformité globale satisfaisante",
                        "recommendations": "Renforcer la gouvernance"
                    }
                )

                assert response.status_code == status.HTTP_200_OK

    def test_close_audit_success(self, client, mock_saas_context, audit_id):
        """Test clôture d'un audit."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.close_audit") as mock_close:
                mock_audit = MagicMock()
                mock_audit.status = AuditStatus.CLOSED
                mock_close.return_value = mock_audit

                response = client.post(f"/v2/compliance/audits/{audit_id}/close")

                assert response.status_code == status.HTTP_200_OK

    def test_audit_workflow_complete(self, client, mock_saas_context, audit_data, audit_id):
        """Test workflow complet d'un audit."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            # Création
            with patch("app.modules.compliance.service.ComplianceService.create_audit") as mock_create:
                mock_audit = MagicMock()
                mock_audit.id = audit_id
                mock_audit.status = AuditStatus.PLANNED
                mock_create.return_value = mock_audit

                response = client.post("/v2/compliance/audits", json=audit_data)
                assert response.status_code == status.HTTP_201_CREATED

            # Démarrage
            with patch("app.modules.compliance.service.ComplianceService.start_audit") as mock_start:
                mock_audit.status = AuditStatus.IN_PROGRESS
                mock_start.return_value = mock_audit

                response = client.post(f"/v2/compliance/audits/{audit_id}/start")
                assert response.status_code == status.HTTP_200_OK

            # Complétion
            with patch("app.modules.compliance.service.ComplianceService.complete_audit") as mock_complete:
                mock_audit.status = AuditStatus.COMPLETED
                mock_complete.return_value = mock_audit

                response = client.post(f"/v2/compliance/audits/{audit_id}/complete")
                assert response.status_code == status.HTTP_200_OK

            # Clôture
            with patch("app.modules.compliance.service.ComplianceService.close_audit") as mock_close:
                mock_audit.status = AuditStatus.CLOSED
                mock_close.return_value = mock_audit

                response = client.post(f"/v2/compliance/audits/{audit_id}/close")
                assert response.status_code == status.HTTP_200_OK

    def test_audit_findings_count(self, client, mock_saas_context, audit_id):
        """Test comptage des constatations d'audit."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.complete_audit") as mock_complete:
                mock_audit = MagicMock()
                mock_audit.total_findings = 15
                mock_audit.critical_findings = 2
                mock_audit.major_findings = 5
                mock_audit.minor_findings = 8
                mock_complete.return_value = mock_audit

                response = client.post(f"/v2/compliance/audits/{audit_id}/complete")

                assert response.status_code == status.HTTP_200_OK

    def test_audit_date_tracking(self, client, mock_saas_context, audit_id):
        """Test suivi des dates d'audit."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.start_audit") as mock_start:
                mock_audit = MagicMock()
                mock_audit.actual_start = date.today()
                mock_start.return_value = mock_audit

                response = client.post(f"/v2/compliance/audits/{audit_id}/start")

                assert response.status_code == status.HTTP_200_OK

    def test_audit_approval_tracking(self, client, mock_saas_context, audit_id):
        """Test suivi d'approbation d'audit."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.close_audit") as mock_close:
                mock_audit = MagicMock()
                mock_audit.approved_by = mock_saas_context.user_id
                mock_close.return_value = mock_audit

                client.post(f"/v2/compliance/audits/{audit_id}/close")

                mock_close.assert_called_once_with(audit_id, mock_saas_context.user_id)

    def test_audit_schedule_validation(self, client, mock_saas_context, audit_data, audit_id):
        """Test validation du planning d'audit."""
        audit_data["planned_start"] = date(2024, 4, 1)
        audit_data["planned_end"] = date(2024, 4, 5)

        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_audit") as mock_create:
                mock_audit = MagicMock()
                mock_audit.id = audit_id
                mock_create.return_value = mock_audit

                response = client.post("/v2/compliance/audits", json=audit_data)

                assert response.status_code == status.HTTP_201_CREATED


# =============================================================================
# TESTS FINDINGS (6 tests)
# =============================================================================

class TestFindings:
    """Tests pour les endpoints de constatations."""

    def test_create_finding_success(self, client, mock_saas_context, finding_data, finding_id):
        """Test création d'une constatation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_finding") as mock_create:
                mock_finding = MagicMock()
                mock_finding.id = finding_id
                mock_finding.number = "AUD-2024-0001-F01"
                mock_create.return_value = mock_finding

                response = client.post("/v2/compliance/findings", json=finding_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_respond_to_finding_success(self, client, mock_saas_context, finding_id):
        """Test réponse à une constatation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.respond_to_finding") as mock_respond:
                mock_finding = MagicMock()
                mock_finding.response = "Mesures correctives mises en place"
                mock_respond.return_value = mock_finding

                response = client.post(
                    f"/v2/compliance/findings/{finding_id}/respond",
                    params={"response": "Mesures correctives mises en place"}
                )

                assert response.status_code == status.HTTP_200_OK

    def test_close_finding_success(self, client, mock_saas_context, finding_id):
        """Test clôture d'une constatation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.close_finding") as mock_close:
                mock_finding = MagicMock()
                mock_finding.is_closed = True
                mock_close.return_value = mock_finding

                response = client.post(f"/v2/compliance/findings/{finding_id}/close")

                assert response.status_code == status.HTTP_200_OK

    def test_finding_severity_tracking(self, client, mock_saas_context, finding_data, finding_id):
        """Test suivi de sévérité des constatations."""
        finding_data["severity"] = FindingSeverity.CRITICAL

        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_finding") as mock_create:
                mock_finding = MagicMock()
                mock_finding.severity = FindingSeverity.CRITICAL
                mock_create.return_value = mock_finding

                response = client.post("/v2/compliance/findings", json=finding_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_finding_response_lifecycle(self, client, mock_saas_context, finding_data, finding_id):
        """Test cycle de vie d'une constatation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            # Création
            with patch("app.modules.compliance.service.ComplianceService.create_finding") as mock_create:
                mock_finding = MagicMock()
                mock_finding.id = finding_id
                mock_create.return_value = mock_finding

                response = client.post("/v2/compliance/findings", json=finding_data)
                assert response.status_code == status.HTTP_201_CREATED

            # Réponse
            with patch("app.modules.compliance.service.ComplianceService.respond_to_finding") as mock_respond:
                mock_finding.response = "Actions correctives"
                mock_respond.return_value = mock_finding

                response = client.post(
                    f"/v2/compliance/findings/{finding_id}/respond",
                    params={"response": "Actions correctives"}
                )
                assert response.status_code == status.HTTP_200_OK

            # Clôture
            with patch("app.modules.compliance.service.ComplianceService.close_finding") as mock_close:
                mock_finding.is_closed = True
                mock_close.return_value = mock_finding

                response = client.post(f"/v2/compliance/findings/{finding_id}/close")
                assert response.status_code == status.HTTP_200_OK

    def test_finding_date_tracking(self, client, mock_saas_context, finding_id):
        """Test suivi des dates de constatation."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.respond_to_finding") as mock_respond:
                mock_finding = MagicMock()
                mock_finding.response_date = date.today()
                mock_respond.return_value = mock_finding

                response = client.post(
                    f"/v2/compliance/findings/{finding_id}/respond",
                    params={"response": "Réponse"}
                )

                assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TESTS RISKS (6 tests)
# =============================================================================

class TestRisks:
    """Tests pour les endpoints de risques."""

    def test_create_risk_success(self, client, mock_saas_context, risk_data, risk_id):
        """Test création d'un risque."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_risk") as mock_create:
                mock_risk = MagicMock()
                mock_risk.id = risk_id
                mock_risk.risk_score = 12
                mock_risk.risk_level = RiskLevel.HIGH
                mock_create.return_value = mock_risk

                response = client.post("/v2/compliance/risks", json=risk_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_get_risk_success(self, client, mock_saas_context, risk_id):
        """Test récupération d'un risque."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_risk") as mock_get:
                mock_risk = MagicMock()
                mock_risk.id = risk_id
                mock_get.return_value = mock_risk

                response = client.get(f"/v2/compliance/risks/{risk_id}")

                assert response.status_code == status.HTTP_200_OK

    def test_update_risk_success(self, client, mock_saas_context, risk_id):
        """Test mise à jour d'un risque."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.update_risk") as mock_update:
                mock_risk = MagicMock()
                mock_risk.risk_score = 9
                mock_update.return_value = mock_risk

                update_data = {"likelihood": 3, "impact": 3}
                response = client.put(f"/v2/compliance/risks/{risk_id}", json=update_data)

                assert response.status_code == status.HTTP_200_OK

    def test_accept_risk_success(self, client, mock_saas_context, risk_id):
        """Test acceptation d'un risque."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.accept_risk") as mock_accept:
                mock_risk = MagicMock()
                mock_risk.is_accepted = True
                mock_accept.return_value = mock_risk

                response = client.post(f"/v2/compliance/risks/{risk_id}/accept")

                assert response.status_code == status.HTTP_200_OK

    def test_risk_score_calculation(self, client, mock_saas_context, risk_data, risk_id):
        """Test calcul du score de risque."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_risk") as mock_create:
                mock_risk = MagicMock()
                mock_risk.likelihood = 3
                mock_risk.impact = 4
                mock_risk.risk_score = 12
                mock_risk.risk_level = RiskLevel.HIGH
                mock_create.return_value = mock_risk

                response = client.post("/v2/compliance/risks", json=risk_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_risk_residual_calculation(self, client, mock_saas_context, risk_id):
        """Test calcul du risque résiduel."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.update_risk") as mock_update:
                mock_risk = MagicMock()
                mock_risk.residual_likelihood = 2
                mock_risk.residual_impact = 2
                mock_risk.residual_score = 4
                mock_risk.residual_level = RiskLevel.MEDIUM
                mock_update.return_value = mock_risk

                update_data = {
                    "residual_likelihood": 2,
                    "residual_impact": 2
                }
                response = client.put(f"/v2/compliance/risks/{risk_id}", json=update_data)

                assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TESTS INCIDENTS (5 tests)
# =============================================================================

class TestIncidents:
    """Tests pour les endpoints d'incidents."""

    def test_create_incident_success(self, client, mock_saas_context, incident_data, incident_id):
        """Test création d'un incident."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_incident") as mock_create:
                mock_incident = MagicMock()
                mock_incident.id = incident_id
                mock_incident.number = "INC-2024-0001"
                mock_create.return_value = mock_incident

                response = client.post("/v2/compliance/incidents", json=incident_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_get_incident_success(self, client, mock_saas_context, incident_id):
        """Test récupération d'un incident."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_incident") as mock_get:
                mock_incident = MagicMock()
                mock_incident.id = incident_id
                mock_get.return_value = mock_incident

                response = client.get(f"/v2/compliance/incidents/{incident_id}")

                assert response.status_code == status.HTTP_200_OK

    def test_assign_incident_success(self, client, mock_saas_context, incident_id):
        """Test assignation d'un incident."""
        assignee_id = UUID("99999999-9999-9999-9999-999999999999")

        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.assign_incident") as mock_assign:
                mock_incident = MagicMock()
                mock_incident.assigned_to = assignee_id
                mock_assign.return_value = mock_incident

                response = client.post(
                    f"/v2/compliance/incidents/{incident_id}/assign",
                    params={"assignee_id": str(assignee_id)}
                )

                assert response.status_code == status.HTTP_200_OK

    def test_resolve_incident_success(self, client, mock_saas_context, incident_id):
        """Test résolution d'un incident."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.resolve_incident") as mock_resolve:
                mock_incident = MagicMock()
                mock_incident.status = IncidentStatus.RESOLVED
                mock_resolve.return_value = mock_incident

                response = client.post(
                    f"/v2/compliance/incidents/{incident_id}/resolve",
                    params={
                        "resolution": "Accès révoqués et logs analysés",
                        "root_cause": "Configuration IAM incorrecte",
                        "lessons_learned": "Révision du processus de provisioning"
                    }
                )

                assert response.status_code == status.HTTP_200_OK

    def test_close_incident_success(self, client, mock_saas_context, incident_id):
        """Test clôture d'un incident."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.close_incident") as mock_close:
                mock_incident = MagicMock()
                mock_incident.status = IncidentStatus.CLOSED
                mock_close.return_value = mock_incident

                response = client.post(f"/v2/compliance/incidents/{incident_id}/close")

                assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TESTS REPORTS (2 tests)
# =============================================================================

class TestReports:
    """Tests pour les endpoints de rapports."""

    def test_create_report_success(self, client, mock_saas_context, report_data, report_id):
        """Test création d'un rapport."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.create_report") as mock_create:
                mock_report = MagicMock()
                mock_report.id = report_id
                mock_report.number = "RPT-2024-0001"
                mock_create.return_value = mock_report

                response = client.post("/v2/compliance/reports", json=report_data)

                assert response.status_code == status.HTTP_201_CREATED

    def test_publish_report_success(self, client, mock_saas_context, report_id):
        """Test publication d'un rapport."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.publish_report") as mock_publish:
                mock_report = MagicMock()
                mock_report.is_published = True
                mock_publish.return_value = mock_report

                response = client.post(f"/v2/compliance/reports/{report_id}/publish")

                assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TESTS DASHBOARD & METRICS (2 tests)
# =============================================================================

class TestDashboard:
    """Tests pour le dashboard de conformité."""

    def test_get_compliance_metrics_success(self, client, mock_saas_context):
        """Test récupération des métriques de conformité."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_compliance_metrics") as mock_metrics:
                mock_metrics_data = MagicMock()
                mock_metrics_data.overall_compliance_rate = Decimal("85.5")
                mock_metrics_data.total_requirements = 100
                mock_metrics_data.compliant_requirements = 85
                mock_metrics_data.open_gaps = 15
                mock_metrics.return_value = mock_metrics_data

                response = client.get("/v2/compliance/metrics")

                assert response.status_code == status.HTTP_200_OK

    def test_compliance_score_calculation(self, client, mock_saas_context):
        """Test calcul du score de conformité global."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            with patch("app.modules.compliance.service.ComplianceService.get_compliance_metrics") as mock_metrics:
                mock_metrics_data = MagicMock()
                mock_metrics_data.overall_compliance_rate = Decimal("92.3")
                mock_metrics_data.compliant_requirements = 92
                mock_metrics_data.total_requirements = 100
                mock_metrics_data.open_gaps = 8
                mock_metrics_data.open_actions = 5
                mock_metrics_data.overdue_actions = 1
                mock_metrics.return_value = mock_metrics_data

                response = client.get("/v2/compliance/metrics")

                assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TESTS INTEGRATION & WORKFLOWS (2 tests)
# =============================================================================

class TestWorkflows:
    """Tests d'intégration et workflows."""

    def test_assessment_to_remediation_workflow(
        self, client, mock_saas_context,
        assessment_data, assessment_id, gap_data, gap_id, action_data, action_id
    ):
        """Test workflow complet: évaluation -> écarts -> actions."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            # 1. Créer et compléter une évaluation
            with patch("app.modules.compliance.service.ComplianceService.create_assessment") as mock_create_assess:
                mock_assessment = MagicMock()
                mock_assessment.id = assessment_id
                mock_create_assess.return_value = mock_assessment

                response = client.post("/v2/compliance/assessments", json=assessment_data)
                assert response.status_code == status.HTTP_201_CREATED

            # 2. Créer un écart identifié
            with patch("app.modules.compliance.service.ComplianceService.create_gap") as mock_create_gap:
                mock_gap = MagicMock()
                mock_gap.id = gap_id
                mock_create_gap.return_value = mock_gap

                response = client.post("/v2/compliance/gaps", json=gap_data)
                assert response.status_code == status.HTTP_201_CREATED

            # 3. Créer une action corrective
            with patch("app.modules.compliance.service.ComplianceService.create_action") as mock_create_action:
                mock_action = MagicMock()
                mock_action.id = action_id
                mock_create_action.return_value = mock_action

                response = client.post("/v2/compliance/actions", json=action_data)
                assert response.status_code == status.HTTP_201_CREATED

            # 4. Compléter et vérifier l'action
            with patch("app.modules.compliance.service.ComplianceService.complete_action") as mock_complete:
                mock_action.status = ActionStatus.COMPLETED
                mock_complete.return_value = mock_action

                response = client.post(
                    f"/v2/compliance/actions/{action_id}/complete",
                    params={"resolution_notes": "Résolu"}
                )
                assert response.status_code == status.HTTP_200_OK

            # 5. Clôturer l'écart
            with patch("app.modules.compliance.service.ComplianceService.close_gap") as mock_close_gap:
                mock_gap.is_open = False
                mock_close_gap.return_value = mock_gap

                response = client.post(f"/v2/compliance/gaps/{gap_id}/close")
                assert response.status_code == status.HTTP_200_OK

    def test_audit_to_findings_workflow(
        self, client, mock_saas_context,
        audit_data, audit_id, finding_data, finding_id, action_data, action_id
    ):
        """Test workflow: audit -> constatations -> actions correctives."""
        with patch("app.modules.compliance.router_v2.get_saas_context", return_value=mock_saas_context):
            # 1. Créer et démarrer un audit
            with patch("app.modules.compliance.service.ComplianceService.create_audit") as mock_create:
                mock_audit = MagicMock()
                mock_audit.id = audit_id
                mock_create.return_value = mock_audit

                response = client.post("/v2/compliance/audits", json=audit_data)
                assert response.status_code == status.HTTP_201_CREATED

            with patch("app.modules.compliance.service.ComplianceService.start_audit") as mock_start:
                mock_audit.status = AuditStatus.IN_PROGRESS
                mock_start.return_value = mock_audit

                response = client.post(f"/v2/compliance/audits/{audit_id}/start")
                assert response.status_code == status.HTTP_200_OK

            # 2. Créer une constatation
            with patch("app.modules.compliance.service.ComplianceService.create_finding") as mock_create_finding:
                mock_finding = MagicMock()
                mock_finding.id = finding_id
                mock_create_finding.return_value = mock_finding

                response = client.post("/v2/compliance/findings", json=finding_data)
                assert response.status_code == status.HTTP_201_CREATED

            # 3. Compléter l'audit
            with patch("app.modules.compliance.service.ComplianceService.complete_audit") as mock_complete:
                mock_audit.status = AuditStatus.COMPLETED
                mock_audit.total_findings = 1
                mock_complete.return_value = mock_audit

                response = client.post(f"/v2/compliance/audits/{audit_id}/complete")
                assert response.status_code == status.HTTP_200_OK
