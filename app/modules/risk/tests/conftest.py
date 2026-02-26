"""
Fixtures de test pour le module Risk Management - GAP-075
=========================================================
"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.modules.risk.models import (
    RiskMatrix, Risk, Control, MitigationAction,
    RiskIndicator, RiskAssessment, RiskIncident,
    RiskCategory, RiskStatus, Probability, Impact, RiskLevel,
    MitigationStrategy, ActionStatus, ControlType, ControlEffectiveness,
    IndicatorStatus, IncidentStatus
)
from app.modules.risk.repository import (
    RiskMatrixRepository, RiskRepository, ControlRepository,
    MitigationActionRepository, RiskIndicatorRepository,
    RiskAssessmentRepository, RiskIncidentRepository
)
from app.modules.risk.service import RiskService


# ============== Database Fixtures ==============

@pytest.fixture(scope="function")
def db_engine():
    """Moteur SQLAlchemy en mémoire pour les tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Session de base de données pour les tests."""
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ============== Tenant Fixtures ==============

@pytest.fixture
def tenant_id() -> UUID:
    """ID du tenant principal pour les tests."""
    return uuid4()


@pytest.fixture
def other_tenant_id() -> UUID:
    """ID d'un autre tenant pour les tests d'isolation."""
    return uuid4()


@pytest.fixture
def user_id() -> UUID:
    """ID de l'utilisateur pour les tests."""
    return uuid4()


@pytest.fixture
def other_user_id() -> UUID:
    """ID d'un autre utilisateur."""
    return uuid4()


# ============== Repository Fixtures ==============

@pytest.fixture
def matrix_repo(db_session: Session, tenant_id: UUID) -> RiskMatrixRepository:
    """Repository des matrices de risques."""
    return RiskMatrixRepository(db_session, tenant_id)


@pytest.fixture
def risk_repo(db_session: Session, tenant_id: UUID) -> RiskRepository:
    """Repository des risques."""
    return RiskRepository(db_session, tenant_id)


@pytest.fixture
def control_repo(db_session: Session, tenant_id: UUID) -> ControlRepository:
    """Repository des contrôles."""
    return ControlRepository(db_session, tenant_id)


@pytest.fixture
def action_repo(db_session: Session, tenant_id: UUID) -> MitigationActionRepository:
    """Repository des actions."""
    return MitigationActionRepository(db_session, tenant_id)


@pytest.fixture
def indicator_repo(db_session: Session, tenant_id: UUID) -> RiskIndicatorRepository:
    """Repository des indicateurs."""
    return RiskIndicatorRepository(db_session, tenant_id)


@pytest.fixture
def assessment_repo(db_session: Session, tenant_id: UUID) -> RiskAssessmentRepository:
    """Repository des évaluations."""
    return RiskAssessmentRepository(db_session, tenant_id)


@pytest.fixture
def incident_repo(db_session: Session, tenant_id: UUID) -> RiskIncidentRepository:
    """Repository des incidents."""
    return RiskIncidentRepository(db_session, tenant_id)


# ============== Service Fixtures ==============

@pytest.fixture
def risk_service(db_session: Session, tenant_id: UUID, user_id: UUID) -> RiskService:
    """Service de gestion des risques."""
    return RiskService(db_session, tenant_id, user_id)


@pytest.fixture
def other_tenant_service(db_session: Session, other_tenant_id: UUID, other_user_id: UUID) -> RiskService:
    """Service pour un autre tenant (tests d'isolation)."""
    return RiskService(db_session, other_tenant_id, other_user_id)


# ============== RiskMatrix Fixtures ==============

@pytest.fixture
def sample_matrix(db_session: Session, tenant_id: UUID, user_id: UUID) -> RiskMatrix:
    """Matrice de risques exemple."""
    matrix = RiskMatrix(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Matrice Standard",
        code="MAT-001",
        description="Matrice de risques standard",
        probability_scale=5,
        impact_scale=5,
        low_threshold=4,
        medium_threshold=9,
        high_threshold=15,
        probability_labels={"1": "Rare", "2": "Unlikely", "3": "Possible", "4": "Likely", "5": "Almost Certain"},
        impact_labels={"1": "Negligible", "2": "Minor", "3": "Moderate", "4": "Major", "5": "Catastrophic"},
        is_default=True,
        is_active=True,
        created_by=user_id
    )
    db_session.add(matrix)
    db_session.flush()
    return matrix


@pytest.fixture
def other_tenant_matrix(db_session: Session, other_tenant_id: UUID, other_user_id: UUID) -> RiskMatrix:
    """Matrice d'un autre tenant."""
    matrix = RiskMatrix(
        id=uuid4(),
        tenant_id=other_tenant_id,
        name="Other Tenant Matrix",
        code="MAT-001",
        description="Matrice autre tenant",
        is_default=True,
        is_active=True,
        created_by=other_user_id
    )
    db_session.add(matrix)
    db_session.flush()
    return matrix


