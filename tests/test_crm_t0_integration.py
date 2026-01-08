"""
AZALS CRM T0 - Tests d'Intégration Complets
============================================

Tests critiques pour la validation du module CRM T0:
- Isolation inter-tenant (CRITIQUE)
- CRUD complet avec persistance
- Export CSV avec isolation tenant
- Droits RBAC

Ces tests utilisent une vraie base de données SQLite pour valider
le comportement réel de l'application.
"""

import pytest
import os
import tempfile
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4, UUID
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Configuration environnement test AVANT imports
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_crm_t0.db")
os.environ.setdefault("SECRET_KEY", "test-key-minimum-32-characters-long-for-tests")
os.environ.setdefault("BOOTSTRAP_SECRET", "test-bootstrap-minimum-32-characters-here")
os.environ.setdefault("ENVIRONMENT", "test")

from app.core.database import Base
from app.modules.commercial.models import (
    Customer, Contact, Opportunity, CustomerActivity,
    CustomerType, OpportunityStatus, ActivityType
)
from app.modules.commercial.schemas import (
    CustomerCreate, CustomerUpdate,
    ContactCreate, ContactUpdate,
    OpportunityCreate, OpportunityUpdate,
    ActivityCreate
)
from app.modules.commercial.service import CommercialService, get_commercial_service


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """
    Crée une base de données SQLite temporaire pour chaque test.
    Garantit l'isolation entre les tests.
    """
    # Créer un fichier temporaire pour la DB
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    yield db

    # Nettoyage
    db.close()
    engine.dispose()

    # Supprimer le fichier DB
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def tenant_a_service(test_db):
    """Service pour le tenant A."""
    return CommercialService(test_db, "tenant-a")


@pytest.fixture
def tenant_b_service(test_db):
    """Service pour le tenant B."""
    return CommercialService(test_db, "tenant-b")


@pytest.fixture
def sample_customer_data():
    """Données de test pour un client."""
    # Note: Le schéma utilise 'type' comme alias pour 'customer_type'
    # Mais on doit passer 'type' car le modèle SQLAlchemy utilise 'type'
    data = CustomerCreate(
        code="CLI001",
        name="Entreprise Test SA",
        type=CustomerType.PROSPECT,
        email="contact@test.com",
        phone="0123456789",
        city="Paris",
        country_code="FR"
    )
    return data


@pytest.fixture
def sample_contact_data():
    """Données de test pour un contact."""
    def _create(customer_id: UUID):
        return ContactCreate(
            customer_id=customer_id,
            first_name="Jean",
            last_name="Dupont",
            email="jean.dupont@test.com",
            job_title="Directeur",
            is_primary=True
        )
    return _create


@pytest.fixture
def sample_opportunity_data():
    """Données de test pour une opportunité."""
    def _create(customer_id: UUID):
        return OpportunityCreate(
            customer_id=customer_id,
            code="OPP001",
            name="Projet Important",
            amount=Decimal("50000.00"),
            probability=30,
            status=OpportunityStatus.NEW
        )
    return _create


# ============================================================================
# TESTS ISOLATION INTER-TENANT (CRITIQUE)
# ============================================================================

