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
    # Technique
    "T0",  # IAM
    "T1",  # Autoconfig
    "T2",  # Triggers
    "T3",  # Audit
    "T4",  # QC
    "T5",  # Country Packs
    "T6",  # Broadcast
    "T7",  # Web
    "T8",  # Website
    # Métier
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
    # Import de Données
    "IMP1",  # Odoo Import
    "IMP2",  # Axonaut Import
    "IMP3",  # Pennylane Import
    "IMP4",  # Sage Import
    "IMP5",  # Chorus Import
]

# Informations détaillées des modules
MODULE_DETAILS = {
    # Technique
    "T0": {"name": "IAM", "description": "Gestion des identités et accès", "category": "Technique"},
    "T1": {"name": "AutoConfig", "description": "Configuration automatique", "category": "Technique"},
    "T2": {"name": "Triggers", "description": "Déclencheurs et automatisations", "category": "Technique"},
    "T3": {"name": "Audit", "description": "Journal d'audit", "category": "Technique"},
    "T4": {"name": "QC", "description": "Contrôle qualité", "category": "Technique"},
    "T5": {"name": "Country Packs", "description": "Packs pays", "category": "Technique"},
    "T6": {"name": "Broadcast", "description": "Diffusion", "category": "Technique"},
    "T7": {"name": "Web", "description": "Services web", "category": "Technique"},
    "T8": {"name": "Website", "description": "Site web", "category": "Technique"},
    # Métier
    "M1": {"name": "Trésorerie", "description": "Gestion de trésorerie", "category": "Métier"},
    "M2": {"name": "Comptabilité", "description": "Comptabilité générale", "category": "Métier"},
    "M3": {"name": "Fiscalité", "description": "Gestion fiscale", "category": "Métier"},
    "M4": {"name": "RH/Paie", "description": "Ressources humaines et paie", "category": "Métier"},
    "M5": {"name": "Ventes", "description": "Gestion commerciale", "category": "Métier"},
    "M6": {"name": "Achats", "description": "Gestion des achats", "category": "Métier"},
    "M7": {"name": "Stock", "description": "Gestion des stocks", "category": "Métier"},
    "M8": {"name": "Production", "description": "Gestion de production", "category": "Métier"},
    "M9": {"name": "Logistique", "description": "Logistique et transport", "category": "Métier"},
    "M10": {"name": "Qualité", "description": "Gestion qualité", "category": "Métier"},
    "M11": {"name": "Juridique", "description": "Gestion juridique", "category": "Métier"},
    # Import de Données
    "IMP1": {"name": "Import Odoo", "description": "Import de données depuis Odoo (versions 8-18)", "category": "Import de Données"},
    "IMP2": {"name": "Import Axonaut", "description": "Import de données depuis Axonaut", "category": "Import de Données"},
    "IMP3": {"name": "Import Pennylane", "description": "Import de données depuis Pennylane", "category": "Import de Données"},
    "IMP4": {"name": "Import Sage", "description": "Import de données depuis Sage", "category": "Import de Données"},
    "IMP5": {"name": "Import Chorus", "description": "Import de données depuis Chorus Pro", "category": "Import de Données"},
}

# Premier client
FIRST_TENANT = {
    "id": "masith",
    "name": "SAS MASITH",
    "plan": "ENTERPRISE",
    "country": "FR",
}
