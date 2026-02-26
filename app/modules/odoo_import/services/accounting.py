"""
AZALS MODULE - Odoo Import Accounting Service
===============================================

Service d'import des données comptables depuis Odoo.
Gère le plan comptable, les journaux et les écritures.
"""
from __future__ import annotations


import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple
from uuid import UUID

from app.modules.odoo_import.models import OdooImportHistory, OdooSyncType

from .base import BaseOdooService

logger = logging.getLogger(__name__)


class AccountingImportService(BaseOdooService[OdooImportHistory]):
    """Service d'import comptable Odoo."""

    model = OdooImportHistory

    # Mapping des types de compte Odoo vers AZALS
    ACCOUNT_TYPE_MAPPING = {
        "asset_receivable": "ASSET",
        "asset_cash": "ASSET",
        "asset_current": "ASSET",
        "asset_non_current": "ASSET",
        "asset_prepayments": "ASSET",
        "asset_fixed": "ASSET",
        "liability_payable": "LIABILITY",
        "liability_credit_card": "LIABILITY",
        "liability_current": "LIABILITY",
        "liability_non_current": "LIABILITY",
        "equity": "EQUITY",
        "equity_unaffected": "EQUITY",
        "income": "REVENUE",
        "income_other": "REVENUE",
        "expense": "EXPENSE",
        "expense_depreciation": "EXPENSE",
        "expense_direct_cost": "EXPENSE",
        "off_balance": "SPECIAL",
    }

    def import_accounting(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les écritures comptables depuis Odoo.

        Processus en 3 étapes:
        1. Import du plan comptable (account.account)
        2. Chargement des journaux (account.journal)
        3. Import des écritures (account.move + account.move.line)

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore le delta

        Returns:
            Historique de l'import
        """
        config = self._require_config(config_id)

        history = self._create_history(
            config_id=config_id,
            sync_type=OdooSyncType.ACCOUNTING,
            is_delta=not full_sync,
        )

        total_created = 0
        total_updated = 0
        all_errors = []

        try:
            connector = self._get_connector(config)
            mapper = self._get_mapper(config_id)

            # ================================================================
            # ÉTAPE 1: Import du plan comptable
            # ================================================================
            logger.info("Import du plan comptable...")

            account_fields = [
                "id",
                "code",
                "name",
                "account_type",
                "reconcile",
                "deprecated",
            ]
            accounts = connector.search_read(
                "account.account",
                [("deprecated", "=", False)],
                account_fields,
            )

            accounts_created, accounts_errors, accounts_map = (
                self._import_chart_of_accounts(accounts)
            )
            total_created += accounts_created
            all_errors.extend(accounts_errors)

            logger.info(
                "Plan comptable: %d comptes importés, %d erreurs",
                accounts_created,
                len(accounts_errors),
            )

            # ================================================================
            # ÉTAPE 2: Chargement des journaux
            # ================================================================
            logger.info("Chargement des journaux comptables...")

            journal_fields = ["id", "code", "name", "type"]
            journals = connector.search_read("account.journal", [], journal_fields)

            journals_map = {}
            for journal in journals:
                journals_map[journal["id"]] = {
                    "code": journal.get("code", f"J{journal['id']}"),
                    "label": journal.get("name", "Journal"),
                    "type": journal.get("type", "general"),
                }

            logger.info("%d journaux chargés", len(journals_map))

            # ================================================================
            # ÉTAPE 3: Import des écritures
            # ================================================================
            logger.info("Import des écritures comptables...")

            delta_date = None
            if not full_sync and config.accounting_last_sync_at:
                delta_date = config.accounting_last_sync_at
                history.delta_from_date = delta_date

            move_domain = [("state", "=", "posted")]  # Écritures validées
            if delta_date:
                move_domain.extend([
                    "|",
                    (
                        "write_date",
                        ">=",
                        delta_date.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                    (
                        "create_date",
                        ">=",
                        delta_date.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                ])

            move_fields = [
                "id",
                "name",
                "ref",
                "date",
                "journal_id",
                "state",
                "move_type",
                "currency_id",
                "partner_id",
                "line_ids",
            ]

            moves = connector.search_read(
                "account.move",
                move_domain,
                move_fields,
                limit=5000,
            )
            history.total_records = len(moves)

            logger.info("Récupéré %d écritures comptables", len(moves))

            # Récupérer toutes les lignes en une seule requête
            if moves:
                lines = self._fetch_move_lines(connector, moves)
                lines_by_move = self._group_lines_by_move(lines)

                entries_created, entries_updated, entries_errors = (
                    self._import_journal_entries(
                        moves,
                        lines_by_move,
                        accounts_map,
                        journals_map,
                    )
                )
                total_created += entries_created
                total_updated += entries_updated
                all_errors.extend(entries_errors)

            # Mettre à jour la configuration
            config.accounting_last_sync_at = datetime.utcnow()
            config.total_imports += 1

            history = self._finalize_history(
                history,
                total_created,
                total_updated,
                all_errors,
            )

            logger.info(
                "Import comptable terminé | created=%d updated=%d errors=%d",
                total_created,
                total_updated,
                len(all_errors),
            )
            return history

        except Exception as e:
            self._fail_history(history, e)
            config.last_error_message = str(e)
            self.db.commit()
            raise

    def import_bank_statements(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les relevés bancaires depuis Odoo (account.bank.statement).

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore le delta

        Returns:
            Historique de l'import
        """
        config = self._require_config(config_id)

        history = self._create_history(
            config_id=config_id,
            sync_type=OdooSyncType.BANK,
            is_delta=not full_sync,
        )

        try:
            connector = self._get_connector(config)

            # Relevés bancaires (Odoo 17+ n'a plus le champ 'state')
            domain = []
            fields = [
                "name",
                "date",
                "journal_id",
                "balance_start",
                "balance_end_real",
                "line_ids",
            ]

            statements = connector.search_read(
                "account.bank.statement",
                domain,
                fields,
            )
            history.total_records = len(statements)

            logger.info("Récupéré %d relevés bancaires", len(statements))

            # Import simplifié pour l'instant
            history = self._finalize_history(history, len(statements), 0, [])
            return history

        except Exception as e:
            self._fail_history(history, e)
            self.db.commit()
            raise

    def _import_chart_of_accounts(
        self,
        odoo_accounts: List[Dict[str, Any]],
    ) -> Tuple[int, List[Dict[str, Any]], Dict[int, str]]:
        """
        Importe le plan comptable Odoo vers AZALS.

        Args:
            odoo_accounts: Liste des comptes Odoo

        Returns:
            Tuple (created_count, errors, accounts_map)
            accounts_map: {odoo_id: account_number}
        """
        from app.modules.accounting.models import AccountType, ChartOfAccounts

        created = 0
        errors = []
        accounts_map = {}

        for account in odoo_accounts:
            odoo_id = account.get("id")
            code = account.get("code", "")
            name = account.get("name", "")
            odoo_type = account.get("account_type", "asset_current")

            if not code:
                errors.append({
                    "odoo_id": odoo_id,
                    "error": "Code compte manquant",
                })
                continue

            # Déterminer la classe comptable (premier chiffre du code)
            account_class = code[0] if code and code[0].isdigit() else "0"

            # Mapper le type de compte
            azals_type_str = self.ACCOUNT_TYPE_MAPPING.get(odoo_type, "ASSET")
            azals_type = getattr(AccountType, azals_type_str, AccountType.ASSET)

            try:
                savepoint = self.db.begin_nested()

                existing = (
                    self.db.query(ChartOfAccounts)
                    .filter(
                        ChartOfAccounts.tenant_id == self.tenant_id,
                        ChartOfAccounts.account_number == code,
                    )
                    .first()
                )

                if existing:
                    existing.account_label = name
                    existing.account_type = azals_type
                    existing.account_class = account_class
                    existing.updated_at = datetime.utcnow()
                    savepoint.commit()
                    accounts_map[odoo_id] = code
                    logger.debug("Compte mis à jour: %s", code)
                else:
                    new_account = ChartOfAccounts(
                        tenant_id=self.tenant_id,
                        account_number=code,
                        account_label=name,
                        account_type=azals_type,
                        account_class=account_class,
                        is_auxiliary=odoo_type in (
                            "asset_receivable",
                            "liability_payable",
                        ),
                        is_active=True,
                    )
                    self.db.add(new_account)
                    savepoint.commit()
                    created += 1
                    accounts_map[odoo_id] = code
                    logger.debug("Compte créé: %s", code)

            except Exception as e:
                self.db.rollback()
                errors.append({
                    "odoo_id": odoo_id,
                    "code": code,
                    "error": str(e)[:200],
                })
                # Ajouter au mapping malgré l'erreur pour ne pas bloquer les écritures
                accounts_map[odoo_id] = code

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

        return created, errors, accounts_map

    def _fetch_move_lines(
        self,
        connector: Any,
        moves: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Récupère toutes les lignes d'écriture en une seule requête.

        Args:
            connector: Connecteur Odoo
            moves: Liste des écritures

        Returns:
            Liste des lignes
        """
        move_ids = [m["id"] for m in moves]
        line_fields = [
            "id",
            "move_id",
            "account_id",
            "partner_id",
            "name",
            "debit",
            "credit",
            "date",
            "ref",
            "currency_id",
        ]
        return connector.search_read(
            "account.move.line",
            [("move_id", "in", move_ids)],
            line_fields,
        )

    @staticmethod
    def _group_lines_by_move(
        lines: List[Dict[str, Any]],
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Groupe les lignes par move_id.

        Args:
            lines: Liste des lignes d'écriture

        Returns:
            Dictionnaire {move_id: [lines]}
        """
        lines_by_move = {}
        for line in lines:
            move_id = line.get("move_id")
            if isinstance(move_id, (list, tuple)):
                move_id = move_id[0]
            if move_id not in lines_by_move:
                lines_by_move[move_id] = []
            lines_by_move[move_id].append(line)
        return lines_by_move

    def _import_journal_entries(
        self,
        moves: List[Dict[str, Any]],
        lines_by_move: Dict[int, List[Dict[str, Any]]],
        accounts_map: Dict[int, str],
        journals_map: Dict[int, Dict[str, str]],
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Importe les écritures comptables Odoo vers AZALS.

        Args:
            moves: Liste des écritures (account.move)
            lines_by_move: Lignes groupées par move_id
            accounts_map: Mapping {odoo_account_id: account_number}
            journals_map: Mapping {odoo_journal_id: {code, label, type}}

        Returns:
            Tuple (created_count, updated_count, errors)
        """
        from app.modules.accounting.models import (
            AccountingFiscalYear,
            AccountingJournalEntry,
            AccountingJournalEntryLine,
            EntryStatus,
        )

        created = 0
        updated = 0
        errors = []
        fiscal_years_cache = {}

        for move in moves:
            odoo_id = move.get("id")
            entry_number = move.get("name", f"ODOO-{odoo_id}")
            entry_date_str = move.get("date")
            journal_value = move.get("journal_id")
            ref = move.get("ref", "")

            # Parser la date
            entry_date = self._parse_date(entry_date_str) or datetime.utcnow()

            # Déterminer le journal
            journal_id = self._get_odoo_id(journal_value)
            journal_info = journals_map.get(
                journal_id,
                {"code": "OD", "label": "Divers"},
            )

            # Période comptable
            period = entry_date.strftime("%Y-%m")
            year = entry_date.year

            # Trouver ou créer l'exercice fiscal
            fiscal_year_id = self._get_or_create_fiscal_year(
                year,
                entry_date,
                fiscal_years_cache,
                AccountingFiscalYear,
            )

            try:
                savepoint = self.db.begin_nested()

                existing = (
                    self.db.query(AccountingJournalEntry)
                    .filter(
                        AccountingJournalEntry.tenant_id == self.tenant_id,
                        AccountingJournalEntry.entry_number == entry_number,
                    )
                    .first()
                )

                if existing:
                    # Supprimer les anciennes lignes et recréer
                    self.db.query(AccountingJournalEntryLine).filter(
                        AccountingJournalEntryLine.entry_id == existing.id
                    ).delete()

                    existing.piece_number = ref or entry_number
                    existing.journal_code = journal_info["code"]
                    existing.journal_label = journal_info["label"]
                    existing.entry_date = entry_date
                    existing.period = period
                    existing.label = f"Import Odoo - {entry_number}"
                    existing.status = EntryStatus.POSTED
                    existing.updated_at = datetime.utcnow()

                    entry = existing
                    updated += 1
                else:
                    entry = AccountingJournalEntry(
                        tenant_id=self.tenant_id,
                        entry_number=entry_number,
                        piece_number=ref or entry_number,
                        journal_code=journal_info["code"],
                        journal_label=journal_info["label"],
                        fiscal_year_id=fiscal_year_id,
                        entry_date=entry_date,
                        period=period,
                        label=f"Import Odoo - {entry_number}",
                        status=EntryStatus.POSTED,
                        document_type="ODOO_IMPORT",
                    )
                    self.db.add(entry)
                    self.db.flush()
                    created += 1

                # Créer les lignes
                move_lines = lines_by_move.get(odoo_id, [])
                total_debit, total_credit = self._create_entry_lines(
                    entry,
                    move_lines,
                    accounts_map,
                    AccountingJournalEntryLine,
                )

                # Mettre à jour les totaux
                entry.total_debit = total_debit
                entry.total_credit = total_credit
                entry.is_balanced = total_debit == total_credit

                savepoint.commit()

            except Exception as e:
                self.db.rollback()
                errors.append({
                    "odoo_id": odoo_id,
                    "entry_number": entry_number,
                    "error": str(e)[:200],
                })
                logger.warning(
                    "Erreur écriture %s: %s",
                    entry_number,
                    str(e)[:100],
                )

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

        return created, updated, errors

    def _get_or_create_fiscal_year(
        self,
        year: int,
        entry_date: datetime,
        cache: Dict[int, UUID],
        model: Any,
    ) -> UUID:
        """
        Récupère ou crée un exercice fiscal pour l'année donnée.

        Args:
            year: Année de l'exercice
            entry_date: Date de l'écriture
            cache: Cache des exercices déjà récupérés
            model: Modèle AccountingFiscalYear

        Returns:
            ID de l'exercice fiscal
        """
        if year in cache:
            return cache[year]

        fiscal_year = (
            self.db.query(model)
            .filter(
                model.tenant_id == self.tenant_id,
                model.start_date <= entry_date,
                model.end_date >= entry_date,
            )
            .first()
        )

        if not fiscal_year:
            fiscal_year = (
                self.db.query(model)
                .filter(
                    model.tenant_id == self.tenant_id,
                    model.code == f"FY{year}",
                )
                .first()
            )

        if not fiscal_year:
            fiscal_year = model(
                tenant_id=self.tenant_id,
                name=f"Exercice {year}",
                code=f"FY{year}",
                start_date=datetime(year, 1, 1),
                end_date=datetime(year, 12, 31, 23, 59, 59),
            )
            self.db.add(fiscal_year)
            self.db.commit()
            self.db.refresh(fiscal_year)
            logger.info("Exercice fiscal créé: FY%d", year)

        cache[year] = fiscal_year.id
        return fiscal_year.id

    def _create_entry_lines(
        self,
        entry: Any,
        move_lines: List[Dict[str, Any]],
        accounts_map: Dict[int, str],
        line_model: Any,
    ) -> Tuple[Decimal, Decimal]:
        """
        Crée les lignes d'une écriture comptable.

        Args:
            entry: Écriture comptable
            move_lines: Lignes Odoo
            accounts_map: Mapping des comptes
            line_model: Modèle AccountingJournalEntryLine

        Returns:
            Tuple (total_debit, total_credit)
        """
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for idx, line in enumerate(move_lines, start=1):
            account_odoo_id = self._get_odoo_id(line.get("account_id"))
            account_number = accounts_map.get(
                account_odoo_id,
                str(account_odoo_id),
            )
            account_label = self._get_odoo_name(line.get("account_id")) or "Compte"

            debit = Decimal(str(line.get("debit", 0) or 0))
            credit = Decimal(str(line.get("credit", 0) or 0))
            label = line.get("name", "")

            # Code auxiliaire si partenaire
            auxiliary_code = None
            partner_id = self._get_odoo_id(line.get("partner_id"))
            if partner_id:
                auxiliary_code = f"ODOO-{partner_id}"

            entry_line = line_model(
                tenant_id=self.tenant_id,
                entry_id=entry.id,
                line_number=idx,
                account_number=account_number,
                account_label=account_label,
                label=label,
                debit=debit,
                credit=credit,
                auxiliary_code=auxiliary_code,
            )
            self.db.add(entry_line)

            total_debit += debit
            total_credit += credit

        return total_debit, total_credit