class TestTenantIsolation:
    """
    Tests CRITIQUES d'isolation inter-tenant.
    Ces tests vérifient qu'aucune donnée ne peut fuiter entre tenants.
    """

    def test_customer_isolation_create(self, test_db, tenant_a_service, tenant_b_service, sample_customer_data):
        """
        CRITIQUE: Un client créé par tenant A ne doit PAS être visible par tenant B.
        """
        user_id = uuid4()

        # Tenant A crée un client
        customer_a = tenant_a_service.create_customer(sample_customer_data, user_id)
        assert customer_a.tenant_id == "tenant-a"

        # Tenant B ne doit PAS voir ce client
        customers_b, total_b = tenant_b_service.list_customers()
        assert total_b == 0
        assert len(customers_b) == 0

        # Tenant B ne doit PAS pouvoir récupérer ce client par ID
        customer_from_b = tenant_b_service.get_customer(customer_a.id)
        assert customer_from_b is None

    def test_customer_isolation_list(self, test_db, tenant_a_service, tenant_b_service, sample_customer_data):
        """
        CRITIQUE: La liste des clients doit être strictement isolée par tenant.
        """
        user_id = uuid4()

        # Créer 3 clients pour tenant A
        for i in range(3):
            data = CustomerCreate(
                code=f"CLI-A-{i}",
                name=f"Client A {i}",
                type=CustomerType.CUSTOMER
            )
            tenant_a_service.create_customer(data, user_id)

        # Créer 2 clients pour tenant B
        for i in range(2):
            data = CustomerCreate(
                code=f"CLI-B-{i}",
                name=f"Client B {i}",
                type=CustomerType.PROSPECT
            )
            tenant_b_service.create_customer(data, user_id)

        # Vérifier l'isolation
        customers_a, total_a = tenant_a_service.list_customers()
        customers_b, total_b = tenant_b_service.list_customers()

        assert total_a == 3
        assert total_b == 2

        # Vérifier que tous les clients A ont le bon tenant
        for c in customers_a:
            assert c.tenant_id == "tenant-a"

        # Vérifier que tous les clients B ont le bon tenant
        for c in customers_b:
            assert c.tenant_id == "tenant-b"

    def test_contact_isolation(self, test_db, tenant_a_service, tenant_b_service, sample_customer_data, sample_contact_data):
        """
        CRITIQUE: Les contacts sont isolés par tenant.
        """
        user_id = uuid4()

        # Tenant A crée un client et un contact
        customer_a = tenant_a_service.create_customer(sample_customer_data, user_id)
        contact_a = tenant_a_service.create_contact(sample_contact_data(customer_a.id))

        # Tenant B ne doit PAS voir les contacts
        contacts_b = tenant_b_service.list_contacts(customer_a.id)
        assert len(contacts_b) == 0

        # Tenant B ne peut pas récupérer le contact par ID
        contact_from_b = tenant_b_service.get_contact(contact_a.id)
        assert contact_from_b is None

    def test_opportunity_isolation(self, test_db, tenant_a_service, tenant_b_service, sample_customer_data, sample_opportunity_data):
        """
        CRITIQUE: Les opportunités sont isolées par tenant.
        """
        user_id = uuid4()

        # Tenant A crée un client et une opportunité
        customer_a = tenant_a_service.create_customer(sample_customer_data, user_id)
        opp_a = tenant_a_service.create_opportunity(sample_opportunity_data(customer_a.id), user_id)

        # Tenant B ne doit PAS voir cette opportunité
        opps_b, total_b = tenant_b_service.list_opportunities()
        assert total_b == 0

        # Tenant B ne peut pas récupérer l'opportunité par ID
        opp_from_b = tenant_b_service.get_opportunity(opp_a.id)
        assert opp_from_b is None

    def test_update_cross_tenant_blocked(self, test_db, tenant_a_service, tenant_b_service, sample_customer_data):
        """
        CRITIQUE: Un tenant ne peut PAS modifier les données d'un autre tenant.
        """
        user_id = uuid4()

        # Tenant A crée un client
        customer_a = tenant_a_service.create_customer(sample_customer_data, user_id)
        original_name = customer_a.name

        # Tenant B tente de modifier le client (doit échouer silencieusement)
        update_data = CustomerUpdate(name="Nom Modifié par B")
        result = tenant_b_service.update_customer(customer_a.id, update_data)
        assert result is None

        # Vérifier que le nom n'a pas changé
        customer_a_refreshed = tenant_a_service.get_customer(customer_a.id)
        assert customer_a_refreshed.name == original_name

    def test_delete_cross_tenant_blocked(self, test_db, tenant_a_service, tenant_b_service, sample_customer_data):
        """
        CRITIQUE: Un tenant ne peut PAS supprimer les données d'un autre tenant.
        """
        user_id = uuid4()

        # Tenant A crée un client
        customer_a = tenant_a_service.create_customer(sample_customer_data, user_id)

        # Tenant B tente de supprimer le client (doit échouer)
        result = tenant_b_service.delete_customer(customer_a.id)
        assert result is False

        # Vérifier que le client existe toujours
        customer_exists = tenant_a_service.get_customer(customer_a.id)
        assert customer_exists is not None


