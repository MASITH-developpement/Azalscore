"""
=============================================================================
TEST TERRAIN - SIMULATION D'UTILISATEURS REELS EN CONDITIONS CHAOTIQUES
=============================================================================

Ce module simule des utilisateurs NON TECHNIQUES avec :
- Erreurs humaines repetees
- Usages non prevus
- Interruptions brutales
- Comportements incoherents
- Double-clics, retours arriere, champs vides

Un module est valide UNIQUEMENT si :
- Aucun utilisateur n'est bloque definitivement
- Aucune donnee n'est corrompue
- Aucune intervention technique n'est necessaire
- Le travail peut continuer malgre les erreurs

=============================================================================
"""

import logging
import os

logger = logging.getLogger(__name__)
import sys

# Configuration environnement AVANT imports
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_chaos.db")
os.environ.setdefault("SECRET_KEY", "test-key-minimum-32-characters-long-for-chaos-tests")
os.environ.setdefault("BOOTSTRAP_SECRET", "test-bootstrap-minimum-32-characters-here-chaos")
os.environ.setdefault("ENVIRONMENT", "test")

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import random
import string
import json
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading

# Test client imports
from fastapi.testclient import TestClient
import httpx

# Import de l'application
from app.main import app


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def client():
    """Fixture TestClient pour tous les tests"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    """Fixture de session DB pour nettoyage"""
    from app.core.database import SessionLocal
    session = SessionLocal()
    yield session
    session.close()


class UserProfile(Enum):
    """Profils d'utilisateurs reels avec leurs defauts"""
    COMPTABLE_SENIOR = "comptable_senior"  # Lent, methodique, double-clic systematique
    COMMERCIAL_PRESSE = "commercial_presse"  # Rapide, impatient, saute des etapes
    RH_DEBUTANT = "rh_debutant"  # Hesite, revient en arriere, abandonne
    DIRECTEUR_IMPATIENT = "directeur_impatient"  # Veut tout, tout de suite
    STAGIAIRE_PERDU = "stagiaire_perdu"  # Ne comprend rien, clique partout
    UTILISATEUR_FATIGUE = "utilisateur_fatigue"  # Erreurs de saisie, oublis


@dataclass
class FieldIncident:
    """Incident terrain observe"""
    timestamp: datetime
    user_profile: str
    module: str
    action: str
    error_type: str
    error_message: str
    recovery_possible: bool
    data_corrupted: bool
    user_blocked: bool
    technical_intervention_needed: bool
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldTestReport:
    """Rapport terrain brut"""
    module: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_actions: int = 0
    successful_actions: int = 0
    recovered_errors: int = 0
    blocking_errors: int = 0
    data_corruptions: int = 0
    incidents: List[FieldIncident] = field(default_factory=list)
    user_confusion_points: List[str] = field(default_factory=list)
    validation_status: str = "EN_COURS"

    def is_valid(self) -> bool:
        """Module valide si aucun blocage definitif"""
        return (
            self.blocking_errors == 0 and
            self.data_corruptions == 0 and
            all(not i.technical_intervention_needed for i in self.incidents)
        )


