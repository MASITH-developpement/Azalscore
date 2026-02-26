"""
Fixtures de test pour le module Referral
========================================
"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4, UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.modules.referral.models import (
    ReferralProgram, ProgramStatus,
    RewardTier, RewardType, RewardTrigger,
    ReferralCode,
    Referral, ReferralStatus,
    Reward,
    Payout, PayoutStatus,
    FraudCheck, FraudReason
)
from app.modules.referral.service import ReferralService


# ============== Database Fixtures ==============

@pytest.fixture(scope="function")
def db_engine():
    """Crée un moteur SQLite en mémoire pour les tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Crée une session de base de données pour les tests."""
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ============== Tenant Fixtures ==============

@pytest.fixture
def tenant_a_id() -> UUID:
    """ID du tenant A."""
    return uuid4()


@pytest.fixture
def tenant_b_id() -> UUID:
    """ID du tenant B (pour tests d'isolation)."""
    return uuid4()


@pytest.fixture
def user_a_id() -> UUID:
    """ID d'un utilisateur du tenant A."""
    return uuid4()


@pytest.fixture
def user_b_id() -> UUID:
    """ID d'un utilisateur du tenant B."""
    return uuid4()


# ============== Service Fixtures ==============

@pytest.fixture
def service_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID):
    """Service Referral pour le tenant A."""
    return ReferralService(db_session, tenant_a_id, user_a_id)


@pytest.fixture
def service_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID):
    """Service Referral pour le tenant B."""
    return ReferralService(db_session, tenant_b_id, user_b_id)


# ============== Program Fixtures ==============

@pytest.fixture
def program_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> ReferralProgram:
    """Crée un programme pour le tenant A."""
    program = ReferralProgram(
        tenant_id=tenant_a_id,
        code="PROG-A-001",
        name="Programme Parrainage A",
        description="Programme de test tenant A",
        status=ProgramStatus.DRAFT,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        budget_total=Decimal("10000.00"),
        budget_used=Decimal("0"),
        max_referrals_per_referrer=10,
        max_referrals_total=1000,
        created_by=user_a_id
    )
    db_session.add(program)
    db_session.commit()
    db_session.refresh(program)
    return program


@pytest.fixture
def program_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID) -> ReferralProgram:
    """Crée un programme pour le tenant B."""
    program = ReferralProgram(
        tenant_id=tenant_b_id,
        code="PROG-B-001",
        name="Programme Parrainage B",
        description="Programme de test tenant B",
        status=ProgramStatus.ACTIVE,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=180),
        budget_total=Decimal("5000.00"),
        budget_used=Decimal("0"),
        max_referrals_per_referrer=5,
        max_referrals_total=500,
        created_by=user_b_id
    )
    db_session.add(program)
    db_session.commit()
    db_session.refresh(program)
    return program


@pytest.fixture
def program_active_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> ReferralProgram:
    """Crée un programme actif pour le tenant A."""
    program = ReferralProgram(
        tenant_id=tenant_a_id,
        code="PROG-A-ACTIVE",
        name="Programme Actif A",
        description="Programme actif pour tests",
        status=ProgramStatus.ACTIVE,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=300),
        budget_total=Decimal("50000.00"),
        budget_used=Decimal("1000.00"),
        max_referrals_per_referrer=20,
        max_referrals_total=5000,
        created_by=user_a_id
    )
    db_session.add(program)
    db_session.commit()
    db_session.refresh(program)
    return program


# ============== Reward Tier Fixtures ==============

@pytest.fixture
def tier_tenant_a(
    db_session: Session,
    tenant_a_id: UUID,
    program_tenant_a: ReferralProgram
) -> RewardTier:
    """Crée un palier de récompense pour le tenant A."""
    tier = RewardTier(
        tenant_id=tenant_a_id,
        program_id=program_tenant_a.id,
        level=1,
        name="Bronze",
        min_referrals=1,
        max_referrals=5,
        reward_type=RewardType.FIXED,
        reward_value=Decimal("50.00"),
        reward_trigger=RewardTrigger.CONVERSION,
        is_active=True
    )
    db_session.add(tier)
    db_session.commit()
    db_session.refresh(tier)
    return tier


