"""
AZALSCORE - Base Exporter
Classe de base abstraite pour les exporters
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseExporter(ABC):
    """Classe de base pour les exporters"""

    @abstractmethod
    def export(self, data: list[dict], options: dict) -> bytes:
        """Exporte les données vers le format cible"""
        pass
