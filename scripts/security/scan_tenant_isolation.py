#!/usr/bin/env python3
"""
AZALSCORE - Scanner d'Isolation Multi-Tenant
=============================================

Ce script analyse le code source pour détecter les violations potentielles
d'isolation tenant:

1. Requêtes session.query() sans filtre tenant_id
2. Requêtes select() sans where tenant_id
3. Requêtes db.execute() sans vérification tenant_id
4. Accès direct aux tables sans filtre tenant

Usage:
    python scripts/security/scan_tenant_isolation.py [--fix] [--verbose]

Options:
    --fix       Suggérer des corrections (non implémenté)
    --verbose   Afficher tous les détails
    --strict    Échouer si des violations sont trouvées (pour CI/CD)

Sortie:
    - Liste des violations avec fichier:ligne
    - Score de sécurité (100% = aucune violation)
    - Exit code 1 si violations détectées (mode --strict)

PRINCIPE: Une mauvaise note vaut mieux qu'une note truquée.
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass
class Violation:
    """Représente une violation d'isolation tenant détectée."""
    file: str
    line: int
    code: str
    pattern: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    recommendation: str


# Patterns dangereux à détecter
# IMPORTANT: Le contexte est analysé sur 15 lignes avant/après pour détecter les filtres tenant_id
DANGEROUS_PATTERNS = [
    # Requêtes SQLAlchemy sans filtre tenant - Ces patterns sont TRÈS dangereux
    {
        "pattern": r"\.query\([^)]+\)\.all\(\)",
        "severity": "CRITICAL",
        "description": "query().all() sans filtre - récupère TOUTES les données",
        "recommendation": "Ajouter .filter(Model.tenant_id == tenant_id) avant .all()",
        "exceptions": ["# TENANT_EXEMPT", "tenant_id", "self.tenant_id", ".tenant_id =="],
        "context_lines": 15  # Fenêtre de contexte élargie
    },
    {
        "pattern": r"\.query\([^)]+\)\.first\(\)",
        "severity": "HIGH",
        "description": "query().first() sans filtre visible",
        "recommendation": "Vérifier que tenant_id est filtré dans la même expression",
        "exceptions": ["tenant_id", "# TENANT_EXEMPT", "self.tenant_id", ".tenant_id =="],
        "context_lines": 15
    },
    {
        "pattern": r"db\.execute\s*\(\s*['\"]SELECT",
        "severity": "CRITICAL",
        "description": "Requête SQL brute sans vérification tenant visible",
        "recommendation": "Utiliser SQLAlchemy ORM avec filtre tenant_id, ou ajouter WHERE tenant_id = :tenant_id",
        "exceptions": ["tenant_id", "# TENANT_EXEMPT", "# RAW_SQL_SAFE", "SELECT 1", "SELECT version"],
        "context_lines": 5
    },
    {
        "pattern": r"session\.execute\s*\(\s*['\"]",
        "severity": "CRITICAL",
        "description": "Requête SQL brute via session",
        "recommendation": "Préférer l'ORM SQLAlchemy avec filtre tenant_id",
        "exceptions": ["tenant_id", "# TENANT_EXEMPT", "SELECT 1"],
        "context_lines": 5
    },
    {
        "pattern": r"\.delete\(\s*\)",
        "severity": "CRITICAL",
        "description": "Suppression potentiellement sans filtre tenant",
        "recommendation": "Vérifier que .filter(tenant_id == ...) est appliqué avant delete()",
        "exceptions": ["tenant_id", "# TENANT_EXEMPT", "self.tenant_id", ".tenant_id ==", "c.tenant_id"],
        "context_lines": 15  # Les chaînes de filtres SQLAlchemy peuvent être longues
    },
    {
        # Pattern plus précis: détecte ).update({ qui indique un update SQLAlchemy après filter()
        "pattern": r"\)\s*\.update\s*\(\s*\{",
        "severity": "HIGH",
        "description": "Mise à jour SQLAlchemy potentiellement sans filtre tenant",
        "recommendation": "Vérifier que .filter(tenant_id == ...) est appliqué avant update()",
        "exceptions": ["tenant_id", "# TENANT_EXEMPT", "self.tenant_id", ".tenant_id =="],
        "context_lines": 15
    },
]

# Fichiers/dossiers à ignorer
IGNORE_PATTERNS = [
    "__pycache__",
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "migrations",
    "alembic/versions",
    "tests",  # Les tests peuvent avoir des patterns spéciaux
    ".pyc",
    "frontend",
]


def should_ignore(path: str) -> bool:
    """Vérifie si un chemin doit être ignoré."""
    for pattern in IGNORE_PATTERNS:
        if pattern in path:
            return True
    return False