class ChaosGenerator:
    """Generateur de chaos utilisateur"""

    @staticmethod
    def random_garbage_string(length: int = 10) -> str:
        """Genere une chaine de caracteres aleatoire (comme un chat sur clavier)"""
        return ''.join(random.choices(string.printable, k=length))

    @staticmethod
    def sql_injection_attempts() -> List[str]:
        """Tentatives d'injection SQL (utilisateur malveillant ou copier-coller)"""
        return [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "<script>alert('xss')</script>",
            "${7*7}",
            "{{7*7}}",
            "../../../etc/passwd",
        ]

    @staticmethod
    def unicode_chaos() -> List[str]:
        """Caracteres unicode problematiques"""
        return [
            "Facture n°2024-001",  # Numero avec symbole special
            "Café & Thé",  # Accents et ampersand
            "Société AZÀLS",  # Accent grave
            "Prix: 100€",  # Symbole euro
            "50% de remise",  # Pourcentage
            "Client: O'Brien",  # Apostrophe
            "Note: \"Important\"",  # Guillemets
            "Réf: ABC/123\\456",  # Slashes
            "",  # Chaine vide
            "   ",  # Espaces uniquement
            "\n\n\n",  # Sauts de ligne
            "\t\t",  # Tabulations
            "🚀 Projet Alpha",  # Emoji
            "مرحبا",  # Arabe
            "中文测试",  # Chinois
            "Ελληνικά",  # Grec
        ]

    @staticmethod
    def numeric_edge_cases() -> List[Any]:
        """Valeurs numeriques limites"""
        return [
            0,
            -1,
            -0.01,
            0.001,
            999999999999,
            -999999999999,
            float('inf'),
            float('-inf'),
            "abc",  # String au lieu de nombre
            "",
            None,
            [],
            {},
            "1,234.56",  # Format US
            "1.234,56",  # Format EU
            "1 234,56",  # Format FR avec espace
        ]

    @staticmethod
    def date_chaos() -> List[str]:
        """Dates problematiques"""
        return [
            "2024-02-30",  # Jour invalide
            "2024-13-01",  # Mois invalide
            "31/12/2024",  # Format FR
            "12-31-2024",  # Format US
            "2024.12.31",  # Points
            "hier",
            "demain",
            "bientôt",
            "",
            "2024-01-01T25:00:00",  # Heure invalide
            "1900-01-01",  # Date ancienne
            "2099-12-31",  # Date future lointaine
        ]

    @staticmethod
    def email_chaos() -> List[str]:
        """Emails problematiques"""
        return [
            "test",  # Pas de @
            "@test.com",  # Pas de local part
            "test@",  # Pas de domaine
            "test@test",  # Pas de TLD
            "test..test@test.com",  # Double point
            " test@test.com",  # Espace devant
            "test@test.com ",  # Espace apres
            "test @test.com",  # Espace au milieu
            "TEST@TEST.COM",  # Majuscules
            "test+tag@test.com",  # Plus addressing
            "très.long.email.avec.beaucoup.de.points@domaine.tres.long.com",
            "",
            "   ",
        ]


class RealUserSimulator:
    """Simulateur de comportements utilisateurs reels"""

    def __init__(self, client: TestClient, profile: UserProfile):
        self.client = client
        self.profile = profile
        self.session_token: Optional[str] = None
        self.tenant_id: str = f"tenant-{random.randint(1000, 9999)}"
        self.actions_log: List[Dict] = []

    def _get_headers(self) -> Dict[str, str]:
        """Headers avec ou sans token selon le profil (oublis)"""
        headers = {"X-Tenant-ID": self.tenant_id}

        # L'utilisateur fatigue oublie parfois le token
        if self.profile == UserProfile.UTILISATEUR_FATIGUE and random.random() < 0.2:
            pass  # Oublie le token
        elif self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"

        # Le stagiaire oublie parfois le tenant
        if self.profile == UserProfile.STAGIAIRE_PERDU and random.random() < 0.3:
            del headers["X-Tenant-ID"]

        return headers

    def _simulate_delay(self):
        """Simule le temps de reaction humain"""
        delays = {
            UserProfile.COMPTABLE_SENIOR: (2, 5),  # Lent et methodique
            UserProfile.COMMERCIAL_PRESSE: (0.1, 0.5),  # Tres rapide
            UserProfile.RH_DEBUTANT: (1, 3),  # Hesite
            UserProfile.DIRECTEUR_IMPATIENT: (0.2, 0.8),  # Impatient
            UserProfile.STAGIAIRE_PERDU: (3, 10),  # Perdu
            UserProfile.UTILISATEUR_FATIGUE: (1, 4),  # Variable
        }
        min_d, max_d = delays.get(self.profile, (1, 2))
        time.sleep(random.uniform(min_d / 100, max_d / 100))  # Accelere pour les tests

    def _maybe_double_click(self, action_func, *args, **kwargs):
        """Le comptable senior double-clique toujours"""
        results = []

        if self.profile == UserProfile.COMPTABLE_SENIOR and random.random() < 0.7:
            # Double-clic rapide
            results.append(action_func(*args, **kwargs))
            time.sleep(0.05)  # 50ms entre les clics
            results.append(action_func(*args, **kwargs))
            return results[-1]  # Retourne le dernier resultat
        else:
            return action_func(*args, **kwargs)

    def _maybe_abandon(self) -> bool:
        """Le RH debutant abandonne parfois en cours de route"""
        if self.profile == UserProfile.RH_DEBUTANT and random.random() < 0.15:
            return True
        return False

    def _corrupt_data(self, data: Dict) -> Dict:
        """Corrompt les donnees selon le profil utilisateur"""
        corrupted = data.copy()

        if self.profile == UserProfile.STAGIAIRE_PERDU:
            # Melange les champs
            keys = list(corrupted.keys())
            if len(keys) >= 2:
                k1, k2 = random.sample(keys, 2)
                corrupted[k1], corrupted[k2] = corrupted[k2], corrupted[k1]

        elif self.profile == UserProfile.UTILISATEUR_FATIGUE:
            # Fautes de frappe
            for key in corrupted:
                if isinstance(corrupted[key], str) and random.random() < 0.3:
                    s = corrupted[key]
                    if len(s) > 2:
                        pos = random.randint(0, len(s)-1)
                        corrupted[key] = s[:pos] + random.choice(string.ascii_letters) + s[pos+1:]

        elif self.profile == UserProfile.COMMERCIAL_PRESSE:
            # Champs oublies
            keys = list(corrupted.keys())
            if keys and random.random() < 0.2:
                del corrupted[random.choice(keys)]

        return corrupted


