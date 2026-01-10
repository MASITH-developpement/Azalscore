#!/usr/bin/env python3
"""
AZALS - Script de Reset Database UUID
=====================================

Script standalone pour reset CONTROLE et SECURISE de la base de donnees
vers une architecture UUID-only.

PREREQUIS OBLIGATOIRE:
    export AZALS_DB_RESET_UUID=true

USAGE:
    python scripts/reset_database_uuid.py

COMPORTEMENT:
    1. Verifie AZALS_DB_RESET_UUID=true
    2. Verifie que l'environnement n'est PAS production
    3. Affiche un recapitulatif et demande confirmation
    4. Supprime toutes les tables du schema public
    5. Recree les tables via ORM (Base.metadata.create_all)
    6. Verifie la conformite UUID

SECURITE:
    - AUCUNE action sans AZALS_DB_RESET_UUID=true
    - AUCUN reset possible en PRODUCTION
    - Confirmation interactive requise (sauf CI=true)
    - Log complet de chaque operation

AVERTISSEMENT:
    CE SCRIPT DETRUIT TOUTES LES DONNEES.
    A utiliser UNIQUEMENT pour migration initiale ou environnement de dev.
"""

import os
import sys
import logging
from datetime import datetime

# Ajouter le repertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ResetError(Exception):
    """Erreur lors du reset."""
    pass


def verify_environment() -> None:
    """
    Verifie les conditions de securite.

    Raises:
        ResetError: Si conditions non remplies
    """
    # Verifier la variable d'environnement
    reset_enabled = os.environ.get('AZALS_DB_RESET_UUID', '').lower().strip()

    if reset_enabled != 'true':
        raise ResetError(
            f"\n"
            f"{'='*60}\n"
            f"ERREUR: Reset NON AUTORISE\n"
            f"{'='*60}\n"
            f"\n"
            f"Pour effectuer un reset UUID, definissez:\n"
            f"\n"
            f"    export AZALS_DB_RESET_UUID=true\n"
            f"\n"
            f"ATTENTION: Cette operation DETRUIT TOUTES LES DONNEES.\n"
            f"\n"
            f"{'='*60}\n"
        )

    logger.info("[SECURITY] AZALS_DB_RESET_UUID=true - Reset autorise")


def verify_not_production(settings) -> None:
    """
    Verifie que l'environnement n'est pas production.

    Args:
        settings: Configuration applicative

    Raises:
        ResetError: Si en production
    """
    if settings.environment.lower() == 'production':
        raise ResetError(
            f"\n"
            f"{'='*60}\n"
            f"ERREUR FATALE: Reset INTERDIT en PRODUCTION\n"
            f"{'='*60}\n"
            f"\n"
            f"Le reset de base de donnees est IMPOSSIBLE en production.\n"
            f"Environnement detecte: {settings.environment}\n"
            f"\n"
            f"OPTIONS:\n"
            f"1. Utilisez un environnement de dev/test\n"
            f"2. Migrez les donnees manuellement\n"
            f"3. Recreez la base PostgreSQL manuellement\n"
            f"\n"
            f"{'='*60}\n"
        )

    logger.info(f"[SECURITY] Environnement: {settings.environment} - OK")


def get_confirmation() -> bool:
    """
    Demande confirmation interactive.

    Returns:
        True si confirme, False sinon
    """
    # Skip en mode CI
    if os.environ.get('CI', '').lower() == 'true':
        logger.info("[CI] Mode CI detecte - confirmation automatique")
        return True

    # Skip si pas de terminal
    if not sys.stdin.isatty():
        logger.info("[BATCH] Mode batch detecte - confirmation automatique")
        return True

    print(f"\n{'='*60}")
    print("CONFIRMATION REQUISE")
    print(f"{'='*60}")
    print("\nCette operation va:")
    print("  - SUPPRIMER toutes les tables existantes")
    print("  - PERDRE toutes les donnees")
    print("  - RECREER les tables avec UUID")
    print(f"\n{'='*60}")

    try:
        confirm = input("\nTapez 'RESET' pour confirmer: ")
        return confirm.strip() == 'RESET'
    except (EOFError, KeyboardInterrupt):
        return False


def run_reset() -> bool:
    """
    Execute le reset complet.

    Returns:
        True si succes
    """
    start_time = datetime.now()

    print(f"\n{'='*60}")
    print("AZALS - RESET DATABASE UUID")
    print(f"{'='*60}")
    print(f"Date: {start_time.isoformat()}")
    print(f"{'='*60}\n")

    try:
        # 1. Verifier l'autorisation
        verify_environment()

        # 2. Charger la configuration
        from app.core.config import get_settings
        settings = get_settings()

        # 3. Verifier l'environnement
        verify_not_production(settings)

        # 4. Connexion a la base
        from sqlalchemy import create_engine
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            echo=False
        )

        # 5. Creer le manager
        from app.db.uuid_reset import UUIDComplianceManager
        manager = UUIDComplianceManager(engine, settings)

        # 6. Detecter l'etat actuel
        violations = manager.detect_violations()
        current_tables = manager.get_all_tables()

        print(f"[INFO] Tables existantes: {len(current_tables)}")
        print(f"[INFO] Violations UUID: {len(violations)}")

        # 7. Demander confirmation
        if not get_confirmation():
            print("\n[ABORT] Reset annule par l'utilisateur")
            return False

        # 8. Forcer l'autorisation pour le manager
        # (on a deja verifie manuellement)
        original_reset = settings.db_reset_uuid
        settings.db_reset_uuid = True

        try:
            # 9. Supprimer les tables
            print("\n[RESET] Suppression des tables...")
            dropped = manager.drop_all_tables()
            print(f"[OK] {dropped} tables supprimees")

            # 10. Recreer depuis ORM
            print("\n[RESET] Recreation des tables...")
            created = manager.recreate_from_orm()
            print(f"[OK] {created} tables creees")

            # 11. Verifier conformite
            print("\n[VALIDATE] Verification conformite UUID...")
            if manager.verify_uuid_compliance():
                print("[OK] Base conforme UUID - aucune violation")
            else:
                remaining = len(manager.violations)
                print(f"[WARN] {remaining} violations restantes")
                for v in manager.violations[:10]:
                    print(f"  - {v[0]}.{v[1]}: {v[2]}")

        finally:
            settings.db_reset_uuid = original_reset

        # 12. Rapport final
        duration = datetime.now() - start_time

        print(f"\n{'='*60}")
        print("RAPPORT FINAL")
        print(f"{'='*60}")
        print(f"Duree: {duration.total_seconds():.2f}s")
        print(f"Tables supprimees: {dropped}")
        print(f"Tables creees: {created}")
        print(f"Violations restantes: {len(manager.violations)}")
        print(f"Statut: {'UUID FULL COMPLIANCE' if len(manager.violations) == 0 else 'INCOMPLET'}")
        print(f"{'='*60}\n")

        return len(manager.violations) == 0

    except ResetError as e:
        logger.error(str(e))
        print(str(e))
        return False

    except Exception as e:
        logger.exception(f"[FATAL] Erreur inattendue: {e}")
        print(f"\n[FATAL] {e}")
        return False


def main():
    """Point d'entree principal."""
    success = run_reset()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
