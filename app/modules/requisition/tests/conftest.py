"""
Fixtures de test pour le module Requisition
============================================
"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4, UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.modules.requisition.models import (
    CatalogCategory, CatalogItem, CatalogItemStatus,
    PreferredVendor, BudgetAllocation,
    Requisition, RequisitionStatus, RequisitionType, Priority,
    RequisitionLine, LineStatus,
    ApprovalStep, ApprovalStatus,
    RequisitionComment, RequisitionTemplate
)
from app.modules.requisition.service import RequisitionService


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
    """Service Requisition pour le tenant A."""
    return RequisitionService(db_session, tenant_a_id, user_a_id)


@pytest.fixture
def service_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID):
    """Service Requisition pour le tenant B."""
    return RequisitionService(db_session, tenant_b_id, user_b_id)


# ============== CatalogCategory Fixtures ==============

@pytest.fixture
def category_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> CatalogCategory:
    """Crée une catégorie pour le tenant A."""
    category = CatalogCategory(
        tenant_id=tenant_a_id,
        code="CAT-A-001",
        name="Office Supplies A",
        description="Office supplies category for tenant A",
        requires_approval=False,
        is_active=True,
        created_by=user_a_id
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def category_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID) -> CatalogCategory:
    """Crée une catégorie pour le tenant B."""
    category = CatalogCategory(
        tenant_id=tenant_b_id,
        code="CAT-B-001",
        name="Office Supplies B",
        description="Office supplies category for tenant B",
        requires_approval=True,
        approval_threshold=Decimal("500.00"),
        is_active=True,
        created_by=user_b_id
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


# ============== CatalogItem Fixtures ==============

@pytest.fixture
def item_tenant_a(
    db_session: Session,
    tenant_a_id: UUID,
    category_tenant_a: CatalogCategory,
    user_a_id: UUID
) -> CatalogItem:
    """Crée un article pour le tenant A."""
    item = CatalogItem(
        tenant_id=tenant_a_id,
        code="ITEM-A-001",
        name="Printer Paper A",
        description="Standard printer paper",
        category_id=category_tenant_a.id,
        category_name=category_tenant_a.name,
        unit_price=Decimal("25.00"),
        currency="EUR",
        unit_of_measure="BOX",
        min_order_qty=1,
        status=CatalogItemStatus.ACTIVE,
        created_by=user_a_id
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def item_tenant_b(
    db_session: Session,
    tenant_b_id: UUID,
    category_tenant_b: CatalogCategory,
    user_b_id: UUID
) -> CatalogItem:
    """Crée un article pour le tenant B."""
    item = CatalogItem(
        tenant_id=tenant_b_id,
        code="ITEM-B-001",
        name="Printer Paper B",
        description="Premium printer paper",
        category_id=category_tenant_b.id,
        category_name=category_tenant_b.name,
        unit_price=Decimal("35.00"),
        currency="EUR",
        unit_of_measure="BOX",
        min_order_qty=2,
        status=CatalogItemStatus.ACTIVE,
        created_by=user_b_id
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


# ============== PreferredVendor Fixtures ==============

@pytest.fixture
def vendor_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> PreferredVendor:
    """Crée un fournisseur préféré pour le tenant A."""
    vendor = PreferredVendor(
        tenant_id=tenant_a_id,
        vendor_id=uuid4(),
        vendor_code="VEND-A-001",
        vendor_name="Office Depot A",
        discount_percentage=Decimal("10.00"),
        rating=4,
        is_primary=True,
        is_active=True,
        created_by=user_a_id
    )
    db_session.add(vendor)
    db_session.commit()
    db_session.refresh(vendor)
    return vendor


@pytest.fixture
def vendor_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID) -> PreferredVendor:
    """Crée un fournisseur préféré pour le tenant B."""
    vendor = PreferredVendor(
        tenant_id=tenant_b_id,
        vendor_id=uuid4(),
        vendor_code="VEND-B-001",
        vendor_name="Staples B",
        discount_percentage=Decimal("15.00"),
        rating=5,
        is_primary=True,
        is_active=True,
        created_by=user_b_id
    )
    db_session.add(vendor)
    db_session.commit()
    db_session.refresh(vendor)
    return vendor


# ============== BudgetAllocation Fixtures ==============

@pytest.fixture
def budget_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> BudgetAllocation:
    """Crée une allocation budgétaire pour le tenant A."""
    budget = BudgetAllocation(
        tenant_id=tenant_a_id,
        budget_id=uuid4(),
        budget_name="IT Budget 2024",
        department_id=uuid4(),
        department_name="IT Department",
        fiscal_year=datetime.utcnow().year,
        total_amount=Decimal("50000.00"),
        committed_amount=Decimal("10000.00"),
        spent_amount=Decimal("5000.00"),
        available_amount=Decimal("35000.00"),
        is_active=True,
        created_by=user_a_id
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    return budget


@pytest.fixture
def budget_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID) -> BudgetAllocation:
    """Crée une allocation budgétaire pour le tenant B."""
    budget = BudgetAllocation(
        tenant_id=tenant_b_id,
        budget_id=uuid4(),
        budget_name="Marketing Budget 2024",
        department_id=uuid4(),
        department_name="Marketing",
        fiscal_year=datetime.utcnow().year,
        total_amount=Decimal("30000.00"),
        committed_amount=Decimal("5000.00"),
        spent_amount=Decimal("2000.00"),
        available_amount=Decimal("23000.00"),
        is_active=True,
        created_by=user_b_id
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    return budget


# ============== Requisition Fixtures ==============

@pytest.fixture
def requisition_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> Requisition:
    """Crée une demande pour le tenant A."""
    req = Requisition(
        tenant_id=tenant_a_id,
        requisition_number="REQ-A-2024-000001",
        requisition_type=RequisitionType.GOODS,
        status=RequisitionStatus.DRAFT,
        priority=Priority.MEDIUM,
        title="Office Supplies Request",
        description="Monthly office supplies order",
        requester_id=user_a_id,
        requester_name="User A",
        required_date=date.today() + timedelta(days=14),
        total_amount=Decimal("500.00"),
        currency="EUR",
        created_by=user_a_id
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)
    return req


@pytest.fixture
def requisition_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID) -> Requisition:
    """Crée une demande pour le tenant B."""
    req = Requisition(
        tenant_id=tenant_b_id,
        requisition_number="REQ-B-2024-000001",
        requisition_type=RequisitionType.SERVICES,
        status=RequisitionStatus.SUBMITTED,
        priority=Priority.HIGH,
        title="Marketing Campaign Services",
        description="Q1 Marketing campaign",
        requester_id=user_b_id,
        requester_name="User B",
        required_date=date.today() + timedelta(days=7),
        total_amount=Decimal("2500.00"),
        currency="EUR",
        submitted_at=datetime.utcnow(),
        created_by=user_b_id
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)
    return req


@pytest.fixture
def requisition_with_lines(
    db_session: Session,
    tenant_a_id: UUID,
    user_a_id: UUID,
    item_tenant_a: CatalogItem
) -> Requisition:
    """Crée une demande avec des lignes pour le tenant A."""
    req = Requisition(
        tenant_id=tenant_a_id,
        requisition_number="REQ-A-2024-000002",
        requisition_type=RequisitionType.GOODS,
        status=RequisitionStatus.DRAFT,
        priority=Priority.MEDIUM,
        title="Office Equipment Request",
        requester_id=user_a_id,
        requester_name="User A",
        total_amount=Decimal("0"),
        currency="EUR",
        created_by=user_a_id
    )
    db_session.add(req)
    db_session.flush()

    total = Decimal("0")
    for i in range(3):
        qty = Decimal(str(i + 1))
        price = Decimal("100.00")
        line = RequisitionLine(
            tenant_id=tenant_a_id,
            requisition_id=req.id,
            line_number=i + 1,
            item_id=item_tenant_a.id,
            item_code=item_tenant_a.code,
            description=f"Item {i + 1}",
            quantity=qty,
            unit_of_measure="EA",
            unit_price=price,
            total_price=qty * price,
            currency="EUR",
            status=LineStatus.PENDING
        )
        db_session.add(line)
        total += line.total_price

    req.total_amount = total
    db_session.commit()
    db_session.refresh(req)
    return req


@pytest.fixture
def requisition_pending_approval(
    db_session: Session,
    tenant_a_id: UUID,
    user_a_id: UUID
) -> Requisition:
    """Crée une demande en attente d'approbation pour le tenant A."""
    approver_id = uuid4()
    req = Requisition(
        tenant_id=tenant_a_id,
        requisition_number="REQ-A-2024-000003",
        requisition_type=RequisitionType.EQUIPMENT,
        status=RequisitionStatus.PENDING_APPROVAL,
        priority=Priority.HIGH,
        title="Laptop Request",
        requester_id=user_a_id,
        requester_name="User A",
        current_approver_id=approver_id,
        current_approver_name="Approver",
        total_amount=Decimal("1500.00"),
        currency="EUR",
        submitted_at=datetime.utcnow(),
        created_by=user_a_id
    )
    db_session.add(req)
    db_session.flush()

    step = ApprovalStep(
        tenant_id=tenant_a_id,
        requisition_id=req.id,
        step_number=1,
        approver_id=approver_id,
        approver_name="Approver",
        status=ApprovalStatus.PENDING
    )
    db_session.add(step)

    db_session.commit()
    db_session.refresh(req)
    return req


