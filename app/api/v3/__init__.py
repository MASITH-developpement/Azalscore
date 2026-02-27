"""
AZALS API V3 - Unified Router Registry
=======================================

Point d'entrée unifié pour tous les modules API sous /v3/.

Ce module implémente un registre déclaratif de routers avec :
- Classification par priorité (CRITICAL, IMPORTANT, STANDARD, OPTIONAL)
- Chargement sécurisé avec logging structuré
- Validation des modules critiques au démarrage
- Métriques d'observabilité

CONFORMITÉ AZALSCORE:
- AZA-NF-003: Modules subordonnés au noyau
- AZA-BE-003: Contrat backend obligatoire
- AZA-API-003: Versioning explicite
- AZA-FE-007: Auditabilité permanente

ARCHITECTURE:
- Tous les routers sont montés sous /v3/{module}
- Import sécurisé avec fallback et logging structuré
- Mode strict optionnel pour environnement production

Auteur: AZALSCORE Team
Version: 3.1.0
Dernière mise à jour: 2026-02-16
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from importlib import import_module
from typing import Dict, List, Optional

from fastapi import APIRouter

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES ET ÉNUMÉRATIONS
# =============================================================================

class ModulePriority(str, Enum):
    """
    Classification des modules par criticité.

    - CRITICAL: Module requis pour le fonctionnement de base.
                L'absence bloque le démarrage en mode strict.
    - IMPORTANT: Fonctionnalité métier principale.
                 L'absence génère un warning.
    - STANDARD: Module standard. L'absence est acceptable.
    - OPTIONAL: Module optionnel/expérimental.
    """
    CRITICAL = "critical"
    IMPORTANT = "important"
    STANDARD = "standard"
    OPTIONAL = "optional"


@dataclass
class ModuleDefinition:
    """
    Définition déclarative d'un module à charger.

    Attributes:
        name: Identifiant unique du module (ex: "contacts")
        import_path: Chemin d'import complet (ex: "app.modules.contacts.router_crud")
        priority: Niveau de criticité
        description: Description courte pour la documentation
        router_attr: Nom de l'attribut router dans le module (défaut: "router")
    """
    name: str
    import_path: str
    priority: ModulePriority
    description: str
    router_attr: str = "router"


@dataclass
class LoadResult:
    """
    Résultat du chargement d'un module.

    Attributes:
        success: True si le module a été chargé
        module_name: Nom du module
        priority: Priorité du module
        error: Message d'erreur si échec
        load_time_ms: Temps de chargement en millisecondes
    """
    success: bool
    module_name: str
    priority: ModulePriority
    error: Optional[str] = None
    load_time_ms: float = 0.0


@dataclass
class RegistryMetrics:
    """
    Métriques du registre de modules.

    Conformité: AZA-FE-007 (Auditabilité permanente)
    """
    total_modules: int = 0
    loaded_modules: int = 0
    failed_modules: int = 0
    critical_failures: int = 0
    total_load_time_ms: float = 0.0
    loaded_by_priority: Dict[str, int] = field(default_factory=dict)
    failed_by_priority: Dict[str, int] = field(default_factory=dict)


# =============================================================================
# REGISTRE DES MODULES
# =============================================================================

# Définition déclarative de tous les modules V3
# Ordre: CRITICAL → IMPORTANT → STANDARD → OPTIONAL
MODULE_REGISTRY: List[ModuleDefinition] = [
    # -------------------------------------------------------------------------
    # MODULES CRITIQUES (P0) - Requis pour le fonctionnement de base
    # -------------------------------------------------------------------------
    ModuleDefinition(
        name="commercial",
        import_path="app.modules.commercial.router_crud",
        priority=ModulePriority.CRITICAL,
        description="Clients, documents, devis, factures"
    ),
    ModuleDefinition(
        name="contacts",
        import_path="app.modules.contacts.router_crud",
        priority=ModulePriority.CRITICAL,
        description="Personnes, adresses, coordonnées"
    ),
    ModuleDefinition(
        name="hr",
        import_path="app.modules.hr.router_crud",
        priority=ModulePriority.CRITICAL,
        description="Employés, départements, congés"
    ),
    ModuleDefinition(
        name="interventions",
        import_path="app.modules.interventions.router_crud",
        priority=ModulePriority.CRITICAL,
        description="Ordres de service, planification terrain"
    ),
    ModuleDefinition(
        name="inventory",
        import_path="app.modules.inventory.router_crud",
        priority=ModulePriority.CRITICAL,
        description="Produits, stocks, mouvements"
    ),

    # -------------------------------------------------------------------------
    # MODULES IMPORTANTS (P1) - Fonctionnalités métier principales
    # -------------------------------------------------------------------------
    ModuleDefinition(
        name="accounting",
        import_path="app.modules.accounting.router_unified",
        priority=ModulePriority.IMPORTANT,
        description="Comptabilité, écritures, rapprochement"
    ),
    ModuleDefinition(
        name="treasury",
        import_path="app.modules.treasury.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Trésorerie, comptes bancaires"
    ),
    ModuleDefinition(
        name="purchases",
        import_path="app.modules.purchases.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Achats, fournisseurs, commandes"
    ),
    ModuleDefinition(
        name="production",
        import_path="app.modules.production.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Ordres de fabrication, centres de travail"
    ),
    ModuleDefinition(
        name="projects",
        import_path="app.modules.projects.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Projets, tâches, temps"
    ),
    ModuleDefinition(
        name="maintenance",
        import_path="app.modules.maintenance.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Équipements, ordres de maintenance"
    ),
    ModuleDefinition(
        name="finance",
        import_path="app.modules.finance.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Journaux, écritures comptables"
    ),
    ModuleDefinition(
        name="finance_providers",
        import_path="app.modules.finance.router_providers",
        priority=ModulePriority.IMPORTANT,
        description="Providers finance: Swan, NMI, Defacto, Solaris"
    ),
    ModuleDefinition(
        name="finance_webhooks",
        import_path="app.modules.finance.webhooks.router",
        priority=ModulePriority.IMPORTANT,
        description="Webhooks finance unifiés"
    ),
    ModuleDefinition(
        name="finance_reconciliation",
        import_path="app.modules.finance.reconciliation.router",
        priority=ModulePriority.IMPORTANT,
        description="Rapprochement bancaire IA"
    ),
    ModuleDefinition(
        name="finance_invoice_ocr",
        import_path="app.modules.finance.invoice_ocr.router",
        priority=ModulePriority.IMPORTANT,
        description="OCR factures fournisseurs"
    ),
    ModuleDefinition(
        name="finance_cash_forecast",
        import_path="app.modules.finance.cash_forecast.router",
        priority=ModulePriority.IMPORTANT,
        description="Prévisionnel de trésorerie"
    ),
    ModuleDefinition(
        name="finance_auto_categorization",
        import_path="app.modules.finance.auto_categorization.router",
        priority=ModulePriority.IMPORTANT,
        description="Catégorisation automatique des opérations"
    ),
    ModuleDefinition(
        name="finance_currency",
        import_path="app.modules.finance.currency.router",
        priority=ModulePriority.IMPORTANT,
        description="Gestion des devises et taux de change"
    ),
    ModuleDefinition(
        name="finance_virtual_cards",
        import_path="app.modules.finance.virtual_cards.router",
        priority=ModulePriority.IMPORTANT,
        description="Cartes bancaires virtuelles"
    ),
    ModuleDefinition(
        name="finance_integration",
        import_path="app.modules.finance.integration.router",
        priority=ModulePriority.IMPORTANT,
        description="Intégration Finance-Comptabilité-Facturation"
    ),
    ModuleDefinition(
        name="finance_suite",
        import_path="app.modules.finance.suite.router",
        priority=ModulePriority.IMPORTANT,
        description="Orchestrateur Finance Suite"
    ),
    ModuleDefinition(
        name="finance_approval",
        import_path="app.modules.finance.approval.router",
        priority=ModulePriority.IMPORTANT,
        description="Workflows d'approbation"
    ),
    ModuleDefinition(
        name="production_gpao",
        import_path="app.modules.production.gpao.router",
        priority=ModulePriority.IMPORTANT,
        description="GPAO/MRP - Gestion de Production Assistée"
    ),
    ModuleDefinition(
        name="production_gantt",
        import_path="app.modules.production.gantt.router",
        priority=ModulePriority.IMPORTANT,
        description="Gantt Production - Visualisation et planification"
    ),
    ModuleDefinition(
        name="production_traceability",
        import_path="app.modules.production.traceability.router",
        priority=ModulePriority.IMPORTANT,
        description="Traçabilité - Lots et numéros de série"
    ),
    ModuleDefinition(
        name="production_delivery",
        import_path="app.modules.production.delivery.router",
        priority=ModulePriority.IMPORTANT,
        description="Bons de livraison et expéditions"
    ),
    ModuleDefinition(
        name="production_wms",
        import_path="app.modules.production.wms.router",
        priority=ModulePriority.IMPORTANT,
        description="WMS - Gestion d'entrepôt"
    ),
    ModuleDefinition(
        name="production_mes",
        import_path="app.modules.production.mes.router",
        priority=ModulePriority.IMPORTANT,
        description="MES - Suivi production temps réel"
    ),
    ModuleDefinition(
        name="helpdesk",
        import_path="app.modules.helpdesk.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Tickets, catégories, SLA"
    ),

    # -------------------------------------------------------------------------
    # MODULES SÉCURITÉ & ADMINISTRATION (P1)
    # -------------------------------------------------------------------------
    ModuleDefinition(
        name="iam",
        import_path="app.modules.iam.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Users, roles, permissions"
    ),
    ModuleDefinition(
        name="tenants",
        import_path="app.modules.tenants.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Multi-tenant management"
    ),
    ModuleDefinition(
        name="audit",
        import_path="app.modules.audit.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Logs, traçabilité, conformité"
    ),
    ModuleDefinition(
        name="compliance",
        import_path="app.modules.compliance.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Conformité, RGPD"
    ),
    ModuleDefinition(
        name="subscriptions",
        import_path="app.modules.subscriptions.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Abonnements, plans, facturation"
    ),
    ModuleDefinition(
        name="backup",
        import_path="app.modules.backup.router_crud",
        priority=ModulePriority.IMPORTANT,
        description="Sauvegardes, restauration"
    ),

    # -------------------------------------------------------------------------
    # MODULES STANDARD (P2) - Interface & UX
    # -------------------------------------------------------------------------
    ModuleDefinition(
        name="cockpit",
        import_path="app.api.cockpit",
        priority=ModulePriority.STANDARD,
        description="Dashboard principal"
    ),
    ModuleDefinition(
        name="pos",
        import_path="app.modules.pos.router_crud",
        priority=ModulePriority.STANDARD,
        description="Point de vente"
    ),
    ModuleDefinition(
        name="mobile",
        import_path="app.modules.mobile.router_crud",
        priority=ModulePriority.STANDARD,
        description="App mobile, préférences"
    ),
    ModuleDefinition(
        name="web",
        import_path="app.modules.web.router_crud",
        priority=ModulePriority.STANDARD,
        description="Pages, thèmes, widgets"
    ),
    ModuleDefinition(
        name="website",
        import_path="app.modules.website.router_crud",
        priority=ModulePriority.STANDARD,
        description="Site web, CMS"
    ),

    # -------------------------------------------------------------------------
    # MODULES STANDARD (P2) - IA & Enrichissement
    # -------------------------------------------------------------------------
    ModuleDefinition(
        name="enrichment",
        import_path="app.modules.enrichment.router",
        priority=ModulePriority.STANDARD,
        description="Enrichissement données, APIs externes"
    ),
    ModuleDefinition(
        name="marceau",
        import_path="app.modules.marceau.router_crud",
        priority=ModulePriority.STANDARD,
        description="Assistant IA, mémoire, knowledge"
    ),
    ModuleDefinition(
        name="ai_assistant",
        import_path="app.modules.ai_assistant.router_crud",
        priority=ModulePriority.STANDARD,
        description="Assistant IA générique"
    ),
    ModuleDefinition(
        name="guardian",
        import_path="app.modules.guardian.router_crud",
        priority=ModulePriority.STANDARD,
        description="Monitoring, alertes, incidents"
    ),

    # -------------------------------------------------------------------------
    # MODULES OPTIONNELS (P3) - Qualité & Analytique
    # -------------------------------------------------------------------------
    ModuleDefinition(
        name="quality",
        import_path="app.modules.quality.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Contrôle qualité, non-conformités"
    ),
    ModuleDefinition(
        name="qc",
        import_path="app.modules.qc.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Quality Control"
    ),
    ModuleDefinition(
        name="bi",
        import_path="app.modules.bi.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Business Intelligence, rapports"
    ),
    ModuleDefinition(
        name="field_service",
        import_path="app.modules.field_service.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Interventions terrain avancées"
    ),
    ModuleDefinition(
        name="procurement",
        import_path="app.modules.procurement.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Approvisionnement"
    ),

    # -------------------------------------------------------------------------
    # MODULES OPTIONNELS (P3) - Automatisation & Integration
    # -------------------------------------------------------------------------
    ModuleDefinition(
        name="triggers",
        import_path="app.modules.triggers.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Automatisations, workflows"
    ),
    ModuleDefinition(
        name="autoconfig",
        import_path="app.modules.autoconfig.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Configuration automatique"
    ),
    ModuleDefinition(
        name="broadcast",
        import_path="app.modules.broadcast.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Diffusion, notifications"
    ),
    ModuleDefinition(
        name="email",
        import_path="app.modules.email.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Gestion emails"
    ),

    # -------------------------------------------------------------------------
    # MODULES OPTIONNELS (P3) - E-Commerce & Paiements
    # -------------------------------------------------------------------------
    ModuleDefinition(
        name="ecommerce",
        import_path="app.modules.ecommerce.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Boutique en ligne"
    ),
    ModuleDefinition(
        name="marketplace",
        import_path="app.modules.marketplace.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Extensions, modules tiers"
    ),
    ModuleDefinition(
        name="stripe_integration",
        import_path="app.modules.stripe_integration.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Paiements Stripe"
    ),

    # -------------------------------------------------------------------------
    # MODULES OPTIONNELS (P3) - Localisation & Import
    # -------------------------------------------------------------------------
    ModuleDefinition(
        name="country_packs",
        import_path="app.modules.country_packs.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Localisations fiscales"
    ),
    ModuleDefinition(
        name="odoo_import",
        import_path="app.modules.odoo_import.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Import depuis Odoo"
    ),
    ModuleDefinition(
        name="automated_accounting",
        import_path="app.modules.automated_accounting.router_crud",
        priority=ModulePriority.OPTIONAL,
        description="Comptabilité automatisée"
    ),

    # -------------------------------------------------------------------------
    # MODULES RÉACTIVÉS (anciennement désactivés)
    # -------------------------------------------------------------------------
    ModuleDefinition(
        name="appointments",
        import_path="app.modules.appointments.router",
        priority=ModulePriority.STANDARD,
        description="Rendez-vous, agenda, planification"
    ),
    ModuleDefinition(
        name="consolidation",
        import_path="app.modules.consolidation.router",
        priority=ModulePriority.OPTIONAL,
        description="Consolidation comptable multi-entités"
    ),
    ModuleDefinition(
        name="contracts",
        import_path="app.modules.contracts.router",
        priority=ModulePriority.STANDARD,
        description="Gestion des contrats"
    ),
    ModuleDefinition(
        name="currency",
        import_path="app.modules.currency.router",
        priority=ModulePriority.OPTIONAL,
        description="Gestion des devises et taux de change"
    ),
    ModuleDefinition(
        name="dashboards",
        import_path="app.modules.dashboards.router",
        priority=ModulePriority.STANDARD,
        description="Tableaux de bord personnalisables"
    ),
    ModuleDefinition(
        name="integrations",
        import_path="app.modules.integrations.router",
        priority=ModulePriority.OPTIONAL,
        description="Intégrations tierces"
    ),
    ModuleDefinition(
        name="manufacturing",
        import_path="app.modules.manufacturing.router",
        priority=ModulePriority.IMPORTANT,
        description="Fabrication, GPAO, ordres de production"
    ),
    ModuleDefinition(
        name="resources",
        import_path="app.modules.resources.router",
        priority=ModulePriority.OPTIONAL,
        description="Gestion des ressources"
    ),
    ModuleDefinition(
        name="shipping",
        import_path="app.modules.shipping.router",
        priority=ModulePriority.STANDARD,
        description="Expédition, livraison, transporteurs"
    ),
]


# =============================================================================
# CLASSE DE CHARGEMENT
# =============================================================================

class ModuleLoader:
    """
    Chargeur de modules avec gestion des erreurs et métriques.

    Cette classe implémente le pattern de chargement sécurisé des modules
    avec logging structuré et métriques d'observabilité.

    Attributes:
        router: Router parent FastAPI
        metrics: Métriques de chargement
        strict_mode: Si True, lève une exception si un module CRITICAL échoue

    Example:
        >>> loader = ModuleLoader(router, strict_mode=True)
        >>> loader.load_all(MODULE_REGISTRY)
        >>> print(loader.metrics)
    """

    def __init__(self, router: APIRouter, strict_mode: bool = False):
        """
        Initialise le chargeur de modules.

        Args:
            router: Router FastAPI parent où monter les sous-routers
            strict_mode: Si True, bloque le démarrage si module CRITICAL absent
        """
        self.router = router
        self.strict_mode = strict_mode
        self.metrics = RegistryMetrics()
        self._results: List[LoadResult] = []

    def load_module(self, module_def: ModuleDefinition) -> LoadResult:
        """
        Charge un module individuel de manière sécurisée.

        Args:
            module_def: Définition du module à charger

        Returns:
            LoadResult avec le statut du chargement
        """
        start_time = time.perf_counter()

        try:
            # Import dynamique du module
            module = import_module(module_def.import_path)

            # Récupération du router
            if not hasattr(module, module_def.router_attr):
                raise AttributeError(
                    f"Module '{module_def.import_path}' has no attribute '{module_def.router_attr}'"
                )

            module_router = getattr(module, module_def.router_attr)

            # Validation du type
            if not isinstance(module_router, APIRouter):
                raise TypeError(
                    f"Expected APIRouter, got {type(module_router).__name__}"
                )

            # Montage du router
            self.router.include_router(module_router)

            load_time_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "[V3] Module loaded: %s (%s) - %.1fms",
                module_def.name,
                module_def.priority.value,
                load_time_ms
            )

            return LoadResult(
                success=True,
                module_name=module_def.name,
                priority=module_def.priority,
                load_time_ms=load_time_ms
            )

        except ImportError as e:
            load_time_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Import failed: {e}"

            self._log_failure(module_def, error_msg)

            return LoadResult(
                success=False,
                module_name=module_def.name,
                priority=module_def.priority,
                error=error_msg,
                load_time_ms=load_time_ms
            )

        except Exception as e:
            load_time_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"{type(e).__name__}: {e}"

            self._log_failure(module_def, error_msg)

            return LoadResult(
                success=False,
                module_name=module_def.name,
                priority=module_def.priority,
                error=error_msg,
                load_time_ms=load_time_ms
            )

    def _log_failure(self, module_def: ModuleDefinition, error: str) -> None:
        """Log l'échec de chargement avec le niveau approprié."""
        if module_def.priority == ModulePriority.CRITICAL:
            logger.error(
                "[V3] CRITICAL module failed: %s - %s",
                module_def.name,
                error
            )
        elif module_def.priority == ModulePriority.IMPORTANT:
            logger.warning(
                "[V3] Module unavailable: %s - %s",
                module_def.name,
                error
            )
        else:
            logger.debug(
                "[V3] Optional module skipped: %s - %s",
                module_def.name,
                error
            )

    def load_all(self, modules: List[ModuleDefinition]) -> RegistryMetrics:
        """
        Charge tous les modules du registre.

        Args:
            modules: Liste des définitions de modules

        Returns:
            Métriques de chargement

        Raises:
            RuntimeError: En mode strict, si un module CRITICAL échoue
        """
        self.metrics = RegistryMetrics(total_modules=len(modules))
        self._results = []

        start_time = time.perf_counter()

        for module_def in modules:
            result = self.load_module(module_def)
            self._results.append(result)

            # Mise à jour des métriques
            priority_key = result.priority.value

            if result.success:
                self.metrics.loaded_modules += 1
                self.metrics.loaded_by_priority[priority_key] = \
                    self.metrics.loaded_by_priority.get(priority_key, 0) + 1
            else:
                self.metrics.failed_modules += 1
                self.metrics.failed_by_priority[priority_key] = \
                    self.metrics.failed_by_priority.get(priority_key, 0) + 1

                if result.priority == ModulePriority.CRITICAL:
                    self.metrics.critical_failures += 1

        self.metrics.total_load_time_ms = (time.perf_counter() - start_time) * 1000

        # Validation mode strict
        if self.strict_mode and self.metrics.critical_failures > 0:
            failed_critical = [
                r.module_name for r in self._results
                if not r.success and r.priority == ModulePriority.CRITICAL
            ]
            raise RuntimeError(
                f"[V3] CRITICAL modules failed to load in strict mode: {failed_critical}"
            )

        # Log récapitulatif
        logger.info(
            "[V3] Registry loaded: %d/%d modules in %.1fms "
            "(critical: %d, failures: %d)",
            self.metrics.loaded_modules,
            self.metrics.total_modules,
            self.metrics.total_load_time_ms,
            self.metrics.loaded_by_priority.get("critical", 0),
            self.metrics.failed_modules
        )

        return self.metrics

    @property
    def results(self) -> List[LoadResult]:
        """Retourne les résultats de chargement détaillés."""
        return self._results.copy()


