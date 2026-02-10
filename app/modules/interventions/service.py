"""
AZALS MODULE INTERVENTIONS - Service
=====================================

Logique métier pour le module Interventions v1.

Responsabilités:
- Numérotation transactionnelle INT-YYYY-XXXX
- Gestion workflow strict des statuts
- Actions terrain (arrivée, démarrage, fin)
- Calcul automatique du temps
- Génération rapports
- Intégration Planning
"""

import logging
import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from .models import (
    DonneurOrdre,
    Intervention,
    InterventionPriorite,
    InterventionSequence,
    InterventionStatut,
    RapportFinal,
    RapportIntervention,
)
from .schemas import (
    ArriveeRequest,
    DonneurOrdreCreate,
    DonneurOrdreUpdate,
    FinInterventionRequest,
    InterventionCreate,
    InterventionPlanifier,
    InterventionStats,
    InterventionUpdate,
    PhotoRequest,
    RapportFinalGenerateRequest,
    RapportInterventionUpdate,
    SignatureRapportRequest,
)

logger = logging.getLogger(__name__)

# ========================================================================
# AUDIT LOGGING (AZA-SEC, AZA-DATA)
# ========================================================================

def _get_audit_service(db: Session, tenant_id: str):
    """
    Retourne le service d'audit si disponible.

    Dégradation gracieuse : si le module audit n'est pas chargé,
    les opérations continuent sans audit (log warning).
    """
    try:
        from app.modules.audit.service import AuditService
        return AuditService(db=db, tenant_id=tenant_id)
    except ImportError:
        logger.warning("[INTERVENTIONS] Module audit non disponible - audit désactivé")
        return None


def _audit_log(
    db: Session,
    tenant_id: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    user_id: str | None = None,
    description: str | None = None,
    old_value=None,
    new_value=None,
):
    """
    Enregistre un événement d'audit pour le module interventions.

    Conforme AZA-SEC-003 : toute mutation est traçable.
    """
    audit = _get_audit_service(db, tenant_id)
    if audit is None:
        return
    try:
        from app.modules.audit.models import AuditAction, AuditCategory, AuditLevel
        action_enum = getattr(AuditAction, action, AuditAction.UPDATE)
        audit.log(
            action=action_enum,
            module="interventions",
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            user_id=int(user_id) if user_id and str(user_id).isdigit() else None,
            description=description,
            old_value=old_value,
            new_value=new_value,
            category=AuditCategory.BUSINESS,
            level=AuditLevel.INFO,
        )
    except Exception as e:
        logger.warning(
            "[INTERVENTIONS_AUDIT] Échec enregistrement audit: %s",
            str(e)[:200],
        )


class InterventionWorkflowError(Exception):
    """Erreur de workflow d'intervention."""
    pass


class InterventionNotFoundError(Exception):
    """Intervention non trouvée."""
    pass


class RapportLockedError(Exception):
    """Rapport verrouillé, modification impossible."""
    pass


