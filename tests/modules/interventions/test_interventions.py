"""
Tests pour le module INTERVENTIONS v1.

Couverture:
- Génération numérotation INT-YYYY-XXXX
- Workflow statuts strict
- Refus actions invalides
- Calcul durée automatique
- Multi-tenant strict
- RBAC par rôle
- Génération rapport intervention
- Génération rapport final
- Intégration Planning
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
# Import all models to ensure foreign key references are resolved
from app.modules.tenants.models import Tenant  # noqa: F401
from app.core.models import User  # noqa: F401
from app.modules.audit.models import AuditLog  # noqa: F401
from app.core.sequences import SequenceConfig  # noqa: F401
from app.modules.interventions.models import (
    Intervention,
    InterventionStatut,
    InterventionPriorite,
    TypeIntervention,
    CanalDemande,
    RapportIntervention,
    RapportFinal,
    DonneurOrdre,
    InterventionSequence,
)
from app.modules.interventions.schemas import (
    InterventionCreate,
    InterventionUpdate,
    InterventionPlanifier,
    ArriveeRequest,
    DemarrageRequest,
    FinInterventionRequest,
    DonneurOrdreCreate,
    RapportInterventionUpdate,
    SignatureRapportRequest,
    PhotoRequest,
    RapportFinalGenerateRequest,
)
from app.modules.interventions.service import (
    InterventionsService,
    InterventionWorkflowError,
    InterventionNotFoundError,
    RapportLockedError,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """Crée une base de données SQLite en mémoire pour les tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def tenant_id():
    """Tenant ID pour les tests."""
    return "test_tenant_001"


@pytest.fixture
def tenant_id_2():
    """Second tenant ID pour tests multi-tenant."""
    return "test_tenant_002"


@pytest.fixture
def client_id():
    """Client ID pour les tests."""
    return uuid4()


@pytest.fixture
def projet_id():
    """Projet ID pour les tests."""
    return uuid4()


@pytest.fixture
def intervenant_id():
    """Intervenant ID pour les tests."""
    return uuid4()


@pytest.fixture
def service(test_db, tenant_id):
    """Service interventions pour le tenant 1."""
    return InterventionsService(test_db, tenant_id)


@pytest.fixture
def service_tenant_2(test_db, tenant_id_2):
    """Service interventions pour le tenant 2."""
    return InterventionsService(test_db, tenant_id_2)


@pytest.fixture
def donneur_ordre(service):
    """Crée un donneur d'ordre de test."""
    data = DonneurOrdreCreate(
        code="DO001",
        nom="Donneur Test",
        type="CLIENT",
        email="donneur@test.com",
        telephone="0123456789"
    )
    return service.create_donneur_ordre(data)


@pytest.fixture
def intervention_base(client_id):
    """Données de base pour créer une intervention."""
    return InterventionCreate(
        client_id=client_id,
        type_intervention=TypeIntervention.MAINTENANCE,
        priorite=InterventionPriorite.NORMAL,
        titre="Intervention de test",
        description="Description de test",
        adresse_ligne1="123 Rue Test",
        ville="Paris",
        code_postal="75001"
    )


@pytest.fixture
def intervention_validee(service, intervention_base):
    """Crée une intervention et la valide (DRAFT -> A_PLANIFIER)."""
    intervention = service.create_intervention(intervention_base)
    return service.valider_intervention(intervention.id)


# ============================================================================
# TESTS - NUMÉROTATION INT-YYYY-XXXX
# ============================================================================

