"""
AZALSCORE - Vérification Conformité Normes Internes
====================================================
Service de vérification de la conformité du code aux normes AZALSCORE.

Standards vérifiés:
- Architecture multi-tenant
- Sécurité (OWASP, RGPD)
- Patterns de code
- Structure des modules
- Conventions API
- Logging et audit
- Tests et documentation
"""

import ast
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS ET CONSTANTES
# ============================================================================

class NormeCategorie(str, Enum):
    """Catégories de normes AZALSCORE."""
    SECURITE = "SECURITE"
    ARCHITECTURE = "ARCHITECTURE"
    CODE_QUALITY = "CODE_QUALITY"
    API_DESIGN = "API_DESIGN"
    MULTI_TENANT = "MULTI_TENANT"
    LOGGING = "LOGGING"
    TESTING = "TESTING"
    DOCUMENTATION = "DOCUMENTATION"


class Severite(str, Enum):
    """Niveaux de sévérité."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


# Patterns de sécurité à vérifier
SECURITY_PATTERNS = {
    "sql_injection": {
        "pattern": r"execute\s*\(\s*['\"].*%s.*['\"]",
        "message": "Risque d'injection SQL - Utiliser des requêtes paramétrées",
        "severity": Severite.CRITICAL
    },
    "hardcoded_secret": {
        "pattern": r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
        "message": "Secret codé en dur détecté - Utiliser des variables d'environnement",
        "severity": Severite.CRITICAL
    },
    "eval_usage": {
        "pattern": r"\beval\s*\(",
        "message": "Utilisation de eval() - Risque d'exécution de code arbitraire",
        "severity": Severite.CRITICAL
    },
    "pickle_usage": {
        "pattern": r"pickle\.(loads?|dumps?)\s*\(",
        "message": "Utilisation de pickle - Risque de désérialisation non sécurisée",
        "severity": Severite.HIGH
    },
    "os_system": {
        "pattern": r"os\.system\s*\(",
        "message": "Utilisation de os.system() - Préférer subprocess avec shell=False",
        "severity": Severite.HIGH
    },
    "shell_true": {
        "pattern": r"subprocess\.[^(]+\([^)]*shell\s*=\s*True",
        "message": "subprocess avec shell=True - Risque d'injection de commandes",
        "severity": Severite.HIGH
    },
}

# Patterns multi-tenant obligatoires
MULTITENANT_PATTERNS = {
    "tenant_filter": {
        "pattern": r"\.filter\s*\([^)]*tenant_id\s*==",
        "required_in": ["service.py", "router.py"],
        "message": "Filtrage tenant_id manquant dans les requêtes",
        "severity": Severite.CRITICAL
    },
    "tenant_param": {
        "pattern": r"def\s+\w+\([^)]*tenant_id\s*:",
        "required_in": ["service.py"],
        "message": "Paramètre tenant_id manquant dans les méthodes de service",
        "severity": Severite.HIGH
    },
}

# Structure de module attendue
MODULE_STRUCTURE = {
    "required_files": [
        "__init__.py",
        "models.py",
        "schemas.py",
        "service.py",
        "router.py",
    ],
    "optional_files": [
        "router_v2.py",
        "service_v2.py",
        "router_crud.py",
        "tests/__init__.py",
        "tests/test_router_v2.py",
        "tests/conftest.py",
    ]
}

# Conventions API
API_CONVENTIONS = {
    "version_prefix": r"^/api/v\d+/",
    "lowercase_endpoints": r"^/[a-z0-9_/-]+$",
    "plural_resources": r"/\w+s(/|$)",
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Violation:
    """Violation de norme détectée."""
    fichier: str
    ligne: int | None
    categorie: NormeCategorie
    severite: Severite
    code: str
    message: str
    suggestion: str | None = None


@dataclass
class ResultatVerification:
    """Résultat de vérification d'un module."""
    module_path: str
    module_name: str
    date_verification: datetime
    violations: list[Violation] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)
    score_conformite: int = 100
    details: dict = field(default_factory=dict)


@dataclass
class RapportConformite:
    """Rapport de conformité global."""
    date_generation: datetime
    modules_verifies: int
    modules_conformes: int
    total_violations: int
    violations_critiques: int
    violations_hautes: int
    violations_moyennes: int
    violations_basses: int
    score_global: int
    resultats_modules: list[ResultatVerification] = field(default_factory=list)
    recommandations: list[str] = field(default_factory=list)


# ============================================================================
# SERVICE DE VÉRIFICATION
# ============================================================================

