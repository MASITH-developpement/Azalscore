"""
AZALSCORE - Tests des Endpoints Signup
=======================================
Tests des routes API d'inscription.

Exécution:
    pytest tests/test_signup_router.py -v
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSignupEndpoints:
    """Tests des endpoints d'inscription."""

    # ========================================================================
    # POST /signup - INSCRIPTION
    # ========================================================================

    def test_signup_success(self, client, mock_email_service):
        """Test: inscription réussie retourne 201."""
        response = client.post("/signup/", json={
            "company_name": "Test Entreprise",
            "company_email": "contact@testentreprise.fr",
            "admin_email": "admin@testentreprise.fr",
            "admin_password": "SecurePass123!",
            "admin_first_name": "Jean",
            "admin_last_name": "Test",
            "plan": "PROFESSIONAL",
            "accept_terms": True,
            "accept_privacy": True,
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["tenant_id"] == "test-entreprise"
        assert "trial_ends_at" in data
        assert "login_url" in data

    def test_signup_missing_company_name(self, client):
        """Test: nom entreprise manquant → 422."""
        response = client.post("/signup/", json={
            "company_email": "contact@test.fr",
            "admin_email": "admin@test.fr",
            "admin_password": "SecurePass123!",
            "admin_first_name": "Jean",
            "admin_last_name": "Test",
            "accept_terms": True,
            "accept_privacy": True,
        })
        
        assert response.status_code == 422

    def test_signup_invalid_email(self, client):
        """Test: email invalide → 422."""
        response = client.post("/signup/", json={
            "company_name": "Test Company",
            "company_email": "invalid-email",
            "admin_email": "also-invalid",
            "admin_password": "SecurePass123!",
            "admin_first_name": "Jean",
            "admin_last_name": "Test",
            "accept_terms": True,
            "accept_privacy": True,
        })
        
        assert response.status_code == 422

    def test_signup_password_too_short(self, client):
        """Test: mot de passe trop court → 422."""
        response = client.post("/signup/", json={
            "company_name": "Test Company",
            "company_email": "contact@test.fr",
            "admin_email": "admin@test.fr",
            "admin_password": "short",  # < 8 caractères
            "admin_first_name": "Jean",
            "admin_last_name": "Test",
            "accept_terms": True,
            "accept_privacy": True,
        })
        
        assert response.status_code == 422

    def test_signup_password_no_uppercase(self, client):
        """Test: mot de passe sans majuscule → 422."""
        response = client.post("/signup/", json={
            "company_name": "Test Company",
            "company_email": "contact@test.fr",
            "admin_email": "admin@test.fr",
            "admin_password": "nouppercase123",  # Pas de majuscule
            "admin_first_name": "Jean",
            "admin_last_name": "Test",
            "accept_terms": True,
            "accept_privacy": True,
        })
        
        assert response.status_code == 422

    def test_signup_password_no_digit(self, client):
        """Test: mot de passe sans chiffre → 422."""
        response = client.post("/signup/", json={
            "company_name": "Test Company",
            "company_email": "contact@test.fr",
            "admin_email": "admin@test.fr",
            "admin_password": "NoDigitsHere!",  # Pas de chiffre
            "admin_first_name": "Jean",
            "admin_last_name": "Test",
            "accept_terms": True,
            "accept_privacy": True,
        })
        
        assert response.status_code == 422

    def test_signup_terms_not_accepted(self, client):
        """Test: CGV non acceptées → 422."""
        response = client.post("/signup/", json={
            "company_name": "Test Company",
            "company_email": "contact@test.fr",
            "admin_email": "admin@test.fr",
            "admin_password": "SecurePass123!",
            "admin_first_name": "Jean",
            "admin_last_name": "Test",
            "accept_terms": False,  # Non accepté
            "accept_privacy": True,
        })
        
        assert response.status_code == 422

    def test_signup_privacy_not_accepted(self, client):
        """Test: politique confidentialité non acceptée → 422."""
        response = client.post("/signup/", json={
            "company_name": "Test Company",
            "company_email": "contact@test.fr",
            "admin_email": "admin@test.fr",
            "admin_password": "SecurePass123!",
            "admin_first_name": "Jean",
            "admin_last_name": "Test",
            "accept_terms": True,
            "accept_privacy": False,  # Non accepté
        })
        
        assert response.status_code == 422

    def test_signup_duplicate_email(self, client, sample_user, mock_email_service):
        """Test: email déjà utilisé → 400."""
        response = client.post("/signup/", json={
            "company_name": "Another Company",
            "company_email": "contact@another.fr",
            "admin_email": sample_user.email,  # Email existant
            "admin_password": "SecurePass123!",
            "admin_first_name": "Jean",
            "admin_last_name": "Test",
            "accept_terms": True,
            "accept_privacy": True,
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "EMAIL_EXISTS"

    # ========================================================================
    # GET /signup/check-email - VÉRIFICATION EMAIL
    # ========================================================================

    def test_check_email_available(self, client):
        """Test: email disponible → available=true."""
        response = client.get("/signup/check-email", params={"email": "nouveau@email.fr"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert data["suggestion"] is None

    def test_check_email_taken(self, client, sample_user):
        """Test: email pris → available=false avec suggestion."""
        response = client.get("/signup/check-email", params={"email": sample_user.email})
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert data["suggestion"] is not None

    def test_check_email_invalid_format(self, client):
        """Test: format email invalide → 422."""
        response = client.get("/signup/check-email", params={"email": "not-an-email"})
        
        assert response.status_code == 422

    # ========================================================================
    # GET /signup/check-company - VÉRIFICATION NOM ENTREPRISE
    # ========================================================================

    def test_check_company_available(self, client):
        """Test: nom disponible → available=true."""
        response = client.get("/signup/check-company", params={"name": "Nouvelle Entreprise"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True

    def test_check_company_taken(self, client, sample_tenant):
        """Test: nom pris → available=false avec suggestion."""
        response = client.get("/signup/check-company", params={"name": sample_tenant.name})
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert data["suggestion"] is not None

    def test_check_company_too_short(self, client):
        """Test: nom trop court → 400."""
        response = client.get("/signup/check-company", params={"name": "A"})
        
        assert response.status_code == 400

    # ========================================================================
    # GET /signup/plans - LISTE DES PLANS
    # ========================================================================

    def test_get_plans(self, client):
        """Test: liste des plans retournée."""
        response = client.get("/signup/plans")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "plans" in data
        assert len(data["plans"]) == 3
        
        # Vérifier les plans
        plan_ids = [p["id"] for p in data["plans"]]
        assert "STARTER" in plan_ids
        assert "PROFESSIONAL" in plan_ids
        assert "ENTERPRISE" in plan_ids

    def test_get_plans_has_recommended(self, client):
        """Test: un plan est marqué comme recommandé."""
        response = client.get("/signup/plans")
        
        data = response.json()
        recommended = [p for p in data["plans"] if p["recommended"]]
        
        assert len(recommended) == 1
        assert recommended[0]["id"] == "PROFESSIONAL"

    def test_get_plans_has_trial_days(self, client):
        """Test: nombre de jours d'essai indiqué."""
        response = client.get("/signup/plans")
        
        data = response.json()
        assert data["trial_days"] == 14

    def test_get_plans_has_prices(self, client):
        """Test: les prix sont présents."""
        response = client.get("/signup/plans")
        
        data = response.json()
        for plan in data["plans"]:
            assert "price_monthly" in plan
            assert "price_yearly" in plan
            assert plan["price_monthly"] > 0
            assert plan["price_yearly"] > 0
            # Annuel doit être moins cher que 12x mensuel
            assert plan["price_yearly"] < plan["price_monthly"] * 12


class TestSignupEndpointsIntegration:
    """Tests d'intégration des endpoints signup."""

    def test_signup_then_check_email_unavailable(self, client, mock_email_service):
        """Test: après inscription, l'email n'est plus disponible."""
        email = "integration@test.fr"
        
        # 1. Vérifier disponibilité avant
        response = client.get("/signup/check-email", params={"email": email})
        assert response.json()["available"] is True
        
        # 2. Inscription
        response = client.post("/signup/", json={
            "company_name": "Integration Test",
            "company_email": "contact@integration.fr",
            "admin_email": email,
            "admin_password": "SecurePass123!",
            "admin_first_name": "Test",
            "admin_last_name": "User",
            "accept_terms": True,
            "accept_privacy": True,
        })
        assert response.status_code == 201
        
        # 3. Vérifier non-disponibilité après
        response = client.get("/signup/check-email", params={"email": email})
        assert response.json()["available"] is False

    def test_signup_returns_valid_login_url(self, client, mock_email_service):
        """Test: l'URL de connexion retournée est valide."""
        response = client.post("/signup/", json={
            "company_name": "Login URL Test",
            "company_email": "contact@loginurl.fr",
            "admin_email": "admin@loginurl.fr",
            "admin_password": "SecurePass123!",
            "admin_first_name": "Test",
            "admin_last_name": "User",
            "accept_terms": True,
            "accept_privacy": True,
        })
        
        data = response.json()
        login_url = data["login_url"]
        
        assert "/login" in login_url
        assert "tenant=" in login_url
        assert data["tenant_id"] in login_url

    def test_multiple_signups_unique_tenant_ids(self, client, mock_email_service):
        """Test: plusieurs inscriptions créent des tenant_id uniques."""
        tenant_ids = []
        
        for i in range(3):
            response = client.post("/signup/", json={
                "company_name": "Same Company Name",  # Même nom
                "company_email": f"contact{i}@unique.fr",
                "admin_email": f"admin{i}@unique.fr",
                "admin_password": "SecurePass123!",
                "admin_first_name": "Test",
                "admin_last_name": "User",
                "accept_terms": True,
                "accept_privacy": True,
            })
            
            assert response.status_code == 201
            tenant_ids.append(response.json()["tenant_id"])
        
        # Tous les tenant_id doivent être uniques
        assert len(tenant_ids) == len(set(tenant_ids))
        # Premier sans suffixe, suivants avec suffixe
        assert tenant_ids[0] == "same-company-name"
        assert tenant_ids[1] == "same-company-name-2"
        assert tenant_ids[2] == "same-company-name-3"
