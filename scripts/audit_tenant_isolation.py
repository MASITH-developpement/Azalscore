#!/usr/bin/env python3
"""
AZALS - Script d'audit d'isolation multi-tenant
================================================

Ce script analyse le code source pour détecter les requêtes SQL
potentiellement non isolées par tenant_id.

AVERTISSEMENT: Un résultat positif ne signifie pas nécessairement
une vulnérabilité. Une analyse manuelle est requise pour chaque cas.

Usage:
    python scripts/audit_tenant_isolation.py
    python scripts/audit_tenant_isolation.py --fix  # Mode correction (non implémenté)
"""

import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Set


@dataclass
class IsolationIssue:
    """Représente un problème d'isolation potentiel."""
    file_path: str
    line_number: int
    code_snippet: str
    model_name: str
    severity: str  # CRITICAL, WARNING, INFO
    context: str


def get_all_models() -> Set[str]:
    """Récupère tous les noms de modèles SQLAlchemy du projet."""
    models = set()
    models_dirs = [
        "app/core/models.py",
        "app/modules"
    ]

    model_pattern = re.compile(r'class\s+(\w+)\s*\([^)]*Base[^)]*\)')

    for path in models_dirs:
        if os.path.isfile(path):
            with open(path, 'r') as f:
                for match in model_pattern.finditer(f.read()):
                    models.add(match.group(1))
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file == 'models.py':
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r') as f:
                                for match in model_pattern.finditer(f.read()):
                                    models.add(match.group(1))
                        except:
                            pass

    return models


def find_tenant_id_in_context(lines: List[str], start_idx: int, max_lines: int = 10) -> bool:
    """
    Vérifie si tenant_id apparaît dans le contexte de la requête.
    Analyse les lignes suivantes jusqu'à trouver un point-virgule ou max_lines.
    """
    context = []
    paren_count = 0

    for i in range(start_idx, min(start_idx + max_lines, len(lines))):
        line = lines[i]
        context.append(line)

        # Compter les parenthèses pour trouver la fin de la requête
        paren_count += line.count('(') - line.count(')')

        # Si tenant_id est trouvé dans le contexte
        if 'tenant_id' in line.lower():
            return True

        # Si on trouve .all(), .first(), .one(), .count(), .scalar()
        if any(end in line for end in ['.all()', '.first()', '.one()', '.count()', '.scalar()', '.delete()', '.update(']):
            break

        # Si les parenthèses sont fermées et qu'on a une fin de statement
        if paren_count <= 0 and (line.strip().endswith(')') or ';' in line):
            break

    return False


def audit_file(filepath: str, all_models: Set[str]) -> List[IsolationIssue]:
    """Audite un fichier pour les problèmes d'isolation."""
    issues = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return issues

    # Patterns de requête à vérifier
    query_patterns = [
        (r'\.query\s*\(\s*(\w+)\s*\)', 'query'),
        (r'select\s*\(\s*(\w+)\s*\)', 'select'),
        (r'db\.execute\s*\(', 'execute'),
        (r'session\.execute\s*\(', 'execute'),
    ]

    for i, line in enumerate(lines):
        # Ignorer les commentaires
        stripped = line.strip()
        if stripped.startswith('#'):
            continue

        # Chercher les patterns de requête
        for pattern, query_type in query_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                # Extraire le nom du modèle si possible
                model_name = match.group(1) if match.lastindex and match.lastindex >= 1 else "Unknown"

                # Vérifier si tenant_id est dans le contexte
                has_tenant_filter = find_tenant_id_in_context(lines, i, max_lines=15)

                if not has_tenant_filter:
                    # Déterminer la sévérité
                    severity = "CRITICAL"

                    # Les requêtes sur Tenant lui-même sont OK
                    if model_name in ['Tenant', 'TenantInvitation', 'TrialRegistration']:
                        severity = "INFO"

                    # Les fichiers de migration sont OK
                    if 'alembic' in filepath or 'migration' in filepath.lower():
                        severity = "INFO"

                    # Les fichiers de test sont moins critiques
                    if 'test' in filepath.lower():
                        severity = "WARNING"

                    issues.append(IsolationIssue(
                        file_path=filepath,
                        line_number=i + 1,
                        code_snippet=line.strip()[:100],
                        model_name=model_name,
                        severity=severity,
                        context='\n'.join(lines[max(0, i-1):min(len(lines), i+5)])
                    ))

    return issues