# =============================================================================
# ROUTER V3 PRINCIPAL
# =============================================================================

router = APIRouter(tags=["API V3"])

# Chargement des modules
# Note: strict_mode=False pour rétrocompatibilité
# En production, activer strict_mode=True via variable d'environnement
_loader = ModuleLoader(router, strict_mode=False)
_metrics = _loader.load_all(MODULE_REGISTRY)


# =============================================================================
# ENDPOINTS SYSTÈME
# =============================================================================

@router.get("/api/status", tags=["System"])
async def get_v3_status() -> Dict:
    """
    Retourne le statut de l'API V3 et les métriques de chargement.

    Cet endpoint est utilisé pour :
    - Healthcheck de l'API V3
    - Monitoring des modules chargés
    - Audit de conformité (AZA-FE-007)

    Returns:
        Dict contenant version, statut, modules et métriques
    """
    return {
        "api_version": "v3",
        "status": "active",
        "modules": {
            "total": _metrics.total_modules,
            "loaded": _metrics.loaded_modules,
            "failed": _metrics.failed_modules,
            "critical_failures": _metrics.critical_failures,
        },
        "loaded_by_priority": _metrics.loaded_by_priority,
        "failed_by_priority": _metrics.failed_by_priority,
        "load_time_ms": round(_metrics.total_load_time_ms, 2),
        "conformity": {
            "AZA-NF-003": "Modules subordonnés au noyau",
            "AZA-BE-003": "Contrat backend obligatoire",
            "AZA-API-003": "Versioning explicite v3",
            "AZA-FE-007": "Auditabilité permanente"
        }
    }


@router.get("/api/modules", tags=["System"])
async def list_modules() -> Dict:
    """
    Liste détaillée de tous les modules du registre.

    Retourne pour chaque module :
    - Nom et description
    - Priorité
    - Statut de chargement
    - Erreur éventuelle

    Returns:
        Dict avec la liste complète des modules
    """
    modules_list = []

    for result in _loader.results:
        # Trouver la définition correspondante
        module_def = next(
            (m for m in MODULE_REGISTRY if m.name == result.module_name),
            None
        )

        modules_list.append({
            "name": result.module_name,
            "description": module_def.description if module_def else "",
            "priority": result.priority.value,
            "loaded": result.success,
            "error": result.error,
            "load_time_ms": round(result.load_time_ms, 2)
        })

    return {
        "total": len(modules_list),
        "modules": modules_list
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "router",
    "ModulePriority",
    "ModuleDefinition",
    "ModuleLoader",
    "MODULE_REGISTRY",
    "_metrics",
    "_loader",
]