# ============================================================================
# TESTS CRUD COMPLET
# ============================================================================

class TestCustomerCRUD:
    """Tests CRUD complet pour les clients."""

    def test_create_customer(self, test_db, tenant_a_service, sample_customer_data):
        """Créer un client."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        assert customer.id is not None
        assert customer.code == "CLI001"
        assert customer.name == "Entreprise Test SA"
        assert customer.tenant_id == "tenant-a"
        assert customer.type == CustomerType.PROSPECT
        assert customer.created_by == user_id

    def test_get_customer_by_id(self, test_db, tenant_a_service, sample_customer_data):
        """Récupérer un client par ID."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        retrieved = tenant_a_service.get_customer(customer.id)
        assert retrieved is not None
        assert retrieved.id == customer.id
        assert retrieved.code == customer.code

    def test_get_customer_by_code(self, test_db, tenant_a_service, sample_customer_data):
        """Récupérer un client par code."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        retrieved = tenant_a_service.get_customer_by_code("CLI001")
        assert retrieved is not None
        assert retrieved.id == customer.id

    def test_list_customers_with_filters(self, test_db, tenant_a_service):
        """Lister les clients avec filtres."""
        user_id = uuid4()

        # Créer des clients de différents types
        tenant_a_service.create_customer(
            CustomerCreate(code="P001", name="Prospect 1", type=CustomerType.PROSPECT),
            user_id
        )
        tenant_a_service.create_customer(
            CustomerCreate(code="C001", name="Client 1", type=CustomerType.CUSTOMER),
            user_id
        )
        tenant_a_service.create_customer(
            CustomerCreate(code="C002", name="Client 2", type=CustomerType.CUSTOMER),
            user_id
        )

        # Filtrer par type
        prospects, _ = tenant_a_service.list_customers(type=CustomerType.PROSPECT)
        assert len(prospects) == 1

        customers, _ = tenant_a_service.list_customers(type=CustomerType.CUSTOMER)
        assert len(customers) == 2

    def test_update_customer(self, test_db, tenant_a_service, sample_customer_data):
        """Mettre à jour un client."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        update_data = CustomerUpdate(
            name="Entreprise Test Modifiée",
            email="nouveau@test.com"
        )
        updated = tenant_a_service.update_customer(customer.id, update_data)

        assert updated is not None
        assert updated.name == "Entreprise Test Modifiée"
        assert updated.email == "nouveau@test.com"
        # Le code ne change pas
        assert updated.code == "CLI001"

    def test_delete_customer(self, test_db, tenant_a_service, sample_customer_data):
        """Supprimer un client."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        result = tenant_a_service.delete_customer(customer.id)
        assert result is True

        # Vérifier que le client n'existe plus
        deleted = tenant_a_service.get_customer(customer.id)
        assert deleted is None

    def test_convert_prospect_to_customer(self, test_db, tenant_a_service, sample_customer_data):
        """Convertir un prospect en client."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)
        assert customer.type == CustomerType.PROSPECT

        converted = tenant_a_service.convert_prospect(customer.id)
        assert converted.type == CustomerType.CUSTOMER


class TestContactCRUD:
    """Tests CRUD complet pour les contacts."""

    def test_create_contact(self, test_db, tenant_a_service, sample_customer_data, sample_contact_data):
        """Créer un contact."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        contact = tenant_a_service.create_contact(sample_contact_data(customer.id))

        assert contact.id is not None
        assert contact.first_name == "Jean"
        assert contact.last_name == "Dupont"
        assert contact.tenant_id == "tenant-a"
        assert contact.customer_id == customer.id

    def test_list_contacts_for_customer(self, test_db, tenant_a_service, sample_customer_data):
        """Lister les contacts d'un client."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        # Créer plusieurs contacts
        for i in range(3):
            tenant_a_service.create_contact(ContactCreate(
                customer_id=customer.id,
                first_name=f"Contact{i}",
                last_name=f"Test{i}",
                email=f"contact{i}@test.com"
            ))

        contacts = tenant_a_service.list_contacts(customer.id)
        assert len(contacts) == 3

    def test_update_contact(self, test_db, tenant_a_service, sample_customer_data, sample_contact_data):
        """Mettre à jour un contact."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)
        contact = tenant_a_service.create_contact(sample_contact_data(customer.id))

        update_data = ContactUpdate(
            job_title="PDG",
            is_decision_maker=True
        )
        updated = tenant_a_service.update_contact(contact.id, update_data)

        assert updated.job_title == "PDG"
        assert updated.is_decision_maker is True

    def test_delete_contact(self, test_db, tenant_a_service, sample_customer_data, sample_contact_data):
        """Supprimer un contact."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)
        contact = tenant_a_service.create_contact(sample_contact_data(customer.id))

        result = tenant_a_service.delete_contact(contact.id)
        assert result is True

        deleted = tenant_a_service.get_contact(contact.id)
        assert deleted is None


