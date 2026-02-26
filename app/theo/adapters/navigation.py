"""
THÉO — Adapter Navigation
==========================

Adapter pour la navigation dans l'ERP:
- Aller à un module
- Ouvrir une page
- Actions rapides
"""
from __future__ import annotations


from typing import Dict, Any, List, Optional
import logging

from app.theo.adapters.base import (
    BaseAdapter,
    AdapterAction,
    AdapterResult,
    ActionStatus
)

logger = logging.getLogger(__name__)


# Mapping des destinations vocales vers les routes ERP
NAVIGATION_ROUTES = {
    # Commercial
    "clients": {"route": "/crm/customers", "label": "Liste des clients"},
    "client": {"route": "/crm/customers", "label": "Liste des clients"},
    "crm": {"route": "/crm", "label": "CRM"},
    "devis": {"route": "/invoicing/quotes", "label": "Devis"},
    "factures": {"route": "/invoicing/invoices", "label": "Factures"},
    "facture": {"route": "/invoicing/invoices", "label": "Factures"},
    "avoirs": {"route": "/invoicing/credits", "label": "Avoirs"},

    # Finance
    "tresorerie": {"route": "/treasury", "label": "Trésorerie"},
    "trésorerie": {"route": "/treasury", "label": "Trésorerie"},
    "comptabilite": {"route": "/accounting", "label": "Comptabilité"},
    "comptabilité": {"route": "/accounting", "label": "Comptabilité"},
    "journal": {"route": "/accounting/journal", "label": "Journal comptable"},

    # RH
    "employes": {"route": "/hr/employees", "label": "Employés"},
    "employés": {"route": "/hr/employees", "label": "Employés"},
    "conges": {"route": "/hr/leaves", "label": "Congés"},
    "congés": {"route": "/hr/leaves", "label": "Congés"},
    "paie": {"route": "/hr/payroll", "label": "Paie"},

    # Autres
    "dashboard": {"route": "/dashboard", "label": "Tableau de bord"},
    "tableau de bord": {"route": "/dashboard", "label": "Tableau de bord"},
    "accueil": {"route": "/", "label": "Accueil"},
    "parametres": {"route": "/settings", "label": "Paramètres"},
    "paramètres": {"route": "/settings", "label": "Paramètres"},
    "profil": {"route": "/profile", "label": "Mon profil"},
}


