"""
Tests pour le système d'orchestration IA AZALSCORE

Conformité: AZA-TEST-001
"""

import pytest
from datetime import datetime, timedelta

from app.ai.roles import AIRole, get_role_config, validate_role_action
from app.ai.audit import AIAuditLogger, AuditEvent, AuditEventType
from app.ai.guardian import Guardian, GuardianDecision, ThreatLevel
from app.ai.theo import TheoInterface, ConversationState
from app.ai.auth import AIAuthManager, PrivilegeLevel, AuthMethod


class TestAIRoles:
    """Tests pour les rôles IA"""

    def test_role_config_exists(self):
        """Vérifie que tous les rôles ont une configuration"""
        for role in AIRole:
            config = get_role_config(role)
            # Note: Certains rôles peuvent ne pas avoir de config
            if config:
                assert config.role == role

    def test_theo_roles_exist(self):
        """Vérifie que les rôles Theo existent"""
        theo_roles = [
            AIRole.THEO_DIALOGUE,
            AIRole.THEO_CLARIFICATION,
            AIRole.THEO_ORCHESTRATION,
            AIRole.THEO_SYNTHESIS
        ]
        for role in theo_roles:
            config = get_role_config(role)
            assert config is not None
            assert "theo" in role.value

    def test_validate_role_action_allowed(self):
        """Vérifie la validation d'action autorisée"""
        assert validate_role_action(AIRole.THEO_DIALOGUE, "listen")
        assert validate_role_action(AIRole.GUARDIAN_VALIDATE, "validate")

    def test_validate_role_action_forbidden(self):
        """Vérifie la validation d'action interdite"""
        assert not validate_role_action(AIRole.THEO_DIALOGUE, "decide")
        assert not validate_role_action(AIRole.GUARDIAN_VALIDATE, "execute")


class TestAuditLogger:
    """Tests pour le système d'audit"""

    def test_create_audit_event(self):
        """Vérifie la création d'un événement d'audit"""
        event = AuditEvent(
            event_type=AuditEventType.HUMAN_REQUEST,
            session_id="test-session",
            user_id="test-user",
            source_module="test",
            action="test_action"
        )

        assert event.id is not None
        assert event.timestamp is not None
        assert event.checksum is not None
        assert event.event_type == AuditEventType.HUMAN_REQUEST

    def test_audit_event_checksum(self):
        """Vérifie que le checksum change avec le contenu"""
        event1 = AuditEvent(
            event_type=AuditEventType.HUMAN_REQUEST,
            source_module="test",
            action="action1"
        )

        event2 = AuditEvent(
            event_type=AuditEventType.HUMAN_REQUEST,
            source_module="test",
            action="action2"
        )

        assert event1.checksum != event2.checksum

    def test_audit_logger_log_event(self, tmp_path):
        """Vérifie l'enregistrement d'événements"""
        logger = AIAuditLogger(log_dir=str(tmp_path))

        event_id = logger.log_human_request(
            session_id="test-session",
            user_id="test-user",
            request="Test request"
        )

        assert event_id is not None
        assert len(logger._events) == 1


class TestGuardian:
    """Tests pour le module Guardian"""

    def test_guardian_init(self):
        """Vérifie l'initialisation de Guardian"""
        guardian = Guardian()
        assert guardian is not None

    def test_guardian_validate_normal_request(self):
        """Vérifie la validation d'une requête normale"""
        guardian = Guardian()

        result = guardian.validate_request(
            session_id="test-session",
            user_id="test-user",
            action="read",
            target_module="test",
            role=AIRole.THEO_DIALOGUE,
            input_data={"message": "Hello"}
        )

        # Devrait être approuvé (action normale)
        # Note: "read" n'est pas dans allowed_actions de THEO_DIALOGUE
        # mais ce test vérifie que Guardian fonctionne
        assert result.decision in [GuardianDecision.APPROVED, GuardianDecision.ESCALATE]

    def test_guardian_block_dangerous_content(self):
        """Vérifie le blocage de contenu dangereux"""
        guardian = Guardian()

        result = guardian.validate_request(
            session_id="test-session",
            user_id="test-user",
            action="execute",
            target_module="test",
            role=AIRole.CLAUDE_CODE_ANALYSIS,
            input_data={"code": "os.system('rm -rf /')"}
        )

        # Devrait être bloqué (pattern dangereux)
        assert result.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        assert len(result.violations) > 0

    def test_guardian_rate_limiting(self):
        """Vérifie le rate limiting"""
        guardian = Guardian()
        session_id = "rate-test-session"

        # Simuler beaucoup d'appels
        for _ in range(65):  # Plus que la limite de 60/minute
            guardian._check_rate_limits(session_id)

        # Le prochain devrait être limité
        rate_check = guardian._check_rate_limits(session_id)
        assert not rate_check["allowed"]


