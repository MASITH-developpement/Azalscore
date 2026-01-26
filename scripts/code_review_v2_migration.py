#!/usr/bin/env python3
"""
Code Review Automatisé - Migration CORE SaaS v2
================================================
Analyse tous les modules migrés et génère un rapport de qualité.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict


class CodeReviewAnalyzer:
    """Analyseur de code pour la migration v2."""

    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
        self.modules_analyzed = []

    def analyze_module(self, module_name: str) -> Dict:
        """Analyse complète d'un module."""
        module_path = Path(f"app/modules/{module_name}")

        result = {
            "name": module_name,
            "files_present": {},
            "issues": [],
            "stats": {},
            "score": 0
        }

        # Vérifier présence des fichiers
        files_to_check = {
            "service.py": module_path / "service.py",
            "router_v2.py": module_path / "router_v2.py",
            "tests/conftest.py": module_path / "tests" / "conftest.py",
            "tests/test_router_v2.py": module_path / "tests" / "test_router_v2.py"
        }

        for file_key, file_path in files_to_check.items():
            result["files_present"][file_key] = file_path.exists()

        # Analyser service.py
        if result["files_present"]["service.py"]:
            service_issues = self._analyze_service(module_path / "service.py")
            result["issues"].extend(service_issues)

        # Analyser router_v2.py
        if result["files_present"]["router_v2.py"]:
            router_issues = self._analyze_router(module_path / "router_v2.py")
            result["issues"].extend(router_issues)
            result["stats"]["endpoints"] = self._count_endpoints(module_path / "router_v2.py")

        # Analyser tests
        if result["files_present"]["tests/test_router_v2.py"]:
            test_issues = self._analyze_tests(module_path / "tests" / "test_router_v2.py")
            result["issues"].extend(test_issues)
            result["stats"]["tests"] = self._count_tests(module_path / "tests" / "test_router_v2.py")

        # Calculer le score
        result["score"] = self._calculate_score(result)

        return result

    def _analyze_service(self, file_path: Path) -> List[Dict]:
        """Analyse le fichier service.py."""
        issues = []
        content = file_path.read_text()

        # Vérifier user_id parameter dans __init__
        if "def __init__" in content:
            if "user_id" not in content:
                issues.append({
                    "severity": "ERROR",
                    "file": str(file_path),
                    "message": "Service __init__ manque le paramètre user_id"
                })

        # Vérifier tenant_id
        if "tenant_id" not in content:
            issues.append({
                "severity": "WARNING",
                "file": str(file_path),
                "message": "tenant_id non trouvé dans le service"
            })

        # Vérifier imports
        if "from sqlalchemy.orm import Session" not in content:
            issues.append({
                "severity": "INFO",
                "file": str(file_path),
                "message": "Import Session manquant"
            })

        return issues

    def _analyze_router(self, file_path: Path) -> List[Dict]:
        """Analyse le fichier router_v2.py."""
        issues = []
        content = file_path.read_text()

        # Vérifier imports CORE SaaS v2
        required_imports = [
            "from app.core.dependencies_v2 import get_saas_context",
            "from app.core.saas_context import SaaSContext"
        ]

        for imp in required_imports:
            if imp not in content:
                issues.append({
                    "severity": "ERROR",
                    "file": str(file_path),
                    "message": f"Import manquant: {imp}"
                })

        # Vérifier utilisation de SaaSContext
        if "context: SaaSContext = Depends(get_saas_context)" not in content:
            issues.append({
                "severity": "WARNING",
                "file": str(file_path),
                "message": "Pattern SaaSContext non utilisé dans les endpoints"
            })

        # Vérifier prefix /v2
        if 'prefix="/v2/' not in content:
            issues.append({
                "severity": "ERROR",
                "file": str(file_path),
                "message": "Prefix /v2/ manquant dans APIRouter"
            })

        # Vérifier factory function
        factory_pattern = r'def get_\w+_service\('
        if not re.search(factory_pattern, content):
            issues.append({
                "severity": "WARNING",
                "file": str(file_path),
                "message": "Factory function pour le service manquante"
            })

        # Vérifier gestion d'erreurs
        if "HTTPException" not in content:
            issues.append({
                "severity": "INFO",
                "file": str(file_path),
                "message": "Aucune HTTPException levée (peut être normal)"
            })

        return issues

    def _analyze_tests(self, file_path: Path) -> List[Dict]:
        """Analyse le fichier de tests."""
        issues = []
        content = file_path.read_text()

        # Vérifier que pytest est utilisé
        if "import pytest" not in content:
            issues.append({
                "severity": "ERROR",
                "file": str(file_path),
                "message": "Import pytest manquant"
            })

        # Vérifier présence de tests
        if "def test_" not in content:
            issues.append({
                "severity": "ERROR",
                "file": str(file_path),
                "message": "Aucune fonction de test trouvée"
            })

        # Vérifier utilisation de test_client fixture
        if "test_client" not in content:
            issues.append({
                "severity": "WARNING",
                "file": str(file_path),
                "message": "Fixture test_client non utilisée (conftest global requis)"
            })

        return issues

    def _count_endpoints(self, file_path: Path) -> int:
        """Compte le nombre d'endpoints dans le router."""
        content = file_path.read_text()
        # Compte les décorateurs @router.get, @router.post, etc.
        return len(re.findall(r'@router\.(get|post|put|delete|patch)', content))

    def _count_tests(self, file_path: Path) -> int:
        """Compte le nombre de tests."""
        content = file_path.read_text()
        return len(re.findall(r'def test_\w+\(', content))

    def _calculate_score(self, result: Dict) -> int:
        """Calcule un score de qualité sur 100."""
        score = 100

        # Pénalités pour fichiers manquants
        for file_key, present in result["files_present"].items():
            if not present:
                if "router_v2" in file_key:
                    score -= 30  # Critique
                elif "service" in file_key:
                    score -= 20  # Important
                elif "test" in file_key:
                    score -= 15  # Important

        # Pénalités pour issues
        for issue in result["issues"]:
            if issue["severity"] == "ERROR":
                score -= 10
            elif issue["severity"] == "WARNING":
                score -= 5
            elif issue["severity"] == "INFO":
                score -= 2

        return max(0, score)

    def analyze_all_modules(self) -> Dict:
        """Analyse tous les modules."""
        modules_dir = Path("app/modules")

        # Liste des modules à analyser
        modules = sorted([
            d.name for d in modules_dir.iterdir()
            if d.is_dir() and not d.name.startswith(("_", "."))
        ])

        results = []
        total_endpoints = 0
        total_tests = 0

        for module in modules:
            print(f"📊 Analyse: {module}...")
            result = self.analyze_module(module)
            results.append(result)

            total_endpoints += result["stats"].get("endpoints", 0)
            total_tests += result["stats"].get("tests", 0)

        # Générer le rapport
        return {
            "modules": results,
            "summary": {
                "total_modules": len(results),
                "total_endpoints": total_endpoints,
                "total_tests": total_tests,
                "avg_score": sum(r["score"] for r in results) / len(results) if results else 0,
                "modules_with_issues": len([r for r in results if r["issues"]]),
                "critical_issues": sum(
                    len([i for i in r["issues"] if i["severity"] == "ERROR"])
                    for r in results
                )
            }
        }


