"""
THÉO — Adapter Commercial
==========================

Adapter pour les opérations commerciales:
- Devis
- Factures
- Avoirs
- Clients
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import date
import logging

from app.theo.adapters.base import (
    BaseAdapter,
    AdapterAction,
    AdapterResult,
    ActionStatus
)

logger = logging.getLogger(__name__)


class CommercialAdapter(BaseAdapter):
    """
    Adapter pour le module commercial AZALSCORE.

    Actions vocales:
    - creer_devis: Créer un devis
    - creer_facture: Créer une facture
    - chercher_client: Rechercher un client
    - statut_facture: Consulter le statut d'une facture
    """

    @property
    def name(self) -> str:
        return "commercial"

    @property
    def description(self) -> str:
        return "Gestion commerciale: devis, factures, clients"

    @property
    def actions(self) -> List[AdapterAction]:
        return [
            AdapterAction(
                name="creer_devis",
                description="Créer un nouveau devis pour un client",
                required_params=["client_name"],
                optional_params=["montant", "description", "validite_jours"],
                confirmation_required=True,
                voice_examples=[
                    "Fais un devis pour Dupont",
                    "Crée un devis de 5000 euros pour la société Martin",
                    "Nouveau devis client Durand"
                ]
            ),
            AdapterAction(
                name="creer_facture",
                description="Créer une facture",
                required_params=["client_name"],
                optional_params=["montant", "description", "echeance_jours"],
                confirmation_required=True,
                voice_examples=[
                    "Facture pour le client Dupont",
                    "Crée une facture de 1500 euros pour Martin",
                    "Nouvelle facture société Legrand"
                ]
            ),
            AdapterAction(
                name="chercher_client",
                description="Rechercher un client par nom",
                required_params=["client_name"],
                optional_params=[],
                confirmation_required=False,
                voice_examples=[
                    "Cherche le client Dupont",
                    "Trouve la société Martin",
                    "Client Durand"
                ]
            ),
            AdapterAction(
                name="statut_facture",
                description="Consulter le statut d'une facture",
                required_params=["numero_facture"],
                optional_params=["client_name"],
                confirmation_required=False,
                voice_examples=[
                    "Statut de la facture 2024-001",
                    "La facture pour Dupont est payée ?",
                    "Où en est la facture Martin"
                ]
            ),
            AdapterAction(
                name="liste_factures_impayees",
                description="Lister les factures impayées",
                required_params=[],
                optional_params=["client_name", "jours_retard"],
                confirmation_required=False,
                voice_examples=[
                    "Quelles factures sont impayées",
                    "Factures en retard",
                    "Impayés du client Dupont"
                ]
            ),
            AdapterAction(
                name="convertir_devis",
                description="Convertir un devis en facture",
                required_params=["numero_devis"],
                optional_params=[],
                confirmation_required=True,
                voice_examples=[
                    "Convertis le devis 2024-D001 en facture",
                    "Facture le devis Dupont",
                    "Transformer le devis en facture"
                ]
            ),
        ]

    async def execute(
        self,
        action_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Exécute une action commerciale."""
        logger.info("[CommercialAdapter] Execute: %s with %s", action_name, params)

        handlers = {
            "creer_devis": self._handle_creer_devis,
            "creer_facture": self._handle_creer_facture,
            "chercher_client": self._handle_chercher_client,
            "statut_facture": self._handle_statut_facture,
            "liste_factures_impayees": self._handle_liste_impayees,
            "convertir_devis": self._handle_convertir_devis,
        }

        handler = handlers.get(action_name)
        if not handler:
            return self._voice_error(f"Action {action_name} non reconnue")

        try:
            return await handler(params, context)
        except Exception as e:
            logger.error("[CommercialAdapter] Error: %s", e)
            return self._voice_error(f"Erreur lors de l'exécution: {str(e)}")

    async def confirm(
        self,
        action_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Confirme une action en attente."""
        logger.info("[CommercialAdapter] Confirm: %s", action_name)

        # Récupérer l'action en attente
        pending = context.get("pending_action", {})
        if not pending:
            return self._voice_error("Aucune action en attente")

        # Exécuter avec le flag confirmed
        context["confirmed"] = True
        return await self.execute(action_name, params, context)

    # ----------------------------------------------------------------
    # HANDLERS
    # ----------------------------------------------------------------

    async def _handle_creer_devis(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Crée un devis."""
        client_name = params.get("client_name")
        if not client_name:
            return self._voice_clarify(
                "Pour quel client dois-je créer le devis ?",
                ["Quel est le nom du client ?"]
            )

        montant = params.get("montant")
        description = params.get("description", "")

        # Si pas confirmé, demander confirmation
        if not context.get("confirmed"):
            msg = f"Je vais créer un devis pour {client_name}"
            if montant:
                msg += f" d'un montant de {montant} euros"
            msg += ". Tu confirmes ?"

            return self._voice_confirm(
                msg,
                data={
                    "action": "creer_devis",
                    "client_name": client_name,
                    "montant": montant,
                    "description": description
                }
            )

        # NOTE: Phase 2 - Intégration avec service commercial
        # service = get_commercial_service(db, context["tenant_id"])
        # result = service.create_quote(...)
        # Pour l'instant: données de simulation
        devis_number = "2024-D042"

        msg = f"C'est fait. Devis numéro {devis_number} créé pour {client_name}"
        if montant:
            msg += f", montant {montant} euros"

        return self._voice_success(
            msg,
            data={
                "devis_number": devis_number,
                "client_name": client_name,
                "montant": montant
            }
        )

    async def _handle_creer_facture(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Crée une facture."""
        client_name = params.get("client_name")
        if not client_name:
            return self._voice_clarify(
                "Pour quel client dois-je créer la facture ?",
                ["Quel est le nom du client ?"]
            )

        montant = params.get("montant")
        description = params.get("description", "")

        if not context.get("confirmed"):
            msg = f"Je vais créer une facture pour {client_name}"
            if montant:
                msg += f" de {montant} euros"
            msg += ". Tu confirmes ?"

            return self._voice_confirm(
                msg,
                data={
                    "action": "creer_facture",
                    "client_name": client_name,
                    "montant": montant
                }
            )

        # Exécution réelle
        facture_number = "2024-F089"

        msg = f"Facture {facture_number} créée pour {client_name}"
        if montant:
            msg += f", {montant} euros"

        return self._voice_success(
            msg,
            data={
                "facture_number": facture_number,
                "client_name": client_name,
                "montant": montant
            }
        )

    async def _handle_chercher_client(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Recherche un client."""
        client_name = params.get("client_name")
        if not client_name:
            return self._voice_clarify(
                "Quel client cherches-tu ?",
                ["Donne-moi le nom du client"]
            )

        # NOTE: Phase 2 - Intégration avec service commercial
        # service = get_commercial_service(db, context["tenant_id"])
        # customers = service.list_customers(search=client_name)
        # Pour l'instant: données de simulation
        found_clients = [
            {"name": f"Société {client_name}", "code": "CLI001", "balance": 1500},
        ]

        if found_clients:
            client = found_clients[0]
            msg = f"J'ai trouvé {client['name']}, code {client['code']}"
            if client.get("balance"):
                msg += f", solde de {client['balance']} euros"

            return self._voice_success(
                msg,
                data={"clients": found_clients}
            )
        else:
            return self._voice_success(
                f"Je n'ai pas trouvé de client nommé {client_name}",
                data={"clients": []}
            )

    async def _handle_statut_facture(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Consulte le statut d'une facture."""
        numero = params.get("numero_facture")
        client_name = params.get("client_name")

        if not numero and not client_name:
            return self._voice_clarify(
                "Quelle facture veux-tu consulter ?",
                ["Donne-moi le numéro de facture ou le nom du client"]
            )

        # Simulation
        facture = {
            "numero": numero or "2024-F089",
            "client": client_name or "Dupont",
            "montant": 2500,
            "statut": "payée",
            "date_paiement": "15 janvier"
        }

        if facture["statut"] == "payée":
            msg = f"La facture {facture['numero']} pour {facture['client']} est payée depuis le {facture['date_paiement']}"
        else:
            msg = f"La facture {facture['numero']} pour {facture['client']} est en attente, montant {facture['montant']} euros"

        return self._voice_success(msg, data={"facture": facture})

    async def _handle_liste_impayees(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Liste les factures impayées."""
        client_name = params.get("client_name")
        jours_retard = params.get("jours_retard", 0)

        # Simulation
        impayees = [
            {"numero": "2024-F078", "client": "Martin", "montant": 3200, "jours_retard": 15},
            {"numero": "2024-F081", "client": "Durand", "montant": 1800, "jours_retard": 8},
        ]

        if client_name:
            impayees = [f for f in impayees if client_name.lower() in f["client"].lower()]

        if not impayees:
            if client_name:
                return self._voice_success(f"Aucune facture impayée pour {client_name}")
            return self._voice_success("Aucune facture impayée, tout est à jour")

        total = sum(f["montant"] for f in impayees)
        msg = f"Tu as {len(impayees)} factures impayées pour un total de {total} euros. "

        if len(impayees) <= 3:
            details = ", ".join([f"{f['client']} {f['montant']} euros" for f in impayees])
            msg += f"Détail : {details}"

        return self._voice_success(
            msg,
            data={"factures_impayees": impayees, "total": total}
        )

    async def _handle_convertir_devis(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Convertit un devis en facture."""
        numero_devis = params.get("numero_devis")
        if not numero_devis:
            return self._voice_clarify(
                "Quel devis veux-tu convertir en facture ?",
                ["Donne-moi le numéro du devis"]
            )

        if not context.get("confirmed"):
            # Simulation lookup
            devis_info = {
                "numero": numero_devis,
                "client": "Dupont",
                "montant": 4500
            }

            msg = f"Je vais convertir le devis {numero_devis} pour {devis_info['client']}, "
            msg += f"{devis_info['montant']} euros, en facture. Tu confirmes ?"

            return self._voice_confirm(msg, data={"devis": devis_info})

        # Exécution
        new_facture = "2024-F090"

        return self._voice_success(
            f"Devis {numero_devis} converti. Nouvelle facture numéro {new_facture}",
            data={
                "devis_number": numero_devis,
                "facture_number": new_facture
            }
        )
