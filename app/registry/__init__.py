"""
Registry AZALSCORE - Bibliothèque centrale de sous-programmes

Conformité : AZA-NF-003, AZA-RT-001
"""

from .loader import RegistryLoader, load_program, list_programs

__all__ = ["RegistryLoader", "load_program", "list_programs"]
