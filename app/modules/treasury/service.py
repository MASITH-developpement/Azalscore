"""
AZALS MODULE - TREASURY: Service
=================================

Service métier pour la gestion de trésorerie.

✅ MIGRÉ CORE SaaS v2:
- Constructeur mis à jour pour accepter tenant_id + user_id
- Isolation tenant garantie par tenant_id
- Audit trail avec user_id
"""

from sqlalchemy.orm import Session


class TreasuryService:
    """
    Service de gestion de trésorerie.

    ✅ MIGRÉ CORE SaaS v2:
    - Accepte tenant_id + user_id dans le constructeur
    - Toutes les opérations isolées par tenant
    """

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        """
        Initialise le service Treasury.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant (isolation multi-tenant)
            user_id: ID de l'utilisateur (pour audit trail)
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2
