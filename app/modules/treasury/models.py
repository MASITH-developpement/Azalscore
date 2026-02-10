"""
AZALS MODULE - TREASURY: Models
================================

Modèles pour la gestion de trésorerie.
"""

from enum import Enum


class AccountType(str, Enum):
    """Types de comptes bancaires"""
    CURRENT = "CURRENT"  # Compte courant
    SAVINGS = "SAVINGS"  # Compte épargne
    INVESTMENT = "INVESTMENT"  # Compte d'investissement
    LOAN = "LOAN"  # Compte de prêt


class TransactionType(str, Enum):
    """Types de transactions"""
    CREDIT = "CREDIT"  # Crédit (entrée)
    DEBIT = "DEBIT"  # Débit (sortie)
