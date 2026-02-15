"""
Fixtures pour les tests Interventions v2

Ce module fournit les fixtures pytest pour tester le module Interventions.
Les fixtures utilisent MockEntity pour simuler les objets SQLAlchemy avec
accès par attributs (obj.id au lieu de obj["id"]).

Hérite des fixtures globales de app/conftest.py.
"""

import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union
from unittest.mock import MagicMock
from uuid import uuid4

from app.modules.interventions.models import (
    InterventionStatut,
    InterventionPriorite,
    TypeIntervention,
    CorpsEtat,
)


# ============================================================================
# UTILITAIRES MOCK
# ============================================================================

class MockEntity:
    """
    Classe utilitaire qui convertit un dict en objet avec accès par attributs.

    Permet aux fixtures de retourner des objets compatibles avec les serializers
    qui utilisent la notation point (ex: donneur.id, intervention.reference).

    Supporte également le déballage dict ({**entity, "key": val}) pour les tests.

    IMPORTANT: Les attributs non définis retournent None (comme les modèles SQLAlchemy)
    au lieu de lever AttributeError. Cela permet aux serializers de fonctionner
    même si toutes les colonnes ne sont pas définies dans les fixtures.

    Exemple:
        data = {"id": "123", "nom": "Test"}
        entity = MockEntity(data)
        entity.id  # "123"
        entity.nom  # "Test"
        entity.unknown  # None (pas d'erreur)
        {**entity, "nom": "New"}  # {"id": "123", "nom": "New"}
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialise un MockEntity à partir d'un dictionnaire.

        Les valeurs imbriquées (dicts) sont également converties en MockEntity.
        Les listes de dicts sont converties en listes de MockEntity.
        """
        object.__setattr__(self, '_data', data.copy())
        for key, value in data.items():
            if isinstance(value, dict):
                object.__setattr__(self, key, MockEntity(value))
            elif isinstance(value, list):
                object.__setattr__(self, key, [
                    MockEntity(item) if isinstance(item, dict) else item
                    for item in value
                ])
            else:
                object.__setattr__(self, key, value)

    def __getattr__(self, name: str) -> Any:
        """
        Retourne None pour les attributs non définis.

        Cela simule le comportement des modèles SQLAlchemy où les colonnes
        non renseignées ont une valeur None.
        """
        # Ne pas retourner None pour les méthodes spéciales
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return None

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self._data.items())
        return f"MockEntity({attrs})"

    # Support pour le déballage dict (**entity)
    def keys(self):
        """Retourne les clés pour le déballage."""
        return self._data.keys()

    def __iter__(self):
        """Permet l'itération sur les clés."""
        return iter(self._data)

    def __getitem__(self, key: str):
        """Permet l'accès par index entity['key']."""
        return self._data.get(key)

    def items(self):
        """Retourne les paires clé-valeur."""
        return self._data.items()

    def to_dict(self) -> Dict[str, Any]:
        """Retourne le dict original."""
        return self._data.copy()

    def with_updates(self, **updates) -> "MockEntity":
        """
        Retourne un nouveau MockEntity avec les mises à jour spécifiées.

        Exemple:
            updated = entity.with_updates(nom="Nouveau nom", is_active=False)
        """
        new_data = {**self._data, **updates}
        return MockEntity(new_data)


def to_mock_entity(data: Union[Dict, List[Dict], None]) -> Union[MockEntity, List[MockEntity], None]:
    """
    Convertit un dict ou une liste de dicts en MockEntity.

    Args:
        data: Dict, liste de dicts, ou None

    Returns:
        MockEntity, liste de MockEntity, ou None
    """
    if data is None:
        return None
    if isinstance(data, list):
        return [MockEntity(item) for item in data]
    return MockEntity(data)


# ============================================================================
# FIXTURES HÉRITÉES DU CONFTEST GLOBAL
# ============================================================================
# Les fixtures suivantes sont héritées de app/conftest.py:
# - tenant_id, user_id, user_uuid
# - db_session, test_db_session
# - test_client (avec headers auto-injectés)
# - mock_auth_global (autouse=True)
# - saas_context


