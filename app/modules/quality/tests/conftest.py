"""
Fixtures pour les tests du module Quality - CORE SaaS v2
=========================================================

Ce module fournit les fixtures pytest pour tester le module Quality.
Les fixtures utilisent le pattern dependency_overrides de FastAPI pour
injecter les mocks correctement et un TestClient avec headers d'auth.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext, UserRole, TenantScope
from app.main import app
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
# UTILITAIRES MOCK
# ============================================================================

class MockEntity:
    """
    Classe utilitaire qui convertit un dict en objet avec accès par attributs.

    Permet aux fixtures de retourner des objets compatibles avec les serializers
    qui utilisent la notation point (ex: nc.id, audit.reference).

    IMPORTANT: Les attributs non définis retournent None (comme les modèles SQLAlchemy)
    au lieu de lever AttributeError.
    """

    def __init__(self, data: Dict[str, Any]):
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
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return None

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self._data.items())
        return f"MockEntity({attrs})"

    def keys(self):
        return self._data.keys()

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key: str):
        return self._data.get(key)

    def with_updates(self, **updates) -> "MockEntity":
        new_data = {**self._data, **updates}
        return MockEntity(new_data)


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
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


@pytest.fixture
def mock_saas_context(saas_context):
    """Alias pour saas_context du conftest global."""
    return saas_context


@pytest.fixture
def mock_get_saas_context(saas_context):
    """Mock de get_saas_context avec contexte valide pour tests."""
    def _mock_context():
        return saas_context
    return _mock_context


# ============================================================================
# MOCK QUALITY SERVICE
# ============================================================================

@pytest.fixture
def mock_quality_service():
    """Mock QualityService pour les tests"""
    mock_service = MagicMock()

    # Configuration par défaut - Non-Conformances
    mock_service.create_non_conformance.return_value = None
    mock_service.list_non_conformances.return_value = ([], 0)
    mock_service.get_non_conformance.return_value = None
    mock_service.update_non_conformance.return_value = None
    mock_service.open_non_conformance.return_value = None
    mock_service.close_non_conformance.return_value = None
    mock_service.add_nc_action.return_value = None
    mock_service.update_nc_action.return_value = None

    # Control Templates
    mock_service.create_control_template.return_value = None
    mock_service.list_control_templates.return_value = ([], 0)
    mock_service.get_control_template.return_value = None
    mock_service.update_control_template.return_value = None
    mock_service.add_template_item.return_value = None

    # Controls
    mock_service.create_control.return_value = None
    mock_service.list_controls.return_value = ([], 0)
    mock_service.get_control.return_value = None
    mock_service.update_control.return_value = None
    mock_service.start_control.return_value = None
    mock_service.update_control_line.return_value = None
    mock_service.complete_control.return_value = None

    # Audits
    mock_service.create_audit.return_value = None
    mock_service.list_audits.return_value = ([], 0)
    mock_service.get_audit.return_value = None
    mock_service.update_audit.return_value = None
    mock_service.start_audit.return_value = None
    mock_service.add_finding.return_value = None
    mock_service.update_finding.return_value = None
    mock_service.close_audit.return_value = None

    # CAPA
    mock_service.create_capa.return_value = None
    mock_service.list_capas.return_value = ([], 0)
    mock_service.get_capa.return_value = None
    mock_service.update_capa.return_value = None
    mock_service.add_capa_action.return_value = None
    mock_service.update_capa_action.return_value = None
    mock_service.close_capa.return_value = None

    # Claims
    mock_service.create_claim.return_value = None
    mock_service.list_claims.return_value = ([], 0)
    mock_service.get_claim.return_value = None
    mock_service.update_claim.return_value = None
    mock_service.acknowledge_claim.return_value = None
    mock_service.respond_claim.return_value = None
    mock_service.resolve_claim.return_value = None
    mock_service.close_claim.return_value = None
    mock_service.add_claim_action.return_value = None

    # Indicators
    mock_service.create_indicator.return_value = None
    mock_service.list_indicators.return_value = ([], 0)
    mock_service.get_indicator.return_value = None
    mock_service.update_indicator.return_value = None
    mock_service.add_measurement.return_value = None

    # Certifications
    mock_service.create_certification.return_value = None
    mock_service.list_certifications.return_value = ([], 0)
    mock_service.get_certification.return_value = None
    mock_service.update_certification.return_value = None
    mock_service.add_certification_audit.return_value = None
    mock_service.update_certification_audit.return_value = None

    # Dashboard
    mock_service.get_dashboard.return_value = None

    return mock_service


# ============================================================================
# TEST CLIENT AVEC MOCKS
# ============================================================================

@pytest.fixture
def test_client(mock_get_saas_context, mock_quality_service, tenant_id, user_id):
    """
    Client de test FastAPI avec mocks et headers d'authentification.

    Utilise:
    - dependency_overrides pour get_saas_context
    - patch pour get_quality_service (appelé directement dans le router)
    - Headers X-Tenant-ID et Authorization pour passer le middleware auth
    """
    # Override get_saas_context
    app.dependency_overrides[get_saas_context] = mock_get_saas_context

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

    # Patch get_quality_service pour retourner le mock
    with patch("app.modules.quality.router_v2.get_quality_service") as mock_factory:
        mock_factory.return_value = mock_quality_service
        client = TestClientWithHeaders(app)
        # Stocker le service mock pour accès dans les tests
        client.mock_service = mock_quality_service
        yield client

    # Nettoyer les overrides
    app.dependency_overrides.clear()


# Pour compatibilité avec les tests qui utilisent 'client' au lieu de 'test_client'
@pytest.fixture
def client(test_client):
    """Alias pour test_client (compatibilité)"""
    return test_client


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
def nc_entity(tenant_id, user_id):
    """Entité non-conformité pour les tests (MockEntity)"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "nc_number": "NC-2024-00001",
        "title": "Pièce défectueuse",
        "description": "Surface rayée sur le produit",
        "nc_type": NonConformanceType.INTERNAL,
        "severity": NonConformanceSeverity.MAJOR,
        "status": NonConformanceStatus.OPEN,
        "detected_date": date.today(),
        "detected_by_id": 101,
        "detection_location": "Ligne A",
        "detection_phase": "PRODUCTION",
        "source_type": "PRODUCTION",
        "product_id": 1,
        "lot_number": "LOT-2024-001",
        "quantity_affected": Decimal("10"),
        "immediate_action": "Isoler les pièces défectueuses",
        "responsible_id": 1,
        # Champs obligatoires du schema NonConformanceResponse
        "capa_required": False,
        "capa_id": None,
        "effectiveness_verified": False,
        "is_recurrent": False,
        "recurrence_count": 0,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
        "actions": [],
    }
    return MockEntity(data)


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
def nc_action_entity(tenant_id):
    """Entité action NC pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "nc_id": 1,
        "action_number": 1,
        "action_type": "CORRECTIVE",
        "description": "Ajuster le réglage de la machine",
        "responsible_id": 1,
        "planned_date": date.today(),
        "due_date": date.today(),
        "completed_date": None,
        "status": "PLANNED",
        "verified": False,
        "verified_date": None,
        "comments": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
    }
    return MockEntity(data)


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
        "control_type": "INCOMING",  # INCOMING, pas RECEIVING (n'existe pas dans l'enum)
        "applies_to": "PRODUCT",
        "instructions": "Mesurer selon le plan",
        "is_active": True,
    }


@pytest.fixture
def control_template_entity(tenant_id):
    """Entité template de contrôle pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "code": "TPL-001",
        "name": "Contrôle dimensionnel",
        "description": "Vérification des dimensions critiques",
        "version": "1.0",
        "control_type": ControlType.INCOMING,
        "applies_to": "PRODUCT",
        "product_category_id": None,
        "instructions": "Mesurer selon le plan",
        "sampling_plan": None,
        "acceptance_criteria": None,
        "estimated_duration_minutes": None,
        "required_equipment": None,
        "is_active": True,
        "valid_from": None,
        "valid_until": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
        "items": [],
    }
    return MockEntity(data)


