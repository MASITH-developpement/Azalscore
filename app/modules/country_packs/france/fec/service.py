"""
AZALS MODULE - FEC: Service
============================

Service de génération et validation du FEC conforme à l'Article A.47 A-1 du LPF.

Conformité DGFiP:
- 18 colonnes obligatoires
- Format YYYYMMDD pour les dates
- Virgule comme séparateur décimal
- Pas de séparateur de milliers
- Numérotation continue sans rupture
- Équilibre débit/crédit par écriture
"""
from __future__ import annotations


import hashlib
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from io import StringIO
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.finance.models import (
    JournalEntry,
    JournalEntryLine,
    Journal,
    Account,
    FiscalYear,
)
from .models import (
    FECExport,
    FECValidationResult,
    FECArchive,
    FECExportStatus,
    FECFormat,
    FECEncoding,
    FECSeparator,
    FECValidationLevel,
)
from .schemas import (
    FECExportRequest,
    FECExportResponse,
    FECValidationResponse,
    FECValidationIssue,
    FECStatistics,
    FECLine,
    FECColumn,
    FEC_COLUMNS,
    FECValidationLevelEnum,
    FECExportStatusEnum,
)
from ..exceptions import FECError, FECGenerationError, FECValidationError

logger = logging.getLogger(__name__)


