"""
AZALS - Modèle Resource
Exemple de ressource métier isolée par tenant
"""

import uuid

from sqlalchemy import Column, String, Text

from app.core.database import Base
from app.core.types import UniversalUUID
from app.models.base import TenantMixin


class Resource(Base, TenantMixin):
    """
    Exemple de ressource métier strictement isolée par tenant.
    Toute ressource appartient à un et un seul tenant.
    """
    __tablename__ = 'resources'

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)

    # Nom de la ressource
    name = Column(String(255), nullable=False, index=True)

    # Description
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Resource(id={self.id}, tenant_id={self.tenant_id}, name={self.name})>"