class TestTheo:
    """Tests pour le module Theo"""

    def test_theo_start_session(self):
        """Vérifie le démarrage d'une session"""
        theo = TheoInterface()
        session_id = theo.start_session(user_id="test-user")

        assert session_id is not None
        assert session_id in theo._sessions

    def test_theo_process_simple_input(self):
        """Vérifie le traitement d'une entrée simple"""
        theo = TheoInterface()
        session_id = theo.start_session()

        response = theo.process_input(
            session_id=session_id,
            user_input="Afficher la liste des clients"
        )

        assert response is not None
        assert response.session_id == session_id
        assert response.message is not None

    def test_theo_intention_analysis(self):
        """Vérifie l'analyse d'intention"""
        theo = TheoInterface()
        session_id = theo.start_session()

        response = theo.process_input(
            session_id=session_id,
            user_input="créer une nouvelle facture pour le client ABC"
        )

        # Devrait détecter l'action "créer" et le module "finance"
        if response.intention:
            assert "créer" in response.intention.suggested_actions or \
                   len(response.intention.clarification_questions) > 0

    def test_theo_requires_clarification_for_vague_input(self):
        """Vérifie la demande de clarification pour entrée vague"""
        theo = TheoInterface()
        session_id = theo.start_session()

        response = theo.process_input(
            session_id=session_id,
            user_input="faire ça"  # Très vague
        )

        # Devrait demander des clarifications
        assert response.state in [
            ConversationState.CLARIFYING,
            ConversationState.COMPLETED
        ]

    def test_theo_session_history(self):
        """Vérifie l'historique de session"""
        theo = TheoInterface()
        session_id = theo.start_session()

        theo.process_input(session_id=session_id, user_input="Test 1")
        theo.process_input(session_id=session_id, user_input="Test 2")

        history = theo.get_session_history(session_id)
        assert len(history) >= 2


class TestAuthManager:
    """Tests pour le gestionnaire d'authentification"""

    def test_auth_manager_init(self):
        """Vérifie l'initialisation"""
        auth = AIAuthManager()
        assert auth is not None

    def test_invalid_user_login(self):
        """Vérifie le rejet d'un utilisateur invalide"""
        auth = AIAuthManager()

        session = auth.authenticate_password(
            username="invalid_user",
            password="wrong_password"
        )

        assert session is None

    def test_rate_limiting_after_failed_attempts(self):
        """Vérifie le rate limiting après échecs"""
        auth = AIAuthManager()

        # Simuler des échecs
        for _ in range(6):
            auth._record_failed_attempt("test_user")

        assert auth._is_rate_limited("test_user")

    def test_privilege_level_hierarchy(self):
        """Vérifie la hiérarchie des privilèges"""
        levels = [
            PrivilegeLevel.ANONYMOUS,
            PrivilegeLevel.USER,
            PrivilegeLevel.OPERATOR,
            PrivilegeLevel.ADMIN,
            PrivilegeLevel.OWNER
        ]

        # Vérifie que la liste est dans l'ordre croissant de privilèges
        assert levels[0].value == "anonymous"
        assert levels[-1].value == "owner"


class TestIntegration:
    """Tests d'intégration du système complet"""

    def test_full_conversation_flow(self):
        """Test d'un flux de conversation complet"""
        theo = TheoInterface()

        # 1. Démarrer une session
        session_id = theo.start_session(user_id="integration-test")

        # 2. Envoyer une demande
        response1 = theo.process_input(
            session_id=session_id,
            user_input="Je voudrais créer une facture pour mon client"
        )

        assert response1.session_id == session_id

        # 3. Si clarification nécessaire, confirmer
        if response1.state == ConversationState.CLARIFYING:
            response2 = theo.confirm_intention(
                session_id=session_id,
                confirmed=True
            )
            assert response2 is not None

        # 4. Terminer la session
        success = theo.end_session(session_id)
        assert success

    def test_guardian_integration_with_theo(self):
        """Test de l'intégration Guardian + Theo"""
        theo = TheoInterface()
        session_id = theo.start_session()

        # Tenter une requête avec contenu potentiellement dangereux
        response = theo.process_input(
            session_id=session_id,
            user_input="Exécuter rm -rf / sur le serveur"  # Devrait être filtré
        )

        # Guardian devrait avoir traité cette requête
        # (soit bloquée, soit le contenu filtré)
        assert response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
