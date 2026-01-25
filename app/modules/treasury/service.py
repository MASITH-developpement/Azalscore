"""
AZALS MODULE - TREASURY: Service
=================================

Service métier pour la gestion de trésorerie.
"""

from sqlalchemy.orm import Session


class TreasuryService:
    """Service de gestion de trésorerie (stub minimal)"""

    def __init__(self, db: Session):
        self.db = db