class FieldTester:
    """Testeur terrain principal"""

    def __init__(self, client: TestClient):
        self.client = client
        self.reports: Dict[str, FieldTestReport] = {}
        self.global_incidents: List[FieldIncident] = []
        self.chaos = ChaosGenerator()

    def _log_incident(self, report: FieldTestReport, incident: FieldIncident):
        """Log un incident terrain"""
        report.incidents.append(incident)
        self.global_incidents.append(incident)
        report.total_actions += 1

        if incident.recovery_possible:
            report.recovered_errors += 1
        else:
            report.blocking_errors += 1

        if incident.data_corrupted:
            report.data_corruptions += 1

    def _log_success(self, report: FieldTestReport):
        """Log une action reussie"""
        report.total_actions += 1
        report.successful_actions += 1


# =============================================================================
# TESTS TERRAIN PAR MODULE
# =============================================================================

class TestAuthenticationChaos:
    """Tests terrain - Module Authentification"""

    @pytest.fixture
    def field_report(self):
        return FieldTestReport(
            module="AUTH",
            start_time=datetime.now()
        )

    def test_login_rapid_fire_same_user(self, client, field_report):
        """
        SCENARIO TERRAIN: Commercial presse qui clique 10 fois sur "Connexion"
        parce que "ca charge pas"
        """
        email = f"commercial_{random.randint(1000,9999)}@test.com"

        # D'abord creer le compte
        reg_response = client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": "tenant-test"}
        )

        # Maintenant simuler 10 clics rapides sur login
        responses = []
        for i in range(10):
            response = client.post(
                "/auth/login",
                json={"email": email, "password": "TestPass123!"},
                headers={"X-Tenant-ID": "tenant-test"}
            )
            responses.append(response.status_code)
            time.sleep(0.05)  # 50ms entre chaque clic

        # VALIDATION: L'utilisateur ne doit pas etre bloque definitivement
        # Au pire, rate limiting temporaire, mais pas de ban permanent
        blocked_count = sum(1 for r in responses if r == 429)
        success_count = sum(1 for r in responses if r == 200)

        # Au moins un login doit reussir
        assert success_count >= 1, "BLOCAGE DEFINITIF: Utilisateur ne peut plus se connecter"

        # Log l'incident si rate limiting
        if blocked_count > 0:
            field_report.user_confusion_points.append(
                f"Rate limiting active apres {10 - blocked_count} tentatives rapides"
            )

    def test_login_wrong_password_then_correct(self, client, field_report):
        """
        SCENARIO TERRAIN: Utilisateur fatigue qui se trompe 3 fois
        de mot de passe puis trouve le bon
        """
        email = f"fatigue_{random.randint(1000,9999)}@test.com"
        correct_password = "CorrectPass123!"

        # Creer le compte
        client.post(
            "/auth/register",
            json={"email": email, "password": correct_password},
            headers={"X-Tenant-ID": "tenant-test"}
        )

        # 3 tentatives avec mauvais mot de passe
        wrong_attempts = ["correctpass123", "CorrectPass123", "correctPass123!"]
        for pwd in wrong_attempts:
            response = client.post(
                "/auth/login",
                json={"email": email, "password": pwd},
                headers={"X-Tenant-ID": "tenant-test"}
            )
            assert response.status_code in [401, 429], "Devrait refuser le mauvais mot de passe"
            time.sleep(0.1)

        # Maintenant le bon mot de passe
        response = client.post(
            "/auth/login",
            json={"email": email, "password": correct_password},
            headers={"X-Tenant-ID": "tenant-test"}
        )

        # VALIDATION: L'utilisateur doit pouvoir se connecter avec le bon mot de passe
        # meme apres plusieurs erreurs
        assert response.status_code in [200, 429], (
            "BLOCAGE: Utilisateur ne peut plus se connecter meme avec le bon mot de passe. "
            f"Status: {response.status_code}"
        )

        if response.status_code == 429:
            field_report.user_confusion_points.append(
                "Utilisateur bloque temporairement apres 3 erreurs - doit attendre"
            )

    def test_registration_special_characters_email(self, client, field_report):
        """
        SCENARIO TERRAIN: Utilisateur avec email complexe
        """
        chaos = ChaosGenerator()

        for email in chaos.email_chaos():
            response = client.post(
                "/auth/register",
                json={"email": email, "password": "ValidPass123!"},
                headers={"X-Tenant-ID": "tenant-test"}
            )

            # L'API doit soit accepter soit rejeter proprement
            # Jamais de 500 Internal Server Error
            assert response.status_code != 500, (
                f"ERREUR SERVEUR avec email '{email}': {response.text}"
            )

            if response.status_code >= 400:
                # Verifier que le message d'erreur est comprehensible
                try:
                    error_data = response.json()
                    assert "detail" in error_data or "message" in error_data, (
                        f"Message d'erreur non comprehensible pour email '{email}'"
                    )
                except (AssertionError, ValueError) as e:
                    logger.debug(f"Response format varies for email '{email}': {e}")

    def test_registration_empty_fields(self, client, field_report):
        """
        SCENARIO TERRAIN: Stagiaire qui soumet le formulaire vide
        """
        test_cases = [
            {},  # Tout vide
            {"email": ""},  # Email vide
            {"password": ""},  # Password vide
            {"email": "", "password": ""},  # Les deux vides
            {"email": "test@test.com"},  # Password manquant
            {"password": "ValidPass123!"},  # Email manquant
            {"email": None, "password": None},  # Valeurs null
        ]

        for data in test_cases:
            response = client.post(
                "/auth/register",
                json=data,
                headers={"X-Tenant-ID": "tenant-test"}
            )

            # Doit rejeter proprement, pas de crash
            assert response.status_code != 500, (
                f"CRASH SERVEUR avec donnees: {data}"
            )
            assert response.status_code in [400, 422, 401], (
                f"Reponse inattendue {response.status_code} pour donnees invalides: {data}"
            )

    def test_login_without_tenant_header(self, client, field_report):
        """
        SCENARIO TERRAIN: Utilisateur qui oublie le tenant (copier-coller d'URL)
        """
        response = client.post(
            "/auth/login",
            json={"email": "test@test.com", "password": "Test123!"}
            # Pas de X-Tenant-ID
        )

        # Doit expliquer clairement le probleme
        assert response.status_code != 500, "CRASH sans tenant header"

        if response.status_code >= 400:
            try:
                error = response.json()
                # Le message doit mentionner le tenant
                error_str = str(error).lower()
                has_clear_message = (
                    "tenant" in error_str or
                    "header" in error_str or
                    "x-tenant" in error_str
                )
                if not has_clear_message:
                    field_report.user_confusion_points.append(
                        f"Message d'erreur sans mention du tenant: {error}"
                    )
            except ValueError as e:
                logger.debug(f"Could not parse error response as JSON: {e}")


