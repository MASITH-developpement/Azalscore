"""
AZALS MODULE T9 - Gestion des Tenants (Clients)
================================================

Module de provisioning et gestion des clients multi-tenant:
- Création et configuration de tenants
- Initialisation des données par défaut
- Activation des modules
- Gestion des abonnements
- Premier client: SAS MASITH

Version: 1.0.0
"""

__version__ = "1.0.0"
__module_code__ = "T9"
__module_name__ = "Gestion des Tenants"
__module_type__ = "TRANSVERSE"
__dependencies__ = ["T0", "T5"]

# Statuts de tenant
TENANT_STATUS = [
    "PENDING",
    "ACTIVE",
    "SUSPENDED",
    "CANCELLED",
    "TRIAL",
]

# Plans d'abonnement
SUBSCRIPTION_PLANS = [
    "STARTER",
    "PROFESSIONAL",
    "ENTERPRISE",
    "CUSTOM",
]

# Modules disponibles
AVAILABLE_MODULES = [
    "T0",  # IAM
    "T1",  # Autoconfig
    "T2",  # Triggers
    "T3",  # Audit
    "T4",  # QC
    "T5",  # Country Packs
    "T6",  # Broadcast
    "T7",  # Web
    "T8",  # Website
    "M1",  # Trésorerie
    "M2",  # Comptabilité
    "M3",  # Fiscalité
    "M4",  # RH/Paie
    "M5",  # Ventes
    "M6",  # Achats
    "M7",  # Stock
    "M8",  # Production
    "M9",  # Logistique
    "M10", # Qualité
    "M11", # Juridique
]

# Premier client
FIRST_TENANT = {
    "id": "masith",
    "name": "SAS MASITH",
    "plan": "ENTERPRISE",
    "country": "FR",
}
