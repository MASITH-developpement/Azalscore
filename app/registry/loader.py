"""
Registry Loader AZALSCORE

Charge les sous-programmes depuis le registry, valide les manifests,
résout les versions (SemVer), refuse les sous-programmes non certifiés.

Conformité : AZA-NF-003, Charte Développeur
Règle : "Le manifest est la vérité, pas le code"

SÉCURITÉ P1:
- Validation JSON Schema formelle des manifests
- Reject manifests non conformes
- Validation cryptographique (SHA256) des fichiers impl.py
- Protection contre path traversal
"""
from __future__ import annotations


import json
import importlib.util
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# JSON Schema validation (optional but recommended)
_JSON_SCHEMA_AVAILABLE = False
_MANIFEST_SCHEMA = None

try:
    import jsonschema
    _JSON_SCHEMA_AVAILABLE = True

    # Charger le schema au démarrage
    _SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "manifest.schema.json"
    if _SCHEMA_PATH.exists():
        with open(_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            _MANIFEST_SCHEMA = json.load(f)
        logger.info("[REGISTRY] JSON Schema loaded from %s", _SCHEMA_PATH)
    else:
        logger.warning("[REGISTRY] JSON Schema not found at %s, using basic validation", _SCHEMA_PATH)
except ImportError:
    logger.warning("[REGISTRY] jsonschema package not installed, using basic validation only")


class RegistryError(Exception):
    """Erreur du registry"""
    pass


class ManifestValidationError(RegistryError):
    """Erreur de validation de manifest"""
    pass


class ProgramNotFoundError(RegistryError):
    """Sous-programme non trouvé"""
    pass


class VersionError(RegistryError):
    """Erreur de résolution de version"""
    pass


class SecurityError(RegistryError):
    """Erreur de sécurité lors du chargement d'un module"""
    pass


class Program:
    """
    Représentation d'un sous-programme AZALSCORE

    Un sous-programme est défini par son manifest (source de vérité)
    et son implémentation (interchangeable).
    """

    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self.program_dir = manifest_path.parent
        self.manifest = self._load_manifest()
        self.impl_module = None

        # Validation obligatoire
        self._validate_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        """Charge le manifest JSON"""
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _validate_manifest(self):
        """
        Valide le manifest selon les règles AZALSCORE

        SÉCURITÉ P1: Utilise JSON Schema si disponible, sinon validation basique.

        RÈGLES BLOQUANTES :
        - Champs obligatoires présents
        - Types corrects
        - Version SemVer valide
        - side_effects et idempotent déclarés
        - no_code_compatible déclaré
        """
        # P1: Validation JSON Schema si disponible
        if _JSON_SCHEMA_AVAILABLE and _MANIFEST_SCHEMA:
            self._validate_with_json_schema()
        else:
            self._validate_basic()

    def _validate_with_json_schema(self):
        """Validation formelle avec JSON Schema (P1)."""
        try:
            jsonschema.validate(instance=self.manifest, schema=_MANIFEST_SCHEMA)
            logger.debug("[REGISTRY] Manifest validated with JSON Schema: %s", self.manifest.get('id'))
        except jsonschema.ValidationError as e:
            raise ManifestValidationError(
                f"Manifest invalide (JSON Schema): {e.message} "
                f"at path '{'/'.join(str(p) for p in e.absolute_path)}' "
                f"in {self.manifest_path}"
            )
        except jsonschema.SchemaError as e:
            logger.error("[REGISTRY] Invalid JSON Schema: %s", e)
            # Fallback to basic validation if schema is broken
            self._validate_basic()

    def _validate_basic(self):
        """Validation basique sans JSON Schema (fallback)."""
        required_fields = [
            "id", "name", "category", "version", "description",
            "inputs", "outputs", "side_effects", "idempotent",
            "no_code_compatible"
        ]

        for field in required_fields:
            if field not in self.manifest:
                raise ManifestValidationError(
                    f"Manifest invalide : champ '{field}' manquant dans {self.manifest_path}"
                )

        # Validation version SemVer
        version = self.manifest["version"]
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            raise ManifestValidationError(
                f"Version invalide '{version}' (doit être SemVer: X.Y.Z)"
            )

        # Validation types
        if not isinstance(self.manifest["side_effects"], bool):
            raise ManifestValidationError("side_effects doit être un boolean")

        if not isinstance(self.manifest["idempotent"], bool):
            raise ManifestValidationError("idempotent doit être un boolean")

        if not isinstance(self.manifest["no_code_compatible"], bool):
            raise ManifestValidationError("no_code_compatible doit être un boolean")

        # Validation inputs/outputs
        if not isinstance(self.manifest["inputs"], dict):
            raise ManifestValidationError("inputs doit être un objet")

        if not isinstance(self.manifest["outputs"], dict):
            raise ManifestValidationError("outputs doit être un objet")

    def _compute_file_hash(self, file_path: Path) -> str:
        """Calcule le hash SHA256 d'un fichier."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _validate_path_security(self, impl_path: Path) -> None:
        """
        Valide que le chemin est sécurisé (pas de path traversal).

        SÉCURITÉ: Empêche le chargement de fichiers en dehors du répertoire du programme.
        """
        # Résoudre les chemins absolus pour détecter le path traversal
        resolved_impl = impl_path.resolve()
        resolved_program_dir = self.program_dir.resolve()

        # Vérifier que impl_path est bien un enfant de program_dir
        try:
            resolved_impl.relative_to(resolved_program_dir)
        except ValueError:
            raise SecurityError(
                f"SÉCURITÉ: Path traversal détecté! "
                f"Le fichier {impl_path} est en dehors du répertoire autorisé {self.program_dir}"
            )

        # Vérifier qu'il n'y a pas de liens symboliques malveillants
        if impl_path.is_symlink():
            symlink_target = impl_path.resolve()
            try:
                symlink_target.relative_to(resolved_program_dir)
            except ValueError:
                raise SecurityError(
                    f"SÉCURITÉ: Lien symbolique malveillant détecté! "
                    f"Le lien {impl_path} pointe vers {symlink_target} en dehors du répertoire autorisé"
                )

    def _validate_impl_hash(self, impl_path: Path) -> None:
        """
        Valide le hash SHA256 du fichier impl.py si spécifié dans le manifest.

        SÉCURITÉ: Assure l'intégrité du code avant exécution.
        """
        expected_hash = self.manifest.get("impl_sha256")

        if expected_hash:
            actual_hash = self._compute_file_hash(impl_path)
            if actual_hash != expected_hash:
                raise SecurityError(
                    f"SÉCURITÉ: Hash invalide pour {impl_path}! "
                    f"Attendu: {expected_hash}, Obtenu: {actual_hash}. "
                    f"Le fichier a peut-être été modifié de manière non autorisée."
                )
            logger.debug("[REGISTRY] Hash validé pour %s", impl_path)
        else:
            # Avertissement si pas de hash défini (recommandé mais pas obligatoire)
            logger.warning(
                "[REGISTRY] Pas de impl_sha256 dans le manifest pour %s. "
                "Recommandé: ajouter le hash pour valider l'intégrité.",
                self.manifest.get('id')
            )

    def _load_implementation(self):
        """
        Charge l'implémentation Python du sous-programme

        L'implémentation doit exposer une fonction execute(inputs) -> outputs

        SÉCURITÉ P1:
        - Validation du chemin (anti path traversal)
        - Validation du hash SHA256 (intégrité)
        """
        impl_path = self.program_dir / "impl.py"

        if not impl_path.exists():
            raise RegistryError(
                f"Implémentation manquante : {impl_path}"
            )

        # SÉCURITÉ: Valider le chemin avant toute opération
        self._validate_path_security(impl_path)

        # SÉCURITÉ: Valider le hash si présent
        self._validate_impl_hash(impl_path)

        # Chargement dynamique du module (après validation)
        spec = importlib.util.spec_from_file_location(
            f"registry.{self.manifest['id']}", impl_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, 'execute'):
            raise RegistryError(
                f"Implémentation invalide : function execute() manquante dans {impl_path}"
            )

        self.impl_module = module

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute le sous-programme avec les inputs fournis

        Args:
            inputs: Dictionnaire des paramètres d'entrée

        Returns:
            Dictionnaire des résultats

        Raises:
            RegistryError: Si l'exécution échoue

        Note:
            La gestion d'erreur est minimale ici.
            Le moteur d'orchestration gère retry/timeout/fallback.
        """
        if self.impl_module is None:
            self._load_implementation()

        # Validation des inputs requis
        for input_name, input_spec in self.manifest["inputs"].items():
            if input_spec.get("required", False) and input_name not in inputs:
                raise RegistryError(
                    f"Input requis manquant : '{input_name}' pour {self.manifest['id']}"
                )

        # Exécution du sous-programme
        # Note: Pas de try/catch ici, délégué au moteur d'orchestration
        result = self.impl_module.execute(inputs)

        return result

    @property
    def program_id(self) -> str:
        return self.manifest["id"]

    @property
    def version(self) -> str:
        return self.manifest["version"]

    @property
    def category(self) -> str:
        return self.manifest["category"]

    @property
    def has_side_effects(self) -> bool:
        return self.manifest["side_effects"]

    @property
    def is_idempotent(self) -> bool:
        return self.manifest["idempotent"]

    @property
    def is_no_code_compatible(self) -> bool:
        return self.manifest["no_code_compatible"]


class RegistryLoader:
    """
    Chargeur du registry AZALSCORE

    Responsabilités :
    - Scanner le registry et charger les manifests
    - Valider les sous-programmes
    - Résoudre les versions (SemVer)
    - Cacher les sous-programmes chargés
    - Refuser les sous-programmes non conformes
    """

    def __init__(self, registry_path: Optional[Path] = None):
        if registry_path is None:
            # Par défaut : /home/ubuntu/azalscore/registry/
            registry_path = Path(__file__).parent.parent.parent / "registry"

        self.registry_path = Path(registry_path)
        self._programs: Dict[str, Program] = {}
        self._scan_registry()

    def _scan_registry(self):
        """
        Scanne le registry et charge tous les manifests

        Structure attendue :
        registry/
          category/
            program_name/
              manifest.json
              impl.py
              tests/
        """
        if not self.registry_path.exists():
            logger.warning("Registry path does not exist: %s", self.registry_path)
            return

        # Recherche récursive de tous les manifest.json
        manifest_files = self.registry_path.rglob("manifest.json")

        for manifest_path in manifest_files:
            # Ignorer les manifests dans versions/
            if "versions" in str(manifest_path):
                continue

            try:
                program = Program(manifest_path)
                program_id = program.program_id

                # Stocker le sous-programme
                # Format: "azalscore.category.name@version"
                full_id = f"{program_id}@{program.version}"
                self._programs[full_id] = program

                # Stocker aussi sans version pour résolution "latest"
                self._programs[program_id] = program

                logger.info("Registry: Loaded %s", full_id)

            except Exception as e:
                logger.error("Failed to load program from %s: %s", manifest_path, e)
                # RÈGLE AZALSCORE : En cas de doute, non-conformité retenue
                # On refuse le sous-programme au lieu de le charger partiellement

    def get_program(self, program_ref: str) -> Program:
        """
        Récupère un sous-programme du registry

        Args:
            program_ref: Référence du sous-programme
                - "azalscore.finance.calculate_margin" (latest version)
                - "azalscore.finance.calculate_margin@1.0.0" (version exacte)
                - "azalscore.finance.calculate_margin@^1.0" (version compatible)

        Returns:
            Program instance

        Raises:
            ProgramNotFoundError: Si le sous-programme n'existe pas
            VersionError: Si la version demandée n'existe pas
        """
        # Parsing de la référence
        if "@" in program_ref:
            program_id, version_spec = program_ref.split("@", 1)
        else:
            program_id = program_ref
            version_spec = None  # Latest

        # Récupération du sous-programme
        if version_spec:
            # Version spécifique
            full_id = f"{program_id}@{version_spec}"
            if full_id in self._programs:
                return self._programs[full_id]

            # NOTE: Phase 2 - Résolution SemVer avancée (^, ~, >=)
            raise VersionError(
                f"Version '{version_spec}' non trouvée pour {program_id}"
            )
        else:
            # Latest version
            if program_id in self._programs:
                return self._programs[program_id]

            raise ProgramNotFoundError(
                f"Sous-programme '{program_id}' non trouvé dans le registry"
            )

    def list_programs(
        self,
        category: Optional[str] = None,
        no_code_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Liste les sous-programmes du registry

        Args:
            category: Filtrer par catégorie (optionnel)
            no_code_only: Filtrer uniquement les sous-programmes No-Code compatibles

        Returns:
            Liste de manifests résumés
        """
        programs = []

        for program_id, program in self._programs.items():
            # Ignorer les versions avec @ (garder uniquement les "latest")
            if "@" in program_id:
                continue

            # Filtrage par catégorie
            if category and program.category != category:
                continue

            # Filtrage No-Code
            if no_code_only and not program.is_no_code_compatible:
                continue

            programs.append({
                "id": program.program_id,
                "name": program.manifest["name"],
                "category": program.category,
                "version": program.version,
                "description": program.manifest["description"],
                "side_effects": program.has_side_effects,
                "idempotent": program.is_idempotent,
                "no_code_compatible": program.is_no_code_compatible,
                "tags": program.manifest.get("tags", [])
            })

        return sorted(programs, key=lambda p: p["id"])


# Instance globale du loader (singleton pattern)
_loader_instance: Optional[RegistryLoader] = None


def get_loader() -> RegistryLoader:
    """Récupère l'instance singleton du loader"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = RegistryLoader()
    return _loader_instance


def load_program(program_ref: str) -> Program:
    """
    Fonction helper pour charger un sous-programme

    Usage:
        program = load_program("azalscore.finance.calculate_margin@^1.0")
        result = program.execute({"price": 1000, "cost": 800})
    """
    loader = get_loader()
    return loader.get_program(program_ref)


def list_programs(category: Optional[str] = None, no_code_only: bool = False) -> List[Dict[str, Any]]:
    """
    Fonction helper pour lister les sous-programmes

    Usage:
        programs = list_programs(category="finance")
    """
    loader = get_loader()
    return loader.list_programs(category=category, no_code_only=no_code_only)
