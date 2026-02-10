#!/usr/bin/env python3
"""
Générateur automatique de sous-programmes AZALSCORE

Lit le fichier subprograms_definitions.json et génère automatiquement :
- manifest.json (complet et validé)
- impl.py (template fonctionnel)
- tests/test_*.py (tests de base)

Usage:
    python scripts/generators/generate_all_subprograms.py [--dry-run] [--force]

Options:
    --dry-run    Affiche ce qui serait créé sans créer les fichiers
    --force      Écrase les fichiers existants
    --category   Génère uniquement une catégorie (ex: calculations, validators)
    --stats      Affiche uniquement les statistiques

Conformité : AZA-NF-003, Charte Développeur
Principe : "Automatisation de la création de sous-programmes atomiques"
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import argparse


class SubprogramGenerator:
    """Générateur de sous-programmes AZALSCORE"""

    def __init__(self, registry_path: Path, definitions_path: Path):
        self.registry_path = registry_path
        self.definitions_path = definitions_path
        self.stats = {
            "total": 0,
            "created": 0,
            "skipped": 0,
            "errors": 0
        }

    def load_definitions(self) -> Dict[str, Any]:
        """Charge le fichier de définitions JSON"""
        with open(self.definitions_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_manifest(self, category: str, module: str, submodule: str,
                          subprogram: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un manifest.json complet"""

        # Construction de l'ID
        subprogram_id = f"azalscore.{category}.{module}.{subprogram['name']}"

        # Construction du manifest
        manifest = {
            "id": subprogram_id,
            "name": subprogram.get("description", subprogram["name"]),
            "category": category,
            "version": "1.0.0",
            "description": subprogram.get("description", ""),
            "inputs": {},
            "outputs": {},
            "side_effects": subprogram.get("side_effects", False),
            "idempotent": subprogram.get("idempotent", True),
            "no_code_compatible": True,
            "retry_strategy": {
                "max_attempts": 3 if subprogram.get("side_effects") else 1,
                "timeout_ms": 5000 if subprogram.get("side_effects") else 1000,
                "fallback": None
            },
            "dependencies": [],
            "tags": [category, module, submodule],
            "author": "AZALSCORE",
            "license": "Proprietary",
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "updated_at": datetime.now().strftime("%Y-%m-%d")
        }

        # Conversion des inputs
        for input_name, input_spec in subprogram.get("inputs", {}).items():
            manifest["inputs"][input_name] = {
                "type": input_spec.get("type", "string"),
                "required": input_spec.get("required", True),
                "description": input_spec.get("description", "")
            }
            if "default" in input_spec:
                manifest["inputs"][input_name]["default"] = input_spec["default"]

        # Conversion des outputs
        for output_name, output_spec in subprogram.get("outputs", {}).items():
            manifest["outputs"][output_name] = {
                "type": output_spec.get("type", "string"),
                "description": output_spec.get("description", "")
            }

        return manifest

    def generate_implementation(self, category: str, module: str,
                                subprogram: Dict[str, Any]) -> str:
        """Génère un fichier impl.py fonctionnel"""

        name = subprogram["name"]
        description = subprogram.get("description", "")
        usage_count = subprogram.get("usage_count", 0)

        impl_code = f'''"""
Implémentation du sous-programme : {name}

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects{" (DÉCLARÉ)" if subprogram.get("side_effects") else ""}
- Idempotent{"" if subprogram.get("idempotent") else " (NON)"}

Utilisation : {usage_count}+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    {description}

    Args:
        inputs: {{'''

        # Génération de la doc des inputs
        for input_name, input_spec in subprogram.get("inputs", {}).items():
            impl_code += f'''
            "{input_name}": {input_spec.get("type", "str")},  # {input_spec.get("description", "")}'''

        impl_code += '''
        }

    Returns:
        {'''

        # Génération de la doc des outputs
        for output_name, output_spec in subprogram.get("outputs", {}).items():
            impl_code += f'''
            "{output_name}": {output_spec.get("type", "str")},  # {output_spec.get("description", "")}'''

        impl_code += '''
        }
    """
    # TODO: Implémenter la logique métier
'''

        # Extraction des inputs
        for input_name in subprogram.get("inputs", {}).keys():
            default = subprogram["inputs"][input_name].get("default")
            if default is not None:
                impl_code += f'''
    {input_name} = inputs.get("{input_name}", {repr(default)})'''
            else:
                impl_code += f'''
    {input_name} = inputs["{input_name}"]'''

        impl_code += '''

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique
'''

        # Génération du return
        impl_code += '''
    return {'''

        for output_name in subprogram.get("outputs", {}).keys():
            impl_code += f'''
        "{output_name}": None,  # TODO: Calculer la valeur'''

        impl_code += '''
    }
'''

        return impl_code

    def generate_tests(self, category: str, module: str,
                      subprogram: Dict[str, Any]) -> str:
        """Génère un fichier de tests basique"""

        name = subprogram["name"]

        test_code = f'''"""
Tests du sous-programme {name}

Couverture cible : >= 80%
"""

import pytest
from ..impl import execute


class Test{name.title().replace("_", "")}:
    """Tests du sous-programme {name}"""

    def test_basic_execution(self):
        """Test d'exécution basique"""
        # TODO: Ajuster selon les inputs réels
        inputs = {{'''

        # Génération d'inputs de test
        for input_name, input_spec in subprogram.get("inputs", {}).items():
            input_type = input_spec.get("type", "string")
            if input_type == "number":
                test_value = "100.0"
            elif input_type == "boolean":
                test_value = "True"
            elif input_type == "array":
                test_value = "[]"
            elif input_type == "object":
                test_value = "{}"
            else:
                test_value = '"test_value"'

            test_code += f'''
            "{input_name}": {test_value},'''

        test_code += '''
        }

        result = execute(inputs)

        # Vérifications basiques
        assert result is not None
        assert isinstance(result, dict)
'''

        # Vérification des outputs
        for output_name in subprogram.get("outputs", {}).keys():
            test_code += f'''
        assert "{output_name}" in result'''

        test_code += '''

    def test_idempotence(self):
        """Test d'idempotence (même input = même output)"""
        inputs = {{'''

        for input_name, input_spec in subprogram.get("inputs", {}).items():
            input_type = input_spec.get("type", "string")
            if input_type == "number":
                test_value = "100.0"
            else:
                test_value = '"test_value"'
            test_code += f'''
            "{input_name}": {test_value},'''

        test_code += '''
        }

        result1 = execute(inputs)
        result2 = execute(inputs)
        result3 = execute(inputs)

        assert result1 == result2 == result3

    def test_no_side_effects_on_inputs(self):
        """Test absence d'effets de bord sur les inputs"""
        inputs = {{'''

        for input_name in subprogram.get("inputs", {}).keys():
            test_code += f'''
            "{input_name}": "test",'''

        test_code += '''
        }
        inputs_copy = inputs.copy()

        execute(inputs)

        # Les inputs ne doivent pas être modifiés
        assert inputs == inputs_copy
'''

        return test_code

    def create_subprogram(self, category: str, module: str, submodule: str,
                         subprogram: Dict[str, Any], dry_run: bool = False,
                         force: bool = False) -> bool:
        """Crée un sous-programme complet (manifest + impl + tests)"""

        name = subprogram["name"]
        self.stats["total"] += 1

        # Construction du chemin
        subprogram_path = (
            self.registry_path / category / module / name
        )

        # Vérification existence
        if subprogram_path.exists() and not force:
            print(f"  ⚠️  Existe déjà : {category}/{module}/{name}")
            self.stats["skipped"] += 1
            return False

        if dry_run:
            print(f"  [DRY-RUN] Créerait : {category}/{module}/{name}")
            return True

        try:
            # Création des répertoires
            subprogram_path.mkdir(parents=True, exist_ok=True)
            tests_path = subprogram_path / "tests"
            tests_path.mkdir(exist_ok=True)

            # Génération manifest.json
            manifest = self.generate_manifest(category, module, submodule, subprogram)
            manifest_file = subprogram_path / "manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            # Génération impl.py
            impl_code = self.generate_implementation(category, module, subprogram)
            impl_file = subprogram_path / "impl.py"
            with open(impl_file, 'w', encoding='utf-8') as f:
                f.write(impl_code)

            # Génération tests
            test_code = self.generate_tests(category, module, subprogram)
            test_file = tests_path / f"test_{name}.py"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_code)

            # Création __init__.py pour tests
            init_file = tests_path / "__init__.py"
            init_file.touch()

            print(f"  ✅ Créé : {category}/{module}/{name}")
            self.stats["created"] += 1
            return True

        except Exception as e:
            print(f"  ❌ Erreur : {category}/{module}/{name} - {e}")
            self.stats["errors"] += 1
            return False

    def generate_all(self, dry_run: bool = False, force: bool = False,
                    category_filter: str = None):
        """Génère tous les sous-programmes définis"""

        definitions = self.load_definitions()

        print(f"\n🚀 GÉNÉRATEUR DE SOUS-PROGRAMMES AZALSCORE")
        print(f"Registry : {self.registry_path}")
        print(f"Mode : {'DRY-RUN' if dry_run else 'PRODUCTION'}")
        if force:
            print(f"Force : Écrasement des fichiers existants activé")
        if category_filter:
            print(f"Filtre : Catégorie '{category_filter}' uniquement")
        print()

        # Parcours des catégories
        for category_name, category_data in definitions.get("categories", {}).items():
            if category_filter and category_name != category_filter:
                continue

            print(f"\n📦 Catégorie : {category_name}")
            print(f"   {category_data.get('description', '')}")

            # Parcours des modules
            for module_name, module_data in category_data.get("modules", {}).items():
                print(f"\n  📁 Module : {module_name}")

                # Parcours des sous-modules
                for submodule_name, subprograms in module_data.items():
                    if subprograms:
                        print(f"    📂 Sous-module : {submodule_name} ({len(subprograms)} sous-programmes)")

                        for subprogram in subprograms:
                            self.create_subprogram(
                                category_name,
                                module_name,
                                submodule_name,
                                subprogram,
                                dry_run=dry_run,
                                force=force
                            )

    def print_stats(self):
        """Affiche les statistiques"""
        print(f"\n📊 STATISTIQUES")
        print(f"Total définis : {self.stats['total']}")
        print(f"✅ Créés : {self.stats['created']}")
        print(f"⚠️  Ignorés : {self.stats['skipped']}")
        print(f"❌ Erreurs : {self.stats['errors']}")
        print()


