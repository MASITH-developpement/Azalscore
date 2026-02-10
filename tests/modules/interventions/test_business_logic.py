"""
Tests métier pour le module INTERVENTIONS — Logique business AZALSCORE.

Couverture:
- State machine 7 états (DRAFT, A_PLANIFIER, PLANIFIEE, EN_COURS, BLOQUEE, TERMINEE, ANNULEE)
- Transitions valides et invalides
- Validation brouillon (DRAFT → A_PLANIFIER)
- Blocage / déblocage (EN_COURS ↔ BLOQUEE)
- Interdiction de changement direct de statut via update
- Indicateurs métier (retard, dérive durée, risque)
- Analyse IA (structure retour, score, déductions)
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.interventions.models import (
    Intervention,
    InterventionStatut,
    InterventionPriorite,
    TypeIntervention,
)
# Import audit models so Base.metadata includes audit_logs table
import app.modules.audit.models  # noqa: F401
from app.modules.interventions.schemas import (
    InterventionCreate,
    InterventionUpdate,
    InterventionPlanifier,
    ArriveeRequest,
    FinInterventionRequest,
)
from app.modules.interventions.service import (
    InterventionsService,
    InterventionWorkflowError,
    InterventionNotFoundError,
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """Base SQLite en mémoire."""
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
    return "test_tenant_biz"


@pytest.fixture
def client_id():
    return uuid4()


@pytest.fixture
def intervenant_id():
    return uuid4()


@pytest.fixture
def service(test_db, tenant_id):
    return InterventionsService(test_db, tenant_id)


@pytest.fixture
def intervention_base(client_id):
    """Données de base pour créer une intervention."""
    return InterventionCreate(
        client_id=client_id,
        type_intervention=TypeIntervention.MAINTENANCE,
        priorite=InterventionPriorite.NORMAL,
        titre="Test Business Logic",
        description="Description test",
        adresse_ligne1="123 Rue Test",
        ville="Paris",
        code_postal="75001",
    )


@pytest.fixture
def intervention_sans_titre(client_id):
    """Intervention sans titre — doit échouer à la validation."""
    return InterventionCreate(
        client_id=client_id,
        type_intervention=TypeIntervention.AUTRE,
        priorite=InterventionPriorite.NORMAL,
    )


@pytest.fixture
def intervention_urgente(client_id):
    """Intervention urgente pour tests risque."""
    return InterventionCreate(
        client_id=client_id,
        type_intervention=TypeIntervention.REPARATION,
        priorite=InterventionPriorite.URGENT,
        titre="Urgente test",
        description="Intervention urgente",
    )


# ============================================================================
# TESTS - ÉTAT DRAFT
# ============================================================================

class TestDraftState:
    """Tests du statut DRAFT (brouillon)."""

    def test_create_intervention_starts_as_draft(self, service, intervention_base):
        """La création doit produire un statut DRAFT."""
        intervention = service.create_intervention(intervention_base)
        fresh = service.get_intervention(intervention.id)
        assert fresh.statut == InterventionStatut.DRAFT

    def test_valider_draft_to_a_planifier(self, service, intervention_base):
        """Valider : DRAFT → A_PLANIFIER."""
        intervention = service.create_intervention(intervention_base)
        validated = service.valider_intervention(intervention.id)
        assert validated.statut == InterventionStatut.A_PLANIFIER

    def test_valider_non_draft_raises_error(self, service, intervention_base, intervenant_id):
        """Valider une intervention non-DRAFT doit lever une erreur."""
        intervention = service.create_intervention(intervention_base)
        service.valider_intervention(intervention.id)
        # L'intervention est maintenant A_PLANIFIER, valider à nouveau doit échouer
        with pytest.raises(InterventionWorkflowError):
            service.valider_intervention(intervention.id)

    def test_valider_sans_titre_raises_error(self, service, intervention_sans_titre):
        """Valider sans titre doit lever une erreur."""
        intervention = service.create_intervention(intervention_sans_titre)
        with pytest.raises(InterventionWorkflowError):
            service.valider_intervention(intervention.id)


# ============================================================================
# TESTS - ÉTAT BLOQUEE
# ============================================================================

class TestBlocageState:
    """Tests du blocage / déblocage."""

    def _advance_to_en_cours(self, service, intervention_base, intervenant_id):
        """Helper : avancer une intervention jusqu'à EN_COURS."""
        intervention = service.create_intervention(intervention_base)
        service.valider_intervention(intervention.id)
        data = InterventionPlanifier(
            date_prevue_debut=datetime.now() + timedelta(hours=1),
            date_prevue_fin=datetime.now() + timedelta(hours=3),
            intervenant_id=intervenant_id,
        )
        service.planifier_intervention(intervention.id, data)
        service.arrivee_sur_site(intervention.id, ArriveeRequest())
        return service.get_intervention(intervention.id)

    def test_bloquer_en_cours(self, service, intervention_base, intervenant_id):
        """Bloquer : EN_COURS → BLOQUEE."""
        intervention = self._advance_to_en_cours(service, intervention_base, intervenant_id)
        blocked = service.bloquer_intervention(intervention.id, "Problème matériel détecté")
        assert blocked.statut == InterventionStatut.BLOQUEE
        assert blocked.motif_blocage == "Problème matériel détecté"
        assert blocked.date_blocage is not None

    def test_bloquer_motif_obligatoire(self, service, intervention_base, intervenant_id):
        """Bloquer sans motif suffisant doit échouer."""
        intervention = self._advance_to_en_cours(service, intervention_base, intervenant_id)
        with pytest.raises((InterventionWorkflowError, ValueError)):
            service.bloquer_intervention(intervention.id, "")

    def test_debloquer_bloquee(self, service, intervention_base, intervenant_id):
        """Débloquer : BLOQUEE → EN_COURS."""
        intervention = self._advance_to_en_cours(service, intervention_base, intervenant_id)
        service.bloquer_intervention(intervention.id, "Attente pièces de rechange")
        unblocked = service.debloquer_intervention(intervention.id)
        assert unblocked.statut == InterventionStatut.EN_COURS
        assert unblocked.date_deblocage is not None

    def test_annuler_bloquee(self, service, intervention_base, intervenant_id):
        """Annuler une intervention BLOQUEE."""
        intervention = self._advance_to_en_cours(service, intervention_base, intervenant_id)
        service.bloquer_intervention(intervention.id, "Client injoignable")
        cancelled = service.annuler_intervention(intervention.id)
        assert cancelled.statut == InterventionStatut.ANNULEE


