"""
Exceptions métier Referral / Parrainage
========================================
"""


class ReferralError(Exception):
    """Exception de base du module Referral."""
    pass


# ============== Program Exceptions ==============

class ProgramNotFoundError(ReferralError):
    """Programme non trouvé."""
    pass


class ProgramDuplicateError(ReferralError):
    """Code programme déjà existant."""
    pass


class ProgramValidationError(ReferralError):
    """Erreur de validation programme."""
    pass


class ProgramStateError(ReferralError):
    """Transition d'état programme invalide."""
    pass


class ProgramBudgetExceededError(ReferralError):
    """Budget du programme dépassé."""
    pass


class ProgramLimitReachedError(ReferralError):
    """Limite de parrainages du programme atteinte."""
    pass


# ============== RewardTier Exceptions ==============

class RewardTierNotFoundError(ReferralError):
    """Palier de récompense non trouvé."""
    pass


class RewardTierValidationError(ReferralError):
    """Erreur de validation palier."""
    pass


# ============== ReferralCode Exceptions ==============

class ReferralCodeNotFoundError(ReferralError):
    """Code de parrainage non trouvé."""
    pass


class ReferralCodeDuplicateError(ReferralError):
    """Code de parrainage déjà existant."""
    pass


class ReferralCodeExpiredError(ReferralError):
    """Code de parrainage expiré."""
    pass


class ReferralCodeLimitReachedError(ReferralError):
    """Limite d'utilisation du code atteinte."""
    pass


class ReferralCodeInactiveError(ReferralError):
    """Code de parrainage inactif."""
    pass


# ============== Referral Exceptions ==============

class ReferralNotFoundError(ReferralError):
    """Parrainage non trouvé."""
    pass


class ReferralValidationError(ReferralError):
    """Erreur de validation parrainage."""
    pass


class ReferralStateError(ReferralError):
    """Transition d'état parrainage invalide."""
    pass


class ReferralExpiredError(ReferralError):
    """Parrainage expiré."""
    pass


class SelfReferralError(ReferralError):
    """Auto-parrainage non autorisé."""
    pass


class DuplicateRefereeError(ReferralError):
    """Filleul déjà parrainé."""
    pass


# ============== Reward Exceptions ==============

class RewardNotFoundError(ReferralError):
    """Récompense non trouvée."""
    pass


class RewardValidationError(ReferralError):
    """Erreur de validation récompense."""
    pass


class RewardAlreadyClaimedError(ReferralError):
    """Récompense déjà réclamée."""
    pass


class RewardExpiredError(ReferralError):
    """Récompense expirée."""
    pass


# ============== Payout Exceptions ==============

class PayoutNotFoundError(ReferralError):
    """Paiement non trouvé."""
    pass


class PayoutValidationError(ReferralError):
    """Erreur de validation paiement."""
    pass


class PayoutStateError(ReferralError):
    """Transition d'état paiement invalide."""
    pass


class PayoutMinimumNotReachedError(ReferralError):
    """Montant minimum de paiement non atteint."""
    pass


# ============== Fraud Exceptions ==============

class FraudDetectedError(ReferralError):
    """Fraude détectée."""
    pass


class FraudCheckFailedError(ReferralError):
    """Vérification anti-fraude échouée."""
    pass
