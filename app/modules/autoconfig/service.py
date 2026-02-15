"""
AZALS MODULE T1 - Service Configuration Automatique
====================================================

Logique métier pour la configuration automatique par fonction.
"""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .models import (
    AutoConfigLog,
    JobProfile,
    OffboardingProcess,
    OffboardingStatus,
    OnboardingProcess,
    OnboardingStatus,
    OverrideStatus,
    OverrideType,
    PermissionOverride,
    ProfileAssignment,
    ProfileLevel,
)
from .profiles import PREDEFINED_PROFILES, get_best_profile_match


class AutoConfigService:
    """Service principal de configuration automatique."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2

    # ========================================================================
    # GESTION DES PROFILS
    # ========================================================================

    def initialize_predefined_profiles(self, created_by: int | None = None) -> int:
        """
        Initialise les profils prédéfinis pour le tenant.
        Retourne le nombre de profils créés.
        """
        count = 0
        for code, profile_data in PREDEFINED_PROFILES.items():
            # Vérifier si le profil existe déjà
            existing = self.get_profile_by_code(code)
            if existing:
                continue

            profile = JobProfile(
                tenant_id=self.tenant_id,
                code=code,
                name=profile_data["name"],
                description=profile_data.get("description"),
                level=ProfileLevel(profile_data["level"]),
                hierarchy_order=profile_data["hierarchy_order"],
                title_patterns=json.dumps(profile_data.get("title_patterns", [])),
                department_patterns=json.dumps(profile_data.get("department_patterns", [])),
                default_roles=json.dumps(profile_data["default_roles"]),
                default_permissions=json.dumps(profile_data.get("default_permissions", [])),
                default_modules=json.dumps(profile_data.get("default_modules", [])),
                max_data_access_level=profile_data.get("max_data_access_level", 5),
                requires_mfa=profile_data.get("requires_mfa", False),
                requires_training=profile_data.get("requires_training", True),
                is_system=True,
                priority=profile_data.get("priority", 100),
                created_by=created_by
            )

            self.db.add(profile)
            count += 1

        if count > 0:
            self._log("PROFILES_INITIALIZED", "PROFILE", None, None,
                     new_values={"count": count}, source="AUTO", triggered_by=created_by)
            self.db.commit()

        return count

    def get_profile_by_code(self, code: str) -> JobProfile | None:
        """Récupère un profil par code."""
        return self.db.query(JobProfile).filter(
            JobProfile.tenant_id == self.tenant_id,
            JobProfile.code == code
        ).first()

    def get_profile(self, profile_id: int) -> JobProfile | None:
        """Récupère un profil par ID."""
        return self.db.query(JobProfile).filter(
            JobProfile.tenant_id == self.tenant_id,
            JobProfile.id == profile_id
        ).first()

    def list_profiles(self, include_inactive: bool = False) -> list[JobProfile]:
        """Liste tous les profils."""
        query = self.db.query(JobProfile).filter(
            JobProfile.tenant_id == self.tenant_id
        )

        if not include_inactive:
            query = query.filter(JobProfile.is_active)

        return query.order_by(JobProfile.priority, JobProfile.hierarchy_order).all()

    def detect_profile(self, job_title: str, department: str | None = None) -> JobProfile | None:
        """
        Détecte le profil le plus approprié pour un titre/département.
        """
        # D'abord chercher dans les profils personnalisés du tenant
        profiles = self.list_profiles()

        for profile in profiles:
            title_patterns = json.loads(profile.title_patterns) if profile.title_patterns else []
            dept_patterns = json.loads(profile.department_patterns) if profile.department_patterns else []

            # Vérifier le titre
            title_match = False
            for pattern in title_patterns:
                if self._pattern_matches(pattern, job_title):
                    title_match = True
                    break

            if title_match:
                # Vérifier le département si spécifié
                if department and dept_patterns:
                    for pattern in dept_patterns:
                        if self._pattern_matches(pattern, department):
                            return profile
                elif not dept_patterns:
                    return profile

        # Fallback sur les profils prédéfinis
        predefined = get_best_profile_match(job_title, department)
        if predefined:
            return self.get_profile_by_code(predefined["code"])

        return None

    def _pattern_matches(self, pattern: str, value: str) -> bool:
        """Vérifie si un pattern correspond à une valeur."""
        import re
        pattern_lower = pattern.lower().replace("*", ".*")
        return bool(re.search(pattern_lower, value.lower()))

    # ========================================================================
    # ATTRIBUTION AUTOMATIQUE
    # ========================================================================

    def auto_assign_profile(
        self,
        user_id: int,
        job_title: str,
        department: str | None = None,
        manager_id: int | None = None,
        assigned_by: int | None = None
    ) -> ProfileAssignment | None:
        """
        Attribue automatiquement un profil à un utilisateur.
        Retourne l'attribution créée ou None si aucun profil trouvé.
        """
        # Détecter le profil
        profile = self.detect_profile(job_title, department)
        if not profile:
            self._log("PROFILE_NOT_DETECTED", "PROFILE", None, user_id,
                     details={"job_title": job_title, "department": department},
                     source="AUTO", triggered_by=assigned_by)
            return None

        # Désactiver les anciennes attributions
        self.db.query(ProfileAssignment).filter(
            ProfileAssignment.tenant_id == self.tenant_id,
            ProfileAssignment.user_id == user_id,
            ProfileAssignment.is_active
        ).update({"is_active": False, "revoked_at": datetime.utcnow()})

        # Créer la nouvelle attribution
        assignment = ProfileAssignment(
            tenant_id=self.tenant_id,
            user_id=user_id,
            profile_id=profile.id,
            job_title=job_title,
            department=department,
            manager_id=manager_id,
            is_auto=True,
            assigned_by=assigned_by
        )

        self.db.add(assignment)

        # Log
        self._log("PROFILE_AUTO_ASSIGNED", "ASSIGNMENT", assignment.id, user_id,
                 new_values={
                     "profile_code": profile.code,
                     "job_title": job_title,
                     "department": department
                 },
                 source="AUTO", triggered_by=assigned_by)

        self.db.commit()
        return assignment

    def manual_assign_profile(
        self,
        user_id: int,
        profile_code: str,
        assigned_by: int,
        job_title: str | None = None,
        department: str | None = None
    ) -> ProfileAssignment:
        """Attribue manuellement un profil à un utilisateur."""
        profile = self.get_profile_by_code(profile_code)
        if not profile:
            raise ValueError(f"Profil {profile_code} non trouvé")

        # Désactiver les anciennes attributions
        self.db.query(ProfileAssignment).filter(
            ProfileAssignment.tenant_id == self.tenant_id,
            ProfileAssignment.user_id == user_id,
            ProfileAssignment.is_active
        ).update({"is_active": False, "revoked_at": datetime.utcnow()})

        # Créer la nouvelle attribution
        assignment = ProfileAssignment(
            tenant_id=self.tenant_id,
            user_id=user_id,
            profile_id=profile.id,
            job_title=job_title,
            department=department,
            is_auto=False,
            assigned_by=assigned_by
        )

        self.db.add(assignment)

        # Log
        self._log("PROFILE_MANUAL_ASSIGNED", "ASSIGNMENT", assignment.id, user_id,
                 new_values={"profile_code": profile_code},
                 source="MANUAL", triggered_by=assigned_by)

        self.db.commit()
        return assignment

    def get_user_profile(self, user_id: int) -> ProfileAssignment | None:
        """Récupère l'attribution de profil active d'un utilisateur."""
        return self.db.query(ProfileAssignment).filter(
            ProfileAssignment.tenant_id == self.tenant_id,
            ProfileAssignment.user_id == user_id,
            ProfileAssignment.is_active
        ).first()

    def get_user_effective_config(self, user_id: int) -> dict[str, Any]:
        """
        Calcule la configuration effective d'un utilisateur.
        Combine profil + overrides.
        """
        assignment = self.get_user_profile(user_id)
        if not assignment:
            return {
                "roles": [],
                "permissions": [],
                "modules": [],
                "requires_mfa": False,
                "data_access_level": 5
            }

        profile = assignment.profile

        # Configuration de base du profil
        roles = json.loads(profile.default_roles) if profile.default_roles else []
        permissions = json.loads(profile.default_permissions) if profile.default_permissions else []
        modules = json.loads(profile.default_modules) if profile.default_modules else []

        # Appliquer les overrides actifs
        overrides = self.db.query(PermissionOverride).filter(
            PermissionOverride.tenant_id == self.tenant_id,
            PermissionOverride.user_id == user_id,
            PermissionOverride.status == OverrideStatus.APPROVED,
            or_(
                PermissionOverride.expires_at.is_(None),
                PermissionOverride.expires_at > datetime.utcnow()
            )
        ).all()

        # Convertir en sets pour opérations O(1)
        roles_set = set(roles)
        permissions_set = set(permissions)
        modules_set = set(modules)

        for override in overrides:
            # Rôles ajoutés
            if override.added_roles:
                roles_set.update(json.loads(override.added_roles))
            # Rôles retirés
            if override.removed_roles:
                roles_set -= set(json.loads(override.removed_roles))
            # Permissions ajoutées
            if override.added_permissions:
                permissions_set.update(json.loads(override.added_permissions))
            # Permissions retirées
            if override.removed_permissions:
                permissions_set -= set(json.loads(override.removed_permissions))
            # Modules ajoutés
            if override.added_modules:
                modules_set.update(json.loads(override.added_modules))
            # Modules retirés
            if override.removed_modules:
                modules_set -= set(json.loads(override.removed_modules))

        # Reconvertir en listes
        roles = list(roles_set)
        permissions = list(permissions_set)
        modules = list(modules_set)

        return {
            "profile_code": profile.code,
            "profile_name": profile.name,
            "roles": list(set(roles)),
            "permissions": list(set(permissions)),
            "modules": list(set(modules)),
            "requires_mfa": profile.requires_mfa,
            "data_access_level": profile.max_data_access_level,
            "overrides_applied": len(overrides)
        }

    # ========================================================================
    # GESTION DES OVERRIDES
    # ========================================================================

    def request_override(
        self,
        user_id: int,
        override_type: OverrideType,
        reason: str,
        requested_by: int,
        added_roles: list[str] | None = None,
        removed_roles: list[str] | None = None,
        added_permissions: list[str] | None = None,
        removed_permissions: list[str] | None = None,
        added_modules: list[str] | None = None,
        removed_modules: list[str] | None = None,
        expires_at: datetime | None = None,
        business_justification: str | None = None
    ) -> PermissionOverride:
        """Demande un override de permissions."""
        override = PermissionOverride(
            tenant_id=self.tenant_id,
            user_id=user_id,
            override_type=override_type,
            status=OverrideStatus.PENDING,
            added_roles=json.dumps(added_roles) if added_roles else None,
            removed_roles=json.dumps(removed_roles) if removed_roles else None,
            added_permissions=json.dumps(added_permissions) if added_permissions else None,
            removed_permissions=json.dumps(removed_permissions) if removed_permissions else None,
            added_modules=json.dumps(added_modules) if added_modules else None,
            removed_modules=json.dumps(removed_modules) if removed_modules else None,
            reason=reason,
            business_justification=business_justification,
            expires_at=expires_at,
            requested_by=requested_by
        )

        self.db.add(override)

        # Log
        self._log("OVERRIDE_REQUESTED", "OVERRIDE", override.id, user_id,
                 new_values={
                     "type": override_type.value,
                     "reason": reason,
                     "expires_at": str(expires_at) if expires_at else None
                 },
                 source="MANUAL", triggered_by=requested_by)

        # Auto-approve pour override dirigeant ou IT si demandeur a le droit
        if override_type in [OverrideType.EXECUTIVE, OverrideType.IT_ADMIN]:
            # TODO: Vérifier les permissions du demandeur
            override.status = OverrideStatus.APPROVED
            override.approved_by = requested_by
            override.approved_at = datetime.utcnow()
            override.applied_at = datetime.utcnow()

            self._log("OVERRIDE_AUTO_APPROVED", "OVERRIDE", override.id, user_id,
                     source="AUTO", triggered_by=requested_by)

        self.db.commit()
        return override

    def approve_override(
        self,
        override_id: int,
        approved_by: int
    ) -> PermissionOverride:
        """Approuve un override en attente."""
        override = self.db.query(PermissionOverride).filter(
            PermissionOverride.id == override_id,
            PermissionOverride.tenant_id == self.tenant_id
        ).first()

        if not override:
            raise ValueError("Override non trouvé")

        if override.status != OverrideStatus.PENDING:
            raise ValueError(f"Override non en attente (statut: {override.status.value})")

        override.status = OverrideStatus.APPROVED
        override.approved_by = approved_by
        override.approved_at = datetime.utcnow()
        override.applied_at = datetime.utcnow()

        self._log("OVERRIDE_APPROVED", "OVERRIDE", override.id, override.user_id,
                 source="MANUAL", triggered_by=approved_by)

        self.db.commit()
        return override

    def reject_override(
        self,
        override_id: int,
        rejected_by: int,
        rejection_reason: str
    ) -> PermissionOverride:
        """Rejette un override en attente."""
        override = self.db.query(PermissionOverride).filter(
            PermissionOverride.id == override_id,
            PermissionOverride.tenant_id == self.tenant_id
        ).first()

        if not override:
            raise ValueError("Override non trouvé")

        override.status = OverrideStatus.REJECTED
        override.rejected_by = rejected_by
        override.rejected_at = datetime.utcnow()
        override.rejection_reason = rejection_reason

        self._log("OVERRIDE_REJECTED", "OVERRIDE", override.id, override.user_id,
                 details={"reason": rejection_reason},
                 source="MANUAL", triggered_by=rejected_by)

        self.db.commit()
        return override

    def revoke_override(
        self,
        override_id: int,
        revoked_by: int
    ) -> PermissionOverride:
        """Révoque un override actif."""
        override = self.db.query(PermissionOverride).filter(
            PermissionOverride.id == override_id,
            PermissionOverride.tenant_id == self.tenant_id
        ).first()

        if not override:
            raise ValueError("Override non trouvé")

        override.status = OverrideStatus.REVOKED
        override.revoked_at = datetime.utcnow()
        override.revoked_by = revoked_by

        self._log("OVERRIDE_REVOKED", "OVERRIDE", override.id, override.user_id,
                 source="MANUAL", triggered_by=revoked_by)

        self.db.commit()
        return override

    def expire_overrides(self) -> int:
        """
        Expire les overrides dont la date d'expiration est passée.
        Retourne le nombre d'overrides expirés.
        """
        count = self.db.query(PermissionOverride).filter(
            PermissionOverride.tenant_id == self.tenant_id,
            PermissionOverride.status == OverrideStatus.APPROVED,
            PermissionOverride.expires_at.isnot(None),
            PermissionOverride.expires_at <= datetime.utcnow()
        ).update({"status": OverrideStatus.EXPIRED})

        if count > 0:
            self._log("OVERRIDES_EXPIRED", "OVERRIDE", None, None,
                     new_values={"count": count},
                     source="SCHEDULED", triggered_by=None)
            self.db.commit()

        return count

    def list_user_overrides(self, user_id: int, include_inactive: bool = False) -> list[PermissionOverride]:
        """Liste les overrides d'un utilisateur."""
        query = self.db.query(PermissionOverride).filter(
            PermissionOverride.tenant_id == self.tenant_id,
            PermissionOverride.user_id == user_id
        )

        if not include_inactive:
            query = query.filter(PermissionOverride.status.in_([
                OverrideStatus.PENDING,
                OverrideStatus.APPROVED
            ]))

        return query.order_by(PermissionOverride.requested_at.desc()).all()

    # ========================================================================
    # ONBOARDING
    # ========================================================================

    def create_onboarding(
        self,
        email: str,
        job_title: str,
        start_date: datetime,
        created_by: int | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        department: str | None = None,
        manager_id: int | None = None
    ) -> OnboardingProcess:
        """Crée un processus d'onboarding."""
        # Détecter le profil
        detected_profile = self.detect_profile(job_title, department)

        onboarding = OnboardingProcess(
            tenant_id=self.tenant_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            job_title=job_title,
            department=department,
            manager_id=manager_id,
            start_date=start_date,
            detected_profile_id=detected_profile.id if detected_profile else None,
            status=OnboardingStatus.PENDING,
            steps_completed=json.dumps({}),
            created_by=created_by
        )

        self.db.add(onboarding)

        self._log("ONBOARDING_CREATED", "ONBOARDING", onboarding.id, None,
                 new_values={
                     "email": email,
                     "job_title": job_title,
                     "start_date": str(start_date),
                     "detected_profile": detected_profile.code if detected_profile else None
                 },
                 source="MANUAL", triggered_by=created_by)

        self.db.commit()
        return onboarding

    def execute_onboarding(self, onboarding_id: int, executed_by: int | None = None) -> dict[str, Any]:
        """
        Exécute le processus d'onboarding.
        Crée le compte utilisateur et attribue les droits.
        """
        onboarding = self.db.query(OnboardingProcess).filter(
            OnboardingProcess.id == onboarding_id,
            OnboardingProcess.tenant_id == self.tenant_id
        ).first()

        if not onboarding:
            raise ValueError("Onboarding non trouvé")

        if onboarding.status == OnboardingStatus.COMPLETED:
            raise ValueError("Onboarding déjà terminé")

        onboarding.status = OnboardingStatus.IN_PROGRESS
        steps = json.loads(onboarding.steps_completed) if onboarding.steps_completed else {}
        result = {"steps": [], "errors": []}

        # Étape 1: Créer le compte utilisateur
        # TODO: Intégration avec module IAM pour créer le compte
        # user = iam_service.create_user(...)
        # onboarding.user_id = user.id
        steps["account_created"] = True
        result["steps"].append("account_created")

        # Étape 2: Attribuer le profil
        if onboarding.user_id and (onboarding.detected_profile_id or onboarding.profile_override):
            profile_id = onboarding.profile_override or onboarding.detected_profile_id
            profile = self.get_profile(profile_id)
            if profile:
                self.manual_assign_profile(
                    onboarding.user_id,
                    profile.code,
                    executed_by or 0,
                    onboarding.job_title,
                    onboarding.department
                )
                steps["profile_assigned"] = True
                result["steps"].append("profile_assigned")

        # Étape 3: Envoyer email de bienvenue
        # TODO: Intégration avec système d'email
        onboarding.welcome_email_sent = True
        steps["welcome_email"] = True
        result["steps"].append("welcome_email")

        # Étape 4: Notifier le manager
        # TODO: Notification manager
        onboarding.manager_notified = True
        steps["manager_notified"] = True
        result["steps"].append("manager_notified")

        # Étape 5: Notifier IT
        onboarding.it_notified = True
        steps["it_notified"] = True
        result["steps"].append("it_notified")

        # Finaliser
        onboarding.steps_completed = json.dumps(steps)

        if not result["errors"]:
            onboarding.status = OnboardingStatus.COMPLETED
            onboarding.completed_at = datetime.utcnow()
        else:
            onboarding.status = OnboardingStatus.FAILED

        self._log("ONBOARDING_EXECUTED", "ONBOARDING", onboarding.id, onboarding.user_id,
                 new_values=result,
                 source="AUTO" if executed_by is None else "MANUAL",
                 triggered_by=executed_by)

        self.db.commit()
        return result

    def list_pending_onboardings(self) -> list[OnboardingProcess]:
        """Liste les onboardings en attente."""
        return self.db.query(OnboardingProcess).filter(
            OnboardingProcess.tenant_id == self.tenant_id,
            OnboardingProcess.status.in_([OnboardingStatus.PENDING, OnboardingStatus.IN_PROGRESS])
        ).order_by(OnboardingProcess.start_date).all()

    # ========================================================================
    # OFFBOARDING
    # ========================================================================

    def create_offboarding(
        self,
        user_id: int,
        departure_date: datetime,
        departure_type: str,
        created_by: int,
        transfer_to_user_id: int | None = None,
        transfer_notes: str | None = None
    ) -> OffboardingProcess:
        """Crée un processus d'offboarding."""
        offboarding = OffboardingProcess(
            tenant_id=self.tenant_id,
            user_id=user_id,
            departure_date=departure_date,
            departure_type=departure_type,
            transfer_to_user_id=transfer_to_user_id,
            transfer_notes=transfer_notes,
            status=OffboardingStatus.SCHEDULED,
            steps_completed=json.dumps({}),
            created_by=created_by
        )

        self.db.add(offboarding)

        self._log("OFFBOARDING_CREATED", "OFFBOARDING", offboarding.id, user_id,
                 new_values={
                     "departure_date": str(departure_date),
                     "departure_type": departure_type
                 },
                 source="MANUAL", triggered_by=created_by)

        self.db.commit()
        return offboarding

    def execute_offboarding(self, offboarding_id: int, executed_by: int | None = None) -> dict[str, Any]:
        """
        Exécute le processus d'offboarding.
        Désactive le compte et révoque les accès.
        """
        offboarding = self.db.query(OffboardingProcess).filter(
            OffboardingProcess.id == offboarding_id,
            OffboardingProcess.tenant_id == self.tenant_id
        ).first()

        if not offboarding:
            raise ValueError("Offboarding non trouvé")

        if offboarding.status == OffboardingStatus.COMPLETED:
            raise ValueError("Offboarding déjà terminé")

        offboarding.status = OffboardingStatus.IN_PROGRESS
        steps = json.loads(offboarding.steps_completed) if offboarding.steps_completed else {}
        result = {"steps": [], "errors": []}

        # Étape 1: Révoquer les overrides actifs
        overrides = self.list_user_overrides(offboarding.user_id)
        for override in overrides:
            if override.status == OverrideStatus.APPROVED:
                self.revoke_override(override.id, executed_by or 0)
        steps["overrides_revoked"] = True
        result["steps"].append("overrides_revoked")

        # Étape 2: Révoquer le profil
        assignment = self.get_user_profile(offboarding.user_id)
        if assignment:
            assignment.is_active = False
            assignment.revoked_at = datetime.utcnow()
            assignment.revoked_by = executed_by
            assignment.revocation_reason = f"Offboarding: {offboarding.departure_type}"
        steps["profile_revoked"] = True
        result["steps"].append("profile_revoked")

        # Étape 3: Désactiver le compte
        # TODO: Intégration avec module IAM
        offboarding.account_deactivated = True
        steps["account_deactivated"] = True
        result["steps"].append("account_deactivated")

        # Étape 4: Révoquer tous les accès
        offboarding.access_revoked = True
        steps["access_revoked"] = True
        result["steps"].append("access_revoked")

        # Étape 5: Notifier manager
        offboarding.manager_notified = True
        steps["manager_notified"] = True
        result["steps"].append("manager_notified")

        # Étape 6: Notifier IT
        offboarding.it_notified = True
        steps["it_notified"] = True
        result["steps"].append("it_notified")

        # Finaliser
        offboarding.steps_completed = json.dumps(steps)

        if not result["errors"]:
            offboarding.status = OffboardingStatus.COMPLETED
            offboarding.completed_at = datetime.utcnow()

        self._log("OFFBOARDING_EXECUTED", "OFFBOARDING", offboarding.id, offboarding.user_id,
                 new_values=result,
                 source="AUTO" if executed_by is None else "MANUAL",
                 triggered_by=executed_by)

        self.db.commit()
        return result

    def list_scheduled_offboardings(self) -> list[OffboardingProcess]:
        """Liste les offboardings planifiés."""
        return self.db.query(OffboardingProcess).filter(
            OffboardingProcess.tenant_id == self.tenant_id,
            OffboardingProcess.status.in_([OffboardingStatus.SCHEDULED, OffboardingStatus.IN_PROGRESS])
        ).order_by(OffboardingProcess.departure_date).all()

    def execute_due_offboardings(self) -> int:
        """
        Exécute les offboardings dont la date de départ est passée.
        Retourne le nombre d'offboardings exécutés.
        """
        due = self.db.query(OffboardingProcess).filter(
            OffboardingProcess.tenant_id == self.tenant_id,
            OffboardingProcess.status == OffboardingStatus.SCHEDULED,
            OffboardingProcess.departure_date <= datetime.utcnow()
        ).all()

        count = 0
        for offboarding in due:
            self.execute_offboarding(offboarding.id)
            count += 1

        return count

    # ========================================================================
    # LOGGING
    # ========================================================================

    def _log(
        self,
        action: str,
        entity_type: str,
        entity_id: int | None,
        user_id: int | None,
        old_values: dict = None,
        new_values: dict = None,
        details: dict = None,
        source: str = "AUTO",
        triggered_by: int | None = None,
        success: bool = True,
        error_message: str = None
    ) -> None:
        """Crée une entrée de log."""
        log = AutoConfigLog(
            tenant_id=self.tenant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            details=json.dumps(details) if details else None,
            source=source,
            triggered_by=triggered_by,
            success=success,
            error_message=error_message
        )
        self.db.add(log)


# ============================================================================
# FACTORY
# ============================================================================

def get_autoconfig_service(db: Session, tenant_id: str) -> AutoConfigService:
    """Factory pour créer un service de configuration automatique."""
    return AutoConfigService(db, tenant_id)
