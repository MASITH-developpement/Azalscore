"""
Tests pour les endpoints Interventions v2 (CORE SaaS)
"""

import pytest
from uuid import uuid4
from app.modules.interventions.service import (
    InterventionNotFoundError,
    InterventionWorkflowError,
    RapportLockedError,
)


# ============================================================================
# TESTS DONNEURS D'ORDRE
# ============================================================================

class TestDonneursOrdre:
    """Tests endpoints donneurs d'ordre"""

    def test_list_donneurs_ordre_success(test_client, self, client, mock_interventions_service, donneur_ordre_list):
        """Test liste donneurs ordre - succès"""
        mock_interventions_service.list_donneurs_ordre.return_value = donneur_ordre_list

        response = test_client.get("/v2/interventions/donneurs-ordre")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["nom"] == "Client Principal"
        mock_interventions_service.list_donneurs_ordre.assert_called_once_with(True)

    def test_list_donneurs_ordre_inactive(test_client, self, client, mock_interventions_service, donneur_ordre_list):
        """Test liste donneurs ordre incluant inactifs"""
        mock_interventions_service.list_donneurs_ordre.return_value = donneur_ordre_list

        response = test_client.get("/v2/interventions/donneurs-ordre?active_only=false")

        assert response.status_code == 200
        mock_interventions_service.list_donneurs_ordre.assert_called_once_with(False)

    def test_get_donneur_ordre_success(test_client, self, client, mock_interventions_service, donneur_ordre):
        """Test récupération donneur ordre - succès"""
        mock_interventions_service.get_donneur_ordre.return_value = donneur_ordre
        donneur_id = donneur_ordre["id"]

        response = test_client.get(f"/v2/interventions/donneurs-ordre/{donneur_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == donneur_id
        assert data["nom"] == "Client Principal"

    def test_get_donneur_ordre_not_found(test_client, self, client, mock_interventions_service):
        """Test récupération donneur ordre - non trouvé"""
        mock_interventions_service.get_donneur_ordre.return_value = None
        donneur_id = str(uuid4())

        response = test_client.get(f"/v2/interventions/donneurs-ordre/{donneur_id}")

        assert response.status_code == 404
        assert "non trouvé" in response.json()["detail"]

    def test_create_donneur_ordre_success(test_client, self, client, mock_interventions_service, donneur_ordre_data, donneur_ordre):
        """Test création donneur ordre - succès"""
        mock_interventions_service.create_donneur_ordre.return_value = donneur_ordre

        response = test_client.post(
            "/v2/interventions/donneurs-ordre",
            json=donneur_ordre_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["nom"] == "Client Principal"
        mock_interventions_service.create_donneur_ordre.assert_called_once()

    def test_update_donneur_ordre_success(test_client, self, client, mock_interventions_service, donneur_ordre):
        """Test mise à jour donneur ordre - succès"""
        donneur_id = donneur_ordre["id"]
        updated = {**donneur_ordre, "nom": "Client Modifié"}
        mock_interventions_service.update_donneur_ordre.return_value = updated

        response = test_client.put(
            f"/v2/interventions/donneurs-ordre/{donneur_id}",
            json={"nom": "Client Modifié"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nom"] == "Client Modifié"

    def test_update_donneur_ordre_not_found(test_client, self, client, mock_interventions_service):
        """Test mise à jour donneur ordre - non trouvé"""
        mock_interventions_service.update_donneur_ordre.return_value = None
        donneur_id = str(uuid4())

        response = test_client.put(
            f"/v2/interventions/donneurs-ordre/{donneur_id}",
            json={"nom": "Test"}
        )

        assert response.status_code == 404


# ============================================================================
# TESTS INTERVENTIONS CRUD
# ============================================================================

class TestInterventionsCRUD:
    """Tests endpoints CRUD interventions"""

    def test_list_interventions_success(test_client, self, client, mock_interventions_service, intervention_list):
        """Test liste interventions - succès"""
        mock_interventions_service.list_interventions.return_value = (intervention_list, 2)

        response = test_client.get("/v2/interventions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_interventions_with_filters(test_client, self, client, mock_interventions_service, intervention_list):
        """Test liste interventions avec filtres"""
        mock_interventions_service.list_interventions.return_value = (intervention_list, 2)

        response = test_client.get(
            "/v2/interventions?statut=PLANIFIEE&priorite=HAUTE&page=1&page_size=10"
        )

        assert response.status_code == 200
        mock_interventions_service.list_interventions.assert_called_once()

    def test_get_stats_success(test_client, self, client, mock_interventions_service, intervention_stats):
        """Test récupération stats - succès"""
        mock_interventions_service.get_stats.return_value = intervention_stats

        response = test_client.get("/v2/interventions/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
        assert data["a_planifier"] == 20
        assert data["terminees"] == 40

    def test_get_intervention_success(test_client, self, client, mock_interventions_service, intervention):
        """Test récupération intervention - succès"""
        mock_interventions_service.get_intervention.return_value = intervention
        intervention_id = intervention["id"]

        response = test_client.get(f"/v2/interventions/{intervention_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == intervention_id
        assert data["reference"] == "INT-2024-0001"

    def test_get_intervention_not_found(test_client, self, client, mock_interventions_service):
        """Test récupération intervention - non trouvée"""
        mock_interventions_service.get_intervention.return_value = None
        intervention_id = str(uuid4())

        response = test_client.get(f"/v2/interventions/{intervention_id}")

        assert response.status_code == 404

    def test_get_intervention_by_reference_success(test_client, self, client, mock_interventions_service, intervention):
        """Test récupération intervention par référence - succès"""
        mock_interventions_service.get_intervention_by_reference.return_value = intervention
        reference = intervention["reference"]

        response = test_client.get(f"/v2/interventions/ref/{reference}")

        assert response.status_code == 200
        data = response.json()
        assert data["reference"] == reference

    def test_get_intervention_by_reference_not_found(test_client, self, client, mock_interventions_service):
        """Test récupération intervention par référence - non trouvée"""
        mock_interventions_service.get_intervention_by_reference.return_value = None

        response = test_client.get("/v2/interventions/ref/INT-2024-9999")

        assert response.status_code == 404

    def test_create_intervention_success(test_client, self, client, mock_interventions_service, intervention_data, intervention):
        """Test création intervention - succès"""
        mock_interventions_service.create_intervention.return_value = intervention

        response = test_client.post(
            "/v2/interventions",
            json=intervention_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["reference"] == "INT-2024-0001"
        assert data["statut"] == "A_PLANIFIER"
        mock_interventions_service.create_intervention.assert_called_once()

    def test_update_intervention_success(test_client, self, client, mock_interventions_service, intervention):
        """Test mise à jour intervention - succès"""
        intervention_id = intervention["id"]
        updated = {**intervention, "titre": "Titre modifié"}
        mock_interventions_service.update_intervention.return_value = updated

        response = test_client.put(
            f"/v2/interventions/{intervention_id}",
            json={"titre": "Titre modifié"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["titre"] == "Titre modifié"

    def test_update_intervention_not_found(test_client, self, client, mock_interventions_service):
        """Test mise à jour intervention - non trouvée"""
        mock_interventions_service.update_intervention.return_value = None
        intervention_id = str(uuid4())

        response = test_client.put(
            f"/v2/interventions/{intervention_id}",
            json={"titre": "Test"}
        )

        assert response.status_code == 404

    def test_delete_intervention_success(test_client, self, client, mock_interventions_service):
        """Test suppression intervention - succès"""
        mock_interventions_service.delete_intervention.return_value = True
        intervention_id = str(uuid4())

        response = test_client.delete(f"/v2/interventions/{intervention_id}")

        assert response.status_code == 204

    def test_delete_intervention_not_found(test_client, self, client, mock_interventions_service):
        """Test suppression intervention - non trouvée"""
        mock_interventions_service.delete_intervention.return_value = False
        intervention_id = str(uuid4())

        response = test_client.delete(f"/v2/interventions/{intervention_id}")

        assert response.status_code == 404

    def test_delete_intervention_workflow_error(test_client, self, client, mock_interventions_service):
        """Test suppression intervention - erreur workflow"""
        mock_interventions_service.delete_intervention.side_effect = InterventionWorkflowError(
            "Impossible de supprimer une intervention terminée"
        )
        intervention_id = str(uuid4())

        response = test_client.delete(f"/v2/interventions/{intervention_id}")

        assert response.status_code == 400
        assert "terminée" in response.json()["detail"]


# ============================================================================
# TESTS PLANIFICATION
# ============================================================================

class TestPlanification:
    """Tests endpoints planification"""

    def test_planifier_intervention_success(test_client, self, client, mock_interventions_service, intervention_planifiee, planifier_data):
        """Test planification intervention - succès"""
        mock_interventions_service.planifier_intervention.return_value = intervention_planifiee
        intervention_id = intervention_planifiee["id"]

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/planifier",
            json=planifier_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["statut"] == "PLANIFIEE"
        assert data["intervenant_id"] is not None

    def test_planifier_intervention_not_found(test_client, self, client, mock_interventions_service, planifier_data):
        """Test planification intervention - non trouvée"""
        mock_interventions_service.planifier_intervention.side_effect = InterventionNotFoundError(
            "Intervention non trouvée"
        )
        intervention_id = str(uuid4())

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/planifier",
            json=planifier_data
        )

        assert response.status_code == 404

    def test_planifier_intervention_workflow_error(test_client, self, client, mock_interventions_service, planifier_data):
        """Test planification intervention - erreur workflow"""
        mock_interventions_service.planifier_intervention.side_effect = InterventionWorkflowError(
            "L'intervention doit être A_PLANIFIER"
        )
        intervention_id = str(uuid4())

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/planifier",
            json=planifier_data
        )

        assert response.status_code == 400

    def test_modifier_planification_success(test_client, self, client, mock_interventions_service, intervention_planifiee, planifier_data):
        """Test modification planification - succès"""
        mock_interventions_service.modifier_planification.return_value = intervention_planifiee
        intervention_id = intervention_planifiee["id"]

        response = test_client.put(
            f"/v2/interventions/{intervention_id}/planification",
            json=planifier_data
        )

        assert response.status_code == 200

    def test_modifier_planification_not_found(test_client, self, client, mock_interventions_service, planifier_data):
        """Test modification planification - non trouvée"""
        mock_interventions_service.modifier_planification.side_effect = InterventionNotFoundError(
            "Intervention non trouvée"
        )
        intervention_id = str(uuid4())

        response = test_client.put(
            f"/v2/interventions/{intervention_id}/planification",
            json=planifier_data
        )

        assert response.status_code == 404

    def test_annuler_planification_success(test_client, self, client, mock_interventions_service, intervention):
        """Test annulation planification - succès"""
        mock_interventions_service.annuler_planification.return_value = intervention
        intervention_id = intervention["id"]

        response = test_client.delete(
            f"/v2/interventions/{intervention_id}/planification"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["statut"] == "A_PLANIFIER"

    def test_annuler_planification_workflow_error(test_client, self, client, mock_interventions_service):
        """Test annulation planification - erreur workflow"""
        mock_interventions_service.annuler_planification.side_effect = InterventionWorkflowError(
            "L'annulation n'est possible que pour les interventions PLANIFIEES"
        )
        intervention_id = str(uuid4())

        response = test_client.delete(
            f"/v2/interventions/{intervention_id}/planification"
        )

        assert response.status_code == 400


# ============================================================================
# TESTS ACTIONS TERRAIN
# ============================================================================

class TestActionsTerrain:
    """Tests endpoints actions terrain"""

    def test_arrivee_sur_site_success(test_client, self, client, mock_interventions_service, intervention_en_cours, arrivee_data):
        """Test arrivée sur site - succès"""
        mock_interventions_service.arrivee_sur_site.return_value = intervention_en_cours
        intervention_id = intervention_en_cours["id"]

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/arrivee",
            json=arrivee_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["statut"] == "EN_COURS"
        assert data["date_arrivee_site"] is not None

    def test_arrivee_sur_site_not_found(test_client, self, client, mock_interventions_service, arrivee_data):
        """Test arrivée sur site - non trouvée"""
        mock_interventions_service.arrivee_sur_site.side_effect = InterventionNotFoundError(
            "Intervention non trouvée"
        )
        intervention_id = str(uuid4())

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/arrivee",
            json=arrivee_data
        )

        assert response.status_code == 404

    def test_arrivee_sur_site_workflow_error(test_client, self, client, mock_interventions_service, arrivee_data):
        """Test arrivée sur site - erreur workflow"""
        mock_interventions_service.arrivee_sur_site.side_effect = InterventionWorkflowError(
            "L'arrivée n'est possible que pour les interventions PLANIFIEES"
        )
        intervention_id = str(uuid4())

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/arrivee",
            json=arrivee_data
        )

        assert response.status_code == 400

    def test_demarrer_intervention_success(test_client, self, client, mock_interventions_service, intervention_en_cours):
        """Test démarrage intervention - succès"""
        mock_interventions_service.demarrer_intervention.return_value = intervention_en_cours
        intervention_id = intervention_en_cours["id"]

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/demarrer"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["date_demarrage"] is not None

    def test_demarrer_intervention_workflow_error(test_client, self, client, mock_interventions_service):
        """Test démarrage intervention - erreur workflow"""
        mock_interventions_service.demarrer_intervention.side_effect = InterventionWorkflowError(
            "Le démarrage n'est possible que pour les interventions EN_COURS"
        )
        intervention_id = str(uuid4())

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/demarrer"
        )

        assert response.status_code == 400

    def test_terminer_intervention_success(test_client, self, client, mock_interventions_service, intervention_terminee, fin_intervention_data):
        """Test fin intervention - succès"""
        mock_interventions_service.terminer_intervention.return_value = intervention_terminee
        intervention_id = intervention_terminee["id"]

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/terminer",
            json=fin_intervention_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["statut"] == "TERMINEE"
        assert data["date_fin"] is not None
        assert data["duree_reelle_minutes"] is not None

    def test_terminer_intervention_workflow_error(test_client, self, client, mock_interventions_service, fin_intervention_data):
        """Test fin intervention - erreur workflow"""
        mock_interventions_service.terminer_intervention.side_effect = InterventionWorkflowError(
            "L'intervention doit être démarrée avant d'être terminée"
        )
        intervention_id = str(uuid4())

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/terminer",
            json=fin_intervention_data
        )

        assert response.status_code == 400


# ============================================================================
# TESTS RAPPORTS INTERVENTION
# ============================================================================

class TestRapportsIntervention:
    """Tests endpoints rapports intervention"""

    def test_get_rapport_intervention_success(test_client, self, client, mock_interventions_service, rapport_intervention):
        """Test récupération rapport - succès"""
        mock_interventions_service.get_rapport_intervention.return_value = rapport_intervention
        intervention_id = rapport_intervention["intervention_id"]

        response = test_client.get(
            f"/v2/interventions/{intervention_id}/rapport"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intervention_id"] == intervention_id

    def test_get_rapport_intervention_not_found(test_client, self, client, mock_interventions_service):
        """Test récupération rapport - non trouvé"""
        mock_interventions_service.get_rapport_intervention.return_value = None
        intervention_id = str(uuid4())

        response = test_client.get(
            f"/v2/interventions/{intervention_id}/rapport"
        )

        assert response.status_code == 404

    def test_update_rapport_intervention_success(test_client, self, client, mock_interventions_service, rapport_intervention, rapport_data):
        """Test mise à jour rapport - succès"""
        mock_interventions_service.update_rapport_intervention.return_value = rapport_intervention
        intervention_id = rapport_intervention["intervention_id"]

        response = test_client.put(
            f"/v2/interventions/{intervention_id}/rapport",
            json=rapport_data
        )

        assert response.status_code == 200

    def test_update_rapport_intervention_locked(test_client, self, client, mock_interventions_service, rapport_data):
        """Test mise à jour rapport - verrouillé"""
        mock_interventions_service.update_rapport_intervention.side_effect = RapportLockedError(
            "Le rapport est verrouillé"
        )
        intervention_id = str(uuid4())

        response = test_client.put(
            f"/v2/interventions/{intervention_id}/rapport",
            json=rapport_data
        )

        assert response.status_code == 400
        assert "verrouillé" in response.json()["detail"]

    def test_ajouter_photo_rapport_success(test_client, self, client, mock_interventions_service, rapport_intervention, photo_data):
        """Test ajout photo rapport - succès"""
        mock_interventions_service.ajouter_photo_rapport.return_value = rapport_intervention
        intervention_id = rapport_intervention["intervention_id"]

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/rapport/photos",
            json=photo_data
        )

        assert response.status_code == 200

    def test_ajouter_photo_rapport_locked(test_client, self, client, mock_interventions_service, photo_data):
        """Test ajout photo rapport - verrouillé"""
        mock_interventions_service.ajouter_photo_rapport.side_effect = RapportLockedError(
            "Le rapport est verrouillé"
        )
        intervention_id = str(uuid4())

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/rapport/photos",
            json=photo_data
        )

        assert response.status_code == 400

    def test_signer_rapport_success(test_client, self, client, mock_interventions_service, rapport_intervention, signature_data):
        """Test signature rapport - succès"""
        signed_rapport = {**rapport_intervention, "is_signed": True}
        mock_interventions_service.signer_rapport.return_value = signed_rapport
        intervention_id = rapport_intervention["intervention_id"]

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/rapport/signer",
            json=signature_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_signed"] is True

    def test_signer_rapport_already_signed(test_client, self, client, mock_interventions_service, signature_data):
        """Test signature rapport - déjà signé"""
        mock_interventions_service.signer_rapport.side_effect = RapportLockedError(
            "Le rapport est déjà signé"
        )
        intervention_id = str(uuid4())

        response = test_client.post(
            f"/v2/interventions/{intervention_id}/rapport/signer",
            json=signature_data
        )

        assert response.status_code == 400


# ============================================================================
# TESTS RAPPORTS FINAUX
# ============================================================================

class TestRapportsFinaux:
    """Tests endpoints rapports finaux"""

    def test_list_rapports_final_success(test_client, self, client, mock_interventions_service, rapport_final_list):
        """Test liste rapports finaux - succès"""
        mock_interventions_service.list_rapports_final.return_value = rapport_final_list

        response = test_client.get("/v2/interventions/rapports-finaux")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_rapports_final_with_filters(test_client, self, client, mock_interventions_service, rapport_final_list):
        """Test liste rapports finaux avec filtres"""
        mock_interventions_service.list_rapports_final.return_value = rapport_final_list
        projet_id = str(uuid4())

        response = test_client.get(
            f"/v2/interventions/rapports-finaux?projet_id={projet_id}"
        )

        assert response.status_code == 200
        mock_interventions_service.list_rapports_final.assert_called_once()

    def test_get_rapport_final_success(test_client, self, client, mock_interventions_service, rapport_final):
        """Test récupération rapport final - succès"""
        mock_interventions_service.get_rapport_final.return_value = rapport_final
        rapport_id = rapport_final["id"]

        response = test_client.get(
            f"/v2/interventions/rapports-finaux/{rapport_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rapport_id
        assert data["reference"] == "RFINAL-2024-0001"

    def test_get_rapport_final_not_found(test_client, self, client, mock_interventions_service):
        """Test récupération rapport final - non trouvé"""
        mock_interventions_service.get_rapport_final.return_value = None
        rapport_id = str(uuid4())

        response = test_client.get(
            f"/v2/interventions/rapports-finaux/{rapport_id}"
        )

        assert response.status_code == 404

    def test_generer_rapport_final_success(test_client, self, client, mock_interventions_service, rapport_final_data, rapport_final):
        """Test génération rapport final - succès"""
        mock_interventions_service.generer_rapport_final.return_value = rapport_final

        response = test_client.post(
            "/v2/interventions/rapports-finaux",
            json=rapport_final_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["reference"] == "RFINAL-2024-0001"
        assert data["is_locked"] is True

    def test_generer_rapport_final_no_interventions(test_client, self, client, mock_interventions_service, rapport_final_data):
        """Test génération rapport final - aucune intervention"""
        mock_interventions_service.generer_rapport_final.side_effect = InterventionNotFoundError(
            "Aucune intervention terminée trouvée"
        )

        response = test_client.post(
            "/v2/interventions/rapports-finaux",
            json=rapport_final_data
        )

        assert response.status_code == 404
        assert "Aucune intervention" in response.json()["detail"]