# ============== Risk Fixtures ==============

@pytest.fixture
def sample_risk(db_session: Session, tenant_id: UUID, user_id: UUID, sample_matrix: RiskMatrix) -> Risk:
    """Risque exemple."""
    risk = Risk(
        id=uuid4(),
        tenant_id=tenant_id,
        code="RSK-0001",
        title="Risque de cybersécurité",
        description="Risque de violation de données",
        category=RiskCategory.SECURITY,
        status=RiskStatus.IDENTIFIED,
        matrix_id=sample_matrix.id,
        inherent_probability=Probability.LIKELY,
        inherent_impact=Impact.MAJOR,
        inherent_score=16,
        inherent_level=RiskLevel.CRITICAL,
        owner_id=user_id,
        mitigation_strategy=MitigationStrategy.REDUCE,
        causes=["Faiblesse du système", "Manque de formation"],
        consequences=["Perte de données", "Amende RGPD"],
        created_by=user_id
    )
    db_session.add(risk)
    db_session.flush()
    return risk


@pytest.fixture
def other_tenant_risk(db_session: Session, other_tenant_id: UUID, other_user_id: UUID) -> Risk:
    """Risque d'un autre tenant."""
    risk = Risk(
        id=uuid4(),
        tenant_id=other_tenant_id,
        code="RSK-0001",
        title="Risque autre tenant",
        description="Description",
        category=RiskCategory.OPERATIONAL,
        status=RiskStatus.IDENTIFIED,
        inherent_probability=Probability.POSSIBLE,
        inherent_impact=Impact.MODERATE,
        inherent_score=9,
        inherent_level=RiskLevel.MEDIUM,
        created_by=other_user_id
    )
    db_session.add(risk)
    db_session.flush()
    return risk


@pytest.fixture
def assessed_risk(db_session: Session, tenant_id: UUID, user_id: UUID) -> Risk:
    """Risque évalué."""
    risk = Risk(
        id=uuid4(),
        tenant_id=tenant_id,
        code="RSK-0002",
        title="Risque évalué",
        description="Risque avec évaluation complète",
        category=RiskCategory.FINANCIAL,
        status=RiskStatus.ASSESSED,
        inherent_probability=Probability.LIKELY,
        inherent_impact=Impact.MAJOR,
        inherent_score=16,
        inherent_level=RiskLevel.CRITICAL,
        residual_probability=Probability.POSSIBLE,
        residual_impact=Impact.MODERATE,
        residual_score=9,
        residual_level=RiskLevel.MEDIUM,
        last_assessed_at=datetime.utcnow(),
        created_by=user_id
    )
    db_session.add(risk)
    db_session.flush()
    return risk


@pytest.fixture
def closed_risk(db_session: Session, tenant_id: UUID, user_id: UUID) -> Risk:
    """Risque clôturé."""
    risk = Risk(
        id=uuid4(),
        tenant_id=tenant_id,
        code="RSK-0003",
        title="Risque clôturé",
        description="Risque fermé",
        category=RiskCategory.OPERATIONAL,
        status=RiskStatus.CLOSED,
        inherent_probability=Probability.RARE,
        inherent_impact=Impact.MINOR,
        inherent_score=2,
        inherent_level=RiskLevel.LOW,
        closed_at=datetime.utcnow(),
        created_by=user_id
    )
    db_session.add(risk)
    db_session.flush()
    return risk


# ============== Control Fixtures ==============

@pytest.fixture
def sample_control(db_session: Session, tenant_id: UUID, user_id: UUID, sample_risk: Risk) -> Control:
    """Contrôle exemple."""
    control = Control(
        id=uuid4(),
        tenant_id=tenant_id,
        risk_id=sample_risk.id,
        code="CTL-0001",
        name="Pare-feu",
        description="Pare-feu de dernière génération",
        control_type=ControlType.PREVENTIVE,
        effectiveness=ControlEffectiveness.HIGHLY_EFFECTIVE,
        cost=Decimal("50000.00"),
        owner_id=user_id,
        frequency="continuous",
        is_automated=True,
        is_active=True,
        created_by=user_id
    )
    db_session.add(control)
    db_session.flush()
    return control


@pytest.fixture
def other_tenant_control(db_session: Session, other_tenant_id: UUID, other_user_id: UUID, other_tenant_risk: Risk) -> Control:
    """Contrôle d'un autre tenant."""
    control = Control(
        id=uuid4(),
        tenant_id=other_tenant_id,
        risk_id=other_tenant_risk.id,
        code="CTL-0001",
        name="Contrôle autre tenant",
        description="Description",
        control_type=ControlType.DETECTIVE,
        effectiveness=ControlEffectiveness.EFFECTIVE,
        is_active=True,
        created_by=other_user_id
    )
    db_session.add(control)
    db_session.flush()
    return control


