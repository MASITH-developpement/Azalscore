"""
AZALS - Modèle de base multi-tenant
Tous les modèles doivent hériter de TenantMixin
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import declared_attr


class TenantMixin:
    """
    Mixin obligatoire pour tous les modèles métier.
    Garantit que chaque entité appartient à un tenant.
    """

    @declared_attr
    def tenant_id(cls):
        """Clé étrangère obligatoire vers tenants.id"""
        return Column(
            String(255),
            ForeignKey('tenants.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        )

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )
