"""
AZALS MODULE - Odoo Import Interventions Service
==================================================

Service d'import des interventions depuis Odoo.
Supporte intervention.intervention, project.task et helpdesk.ticket.
"""
from __future__ import annotations


import logging
import uuid as uuid_module
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.modules.odoo_import.models import OdooImportHistory, OdooSyncType

from .base import BaseOdooService

logger = logging.getLogger(__name__)


class InterventionImportService(BaseOdooService[OdooImportHistory]):
    """Service d'import des interventions Odoo."""

    model = OdooImportHistory

    def import_interventions(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les interventions depuis Odoo.

        Essaie dans l'ordre:
        1. intervention.intervention (module custom MASITH)
        2. project.task (module projet standard)
        3. helpdesk.ticket (module helpdesk)

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore le delta

        Returns:
            Historique de l'import
        """
        config = self._require_config(config_id)

        history = self._create_history(
            config_id=config_id,
            sync_type=OdooSyncType.INTERVENTIONS,
            is_delta=not full_sync,
        )

        try:
            connector = self._get_connector(config)

            tasks = []
            source_model = None

            # Essayer intervention.intervention (module custom)
            tasks, source_model = self._try_fetch_interventions(connector)

            # Fallback: project.task
            if not tasks:
                tasks, source_model = self._try_fetch_project_tasks(connector)

            # Fallback: helpdesk.ticket
            if not tasks:
                tasks, source_model = self._try_fetch_helpdesk_tickets(connector)

            history.total_records = len(tasks)
            logger.info(
                "Récupéré %d interventions depuis %s",
                len(tasks),
                source_model or "aucun module",
            )

            # Importer les interventions
            created, updated, errors = self._import_batch(tasks, source_model)

            config.total_imports += 1

            history = self._finalize_history(history, created, updated, errors)

            logger.info(
                "Import interventions terminé | created=%d updated=%d errors=%d",
                created,
                updated,
                len(errors),
            )
            return history

        except Exception as e:
            self._fail_history(history, e)
            self.db.commit()
            raise

    def _try_fetch_interventions(
        self,
        connector: Any,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Essaie de récupérer depuis intervention.intervention (MASITH).

        Returns:
            Tuple (tasks, source_model)
        """
        try:
            fields = [
                "id",
                "display_name",
                "description",
                "date_prevue",
                "date_debut",
                "date_fin",
                "heure_arrivee",
                "duree_prevue",
                "duree_reelle",
                "client_final_id",
                "donneur_ordre_id",
                "technicien_principal_id",
                "adresse_intervention",
                "adresse_entreprise",
                "latitude",
                "longitude",
                "facturer_a",
                "distance_km",
                "duree_trajet_min",
                "date_signature",
                "create_date",
                "company_id",
            ]
            tasks = connector.search_read("intervention.intervention", [], fields)
            if tasks:
                logger.info(
                    "Trouvé %d intervention.intervention",
                    len(tasks),
                )
                return tasks, "intervention.intervention"
        except Exception as e:
            logger.debug(
                "Module intervention.intervention non disponible: %s",
                str(e),
            )
        return [], None

    def _try_fetch_project_tasks(
        self,
        connector: Any,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Essaie de récupérer depuis project.task.

        Returns:
            Tuple (tasks, source_model)
        """
        try:
            fields = [
                "id",
                "name",
                "project_id",
                "partner_id",
                "user_ids",
                "date_deadline",
                "stage_id",
                "description",
                "create_date",
                "priority",
                "kanban_state",
                "date_assign",
                "date_end",
                "sequence",
                "display_name",
            ]
            tasks = connector.search_read("project.task", [], fields)
            if tasks:
                logger.info("Trouvé %d project.task", len(tasks))
                return tasks, "project.task"
        except Exception as e:
            logger.debug("Module project non disponible: %s", str(e))
        return [], None

    def _try_fetch_helpdesk_tickets(
        self,
        connector: Any,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Essaie de récupérer depuis helpdesk.ticket.

        Returns:
            Tuple (tasks, source_model)
        """
        try:
            fields = [
                "id",
                "name",
                "partner_id",
                "user_id",
                "stage_id",
                "description",
                "ticket_type_id",
                "create_date",
                "priority",
            ]
            tasks = connector.search_read("helpdesk.ticket", [], fields)
            if tasks:
                logger.info("Trouvé %d helpdesk.ticket", len(tasks))
                return tasks, "helpdesk.ticket"
        except Exception as e:
            logger.debug("Module helpdesk non disponible: %s", str(e))
        return [], None

    def _import_batch(
        self,
        tasks: List[Dict[str, Any]],
        source_model: Optional[str],
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Importe un lot d'interventions.

        Args:
            tasks: Liste des tâches/interventions Odoo
            source_model: Modèle source

        Returns:
            Tuple (created_count, updated_count, errors)
        """
        from app.modules.interventions.models import (
            Intervention,
            InterventionPriorite,
            InterventionStatut,
            TypeIntervention,
        )

        created = 0
        updated = 0
        errors = []

        default_client_id = self._get_or_create_default_client()

        for task in tasks:
            odoo_id = task.get("id")
            display_name = task.get("display_name", "")
            description = task.get("description", "")

            if not display_name:
                errors.append({
                    "odoo_id": odoo_id,
                    "error": "Référence intervention manquante",
                })
                continue

            try:
                savepoint = self.db.begin_nested()

                # Rechercher par référence externe
                ref_externe = f"ODOO-{odoo_id}"
                existing = (
                    self.db.query(Intervention)
                    .filter(
                        Intervention.tenant_id == self.tenant_id,
                        Intervention.reference_externe == ref_externe,
                    )
                    .first()
                )

                # Extraire les informations client
                client_id, client_name = self._extract_client_info(
                    task,
                    default_client_id,
                )

                # Extraire les dates
                date_prevue = self._parse_date(
                    task.get("date_prevue"),
                    include_time=True,
                )
                date_debut = self._parse_date(
                    task.get("date_debut"),
                    include_time=True,
                )
                date_fin = self._parse_date(
                    task.get("date_fin"),
                    include_time=True,
                )

                # Déterminer le statut
                statut = self._determine_status(
                    date_prevue,
                    date_debut,
                    date_fin,
                    InterventionStatut,
                )

                # Calculer les durées
                duree_minutes = self._parse_duration(task.get("duree_prevue"))
                duree_reelle_minutes = self._parse_duration(task.get("duree_reelle"))

                # Adresse
                adresse = (
                    task.get("adresse_intervention")
                    or task.get("adresse_entreprise")
                    or ""
                )

                # Référence Odoo
                odoo_reference = self._get_reference(task)

                # Notes
                notes_internes = self._build_notes(
                    source_model,
                    odoo_id,
                    task.get("donneur_ordre_id"),
                    client_name,
                )

                if existing:
                    self._update_intervention(
                        existing,
                        description,
                        display_name,
                        notes_internes,
                        statut,
                        client_id,
                        date_prevue,
                        date_debut,
                        date_fin,
                        duree_minutes,
                        duree_reelle_minutes,
                        adresse,
                    )
                    savepoint.commit()
                    updated += 1
                else:
                    # Vérifier si la référence existe
                    existing_ref = (
                        self.db.query(Intervention)
                        .filter(
                            Intervention.tenant_id == self.tenant_id,
                            Intervention.reference == odoo_reference,
                        )
                        .first()
                    )

                    if existing_ref:
                        self._update_intervention(
                            existing_ref,
                            description,
                            display_name,
                            notes_internes,
                            statut,
                            client_id,
                            date_prevue,
                            date_debut,
                            date_fin,
                            duree_minutes,
                            duree_reelle_minutes,
                            adresse,
                        )
                        existing_ref.reference_externe = ref_externe
                        savepoint.commit()
                        updated += 1
                    else:
                        intervention = Intervention(
                            id=uuid_module.uuid4(),
                            tenant_id=self.tenant_id,
                            reference=odoo_reference,
                            reference_externe=ref_externe,
                            client_id=client_id,
                            titre=(
                                description[:500]
                                if description
                                else display_name
                            ),
                            description=description or "",
                            notes_internes=notes_internes,
                            statut=statut,
                            priorite=InterventionPriorite.NORMAL,
                            type_intervention=TypeIntervention.MAINTENANCE,
                            date_prevue_debut=date_prevue,
                            date_demarrage=date_debut,
                            date_fin=date_fin,
                            duree_prevue_minutes=duree_minutes,
                            duree_reelle_minutes=duree_reelle_minutes,
                            adresse_ligne1=adresse[:255] if adresse else None,
                            facturable=True,
                        )
                        self.db.add(intervention)
                        savepoint.commit()
                        created += 1

            except Exception as e:
                try:
                    savepoint.rollback()
                except Exception:
                    pass
                errors.append({
                    "odoo_id": odoo_id,
                    "reference": display_name,
                    "error": str(e),
                })
                logger.warning(
                    "Erreur intervention %s (%s): %s",
                    odoo_id,
                    display_name,
                    str(e),
                )

        return created, updated, errors

    def _get_or_create_default_client(self) -> UUID:
        """
        Récupère ou crée un client par défaut pour les imports Odoo.

        Returns:
            ID du client par défaut
        """
        from app.modules.commercial.models import Customer

        existing = (
            self.db.query(Customer)
            .filter(
                Customer.tenant_id == self.tenant_id,
                Customer.code == "ODOO-DEFAULT",
            )
            .first()
        )

        if existing:
            return existing.id

        default_client = Customer(
            id=uuid_module.uuid4(),
            tenant_id=self.tenant_id,
            code="ODOO-DEFAULT",
            name="Client Import Odoo",
            is_active=True,
        )
        self.db.add(default_client)
        self.db.flush()
        return default_client.id

    def _extract_client_info(
        self,
        task: Dict[str, Any],
        default_client_id: UUID,
    ) -> Tuple[UUID, Optional[str]]:
        """
        Extrait les informations client d'une tâche.

        Returns:
            Tuple (client_id, client_name)
        """
        from app.modules.commercial.models import Customer

        client_final = task.get("client_final_id")
        client_id = default_client_id
        client_name = None

        if client_final and isinstance(client_final, (list, tuple)):
            if len(client_final) > 1:
                client_name = client_final[1]
                matched_client = (
                    self.db.query(Customer)
                    .filter(
                        Customer.tenant_id == self.tenant_id,
                        Customer.name.ilike(f"%{client_name}%"),
                    )
                    .first()
                )
                if matched_client:
                    client_id = matched_client.id

        return client_id, client_name

    @staticmethod
    def _determine_status(
        date_prevue: Optional[datetime],
        date_debut: Optional[datetime],
        date_fin: Optional[datetime],
        status_enum: Any,
    ):
        """
        Détermine le statut en fonction des dates.

        Returns:
            Statut d'intervention
        """
        if date_fin:
            return status_enum.TERMINEE
        elif date_debut:
            return status_enum.EN_COURS
        elif date_prevue:
            return status_enum.PLANIFIEE
        else:
            return status_enum.A_PLANIFIER

    @staticmethod
    def _parse_duration(value: Any) -> Optional[int]:
        """
        Convertit une durée en heures vers minutes.

        Args:
            value: Durée en heures

        Returns:
            Durée en minutes ou None
        """
        if not value:
            return None
        try:
            return int(float(value) * 60)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _get_reference(task: Dict[str, Any]) -> str:
        """
        Extrait la meilleure référence d'une tâche Odoo.

        Args:
            task: Données de la tâche

        Returns:
            Référence (max 20 caractères)
        """
        display_name = task.get("display_name", "")
        if display_name and display_name.strip():
            return display_name.strip()[:20]
        return f"ODOO-{task.get('id', 0)}"

    @staticmethod
    def _build_notes(
        source_model: Optional[str],
        odoo_id: int,
        donneur_ordre: Any,
        client_name: Optional[str],
    ) -> str:
        """
        Construit les notes internes pour une intervention.

        Returns:
            Notes internes
        """
        notes = f"Import Odoo {source_model} ID: {odoo_id}"

        if donneur_ordre:
            donneur_name = None
            if isinstance(donneur_ordre, (list, tuple)) and len(donneur_ordre) > 1:
                donneur_name = donneur_ordre[1]
            if donneur_name:
                notes += f"\nDonneur d'ordre: {donneur_name}"

        if client_name:
            notes += f"\nClient Odoo: {client_name}"

        return notes

    @staticmethod
    def _update_intervention(
        intervention: Any,
        description: str,
        display_name: str,
        notes: str,
        statut: Any,
        client_id: UUID,
        date_prevue: Optional[datetime],
        date_debut: Optional[datetime],
        date_fin: Optional[datetime],
        duree_minutes: Optional[int],
        duree_reelle_minutes: Optional[int],
        adresse: str,
    ) -> None:
        """Met à jour une intervention existante."""
        intervention.titre = description[:500] if description else display_name
        intervention.description = description or intervention.description
        intervention.notes_internes = notes
        intervention.statut = statut
        intervention.client_id = client_id

        if date_prevue:
            intervention.date_prevue_debut = date_prevue
        if date_debut:
            intervention.date_demarrage = date_debut
        if date_fin:
            intervention.date_fin = date_fin
        if duree_minutes:
            intervention.duree_prevue_minutes = duree_minutes
        if duree_reelle_minutes:
            intervention.duree_reelle_minutes = duree_reelle_minutes
        if adresse:
            intervention.adresse_ligne1 = adresse[:255]

        intervention.updated_at = datetime.utcnow()