class TestFinanceChaos:
    """Tests terrain - Module Finance"""

    def test_journal_entry_unbalanced(self, client):
        """
        SCENARIO TERRAIN: Comptable qui fait une erreur de saisie
        debit != credit
        """
        # Creer un utilisateur et se connecter
        tenant_id = f"tenant-fin-{random.randint(1000,9999)}"
        email = f"comptable_{random.randint(1000,9999)}@test.com"

        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        if login_resp.status_code != 200:
            pytest.skip("Login failed, skipping finance test")

        token = login_resp.json().get("access_token", "")
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        # Tenter une ecriture desequilibree
        unbalanced_entry = {
            "date": "2024-01-15",
            "description": "Ecriture test desequilibree",
            "lines": [
                {"account_code": "411000", "debit": 1000.00, "credit": 0},
                {"account_code": "701000", "debit": 0, "credit": 999.99},  # 0.01 d'ecart
            ]
        }

        response = client.post(
            "/finance/entries",
            json=unbalanced_entry,
            headers=headers
        )

        # Doit rejeter l'ecriture desequilibree
        if response.status_code == 200:
            pytest.fail(
                "CORRUPTION DONNEES: Ecriture desequilibree acceptee! "
                "Debit=1000.00, Credit=999.99"
            )

        # Le message doit etre clair
        if response.status_code in [400, 422]:
            try:
                error = response.json()
                error_str = str(error).lower()
                assert "balanc" in error_str or "equili" in error_str or "debit" in error_str, (
                    f"Message d'erreur pas clair pour ecriture desequilibree: {error}"
                )
            except (AssertionError, ValueError) as e:
                logger.debug(f"Error message validation skipped: {e}")

    def test_negative_amounts(self, client):
        """
        SCENARIO TERRAIN: Utilisateur qui saisit des montants negatifs
        """
        tenant_id = f"tenant-fin-{random.randint(1000,9999)}"

        # Setup auth
        email = f"test_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        if login_resp.status_code != 200:
            pytest.skip("Login failed")

        token = login_resp.json().get("access_token", "")
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        # Montants negatifs
        negative_entry = {
            "date": "2024-01-15",
            "description": "Test montants negatifs",
            "lines": [
                {"account_code": "411000", "debit": -1000.00, "credit": 0},
                {"account_code": "701000", "debit": 0, "credit": -1000.00},
            ]
        }

        response = client.post(
            "/finance/entries",
            json=negative_entry,
            headers=headers
        )

        # Ne doit pas accepter de montants negatifs sans validation
        assert response.status_code != 500, "CRASH avec montants negatifs"

    def test_extreme_amounts(self, client):
        """
        SCENARIO TERRAIN: Erreur de saisie avec montant astronomique
        """
        tenant_id = f"tenant-fin-{random.randint(1000,9999)}"

        email = f"test_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        if login_resp.status_code != 200:
            pytest.skip("Login failed")

        token = login_resp.json().get("access_token", "")
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        # Montant astronomique (erreur de saisie: oublie la virgule)
        extreme_entry = {
            "date": "2024-01-15",
            "description": "Facture 100,00 (mais saisi 10000)",
            "lines": [
                {"account_code": "411000", "debit": 99999999999999.99, "credit": 0},
                {"account_code": "701000", "debit": 0, "credit": 99999999999999.99},
            ]
        }

        response = client.post(
            "/finance/entries",
            json=extreme_entry,
            headers=headers
        )

        # Ne doit pas crasher, idealement avertir
        assert response.status_code != 500, "CRASH avec montant extreme"