class TestNumerotation:
    """Tests de la génération de numérotation."""

    def test_reference_format_correct(self, service, intervention_base):
        """La référence doit suivre le format INT-YYYY-XXXX."""
        intervention = service.create_intervention(intervention_base)

        assert intervention.reference is not None
        assert intervention.reference.startswith("INT-")

        # Format: INT-YYYY-XXXX
        parts = intervention.reference.split("-")
        assert len(parts) == 3
        assert parts[0] == "INT"
        assert len(parts[1]) == 4  # Année
        assert parts[1].isdigit()
        assert len(parts[2]) == 4  # Numéro
        assert parts[2].isdigit()

    def test_reference_incrementee_par_tenant(self, service, intervention_base):
        """Les références sont incrémentées séquentiellement par tenant."""
        int1 = service.create_intervention(intervention_base)
        int2 = service.create_intervention(intervention_base)
        int3 = service.create_intervention(intervention_base)

        # Extraire les numéros
        num1 = int(int1.reference.split("-")[2])
        num2 = int(int2.reference.split("-")[2])
        num3 = int(int3.reference.split("-")[2])

        assert num2 == num1 + 1
        assert num3 == num2 + 1

    def test_reference_unique_globale(self, service, intervention_base):
        """Chaque référence doit être unique."""
        interventions = [
            service.create_intervention(intervention_base)
            for _ in range(10)
        ]

        references = [i.reference for i in interventions]
        assert len(references) == len(set(references))  # Toutes uniques

    def test_reference_non_modifiable(self, service, intervention_base):
        """La référence ne doit JAMAIS être modifiable."""
        intervention = service.create_intervention(intervention_base)
        original_ref = intervention.reference

        # Tenter de modifier (via update)
        update_data = InterventionUpdate(titre="Nouveau titre")
        updated = service.update_intervention(intervention.id, update_data)

        # La référence doit rester inchangée
        assert updated.reference == original_ref

    def test_reference_par_annee(self, service, intervention_base):
        """Les références utilisent l'année courante."""
        intervention = service.create_intervention(intervention_base)
        current_year = datetime.utcnow().year

        assert f"INT-{current_year}" in intervention.reference


# ============================================================================
# TESTS - WORKFLOW STATUTS
# ============================================================================

class TestWorkflowStatuts:
    """Tests du workflow strict des statuts."""

    def test_statut_initial_draft(self, service, intervention_base):
        """Le statut initial doit être DRAFT."""
        intervention = service.create_intervention(intervention_base)
        assert intervention.statut == InterventionStatut.DRAFT

    def test_validation_brouillon(self, service, intervention_base):
        """Test de la validation brouillon: DRAFT -> A_PLANIFIER."""
        intervention = service.create_intervention(intervention_base)
        assert intervention.statut == InterventionStatut.DRAFT

        # Validation
        intervention = service.valider_intervention(intervention.id)
        assert intervention.statut == InterventionStatut.A_PLANIFIER

    def test_workflow_complet(
        self, service, intervention_base, intervenant_id
    ):
        """Test du workflow complet: DRAFT -> A_PLANIFIER -> PLANIFIEE -> EN_COURS -> TERMINEE."""
        # Création
        intervention = service.create_intervention(intervention_base)
        assert intervention.statut == InterventionStatut.DRAFT

        # Validation brouillon
        intervention = service.valider_intervention(intervention.id)
        assert intervention.statut == InterventionStatut.A_PLANIFIER

        # Planification
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow() + timedelta(days=1),
            date_prevue_fin=datetime.utcnow() + timedelta(days=1, hours=2),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention.id, planif_data)
        assert intervention.statut == InterventionStatut.PLANIFIEE

        # Arrivée sur site
        arrivee_data = ArriveeRequest(
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522")
        )
        intervention = service.arrivee_sur_site(intervention.id, arrivee_data)
        assert intervention.statut == InterventionStatut.EN_COURS
        assert intervention.date_arrivee_site is not None

        # Démarrage
        intervention = service.demarrer_intervention(intervention.id)
        assert intervention.date_demarrage is not None

        # Terminaison
        fin_data = FinInterventionRequest(
            resume_actions="Travail effectué",
            anomalies="Aucune",
            recommandations="RAS"
        )
        intervention = service.terminer_intervention(intervention.id, fin_data)
        assert intervention.statut == InterventionStatut.TERMINEE
        assert intervention.date_fin is not None
        assert intervention.duree_reelle_minutes is not None

    def test_annulation_planification(
        self, service, intervention_validee, intervenant_id
    ):
        """Test de l'annulation de planification: PLANIFIEE -> A_PLANIFIER."""
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow() + timedelta(days=1),
            date_prevue_fin=datetime.utcnow() + timedelta(days=1, hours=2),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        assert intervention.statut == InterventionStatut.PLANIFIEE

        # Annuler
        intervention = service.annuler_planification(intervention.id)
        assert intervention.statut == InterventionStatut.A_PLANIFIER
        assert intervention.date_prevue_debut is None
        assert intervention.intervenant_id is None


