"""
Fixtures réutilisables pour les tests du module Compliance - CORE SaaS v2
==========================================================================
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.saas_context import SaaSContext, UserRole, TenantScope
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
# MOCK SAAS CONTEXT
# =============================================================================

@pytest.fixture
def mock_saas_context():
    """Crée un mock de SaaSContext pour les tests."""
    return SaaSContext(
        tenant_id="test-tenant-001",
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        role=UserRole.ADMIN,
        permissions={"compliance.*"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="pytest",
        correlation_id="test-correlation-id"
    )


# =============================================================================
# FIXTURES DATA
# =============================================================================

@pytest.fixture
def regulation_data():
    """Données pour créer une réglementation."""
    return {
        "code": "GDPR-2016-679",
        "name": "Règlement Général sur la Protection des Données",
        "type": RegulationType.PRIVACY,
        "description": "Réglementation européenne sur la protection des données personnelles",
        "authority": "Commission Européenne",
        "effective_date": date(2018, 5, 25),
        "jurisdiction": "UE",
        "scope": "Protection des données personnelles",
        "is_mandatory": True,
        "is_active": True
    }


@pytest.fixture
def requirement_data(regulation_id):
    """Données pour créer une exigence."""
    return {
        "regulation_id": regulation_id,
        "code": "GDPR-ART-32",
        "title": "Sécurité du traitement",
        "description": "Mesures techniques et organisationnelles appropriées",
        "category": "Sécurité",
        "priority": RequirementPriority.HIGH,
        "compliance_status": ComplianceStatus.PENDING,
        "control_objectives": ["Confidentialité", "Intégrité", "Disponibilité"],
        "is_active": True
    }


@pytest.fixture
def assessment_data():
    """Données pour créer une évaluation."""
    return {
        "title": "Évaluation GDPR Q1 2024",
        "description": "Évaluation trimestrielle de conformité GDPR",
        "scope": "Ensemble des traitements de données personnelles",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 3, 31),
        "assessor_name": "Jean Dupont",
        "assessor_organization": "ACME Compliance"
    }


@pytest.fixture
def gap_data(assessment_id, requirement_id):
    """Données pour créer un écart."""
    return {
        "assessment_id": assessment_id,
        "requirement_id": requirement_id,
        "title": "Absence de chiffrement des données sensibles",
        "description": "Les données sensibles ne sont pas chiffrées au repos",
        "current_status": ComplianceStatus.NON_COMPLIANT,
        "severity": RiskLevel.HIGH,
        "impact": "Risque de fuite de données en cas d'intrusion",
        "target_closure_date": date(2024, 6, 30),
        "is_open": True
    }


@pytest.fixture
def action_data(gap_id):
    """Données pour créer une action corrective."""
    return {
        "gap_id": gap_id,
        "title": "Mise en place du chiffrement TDE",
        "description": "Implémenter Transparent Data Encryption sur la base de données",
        "priority": RequirementPriority.HIGH,
        "owner_id": UUID("87654321-4321-8765-4321-876543218765"),
        "due_date": date(2024, 5, 31),
        "estimated_cost": Decimal("5000.00")
    }


@pytest.fixture
def policy_data():
    """Données pour créer une politique."""
    return {
        "code": "POL-SEC-001",
        "title": "Politique de Sécurité de l'Information",
        "category": "Sécurité",
        "version": "1.0",
        "description": "Politique générale de sécurité de l'information",
        "content": "# Politique de Sécurité\\n\\nObjectif: Protéger les actifs informationnels...",
        "owner_id": UUID("11111111-1111-1111-1111-111111111111"),
        "requires_acknowledgment": True,
        "is_active": True
    }


@pytest.fixture
def training_data():
    """Données pour créer une formation."""
    return {
        "code": "TRAIN-GDPR-001",
        "title": "Formation GDPR - Fondamentaux",
        "description": "Formation de base sur le RGPD",
        "category": "Conformité",
        "duration_hours": Decimal("4.0"),
        "delivery_method": "E-learning",
        "passing_score": 80,
        "is_mandatory": True,
        "recurrence_months": 12
    }


@pytest.fixture
def audit_data():
    """Données pour créer un audit."""
    return {
        "title": "Audit de conformité ISO 27001",
        "scope": "Système de management de la sécurité de l'information",
        "planned_start": date(2024, 4, 1),
        "planned_end": date(2024, 4, 5),
        "audit_type": "Certification",
        "lead_auditor": "Marie Martin",
        "audit_organization": "Bureau Veritas"
    }


@pytest.fixture
def finding_data(audit_id, requirement_id):
    """Données pour créer une constatation."""
    return {
        "audit_id": audit_id,
        "requirement_id": requirement_id,
        "title": "Absence de revue des droits d'accès",
        "description": "Aucun processus de revue périodique des droits d'accès",
        "severity": FindingSeverity.MAJOR,
        "evidence": "Analyse des logs, entretiens avec les administrateurs",
        "recommendation": "Mettre en place une revue trimestrielle des droits d'accès"
    }


@pytest.fixture
def risk_data(requirement_id):
    """Données pour créer un risque."""
    return {
        "requirement_id": requirement_id,
        "title": "Risque de perte de données",
        "description": "Absence de sauvegardes externalisées",
        "category": "Disponibilité",
        "likelihood": 3,
        "impact": 4,
        "owner_id": UUID("22222222-2222-2222-2222-222222222222")
    }


@pytest.fixture
def incident_data(requirement_id):
    """Données pour créer un incident."""
    return {
        "requirement_id": requirement_id,
        "title": "Accès non autorisé détecté",
        "description": "Tentative d'accès non autorisée aux données clients",
        "severity": FindingSeverity.CRITICAL,
        "occurred_at": datetime.utcnow(),
        "detection_method": "Système de détection d'intrusion"
    }


@pytest.fixture
def report_data():
    """Données pour créer un rapport."""
    return {
        "title": "Rapport de conformité Q1 2024",
        "report_type": "Trimestriel",
        "period_start": date(2024, 1, 1),
        "period_end": date(2024, 3, 31),
        "executive_summary": "Niveau de conformité global: 85%",
        "content": "# Rapport Q1\\n\\n## Résultats..."
    }


# =============================================================================
# FIXTURES ENTITÉS COMPLÈTES
# =============================================================================

@pytest.fixture
def regulation_id():
    """ID d'une réglementation pour les tests."""
    return UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def requirement_id():
    """ID d'une exigence pour les tests."""
    return UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def assessment_id():
    """ID d'une évaluation pour les tests."""
    return UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


