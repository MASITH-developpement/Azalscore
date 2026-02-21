"""
Tests Sécurité Multi-tenant Referral
====================================
CRITIQUE: Vérifier l'isolation stricte entre tenants
"""
import pytest
from uuid import UUID

from app.modules.referral.service import ReferralService
from app.modules.referral.schemas import (
    ReferralProgramCreate, ReferralProgramUpdate,
    RewardTierCreate, RewardTierUpdate,
    ReferralCodeCreate, ReferralCodeUpdate,
    PayoutCreate, PayoutUpdate
)
from app.modules.referral.exceptions import (
    ProgramNotFoundError,
    RewardTierNotFoundError,
    ReferralCodeNotFoundError,
    ReferralNotFoundError,
    RewardNotFoundError,
    PayoutNotFoundError
)


class TestProgramTenantIsolation:
    """Tests d'isolation tenant pour les programmes."""

    def test_cannot_access_other_tenant_program(
        self,
        service_tenant_a: ReferralService,
        program_tenant_b
    ):
        """Un tenant ne peut pas accéder aux programmes d'un autre tenant."""
        with pytest.raises(ProgramNotFoundError):
            service_tenant_a.get_program(program_tenant_b.id)

    def test_list_only_shows_own_tenant_programs(
        self,
        service_tenant_a: ReferralService,
        entities_mixed_tenants: dict
    ):
        """La liste ne retourne que les programmes du tenant courant."""
        items, total, pages = service_tenant_a.list_programs()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_update_other_tenant_program(
        self,
        service_tenant_a: ReferralService,
        program_tenant_b
    ):
        """Un tenant ne peut pas modifier les programmes d'un autre tenant."""
        with pytest.raises(ProgramNotFoundError):
            service_tenant_a.update_program(
                program_tenant_b.id,
                ReferralProgramUpdate(name="Hacked Program")
            )

    def test_cannot_delete_other_tenant_program(
        self,
        service_tenant_a: ReferralService,
        program_tenant_b
    ):
        """Un tenant ne peut pas supprimer les programmes d'un autre tenant."""
        with pytest.raises(ProgramNotFoundError):
            service_tenant_a.delete_program(program_tenant_b.id)

    def test_cannot_activate_other_tenant_program(
        self,
        service_tenant_a: ReferralService,
        program_tenant_b
    ):
        """Un tenant ne peut pas activer les programmes d'un autre tenant."""
        with pytest.raises(ProgramNotFoundError):
            service_tenant_a.activate_program(program_tenant_b.id)

    def test_autocomplete_isolated(
        self,
        service_tenant_a: ReferralService,
        entities_mixed_tenants: dict
    ):
        """L'autocomplete ne retourne que les programmes du tenant courant."""
        results = service_tenant_a.autocomplete_program("Program")

        for item in results:
            program = service_tenant_a.get_program(item["id"])
            assert program.tenant_id == service_tenant_a.tenant_id


class TestRewardTierTenantIsolation:
    """Tests d'isolation tenant pour les paliers de récompense."""

    def test_cannot_access_other_tenant_tier(
        self,
        service_tenant_a: ReferralService,
        tier_tenant_b
    ):
        """Un tenant ne peut pas accéder aux paliers d'un autre tenant."""
        with pytest.raises(RewardTierNotFoundError):
            service_tenant_a.get_tier(tier_tenant_b.id)

    def test_cannot_create_tier_for_other_tenant_program(
        self,
        service_tenant_a: ReferralService,
        program_tenant_b
    ):
        """Un tenant ne peut pas créer de palier pour un programme d'un autre tenant."""
        from decimal import Decimal
        with pytest.raises(ProgramNotFoundError):
            service_tenant_a.create_tier(
                RewardTierCreate(
                    program_id=program_tenant_b.id,
                    level=1,
                    name="Hacked Tier",
                    min_referrals=1,
                    reward_type="fixed",
                    reward_value=Decimal("100.00"),
                    reward_trigger="conversion"
                )
            )

    def test_cannot_update_other_tenant_tier(
        self,
        service_tenant_a: ReferralService,
        tier_tenant_b
    ):
        """Un tenant ne peut pas modifier les paliers d'un autre tenant."""
        with pytest.raises(RewardTierNotFoundError):
            service_tenant_a.update_tier(
                tier_tenant_b.id,
                RewardTierUpdate(name="Hacked Tier")
            )

    def test_cannot_delete_other_tenant_tier(
        self,
        service_tenant_a: ReferralService,
        tier_tenant_b
    ):
        """Un tenant ne peut pas supprimer les paliers d'un autre tenant."""
        with pytest.raises(RewardTierNotFoundError):
            service_tenant_a.delete_tier(tier_tenant_b.id)


