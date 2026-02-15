#!/usr/bin/env python3
"""
AZALS - Script de mise à jour des hashes impl.py

Ce script calcule et ajoute le hash SHA256 de chaque fichier impl.py
dans le manifest.json correspondant.

Usage:
    python scripts/update-impl-hashes.py [--dry-run]

Options:
    --dry-run    Affiche les modifications sans les appliquer
"""

import json
import hashlib
import sys
from pathlib import Path


def compute_file_hash(file_path: Path) -> str:
    """Calcule le hash SHA256 d'un fichier."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def update_manifest_hashes(registry_path: Path, dry_run: bool = False) -> int:
    """
    Met à jour tous les manifests avec les hashes des impl.py.

    Returns:
        Nombre de manifests mis à jour
    """
    updated_count = 0

    # Recherche de tous les manifest.json
    for manifest_path in registry_path.rglob("manifest.json"):
        # Ignorer les versions archivées
        if "versions" in str(manifest_path):
            continue

        program_dir = manifest_path.parent
        impl_path = program_dir / "impl.py"

        if not impl_path.exists():
            print(f"[SKIP] {manifest_path}: pas de impl.py")
            continue

        # Calculer le hash
        impl_hash = compute_file_hash(impl_path)

        # Lire le manifest
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        # Vérifier si mise à jour nécessaire
        current_hash = manifest.get("impl_sha256")
        if current_hash == impl_hash:
            print(f"[OK] {manifest.get('id', 'unknown')}: hash déjà à jour")
            continue

        # Mettre à jour le hash
        manifest["impl_sha256"] = impl_hash

        if dry_run:
            print(f"[DRY-RUN] {manifest.get('id', 'unknown')}: ajouterait hash {impl_hash[:16]}...")
        else:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            print(f"[UPDATED] {manifest.get('id', 'unknown')}: hash mis à jour ({impl_hash[:16]}...)")

        updated_count += 1

    return updated_count


def main():
    dry_run = "--dry-run" in sys.argv

    # Chemin du registry
    script_dir = Path(__file__).parent
    registry_path = script_dir.parent / "registry"

    if not registry_path.exists():
        print(f"Erreur: Registry non trouvé à {registry_path}")
        sys.exit(1)

    print(f"=== AZALS - Mise à jour des hashes impl.py ===")
    print(f"Registry: {registry_path}")
    print(f"Mode: {'DRY-RUN (simulation)' if dry_run else 'MISE À JOUR RÉELLE'}")
    print()

    updated = update_manifest_hashes(registry_path, dry_run)

    print()
    print(f"=== Résumé ===")
    print(f"Manifests {'à mettre à jour' if dry_run else 'mis à jour'}: {updated}")

    if dry_run and updated > 0:
        print()
        print("Pour appliquer les modifications, relancez sans --dry-run")


if __name__ == "__main__":
    main()
