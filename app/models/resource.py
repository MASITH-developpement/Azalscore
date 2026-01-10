"""
AZALS - Modèle Resource
Exemple de ressource métier isolée par tenant
"""

import uuid

from sqlalchemy import String, Text

from app.db import Base
from app.core.types import UniversalUUID
from app.models.base import TenantMixin
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional


class Resource(Base, TenantMixin):
    """
    Exemple de ressource métier strictement isolée par tenant.
    Toute ressource appartient à un et un seul tenant.
    """
    __tablename__ = 'resources'

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)

    # Nom de la ressource
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<Resource(id={self.id}, tenant_id={self.tenant_id}, name={self.name})>"
