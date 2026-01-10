"""
AZALS MODULE GUARDIAN - Modèles de données
===========================================

Modèles SQLAlchemy pour le système de correction automatique gouvernée.

IMPORTANT: Le CorrectionRegistry est append-only (INSERT uniquement).
Les UPDATE et DELETE sont interdits par contrainte logique.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.db import Base
from app.core.types import JSONB, UniversalUUID

# ============================================================================
# ENUMS
# ============================================================================

class ErrorSeverity(str, enum.Enum):
    """Niveau de gravité des erreurs."""
    CRITICAL = "CRITICAL"    # Bloquant, action immédiate requise
    MAJOR = "MAJOR"          # Impact significatif, correction prioritaire
    MINOR = "MINOR"          # Impact limité, correction planifiable
    WARNING = "WARNING"      # Alerte préventive, surveillance
    INFO = "INFO"            # Information, pas d'action requise


class ErrorSource(str, enum.Enum):
    """Source de l'erreur détectée."""
    FRONTEND_LOG = "FRONTEND_LOG"        # Log frontend (browser)
    BACKEND_LOG = "BACKEND_LOG"          # Log backend (serveur)
    SYSTEM_ALERT = "SYSTEM_ALERT"        # Alerte système (monitoring)
    DATABASE_ERROR = "DATABASE_ERROR"     # Erreur base de données
    API_ERROR = "API_ERROR"              # Erreur API (HTTP 4xx/5xx)
    SECURITY_ALERT = "SECURITY_ALERT"    # Alerte sécurité
    PERFORMANCE_ALERT = "PERFORMANCE_ALERT"  # Alerte performance
    SCHEDULED_CHECK = "SCHEDULED_CHECK"  # Vérification planifiée
    USER_REPORT = "USER_REPORT"          # Signalement utilisateur
    EXTERNAL_WEBHOOK = "EXTERNAL_WEBHOOK"  # Webhook externe


class ErrorType(str, enum.Enum):
    """Type d'erreur détectée."""
    EXCEPTION = "EXCEPTION"              # Exception non gérée
    VALIDATION = "VALIDATION"            # Erreur de validation
    AUTHENTICATION = "AUTHENTICATION"    # Erreur d'authentification
    AUTHORIZATION = "AUTHORIZATION"      # Erreur d'autorisation
    DATABASE = "DATABASE"                # Erreur base de données
    NETWORK = "NETWORK"                  # Erreur réseau
    TIMEOUT = "TIMEOUT"                  # Timeout
    RATE_LIMIT = "RATE_LIMIT"            # Rate limiting
    CONFIGURATION = "CONFIGURATION"      # Erreur de configuration
    DATA_INTEGRITY = "DATA_INTEGRITY"    # Intégrité des données
    BUSINESS_LOGIC = "BUSINESS_LOGIC"    # Logique métier
    DEPENDENCY = "DEPENDENCY"            # Dépendance externe
    MEMORY = "MEMORY"                    # Mémoire
    STORAGE = "STORAGE"                  # Stockage
    UNKNOWN = "UNKNOWN"                  # Type inconnu


class CorrectionStatus(str, enum.Enum):
    """Statut d'une correction."""
    PENDING = "PENDING"                  # En attente de traitement
    ANALYZING = "ANALYZING"              # En cours d'analyse
    PROPOSED = "PROPOSED"                # Correction proposée, en attente validation
    APPROVED = "APPROVED"                # Correction approuvée
    IN_PROGRESS = "IN_PROGRESS"          # Correction en cours d'application
    TESTING = "TESTING"                  # Tests post-correction en cours
    APPLIED = "APPLIED"                  # Correction appliquée avec succès
    FAILED = "FAILED"                    # Correction échouée
    ROLLED_BACK = "ROLLED_BACK"          # Correction annulée (rollback)
    REJECTED = "REJECTED"                # Correction refusée
    DEFERRED = "DEFERRED"                # Correction différée
    BLOCKED = "BLOCKED"                  # Correction bloquée (validation humaine requise)


class CorrectionAction(str, enum.Enum):
    """Type d'action corrective."""
    AUTO_FIX = "AUTO_FIX"                # Correction automatique
    CONFIG_UPDATE = "CONFIG_UPDATE"      # Mise à jour configuration
    CACHE_CLEAR = "CACHE_CLEAR"          # Vidage cache
    SERVICE_RESTART = "SERVICE_RESTART"  # Redémarrage service
    DATABASE_REPAIR = "DATABASE_REPAIR"  # Réparation base de données
    DATA_MIGRATION = "DATA_MIGRATION"    # Migration de données
    PERMISSION_FIX = "PERMISSION_FIX"    # Correction permissions
    DEPENDENCY_UPDATE = "DEPENDENCY_UPDATE"  # Mise à jour dépendance
    ROLLBACK = "ROLLBACK"                # Rollback
    MANUAL_INTERVENTION = "MANUAL_INTERVENTION"  # Intervention manuelle requise
    WORKAROUND = "WORKAROUND"            # Contournement temporaire
    MONITORING_ONLY = "MONITORING_ONLY"  # Surveillance uniquement
    ESCALATION = "ESCALATION"            # Escalade (alerte humain)


