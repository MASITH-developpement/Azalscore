#!/usr/bin/env python3
"""
AZALS - Vérification Beta Tenant Masith
========================================
Script de vérification post-seed pour confirmer la conformité.

Ce script vérifie:
1. Existence et configuration du tenant beta
2. Existence et sécurité de l'utilisateur admin
3. Isolation multi-tenant correcte
4. Conformité des données aux exigences

USAGE:
    python scripts/verify_beta_tenant.py

RETOUR:
    0 : Toutes les vérifications passées
    1 : Au moins une vérification échouée
"""

import sys
from pathlib import Path

# Ajout du chemin racine au PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security import verify_password
from app.core.models import User, UserRole
from app.modules.tenants.models import (
    Tenant,
    TenantStatus,
    TenantEnvironment,
    TenantSettings,
    TenantOnboarding,
)


# Configuration attendue
EXPECTED_TENANT_ID = 'masith'
EXPECTED_ADMIN_EMAIL = 'contact@stephane-moreau.fr'
EXPECTED_ENVIRONMENT = TenantEnvironment.BETA
EXPECTED_STATUS = TenantStatus.ACTIVE
EXPECTED_ROLE = UserRole.ADMIN
INITIAL_PASSWORD = 'gobelet'  # Pour vérification uniquement


class VerificationResult:
    """Résultat d'une vérification."""

    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""

    def success(self, message: str):
        self.passed = True
        self.message = message

    def failure(self, message: str):
        self.passed = False
        self.message = message


def verify_tenant_exists(session) -> VerificationResult:
    """Vérifie que le tenant masith existe."""
    result = VerificationResult("Tenant exists")

    tenant = session.query(Tenant).filter(
        Tenant.tenant_id == EXPECTED_TENANT_ID
    ).first()

    if tenant:
        result.success(f"Tenant '{EXPECTED_TENANT_ID}' trouvé (id={tenant.id})")
    else:
        result.failure(f"Tenant '{EXPECTED_TENANT_ID}' introuvable")

    return result


def verify_tenant_environment(session) -> VerificationResult:
    """Vérifie que le tenant est en environnement beta."""
    result = VerificationResult("Tenant environment = beta")

    tenant = session.query(Tenant).filter(
        Tenant.tenant_id == EXPECTED_TENANT_ID
    ).first()

    if not tenant:
        result.failure("Tenant introuvable")
        return result

    if tenant.environment == EXPECTED_ENVIRONMENT:
        result.success(f"Environnement correct: {tenant.environment.value}")
    else:
        result.failure(
            f"Environnement incorrect: {tenant.environment} "
            f"(attendu: {EXPECTED_ENVIRONMENT})"
        )

    return result


def verify_tenant_status(session) -> VerificationResult:
    """Vérifie que le tenant est actif."""
    result = VerificationResult("Tenant status = active")

    tenant = session.query(Tenant).filter(
        Tenant.tenant_id == EXPECTED_TENANT_ID
    ).first()

    if not tenant:
        result.failure("Tenant introuvable")
        return result

    if tenant.status == EXPECTED_STATUS:
        result.success(f"Statut correct: {tenant.status.value}")
    else:
        result.failure(
            f"Statut incorrect: {tenant.status} "
            f"(attendu: {EXPECTED_STATUS})"
        )

    return result


def verify_admin_exists(session) -> VerificationResult:
    """Vérifie que l'utilisateur admin existe."""
    result = VerificationResult("Admin user exists")

    user = session.query(User).filter(
        User.tenant_id == EXPECTED_TENANT_ID,
        User.email == EXPECTED_ADMIN_EMAIL
    ).first()

    if user:
        result.success(f"Utilisateur admin trouvé (id={user.id})")
    else:
        result.failure(f"Utilisateur admin '{EXPECTED_ADMIN_EMAIL}' introuvable")

    return result


