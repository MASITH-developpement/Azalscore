"""
AZALS MODULE GAMIFICATION - Exceptions
======================================

Exceptions specifiques au module de gamification.
"""
from __future__ import annotations


from typing import Any


class GamificationError(Exception):
    """Exception de base pour le module gamification."""

    def __init__(self, message: str, code: str = "GAMIFICATION_ERROR", details: dict[str, Any] | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# =============================================================================
# EXCEPTIONS PROFIL
# =============================================================================

class ProfileNotFoundError(GamificationError):
    """Profil de gamification non trouve."""

    def __init__(self, user_id: str | None = None):
        message = "Profil de gamification non trouve"
        if user_id:
            message = f"Profil de gamification non trouve pour l'utilisateur {user_id}"
        super().__init__(message, "PROFILE_NOT_FOUND", {"user_id": user_id})


class ProfileAlreadyExistsError(GamificationError):
    """Profil de gamification deja existant."""

    def __init__(self, user_id: str | None = None):
        message = "Un profil de gamification existe deja pour cet utilisateur"
        super().__init__(message, "PROFILE_ALREADY_EXISTS", {"user_id": user_id})


# =============================================================================
# EXCEPTIONS POINTS
# =============================================================================

class InsufficientPointsError(GamificationError):
    """Points insuffisants pour l'operation."""

    def __init__(self, required: int, available: int, point_type: str = "points"):
        message = f"Points insuffisants: {available} {point_type} disponibles, {required} requis"
        super().__init__(
            message,
            "INSUFFICIENT_POINTS",
            {"required": required, "available": available, "point_type": point_type}
        )


class InvalidPointAmountError(GamificationError):
    """Montant de points invalide."""

    def __init__(self, amount: int):
        message = f"Montant de points invalide: {amount}"
        super().__init__(message, "INVALID_POINT_AMOUNT", {"amount": amount})


class PointsExpiredError(GamificationError):
    """Points expires."""

    def __init__(self, transaction_id: str | None = None):
        message = "Les points ont expire"
        super().__init__(message, "POINTS_EXPIRED", {"transaction_id": transaction_id})


class DailyPointLimitExceededError(GamificationError):
    """Limite journaliere de points depassee."""

    def __init__(self, limit: int, current: int):
        message = f"Limite journaliere de points depassee: {current}/{limit}"
        super().__init__(message, "DAILY_POINT_LIMIT_EXCEEDED", {"limit": limit, "current": current})


# =============================================================================
# EXCEPTIONS BADGES
# =============================================================================

class BadgeNotFoundError(GamificationError):
    """Badge non trouve."""

    def __init__(self, badge_id: str | None = None, code: str | None = None):
        identifier = badge_id or code or "inconnu"
        message = f"Badge non trouve: {identifier}"
        super().__init__(message, "BADGE_NOT_FOUND", {"badge_id": badge_id, "code": code})


class BadgeAlreadyUnlockedError(GamificationError):
    """Badge deja debloque."""

    def __init__(self, badge_id: str, user_id: str):
        message = "Ce badge a deja ete debloque"
        super().__init__(message, "BADGE_ALREADY_UNLOCKED", {"badge_id": badge_id, "user_id": user_id})


class BadgeNotAvailableError(GamificationError):
    """Badge non disponible."""

    def __init__(self, badge_id: str, reason: str = ""):
        message = f"Badge non disponible"
        if reason:
            message += f": {reason}"
        super().__init__(message, "BADGE_NOT_AVAILABLE", {"badge_id": badge_id, "reason": reason})


class BadgeLimitReachedError(GamificationError):
    """Limite de detenteurs du badge atteinte."""

    def __init__(self, badge_id: str, max_holders: int):
        message = f"Le nombre maximum de detenteurs pour ce badge a ete atteint ({max_holders})"
        super().__init__(message, "BADGE_LIMIT_REACHED", {"badge_id": badge_id, "max_holders": max_holders})


class BadgeCategoryNotFoundError(GamificationError):
    """Categorie de badge non trouvee."""

    def __init__(self, category_id: str | None = None):
        message = "Categorie de badge non trouvee"
        super().__init__(message, "BADGE_CATEGORY_NOT_FOUND", {"category_id": category_id})


# =============================================================================
# EXCEPTIONS DEFIS
# =============================================================================

class ChallengeNotFoundError(GamificationError):
    """Defi non trouve."""

    def __init__(self, challenge_id: str | None = None, code: str | None = None):
        identifier = challenge_id or code or "inconnu"
        message = f"Defi non trouve: {identifier}"
        super().__init__(message, "CHALLENGE_NOT_FOUND", {"challenge_id": challenge_id, "code": code})


class ChallengeNotActiveError(GamificationError):
    """Defi non actif."""

    def __init__(self, challenge_id: str, status: str):
        message = f"Le defi n'est pas actif (statut: {status})"
        super().__init__(message, "CHALLENGE_NOT_ACTIVE", {"challenge_id": challenge_id, "status": status})


class ChallengeFullError(GamificationError):
    """Defi complet."""

    def __init__(self, challenge_id: str, max_participants: int):
        message = f"Le defi a atteint son nombre maximum de participants ({max_participants})"
        super().__init__(
            message,
            "CHALLENGE_FULL",
            {"challenge_id": challenge_id, "max_participants": max_participants}
        )


class AlreadyJoinedChallengeError(GamificationError):
    """Deja inscrit au defi."""

    def __init__(self, challenge_id: str, user_id: str):
        message = "Vous etes deja inscrit a ce defi"
        super().__init__(message, "ALREADY_JOINED_CHALLENGE", {"challenge_id": challenge_id, "user_id": user_id})


class ChallengeNotJoinedError(GamificationError):
    """Non inscrit au defi."""

    def __init__(self, challenge_id: str, user_id: str):
        message = "Vous n'etes pas inscrit a ce defi"
        super().__init__(message, "CHALLENGE_NOT_JOINED", {"challenge_id": challenge_id, "user_id": user_id})


class RewardsAlreadyClaimedError(GamificationError):
    """Recompenses deja reclamees."""

    def __init__(self, challenge_id: str):
        message = "Les recompenses de ce defi ont deja ete reclamees"
        super().__init__(message, "REWARDS_ALREADY_CLAIMED", {"challenge_id": challenge_id})


class ChallengeNotCompletedError(GamificationError):
    """Defi non complete."""

    def __init__(self, challenge_id: str, progress: int, target: int):
        message = f"Le defi n'est pas encore complete ({progress}/{target})"
        super().__init__(
            message,
            "CHALLENGE_NOT_COMPLETED",
            {"challenge_id": challenge_id, "progress": progress, "target": target}
        )


class RegistrationClosedError(GamificationError):
    """Inscriptions fermees."""

    def __init__(self, challenge_id: str):
        message = "Les inscriptions pour ce defi sont fermees"
        super().__init__(message, "REGISTRATION_CLOSED", {"challenge_id": challenge_id})


# =============================================================================
# EXCEPTIONS RECOMPENSES
# =============================================================================

class RewardNotFoundError(GamificationError):
    """Recompense non trouvee."""

    def __init__(self, reward_id: str | None = None, code: str | None = None):
        identifier = reward_id or code or "inconnu"
        message = f"Recompense non trouvee: {identifier}"
        super().__init__(message, "REWARD_NOT_FOUND", {"reward_id": reward_id, "code": code})


class RewardNotAvailableError(GamificationError):
    """Recompense non disponible."""

    def __init__(self, reward_id: str, reason: str = ""):
        message = "Recompense non disponible"
        if reason:
            message += f": {reason}"
        super().__init__(message, "REWARD_NOT_AVAILABLE", {"reward_id": reward_id, "reason": reason})


class RewardOutOfStockError(GamificationError):
    """Recompense en rupture de stock."""

    def __init__(self, reward_id: str):
        message = "Cette recompense n'est plus disponible (rupture de stock)"
        super().__init__(message, "REWARD_OUT_OF_STOCK", {"reward_id": reward_id})


class RewardLimitReachedError(GamificationError):
    """Limite de reclamation atteinte."""

    def __init__(self, reward_id: str, limit_type: str, limit: int):
        message = f"Limite de reclamation atteinte ({limit_type}: {limit})"
        super().__init__(
            message,
            "REWARD_LIMIT_REACHED",
            {"reward_id": reward_id, "limit_type": limit_type, "limit": limit}
        )


class LevelRequirementNotMetError(GamificationError):
    """Niveau requis non atteint."""

    def __init__(self, required_level: int, current_level: int):
        message = f"Niveau {required_level} requis (niveau actuel: {current_level})"
        super().__init__(
            message,
            "LEVEL_REQUIREMENT_NOT_MET",
            {"required_level": required_level, "current_level": current_level}
        )


class ClaimNotFoundError(GamificationError):
    """Reclamation non trouvee."""

    def __init__(self, claim_id: str | None = None):
        message = "Reclamation non trouvee"
        super().__init__(message, "CLAIM_NOT_FOUND", {"claim_id": claim_id})


class ClaimStatusError(GamificationError):
    """Statut de reclamation invalide pour l'operation."""

    def __init__(self, claim_id: str, current_status: str, expected_status: str | list[str]):
        message = f"Operation impossible: statut actuel '{current_status}'"
        if isinstance(expected_status, list):
            message += f", attendu: {', '.join(expected_status)}"
        else:
            message += f", attendu: {expected_status}"
        super().__init__(
            message,
            "CLAIM_STATUS_ERROR",
            {"claim_id": claim_id, "current_status": current_status, "expected_status": expected_status}
        )


# =============================================================================
# EXCEPTIONS REGLES
# =============================================================================

class RuleNotFoundError(GamificationError):
    """Regle non trouvee."""

    def __init__(self, rule_id: str | None = None, code: str | None = None):
        identifier = rule_id or code or "inconnu"
        message = f"Regle non trouvee: {identifier}"
        super().__init__(message, "RULE_NOT_FOUND", {"rule_id": rule_id, "code": code})


class RuleTriggerError(GamificationError):
    """Erreur lors du declenchement d'une regle."""

    def __init__(self, rule_id: str, error: str):
        message = f"Erreur lors du declenchement de la regle: {error}"
        super().__init__(message, "RULE_TRIGGER_ERROR", {"rule_id": rule_id, "error": error})


class RuleCooldownError(GamificationError):
    """Regle en cooldown."""

    def __init__(self, rule_id: str, remaining_minutes: int):
        message = f"Cette regle ne peut pas etre declenchee avant {remaining_minutes} minutes"
        super().__init__(
            message,
            "RULE_COOLDOWN_ERROR",
            {"rule_id": rule_id, "remaining_minutes": remaining_minutes}
        )


class RuleConditionError(GamificationError):
    """Conditions de la regle non remplies."""

    def __init__(self, rule_id: str, condition: str):
        message = f"Les conditions de la regle ne sont pas remplies: {condition}"
        super().__init__(message, "RULE_CONDITION_ERROR", {"rule_id": rule_id, "condition": condition})


# =============================================================================
# EXCEPTIONS EQUIPES
# =============================================================================

class TeamNotFoundError(GamificationError):
    """Equipe non trouvee."""

    def __init__(self, team_id: str | None = None, code: str | None = None):
        identifier = team_id or code or "inconnu"
        message = f"Equipe non trouvee: {identifier}"
        super().__init__(message, "TEAM_NOT_FOUND", {"team_id": team_id, "code": code})


class TeamFullError(GamificationError):
    """Equipe complete."""

    def __init__(self, team_id: str, max_members: int):
        message = f"L'equipe a atteint son nombre maximum de membres ({max_members})"
        super().__init__(message, "TEAM_FULL", {"team_id": team_id, "max_members": max_members})


class AlreadyInTeamError(GamificationError):
    """Deja membre d'une equipe."""

    def __init__(self, user_id: str, current_team_id: str | None = None):
        message = "Vous etes deja membre d'une equipe"
        super().__init__(message, "ALREADY_IN_TEAM", {"user_id": user_id, "current_team_id": current_team_id})


class NotTeamMemberError(GamificationError):
    """Non membre de l'equipe."""

    def __init__(self, user_id: str, team_id: str):
        message = "Vous n'etes pas membre de cette equipe"
        super().__init__(message, "NOT_TEAM_MEMBER", {"user_id": user_id, "team_id": team_id})


class NotTeamCaptainError(GamificationError):
    """Non capitaine de l'equipe."""

    def __init__(self, user_id: str, team_id: str):
        message = "Vous n'etes pas le capitaine de cette equipe"
        super().__init__(message, "NOT_TEAM_CAPTAIN", {"user_id": user_id, "team_id": team_id})


class CannotLeaveAsLastMemberError(GamificationError):
    """Impossible de quitter en tant que dernier membre."""

    def __init__(self, team_id: str):
        message = "Vous ne pouvez pas quitter l'equipe en etant le dernier membre. Supprimez l'equipe a la place."
        super().__init__(message, "CANNOT_LEAVE_AS_LAST_MEMBER", {"team_id": team_id})


# =============================================================================
# EXCEPTIONS COMPETITIONS
# =============================================================================

class CompetitionNotFoundError(GamificationError):
    """Competition non trouvee."""

    def __init__(self, competition_id: str | None = None, code: str | None = None):
        identifier = competition_id or code or "inconnu"
        message = f"Competition non trouvee: {identifier}"
        super().__init__(message, "COMPETITION_NOT_FOUND", {"competition_id": competition_id, "code": code})


class CompetitionNotOpenError(GamificationError):
    """Competition non ouverte aux inscriptions."""

    def __init__(self, competition_id: str, status: str):
        message = f"La competition n'est pas ouverte aux inscriptions (statut: {status})"
        super().__init__(message, "COMPETITION_NOT_OPEN", {"competition_id": competition_id, "status": status})


class AlreadyRegisteredError(GamificationError):
    """Deja inscrit a la competition."""

    def __init__(self, competition_id: str, participant_id: str):
        message = "Vous etes deja inscrit a cette competition"
        super().__init__(
            message,
            "ALREADY_REGISTERED",
            {"competition_id": competition_id, "participant_id": participant_id}
        )


class CompetitionFullError(GamificationError):
    """Competition complete."""

    def __init__(self, competition_id: str, max_participants: int):
        message = f"La competition a atteint son nombre maximum de participants ({max_participants})"
        super().__init__(
            message,
            "COMPETITION_FULL",
            {"competition_id": competition_id, "max_participants": max_participants}
        )


# =============================================================================
# EXCEPTIONS LEADERBOARD
# =============================================================================

class LeaderboardNotFoundError(GamificationError):
    """Classement non trouve."""

    def __init__(self, leaderboard_id: str | None = None, code: str | None = None):
        identifier = leaderboard_id or code or "inconnu"
        message = f"Classement non trouve: {identifier}"
        super().__init__(message, "LEADERBOARD_NOT_FOUND", {"leaderboard_id": leaderboard_id, "code": code})


# =============================================================================
# EXCEPTIONS NIVEAUX
# =============================================================================

class LevelNotFoundError(GamificationError):
    """Niveau non trouve."""

    def __init__(self, level_number: int | None = None, level_id: str | None = None):
        identifier = str(level_number) if level_number else level_id or "inconnu"
        message = f"Niveau non trouve: {identifier}"
        super().__init__(message, "LEVEL_NOT_FOUND", {"level_number": level_number, "level_id": level_id})


class InvalidLevelConfigError(GamificationError):
    """Configuration de niveau invalide."""

    def __init__(self, error: str):
        message = f"Configuration de niveau invalide: {error}"
        super().__init__(message, "INVALID_LEVEL_CONFIG", {"error": error})


# =============================================================================
# EXCEPTIONS CONFIGURATION
# =============================================================================

class ConfigNotFoundError(GamificationError):
    """Configuration non trouvee."""

    def __init__(self, tenant_id: str):
        message = f"Configuration de gamification non trouvee pour le tenant {tenant_id}"
        super().__init__(message, "CONFIG_NOT_FOUND", {"tenant_id": tenant_id})


class FeatureDisabledError(GamificationError):
    """Fonctionnalite desactivee."""

    def __init__(self, feature: str):
        message = f"La fonctionnalite '{feature}' est desactivee"
        super().__init__(message, "FEATURE_DISABLED", {"feature": feature})


# =============================================================================
# EXCEPTIONS GENERIQUES
# =============================================================================

class DuplicateCodeError(GamificationError):
    """Code deja existant."""

    def __init__(self, entity_type: str, code: str):
        message = f"Un(e) {entity_type} avec le code '{code}' existe deja"
        super().__init__(message, "DUPLICATE_CODE", {"entity_type": entity_type, "code": code})


class InvalidStateError(GamificationError):
    """Etat invalide pour l'operation."""

    def __init__(self, entity_type: str, current_state: str, operation: str):
        message = f"Impossible d'effectuer '{operation}' sur {entity_type} dans l'etat '{current_state}'"
        super().__init__(
            message,
            "INVALID_STATE",
            {"entity_type": entity_type, "current_state": current_state, "operation": operation}
        )


class PermissionDeniedError(GamificationError):
    """Permission refusee."""

    def __init__(self, action: str, reason: str = ""):
        message = f"Permission refusee pour l'action '{action}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, "PERMISSION_DENIED", {"action": action, "reason": reason})


class RateLimitError(GamificationError):
    """Limite de taux atteinte."""

    def __init__(self, limit_type: str, limit: int, window: str):
        message = f"Limite atteinte: {limit} {limit_type} par {window}"
        super().__init__(
            message,
            "RATE_LIMIT_ERROR",
            {"limit_type": limit_type, "limit": limit, "window": window}
        )
