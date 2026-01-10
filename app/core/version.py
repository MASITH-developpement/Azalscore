"""
AZALS - Version Canonique
==========================
SOURCE DE VERITE UNIQUE pour la version de l'application.

REGLES ABSOLUES:
----------------
- Sur branche 'develop': AZALS_VERSION = "X.Y.Z-dev"
- Sur branche 'main':    AZALS_VERSION = "X.Y.Z-prod"

CETTE VERSION NE DOIT JAMAIS ETRE CALCULEE DYNAMIQUEMENT.
Elle est la reference unique pour tous les composants de l'application.

PROCESSUS DE RELEASE:
--------------------
1. Sur develop: version "X.Y.Z-dev" (developpement)
2. Merge vers main: modifier en "X.Y.Z-prod" AVANT le merge
3. Apres merge: incrementer sur develop vers "X.Y+1.Z-dev"

SECURITE:
---------
- En production (main), seules les versions "-prod" sont autorisees
- Toute version "-dev" en production provoque un CRASH IMMEDIAT
"""

# =============================================================================
# VERSION CANONIQUE - NE JAMAIS MODIFIER DYNAMIQUEMENT
# =============================================================================

AZALS_VERSION = "0.0.0-dev"

# =============================================================================
# CONSTANTES DE VERSION
# =============================================================================

# Suffixes autorises
VERSION_SUFFIX_DEV = "-dev"
VERSION_SUFFIX_PROD = "-prod"

# Branches correspondantes
BRANCH_DEVELOP = "develop"
BRANCH_MAIN = "main"


def is_dev_version() -> bool:
    """Retourne True si la version est une version de developpement."""
    return AZALS_VERSION.endswith(VERSION_SUFFIX_DEV)


def is_prod_version() -> bool:
    """Retourne True si la version est une version de production."""
    return AZALS_VERSION.endswith(VERSION_SUFFIX_PROD)


def get_version_base() -> str:
    """Retourne la version sans le suffixe (ex: '0.0.0')."""
    version = AZALS_VERSION
    if version.endswith(VERSION_SUFFIX_DEV):
        return version[:-len(VERSION_SUFFIX_DEV)]
    if version.endswith(VERSION_SUFFIX_PROD):
        return version[:-len(VERSION_SUFFIX_PROD)]
    return version


def get_version_suffix() -> str:
    """Retourne le suffixe de la version ('-dev' ou '-prod')."""
    if AZALS_VERSION.endswith(VERSION_SUFFIX_DEV):
        return VERSION_SUFFIX_DEV
    if AZALS_VERSION.endswith(VERSION_SUFFIX_PROD):
        return VERSION_SUFFIX_PROD
    return ""


def get_version_info() -> dict:
    """Retourne un dictionnaire avec toutes les informations de version."""
    return {
        "version": AZALS_VERSION,
        "base": get_version_base(),
        "suffix": get_version_suffix(),
        "is_dev": is_dev_version(),
        "is_prod": is_prod_version(),
    }
