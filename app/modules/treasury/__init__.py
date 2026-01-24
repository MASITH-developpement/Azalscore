"""
AZALS MODULE - TREASURY (Trésorerie)
=====================================

Module métier complet pour la gestion de la trésorerie.

Fonctionnalités :
- Comptes bancaires (IBAN, BIC, soldes)
- Transactions bancaires (crédit/débit)
- Rapprochement bancaire (lier transactions aux documents)
- Prévisions de trésorerie
- Alertes de trésorerie
"""

__version__ = "1.0.0"
__module_code__ = "TREASURY"
__module_name__ = "Treasury - Gestion de la Trésorerie"
__dependencies__ = ["T0", "T2", "Finance", "Accounting"]

# Types de comptes bancaires
ACCOUNT_TYPES = {
    "CURRENT": "Compte courant",
    "SAVINGS": "Compte épargne",
    "TERM_DEPOSIT": "Dépôt à terme",
    "CREDIT_LINE": "Ligne de crédit",
}

# États des transactions
TRANSACTION_TYPES = [
    "credit",  # Crédit (encaissement)
    "debit",   # Débit (décaissement)
]

# États de rapprochement
RECONCILIATION_STATUS = [
    "pending",      # En attente de rapprochement
    "reconciled",   # Rapproché
    "ignored",      # Ignoré (non rapprochable)
]

# Catégories de transactions (si automatiques)
TRANSACTION_CATEGORIES = {
    "INVOICE_PAYMENT": "Paiement facture client",
    "SUPPLIER_PAYMENT": "Paiement fournisseur",
    "SALARY": "Salaire",
    "TAX": "Impôts et taxes",
    "LOAN": "Prêt/Emprunt",
    "BANK_FEES": "Frais bancaires",
    "OTHER": "Autre",
}