# ============================================================================
# TESTS - TRANSITIONS INVALIDES
# ============================================================================

class TestInvalidTransitions:
    """Tests des transitions interdites."""

    def _create_draft(self, service, intervention_base):
        return service.create_intervention(intervention_base)

    def test_draft_cannot_planifier(self, service, intervention_base, intervenant_id):
        """DRAFT ne peut pas être planifié directement."""
        intervention = self._create_draft(service, intervention_base)
        data = InterventionPlanifier(
            date_prevue_debut=datetime.now() + timedelta(hours=1),
            date_prevue_fin=datetime.now() + timedelta(hours=3),
            intervenant_id=intervenant_id,
        )
        with pytest.raises(InterventionWorkflowError):
            service.planifier_intervention(intervention.id, data)

    def test_draft_cannot_demarrer(self, service, intervention_base):
        """DRAFT ne peut pas être démarré."""
        intervention = self._create_draft(service, intervention_base)
        with pytest.raises(InterventionWorkflowError):
            service.arrivee_sur_site(intervention.id, ArriveeRequest())

    def test_draft_cannot_terminer(self, service, intervention_base):
        """DRAFT ne peut pas être terminé."""
        intervention = self._create_draft(service, intervention_base)
        with pytest.raises(InterventionWorkflowError):
            service.terminer_intervention(intervention.id, FinInterventionRequest())

    def test_draft_cannot_bloquer(self, service, intervention_base):
        """DRAFT ne peut pas être bloqué."""
        intervention = self._create_draft(service, intervention_base)
        with pytest.raises(InterventionWorkflowError):
            service.bloquer_intervention(intervention.id, "Motif test blocage")

    def test_a_planifier_cannot_demarrer(self, service, intervention_base):
        """A_PLANIFIER ne peut pas être démarré."""
        intervention = self._create_draft(service, intervention_base)
        service.valider_intervention(intervention.id)
        with pytest.raises(InterventionWorkflowError):
            service.arrivee_sur_site(intervention.id, ArriveeRequest())

    def test_planifiee_cannot_bloquer(self, service, intervention_base, intervenant_id):
        """PLANIFIEE ne peut pas être bloquée."""
        intervention = self._create_draft(service, intervention_base)
        service.valider_intervention(intervention.id)
        data = InterventionPlanifier(
            date_prevue_debut=datetime.now() + timedelta(hours=1),
            date_prevue_fin=datetime.now() + timedelta(hours=3),
            intervenant_id=intervenant_id,
        )
        service.planifier_intervention(intervention.id, data)
        with pytest.raises(InterventionWorkflowError):
            service.bloquer_intervention(intervention.id, "Motif test blocage")

    def test_terminee_is_terminal(self, service, intervention_base, intervenant_id):
        """TERMINEE est un état terminal : aucune transition possible."""
        intervention = service.create_intervention(intervention_base)
        service.valider_intervention(intervention.id)
        data = InterventionPlanifier(
            date_prevue_debut=datetime.now() + timedelta(hours=1),
            date_prevue_fin=datetime.now() + timedelta(hours=3),
            intervenant_id=intervenant_id,
        )
        service.planifier_intervention(intervention.id, data)
        service.arrivee_sur_site(intervention.id, ArriveeRequest())
        service.demarrer_intervention(intervention.id)
        service.terminer_intervention(intervention.id, FinInterventionRequest())
        with pytest.raises(InterventionWorkflowError):
            service.annuler_intervention(intervention.id)

    def test_annulee_is_terminal(self, service, intervention_base):
        """ANNULEE est un état terminal : aucune transition possible."""
        intervention = service.create_intervention(intervention_base)
        service.valider_intervention(intervention.id)
        service.annuler_intervention(intervention.id)
        with pytest.raises(InterventionWorkflowError):
            service.valider_intervention(intervention.id)

    def test_bloquee_cannot_terminer(self, service, intervention_base, intervenant_id):
        """BLOQUEE ne peut pas être terminée directement."""
        intervention = service.create_intervention(intervention_base)
        service.valider_intervention(intervention.id)
        data = InterventionPlanifier(
            date_prevue_debut=datetime.now() + timedelta(hours=1),
            date_prevue_fin=datetime.now() + timedelta(hours=3),
            intervenant_id=intervenant_id,
        )
        service.planifier_intervention(intervention.id, data)
        service.arrivee_sur_site(intervention.id, ArriveeRequest())
        service.bloquer_intervention(intervention.id, "Problème technique")
        with pytest.raises(InterventionWorkflowError):
            service.terminer_intervention(intervention.id, FinInterventionRequest())

    def test_bloquee_cannot_bloquer_again(self, service, intervention_base, intervenant_id):
        """BLOQUEE ne peut pas être bloquée à nouveau."""
        intervention = service.create_intervention(intervention_base)
        service.valider_intervention(intervention.id)
        data = InterventionPlanifier(
            date_prevue_debut=datetime.now() + timedelta(hours=1),
            date_prevue_fin=datetime.now() + timedelta(hours=3),
            intervenant_id=intervenant_id,
        )
        service.planifier_intervention(intervention.id, data)
        service.arrivee_sur_site(intervention.id, ArriveeRequest())
        service.bloquer_intervention(intervention.id, "Premier blocage")
        with pytest.raises(InterventionWorkflowError):
            service.bloquer_intervention(intervention.id, "Deuxième blocage")


