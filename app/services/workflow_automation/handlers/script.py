"""
AZALSCORE - Workflow Automation Script Handler
Handler pour l'exécution de scripts Python sécurisés
"""
from __future__ import annotations

import ast
import logging
from typing import Any, Optional

from ..types import ActionConfig
from .base import ActionHandler

logger = logging.getLogger(__name__)


class ExecuteScriptHandler(ActionHandler):
    """
    Handler pour l'exécution de scripts Python sécurisés.

    SÉCURITÉ (bandit B102 - exec):
    L'utilisation de exec() est intentionnelle pour les workflows.
    Mesures de sécurité appliquées:
    1. SAFE_BUILTINS: Seules les fonctions sûres sont disponibles
    2. FORBIDDEN_KEYWORDS: Mots-clés dangereux bloqués
    3. Validation AST: Analyse syntaxique pour bloquer les patterns dangereux
    4. Double-underscore bloqué: Pas d'accès aux attributs spéciaux
    5. Taille limitée: MAX_SCRIPT_SIZE caractères maximum
    6. Isolation: Variables copiées, pas d'accès au contexte global
    """

    # Builtins sûrs autorisés - Liste blanche stricte
    SAFE_BUILTINS = {
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "float": float,
        "int": int,
        "len": len,
        "list": list,
        "max": max,
        "min": min,
        "round": round,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
        "range": range,
        "enumerate": enumerate,
        "True": True,
        "False": False,
        "None": None,
    }

    # Mots-clés dangereux interdits - Liste noire extensive
    FORBIDDEN_KEYWORDS = {
        # Exécution de code
        "import", "exec", "eval", "compile", "open", "file",
        # Introspection dangereuse
        "__import__", "__builtins__", "__class__", "__bases__",
        "__subclasses__", "__mro__", "__globals__", "__code__",
        "__dict__", "__module__", "__name__", "__qualname__",
        # Accès aux attributs
        "getattr", "setattr", "delattr", "hasattr",
        "globals", "locals", "vars", "dir",
        # Types dangereux
        "type", "object", "super", "classmethod", "staticmethod",
        # Modules système
        "os", "sys", "subprocess", "shutil", "socket", "pickle",
        "marshal", "ctypes", "multiprocessing", "threading",
        # Fichiers et I/O
        "input", "print", "breakpoint", "exit", "quit",
    }

    # Taille maximale du script (caractères)
    MAX_SCRIPT_SIZE = 10000

    def _validate_script(self, script: str) -> tuple[bool, str]:
        """
        Valide le script avant exécution avec validation AST.

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if not script or not script.strip():
            return False, "Script vide"

        if len(script) > self.MAX_SCRIPT_SIZE:
            return False, f"Script trop long (max {self.MAX_SCRIPT_SIZE} caractères)"

        # Vérifier les caractères nuls et encoding tricks
        if "\x00" in script or "\\" + "x" in script:
            return False, "Caractères invalides détectés"

        # Vérifier les mots-clés interdits
        script_lower = script.lower()
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in script_lower:
                return False, f"Mot-clé interdit: {keyword}"

        # Vérifier les tentatives d'accès aux attributs sensibles
        if "__" in script:
            return False, "Accès aux attributs spéciaux interdit"

        # Validation AST - Parse et vérifie la syntaxe
        try:
            tree = ast.parse(script, mode='exec')
        except SyntaxError as e:
            return False, f"Erreur de syntaxe: {e}"

        # Vérifier les nodes AST dangereux
        for node in ast.walk(tree):
            # Bloquer les imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return False, "Import interdit"
            # Bloquer les appels à des fonctions interdites
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_KEYWORDS:
                        return False, f"Appel interdit: {node.func.id}"
            # Bloquer l'accès aux attributs avec __
            if isinstance(node, ast.Attribute):
                if node.attr.startswith("_"):
                    return False, f"Accès attribut privé interdit: {node.attr}"

        return True, ""

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        script = params.get("script", "")

        # Validation du script
        is_valid, error_msg = self._validate_script(script)
        if not is_valid:
            logger.warning(f"Script rejeté: {error_msg}")
            return None, f"Script invalide: {error_msg}"

        try:
            local_vars = {
                "variables": dict(variables),  # Copie pour isolation
                "context": dict(context),
                "result": None
            }

            # Exécution sandbox - voir docstring classe pour mesures sécurité
            exec(  # nosec B102 - Sandbox: SAFE_BUILTINS + FORBIDDEN_KEYWORDS + AST validation
                script,
                {"__builtins__": self.SAFE_BUILTINS},
                local_vars
            )

            return local_vars.get("result"), None
        except SyntaxError as e:
            return None, f"Erreur de syntaxe: {str(e)}"
        except Exception as e:
            logger.warning(f"Erreur exécution script: {e}")
            return None, f"Erreur script: {str(e)}"