class FECService:
    """
    Service de génération et validation FEC.

    Implémente les exigences de l'Article A.47 A-1 du Livre des Procédures Fiscales:
    - Format fichier normalisé (18 colonnes)
    - Nommage: {SIREN}FEC{YYYYMMDD}.txt
    - Encodage UTF-8 ou ISO-8859-15
    - Séparateur TAB ou PIPE
    """

    # En-têtes FEC (noms des colonnes)
    FEC_HEADERS = [col.name for col in FEC_COLUMNS]

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # GÉNÉRATION FEC
    # ========================================================================

    async def generate_fec(self, request: FECExportRequest) -> FECExport:
        """
        Génère un fichier FEC complet pour un exercice fiscal.

        Args:
            request: Paramètres d'export

        Returns:
            FECExport: Export créé avec fichier généré

        Raises:
            ValueError: Si les paramètres sont invalides
            RuntimeError: Si la génération échoue
        """
        logger.info(f"[FEC] Génération FEC pour tenant={self.tenant_id}, siren={request.siren}")

        # 1. Récupérer l'exercice fiscal
        fiscal_year = await self._get_fiscal_year(request.fiscal_year_id)
        if not fiscal_year:
            raise ValueError(f"Exercice fiscal non trouvé: {request.fiscal_year_id}")

        # 2. Créer l'enregistrement d'export
        export = FECExport(
            tenant_id=self.tenant_id,
            siren=request.siren,
            company_name=request.company_name,
            fiscal_year_id=fiscal_year.id,
            fiscal_year_code=fiscal_year.code,
            start_date=request.start_date or fiscal_year.start_date,
            end_date=request.end_date or fiscal_year.end_date,
            format=FECFormat(request.format.value),
            encoding=FECEncoding(request.encoding.value),
            separator=FECSeparator(request.separator.value),
            status=FECExportStatus.GENERATING,
            requested_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
        )
        self.db.add(export)
        await self.db.flush()

        try:
            # 3. Récupérer les écritures comptables
            entries = await self._get_journal_entries(
                fiscal_year_id=fiscal_year.id,
                start_date=export.start_date,
                end_date=export.end_date,
                journal_codes=request.journal_codes,
                include_draft=request.include_draft,
            )

            if not entries:
                raise ValueError("Aucune écriture comptable trouvée pour cette période")

            # 4. Générer le contenu FEC
            fec_content, statistics = await self._generate_fec_content(
                entries=entries,
                separator=self._get_separator_char(export.separator),
            )

            # 5. Encoder le fichier
            encoded_content = self._encode_content(fec_content, export.encoding)

            # 6. Calculer le hash et générer le nom de fichier
            file_hash = hashlib.sha256(encoded_content).hexdigest()
            filename = self._generate_filename(request.siren, export.end_date, export.format)

            # 7. Mettre à jour l'export
            export.filename = filename
            export.file_size = len(encoded_content)
            export.file_hash = file_hash
            export.total_entries = statistics.total_entries
            export.total_lines = statistics.total_lines
            export.total_debit = statistics.total_debit
            export.total_credit = statistics.total_credit
            export.status = FECExportStatus.VALIDATING

            # 8. Valider le FEC généré
            validation_result = await self._validate_fec_content(fec_content, export)

            export.is_valid = validation_result.is_valid
            export.validation_errors = validation_result.errors_count
            export.validation_warnings = validation_result.warnings_count
            export.validation_details = [issue.model_dump() for issue in validation_result.issues]

            if validation_result.is_valid:
                export.status = FECExportStatus.COMPLETED
                # Stocker le fichier (à implémenter selon le storage backend)
                export.file_path = f"/fec/{self.tenant_id}/{filename}"
            else:
                export.status = FECExportStatus.FAILED
                export.error_message = f"{validation_result.errors_count} erreurs de validation"

            export.completed_at = datetime.utcnow()
            await self.db.commit()

            logger.info(f"[FEC] Export terminé: {filename}, valid={export.is_valid}")
            return export

        except (FECGenerationError, FECValidationError, ValueError, IOError) as e:
            logger.error(f"[FEC] Erreur generation: {e}")
            export.status = FECExportStatus.FAILED
            export.error_message = str(e)
            export.completed_at = datetime.utcnow()
            await self.db.commit()
            raise

    async def _get_fiscal_year(self, fiscal_year_id: UUID) -> Optional[FiscalYear]:
        """Récupère l'exercice fiscal."""
        result = await self.db.execute(
            select(FiscalYear).where(
                and_(
                    FiscalYear.id == fiscal_year_id,
                    FiscalYear.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_journal_entries(
        self,
        fiscal_year_id: UUID,
        start_date: date,
        end_date: date,
        journal_codes: Optional[list[str]] = None,
        include_draft: bool = False,
    ) -> list[JournalEntry]:
        """
        Récupère les écritures comptables pour l'export FEC.

        Tri obligatoire: JournalCode, EcritureDate, EcritureNum
        """
        from app.modules.finance.models import EntryStatus

        query = (
            select(JournalEntry)
            .options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
                selectinload(JournalEntry.journal),
            )
            .where(
                and_(
                    JournalEntry.tenant_id == self.tenant_id,
                    JournalEntry.fiscal_year_id == fiscal_year_id,
                    JournalEntry.date >= start_date,
                    JournalEntry.date <= end_date,
                )
            )
        )

        # Filtrer les brouillons si non inclus
        if not include_draft:
            query = query.where(
                JournalEntry.status.in_([
                    EntryStatus.VALIDATED,
                    EntryStatus.POSTED,
                ])
            )

        # Filtrer par journaux si spécifié
        if journal_codes:
            query = query.join(JournalEntry.journal).where(
                Journal.code.in_(journal_codes)
            )

        # Tri obligatoire FEC: Journal, Date, Numéro
        query = query.join(JournalEntry.journal).order_by(
            Journal.code,
            JournalEntry.date,
            JournalEntry.number,
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _generate_fec_content(
        self,
        entries: list[JournalEntry],
        separator: str,
    ) -> tuple[str, FECStatistics]:
        """
        Génère le contenu du fichier FEC.

        Returns:
            tuple: (contenu_fec, statistiques)
        """
        output = StringIO()

        # En-tête (noms des colonnes)
        output.write(separator.join(self.FEC_HEADERS) + "\n")

        # Statistiques
        total_debit = Decimal("0")
        total_credit = Decimal("0")
        total_lines = 0
        journals_used = set()
        accounts_used = set()
        first_date = None
        last_date = None

        # Générer les lignes
        for entry in entries:
            journal_code = entry.journal.code if entry.journal else "OD"
            journal_lib = entry.journal.name if entry.journal else "Opérations Diverses"
            journals_used.add(journal_code)

            # Dates
            entry_date = self._format_date(entry.date)
            piece_date = entry_date  # Même date si pas de pièce séparée
            valid_date = self._format_date(entry.validated_at or entry.posted_at or entry.date)

            # Suivi dates
            if first_date is None or entry.date < first_date:
                first_date = entry.date
            if last_date is None or entry.date > last_date:
                last_date = entry.date

            # Générer une ligne par ligne d'écriture
            for line in entry.lines:
                account = line.account
                accounts_used.add(line.account_id)

                # Construire la ligne FEC
                fec_line = FECLine(
                    JournalCode=journal_code[:10],
                    JournalLib=journal_lib[:100],
                    EcritureNum=entry.number[:50],
                    EcritureDate=entry_date,
                    CompteNum=account.code[:20] if account else str(line.account_id)[:20],
                    CompteLib=account.name[:255] if account else "Compte inconnu",
                    CompAuxNum=line.partner_id[:50] if line.partner_id else None,
                    CompAuxLib=line.partner_type[:255] if line.partner_type else None,
                    PieceRef=entry.reference[:100] if entry.reference else entry.number[:100],
                    PieceDate=piece_date,
                    EcritureLib=(line.label or entry.description or "")[:255],
                    Debit=line.debit or Decimal("0"),
                    Credit=line.credit or Decimal("0"),
                    EcritureLet=line.reconcile_ref[:50] if line.reconcile_ref else None,
                    DateLet=self._format_date(line.reconciled_at) if line.reconciled_at else None,
                    ValidDate=valid_date,
                    Montantdevise=None,  # À implémenter si multi-devises
                    Idevise=None,
                )

                # Écrire la ligne
                output.write(fec_line.to_fec_row(separator) + "\n")

                # Statistiques
                total_debit += fec_line.Debit
                total_credit += fec_line.Credit
                total_lines += 1

        # Construire les statistiques
        statistics = FECStatistics(
            total_entries=len(entries),
            total_lines=total_lines,
            total_debit=total_debit,
            total_credit=total_credit,
            balance=total_debit - total_credit,
            is_balanced=abs(total_debit - total_credit) < Decimal("0.01"),
            journals_count=len(journals_used),
            accounts_count=len(accounts_used),
            first_entry_date=first_date,
            last_entry_date=last_date,
        )

        return output.getvalue(), statistics

    # ========================================================================
    # VALIDATION FEC
    # ========================================================================

    async def validate_fec(self, export_id: UUID) -> FECValidationResponse:
        """
        Valide un export FEC existant.

        Args:
            export_id: ID de l'export à valider

        Returns:
            FECValidationResponse: Résultat de validation
        """
        export = await self._get_export(export_id)
        if not export:
            raise ValueError(f"Export FEC non trouvé: {export_id}")

        # NOTE: Phase 2 - Intégration avec storage_service pour récupération fichier
        raise NotImplementedError("Validation d'export existant non implémentée")

    async def validate_fec_content(self, content: str) -> FECValidationResponse:
        """
        Valide un contenu FEC brut.

        Args:
            content: Contenu du fichier FEC

        Returns:
            FECValidationResponse: Résultat de validation
        """
        return await self._validate_fec_content(content, None)

    async def _validate_fec_content(
        self,
        content: str,
        export: Optional[FECExport],
    ) -> FECValidationResponse:
        """
        Valide le contenu d'un fichier FEC.

        Règles de validation DGFiP:
        - Structure 18 colonnes
        - Types de données corrects
        - Dates au format YYYYMMDD
        - Équilibre débit/crédit par écriture
        - Numérotation continue sans rupture
        - Montants positifs ou nuls
        """
        issues: list[FECValidationIssue] = []
        lines = content.strip().split("\n")

        if len(lines) < 2:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-001",
                message="Le fichier FEC doit contenir au moins l'en-tête et une ligne de données",
            ))
            return FECValidationResponse(
                is_valid=False,
                errors_count=1,
                issues=issues,
            )

        # 1. Valider l'en-tête
        header = lines[0]
        header_issues = self._validate_header(header)
        issues.extend(header_issues)

        # Détecter le séparateur
        separator = "\t" if "\t" in header else "|"

        # 2. Valider les lignes de données
        total_debit = Decimal("0")
        total_credit = Decimal("0")
        entries_balance: dict[str, tuple[Decimal, Decimal]] = {}  # entry_num -> (debit, credit)
        previous_entry_num = ""
        seen_entry_nums = set()

        for line_num, line in enumerate(lines[1:], start=2):
            if not line.strip():
                continue

            line_issues, debit, credit, entry_num = self._validate_line(
                line, line_num, separator
            )
            issues.extend(line_issues)

            # Statistiques
            total_debit += debit
            total_credit += credit

            # Vérifier équilibre par écriture
            if entry_num:
                if entry_num not in entries_balance:
                    entries_balance[entry_num] = (Decimal("0"), Decimal("0"))
                d, c = entries_balance[entry_num]
                entries_balance[entry_num] = (d + debit, c + credit)

                # Vérifier numérotation continue
                if entry_num in seen_entry_nums and entry_num != previous_entry_num:
                    issues.append(FECValidationIssue(
                        level=FECValidationLevelEnum.ERROR,
                        code="FEC-010",
                        message=f"Rupture de séquence: l'écriture {entry_num} apparaît après d'autres écritures",
                        line_number=line_num,
                        entry_number=entry_num,
                    ))
                seen_entry_nums.add(entry_num)
                previous_entry_num = entry_num

        # 3. Vérifier équilibre global
        if abs(total_debit - total_credit) >= Decimal("0.01"):
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-020",
                message=f"Déséquilibre global: Débit={total_debit}, Crédit={total_credit}, Différence={total_debit - total_credit}",
                expected_value="0.00",
                actual_value=str(total_debit - total_credit),
            ))

        # 4. Vérifier équilibre par écriture
        for entry_num, (debit, credit) in entries_balance.items():
            if abs(debit - credit) >= Decimal("0.01"):
                issues.append(FECValidationIssue(
                    level=FECValidationLevelEnum.ERROR,
                    code="FEC-021",
                    message=f"Déséquilibre écriture {entry_num}: Débit={debit}, Crédit={credit}",
                    entry_number=entry_num,
                    expected_value="0.00",
                    actual_value=str(debit - credit),
                ))

        # Compter erreurs et warnings
        errors_count = sum(1 for i in issues if i.level == FECValidationLevelEnum.ERROR)
        warnings_count = sum(1 for i in issues if i.level == FECValidationLevelEnum.WARNING)

        # Statistiques
        statistics = FECStatistics(
            total_entries=len(entries_balance),
            total_lines=len(lines) - 1,
            total_debit=total_debit,
            total_credit=total_credit,
            balance=total_debit - total_credit,
            is_balanced=abs(total_debit - total_credit) < Decimal("0.01"),
            journals_count=0,  # À calculer si nécessaire
            accounts_count=0,
        )

        return FECValidationResponse(
            is_valid=errors_count == 0,
            errors_count=errors_count,
            warnings_count=warnings_count,
            issues=issues,
            statistics=statistics,
        )

    def _validate_header(self, header: str) -> list[FECValidationIssue]:
        """Valide l'en-tête du fichier FEC."""
        issues = []

        # Détecter le séparateur
        if "\t" in header:
            separator = "\t"
        elif "|" in header:
            separator = "|"
        else:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-002",
                message="Séparateur non reconnu (TAB ou PIPE attendu)",
                line_number=1,
            ))
            return issues

        columns = header.split(separator)

        # Vérifier le nombre de colonnes
        if len(columns) != 18:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-003",
                message=f"Nombre de colonnes incorrect: {len(columns)} (18 attendues)",
                line_number=1,
                expected_value="18",
                actual_value=str(len(columns)),
            ))
            return issues

        # Vérifier les noms de colonnes
        for i, (expected, actual) in enumerate(zip(self.FEC_HEADERS, columns)):
            if expected.strip().lower() != actual.strip().lower():
                issues.append(FECValidationIssue(
                    level=FECValidationLevelEnum.ERROR,
                    code="FEC-004",
                    message=f"Colonne {i + 1}: '{actual}' trouvé, '{expected}' attendu",
                    line_number=1,
                    column_name=expected,
                    expected_value=expected,
                    actual_value=actual,
                ))

        return issues

    def _validate_line(
        self,
        line: str,
        line_num: int,
        separator: str,
    ) -> tuple[list[FECValidationIssue], Decimal, Decimal, str]:
        """
        Valide une ligne de données FEC.

        Returns:
            tuple: (issues, debit, credit, entry_number)
        """
        issues = []
        debit = Decimal("0")
        credit = Decimal("0")
        entry_num = ""

        columns = line.split(separator)

        # Vérifier le nombre de colonnes
        if len(columns) != 18:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-005",
                message=f"Nombre de colonnes incorrect: {len(columns)} (18 attendues)",
                line_number=line_num,
                expected_value="18",
                actual_value=str(len(columns)),
            ))
            return issues, debit, credit, entry_num

        # Extraire les valeurs
        journal_code = columns[0].strip()
        journal_lib = columns[1].strip()
        entry_num = columns[2].strip()
        entry_date = columns[3].strip()
        compte_num = columns[4].strip()
        compte_lib = columns[5].strip()
        piece_ref = columns[8].strip()
        piece_date = columns[9].strip()
        ecriture_lib = columns[10].strip()
        debit_str = columns[11].strip()
        credit_str = columns[12].strip()
        valid_date = columns[15].strip()

        # Valider les champs obligatoires
        if not journal_code:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-006",
                message="JournalCode obligatoire",
                line_number=line_num,
                column_name="JournalCode",
            ))

        if not entry_num:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-006",
                message="EcritureNum obligatoire",
                line_number=line_num,
                column_name="EcritureNum",
            ))

        if not compte_num:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-006",
                message="CompteNum obligatoire",
                line_number=line_num,
                column_name="CompteNum",
            ))

        # Valider les dates
        for date_field, date_value, col_name in [
            (entry_date, entry_date, "EcritureDate"),
            (piece_date, piece_date, "PieceDate"),
            (valid_date, valid_date, "ValidDate"),
        ]:
            if date_value and not self._is_valid_date(date_value):
                issues.append(FECValidationIssue(
                    level=FECValidationLevelEnum.ERROR,
                    code="FEC-007",
                    message=f"Date invalide: '{date_value}' (format YYYYMMDD attendu)",
                    line_number=line_num,
                    column_name=col_name,
                    actual_value=date_value,
                ))

        # Valider les montants
        debit = self._parse_amount(debit_str)
        credit = self._parse_amount(credit_str)

        if debit < 0:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-008",
                message="Montant débit négatif",
                line_number=line_num,
                column_name="Debit",
                actual_value=debit_str,
            ))

        if credit < 0:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-008",
                message="Montant crédit négatif",
                line_number=line_num,
                column_name="Credit",
                actual_value=credit_str,
            ))

        if debit > 0 and credit > 0:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.ERROR,
                code="FEC-009",
                message="Débit et crédit tous deux positifs sur la même ligne",
                line_number=line_num,
                entry_number=entry_num,
            ))

        if debit == 0 and credit == 0:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.WARNING,
                code="FEC-011",
                message="Ligne avec débit et crédit à zéro",
                line_number=line_num,
                entry_number=entry_num,
            ))

        # Vérifier cohérence dates (EcritureDate >= PieceDate)
        if entry_date and piece_date and entry_date < piece_date:
            issues.append(FECValidationIssue(
                level=FECValidationLevelEnum.WARNING,
                code="FEC-012",
                message="Date d'écriture antérieure à la date de pièce",
                line_number=line_num,
                entry_number=entry_num,
            ))

        return issues, debit, credit, entry_num

    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    def _format_date(self, d: date | datetime | None) -> str:
        """Formate une date au format FEC (YYYYMMDD)."""
        if d is None:
            return ""
        if isinstance(d, datetime):
            d = d.date()
        return d.strftime("%Y%m%d")

    def _is_valid_date(self, date_str: str) -> bool:
        """Vérifie si une chaîne est une date valide au format YYYYMMDD."""
        if len(date_str) != 8 or not date_str.isdigit():
            return False
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            date(year, month, day)
            return True
        except ValueError:
            return False

    def _parse_amount(self, amount_str: str) -> Decimal:
        """Parse un montant FEC (virgule décimale)."""
        if not amount_str:
            return Decimal("0")
        # Remplacer la virgule par un point pour le parsing
        amount_str = amount_str.replace(",", ".").replace(" ", "")
        try:
            return Decimal(amount_str)
        except (ValueError, TypeError, ArithmeticError):
            return Decimal("0")

    def _get_separator_char(self, separator: FECSeparator) -> str:
        """Retourne le caractère séparateur."""
        return "\t" if separator == FECSeparator.TAB else "|"

    def _encode_content(self, content: str, encoding: FECEncoding) -> bytes:
        """Encode le contenu selon l'encodage spécifié."""
        encoding_name = "utf-8" if encoding == FECEncoding.UTF8 else "iso-8859-15"
        return content.encode(encoding_name)

    def _generate_filename(
        self,
        siren: str,
        end_date: date | datetime,
        format: FECFormat,
    ) -> str:
        """
        Génère le nom de fichier FEC selon la norme DGFiP.

        Format: {SIREN}FEC{YYYYMMDD}.{ext}
        """
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        date_str = end_date.strftime("%Y%m%d")
        ext = "txt" if format == FECFormat.TXT else "xml"
        return f"{siren}FEC{date_str}.{ext}"

    # ========================================================================
    # CRUD EXPORTS
    # ========================================================================

    async def _get_export(self, export_id: UUID) -> Optional[FECExport]:
        """Récupère un export FEC."""
        result = await self.db.execute(
            select(FECExport).where(
                and_(
                    FECExport.id == export_id,
                    FECExport.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_exports(
        self,
        fiscal_year_code: Optional[str] = None,
        status: Optional[FECExportStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[FECExport], int]:
        """Liste les exports FEC avec filtres."""
        query = select(FECExport).where(FECExport.tenant_id == self.tenant_id)

        if fiscal_year_code:
            query = query.where(FECExport.fiscal_year_code == fiscal_year_code)
        if status:
            query = query.where(FECExport.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        # Results
        query = query.order_by(FECExport.requested_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_export(self, export_id: UUID) -> Optional[FECExport]:
        """Récupère un export FEC par ID."""
        return await self._get_export(export_id)

    async def download_export(self, export_id: UUID) -> tuple[str, bytes]:
        """
        Télécharge le fichier FEC.

        Returns:
            tuple: (filename, content)
        """
        export = await self._get_export(export_id)
        if not export:
            raise ValueError(f"Export FEC non trouvé: {export_id}")

        if export.status != FECExportStatus.COMPLETED:
            raise ValueError(f"Export non terminé: {export.status}")

        # NOTE: Phase 2 - Intégration avec storage_service
        raise NotImplementedError("Téléchargement depuis storage non implémenté")

    # ========================================================================
    # ARCHIVAGE
    # ========================================================================

    async def archive_export(self, export_id: UUID) -> FECArchive:
        """
        Archive un export FEC pour conservation légale (10 ans).

        Args:
            export_id: ID de l'export à archiver

        Returns:
            FECArchive: Archive créée
        """
        export = await self._get_export(export_id)
        if not export:
            raise ValueError(f"Export FEC non trouvé: {export_id}")

        if export.status != FECExportStatus.COMPLETED:
            raise ValueError("Seuls les exports terminés peuvent être archivés")

        if not export.is_valid:
            raise ValueError("Seuls les exports valides peuvent être archivés")

        # Créer l'archive
        archive = FECArchive(
            tenant_id=self.tenant_id,
            export_id=export.id,
            siren=export.siren,
            fiscal_year_code=export.fiscal_year_code,
            filename=export.filename,
            file_hash=export.file_hash,
            file_size=export.file_size,
            archived_at=datetime.utcnow(),
            retention_until=datetime.utcnow() + timedelta(days=365 * 10),  # 10 ans
        )
        self.db.add(archive)

        # Mettre à jour le statut de l'export
        export.status = FECExportStatus.ARCHIVED

        await self.db.commit()
        return archive