# ============================================================================
# TESTS - INTERDICTION STATUT VIA CRUD
# ============================================================================

class TestNoDirectStatutUpdate:
    """Interdiction de modifier le statut via update_intervention."""

    def test_update_schema_strips_statut(self, service, intervention_base):
        """InterventionUpdate ne doit pas inclure 'statut' dans model_dump."""
        update_data = InterventionUpdate(titre="Nouveau titre")
        raw = update_data.model_dump(exclude_unset=True)
        assert "statut" not in raw, "Le schéma InterventionUpdate ne doit pas exposer le statut"

    def test_update_with_statut_raises_error(self, service, intervention_base):
        """Le service rejette les mises à jour contenant 'statut' (défense en profondeur)."""
        intervention = service.create_intervention(intervention_base)
        # Simuler un bypass du schéma Pydantic (défense en profondeur)
        class _FakeUpdate:
            def model_dump(self, **kwargs):
                return {"titre": "Nouveau titre", "statut": "TERMINEE"}
        with pytest.raises(InterventionWorkflowError):
            service.update_intervention(intervention.id, _FakeUpdate())

    def test_update_without_statut_works(self, service, intervention_base):
        """update_intervention sans statut doit fonctionner."""
        intervention = service.create_intervention(intervention_base)
        update_data = InterventionUpdate(titre="Titre modifié")
        updated = service.update_intervention(intervention.id, update_data)
        assert updated.titre == "Titre modifié"


# ============================================================================
# TESTS - INDICATEURS MÉTIER
# ============================================================================

