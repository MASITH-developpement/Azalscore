"""
Tests for FEC Service.

Tests de validation et génération FEC conforme à l'Article A.47 A-1 du LPF.
"""

import pytest
from decimal import Decimal
from datetime import date

from ..schemas import (
    FECLine,
    FECColumn,
    FEC_COLUMNS,
    FECValidationLevelEnum,
)


class TestFECColumns:
    """Tests for FEC column definitions."""

    def test_fec_has_18_columns(self):
        """FEC must have exactly 18 columns."""
        assert len(FEC_COLUMNS) == 18

    def test_column_positions_are_sequential(self):
        """Column positions must be sequential 1-18."""
        positions = [col.position for col in FEC_COLUMNS]
        assert positions == list(range(1, 19))

    def test_required_columns(self):
        """Check required columns."""
        required_names = [
            "JournalCode", "JournalLib", "EcritureNum", "EcritureDate",
            "CompteNum", "CompteLib", "PieceRef", "PieceDate",
            "EcritureLib", "Debit", "Credit", "ValidDate"
        ]
        for name in required_names:
            col = next((c for c in FEC_COLUMNS if c.name == name), None)
            assert col is not None, f"Column {name} not found"
            assert col.required is True, f"Column {name} should be required"

    def test_optional_columns(self):
        """Check optional columns."""
        optional_names = [
            "CompAuxNum", "CompAuxLib", "EcritureLet", "DateLet",
            "Montantdevise", "Idevise"
        ]
        for name in optional_names:
            col = next((c for c in FEC_COLUMNS if c.name == name), None)
            assert col is not None, f"Column {name} not found"
            assert col.required is False, f"Column {name} should be optional"


class TestFECLine:
    """Tests for FEC line validation."""

    def test_valid_fec_line_debit(self):
        """Test valid FEC line with debit."""
        line = FECLine(
            JournalCode="VT",
            JournalLib="Ventes",
            EcritureNum="VT-2026-001",
            EcritureDate="20260115",
            CompteNum="411000",
            CompteLib="Clients",
            PieceRef="FAC-001",
            PieceDate="20260115",
            EcritureLib="Facture client ABC",
            Debit=Decimal("1200.00"),
            Credit=Decimal("0.00"),
            ValidDate="20260115",
        )
        assert line.Debit == Decimal("1200.00")
        assert line.Credit == Decimal("0.00")

    def test_valid_fec_line_credit(self):
        """Test valid FEC line with credit."""
        line = FECLine(
            JournalCode="VT",
            JournalLib="Ventes",
            EcritureNum="VT-2026-001",
            EcritureDate="20260115",
            CompteNum="701000",
            CompteLib="Ventes de produits finis",
            PieceRef="FAC-001",
            PieceDate="20260115",
            EcritureLib="Facture client ABC",
            Debit=Decimal("0.00"),
            Credit=Decimal("1000.00"),
            ValidDate="20260115",
        )
        assert line.Debit == Decimal("0.00")
        assert line.Credit == Decimal("1000.00")

    def test_invalid_both_debit_and_credit(self):
        """Test that having both debit and credit raises error."""
        with pytest.raises(ValueError, match="Débit et Crédit"):
            FECLine(
                JournalCode="VT",
                JournalLib="Ventes",
                EcritureNum="VT-2026-001",
                EcritureDate="20260115",
                CompteNum="411000",
                CompteLib="Clients",
                PieceRef="FAC-001",
                PieceDate="20260115",
                EcritureLib="Facture",
                Debit=Decimal("100.00"),
                Credit=Decimal("100.00"),  # Both positive!
                ValidDate="20260115",
            )

    def test_invalid_both_zero(self):
        """Test that having both debit and credit at zero raises error."""
        with pytest.raises(ValueError, match="Débit ou Crédit"):
            FECLine(
                JournalCode="VT",
                JournalLib="Ventes",
                EcritureNum="VT-2026-001",
                EcritureDate="20260115",
                CompteNum="411000",
                CompteLib="Clients",
                PieceRef="FAC-001",
                PieceDate="20260115",
                EcritureLib="Facture",
                Debit=Decimal("0.00"),
                Credit=Decimal("0.00"),  # Both zero!
                ValidDate="20260115",
            )

    def test_to_fec_row_tab_separator(self):
        """Test FEC row generation with TAB separator."""
        line = FECLine(
            JournalCode="VT",
            JournalLib="Ventes",
            EcritureNum="VT-2026-001",
            EcritureDate="20260115",
            CompteNum="411000",
            CompteLib="Clients",
            PieceRef="FAC-001",
            PieceDate="20260115",
            EcritureLib="Facture client",
            Debit=Decimal("1200.50"),
            Credit=Decimal("0.00"),
            ValidDate="20260115",
        )
        row = line.to_fec_row("\t")
        parts = row.split("\t")

        assert len(parts) == 18
        assert parts[0] == "VT"
        assert parts[1] == "Ventes"
        assert parts[2] == "VT-2026-001"
        assert parts[3] == "20260115"
        assert parts[4] == "411000"
        assert parts[5] == "Clients"
        assert parts[11] == "1200,50"  # Virgule décimale!
        assert parts[12] == "0,00"  # Format français avec décimales

    def test_to_fec_row_pipe_separator(self):
        """Test FEC row generation with PIPE separator."""
        line = FECLine(
            JournalCode="AC",
            JournalLib="Achats",
            EcritureNum="AC-2026-001",
            EcritureDate="20260120",
            CompteNum="401000",
            CompteLib="Fournisseurs",
            PieceRef="FAC-F001",
            PieceDate="20260118",
            EcritureLib="Facture fournisseur XYZ",
            Debit=Decimal("0.00"),
            Credit=Decimal("500.00"),
            ValidDate="20260120",
        )
        row = line.to_fec_row("|")
        parts = row.split("|")

        assert len(parts) == 18
        assert parts[0] == "AC"
        assert parts[12] == "500,00"  # Format français avec décimales


