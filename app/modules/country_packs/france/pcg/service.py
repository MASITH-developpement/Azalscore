"""
AZALS MODULE - PCG 2025: Service
==================================

Service de gestion du Plan Comptable Général 2025.

Fonctionnalités:
- Initialisation du PCG standard
- Création de comptes personnalisés
- Validation de conformité
- Migration PCG 2024 -> 2025
"""
from __future__ import annotations


import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from ..models import PCGAccount, PCGClass
from .pcg2025_accounts import (
    PCG2025_ALL_ACCOUNTS,
    PCG2025Account as PCG2025AccountDef,
    get_pcg2025_account,
    get_pcg2025_class,
    validate_pcg_account_number,
    get_parent_account_number,
)
from .schemas import (
    PCGAccountCreate,
    PCGAccountResponse,
    PCGInitResult,
    PCGValidationResult,
    PCGValidationIssue,
    PCGMigrationResult,
)

logger = logging.getLogger(__name__)


class PCG2025Service:
    """Service de gestion du PCG 2025."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # INITIALISATION
    # ========================================================================

    def initialize_pcg2025(self, force: bool = False) -> PCGInitResult:
        """
        Initialiser le PCG 2025 pour le tenant.

        Args:
            force: Si True, supprime les comptes existants avant init

        Returns:
            PCGInitResult avec statistiques d'initialisation
        """
        # Vérifier si déjà initialisé
        existing_count = self.db.query(func.count(PCGAccount.id)).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.is_custom == False  # noqa: E712
        ).scalar()

        if existing_count > 0 and not force:
            logger.info(f"[PCG2025] Tenant {self.tenant_id} déjà initialisé ({existing_count} comptes)")
            return PCGInitResult(
                success=False,
                message="PCG déjà initialisé. Utilisez force=True pour réinitialiser.",
                accounts_created=0,
                accounts_existing=existing_count,
            )

        # Si force, supprimer les comptes standard existants
        if force and existing_count > 0:
            self.db.query(PCGAccount).filter(
                PCGAccount.tenant_id == self.tenant_id,
                PCGAccount.is_custom == False  # noqa: E712
            ).delete()
            logger.info(f"[PCG2025] Suppression de {existing_count} comptes existants")

        # Créer les comptes PCG 2025
        created_count = 0
        for account_def in PCG2025_ALL_ACCOUNTS:
            account = PCGAccount(
                tenant_id=self.tenant_id,
                account_number=account_def.number,
                account_label=account_def.label,
                pcg_class=PCGClass(f"CLASSE_{account_def.pcg_class}"),
                parent_account=get_parent_account_number(account_def.number),
                is_summary=account_def.is_summary,
                normal_balance=account_def.normal_balance,
                is_active=True,
                is_custom=False,
                description=account_def.notes,
            )
            self.db.add(account)
            created_count += 1

        self.db.commit()

        logger.info(f"[PCG2025] Tenant {self.tenant_id}: {created_count} comptes créés")

        return PCGInitResult(
            success=True,
            message=f"PCG 2025 initialisé avec {created_count} comptes",
            accounts_created=created_count,
            accounts_existing=0,
            version="2025",
        )

    def get_initialization_status(self) -> dict:
        """Vérifier l'état d'initialisation du PCG."""
        total_standard = self.db.query(func.count(PCGAccount.id)).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.is_custom == False  # noqa: E712
        ).scalar()

        total_custom = self.db.query(func.count(PCGAccount.id)).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.is_custom == True  # noqa: E712
        ).scalar()

        expected_count = len(PCG2025_ALL_ACCOUNTS)

        return {
            "is_initialized": total_standard > 0,
            "standard_accounts": total_standard,
            "custom_accounts": total_custom,
            "total_accounts": total_standard + total_custom,
            "expected_standard": expected_count,
            "is_complete": total_standard >= expected_count,
            "completion_percentage": round((total_standard / expected_count) * 100, 1) if expected_count > 0 else 0,
        }

    # ========================================================================
    # GESTION DES COMPTES
    # ========================================================================

    def get_account(self, account_number: str) -> Optional[PCGAccount]:
        """Récupérer un compte par son numéro."""
        return self.db.query(PCGAccount).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.account_number == account_number
        ).first()

    def get_account_by_id(self, account_id: UUID) -> Optional[PCGAccount]:
        """Récupérer un compte par son ID."""
        return self.db.query(PCGAccount).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.id == account_id
        ).first()

    def list_accounts(
        self,
        pcg_class: Optional[str] = None,
        active_only: bool = True,
        custom_only: bool = False,
        summary_only: bool = False,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[PCGAccount], int]:
        """
        Lister les comptes PCG avec filtres.

        Returns:
            Tuple (liste des comptes, total)
        """
        query = self.db.query(PCGAccount).filter(
            PCGAccount.tenant_id == self.tenant_id
        )

        if pcg_class:
            query = query.filter(PCGAccount.pcg_class == PCGClass(f"CLASSE_{pcg_class}"))

        if active_only:
            query = query.filter(PCGAccount.is_active == True)  # noqa: E712

        if custom_only:
            query = query.filter(PCGAccount.is_custom == True)  # noqa: E712

        if summary_only:
            query = query.filter(PCGAccount.is_summary == True)  # noqa: E712

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (PCGAccount.account_number.ilike(search_pattern)) |
                (PCGAccount.account_label.ilike(search_pattern))
            )

        total = query.count()
        accounts = query.order_by(PCGAccount.account_number).offset(skip).limit(limit).all()

        return accounts, total

    def create_custom_account(self, data: PCGAccountCreate) -> PCGAccount:
        """
        Créer un compte personnalisé.

        Le compte doit respecter la hiérarchie PCG:
        - Le numéro doit commencer par un chiffre de classe valide (1-8)
        - Le compte parent doit exister si spécifié
        """
        # Validation du numéro
        if not validate_pcg_account_number(data.account_number):
            raise ValueError(f"Numéro de compte invalide: {data.account_number}")

        # Vérifier si le compte existe déjà
        existing = self.get_account(data.account_number)
        if existing:
            raise ValueError(f"Le compte {data.account_number} existe déjà")

        # Valider le compte parent
        parent_number = data.parent_account or get_parent_account_number(data.account_number)
        if parent_number:
            parent = self.get_account(parent_number)
            if not parent:
                raise ValueError(f"Compte parent {parent_number} introuvable")

        # Déterminer la classe PCG
        pcg_class = PCGClass(f"CLASSE_{data.account_number[0]}")

        account = PCGAccount(
            tenant_id=self.tenant_id,
            account_number=data.account_number,
            account_label=data.account_label,
            pcg_class=pcg_class,
            parent_account=parent_number,
            is_summary=data.is_summary or False,
            normal_balance=data.normal_balance or "D",
            is_active=True,
            is_custom=True,
            description=data.description,
            default_vat_code=data.default_vat_code,
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        logger.info(f"[PCG2025] Compte personnalisé créé: {data.account_number}")

        return account

    def update_account(self, account_id: UUID, **kwargs) -> PCGAccount:
        """Mettre à jour un compte (uniquement les comptes personnalisés)."""
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Compte {account_id} introuvable")

        if not account.is_custom:
            raise ValueError("Impossible de modifier un compte PCG standard")

        allowed_fields = {"account_label", "description", "is_active", "default_vat_code", "notes"}
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(account, key, value)

        account.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(account)

        return account

    def deactivate_account(self, account_number: str) -> PCGAccount:
        """Désactiver un compte (ne peut pas être supprimé s'il a des écritures)."""
        account = self.get_account(account_number)
        if not account:
            raise ValueError(f"Compte {account_number} introuvable")

        account.is_active = False
        account.updated_at = datetime.utcnow()
        self.db.commit()

        return account

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def validate_account_number(self, account_number: str) -> PCGValidationResult:
        """
        Valider un numéro de compte selon les règles PCG 2025.

        Returns:
            PCGValidationResult avec détails de validation
        """
        issues: list[PCGValidationIssue] = []

        # Format de base
        if not account_number:
            issues.append(PCGValidationIssue(
                code="PCG_EMPTY",
                message="Le numéro de compte est vide",
                severity="error",
            ))
            return PCGValidationResult(
                is_valid=False,
                account_number=account_number,
                issues=issues,
            )

        if not account_number.isdigit():
            issues.append(PCGValidationIssue(
                code="PCG_NOT_NUMERIC",
                message="Le numéro de compte doit être numérique",
                severity="error",
            ))

        if len(account_number) < 2:
            issues.append(PCGValidationIssue(
                code="PCG_TOO_SHORT",
                message="Le numéro de compte doit avoir au moins 2 chiffres",
                severity="error",
            ))

        if account_number and account_number[0] not in "12345678":
            issues.append(PCGValidationIssue(
                code="PCG_INVALID_CLASS",
                message=f"Classe {account_number[0]} invalide (1-8 attendu)",
                severity="error",
            ))

        # Vérifier si c'est un compte standard PCG
        standard_account = get_pcg2025_account(account_number)
        if standard_account:
            return PCGValidationResult(
                is_valid=len(issues) == 0,
                account_number=account_number,
                is_standard=True,
                standard_label=standard_account.label,
                pcg_class=standard_account.pcg_class,
                normal_balance=standard_account.normal_balance,
                issues=issues,
            )

        # Vérifier la hiérarchie
        parent_number = get_parent_account_number(account_number)
        if parent_number:
            parent_account = get_pcg2025_account(parent_number)
            existing_parent = self.get_account(parent_number)

            if not parent_account and not existing_parent:
                issues.append(PCGValidationIssue(
                    code="PCG_NO_PARENT",
                    message=f"Compte parent {parent_number} introuvable",
                    severity="warning",
                ))

        return PCGValidationResult(
            is_valid=len([i for i in issues if i.severity == "error"]) == 0,
            account_number=account_number,
            is_standard=False,
            pcg_class=account_number[0] if account_number else None,
            issues=issues,
        )

    def validate_chart_of_accounts(self) -> dict:
        """
        Valider le plan comptable complet du tenant.

        Vérifie:
        - Présence des comptes obligatoires
        - Cohérence de la hiérarchie
        - Soldes normaux corrects
        """
        issues: list[dict] = []
        warnings: list[dict] = []

        # Récupérer tous les comptes du tenant
        accounts, total = self.list_accounts(active_only=False, limit=10000)
        account_numbers = {a.account_number for a in accounts}

        # Vérifier les comptes obligatoires (comptes de base de chaque classe)
        required_base = ["10", "20", "30", "40", "50", "60", "70"]
        for base in required_base:
            has_class = any(a.startswith(base) for a in account_numbers)
            if not has_class:
                issues.append({
                    "code": "PCG_MISSING_CLASS",
                    "message": f"Aucun compte de classe {base[0]} trouvé",
                })

        # Vérifier la hiérarchie
        for account in accounts:
            parent_number = account.parent_account or get_parent_account_number(account.account_number)
            if parent_number and parent_number not in account_numbers:
                # Vérifier si le parent est un compte standard PCG
                if not get_pcg2025_account(parent_number):
                    warnings.append({
                        "code": "PCG_ORPHAN_ACCOUNT",
                        "message": f"Compte {account.account_number} sans parent {parent_number}",
                    })

        return {
            "is_valid": len(issues) == 0,
            "total_accounts": total,
            "issues": issues,
            "warnings": warnings,
            "summary": {
                "classes": {
                    str(i): len([a for a in accounts if a.account_number.startswith(str(i))])
                    for i in range(1, 9)
                }
            }
        }

    # ========================================================================
    # MIGRATION
    # ========================================================================

    def migrate_from_2024(self) -> PCGMigrationResult:
        """
        Migrer le plan comptable de PCG 2024 vers PCG 2025.

        Cette migration:
        - Conserve les comptes personnalisés
        - Met à jour les libellés des comptes standard si modifiés
        - Ajoute les nouveaux comptes PCG 2025
        """
        accounts_updated = 0
        accounts_added = 0
        accounts_unchanged = 0
        details: list[str] = []

        existing_accounts = {
            a.account_number: a
            for a in self.db.query(PCGAccount).filter(
                PCGAccount.tenant_id == self.tenant_id
            ).all()
        }

        for account_def in PCG2025_ALL_ACCOUNTS:
            existing = existing_accounts.get(account_def.number)

            if existing:
                # Compte existe - vérifier si mise à jour nécessaire
                if existing.is_custom:
                    accounts_unchanged += 1
                    continue

                # Mettre à jour le libellé si différent
                if existing.account_label != account_def.label:
                    old_label = existing.account_label
                    existing.account_label = account_def.label
                    accounts_updated += 1
                    details.append(f"{account_def.number}: '{old_label}' -> '{account_def.label}'")
                else:
                    accounts_unchanged += 1
            else:
                # Nouveau compte - créer
                account = PCGAccount(
                    tenant_id=self.tenant_id,
                    account_number=account_def.number,
                    account_label=account_def.label,
                    pcg_class=PCGClass(f"CLASSE_{account_def.pcg_class}"),
                    parent_account=get_parent_account_number(account_def.number),
                    is_summary=account_def.is_summary,
                    normal_balance=account_def.normal_balance,
                    is_active=True,
                    is_custom=False,
                    description=account_def.notes,
                )
                self.db.add(account)
                accounts_added += 1
                details.append(f"{account_def.number}: Nouveau compte ajouté")

        self.db.commit()

        logger.info(
            f"[PCG2025] Migration terminée: "
            f"{accounts_added} ajoutés, {accounts_updated} mis à jour, {accounts_unchanged} inchangés"
        )

        return PCGMigrationResult(
            success=True,
            source_version="2024",
            target_version="2025",
            accounts_updated=accounts_updated,
            accounts_added=accounts_added,
            accounts_unchanged=accounts_unchanged,
            details=details if len(details) <= 20 else details[:20] + ["..."],
        )

    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    def get_account_hierarchy(self, account_number: str) -> list[PCGAccount]:
        """Récupérer la hiérarchie d'un compte (du plus général au plus détaillé)."""
        hierarchy = []
        current = account_number

        while current:
            account = self.get_account(current)
            if account:
                hierarchy.insert(0, account)
            current = get_parent_account_number(current)

        return hierarchy

    def get_child_accounts(self, parent_number: str) -> list[PCGAccount]:
        """Récupérer les comptes enfants directs."""
        return self.db.query(PCGAccount).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.parent_account == parent_number,
            PCGAccount.is_active == True  # noqa: E712
        ).order_by(PCGAccount.account_number).all()

    def search_accounts(self, query: str, limit: int = 20) -> list[PCGAccount]:
        """Rechercher des comptes par numéro ou libellé."""
        search_pattern = f"%{query}%"
        return self.db.query(PCGAccount).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.is_active == True,  # noqa: E712
            (PCGAccount.account_number.ilike(search_pattern)) |
            (PCGAccount.account_label.ilike(search_pattern))
        ).order_by(PCGAccount.account_number).limit(limit).all()

    def get_statistics(self) -> dict:
        """Statistiques du plan comptable."""
        total = self.db.query(func.count(PCGAccount.id)).filter(
            PCGAccount.tenant_id == self.tenant_id
        ).scalar()

        active = self.db.query(func.count(PCGAccount.id)).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.is_active == True  # noqa: E712
        ).scalar()

        custom = self.db.query(func.count(PCGAccount.id)).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.is_custom == True  # noqa: E712
        ).scalar()

        # Comptes par classe
        by_class = {}
        for i in range(1, 9):
            count = self.db.query(func.count(PCGAccount.id)).filter(
                PCGAccount.tenant_id == self.tenant_id,
                PCGAccount.pcg_class == PCGClass(f"CLASSE_{i}")
            ).scalar()
            by_class[f"classe_{i}"] = count

        return {
            "total_accounts": total,
            "active_accounts": active,
            "inactive_accounts": total - active,
            "custom_accounts": custom,
            "standard_accounts": total - custom,
            "by_class": by_class,
            "pcg_version": "2025",
        }
