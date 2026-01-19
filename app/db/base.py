"""
AZALS - Base ORM Unifiée
========================
Base SQLAlchemy avec UUIDMixin intégré.
TOUS les modèles doivent hériter de cette Base.

RÈGLE NON NÉGOCIABLE:
- Hériter UNIQUEMENT de Base (pas de declarative_base() manuel)
- NE JAMAIS redéfinir 'id' manuellement
- NE JAMAIS utiliser Integer/BigInteger pour les identifiants

Usage correct:
    from app.db import Base

    class MyModel(Base):
        __tablename__ = "my_table"
        name: Mapped[Optional[str]] = mapped_column(String(255))
        # id est automatiquement UUID

Usage INTERDIT:
    from sqlalchemy.orm import declarative_base, Mapped, mapped_column
    Base = declarative_base()  # INTERDIT

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # INTERDIT
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # INTERDIT
"""

from sqlalchemy.orm import declarative_base

from app.db.uuid_base import UUIDMixin


class _UUIDDeclarativeBase:
    """
    Classe de base interne combinant les fonctionnalités SQLAlchemy
    avec le mixin UUID obligatoire.

    __allow_unmapped__ permet d'utiliser Column() sans Mapped[] pour
    compatibilité avec le code existant.
    """
    __allow_unmapped__ = True


# Base unifiée avec UUIDMixin intégré
# TOUS les modèles héritent automatiquement de UUIDMixin
Base = declarative_base(cls=(UUIDMixin, _UUIDDeclarativeBase))


def get_base():
    """
    Retourne la Base unifiée.
    Utilisé pour les imports dynamiques.
    """
    return Base
