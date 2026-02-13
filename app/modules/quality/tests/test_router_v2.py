"""
Tests pour le router Quality v2 - CORE SaaS
============================================

Couvre tous les endpoints du module quality avec SaaSContext.
90 tests pour valider la migration CORE SaaS v2.

Les mocks sont injectés via le fixture test_client qui configure:
- dependency_overrides pour get_saas_context
- patch de get_quality_service
- Headers d'authentification automatiques
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


# ============================================================================
# NON-CONFORMITÉS - 12 tests
# ============================================================================

class TestNonConformances:
    """Tests pour les endpoints de non-conformités"""

    def test_create_non_conformance(self, test_client, nc_data, nc_entity):
        """Test création d'une non-conformité"""
        test_client.mock_service.create_non_conformance.return_value = nc_entity

        response = test_client.post("/v2/quality/non-conformances", json=nc_data)

        assert response.status_code == 200
        data = response.json()
        assert data["nc_number"] == "NC-2024-00001"
        assert data["title"] == "Pièce défectueuse"
        assert data["severity"] == "MAJOR"

    def test_list_non_conformances(self, test_client, nc_entity):
        """Test listing des non-conformités"""
        test_client.mock_service.list_non_conformances.return_value = ([nc_entity], 1)

        response = test_client.get("/v2/quality/non-conformances")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["nc_number"] == "NC-2024-00001"

    def test_list_non_conformances_with_filters(self, test_client, nc_entity):
        """Test listing avec filtres (type, status, severity)"""
        test_client.mock_service.list_non_conformances.return_value = ([nc_entity], 1)

        response = test_client.get(
            "/v2/quality/non-conformances",
            params={"nc_type": "INTERNAL", "status": "OPEN", "severity": "MAJOR"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_non_conformance(self, test_client, nc_entity):
        """Test récupération d'une non-conformité par ID"""
        test_client.mock_service.get_non_conformance.return_value = nc_entity

        response = test_client.get("/v2/quality/non-conformances/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["nc_number"] == "NC-2024-00001"

    def test_get_non_conformance_not_found(self, test_client):
        """Test récupération NC inexistante"""
        test_client.mock_service.get_non_conformance.return_value = None

        response = test_client.get("/v2/quality/non-conformances/999")

        assert response.status_code == 404

    def test_update_non_conformance(self, test_client, nc_entity):
        """Test mise à jour d'une non-conformité"""
        updated_entity = nc_entity.with_updates(title="Titre modifié")
        test_client.mock_service.update_non_conformance.return_value = updated_entity

        response = test_client.put("/v2/quality/non-conformances/1", json={"title": "Titre modifié"})

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Titre modifié"

    def test_open_non_conformance(self, test_client, nc_entity):
        """Test ouverture d'une non-conformité"""
        test_client.mock_service.open_non_conformance.return_value = nc_entity

        response = test_client.post("/v2/quality/non-conformances/1/open")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OPEN"

    def test_close_non_conformance(self, test_client, nc_entity):
        """Test clôture d'une non-conformité"""
        closed_entity = nc_entity.with_updates(status="CLOSED")
        test_client.mock_service.close_non_conformance.return_value = closed_entity

        close_data = {
            "closure_justification": "Actions terminées",
            "effectiveness_verified": True
        }
        response = test_client.post("/v2/quality/non-conformances/1/close", json=close_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"

    def test_add_nc_action(self, test_client, nc_action_data, nc_action_entity):
        """Test ajout d'une action à une NC"""
        test_client.mock_service.add_nc_action.return_value = nc_action_entity

        response = test_client.post("/v2/quality/non-conformances/1/actions", json=nc_action_data)

        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "CORRECTIVE"

    def test_update_nc_action(self, test_client, nc_action_entity):
        """Test mise à jour d'une action NC"""
        updated_action = nc_action_entity.with_updates(status="COMPLETED")
        test_client.mock_service.update_nc_action.return_value = updated_action

        response = test_client.put("/v2/quality/nc-actions/1", json={"status": "COMPLETED"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"

    def test_search_non_conformances(self, test_client, nc_entity):
        """Test recherche dans les NC"""
        test_client.mock_service.list_non_conformances.return_value = ([nc_entity], 1)

        response = test_client.get("/v2/quality/non-conformances", params={"search": "défectueuse"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_filter_nc_by_date_range(self, test_client, nc_entity):
        """Test filtrage NC par période"""
        test_client.mock_service.list_non_conformances.return_value = ([nc_entity], 1)

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

    def test_create_control_template(self, test_client, control_template_data, control_template_entity):
        """Test création d'un template de contrôle"""
        test_client.mock_service.create_control_template.return_value = control_template_entity

        response = test_client.post("/v2/quality/control-templates", json=control_template_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "TPL-001"
        assert data["name"] == "Contrôle dimensionnel"

    def test_list_control_templates(self, test_client, control_template_entity):
        """Test listing des templates"""
        test_client.mock_service.list_control_templates.return_value = ([control_template_entity], 1)

        response = test_client.get("/v2/quality/control-templates")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_control_template(self, test_client, control_template_entity):
        """Test récupération d'un template"""
        test_client.mock_service.get_control_template.return_value = control_template_entity

        response = test_client.get("/v2/quality/control-templates/1")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "TPL-001"

    def test_update_control_template(self, test_client, control_template_entity):
        """Test mise à jour d'un template"""
        updated_template = control_template_entity.with_updates(version="2.0")
        test_client.mock_service.update_control_template.return_value = updated_template

        response = test_client.put("/v2/quality/control-templates/1", json={"version": "2.0"})

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0"

    def test_add_template_item(self, test_client, control_template_item_entity):
        """Test ajout d'un item à un template"""
        test_client.mock_service.add_template_item.return_value = control_template_item_entity

        item_data = {
            "sequence": 1,
            "characteristic": "Longueur",
            "measurement_type": "NUMERIC",
            "is_critical": True
        }
        response = test_client.post("/v2/quality/control-templates/1/items", json=item_data)

        assert response.status_code == 200

    def test_filter_templates_by_type(self, test_client, control_template_entity):
        """Test filtrage des templates par type"""
        test_client.mock_service.list_control_templates.return_value = ([control_template_entity], 1)

        response = test_client.get("/v2/quality/control-templates", params={"control_type": "INCOMING"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# CONTRÔLES QUALITÉ - 8 tests
# ============================================================================

class TestControls:
    """Tests pour les endpoints de contrôles qualité"""

    def test_create_control(self, test_client, control_data, control_entity):
        """Test création d'un contrôle"""
        test_client.mock_service.create_control.return_value = control_entity

        response = test_client.post("/v2/quality/controls", json=control_data)

        assert response.status_code == 200
        data = response.json()
        assert data["control_number"] == "QC-2024-00001"

    def test_list_controls(self, test_client, control_entity):
        """Test listing des contrôles"""
        test_client.mock_service.list_controls.return_value = ([control_entity], 1)

        response = test_client.get("/v2/quality/controls")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_control(self, test_client, control_entity):
        """Test récupération d'un contrôle"""
        test_client.mock_service.get_control.return_value = control_entity

        response = test_client.get("/v2/quality/controls/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_update_control(self, test_client, control_entity):
        """Test mise à jour d'un contrôle"""
        updated_control = control_entity.with_updates(observations="Notes ajoutées")
        test_client.mock_service.update_control.return_value = updated_control

        response = test_client.put("/v2/quality/controls/1", json={"observations": "Notes ajoutées"})

        assert response.status_code == 200

    def test_start_control(self, test_client, control_entity):
        """Test démarrage d'un contrôle"""
        started_control = control_entity.with_updates(status="IN_PROGRESS")
        test_client.mock_service.start_control.return_value = started_control

        response = test_client.post("/v2/quality/controls/1/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"

    def test_update_control_line(self, test_client, control_entity):
        """Test mise à jour d'une ligne de contrôle"""
        line = MagicMock()
        line.id = 1
        line.control_id = 1
        line.measured_value = Decimal("10.5")
        test_client.mock_service.update_control_line.return_value = line
        test_client.mock_service.get_control.return_value = control_entity

        response = test_client.put("/v2/quality/control-lines/1", json={"measured_value": "10.5"})

        assert response.status_code == 200

    def test_complete_control(self, test_client, control_entity):
        """Test finalisation d'un contrôle"""
        completed_control = control_entity.with_updates(status="COMPLETED", result="PASSED")
        test_client.mock_service.complete_control.return_value = completed_control

        response = test_client.post("/v2/quality/controls/1/complete", params={"decision": "ACCEPT"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"

    def test_filter_controls_by_status_and_result(self, test_client, control_entity):
        """Test filtrage des contrôles par statut et résultat"""
        test_client.mock_service.list_controls.return_value = ([control_entity], 1)

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

    def test_create_audit(self, test_client, audit_data, audit_entity):
        """Test création d'un audit"""
        test_client.mock_service.create_audit.return_value = audit_entity

        response = test_client.post("/v2/quality/audits", json=audit_data)

        assert response.status_code == 200
        data = response.json()
        assert data["audit_number"] == "AUD-2024-0001"
        assert data["title"] == "Audit ISO 9001"

    def test_list_audits(self, test_client, audit_entity):
        """Test listing des audits"""
        test_client.mock_service.list_audits.return_value = ([audit_entity], 1)

        response = test_client.get("/v2/quality/audits")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_list_audits_with_filters(self, test_client, audit_entity):
        """Test listing avec filtres (type, status)"""
        test_client.mock_service.list_audits.return_value = ([audit_entity], 1)

        response = test_client.get(
            "/v2/quality/audits",
            params={"audit_type": "INTERNAL", "status": "PLANNED"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_audit(self, test_client, audit_entity):
        """Test récupération d'un audit"""
        test_client.mock_service.get_audit.return_value = audit_entity

        response = test_client.get("/v2/quality/audits/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_update_audit(self, test_client, audit_entity):
        """Test mise à jour d'un audit"""
        updated_audit = audit_entity.with_updates(title="Audit modifié")
        test_client.mock_service.update_audit.return_value = updated_audit

        response = test_client.put("/v2/quality/audits/1", json={"title": "Audit modifié"})

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Audit modifié"

    def test_start_audit(self, test_client, audit_entity):
        """Test démarrage d'un audit"""
        started_audit = audit_entity.with_updates(status="IN_PROGRESS")
        test_client.mock_service.start_audit.return_value = started_audit

        response = test_client.post("/v2/quality/audits/1/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"

    def test_add_finding(self, test_client, audit_finding_data, audit_finding_entity):
        """Test ajout d'un constat à un audit"""
        test_client.mock_service.add_finding.return_value = audit_finding_entity

        response = test_client.post("/v2/quality/audits/1/findings", json=audit_finding_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Procédure non suivie"
        assert data["severity"] == "MAJOR"

    def test_update_finding(self, test_client, audit_finding_entity):
        """Test mise à jour d'un constat"""
        updated_finding = audit_finding_entity.with_updates(status="CLOSED")
        test_client.mock_service.update_finding.return_value = updated_finding

        response = test_client.put("/v2/quality/audit-findings/1", json={"status": "CLOSED"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"

    def test_close_audit(self, test_client, audit_entity):
        """Test clôture d'un audit"""
        closed_audit = audit_entity.with_updates(status="CLOSED")
        test_client.mock_service.close_audit.return_value = closed_audit

        close_data = {
            "audit_conclusion": "Audit conforme aux exigences de la norme",
            "recommendation": "Maintenir les bonnes pratiques"
        }
        response = test_client.post("/v2/quality/audits/1/close", json=close_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"

    def test_audit_not_found(self, test_client):
        """Test audit inexistant"""
        test_client.mock_service.get_audit.return_value = None

        response = test_client.get("/v2/quality/audits/999")

        assert response.status_code == 404

    def test_filter_audits_by_date_range(self, test_client, audit_entity):
        """Test filtrage des audits par période"""
        test_client.mock_service.list_audits.return_value = ([audit_entity], 1)

        response = test_client.get(
            "/v2/quality/audits",
            params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_search_audits(self, test_client, audit_entity):
        """Test recherche dans les audits"""
        test_client.mock_service.list_audits.return_value = ([audit_entity], 1)

        response = test_client.get("/v2/quality/audits", params={"search": "ISO"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# CAPA - 8 tests
# ============================================================================

class TestCAPA:
    """Tests pour les endpoints CAPA"""

    def test_create_capa(self, test_client, capa_data, capa_entity):
        """Test création d'un CAPA"""
        test_client.mock_service.create_capa.return_value = capa_entity

        response = test_client.post("/v2/quality/capas", json=capa_data)

        assert response.status_code == 200
        data = response.json()
        assert data["capa_number"] == "CAPA-2024-0001"

    def test_list_capas(self, test_client, capa_entity):
        """Test listing des CAPA"""
        test_client.mock_service.list_capas.return_value = ([capa_entity], 1)

        response = test_client.get("/v2/quality/capas")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_capa(self, test_client, capa_entity):
        """Test récupération d'un CAPA"""
        test_client.mock_service.get_capa.return_value = capa_entity

        response = test_client.get("/v2/quality/capas/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_update_capa(self, test_client, capa_entity):
        """Test mise à jour d'un CAPA"""
        updated_capa = capa_entity.with_updates(priority="CRITICAL")
        test_client.mock_service.update_capa.return_value = updated_capa

        response = test_client.put("/v2/quality/capas/1", json={"priority": "CRITICAL"})

        assert response.status_code == 200

    def test_add_capa_action(self, test_client, capa_action_data, capa_action_entity):
        """Test ajout d'une action à un CAPA"""
        test_client.mock_service.add_capa_action.return_value = capa_action_entity

        response = test_client.post("/v2/quality/capas/1/actions", json=capa_action_data)

        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "PREVENTIVE"

    def test_update_capa_action(self, test_client, capa_action_entity):
        """Test mise à jour d'une action CAPA"""
        updated_action = capa_action_entity.with_updates(status="COMPLETED")
        test_client.mock_service.update_capa_action.return_value = updated_action

        response = test_client.put("/v2/quality/capa-actions/1", json={"status": "COMPLETED"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"

    def test_close_capa(self, test_client, capa_entity):
        """Test clôture d'un CAPA"""
        closed_capa = capa_entity.with_updates(status="CLOSED_EFFECTIVE")
        test_client.mock_service.close_capa.return_value = closed_capa

        close_data = {
            "effectiveness_verified": True,
            "effectiveness_result": "Actions correctives efficaces et résultats validés",
            "closure_comments": "Toutes les actions sont terminées"
        }
        response = test_client.post("/v2/quality/capas/1/close", json=close_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED_EFFECTIVE"

    def test_filter_capas_by_type_and_priority(self, test_client, capa_entity):
        """Test filtrage des CAPA par type et priorité"""
        test_client.mock_service.list_capas.return_value = ([capa_entity], 1)

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

    def test_create_claim(self, test_client, claim_data, claim_entity):
        """Test création d'une réclamation"""
        test_client.mock_service.create_claim.return_value = claim_entity

        response = test_client.post("/v2/quality/claims", json=claim_data)

        assert response.status_code == 200
        data = response.json()
        assert data["claim_number"] == "REC-2024-00001"

    def test_list_claims(self, test_client, claim_entity):
        """Test listing des réclamations"""
        test_client.mock_service.list_claims.return_value = ([claim_entity], 1)

        response = test_client.get("/v2/quality/claims")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_claim(self, test_client, claim_entity):
        """Test récupération d'une réclamation"""
        test_client.mock_service.get_claim.return_value = claim_entity

        response = test_client.get("/v2/quality/claims/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_update_claim(self, test_client, claim_entity):
        """Test mise à jour d'une réclamation"""
        updated_claim = claim_entity.with_updates(priority="CRITICAL")
        test_client.mock_service.update_claim.return_value = updated_claim

        response = test_client.put("/v2/quality/claims/1", json={"priority": "CRITICAL"})

        assert response.status_code == 200

    def test_acknowledge_claim(self, test_client, claim_entity):
        """Test accusé de réception d'une réclamation"""
        acked_claim = claim_entity.with_updates(status="ACKNOWLEDGED")
        test_client.mock_service.acknowledge_claim.return_value = acked_claim

        response = test_client.post("/v2/quality/claims/1/acknowledge")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ACKNOWLEDGED"

    def test_respond_claim(self, test_client, claim_entity):
        """Test réponse à une réclamation"""
        responded_claim = claim_entity.with_updates(status="RESPONSE_SENT")
        test_client.mock_service.respond_claim.return_value = responded_claim

        response_data = {"response_content": "Nous allons remplacer les pièces"}
        response = test_client.post("/v2/quality/claims/1/respond", json=response_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RESPONSE_SENT"

    def test_resolve_claim(self, test_client, claim_entity):
        """Test résolution d'une réclamation"""
        resolved_claim = claim_entity.with_updates(status="RESOLVED")
        test_client.mock_service.resolve_claim.return_value = resolved_claim

        resolve_data = {
            "resolution_type": "REPLACEMENT",
            "resolution_description": "Pièces remplacées"
        }
        response = test_client.post("/v2/quality/claims/1/resolve", json=resolve_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RESOLVED"

    def test_close_claim(self, test_client, claim_entity):
        """Test clôture d'une réclamation"""
        closed_claim = claim_entity.with_updates(status="CLOSED")
        test_client.mock_service.close_claim.return_value = closed_claim

        close_data = {
            "customer_satisfied": True,
            "satisfaction_feedback": "Client satisfait"
        }
        response = test_client.post("/v2/quality/claims/1/close", json=close_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"

    def test_add_claim_action(self, test_client, claim_action_data, claim_action_entity):
        """Test ajout d'une action à une réclamation"""
        test_client.mock_service.add_claim_action.return_value = claim_action_entity

        response = test_client.post("/v2/quality/claims/1/actions", json=claim_action_data)

        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "IMMEDIATE"

    def test_filter_claims_by_customer(self, test_client, claim_entity):
        """Test filtrage des réclamations par client"""
        test_client.mock_service.list_claims.return_value = ([claim_entity], 1)

        response = test_client.get("/v2/quality/claims", params={"customer_id": 1})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# INDICATEURS - 6 tests
# ============================================================================

class TestIndicators:
    """Tests pour les endpoints d'indicateurs"""

    def test_create_indicator(self, test_client, indicator_data, indicator_entity):
        """Test création d'un indicateur"""
        test_client.mock_service.create_indicator.return_value = indicator_entity

        response = test_client.post("/v2/quality/indicators", json=indicator_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "IND-001"

    def test_list_indicators(self, test_client, indicator_entity):
        """Test listing des indicateurs"""
        test_client.mock_service.list_indicators.return_value = ([indicator_entity], 1)

        response = test_client.get("/v2/quality/indicators")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_indicator(self, test_client, indicator_entity):
        """Test récupération d'un indicateur"""
        test_client.mock_service.get_indicator.return_value = indicator_entity

        response = test_client.get("/v2/quality/indicators/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_update_indicator(self, test_client, indicator_entity):
        """Test mise à jour d'un indicateur"""
        updated_indicator = indicator_entity.with_updates(target_value=Decimal("99"))
        test_client.mock_service.update_indicator.return_value = updated_indicator

        response = test_client.put("/v2/quality/indicators/1", json={"target_value": "99"})

        assert response.status_code == 200

    def test_add_measurement(self, test_client, indicator_measurement_data, indicator_measurement_entity):
        """Test ajout d'une mesure à un indicateur"""
        test_client.mock_service.add_measurement.return_value = indicator_measurement_entity

        response = test_client.post("/v2/quality/indicators/1/measurements", json=indicator_measurement_data)

        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "97.5"

    def test_filter_indicators_by_category(self, test_client, indicator_entity):
        """Test filtrage des indicateurs par catégorie"""
        test_client.mock_service.list_indicators.return_value = ([indicator_entity], 1)

        response = test_client.get("/v2/quality/indicators", params={"category": "QUALITY"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# CERTIFICATIONS - 6 tests
# ============================================================================

class TestCertifications:
    """Tests pour les endpoints de certifications"""

    def test_create_certification(self, test_client, certification_data, certification_entity):
        """Test création d'une certification"""
        test_client.mock_service.create_certification.return_value = certification_entity

        response = test_client.post("/v2/quality/certifications", json=certification_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "ISO-9001"

    def test_list_certifications(self, test_client, certification_entity):
        """Test listing des certifications"""
        test_client.mock_service.list_certifications.return_value = ([certification_entity], 1)

        response = test_client.get("/v2/quality/certifications")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_certification(self, test_client, certification_entity):
        """Test récupération d'une certification"""
        test_client.mock_service.get_certification.return_value = certification_entity

        response = test_client.get("/v2/quality/certifications/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_update_certification(self, test_client, certification_entity):
        """Test mise à jour d'une certification"""
        updated_cert = certification_entity.with_updates(status="EXPIRED")
        test_client.mock_service.update_certification.return_value = updated_cert

        response = test_client.put("/v2/quality/certifications/1", json={"status": "EXPIRED"})

        assert response.status_code == 200

    def test_add_certification_audit(self, test_client, certification_audit_data, certification_audit_entity):
        """Test ajout d'un audit à une certification"""
        test_client.mock_service.add_certification_audit.return_value = certification_audit_entity

        response = test_client.post("/v2/quality/certifications/1/audits", json=certification_audit_data)

        assert response.status_code == 200
        data = response.json()
        assert data["audit_type"] == "SURVEILLANCE"

    def test_update_certification_audit(self, test_client, certification_audit_entity):
        """Test mise à jour d'un audit de certification"""
        updated_audit = certification_audit_entity.with_updates(notes="Audit réussi")
        test_client.mock_service.update_certification_audit.return_value = updated_audit

        response = test_client.put("/v2/quality/certification-audits/1", json={"notes": "Audit réussi"})

        assert response.status_code == 200


# ============================================================================
# DASHBOARD - 2 tests
# ============================================================================

class TestDashboard:
    """Tests pour l'endpoint du dashboard"""

    def test_get_dashboard(self, test_client, dashboard_entity):
        """Test récupération du dashboard qualité"""
        test_client.mock_service.get_dashboard.return_value = dashboard_entity

        response = test_client.get("/v2/quality/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "nc_total" in data
        assert "controls_total" in data
        assert "capa_total" in data

    def test_dashboard_statistics(self, test_client, dashboard_entity):
        """Test statistiques complètes du dashboard"""
        test_client.mock_service.get_dashboard.return_value = dashboard_entity

        response = test_client.get("/v2/quality/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["nc_total"] == 10
        assert data["capa_effectiveness_rate"] == "85.0"


# ============================================================================
# WORKFLOWS - 2 tests
# ============================================================================

class TestWorkflows:
    """Tests pour les workflows qualité"""

    def test_nc_to_capa_workflow(self, test_client, nc_entity, capa_entity):
        """Test workflow: NC -> CAPA -> Clôture"""
        # 1. Créer NC
        test_client.mock_service.create_non_conformance.return_value = nc_entity
        nc_response = test_client.post("/v2/quality/non-conformances", json={
            "title": "Pièce défectueuse",
            "description": "Surface rayée",
            "nc_type": "INTERNAL",
            "severity": "MAJOR",
            "detected_date": str(date.today()),
        })
        assert nc_response.status_code == 200

        # 2. Créer CAPA lié
        test_client.mock_service.create_capa.return_value = capa_entity
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
        closed_capa = capa_entity.with_updates(status="CLOSED_EFFECTIVE")
        test_client.mock_service.close_capa.return_value = closed_capa
        close_response = test_client.post("/v2/quality/capas/1/close", json={
            "effectiveness_verified": True,
            "effectiveness_result": "Actions correctives efficaces et vérifiées",
            "closure_comments": "Toutes les actions sont terminées et validées"
        })
        assert close_response.status_code == 200

    def test_audit_finding_to_action_workflow(self, test_client, audit_entity, audit_finding_entity):
        """Test workflow: Audit -> Constat -> Action corrective"""
        # 1. Créer audit
        test_client.mock_service.create_audit.return_value = audit_entity
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
        test_client.mock_service.add_finding.return_value = audit_finding_entity
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

    def test_pagination_skip_limit(self, test_client, nc_entity):
        """Test pagination avec skip et limit"""
        test_client.mock_service.list_non_conformances.return_value = ([nc_entity], 100)

        response = test_client.get("/v2/quality/non-conformances", params={"skip": 10, "limit": 20})

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 10
        assert data["limit"] == 20
        assert data["total"] == 100

    def test_pagination_limits(self, test_client):
        """Test limites de pagination"""
        # Test limite max (200)
        response = test_client.get("/v2/quality/non-conformances", params={"limit": 300})
        assert response.status_code == 422  # Validation error

        # Test limite valide
        test_client.mock_service.list_non_conformances.return_value = ([], 0)
        response = test_client.get("/v2/quality/non-conformances", params={"limit": 50})
        assert response.status_code == 200


# ============================================================================
# TENANT ISOLATION - 2 tests
# ============================================================================

class TestTenantIsolation:
    """Tests pour l'isolation des tenants"""

    def test_tenant_context_used(self, test_client, nc_entity):
        """Test que le contexte tenant est bien utilisé"""
        test_client.mock_service.create_non_conformance.return_value = nc_entity

        nc_data = {
            "title": "Test NC",
            "description": "Description",
            "nc_type": "INTERNAL",
            "severity": "MINOR",
            "detected_date": str(date.today()),
        }
        response = test_client.post("/v2/quality/non-conformances", json=nc_data)

        assert response.status_code == 200
        # Le service mock a été appelé (ce qui signifie que l'auth a passé)
        test_client.mock_service.create_non_conformance.assert_called()

    def test_user_context_used(self, test_client, nc_entity):
        """Test que le contexte utilisateur est bien utilisé"""
        test_client.mock_service.list_non_conformances.return_value = ([nc_entity], 1)

        response = test_client.get("/v2/quality/non-conformances")

        assert response.status_code == 200
        # Le service mock a été appelé
        test_client.mock_service.list_non_conformances.assert_called()


# ============================================================================
# ERROR HANDLING - 6 tests
# ============================================================================

class TestErrorHandling:
    """Tests pour la gestion des erreurs"""

    def test_nc_action_not_found(self, test_client):
        """Test action NC inexistante"""
        test_client.mock_service.update_nc_action.return_value = None

        response = test_client.put("/v2/quality/nc-actions/999", json={"status": "COMPLETED"})

        assert response.status_code == 404

    def test_control_not_found(self, test_client):
        """Test contrôle inexistant"""
        test_client.mock_service.get_control.return_value = None

        response = test_client.get("/v2/quality/controls/999")

        assert response.status_code == 404

    def test_capa_action_not_found(self, test_client):
        """Test action CAPA inexistante"""
        test_client.mock_service.update_capa_action.return_value = None

        response = test_client.put("/v2/quality/capa-actions/999", json={"status": "COMPLETED"})

        assert response.status_code == 404

    def test_claim_not_found(self, test_client):
        """Test réclamation inexistante"""
        test_client.mock_service.get_claim.return_value = None

        response = test_client.get("/v2/quality/claims/999")

        assert response.status_code == 404

    def test_indicator_not_found(self, test_client):
        """Test indicateur inexistant"""
        test_client.mock_service.get_indicator.return_value = None

        response = test_client.get("/v2/quality/indicators/999")

        assert response.status_code == 404

    def test_certification_not_found(self, test_client):
        """Test certification inexistante"""
        test_client.mock_service.get_certification.return_value = None

        response = test_client.get("/v2/quality/certifications/999")

        assert response.status_code == 404


# ============================================================================
# VALIDATION - 8 tests
# ============================================================================

class TestValidation:
    """Tests pour la validation des données"""

    def test_nc_missing_required_fields(self, test_client):
        """Test validation NC avec champs manquants"""
        response = test_client.post("/v2/quality/non-conformances", json={})

        assert response.status_code == 422

    def test_audit_missing_required_fields(self, test_client):
        """Test validation audit avec champs manquants"""
        response = test_client.post("/v2/quality/audits", json={})

        assert response.status_code == 422

    def test_capa_missing_required_fields(self, test_client):
        """Test validation CAPA avec champs manquants"""
        response = test_client.post("/v2/quality/capas", json={})

        assert response.status_code == 422

    def test_claim_missing_required_fields(self, test_client):
        """Test validation réclamation avec champs manquants"""
        response = test_client.post("/v2/quality/claims", json={})

        assert response.status_code == 422

    def test_invalid_pagination_skip(self, test_client):
        """Test validation skip négatif"""
        response = test_client.get("/v2/quality/non-conformances", params={"skip": -1})

        assert response.status_code == 422

    def test_invalid_pagination_limit_too_high(self, test_client):
        """Test validation limit trop élevé"""
        response = test_client.get("/v2/quality/non-conformances", params={"limit": 1000})

        assert response.status_code == 422

    def test_invalid_pagination_limit_zero(self, test_client):
        """Test validation limit à zéro"""
        response = test_client.get("/v2/quality/non-conformances", params={"limit": 0})

        assert response.status_code == 422

    def test_invalid_date_format(self, test_client):
        """Test validation format de date invalide"""
        response = test_client.get("/v2/quality/non-conformances", params={"date_from": "invalid-date"})

        assert response.status_code == 422