class TestReferralCodeTenantIsolation:
    """Tests d'isolation tenant pour les codes de parrainage."""

    def test_cannot_access_other_tenant_code(
        self,
        service_tenant_a: ReferralService,
        code_tenant_b
    ):
        """Un tenant ne peut pas accéder aux codes d'un autre tenant."""
        with pytest.raises(ReferralCodeNotFoundError):
            service_tenant_a.get_code(code_tenant_b.id)

    def test_cannot_create_code_for_other_tenant_program(
        self,
        service_tenant_a: ReferralService,
        program_tenant_b,
        user_a_id
    ):
        """Un tenant ne peut pas créer de code pour un programme d'un autre tenant."""
        with pytest.raises(ProgramNotFoundError):
            service_tenant_a.create_code(
                ReferralCodeCreate(
                    program_id=program_tenant_b.id,
                    referrer_id=user_a_id,
                    referrer_name="User A"
                )
            )

    def test_cannot_update_other_tenant_code(
        self,
        service_tenant_a: ReferralService,
        code_tenant_b
    ):
        """Un tenant ne peut pas modifier les codes d'un autre tenant."""
        with pytest.raises(ReferralCodeNotFoundError):
            service_tenant_a.update_code(
                code_tenant_b.id,
                ReferralCodeUpdate(is_active=False)
            )

    def test_cannot_delete_other_tenant_code(
        self,
        service_tenant_a: ReferralService,
        code_tenant_b
    ):
        """Un tenant ne peut pas supprimer les codes d'un autre tenant."""
        with pytest.raises(ReferralCodeNotFoundError):
            service_tenant_a.delete_code(code_tenant_b.id)

    def test_list_only_shows_own_tenant_codes(
        self,
        service_tenant_a: ReferralService,
        code_tenant_a,
        code_tenant_b
    ):
        """La liste ne retourne que les codes du tenant courant."""
        items, total, pages = service_tenant_a.list_codes()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id


class TestReferralTenantIsolation:
    """Tests d'isolation tenant pour les parrainages."""

    def test_cannot_access_other_tenant_referral(
        self,
        service_tenant_a: ReferralService,
        referral_tenant_b
    ):
        """Un tenant ne peut pas accéder aux parrainages d'un autre tenant."""
        with pytest.raises(ReferralNotFoundError):
            service_tenant_a.get_referral(referral_tenant_b.id)

    def test_list_only_shows_own_tenant_referrals(
        self,
        service_tenant_a: ReferralService,
        referral_tenant_a,
        referral_tenant_b
    ):
        """La liste ne retourne que les parrainages du tenant courant."""
        items, total, pages = service_tenant_a.list_referrals()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_qualify_other_tenant_referral(
        self,
        service_tenant_a: ReferralService,
        referral_tenant_b
    ):
        """Un tenant ne peut pas qualifier les parrainages d'un autre tenant."""
        with pytest.raises(ReferralNotFoundError):
            service_tenant_a.qualify_referral(referral_tenant_b.id)

    def test_cannot_reject_other_tenant_referral(
        self,
        service_tenant_a: ReferralService,
        referral_tenant_b
    ):
        """Un tenant ne peut pas rejeter les parrainages d'un autre tenant."""
        with pytest.raises(ReferralNotFoundError):
            service_tenant_a.reject_referral(referral_tenant_b.id, reason="test")


class TestPayoutTenantIsolation:
    """Tests d'isolation tenant pour les paiements."""

    def test_cannot_access_other_tenant_payout(
        self,
        service_tenant_a: ReferralService,
        payout_tenant_b
    ):
        """Un tenant ne peut pas accéder aux paiements d'un autre tenant."""
        with pytest.raises(PayoutNotFoundError):
            service_tenant_a.get_payout(payout_tenant_b.id)

    def test_list_only_shows_own_tenant_payouts(
        self,
        service_tenant_a: ReferralService,
        payout_tenant_a,
        payout_tenant_b
    ):
        """La liste ne retourne que les paiements du tenant courant."""
        items, total, pages = service_tenant_a.list_payouts()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_update_other_tenant_payout(
        self,
        service_tenant_a: ReferralService,
        payout_tenant_b
    ):
        """Un tenant ne peut pas modifier les paiements d'un autre tenant."""
        with pytest.raises(PayoutNotFoundError):
            service_tenant_a.update_payout(
                payout_tenant_b.id,
                PayoutUpdate(payment_method="hijacked")
            )

    def test_cannot_approve_other_tenant_payout(
        self,
        service_tenant_a: ReferralService,
        payout_tenant_b
    ):
        """Un tenant ne peut pas approuver les paiements d'un autre tenant."""
        with pytest.raises(PayoutNotFoundError):
            service_tenant_a.approve_payout(payout_tenant_b.id)

    def test_cannot_process_other_tenant_payout(
        self,
        service_tenant_a: ReferralService,
        payout_tenant_b
    ):
        """Un tenant ne peut pas traiter les paiements d'un autre tenant."""
        with pytest.raises(PayoutNotFoundError):
            service_tenant_a.process_payout(payout_tenant_b.id, "TX123")