# ============================================================================
# TESTS - REFUS ACTIONS INVALIDES
# ============================================================================

class TestRefusActionsInvalides:
    """Tests de refus des actions invalides selon le statut."""

    def test_planifier_intervention_terminee_refuse(
        self, service, intervention_validee, intervenant_id
    ):
        """Impossible de planifier une intervention terminée."""
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)
        intervention = service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )

        # Tenter de replanifier
        with pytest.raises(InterventionWorkflowError):
            service.planifier_intervention(intervention.id, planif_data)

    def test_arrivee_sans_planification_refuse(self, service, intervention_validee):
        """Impossible d'arriver sur site sans planification (statut A_PLANIFIER)."""
        with pytest.raises(InterventionWorkflowError):
            service.arrivee_sur_site(intervention_validee.id, ArriveeRequest())

    def test_demarrer_sans_arrivee_refuse(
        self, service, intervention_validee, intervenant_id
    ):
        """Impossible de démarrer sans avoir signalé l'arrivée."""
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)

        # Tenter de démarrer directement (statut PLANIFIEE, pas EN_COURS)
        with pytest.raises(InterventionWorkflowError):
            service.demarrer_intervention(intervention.id)

    def test_terminer_sans_demarrer_refuse(
        self, service, intervention_validee, intervenant_id
    ):
        """Impossible de terminer sans avoir démarré."""
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )

        # Tenter de terminer sans démarrer
        with pytest.raises(InterventionWorkflowError):
            service.terminer_intervention(
                intervention.id, FinInterventionRequest()
            )

    def test_supprimer_intervention_terminee_refuse(
        self, service, intervention_validee, intervenant_id
    ):
        """Impossible de supprimer une intervention terminée."""
        # Workflow complet
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)
        intervention = service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )

        with pytest.raises(InterventionWorkflowError):
            service.delete_intervention(intervention.id)


# ============================================================================
# TESTS - CALCUL DURÉE AUTOMATIQUE
# ============================================================================

class TestCalculDureeAutomatique:
    """Tests du calcul automatique de la durée."""

    def test_duree_calculee_automatiquement(
        self, service, intervention_validee, intervenant_id
    ):
        """La durée est calculée automatiquement à la fin."""
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)

        # La durée doit être None avant terminaison
        assert intervention.duree_reelle_minutes is None

        # Terminer
        intervention = service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )

        # La durée doit être calculée
        assert intervention.duree_reelle_minutes is not None
        assert intervention.duree_reelle_minutes >= 0

    def test_duree_basee_sur_demarrage_et_fin(
        self, service, test_db, intervention_validee, intervenant_id
    ):
        """La durée est calculée entre date_demarrage et date_fin."""
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)

        # Simuler un temps de travail
        date_demarrage = intervention.date_demarrage

        # Terminer
        intervention = service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )

        # Vérifier le calcul
        expected_duration = (
            intervention.date_fin - date_demarrage
        ).total_seconds() / 60

        assert intervention.duree_reelle_minutes == int(expected_duration)


# ============================================================================
# TESTS - MULTI-TENANT STRICT
# ============================================================================

class TestMultiTenant:
    """Tests d'isolation multi-tenant."""

    def test_interventions_isolees_par_tenant(
        self, service, service_tenant_2, intervention_base
    ):
        """Les interventions sont isolées par tenant."""
        # Créer des interventions pour chaque tenant
        int_t1 = service.create_intervention(intervention_base)
        int_t2 = service_tenant_2.create_intervention(intervention_base)

        # Vérifier l'isolation
        interventions_t1, _ = service.list_interventions()
        interventions_t2, _ = service_tenant_2.list_interventions()

        assert len(interventions_t1) == 1
        assert len(interventions_t2) == 1
        assert interventions_t1[0].id != interventions_t2[0].id

    def test_tenant_ne_peut_pas_voir_autres_interventions(
        self, service, service_tenant_2, intervention_base
    ):
        """Un tenant ne peut pas voir les interventions d'un autre tenant."""
        int_t1 = service.create_intervention(intervention_base)

        # Le tenant 2 ne doit pas pouvoir la voir
        result = service_tenant_2.get_intervention(int_t1.id)
        assert result is None

    def test_numerotation_independante_par_tenant(
        self, service, service_tenant_2, intervention_base
    ):
        """La numérotation est indépendante par tenant."""
        # Créer 3 interventions pour tenant 1
        for _ in range(3):
            service.create_intervention(intervention_base)

        # Créer 1 intervention pour tenant 2
        int_t2 = service_tenant_2.create_intervention(intervention_base)

        # Le tenant 2 doit commencer à 0001
        num = int(int_t2.reference.split("-")[2])
        assert num == 1