class TestOpportunityCRUD:
    """Tests CRUD complet pour les opportunités."""

    def test_create_opportunity(self, test_db, tenant_a_service, sample_customer_data, sample_opportunity_data):
        """Créer une opportunité."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        opp = tenant_a_service.create_opportunity(sample_opportunity_data(customer.id), user_id)

        assert opp.id is not None
        assert opp.code == "OPP001"
        assert opp.name == "Projet Important"
        assert opp.amount == Decimal("50000.00")
        assert opp.probability == 30
        assert opp.weighted_amount == Decimal("15000.00")  # 50000 * 30%
        assert opp.tenant_id == "tenant-a"

    def test_list_opportunities_with_filters(self, test_db, tenant_a_service, sample_customer_data):
        """Lister les opportunités avec filtres."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        # Créer des opportunités avec différents statuts
        for i, status in enumerate([OpportunityStatus.NEW, OpportunityStatus.QUALIFIED, OpportunityStatus.WON]):
            tenant_a_service.create_opportunity(
                OpportunityCreate(
                    customer_id=customer.id,
                    code=f"OPP{i}",
                    name=f"Opp {i}",
                    amount=Decimal("10000"),
                    status=status
                ),
                user_id
            )

        # Filtrer par statut
        new_opps, _ = tenant_a_service.list_opportunities(status=OpportunityStatus.NEW)
        assert len(new_opps) == 1

        won_opps, _ = tenant_a_service.list_opportunities(status=OpportunityStatus.WON)
        assert len(won_opps) == 1

    def test_win_opportunity(self, test_db, tenant_a_service, sample_customer_data, sample_opportunity_data):
        """Marquer une opportunité comme gagnée."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)
        opp = tenant_a_service.create_opportunity(sample_opportunity_data(customer.id), user_id)

        won = tenant_a_service.win_opportunity(opp.id, "Meilleure offre")

        assert won.status == OpportunityStatus.WON
        assert won.probability == 100
        assert won.weighted_amount == won.amount
        assert won.win_reason == "Meilleure offre"
        assert won.actual_close_date is not None

    def test_lose_opportunity(self, test_db, tenant_a_service, sample_customer_data, sample_opportunity_data):
        """Marquer une opportunité comme perdue."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)
        opp = tenant_a_service.create_opportunity(sample_opportunity_data(customer.id), user_id)

        lost = tenant_a_service.lose_opportunity(opp.id, "Prix trop élevé")

        assert lost.status == OpportunityStatus.LOST
        assert lost.probability == 0
        assert lost.weighted_amount == Decimal("0")
        assert lost.loss_reason == "Prix trop élevé"


# ============================================================================
# TESTS EXPORT CSV
# ============================================================================