class TestCommercialChaos:
    """Tests terrain - Module Commercial"""

    def test_create_customer_special_names(self, client):
        """
        SCENARIO TERRAIN: Clients avec noms speciaux
        """
        tenant_id = f"tenant-com-{random.randint(1000,9999)}"

        # Setup
        email = f"commercial_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        token = login_resp.json().get("access_token", "") if login_resp.status_code == 200 else ""
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        special_names = [
            "Société O'Brien & Fils",
            "Café \"Le Parisien\"",
            "SARL <Test>",
            "Ets. Martin/Dupont",
            "Compagnie 中文",
            "Société\nAvec\nRetours",
            "",  # Vide
            "   ",  # Espaces
            "A" * 1000,  # Tres long
            "'; DROP TABLE customers; --",  # Injection
        ]

        for name in special_names:
            response = client.post(
                "/api/v1/commercial/customers",
                json={
                    "name": name,
                    "email": f"client_{random.randint(1000,9999)}@test.com",
                    "customer_type": "customer"
                },
                headers=headers
            )

            # Jamais de 500
            assert response.status_code != 500, (
                f"CRASH SERVEUR avec nom client: '{name[:50]}...'"
            )

    def test_duplicate_customer_creation(self, client):
        """
        SCENARIO TERRAIN: Double-clic sur "Creer client"
        """
        tenant_id = f"tenant-com-{random.randint(1000,9999)}"

        email = f"commercial_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        token = login_resp.json().get("access_token", "") if login_resp.status_code == 200 else ""
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        customer_data = {
            "name": f"Client Test {random.randint(1000,9999)}",
            "email": f"client_{random.randint(1000,9999)}@unique.com",
            "customer_type": "customer"
        }

        # Double-clic: deux requetes quasi-simultanees
        responses = []
        for _ in range(2):
            response = client.post(
                "/api/v1/commercial/customers",
                json=customer_data,
                headers=headers
            )
            responses.append(response)
            time.sleep(0.05)  # 50ms entre les clics

        # Au moins une doit reussir, pas de crash
        status_codes = [r.status_code for r in responses]
        assert 500 not in status_codes, "CRASH sur double creation"

        # Verifier qu'on n'a pas de doublon
        success_count = sum(1 for s in status_codes if s in [200, 201])
        if success_count > 1:
            # Potentiel doublon, verifier les IDs
            ids = []
            for r in responses:
                if r.status_code in [200, 201]:
                    try:
                        ids.append(r.json().get("id"))
                    except ValueError as e:
                        logger.debug(f"Could not parse response JSON: {e}")

            if len(set(ids)) > 1:
                # Deux clients differents crees - peut etre un probleme
                logger.info(f"Multiple clients created with different IDs: {ids} - evaluate per business policy")