class TestResult(str, enum.Enum):
    """Résultat d'un test post-correction."""
    PASSED = "PASSED"                    # Test réussi
    FAILED = "FAILED"                    # Test échoué
    SKIPPED = "SKIPPED"                  # Test ignoré
    ERROR = "ERROR"                      # Erreur lors du test
    TIMEOUT = "TIMEOUT"                  # Timeout du test
    NOT_APPLICABLE = "NOT_APPLICABLE"    # Non applicable


class Environment(str, enum.Enum):
    """Environnement concerné."""
    SANDBOX = "SANDBOX"                  # Environnement de test/développement
    BETA = "BETA"                        # Environnement bêta/staging
    PRODUCTION = "PRODUCTION"            # Environnement de production


# ============================================================================
# MODÈLES PRINCIPAUX
# ============================================================================

class ErrorDetection(Base):
    """
    Erreur détectée par GUARDIAN.
    Chaque erreur détectée est enregistrée pour analyse.
    """
    __tablename__ = "guardian_error_detections"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    error_uid = Column(String(36), unique=True, nullable=False, index=True,
                       default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(255), nullable=False, index=True)

    # Classification
    severity = Column(Enum(ErrorSeverity), nullable=False, index=True)
    source = Column(Enum(ErrorSource), nullable=False, index=True)
    error_type = Column(Enum(ErrorType), nullable=False, index=True)
    environment = Column(Enum(Environment), nullable=False, index=True)

    # Localisation
    module = Column(String(100), nullable=True, index=True)
    route = Column(String(500), nullable=True)
    component = Column(String(200), nullable=True)
    function_name = Column(String(200), nullable=True)
    line_number = Column(Integer, nullable=True)
    file_path = Column(String(500), nullable=True)

    # Contexte utilisateur (pseudonymisé pour RGPD)
    user_role = Column(String(50), nullable=True)
    user_id_hash = Column(String(64), nullable=True)  # Hash SHA-256 de l'ID
    session_id_hash = Column(String(64), nullable=True)  # Hash SHA-256

    # Détails de l'erreur
    error_code = Column(String(50), nullable=True, index=True)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)  # Anonymisé si nécessaire
    request_id = Column(String(255), nullable=True, index=True)
    correlation_id = Column(String(255), nullable=True, index=True)

    # Contexte supplémentaire (pas de données personnelles)
    context_data = Column(JSONB, nullable=True)  # Métadonnées techniques uniquement
    http_status = Column(Integer, nullable=True)
    http_method = Column(String(10), nullable=True)

    # Récurrence
    occurrence_count = Column(Integer, default=1, nullable=False)
    first_occurrence_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    last_occurrence_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    # Statut de traitement
    is_processed = Column(Boolean, default=False, nullable=False, index=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(UniversalUUID(), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    # Relation avec la correction
    correction_id = Column(UniversalUUID(), ForeignKey('guardian_correction_registry.id'), nullable=True)

    # Timestamps
    detected_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_guardian_errors_tenant_detected', 'tenant_id', 'detected_at'),
        Index('idx_guardian_errors_severity_env', 'severity', 'environment'),
        Index('idx_guardian_errors_module_type', 'module', 'error_type'),
        Index('idx_guardian_errors_unprocessed', 'is_processed', 'detected_at'),
        Index('idx_guardian_errors_error_code', 'error_code'),
    )


class CorrectionRegistry(Base):
    """
    Registre des corrections - APPEND-ONLY.

    IMPORTANT: Ce registre est immuable. Seuls les INSERT sont autorisés.
    Aucun UPDATE ou DELETE ne doit être effectué sur cette table.

    Chaque entrée constitue une preuve d'audit pour une correction.
    """
    __tablename__ = "guardian_correction_registry"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    correction_uid = Column(String(36), unique=True, nullable=False, index=True,
                           default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(255), nullable=False, index=True)

    # =========================================================================
    # CHAMPS OBLIGATOIRES DU REGISTRE (selon les exigences)
    # =========================================================================

    # 1. Horodatage précis (server-side pour garantie)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False, index=True)

    # 2. Environnement concerné
    environment = Column(Enum(Environment), nullable=False, index=True)

    # 3. Source de l'erreur
    error_source = Column(Enum(ErrorSource), nullable=False)
    error_detection_id = Column(UniversalUUID(), nullable=True)  # Lien vers ErrorDetection

    # 4. Type d'erreur détectée
    error_type = Column(Enum(ErrorType), nullable=False)

    # 5. Niveau de gravité
    severity = Column(Enum(ErrorSeverity), nullable=False, index=True)

    # 6. Module concerné
    module = Column(String(100), nullable=False, index=True)

    # 7. Route, composant ou fonction impactée
    route = Column(String(500), nullable=True)
    component = Column(String(200), nullable=True)
    function_impacted = Column(String(200), nullable=True)

    # 8. Rôle utilisateur concerné (si applicable)
    affected_user_role = Column(String(50), nullable=True)

    # 9. Cause probable identifiée
    probable_cause = Column(Text, nullable=False)

    # 10. Action corrective appliquée ou proposée
    correction_action = Column(Enum(CorrectionAction), nullable=False)
    correction_description = Column(Text, nullable=False)
    correction_details = Column(JSONB, nullable=True)  # Détails techniques

    # 11. Impact estimé sur le système et les utilisateurs
    estimated_impact = Column(Text, nullable=False)
    impact_scope = Column(String(100), nullable=True)  # global, tenant, user, module
    affected_entities_count = Column(Integer, nullable=True)

    # 12. Caractère réversible ou non de l'action (avec justification)
    is_reversible = Column(Boolean, nullable=False)
    reversibility_justification = Column(Text, nullable=False)
    rollback_procedure = Column(Text, nullable=True)

    # 13. Tests exécutés après correction
    tests_executed = Column(JSONB, nullable=True)  # Liste des tests avec résultats

    # 14. Résultat de la correction
    correction_result = Column(Text, nullable=True)
    correction_successful = Column(Boolean, nullable=True)

    # 15. Statut final
    status = Column(Enum(CorrectionStatus), nullable=False, index=True)

    # =========================================================================
    # CHAMPS ADDITIONNELS POUR TRAÇABILITÉ
    # =========================================================================

    # Contexte de l'erreur originale
    original_error_message = Column(Text, nullable=True)
    original_error_code = Column(String(50), nullable=True)
    original_stack_trace = Column(Text, nullable=True)

    # Validation humaine (si requise)
    requires_human_validation = Column(Boolean, default=False, nullable=False)
    validated_by = Column(UniversalUUID(), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    validation_comment = Column(Text, nullable=True)

    # Exécution
    executed_by = Column(String(100), nullable=True)  # "GUARDIAN" ou user_id
    executed_at = Column(DateTime, nullable=True)
    execution_duration_ms = Column(Float, nullable=True)

    # Rollback (si effectué)
    rolled_back = Column(Boolean, default=False, nullable=False)
    rollback_at = Column(DateTime, nullable=True)
    rollback_reason = Column(Text, nullable=True)
    rollback_by = Column(String(100), nullable=True)

    # Audit trail
    decision_trail = Column(JSONB, nullable=True)  # Historique des décisions

    # Relations
    error_detections = relationship("ErrorDetection", backref="correction",
                                    foreign_keys=[ErrorDetection.correction_id])

    __table_args__ = (
        Index('idx_guardian_registry_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_guardian_registry_env_status', 'environment', 'status'),
        Index('idx_guardian_registry_severity_module', 'severity', 'module'),
        Index('idx_guardian_registry_requires_validation', 'requires_human_validation', 'status'),
        # Contrainte: created_at doit être défini par le serveur uniquement
        CheckConstraint('created_at IS NOT NULL', name='ck_registry_created_at_not_null'),
    )


class CorrectionRule(Base):
    """
    Règle de correction automatique.
    Définit les conditions et actions pour les corrections automatiques.
    """
    __tablename__ = "guardian_correction_rules"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    rule_uid = Column(String(36), unique=True, nullable=False, index=True,
                      default=lambda: str(uuid.uuid4()))

    # Identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), default='1.0', nullable=False)

    # Conditions de déclenchement
    trigger_error_type = Column(Enum(ErrorType), nullable=True)
    trigger_error_code = Column(String(50), nullable=True)
    trigger_module = Column(String(100), nullable=True)
    trigger_severity_min = Column(Enum(ErrorSeverity), nullable=True)
    trigger_conditions = Column(JSONB, nullable=True)  # Conditions avancées

    # Action
    correction_action = Column(Enum(CorrectionAction), nullable=False)
    action_config = Column(JSONB, nullable=True)  # Configuration de l'action
    action_script = Column(Text, nullable=True)  # Script/commande (si applicable)

    # Environnements autorisés
    allowed_environments = Column(JSONB, nullable=False)  # ["SANDBOX", "BETA", "PRODUCTION"]

    # Seuils et limites
    max_auto_corrections_per_hour = Column(Integer, default=10, nullable=False)
    cooldown_seconds = Column(Integer, default=60, nullable=False)
    requires_human_validation = Column(Boolean, default=False, nullable=False)

    # Évaluation des risques
    risk_level = Column(String(20), default='LOW', nullable=False)  # LOW, MEDIUM, HIGH
    is_reversible = Column(Boolean, default=True, nullable=False)

    # Tests requis après correction
    required_tests = Column(JSONB, nullable=True)  # Liste des tests à exécuter

    # Statistiques
    total_executions = Column(Integer, default=0, nullable=False)
    successful_executions = Column(Integer, default=0, nullable=False)
    failed_executions = Column(Integer, default=0, nullable=False)
    last_execution_at = Column(DateTime, nullable=True)

    # Statut
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system_rule = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index('idx_guardian_rules_tenant', 'tenant_id'),
        Index('idx_guardian_rules_active', 'is_active'),
        Index('idx_guardian_rules_trigger', 'trigger_error_type', 'trigger_module'),
    )


class CorrectionTest(Base):
    """
    Test post-correction.
    Enregistre les résultats des tests exécutés après une correction.
    """
    __tablename__ = "guardian_correction_tests"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Lien avec la correction
    correction_id = Column(UniversalUUID(), ForeignKey('guardian_correction_registry.id', ondelete='CASCADE'),
                          nullable=False, index=True)

    # Test identifiant
    test_name = Column(String(200), nullable=False)
    test_type = Column(String(50), nullable=False)  # SCENARIO, REGRESSION, PERSISTENCE, PERMISSION, ACCESS

    # Configuration du test
    test_config = Column(JSONB, nullable=True)
    test_input = Column(JSONB, nullable=True)

    # Exécution
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)

    # Résultat
    result = Column(Enum(TestResult), nullable=False, index=True)
    result_details = Column(JSONB, nullable=True)
    expected_output = Column(JSONB, nullable=True)
    actual_output = Column(JSONB, nullable=True)

    # Erreur (si échec)
    error_message = Column(Text, nullable=True)
    error_trace = Column(Text, nullable=True)

    # Impact sur la correction
    triggers_rollback = Column(Boolean, default=False, nullable=False)
    blocking = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index('idx_guardian_tests_correction', 'correction_id'),
        Index('idx_guardian_tests_result', 'result'),
        Index('idx_guardian_tests_tenant', 'tenant_id'),
    )


