"""
Fixtures pour les tests du module Quality - CORE SaaS v2
=========================================================
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.saas_context import SaaSContext, UserRole, TenantScope
from app.modules.quality.models import (
    CAPA,
    AuditFinding,
    AuditStatus,
    AuditType,
    CAPAAction,
    CAPAStatus,
    CAPAType,
    Certification,
    CertificationAudit,
    CertificationStatus,
    ClaimAction,
    ClaimStatus,
    ControlResult,
    ControlStatus,
    ControlType,
    CustomerClaim,
    FindingSeverity,
    IndicatorMeasurement,
    NonConformance,
    NonConformanceAction,
    NonConformanceSeverity,
    NonConformanceStatus,
    NonConformanceType,
    QualityAudit,
    QualityControl,
    QualityControlLine,
    QualityControlTemplate,
    QualityControlTemplateItem,
    QualityIndicator,
)


# ============================================================================
# MOCK SAAS CONTEXT
# ============================================================================

@pytest.fixture
def mock_saas_context():
    """Mock SaaSContext pour les tests"""
    return SaaSContext(
        tenant_id="1",
        user_id=UUID("00000000-0000-0000-0000-000000000101"),
        role=UserRole.ADMIN,
        permissions={"quality.*"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="pytest",
        correlation_id="test-quality-001"
    )


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


# ============================================================================
# DATA FIXTURES - Non-Conformités
# ============================================================================

@pytest.fixture
def nc_data():
    """Données pour créer une non-conformité"""
    return {
        "title": "Pièce défectueuse",
        "description": "Surface rayée sur le produit",
        "nc_type": "INTERNAL",
        "severity": "MAJOR",
        "detected_date": date.today().isoformat(),
        "detection_location": "Ligne A",
        "detection_phase": "PRODUCTION",
        "source_type": "PRODUCTION",
        "product_id": 1,
        "lot_number": "LOT-2024-001",
        "quantity_affected": 10,
        "immediate_action": "Isoler les pièces défectueuses",
        "responsible_id": 1,
    }


@pytest.fixture
def nc_entity():
    """Entité non-conformité pour les tests"""
    nc = NonConformance(
        id=1,
        tenant_id=1,
        nc_number="NC-2024-00001",
        title="Pièce défectueuse",
        description="Surface rayée sur le produit",
        nc_type=NonConformanceType.INTERNAL,
        severity=NonConformanceSeverity.MAJOR,
        status=NonConformanceStatus.OPEN,
        detected_date=date.today(),
        detected_by_id=101,
        detection_location="Ligne A",
        detection_phase="PRODUCTION",
        source_type="PRODUCTION",
        product_id=1,
        lot_number="LOT-2024-001",
        quantity_affected=Decimal("10"),
        immediate_action="Isoler les pièces défectueuses",
        responsible_id=1,
        created_by=101,
        created_at=datetime.now(),
    )
    nc.actions = []
    return nc


# ============================================================================
# DATA FIXTURES - Actions NC
# ============================================================================

@pytest.fixture
def nc_action_data():
    """Données pour créer une action NC"""
    return {
        "action_type": "CORRECTIVE",
        "description": "Ajuster le réglage de la machine",
        "responsible_id": 1,
        "planned_date": date.today().isoformat(),
        "due_date": date.today().isoformat(),
    }


@pytest.fixture
def nc_action_entity():
    """Entité action NC pour les tests"""
    return NonConformanceAction(
        id=1,
        tenant_id=1,
        nc_id=1,
        action_number=1,
        action_type="CORRECTIVE",
        description="Ajuster le réglage de la machine",
        responsible_id=1,
        planned_date=date.today(),
        due_date=date.today(),
        status="PLANNED",
        created_by=101,
        created_at=datetime.now(),
    )


# ============================================================================
# DATA FIXTURES - Templates de Contrôle
# ============================================================================

@pytest.fixture
def control_template_data():
    """Données pour créer un template de contrôle"""
    return {
        "code": "TPL-001",
        "name": "Contrôle dimensionnel",
        "description": "Vérification des dimensions critiques",
        "version": "1.0",
        "control_type": "RECEIVING",
        "applies_to": "PRODUCT",
        "instructions": "Mesurer selon le plan",
        "is_active": True,
    }


@pytest.fixture
def control_template_entity():
    """Entité template de contrôle pour les tests"""
    template = QualityControlTemplate(
        id=1,
        tenant_id=1,
        code="TPL-001",
        name="Contrôle dimensionnel",
        description="Vérification des dimensions critiques",
        version="1.0",
        control_type=ControlType.RECEIVING,
        applies_to="PRODUCT",
        instructions="Mesurer selon le plan",
        is_active=True,
        created_by=101,
        created_at=datetime.now(),
    )
    template.items = []
    return template


# ============================================================================
# DATA FIXTURES - Contrôles Qualité
# ============================================================================

@pytest.fixture
def control_data():
    """Données pour créer un contrôle"""
    return {
        "template_id": 1,
        "control_type": "RECEIVING",
        "source_type": "PURCHASE",
        "product_id": 1,
        "lot_number": "LOT-2024-001",
        "quantity_to_control": 100,
        "control_date": date.today().isoformat(),
        "location": "Zone réception",
    }


@pytest.fixture
def control_entity():
    """Entité contrôle pour les tests"""
    control = QualityControl(
        id=1,
        tenant_id=1,
        control_number="QC-2024-00001",
        template_id=1,
        control_type=ControlType.RECEIVING,
        source_type="PURCHASE",
        product_id=1,
        lot_number="LOT-2024-001",
        quantity_to_control=Decimal("100"),
        control_date=date.today(),
        location="Zone réception",
        status=ControlStatus.PLANNED,
        controller_id=101,
        created_by=101,
        created_at=datetime.now(),
    )
    control.lines = []
    return control


# ============================================================================
# DATA FIXTURES - Audits
# ============================================================================

@pytest.fixture
def audit_data():
    """Données pour créer un audit"""
    return {
        "title": "Audit ISO 9001",
        "description": "Audit de surveillance annuel",
        "audit_type": "INTERNAL",
        "reference_standard": "ISO 9001:2015",
        "audit_scope": "Système qualité complet",
        "planned_date": date.today().isoformat(),
        "lead_auditor_id": 1,
        "audited_entity": "Production",
    }


@pytest.fixture
def audit_entity():
    """Entité audit pour les tests"""
    audit = QualityAudit(
        id=1,
        tenant_id=1,
        audit_number="AUD-2024-0001",
        title="Audit ISO 9001",
        description="Audit de surveillance annuel",
        audit_type=AuditType.INTERNAL,
        reference_standard="ISO 9001:2015",
        audit_scope="Système qualité complet",
        planned_date=date.today(),
        lead_auditor_id=1,
        audited_entity="Production",
        status=AuditStatus.PLANNED,
        created_by=101,
        created_at=datetime.now(),
    )
    audit.findings = []
    return audit


# ============================================================================
# DATA FIXTURES - Constats d'Audit
# ============================================================================

@pytest.fixture
def audit_finding_data():
    """Données pour créer un constat d'audit"""
    return {
        "title": "Procédure non suivie",
        "description": "La procédure de contrôle n'est pas respectée",
        "severity": "MAJOR",
        "category": "PROCESS",
        "clause_reference": "8.5.1",
        "evidence": "Observation sur site",
        "capa_required": True,
    }