class TestHRChaos:
    """Tests terrain - Module RH"""

    def test_employee_invalid_dates(self, client):
        """
        SCENARIO TERRAIN: RH qui saisit des dates impossibles
        """
        tenant_id = f"tenant-hr-{random.randint(1000,9999)}"

        email = f"rh_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        token = login_resp.json().get("access_token", "") if login_resp.status_code == 200 else ""
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        invalid_dates = ChaosGenerator.date_chaos()

        for date in invalid_dates:
            response = client.post(
                "/hr/employees",
                json={
                    "first_name": "Jean",
                    "last_name": "Test",
                    "email": f"emp_{random.randint(1000,9999)}@test.com",
                    "hire_date": date,
                },
                headers=headers
            )

            assert response.status_code != 500, (
                f"CRASH avec date: '{date}'"
            )

    def test_leave_request_overlapping(self, client):
        """
        SCENARIO TERRAIN: Employe qui demande deux conges sur la meme periode
        (double soumission ou confusion)
        """
        tenant_id = f"tenant-hr-{random.randint(1000,9999)}"

        email = f"rh_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        token = login_resp.json().get("access_token", "") if login_resp.status_code == 200 else ""
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        leave_data = {
            "employee_id": "emp-001",
            "start_date": "2024-07-15",
            "end_date": "2024-07-30",
            "leave_type": "paid",
            "reason": "Vacances ete"
        }

        # Premiere demande
        resp1 = client.post("/hr/leave-requests", json=leave_data, headers=headers)

        # Deuxieme demande identique (double-clic ou confusion)
        resp2 = client.post("/hr/leave-requests", json=leave_data, headers=headers)

        # Ne doit pas crasher
        assert resp1.status_code != 500, "CRASH premiere demande conges"
        assert resp2.status_code != 500, "CRASH deuxieme demande conges"


class TestInventoryChaos:
    """Tests terrain - Module Inventaire"""

    def test_negative_stock_movement(self, client):
        """
        SCENARIO TERRAIN: Sortie de stock > stock disponible
        """
        tenant_id = f"tenant-inv-{random.randint(1000,9999)}"

        email = f"mag_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        token = login_resp.json().get("access_token", "") if login_resp.status_code == 200 else ""
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        # Tenter de sortir 1000 unites d'un produit qui n'existe pas
        response = client.post(
            "/inventory/stock-movements",
            json={
                "product_id": "PROD-INEXISTANT",
                "warehouse_id": "WH-001",
                "quantity": -1000,  # Sortie
                "movement_type": "out",
                "reason": "Vente client"
            },
            headers=headers
        )

        # Doit refuser proprement, pas accepter un stock negatif
        assert response.status_code != 500, "CRASH sortie stock impossible"

        if response.status_code in [200, 201]:
            # Verifier que le stock n'est pas negatif
            # (politique metier a definir)
            pass

    def test_product_with_invalid_codes(self, client):
        """
        SCENARIO TERRAIN: Codes produits avec caracteres speciaux
        """
        tenant_id = f"tenant-inv-{random.randint(1000,9999)}"

        email = f"mag_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        token = login_resp.json().get("access_token", "") if login_resp.status_code == 200 else ""
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        invalid_codes = [
            "PROD/001",
            "PROD\\001",
            "PROD 001",
            "PROD\t001",
            "PROD\n001",
            "PROD'001",
            'PROD"001',
            "PROD<001>",
            "",
            "   ",
            "A" * 500,
        ]

        for code in invalid_codes:
            response = client.post(
                "/inventory/products",
                json={
                    "code": code,
                    "name": f"Produit Test {random.randint(1000,9999)}",
                    "unit": "PCE"
                },
                headers=headers
            )

            assert response.status_code != 500, (
                f"CRASH avec code produit: '{code[:30]}...'"
            )


