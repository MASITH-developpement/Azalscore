"""
AZALS MODULE T4 - Contrôle Qualité Central (QC)
================================================

Module de contrôle qualité central pour valider tous les modules AZALS.
Fournit validation automatique, scoring, checks, dashboards QC.
"""

__version__ = "1.0.0"
__module_code__ = "T4"
__module_name__ = "Contrôle Qualité Central"
__dependencies__ = ["T0", "T3"]  # IAM pour permissions, Audit pour logs

MODULE_INFO = {
    "code": __module_code__,
    "name": __module_name__,
    "version": __version__,
    "description": "Système de contrôle qualité central pour validation des modules",
    "author": "AZALS Team",
    "dependencies": __dependencies__,
}
