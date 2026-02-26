"""
THÉO — Délégateur Principal
============================

Le délégateur route les intentions vers les adapters appropriés.
C'est le pont entre l'orchestrateur vocal et les modules métier.
"""
from __future__ import annotations


from typing import Dict, Any, List, Optional, Tuple
import logging
import re

from app.theo.core.intent_detector import Intent, IntentCategory, ActionType
from app.theo.adapters.base import (
    BaseAdapter,
    AdapterResult,
    ActionStatus,
    get_adapter_registry
)
from app.theo.adapters.commercial import CommercialAdapter
from app.theo.adapters.treasury import TreasuryAdapter
from app.theo.adapters.navigation import NavigationAdapter

logger = logging.getLogger(__name__)


# ============================================================
# MAPPING INTENT → ADAPTER/ACTION
# ============================================================

# Mapping des catégories d'intent vers les adapters
CATEGORY_ADAPTER_MAP = {
    IntentCategory.BUSINESS_ACTION: ("commercial", "creer_devis"),  # Default business = devis
    IntentCategory.NAVIGATION: ("navigation", "aller_a"),
    IntentCategory.INFORMATION: ("treasury", "solde_tresorerie"),  # Default info = tréso
}

# Mapping des types d'action vers les actions adapter
ACTION_TYPE_MAP = {
    ActionType.CREATE_QUOTE: ("commercial", "creer_devis"),
    ActionType.CREATE_INVOICE: ("commercial", "creer_facture"),
    ActionType.SEARCH_CLIENT: ("commercial", "chercher_client"),
    ActionType.CHECK_PAYMENT: ("commercial", "statut_facture"),
    ActionType.GET_DIRECTIONS: ("navigation", "aller_a"),
    ActionType.ASK_QUESTION: ("treasury", "solde_tresorerie"),  # Default query
}