@pytest.fixture
def control_template_item_entity(tenant_id):
    """Entité item de template de contrôle pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "template_id": 1,
        "sequence": 1,
        "characteristic": "Longueur",
        "description": "Vérification de la longueur",
        "measurement_type": "NUMERIC",
        "unit": "mm",
        "nominal_value": Decimal("100.0"),
        "tolerance_min": Decimal("-0.5"),
        "tolerance_max": Decimal("0.5"),
        "upper_limit": Decimal("100.5"),
        "lower_limit": Decimal("99.5"),
        "expected_result": None,
        "measurement_method": None,
        "equipment_code": None,
        "is_critical": True,
        "is_mandatory": True,
        "sampling_frequency": None,
        "created_by": 101,
        "created_at": now,
    }
    return MockEntity(data)


# ============================================================================
# DATA FIXTURES - Contrôles Qualité
# ============================================================================

@pytest.fixture
def control_data():
    """Données pour créer un contrôle"""
    return {
        "template_id": 1,
        "control_type": "INCOMING",  # INCOMING, pas RECEIVING
        "source_type": "PURCHASE",
        "product_id": 1,
        "lot_number": "LOT-2024-001",
        "quantity_to_control": 100,
        "control_date": date.today().isoformat(),
        "location": "Zone réception",
    }


@pytest.fixture
def control_entity(tenant_id):
    """Entité contrôle pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "control_number": "QC-2024-00001",
        "template_id": 1,
        "control_type": ControlType.INCOMING,
        "control_date": date.today(),
        "source_type": "PURCHASE",
        "source_reference": None,
        "product_id": 1,
        "lot_number": "LOT-2024-001",
        "serial_number": None,
        "quantity_to_control": Decimal("100"),
        "quantity_controlled": None,
        "quantity_conforming": None,
        "quantity_non_conforming": None,
        "supplier_id": None,
        "customer_id": None,
        "start_time": None,
        "end_time": None,
        "location": "Zone réception",
        "controller_id": 101,
        "status": ControlStatus.PLANNED,
        "result": None,
        "result_date": None,
        "decision": None,
        "decision_by_id": None,
        "decision_date": None,
        "decision_comments": None,
        "nc_id": None,
        "observations": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
        "lines": [],
    }
    return MockEntity(data)


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
def audit_entity(tenant_id):
    """Entité audit pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "audit_number": "AUD-2024-0001",
        "title": "Audit ISO 9001",
        "description": "Audit de surveillance annuel",
        "audit_type": AuditType.INTERNAL,
        "reference_standard": "ISO 9001:2015",
        "reference_version": None,
        "audit_scope": "Système qualité complet",
        "planned_date": date.today(),
        "planned_end_date": None,
        "actual_date": None,
        "actual_end_date": None,
        "status": AuditStatus.PLANNED,
        "lead_auditor_id": 1,
        "auditors": None,
        "audited_entity": "Production",
        "audited_department": None,
        "auditee_contact_id": None,
        "supplier_id": None,
        # Champs obligatoires du schema AuditResponse
        "total_findings": 0,
        "critical_findings": 0,
        "major_findings": 0,
        "minor_findings": 0,
        "observations": 0,
        "overall_score": None,
        "max_score": None,
        "audit_conclusion": None,
        "recommendation": None,
        "report_date": None,
        "report_file": None,
        "follow_up_required": False,
        "follow_up_date": None,
        "follow_up_completed": False,
        "closed_date": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
        "findings": [],
    }
    return MockEntity(data)


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
def audit_finding_entity(tenant_id):
    """Entité constat d'audit pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "audit_id": 1,
        "finding_number": 1,
        "title": "Procédure non suivie",
        "description": "La procédure de contrôle n'est pas respectée",
        "severity": FindingSeverity.MAJOR,
        "category": "PROCESS",
        "clause_reference": "8.5.1",
        "process_reference": None,
        "evidence": "Observation sur site",
        "risk_description": None,
        "risk_level": None,
        "capa_required": True,
        "capa_id": None,
        "auditee_response": None,
        "response_date": None,
        "action_due_date": None,
        "action_completed_date": None,
        "status": "OPEN",
        "verified": False,
        "verified_date": None,
        "verification_comments": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
    }
    return MockEntity(data)


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
def capa_entity(tenant_id):
    """Entité CAPA pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "capa_number": "CAPA-2024-0001",
        "title": "Amélioration du processus de contrôle",
        "description": "Mettre en place un contrôle statistique",
        "capa_type": CAPAType.PREVENTIVE,
        "source_type": "AUDIT",
        "source_reference": None,
        "source_id": 1,
        "status": CAPAStatus.OPEN,
        "priority": "HIGH",
        "open_date": date.today(),
        "target_close_date": date.today(),
        "actual_close_date": None,
        "owner_id": 1,
        "department": "Quality",
        "problem_statement": "Trop de variations dans les résultats",
        "immediate_containment": None,
        "root_cause_analysis": None,
        "root_cause_method": None,
        "root_cause_verified": False,
        "impact_assessment": None,
        "risk_level": None,
        "effectiveness_criteria": None,
        "effectiveness_verified": False,
        "effectiveness_date": None,
        "effectiveness_result": None,
        "extension_required": False,
        "extension_scope": None,
        "extension_completed": False,
        "closure_comments": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
        "actions": [],
    }
    return MockEntity(data)


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
def capa_action_entity(tenant_id):
    """Entité action CAPA pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "capa_id": 1,
        "action_number": 1,
        "action_type": "PREVENTIVE",
        "description": "Former les opérateurs au SPC",
        "responsible_id": 1,
        "planned_date": date.today(),
        "due_date": date.today(),
        "completed_date": None,
        "status": "PLANNED",
        "result": None,
        "evidence": None,
        "verification_required": True,
        "verified": False,
        "verified_date": None,
        "verification_result": None,
        "estimated_cost": None,
        "actual_cost": None,
        "comments": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
    }
    return MockEntity(data)


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
        "severity": "MAJOR",
        "priority": "HIGH",
        "owner_id": 1,
    }


