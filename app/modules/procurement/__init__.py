"""
AZALS MODULE M4 - ACHATS (Procurement)
======================================

Module métier complet pour la gestion des achats :
- Fournisseurs et contacts
- Demandes d'achat (requisitions)
- Devis fournisseurs
- Commandes d'achat
- Réceptions de marchandises
- Factures d'achat
- Évaluations fournisseurs
- Contrats d'approvisionnement

Version: 1.0.0
Dépendances: T0 (IAM), T5 (Packs Pays), M2 (Finance), M5 (Stock)
"""

__version__ = "1.0.0"
__module_code__ = "M4"
__module_name__ = "Achats - Procurement"
__dependencies__ = ["T0", "T5", "M2"]

# Statuts fournisseur
SUPPLIER_STATUSES = [
    "PROSPECT",       # Prospect
    "PENDING",        # En attente validation
    "APPROVED",       # Approuvé
    "BLOCKED",        # Bloqué
    "INACTIVE",       # Inactif
]

# Types de fournisseur
SUPPLIER_TYPES = [
    "MANUFACTURER",   # Fabricant
    "DISTRIBUTOR",    # Distributeur
    "SERVICE",        # Service
    "FREELANCE",      # Indépendant
    "OTHER",          # Autre
]

# Statuts demande d'achat
REQUISITION_STATUSES = [
    "DRAFT",          # Brouillon
    "SUBMITTED",      # Soumise
    "APPROVED",       # Approuvée
    "REJECTED",       # Rejetée
    "ORDERED",        # Commandée
    "CANCELLED",      # Annulée
]

# Statuts commande d'achat
PURCHASE_ORDER_STATUSES = [
    "DRAFT",          # Brouillon
    "SENT",           # Envoyée
    "CONFIRMED",      # Confirmée
    "PARTIAL",        # Partiellement reçue
    "RECEIVED",       # Reçue
    "INVOICED",       # Facturée
    "CANCELLED",      # Annulée
]

# Statuts réception
RECEIVING_STATUSES = [
    "DRAFT",          # Brouillon
    "VALIDATED",      # Validée
    "CANCELLED",      # Annulée
]

# Statuts facture d'achat
PURCHASE_INVOICE_STATUSES = [
    "DRAFT",          # Brouillon
    "VALIDATED",      # Validée
    "PAID",           # Payée
    "PARTIAL",        # Partiellement payée
    "CANCELLED",      # Annulée
]

# Statuts devis fournisseur
QUOTATION_STATUSES = [
    "REQUESTED",      # Demandé
    "RECEIVED",       # Reçu
    "ACCEPTED",       # Accepté
    "REJECTED",       # Rejeté
    "EXPIRED",        # Expiré
]

# Types de paiement fournisseur
PAYMENT_TERMS = [
    {"code": "IMMEDIATE", "name": "Paiement immédiat", "days": 0},
    {"code": "NET15", "name": "Net 15 jours", "days": 15},
    {"code": "NET30", "name": "Net 30 jours", "days": 30},
    {"code": "NET45", "name": "Net 45 jours", "days": 45},
    {"code": "NET60", "name": "Net 60 jours", "days": 60},
    {"code": "EOM", "name": "Fin de mois", "days": 30},
    {"code": "EOM15", "name": "Fin de mois + 15", "days": 45},
    {"code": "EOM30", "name": "Fin de mois + 30", "days": 60},
]

# Catégories d'achat
PURCHASE_CATEGORIES = [
    {"code": "RAW_MATERIALS", "name": "Matières premières"},
    {"code": "COMPONENTS", "name": "Composants"},
    {"code": "PACKAGING", "name": "Emballages"},
    {"code": "EQUIPMENT", "name": "Équipements"},
    {"code": "SERVICES", "name": "Services"},
    {"code": "CONSUMABLES", "name": "Consommables"},
    {"code": "MAINTENANCE", "name": "Maintenance"},
    {"code": "IT", "name": "Informatique"},
    {"code": "MARKETING", "name": "Marketing"},
    {"code": "OTHER", "name": "Autres"},
]

# Critères d'évaluation fournisseur
EVALUATION_CRITERIA = [
    {"code": "QUALITY", "name": "Qualité", "weight": 25},
    {"code": "PRICE", "name": "Prix", "weight": 25},
    {"code": "DELIVERY", "name": "Délais de livraison", "weight": 20},
    {"code": "SERVICE", "name": "Service client", "weight": 15},
    {"code": "RELIABILITY", "name": "Fiabilité", "weight": 15},
]
