"""
Tests for PCG 2025 Module.

Tests de validation du Plan Comptable Général 2025 conforme à l'ANC.
"""

import pytest

from ..pcg2025_accounts import (
    PCG2025_ALL_ACCOUNTS,
    PCG2025_CLASSE_1,
    PCG2025_CLASSE_2,
    PCG2025_CLASSE_3,
    PCG2025_CLASSE_4,
    PCG2025_CLASSE_5,
    PCG2025_CLASSE_6,
    PCG2025_CLASSE_7,
    PCG2025_CLASSE_8,
    get_pcg2025_account,
    get_pcg2025_class,
    get_pcg2025_summary_accounts,
    validate_pcg_account_number,
    get_parent_account_number,
)
from ..schemas import PCGAccountCreate, PCG_CLASSES


class TestPCG2025Accounts:
    """Tests for PCG 2025 account definitions."""

    def test_pcg_has_all_classes(self):
        """PCG must have accounts in all 8 classes."""
        classes_present = set()
        for account in PCG2025_ALL_ACCOUNTS:
            classes_present.add(account.pcg_class)

        assert classes_present == {"1", "2", "3", "4", "5", "6", "7", "8"}

    def test_pcg_has_minimum_accounts(self):
        """PCG 2025 should have at least 300 standard accounts."""
        assert len(PCG2025_ALL_ACCOUNTS) >= 300

    def test_classe_1_comptes_capitaux(self):
        """Classe 1 should have capital accounts."""
        class_1 = get_pcg2025_class("1")
        assert len(class_1) > 0

        # Check essential accounts
        essential = ["10", "101", "106", "12", "16"]
        class_1_numbers = [a.number for a in class_1]
        for num in essential:
            assert num in class_1_numbers, f"Compte {num} manquant en classe 1"

    def test_classe_2_immobilisations(self):
        """Classe 2 should have asset accounts."""
        class_2 = get_pcg2025_class("2")
        assert len(class_2) > 0

        # Check essential accounts
        essential = ["20", "21", "27", "28"]
        class_2_numbers = [a.number for a in class_2]
        for num in essential:
            assert num in class_2_numbers, f"Compte {num} manquant en classe 2"

    def test_classe_4_tiers(self):
        """Classe 4 should have third-party accounts."""
        class_4 = get_pcg2025_class("4")
        assert len(class_4) > 0

        # Check essential accounts
        essential = ["40", "401", "41", "411", "44", "445"]
        class_4_numbers = [a.number for a in class_4]
        for num in essential:
            assert num in class_4_numbers, f"Compte {num} manquant en classe 4"

    def test_classe_6_charges(self):
        """Classe 6 should have expense accounts."""
        class_6 = get_pcg2025_class("6")
        assert len(class_6) > 0

        # Check essential accounts
        essential = ["60", "61", "62", "63", "64", "65", "66", "67", "68"]
        class_6_numbers = [a.number for a in class_6]
        for num in essential:
            assert num in class_6_numbers, f"Compte {num} manquant en classe 6"

    def test_classe_7_produits(self):
        """Classe 7 should have revenue accounts."""
        class_7 = get_pcg2025_class("7")
        assert len(class_7) > 0

        # Check essential accounts
        essential = ["70", "74", "75", "76", "77", "78"]
        class_7_numbers = [a.number for a in class_7]
        for num in essential:
            assert num in class_7_numbers, f"Compte {num} manquant en classe 7"


class TestAccountValidation:
    """Tests for account number validation."""

    def test_valid_account_numbers(self):
        """Test valid PCG account numbers."""
        valid_numbers = ["10", "101", "411000", "6011", "70", "8011"]
        for num in valid_numbers:
            assert validate_pcg_account_number(num), f"{num} should be valid"

    def test_invalid_account_numbers(self):
        """Test invalid PCG account numbers."""
        invalid_numbers = ["0", "9", "91", "A10", "", "1"]
        for num in invalid_numbers:
            assert not validate_pcg_account_number(num), f"{num} should be invalid"

    def test_class_0_invalid(self):
        """Classe 0 is not valid in PCG."""
        assert not validate_pcg_account_number("01")
        assert not validate_pcg_account_number("001")

    def test_class_9_invalid(self):
        """Classe 9 (analytical) is not in standard PCG."""
        assert not validate_pcg_account_number("91")
        assert not validate_pcg_account_number("901")


class TestAccountHierarchy:
    """Tests for account hierarchy."""

    def test_parent_account_number(self):
        """Test parent account number extraction."""
        assert get_parent_account_number("411") == "41"
        assert get_parent_account_number("4111") == "411"
        # 2-digit accounts have no parent (single-digit accounts don't exist in PCG)
        assert get_parent_account_number("41") is None
        assert get_parent_account_number("4") is None
        assert get_parent_account_number("10") is None

    def test_get_existing_account(self):
        """Test retrieving existing PCG account."""
        account = get_pcg2025_account("411")
        assert account is not None
        assert account.label == "Clients"
        assert account.pcg_class == "4"
        assert account.normal_balance == "D"

    def test_get_nonexistent_account(self):
        """Test retrieving non-existent account."""
        account = get_pcg2025_account("999999")
        assert account is None


