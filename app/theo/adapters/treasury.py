"""
THÉO — Adapter Trésorerie
==========================

Adapter pour les opérations de trésorerie:
- Solde bancaire
- Encaissements
- Décaissements
- Prévisions
"""
from __future__ import annotations


from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import date, datetime
import logging

from app.theo.adapters.base import (
    BaseAdapter,
    AdapterAction,
    AdapterResult,
    ActionStatus
)

logger = logging.getLogger(__name__)


class TreasuryAdapter(BaseAdapter):
    """
    Adapter pour le module trésorerie AZALSCORE.

    Actions vocales:
    - solde_tresorerie: Consulter le solde
    - prevision_tresorerie: Prévisions à X jours
    - enregistrer_encaissement: Noter un encaissement
    - liste_echeances: Échéances à venir
    """

    @property
    def name(self) -> str:
        return "treasury"

    @property
    def description(self) -> str:
        return "Gestion de trésorerie: soldes, prévisions, encaissements"

    @property
    def actions(self) -> List[AdapterAction]:
        return [
            AdapterAction(
                name="solde_tresorerie",
                description="Consulter le solde de trésorerie actuel",
                required_params=[],
                optional_params=["compte"],
                confirmation_required=False,
                voice_examples=[
                    "Quel est mon solde",
                    "Combien j'ai en banque",
                    "Solde trésorerie",
                    "Où en est la tréso"
                ]
            ),
            AdapterAction(
                name="prevision_tresorerie",
                description="Obtenir les prévisions de trésorerie",
                required_params=[],
                optional_params=["jours", "periode"],
                confirmation_required=False,
                voice_examples=[
                    "Prévisions à 30 jours",
                    "Comment sera la tréso dans une semaine",
                    "Projection de trésorerie",
                    "Trésorerie prévisionnelle"
                ]
            ),
            AdapterAction(
                name="enregistrer_encaissement",
                description="Enregistrer un encaissement reçu",
                required_params=["montant"],
                optional_params=["client_name", "reference", "mode_paiement"],
                confirmation_required=True,
                voice_examples=[
                    "J'ai reçu 1500 euros de Dupont",
                    "Encaissement de 3000 euros",
                    "Paiement reçu 2500 euros client Martin"
                ]
            ),
            AdapterAction(
                name="enregistrer_decaissement",
                description="Enregistrer un décaissement",
                required_params=["montant"],
                optional_params=["fournisseur", "reference", "categorie"],
                confirmation_required=True,
                voice_examples=[
                    "J'ai payé 800 euros au fournisseur",
                    "Décaissement 1200 euros",
                    "Paiement de 500 euros"
                ]
            ),
            AdapterAction(
                name="liste_echeances",
                description="Lister les échéances à venir",
                required_params=[],
                optional_params=["jours", "type"],
                confirmation_required=False,
                voice_examples=[
                    "Quelles échéances cette semaine",
                    "Échéances à venir",
                    "Qu'est-ce que je dois payer bientôt"
                ]
            ),
            AdapterAction(
                name="alerte_tresorerie",
                description="Vérifier les alertes de trésorerie",
                required_params=[],
                optional_params=[],
                confirmation_required=False,
                voice_examples=[
                    "Y a-t-il des alertes",
                    "Situation critique",
                    "Problèmes de trésorerie"
                ]
            ),
        ]

    async def execute(
        self,
        action_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Exécute une action de trésorerie."""
        logger.info("[TreasuryAdapter] Execute: %s with %s", action_name, params)

        handlers = {
            "solde_tresorerie": self._handle_solde,
            "prevision_tresorerie": self._handle_prevision,
            "enregistrer_encaissement": self._handle_encaissement,
            "enregistrer_decaissement": self._handle_decaissement,
            "liste_echeances": self._handle_echeances,
            "alerte_tresorerie": self._handle_alertes,
        }

        handler = handlers.get(action_name)
        if not handler:
            return self._voice_error(f"Action {action_name} non reconnue")

        try:
            return await handler(params, context)
        except Exception as e:
            logger.error("[TreasuryAdapter] Error: %s", e)
            return self._voice_error(f"Erreur: {str(e)}")

    async def confirm(
        self,
        action_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Confirme une action en attente."""
        context["confirmed"] = True
        return await self.execute(action_name, params, context)

    # ----------------------------------------------------------------
    # HANDLERS
    # ----------------------------------------------------------------

    async def _handle_solde(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Consulte le solde de trésorerie."""
        compte = params.get("compte")

        # NOTE: Phase 2 - Intégration avec service trésorerie
        # service = get_treasury_service(db, context["tenant_id"])
        # solde = service.get_current_balance()
        # Pour l'instant: données de simulation
        soldes = {
            "principal": {"nom": "Compte principal", "solde": 45670.50},
            "caisse": {"nom": "Caisse", "solde": 1250.00},
        }

        if compte:
            compte_data = soldes.get(compte.lower())
            if compte_data:
                msg = f"Le {compte_data['nom']} a un solde de {compte_data['solde']:.0f} euros"
            else:
                msg = f"Je ne trouve pas le compte {compte}"
        else:
            total = sum(c["solde"] for c in soldes.values())
            msg = f"Solde total de trésorerie : {total:.0f} euros"

        return self._voice_success(msg, data={"soldes": soldes})

    async def _handle_prevision(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Prévisions de trésorerie."""
        jours = params.get("jours", 30)

        # Simulation
        prevision = {
            "solde_actuel": 45670,
            "encaissements_prevus": 28500,
            "decaissements_prevus": 32100,
            "solde_prevu": 42070,
            "variation": -3600
        }

        if prevision["variation"] >= 0:
            tendance = "en hausse"
        else:
            tendance = "en baisse"

        msg = f"Dans {jours} jours, trésorerie prévue à {prevision['solde_prevu']:.0f} euros, "
        msg += f"{tendance} de {abs(prevision['variation']):.0f} euros. "
        msg += f"Encaissements prévus {prevision['encaissements_prevus']:.0f}, "
        msg += f"décaissements {prevision['decaissements_prevus']:.0f}."

        return self._voice_success(msg, data={"prevision": prevision})

    async def _handle_encaissement(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Enregistre un encaissement."""
        montant = params.get("montant")
        if not montant:
            return self._voice_clarify(
                "Quel montant as-tu reçu ?",
                ["Indique le montant de l'encaissement"]
            )

        client_name = params.get("client_name", "")
        reference = params.get("reference", "")
        mode = params.get("mode_paiement", "virement")

        if not context.get("confirmed"):
            msg = f"J'enregistre un encaissement de {montant} euros"
            if client_name:
                msg += f" de {client_name}"
            msg += ". Tu confirmes ?"

            return self._voice_confirm(
                msg,
                data={
                    "montant": montant,
                    "client_name": client_name,
                    "mode": mode
                }
            )

        # NOTE: Phase 2 - Appeler service.register_incoming_payment(...)

        msg = f"Encaissement de {montant} euros enregistré"
        if client_name:
            msg += f" pour {client_name}"

        return self._voice_success(
            msg,
            data={
                "montant": montant,
                "client_name": client_name,
                "reference": f"ENC-{datetime.now().strftime('%Y%m%d')}-001"
            }
        )

    async def _handle_decaissement(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Enregistre un décaissement."""
        montant = params.get("montant")
        if not montant:
            return self._voice_clarify(
                "Quel montant as-tu payé ?",
                ["Indique le montant du décaissement"]
            )

        fournisseur = params.get("fournisseur", "")
        categorie = params.get("categorie", "")

        if not context.get("confirmed"):
            msg = f"J'enregistre un décaissement de {montant} euros"
            if fournisseur:
                msg += f" pour {fournisseur}"
            msg += ". Tu confirmes ?"

            return self._voice_confirm(
                msg,
                data={"montant": montant, "fournisseur": fournisseur}
            )

        # Exécution
        msg = f"Décaissement de {montant} euros enregistré"
        if fournisseur:
            msg += f" pour {fournisseur}"

        return self._voice_success(
            msg,
            data={
                "montant": montant,
                "fournisseur": fournisseur,
                "reference": f"DEC-{datetime.now().strftime('%Y%m%d')}-001"
            }
        )

    async def _handle_echeances(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Liste les échéances à venir."""
        jours = params.get("jours", 7)
        type_echeance = params.get("type")  # "encaissement" ou "decaissement"

        # Simulation
        echeances = [
            {"type": "decaissement", "libelle": "Loyer", "montant": 2500, "date": "25 janvier"},
            {"type": "encaissement", "libelle": "Facture Dupont", "montant": 3200, "date": "28 janvier"},
            {"type": "decaissement", "libelle": "Fournisseur X", "montant": 1800, "date": "30 janvier"},
        ]

        if type_echeance:
            echeances = [e for e in echeances if e["type"] == type_echeance]

        if not echeances:
            return self._voice_success(f"Aucune échéance dans les {jours} prochains jours")

        encaissements = sum(e["montant"] for e in echeances if e["type"] == "encaissement")
        decaissements = sum(e["montant"] for e in echeances if e["type"] == "decaissement")

        msg = f"Dans les {jours} prochains jours : "
        msg += f"{encaissements:.0f} euros à recevoir, "
        msg += f"{decaissements:.0f} euros à payer. "

        if len(echeances) <= 3:
            details = ", ".join([f"{e['libelle']} le {e['date']}" for e in echeances])
            msg += f"Détail : {details}"

        return self._voice_success(msg, data={"echeances": echeances})

    async def _handle_alertes(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Vérifie les alertes de trésorerie."""
        # Simulation
        alertes = [
            {"niveau": "warning", "message": "Solde passera sous 40000 euros dans 15 jours"},
        ]

        if not alertes:
            return self._voice_success("Aucune alerte, la trésorerie est saine")

        critiques = [a for a in alertes if a["niveau"] == "critical"]
        warnings = [a for a in alertes if a["niveau"] == "warning"]

        if critiques:
            msg = f"Attention, {len(critiques)} alerte critique. "
            msg += critiques[0]["message"]
        elif warnings:
            msg = f"Tu as {len(warnings)} point d'attention. "
            msg += warnings[0]["message"]
        else:
            msg = "Situation normale"

        return self._voice_success(msg, data={"alertes": alertes})
