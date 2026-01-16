#!/usr/bin/env python3
"""
AZALSCORE - Script de Validation Production
============================================

Ce script verifie que toutes les conditions sont reunies pour un
deploiement en production. A executer AVANT chaque mise en production.

Usage:
    python scripts/validate_production.py

Codes de sortie:
    0 - Validation reussie, pret pour production
    1 - Erreurs critiques detectees, deploiement interdit
    2 - Avertissements detectes, deploiement possible mais attention requise
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

# Ajouter le repertoire racine au path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


class ValidationResult:
    """Resultat d'une validation."""

    def __init__(self, name: str, success: bool, message: str, critical: bool = True):
        self.name = name
        self.success = success
        self.message = message
        self.critical = critical


class ProductionValidator:
    """Validateur de production pour AZALSCORE."""

    def __init__(self):
        self.results: list[ValidationResult] = []
        self.root_dir = ROOT_DIR

    def add_result(self, result: ValidationResult):
        """Ajoute un resultat de validation."""
        self.results.append(result)

    def check_env_file(self) -> ValidationResult:
        """Verifie que le fichier .env existe et est configure."""
        env_file = self.root_dir / ".env"

        if not env_file.exists():
            return ValidationResult(
                "Fichier .env",
                False,
                "Fichier .env manquant - Copier .env.example vers .env",
                critical=True
            )

        # Verifier les variables obligatoires
        required_vars = [
            "DATABASE_URL",
            "SECRET_KEY",
            "BOOTSTRAP_SECRET",
            "ENCRYPTION_KEY",
        ]

        env_content = env_file.read_text()
        missing_vars = []

        for var in required_vars:
            if f"{var}=" not in env_content:
                missing_vars.append(var)
            elif f"{var}=CHANGEME" in env_content or f"{var}=\"\"" in env_content:
                missing_vars.append(f"{var} (non configure)")

        if missing_vars:
            return ValidationResult(
                "Fichier .env",
                False,
                f"Variables manquantes ou non configurees: {', '.join(missing_vars)}",
                critical=True
            )

        return ValidationResult(
            "Fichier .env",
            True,
            "Fichier .env present et configure correctement"
        )

    def check_secret_key_strength(self) -> ValidationResult:
        """Verifie que SECRET_KEY est suffisamment fort."""
        env_file = self.root_dir / ".env"

        if not env_file.exists():
            return ValidationResult(
                "SECRET_KEY",
                False,
                "Impossible de verifier - fichier .env manquant",
                critical=True
            )

        env_content = env_file.read_text()

        for line in env_content.split("\n"):
            if line.startswith("SECRET_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")

                if len(key) < 32:
                    return ValidationResult(
                        "SECRET_KEY",
                        False,
                        f"SECRET_KEY trop court ({len(key)} chars, min 32)",
                        critical=True
                    )

                # Verifier que ce n'est pas une valeur par defaut
                weak_patterns = ["test", "changeme", "secret", "password", "12345"]
                for pattern in weak_patterns:
                    if pattern.lower() in key.lower():
                        return ValidationResult(
                            "SECRET_KEY",
                            False,
                            "SECRET_KEY contient un pattern faible",
                            critical=True
                        )

                return ValidationResult(
                    "SECRET_KEY",
                    True,
                    f"SECRET_KEY valide ({len(key)} caracteres)"
                )

        return ValidationResult(
            "SECRET_KEY",
            False,
            "SECRET_KEY non trouve dans .env",
            critical=True
        )

    def check_encryption_key(self) -> ValidationResult:
        """Verifie que ENCRYPTION_KEY est valide."""
        env_file = self.root_dir / ".env"

        if not env_file.exists():
            return ValidationResult(
                "ENCRYPTION_KEY",
                False,
                "Impossible de verifier - fichier .env manquant",
                critical=True
            )

        env_content = env_file.read_text()

        for line in env_content.split("\n"):
            if line.startswith("ENCRYPTION_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")

                # Fernet keys sont exactement 44 caracteres
                if len(key) != 44:
                    return ValidationResult(
                        "ENCRYPTION_KEY",
                        False,
                        f"ENCRYPTION_KEY invalide ({len(key)} chars, doit etre 44)",
                        critical=True
                    )

                # Essayer de creer une instance Fernet
                try:
                    from cryptography.fernet import Fernet
                    Fernet(key.encode())
                    return ValidationResult(
                        "ENCRYPTION_KEY",
                        True,
                        "ENCRYPTION_KEY valide (format Fernet)"
                    )
                except Exception as e:
                    return ValidationResult(
                        "ENCRYPTION_KEY",
                        False,
                        f"ENCRYPTION_KEY invalide: {e}",
                        critical=True
                    )

        return ValidationResult(
            "ENCRYPTION_KEY",
            False,
            "ENCRYPTION_KEY non trouve dans .env",
            critical=True
        )

    def check_debug_mode(self) -> ValidationResult:
        """Verifie que DEBUG est desactive en production."""
        env_file = self.root_dir / ".env"

        if not env_file.exists():
            return ValidationResult(
                "Mode DEBUG",
                False,
                "Impossible de verifier - fichier .env manquant",
                critical=False
            )

        env_content = env_file.read_text()

        for line in env_content.split("\n"):
            if line.startswith("DEBUG="):
                value = line.split("=", 1)[1].strip().lower()
                if value in ["true", "1", "yes"]:
                    return ValidationResult(
                        "Mode DEBUG",
                        False,
                        "DEBUG=true - Doit etre false en production",
                        critical=False
                    )

        return ValidationResult(
            "Mode DEBUG",
            True,
            "DEBUG desactive ou non configure (ok)"
        )

    def check_python_syntax(self) -> ValidationResult:
        """Verifie la syntaxe Python de tous les fichiers."""
        errors = []
        files_checked = 0

        for py_file in (self.root_dir / "app").rglob("*.py"):
            try:
                with open(py_file, "r") as f:
                    compile(f.read(), py_file, "exec")
                files_checked += 1
            except SyntaxError as e:
                errors.append(f"{py_file.relative_to(self.root_dir)}: {e}")

        if errors:
            return ValidationResult(
                "Syntaxe Python",
                False,
                f"{len(errors)} erreurs de syntaxe: {errors[0]}...",
                critical=True
            )

        return ValidationResult(
            "Syntaxe Python",
            True,
            f"{files_checked} fichiers Python verifies sans erreur"
        )

    def check_frontend_build(self) -> ValidationResult:
        """Verifie que le frontend est builde."""
        dist_dir = self.root_dir / "frontend" / "dist"

        if not dist_dir.exists():
            return ValidationResult(
                "Build Frontend",
                False,
                "Dossier frontend/dist manquant - Executer 'npm run build'",
                critical=False
            )

        index_file = dist_dir / "index.html"
        if not index_file.exists():
            return ValidationResult(
                "Build Frontend",
                False,
                "frontend/dist/index.html manquant",
                critical=False
            )

        return ValidationResult(
            "Build Frontend",
            True,
            "Build frontend present (dist/index.html existe)"
        )

    def check_no_debug_prints(self) -> ValidationResult:
        """Verifie qu'il n'y a pas de print debug dans le code."""
        debug_patterns = [
            "print(f\"[DEBUG]",
            "print(\"[DEBUG]",
            "print('[DEBUG]",
        ]

        files_with_debug = []

        for py_file in (self.root_dir / "app").rglob("*.py"):
            content = py_file.read_text()
            for pattern in debug_patterns:
                if pattern in content:
                    files_with_debug.append(str(py_file.relative_to(self.root_dir)))
                    break

        if files_with_debug:
            return ValidationResult(
                "Debug prints",
                False,
                f"Print debug trouves dans: {', '.join(files_with_debug[:3])}...",
                critical=False
            )

        return ValidationResult(
            "Debug prints",
            True,
            "Aucun print debug trouve"
        )

    def check_requirements(self) -> ValidationResult:
        """Verifie que requirements.txt existe."""
        req_file = self.root_dir / "requirements.txt"

        if not req_file.exists():
            return ValidationResult(
                "Requirements",
                False,
                "requirements.txt manquant",
                critical=True
            )

        # Compter les dependances
        lines = [l.strip() for l in req_file.read_text().split("\n") if l.strip() and not l.startswith("#")]

        return ValidationResult(
            "Requirements",
            True,
            f"requirements.txt present ({len(lines)} dependances)"
        )

    def check_tests_exist(self) -> ValidationResult:
        """Verifie que des tests existent."""
        tests_dir = self.root_dir / "tests"

        if not tests_dir.exists():
            return ValidationResult(
                "Tests",
                False,
                "Dossier tests manquant",
                critical=False
            )

        test_files = list(tests_dir.rglob("test_*.py"))

        if len(test_files) < 5:
            return ValidationResult(
                "Tests",
                False,
                f"Seulement {len(test_files)} fichiers de test trouves (minimum 5)",
                critical=False
            )

        return ValidationResult(
            "Tests",
            True,
            f"{len(test_files)} fichiers de test trouves"
        )

    def check_docker_files(self) -> ValidationResult:
        """Verifie que les fichiers Docker existent."""
        dockerfile = self.root_dir / "Dockerfile"
        compose = self.root_dir / "docker-compose.yml"

        missing = []
        if not dockerfile.exists():
            missing.append("Dockerfile")
        if not compose.exists():
            missing.append("docker-compose.yml")

        if missing:
            return ValidationResult(
                "Docker",
                False,
                f"Fichiers Docker manquants: {', '.join(missing)}",
                critical=False
            )

        return ValidationResult(
            "Docker",
            True,
            "Dockerfile et docker-compose.yml presents"
        )

    def check_encryption_implementation(self) -> ValidationResult:
        """Verifie que le chiffrement est implemente."""
        iam_service = self.root_dir / "app" / "modules" / "iam" / "service.py"

        if not iam_service.exists():
            return ValidationResult(
                "Chiffrement MFA",
                False,
                "Service IAM non trouve",
                critical=True
            )

        content = iam_service.read_text()

        # Verifier que encrypt_value est utilise
        if "encrypt_value" not in content:
            return ValidationResult(
                "Chiffrement MFA",
                False,
                "Chiffrement MFA non implemente (encrypt_value manquant)",
                critical=True
            )

        # Verifier qu'il n'y a plus de TODO Chiffrer
        if "# TODO: Chiffrer" in content:
            return ValidationResult(
                "Chiffrement MFA",
                False,
                "TODO Chiffrer encore present dans le code",
                critical=True
            )

        return ValidationResult(
            "Chiffrement MFA",
            True,
            "Chiffrement MFA implemente"
        )

    def run_all_checks(self):
        """Execute toutes les validations."""
        checks = [
            self.check_env_file,
            self.check_secret_key_strength,
            self.check_encryption_key,
            self.check_debug_mode,
            self.check_python_syntax,
            self.check_frontend_build,
            self.check_no_debug_prints,
            self.check_requirements,
            self.check_tests_exist,
            self.check_docker_files,
            self.check_encryption_implementation,
        ]

        print("\n" + "=" * 60)
        print("  AZALSCORE - VALIDATION PRODUCTION")
        print("=" * 60 + "\n")

        for check in checks:
            try:
                result = check()
                self.add_result(result)

                status = "[OK]" if result.success else ("[ERREUR]" if result.critical else "[WARN]")
                print(f"  {status:8} {result.name}")
                if not result.success:
                    print(f"           -> {result.message}")

            except Exception as e:
                self.add_result(ValidationResult(
                    check.__name__,
                    False,
                    f"Exception: {str(e)[:50]}",
                    critical=True
                ))
                print(f"  [ERREUR] {check.__name__}: Exception")

        print("\n" + "=" * 60)

    def get_summary(self) -> tuple[int, int, int]:
        """Retourne (total, succes, echecs_critiques)."""
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        critical_failures = sum(1 for r in self.results if not r.success and r.critical)
        warnings = sum(1 for r in self.results if not r.success and not r.critical)
        return total, success, critical_failures, warnings

    def print_summary(self) -> int:
        """Affiche le resume et retourne le code de sortie."""
        total, success, critical, warnings = self.get_summary()

        if critical > 0:
            print("\n  [ECHEC] DEPLOIEMENT INTERDIT")
            print(f"           {critical} erreur(s) critique(s) detectee(s)")
            print(f"           Corriger les erreurs avant deploiement")
            print("=" * 60 + "\n")
            return 1
        elif warnings > 0:
            print("\n  [ATTENTION] DEPLOIEMENT POSSIBLE AVEC RESERVES")
            print(f"              {warnings} avertissement(s) detecte(s)")
            print(f"              Reviser les avertissements si possible")
            print("=" * 60 + "\n")
            return 2
        else:
            print("\n  [SUCCES] PRET POUR PRODUCTION")
            print(f"           {success}/{total} validations reussies")
            print("=" * 60 + "\n")
            return 0


def main():
    """Point d'entree principal."""
    validator = ProductionValidator()
    validator.run_all_checks()
    exit_code = validator.print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