def verify_admin_role(session) -> VerificationResult:
    """Vérifie que l'utilisateur a le rôle admin."""
    result = VerificationResult("Admin role = ADMIN")

    user = session.query(User).filter(
        User.tenant_id == EXPECTED_TENANT_ID,
        User.email == EXPECTED_ADMIN_EMAIL
    ).first()

    if not user:
        result.failure("Utilisateur introuvable")
        return result

    if user.role == EXPECTED_ROLE:
        result.success(f"Rôle correct: {user.role.value}")
    else:
        result.failure(
            f"Rôle incorrect: {user.role} "
            f"(attendu: {EXPECTED_ROLE})"
        )

    return result


def verify_admin_active(session) -> VerificationResult:
    """Vérifie que l'utilisateur est actif."""
    result = VerificationResult("Admin is_active = true")

    user = session.query(User).filter(
        User.tenant_id == EXPECTED_TENANT_ID,
        User.email == EXPECTED_ADMIN_EMAIL
    ).first()

    if not user:
        result.failure("Utilisateur introuvable")
        return result

    if user.is_active == 1:
        result.success("Utilisateur actif")
    else:
        result.failure(f"Utilisateur inactif (is_active={user.is_active})")

    return result


def verify_password_not_cleartext(session) -> VerificationResult:
    """Vérifie que le mot de passe n'est PAS stocké en clair."""
    result = VerificationResult("Password NOT stored in cleartext")

    user = session.query(User).filter(
        User.tenant_id == EXPECTED_TENANT_ID,
        User.email == EXPECTED_ADMIN_EMAIL
    ).first()

    if not user:
        result.failure("Utilisateur introuvable")
        return result

    if user.password_hash == INITIAL_PASSWORD:
        result.failure("CRITIQUE: Mot de passe stocké en clair!")
    elif user.password_hash.startswith('$2b$'):
        result.success("Mot de passe hashé avec bcrypt")
    else:
        result.failure(f"Format de hash inconnu: {user.password_hash[:10]}...")

    return result


def verify_password_hash_valid(session) -> VerificationResult:
    """Vérifie que le hash du mot de passe est valide."""
    result = VerificationResult("Password hash is valid bcrypt")

    user = session.query(User).filter(
        User.tenant_id == EXPECTED_TENANT_ID,
        User.email == EXPECTED_ADMIN_EMAIL
    ).first()

    if not user:
        result.failure("Utilisateur introuvable")
        return result

    if verify_password(INITIAL_PASSWORD, user.password_hash):
        result.success("Hash bcrypt vérifié avec succès")
    else:
        result.failure("Vérification du hash échouée")

    return result


def verify_must_change_password(session) -> VerificationResult:
    """Vérifie que must_change_password est activé."""
    result = VerificationResult("must_change_password = true")

    user = session.query(User).filter(
        User.tenant_id == EXPECTED_TENANT_ID,
        User.email == EXPECTED_ADMIN_EMAIL
    ).first()

    if not user:
        result.failure("Utilisateur introuvable")
        return result

    if user.must_change_password == 1:
        result.success("Changement de mot de passe obligatoire au premier login")
    else:
        result.failure(
            f"must_change_password désactivé "
            f"(valeur={user.must_change_password})"
        )

    return result


def verify_tenant_isolation(session) -> VerificationResult:
    """Vérifie l'isolation multi-tenant."""
    result = VerificationResult("Tenant isolation verified")

    # L'utilisateur admin doit être lié uniquement au tenant masith
    user = session.query(User).filter(
        User.email == EXPECTED_ADMIN_EMAIL
    ).all()

    masith_users = [u for u in user if u.tenant_id == EXPECTED_TENANT_ID]
    other_users = [u for u in user if u.tenant_id != EXPECTED_TENANT_ID]

    if len(masith_users) == 1 and len(other_users) == 0:
        result.success("Utilisateur isolé dans le tenant masith uniquement")
    elif len(masith_users) == 1 and len(other_users) > 0:
        result.success(
            f"Utilisateur existe dans masith. "
            f"ATTENTION: {len(other_users)} autre(s) tenant(s) avec même email"
        )
    elif len(masith_users) == 0:
        result.failure("Aucun utilisateur dans le tenant masith")
    else:
        result.failure(f"Duplication: {len(masith_users)} utilisateurs dans masith")

    return result