@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilité avec anciens tests).

    Le test_client du conftest global ajoute déjà les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


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
    """Mock de get_saas_context avec contexte valide pour tests"""
    # Convertir user_id string en UUID
    from uuid import UUID
    user_uuid = UUID(user_id) if isinstance(user_id, str) and "-" in user_id else uuid4()

    def _mock_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_uuid,
            role=UserRole.ADMIN,
            permissions={"interventions.*"},
            scope=TenantScope.TENANT,
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
def test_client(mock_get_saas_context, mock_interventions_service, tenant_id, user_id):
    """Client de test FastAPI avec mocks et headers d'authentification"""
    from app.modules.interventions.router_v2 import _get_service

    # Remplacer les dépendances par les mocks
    app.dependency_overrides[get_saas_context] = mock_get_saas_context
    app.dependency_overrides[_get_service] = lambda: mock_interventions_service

    class TestClientWithHeaders(TestClient):
        """TestClient qui ajoute automatiquement les headers requis."""

        def request(self, method: str, url: str, **kwargs):
            headers = kwargs.get("headers") or {}
            if "X-Tenant-ID" not in headers:
                headers["X-Tenant-ID"] = tenant_id
            if "Authorization" not in headers:
                headers["Authorization"] = f"Bearer mock-jwt-{user_id}"
            kwargs["headers"] = headers
            return super().request(method, url, **kwargs)

    client = TestClientWithHeaders(app)
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
    """Instance donneur d'ordre sample (MockEntity pour compatibilité serializer)"""
    now = datetime.utcnow()
    data = {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        **donneur_ordre_data,
        "created_at": now,  # datetime, pas string
        "updated_at": now,  # datetime, pas string
    }
    return MockEntity(data)


@pytest.fixture
def donneur_ordre_list(donneur_ordre_data, tenant_id):
    """Liste de donneurs d'ordre sample (MockEntity pour compatibilité serializer)"""
    now = datetime.utcnow()
    base_data = {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        **donneur_ordre_data,
        "created_at": now,
        "updated_at": now,
    }
    second_data = {
        **base_data,
        "id": str(uuid4()),
        "nom": "Client Secondaire",
        "email": "contact@client2.com",
    }
    return [MockEntity(base_data), MockEntity(second_data)]


# ============================================================================
# FIXTURES DONNÉES INTERVENTION
# ============================================================================

@pytest.fixture
def intervention_data():
    """Données d'intervention sample.

    Utilise les noms de champs exacts du modèle Intervention.
    """
    return {
        "titre": "Installation équipement",
        "description": "Installation d'un nouveau système",
        "client_id": str(uuid4()),
        "donneur_ordre_id": str(uuid4()),
        "projet_id": str(uuid4()),
        "priorite": InterventionPriorite.NORMAL,
        "type_intervention": TypeIntervention.INSTALLATION,
        "reference_externe": "EXT-2024-001",
        # Adresse - noms de champs du modèle
        "adresse_ligne1": "456 Avenue des Champs",
        "adresse_ligne2": None,
        "code_postal": "75008",
        "ville": "Paris",
        "contact_site_nom": "Marie Martin",
        "contact_site_telephone": "+33198765432",
        "duree_prevue_minutes": 120,
    }


@pytest.fixture
def intervention_dict(intervention_data, tenant_id, user_id):
    """Données brutes d'intervention (dict) pour construction d'autres fixtures.

    Utilise les Enums appropriés pour simuler le comportement des modèles SQLAlchemy.
    Les dates sont des objets datetime (pas des chaînes ISO).
    """
    now = datetime.utcnow()
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "reference": "INT-2024-0001",
        "statut": InterventionStatut.A_PLANIFIER,
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
        "donneur_ordre": None,  # Relation pour serializer
        "rapport": None,  # Relation pour serializer
        "corps_etat": None,  # CorpsEtat optionnel
        "created_by": user_id,
        "created_at": now,  # datetime, pas string
        "updated_at": now,  # datetime, pas string
        "deleted_at": None,
    }


@pytest.fixture
def intervention(intervention_dict):
    """Instance intervention sample (MockEntity pour compatibilité serializer)"""
    return MockEntity(intervention_dict)


@pytest.fixture
def intervention_planifiee(intervention_dict, user_id):
    """Intervention planifiée sample (MockEntity pour compatibilité serializer)"""
    now = datetime.utcnow()
    data = {
        **intervention_dict,
        "statut": InterventionStatut.PLANIFIEE,
        "intervenant_id": user_id,
        "date_prevue_debut": now + timedelta(hours=1),  # datetime pour calcul delta
        "date_prevue_fin": now + timedelta(hours=3),
        "planning_event_id": str(uuid4()),
    }
    return MockEntity(data)