class TheoDelegator:
    """
    Délègue les intentions aux adapters métier.

    Workflow:
    1. Reçoit une intention de l'orchestrateur
    2. Identifie l'adapter et l'action appropriés
    3. Prépare les paramètres
    4. Appelle l'adapter
    5. Retourne le résultat formaté pour la voix
    """

    def __init__(self):
        self._registry = get_adapter_registry()
        self._init_adapters()

    def _init_adapters(self) -> None:
        """Initialise et enregistre les adapters."""
        adapters = [
            CommercialAdapter(),
            TreasuryAdapter(),
            NavigationAdapter(),
        ]

        for adapter in adapters:
            self._registry.register(adapter)

        logger.info("[Delegator] Initialized %s adapters", len(adapters))

    async def delegate(
        self,
        intent: Intent,
        context: Dict[str, Any]
    ) -> AdapterResult:
        """
        Délègue une intention à l'adapter approprié.

        Args:
            intent: Intention détectée par l'IntentDetector
            context: Contexte de session (user_id, tenant_id, etc.)

        Returns:
            AdapterResult avec le message vocal
        """
        logger.info("[Delegator] Processing intent: %s/%s", intent.category, intent.action)

        # 1. Trouver l'adapter et l'action
        adapter_name, action_name = self._resolve_adapter(intent)

        if not adapter_name:
            return AdapterResult(
                status=ActionStatus.ERROR,
                message="Je ne sais pas comment traiter cette demande"
            )

        # 2. Récupérer l'adapter
        adapter = self._registry.get(adapter_name)
        if not adapter:
            logger.error("[Delegator] Adapter not found: %s", adapter_name)
            return AdapterResult(
                status=ActionStatus.ERROR,
                message="Module indisponible"
            )

        # 3. Préparer les paramètres
        params = self._extract_params(intent, adapter_name, action_name)

        # 4. Exécuter
        try:
            result = await adapter.execute(action_name, params, context)
            logger.info("[Delegator] Result: %s", result.status)
            return result

        except Exception as e:
            logger.error("[Delegator] Execution error: %s", e)
            return AdapterResult(
                status=ActionStatus.ERROR,
                message=f"Erreur lors de l'exécution: {str(e)}"
            )

    async def confirm_pending(
        self,
        adapter_name: str,
        action_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """
        Confirme une action en attente.

        Args:
            adapter_name: Nom de l'adapter
            action_name: Nom de l'action
            params: Paramètres originaux
            context: Contexte incluant pending_action

        Returns:
            AdapterResult
        """
        adapter = self._registry.get(adapter_name)
        if not adapter:
            return AdapterResult(
                status=ActionStatus.ERROR,
                message="Module indisponible"
            )

        return await adapter.confirm(action_name, params, context)

    def _resolve_adapter(self, intent: Intent) -> Tuple[Optional[str], Optional[str]]:
        """
        Résout l'adapter et l'action pour une intention.

        Returns:
            Tuple (adapter_name, action_name) ou (None, None)
        """
        # 1. Essayer par type d'action directement
        if intent.action in ACTION_TYPE_MAP:
            return ACTION_TYPE_MAP[intent.action]

        # 2. Essayer par catégorie
        if intent.category in CATEGORY_ADAPTER_MAP:
            return CATEGORY_ADAPTER_MAP[intent.category]

        # 3. Fallback intelligent basé sur le texte
        return self._fuzzy_resolve(intent)

    def _fuzzy_resolve(self, intent: Intent) -> Tuple[Optional[str], Optional[str]]:
        """Résolution floue basée sur les mots-clés du texte original."""
        text = intent.original_text.lower()

        # Keywords → adapter/action
        keyword_map = {
            ("facture", "facturer"): ("commercial", "creer_facture"),
            ("devis",): ("commercial", "creer_devis"),
            ("client",): ("commercial", "chercher_client"),
            ("solde", "combien", "tréso", "banque"): ("treasury", "solde_tresorerie"),
            ("prévision", "projection"): ("treasury", "prevision_tresorerie"),
            ("impayé", "retard"): ("commercial", "liste_factures_impayees"),
            ("échéance",): ("treasury", "liste_echeances"),
            ("encaissement", "reçu"): ("treasury", "enregistrer_encaissement"),
            ("décaissement", "payé"): ("treasury", "enregistrer_decaissement"),
            ("va ", "ouvre", "affiche", "montre"): ("navigation", "aller_a"),
            ("retour",): ("navigation", "retour"),
        }

        for keywords, target in keyword_map.items():
            for kw in keywords:
                if kw in text:
                    return target

        return None, None

    def _extract_params(
        self,
        intent: Intent,
        adapter_name: str,
        action_name: str
    ) -> Dict[str, Any]:
        """
        Extrait les paramètres de l'intent pour l'action.

        Mappe les entités extraites vers les paramètres attendus par l'adapter.
        """
        params = {}

        # Mapper les entités connues
        entity_mapping = {
            "client_name": ["client_name", "client", "nom_client"],
            "montant": ["montant", "amount", "prix"],
            "numero_facture": ["numero_facture", "facture", "numero"],
            "numero_devis": ["numero_devis", "devis"],
            "destination": ["destination", "page", "module"],
            "terme": ["terme", "query", "recherche"],
        }

        for param_name, entity_keys in entity_mapping.items():
            for key in entity_keys:
                if key in intent.entities:
                    params[param_name] = intent.entities[key]
                    break

        # Pour la navigation, extraire la destination du texte brut
        if adapter_name == "navigation" and action_name == "aller_a":
            if "destination" not in params:
                params["destination"] = self._extract_destination(intent.raw_text)

        # Pour les créations, extraire le type d'élément
        if action_name == "nouveau":
            params["type_element"] = intent.entities.get("type", "")

        return params

    def _extract_destination(self, text: str) -> str:
        """Extrait la destination d'une commande de navigation."""
        text = text.lower()

        # Patterns de navigation
        patterns = [
            r"(?:va|aller|ouvre|affiche|montre)(?:\s+(?:aux?|vers|à))?\s+(?:la\s+|les\s+)?(\w+)",
            r"(?:direction|emmène[-\s]moi)\s+(?:à\s+|aux?\s+)?(?:la\s+|les\s+)?(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        # Fallback: dernier mot significatif
        words = [w for w in text.split() if len(w) > 3]
        return words[-1] if words else ""

    def get_available_actions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retourne toutes les actions disponibles."""
        return self._registry.get_all_actions()

    def get_adapter_for_category(self, category: IntentCategory) -> Optional[BaseAdapter]:
        """Retourne l'adapter approprié pour une catégorie d'intent."""
        if category in CATEGORY_ADAPTER_MAP:
            adapter_name, _ = CATEGORY_ADAPTER_MAP[category]
            return self._registry.get(adapter_name)
        return None


# ============================================================
# SINGLETON
# ============================================================

_delegator: Optional[TheoDelegator] = None


def get_delegator() -> TheoDelegator:
    """Retourne l'instance singleton du délégateur."""
    global _delegator
    if _delegator is None:
        _delegator = TheoDelegator()
    return _delegator