class TestExportCSV:
    """Tests de l'export CSV avec isolation tenant."""

    def test_export_customers_csv(self, test_db, tenant_a_service, sample_customer_data):
        """Exporter les clients en CSV."""
        user_id = uuid4()

        # Créer quelques clients
        for i in range(3):
            tenant_a_service.create_customer(
                CustomerCreate(code=f"CLI{i}", name=f"Client {i}"),
                user_id
            )

        csv_content = tenant_a_service.export_customers_csv()

        # Vérifier le format CSV
        assert "Code;Nom;Type" in csv_content
        assert "CLI0" in csv_content
        assert "CLI1" in csv_content
        assert "CLI2" in csv_content

    def test_export_csv_tenant_isolation(self, test_db, tenant_a_service, tenant_b_service):
        """
        CRITIQUE: L'export CSV ne doit contenir que les données du tenant.
        """
        user_id = uuid4()

        # Tenant A crée des clients
        for i in range(3):
            tenant_a_service.create_customer(
                CustomerCreate(code=f"CLI-A-{i}", name=f"Client A {i}"),
                user_id
            )

        # Tenant B crée des clients
        for i in range(2):
            tenant_b_service.create_customer(
                CustomerCreate(code=f"CLI-B-{i}", name=f"Client B {i}"),
                user_id
            )

        # Export tenant A
        csv_a = tenant_a_service.export_customers_csv()
        assert "CLI-A-0" in csv_a
        assert "CLI-A-1" in csv_a
        assert "CLI-A-2" in csv_a
        assert "CLI-B-" not in csv_a  # CRITIQUE: pas de données tenant B

        # Export tenant B
        csv_b = tenant_b_service.export_customers_csv()
        assert "CLI-B-0" in csv_b
        assert "CLI-B-1" in csv_b
        assert "CLI-A-" not in csv_b  # CRITIQUE: pas de données tenant A

    def test_export_contacts_csv(self, test_db, tenant_a_service, sample_customer_data):
        """Exporter les contacts en CSV."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        # Créer des contacts
        for i in range(2):
            tenant_a_service.create_contact(ContactCreate(
                customer_id=customer.id,
                first_name=f"Prénom{i}",
                last_name=f"Nom{i}",
                email=f"contact{i}@test.com"
            ))

        csv_content = tenant_a_service.export_contacts_csv()

        assert "Prénom;Nom;Fonction" in csv_content
        assert "Prénom0" in csv_content
        assert "Nom1" in csv_content

    def test_export_opportunities_csv(self, test_db, tenant_a_service, sample_customer_data):
        """Exporter les opportunités en CSV."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        # Créer des opportunités
        for i in range(2):
            tenant_a_service.create_opportunity(
                OpportunityCreate(
                    customer_id=customer.id,
                    code=f"OPP{i}",
                    name=f"Opportunité {i}",
                    amount=Decimal(f"{i+1}0000")
                ),
                user_id
            )

        csv_content = tenant_a_service.export_opportunities_csv()

        assert "Code;Nom;Statut" in csv_content
        assert "OPP0" in csv_content
        assert "OPP1" in csv_content


# ============================================================================
# TESTS HISTORIQUE (ACTIVITÉS)
# ============================================================================

