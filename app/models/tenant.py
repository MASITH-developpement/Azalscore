"""
AZALS - Modèle Tenant
Représente une organisation/entreprise isolée
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from app.core.database import Base


class Tenant(Base):
    """
    Table des tenants (organisations/entreprises).
    Point central de l'isolation multi-tenant.
    """
    __tablename__ = 'tenants'
    
    # ID alphanumérique lisible (ex: "acme-corp")
    id = Column(String(255), primary_key=True, index=True)
    
    # Nom commercial du tenant
    name = Column(String(255), nullable=False)
    
    # Tenant actif ou désactivé
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Métadonnées temporelles
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, active={self.is_active})>"