class GuardianAlert(Base):
    """
    Alerte GUARDIAN.
    Notifications pour les événements nécessitant une attention.
    """
    __tablename__ = "guardian_alerts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    alert_uid = Column(String(36), unique=True, nullable=False, index=True,
                       default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(255), nullable=False, index=True)

    # Type d'alerte
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(Enum(ErrorSeverity), nullable=False, index=True)

    # Contenu
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)

    # Liens
    error_detection_id = Column(UniversalUUID(), nullable=True)
    correction_id = Column(UniversalUUID(), nullable=True)

    # Destinataires
    target_roles = Column(JSONB, nullable=True)  # ["DIRIGEANT", "ADMIN"]
    target_users = Column(JSONB, nullable=True)  # [user_id_1, user_id_2]

    # Statut
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_by = Column(UniversalUUID(), nullable=True)
    read_at = Column(DateTime, nullable=True)

    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(UniversalUUID(), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_by = Column(UniversalUUID(), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_comment = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_guardian_alerts_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_guardian_alerts_unread', 'is_read', 'is_resolved'),
        Index('idx_guardian_alerts_severity', 'severity'),
    )


class GuardianConfig(Base):
    """
    Configuration GUARDIAN par tenant.
    """
    __tablename__ = "guardian_config"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), unique=True, nullable=False, index=True)

    # Activation
    is_enabled = Column(Boolean, default=True, nullable=False)
    auto_correction_enabled = Column(Boolean, default=True, nullable=False)

    # Environnements autorisés pour correction auto
    auto_correction_environments = Column(JSONB, default=["SANDBOX", "BETA"])

    # Seuils
    max_auto_corrections_per_day = Column(Integer, default=100, nullable=False)
    max_auto_corrections_production = Column(Integer, default=10, nullable=False)
    cooldown_between_corrections_seconds = Column(Integer, default=30, nullable=False)

    # Notifications
    alert_on_critical = Column(Boolean, default=True, nullable=False)
    alert_on_major = Column(Boolean, default=True, nullable=False)
    alert_on_correction_failed = Column(Boolean, default=True, nullable=False)
    alert_on_rollback = Column(Boolean, default=True, nullable=False)

    # Rétention des données (RGPD)
    error_retention_days = Column(Integer, default=90, nullable=False)
    correction_retention_days = Column(Integer, default=365 * 10, nullable=False)  # 10 ans légal
    alert_retention_days = Column(Integer, default=180, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
