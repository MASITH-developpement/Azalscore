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

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import func, or_, and_
from sqlalchemy.exc import IntegrityError

from .models import (
    Intervention,
    InterventionStatut,
    InterventionPriorite,
    TypeIntervention,
    RapportIntervention,
    RapportFinal,
    DonneurOrdre,
    InterventionSequence,
)
from .schemas import (
    InterventionCreate,
    InterventionUpdate,
    InterventionPlanifier,
    ArriveeRequest,
    FinInterventionRequest,
    DonneurOrdreCreate,
    DonneurOrdreUpdate,
    RapportInterventionUpdate,
    SignatureRapportRequest,
    PhotoRequest,
    RapportFinalGenerateRequest,
    InterventionStats,
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

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # NUMÉROTATION TRANSACTIONNELLE
    # ========================================================================

    def _generate_reference(self) -> str:
        """
        Génère une référence INT-YYYY-XXXX de manière transactionnelle.

        Utilise SELECT FOR UPDATE pour éviter les conflits concurrents.
        La numérotation est incrémentée par tenant et par année.
        """
        current_year = datetime.utcnow().year

        # Récupérer ou créer la séquence avec verrouillage
        sequence = self.db.query(InterventionSequence).filter(
            InterventionSequence.tenant_id == self.tenant_id,
            InterventionSequence.year == current_year
        ).with_for_update().first()

        if not sequence:
            # Créer nouvelle séquence pour cette année
            sequence = InterventionSequence(
                tenant_id=self.tenant_id,
                year=current_year,
                last_number=0
            )
            self.db.add(sequence)
            self.db.flush()

        # Incrémenter le numéro
        sequence.last_number += 1
        new_number = sequence.last_number

        # Générer la référence
        reference = f"INT-{current_year}-{new_number:04d}"

        return reference

    def _generate_rapport_final_reference(self) -> str:
        """Génère une référence pour le rapport final."""
        current_year = datetime.utcnow().year

        # Compter les rapports finaux existants pour cette année
        count = self.db.query(RapportFinal).filter(
            RapportFinal.tenant_id == self.tenant_id,
            RapportFinal.reference.like(f"RFINAL-{current_year}-%")
        ).count()

        return f"RFINAL-{current_year}-{count + 1:04d}"

    # ========================================================================
    # DONNEURS D'ORDRE
    # ========================================================================

    def list_donneurs_ordre(self, active_only: bool = True) -> List[DonneurOrdre]:
        """Liste des donneurs d'ordre."""
        query = self.db.query(DonneurOrdre).filter(
            DonneurOrdre.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(DonneurOrdre.is_active == True)
        return query.order_by(DonneurOrdre.nom).all()

    def get_donneur_ordre(self, donneur_id: UUID) -> Optional[DonneurOrdre]:
        """Récupère un donneur d'ordre."""
        return self.db.query(DonneurOrdre).filter(
            DonneurOrdre.id == donneur_id,
            DonneurOrdre.tenant_id == self.tenant_id
        ).first()

    def create_donneur_ordre(self, data: DonneurOrdreCreate) -> DonneurOrdre:
        """Crée un donneur d'ordre."""
        donneur = DonneurOrdre(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(donneur)
        self.db.commit()
        self.db.refresh(donneur)
        return donneur

    def update_donneur_ordre(
        self,
        donneur_id: UUID,
        data: DonneurOrdreUpdate
    ) -> Optional[DonneurOrdre]:
        """Met à jour un donneur d'ordre."""
        donneur = self.get_donneur_ordre(donneur_id)
        if not donneur:
            return None

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(donneur, key, value)

        self.db.commit()
        self.db.refresh(donneur)
        return donneur

    # ========================================================================
    # INTERVENTIONS - CRUD
    # ========================================================================

    def list_interventions(
        self,
        statut: Optional[InterventionStatut] = None,
        priorite: Optional[InterventionPriorite] = None,
        client_id: Optional[UUID] = None,
        donneur_ordre_id: Optional[UUID] = None,
        projet_id: Optional[UUID] = None,
        intervenant_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Intervention], int]:
        """Liste des interventions avec filtres et pagination."""
        query = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id
        )

        # Soft delete
        if not include_deleted:
            query = query.filter(Intervention.deleted_at == None)

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

    def get_intervention(self, intervention_id: UUID) -> Optional[Intervention]:
        """Récupère une intervention par ID."""
        return self.db.query(Intervention).filter(
            Intervention.id == intervention_id,
            Intervention.tenant_id == self.tenant_id,
            Intervention.deleted_at == None
        ).first()

    def get_intervention_by_reference(self, reference: str) -> Optional[Intervention]:
        """Récupère une intervention par référence."""
        return self.db.query(Intervention).filter(
            Intervention.reference == reference,
            Intervention.tenant_id == self.tenant_id,
            Intervention.deleted_at == None
        ).first()

    def create_intervention(
        self,
        data: InterventionCreate,
        created_by: Optional[UUID] = None
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
            statut=InterventionStatut.A_PLANIFIER,
            created_by=created_by,
            **data.model_dump()
        )

        self.db.add(intervention)
        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def update_intervention(
        self,
        intervention_id: UUID,
        data: InterventionUpdate
    ) -> Optional[Intervention]:
        """
        Met à jour une intervention.

        ATTENTION: La référence n'est JAMAIS modifiable.
        Le statut ne peut être changé que via les actions terrain.
        """
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            return None

        # Mise à jour des champs autorisés uniquement
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(intervention, key, value)

        intervention.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(intervention)

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
        return True

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
    ) -> Optional[RapportIntervention]:
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

        return rapport

    # ========================================================================
    # RAPPORT FINAL CONSOLIDÉ
    # ========================================================================

    def generer_rapport_final(
        self,
        data: RapportFinalGenerateRequest,
        created_by: Optional[UUID] = None
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
            Intervention.deleted_at == None
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

    def get_rapport_final(self, rapport_id: UUID) -> Optional[RapportFinal]:
        """Récupère un rapport final."""
        return self.db.query(RapportFinal).filter(
            RapportFinal.id == rapport_id,
            RapportFinal.tenant_id == self.tenant_id
        ).first()

    def list_rapports_final(
        self,
        projet_id: Optional[UUID] = None,
        donneur_ordre_id: Optional[UUID] = None
    ) -> List[RapportFinal]:
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

    def _create_planning_event(self, intervention: Intervention) -> Optional[UUID]:
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
        except Exception:
            # En cas d'erreur, on continue sans bloquer
            return None

    def _update_planning_event(self, intervention: Intervention) -> bool:
        """Met à jour un événement Planning."""
        if not intervention.planning_event_id:
            return False

        try:
            # Placeholder pour l'intégration
            return True
        except Exception:
            return False

    def _delete_planning_event(self, intervention: Intervention) -> bool:
        """Supprime un événement Planning."""
        if not intervention.planning_event_id:
            return False

        try:
            # Placeholder pour l'intégration
            return True
        except Exception:
            return False

    # ========================================================================
    # STATISTIQUES
    # ========================================================================

    def get_stats(self) -> InterventionStats:
        """Calcule les statistiques des interventions."""
        base_query = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.deleted_at == None
        )

        total = base_query.count()

        # Par statut
        a_planifier = base_query.filter(
            Intervention.statut == InterventionStatut.A_PLANIFIER
        ).count()
        planifiees = base_query.filter(
            Intervention.statut == InterventionStatut.PLANIFIEE
        ).count()
        en_cours = base_query.filter(
            Intervention.statut == InterventionStatut.EN_COURS
        ).count()
        terminees = base_query.filter(
            Intervention.statut == InterventionStatut.TERMINEE
        ).count()

        # Durée moyenne
        avg_duration = self.db.query(
            func.avg(Intervention.duree_reelle_minutes)
        ).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.statut == InterventionStatut.TERMINEE,
            Intervention.duree_reelle_minutes != None
        ).scalar() or 0

        return InterventionStats(
            total=total,
            a_planifier=a_planifier,
            planifiees=planifiees,
            en_cours=en_cours,
            terminees=terminees,
            duree_moyenne_minutes=float(avg_duration)
        )