class InterventionsService:
    """
    Service de gestion des interventions.

    Implémente les règles métier strictes:
    - Numérotation anti-conflit
    - Workflow statuts strict
    - Temps automatique
    - Rapports automatiques
    """

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # ========================================================================
    # NUMÉROTATION TRANSACTIONNELLE
    # ========================================================================

    def _generate_reference(self) -> str:
        """
        Génère une référence INT-YYYY-XXXX via le système centralisé.
        """
        from app.core.sequences import SequenceGenerator
        seq = SequenceGenerator(self.db, self.tenant_id)
        return seq.next_reference("INTERVENTION")

    def _generate_rapport_final_reference(self) -> str:
        """Génère une référence pour le rapport final via le système centralisé."""
        from app.core.sequences import SequenceGenerator
        seq = SequenceGenerator(self.db, self.tenant_id)
        return seq.next_reference("RAPPORT_INTERVENTION")

    # ========================================================================
    # DONNEURS D'ORDRE
    # ========================================================================

    def list_donneurs_ordre(self, active_only: bool = True) -> list[DonneurOrdre]:
        """Liste des donneurs d'ordre."""
        query = self.db.query(DonneurOrdre).filter(
            DonneurOrdre.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(DonneurOrdre.is_active)
        return query.order_by(DonneurOrdre.nom).all()

    def get_donneur_ordre(self, donneur_id: UUID) -> DonneurOrdre | None:
        """Récupère un donneur d'ordre."""
        return self.db.query(DonneurOrdre).filter(
            DonneurOrdre.id == donneur_id,
            DonneurOrdre.tenant_id == self.tenant_id
        ).first()

    def create_donneur_ordre(self, data: DonneurOrdreCreate) -> DonneurOrdre:
        """Crée un donneur d'ordre avec code auto-généré si non fourni."""
        from app.core.sequences import SequenceGenerator

        data_dict = data.model_dump()

        # Auto-génère le code si non fourni ou vide
        if not data_dict.get('code'):
            seq = SequenceGenerator(self.db, self.tenant_id)
            data_dict['code'] = seq.next_reference("DONNEUR_ORDRE")

        donneur = DonneurOrdre(
            tenant_id=self.tenant_id,
            **data_dict
        )
        self.db.add(donneur)
        self.db.commit()
        self.db.refresh(donneur)
        return donneur

    def update_donneur_ordre(
        self,
        donneur_id: UUID,
        data: DonneurOrdreUpdate
    ) -> DonneurOrdre | None:
        """Met à jour un donneur d'ordre."""
        donneur = self.get_donneur_ordre(donneur_id)
        if not donneur:
            return None

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(donneur, key, value)

        self.db.commit()
        self.db.refresh(donneur)
        return donneur

    def delete_donneur_ordre(self, donneur_id: UUID) -> bool:
        """Supprime un donneur d'ordre (soft delete via is_active=False)."""
        donneur = self.get_donneur_ordre(donneur_id)
        if not donneur:
            return False

        donneur.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # INTERVENTIONS - CRUD
    # ========================================================================

    def list_interventions(
        self,
        statut: InterventionStatut | None = None,
        priorite: InterventionPriorite | None = None,
        client_id: UUID | None = None,
        donneur_ordre_id: UUID | None = None,
        projet_id: UUID | None = None,
        intervenant_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Intervention], int]:
        """Liste des interventions avec filtres et pagination."""
        query = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id
        )

        # Soft delete
        if not include_deleted:
            query = query.filter(Intervention.deleted_at.is_(None))

        # Filtres
        if statut:
            query = query.filter(Intervention.statut == statut)
        if priorite:
            query = query.filter(Intervention.priorite == priorite)
        if client_id:
            query = query.filter(Intervention.client_id == client_id)
        if donneur_ordre_id:
            query = query.filter(Intervention.donneur_ordre_id == donneur_ordre_id)
        if projet_id:
            query = query.filter(Intervention.projet_id == projet_id)
        if intervenant_id:
            query = query.filter(Intervention.intervenant_id == intervenant_id)
        if date_from:
            query = query.filter(Intervention.date_prevue_debut >= date_from)
        if date_to:
            query = query.filter(Intervention.date_prevue_fin <= date_to)
        if search:
            query = query.filter(
                or_(
                    Intervention.reference.ilike(f"%{search}%"),
                    Intervention.titre.ilike(f"%{search}%"),
                    Intervention.reference_externe.ilike(f"%{search}%")
                )
            )

        total = query.count()

        interventions = query.order_by(
            Intervention.date_prevue_debut.desc(),
            Intervention.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return interventions, total

    def get_intervention(self, intervention_id: UUID) -> Intervention | None:
        """Récupère une intervention par ID."""
        return self.db.query(Intervention).filter(
            Intervention.id == intervention_id,
            Intervention.tenant_id == self.tenant_id,
            Intervention.deleted_at.is_(None)
        ).first()

    def get_intervention_by_reference(self, reference: str) -> Intervention | None:
        """Récupère une intervention par référence."""
        return self.db.query(Intervention).filter(
            Intervention.reference == reference,
            Intervention.tenant_id == self.tenant_id,
            Intervention.deleted_at.is_(None)
        ).first()

    def create_intervention(
        self,
        data: InterventionCreate,
        created_by: UUID | None = None
    ) -> Intervention:
        """
        Crée une nouvelle intervention.

        La référence INT-YYYY-XXXX est générée automatiquement.
        Le statut initial est A_PLANIFIER.
        """
        # Générer la référence de manière transactionnelle
        reference = self._generate_reference()

        intervention = Intervention(
            tenant_id=self.tenant_id,
            reference=reference,
            statut=InterventionStatut.DRAFT,
            created_by=created_by,
            **data.model_dump()
        )

        self.db.add(intervention)
        self.db.commit()
        self.db.refresh(intervention)

        _audit_log(
            self.db, self.tenant_id,
            action="CREATE",
            entity_type="intervention",
            entity_id=str(intervention.id),
            user_id=self.user_id,
            description=f"Création intervention {reference}",
            new_value={"reference": reference, "statut": "DRAFT"},
        )

        return intervention

    # Transitions de statut autorisées — state machine 7 états
    TRANSITIONS_AUTORISEES = {
        InterventionStatut.DRAFT: {InterventionStatut.A_PLANIFIER, InterventionStatut.ANNULEE},
        InterventionStatut.A_PLANIFIER: {InterventionStatut.PLANIFIEE, InterventionStatut.ANNULEE},
        InterventionStatut.PLANIFIEE: {InterventionStatut.EN_COURS, InterventionStatut.A_PLANIFIER, InterventionStatut.ANNULEE},
        InterventionStatut.EN_COURS: {InterventionStatut.TERMINEE, InterventionStatut.BLOQUEE, InterventionStatut.ANNULEE},
        InterventionStatut.BLOQUEE: {InterventionStatut.EN_COURS, InterventionStatut.ANNULEE},
        InterventionStatut.TERMINEE: set(),
        InterventionStatut.ANNULEE: set(),
    }

    def update_intervention(
        self,
        intervention_id: UUID,
        data: InterventionUpdate
    ) -> Intervention | None:
        """
        Met à jour une intervention.

        ATTENTION: La référence n'est JAMAIS modifiable.
        Le statut peut être changé si la transition est autorisée.
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # RÈGLE MÉTIER : le statut ne peut PAS être modifié via update générique.
        # Utiliser les actions métier dédiées : /valider, /planifier, /demarrer,
        # /terminer, /bloquer, /debloquer, /annuler.
        if "statut" in update_data:
            raise InterventionWorkflowError(
                "Le statut ne peut pas être modifié directement. "
                "Utilisez les actions métier : /valider, /planifier, /demarrer, "
                "/terminer, /bloquer, /debloquer, /annuler"
            )

        # Mise à jour des autres champs
        old_values = {k: getattr(intervention, k, None) for k in update_data}
        for key, value in update_data.items():
            setattr(intervention, key, value)

        intervention.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(intervention)

        _audit_log(
            self.db, self.tenant_id,
            action="UPDATE",
            entity_type="intervention",
            entity_id=str(intervention.id),
            user_id=self.user_id,
            description=f"Mise à jour intervention {intervention.reference}",
            old_value={k: str(v) for k, v in old_values.items() if v is not None},
            new_value={k: str(v) for k, v in update_data.items() if v is not None},
        )

        return intervention

    def delete_intervention(self, intervention_id: UUID) -> bool:
        """
        Supprime une intervention (soft delete).

        Impossible si l'intervention est TERMINEE.
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            return False

        if intervention.statut == InterventionStatut.TERMINEE:
            raise InterventionWorkflowError(
                "Impossible de supprimer une intervention terminée"
            )

        intervention.deleted_at = datetime.utcnow()
        self.db.commit()

        _audit_log(
            self.db, self.tenant_id,
            action="DELETE",
            entity_type="intervention",
            entity_id=str(intervention.id),
            user_id=self.user_id,
            description=f"Suppression (soft) intervention {intervention.reference}",
            old_value={"statut": intervention.statut.value},
        )

        return True

    def annuler_intervention(self, intervention_id: UUID) -> Intervention:
        """
        Annule une intervention.

        Transition: tout sauf TERMINEE/ANNULEE -> ANNULEE
        Traçable et auditable.
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(
                f"Intervention {intervention_id} non trouvée"
            )

        if intervention.statut in (
            InterventionStatut.TERMINEE,
            InterventionStatut.ANNULEE,
        ):
            raise InterventionWorkflowError(
                f"Impossible d'annuler une intervention {intervention.statut.value}"
            )

        old_statut = intervention.statut.value
        intervention.statut = InterventionStatut.ANNULEE
        intervention.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(intervention)

        _audit_log(
            self.db, self.tenant_id,
            action="CANCEL",
            entity_type="intervention",
            entity_id=str(intervention.id),
            user_id=self.user_id,
            description=f"Annulation intervention {intervention.reference}",
            old_value={"statut": old_statut},
            new_value={"statut": "ANNULEE"},
        )

        return intervention

    # ========================================================================
    # VALIDATION (DRAFT -> A_PLANIFIER)
    # ========================================================================

    def valider_intervention(self, intervention_id: UUID) -> Intervention:
        """
        Valide/soumet un brouillon d'intervention.

        Transition: DRAFT -> A_PLANIFIER
        Vérifie que les champs obligatoires sont remplis (client_id, titre).
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(f"Intervention {intervention_id} non trouvée")

        if intervention.statut != InterventionStatut.DRAFT:
            raise InterventionWorkflowError(
                f"Seul un brouillon (DRAFT) peut être validé. "
                f"Statut actuel: {intervention.statut.value}"
            )

        # Validation métier minimale
        if not intervention.client_id:
            raise InterventionWorkflowError("Le client est obligatoire pour valider l'intervention")
        if not intervention.titre:
            raise InterventionWorkflowError("Le titre est obligatoire pour valider l'intervention")

        intervention.statut = InterventionStatut.A_PLANIFIER
        intervention.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(intervention)

        _audit_log(
            self.db, self.tenant_id,
            action="VALIDATE",
            entity_type="intervention",
            entity_id=str(intervention.id),
            user_id=self.user_id,
            description=f"Validation brouillon intervention {intervention.reference}",
            old_value={"statut": "DRAFT"},
            new_value={"statut": "A_PLANIFIER"},
        )

        return intervention

    # ========================================================================
    # BLOCAGE / DÉBLOCAGE
    # ========================================================================

    def bloquer_intervention(self, intervention_id: UUID, motif: str) -> Intervention:
        """
        Bloque une intervention en cours.

        Transition: EN_COURS -> BLOQUEE
        Motif obligatoire (audit-proof).
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(f"Intervention {intervention_id} non trouvée")

        if intervention.statut != InterventionStatut.EN_COURS:
            raise InterventionWorkflowError(
                f"Seule une intervention EN_COURS peut être bloquée. "
                f"Statut actuel: {intervention.statut.value}"
            )

        if not motif or not motif.strip():
            raise InterventionWorkflowError("Le motif de blocage est obligatoire")

        now = datetime.utcnow()
        intervention.statut = InterventionStatut.BLOQUEE
        intervention.motif_blocage = motif.strip()
        intervention.date_blocage = now
        intervention.updated_at = now

        self.db.commit()
        self.db.refresh(intervention)

        _audit_log(
            self.db, self.tenant_id,
            action="UPDATE",
            entity_type="intervention",
            entity_id=str(intervention.id),
            user_id=self.user_id,
            description=f"Blocage intervention {intervention.reference}: {motif[:100]}",
            old_value={"statut": "EN_COURS"},
            new_value={"statut": "BLOQUEE", "motif_blocage": motif[:200]},
        )

        return intervention

    def debloquer_intervention(self, intervention_id: UUID) -> Intervention:
        """
        Débloque une intervention bloquée.

        Transition: BLOQUEE -> EN_COURS
        Le motif_blocage est préservé pour audit trail.
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(f"Intervention {intervention_id} non trouvée")

        if intervention.statut != InterventionStatut.BLOQUEE:
            raise InterventionWorkflowError(
                f"Seule une intervention BLOQUEE peut être débloquée. "
                f"Statut actuel: {intervention.statut.value}"
            )

        now = datetime.utcnow()
        old_motif = intervention.motif_blocage
        intervention.statut = InterventionStatut.EN_COURS
        intervention.date_deblocage = now
        intervention.updated_at = now

        self.db.commit()
        self.db.refresh(intervention)

        _audit_log(
            self.db, self.tenant_id,
            action="UPDATE",
            entity_type="intervention",
            entity_id=str(intervention.id),
            user_id=self.user_id,
            description=f"Déblocage intervention {intervention.reference}",
            old_value={"statut": "BLOQUEE", "motif_blocage": old_motif},
            new_value={"statut": "EN_COURS"},
        )

        return intervention

    # ========================================================================
    # CALCULS MÉTIER (retard, dérive, risque)
    # ========================================================================

    def calculer_indicateurs_business(self, intervention: Intervention) -> dict:
        """
        Calcule les indicateurs métier en temps réel.

        Retourne:
        - en_retard: bool
        - jours_retard: int
        - derive_duree_minutes: int | None
        - derive_duree_pct: float | None
        - indicateur_risque: FAIBLE | MOYEN | ELEVE | CRITIQUE
        - risque_justification: str (audit-proof)
        """
        now = datetime.utcnow()
        statuts_actifs = {
            InterventionStatut.A_PLANIFIER,
            InterventionStatut.PLANIFIEE,
            InterventionStatut.EN_COURS,
            InterventionStatut.BLOQUEE,
        }

        # --- Retard ---
        en_retard = False
        jours_retard = 0
        if intervention.statut in statuts_actifs:
            date_limite = intervention.date_prevue_fin or intervention.date_prevue_debut
            if date_limite and now > date_limite:
                en_retard = True
                jours_retard = (now - date_limite).days

        # --- Dérive durée ---
        derive_duree_minutes = None
        derive_duree_pct = None
        if intervention.duree_reelle_minutes and intervention.duree_prevue_minutes:
            derive_duree_minutes = intervention.duree_reelle_minutes - intervention.duree_prevue_minutes
            if intervention.duree_prevue_minutes > 0:
                derive_duree_pct = round(
                    (derive_duree_minutes / intervention.duree_prevue_minutes) * 100, 1
                )

        # --- Indicateur risque ---
        score = 0
        justifications = []

        if en_retard:
            if jours_retard >= 7:
                score += 40
                justifications.append(f"Retard critique: {jours_retard} jours")
            elif jours_retard >= 3:
                score += 25
                justifications.append(f"Retard significatif: {jours_retard} jours")
            else:
                score += 10
                justifications.append(f"Retard léger: {jours_retard} jours")

        if intervention.statut == InterventionStatut.BLOQUEE:
            score += 30
            justifications.append(
                f"Intervention bloquée: {intervention.motif_blocage or 'motif non renseigné'}"
            )

        if intervention.priorite == InterventionPriorite.URGENT:
            score += 15
            justifications.append("Priorité urgente")
        elif intervention.priorite == InterventionPriorite.HIGH:
            score += 5

        if derive_duree_pct is not None and derive_duree_pct > 50:
            score += 15
            justifications.append(f"Dépassement durée: +{derive_duree_pct}%")
        elif derive_duree_pct is not None and derive_duree_pct > 20:
            score += 5
            justifications.append(f"Dérive durée: +{derive_duree_pct}%")

        if not intervention.intervenant_id and intervention.statut in (
            InterventionStatut.A_PLANIFIER, InterventionStatut.PLANIFIEE
        ):
            score += 10
            justifications.append("Aucun intervenant assigné")

        if score >= 60:
            indicateur = "CRITIQUE"
        elif score >= 35:
            indicateur = "ELEVE"
        elif score >= 15:
            indicateur = "MOYEN"
        else:
            indicateur = "FAIBLE"

        return {
            "en_retard": en_retard,
            "jours_retard": jours_retard,
            "derive_duree_minutes": derive_duree_minutes,
            "derive_duree_pct": derive_duree_pct,
            "indicateur_risque": indicateur,
            "risque_justification": " | ".join(justifications) if justifications else "Aucun risque identifié",
        }

    # ========================================================================
    # ANALYSE IA (audit-proof)
    # ========================================================================

    def analyser_ia(self, intervention_id: UUID) -> dict:
        """
        Analyse IA d'une intervention.

        Retourne une analyse structurée audit-proof:
        - indicateurs: dict
        - resume_ia: str
        - actions_suggerees: list[dict]
        - score_preparation: int (0-100)
        - generated_at: str (ISO datetime pour audit)
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(f"Intervention {intervention_id} non trouvée")

        indicateurs = self.calculer_indicateurs_business(intervention)

        # Score de préparation (0-100)
        score = 100
        deductions = []
        if not intervention.intervenant_id:
            score -= 20
            deductions.append("Pas d'intervenant (-20)")
        if not intervention.date_prevue_debut:
            score -= 20
            deductions.append("Pas de date prévue (-20)")
        if not (intervention.adresse_ligne1 or intervention.ville):
            score -= 15
            deductions.append("Adresse manquante (-15)")
        if not intervention.description:
            score -= 10
            deductions.append("Description manquante (-10)")
        if not intervention.materiel_necessaire and intervention.type_intervention and \
           intervention.type_intervention.value in ('REPARATION', 'INSTALLATION', 'MAINTENANCE'):
            score -= 10
            deductions.append("Matériel non défini (-10)")
        if indicateurs["en_retard"]:
            score -= 15
            deductions.append(f"En retard de {indicateurs['jours_retard']}j (-15)")
        score = max(score, 0)

        # Actions suggérées
        actions = []
        statut = intervention.statut
        if statut == InterventionStatut.DRAFT:
            actions.append({"action": "valider", "label": "Valider le brouillon", "confiance": 90})
        if statut == InterventionStatut.A_PLANIFIER:
            actions.append({"action": "planifier", "label": "Planifier l'intervention", "confiance": 90})
        if statut == InterventionStatut.PLANIFIEE:
            actions.append({"action": "demarrer", "label": "Démarrer l'intervention", "confiance": 85})
        if statut == InterventionStatut.EN_COURS:
            actions.append({"action": "terminer", "label": "Terminer l'intervention", "confiance": 90})
        if statut == InterventionStatut.BLOQUEE:
            actions.append({"action": "debloquer", "label": "Débloquer et reprendre", "confiance": 80})
        if statut == InterventionStatut.TERMINEE:
            rapport = self.get_rapport_intervention(intervention_id)
            if rapport and not rapport.is_signed:
                actions.append({"action": "signer_rapport", "label": "Faire signer le rapport", "confiance": 85})
        if indicateurs["en_retard"]:
            actions.append({"action": "replanifier", "label": "Replanifier (retard)", "confiance": 85})

        # Résumé IA
        resume_parts = [f"Intervention {intervention.reference}"]
        resume_parts.append(f"Statut: {intervention.statut.value}")
        if indicateurs["en_retard"]:
            resume_parts.append(f"EN RETARD ({indicateurs['jours_retard']}j)")
        if indicateurs["indicateur_risque"] in ("ELEVE", "CRITIQUE"):
            resume_parts.append(f"Risque {indicateurs['indicateur_risque']}")
        resume_parts.append(f"Score préparation: {score}/100")

        return {
            "indicateurs": indicateurs,
            "resume_ia": " | ".join(resume_parts),
            "actions_suggerees": actions,
            "score_preparation": score,
            "score_deductions": deductions,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ========================================================================
    # PLANIFICATION
    # ========================================================================

    def planifier_intervention(
        self,
        intervention_id: UUID,
        data: InterventionPlanifier
    ) -> Intervention:
        """
        Planifie une intervention.

        Transition: A_PLANIFIER -> PLANIFIEE
        Crée un événement dans le module Planning.
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(f"Intervention {intervention_id} non trouvée")

        if intervention.statut != InterventionStatut.A_PLANIFIER:
            raise InterventionWorkflowError(
                f"L'intervention doit être A_PLANIFIER pour être planifiée. "
                f"Statut actuel: {intervention.statut.value}"
            )

        # Mise à jour des dates et intervenant
        intervention.date_prevue_debut = data.date_prevue_debut
        intervention.date_prevue_fin = data.date_prevue_fin
        intervention.intervenant_id = data.intervenant_id
        intervention.statut = InterventionStatut.PLANIFIEE
        intervention.updated_at = datetime.utcnow()

        # Créer l'événement Planning
        planning_event_id = self._create_planning_event(intervention)
        if planning_event_id:
            intervention.planning_event_id = planning_event_id

        self.db.commit()
        self.db.refresh(intervention)

        _audit_log(
            self.db, self.tenant_id,
            action="UPDATE",
            entity_type="intervention",
            entity_id=str(intervention.id),
            user_id=self.user_id,
            description=f"Planification intervention {intervention.reference}",
            old_value={"statut": "A_PLANIFIER"},
            new_value={
                "statut": "PLANIFIEE",
                "date_prevue_debut": str(data.date_prevue_debut),
                "intervenant_id": str(data.intervenant_id),
            },
        )

        return intervention

    def modifier_planification(
        self,
        intervention_id: UUID,
        data: InterventionPlanifier
    ) -> Intervention:
        """
        Modifie la planification d'une intervention.

        Possible uniquement si statut PLANIFIEE.
        Met à jour l'événement Planning.
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(f"Intervention {intervention_id} non trouvée")

        if intervention.statut != InterventionStatut.PLANIFIEE:
            raise InterventionWorkflowError(
                f"La modification de planification n'est possible que pour "
                f"les interventions PLANIFIEES. Statut actuel: {intervention.statut.value}"
            )

        # Mise à jour
        intervention.date_prevue_debut = data.date_prevue_debut
        intervention.date_prevue_fin = data.date_prevue_fin
        intervention.intervenant_id = data.intervenant_id
        intervention.updated_at = datetime.utcnow()

        # Mettre à jour l'événement Planning
        self._update_planning_event(intervention)

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def annuler_planification(self, intervention_id: UUID) -> Intervention:
        """
        Annule la planification d'une intervention.

        Transition: PLANIFIEE -> A_PLANIFIER
        Supprime l'événement Planning.
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(f"Intervention {intervention_id} non trouvée")

        if intervention.statut != InterventionStatut.PLANIFIEE:
            raise InterventionWorkflowError(
                f"L'annulation n'est possible que pour les interventions PLANIFIEES. "
                f"Statut actuel: {intervention.statut.value}"
            )

        # Supprimer l'événement Planning
        self._delete_planning_event(intervention)

        # Réinitialiser
        intervention.date_prevue_debut = None
        intervention.date_prevue_fin = None
        intervention.intervenant_id = None
        intervention.planning_event_id = None
        intervention.statut = InterventionStatut.A_PLANIFIER
        intervention.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    # ========================================================================
    # ACTIONS TERRAIN
    # ========================================================================

    def arrivee_sur_site(
        self,
        intervention_id: UUID,
        data: ArriveeRequest
    ) -> Intervention:
        """
        Action terrain: arrivee_sur_site()

        Horodatage automatique de l'arrivée sur site.
        Enregistre la géolocalisation si fournie.
        Transition: PLANIFIEE -> EN_COURS
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(f"Intervention {intervention_id} non trouvée")

        if intervention.statut != InterventionStatut.PLANIFIEE:
            raise InterventionWorkflowError(
                f"L'arrivée sur site n'est possible que pour les interventions PLANIFIEES. "
                f"Statut actuel: {intervention.statut.value}"
            )

        now = datetime.utcnow()
        intervention.date_arrivee_site = now
        intervention.statut = InterventionStatut.EN_COURS
        intervention.updated_at = now

        # Géolocalisation
        if data.latitude is not None:
            intervention.geoloc_arrivee_lat = data.latitude
        if data.longitude is not None:
            intervention.geoloc_arrivee_lng = data.longitude

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def demarrer_intervention(self, intervention_id: UUID) -> Intervention:
        """
        Action terrain: demarrer_intervention()

        Horodatage automatique du démarrage effectif.
        Requiert: statut EN_COURS (arrivée déjà enregistrée)
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(f"Intervention {intervention_id} non trouvée")

        if intervention.statut != InterventionStatut.EN_COURS:
            raise InterventionWorkflowError(
                f"Le démarrage n'est possible que pour les interventions EN_COURS. "
                f"Statut actuel: {intervention.statut.value}"
            )

        if not intervention.date_arrivee_site:
            raise InterventionWorkflowError(
                "L'arrivée sur site doit être enregistrée avant le démarrage"
            )

        if intervention.date_demarrage:
            raise InterventionWorkflowError(
                "L'intervention a déjà été démarrée"
            )

        now = datetime.utcnow()
        intervention.date_demarrage = now
        intervention.updated_at = now

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def terminer_intervention(
        self,
        intervention_id: UUID,
        data: FinInterventionRequest
    ) -> Intervention:
        """
        Action terrain: terminer_intervention()

        Horodatage automatique de la fin.
        Calcule automatiquement la durée_reelle_minutes.
        Transition: EN_COURS -> TERMINEE
        Déclenche la génération du rapport d'intervention.
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            raise InterventionNotFoundError(f"Intervention {intervention_id} non trouvée")

        if intervention.statut != InterventionStatut.EN_COURS:
            raise InterventionWorkflowError(
                f"La terminaison n'est possible que pour les interventions EN_COURS. "
                f"Statut actuel: {intervention.statut.value}"
            )

        if not intervention.date_demarrage:
            raise InterventionWorkflowError(
                "L'intervention doit être démarrée avant d'être terminée"
            )

        now = datetime.utcnow()
        intervention.date_fin = now
        intervention.statut = InterventionStatut.TERMINEE
        intervention.updated_at = now

        # Calcul automatique de la durée réelle en minutes
        duration = (intervention.date_fin - intervention.date_demarrage).total_seconds()
        intervention.duree_reelle_minutes = int(duration / 60)

        self.db.flush()

        # Générer automatiquement le rapport d'intervention
        self._generer_rapport_intervention(intervention, data)

        self.db.commit()
        self.db.refresh(intervention)

        _audit_log(
            self.db, self.tenant_id,
            action="UPDATE",
            entity_type="intervention",
            entity_id=str(intervention.id),
            user_id=self.user_id,
            description=f"Terminaison intervention {intervention.reference} — durée réelle: {intervention.duree_reelle_minutes}min",
            old_value={"statut": "EN_COURS"},
            new_value={
                "statut": "TERMINEE",
                "duree_reelle_minutes": intervention.duree_reelle_minutes,
            },
        )

        return intervention

    # ========================================================================
    # RAPPORTS D'INTERVENTION
    # ========================================================================

    def _generer_rapport_intervention(
        self,
        intervention: Intervention,
        data: FinInterventionRequest
    ) -> RapportIntervention:
        """
        Génère automatiquement le rapport d'intervention à la fin.
        """
        rapport = RapportIntervention(
            tenant_id=self.tenant_id,
            intervention_id=intervention.id,
            reference_intervention=intervention.reference,
            client_id=intervention.client_id,
            donneur_ordre_id=intervention.donneur_ordre_id,
            resume_actions=data.resume_actions,
            anomalies=data.anomalies,
            recommandations=data.recommandations,
            photos=[],
            is_signed=False,
            is_locked=False,
        )
        self.db.add(rapport)
        self.db.flush()
        return rapport

    def get_rapport_intervention(
        self,
        intervention_id: UUID
    ) -> RapportIntervention | None:
        """Récupère le rapport d'une intervention."""
        return self.db.query(RapportIntervention).filter(
            RapportIntervention.intervention_id == intervention_id,
            RapportIntervention.tenant_id == self.tenant_id
        ).first()

    def update_rapport_intervention(
        self,
        intervention_id: UUID,
        data: RapportInterventionUpdate
    ) -> RapportIntervention:
        """
        Met à jour le rapport d'intervention.

        IMPOSSIBLE si le rapport est signé ou verrouillé.
        """
        rapport = self.get_rapport_intervention(intervention_id)
        if not rapport:
            raise InterventionNotFoundError(
                f"Rapport pour l'intervention {intervention_id} non trouvé"
            )

        if rapport.is_locked or rapport.is_signed:
            raise RapportLockedError(
                "Le rapport est verrouillé et ne peut plus être modifié"
            )

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(rapport, key, value)

        rapport.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rapport)

        return rapport

    def ajouter_photo_rapport(
        self,
        intervention_id: UUID,
        photo: PhotoRequest
    ) -> RapportIntervention:
        """Ajoute une photo au rapport."""
        rapport = self.get_rapport_intervention(intervention_id)
        if not rapport:
            raise InterventionNotFoundError(
                f"Rapport pour l'intervention {intervention_id} non trouvé"
            )

        if rapport.is_locked or rapport.is_signed:
            raise RapportLockedError(
                "Le rapport est verrouillé et ne peut plus être modifié"
            )

        photos = list(rapport.photos or [])
        photos.append({
            "url": photo.url,
            "caption": photo.caption,
            "taken_at": datetime.utcnow().isoformat()
        })
        rapport.photos = photos
        rapport.updated_at = datetime.utcnow()

        # Signaler à SQLAlchemy que le JSON a été modifié
        flag_modified(rapport, 'photos')

        self.db.commit()
        self.db.refresh(rapport)

        return rapport

    def signer_rapport(
        self,
        intervention_id: UUID,
        data: SignatureRapportRequest
    ) -> RapportIntervention:
        """
        Signe le rapport d'intervention.

        Une fois signé, le rapport est figé et non modifiable.
        """
        rapport = self.get_rapport_intervention(intervention_id)
        if not rapport:
            raise InterventionNotFoundError(
                f"Rapport pour l'intervention {intervention_id} non trouvé"
            )

        if rapport.is_signed:
            raise RapportLockedError("Le rapport est déjà signé")

        now = datetime.utcnow()
        rapport.signature_client = data.signature_client
        rapport.nom_signataire = data.nom_signataire
        rapport.date_signature = now

        if data.latitude is not None:
            rapport.geoloc_signature_lat = data.latitude
        if data.longitude is not None:
            rapport.geoloc_signature_lng = data.longitude

        rapport.is_signed = True
        rapport.is_locked = True
        rapport.updated_at = now

        self.db.commit()
        self.db.refresh(rapport)

        _audit_log(
            self.db, self.tenant_id,
            action="VALIDATE",
            entity_type="rapport_intervention",
            entity_id=str(rapport.id),
            user_id=self.user_id,
            description=f"Signature rapport intervention {rapport.reference_intervention} par {data.nom_signataire}",
            new_value={"is_signed": True, "nom_signataire": data.nom_signataire},
        )

        return rapport

    # ========================================================================
    # RAPPORT FINAL CONSOLIDÉ
    # ========================================================================

    def generer_rapport_final(
        self,
        data: RapportFinalGenerateRequest,
        created_by: UUID | None = None
    ) -> RapportFinal:
        """
        Génère un rapport final consolidé.

        Regroupe les interventions par:
        - projet_id
        - OU donneur_ordre_id

        Le rapport final est non modifiable et horodaté.
        """
        # Construire la requête pour trouver les interventions
        query = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.statut == InterventionStatut.TERMINEE,
            Intervention.deleted_at.is_(None)
        )

        if data.projet_id:
            query = query.filter(Intervention.projet_id == data.projet_id)
        elif data.donneur_ordre_id:
            query = query.filter(Intervention.donneur_ordre_id == data.donneur_ordre_id)

        interventions = query.all()

        if not interventions:
            raise InterventionNotFoundError(
                "Aucune intervention terminée trouvée pour ce critère"
            )

        # Calculer le temps total
        temps_total = sum(
            i.duree_reelle_minutes or 0
            for i in interventions
        )

        # Collecter les références
        references = [i.reference for i in interventions]

        # Générer la référence du rapport final
        reference = self._generate_rapport_final_reference()

        rapport_final = RapportFinal(
            tenant_id=self.tenant_id,
            reference=reference,
            projet_id=data.projet_id,
            donneur_ordre_id=data.donneur_ordre_id,
            interventions_references=references,
            temps_total_minutes=temps_total,
            synthese=data.synthese,
            date_generation=datetime.utcnow(),
            is_locked=True,  # Toujours verrouillé à la création
            created_by=created_by,
        )

        self.db.add(rapport_final)
        self.db.commit()
        self.db.refresh(rapport_final)

        return rapport_final

    def get_rapport_final(self, rapport_id: UUID) -> RapportFinal | None:
        """Récupère un rapport final."""
        return self.db.query(RapportFinal).filter(
            RapportFinal.id == rapport_id,
            RapportFinal.tenant_id == self.tenant_id
        ).first()

    def list_rapports_final(
        self,
        projet_id: UUID | None = None,
        donneur_ordre_id: UUID | None = None
    ) -> list[RapportFinal]:
        """Liste les rapports finaux."""
        query = self.db.query(RapportFinal).filter(
            RapportFinal.tenant_id == self.tenant_id
        )

        if projet_id:
            query = query.filter(RapportFinal.projet_id == projet_id)
        if donneur_ordre_id:
            query = query.filter(RapportFinal.donneur_ordre_id == donneur_ordre_id)

        return query.order_by(RapportFinal.date_generation.desc()).all()

    # ========================================================================
    # INTÉGRATION PLANNING (Consommation)
    # ========================================================================

    def _create_planning_event(self, intervention: Intervention) -> UUID | None:
        """
        Crée un événement dans le module Planning.

        NOTE: Le module Planning doit exister et exposer un service.
        Cette méthode est un placeholder pour l'intégration.
        """
        try:
            # Placeholder pour l'intégration avec le module Planning
            # La logique métier INTERVENTIONS ne doit PAS être dans Planning
            event_id = uuid.uuid4()
            return event_id
        except Exception as e:
            # En cas d'erreur, on continue sans bloquer
            logger.warning(
                "[INTERVENTIONS_PLANNING] Échec création événement planning",
                extra={"error": str(e)[:300], "consequence": "planning_event_skipped"}
            )
            return None

    def _update_planning_event(self, intervention: Intervention) -> bool:
        """Met à jour un événement Planning."""
        if not intervention.planning_event_id:
            return False

        try:
            # Placeholder pour l'intégration
            return True
        except Exception as e:
            logger.warning(
                "[INTERVENTIONS_PLANNING] Échec mise à jour événement planning",
                extra={"error": str(e)[:300], "consequence": "planning_update_skipped"}
            )
            return False

    def _delete_planning_event(self, intervention: Intervention) -> bool:
        """Supprime un événement Planning."""
        if not intervention.planning_event_id:
            return False

        try:
            # Placeholder pour l'intégration
            return True
        except Exception as e:
            logger.warning(
                "[INTERVENTIONS_PLANNING] Échec suppression événement planning",
                extra={"error": str(e)[:300], "consequence": "planning_delete_skipped"}
            )
            return False

    # ========================================================================
    # STATISTIQUES
    # ========================================================================

    def get_stats(self) -> dict:
        """
        Calcule les statistiques des interventions.

        Retourne un dict enrichi compatible avec le frontend v2 :
        - a_planifier, planifiees, en_cours
        - terminees_semaine, terminees_mois
        - duree_moyenne_minutes, interventions_jour
        """
        from datetime import timedelta

        now = datetime.utcnow()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        base_query = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.deleted_at.is_(None)
        )

        # Par statut
        brouillons = base_query.filter(
            Intervention.statut == InterventionStatut.DRAFT
        ).count()
        a_planifier = base_query.filter(
            Intervention.statut == InterventionStatut.A_PLANIFIER
        ).count()
        planifiees = base_query.filter(
            Intervention.statut == InterventionStatut.PLANIFIEE
        ).count()
        en_cours = base_query.filter(
            Intervention.statut == InterventionStatut.EN_COURS
        ).count()
        bloquees = base_query.filter(
            Intervention.statut == InterventionStatut.BLOQUEE
        ).count()

        # Terminées cette semaine
        terminees_semaine = base_query.filter(
            Intervention.statut == InterventionStatut.TERMINEE,
            Intervention.date_fin >= start_of_week
        ).count()

        # Terminées ce mois
        terminees_mois = base_query.filter(
            Intervention.statut == InterventionStatut.TERMINEE,
            Intervention.date_fin >= start_of_month
        ).count()

        # Interventions du jour (planifiées ou en cours aujourd'hui)
        interventions_jour = base_query.filter(
            or_(
                Intervention.date_prevue_debut >= start_of_day,
                Intervention.statut == InterventionStatut.EN_COURS
            )
        ).count()

        # Durée moyenne
        avg_duration = self.db.query(
            func.avg(Intervention.duree_reelle_minutes)
        ).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.statut == InterventionStatut.TERMINEE,
            Intervention.duree_reelle_minutes.isnot(None)
        ).scalar() or 0

        return {
            "brouillons": brouillons,
            "a_planifier": a_planifier,
            "planifiees": planifiees,
            "en_cours": en_cours,
            "bloquees": bloquees,
            "terminees_semaine": terminees_semaine,
            "terminees_mois": terminees_mois,
            "duree_moyenne_minutes": float(avg_duration),
            "interventions_jour": interventions_jour,
        }