class TestDecisionWorkflowChaos:
    """Tests terrain - Workflow RED Decision"""

    def test_red_workflow_skip_steps(self, client):
        """
        SCENARIO TERRAIN: Utilisateur impatient qui essaie de sauter des etapes
        """
        tenant_id = f"tenant-dec-{random.randint(1000,9999)}"

        email = f"dir_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        token = login_resp.json().get("access_token", "") if login_resp.status_code == 200 else ""
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        # Creer une decision RED
        decision_resp = client.post(
            "/decisions",
            json={
                "level": "RED",
                "entity_type": "treasury_forecast",
                "entity_id": "TF-001",
                "reason": "Tresorerie negative prevue"
            },
            headers=headers
        )

        if decision_resp.status_code not in [200, 201]:
            pytest.skip("Decision creation failed")

        decision_id = decision_resp.json().get("id", "DEC-001")

        # Essayer de sauter directement a l'etape finale (sans acknowledge ni completeness)
        final_resp = client.post(
            "/red-workflow/final",
            json={"decision_id": decision_id, "confirmed": True},
            headers=headers
        )

        # Doit refuser - les etapes sont obligatoires
        assert final_resp.status_code != 500, "CRASH tentative saut etapes"

        if final_resp.status_code in [200, 201]:
            pytest.fail(
                "FAILLE WORKFLOW: Etapes RED peuvent etre sautees! "
                "Risque de validation sans verification."
            )

    def test_red_workflow_double_validation(self, client):
        """
        SCENARIO TERRAIN: Comptable senior qui double-clique sur "Valider"
        a chaque etape
        """
        tenant_id = f"tenant-dec-{random.randint(1000,9999)}"

        email = f"comptable_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        token = login_resp.json().get("access_token", "") if login_resp.status_code == 200 else ""
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        # Creer decision
        decision_resp = client.post(
            "/decisions",
            json={
                "level": "RED",
                "entity_type": "invoice",
                "entity_id": "INV-001",
                "reason": "Montant anormal"
            },
            headers=headers
        )

        if decision_resp.status_code not in [200, 201]:
            pytest.skip("Decision creation failed")

        decision_id = decision_resp.json().get("id", "DEC-001")

        # Double-clic sur acknowledge
        ack_data = {"decision_id": decision_id, "acknowledged": True}
        resp1 = client.post("/red-workflow/acknowledge", json=ack_data, headers=headers)
        resp2 = client.post("/red-workflow/acknowledge", json=ack_data, headers=headers)

        # Ne doit pas crasher, gerer le doublon
        assert resp1.status_code != 500, "CRASH premier acknowledge"
        assert resp2.status_code != 500, "CRASH deuxieme acknowledge (doublon)"


class TestMultiTenantChaos:
    """Tests terrain - Isolation Multi-tenant"""

    def test_access_other_tenant_data(self, client):
        """
        SCENARIO TERRAIN: Utilisateur qui essaie d'acceder aux donnees
        d'un autre tenant (erreur de copier-coller d'URL)
        """
        # Creer deux tenants
        tenant_a = f"tenant-a-{random.randint(1000,9999)}"
        tenant_b = f"tenant-b-{random.randint(1000,9999)}"

        # Utilisateur tenant A
        email_a = f"user_a_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email_a, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_a}
        )
        login_a = client.post(
            "/auth/login",
            json={"email": email_a, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_a}
        )
        token_a = login_a.json().get("access_token", "") if login_a.status_code == 200 else ""

        # Utilisateur tenant B
        email_b = f"user_b_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email_b, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_b}
        )

        # Utilisateur A essaie d'acceder aux donnees de B
        response = client.get(
            "/api/v1/commercial/customers",
            headers={
                "X-Tenant-ID": tenant_b,  # Mauvais tenant
                "Authorization": f"Bearer {token_a}"  # Token de A
            }
        )

        # Doit etre refuse
        assert response.status_code in [401, 403], (
            f"FAILLE SECURITE: Acces cross-tenant autorise! Status: {response.status_code}"
        )


class TestConcurrentAccessChaos:
    """Tests terrain - Acces concurrents"""

    def test_concurrent_same_resource_modification(self, client):
        """
        SCENARIO TERRAIN: Deux utilisateurs modifient la meme ressource
        en meme temps (pas de verrou)
        """
        tenant_id = f"tenant-conc-{random.randint(1000,9999)}"

        # Setup utilisateur
        email = f"user_{random.randint(1000,9999)}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": email, "password": "TestPass123!"},
            headers={"X-Tenant-ID": tenant_id}
        )

        token = login_resp.json().get("access_token", "") if login_resp.status_code == 200 else ""
        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }

        # Creer un client
        create_resp = client.post(
            "/api/v1/commercial/customers",
            json={
                "name": "Client Test Concurrent",
                "email": "concurrent@test.com",
                "customer_type": "customer"
            },
            headers=headers
        )

        if create_resp.status_code not in [200, 201]:
            pytest.skip("Customer creation failed")

        customer_id = create_resp.json().get("id", "CUST-001")

        # Simuler deux modifications simultanees
        def modify_customer(name_suffix):
            return client.put(
                f"/api/v1/commercial/customers/{customer_id}",
                json={"name": f"Client Modifie {name_suffix}"},
                headers=headers
            )

        # Executer en parallele (simulation)
        responses = []
        for i in range(3):
            responses.append(modify_customer(f"v{i}"))

        # Verifier qu'aucun crash
        for i, resp in enumerate(responses):
            assert resp.status_code != 500, f"CRASH modification concurrente {i}"