@pytest.fixture
def audit_finding_entity():
    """Entité constat d'audit pour les tests"""
    return AuditFinding(
        id=1,
        tenant_id=1,
        audit_id=1,
        finding_number=1,
        title="Procédure non suivie",
        description="La procédure de contrôle n'est pas respectée",
        severity=FindingSeverity.MAJOR,
        category="PROCESS",
        clause_reference="8.5.1",
        evidence="Observation sur site",
        capa_required=True,
        status="OPEN",
        created_by=101,
        created_at=datetime.now(),
    )


# ============================================================================
# DATA FIXTURES - CAPA
# ============================================================================

@pytest.fixture
def capa_data():
    """Données pour créer un CAPA"""
    return {
        "title": "Amélioration du processus de contrôle",
        "description": "Mettre en place un contrôle statistique",
        "capa_type": "PREVENTIVE",
        "source_type": "AUDIT",
        "source_id": 1,
        "priority": "HIGH",
        "open_date": date.today().isoformat(),
        "target_close_date": date.today().isoformat(),
        "owner_id": 1,
        "department": "Quality",
        "problem_statement": "Trop de variations dans les résultats",
    }


@pytest.fixture
def capa_entity():
    """Entité CAPA pour les tests"""
    capa = CAPA(
        id=1,
        tenant_id=1,
        capa_number="CAPA-2024-0001",
        title="Amélioration du processus de contrôle",
        description="Mettre en place un contrôle statistique",
        capa_type=CAPAType.PREVENTIVE,
        source_type="AUDIT",
        source_id=1,
        status=CAPAStatus.OPEN,
        priority="HIGH",
        open_date=date.today(),
        target_close_date=date.today(),
        owner_id=1,
        department="Quality",
        problem_statement="Trop de variations dans les résultats",
        created_by=101,
        created_at=datetime.now(),
    )
    capa.actions = []
    return capa