class TestAccountBalance:
    """Tests for normal balance rules."""

    def test_classe_1_balance(self):
        """Classe 1 (capitaux) should mostly be credit."""
        class_1 = get_pcg2025_class("1")
        # Most capital accounts have credit balance
        credit_accounts = [a for a in class_1 if a.normal_balance == "C"]
        assert len(credit_accounts) > len(class_1) / 2

    def test_classe_2_balance(self):
        """Classe 2 (immobilisations) should mostly be debit."""
        class_2 = get_pcg2025_class("2")
        debit_accounts = [a for a in class_2 if a.normal_balance == "D"]
        # Most immobilizations are debit except amortissements
        assert len(debit_accounts) > len(class_2) / 2

    def test_classe_6_charges_debit(self):
        """Classe 6 (charges) should be debit."""
        class_6 = get_pcg2025_class("6")
        debit_accounts = [a for a in class_6 if a.normal_balance == "D"]
        # Almost all expense accounts are debit
        assert len(debit_accounts) > len(class_6) * 0.9

    def test_classe_7_produits_credit(self):
        """Classe 7 (produits) should be credit."""
        class_7 = get_pcg2025_class("7")
        credit_accounts = [a for a in class_7 if a.normal_balance == "C"]
        # Almost all revenue accounts are credit
        assert len(credit_accounts) > len(class_7) * 0.9


class TestSummaryAccounts:
    """Tests for summary (synthetic) accounts."""

    def test_summary_accounts_exist(self):
        """Summary accounts should exist."""
        summary = get_pcg2025_summary_accounts()
        assert len(summary) > 0

    def test_summary_accounts_are_short(self):
        """Summary accounts should have short numbers (2-3 digits)."""
        summary = get_pcg2025_summary_accounts()
        for account in summary:
            assert len(account.number) <= 4, f"Summary {account.number} too long"


class TestPCGClasses:
    """Tests for PCG class definitions."""

    def test_8_classes_defined(self):
        """There should be 8 PCG classes."""
        assert len(PCG_CLASSES) == 8

    def test_class_numbers(self):
        """Classes should be numbered 1-8."""
        class_numbers = [c.class_number for c in PCG_CLASSES]
        assert class_numbers == ["1", "2", "3", "4", "5", "6", "7", "8"]


class TestAccountCreateSchema:
    """Tests for PCGAccountCreate schema validation."""

    def test_valid_account_create(self):
        """Test valid account creation."""
        data = PCGAccountCreate(
            account_number="411001",
            account_label="Client ABC",
            normal_balance="D",
        )
        assert data.account_number == "411001"
        assert data.account_label == "Client ABC"

    def test_invalid_class_0(self):
        """Class 0 should be rejected."""
        with pytest.raises(ValueError):
            PCGAccountCreate(
                account_number="01234",
                account_label="Invalid",
            )

    def test_invalid_class_9(self):
        """Class 9 should be rejected."""
        with pytest.raises(ValueError):
            PCGAccountCreate(
                account_number="91234",
                account_label="Invalid",
            )

    def test_non_numeric_rejected(self):
        """Non-numeric accounts should be rejected."""
        with pytest.raises(ValueError):
            PCGAccountCreate(
                account_number="ABC12",
                account_label="Invalid",
            )


class TestTVAAccounts:
    """Tests for VAT-related accounts."""

    def test_tva_accounts_exist(self):
        """VAT accounts should be in classe 4."""
        tva_deductible = get_pcg2025_account("44566")
        assert tva_deductible is not None
        assert "TVA" in tva_deductible.label
        assert tva_deductible.normal_balance == "D"  # TVA déductible is debit

        tva_collectee = get_pcg2025_account("44571")
        assert tva_collectee is not None
        assert "TVA" in tva_collectee.label
        assert tva_collectee.normal_balance == "C"  # TVA collectée is credit

        tva_decaisser = get_pcg2025_account("44551")
        assert tva_decaisser is not None
        assert "TVA" in tva_decaisser.label


class TestEssentialAccounts:
    """Tests for essential business accounts."""

    def test_client_accounts(self):
        """Client accounts should exist."""
        clients = get_pcg2025_account("411")
        assert clients is not None
        assert clients.normal_balance == "D"

    def test_supplier_accounts(self):
        """Supplier accounts should exist."""
        fournisseurs = get_pcg2025_account("401")
        assert fournisseurs is not None
        assert fournisseurs.normal_balance == "C"

    def test_bank_accounts(self):
        """Bank accounts should exist."""
        banques = get_pcg2025_account("512")
        assert banques is not None
        assert banques.normal_balance == "D"

    def test_capital_account(self):
        """Capital account should exist."""
        capital = get_pcg2025_account("101")
        assert capital is not None
        assert capital.normal_balance == "C"

    def test_sales_account(self):
        """Sales account should exist."""
        ventes = get_pcg2025_account("707")
        assert ventes is not None
        assert ventes.normal_balance == "C"

    def test_purchases_account(self):
        """Purchases account should exist."""
        achats = get_pcg2025_account("607")
        assert achats is not None
        assert achats.normal_balance == "D"