class AzalscoreNormsService:
    """Service de vérification de conformité aux normes AZALSCORE."""

    def __init__(self, base_path: str = "/home/ubuntu/azalscore"):
        self.base_path = Path(base_path)
        self.app_path = self.base_path / "app"
        self.modules_path = self.app_path / "modules"

    # ========================================================================
    # VÉRIFICATION DE SÉCURITÉ
    # ========================================================================

    def verifier_securite(self, fichier: Path) -> list[Violation]:
        """Vérifier les patterns de sécurité dans un fichier."""
        violations = []

        try:
            content = fichier.read_text(encoding="utf-8")
            lines = content.split("\n")

            for code, pattern_info in SECURITY_PATTERNS.items():
                pattern = re.compile(pattern_info["pattern"], re.IGNORECASE)

                for i, line in enumerate(lines, 1):
                    # Ignorer les commentaires
                    if line.strip().startswith("#"):
                        continue

                    if pattern.search(line):
                        violations.append(Violation(
                            fichier=str(fichier.relative_to(self.base_path)),
                            ligne=i,
                            categorie=NormeCategorie.SECURITE,
                            severite=pattern_info["severity"],
                            code=f"SEC-{code.upper()}",
                            message=pattern_info["message"],
                            suggestion=self._get_security_suggestion(code)
                        ))

        except Exception as e:
            logger.error(f"Error checking security in {fichier}: {e}")

        return violations

    def _get_security_suggestion(self, code: str) -> str:
        """Obtenir une suggestion de correction pour un problème de sécurité."""
        suggestions = {
            "sql_injection": "Utiliser SQLAlchemy ORM ou des requêtes paramétrées: db.execute(text('SELECT * FROM t WHERE id = :id'), {'id': value})",
            "hardcoded_secret": "Utiliser: os.environ.get('SECRET_NAME') ou settings.secret_name",
            "eval_usage": "Utiliser ast.literal_eval() pour les expressions simples ou json.loads() pour JSON",
            "pickle_usage": "Utiliser json ou msgpack pour la sérialisation",
            "os_system": "Utiliser subprocess.run(['cmd', 'arg'], check=True, capture_output=True)",
            "shell_true": "Utiliser subprocess.run(['cmd', 'arg'], shell=False)",
        }
        return suggestions.get(code, "Consulter la documentation de sécurité AZALSCORE")

    # ========================================================================
    # VÉRIFICATION MULTI-TENANT
    # ========================================================================

    def verifier_multitenant(self, module_path: Path) -> list[Violation]:
        """Vérifier la conformité multi-tenant d'un module."""
        violations = []

        # Vérifier service.py
        service_file = module_path / "service.py"
        if service_file.exists():
            content = service_file.read_text(encoding="utf-8")

            # Vérifier présence de tenant_id dans __init__
            if "def __init__" in content:
                if "tenant_id" not in content.split("def __init__")[1].split(")")[0]:
                    violations.append(Violation(
                        fichier=str(service_file.relative_to(self.base_path)),
                        ligne=None,
                        categorie=NormeCategorie.MULTI_TENANT,
                        severite=Severite.CRITICAL,
                        code="MT-001",
                        message="tenant_id manquant dans le constructeur du service",
                        suggestion="Ajouter tenant_id: str dans __init__ et le stocker comme self.tenant_id"
                    ))

            # Vérifier les requêtes sans filtre tenant
            # Pattern: .query(...).filter(... sans tenant_id
            query_pattern = r"\.query\([^)]+\)\.filter\([^)]+\)"
            for match in re.finditer(query_pattern, content):
                if "tenant_id" not in match.group():
                    # Trouver le numéro de ligne
                    line_num = content[:match.start()].count("\n") + 1
                    violations.append(Violation(
                        fichier=str(service_file.relative_to(self.base_path)),
                        ligne=line_num,
                        categorie=NormeCategorie.MULTI_TENANT,
                        severite=Severite.CRITICAL,
                        code="MT-002",
                        message="Requête sans filtre tenant_id détectée",
                        suggestion="Ajouter .filter(Model.tenant_id == self.tenant_id)"
                    ))

        # Vérifier router.py
        router_file = module_path / "router.py"
        if router_file.exists():
            content = router_file.read_text(encoding="utf-8")

            # Vérifier injection de tenant via dépendance
            if "def get_" in content and "tenant" not in content.lower():
                violations.append(Violation(
                    fichier=str(router_file.relative_to(self.base_path)),
                    ligne=None,
                    categorie=NormeCategorie.MULTI_TENANT,
                    severite=Severite.HIGH,
                    code="MT-003",
                    message="Pas de gestion du tenant_id visible dans le router",
                    suggestion="Utiliser get_current_tenant() ou extraire tenant_id du token JWT"
                ))

        return violations

    # ========================================================================
    # VÉRIFICATION STRUCTURE MODULE
    # ========================================================================

    def verifier_structure_module(self, module_path: Path) -> list[Violation]:
        """Vérifier la structure d'un module."""
        violations = []
        module_name = module_path.name

        # Vérifier fichiers requis
        for required_file in MODULE_STRUCTURE["required_files"]:
            file_path = module_path / required_file
            if not file_path.exists():
                violations.append(Violation(
                    fichier=str(module_path.relative_to(self.base_path)),
                    ligne=None,
                    categorie=NormeCategorie.ARCHITECTURE,
                    severite=Severite.MEDIUM,
                    code="ARCH-001",
                    message=f"Fichier requis manquant: {required_file}",
                    suggestion=f"Créer {module_path}/{required_file}"
                ))

        # Vérifier __init__.py non vide
        init_file = module_path / "__init__.py"
        if init_file.exists():
            content = init_file.read_text(encoding="utf-8").strip()
            if not content:
                violations.append(Violation(
                    fichier=str(init_file.relative_to(self.base_path)),
                    ligne=None,
                    categorie=NormeCategorie.ARCHITECTURE,
                    severite=Severite.LOW,
                    code="ARCH-002",
                    message="__init__.py vide - devrait exporter les classes principales",
                    suggestion="Ajouter les exports: from .service import Service, from .models import Model"
                ))

        # Vérifier présence de tests
        tests_path = module_path / "tests"
        if not tests_path.exists() or not any(tests_path.glob("test_*.py")):
            violations.append(Violation(
                fichier=str(module_path.relative_to(self.base_path)),
                ligne=None,
                categorie=NormeCategorie.TESTING,
                severite=Severite.MEDIUM,
                code="TEST-001",
                message="Aucun test trouvé pour ce module",
                suggestion=f"Créer {module_path}/tests/test_service.py et test_router.py"
            ))

        return violations

    # ========================================================================
    # VÉRIFICATION QUALITÉ CODE
    # ========================================================================

    def verifier_qualite_code(self, fichier: Path) -> list[Violation]:
        """Vérifier la qualité du code Python."""
        violations = []

        try:
            content = fichier.read_text(encoding="utf-8")

            # Vérifier docstrings des fonctions
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Ignorer les méthodes privées et magiques
                        if node.name.startswith("_"):
                            continue

                        docstring = ast.get_docstring(node)
                        if not docstring:
                            violations.append(Violation(
                                fichier=str(fichier.relative_to(self.base_path)),
                                ligne=node.lineno,
                                categorie=NormeCategorie.DOCUMENTATION,
                                severite=Severite.LOW,
                                code="DOC-001",
                                message=f"Fonction '{node.name}' sans docstring",
                                suggestion="Ajouter une docstring décrivant le but et les paramètres"
                            ))

                    elif isinstance(node, ast.ClassDef):
                        docstring = ast.get_docstring(node)
                        if not docstring:
                            violations.append(Violation(
                                fichier=str(fichier.relative_to(self.base_path)),
                                ligne=node.lineno,
                                categorie=NormeCategorie.DOCUMENTATION,
                                severite=Severite.LOW,
                                code="DOC-002",
                                message=f"Classe '{node.name}' sans docstring",
                                suggestion="Ajouter une docstring décrivant la responsabilité de la classe"
                            ))

            except SyntaxError:
                violations.append(Violation(
                    fichier=str(fichier.relative_to(self.base_path)),
                    ligne=None,
                    categorie=NormeCategorie.CODE_QUALITY,
                    severite=Severite.CRITICAL,
                    code="SYNTAX-001",
                    message="Erreur de syntaxe Python dans le fichier",
                    suggestion="Corriger la syntaxe Python"
                ))

            # Vérifier longueur des lignes
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    violations.append(Violation(
                        fichier=str(fichier.relative_to(self.base_path)),
                        ligne=i,
                        categorie=NormeCategorie.CODE_QUALITY,
                        severite=Severite.INFO,
                        code="STYLE-001",
                        message=f"Ligne trop longue ({len(line)} > 120 caractères)",
                        suggestion="Découper la ligne sur plusieurs lignes"
                    ))

            # Vérifier imports absolus
            if "from ." not in content and "import " in content:
                pass  # OK - imports absolus

        except Exception as e:
            logger.error(f"Error checking code quality in {fichier}: {e}")

        return violations

    # ========================================================================
    # VÉRIFICATION LOGGING
    # ========================================================================

    def verifier_logging(self, fichier: Path) -> list[Violation]:
        """Vérifier l'utilisation du logging."""
        violations = []

        try:
            content = fichier.read_text(encoding="utf-8")

            # Vérifier présence de logger
            if "logger = logging.getLogger" not in content:
                if "class " in content or "def " in content:
                    # C'est un fichier avec du code - devrait avoir un logger
                    violations.append(Violation(
                        fichier=str(fichier.relative_to(self.base_path)),
                        ligne=None,
                        categorie=NormeCategorie.LOGGING,
                        severite=Severite.LOW,
                        code="LOG-001",
                        message="Module sans logger configuré",
                        suggestion="Ajouter: logger = logging.getLogger(__name__)"
                    ))

            # Vérifier print() au lieu de logger
            if re.search(r'\bprint\s*\(', content):
                for i, line in enumerate(content.split("\n"), 1):
                    if "print(" in line and not line.strip().startswith("#"):
                        violations.append(Violation(
                            fichier=str(fichier.relative_to(self.base_path)),
                            ligne=i,
                            categorie=NormeCategorie.LOGGING,
                            severite=Severite.MEDIUM,
                            code="LOG-002",
                            message="Utilisation de print() au lieu de logger",
                            suggestion="Utiliser logger.info(), logger.debug(), etc."
                        ))

        except Exception as e:
            logger.error(f"Error checking logging in {fichier}: {e}")

        return violations

    # ========================================================================
    # VÉRIFICATION API
    # ========================================================================

    def verifier_api_conventions(self, fichier: Path) -> list[Violation]:
        """Vérifier les conventions API dans les routers."""
        violations = []

        if "router" not in fichier.name:
            return violations

        try:
            content = fichier.read_text(encoding="utf-8")

            # Vérifier les réponses sans code status explicite
            if "@router." in content:
                # Vérifier présence de status_code
                route_matches = re.findall(r'@router\.(get|post|put|delete|patch)\s*\([^)]+\)', content)
                for match in route_matches:
                    # Les POST devraient avoir status_code=201
                    if "post" in match.lower() and "status_code" not in content.split(match)[1].split(")")[0]:
                        violations.append(Violation(
                            fichier=str(fichier.relative_to(self.base_path)),
                            ligne=None,
                            categorie=NormeCategorie.API_DESIGN,
                            severite=Severite.LOW,
                            code="API-001",
                            message="Route POST sans status_code=201 explicite",
                            suggestion="Ajouter status_code=status.HTTP_201_CREATED"
                        ))

            # Vérifier les réponses d'erreur
            if "HTTPException" in content and "detail" not in content:
                violations.append(Violation(
                    fichier=str(fichier.relative_to(self.base_path)),
                    ligne=None,
                    categorie=NormeCategorie.API_DESIGN,
                    severite=Severite.MEDIUM,
                    code="API-002",
                    message="HTTPException sans détail descriptif",
                    suggestion="Ajouter detail='Message explicatif' aux HTTPException"
                ))

        except Exception as e:
            logger.error(f"Error checking API conventions in {fichier}: {e}")

        return violations

    # ========================================================================
    # VÉRIFICATION COMPLÈTE D'UN MODULE
    # ========================================================================

    def verifier_module(self, module_path: Path) -> ResultatVerification:
        """Vérifier un module complet."""
        module_name = module_path.name
        logger.info(f"Verifying module: {module_name}")

        result = ResultatVerification(
            module_path=str(module_path),
            module_name=module_name,
            date_verification=datetime.utcnow()
        )

        # Vérifier structure
        result.violations.extend(self.verifier_structure_module(module_path))

        # Vérifier chaque fichier Python
        for py_file in module_path.rglob("*.py"):
            # Sécurité
            result.violations.extend(self.verifier_securite(py_file))

            # Qualité code
            result.violations.extend(self.verifier_qualite_code(py_file))

            # Logging
            result.violations.extend(self.verifier_logging(py_file))

            # API (pour routers)
            result.violations.extend(self.verifier_api_conventions(py_file))

        # Multi-tenant
        result.violations.extend(self.verifier_multitenant(module_path))

        # Calculer le score
        result.score_conformite = self._calculer_score(result.violations)

        # Stats
        result.details = {
            "total_violations": len(result.violations),
            "critical": sum(1 for v in result.violations if v.severite == Severite.CRITICAL),
            "high": sum(1 for v in result.violations if v.severite == Severite.HIGH),
            "medium": sum(1 for v in result.violations if v.severite == Severite.MEDIUM),
            "low": sum(1 for v in result.violations if v.severite == Severite.LOW),
            "info": sum(1 for v in result.violations if v.severite == Severite.INFO),
        }

        return result

    def _calculer_score(self, violations: list[Violation]) -> int:
        """Calculer le score de conformité."""
        score = 100

        for v in violations:
            if v.severite == Severite.CRITICAL:
                score -= 20
            elif v.severite == Severite.HIGH:
                score -= 10
            elif v.severite == Severite.MEDIUM:
                score -= 5
            elif v.severite == Severite.LOW:
                score -= 2
            elif v.severite == Severite.INFO:
                score -= 1

        return max(0, score)

    # ========================================================================
    # RAPPORT GLOBAL
    # ========================================================================

    def generer_rapport_global(self) -> RapportConformite:
        """Générer un rapport de conformité pour tous les modules."""
        logger.info("Generating global compliance report")

        rapport = RapportConformite(
            date_generation=datetime.utcnow(),
            modules_verifies=0,
            modules_conformes=0,
            total_violations=0,
            violations_critiques=0,
            violations_hautes=0,
            violations_moyennes=0,
            violations_basses=0,
            score_global=0
        )

        # Parcourir tous les modules
        if not self.modules_path.exists():
            logger.warning(f"Modules path not found: {self.modules_path}")
            return rapport

        modules = [d for d in self.modules_path.iterdir() if d.is_dir() and not d.name.startswith("_")]

        for module_path in modules:
            result = self.verifier_module(module_path)
            rapport.resultats_modules.append(result)
            rapport.modules_verifies += 1

            if result.score_conformite >= 80:
                rapport.modules_conformes += 1

            rapport.total_violations += result.details.get("total_violations", 0)
            rapport.violations_critiques += result.details.get("critical", 0)
            rapport.violations_hautes += result.details.get("high", 0)
            rapport.violations_moyennes += result.details.get("medium", 0)
            rapport.violations_basses += result.details.get("low", 0)

        # Score global
        if rapport.modules_verifies > 0:
            scores = [r.score_conformite for r in rapport.resultats_modules]
            rapport.score_global = sum(scores) // len(scores)

        # Recommandations
        if rapport.violations_critiques > 0:
            rapport.recommandations.append(
                f"URGENT: {rapport.violations_critiques} violations critiques à corriger immédiatement (sécurité, multi-tenant)"
            )

        if rapport.violations_hautes > 0:
            rapport.recommandations.append(
                f"IMPORTANT: {rapport.violations_hautes} violations hautes à corriger rapidement"
            )

        modules_non_conformes = [
            r.module_name for r in rapport.resultats_modules
            if r.score_conformite < 80
        ]
        if modules_non_conformes:
            rapport.recommandations.append(
                f"Modules à améliorer: {', '.join(modules_non_conformes[:5])}"
            )

        logger.info(
            "Global report generated | modules=%s conformes=%s score=%s",
            rapport.modules_verifies, rapport.modules_conformes, rapport.score_global
        )

        return rapport

    def exporter_rapport_json(self, rapport: RapportConformite) -> dict:
        """Exporter le rapport en format JSON."""
        return {
            "metadata": {
                "date_generation": rapport.date_generation.isoformat(),
                "version": "1.0",
                "standard": "AZALSCORE-NORMS-2024"
            },
            "summary": {
                "modules_verifies": rapport.modules_verifies,
                "modules_conformes": rapport.modules_conformes,
                "taux_conformite": f"{(rapport.modules_conformes / max(1, rapport.modules_verifies)) * 100:.1f}%",
                "score_global": rapport.score_global,
                "total_violations": rapport.total_violations,
                "violations_par_severite": {
                    "critical": rapport.violations_critiques,
                    "high": rapport.violations_hautes,
                    "medium": rapport.violations_moyennes,
                    "low": rapport.violations_basses
                }
            },
            "modules": [
                {
                    "name": r.module_name,
                    "score": r.score_conformite,
                    "violations": r.details,
                    "details": [
                        {
                            "fichier": v.fichier,
                            "ligne": v.ligne,
                            "categorie": v.categorie.value,
                            "severite": v.severite.value,
                            "code": v.code,
                            "message": v.message,
                            "suggestion": v.suggestion
                        }
                        for v in r.violations
                    ]
                }
                for r in rapport.resultats_modules
            ],
            "recommandations": rapport.recommandations
        }
