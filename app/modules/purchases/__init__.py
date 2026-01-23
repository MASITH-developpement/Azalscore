"""
AZALS MODULE M4 - PURCHASES (Achats)
====================================

Module métier complet pour la gestion des achats :
- Fournisseurs (Suppliers)
- Commandes d'achat (Purchase Orders)
- Réception de marchandises
- Factures fournisseurs (Purchase Invoices)
- Suivi des paiements fournisseurs

Version: 1.0.0
Dépendances: T0 (IAM), T2 (Triggers), Finance
"""

__version__ = "1.0.0"
__module_code__ = "M4"
__module_name__ = "Purchases - Gestion des Achats"
__dependencies__ = ["T0", "T2", "Finance"]

# Statuts fournisseurs
SUPPLIER_STATUSES = [
    "PROSPECT",      # Prospect fournisseur
    "PENDING",       # En attente d'approbation
    "APPROVED",      # Approuvé et actif
    "BLOCKED",       # Bloqué temporairement
    "INACTIVE",      # Inactif
]

# Statuts commandes d'achat
ORDER_STATUSES = [
    "DRAFT",         # Brouillon
    "PENDING",       # En attente validation
    "APPROVED",      # Approuvée
    "SENT",          # Envoyée au fournisseur
    "CONFIRMED",     # Confirmée par fournisseur
    "RECEIVED",      # Marchandises reçues
    "INVOICED",      # Facturée
    "CANCELLED",     # Annulée
]

# Statuts factures fournisseurs
INVOICE_STATUSES = [
    "DRAFT",         # Brouillon
    "PENDING",       # En attente validation
    "VALIDATED",     # Validée
    "PAID",          # Payée
    "PARTIALLY_PAID",# Partiellement payée
    "OVERDUE",       # En retard
    "CANCELLED",     # Annulée
]

# Types de fournisseurs
SUPPLIER_TYPES = [
    "GOODS",         # Marchandises
    "SERVICES",      # Services
    "BOTH",          # Marchandises et services
    "RAW_MATERIALS", # Matières premières
    "EQUIPMENT",     # Équipements
]

# Conditions de paiement fournisseurs
PAYMENT_TERMS = [
    "IMMEDIATE",     # Paiement immédiat
    "NET_15",        # Net 15 jours
    "NET_30",        # Net 30 jours
    "NET_45",        # Net 45 jours
    "NET_60",        # Net 60 jours
    "NET_90",        # Net 90 jours
    "END_OF_MONTH",  # Fin de mois
    "CUSTOM",        # Personnalisé
]

# Méthodes de paiement fournisseurs
PAYMENT_METHODS = [
    "BANK_TRANSFER", # Virement bancaire
    "CHECK",         # Chèque
    "CREDIT_CARD",   # Carte de crédit
    "CASH",          # Espèces
    "DIRECT_DEBIT",  # Prélèvement
    "LC",            # Lettre de crédit
    "OTHER",         # Autre
]

# Devises supportées
CURRENCIES = [
    "EUR",           # Euro
    "USD",           # Dollar US
    "GBP",           # Livre Sterling
    "CHF",           # Franc Suisse
    "JPY",           # Yen
    "CAD",           # Dollar Canadien
]

# Unités de mesure
UNITS_OF_MEASURE = [
    "UNIT",          # Unité
    "KG",            # Kilogramme
    "LITER",         # Litre
    "METER",         # Mètre
    "HOUR",          # Heure
    "DAY",           # Jour
    "BOX",           # Carton
    "PALLET",        # Palette
]
