"""
AZALS MODULE T6 - Diffusion d'Information Périodique
=====================================================

Module transverse pour la diffusion automatique d'informations:
- Newsletters et digests
- Rapports périodiques
- Alertes programmées
- Multi-canal (email, PDF, webhook)

Version: 1.0.0
"""

__version__ = "1.0.0"
__module_code__ = "T6"
__module_name__ = "Diffusion d'Information Périodique"
__module_type__ = "TRANSVERSE"
__dependencies__ = ["T0", "T2", "T5"]

# Canaux de diffusion supportés
DELIVERY_CHANNELS = [
    "EMAIL",
    "IN_APP",
    "WEBHOOK",
    "PDF_DOWNLOAD",
    "SMS",
]

# Fréquences de diffusion
BROADCAST_FREQUENCIES = [
    "ONCE",        # Une seule fois
    "DAILY",       # Quotidien
    "WEEKLY",      # Hebdomadaire
    "BIWEEKLY",    # Bi-hebdomadaire
    "MONTHLY",     # Mensuel
    "QUARTERLY",   # Trimestriel
    "YEARLY",      # Annuel
    "CUSTOM",      # Expression cron personnalisée
]

# Types de contenu
CONTENT_TYPES = [
    "DIGEST",      # Résumé automatique
    "NEWSLETTER",  # Newsletter éditée
    "REPORT",      # Rapport généré
    "ALERT",       # Alerte périodique
    "KPI_SUMMARY", # Résumé KPIs
]