def generate_report(analysis: Dict) -> str:
    """Génère un rapport markdown."""
    report = []

    report.append("# Code Review - Migration CORE SaaS v2")
    report.append("")
    report.append("## 📊 Résumé Global")
    report.append("")

    summary = analysis["summary"]
    report.append(f"- **Modules analysés**: {summary['total_modules']}")
    report.append(f"- **Endpoints v2 totaux**: {summary['total_endpoints']}")
    report.append(f"- **Tests totaux**: {summary['total_tests']}")
    report.append(f"- **Score moyen**: {summary['avg_score']:.1f}/100")
    report.append(f"- **Modules avec issues**: {summary['modules_with_issues']}")
    report.append(f"- **Issues critiques**: {summary['critical_issues']}")
    report.append("")

    # Modules par score
    report.append("## 🎯 Modules par Score")
    report.append("")

    modules_sorted = sorted(analysis["modules"], key=lambda x: x["score"], reverse=True)

    report.append("| Module | Score | Endpoints | Tests | Issues |")
    report.append("|--------|-------|-----------|-------|--------|")

    for module in modules_sorted:
        score_emoji = "🟢" if module["score"] >= 80 else "🟡" if module["score"] >= 60 else "🔴"
        report.append(
            f"| {module['name']} | {score_emoji} {module['score']}/100 | "
            f"{module['stats'].get('endpoints', 0)} | "
            f"{module['stats'].get('tests', 0)} | "
            f"{len(module['issues'])} |"
        )

    report.append("")

    # Issues par sévérité
    report.append("## ⚠️ Issues par Sévérité")
    report.append("")

    all_issues = []
    for module in analysis["modules"]:
        for issue in module["issues"]:
            issue["module"] = module["name"]
            all_issues.append(issue)

    # Grouper par sévérité
    issues_by_severity = defaultdict(list)
    for issue in all_issues:
        issues_by_severity[issue["severity"]].append(issue)

    for severity in ["ERROR", "WARNING", "INFO"]:
        if severity in issues_by_severity:
            emoji = "🔴" if severity == "ERROR" else "🟡" if severity == "WARNING" else "ℹ️"
            report.append(f"### {emoji} {severity} ({len(issues_by_severity[severity])})")
            report.append("")

            for issue in issues_by_severity[severity][:10]:  # Top 10
                report.append(f"- **{issue['module']}**: {issue['message']}")

            if len(issues_by_severity[severity]) > 10:
                report.append(f"- ... et {len(issues_by_severity[severity]) - 10} autres")

            report.append("")

    # Top 10 modules
    report.append("## 🏆 Top 10 Modules (Meilleur Score)")
    report.append("")

    for i, module in enumerate(modules_sorted[:10], 1):
        report.append(f"{i}. **{module['name']}** - {module['score']}/100")
        report.append(f"   - Endpoints: {module['stats'].get('endpoints', 0)}")
        report.append(f"   - Tests: {module['stats'].get('tests', 0)}")
        report.append(f"   - Issues: {len(module['issues'])}")
        report.append("")

    # Recommandations
    report.append("## 💡 Recommandations")
    report.append("")

    if summary["critical_issues"] > 0:
        report.append("### Priorité Haute")
        report.append(f"- Corriger les {summary['critical_issues']} issues critiques")
        report.append("")

    modules_low_score = [m for m in analysis["modules"] if m["score"] < 60]
    if modules_low_score:
        report.append("### Modules à Revoir")
        for module in modules_low_score:
            report.append(f"- **{module['name']}** (score: {module['score']}/100)")
        report.append("")

    report.append("### Actions Suggérées")
    report.append("1. Vérifier que tous les modules ont router_v2.py")
    report.append("2. S'assurer que SaaSContext est utilisé partout")
    report.append("3. Ajouter tests manquants pour coverage ≥50%")
    report.append("4. Standardiser les factory functions")
    report.append("")

    # Statistiques finales
    report.append("## 📈 Statistiques de Migration")
    report.append("")
    report.append(f"- **Ratio endpoints/module**: {summary['total_endpoints'] / summary['total_modules']:.1f}")
    report.append(f"- **Ratio tests/module**: {summary['total_tests'] / summary['total_modules']:.1f}")
    report.append(f"- **Coverage estimée**: ~{min(100, (summary['total_tests'] / max(1, summary['total_endpoints'])) * 100):.0f}%")
    report.append("")

    report.append("---")
    report.append("")
    report.append("**Généré par**: Code Review Automatisé")
    report.append(f"**Date**: {Path('.').absolute()}")
    report.append("")

    return "\n".join(report)


def main():
    """Main function."""
    print("🔍 Code Review - Migration CORE SaaS v2")
    print("=" * 50)
    print()

    analyzer = CodeReviewAnalyzer()
    analysis = analyzer.analyze_all_modules()

    print()
    print("✅ Analyse terminée!")
    print()
    print(f"📊 {analysis['summary']['total_modules']} modules analysés")
    print(f"🎯 Score moyen: {analysis['summary']['avg_score']:.1f}/100")
    print(f"⚠️  {analysis['summary']['critical_issues']} issues critiques")
    print()

    # Générer le rapport
    report = generate_report(analysis)

    # Sauvegarder
    output_file = Path("CODE_REVIEW_V2_MIGRATION.md")
    output_file.write_text(report)

    print(f"📄 Rapport généré: {output_file}")
    print()

    return 0 if analysis['summary']['critical_issues'] == 0 else 1


if __name__ == "__main__":
    exit(main())
