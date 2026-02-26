"""
AZALSCORE - Base Parser
Classe de base abstraite pour les parsers
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generator


class BaseParser(ABC):
    """Classe de base pour les parsers"""

    @abstractmethod
    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        """Parse le contenu et génère des enregistrements"""
        pass

    @abstractmethod
    def get_headers(self, content: bytes, options: dict) -> list[str]:
        """Retourne les en-têtes du fichier"""
        pass