# ============== MitigationAction Fixtures ==============

@pytest.fixture
def sample_action(db_session: Session, tenant_id: UUID, user_id: UUID, sample_risk: Risk) -> MitigationAction:
    """Action de mitigation exemple."""
    action = MitigationAction(
        id=uuid4(),
        tenant_id=tenant_id,
        risk_id=sample_risk.id,
        code="ACT-0001",
        title="Mise à jour du pare-feu",
        description="Mettre à jour les règles du pare-feu",
        status=ActionStatus.PLANNED,
        assignee_id=user_id,
        planned_start=date.today(),
        planned_end=date.today() + timedelta(days=30),
        estimated_cost=Decimal("5000.00"),
        priority=5,
        created_by=user_id
    )
    db_session.add(action)
    db_session.flush()
    return action


@pytest.fixture
def in_progress_action(db_session: Session, tenant_id: UUID, user_id: UUID, sample_risk: Risk) -> MitigationAction:
    """Action en cours."""
    action = MitigationAction(
        id=uuid4(),
        tenant_id=tenant_id,
        risk_id=sample_risk.id,
        code="ACT-0002",
        title="Action en cours",
        description="Description",
        status=ActionStatus.IN_PROGRESS,
        assignee_id=user_id,
        planned_start=date.today() - timedelta(days=5),
        planned_end=date.today() + timedelta(days=25),
        actual_start=date.today() - timedelta(days=5),
        progress_percent=50,
        created_by=user_id
    )
    db_session.add(action)
    db_session.flush()
    return action


@pytest.fixture
def overdue_action(db_session: Session, tenant_id: UUID, user_id: UUID, sample_risk: Risk) -> MitigationAction:
    """Action en retard."""
    action = MitigationAction(
        id=uuid4(),
        tenant_id=tenant_id,
        risk_id=sample_risk.id,
        code="ACT-0003",
        title="Action en retard",
        description="Description",
        status=ActionStatus.IN_PROGRESS,
        assignee_id=user_id,
        planned_start=date.today() - timedelta(days=60),
        planned_end=date.today() - timedelta(days=30),
        actual_start=date.today() - timedelta(days=60),
        progress_percent=30,
        created_by=user_id
    )
    db_session.add(action)
    db_session.flush()
    return action


@pytest.fixture
def other_tenant_action(db_session: Session, other_tenant_id: UUID, other_user_id: UUID, other_tenant_risk: Risk) -> MitigationAction:
    """Action d'un autre tenant."""
    action = MitigationAction(
        id=uuid4(),
        tenant_id=other_tenant_id,
        risk_id=other_tenant_risk.id,
        code="ACT-0001",
        title="Action autre tenant",
        description="Description",
        status=ActionStatus.PLANNED,
        created_by=other_user_id
    )
    db_session.add(action)
    db_session.flush()
    return action


# ============== RiskIndicator Fixtures ==============

@pytest.fixture
def sample_indicator(db_session: Session, tenant_id: UUID, user_id: UUID, sample_risk: Risk) -> RiskIndicator:
    """Indicateur exemple."""
    indicator = RiskIndicator(
        id=uuid4(),
        tenant_id=tenant_id,
        risk_id=sample_risk.id,
        code="KRI-0001",
        name="Nombre d'incidents de sécurité",
        description="Nombre d'incidents par mois",
        metric_type="count",
        unit="incidents",
        current_value=Decimal("5"),
        green_threshold=Decimal("3"),
        amber_threshold=Decimal("7"),
        red_threshold=Decimal("10"),
        higher_is_worse=True,
        current_status=IndicatorStatus.AMBER,
        measurement_frequency="monthly",
        is_active=True,
        created_by=user_id
    )
    db_session.add(indicator)
    db_session.flush()
    return indicator


@pytest.fixture
def red_indicator(db_session: Session, tenant_id: UUID, user_id: UUID, sample_risk: Risk) -> RiskIndicator:
    """Indicateur en alerte rouge."""
    indicator = RiskIndicator(
        id=uuid4(),
        tenant_id=tenant_id,
        risk_id=sample_risk.id,
        code="KRI-0002",
        name="Temps de réponse moyen",
        description="Temps de réponse aux incidents",
        metric_type="duration",
        unit="hours",
        current_value=Decimal("48"),
        green_threshold=Decimal("4"),
        amber_threshold=Decimal("8"),
        red_threshold=Decimal("24"),
        higher_is_worse=True,
        current_status=IndicatorStatus.RED,
        measurement_frequency="weekly",
        is_active=True,
        created_by=user_id
    )
    db_session.add(indicator)
    db_session.flush()
    return indicator


