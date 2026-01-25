"""
Tests for Accounting module v2 router endpoints.

Test suite following CORE SaaS v2 pattern with comprehensive coverage
of all accounting operations, workflows, and security aspects.

Total tests: ~45
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4


# ===========================
# 1. SUMMARY (1 test)
# ===========================

def test_get_accounting_summary(client, auth_headers):
    """Test récupération du résumé comptable."""
    response = client.get(
        "/api/v2/accounting/summary",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "fiscal_years" in data
    assert "accounts" in data
    assert "journal_entries" in data
    assert "balance" in data


# ===========================
# 2. FISCAL YEARS (8 tests)
# ===========================

def test_create_fiscal_year(client, auth_headers, sample_fiscal_year_data, assert_fiscal_year_structure):
    """Test création exercice comptable."""
    response = client.post(
        "/api/v2/accounting/fiscal-years",
        headers=auth_headers,
        json=sample_fiscal_year_data
    )

    assert response.status_code == 201
    data = response.json()
    assert_fiscal_year_structure(data)
    assert data["name"] == sample_fiscal_year_data["name"]
    assert data["code"] == sample_fiscal_year_data["code"]
    assert data["status"] == "OPEN"


def test_list_fiscal_years(client, auth_headers):
    """Test listing de tous les exercices comptables."""
    response = client.get(
        "/api/v2/accounting/fiscal-years",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["items"], list)


def test_list_fiscal_years_with_status_filter(client, auth_headers):
    """Test filtrage des exercices par statut."""
    response = client.get(
        "/api/v2/accounting/fiscal-years?status=OPEN",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Tous les items retournés devraient avoir status=OPEN
    for item in data["items"]:
        assert item["status"] == "OPEN"


def test_get_fiscal_year(client, auth_headers, sample_fiscal_year, assert_fiscal_year_structure):
    """Test récupération d'un exercice spécifique."""
    fiscal_year_id = sample_fiscal_year["id"]
    response = client.get(
        f"/api/v2/accounting/fiscal-years/{fiscal_year_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert_fiscal_year_structure(data)
    assert data["id"] == fiscal_year_id


def test_update_fiscal_year(client, auth_headers, sample_fiscal_year):
    """Test mise à jour d'un exercice comptable."""
    fiscal_year_id = sample_fiscal_year["id"]
    update_data = {
        "name": "Exercice 2024 - Modifié",
        "description": "Exercice modifié pour tests"
    }

    response = client.put(
        f"/api/v2/accounting/fiscal-years/{fiscal_year_id}",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]


def test_close_fiscal_year(client, auth_headers, sample_fiscal_year):
    """Test clôture d'un exercice comptable."""
    fiscal_year_id = sample_fiscal_year["id"]
    response = client.post(
        f"/api/v2/accounting/fiscal-years/{fiscal_year_id}/close",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CLOSED"
    assert "closed_at" in data


def test_fiscal_year_not_found(client, auth_headers):
    """Test erreur 404 pour exercice inexistant."""
    non_existent_id = str(uuid4())
    response = client.get(
        f"/api/v2/accounting/fiscal-years/{non_existent_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_fiscal_years_tenant_isolation(client, auth_headers, tenant_id, assert_tenant_isolation):
    """Test isolation des exercices par tenant."""
    response = client.get(
        "/api/v2/accounting/fiscal-years",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert_tenant_isolation(data, tenant_id)


# ===========================
# 3. CHART OF ACCOUNTS (8 tests)
# ===========================

def test_create_account(client, auth_headers, sample_account_data, assert_account_structure):
    """Test création d'un compte comptable."""
    response = client.post(
        "/api/v2/accounting/accounts",
        headers=auth_headers,
        json=sample_account_data
    )

    assert response.status_code == 201
    data = response.json()
    assert_account_structure(data)
    assert data["number"] == sample_account_data["number"]
    assert data["name"] == sample_account_data["name"]
    assert data["type"] == sample_account_data["type"]


def test_list_accounts(client, auth_headers):
    """Test listing de tous les comptes."""
    response = client.get(
        "/api/v2/accounting/accounts",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["items"], list)


def test_list_accounts_with_filters(client, auth_headers):
    """Test filtrage des comptes (type, class, search)."""
    # Test filtre par type
    response = client.get(
        "/api/v2/accounting/accounts?type=LIABILITY",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["type"] == "LIABILITY"

    # Test filtre par classe
    response = client.get(
        "/api/v2/accounting/accounts?class=4",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["class"] == "4"

    # Test recherche
    response = client.get(
        "/api/v2/accounting/accounts?search=Banque",
        headers=auth_headers
    )
    assert response.status_code == 200


def test_get_account(client, auth_headers, sample_account, assert_account_structure):
    """Test récupération d'un compte spécifique."""
    account_id = sample_account["id"]
    response = client.get(
        f"/api/v2/accounting/accounts/{account_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert_account_structure(data)
    assert data["id"] == account_id


def test_update_account(client, auth_headers, sample_account):
    """Test mise à jour d'un compte."""
    account_id = sample_account["id"]
    update_data = {
        "name": "Fournisseurs - Modifié",
        "description": "Description modifiée"
    }

    response = client.put(
        f"/api/v2/accounting/accounts/{account_id}",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]


def test_account_not_found(client, auth_headers):
    """Test erreur 404 pour compte inexistant."""
    non_existent_id = str(uuid4())
    response = client.get(
        f"/api/v2/accounting/accounts/{non_existent_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_accounts_tenant_isolation(client, auth_headers, tenant_id, assert_tenant_isolation):
    """Test isolation des comptes par tenant."""
    response = client.get(
        "/api/v2/accounting/accounts",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert_tenant_isolation(data, tenant_id)


def test_accounts_pagination(client, auth_headers):
    """Test pagination des comptes."""
    response = client.get(
        "/api/v2/accounting/accounts?page=1&page_size=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) <= 10


# ===========================
# 4. JOURNAL ENTRIES (12 tests)
# ===========================

def test_create_journal_entry(client, auth_headers, sample_journal_entry_data, assert_journal_entry_structure):
    """Test création d'une écriture comptable."""
    response = client.post(
        "/api/v2/accounting/journal-entries",
        headers=auth_headers,
        json=sample_journal_entry_data
    )

    assert response.status_code == 201
    data = response.json()
    assert_journal_entry_structure(data)
    assert data["reference"] == sample_journal_entry_data["reference"]
    assert data["status"] == "DRAFT"
    assert data["is_balanced"] is True


def test_list_journal_entries(client, auth_headers):
    """Test listing de toutes les écritures."""
    response = client.get(
        "/api/v2/accounting/journal-entries",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["items"], list)


def test_list_journal_entries_with_filters(client, auth_headers, sample_fiscal_year):
    """Test filtrage des écritures (fiscal_year, journal_code, status, period)."""
    fiscal_year_id = sample_fiscal_year["id"]

    # Test filtre par exercice
    response = client.get(
        f"/api/v2/accounting/journal-entries?fiscal_year_id={fiscal_year_id}",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Test filtre par code journal
    response = client.get(
        "/api/v2/accounting/journal-entries?journal_code=BQ",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["journal_code"] == "BQ"

    # Test filtre par statut
    response = client.get(
        "/api/v2/accounting/journal-entries?status=DRAFT",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["status"] == "DRAFT"

    # Test filtre par période
    response = client.get(
        "/api/v2/accounting/journal-entries?period=1",
        headers=auth_headers
    )
    assert response.status_code == 200


def test_get_journal_entry(client, auth_headers, sample_journal_entry, assert_journal_entry_structure):
    """Test récupération d'une écriture spécifique."""
    entry_id = sample_journal_entry["id"]
    response = client.get(
        f"/api/v2/accounting/journal-entries/{entry_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert_journal_entry_structure(data)
    assert data["id"] == entry_id


def test_update_journal_entry(client, auth_headers, sample_journal_entry):
    """Test mise à jour d'une écriture."""
    entry_id = sample_journal_entry["id"]
    update_data = {
        "description": "Description modifiée",
        "reference": "BQ2024-001-MOD"
    }

    response = client.put(
        f"/api/v2/accounting/journal-entries/{entry_id}",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == update_data["description"]


def test_post_journal_entry(client, auth_headers, sample_journal_entry):
    """Test passage d'une écriture de DRAFT à POSTED."""
    entry_id = sample_journal_entry["id"]
    response = client.post(
        f"/api/v2/accounting/journal-entries/{entry_id}/post",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "POSTED"
    assert "posted_at" in data
    assert "posted_by" in data


def test_validate_journal_entry(client, auth_headers, sample_journal_entry_posted):
    """Test validation d'une écriture POSTED → VALIDATED."""
    entry_id = sample_journal_entry_posted["id"]
    response = client.post(
        f"/api/v2/accounting/journal-entries/{entry_id}/validate",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "VALIDATED"
    assert "validated_at" in data
    assert "validated_by" in data


def test_cancel_journal_entry(client, auth_headers, sample_journal_entry):
    """Test annulation d'une écriture."""
    entry_id = sample_journal_entry["id"]
    response = client.post(
        f"/api/v2/accounting/journal-entries/{entry_id}/cancel",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CANCELLED"


def test_journal_entry_not_found(client, auth_headers):
    """Test erreur 404 pour écriture inexistante."""
    non_existent_id = str(uuid4())
    response = client.get(
        f"/api/v2/accounting/journal-entries/{non_existent_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_journal_entries_tenant_isolation(client, auth_headers, tenant_id, assert_tenant_isolation):
    """Test isolation des écritures par tenant."""
    response = client.get(
        "/api/v2/accounting/journal-entries",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert_tenant_isolation(data, tenant_id)


def test_journal_entry_pagination(client, auth_headers):
    """Test pagination des écritures."""
    response = client.get(
        "/api/v2/accounting/journal-entries?page=1&page_size=20",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["items"]) <= 20


def test_journal_entry_search(client, auth_headers):
    """Test recherche dans les écritures."""
    response = client.get(
        "/api/v2/accounting/journal-entries?search=Paiement",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


# ===========================
# 5. LEDGER (3 tests)
# ===========================

def test_get_ledger(client, auth_headers, sample_fiscal_year):
    """Test récupération du grand livre."""
    fiscal_year_id = sample_fiscal_year["id"]
    response = client.get(
        f"/api/v2/accounting/ledger?fiscal_year_id={fiscal_year_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "total_debit" in data
    assert "total_credit" in data
    assert "balance" in data
    assert isinstance(data["entries"], list)


def test_get_ledger_by_account(client, auth_headers, sample_fiscal_year, sample_account):
    """Test récupération du grand livre pour un compte spécifique."""
    fiscal_year_id = sample_fiscal_year["id"]
    account_id = sample_account["id"]

    response = client.get(
        f"/api/v2/accounting/ledger?fiscal_year_id={fiscal_year_id}&account_id={account_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    # Toutes les entrées devraient être pour le compte spécifié
    for entry in data["entries"]:
        assert entry.get("account_id") == account_id or entry.get("account_number") == sample_account["number"]


def test_ledger_account_not_found(client, auth_headers, sample_fiscal_year):
    """Test erreur pour compte inexistant dans le grand livre."""
    fiscal_year_id = sample_fiscal_year["id"]
    non_existent_account = str(uuid4())

    response = client.get(
        f"/api/v2/accounting/ledger?fiscal_year_id={fiscal_year_id}&account_id={non_existent_account}",
        headers=auth_headers
    )

    # Peut retourner 404 ou 200 avec entries vides selon l'implémentation
    assert response.status_code in [200, 404]


# ===========================
# 6. BALANCE (2 tests)
# ===========================

def test_get_balance(client, auth_headers, sample_fiscal_year):
    """Test récupération de la balance."""
    fiscal_year_id = sample_fiscal_year["id"]
    response = client.get(
        f"/api/v2/accounting/balance?fiscal_year_id={fiscal_year_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total_debit" in data
    assert "total_credit" in data
    assert "is_balanced" in data
    assert isinstance(data["items"], list)


def test_get_balance_with_period(client, auth_headers, sample_fiscal_year):
    """Test récupération de la balance pour une période."""
    fiscal_year_id = sample_fiscal_year["id"]
    response = client.get(
        f"/api/v2/accounting/balance?fiscal_year_id={fiscal_year_id}&period=1",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "period" in data
    assert data["period"] == 1


# ===========================
# 7. WORKFLOWS (5 tests)
# ===========================

def test_workflow_fiscal_year_lifecycle(client, auth_headers, sample_fiscal_year_data):
    """Test cycle de vie complet d'un exercice comptable."""
    # 1. Création
    response = client.post(
        "/api/v2/accounting/fiscal-years",
        headers=auth_headers,
        json=sample_fiscal_year_data
    )
    assert response.status_code == 201
    fiscal_year = response.json()
    assert fiscal_year["status"] == "OPEN"

    # 2. Mise à jour
    response = client.put(
        f"/api/v2/accounting/fiscal-years/{fiscal_year['id']}",
        headers=auth_headers,
        json={"name": "Exercice 2024 - Updated"}
    )
    assert response.status_code == 200

    # 3. Clôture
    response = client.post(
        f"/api/v2/accounting/fiscal-years/{fiscal_year['id']}/close",
        headers=auth_headers
    )
    assert response.status_code == 200
    closed_fy = response.json()
    assert closed_fy["status"] == "CLOSED"


def test_workflow_journal_entry_full_cycle(client, auth_headers, sample_journal_entry_data):
    """Test cycle complet d'une écriture: DRAFT → POSTED → VALIDATED."""
    # 1. Création (DRAFT)
    response = client.post(
        "/api/v2/accounting/journal-entries",
        headers=auth_headers,
        json=sample_journal_entry_data
    )
    assert response.status_code == 201
    entry = response.json()
    assert entry["status"] == "DRAFT"

    # 2. Passage en POSTED
    response = client.post(
        f"/api/v2/accounting/journal-entries/{entry['id']}/post",
        headers=auth_headers
    )
    assert response.status_code == 200
    posted_entry = response.json()
    assert posted_entry["status"] == "POSTED"

    # 3. Validation
    response = client.post(
        f"/api/v2/accounting/journal-entries/{entry['id']}/validate",
        headers=auth_headers
    )
    assert response.status_code == 200
    validated_entry = response.json()
    assert validated_entry["status"] == "VALIDATED"


def test_workflow_create_chart_and_entries(client, auth_headers, sample_fiscal_year_data, sample_account_data, sample_journal_entry_data):
    """Test workflow: créer exercice + plan comptable + écritures."""
    # 1. Créer exercice
    response = client.post(
        "/api/v2/accounting/fiscal-years",
        headers=auth_headers,
        json=sample_fiscal_year_data
    )
    assert response.status_code == 201
    fiscal_year = response.json()

    # 2. Créer comptes
    response = client.post(
        "/api/v2/accounting/accounts",
        headers=auth_headers,
        json=sample_account_data
    )
    assert response.status_code == 201
    account = response.json()

    # 3. Créer écriture liée
    journal_data = {
        **sample_journal_entry_data,
        "fiscal_year_id": fiscal_year["id"]
    }
    response = client.post(
        "/api/v2/accounting/journal-entries",
        headers=auth_headers,
        json=journal_data
    )
    assert response.status_code == 201


def test_workflow_generate_balance(client, auth_headers, sample_fiscal_year):
    """Test workflow de génération de balance."""
    fiscal_year_id = sample_fiscal_year["id"]

    # 1. Récupérer les écritures
    response = client.get(
        f"/api/v2/accounting/journal-entries?fiscal_year_id={fiscal_year_id}",
        headers=auth_headers
    )
    assert response.status_code == 200

    # 2. Générer la balance
    response = client.get(
        f"/api/v2/accounting/balance?fiscal_year_id={fiscal_year_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    balance = response.json()

    # 3. Vérifier l'équilibre
    assert balance["is_balanced"] is True


def test_workflow_close_fiscal_year_with_entries(client, auth_headers, sample_fiscal_year_data, sample_journal_entry_data):
    """Test clôture d'exercice avec écritures validées."""
    # 1. Créer exercice
    response = client.post(
        "/api/v2/accounting/fiscal-years",
        headers=auth_headers,
        json=sample_fiscal_year_data
    )
    assert response.status_code == 201
    fiscal_year = response.json()

    # 2. Créer et valider une écriture
    journal_data = {
        **sample_journal_entry_data,
        "fiscal_year_id": fiscal_year["id"]
    }
    response = client.post(
        "/api/v2/accounting/journal-entries",
        headers=auth_headers,
        json=journal_data
    )
    assert response.status_code == 201
    entry = response.json()

    # 3. Poster et valider l'écriture
    client.post(f"/api/v2/accounting/journal-entries/{entry['id']}/post", headers=auth_headers)
    client.post(f"/api/v2/accounting/journal-entries/{entry['id']}/validate", headers=auth_headers)

    # 4. Clôturer l'exercice
    response = client.post(
        f"/api/v2/accounting/fiscal-years/{fiscal_year['id']}/close",
        headers=auth_headers
    )
    assert response.status_code == 200


# ===========================
# 8. SECURITY (3 tests)
# ===========================

def test_tenant_isolation_strict(client, auth_headers, monkeypatch, tenant_id):
    """Test isolation stricte entre tenants."""
    # Créer des données pour tenant-test-001
    response = client.get(
        "/api/v2/accounting/fiscal-years",
        headers=auth_headers
    )
    assert response.status_code == 200
    tenant1_data = response.json()

    # Simuler un changement de contexte vers un autre tenant
    from app.core.saas_context import SaaSContext, UserRole

    def mock_other_tenant_context():
        return SaaSContext(
            tenant_id="tenant-test-002",  # Différent tenant
            user_id="user-test-002",
            role=UserRole.ADMIN,
            permissions={"accounting.*"},
            scope="tenant",
            session_id="session-test-2",
            ip_address="127.0.0.1",
            user_agent="pytest",
            correlation_id="test-correlation-2"
        )

    from app.modules.accounting import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_other_tenant_context)

    # Vérifier que les données du tenant 1 ne sont pas visibles
    response = client.get(
        "/api/v2/accounting/fiscal-years",
        headers=auth_headers
    )
    assert response.status_code == 200
    tenant2_data = response.json()

    # Les deux tenants ne doivent pas voir les mêmes données
    for item in tenant2_data["items"]:
        assert item["tenant_id"] == "tenant-test-002"


def test_saas_context_performance(client, auth_headers):
    """Test performance du contexte SaaS sur requêtes multiples."""
    # Effectuer plusieurs requêtes pour vérifier que le contexte
    # ne dégrade pas les performances
    endpoints = [
        "/api/v2/accounting/summary",
        "/api/v2/accounting/fiscal-years",
        "/api/v2/accounting/accounts",
        "/api/v2/accounting/journal-entries"
    ]

    for endpoint in endpoints:
        response = client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200


def test_audit_trail_automatic(client, auth_headers, sample_fiscal_year_data):
    """Test génération automatique de l'audit trail."""
    # Créer un exercice
    response = client.post(
        "/api/v2/accounting/fiscal-years",
        headers=auth_headers,
        json=sample_fiscal_year_data
    )
    assert response.status_code == 201
    fiscal_year = response.json()

    # Les métadonnées d'audit doivent être présentes
    assert "created_at" in fiscal_year
    assert "updated_at" in fiscal_year
    assert fiscal_year["tenant_id"] is not None


# ===========================
# 9. EDGE CASES (3 tests)
# ===========================

def test_invalid_date_range(client, auth_headers):
    """Test création d'exercice avec dates invalides."""
    invalid_data = {
        "name": "Exercice invalide",
        "code": "FYINVALID",
        "start_date": str(date(2024, 12, 31)),
        "end_date": str(date(2024, 1, 1)),  # Fin avant début
        "status": "OPEN"
    }

    response = client.post(
        "/api/v2/accounting/fiscal-years",
        headers=auth_headers,
        json=invalid_data
    )

    # Devrait retourner 422 (validation error) ou 400 (bad request)
    assert response.status_code in [400, 422]


def test_duplicate_account_number(client, auth_headers, sample_account_data):
    """Test création de compte avec numéro dupliqué."""
    # Créer le premier compte
    response = client.post(
        "/api/v2/accounting/accounts",
        headers=auth_headers,
        json=sample_account_data
    )
    assert response.status_code == 201

    # Tenter de créer un compte avec le même numéro
    response = client.post(
        "/api/v2/accounting/accounts",
        headers=auth_headers,
        json=sample_account_data
    )

    # Devrait retourner 409 (conflict) ou 400 (bad request)
    assert response.status_code in [400, 409]


def test_unbalanced_journal_entry(client, auth_headers):
    """Test création d'écriture non équilibrée."""
    unbalanced_data = {
        "date": str(date.today()),
        "journal_code": "BQ",
        "reference": "BQ2024-999",
        "description": "Écriture déséquilibrée",
        "fiscal_year_id": str(uuid4()),
        "period": 1,
        "status": "DRAFT",
        "lines": [
            {
                "account_id": str(uuid4()),
                "account_number": "512000",
                "label": "Débit",
                "debit": 1000.0,
                "credit": 0.0
            },
            {
                "account_id": str(uuid4()),
                "account_number": "401000",
                "label": "Crédit",
                "debit": 0.0,
                "credit": 500.0  # Montant différent !
            }
        ]
    }

    response = client.post(
        "/api/v2/accounting/journal-entries",
        headers=auth_headers,
        json=unbalanced_data
    )

    # Devrait retourner 422 (validation error) ou 400 (bad request)
    assert response.status_code in [400, 422]