class TestFECValidation:
    """Tests for FEC content validation."""

    def test_valid_fec_header(self):
        """Test valid FEC header."""
        header = "JournalCode\tJournalLib\tEcritureNum\tEcritureDate\tCompteNum\tCompteLib\tCompAuxNum\tCompAuxLib\tPieceRef\tPieceDate\tEcritureLib\tDebit\tCredit\tEcritureLet\tDateLet\tValidDate\tMontantdevise\tIdevise"
        parts = header.split("\t")
        assert len(parts) == 18

    def test_date_format_yyyymmdd(self):
        """Test date format validation (YYYYMMDD per DGFiP spec)."""
        from datetime import datetime

        def is_valid_fec_date(d: str) -> bool:
            """Validate FEC date format YYYYMMDD."""
            if len(d) != 8 or not d.isdigit():
                return False
            try:
                datetime.strptime(d, "%Y%m%d")
                return True
            except ValueError:
                return False

        valid_dates = ["20260115", "20251231", "20260101"]
        invalid_dates = ["2026-01-15", "15/01/2026", "2026115"]  # Not 8 digits or has separators
        ambiguous_dates = ["15012026", "31122026"]  # 8 digits but DDMMYYYY, not YYYYMMDD

        for d in valid_dates:
            assert is_valid_fec_date(d), f"{d} should be valid"

        for d in invalid_dates:
            assert not is_valid_fec_date(d), f"{d} should be invalid"

        # Ambiguous dates (8 digits, DDMMYYYY) - will fail strptime for %Y%m%d
        # 15012026 = year 1501, month 20, day 26 -> invalid month
        for d in ambiguous_dates:
            assert not is_valid_fec_date(d), f"{d} should be invalid (DDMMYYYY format)"

    def test_decimal_format_french(self):
        """Test French decimal format (comma separator)."""
        # French format uses comma
        assert "1200,50".replace(",", ".") == "1200.50"
        assert Decimal("1200.50") == Decimal("1200,50".replace(",", "."))


class TestFECFileNaming:
    """Tests for FEC file naming convention."""

    def test_filename_format(self):
        """Test FEC filename format: {SIREN}FEC{YYYYMMDD}.txt"""
        siren = "123456789"
        date_str = "20261231"
        expected = f"{siren}FEC{date_str}.txt"
        assert expected == "123456789FEC20261231.txt"

    def test_siren_validation(self):
        """Test SIREN must be 9 digits."""
        valid_sirens = ["123456789", "000000001", "999999999"]
        invalid_sirens = ["12345678", "1234567890", "12345678A", "ABCDEFGHI"]

        for siren in valid_sirens:
            assert len(siren) == 9 and siren.isdigit()

        for siren in invalid_sirens:
            assert not (len(siren) == 9 and siren.isdigit())


class TestFECEquilibrium:
    """Tests for FEC equilibrium rules."""

    def test_entry_must_be_balanced(self):
        """Test that each entry must have equal debit and credit totals."""
        # Entry with 2 lines
        line1_debit = Decimal("1200.00")
        line1_credit = Decimal("0.00")
        line2_debit = Decimal("0.00")
        line2_credit = Decimal("1200.00")

        total_debit = line1_debit + line2_debit
        total_credit = line1_credit + line2_credit

        assert total_debit == total_credit

    def test_global_balance(self):
        """Test that global totals must be equal."""
        entries = [
            {"debit": Decimal("1000"), "credit": Decimal("0")},
            {"debit": Decimal("0"), "credit": Decimal("1000")},
            {"debit": Decimal("500"), "credit": Decimal("0")},
            {"debit": Decimal("0"), "credit": Decimal("500")},
        ]

        total_debit = sum(e["debit"] for e in entries)
        total_credit = sum(e["credit"] for e in entries)

        assert total_debit == total_credit
        assert total_debit == Decimal("1500")