@pytest.fixture
def other_tenant_indicator(db_session: Session, other_tenant_id: UUID, other_user_id: UUID, other_tenant_risk: Risk) -> RiskIndicator:
    """Indicateur d'un autre tenant."""
    indicator = RiskIndicator(
        id=uuid4(),
        tenant_id=other_tenant_id,
        risk_id=other_tenant_risk.id,
        code="KRI-0001",
        name="Indicateur autre tenant",
        description="Description",
        metric_type="count",
        current_value=Decimal("10"),
        green_threshold=Decimal("5"),
        amber_threshold=Decimal("15"),
        red_threshold=Decimal("25"),
        higher_is_worse=True,
        current_status=IndicatorStatus.AMBER,
        is_active=True,
        created_by=other_user_id
    )
    db_session.add(indicator)
    db_session.flush()
    return indicator


# ============== RiskAssessment Fixtures ==============

@pytest.fixture
def sample_assessment(db_session: Session, tenant_id: UUID, user_id: UUID, sample_risk: Risk) -> RiskAssessment:
    """Évaluation exemple."""
    assessment = RiskAssessment(
        id=uuid4(),
        tenant_id=tenant_id,
        risk_id=sample_risk.id,
        assessor_id=user_id,
        probability=Probability.LIKELY,
        impact=Impact.MAJOR,
        score=16,
        level=RiskLevel.CRITICAL,
        assessment_type="initial",
        rationale="Évaluation initiale du risque",
        is_validated=False,
        created_by=user_id
    )
    db_session.add(assessment)
    db_session.flush()
    return assessment


@pytest.fixture
def validated_assessment(db_session: Session, tenant_id: UUID, user_id: UUID, sample_risk: Risk) -> RiskAssessment:
    """Évaluation validée."""
    assessment = RiskAssessment(
        id=uuid4(),
        tenant_id=tenant_id,
        risk_id=sample_risk.id,
        assessor_id=user_id,
        probability=Probability.POSSIBLE,
        impact=Impact.MODERATE,
        score=9,
        level=RiskLevel.MEDIUM,
        assessment_type="periodic",
        is_validated=True,
        validated_by=user_id,
        validated_at=datetime.utcnow(),
        created_by=user_id
    )
    db_session.add(assessment)
    db_session.flush()
    return assessment


# ============== RiskIncident Fixtures ==============

@pytest.fixture
def sample_incident(db_session: Session, tenant_id: UUID, user_id: UUID, sample_risk: Risk) -> RiskIncident:
    """Incident exemple."""
    incident = RiskIncident(
        id=uuid4(),
        tenant_id=tenant_id,
        risk_id=sample_risk.id,
        code="INC-0001",
        title="Tentative d'intrusion détectée",
        description="Tentative d'accès non autorisé",
        status=IncidentStatus.OPEN,
        occurred_at=datetime.utcnow() - timedelta(hours=2),
        detected_at=datetime.utcnow() - timedelta(hours=1),
        actual_impact=Impact.MINOR,
        financial_loss=Decimal("1000.00"),
        root_cause="Mot de passe faible",
        reporter_id=user_id,
        created_by=user_id
    )
    db_session.add(incident)
    db_session.flush()
    return incident


@pytest.fixture
def resolved_incident(db_session: Session, tenant_id: UUID, user_id: UUID, sample_risk: Risk) -> RiskIncident:
    """Incident résolu."""
    incident = RiskIncident(
        id=uuid4(),
        tenant_id=tenant_id,
        risk_id=sample_risk.id,
        code="INC-0002",
        title="Incident résolu",
        description="Description",
        status=IncidentStatus.RESOLVED,
        occurred_at=datetime.utcnow() - timedelta(days=7),
        detected_at=datetime.utcnow() - timedelta(days=7),
        resolved_at=datetime.utcnow() - timedelta(days=5),
        actual_impact=Impact.MINOR,
        financial_loss=Decimal("500.00"),
        lessons_learned="Renforcer les mots de passe",
        reporter_id=user_id,
        created_by=user_id
    )
    db_session.add(incident)
    db_session.flush()
    return incident


@pytest.fixture
def other_tenant_incident(db_session: Session, other_tenant_id: UUID, other_user_id: UUID, other_tenant_risk: Risk) -> RiskIncident:
    """Incident d'un autre tenant."""
    incident = RiskIncident(
        id=uuid4(),
        tenant_id=other_tenant_id,
        risk_id=other_tenant_risk.id,
        code="INC-0001",
        title="Incident autre tenant",
        description="Description",
        status=IncidentStatus.OPEN,
        occurred_at=datetime.utcnow(),
        actual_impact=Impact.MODERATE,
        reporter_id=other_user_id,
        created_by=other_user_id
    )
    db_session.add(incident)
    db_session.flush()
    return incident
