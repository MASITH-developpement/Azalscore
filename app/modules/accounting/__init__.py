"""
AZALS MODULE - ACCOUNTING (Comptabilité)
=========================================

Module métier complet pour la gestion comptable.

Fonctionnalités :
- Plan comptable (Chart of Accounts)
- Écritures comptables (Journal Entries)
- Grand livre (General Ledger)
- Balance (Trial Balance)
- États financiers (Bilan, Compte de résultat)
- Exercices comptables (Fiscal Years)
"""

__version__ = "1.0.0"
__module_code__ = "ACCOUNTING"
__module_name__ = "Accounting - Comptabilité Générale"
__dependencies__ = ["T0", "T2", "Finance"]

# Types de journaux comptables
JOURNAL_TYPES = {
    "VT": "Ventes",
    "AC": "Achats",
    "BQ": "Banque",
    "CA": "Caisse",
    "OD": "Opérations diverses",
    "AN": "À-nouveaux",
}

# Catégories de comptes (Plan Comptable Français)
ACCOUNT_CATEGORIES = {
    "1": "Capitaux",
    "2": "Immobilisations",
    "3": "Stocks",
    "4": "Tiers",
    "5": "Financiers",
    "6": "Charges",
    "7": "Produits",
    "8": "Comptes spéciaux",
}

# États des exercices comptables
FISCAL_YEAR_STATUS = [
    "OPEN",      # Exercice ouvert (saisie autorisée)
    "CLOSED",    # Exercice clôturé (saisie interdite)
    "ARCHIVED",  # Exercice archivé
]

# États des écritures
ENTRY_STATUS = [
    "DRAFT",      # Brouillon (modifiable)
    "POSTED",     # Comptabilisée (validée)
    "VALIDATED",  # Validée définitivement
    "CANCELLED",  # Annulée
]