def main():
    """Point d'entrée principal"""

    parser = argparse.ArgumentParser(
        description="Génère automatiquement tous les sous-programmes AZALSCORE"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche ce qui serait créé sans créer les fichiers"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Écrase les fichiers existants"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Génère uniquement une catégorie (ex: calculations, validators)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Affiche uniquement les statistiques sans générer"
    )

    args = parser.parse_args()

    # Chemins
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    registry_path = project_root / "registry"
    definitions_path = script_dir / "subprograms_definitions.json"

    # Vérification existence du fichier de définitions
    if not definitions_path.exists():
        print(f"❌ Fichier de définitions introuvable : {definitions_path}")
        sys.exit(1)

    # Création du générateur
    generator = SubprogramGenerator(registry_path, definitions_path)

    # Mode stats uniquement
    if args.stats:
        definitions = generator.load_definitions()
        total = 0
        for category_name, category_data in definitions.get("categories", {}).items():
            for module_name, module_data in category_data.get("modules", {}).items():
                for submodule_name, subprograms in module_data.items():
                    total += len(subprograms) if subprograms else 0

        print(f"\n📊 STATISTIQUES DES DÉFINITIONS")
        print(f"Total de sous-programmes définis : {total}")
        print(f"Catégories : {len(definitions.get('categories', {}))}")
        sys.exit(0)

    # Génération
    generator.generate_all(
        dry_run=args.dry_run,
        force=args.force,
        category_filter=args.category
    )

    # Affichage des stats
    generator.print_stats()

    # Code retour
    if generator.stats["errors"] > 0:
        sys.exit(1)
    else:
        print("✅ Génération terminée avec succès !")
        sys.exit(0)


if __name__ == "__main__":
    main()