@pytest.fixture
def tier_tenant_b(
    db_session: Session,
    tenant_b_id: UUID,
    program_tenant_b: ReferralProgram
) -> RewardTier:
    """Crée un palier de récompense pour le tenant B."""
    tier = RewardTier(
        tenant_id=tenant_b_id,
        program_id=program_tenant_b.id,
        level=1,
        name="Standard",
        min_referrals=1,
        max_referrals=10,
        reward_type=RewardType.PERCENTAGE,
        reward_value=Decimal("10.00"),
        reward_trigger=RewardTrigger.SIGNUP,
        is_active=True
    )
    db_session.add(tier)
    db_session.commit()
    db_session.refresh(tier)
    return tier


@pytest.fixture
def tiers_multi_level(
    db_session: Session,
    tenant_a_id: UUID,
    program_active_tenant_a: ReferralProgram
) -> list:
    """Crée plusieurs paliers pour le tenant A."""
    tiers = []
    tier_configs = [
        ("Bronze", 1, 5, Decimal("25.00")),
        ("Silver", 6, 15, Decimal("50.00")),
        ("Gold", 16, 30, Decimal("100.00")),
        ("Platinum", 31, None, Decimal("200.00")),
    ]
    for level, (name, min_ref, max_ref, value) in enumerate(tier_configs, 1):
        tier = RewardTier(
            tenant_id=tenant_a_id,
            program_id=program_active_tenant_a.id,
            level=level,
            name=name,
            min_referrals=min_ref,
            max_referrals=max_ref,
            reward_type=RewardType.FIXED,
            reward_value=value,
            reward_trigger=RewardTrigger.CONVERSION,
            is_active=True
        )
        db_session.add(tier)
        tiers.append(tier)
    db_session.commit()
    for t in tiers:
        db_session.refresh(t)
    return tiers


# ============== Referral Code Fixtures ==============

@pytest.fixture
def code_tenant_a(
    db_session: Session,
    tenant_a_id: UUID,
    program_active_tenant_a: ReferralProgram,
    user_a_id: UUID
) -> ReferralCode:
    """Crée un code de parrainage pour le tenant A."""
    code = ReferralCode(
        tenant_id=tenant_a_id,
        program_id=program_active_tenant_a.id,
        code="REFCODE-A-001",
        referrer_id=user_a_id,
        referrer_name="User A",
        max_uses=100,
        current_uses=0,
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=90)
    )
    db_session.add(code)
    db_session.commit()
    db_session.refresh(code)
    return code


@pytest.fixture
def code_tenant_b(
    db_session: Session,
    tenant_b_id: UUID,
    program_tenant_b: ReferralProgram,
    user_b_id: UUID
) -> ReferralCode:
    """Crée un code de parrainage pour le tenant B."""
    code = ReferralCode(
        tenant_id=tenant_b_id,
        program_id=program_tenant_b.id,
        code="REFCODE-B-001",
        referrer_id=user_b_id,
        referrer_name="User B",
        max_uses=50,
        current_uses=5,
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=60)
    )
    db_session.add(code)
    db_session.commit()
    db_session.refresh(code)
    return code