# ============== Template Fixtures ==============

@pytest.fixture
def template_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> RequisitionTemplate:
    """Crée un modèle pour le tenant A."""
    template = RequisitionTemplate(
        tenant_id=tenant_a_id,
        code="TPL-A-001",
        name="Standard Office Supplies",
        description="Template for standard office supplies",
        requisition_type=RequisitionType.OFFICE_SUPPLIES,
        default_lines=[
            {"description": "Printer Paper", "quantity": 5, "unit_price": 25.00},
            {"description": "Pens", "quantity": 20, "unit_price": 2.00}
        ],
        is_active=True,
        created_by=user_a_id
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def template_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID) -> RequisitionTemplate:
    """Crée un modèle pour le tenant B."""
    template = RequisitionTemplate(
        tenant_id=tenant_b_id,
        code="TPL-B-001",
        name="IT Equipment Request",
        description="Template for IT equipment",
        requisition_type=RequisitionType.IT,
        default_lines=[
            {"description": "Laptop", "quantity": 1, "unit_price": 1200.00}
        ],
        is_active=True,
        created_by=user_b_id
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


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
    entities = {
        "tenant_a": {"categories": [], "items": [], "requisitions": []},
        "tenant_b": {"categories": [], "items": [], "requisitions": []}
    }

    # Categories tenant A
    for i in range(3):
        cat = CatalogCategory(
            tenant_id=tenant_a_id,
            code=f"CAT-A-{i+10:03d}",
            name=f"Category Test A{i}",
            is_active=True,
            created_by=user_a_id
        )
        db_session.add(cat)
        entities["tenant_a"]["categories"].append(cat)

    # Categories tenant B
    for i in range(2):
        cat = CatalogCategory(
            tenant_id=tenant_b_id,
            code=f"CAT-B-{i+10:03d}",
            name=f"Category Test B{i}",
            is_active=True,
            created_by=user_b_id
        )
        db_session.add(cat)
        entities["tenant_b"]["categories"].append(cat)

    # Requisitions tenant A
    for i in range(3):
        req = Requisition(
            tenant_id=tenant_a_id,
            requisition_number=f"REQ-A-TEST-{i+10:03d}",
            requisition_type=RequisitionType.GOODS,
            status=RequisitionStatus.DRAFT if i == 0 else RequisitionStatus.SUBMITTED,
            priority=Priority.MEDIUM,
            title=f"Test Request A{i}",
            requester_id=user_a_id,
            requester_name="User A",
            total_amount=Decimal(str((i + 1) * 100)),
            currency="EUR",
            created_by=user_a_id
        )
        db_session.add(req)
        entities["tenant_a"]["requisitions"].append(req)

    # Requisitions tenant B
    for i in range(2):
        req = Requisition(
            tenant_id=tenant_b_id,
            requisition_number=f"REQ-B-TEST-{i+10:03d}",
            requisition_type=RequisitionType.SERVICES,
            status=RequisitionStatus.APPROVED,
            priority=Priority.HIGH,
            title=f"Test Request B{i}",
            requester_id=user_b_id,
            requester_name="User B",
            total_amount=Decimal(str((i + 1) * 200)),
            currency="EUR",
            created_by=user_b_id
        )
        db_session.add(req)
        entities["tenant_b"]["requisitions"].append(req)

    db_session.commit()
    return entities