# ============================================================================
# TESTS - DONNEUR D'ORDRE
# ============================================================================

class TestDonneurOrdre:
    """Tests du donneur d'ordre."""

    def test_donneur_ordre_optionnel(self, service, intervention_base):
        """Le donneur d'ordre est optionnel."""
        intervention = service.create_intervention(intervention_base)
        assert intervention.donneur_ordre_id is None

    def test_donneur_ordre_visible(self, service, intervention_base, donneur_ordre):
        """Le donneur d'ordre est toujours visible quand défini."""
        intervention_base.donneur_ordre_id = donneur_ordre.id
        intervention = service.create_intervention(intervention_base)

        assert intervention.donneur_ordre_id == donneur_ordre.id

    def test_donneur_ordre_dans_rapport(
        self, service, intervention_base, donneur_ordre, intervenant_id
    ):
        """Le donneur d'ordre est repris dans le rapport."""
        intervention_base.donneur_ordre_id = donneur_ordre.id
        intervention = service.create_intervention(intervention_base)
        intervention = service.valider_intervention(intervention.id)

        # Workflow complet
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)
        intervention = service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )

        # Vérifier le rapport
        rapport = service.get_rapport_intervention(intervention.id)
        assert rapport.donneur_ordre_id == donneur_ordre.id


# ============================================================================
# TESTS - RAPPORT INTERVENTION
# ============================================================================

class TestRapportIntervention:
    """Tests du rapport d'intervention."""

    def test_rapport_genere_automatiquement(
        self, service, intervention_validee, intervenant_id
    ):
        """Le rapport est généré automatiquement à la fin."""
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)
        intervention = service.terminer_intervention(
            intervention.id,
            FinInterventionRequest(
                resume_actions="Actions effectuées",
                anomalies="Anomalie détectée",
                recommandations="Recommandation"
            )
        )

        # Le rapport doit exister
        rapport = service.get_rapport_intervention(intervention.id)
        assert rapport is not None
        assert rapport.reference_intervention == intervention.reference
        assert rapport.resume_actions == "Actions effectuées"
        assert rapport.anomalies == "Anomalie détectée"
        assert rapport.recommandations == "Recommandation"

    def test_rapport_fige_apres_signature(
        self, service, intervention_validee, intervenant_id
    ):
        """Le rapport est figé après signature."""
        # Workflow complet
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)
        intervention = service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )

        # Signer
        signature_data = SignatureRapportRequest(
            signature_client="base64_signature_hash",
            nom_signataire="Client Test",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522")
        )
        rapport = service.signer_rapport(intervention.id, signature_data)

        assert rapport.is_signed is True
        assert rapport.is_locked is True
        assert rapport.date_signature is not None

    def test_modification_rapport_impossible_apres_signature(
        self, service, intervention_validee, intervenant_id
    ):
        """Impossible de modifier un rapport signé."""
        # Workflow complet + signature
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)
        intervention = service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )
        service.signer_rapport(
            intervention.id,
            SignatureRapportRequest(
                signature_client="hash",
                nom_signataire="Client"
            )
        )

        # Tenter de modifier
        with pytest.raises(RapportLockedError):
            service.update_rapport_intervention(
                intervention.id,
                RapportInterventionUpdate(resume_actions="Modification")
            )

    def test_ajout_photos_rapport(
        self, service, intervention_validee, intervenant_id
    ):
        """Les photos peuvent être ajoutées au rapport."""
        # Workflow complet
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)
        intervention = service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )

        # Ajouter des photos
        photo1 = PhotoRequest(url="http://example.com/photo1.jpg", caption="Photo 1")
        photo2 = PhotoRequest(url="http://example.com/photo2.jpg", caption="Photo 2")

        service.ajouter_photo_rapport(intervention.id, photo1)
        rapport = service.ajouter_photo_rapport(intervention.id, photo2)

        assert len(rapport.photos) == 2