def main():
    """Point d'entrée principal."""
    print("=" * 80)
    print("AZALSCORE - Audit d'isolation multi-tenant")
    print("=" * 80)
    print()

    # Changer vers le répertoire du projet
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    # Récupérer tous les modèles
    all_models = get_all_models()
    print(f"Modèles SQLAlchemy détectés: {len(all_models)}")

    # Scanner les fichiers
    all_issues = []
    scanned_files = 0

    for root, dirs, files in os.walk('app/modules'):
        # Ignorer les répertoires de cache et tests
        dirs[:] = [d for d in dirs if '__pycache__' not in d]

        for file in files:
            if not file.endswith('.py'):
                continue

            filepath = os.path.join(root, file)
            scanned_files += 1
            issues = audit_file(filepath, all_models)
            all_issues.extend(issues)

    # Trier par sévérité
    severity_order = {'CRITICAL': 0, 'WARNING': 1, 'INFO': 2}
    all_issues.sort(key=lambda x: (severity_order.get(x.severity, 99), x.file_path))

    # Afficher les résultats
    print(f"Fichiers scannés: {scanned_files}")
    print(f"Problèmes potentiels détectés: {len(all_issues)}")
    print()

    # Regrouper par sévérité
    critical = [i for i in all_issues if i.severity == 'CRITICAL']
    warnings = [i for i in all_issues if i.severity == 'WARNING']
    info = [i for i in all_issues if i.severity == 'INFO']

    print(f"  CRITICAL: {len(critical)}")
    print(f"  WARNING:  {len(warnings)}")
    print(f"  INFO:     {len(info)}")
    print()

    if critical:
        print("=" * 80)
        print("PROBLÈMES CRITIQUES (requièrent une analyse manuelle)")
        print("=" * 80)

        for issue in critical[:30]:  # Limiter l'affichage
            print(f"\n[{issue.severity}] {issue.file_path}:{issue.line_number}")
            print(f"  Modèle: {issue.model_name}")
            print(f"  Code: {issue.code_snippet}")

    # Générer un rapport détaillé
    report_path = 'reports/tenant_isolation_audit.txt'
    os.makedirs('reports', exist_ok=True)

    with open(report_path, 'w') as f:
        f.write("AZALSCORE - Rapport d'audit d'isolation multi-tenant\n")
        f.write("=" * 80 + "\n")
        f.write(f"Date: {__import__('datetime').datetime.now().isoformat()}\n")
        f.write(f"Fichiers scannés: {scanned_files}\n")
        f.write(f"Problèmes détectés: {len(all_issues)}\n")
        f.write(f"  CRITICAL: {len(critical)}\n")
        f.write(f"  WARNING: {len(warnings)}\n")
        f.write(f"  INFO: {len(info)}\n")
        f.write("\n" + "=" * 80 + "\n\n")

        for issue in all_issues:
            f.write(f"[{issue.severity}] {issue.file_path}:{issue.line_number}\n")
            f.write(f"  Modèle: {issue.model_name}\n")
            f.write(f"  Code: {issue.code_snippet}\n")
            f.write(f"  Contexte:\n")
            for ctx_line in issue.context.split('\n'):
                f.write(f"    {ctx_line}\n")
            f.write("\n")

    print(f"\nRapport détaillé généré: {report_path}")

    # Code de sortie basé sur les problèmes critiques
    if critical:
        print(f"\n⚠️  {len(critical)} problèmes CRITIQUES détectés - analyse manuelle requise")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