@pytest.fixture
def claim_entity(tenant_id):
    """Entité réclamation pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "claim_number": "REC-2024-00001",
        "title": "Produit défectueux",
        "description": "Le client a reçu des pièces non conformes",
        "customer_id": 1,
        "customer_contact": "client@example.com",
        "customer_reference": None,
        "received_date": date.today(),
        "received_via": "EMAIL",
        "received_by_id": 101,
        "product_id": 1,
        "order_reference": None,
        "invoice_reference": None,
        "lot_number": "LOT-2024-001",
        "quantity_affected": Decimal("5"),
        "claim_type": "QUALITY",
        "severity": NonConformanceSeverity.MAJOR,
        "priority": "HIGH",
        "status": ClaimStatus.RECEIVED,
        "owner_id": 1,
        "investigation_summary": None,
        "root_cause": None,
        "our_responsibility": None,
        "nc_id": None,
        "capa_id": None,
        "response_due_date": None,
        "response_date": None,
        "response_content": None,
        "resolution_type": None,
        "resolution_description": None,
        "resolution_date": None,
        "claim_amount": None,
        "accepted_amount": None,
        "customer_satisfied": None,
        "satisfaction_feedback": None,
        "closed_date": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
        "actions": [],
    }
    return MockEntity(data)


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
def claim_action_entity(tenant_id):
    """Entité action réclamation pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "claim_id": 1,
        "action_number": 1,
        "action_type": "IMMEDIATE",
        "description": "Remplacer les pièces défectueuses",
        "responsible_id": 1,
        "due_date": date.today(),
        "completed_date": None,
        "status": "PLANNED",
        "result": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
    }
    return MockEntity(data)


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
def indicator_entity(tenant_id):
    """Entité indicateur pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "code": "IND-001",
        "name": "Taux de conformité",
        "description": "Pourcentage de pièces conformes",
        "category": "QUALITY",
        "formula": "(Conformes / Total) * 100",
        "unit": "%",
        "target_value": Decimal("98"),
        "target_min": Decimal("95"),
        "target_max": Decimal("100"),
        "warning_threshold": None,
        "critical_threshold": None,
        "direction": "HIGHER_BETTER",
        "measurement_frequency": "MONTHLY",
        "data_source": None,
        "owner_id": 1,
        "is_active": True,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
        "measurements": [],
    }
    return MockEntity(data)


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
def indicator_measurement_entity(tenant_id):
    """Entité mesure d'indicateur pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "indicator_id": 1,
        "measurement_date": date.today(),
        "period_start": date.today(),
        "period_end": date.today(),
        "value": Decimal("97.5"),
        "numerator": Decimal("975"),
        "denominator": Decimal("1000"),
        "target_value": Decimal("98"),
        "deviation": None,
        "achievement_rate": None,
        "status": "ON_TARGET",
        "comments": None,
        "action_required": False,
        "source": "MANUAL",
        "created_by": 101,
        "created_at": now,
    }
    return MockEntity(data)


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
def certification_entity(tenant_id):
    """Entité certification pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "code": "ISO-9001",
        "name": "ISO 9001:2015",
        "description": "Système de management de la qualité",
        "standard": "ISO 9001",
        "standard_version": "2015",
        "scope": "Conception et fabrication",
        "certification_body": "Bureau Veritas",
        "certification_body_accreditation": None,
        "initial_certification_date": date.today(),
        "current_certificate_date": None,
        "expiry_date": None,
        "next_surveillance_date": None,
        "next_renewal_date": None,
        "certificate_number": None,
        "certificate_file": None,
        "status": CertificationStatus.CERTIFIED,
        "manager_id": 1,
        "annual_cost": None,
        "notes": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
        "audits": [],
    }
    return MockEntity(data)


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
def certification_audit_entity(tenant_id):
    """Entité audit de certification pour les tests"""
    now = datetime.now()
    data = {
        "id": 1,
        "tenant_id": int(tenant_id),
        "certification_id": 1,
        "audit_type": "SURVEILLANCE",
        "audit_date": date.today(),
        "audit_end_date": None,
        "lead_auditor": "Jean Dupont",
        "audit_team": None,
        "result": None,
        "findings_count": 0,
        "major_nc_count": 0,
        "minor_nc_count": 0,
        "observations_count": 0,
        "report_date": None,
        "report_file": None,
        "corrective_actions_due": None,
        "corrective_actions_closed": None,
        "follow_up_audit_date": None,
        "quality_audit_id": None,
        "notes": None,
        "created_by": 101,
        "created_at": now,
        "updated_at": now,
    }
    return MockEntity(data)


# ============================================================================
# DATA FIXTURES - Dashboard
# ============================================================================

@pytest.fixture
def dashboard_entity():
    """Entité dashboard qualité pour les tests.

    Utilise types.SimpleNamespace au lieu de MockEntity pour préserver
    les dictionnaires imbriqués (nc_by_type, nc_by_status, controls_by_type)
    qui sont requis par le schema Pydantic.
    """
    from types import SimpleNamespace

    return SimpleNamespace(
        # Non-conformités
        nc_total=10,
        nc_open=3,
        nc_critical=1,
        nc_by_type={"INTERNAL": 5, "SUPPLIER": 3, "CUSTOMER": 2},
        nc_by_status={"OPEN": 3, "IN_PROGRESS": 4, "CLOSED": 3},
        # Contrôles qualité
        controls_total=50,
        controls_completed=45,
        controls_pass_rate=Decimal("90.0"),
        controls_by_type={"INCOMING": 20, "PROCESS": 15, "FINAL": 15},
        # Audits
        audits_planned=5,
        audits_completed=3,
        audit_findings_open=2,
        # CAPA
        capa_total=8,
        capa_open=3,
        capa_overdue=1,
        capa_effectiveness_rate=Decimal("85.0"),
        # Réclamations clients
        claims_total=12,
        claims_open=4,
        claims_avg_resolution_days=Decimal("7.5"),
        claims_satisfaction_rate=Decimal("88.0"),
        # Certifications
        certifications_active=3,
        certifications_expiring_soon=1,
        # Indicateurs
        indicators_on_target=8,
        indicators_warning=2,
        indicators_critical=0,
        # Tendances
        nc_trend_30_days=[],
        control_trend_30_days=[],
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