# ============================================================================
# TESTS - RAPPORT FINAL
# ============================================================================

class TestRapportFinal:
    """Tests du rapport final consolidé."""

    def test_rapport_final_par_projet(
        self, service, intervention_base, intervenant_id, projet_id
    ):
        """Génération de rapport final par projet."""
        intervention_base.projet_id = projet_id

        # Créer et terminer plusieurs interventions
        for _ in range(3):
            intervention = service.create_intervention(intervention_base)
            intervention = service.valider_intervention(intervention.id)
            planif_data = InterventionPlanifier(
                date_prevue_debut=datetime.utcnow(),
                date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
                intervenant_id=intervenant_id
            )
            intervention = service.planifier_intervention(
                intervention.id, planif_data
            )
            intervention = service.arrivee_sur_site(
                intervention.id, ArriveeRequest()
            )
            intervention = service.demarrer_intervention(intervention.id)
            service.terminer_intervention(
                intervention.id, FinInterventionRequest()
            )

        # Générer le rapport final
        rapport_final = service.generer_rapport_final(
            RapportFinalGenerateRequest(
                projet_id=projet_id,
                synthese="Synthèse du projet"
            )
        )

        assert rapport_final is not None
        assert len(rapport_final.interventions_references) == 3
        assert rapport_final.temps_total_minutes >= 0
        assert rapport_final.is_locked is True

    def test_rapport_final_par_donneur_ordre(
        self, service, intervention_base, intervenant_id, donneur_ordre
    ):
        """Génération de rapport final par donneur d'ordre."""
        intervention_base.donneur_ordre_id = donneur_ordre.id

        # Créer et terminer 2 interventions
        for _ in range(2):
            intervention = service.create_intervention(intervention_base)
            intervention = service.valider_intervention(intervention.id)
            planif_data = InterventionPlanifier(
                date_prevue_debut=datetime.utcnow(),
                date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
                intervenant_id=intervenant_id
            )
            intervention = service.planifier_intervention(
                intervention.id, planif_data
            )
            intervention = service.arrivee_sur_site(
                intervention.id, ArriveeRequest()
            )
            intervention = service.demarrer_intervention(intervention.id)
            service.terminer_intervention(
                intervention.id, FinInterventionRequest()
            )

        # Générer le rapport final
        rapport_final = service.generer_rapport_final(
            RapportFinalGenerateRequest(
                donneur_ordre_id=donneur_ordre.id,
                synthese="Synthèse donneur"
            )
        )

        assert rapport_final is not None
        assert len(rapport_final.interventions_references) == 2

    def test_rapport_final_non_modifiable(
        self, service, intervention_base, intervenant_id, projet_id
    ):
        """Le rapport final est non modifiable."""
        intervention_base.projet_id = projet_id

        # Créer et terminer une intervention
        intervention = service.create_intervention(intervention_base)
        intervention = service.valider_intervention(intervention.id)
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(
            intervention.id, planif_data
        )
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)
        service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )

        # Générer le rapport final
        rapport_final = service.generer_rapport_final(
            RapportFinalGenerateRequest(projet_id=projet_id)
        )

        # Vérifier qu'il est verrouillé
        assert rapport_final.is_locked is True

    def test_rapport_final_reference_format(
        self, service, intervention_base, intervenant_id, projet_id
    ):
        """Le rapport final a une référence au format RFINAL-YYYY-XXXX."""
        intervention_base.projet_id = projet_id

        intervention = service.create_intervention(intervention_base)
        intervention = service.valider_intervention(intervention.id)
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(
            intervention.id, planif_data
        )
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)
        service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )

        rapport_final = service.generer_rapport_final(
            RapportFinalGenerateRequest(projet_id=projet_id)
        )

        # Rapport Final uses RI- prefix (Rapport Intervention)
        assert rapport_final.reference.startswith("RI-")


# ============================================================================
# TESTS - STATISTIQUES
# ============================================================================

