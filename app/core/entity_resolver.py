"""
AZALSCORE Core - Entity Resolver (AZA-NF-003)
==============================================

Service centralisé de résolution d'entités inter-modules.

Ce module respecte l'invariant NF-003 : les modules ne communiquent
PAS directement entre eux. Toute résolution d'entité cross-module
passe par ce resolver centralisé (couche noyau).

Usage:
    resolver = EntityResolver(db, tenant_id)
    name, code = resolver.resolve_client(client_id)
    name = resolver.resolve_employee(employee_id)
"""
from __future__ import annotations


import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EntityResolver:
    """
    Résolution centralisée d'entités cross-modules.

    Conforme AZA-NF-003 : pas de communication inter-modules directe.
    Les modules utilisent ce resolver (couche noyau) pour obtenir
    des données d'autres modules.
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # MODULE COMMERCIAL
    # ========================================================================

    def resolve_client(self, client_id: Any) -> tuple[str | None, str | None]:
        """
        Résout nom + code d'un client depuis le module commercial.

        Returns:
            (name, code) ou (None, None) si non trouvé.
        """
        if not client_id:
            return None, None
        try:
            from app.modules.commercial.models import Customer
            c = self.db.query(Customer).filter(
                Customer.id == client_id,
                Customer.tenant_id == self.tenant_id,
            ).first()
            if c:
                return getattr(c, "name", None), getattr(c, "code", None)
        except Exception as e:
            logger.warning(
                "[ENTITY_RESOLVER] Échec résolution client %s: %s",
                client_id, str(e)[:200],
            )
        return None, None

    def resolve_client_address(self, client_id: Any) -> dict | None:
        """
        Résout l'adresse d'un client depuis le module commercial.

        Returns:
            Dict avec adresse_ligne1, adresse_ligne2, ville, code_postal
            ou None si non trouvé.
        """
        if not client_id:
            return None
        try:
            from app.modules.commercial.models import Customer
            c = self.db.query(Customer).filter(
                Customer.id == client_id,
                Customer.tenant_id == self.tenant_id,
            ).first()
            if c:
                return {
                    "adresse_ligne1": getattr(c, "address_line1", None),
                    "adresse_ligne2": getattr(c, "address_line2", None),
                    "ville": getattr(c, "city", None),
                    "code_postal": getattr(c, "postal_code", None),
                }
        except Exception as e:
            logger.warning(
                "[ENTITY_RESOLVER] Échec résolution adresse client %s: %s",
                client_id, str(e)[:200],
            )
        return None

    # ========================================================================
    # MODULE RH
    # ========================================================================

    def resolve_employee(self, employee_id: Any) -> str | None:
        """
        Résout le nom complet d'un employé depuis le module RH.

        Returns:
            Nom complet (prénom nom) ou None si non trouvé.
        """
        if not employee_id:
            return None
        try:
            from app.modules.hr.models import Employee
            e = self.db.query(Employee).filter(
                Employee.id == employee_id,
                Employee.tenant_id == self.tenant_id,
            ).first()
            if e:
                first = getattr(e, "first_name", "") or ""
                last = getattr(e, "last_name", "") or ""
                return f"{first} {last}".strip() or None
        except Exception as e:
            logger.warning(
                "[ENTITY_RESOLVER] Échec résolution employé %s: %s",
                employee_id, str(e)[:200],
            )
        return None
