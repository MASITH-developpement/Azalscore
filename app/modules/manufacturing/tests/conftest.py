"""
Fixtures de test pour le module Manufacturing
==============================================
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4, UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.modules.manufacturing.models import (
    BOM, BOMLine, BOMStatus, BOMType,
    Workcenter, WorkcenterState, WorkcenterType,
    Routing, Operation,
    WorkOrder, WorkOrderStatus, WorkOrderOperation, OperationStatus,
    QualityCheck, QualityCheckType, QualityResult,
    ProductionLog
)
from app.modules.manufacturing.service import ManufacturingService


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
    """Service Manufacturing pour le tenant A."""
    return ManufacturingService(db_session, tenant_a_id, user_a_id)


@pytest.fixture
def service_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID):
    """Service Manufacturing pour le tenant B."""
    return ManufacturingService(db_session, tenant_b_id, user_b_id)


# ============== BOM Fixtures ==============

@pytest.fixture
def bom_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> BOM:
    """Crée une BOM pour le tenant A."""
    bom = BOM(
        tenant_id=tenant_a_id,
        code="BOM-A-001",
        name="BOM Test Tenant A",
        bom_type=BOMType.MANUFACTURING,
        status=BOMStatus.DRAFT,
        product_id=uuid4(),
        product_code="PROD-A-001",
        product_name="Product A",
        quantity=Decimal("1"),
        unit="pcs",
        created_by=user_a_id
    )
    db_session.add(bom)
    db_session.commit()
    db_session.refresh(bom)
    return bom


@pytest.fixture
def bom_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID) -> BOM:
    """Crée une BOM pour le tenant B."""
    bom = BOM(
        tenant_id=tenant_b_id,
        code="BOM-B-001",
        name="BOM Test Tenant B",
        bom_type=BOMType.MANUFACTURING,
        status=BOMStatus.DRAFT,
        product_id=uuid4(),
        product_code="PROD-B-001",
        product_name="Product B",
        quantity=Decimal("1"),
        unit="pcs",
        created_by=user_b_id
    )
    db_session.add(bom)
    db_session.commit()
    db_session.refresh(bom)
    return bom


@pytest.fixture
def bom_with_lines(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> BOM:
    """Crée une BOM avec des lignes pour le tenant A."""
    bom = BOM(
        tenant_id=tenant_a_id,
        code="BOM-A-002",
        name="BOM With Lines",
        bom_type=BOMType.MANUFACTURING,
        status=BOMStatus.DRAFT,
        product_id=uuid4(),
        product_code="PROD-A-002",
        product_name="Product A2",
        quantity=Decimal("1"),
        unit="pcs",
        created_by=user_a_id
    )
    db_session.add(bom)
    db_session.flush()

    for i in range(3):
        line = BOMLine(
            tenant_id=tenant_a_id,
            bom_id=bom.id,
            sequence=i + 1,
            component_id=uuid4(),
            component_code=f"COMP-{i+1:03d}",
            component_name=f"Component {i+1}",
            quantity=Decimal(str(i + 1)),
            unit="pcs",
            unit_cost=Decimal("10.00")
        )
        db_session.add(line)

    db_session.commit()
    db_session.refresh(bom)
    return bom


# ============== Workcenter Fixtures ==============

@pytest.fixture
def workcenter_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> Workcenter:
    """Crée un workcenter pour le tenant A."""
    wc = Workcenter(
        tenant_id=tenant_a_id,
        code="WC-A-001",
        name="Workcenter A",
        workcenter_type=WorkcenterType.MACHINE,
        state=WorkcenterState.AVAILABLE,
        capacity=Decimal("100"),
        hourly_cost=Decimal("50.00"),
        is_active=True,
        created_by=user_a_id
    )
    db_session.add(wc)
    db_session.commit()
    db_session.refresh(wc)
    return wc


@pytest.fixture
def workcenter_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID) -> Workcenter:
    """Crée un workcenter pour le tenant B."""
    wc = Workcenter(
        tenant_id=tenant_b_id,
        code="WC-B-001",
        name="Workcenter B",
        workcenter_type=WorkcenterType.MACHINE,
        state=WorkcenterState.AVAILABLE,
        capacity=Decimal("100"),
        hourly_cost=Decimal("50.00"),
        is_active=True,
        created_by=user_b_id
    )
    db_session.add(wc)
    db_session.commit()
    db_session.refresh(wc)
    return wc


# ============== Routing Fixtures ==============

@pytest.fixture
def routing_tenant_a(
    db_session: Session,
    tenant_a_id: UUID,
    user_a_id: UUID,
    workcenter_tenant_a: Workcenter
) -> Routing:
    """Crée une routing pour le tenant A."""
    routing = Routing(
        tenant_id=tenant_a_id,
        code="RTG-A-001",
        name="Routing A",
        product_id=uuid4(),
        is_active=True,
        created_by=user_a_id
    )
    db_session.add(routing)
    db_session.flush()

    op = Operation(
        tenant_id=tenant_a_id,
        routing_id=routing.id,
        sequence=1,
        name="Operation 1",
        workcenter_id=workcenter_tenant_a.id,
        workcenter_name=workcenter_tenant_a.name,
        setup_time=30,
        run_time=60
    )
    db_session.add(op)

    db_session.commit()
    db_session.refresh(routing)
    return routing


@pytest.fixture
def routing_tenant_b(
    db_session: Session,
    tenant_b_id: UUID,
    user_b_id: UUID,
    workcenter_tenant_b: Workcenter
) -> Routing:
    """Crée une routing pour le tenant B."""
    routing = Routing(
        tenant_id=tenant_b_id,
        code="RTG-B-001",
        name="Routing B",
        product_id=uuid4(),
        is_active=True,
        created_by=user_b_id
    )
    db_session.add(routing)
    db_session.flush()

    op = Operation(
        tenant_id=tenant_b_id,
        routing_id=routing.id,
        sequence=1,
        name="Operation B1",
        workcenter_id=workcenter_tenant_b.id,
        workcenter_name=workcenter_tenant_b.name,
        setup_time=30,
        run_time=60
    )
    db_session.add(op)

    db_session.commit()
    db_session.refresh(routing)
    return routing


# ============== Work Order Fixtures ==============

@pytest.fixture
def work_order_tenant_a(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> WorkOrder:
    """Crée un work order pour le tenant A."""
    wo = WorkOrder(
        tenant_id=tenant_a_id,
        number="WO-A-001",
        name="Work Order A",
        status=WorkOrderStatus.DRAFT,
        product_id=uuid4(),
        product_code="PROD-A-001",
        product_name="Product A",
        quantity_to_produce=Decimal("100"),
        unit="pcs",
        created_by=user_a_id
    )
    db_session.add(wo)
    db_session.commit()
    db_session.refresh(wo)
    return wo


@pytest.fixture
def work_order_tenant_b(db_session: Session, tenant_b_id: UUID, user_b_id: UUID) -> WorkOrder:
    """Crée un work order pour le tenant B."""
    wo = WorkOrder(
        tenant_id=tenant_b_id,
        number="WO-B-001",
        name="Work Order B",
        status=WorkOrderStatus.DRAFT,
        product_id=uuid4(),
        product_code="PROD-B-001",
        product_name="Product B",
        quantity_to_produce=Decimal("100"),
        unit="pcs",
        created_by=user_b_id
    )
    db_session.add(wo)
    db_session.commit()
    db_session.refresh(wo)
    return wo


@pytest.fixture
def work_order_in_progress(db_session: Session, tenant_a_id: UUID, user_a_id: UUID) -> WorkOrder:
    """Crée un work order en cours pour le tenant A."""
    wo = WorkOrder(
        tenant_id=tenant_a_id,
        number="WO-A-002",
        name="Work Order A In Progress",
        status=WorkOrderStatus.IN_PROGRESS,
        product_id=uuid4(),
        product_code="PROD-A-002",
        product_name="Product A2",
        quantity_to_produce=Decimal("50"),
        unit="pcs",
        actual_start=datetime.utcnow(),
        created_by=user_a_id
    )
    db_session.add(wo)
    db_session.commit()
    db_session.refresh(wo)
    return wo


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
    entities = {"tenant_a": [], "tenant_b": []}

    # BOMs tenant A
    for i in range(3):
        bom = BOM(
            tenant_id=tenant_a_id,
            code=f"BOM-A-{i+10:03d}",
            name=f"Test BOM A{i}",
            bom_type=BOMType.MANUFACTURING,
            status=BOMStatus.ACTIVE if i > 0 else BOMStatus.DRAFT,
            product_id=uuid4(),
            product_code=f"PROD-A-{i+10:03d}",
            product_name=f"Test Product A{i}",
            quantity=Decimal("1"),
            unit="pcs",
            created_by=user_a_id
        )
        db_session.add(bom)
        entities["tenant_a"].append(bom)

    # BOMs tenant B
    for i in range(2):
        bom = BOM(
            tenant_id=tenant_b_id,
            code=f"BOM-B-{i+10:03d}",
            name=f"Test BOM B{i}",
            bom_type=BOMType.ASSEMBLY,
            status=BOMStatus.ACTIVE,
            product_id=uuid4(),
            product_code=f"PROD-B-{i+10:03d}",
            product_name=f"Test Product B{i}",
            quantity=Decimal("1"),
            unit="pcs",
            created_by=user_b_id
        )
        db_session.add(bom)
        entities["tenant_b"].append(bom)

    db_session.commit()
    return entities


# ============== Quality Check Fixtures ==============

@pytest.fixture
def quality_check_tenant_a(
    db_session: Session,
    tenant_a_id: UUID,
    work_order_tenant_a: WorkOrder
) -> QualityCheck:
    """Crée un contrôle qualité pour le tenant A."""
    qc = QualityCheck(
        tenant_id=tenant_a_id,
        work_order_id=work_order_tenant_a.id,
        check_type=QualityCheckType.IN_PROCESS,
        sample_size=10
    )
    db_session.add(qc)
    db_session.commit()
    db_session.refresh(qc)
    return qc


@pytest.fixture
def quality_check_tenant_b(
    db_session: Session,
    tenant_b_id: UUID,
    work_order_tenant_b: WorkOrder
) -> QualityCheck:
    """Crée un contrôle qualité pour le tenant B."""
    qc = QualityCheck(
        tenant_id=tenant_b_id,
        work_order_id=work_order_tenant_b.id,
        check_type=QualityCheckType.FINAL,
        sample_size=5
    )
    db_session.add(qc)
    db_session.commit()
    db_session.refresh(qc)
    return qc