def scan_file(filepath: str, verbose: bool = False) -> List[Violation]:
    """Scanne un fichier Python pour les violations."""
    violations = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        if verbose:
            print(f"  [SKIP] Impossible de lire {filepath}: {e}")
        return []

    for line_num, line in enumerate(lines, 1):
        # Ignorer les commentaires et les lignes vides
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        for pattern_info in DANGEROUS_PATTERNS:
            if re.search(pattern_info["pattern"], line, re.IGNORECASE):
                # Fenêtre de contexte configurable par pattern (défaut: 15 lignes)
                context_lines = pattern_info.get("context_lines", 15)
                context_start = max(0, line_num - 1 - context_lines)  # line_num est 1-indexed
                context_end = min(len(lines), line_num + context_lines)
                context = ''.join(lines[context_start:context_end])

                # Si une exception est trouvée dans le contexte, ignorer
                is_exception = False
                for exc in pattern_info.get("exceptions", []):
                    if exc in context:
                        is_exception = True
                        break

                if not is_exception:
                    violations.append(Violation(
                        file=filepath,
                        line=line_num,
                        code=line.strip()[:100],  # Tronquer les lignes longues
                        pattern=pattern_info["description"],
                        severity=pattern_info["severity"],
                        recommendation=pattern_info["recommendation"]
                    ))

    return violations


def scan_directory(directory: str, verbose: bool = False) -> Tuple[List[Violation], int]:
    """Scanne récursivement un répertoire pour les violations."""
    all_violations = []
    files_scanned = 0

    for root, dirs, files in os.walk(directory):
        # Filtrer les dossiers à ignorer
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]

        for file in files:
            if not file.endswith('.py'):
                continue

            filepath = os.path.join(root, file)

            if should_ignore(filepath):
                continue

            if verbose:
                print(f"  Scanning: {filepath}")

            violations = scan_file(filepath, verbose)
            all_violations.extend(violations)
            files_scanned += 1

    return all_violations, files_scanned


def print_report(violations: List[Violation], files_scanned: int):
    """Affiche le rapport de scan."""
    print("\n" + "=" * 70)
    print("AZALSCORE - RAPPORT D'AUDIT ISOLATION TENANT")
    print("=" * 70)

    if not violations:
        print("\n✅ AUCUNE VIOLATION DÉTECTÉE")
        print(f"   Fichiers analysés: {files_scanned}")
        print("\n   Toutes les requêtes semblent correctement filtrées par tenant_id.")
        print("=" * 70)
        return

    # Grouper par sévérité
    by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for v in violations:
        by_severity[v.severity].append(v)

    # Afficher les violations
    print(f"\n❌ {len(violations)} VIOLATION(S) DÉTECTÉE(S)")
    print(f"   Fichiers analysés: {files_scanned}")

    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        items = by_severity[severity]
        if not items:
            continue

        severity_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }

        print(f"\n{severity_emoji[severity]} {severity} ({len(items)} violation(s)):")
        print("-" * 50)

        for v in items:
            print(f"\n  📁 {v.file}:{v.line}")
            print(f"     Code: {v.code}")
            print(f"     Pattern: {v.pattern}")
            print(f"     💡 {v.recommendation}")

    # Score de sécurité
    critical_count = len(by_severity["CRITICAL"])
    high_count = len(by_severity["HIGH"])

    # Calcul du score (pénalités)
    score = 100
    score -= critical_count * 20  # -20 points par CRITICAL
    score -= high_count * 10  # -10 points par HIGH
    score -= len(by_severity["MEDIUM"]) * 5  # -5 points par MEDIUM
    score -= len(by_severity["LOW"]) * 2  # -2 points par LOW
    score = max(0, score)

    print("\n" + "=" * 70)
    print(f"SCORE ISOLATION TENANT: {score}/100")

    if score < 50:
        print("⚠️  ATTENTION: Score critique - action immédiate requise")
    elif score < 80:
        print("⚠️  Score insuffisant - corrections recommandées")
    else:
        print("✅ Score acceptable mais des améliorations sont possibles")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Scanner d'isolation multi-tenant AZALSCORE"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Afficher les détails du scan"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Retourner exit code 1 si des violations sont trouvées"
    )
    parser.add_argument(
        "--path",
        default="app",
        help="Chemin à scanner (défaut: app)"
    )

    args = parser.parse_args()

    # Déterminer le chemin à scanner
    base_dir = Path(__file__).parent.parent.parent
    scan_path = base_dir / args.path

    if not scan_path.exists():
        print(f"Erreur: Le chemin {scan_path} n'existe pas")
        sys.exit(1)

    print(f"🔍 Scan du répertoire: {scan_path}")

    violations, files_scanned = scan_directory(str(scan_path), args.verbose)

    print_report(violations, files_scanned)

    # Mode strict pour CI/CD
    if args.strict and violations:
        critical_or_high = [v for v in violations if v.severity in ["CRITICAL", "HIGH"]]
        if critical_or_high:
            print("\n❌ Mode strict: Violations CRITICAL/HIGH détectées")
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
