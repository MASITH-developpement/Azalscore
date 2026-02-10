"""
Fixtures pour les tests Interventions v2
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext, UserRole
from app.main import app
from app.modules.interventions.models import InterventionStatut, InterventionPriorite


# ============================================================================
# FIXTURES GLOBALES
# ============================================================================

@pytest.fixture
def tenant_id():
    """Tenant ID de test"""
    return "tenant-test-interventions-001"


@pytest.fixture
def user_id():
    """User ID de test"""
    return "user-test-interventions-001"


# ============================================================================
# FIXTURES SERVICE
# ============================================================================

@pytest.fixture
def mock_interventions_service():
    """Mock InterventionsService pour les tests"""
    mock_service = MagicMock()

    # Configuration par défaut
    mock_service.list_donneurs_ordre.return_value = []
    mock_service.get_donneur_ordre.return_value = None
    mock_service.create_donneur_ordre.return_value = None
    mock_service.update_donneur_ordre.return_value = None

    mock_service.list_interventions.return_value = ([], 0)
    mock_service.get_intervention.return_value = None
    mock_service.get_intervention_by_reference.return_value = None
    mock_service.create_intervention.return_value = None
    mock_service.update_intervention.return_value = None
    mock_service.delete_intervention.return_value = False

    mock_service.planifier_intervention.return_value = None
    mock_service.modifier_planification.return_value = None
    mock_service.annuler_planification.return_value = None

    mock_service.arrivee_sur_site.return_value = None
    mock_service.demarrer_intervention.return_value = None
    mock_service.terminer_intervention.return_value = None

    mock_service.get_rapport_intervention.return_value = None
    mock_service.update_rapport_intervention.return_value = None
    mock_service.ajouter_photo_rapport.return_value = None
    mock_service.signer_rapport.return_value = None

    mock_service.list_rapports_final.return_value = []
    mock_service.get_rapport_final.return_value = None
    mock_service.generer_rapport_final.return_value = None

    mock_service.get_stats.return_value = None

    return mock_service


@pytest.fixture
def mock_get_saas_context(tenant_id, user_id):
    """Mock de get_saas_context"""
    def _mock_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole.ADMIN,
            permissions={"interventions.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            correlation_id="test-correlation"
        )
    return _mock_context


@pytest.fixture
def mock_get_interventions_service(mock_interventions_service):
    """Mock de get_interventions_service"""
    def _mock_factory(db, tenant_id, user_id=None):
        return mock_interventions_service
    return _mock_factory


@pytest.fixture
def client(mock_get_saas_context, mock_interventions_service):
    """Client de test FastAPI avec mocks"""
    from app.modules.interventions.router_v2 import get_interventions_service

    # Remplacer les dépendances par les mocks
    app.dependency_overrides[get_saas_context] = mock_get_saas_context
    app.dependency_overrides[get_interventions_service] = lambda: mock_interventions_service

    client = TestClient(app)
    yield client

    # Nettoyer les overrides
    app.dependency_overrides.clear()


# ============================================================================
# FIXTURES DONNÉES DONNEUR ORDRE
# ============================================================================

@pytest.fixture
def donneur_ordre_data():
    """Données de donneur d'ordre sample"""
    return {
        "nom": "Client Principal",
        "type_organisation": "entreprise",
        "siret": "12345678901234",
        "adresse": "123 Rue de Paris",
        "code_postal": "75001",
        "ville": "Paris",
        "pays": "France",
        "email": "contact@client.com",
        "telephone": "+33123456789",
        "contact_nom": "Jean Dupont",
        "contact_fonction": "Responsable Achats",
        "is_active": True,
    }


@pytest.fixture
def donneur_ordre(donneur_ordre_data, tenant_id):
    """Instance donneur d'ordre sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        **donneur_ordre_data,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def donneur_ordre_list(donneur_ordre):
    """Liste de donneurs d'ordre sample"""
    return [
        donneur_ordre,
        {
            **donneur_ordre,
            "id": str(uuid4()),
            "nom": "Client Secondaire",
            "email": "contact@client2.com",
        },
    ]


# ============================================================================
# FIXTURES DONNÉES INTERVENTION
# ============================================================================

@pytest.fixture
def intervention_data():
    """Données d'intervention sample"""
    return {
        "titre": "Installation équipement",
        "description": "Installation d'un nouveau système",
        "client_id": str(uuid4()),
        "donneur_ordre_id": str(uuid4()),
        "projet_id": str(uuid4()),
        "priorite": "NORMALE",
        "type_intervention": "installation",
        "reference_externe": "EXT-2024-001",
        "adresse_intervention": "456 Avenue des Champs",
        "code_postal_intervention": "75008",
        "ville_intervention": "Paris",
        "contact_site_nom": "Marie Martin",
        "contact_site_telephone": "+33198765432",
        "duree_prevue_minutes": 120,
    }


