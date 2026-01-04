"""
AZALS MODULE M2 - FINANCE (Comptabilité + Trésorerie)
======================================================

Module métier complet pour la gestion financière :
- Plan comptable et comptes
- Écritures comptables
- Journaux comptables
- Exercices fiscaux et clôtures
- Trésorerie et prévisions
- Rapprochement bancaire
- Reporting financier

Version: 1.0.0
Dépendances: T0 (IAM), T5 (Packs Pays), M1 (Commercial)
"""

__version__ = "1.0.0"
__module_code__ = "M2"
__module_name__ = "Finance - Comptabilité & Trésorerie"
__dependencies__ = ["T0", "T5", "M1"]

# Classes de comptes
ACCOUNT_CLASSES = [
    {"code": "1", "name": "Comptes de capitaux"},
    {"code": "2", "name": "Comptes d'immobilisations"},
    {"code": "3", "name": "Comptes de stocks"},
    {"code": "4", "name": "Comptes de tiers"},
    {"code": "5", "name": "Comptes financiers"},
    {"code": "6", "name": "Comptes de charges"},
    {"code": "7", "name": "Comptes de produits"},
]

# Types de journaux
JOURNAL_TYPES = [
    "GENERAL",       # Journal général
    "PURCHASES",     # Achats
    "SALES",         # Ventes
    "BANK",          # Banque
    "CASH",          # Caisse
    "OD",            # Opérations diverses
    "OPENING",       # À nouveau
    "CLOSING",       # Clôture
]

# Statuts d'écriture
ENTRY_STATUSES = [
    "DRAFT",         # Brouillon
    "PENDING",       # En attente de validation
    "VALIDATED",     # Validé
    "POSTED",        # Comptabilisé
    "CANCELLED",     # Annulé
]

# Types de transactions bancaires
BANK_TRANSACTION_TYPES = [
    "CREDIT",        # Crédit (encaissement)
    "DEBIT",         # Débit (décaissement)
    "TRANSFER",      # Virement interne
    "FEE",           # Frais bancaires
    "INTEREST",      # Intérêts
]

# Statuts d'exercice
FISCAL_YEAR_STATUSES = [
    "OPEN",          # Ouvert
    "CLOSING",       # En cours de clôture
    "CLOSED",        # Clôturé
]

# Périodes de trésorerie
FORECAST_PERIODS = [
    "DAILY",         # Quotidien
    "WEEKLY",        # Hebdomadaire
    "MONTHLY",       # Mensuel
    "QUARTERLY",     # Trimestriel
]

# Plan comptable français simplifié (comptes principaux)
PCG_ACCOUNTS = [
    # Classe 1 - Capitaux
    {"code": "101000", "name": "Capital social", "type": "EQUITY"},
    {"code": "106000", "name": "Réserves", "type": "EQUITY"},
    {"code": "120000", "name": "Résultat de l'exercice (bénéfice)", "type": "EQUITY"},
    {"code": "129000", "name": "Résultat de l'exercice (perte)", "type": "EQUITY"},
    # Classe 2 - Immobilisations
    {"code": "211000", "name": "Terrains", "type": "ASSET"},
    {"code": "213000", "name": "Constructions", "type": "ASSET"},
    {"code": "215000", "name": "Matériel et outillage", "type": "ASSET"},
    {"code": "218000", "name": "Autres immobilisations", "type": "ASSET"},
    # Classe 4 - Tiers
    {"code": "401000", "name": "Fournisseurs", "type": "LIABILITY"},
    {"code": "411000", "name": "Clients", "type": "ASSET"},
    {"code": "421000", "name": "Personnel - Rémunérations dues", "type": "LIABILITY"},
    {"code": "431000", "name": "Sécurité sociale", "type": "LIABILITY"},
    {"code": "445100", "name": "TVA à décaisser", "type": "LIABILITY"},
    {"code": "445660", "name": "TVA déductible sur biens et services", "type": "ASSET"},
    {"code": "445670", "name": "TVA collectée", "type": "LIABILITY"},
    # Classe 5 - Financiers
    {"code": "512000", "name": "Banque", "type": "ASSET"},
    {"code": "530000", "name": "Caisse", "type": "ASSET"},
    # Classe 6 - Charges
    {"code": "601000", "name": "Achats de matières premières", "type": "EXPENSE"},
    {"code": "606000", "name": "Achats non stockés", "type": "EXPENSE"},
    {"code": "607000", "name": "Achats de marchandises", "type": "EXPENSE"},
    {"code": "613000", "name": "Locations", "type": "EXPENSE"},
    {"code": "615000", "name": "Entretien et réparations", "type": "EXPENSE"},
    {"code": "616000", "name": "Assurances", "type": "EXPENSE"},
    {"code": "622000", "name": "Honoraires", "type": "EXPENSE"},
    {"code": "626000", "name": "Frais postaux et télécoms", "type": "EXPENSE"},
    {"code": "627000", "name": "Services bancaires", "type": "EXPENSE"},
    {"code": "641000", "name": "Rémunérations du personnel", "type": "EXPENSE"},
    {"code": "645000", "name": "Charges sociales", "type": "EXPENSE"},
    {"code": "681000", "name": "Dotations aux amortissements", "type": "EXPENSE"},
    # Classe 7 - Produits
    {"code": "701000", "name": "Ventes de produits finis", "type": "REVENUE"},
    {"code": "706000", "name": "Prestations de services", "type": "REVENUE"},
    {"code": "707000", "name": "Ventes de marchandises", "type": "REVENUE"},
    {"code": "708000", "name": "Produits des activités annexes", "type": "REVENUE"},
    {"code": "761000", "name": "Produits financiers", "type": "REVENUE"},
]