class TestBusinessIndicators:
    """Tests des calculs d'indicateurs métier."""

    def _create_intervention_with_dates(self, service, client_id, date_prevue_fin, statut_cible="EN_COURS", intervenant_id=None):
        """Crée une intervention et l'avance au statut souhaité avec une date de fin."""
        data = InterventionCreate(
            client_id=client_id,
            type_intervention=TypeIntervention.MAINTENANCE,
            priorite=InterventionPriorite.NORMAL,
            titre="Test indicateurs",
            date_prevue_debut=date_prevue_fin - timedelta(hours=2),
            date_prevue_fin=date_prevue_fin,
        )
        intervention = service.create_intervention(data)

        if statut_cible == "DRAFT":
            return service.get_intervention(intervention.id)

        service.valider_intervention(intervention.id)
        if statut_cible == "A_PLANIFIER":
            return service.get_intervention(intervention.id)

        plan_data = InterventionPlanifier(
            date_prevue_debut=date_prevue_fin - timedelta(hours=2),
            date_prevue_fin=date_prevue_fin,
            intervenant_id=intervenant_id or uuid4(),
        )
        service.planifier_intervention(intervention.id, plan_data)
        if statut_cible == "PLANIFIEE":
            return service.get_intervention(intervention.id)

        service.arrivee_sur_site(intervention.id, ArriveeRequest())
        return service.get_intervention(intervention.id)

    def test_indicateurs_retard(self, service, client_id, intervenant_id):
        """En retard si date_prevue_fin est dépassée."""
        past_date = datetime.now() - timedelta(days=3)
        intervention = self._create_intervention_with_dates(
            service, client_id, past_date, "EN_COURS", intervenant_id
        )
        indicateurs = service.calculer_indicateurs_business(intervention)
        assert indicateurs["en_retard"] is True
        assert indicateurs["jours_retard"] > 0
        assert indicateurs["indicateur_risque"] in ("MOYEN", "ELEVE", "CRITIQUE")

    def test_indicateurs_pas_retard_terminee(self, service, client_id, intervenant_id):
        """Pas de retard si l'intervention est TERMINEE."""
        past_date = datetime.now() - timedelta(days=3)
        data = InterventionCreate(
            client_id=client_id,
            type_intervention=TypeIntervention.MAINTENANCE,
            priorite=InterventionPriorite.NORMAL,
            titre="Test terminée",
            date_prevue_debut=past_date - timedelta(hours=2),
            date_prevue_fin=past_date,
        )
        intervention = service.create_intervention(data)
        service.valider_intervention(intervention.id)
        plan_data = InterventionPlanifier(
            date_prevue_debut=past_date - timedelta(hours=2),
            date_prevue_fin=past_date,
            intervenant_id=intervenant_id,
        )
        service.planifier_intervention(intervention.id, plan_data)
        service.arrivee_sur_site(intervention.id, ArriveeRequest())
        service.demarrer_intervention(intervention.id)
        service.terminer_intervention(intervention.id, FinInterventionRequest())
        finished = service.get_intervention(intervention.id)
        indicateurs = service.calculer_indicateurs_business(finished)
        assert indicateurs["en_retard"] is False

    def test_indicateurs_risque_critique(self, service, client_id, intervenant_id):
        """Risque CRITIQUE = retard important + urgente + bloquée."""
        past_date = datetime.now() - timedelta(days=10)
        data = InterventionCreate(
            client_id=client_id,
            type_intervention=TypeIntervention.REPARATION,
            priorite=InterventionPriorite.URGENT,
            titre="Test critique",
            date_prevue_debut=past_date - timedelta(hours=2),
            date_prevue_fin=past_date,
        )
        intervention = service.create_intervention(data)
        service.valider_intervention(intervention.id)
        plan_data = InterventionPlanifier(
            date_prevue_debut=past_date - timedelta(hours=2),
            date_prevue_fin=past_date,
            intervenant_id=intervenant_id,
        )
        service.planifier_intervention(intervention.id, plan_data)
        service.arrivee_sur_site(intervention.id, ArriveeRequest())
        service.bloquer_intervention(intervention.id, "Pièces manquantes grave")
        blocked = service.get_intervention(intervention.id)
        indicateurs = service.calculer_indicateurs_business(blocked)
        assert indicateurs["indicateur_risque"] == "CRITIQUE"

    def test_indicateurs_faible_sans_probleme(self, service, client_id, intervenant_id):
        """Risque FAIBLE si tout est OK."""
        future_date = datetime.now() + timedelta(days=5)
        intervention = self._create_intervention_with_dates(
            service, client_id, future_date, "EN_COURS", intervenant_id
        )
        indicateurs = service.calculer_indicateurs_business(intervention)
        assert indicateurs["en_retard"] is False
        assert indicateurs["indicateur_risque"] == "FAIBLE"