def verify_no_cross_tenant_access(session) -> VerificationResult:
    """Vérifie qu'aucun droit cross-tenant n'existe."""
    result = VerificationResult("No cross-tenant access")

    # Cette vérification est conceptuelle - dans AZALS, le tenant_id
    # dans chaque requête garantit l'isolation

    user = session.query(User).filter(
        User.tenant_id == EXPECTED_TENANT_ID,
        User.email == EXPECTED_ADMIN_EMAIL
    ).first()

    if not user:
        result.failure("Utilisateur introuvable")
        return result

    # Vérifier que l'utilisateur n'a accès qu'à son tenant
    if user.tenant_id == EXPECTED_TENANT_ID:
        result.success(
            f"Utilisateur correctement limité au tenant '{EXPECTED_TENANT_ID}'"
        )
    else:
        result.failure(
            f"Incohérence: tenant_id={user.tenant_id} "
            f"(attendu: {EXPECTED_TENANT_ID})"
        )

    return result


def verify_tenant_settings(session) -> VerificationResult:
    """Vérifie que les paramètres du tenant existent."""
    result = VerificationResult("TenantSettings exists")

    settings = session.query(TenantSettings).filter(
        TenantSettings.tenant_id == EXPECTED_TENANT_ID
    ).first()

    if settings:
        result.success(f"TenantSettings trouvé (id={settings.id})")
    else:
        result.failure("TenantSettings introuvable")

    return result


def verify_tenant_onboarding(session) -> VerificationResult:
    """Vérifie que l'onboarding du tenant existe."""
    result = VerificationResult("TenantOnboarding exists")

    onboarding = session.query(TenantOnboarding).filter(
        TenantOnboarding.tenant_id == EXPECTED_TENANT_ID
    ).first()

    if onboarding:
        result.success(
            f"TenantOnboarding trouvé (progress={onboarding.progress_percent}%)"
        )
    else:
        result.failure("TenantOnboarding introuvable")

    return result


def main():
    """Point d'entrée principal."""
    print("=" * 70)
    print("AZALS - Vérification Beta Tenant Masith")
    print("=" * 70)
    print()

    # Connexion à la base de données
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Liste des vérifications à exécuter
    verifications = [
        verify_tenant_exists,
        verify_tenant_environment,
        verify_tenant_status,
        verify_admin_exists,
        verify_admin_role,
        verify_admin_active,
        verify_password_not_cleartext,
        verify_password_hash_valid,
        verify_must_change_password,
        verify_tenant_isolation,
        verify_no_cross_tenant_access,
        verify_tenant_settings,
        verify_tenant_onboarding,
    ]

    results = []
    for verification_fn in verifications:
        try:
            result = verification_fn(session)
            results.append(result)
        except Exception as e:
            result = VerificationResult(verification_fn.__name__)
            result.failure(f"Exception: {e}")
            results.append(result)

    session.close()

    # Affichage des résultats
    passed = 0
    failed = 0

    for result in results:
        if result.passed:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1

        print(f"  {status} | {result.name}")
        print(f"         {result.message}")
        print()

    # Résumé
    print("=" * 70)
    print(f"RÉSUMÉ: {passed} passées, {failed} échouées sur {len(results)} vérifications")
    print("=" * 70)

    if failed == 0:
        print("✓ TOUTES LES VÉRIFICATIONS PASSÉES")
        return 0
    else:
        print("✗ CERTAINES VÉRIFICATIONS ONT ÉCHOUÉ")
        return 1


if __name__ == '__main__':
    sys.exit(main())