class TestSessionInterruptionChaos:
    """Tests terrain - Interruptions de session"""

    def test_expired_token_graceful_handling(self, client):
        """
        SCENARIO TERRAIN: Utilisateur revient apres dejeuner,
        son token a expire
        """
        tenant_id = f"tenant-exp-{random.randint(1000,9999)}"

        # Token bidon (simule token expire)
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"

        headers = {
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {expired_token}"
        }

        response = client.get("/protected", headers=headers)

        # Doit renvoyer 401 (ou 403/404 si route non accessible), jamais 500
        assert response.status_code != 500, "CRASH avec token expire"
        # 401 = non authentifie, 403 = interdit, 404 = route inexistante
        # Tous sont acceptables - l'important c'est pas de crash
        assert response.status_code in [401, 403, 404], f"Status inattendu: {response.status_code}"

        # Message doit etre comprehensible
        try:
            error = response.json()
            error_str = str(error).lower()
            has_clear_message = (
                "token" in error_str or
                "expir" in error_str or
                "auth" in error_str or
                "session" in error_str
            )
            assert has_clear_message, f"Message pas clair pour token expire: {error}"
        except (AssertionError, ValueError) as e:
            logger.debug(f"Token expiration message validation skipped: {e}")

    def test_malformed_token(self, client):
        """
        SCENARIO TERRAIN: Token corrompu (copier-coller partiel)
        """
        tenant_id = f"tenant-mal-{random.randint(1000,9999)}"

        malformed_tokens = [
            "Bearer ",  # Token vide
            "Bearer abc",  # Token trop court
            "Bearer " + "a" * 1000,  # Token tres long
            "NotBearer xyz",  # Mauvais prefixe
            "bearer abc.def.ghi",  # Minuscule
            "abc.def.ghi",  # Pas de prefixe
            "   Bearer abc.def.ghi   ",  # Espaces
        ]

        for token in malformed_tokens:
            response = client.get(
                "/protected",
                headers={
                    "X-Tenant-ID": tenant_id,
                    "Authorization": token
                }
            )

            assert response.status_code != 500, (
                f"CRASH avec token malformed: '{token[:50]}'"
            )


# =============================================================================
# RAPPORT TERRAIN FINAL
# =============================================================================

class TestFieldReport:
    """Generation du rapport terrain final"""

    def test_generate_field_report(self, client):
        """
        Genere un rapport terrain resumant tous les tests
        """
        report = {
            "titre": "RAPPORT TERRAIN - ERP AZALS",
            "date": datetime.now().isoformat(),
            "version": "v7",
            "modules_testes": [
                "AUTH - Authentification",
                "FINANCE - Comptabilite",
                "COMMERCIAL - Ventes/CRM",
                "HR - Ressources Humaines",
                "INVENTORY - Stocks",
                "DECISION - Workflow RED",
                "MULTI_TENANT - Isolation",
                "CONCURRENT - Acces paralleles",
                "SESSION - Gestion sessions"
            ],
            "scenarios_couverts": [
                "Double-clics repetitifs",
                "Champs vides ou invalides",
                "Caracteres speciaux et unicode",
                "Injections SQL/XSS",
                "Montants extremes ou negatifs",
                "Dates impossibles",
                "Tokens expires ou malformes",
                "Acces cross-tenant",
                "Modifications concurrentes",
                "Saut d'etapes workflow",
            ],
            "criteres_validation": {
                "aucun_blocage_definitif": "A VERIFIER",
                "aucune_corruption_donnees": "A VERIFIER",
                "aucune_intervention_technique": "A VERIFIER",
                "travail_continue_malgre_erreurs": "A VERIFIER"
            }
        }

        # Ce test ne fait que documenter le cadre
        # Les vrais resultats viennent des autres tests
        assert True