# ============================================================================
# TESTS - ANALYSE IA
# ============================================================================

class TestAnalyseIA:
    """Tests de l'analyse IA audit-proof."""

    def test_analyse_ia_structure(self, service, intervention_base, intervenant_id):
        """L'analyse IA doit retourner la structure attendue."""
        intervention = service.create_intervention(intervention_base)
        service.valider_intervention(intervention.id)
        result = service.analyser_ia(intervention.id)
        assert "indicateurs" in result
        assert "resume_ia" in result
        assert "actions_suggerees" in result
        assert "score_preparation" in result
        assert "score_deductions" in result
        assert "generated_at" in result

    def test_analyse_ia_score_range(self, service, intervention_base):
        """Le score de préparation doit être entre 0 et 100."""
        intervention = service.create_intervention(intervention_base)
        result = service.analyser_ia(intervention.id)
        assert 0 <= result["score_preparation"] <= 100

    def test_analyse_ia_deductions(self, service, client_id):
        """L'analyse IA doit inclure des déductions si problèmes."""
        data = InterventionCreate(
            client_id=client_id,
            type_intervention=TypeIntervention.AUTRE,
            priorite=InterventionPriorite.URGENT,
            titre="Test déductions",
        )
        intervention = service.create_intervention(data)
        result = service.analyser_ia(intervention.id)
        # Pas d'adresse + pas d'intervenant + DRAFT → déductions
        assert len(result["score_deductions"]) > 0

    def test_analyse_ia_actions_draft(self, service, intervention_base):
        """Pour un DRAFT, l'IA doit suggérer de valider."""
        intervention = service.create_intervention(intervention_base)
        result = service.analyser_ia(intervention.id)
        action_names = [a["action"] for a in result["actions_suggerees"]]
        assert "valider" in action_names

    def test_analyse_ia_actions_bloquee(self, service, intervention_base, intervenant_id):
        """Pour une BLOQUEE, l'IA doit suggérer de débloquer."""
        intervention = service.create_intervention(intervention_base)
        service.valider_intervention(intervention.id)
        data = InterventionPlanifier(
            date_prevue_debut=datetime.now() + timedelta(hours=1),
            date_prevue_fin=datetime.now() + timedelta(hours=3),
            intervenant_id=intervenant_id,
        )
        service.planifier_intervention(intervention.id, data)
        service.arrivee_sur_site(intervention.id, ArriveeRequest())
        service.bloquer_intervention(intervention.id, "Attente autorisation")
        result = service.analyser_ia(intervention.id)
        action_names = [a["action"] for a in result["actions_suggerees"]]
        assert "debloquer" in action_names

    def test_analyse_ia_not_found(self, service):
        """Analyse IA sur intervention inexistante doit lever une erreur."""
        with pytest.raises(InterventionNotFoundError):
            service.analyser_ia(uuid4())

    def test_analyse_ia_generated_at(self, service, intervention_base):
        """generated_at doit être un timestamp ISO valide."""
        intervention = service.create_intervention(intervention_base)
        result = service.analyser_ia(intervention.id)
        generated_at = result["generated_at"]
        # Doit être parseable comme datetime ISO
        dt = datetime.fromisoformat(generated_at)
        assert dt.year >= 2026


# ============================================================================
# TESTS - STATS ENRICHIES
# ============================================================================

class TestStatsEnrichies:
    """Tests des statistiques avec brouillons et bloquées."""

    def test_stats_includes_brouillons(self, service, intervention_base):
        """Les stats doivent inclure le compteur brouillons."""
        service.create_intervention(intervention_base)
        stats = service.get_stats()
        assert "brouillons" in stats
        assert stats["brouillons"] >= 1

    def test_stats_includes_bloquees(self, service, intervention_base, intervenant_id):
        """Les stats doivent inclure le compteur bloquées."""
        intervention = service.create_intervention(intervention_base)
        service.valider_intervention(intervention.id)
        data = InterventionPlanifier(
            date_prevue_debut=datetime.now() + timedelta(hours=1),
            date_prevue_fin=datetime.now() + timedelta(hours=3),
            intervenant_id=intervenant_id,
        )
        service.planifier_intervention(intervention.id, data)
        service.arrivee_sur_site(intervention.id, ArriveeRequest())
        service.bloquer_intervention(intervention.id, "Attente pièces")
        stats = service.get_stats()
        assert "bloquees" in stats
        assert stats["bloquees"] >= 1