class TestActivityHistory:
    """Tests de l'historique basique (activités CRM)."""

    def test_create_activity(self, test_db, tenant_a_service, sample_customer_data):
        """Créer une activité."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        activity = tenant_a_service.create_activity(
            ActivityCreate(
                customer_id=customer.id,
                type=ActivityType.CALL,
                subject="Appel de suivi"
            ),
            user_id
        )

        assert activity.id is not None
        assert activity.type == ActivityType.CALL
        assert activity.subject == "Appel de suivi"
        assert activity.tenant_id == "tenant-a"

    def test_list_activities(self, test_db, tenant_a_service, sample_customer_data):
        """Lister les activités."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        # Créer plusieurs activités
        for activity_type in [ActivityType.CALL, ActivityType.EMAIL, ActivityType.MEETING]:
            tenant_a_service.create_activity(
                ActivityCreate(
                    customer_id=customer.id,
                    type=activity_type,
                    subject=f"Activité {activity_type.value}"
                ),
                user_id
            )

        activities = tenant_a_service.list_activities(customer_id=customer.id)
        assert len(activities) == 3

    def test_complete_activity(self, test_db, tenant_a_service, sample_customer_data):
        """Marquer une activité comme terminée."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        activity = tenant_a_service.create_activity(
            ActivityCreate(
                customer_id=customer.id,
                type=ActivityType.TASK,
                subject="Tâche à faire"
            ),
            user_id
        )

        assert activity.is_completed is False

        completed = tenant_a_service.complete_activity(activity.id)

        assert completed.is_completed is True
        assert completed.completed_at is not None

    def test_activity_isolation(self, test_db, tenant_a_service, tenant_b_service, sample_customer_data):
        """
        CRITIQUE: Les activités sont isolées par tenant.
        """
        user_id = uuid4()

        # Tenant A crée un client et une activité
        customer_a = tenant_a_service.create_customer(sample_customer_data, user_id)
        activity_a = tenant_a_service.create_activity(
            ActivityCreate(
                customer_id=customer_a.id,
                type=ActivityType.CALL,
                subject="Appel tenant A"
            ),
            user_id
        )

        # Tenant B ne doit pas voir cette activité
        activities_b = tenant_b_service.list_activities()
        assert len(activities_b) == 0


# ============================================================================
# TESTS PERSISTANCE
# ============================================================================

class TestPersistence:
    """Tests de persistance des données."""

    def test_data_persists_after_commit(self, test_db, tenant_a_service, sample_customer_data):
        """Les données persistent après commit."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)
        customer_id = customer.id

        # Commit explicite
        test_db.commit()

        # Récupérer dans une nouvelle requête
        persisted = tenant_a_service.get_customer(customer_id)
        assert persisted is not None
        assert persisted.code == "CLI001"

    def test_update_persists(self, test_db, tenant_a_service, sample_customer_data):
        """Les modifications persistent."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        # Modifier
        tenant_a_service.update_customer(
            customer.id,
            CustomerUpdate(name="Nom Modifié")
        )

        # Vérifier la persistance
        test_db.expire_all()  # Invalider le cache
        refreshed = tenant_a_service.get_customer(customer.id)
        assert refreshed.name == "Nom Modifié"


# ============================================================================
# TESTS VALIDATION DONNÉES
# ============================================================================

class TestDataValidation:
    """Tests de validation des données."""

    def test_customer_code_unique_per_tenant(self, test_db, tenant_a_service, sample_customer_data):
        """Le code client est unique par tenant."""
        user_id = uuid4()

        # Créer un premier client
        tenant_a_service.create_customer(sample_customer_data, user_id)

        # Tenter de créer un client avec le même code doit échouer
        with pytest.raises(Exception):
            tenant_a_service.create_customer(sample_customer_data, user_id)

    def test_opportunity_code_unique_per_tenant(self, test_db, tenant_a_service, sample_customer_data, sample_opportunity_data):
        """Le code opportunité est unique par tenant."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        # Créer une première opportunité
        tenant_a_service.create_opportunity(sample_opportunity_data(customer.id), user_id)

        # Tenter de créer avec le même code doit échouer
        with pytest.raises(Exception):
            tenant_a_service.create_opportunity(sample_opportunity_data(customer.id), user_id)


# ============================================================================
# TESTS CALCULS
# ============================================================================

class TestCalculations:
    """Tests des calculs automatiques."""

    def test_weighted_amount_calculation(self, test_db, tenant_a_service, sample_customer_data):
        """Le montant pondéré est calculé correctement."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        opp = tenant_a_service.create_opportunity(
            OpportunityCreate(
                customer_id=customer.id,
                code="OPP001",
                name="Test",
                amount=Decimal("100000.00"),
                probability=25
            ),
            user_id
        )

        # Montant pondéré = 100000 * 25% = 25000
        assert opp.weighted_amount == Decimal("25000.00")

    def test_weighted_amount_updates_on_probability_change(self, test_db, tenant_a_service, sample_customer_data):
        """Le montant pondéré se met à jour quand la probabilité change."""
        user_id = uuid4()
        customer = tenant_a_service.create_customer(sample_customer_data, user_id)

        opp = tenant_a_service.create_opportunity(
            OpportunityCreate(
                customer_id=customer.id,
                code="OPP001",
                name="Test",
                amount=Decimal("100000.00"),
                probability=25
            ),
            user_id
        )

        # Modifier la probabilité
        updated = tenant_a_service.update_opportunity(
            opp.id,
            OpportunityUpdate(probability=50)
        )

        # Nouveau montant pondéré = 100000 * 50% = 50000
        assert updated.weighted_amount == Decimal("50000.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