class NavigationAdapter(BaseAdapter):
    """
    Adapter pour la navigation ERP.

    Permet de naviguer vocalement dans l'application.
    """

    @property
    def name(self) -> str:
        return "navigation"

    @property
    def description(self) -> str:
        return "Navigation dans l'ERP: modules, pages, actions"

    @property
    def actions(self) -> List[AdapterAction]:
        return [
            AdapterAction(
                name="aller_a",
                description="Naviguer vers une page de l'ERP",
                required_params=["destination"],
                optional_params=[],
                confirmation_required=False,
                voice_examples=[
                    "Va aux factures",
                    "Ouvre les clients",
                    "Affiche le tableau de bord",
                    "Emmène-moi à la trésorerie",
                    "Direction la comptabilité"
                ]
            ),
            AdapterAction(
                name="retour",
                description="Retourner à la page précédente",
                required_params=[],
                optional_params=[],
                confirmation_required=False,
                voice_examples=[
                    "Retour",
                    "Page précédente",
                    "Reviens en arrière"
                ]
            ),
            AdapterAction(
                name="accueil",
                description="Retourner à l'accueil",
                required_params=[],
                optional_params=[],
                confirmation_required=False,
                voice_examples=[
                    "Accueil",
                    "Retour accueil",
                    "Page d'accueil"
                ]
            ),
            AdapterAction(
                name="rechercher",
                description="Rechercher dans l'ERP",
                required_params=["terme"],
                optional_params=["scope"],
                confirmation_required=False,
                voice_examples=[
                    "Recherche Dupont",
                    "Trouve la facture 2024-001",
                    "Cherche dans les clients"
                ]
            ),
            AdapterAction(
                name="nouveau",
                description="Créer un nouvel élément",
                required_params=["type_element"],
                optional_params=[],
                confirmation_required=False,
                voice_examples=[
                    "Nouveau client",
                    "Nouvelle facture",
                    "Créer un devis"
                ]
            ),
        ]

    async def execute(
        self,
        action_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Exécute une action de navigation."""
        logger.info("[NavigationAdapter] Execute: %s with %s", action_name, params)

        handlers = {
            "aller_a": self._handle_aller_a,
            "retour": self._handle_retour,
            "accueil": self._handle_accueil,
            "rechercher": self._handle_rechercher,
            "nouveau": self._handle_nouveau,
        }

        handler = handlers.get(action_name)
        if not handler:
            return self._voice_error(f"Action {action_name} non reconnue")

        try:
            return await handler(params, context)
        except Exception as e:
            logger.error("[NavigationAdapter] Error: %s", e)
            return self._voice_error(f"Erreur: {str(e)}")

    async def confirm(
        self,
        action_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Navigation ne nécessite pas de confirmation."""
        return await self.execute(action_name, params, context)

    # ----------------------------------------------------------------
    # HANDLERS
    # ----------------------------------------------------------------

    async def _handle_aller_a(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Navigue vers une destination."""
        destination = params.get("destination", "").lower().strip()

        if not destination:
            return self._voice_clarify(
                "Où veux-tu aller ?",
                ["Dis-moi quelle page tu veux voir"]
            )

        # Chercher dans les routes
        route_info = NAVIGATION_ROUTES.get(destination)

        if route_info:
            return self._voice_success(
                f"Je t'emmène aux {route_info['label']}",
                data={
                    "action": "navigate",
                    "route": route_info["route"],
                    "label": route_info["label"]
                }
            )

        # Recherche partielle
        for key, info in NAVIGATION_ROUTES.items():
            if destination in key or key in destination:
                return self._voice_success(
                    f"Je t'emmène aux {info['label']}",
                    data={
                        "action": "navigate",
                        "route": info["route"],
                        "label": info["label"]
                    }
                )

        # Destination inconnue
        available = ", ".join(list(NAVIGATION_ROUTES.keys())[:5])
        return self._voice_error(
            f"Je ne connais pas cette destination. "
            f"Tu peux dire par exemple : {available}"
        )

    async def _handle_retour(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Retour à la page précédente."""
        return self._voice_success(
            "Retour à la page précédente",
            data={
                "action": "back"
            }
        )

    async def _handle_accueil(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Retour à l'accueil."""
        return self._voice_success(
            "Retour à l'accueil",
            data={
                "action": "navigate",
                "route": "/dashboard",
                "label": "Tableau de bord"
            }
        )

    async def _handle_rechercher(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Recherche globale."""
        terme = params.get("terme")
        scope = params.get("scope")

        if not terme:
            return self._voice_clarify(
                "Que veux-tu rechercher ?",
                ["Dis-moi ce que tu cherches"]
            )

        msg = f"Je recherche '{terme}'"
        if scope:
            msg += f" dans {scope}"

        return self._voice_success(
            msg,
            data={
                "action": "search",
                "query": terme,
                "scope": scope
            }
        )

    async def _handle_nouveau(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """Création d'un nouvel élément."""
        type_element = params.get("type_element", "").lower()

        if not type_element:
            return self._voice_clarify(
                "Que veux-tu créer ?",
                ["Client, facture, devis..."]
            )

        # Mapper vers les routes de création
        creation_routes = {
            "client": "/crm/customers/new",
            "facture": "/invoicing/invoices/new",
            "devis": "/invoicing/quotes/new",
            "avoir": "/invoicing/credits/new",
            "employe": "/hr/employees/new",
            "employé": "/hr/employees/new",
        }

        route = creation_routes.get(type_element)
        if route:
            return self._voice_success(
                f"J'ouvre le formulaire de création de {type_element}",
                data={
                    "action": "navigate",
                    "route": route,
                    "label": f"Nouveau {type_element}"
                }
            )

        return self._voice_error(
            f"Je ne peux pas créer de '{type_element}' directement. "
            "Dis-moi 'nouveau client' ou 'nouvelle facture' par exemple."
        )