# ============================================================================
# DATA FIXTURES - Actions CAPA
# ============================================================================

@pytest.fixture
def capa_action_data():
    """Données pour créer une action CAPA"""
    return {
        "action_type": "PREVENTIVE",
        "description": "Former les opérateurs au SPC",
        "responsible_id": 1,
        "planned_date": date.today().isoformat(),
        "due_date": date.today().isoformat(),
        "verification_required": True,
    }


@pytest.fixture
def capa_action_entity():
    """Entité action CAPA pour les tests"""
    return CAPAAction(
        id=1,
        tenant_id=1,
        capa_id=1,
        action_number=1,
        action_type="PREVENTIVE",
        description="Former les opérateurs au SPC",
        responsible_id=1,
        planned_date=date.today(),
        due_date=date.today(),
        status="PLANNED",
        verification_required=True,
        created_by=101,
        created_at=datetime.now(),
    )


# ============================================================================
# DATA FIXTURES - Réclamations
# ============================================================================

@pytest.fixture
def claim_data():
    """Données pour créer une réclamation"""
    return {
        "title": "Produit défectueux",
        "description": "Le client a reçu des pièces non conformes",
        "customer_id": 1,
        "customer_contact": "client@example.com",
        "received_date": date.today().isoformat(),
        "received_via": "EMAIL",
        "product_id": 1,
        "lot_number": "LOT-2024-001",
        "quantity_affected": 5,
        "claim_type": "QUALITY",
        "severity": "HIGH",
        "priority": "HIGH",
        "owner_id": 1,
    }


@pytest.fixture
def claim_entity():
    """Entité réclamation pour les tests"""
    claim = CustomerClaim(
        id=1,
        tenant_id=1,
        claim_number="REC-2024-00001",
        title="Produit défectueux",
        description="Le client a reçu des pièces non conformes",
        customer_id=1,
        customer_contact="client@example.com",
        received_date=date.today(),
        received_via="EMAIL",
        received_by_id=101,
        product_id=1,
        lot_number="LOT-2024-001",
        quantity_affected=Decimal("5"),
        claim_type="QUALITY",
        severity="HIGH",
        priority="HIGH",
        status=ClaimStatus.RECEIVED,
        owner_id=1,
        created_by=101,
        created_at=datetime.now(),
    )
    claim.actions = []
    return claim


# ============================================================================
# DATA FIXTURES - Actions Réclamation
# ============================================================================

@pytest.fixture
def claim_action_data():
    """Données pour créer une action réclamation"""
    return {
        "action_type": "IMMEDIATE",
        "description": "Remplacer les pièces défectueuses",
        "responsible_id": 1,
        "due_date": date.today().isoformat(),
    }


@pytest.fixture
def claim_action_entity():
    """Entité action réclamation pour les tests"""
    return ClaimAction(
        id=1,
        tenant_id=1,
        claim_id=1,
        action_number=1,
        action_type="IMMEDIATE",
        description="Remplacer les pièces défectueuses",
        responsible_id=1,
        due_date=date.today(),
        status="PLANNED",
        created_by=101,
        created_at=datetime.now(),
    )


# ============================================================================
# DATA FIXTURES - Indicateurs
# ============================================================================

@pytest.fixture
def indicator_data():
    """Données pour créer un indicateur"""
    return {
        "code": "IND-001",
        "name": "Taux de conformité",
        "description": "Pourcentage de pièces conformes",
        "category": "QUALITY",
        "formula": "(Conformes / Total) * 100",
        "unit": "%",
        "target_value": 98,
        "target_min": 95,
        "target_max": 100,
        "direction": "HIGHER_BETTER",
        "measurement_frequency": "MONTHLY",
        "owner_id": 1,
    }


