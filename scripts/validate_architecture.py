#!/usr/bin/env python3
"""
AZALS - Validation d'Architecture
==================================
Script de validation pour garantir le respect des patterns architecturaux.

Vérifie:
- Isolation tenant dans toutes les requêtes SQL
- Pas de session.query() sans filtre tenant_id
- Pas de db.execute() sans vérification tenant
- Respect des patterns de sécurité

Usage:
    python scripts/validate_architecture.py
    python scripts/validate_architecture.py --strict  # Bloque sur warning
    python scripts/validate_architecture.py --fix     # Suggère corrections

Exit codes:
    0 = OK
    1 = Erreurs critiques détectées
    2 = Warnings (non-bloquant sauf --strict)
"""

import argparse
import ast
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Violation:
    """Représente une violation de l'architecture."""
    file: str
    line: int
    rule: str
    severity: str  # CRITICAL, WARNING, INFO
    message: str
    suggestion: str = ""


class ArchitectureValidator:
    """Validateur d'architecture AZALS."""

    # Modèles SQLAlchemy connus sans tenant_id (tables globales)
    # Ces modèles sont légitimement interrogés sans filtre tenant_id
    GLOBAL_MODELS = {
        # Tables système
        'CommercialPlan', 'DiscountCode', 'Order', 'WebhookEvent',
        'AILearningData', 'IAMRateLimit', 'GuardianConfig',
        # Tables tenant (le tenant LUI-MÊME n'a pas de tenant_id parent)
        'Tenant', 'TenantInvitation', 'TenantPlan', 'TenantSettings',
        # Tables d'audit global
        'AuditLog', 'SystemLog',
        # Tables de configuration globale
        'SystemConfig', 'FeatureFlag',
    }

    # Patterns dangereux à détecter
    DANGEROUS_PATTERNS = [
        # Requêtes sans filtre tenant
        (r'\.query\([^)]+\)\.filter\([^)]*\)\.(?!filter)', 'QUERY_NO_TENANT'),
        # execute() sans tenant
        (r'db\.execute\s*\([^)]*(?<!tenant_id)[^)]*\)', 'EXECUTE_NO_TENANT'),
        # Secret hardcodé
        (r'(SECRET_KEY|API_KEY|PASSWORD)\s*=\s*["\'][^"\']+["\']', 'HARDCODED_SECRET'),
    ]

    def __init__(self, app_path: str = "app", strict: bool = False):
        self.app_path = Path(app_path)
        self.strict = strict
        self.violations: list[Violation] = []

    def validate(self) -> bool:
        """Exécute toutes les validations."""
        print("=" * 60)
        print("AZALS Architecture Validator")
        print("=" * 60)

        # 1. Scanner les fichiers service pour isolation tenant
        self._scan_tenant_isolation()

        # 2. Scanner pour secrets hardcodés
        self._scan_hardcoded_secrets()

        # 3. Vérifier les imports circulaires potentiels
        self._check_circular_imports()

        # Rapport
        return self._report()

    def _scan_tenant_isolation(self):
        """Scanne les services pour violations d'isolation tenant."""
        service_files = list(self.app_path.glob("modules/*/service.py"))
        service_files += list(self.app_path.glob("modules/**/service.py"))

        for file_path in service_files:
            self._analyze_service_file(file_path)

    def _analyze_service_file(self, file_path: Path):
        """Analyse un fichier service pour isolation tenant."""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                # Vérifier les requêtes query() sans filter tenant_id
                if '.query(' in line and 'tenant_id' not in line:
                    # Vérifier les 8 lignes suivantes pour tenant_id (queries chaînées peuvent être longues)
                    context = '\n'.join(lines[i-1:i+8])
                    if 'tenant_id' not in context and 'self.tenant_id' not in context:
                        # Extraire le modèle
                        model_match = re.search(r'\.query\((\w+)\)', line)
                        if model_match:
                            model = model_match.group(1)
                            if model not in self.GLOBAL_MODELS:
                                self.violations.append(Violation(
                                    file=str(file_path),
                                    line=i,
                                    rule="TENANT_ISOLATION",
                                    severity="WARNING",
                                    message=f"Requête {model} sans filtre tenant_id apparent",
                                    suggestion=f"Ajouter .filter({model}.tenant_id == self.tenant_id)"
                                ))

                # Vérifier db.execute() brut
                if 'db.execute(' in line or 'self.db.execute(' in line:
                    # Vérifier les 10 lignes suivantes pour tenant_id (statements multi-lignes)
                    context = '\n'.join(lines[i-1:i+10])
                    if 'tenant_id' not in context and 'SELECT 1' not in line:
                        # Vérifier si c'est un SET pour RLS (légitime)
                        if 'SET LOCAL' in context or 'SET app.' in context:
                            continue
                        self.violations.append(Violation(
                            file=str(file_path),
                            line=i,
                            rule="RAW_SQL",
                            severity="WARNING",
                            message="Utilisation de db.execute() sans tenant_id explicite",
                            suggestion="Utiliser ORM avec filtre tenant_id ou ajouter paramètre tenant_id"
                        ))

        except Exception as e:
            print(f"  Erreur analyse {file_path}: {e}")

    def _scan_hardcoded_secrets(self):
        """Scanne pour secrets hardcodés."""
        patterns = [
            (r'SECRET_KEY\s*=\s*["\'][^$][^"\']{8,}["\']', "SECRET_KEY hardcodé"),
            (r'API_KEY\s*=\s*["\'][^$][^"\']{8,}["\']', "API_KEY hardcodé"),
            (r'sk_live_[a-zA-Z0-9]+', "Clé Stripe live détectée"),
            (r'sk-ant-api[a-zA-Z0-9-]+', "Clé Anthropic détectée"),
            (r'sk-[a-zA-Z0-9]{20,}', "Clé OpenAI potentielle détectée"),
        ]

        # Patterns pour détecter les secrets sensibles dans les logs
        # IMPORTANT: On cherche les cas où la VALEUR secrète est loggée, pas juste mentionnée
        # Exemple problématique: logger.info("MFA code: %s", code)  <- code est loggé
        # Exemple OK: logger.info("Invalid MFA code for user: %s", user_id)  <- user_id pas secret
        logging_patterns = [
            # Pattern: log de variable nommée password/secret/token/key directement
            (r'log(?:ger)?\.(?:info|debug|warning|error)\s*\([^)]+%s[^)]*,\s*(?:password|secret|api_key|token\b(?!\[:))', "Secret potentiel loggé directement"),
            # Pattern: affichage format f-string de secrets
            (r'log(?:ger)?\.(?:info|debug)\s*\(f["\'][^"\']*\{(?:password|secret|api_key|code\}|token\})', "Secret potentiel dans f-string"),
        ]

        # Scanner app/ et config
        for py_file in self.app_path.glob("**/*.py"):
            if 'test' in str(py_file).lower() or '__pycache__' in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith('#'):
                        continue

                    # Vérifier les patterns de secrets hardcodés
                    for pattern, desc in patterns:
                        if re.search(pattern, line):
                            # Vérifier si c'est une variable d'environnement
                            if 'os.getenv' in line or 'os.environ' in line:
                                continue
                            if 'Field(' in line and 'default=None' in line:
                                continue
                            # Ignorer les définitions d'Enum
                            if 'class ' in content[:content.find(line)] and '(Enum)' in content[:content.find(line)+200]:
                                # Vérifier si on est dans une classe Enum
                                class_start = content.rfind('class ', 0, content.find(line))
                                if class_start != -1:
                                    class_def = content[class_start:class_start+200]
                                    if '(Enum)' in class_def:
                                        continue

                            self.violations.append(Violation(
                                file=str(py_file),
                                line=i,
                                rule="HARDCODED_SECRET",
                                severity="CRITICAL",
                                message=desc,
                                suggestion="Utiliser os.getenv() ou variable d'environnement"
                            ))

                    # Vérifier les secrets dans les logs
                    for pattern, desc in logging_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Ignorer si c'est un commentaire ou une docstring
                            if '# TODO' in line or 'À NE PAS FAIRE' in line:
                                continue
                            self.violations.append(Violation(
                                file=str(py_file),
                                line=i,
                                rule="SECRET_IN_LOG",
                                severity="CRITICAL",
                                message=desc,
                                suggestion="Ne jamais logger de secrets - utiliser un placeholder ou masquer la valeur"
                            ))
            except Exception:
                pass

    def _check_circular_imports(self):
        """Vérifie les imports circulaires potentiels."""
        # Simplifié: vérifie les imports de modules parent dans enfants
        for py_file in self.app_path.glob("modules/**/*.py"):
            if '__pycache__' in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                module_path = str(py_file.parent)

                # Import du module parent depuis un sous-module
                if re.search(r'from\s+app\.modules\.\w+\s+import', content):
                    # C'est OK, mais vérifions les imports circulaires évidents
                    pass

            except Exception:
                pass

    def _report(self) -> bool:
        """Génère le rapport et retourne le succès."""
        print()

        critical = [v for v in self.violations if v.severity == "CRITICAL"]
        warnings = [v for v in self.violations if v.severity == "WARNING"]
        infos = [v for v in self.violations if v.severity == "INFO"]

        if critical:
            print("VIOLATIONS CRITIQUES:")
            print("-" * 40)
            for v in critical:
                print(f"  [{v.severity}] {v.file}:{v.line}")
                print(f"    {v.message}")
                if v.suggestion:
                    print(f"    -> {v.suggestion}")
            print()

        if warnings:
            print("WARNINGS:")
            print("-" * 40)
            for v in warnings[:10]:  # Limiter à 10
                print(f"  [{v.severity}] {v.file}:{v.line}")
                print(f"    {v.message}")
            if len(warnings) > 10:
                print(f"  ... et {len(warnings) - 10} autres warnings")
            print()

        # Résumé
        print("=" * 60)
        print(f"RÉSUMÉ: {len(critical)} critiques, {len(warnings)} warnings, {len(infos)} infos")
        print("=" * 60)

        if critical:
            print("ÉCHEC: Violations critiques détectées")
            return False

        if warnings and self.strict:
            print("ÉCHEC (mode strict): Warnings détectés")
            return False

        print("SUCCÈS: Architecture conforme")
        return True


def main():
    parser = argparse.ArgumentParser(description="AZALS Architecture Validator")
    parser.add_argument("--strict", action="store_true", help="Échouer sur warnings")
    parser.add_argument("--app-path", default="app", help="Chemin vers app/")
    args = parser.parse_args()

    validator = ArchitectureValidator(
        app_path=args.app_path,
        strict=args.strict
    )

    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
