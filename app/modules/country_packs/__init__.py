"""
AZALS MODULE T5 - Packs Pays
=============================

Module de configuration par pays pour l'ERP AZALS.
Gère les localisations, règles fiscales, formats légaux et bancaires.
"""

__version__ = "1.0.0"
__module_code__ = "T5"
__module_name__ = "Packs Pays"
__dependencies__ = ["T0"]  # IAM pour permissions

MODULE_INFO = {
    "code": __module_code__,
    "name": __module_name__,
    "version": __version__,
    "description": "Configurations spécifiques par pays (fiscal, légal, bancaire)",
    "author": "AZALS Team",
    "dependencies": __dependencies__,
}

# Pays supportés par défaut
SUPPORTED_COUNTRIES = [
    "FR",  # France
    "MA",  # Maroc
    "SN",  # Sénégal
    "CI",  # Côte d'Ivoire
    "CM",  # Cameroun
    "TN",  # Tunisie
    "DZ",  # Algérie
    "BE",  # Belgique
    "CH",  # Suisse
    "LU",  # Luxembourg
    "CA",  # Canada
]
