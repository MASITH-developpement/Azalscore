"""
AZALS MODULE M1 - COMMERCIAL (CRM + Ventes)
============================================

Module métier complet pour la gestion commerciale :
- CRM (Clients, Prospects, Contacts)
- Opportunités commerciales (Pipeline)
- Devis et propositions
- Commandes clients
- Facturation
- Relances et recouvrement

Version: 1.0.0
Dépendances: T0 (IAM), T2 (Triggers), T5 (Packs Pays)
"""

__version__ = "1.0.0"
__module_code__ = "M1"
__module_name__ = "Commercial - CRM & Ventes"
__dependencies__ = ["T0", "T2", "T5"]

# Types de clients
CUSTOMER_TYPES = [
    "PROSPECT",      # Prospect non qualifié
    "LEAD",          # Lead qualifié
    "CUSTOMER",      # Client actif
    "VIP",           # Client VIP
    "PARTNER",       # Partenaire commercial
    "CHURNED",       # Client perdu
]

# Statuts opportunités
OPPORTUNITY_STATUSES = [
    "NEW",           # Nouvelle opportunité
    "QUALIFIED",     # Qualifiée
    "PROPOSAL",      # Proposition envoyée
    "NEGOTIATION",   # En négociation
    "WON",           # Gagnée
    "LOST",          # Perdue
]

# Types de documents
DOCUMENT_TYPES = [
    "QUOTE",         # Devis
    "ORDER",         # Commande
    "INVOICE",       # Facture
    "CREDIT_NOTE",   # Avoir
    "PROFORMA",      # Facture proforma
    "DELIVERY",      # Bon de livraison
]

# Statuts documents
DOCUMENT_STATUSES = [
    "DRAFT",         # Brouillon
    "PENDING",       # En attente validation
    "VALIDATED",     # Validé
    "SENT",          # Envoyé au client
    "ACCEPTED",      # Accepté (devis)
    "REJECTED",      # Rejeté (devis)
    "DELIVERED",     # Livré
    "INVOICED",      # Facturé
    "PAID",          # Payé
    "CANCELLED",     # Annulé
]

# Méthodes de paiement
PAYMENT_METHODS = [
    "BANK_TRANSFER", # Virement bancaire
    "CHECK",         # Chèque
    "CREDIT_CARD",   # Carte de crédit
    "CASH",          # Espèces
    "DIRECT_DEBIT",  # Prélèvement
    "PAYPAL",        # PayPal
    "OTHER",         # Autre
]

# Conditions de paiement
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

# Étapes du pipeline par défaut
DEFAULT_PIPELINE_STAGES = [
    {"order": 1, "name": "Nouveau", "probability": 10},
    {"order": 2, "name": "Qualifié", "probability": 25},
    {"order": 3, "name": "Proposition", "probability": 50},
    {"order": 4, "name": "Négociation", "probability": 75},
    {"order": 5, "name": "Gagné", "probability": 100},
    {"order": 6, "name": "Perdu", "probability": 0},
]