@pytest.fixture
def code_expired_tenant_a(
    db_session: Session,
    tenant_a_id: UUID,
    program_active_tenant_a: ReferralProgram,
    user_a_id: UUID
) -> ReferralCode:
    """Crée un code de parrainage expiré pour le tenant A."""
    code = ReferralCode(
        tenant_id=tenant_a_id,
        program_id=program_active_tenant_a.id,
        code="REFCODE-A-EXPIRED",
        referrer_id=user_a_id,
        referrer_name="User A",
        max_uses=100,
        current_uses=0,
        is_active=True,
        expires_at=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(code)
    db_session.commit()
    db_session.refresh(code)
    return code


# ============== Referral Fixtures ==============

@pytest.fixture
def referral_tenant_a(
    db_session: Session,
    tenant_a_id: UUID,
    program_active_tenant_a: ReferralProgram,
    code_tenant_a: ReferralCode,
    user_a_id: UUID
) -> Referral:
    """Crée un parrainage pour le tenant A."""
    referee_id = uuid4()
    referral = Referral(
        tenant_id=tenant_a_id,
        program_id=program_active_tenant_a.id,
        code_id=code_tenant_a.id,
        referrer_id=user_a_id,
        referrer_name="User A",
        referee_id=referee_id,
        referee_name="Referee A1",
        referee_email="referee.a1@example.com",
        status=ReferralStatus.PENDING,
        click_count=3,
        clicked_at=datetime.utcnow() - timedelta(hours=2),
        signed_up_at=datetime.utcnow() - timedelta(hours=1),
        created_by=user_a_id
    )
    db_session.add(referral)
    db_session.commit()
    db_session.refresh(referral)
    return referral


@pytest.fixture
def referral_tenant_b(
    db_session: Session,
    tenant_b_id: UUID,
    program_tenant_b: ReferralProgram,
    code_tenant_b: ReferralCode,
    user_b_id: UUID
) -> Referral:
    """Crée un parrainage pour le tenant B."""
    referee_id = uuid4()
    referral = Referral(
        tenant_id=tenant_b_id,
        program_id=program_tenant_b.id,
        code_id=code_tenant_b.id,
        referrer_id=user_b_id,
        referrer_name="User B",
        referee_id=referee_id,
        referee_name="Referee B1",
        referee_email="referee.b1@example.com",
        status=ReferralStatus.QUALIFIED,
        click_count=5,
        clicked_at=datetime.utcnow() - timedelta(days=2),
        signed_up_at=datetime.utcnow() - timedelta(days=1),
        qualified_at=datetime.utcnow(),
        created_by=user_b_id
    )
    db_session.add(referral)
    db_session.commit()
    db_session.refresh(referral)
    return referral


@pytest.fixture
def referral_converted(
    db_session: Session,
    tenant_a_id: UUID,
    program_active_tenant_a: ReferralProgram,
    code_tenant_a: ReferralCode,
    user_a_id: UUID
) -> Referral:
    """Crée un parrainage converti pour le tenant A."""
    referee_id = uuid4()
    referral = Referral(
        tenant_id=tenant_a_id,
        program_id=program_active_tenant_a.id,
        code_id=code_tenant_a.id,
        referrer_id=user_a_id,
        referrer_name="User A",
        referee_id=referee_id,
        referee_name="Referee A2",
        referee_email="referee.a2@example.com",
        status=ReferralStatus.CONVERTED,
        click_count=2,
        clicked_at=datetime.utcnow() - timedelta(days=7),
        signed_up_at=datetime.utcnow() - timedelta(days=5),
        qualified_at=datetime.utcnow() - timedelta(days=3),
        converted_at=datetime.utcnow() - timedelta(days=1),
        conversion_value=Decimal("500.00"),
        created_by=user_a_id
    )
    db_session.add(referral)
    db_session.commit()
    db_session.refresh(referral)
    return referral


# ============== Reward Fixtures ==============

@pytest.fixture
def reward_tenant_a(
    db_session: Session,
    tenant_a_id: UUID,
    referral_converted: Referral,
    tiers_multi_level: list
) -> Reward:
    """Crée une récompense pour le tenant A."""
    reward = Reward(
        tenant_id=tenant_a_id,
        referral_id=referral_converted.id,
        tier_id=tiers_multi_level[0].id,
        referrer_id=referral_converted.referrer_id,
        amount=Decimal("25.00"),
        is_claimed=False
    )
    db_session.add(reward)
    db_session.commit()
    db_session.refresh(reward)
    return reward


@pytest.fixture
def reward_claimed(
    db_session: Session,
    tenant_a_id: UUID,
    referral_converted: Referral,
    tiers_multi_level: list
) -> Reward:
    """Crée une récompense réclamée pour le tenant A."""
    reward = Reward(
        tenant_id=tenant_a_id,
        referral_id=referral_converted.id,
        tier_id=tiers_multi_level[0].id,
        referrer_id=referral_converted.referrer_id,
        amount=Decimal("50.00"),
        is_claimed=True,
        claimed_at=datetime.utcnow()
    )
    db_session.add(reward)
    db_session.commit()
    db_session.refresh(reward)
    return reward


# ============== Payout Fixtures ==============

@pytest.fixture
def payout_tenant_a(
    db_session: Session,
    tenant_a_id: UUID,
    user_a_id: UUID
) -> Payout:
    """Crée un paiement pour le tenant A."""
    payout = Payout(
        tenant_id=tenant_a_id,
        referrer_id=user_a_id,
        referrer_name="User A",
        amount=Decimal("150.00"),
        status=PayoutStatus.PENDING,
        payment_method="bank_transfer",
        created_by=user_a_id
    )
    db_session.add(payout)
    db_session.commit()
    db_session.refresh(payout)
    return payout


@pytest.fixture
def payout_tenant_b(
    db_session: Session,
    tenant_b_id: UUID,
    user_b_id: UUID
) -> Payout:
    """Crée un paiement pour le tenant B."""
    payout = Payout(
        tenant_id=tenant_b_id,
        referrer_id=user_b_id,
        referrer_name="User B",
        amount=Decimal("75.00"),
        status=PayoutStatus.APPROVED,
        payment_method="paypal",
        approved_at=datetime.utcnow(),
        approved_by=user_b_id,
        created_by=user_b_id
    )
    db_session.add(payout)
    db_session.commit()
    db_session.refresh(payout)
    return payout


# ============== Fraud Check Fixtures ==============

@pytest.fixture
def fraud_check_tenant_a(
    db_session: Session,
    tenant_a_id: UUID,
    referral_tenant_a: Referral
) -> FraudCheck:
    """Crée un contrôle fraude pour le tenant A."""
    check = FraudCheck(
        tenant_id=tenant_a_id,
        referral_id=referral_tenant_a.id,
        is_fraud=False,
        confidence_score=Decimal("0.15"),
        checked_at=datetime.utcnow()
    )
    db_session.add(check)
    db_session.commit()
    db_session.refresh(check)
    return check


@pytest.fixture
def fraud_check_positive(
    db_session: Session,
    tenant_a_id: UUID,
    referral_tenant_a: Referral
) -> FraudCheck:
    """Crée un contrôle fraude positif pour le tenant A."""
    check = FraudCheck(
        tenant_id=tenant_a_id,
        referral_id=referral_tenant_a.id,
        is_fraud=True,
        fraud_reason=FraudReason.SAME_IP,
        confidence_score=Decimal("0.95"),
        details={"ip": "192.168.1.1", "matches": 5},
        checked_at=datetime.utcnow()
    )
    db_session.add(check)
    db_session.commit()
    db_session.refresh(check)
    return check


# ============== Mixed Tenant Fixtures ==============

@pytest.fixture
def entities_mixed_tenants(
    db_session: Session,
    tenant_a_id: UUID,
    tenant_b_id: UUID,
    user_a_id: UUID,
    user_b_id: UUID
) -> dict:
    """Crée des entités pour les deux tenants."""
    entities = {"tenant_a": {"programs": [], "codes": [], "referrals": []},
                "tenant_b": {"programs": [], "codes": [], "referrals": []}}

    # Programs tenant A
    for i in range(3):
        program = ReferralProgram(
            tenant_id=tenant_a_id,
            code=f"PROG-A-{i+10:03d}",
            name=f"Program Test A{i}",
            status=ProgramStatus.ACTIVE if i > 0 else ProgramStatus.DRAFT,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            budget_total=Decimal("10000.00"),
            budget_used=Decimal("0"),
            created_by=user_a_id
        )
        db_session.add(program)
        entities["tenant_a"]["programs"].append(program)

    # Programs tenant B
    for i in range(2):
        program = ReferralProgram(
            tenant_id=tenant_b_id,
            code=f"PROG-B-{i+10:03d}",
            name=f"Program Test B{i}",
            status=ProgramStatus.ACTIVE,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=180),
            budget_total=Decimal("5000.00"),
            budget_used=Decimal("0"),
            created_by=user_b_id
        )
        db_session.add(program)
        entities["tenant_b"]["programs"].append(program)

    db_session.commit()
    return entities