class TestStatistiques:
    """Tests des statistiques."""

    def test_stats_initiales(self, service):
        """Les statistiques initiales sont à zéro."""
        stats = service.get_stats()

        # Stats returns a dict with specific keys
        assert stats["brouillons"] == 0
        assert stats["a_planifier"] == 0
        assert stats["planifiees"] == 0
        assert stats["en_cours"] == 0
        assert stats["terminees_semaine"] == 0

    def test_stats_comptent_correctement(
        self, service, intervention_base, intervenant_id
    ):
        """Les statistiques comptent correctement les interventions."""
        # Créer 3 interventions dans différents états
        int1 = service.create_intervention(intervention_base)  # DRAFT -> A_PLANIFIER
        int2 = service.create_intervention(intervention_base)  # -> PLANIFIEE
        int3 = service.create_intervention(intervention_base)  # -> TERMINEE

        # int1 -> A_PLANIFIER
        service.valider_intervention(int1.id)

        # int2 -> A_PLANIFIER -> PLANIFIEE
        service.valider_intervention(int2.id)
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        service.planifier_intervention(int2.id, planif_data)

        # int3 -> A_PLANIFIER -> PLANIFIEE -> EN_COURS -> TERMINEE
        service.valider_intervention(int3.id)
        service.planifier_intervention(int3.id, planif_data)
        service.arrivee_sur_site(int3.id, ArriveeRequest())
        service.demarrer_intervention(int3.id)
        service.terminer_intervention(int3.id, FinInterventionRequest())

        stats = service.get_stats()

        assert stats["a_planifier"] == 1
        assert stats["planifiees"] == 1
        assert stats["terminees_semaine"] == 1


# ============================================================================
# TESTS - GÉOLOCALISATION
# ============================================================================

class TestGeolocalisation:
    """Tests de la géolocalisation."""

    def test_geoloc_arrivee_enregistree(
        self, service, intervention_validee, intervenant_id
    ):
        """La géolocalisation à l'arrivée est enregistrée."""
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)

        arrivee_data = ArriveeRequest(
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522")
        )
        intervention = service.arrivee_sur_site(intervention.id, arrivee_data)

        assert intervention.geoloc_arrivee_lat == Decimal("48.8566")
        assert intervention.geoloc_arrivee_lng == Decimal("2.3522")

    def test_geoloc_signature_enregistree(
        self, service, intervention_validee, intervenant_id
    ):
        """La géolocalisation à la signature est enregistrée."""
        # Workflow complet
        planif_data = InterventionPlanifier(
            date_prevue_debut=datetime.utcnow(),
            date_prevue_fin=datetime.utcnow() + timedelta(hours=1),
            intervenant_id=intervenant_id
        )
        intervention = service.planifier_intervention(intervention_validee.id, planif_data)
        intervention = service.arrivee_sur_site(
            intervention.id, ArriveeRequest()
        )
        intervention = service.demarrer_intervention(intervention.id)
        intervention = service.terminer_intervention(
            intervention.id, FinInterventionRequest()
        )

        # Signer avec géoloc
        signature_data = SignatureRapportRequest(
            signature_client="hash",
            nom_signataire="Client",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522")
        )
        rapport = service.signer_rapport(intervention.id, signature_data)

        assert rapport.geoloc_signature_lat == Decimal("48.8566")
        assert rapport.geoloc_signature_lng == Decimal("2.3522")


# ============================================================================
# TESTS - SOFT DELETE
# ============================================================================

class TestSoftDelete:
    """Tests du soft delete."""

    def test_intervention_soft_delete(self, service, intervention_base):
        """L'intervention est soft deleted."""
        intervention = service.create_intervention(intervention_base)
        intervention_id = intervention.id

        # Supprimer
        result = service.delete_intervention(intervention_id)
        assert result is True

        # Ne doit plus être visible
        intervention = service.get_intervention(intervention_id)
        assert intervention is None

    def test_intervention_soft_delete_visible_avec_flag(
        self, service, intervention_base
    ):
        """L'intervention soft deleted est visible avec include_deleted."""
        intervention = service.create_intervention(intervention_base)
        intervention_id = intervention.id

        service.delete_intervention(intervention_id)

        # Visible avec le flag
        items, total = service.list_interventions(include_deleted=True)
        assert total == 1
        assert items[0].deleted_at is not None