@pytest.fixture
def gap_id():
    """ID d'un écart pour les tests."""
    return UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


@pytest.fixture
def action_id():
    """ID d'une action pour les tests."""
    return UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")


@pytest.fixture
def policy_id():
    """ID d'une politique pour les tests."""
    return UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")


@pytest.fixture
def training_id():
    """ID d'une formation pour les tests."""
    return UUID("10101010-1010-1010-1010-101010101010")


@pytest.fixture
def audit_id():
    """ID d'un audit pour les tests."""
    return UUID("20202020-2020-2020-2020-202020202020")


@pytest.fixture
def finding_id():
    """ID d'une constatation pour les tests."""
    return UUID("30303030-3030-3030-3030-303030303030")


@pytest.fixture
def risk_id():
    """ID d'un risque pour les tests."""
    return UUID("40404040-4040-4040-4040-404040404040")


@pytest.fixture
def incident_id():
    """ID d'un incident pour les tests."""
    return UUID("50505050-5050-5050-5050-505050505050")


@pytest.fixture
def report_id():
    """ID d'un rapport pour les tests."""
    return UUID("60606060-6060-6060-6060-606060606060")


@pytest.fixture
def completion_id():
    """ID d'une completion de formation pour les tests."""
    return UUID("70707070-7070-7070-7070-707070707070")


# =============================================================================
# HELPER ASSERTIONS
# =============================================================================

def assert_regulation_response(response_data, expected_data):
    """Vérifie qu'une réponse de réglementation contient les bonnes données."""
    assert response_data["code"] == expected_data["code"]
    assert response_data["name"] == expected_data["name"]
    assert response_data["type"] == expected_data["type"]


def assert_requirement_response(response_data, expected_data):
    """Vérifie qu'une réponse d'exigence contient les bonnes données."""
    assert response_data["code"] == expected_data["code"]
    assert response_data["title"] == expected_data["title"]
    assert response_data["priority"] == expected_data["priority"]


def assert_assessment_response(response_data, expected_data):
    """Vérifie qu'une réponse d'évaluation contient les bonnes données."""
    assert response_data["title"] == expected_data["title"]
    assert response_data["scope"] == expected_data["scope"]


def assert_action_response(response_data, expected_data):
    """Vérifie qu'une réponse d'action contient les bonnes données."""
    assert response_data["title"] == expected_data["title"]
    assert response_data["priority"] == expected_data["priority"]
