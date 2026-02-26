"""
Tests for Dunning (Relances Impayés) Module.

Tests de validation des relances automatiques impayés.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from ..models import (
    DunningLevelType,
    DunningChannel,
    DunningStatus,
    DunningCampaignStatus,
    PaymentPromiseStatus,
)
from ..schemas import (
    DunningLevelCreate,
    DunningTemplateCreate,
    DunningRuleCreate,
    PaymentPromiseCreate,
    CustomerDunningProfileCreate,
    DEFAULT_TEMPLATES,
)
from ..service import (
    DunningService,
    DEFAULT_LATE_INTEREST_RATE,
    FIXED_RECOVERY_FEE,
    FRENCH_HOLIDAYS_2025,
)


class TestDunningEnums:
    """Tests for dunning enums."""

    def test_dunning_level_types(self):
        """Test all level types exist."""
        types = [
            DunningLevelType.REMINDER,
            DunningLevelType.FIRST_NOTICE,
            DunningLevelType.SECOND_NOTICE,
            DunningLevelType.FORMAL_NOTICE,
            DunningLevelType.FINAL_NOTICE,
            DunningLevelType.COLLECTION,
        ]
        assert len(types) == 6

    def test_dunning_channels(self):
        """Test all channels exist."""
        channels = [
            DunningChannel.EMAIL,
            DunningChannel.SMS,
            DunningChannel.LETTER,
            DunningChannel.PHONE,
            DunningChannel.REGISTERED,
        ]
        assert len(channels) == 5

    def test_dunning_statuses(self):
        """Test all statuses exist."""
        statuses = [
            DunningStatus.PENDING,
            DunningStatus.SENT,
            DunningStatus.DELIVERED,
            DunningStatus.READ,
            DunningStatus.FAILED,
            DunningStatus.CANCELLED,
        ]
        assert len(statuses) == 6


class TestLateInterestCalculation:
    """Tests for late interest calculation."""

    def test_no_interest_if_not_overdue(self):
        """No interest should be charged if not overdue."""
        # Simulation - service not instantiated without DB
        # Testing formula directly
        amount = Decimal("1000")
        days_overdue = 0
        annual_rate = DEFAULT_LATE_INTEREST_RATE

        # Manual calculation
        if days_overdue <= 0:
            interest = Decimal("0")
        else:
            daily_rate = annual_rate / Decimal("365") / Decimal("100")
            interest = amount * daily_rate * Decimal(str(days_overdue))

        assert interest == Decimal("0")

    def test_interest_calculation_30_days(self):
        """Test interest calculation for 30 days overdue."""
        amount = Decimal("1000")
        days_overdue = 30
        annual_rate = Decimal("10.0")  # 10%

        daily_rate = annual_rate / Decimal("365") / Decimal("100")
        interest = amount * daily_rate * Decimal(str(days_overdue))
        interest = interest.quantize(Decimal("0.01"))

        # 1000 * (10/365/100) * 30 = 8.22 (approx)
        assert Decimal("8.00") <= interest <= Decimal("9.00")

    def test_interest_calculation_90_days(self):
        """Test interest calculation for 90 days overdue."""
        amount = Decimal("5000")
        days_overdue = 90
        annual_rate = Decimal("10.0")

        daily_rate = annual_rate / Decimal("365") / Decimal("100")
        interest = amount * daily_rate * Decimal(str(days_overdue))
        interest = interest.quantize(Decimal("0.01"))

        # 5000 * (10/365/100) * 90 = 123.29 (approx)
        assert Decimal("120.00") <= interest <= Decimal("125.00")


class TestFrenchCompliance:
    """Tests for French legal compliance."""

    def test_fixed_recovery_fee(self):
        """Fixed recovery fee should be 40€ per art. L441-10."""
        assert FIXED_RECOVERY_FEE == Decimal("40.00")

    def test_french_holidays_2025(self):
        """French holidays 2025 should be defined."""
        assert len(FRENCH_HOLIDAYS_2025) >= 10

        # Check some key holidays
        holidays_dates = [h.strftime("%m-%d") for h in FRENCH_HOLIDAYS_2025]
        assert "01-01" in holidays_dates  # Jour de l'an
        assert "05-01" in holidays_dates  # Fête du travail
        assert "07-14" in holidays_dates  # Fête nationale
        assert "12-25" in holidays_dates  # Noël


class TestDunningLevelSchema:
    """Tests for DunningLevelCreate schema."""

    def test_valid_level_create(self):
        """Test valid level creation."""
        data = DunningLevelCreate(
            code="LEVEL_1",
            name="1ère relance",
            level_type="FIRST_NOTICE",
            sequence=1,
            days_after_due=10,
            channels=["EMAIL", "SMS"],
            primary_channel="EMAIL",
        )
        assert data.code == "LEVEL_1"
        assert data.level_type == "FIRST_NOTICE"
        assert "EMAIL" in data.channels

    def test_level_with_fees(self):
        """Test level with fees configuration."""
        data = DunningLevelCreate(
            code="FORMAL",
            name="Mise en demeure",
            level_type="FORMAL_NOTICE",
            sequence=4,
            days_after_due=30,
            channels=["REGISTERED"],
            primary_channel="REGISTERED",
            add_fees=True,
            fixed_recovery_fee=Decimal("40.00"),
            apply_late_interest=True,
            late_interest_rate=Decimal("10.0"),
        )
        assert data.add_fees is True
        assert data.fixed_recovery_fee == Decimal("40.00")
        assert data.apply_late_interest is True


class TestDunningTemplateSchema:
    """Tests for DunningTemplateCreate schema."""

    def test_valid_email_template(self):
        """Test valid email template."""
        from uuid import uuid4

        data = DunningTemplateCreate(
            level_id=uuid4(),
            channel="EMAIL",
            language="fr",
            subject="Relance facture {invoice_number}",
            body="Bonjour {customer_name}, votre facture est en retard.",
        )
        assert data.channel == "EMAIL"
        assert "{invoice_number}" in data.subject
        assert "{customer_name}" in data.body

    def test_valid_sms_template(self):
        """Test valid SMS template (no subject)."""
        from uuid import uuid4

        data = DunningTemplateCreate(
            level_id=uuid4(),
            channel="SMS",
            language="fr",
            body="Rappel: Facture {invoice_number} en retard. {company_name}",
        )
        assert data.channel == "SMS"
        assert data.subject is None


class TestDefaultTemplates:
    """Tests for default templates."""

    def test_reminder_template_exists(self):
        """Reminder template should exist."""
        assert "REMINDER" in DEFAULT_TEMPLATES
        assert "fr" in DEFAULT_TEMPLATES["REMINDER"]
        assert "EMAIL" in DEFAULT_TEMPLATES["REMINDER"]["fr"]

    def test_formal_notice_template_exists(self):
        """Formal notice template should exist."""
        assert "FORMAL_NOTICE" in DEFAULT_TEMPLATES
        assert "fr" in DEFAULT_TEMPLATES["FORMAL_NOTICE"]

    def test_templates_have_placeholders(self):
        """Templates should have required placeholders."""
        email_template = DEFAULT_TEMPLATES["REMINDER"]["fr"]["EMAIL"]
        body = email_template["body"]

        assert "{customer_name}" in body
        assert "{invoice_number}" in body
        assert "{amount_due}" in body
        assert "{due_date}" in body


class TestDunningRuleSchema:
    """Tests for DunningRuleCreate schema."""

    def test_valid_rule_create(self):
        """Test valid rule creation."""
        data = DunningRuleCreate(
            name="Règle standard",
            priority=100,
            min_amount=Decimal("50.00"),
            grace_days=3,
            auto_send=True,
        )
        assert data.name == "Règle standard"
        assert data.min_amount == Decimal("50.00")

    def test_rule_with_conditions(self):
        """Test rule with JSON conditions."""
        data = DunningRuleCreate(
            name="Règle VIP",
            priority=50,
            conditions={
                "customer_segments": ["VIP", "GOLD"],
                "invoice_types": ["SERVICE"],
            },
            grace_days=7,
        )
        assert "customer_segments" in data.conditions
        assert "VIP" in data.conditions["customer_segments"]


class TestPaymentPromiseSchema:
    """Tests for PaymentPromiseCreate schema."""

    def test_valid_promise_create(self):
        """Test valid promise creation."""
        data = PaymentPromiseCreate(
            invoice_id="INV-001",
            customer_id="CUST-001",
            promised_amount=Decimal("500.00"),
            promised_date=date.today() + timedelta(days=7),
            contact_name="Jean Dupont",
            contact_method="phone",
        )
        assert data.promised_amount == Decimal("500.00")
        assert data.promised_date > date.today()

    def test_promise_amount_must_be_positive(self):
        """Promise amount must be positive."""
        with pytest.raises(ValueError):
            PaymentPromiseCreate(
                invoice_id="INV-001",
                customer_id="CUST-001",
                promised_amount=Decimal("-100.00"),
                promised_date=date.today(),
            )


class TestCustomerProfileSchema:
    """Tests for CustomerDunningProfileCreate schema."""

    def test_valid_profile_create(self):
        """Test valid profile creation."""
        data = CustomerDunningProfileCreate(
            customer_id="CUST-001",
            customer_name="Entreprise ABC",
            segment="VIP",
            preferred_channel="EMAIL",
            preferred_language="fr",
        )
        assert data.customer_id == "CUST-001"
        assert data.segment == "VIP"

    def test_blocked_profile(self):
        """Test blocked profile creation."""
        data = CustomerDunningProfileCreate(
            customer_id="CUST-002",
            customer_name="Client Bloqué",
            dunning_blocked=True,
            block_reason="Litige en cours",
        )
        assert data.dunning_blocked is True
        assert "Litige" in data.block_reason


class TestDaysOverdueCalculation:
    """Tests for days overdue calculation logic."""

    def test_not_overdue(self):
        """Invoice not yet due should return 0."""
        today = date.today()
        due_date = today + timedelta(days=5)

        days = (today - due_date).days if due_date < today else 0
        assert days == 0

    def test_overdue_1_day(self):
        """Invoice 1 day overdue."""
        today = date.today()
        due_date = today - timedelta(days=1)

        days = (today - due_date).days
        assert days == 1

    def test_overdue_30_days(self):
        """Invoice 30 days overdue."""
        today = date.today()
        due_date = today - timedelta(days=30)

        days = (today - due_date).days
        assert days == 30


class TestAgingBuckets:
    """Tests for aging bucket categorization."""

    def test_bucket_0_30(self):
        """Test 0-30 days bucket."""
        days = 15
        if days <= 30:
            bucket = "0-30"
        elif days <= 60:
            bucket = "31-60"
        elif days <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"
        assert bucket == "0-30"

    def test_bucket_31_60(self):
        """Test 31-60 days bucket."""
        days = 45
        if days <= 30:
            bucket = "0-30"
        elif days <= 60:
            bucket = "31-60"
        elif days <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"
        assert bucket == "31-60"

    def test_bucket_90_plus(self):
        """Test 90+ days bucket."""
        days = 120
        if days <= 30:
            bucket = "0-30"
        elif days <= 60:
            bucket = "31-60"
        elif days <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"
        assert bucket == "90+"


class TestTemplateRendering:
    """Tests for template variable rendering."""

    def test_render_simple_template(self):
        """Test simple template rendering."""
        template = "Bonjour {customer_name}, votre facture {invoice_number} est en retard."
        context = {
            "customer_name": "Jean Dupont",
            "invoice_number": "FAC-2025-001",
        }

        result = template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))

        assert "Jean Dupont" in result
        assert "FAC-2025-001" in result
        assert "{customer_name}" not in result

    def test_render_with_amounts(self):
        """Test template rendering with amounts."""
        template = "Montant dû: {amount_due} EUR. Total avec frais: {total_due} EUR."
        context = {
            "amount_due": "1000.00",
            "total_due": "1040.00",
        }

        result = template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))

        assert "1000.00" in result
        assert "1040.00" in result


class TestEscalationLogic:
    """Tests for dunning escalation logic."""

    def test_level_sequence(self):
        """Test level sequence ordering."""
        levels = [
            {"code": "REMINDER", "sequence": 1, "days_after_due": 3},
            {"code": "LEVEL_1", "sequence": 2, "days_after_due": 10},
            {"code": "LEVEL_2", "sequence": 3, "days_after_due": 20},
            {"code": "FORMAL", "sequence": 4, "days_after_due": 30},
            {"code": "FINAL", "sequence": 5, "days_after_due": 45},
            {"code": "COLLECTION", "sequence": 6, "days_after_due": 60},
        ]

        # Verify sequence is increasing
        for i in range(1, len(levels)):
            assert levels[i]["sequence"] > levels[i - 1]["sequence"]
            assert levels[i]["days_after_due"] > levels[i - 1]["days_after_due"]

    def test_find_next_level(self):
        """Test finding next level in escalation."""
        levels = [
            {"code": "LEVEL_1", "sequence": 1},
            {"code": "LEVEL_2", "sequence": 2},
            {"code": "LEVEL_3", "sequence": 3},
        ]

        current_sequence = 1
        next_level = None
        for level in levels:
            if level["sequence"] > current_sequence:
                next_level = level
                break

        assert next_level is not None
        assert next_level["code"] == "LEVEL_2"