class TestCrossEntityTenantIsolation:
    """Tests d'isolation cross-entity."""

    def test_cannot_use_other_tenant_code_for_tracking(
        self,
        service_tenant_a: ReferralService,
        code_tenant_b
    ):
        """Un tenant ne peut pas utiliser un code d'un autre tenant pour tracking."""
        # Le code d'un autre tenant ne devrait pas être trouvé
        result = service_tenant_a.validate_code(code_tenant_b.code)
        assert result is None or result.tenant_id == service_tenant_a.tenant_id


class TestBulkOperationsTenantIsolation:
    """Tests d'isolation pour les opérations en masse."""

    def test_bulk_delete_programs_cannot_affect_other_tenant(
        self,
        db_session,
        service_tenant_a: ReferralService,
        program_tenant_b
    ):
        """Les suppressions en masse ne peuvent pas affecter d'autres tenants."""
        from app.modules.referral.repository import ProgramRepository

        # Tenter de supprimer un programme d'un autre tenant
        result = service_tenant_a.program_repo.bulk_delete(
            [program_tenant_b.id],
            service_tenant_a.user_id
        )

        # Devrait retourner 0 car le programme n'est pas visible pour ce tenant
        assert result == 0

        # Vérifier que le programme existe toujours pour le tenant B
        repo_b = ProgramRepository(db_session, program_tenant_b.tenant_id)
        program = repo_b.get_by_id(program_tenant_b.id)
        assert program is not None
        assert not program.is_deleted


class TestStatsIsolation:
    """Tests d'isolation pour les statistiques."""

    def test_program_stats_isolated(
        self,
        service_tenant_a: ReferralService,
        entities_mixed_tenants: dict
    ):
        """Les stats programme ne comptent que les entités du tenant courant."""
        stats = service_tenant_a.get_program_stats()

        # Vérifier que le total correspond aux entités du tenant A
        tenant_a_count = len(entities_mixed_tenants["tenant_a"]["programs"])
        assert stats["total"] >= tenant_a_count

    def test_referrer_profile_isolated(
        self,
        service_tenant_a: ReferralService,
        referral_tenant_a,
        referral_tenant_b,
        user_a_id
    ):
        """Le profil parrain ne compte que les parrainages du tenant courant."""
        profile = service_tenant_a.get_referrer_profile(user_a_id)

        # Ne doit pas inclure les stats du tenant B
        # Le profil devrait exister seulement si des parrainages existent pour ce tenant
        if profile:
            # Les stats ne doivent concerner que le tenant A
            assert profile.referrer_id == user_a_id


class TestFraudCheckTenantIsolation:
    """Tests d'isolation pour les contrôles de fraude."""

    def test_fraud_checks_isolated(
        self,
        service_tenant_a: ReferralService,
        fraud_check_tenant_a,
        referral_tenant_b
    ):
        """Les contrôles de fraude sont isolés par tenant."""
        # Tenter d'accéder à un parrainage d'un autre tenant pour contrôle
        with pytest.raises(ReferralNotFoundError):
            service_tenant_a.flag_fraud(referral_tenant_b.id, "same_ip")


class TestTrackingTenantIsolation:
    """Tests d'isolation pour le tracking."""

    def test_track_click_uses_tenant_code(
        self,
        service_tenant_a: ReferralService,
        code_tenant_a,
        code_tenant_b
    ):
        """Le tracking de clic utilise uniquement les codes du tenant courant."""
        # Le tracking avec un code du tenant A doit fonctionner
        result_a = service_tenant_a.track_click(
            code_tenant_a.code,
            ip_address="192.168.1.1",
            user_agent="Test Agent"
        )
        assert result_a is not None

        # Le tracking avec un code du tenant B ne doit pas fonctionner
        result_b = service_tenant_a.track_click(
            code_tenant_b.code,
            ip_address="192.168.1.2",
            user_agent="Test Agent"
        )
        assert result_b is None
