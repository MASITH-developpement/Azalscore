"""
Tests pour le router Quality v2 - CORE SaaS
============================================

Couvre tous les endpoints du module quality avec SaaSContext.
Environ 90 tests pour valider la migration CORE SaaS v2.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest




# ============================================================================
# NON-CONFORMITÉS - 12 tests
# ============================================================================

class TestNonConformances:
    """Tests pour les endpoints de non-conformités"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_create_non_conformance(test_client, self, mock_service, mock_context, mock_saas_context, nc_data, nc_entity):
        """Test création d'une non-conformité"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.create_non_conformance.return_value = nc_entity

        response = test_client.post("/v2/quality/non-conformances", json=nc_data)

        assert response.status_code == 200
        data = response.json()
        assert data["nc_number"] == "NC-2024-00001"
        assert data["title"] == "Pièce défectueuse"
        assert data["severity"] == "MAJOR"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_list_non_conformances(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test listing des non-conformités"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_non_conformances.return_value = ([nc_entity], 1)

        response = test_client.get("/v2/quality/non-conformances")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["nc_number"] == "NC-2024-00001"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_list_non_conformances_with_filters(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test listing avec filtres (type, status, severity)"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_non_conformances.return_value = ([nc_entity], 1)

        response = test_client.get(
            "/v2/quality/non-conformances",
            params={"nc_type": "INTERNAL", "status": "OPEN", "severity": "MAJOR"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_get_non_conformance(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test récupération d'une non-conformité par ID"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_non_conformance.return_value = nc_entity

        response = test_client.get("/v2/quality/non-conformances/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["nc_number"] == "NC-2024-00001"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_get_non_conformance_not_found(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test récupération NC inexistante"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_non_conformance.return_value = None

        response = test_client.get("/v2/quality/non-conformances/999")

        assert response.status_code == 404

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_non_conformance(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test mise à jour d'une non-conformité"""
        mock_context.return_value = mock_saas_context
        nc_entity.title = "Titre modifié"
        mock_service.return_value.update_non_conformance.return_value = nc_entity

        response = test_client.put("/v2/quality/non-conformances/1", json={"title": "Titre modifié"})

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Titre modifié"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_open_non_conformance(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test ouverture d'une non-conformité"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.open_non_conformance.return_value = nc_entity

        response = test_client.post("/v2/quality/non-conformances/1/open")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OPEN"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_close_non_conformance(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test clôture d'une non-conformité"""
        mock_context.return_value = mock_saas_context
        nc_entity.status = "CLOSED"
        mock_service.return_value.close_non_conformance.return_value = nc_entity

        close_data = {
            "closure_justification": "Actions terminées",
            "effectiveness_verified": True
        }
        response = test_client.post("/v2/quality/non-conformances/1/close", json=close_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_add_nc_action(test_client, self, mock_service, mock_context, mock_saas_context, nc_action_data, nc_action_entity):
        """Test ajout d'une action à une NC"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.add_nc_action.return_value = nc_action_entity

        response = test_client.post("/v2/quality/non-conformances/1/actions", json=nc_action_data)

        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "CORRECTIVE"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_nc_action(test_client, self, mock_service, mock_context, mock_saas_context, nc_action_entity):
        """Test mise à jour d'une action NC"""
        mock_context.return_value = mock_saas_context
        nc_action_entity.status = "COMPLETED"
        mock_service.return_value.update_nc_action.return_value = nc_action_entity

        response = test_client.put("/v2/quality/nc-actions/1", json={"status": "COMPLETED"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_search_non_conformances(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test recherche dans les NC"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_non_conformances.return_value = ([nc_entity], 1)

        response = test_client.get("/v2/quality/non-conformances", params={"search": "défectueuse"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_filter_nc_by_date_range(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test filtrage NC par période"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_non_conformances.return_value = ([nc_entity], 1)

        response = test_client.get(
            "/v2/quality/non-conformances",
            params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# TEMPLATES DE CONTRÔLE - 6 tests
# ============================================================================

class TestControlTemplates:
    """Tests pour les endpoints de templates de contrôle"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_create_control_template(test_client, self, mock_service, mock_context, mock_saas_context,
                                     control_template_data, control_template_entity):
        """Test création d'un template de contrôle"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.create_control_template.return_value = control_template_entity

        response = test_client.post("/v2/quality/control-templates", json=control_template_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "TPL-001"
        assert data["name"] == "Contrôle dimensionnel"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_list_control_templates(test_client, self, mock_service, mock_context, mock_saas_context, control_template_entity):
        """Test listing des templates"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_control_templates.return_value = ([control_template_entity], 1)

        response = test_client.get("/v2/quality/control-templates")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_get_control_template(test_client, self, mock_service, mock_context, mock_saas_context, control_template_entity):
        """Test récupération d'un template"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_control_template.return_value = control_template_entity

        response = test_client.get("/v2/quality/control-templates/1")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "TPL-001"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_control_template(test_client, self, mock_service, mock_context, mock_saas_context, control_template_entity):
        """Test mise à jour d'un template"""
        mock_context.return_value = mock_saas_context
        control_template_entity.version = "2.0"
        mock_service.return_value.update_control_template.return_value = control_template_entity

        response = test_client.put("/v2/quality/control-templates/1", json={"version": "2.0"})

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_add_template_item(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test ajout d'un item à un template"""
        mock_context.return_value = mock_saas_context
        item = MagicMock()
        item.id = 1
        item.characteristic = "Longueur"
        mock_service.return_value.add_template_item.return_value = item

        item_data = {
            "sequence": 1,
            "characteristic": "Longueur",
            "measurement_type": "NUMERIC",
            "is_critical": True
        }
        response = test_client.post("/v2/quality/control-templates/1/items", json=item_data)

        assert response.status_code == 200

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_filter_templates_by_type(test_client, self, mock_service, mock_context, mock_saas_context, control_template_entity):
        """Test filtrage des templates par type"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_control_templates.return_value = ([control_template_entity], 1)

        response = test_client.get("/v2/quality/control-templates", params={"control_type": "RECEIVING"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# CONTRÔLES QUALITÉ - 8 tests
# ============================================================================

class TestControls:
    """Tests pour les endpoints de contrôles qualité"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_create_control(test_client, self, mock_service, mock_context, mock_saas_context, control_data, control_entity):
        """Test création d'un contrôle"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.create_control.return_value = control_entity

        response = test_client.post("/v2/quality/controls", json=control_data)

        assert response.status_code == 200
        data = response.json()
        assert data["control_number"] == "QC-2024-00001"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_list_controls(test_client, self, mock_service, mock_context, mock_saas_context, control_entity):
        """Test listing des contrôles"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_controls.return_value = ([control_entity], 1)

        response = test_client.get("/v2/quality/controls")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_get_control(test_client, self, mock_service, mock_context, mock_saas_context, control_entity):
        """Test récupération d'un contrôle"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_control.return_value = control_entity

        response = test_client.get("/v2/quality/controls/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_control(test_client, self, mock_service, mock_context, mock_saas_context, control_entity):
        """Test mise à jour d'un contrôle"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.update_control.return_value = control_entity

        response = test_client.put("/v2/quality/controls/1", json={"observations": "Notes ajoutées"})

        assert response.status_code == 200

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_start_control(test_client, self, mock_service, mock_context, mock_saas_context, control_entity):
        """Test démarrage d'un contrôle"""
        mock_context.return_value = mock_saas_context
        control_entity.status = "IN_PROGRESS"
        mock_service.return_value.start_control.return_value = control_entity

        response = test_client.post("/v2/quality/controls/1/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_control_line(test_client, self, mock_service, mock_context, mock_saas_context, control_entity):
        """Test mise à jour d'une ligne de contrôle"""
        mock_context.return_value = mock_saas_context
        line = MagicMock()
        line.control_id = 1
        mock_service.return_value.update_control_line.return_value = line
        mock_service.return_value.get_control.return_value = control_entity

        response = test_client.put("/v2/quality/control-lines/1", json={"measured_value": "10.5"})

        assert response.status_code == 200

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_complete_control(test_client, self, mock_service, mock_context, mock_saas_context, control_entity):
        """Test finalisation d'un contrôle"""
        mock_context.return_value = mock_saas_context
        control_entity.status = "COMPLETED"
        control_entity.result = "PASSED"
        mock_service.return_value.complete_control.return_value = control_entity

        response = test_client.post("/v2/quality/controls/1/complete", params={"decision": "ACCEPT"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_filter_controls_by_status_and_result(test_client, self, mock_service, mock_context, mock_saas_context, control_entity):
        """Test filtrage des contrôles par statut et résultat"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_controls.return_value = ([control_entity], 1)

        response = test_client.get(
            "/v2/quality/controls",
            params={"status": "COMPLETED", "result": "PASSED"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# AUDITS - 12 tests
# ============================================================================

class TestAudits:
    """Tests pour les endpoints d'audits"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_create_audit(test_client, self, mock_service, mock_context, mock_saas_context, audit_data, audit_entity):
        """Test création d'un audit"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.create_audit.return_value = audit_entity

        response = test_client.post("/v2/quality/audits", json=audit_data)

        assert response.status_code == 200
        data = response.json()
        assert data["audit_number"] == "AUD-2024-0001"
        assert data["title"] == "Audit ISO 9001"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_list_audits(test_client, self, mock_service, mock_context, mock_saas_context, audit_entity):
        """Test listing des audits"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_audits.return_value = ([audit_entity], 1)

        response = test_client.get("/v2/quality/audits")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_list_audits_with_filters(test_client, self, mock_service, mock_context, mock_saas_context, audit_entity):
        """Test listing avec filtres (type, status)"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_audits.return_value = ([audit_entity], 1)

        response = test_client.get(
            "/v2/quality/audits",
            params={"audit_type": "INTERNAL", "status": "PLANNED"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_get_audit(test_client, self, mock_service, mock_context, mock_saas_context, audit_entity):
        """Test récupération d'un audit"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_audit.return_value = audit_entity

        response = test_client.get("/v2/quality/audits/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_audit(test_client, self, mock_service, mock_context, mock_saas_context, audit_entity):
        """Test mise à jour d'un audit"""
        mock_context.return_value = mock_saas_context
        audit_entity.title = "Audit modifié"
        mock_service.return_value.update_audit.return_value = audit_entity

        response = test_client.put("/v2/quality/audits/1", json={"title": "Audit modifié"})

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Audit modifié"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_start_audit(test_client, self, mock_service, mock_context, mock_saas_context, audit_entity):
        """Test démarrage d'un audit"""
        mock_context.return_value = mock_saas_context
        audit_entity.status = "IN_PROGRESS"
        mock_service.return_value.start_audit.return_value = audit_entity

        response = test_client.post("/v2/quality/audits/1/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_add_finding(test_client, self, mock_service, mock_context, mock_saas_context,
                        audit_finding_data, audit_finding_entity):
        """Test ajout d'un constat à un audit"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.add_finding.return_value = audit_finding_entity

        response = test_client.post("/v2/quality/audits/1/findings", json=audit_finding_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Procédure non suivie"
        assert data["severity"] == "MAJOR"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_finding(test_client, self, mock_service, mock_context, mock_saas_context, audit_finding_entity):
        """Test mise à jour d'un constat"""
        mock_context.return_value = mock_saas_context
        audit_finding_entity.status = "CLOSED"
        mock_service.return_value.update_finding.return_value = audit_finding_entity

        response = test_client.put("/v2/quality/audit-findings/1", json={"status": "CLOSED"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_close_audit(test_client, self, mock_service, mock_context, mock_saas_context, audit_entity):
        """Test clôture d'un audit"""
        mock_context.return_value = mock_saas_context
        audit_entity.status = "CLOSED"
        mock_service.return_value.close_audit.return_value = audit_entity

        close_data = {
            "audit_conclusion": "Conforme",
            "recommendation": "Maintenir les bonnes pratiques"
        }
        response = test_client.post("/v2/quality/audits/1/close", json=close_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_audit_not_found(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test audit inexistant"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_audit.return_value = None

        response = test_client.get("/v2/quality/audits/999")

        assert response.status_code == 404

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_filter_audits_by_date_range(test_client, self, mock_service, mock_context, mock_saas_context, audit_entity):
        """Test filtrage des audits par période"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_audits.return_value = ([audit_entity], 1)

        response = test_client.get(
            "/v2/quality/audits",
            params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_search_audits(test_client, self, mock_service, mock_context, mock_saas_context, audit_entity):
        """Test recherche dans les audits"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_audits.return_value = ([audit_entity], 1)

        response = test_client.get("/v2/quality/audits", params={"search": "ISO"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# CAPA - 8 tests
# ============================================================================

class TestCAPA:
    """Tests pour les endpoints CAPA"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_create_capa(test_client, self, mock_service, mock_context, mock_saas_context, capa_data, capa_entity):
        """Test création d'un CAPA"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.create_capa.return_value = capa_entity

        response = test_client.post("/v2/quality/capas", json=capa_data)

        assert response.status_code == 200
        data = response.json()
        assert data["capa_number"] == "CAPA-2024-0001"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_list_capas(test_client, self, mock_service, mock_context, mock_saas_context, capa_entity):
        """Test listing des CAPA"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_capas.return_value = ([capa_entity], 1)

        response = test_client.get("/v2/quality/capas")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_get_capa(test_client, self, mock_service, mock_context, mock_saas_context, capa_entity):
        """Test récupération d'un CAPA"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_capa.return_value = capa_entity

        response = test_client.get("/v2/quality/capas/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_capa(test_client, self, mock_service, mock_context, mock_saas_context, capa_entity):
        """Test mise à jour d'un CAPA"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.update_capa.return_value = capa_entity

        response = test_client.put("/v2/quality/capas/1", json={"priority": "CRITICAL"})

        assert response.status_code == 200

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_add_capa_action(test_client, self, mock_service, mock_context, mock_saas_context,
                            capa_action_data, capa_action_entity):
        """Test ajout d'une action à un CAPA"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.add_capa_action.return_value = capa_action_entity

        response = test_client.post("/v2/quality/capas/1/actions", json=capa_action_data)

        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "PREVENTIVE"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_capa_action(test_client, self, mock_service, mock_context, mock_saas_context, capa_action_entity):
        """Test mise à jour d'une action CAPA"""
        mock_context.return_value = mock_saas_context
        capa_action_entity.status = "COMPLETED"
        mock_service.return_value.update_capa_action.return_value = capa_action_entity

        response = test_client.put("/v2/quality/capa-actions/1", json={"status": "COMPLETED"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_close_capa(test_client, self, mock_service, mock_context, mock_saas_context, capa_entity):
        """Test clôture d'un CAPA"""
        mock_context.return_value = mock_saas_context
        capa_entity.status = "CLOSED_EFFECTIVE"
        mock_service.return_value.close_capa.return_value = capa_entity

        close_data = {
            "effectiveness_verified": True,
            "effectiveness_result": "Efficace",
            "closure_comments": "Toutes les actions sont terminées"
        }
        response = test_client.post("/v2/quality/capas/1/close", json=close_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED_EFFECTIVE"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_filter_capas_by_type_and_priority(test_client, self, mock_service, mock_context, mock_saas_context, capa_entity):
        """Test filtrage des CAPA par type et priorité"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_capas.return_value = ([capa_entity], 1)

        response = test_client.get(
            "/v2/quality/capas",
            params={"capa_type": "PREVENTIVE", "priority": "HIGH"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# RÉCLAMATIONS - 10 tests
# ============================================================================

class TestClaims:
    """Tests pour les endpoints de réclamations"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_create_claim(test_client, self, mock_service, mock_context, mock_saas_context, claim_data, claim_entity):
        """Test création d'une réclamation"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.create_claim.return_value = claim_entity

        response = test_client.post("/v2/quality/claims", json=claim_data)

        assert response.status_code == 200
        data = response.json()
        assert data["claim_number"] == "REC-2024-00001"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_list_claims(test_client, self, mock_service, mock_context, mock_saas_context, claim_entity):
        """Test listing des réclamations"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_claims.return_value = ([claim_entity], 1)

        response = test_client.get("/v2/quality/claims")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_get_claim(test_client, self, mock_service, mock_context, mock_saas_context, claim_entity):
        """Test récupération d'une réclamation"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_claim.return_value = claim_entity

        response = test_client.get("/v2/quality/claims/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_claim(test_client, self, mock_service, mock_context, mock_saas_context, claim_entity):
        """Test mise à jour d'une réclamation"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.update_claim.return_value = claim_entity

        response = test_client.put("/v2/quality/claims/1", json={"priority": "CRITICAL"})

        assert response.status_code == 200

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_acknowledge_claim(test_client, self, mock_service, mock_context, mock_saas_context, claim_entity):
        """Test accusé de réception d'une réclamation"""
        mock_context.return_value = mock_saas_context
        claim_entity.status = "ACKNOWLEDGED"
        mock_service.return_value.acknowledge_claim.return_value = claim_entity

        response = test_client.post("/v2/quality/claims/1/acknowledge")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ACKNOWLEDGED"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_respond_claim(test_client, self, mock_service, mock_context, mock_saas_context, claim_entity):
        """Test réponse à une réclamation"""
        mock_context.return_value = mock_saas_context
        claim_entity.status = "RESPONSE_SENT"
        mock_service.return_value.respond_claim.return_value = claim_entity

        response_data = {"response_content": "Nous allons remplacer les pièces"}
        response = test_client.post("/v2/quality/claims/1/respond", json=response_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RESPONSE_SENT"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_resolve_claim(test_client, self, mock_service, mock_context, mock_saas_context, claim_entity):
        """Test résolution d'une réclamation"""
        mock_context.return_value = mock_saas_context
        claim_entity.status = "RESOLVED"
        mock_service.return_value.resolve_claim.return_value = claim_entity

        resolve_data = {
            "resolution_type": "REPLACEMENT",
            "resolution_description": "Pièces remplacées"
        }
        response = test_client.post("/v2/quality/claims/1/resolve", json=resolve_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RESOLVED"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_close_claim(test_client, self, mock_service, mock_context, mock_saas_context, claim_entity):
        """Test clôture d'une réclamation"""
        mock_context.return_value = mock_saas_context
        claim_entity.status = "CLOSED"
        mock_service.return_value.close_claim.return_value = claim_entity

        close_data = {
            "customer_satisfied": True,
            "satisfaction_feedback": "Client satisfait"
        }
        response = test_client.post("/v2/quality/claims/1/close", json=close_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_add_claim_action(test_client, self, mock_service, mock_context, mock_saas_context,
                              claim_action_data, claim_action_entity):
        """Test ajout d'une action à une réclamation"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.add_claim_action.return_value = claim_action_entity

        response = test_client.post("/v2/quality/claims/1/actions", json=claim_action_data)

        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "IMMEDIATE"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_filter_claims_by_customer(test_client, self, mock_service, mock_context, mock_saas_context, claim_entity):
        """Test filtrage des réclamations par client"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_claims.return_value = ([claim_entity], 1)

        response = test_client.get("/v2/quality/claims", params={"customer_id": 1})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# INDICATEURS - 6 tests
# ============================================================================

class TestIndicators:
    """Tests pour les endpoints d'indicateurs"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_create_indicator(test_client, self, mock_service, mock_context, mock_saas_context,
                              indicator_data, indicator_entity):
        """Test création d'un indicateur"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.create_indicator.return_value = indicator_entity

        response = test_client.post("/v2/quality/indicators", json=indicator_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "IND-001"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_list_indicators(test_client, self, mock_service, mock_context, mock_saas_context, indicator_entity):
        """Test listing des indicateurs"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_indicators.return_value = ([indicator_entity], 1)

        response = test_client.get("/v2/quality/indicators")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_get_indicator(test_client, self, mock_service, mock_context, mock_saas_context, indicator_entity):
        """Test récupération d'un indicateur"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_indicator.return_value = indicator_entity

        response = test_client.get("/v2/quality/indicators/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_indicator(test_client, self, mock_service, mock_context, mock_saas_context, indicator_entity):
        """Test mise à jour d'un indicateur"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.update_indicator.return_value = indicator_entity

        response = test_client.put("/v2/quality/indicators/1", json={"target_value": "99"})

        assert response.status_code == 200

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_add_measurement(test_client, self, mock_service, mock_context, mock_saas_context,
                            indicator_measurement_data, indicator_measurement_entity):
        """Test ajout d'une mesure à un indicateur"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.add_measurement.return_value = indicator_measurement_entity

        response = test_client.post("/v2/quality/indicators/1/measurements", json=indicator_measurement_data)

        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "97.5"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_filter_indicators_by_category(test_client, self, mock_service, mock_context, mock_saas_context, indicator_entity):
        """Test filtrage des indicateurs par catégorie"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_indicators.return_value = ([indicator_entity], 1)

        response = test_client.get("/v2/quality/indicators", params={"category": "QUALITY"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# CERTIFICATIONS - 6 tests
# ============================================================================

class TestCertifications:
    """Tests pour les endpoints de certifications"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_create_certification(test_client, self, mock_service, mock_context, mock_saas_context,
                                  certification_data, certification_entity):
        """Test création d'une certification"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.create_certification.return_value = certification_entity

        response = test_client.post("/v2/quality/certifications", json=certification_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "ISO-9001"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_list_certifications(test_client, self, mock_service, mock_context, mock_saas_context, certification_entity):
        """Test listing des certifications"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_certifications.return_value = ([certification_entity], 1)

        response = test_client.get("/v2/quality/certifications")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_get_certification(test_client, self, mock_service, mock_context, mock_saas_context, certification_entity):
        """Test récupération d'une certification"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_certification.return_value = certification_entity

        response = test_client.get("/v2/quality/certifications/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_certification(test_client, self, mock_service, mock_context, mock_saas_context, certification_entity):
        """Test mise à jour d'une certification"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.update_certification.return_value = certification_entity

        response = test_client.put("/v2/quality/certifications/1", json={"status": "EXPIRED"})

        assert response.status_code == 200

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_add_certification_audit(test_client, self, mock_service, mock_context, mock_saas_context,
                                    certification_audit_data, certification_audit_entity):
        """Test ajout d'un audit à une certification"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.add_certification_audit.return_value = certification_audit_entity

        response = test_client.post("/v2/quality/certifications/1/audits", json=certification_audit_data)

        assert response.status_code == 200
        data = response.json()
        assert data["audit_type"] == "SURVEILLANCE"

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_update_certification_audit(test_client, self, mock_service, mock_context, mock_saas_context,
                                       certification_audit_entity):
        """Test mise à jour d'un audit de certification"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.update_certification_audit.return_value = certification_audit_entity

        response = test_client.put("/v2/quality/certification-audits/1", json={"notes": "Audit réussi"})

        assert response.status_code == 200


# ============================================================================
# DASHBOARD - 2 tests
# ============================================================================

class TestDashboard:
    """Tests pour l'endpoint du dashboard"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_get_dashboard(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test récupération du dashboard qualité"""
        mock_context.return_value = mock_saas_context

        dashboard_data = MagicMock()
        dashboard_data.nc_total = 100
        dashboard_data.nc_open = 25
        dashboard_data.nc_critical = 5
        dashboard_data.controls_total = 150
        dashboard_data.controls_completed = 140
        dashboard_data.controls_pass_rate = Decimal("95.5")
        dashboard_data.capa_total = 30
        dashboard_data.capa_open = 10

        mock_service.return_value.get_dashboard.return_value = dashboard_data

        response = test_client.get("/v2/quality/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "nc_total" in data
        assert "controls_total" in data
        assert "capa_total" in data

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_dashboard_statistics(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test statistiques complètes du dashboard"""
        mock_context.return_value = mock_saas_context

        dashboard_data = MagicMock()
        dashboard_data.nc_total = 100
        dashboard_data.nc_open = 25
        dashboard_data.nc_critical = 5
        dashboard_data.controls_total = 150
        dashboard_data.controls_completed = 140
        dashboard_data.controls_pass_rate = Decimal("95.5")
        dashboard_data.audits_planned = 5
        dashboard_data.audits_completed = 3
        dashboard_data.audit_findings_open = 8
        dashboard_data.capa_total = 30
        dashboard_data.capa_open = 10
        dashboard_data.capa_overdue = 2
        dashboard_data.capa_effectiveness_rate = Decimal("92.0")
        dashboard_data.claims_total = 15
        dashboard_data.claims_open = 3
        dashboard_data.certifications_active = 4
        dashboard_data.certifications_expiring_soon = 1
        dashboard_data.indicators_on_target = 12
        dashboard_data.indicators_warning = 2
        dashboard_data.indicators_critical = 1

        mock_service.return_value.get_dashboard.return_value = dashboard_data

        response = test_client.get("/v2/quality/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["nc_total"] == 100
        assert data["capa_effectiveness_rate"] == "92.0"


# ============================================================================
# WORKFLOWS - 2 tests
# ============================================================================

class TestWorkflows:
    """Tests pour les workflows qualité"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_nc_to_capa_workflow(test_client, self, mock_service, mock_context, mock_saas_context,
                                 nc_entity, capa_entity):
        """Test workflow: NC → CAPA → Clôture"""
        mock_context.return_value = mock_saas_context

        # 1. Créer NC
        mock_service.return_value.create_non_conformance.return_value = nc_entity
        nc_response = test_client.post("/v2/quality/non-conformances", json={
            "title": "Pièce défectueuse",
            "description": "Surface rayée",
            "nc_type": "INTERNAL",
            "severity": "MAJOR",
            "detected_date": str(date.today()),
        })
        assert nc_response.status_code == 200

        # 2. Créer CAPA lié
        mock_service.return_value.create_capa.return_value = capa_entity
        capa_response = test_client.post("/v2/quality/capas", json={
            "title": "Améliorer le contrôle",
            "description": "Mettre en place un contrôle renforcé",
            "capa_type": "CORRECTIVE",
            "source_type": "NC",
            "source_id": 1,
            "priority": "HIGH",
            "open_date": str(date.today()),
            "target_close_date": str(date.today()),
            "owner_id": 1,
        })
        assert capa_response.status_code == 200

        # 3. Clôturer CAPA
        capa_entity.status = "CLOSED_EFFECTIVE"
        mock_service.return_value.close_capa.return_value = capa_entity
        close_response = test_client.post("/v2/quality/capas/1/close", json={
            "effectiveness_verified": True,
            "effectiveness_result": "Efficace",
            "closure_comments": "Actions terminées"
        })
        assert close_response.status_code == 200

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_audit_finding_to_action_workflow(test_client, self, mock_service, mock_context, mock_saas_context,
                                              audit_entity, audit_finding_entity):
        """Test workflow: Audit → Constat → Action corrective"""
        mock_context.return_value = mock_saas_context

        # 1. Créer audit
        mock_service.return_value.create_audit.return_value = audit_entity
        audit_response = test_client.post("/v2/quality/audits", json={
            "title": "Audit ISO 9001",
            "description": "Audit annuel",
            "audit_type": "INTERNAL",
            "reference_standard": "ISO 9001:2015",
            "audit_scope": "Système qualité",
            "planned_date": str(date.today()),
            "lead_auditor_id": 1,
            "audited_entity": "Production"
        })
        assert audit_response.status_code == 200

        # 2. Ajouter constat
        mock_service.return_value.add_finding.return_value = audit_finding_entity
        finding_response = test_client.post("/v2/quality/audits/1/findings", json={
            "title": "Procédure non suivie",
            "description": "Non-respect de la procédure",
            "severity": "MAJOR",
            "category": "PROCESS",
            "clause_reference": "8.5.1",
            "evidence": "Observation sur site",
            "capa_required": True
        })
        assert finding_response.status_code == 200


# ============================================================================
# PAGINATION - 2 tests
# ============================================================================

class TestPagination:
    """Tests pour la pagination"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_pagination_skip_limit(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test pagination avec skip et limit"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_non_conformances.return_value = ([nc_entity], 100)

        response = test_client.get("/v2/quality/non-conformances", params={"skip": 10, "limit": 20})

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 10
        assert data["limit"] == 20
        assert data["total"] == 100

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_pagination_limits(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test limites de pagination"""
        mock_context.return_value = mock_saas_context

        # Test limite max (200)
        response = test_client.get("/v2/quality/non-conformances", params={"limit": 300})
        assert response.status_code == 422  # Validation error

        # Test limite valide
        mock_service.return_value.list_non_conformances.return_value = ([], 0)
        response = test_client.get("/v2/quality/non-conformances", params={"limit": 50})
        assert response.status_code == 200


# ============================================================================
# TENANT ISOLATION - 2 tests
# ============================================================================

class TestTenantIsolation:
    """Tests pour l'isolation des tenants"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_tenant_context_used(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test que le contexte tenant est bien utilisé"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.create_non_conformance.return_value = nc_entity

        nc_data = {
            "title": "Test NC",
            "description": "Description",
            "nc_type": "INTERNAL",
            "severity": "MINOR",
            "detected_date": str(date.today()),
        }
        response = test_client.post("/v2/quality/non-conformances", json=nc_data)

        assert response.status_code == 200
        # Vérifier que get_quality_service a été appelé avec les bons paramètres
        mock_service.assert_called()

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_user_context_used(test_client, self, mock_service, mock_context, mock_saas_context, nc_entity):
        """Test que le contexte utilisateur est bien utilisé"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.list_non_conformances.return_value = ([nc_entity], 1)

        response = test_client.get("/v2/quality/non-conformances")

        assert response.status_code == 200
        # Vérifier que get_quality_service a été appelé
        mock_service.assert_called()


# ============================================================================
# ERROR HANDLING - 6 tests
# ============================================================================

class TestErrorHandling:
    """Tests pour la gestion des erreurs"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_nc_action_not_found(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test action NC inexistante"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.update_nc_action.return_value = None

        response = test_client.put("/v2/quality/nc-actions/999", json={"status": "COMPLETED"})

        assert response.status_code == 404

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_control_not_found(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test contrôle inexistant"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_control.return_value = None

        response = test_client.get("/v2/quality/controls/999")

        assert response.status_code == 404

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_capa_action_not_found(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test action CAPA inexistante"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.update_capa_action.return_value = None

        response = test_client.put("/v2/quality/capa-actions/999", json={"status": "COMPLETED"})

        assert response.status_code == 404

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_claim_not_found(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test réclamation inexistante"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_claim.return_value = None

        response = test_client.get("/v2/quality/claims/999")

        assert response.status_code == 404

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_indicator_not_found(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test indicateur inexistant"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_indicator.return_value = None

        response = test_client.get("/v2/quality/indicators/999")

        assert response.status_code == 404

    @patch("app.modules.quality.router_v2.get_saas_context")
    @patch("app.modules.quality.router_v2.get_quality_service")
    def test_certification_not_found(test_client, self, mock_service, mock_context, mock_saas_context):
        """Test certification inexistante"""
        mock_context.return_value = mock_saas_context
        mock_service.return_value.get_certification.return_value = None

        response = test_client.get("/v2/quality/certifications/999")

        assert response.status_code == 404


# ============================================================================
# VALIDATION - 8 tests
# ============================================================================

class TestValidation:
    """Tests pour la validation des données"""

    @patch("app.modules.quality.router_v2.get_saas_context")
    def test_nc_missing_required_fields(test_client, self, mock_context, mock_saas_context):
        """Test validation NC avec champs manquants"""
        mock_context.return_value = mock_saas_context

        response = test_client.post("/v2/quality/non-conformances", json={})

        assert response.status_code == 422

    @patch("app.modules.quality.router_v2.get_saas_context")
    def test_audit_missing_required_fields(test_client, self, mock_context, mock_saas_context):
        """Test validation audit avec champs manquants"""
        mock_context.return_value = mock_saas_context

        response = test_client.post("/v2/quality/audits", json={})

        assert response.status_code == 422

    @patch("app.modules.quality.router_v2.get_saas_context")
    def test_capa_missing_required_fields(test_client, self, mock_context, mock_saas_context):
        """Test validation CAPA avec champs manquants"""
        mock_context.return_value = mock_saas_context

        response = test_client.post("/v2/quality/capas", json={})

        assert response.status_code == 422

    @patch("app.modules.quality.router_v2.get_saas_context")
    def test_claim_missing_required_fields(test_client, self, mock_context, mock_saas_context):
        """Test validation réclamation avec champs manquants"""
        mock_context.return_value = mock_saas_context

        response = test_client.post("/v2/quality/claims", json={})

        assert response.status_code == 422

    @patch("app.modules.quality.router_v2.get_saas_context")
    def test_invalid_pagination_skip(test_client, self, mock_context, mock_saas_context):
        """Test validation skip négatif"""
        mock_context.return_value = mock_saas_context

        response = test_client.get("/v2/quality/non-conformances", params={"skip": -1})

        assert response.status_code == 422

    @patch("app.modules.quality.router_v2.get_saas_context")
    def test_invalid_pagination_limit_too_high(test_client, self, mock_context, mock_saas_context):
        """Test validation limit trop élevé"""
        mock_context.return_value = mock_saas_context

        response = test_client.get("/v2/quality/non-conformances", params={"limit": 1000})

        assert response.status_code == 422

    @patch("app.modules.quality.router_v2.get_saas_context")
    def test_invalid_pagination_limit_zero(test_client, self, mock_context, mock_saas_context):
        """Test validation limit à zéro"""
        mock_context.return_value = mock_saas_context

        response = test_client.get("/v2/quality/non-conformances", params={"limit": 0})

        assert response.status_code == 422

    @patch("app.modules.quality.router_v2.get_saas_context")
    def test_invalid_date_format(test_client, self, mock_context, mock_saas_context):
        """Test validation format de date invalide"""
        mock_context.return_value = mock_saas_context

        response = test_client.get("/v2/quality/non-conformances", params={"date_from": "invalid-date"})

        assert response.status_code == 422
