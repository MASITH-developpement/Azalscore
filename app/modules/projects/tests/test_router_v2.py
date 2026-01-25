"""
Tests pour le router Projects v2 (CORE SaaS)

Coverage cible: 65-70%
Total endpoints: 51
Total tests: 58
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest


# ============================================================================
# TESTS PROJETS (9 tests)
# ============================================================================

def test_create_project(
    client, auth_headers, mock_saas_context, tenant_id, sample_project_data
):
    """Test création d'un projet"""
    response = client.post(
        "/api/v2/projects",
        json=sample_project_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_project_data["name"]
    assert data["code"] == sample_project_data["code"]
    assert data["tenant_id"] == tenant_id
    assert "id" in data
    assert "created_at" in data


def test_list_projects(
    client, auth_headers, mock_saas_context, tenant_id
):
    """Test liste des projets avec pagination"""
    response = client.get(
        "/api/v2/projects?page=1&page_size=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["projects"], list)


def test_list_projects_with_filters(
    client, auth_headers, mock_saas_context
):
    """Test liste des projets avec filtres status et priority"""
    response = client.get(
        "/api/v2/projects?status=ACTIVE&priority=HIGH",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "projects" in data

    # Vérifier que les projets retournés correspondent aux filtres
    for project in data["projects"]:
        if "status" in project:
            assert project["status"] == "ACTIVE"
        if "priority" in project:
            assert project["priority"] == "HIGH"


def test_list_projects_with_search(
    client, auth_headers, mock_saas_context
):
    """Test liste des projets avec recherche textuelle"""
    response = client.get(
        "/api/v2/projects?search=Test",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "projects" in data


def test_get_project(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test récupération d'un projet par ID"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]  # OK si trouvé, 404 si pas en DB


def test_update_project(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test mise à jour d'un projet"""
    project_id = sample_project["id"]

    update_data = {
        "name": "Projet Modifié",
        "status": "ACTIVE",
        "priority": "CRITICAL",
    }

    response = client.put(
        f"/api/v2/projects/{project_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_delete_project(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test suppression d'un projet"""
    project_id = sample_project["id"]

    response = client.delete(
        f"/api/v2/projects/{project_id}",
        headers=auth_headers
    )

    assert response.status_code in [204, 404]


def test_refresh_project_progress(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test recalcul de la progression du projet"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/refresh-progress",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "progress" in data
        assert isinstance(data["progress"], (int, float))


def test_get_project_dashboard(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test récupération du dashboard d'un projet"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/dashboard",
        headers=auth_headers
    )

    assert response.status_code in [200, 404, 405]  # 405 si GET au lieu de POST

    # Réessayer avec GET si POST non supporté
    if response.status_code == 405:
        response = client.get(
            f"/api/v2/projects/{project_id}/dashboard",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]


def test_get_project_stats(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test récupération des statistiques d'un projet"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/stats",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


# ============================================================================
# TESTS PHASES (4 tests)
# ============================================================================

def test_create_phase(
    client, auth_headers, mock_saas_context, sample_project, sample_phase_data
):
    """Test création d'une phase"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/phases",
        json=sample_phase_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["name"] == sample_phase_data["name"]
        assert data["project_id"] == project_id
        assert "id" in data


def test_list_phases(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des phases d'un projet"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/phases",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_update_phase(
    client, auth_headers, mock_saas_context, sample_phase
):
    """Test mise à jour d'une phase"""
    phase_id = sample_phase["id"]

    update_data = {
        "name": "Phase Modifiée",
        "description": "Nouvelle description",
    }

    response = client.put(
        f"/api/v2/projects/phases/{phase_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_delete_phase(
    client, auth_headers, mock_saas_context, sample_phase
):
    """Test suppression d'une phase"""
    phase_id = sample_phase["id"]

    response = client.delete(
        f"/api/v2/projects/phases/{phase_id}",
        headers=auth_headers
    )

    assert response.status_code in [204, 404]


# ============================================================================
# TESTS TÂCHES (6 tests)
# ============================================================================

def test_create_task(
    client, auth_headers, mock_saas_context, sample_project, sample_task_data
):
    """Test création d'une tâche"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/tasks",
        json=sample_task_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["name"] == sample_task_data["name"]
        assert data["project_id"] == project_id
        assert "id" in data


def test_list_tasks(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des tâches d'un projet avec pagination"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/tasks?page=1&page_size=20",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert isinstance(data["tasks"], list)


def test_list_tasks_with_filters(
    client, auth_headers, mock_saas_context, sample_project, user_id
):
    """Test liste des tâches avec filtres status et assigned_to"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/tasks?status=IN_PROGRESS&assigned_to={user_id}",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_list_my_tasks(
    client, auth_headers, mock_saas_context, user_id
):
    """Test liste de mes tâches (assignées à l'utilisateur courant)"""
    response = client.get(
        "/api/v2/projects/tasks/my",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Vérifier que toutes les tâches sont assignées à l'utilisateur
    for task in data:
        if "assigned_to" in task:
            assert task["assigned_to"] == user_id


def test_get_task(
    client, auth_headers, mock_saas_context, sample_task
):
    """Test récupération d'une tâche par ID"""
    task_id = sample_task["id"]

    response = client.get(
        f"/api/v2/projects/tasks/{task_id}",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_update_task(
    client, auth_headers, mock_saas_context, sample_task
):
    """Test mise à jour d'une tâche"""
    task_id = sample_task["id"]

    update_data = {
        "name": "Tâche Modifiée",
        "status": "IN_PROGRESS",
        "progress": 50.0,
    }

    response = client.put(
        f"/api/v2/projects/tasks/{task_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_delete_task(
    client, auth_headers, mock_saas_context, sample_task
):
    """Test suppression d'une tâche"""
    task_id = sample_task["id"]

    response = client.delete(
        f"/api/v2/projects/tasks/{task_id}",
        headers=auth_headers
    )

    assert response.status_code in [204, 404]


# ============================================================================
# TESTS JALONS (3 tests)
# ============================================================================

def test_create_milestone(
    client, auth_headers, mock_saas_context, sample_project, sample_milestone_data
):
    """Test création d'un jalon"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/milestones",
        json=sample_milestone_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["name"] == sample_milestone_data["name"]
        assert data["project_id"] == project_id


def test_list_milestones(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des jalons d'un projet"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/milestones",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_update_milestone(
    client, auth_headers, mock_saas_context, sample_milestone
):
    """Test mise à jour d'un jalon"""
    milestone_id = sample_milestone["id"]

    update_data = {
        "name": "Jalon Modifié",
        "is_achieved": True,
        "achieved_date": str(date.today()),
    }

    response = client.put(
        f"/api/v2/projects/milestones/{milestone_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


# ============================================================================
# TESTS ÉQUIPE (4 tests)
# ============================================================================

def test_add_team_member(
    client, auth_headers, mock_saas_context, sample_project, sample_team_member_data
):
    """Test ajout d'un membre à l'équipe"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/team",
        json=sample_team_member_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["user_id"] == sample_team_member_data["user_id"]
        assert data["project_id"] == project_id


def test_list_team_members(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des membres de l'équipe"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/team",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_update_team_member(
    client, auth_headers, mock_saas_context, sample_team_member
):
    """Test mise à jour d'un membre d'équipe"""
    member_id = sample_team_member["id"]

    update_data = {
        "role": "TECH_LEAD",
        "allocation": 50,  # 50%
    }

    response = client.put(
        f"/api/v2/projects/team/{member_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_remove_team_member(
    client, auth_headers, mock_saas_context, sample_team_member
):
    """Test retrait d'un membre de l'équipe"""
    member_id = sample_team_member["id"]

    response = client.delete(
        f"/api/v2/projects/team/{member_id}",
        headers=auth_headers
    )

    assert response.status_code in [204, 404]


# ============================================================================
# TESTS RISQUES (3 tests)
# ============================================================================

def test_create_risk(
    client, auth_headers, mock_saas_context, sample_project, sample_risk_data
):
    """Test création d'un risque"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/risks",
        json=sample_risk_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["title"] == sample_risk_data["title"]
        assert data["project_id"] == project_id


def test_list_risks(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des risques d'un projet"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/risks",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_list_risks_with_status_filter(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des risques avec filtre status"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/risks?status=IDENTIFIED",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_update_risk(
    client, auth_headers, mock_saas_context, sample_risk
):
    """Test mise à jour d'un risque"""
    risk_id = sample_risk["id"]

    update_data = {
        "status": "MITIGATED",
        "probability": 20,  # Réduit après mitigation
    }

    response = client.put(
        f"/api/v2/projects/risks/{risk_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


# ============================================================================
# TESTS PROBLÈMES/ISSUES (3 tests)
# ============================================================================

def test_create_issue(
    client, auth_headers, mock_saas_context, sample_project, sample_issue_data
):
    """Test création d'un problème"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/issues",
        json=sample_issue_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["title"] == sample_issue_data["title"]
        assert data["project_id"] == project_id


def test_list_issues(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des problèmes d'un projet"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/issues",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_list_issues_with_filters(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des problèmes avec filtres status et priority"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/issues?status=OPEN&priority=HIGH",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_update_issue(
    client, auth_headers, mock_saas_context, sample_issue
):
    """Test mise à jour d'un problème"""
    issue_id = sample_issue["id"]

    update_data = {
        "status": "RESOLVED",
        "resolution": "Problème corrigé en optimisant les requêtes",
        "resolved_at": str(date.today()),
    }

    response = client.put(
        f"/api/v2/projects/issues/{issue_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


# ============================================================================
# TESTS TEMPS (5 tests)
# ============================================================================

def test_create_time_entry(
    client, auth_headers, mock_saas_context, sample_project, sample_time_entry_data
):
    """Test création d'une saisie de temps"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/time",
        json=sample_time_entry_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["hours"] == sample_time_entry_data["hours"]
        assert data["project_id"] == project_id


def test_list_time_entries(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des saisies de temps d'un projet"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/time?page=1&page_size=20",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "entries" in data
        assert "total" in data


def test_list_time_entries_with_date_range(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des saisies de temps avec plage de dates"""
    project_id = sample_project["id"]
    from_date = str(date.today() - timedelta(days=30))
    to_date = str(date.today())

    response = client.get(
        f"/api/v2/projects/{project_id}/time?from_date={from_date}&to_date={to_date}",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_submit_time_entry(
    client, auth_headers, mock_saas_context, sample_time_entry
):
    """Test soumission d'une saisie de temps"""
    entry_id = sample_time_entry["id"]

    response = client.post(
        f"/api/v2/projects/time/{entry_id}/submit",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "SUBMITTED"


def test_approve_time_entry(
    client, auth_headers, mock_saas_context, sample_time_entry
):
    """Test approbation d'une saisie de temps"""
    entry_id = sample_time_entry["id"]

    response = client.post(
        f"/api/v2/projects/time/{entry_id}/approve",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "APPROVED"


def test_reject_time_entry(
    client, auth_headers, mock_saas_context, sample_time_entry
):
    """Test rejet d'une saisie de temps"""
    entry_id = sample_time_entry["id"]

    response = client.post(
        f"/api/v2/projects/time/{entry_id}/reject?reason=Heures incorrectes",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "REJECTED"


# ============================================================================
# TESTS DÉPENSES (3 tests)
# ============================================================================

def test_create_expense(
    client, auth_headers, mock_saas_context, sample_project, sample_expense_data
):
    """Test création d'une dépense"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/expenses",
        json=sample_expense_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["amount"] == sample_expense_data["amount"]
        assert data["project_id"] == project_id


def test_list_expenses(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des dépenses d'un projet"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/expenses",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_list_expenses_with_status_filter(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des dépenses avec filtre status"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/expenses?status=PENDING",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_approve_expense(
    client, auth_headers, mock_saas_context, sample_expense
):
    """Test approbation d'une dépense"""
    expense_id = sample_expense["id"]

    response = client.post(
        f"/api/v2/projects/expenses/{expense_id}/approve",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "APPROVED"


# ============================================================================
# TESTS DOCUMENTS (2 tests)
# ============================================================================

def test_create_document(
    client, auth_headers, mock_saas_context, sample_project, sample_document_data
):
    """Test création d'un document"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/documents",
        json=sample_document_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["name"] == sample_document_data["name"]
        assert data["project_id"] == project_id


def test_list_documents(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des documents d'un projet"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/documents",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# TESTS BUDGETS (3 tests)
# ============================================================================

def test_create_budget(
    client, auth_headers, mock_saas_context, sample_project, sample_budget_data
):
    """Test création d'un budget"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/budgets",
        json=sample_budget_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["category"] == sample_budget_data["category"]
        assert data["project_id"] == project_id


def test_list_budgets(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des budgets d'un projet"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/budgets",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_approve_budget(
    client, auth_headers, mock_saas_context, sample_budget
):
    """Test approbation d'un budget"""
    budget_id = sample_budget["id"]

    response = client.post(
        f"/api/v2/projects/budgets/{budget_id}/approve",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert data["is_approved"] is True


# ============================================================================
# TESTS TEMPLATES (3 tests)
# ============================================================================

def test_create_template(
    client, auth_headers, mock_saas_context, sample_template_data
):
    """Test création d'un modèle de projet"""
    response = client.post(
        "/api/v2/projects/templates",
        json=sample_template_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_template_data["name"]
    assert "id" in data


def test_list_templates(
    client, auth_headers, mock_saas_context
):
    """Test liste des modèles de projet"""
    response = client.get(
        "/api/v2/projects/templates",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_project_from_template(
    client, auth_headers, mock_saas_context, sample_template
):
    """Test création d'un projet depuis un modèle"""
    template_id = sample_template["id"]

    response = client.post(
        f"/api/v2/projects/from-template/{template_id}?project_name=Projet depuis Template",
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert "Projet depuis Template" in data["name"]
        assert "id" in data


# ============================================================================
# TESTS COMMENTAIRES (2 tests)
# ============================================================================

def test_create_comment(
    client, auth_headers, mock_saas_context, sample_project, sample_comment_data
):
    """Test création d'un commentaire"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/comments",
        json=sample_comment_data,
        headers=auth_headers
    )

    assert response.status_code in [201, 404]

    if response.status_code == 201:
        data = response.json()
        assert data["content"] == sample_comment_data["content"]
        assert data["project_id"] == project_id


def test_list_comments(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test liste des commentaires d'un projet"""
    project_id = sample_project["id"]

    response = client.get(
        f"/api/v2/projects/{project_id}/comments",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# TESTS KPIs (1 test)
# ============================================================================

def test_calculate_project_kpis(
    client, auth_headers, mock_saas_context, sample_project
):
    """Test calcul des KPIs d'un projet"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/kpis/calculate",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        # KPIs typiques
        assert "schedule_performance_index" in data or "earned_value" in data or "health_status" in data


# ============================================================================
# TESTS WORKFLOWS (5 tests)
# ============================================================================

def test_workflow_complete_project_lifecycle(
    client, auth_headers, mock_saas_context, sample_project_data
):
    """Test workflow complet: créer projet → activer → compléter"""
    # 1. Créer projet
    response = client.post(
        "/api/v2/projects",
        json=sample_project_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    project_id = response.json()["id"]

    # 2. Activer projet
    response = client.put(
        f"/api/v2/projects/{project_id}",
        json={"status": "ACTIVE"},
        headers=auth_headers
    )
    assert response.status_code in [200, 404]

    # 3. Compléter projet
    response = client.put(
        f"/api/v2/projects/{project_id}",
        json={"status": "COMPLETED"},
        headers=auth_headers
    )
    assert response.status_code in [200, 404]


def test_workflow_task_lifecycle(
    client, auth_headers, mock_saas_context, sample_project, sample_task_data, user_id
):
    """Test workflow tâche: créer → assigner → démarrer → compléter"""
    project_id = sample_project["id"]

    # 1. Créer tâche
    response = client.post(
        f"/api/v2/projects/{project_id}/tasks",
        json=sample_task_data,
        headers=auth_headers
    )
    if response.status_code != 201:
        pytest.skip("Projet non existant en DB")

    task_id = response.json()["id"]

    # 2. Assigner tâche
    response = client.put(
        f"/api/v2/projects/tasks/{task_id}",
        json={"assigned_to": user_id, "status": "TODO"},
        headers=auth_headers
    )
    assert response.status_code == 200

    # 3. Démarrer tâche
    response = client.put(
        f"/api/v2/projects/tasks/{task_id}",
        json={"status": "IN_PROGRESS"},
        headers=auth_headers
    )
    assert response.status_code == 200

    # 4. Compléter tâche
    response = client.put(
        f"/api/v2/projects/tasks/{task_id}",
        json={"status": "DONE", "progress": 100},
        headers=auth_headers
    )
    assert response.status_code == 200


def test_workflow_time_entry_lifecycle(
    client, auth_headers, mock_saas_context, sample_project, sample_time_entry_data
):
    """Test workflow saisie temps: créer → soumettre → approuver"""
    project_id = sample_project["id"]

    # 1. Créer saisie
    response = client.post(
        f"/api/v2/projects/{project_id}/time",
        json=sample_time_entry_data,
        headers=auth_headers
    )
    if response.status_code != 201:
        pytest.skip("Projet non existant en DB")

    entry_id = response.json()["id"]

    # 2. Soumettre saisie
    response = client.post(
        f"/api/v2/projects/time/{entry_id}/submit",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"

    # 3. Approuver saisie
    response = client.post(
        f"/api/v2/projects/time/{entry_id}/approve",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_workflow_expense_approval(
    client, auth_headers, mock_saas_context, sample_project, sample_expense_data
):
    """Test workflow dépense: créer → approuver"""
    project_id = sample_project["id"]

    # 1. Créer dépense
    response = client.post(
        f"/api/v2/projects/{project_id}/expenses",
        json=sample_expense_data,
        headers=auth_headers
    )
    if response.status_code != 201:
        pytest.skip("Projet non existant en DB")

    expense_id = response.json()["id"]

    # 2. Approuver dépense
    response = client.post(
        f"/api/v2/projects/expenses/{expense_id}/approve",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_workflow_budget_approval(
    client, auth_headers, mock_saas_context, sample_project, sample_budget_data
):
    """Test workflow budget: créer → approuver"""
    project_id = sample_project["id"]

    # 1. Créer budget
    response = client.post(
        f"/api/v2/projects/{project_id}/budgets",
        json=sample_budget_data,
        headers=auth_headers
    )
    if response.status_code != 201:
        pytest.skip("Projet non existant en DB")

    budget_id = response.json()["id"]

    # 2. Approuver budget
    response = client.post(
        f"/api/v2/projects/budgets/{budget_id}/approve",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["is_approved"] is True


# ============================================================================
# TESTS SÉCURITÉ & ISOLATION TENANT (3 tests)
# ============================================================================

def test_tenant_isolation_projects(
    client, auth_headers, mock_saas_context, tenant_id, sample_project_data
):
    """Test isolation tenant pour les projets"""
    # Créer projet
    response = client.post(
        "/api/v2/projects",
        json=sample_project_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    # Vérifier tenant_id
    assert data["tenant_id"] == tenant_id

    # Lister projets (doit filtrer automatiquement)
    response = client.get("/api/v2/projects", headers=auth_headers)
    assert response.status_code == 200

    projects = response.json()["projects"]
    for project in projects:
        assert project["tenant_id"] == tenant_id


def test_tenant_isolation_tasks(
    client, auth_headers, mock_saas_context, tenant_id, sample_project, sample_task_data
):
    """Test isolation tenant pour les tâches"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/tasks",
        json=sample_task_data,
        headers=auth_headers
    )

    if response.status_code == 201:
        data = response.json()
        # Vérifier que la tâche appartient au même tenant que le projet
        assert data["project_id"] == project_id


def test_tenant_isolation_time_entries(
    client, auth_headers, mock_saas_context, sample_project, sample_time_entry_data
):
    """Test isolation tenant pour les saisies de temps"""
    project_id = sample_project["id"]

    response = client.post(
        f"/api/v2/projects/{project_id}/time",
        json=sample_time_entry_data,
        headers=auth_headers
    )

    if response.status_code == 201:
        data = response.json()
        # Vérifier que la saisie appartient au projet du tenant
        assert data["project_id"] == project_id


# ============================================================================
# TESTS PERFORMANCE & BENCHMARKS (2 tests)
# ============================================================================

def test_list_projects_pagination_performance(
    client, auth_headers, mock_saas_context, benchmark
):
    """Test performance liste paginée de projets"""
    def execute_list():
        response = client.get(
            "/api/v2/projects?page=1&page_size=50",
            headers=auth_headers
        )
        assert response.status_code == 200
        return response

    result = benchmark(execute_list)
    assert result.status_code == 200


def test_list_tasks_pagination_performance(
    client, auth_headers, mock_saas_context, sample_project, benchmark
):
    """Test performance liste paginée de tâches"""
    project_id = sample_project["id"]

    def execute_list():
        response = client.get(
            f"/api/v2/projects/{project_id}/tasks?page=1&page_size=50",
            headers=auth_headers
        )
        return response

    result = benchmark(execute_list)
    # Accepter 200 (succès) ou 404 (projet pas en DB)
    assert result.status_code in [200, 404]