@pytest.fixture
def intervention(intervention_data, tenant_id, user_id):
    """Instance intervention sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "reference": "INT-2024-0001",
        "statut": "A_PLANIFIER",
        **intervention_data,
        "intervenant_id": None,
        "date_prevue_debut": None,
        "date_prevue_fin": None,
        "date_arrivee_site": None,
        "date_demarrage": None,
        "date_fin": None,
        "duree_reelle_minutes": None,
        "planning_event_id": None,
        "geoloc_arrivee_lat": None,
        "geoloc_arrivee_lng": None,
        "created_by": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "deleted_at": None,
    }


@pytest.fixture
def intervention_planifiee(intervention, user_id):
    """Intervention planifiée sample"""
    now = datetime.utcnow()
    return {
        **intervention,
        "statut": "PLANIFIEE",
        "intervenant_id": user_id,
        "date_prevue_debut": (now + timedelta(hours=1)).isoformat(),
        "date_prevue_fin": (now + timedelta(hours=3)).isoformat(),
        "planning_event_id": str(uuid4()),
    }


@pytest.fixture
def intervention_en_cours(intervention_planifiee):
    """Intervention en cours sample"""
    now = datetime.utcnow()
    return {
        **intervention_planifiee,
        "statut": "EN_COURS",
        "date_arrivee_site": now.isoformat(),
        "date_demarrage": (now + timedelta(minutes=5)).isoformat(),
        "geoloc_arrivee_lat": 48.8566,
        "geoloc_arrivee_lng": 2.3522,
    }


@pytest.fixture
def intervention_terminee(intervention_en_cours):
    """Intervention terminée sample"""
    now = datetime.utcnow()
    return {
        **intervention_en_cours,
        "statut": "TERMINEE",
        "date_fin": (now + timedelta(hours=2)).isoformat(),
        "duree_reelle_minutes": 115,
    }


@pytest.fixture
def intervention_list(intervention, intervention_planifiee):
    """Liste d'interventions sample"""
    return [intervention, intervention_planifiee]


@pytest.fixture
def planifier_data(user_id):
    """Données de planification sample"""
    now = datetime.utcnow()
    return {
        "intervenant_id": user_id,
        "date_prevue_debut": (now + timedelta(hours=1)).isoformat(),
        "date_prevue_fin": (now + timedelta(hours=3)).isoformat(),
    }


@pytest.fixture
def arrivee_data():
    """Données d'arrivée sample"""
    return {
        "latitude": 48.8566,
        "longitude": 2.3522,
    }


@pytest.fixture
def fin_intervention_data():
    """Données de fin d'intervention sample"""
    return {
        "resume_actions": "Installation réalisée avec succès",
        "anomalies": "Aucune anomalie détectée",
        "recommandations": "Vérifier le fonctionnement dans 1 mois",
    }


# ============================================================================
# FIXTURES DONNÉES RAPPORT
# ============================================================================

@pytest.fixture
def rapport_data():
    """Données de rapport sample"""
    return {
        "resume_actions": "Actions effectuées durant l'intervention",
        "anomalies": "Quelques anomalies mineures",
        "recommandations": "Prévoir un suivi dans 2 semaines",
    }


@pytest.fixture
def rapport_intervention(intervention, tenant_id):
    """Instance rapport intervention sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "intervention_id": intervention["id"],
        "reference_intervention": intervention["reference"],
        "client_id": intervention["client_id"],
        "donneur_ordre_id": intervention["donneur_ordre_id"],
        "resume_actions": "Actions réalisées",
        "anomalies": "Aucune",
        "recommandations": "RAS",
        "photos": [],
        "signature_client": None,
        "nom_signataire": None,
        "date_signature": None,
        "geoloc_signature_lat": None,
        "geoloc_signature_lng": None,
        "is_signed": False,
        "is_locked": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def photo_data():
    """Données de photo sample"""
    return {
        "url": "https://example.com/photo.jpg",
        "caption": "Photo de l'installation",
    }


@pytest.fixture
def signature_data():
    """Données de signature sample"""
    return {
        "signature_client": "data:image/png;base64,iVBORw0KG...",
        "nom_signataire": "Jean Dupont",
        "latitude": 48.8566,
        "longitude": 2.3522,
    }


@pytest.fixture
def rapport_final_data():
    """Données de rapport final sample"""
    return {
        "projet_id": str(uuid4()),
        "donneur_ordre_id": None,
        "synthese": "Synthèse des interventions du projet",
    }


@pytest.fixture
def rapport_final(rapport_final_data, tenant_id, user_id):
    """Instance rapport final sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "reference": "RFINAL-2024-0001",
        "projet_id": rapport_final_data["projet_id"],
        "donneur_ordre_id": rapport_final_data["donneur_ordre_id"],
        "interventions_references": ["INT-2024-0001", "INT-2024-0002"],
        "temps_total_minutes": 240,
        "synthese": rapport_final_data["synthese"],
        "date_generation": datetime.utcnow().isoformat(),
        "is_locked": True,
        "created_by": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def rapport_final_list(rapport_final):
    """Liste de rapports finaux sample"""
    return [
        rapport_final,
        {
            **rapport_final,
            "id": str(uuid4()),
            "reference": "RFINAL-2024-0002",
            "temps_total_minutes": 180,
        },
    ]


# ============================================================================
# FIXTURES STATISTIQUES
# ============================================================================

@pytest.fixture
def intervention_stats():
    """Statistiques interventions sample"""
    return {
        "total": 100,
        "a_planifier": 20,
        "planifiees": 30,
        "en_cours": 10,
        "terminees": 40,
        "duree_moyenne_minutes": 125.5,
    }