@pytest.fixture
def intervention_en_cours(intervention_dict, user_id):
    """Intervention en cours sample (MockEntity pour compatibilité serializer)"""
    now = datetime.utcnow()
    data = {
        **intervention_dict,
        "statut": InterventionStatut.EN_COURS,
        "intervenant_id": user_id,
        "date_prevue_debut": now - timedelta(hours=1),
        "date_prevue_fin": now + timedelta(hours=1),
        "date_arrivee_site": now,
        "date_demarrage": now + timedelta(minutes=5),
        "geoloc_arrivee_lat": 48.8566,
        "geoloc_arrivee_lng": 2.3522,
        "planning_event_id": str(uuid4()),
    }
    return MockEntity(data)


@pytest.fixture
def intervention_terminee(intervention_dict, user_id):
    """Intervention terminée sample (MockEntity pour compatibilité serializer)"""
    now = datetime.utcnow()
    data = {
        **intervention_dict,
        "statut": InterventionStatut.TERMINEE,
        "intervenant_id": user_id,
        "date_prevue_debut": now - timedelta(hours=3),
        "date_prevue_fin": now - timedelta(hours=1),
        "date_arrivee_site": now - timedelta(hours=3),
        "date_demarrage": now - timedelta(hours=2, minutes=55),
        "date_fin": now - timedelta(hours=1),
        "duree_reelle_minutes": 115,
        "geoloc_arrivee_lat": 48.8566,
        "geoloc_arrivee_lng": 2.3522,
        "planning_event_id": str(uuid4()),
    }
    return MockEntity(data)


@pytest.fixture
def intervention_list(intervention_dict, user_id):
    """Liste d'interventions sample (MockEntity pour compatibilité serializer)"""
    now = datetime.utcnow()
    intervention1 = MockEntity(intervention_dict)
    intervention2_data = {
        **intervention_dict,
        "id": str(uuid4()),
        "reference": "INT-2024-0002",
        "statut": InterventionStatut.PLANIFIEE,
        "intervenant_id": user_id,
        "date_prevue_debut": now + timedelta(hours=1),
        "date_prevue_fin": now + timedelta(hours=3),
        "planning_event_id": str(uuid4()),
    }
    return [intervention1, MockEntity(intervention2_data)]


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
def rapport_intervention(intervention_dict, tenant_id):
    """Instance rapport intervention sample (MockEntity pour compatibilité serializer)"""
    now = datetime.utcnow()
    data = {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "intervention_id": intervention_dict["id"],
        "reference_intervention": intervention_dict["reference"],
        "client_id": intervention_dict["client_id"],
        "donneur_ordre_id": intervention_dict["donneur_ordre_id"],
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
        "created_at": now,  # datetime, pas string
        "updated_at": now,  # datetime, pas string
    }
    return MockEntity(data)


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
def rapport_final_dict(rapport_final_data, tenant_id, user_id):
    """Données brutes de rapport final (dict) pour construction d'autres fixtures.

    Les dates sont des objets datetime (pas des chaînes ISO).
    """
    now = datetime.utcnow()
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "reference": "RFINAL-2024-0001",
        "projet_id": rapport_final_data["projet_id"],
        "donneur_ordre_id": rapport_final_data["donneur_ordre_id"],
        "interventions_references": ["INT-2024-0001", "INT-2024-0002"],
        "temps_total_minutes": 240,
        "synthese": rapport_final_data["synthese"],
        "date_generation": now,  # datetime, pas string
        "is_locked": True,
        "created_by": user_id,
        "created_at": now,  # datetime, pas string
        "updated_at": now,  # datetime, pas string
    }


@pytest.fixture
def rapport_final(rapport_final_dict):
    """Instance rapport final sample (MockEntity pour compatibilité serializer)"""
    return MockEntity(rapport_final_dict)


@pytest.fixture
def rapport_final_list(rapport_final_dict):
    """Liste de rapports finaux sample (MockEntity pour compatibilité serializer)"""
    second_data = {
        **rapport_final_dict,
        "id": str(uuid4()),
        "reference": "RFINAL-2024-0002",
        "temps_total_minutes": 180,
    }
    return [MockEntity(rapport_final_dict), MockEntity(second_data)]


# ============================================================================
# FIXTURES STATISTIQUES
# ============================================================================

@pytest.fixture
def intervention_stats():
    """Statistiques interventions sample (MockEntity pour compatibilité serializer)"""
    data = {
        "total": 100,
        "a_planifier": 20,
        "planifiees": 30,
        "en_cours": 10,
        "terminees": 40,
        "duree_moyenne_minutes": 125.5,
    }
    return MockEntity(data)
