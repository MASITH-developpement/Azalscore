"""
AZALS - Service Journal APPEND-ONLY
Gestion du journal d'audit inaltérable
"""


from sqlalchemy.orm import Session

from app.core.models import CoreAuditJournal


class JournalService:
    """
    Service d'écriture dans le journal APPEND-ONLY.
    Garantit la traçabilité de toutes les actions critiques.
    """

    @staticmethod
    def write(
        db: Session,
        tenant_id: str,
        user_id: int,
        action: str,
        details: str | None = None
    ) -> CoreAuditJournal:
        """
        Écrit une entrée dans le journal.
        Seule opération autorisée : INSERT.

        Args:
            db: Session SQLAlchemy
            tenant_id: Identifiant du tenant
            user_id: Identifiant de l'utilisateur
            action: Action tracée (ex: "USER_LOGIN", "ITEM_CREATED")
            details: Détails optionnels (JSON stringifié recommandé)

        Returns:
            CoreAuditJournal créée
        """
        entry = CoreAuditJournal(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            details=details
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def read_tenant_entries(
        db: Session,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[CoreAuditJournal]:
        """
        Lit les entrées du journal pour un tenant.
        Filtrage strict par tenant_id.

        Args:
            db: Session SQLAlchemy
            tenant_id: Identifiant du tenant
            limit: Nombre max d'entrées (défaut 100)
            offset: Offset pour pagination

        Returns:
            Liste des entrées du journal
        """
        return db.query(CoreAuditJournal)\
            .filter(CoreAuditJournal.tenant_id == tenant_id)\
            .order_by(CoreAuditJournal.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