@pytest.fixture
def indicator_entity():
    """Entité indicateur pour les tests"""
    indicator = QualityIndicator(
        id=1,
        tenant_id=1,
        code="IND-001",
        name="Taux de conformité",
        description="Pourcentage de pièces conformes",
        category="QUALITY",
        formula="(Conformes / Total) * 100",
        unit="%",
        target_value=Decimal("98"),
        target_min=Decimal("95"),
        target_max=Decimal("100"),
        direction="HIGHER_BETTER",
        measurement_frequency="MONTHLY",
        owner_id=1,
        is_active=True,
        created_by=101,
        created_at=datetime.now(),
    )
    indicator.measurements = []
    return indicator


# ============================================================================
# DATA FIXTURES - Mesures d'Indicateurs
# ============================================================================

@pytest.fixture
def indicator_measurement_data():
    """Données pour créer une mesure d'indicateur"""
    return {
        "measurement_date": date.today().isoformat(),
        "period_start": date.today().isoformat(),
        "period_end": date.today().isoformat(),
        "value": 97.5,
        "numerator": 975,
        "denominator": 1000,
    }


@pytest.fixture
def indicator_measurement_entity():
    """Entité mesure d'indicateur pour les tests"""
    return IndicatorMeasurement(
        id=1,
        tenant_id=1,
        indicator_id=1,
        measurement_date=date.today(),
        period_start=date.today(),
        period_end=date.today(),
        value=Decimal("97.5"),
        numerator=Decimal("975"),
        denominator=Decimal("1000"),
        target_value=Decimal("98"),
        status="ON_TARGET",
        created_by=101,
        created_at=datetime.now(),
    )


# ============================================================================
# DATA FIXTURES - Certifications
# ============================================================================

@pytest.fixture
def certification_data():
    """Données pour créer une certification"""
    return {
        "code": "ISO-9001",
        "name": "ISO 9001:2015",
        "description": "Système de management de la qualité",
        "standard": "ISO 9001",
        "standard_version": "2015",
        "scope": "Conception et fabrication",
        "certification_body": "Bureau Veritas",
        "initial_certification_date": date.today().isoformat(),
        "manager_id": 1,
    }


@pytest.fixture
def certification_entity():
    """Entité certification pour les tests"""
    certification = Certification(
        id=1,
        tenant_id=1,
        code="ISO-9001",
        name="ISO 9001:2015",
        description="Système de management de la qualité",
        standard="ISO 9001",
        standard_version="2015",
        scope="Conception et fabrication",
        certification_body="Bureau Veritas",
        initial_certification_date=date.today(),
        status=CertificationStatus.CERTIFIED,
        manager_id=1,
        created_by=101,
        created_at=datetime.now(),
    )
    certification.audits = []
    return certification


# ============================================================================
# DATA FIXTURES - Audits de Certification
# ============================================================================

@pytest.fixture
def certification_audit_data():
    """Données pour créer un audit de certification"""
    return {
        "audit_type": "SURVEILLANCE",
        "audit_date": date.today().isoformat(),
        "lead_auditor": "Jean Dupont",
    }


@pytest.fixture
def certification_audit_entity():
    """Entité audit de certification pour les tests"""
    return CertificationAudit(
        id=1,
        tenant_id=1,
        certification_id=1,
        audit_type="SURVEILLANCE",
        audit_date=date.today(),
        lead_auditor="Jean Dupont",
        created_by=101,
        created_at=datetime.now(),
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def assert_response_model(response_data: dict, expected_fields: list[str]):
    """Vérifie que la réponse contient tous les champs attendus"""
    for field in expected_fields:
        assert field in response_data, f"Field '{field}' missing in response"


def assert_paginated_response(response_data: dict, expected_total: int = None):
    """Vérifie la structure d'une réponse paginée"""
    assert "items" in response_data
    assert "total" in response_data
    assert "skip" in response_data
    assert "limit" in response_data
    assert isinstance(response_data["items"], list)
    if expected_total is not None:
        assert response_data["total"] == expected_total
