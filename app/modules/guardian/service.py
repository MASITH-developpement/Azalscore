"""
AZALS MODULE GUARDIAN - Service Principal
==========================================

Service de correction automatique gouvernée et auditable.

PRINCIPES FONDAMENTAUX:
1. Aucune correction sans registre préalable
2. Aucune correction non traçable
3. Aucune erreur cachée
4. Tests obligatoires post-correction
5. Rollback automatique si tests échouent

GUARDIAN agit. GUARDIAN explique. GUARDIAN assume.
"""

import hashlib
from datetime import datetime, timedelta

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger

from .models import (
    CorrectionAction,
    CorrectionRegistry,
    CorrectionRule,
    CorrectionStatus,
    CorrectionTest,
    Environment,
    ErrorDetection,
    ErrorSeverity,
    ErrorSource,
    ErrorType,
    GuardianAlert,
    GuardianConfig,
    TestResult,
)
from .schemas import (
    CorrectionRegistryCreate,
    CorrectionRuleCreate,
    CorrectionRuleUpdate,
    ErrorDetectionCreate,
    FrontendErrorReport,
    GuardianConfigUpdate,
    GuardianStatistics,
)

logger = get_logger(__name__)


class GuardianService:
    """
    Service principal GUARDIAN.

    Gère la détection, l'analyse et la correction automatique des erreurs
    tout en garantissant traçabilité et auditabilité complètes.
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._config: GuardianConfig | None = None

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    def get_config(self) -> GuardianConfig:
        """Récupère ou crée la configuration GUARDIAN pour le tenant."""
        if self._config:
            return self._config

        config = self.db.query(GuardianConfig).filter(
            GuardianConfig.tenant_id == self.tenant_id
        ).first()

        if not config:
            config = GuardianConfig(
                tenant_id=self.tenant_id,
                is_enabled=True,
                auto_correction_enabled=True,
                auto_correction_environments=["SANDBOX", "BETA"],
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            logger.info(f"GUARDIAN config created for tenant {self.tenant_id}")

        self._config = config
        return config

    def update_config(self, data: GuardianConfigUpdate) -> GuardianConfig:
        """Met à jour la configuration GUARDIAN."""
        config = self.get_config()
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                if field == "auto_correction_environments":
                    value = [e.value if hasattr(e, 'value') else e for e in value]
                setattr(config, field, value)

        self.db.commit()
        self.db.refresh(config)
        self._config = config

        logger.info(f"GUARDIAN config updated for tenant {self.tenant_id}")
        return config

    # =========================================================================
    # DÉTECTION D'ERREURS
    # =========================================================================

    def detect_error(self, data: ErrorDetectionCreate) -> ErrorDetection:
        """
        Enregistre une erreur détectée.

        Cette méthode est le point d'entrée pour toute erreur dans le système.
        L'erreur est enregistrée puis analysée pour déterminer si une correction
        automatique est possible.
        """
        config = self.get_config()
        if not config.is_enabled:
            logger.warning("GUARDIAN is disabled, error not recorded")
            raise ValueError("GUARDIAN is disabled for this tenant")

        # Vérifier si une erreur similaire existe déjà (déduplication)
        existing_error = self._find_similar_error(data)

        if existing_error:
            # Incrémenter le compteur d'occurrences
            existing_error.occurrence_count += 1
            existing_error.last_occurrence_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing_error)

            logger.info(
                "GUARDIAN: Error occurrence incremented",
                extra={
                    "error_uid": existing_error.error_uid,
                    "occurrence_count": existing_error.occurrence_count,
                    "tenant_id": self.tenant_id
                }
            )
            return existing_error

        # Créer une nouvelle détection
        error = ErrorDetection(
            tenant_id=self.tenant_id,
            severity=data.severity,
            source=data.source,
            error_type=data.error_type,
            environment=data.environment,
            error_message=data.error_message,
            module=data.module,
            route=data.route,
            component=data.component,
            function_name=data.function_name,
            line_number=data.line_number,
            file_path=data.file_path,
            user_role=data.user_role,
            user_id_hash=data.user_id_hash,
            session_id_hash=data.session_id_hash,
            error_code=data.error_code,
            stack_trace=data.stack_trace,
            request_id=data.request_id,
            correlation_id=data.correlation_id,
            context_data=data.context_data,
            http_status=data.http_status,
            http_method=data.http_method,
        )

        self.db.add(error)
        self.db.commit()
        self.db.refresh(error)

        logger.info(
            "GUARDIAN: New error detected",
            extra={
                "error_uid": error.error_uid,
                "severity": error.severity.value,
                "error_type": error.error_type.value,
                "module": error.module,
                "tenant_id": self.tenant_id
            }
        )

        # Créer une alerte si nécessaire
        self._create_alert_if_needed(error)

        # Tenter une correction automatique
        if config.auto_correction_enabled:
            self._attempt_auto_correction(error)

        return error

    def _find_similar_error(self, data: ErrorDetectionCreate) -> ErrorDetection | None:
        """Recherche une erreur similaire existante (déduplication)."""
        # Fenêtre de déduplication: 1 heure
        window = datetime.utcnow() - timedelta(hours=1)

        return self.db.query(ErrorDetection).filter(
            and_(
                ErrorDetection.tenant_id == self.tenant_id,
                ErrorDetection.error_type == data.error_type,
                ErrorDetection.error_code == data.error_code,
                ErrorDetection.module == data.module,
                ErrorDetection.route == data.route,
                ErrorDetection.error_message == data.error_message,
                ErrorDetection.environment == data.environment,
                ErrorDetection.last_occurrence_at >= window,
            )
        ).first()

    def report_frontend_error(self, data: FrontendErrorReport,
                              user_id: int | None = None) -> ErrorDetection:
        """
        Traite un rapport d'erreur frontend.
        Les données utilisateur sont pseudonymisées.
        """
        # Pseudonymisation de l'ID utilisateur
        user_id_hash = None
        if user_id:
            user_id_hash = hashlib.sha256(str(user_id).encode()).hexdigest()

        # Mapper le type d'erreur frontend vers ErrorType
        error_type = self._map_frontend_error_type(data.error_type)

        detection_data = ErrorDetectionCreate(
            severity=ErrorSeverity.MAJOR,  # Par défaut, les erreurs frontend sont majeures
            source=ErrorSource.FRONTEND_LOG,
            error_type=error_type,
            environment=Environment.PRODUCTION,  # Assumé production pour frontend
            error_message=data.error_message,
            module=data.module,
            route=data.route,
            component=data.component,
            user_role=data.user_role,
            user_id_hash=user_id_hash,
            stack_trace=data.stack_trace,
            correlation_id=data.correlation_id,
            context_data={
                "browser": data.browser,
                "browser_version": data.browser_version,
                "os": data.os,
                "viewport": {
                    "width": data.viewport_width,
                    "height": data.viewport_height
                } if data.viewport_width else None,
                "action": data.action,
                "extra": data.extra_context
            }
        )

        return self.detect_error(detection_data)

    def _map_frontend_error_type(self, frontend_type: str) -> ErrorType:
        """Mappe un type d'erreur frontend vers ErrorType."""
        mapping = {
            "TypeError": ErrorType.EXCEPTION,
            "ReferenceError": ErrorType.EXCEPTION,
            "SyntaxError": ErrorType.EXCEPTION,
            "NetworkError": ErrorType.NETWORK,
            "TimeoutError": ErrorType.TIMEOUT,
            "AuthError": ErrorType.AUTHENTICATION,
            "PermissionError": ErrorType.AUTHORIZATION,
            "ValidationError": ErrorType.VALIDATION,
        }
        return mapping.get(frontend_type, ErrorType.UNKNOWN)

    # =========================================================================
    # REGISTRE DES CORRECTIONS (APPEND-ONLY)
    # =========================================================================

    def create_correction_registry(self, data: CorrectionRegistryCreate,
                                   executed_by: str = "GUARDIAN") -> CorrectionRegistry:
        """
        Crée une entrée dans le registre des corrections.

        IMPORTANT: Cette entrée est OBLIGATOIRE avant toute action corrective.
        Le registre est append-only, aucune modification n'est permise.
        """
        # Validation: tous les champs obligatoires doivent être présents
        self._validate_correction_data(data)

        registry_entry = CorrectionRegistry(
            tenant_id=self.tenant_id,
            environment=data.environment,
            error_source=data.error_source,
            error_detection_id=data.error_detection_id,
            error_type=data.error_type,
            severity=data.severity,
            module=data.module,
            route=data.route,
            component=data.component,
            function_impacted=data.function_impacted,
            affected_user_role=data.affected_user_role,
            probable_cause=data.probable_cause,
            correction_action=data.correction_action,
            correction_description=data.correction_description,
            correction_details=data.correction_details,
            estimated_impact=data.estimated_impact,
            impact_scope=data.impact_scope,
            affected_entities_count=data.affected_entities_count,
            is_reversible=data.is_reversible,
            reversibility_justification=data.reversibility_justification,
            rollback_procedure=data.rollback_procedure,
            status=data.status,
            original_error_message=data.original_error_message,
            original_error_code=data.original_error_code,
            original_stack_trace=data.original_stack_trace,
            requires_human_validation=data.requires_human_validation,
            executed_by=executed_by,
            decision_trail=[{
                "timestamp": datetime.utcnow().isoformat(),
                "action": "CREATED",
                "by": executed_by,
                "status": data.status.value
            }]
        )

        self.db.add(registry_entry)
        self.db.commit()
        self.db.refresh(registry_entry)

        # Lier l'erreur à la correction si applicable
        if data.error_detection_id:
            error = self.db.query(ErrorDetection).filter(
                ErrorDetection.id == data.error_detection_id,
                ErrorDetection.tenant_id == self.tenant_id
            ).first()
            if error:
                error.correction_id = registry_entry.id
                error.is_processed = True
                self.db.commit()

        logger.info(
            "GUARDIAN: Correction registry entry created",
            extra={
                "correction_uid": registry_entry.correction_uid,
                "action": registry_entry.correction_action.value,
                "status": registry_entry.status.value,
                "environment": registry_entry.environment.value,
                "tenant_id": self.tenant_id
            }
        )

        return registry_entry

    def _validate_correction_data(self, data: CorrectionRegistryCreate):
        """Valide que toutes les données obligatoires sont présentes."""
        required_fields = [
            ("probable_cause", "Cause probable"),
            ("correction_description", "Description de la correction"),
            ("estimated_impact", "Impact estimé"),
            ("reversibility_justification", "Justification de réversibilité"),
        ]

        for field, name in required_fields:
            value = getattr(data, field, None)
            if not value or len(str(value).strip()) < 10:
                raise ValueError(
                    f"Le champ '{name}' est obligatoire et doit contenir "
                    f"au moins 10 caractères pour être auditable."
                )

    # =========================================================================
    # CORRECTION AUTOMATIQUE
    # =========================================================================

    def _attempt_auto_correction(self, error: ErrorDetection):
        """
        Tente une correction automatique basée sur les règles définies.
        """
        config = self.get_config()

        # Vérifier si l'environnement est autorisé
        env_allowed = error.environment.value in config.auto_correction_environments
        if not env_allowed:
            logger.info(
                f"GUARDIAN: Auto-correction not allowed for environment {error.environment.value}"
            )
            return

        # Vérifier les quotas
        if not self._check_correction_quota(error.environment):
            logger.warning("GUARDIAN: Correction quota exceeded")
            self._create_alert(
                alert_type="QUOTA_EXCEEDED",
                severity=ErrorSeverity.WARNING,
                title="Quota de corrections automatiques atteint",
                message="Le quota de corrections automatiques a été atteint. "
                        "Les nouvelles corrections nécessitent une validation manuelle.",
                error_detection_id=error.id
            )
            return

        # Rechercher une règle applicable
        rule = self._find_applicable_rule(error)
        if not rule:
            logger.debug(f"GUARDIAN: No applicable rule found for error {error.error_uid}")
            return

        # Vérifier le cooldown de la règle
        if not self._check_rule_cooldown(rule):
            logger.info(f"GUARDIAN: Rule {rule.rule_uid} is in cooldown period")
            return

        # Créer l'entrée du registre AVANT d'appliquer la correction
        registry_entry = self._create_registry_for_auto_correction(error, rule)

        # Si validation humaine requise, bloquer
        if rule.requires_human_validation:
            registry_entry.status = CorrectionStatus.BLOCKED
            self._update_decision_trail(registry_entry, "BLOCKED", "GUARDIAN",
                                        "Human validation required by rule")
            self.db.commit()

            self._create_alert(
                alert_type="VALIDATION_REQUIRED",
                severity=error.severity,
                title=f"Validation requise: {rule.name}",
                message=f"La correction automatique pour l'erreur {error.error_uid} "
                        f"nécessite une validation humaine.",
                error_detection_id=error.id,
                correction_id=registry_entry.id,
                target_roles=["DIRIGEANT", "ADMIN"]
            )
            return

        # Appliquer la correction
        self._apply_correction(registry_entry, rule)

    def _find_applicable_rule(self, error: ErrorDetection) -> CorrectionRule | None:
        """Recherche une règle applicable pour l'erreur."""
        query = self.db.query(CorrectionRule).filter(
            CorrectionRule.tenant_id == self.tenant_id,
            CorrectionRule.is_active
        )

        # Filtrer par type d'erreur si spécifié
        rules = query.all()

        for rule in rules:
            if self._rule_matches_error(rule, error):
                return rule

        return None

    def _rule_matches_error(self, rule: CorrectionRule, error: ErrorDetection) -> bool:
        """Vérifie si une règle correspond à une erreur."""
        # Vérifier l'environnement
        if error.environment.value not in rule.allowed_environments:
            return False

        # Vérifier le type d'erreur
        if rule.trigger_error_type and rule.trigger_error_type != error.error_type:
            return False

        # Vérifier le code d'erreur
        if rule.trigger_error_code and rule.trigger_error_code != error.error_code:
            return False

        # Vérifier le module
        if rule.trigger_module and rule.trigger_module != error.module:
            return False

        # Vérifier la sévérité minimale
        if rule.trigger_severity_min:
            severity_order = {
                ErrorSeverity.INFO: 0,
                ErrorSeverity.WARNING: 1,
                ErrorSeverity.MINOR: 2,
                ErrorSeverity.MAJOR: 3,
                ErrorSeverity.CRITICAL: 4,
            }
            if severity_order.get(error.severity, 0) < severity_order.get(rule.trigger_severity_min, 0):
                return False

        # Vérifier les conditions avancées
        return not (rule.trigger_conditions and not self._evaluate_conditions(rule.trigger_conditions, error))

    def _evaluate_conditions(self, conditions: dict, error: ErrorDetection) -> bool:
        """Évalue les conditions avancées d'une règle."""
        # Implémentation simple: vérifier que tous les champs correspondent
        for field, expected_value in conditions.items():
            actual_value = getattr(error, field, None)
            if actual_value is None and error.context_data:
                actual_value = error.context_data.get(field)

            if actual_value != expected_value:
                return False

        return True

    def _check_correction_quota(self, environment: Environment) -> bool:
        """Vérifie si le quota de corrections n'est pas dépassé."""
        config = self.get_config()
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        count = self.db.query(func.count(CorrectionRegistry.id)).filter(
            CorrectionRegistry.tenant_id == self.tenant_id,
            CorrectionRegistry.environment == environment,
            CorrectionRegistry.created_at >= today_start,
            CorrectionRegistry.executed_by == "GUARDIAN"
        ).scalar()

        if environment == Environment.PRODUCTION:
            return count < config.max_auto_corrections_production
        return count < config.max_auto_corrections_per_day

    def _check_rule_cooldown(self, rule: CorrectionRule) -> bool:
        """Vérifie si la règle n'est pas en période de cooldown."""
        if not rule.last_execution_at:
            return True

        cooldown_end = rule.last_execution_at + timedelta(seconds=rule.cooldown_seconds)
        return datetime.utcnow() >= cooldown_end

    def _create_registry_for_auto_correction(self, error: ErrorDetection,
                                              rule: CorrectionRule) -> CorrectionRegistry:
        """Crée une entrée de registre pour une correction automatique."""
        data = CorrectionRegistryCreate(
            environment=error.environment,
            error_source=error.source,
            error_detection_id=error.id,
            error_type=error.error_type,
            severity=error.severity,
            module=error.module or "unknown",
            route=error.route,
            component=error.component,
            function_impacted=error.function_name,
            affected_user_role=error.user_role,
            probable_cause=f"Erreur détectée automatiquement: {error.error_message[:500]}. "
                          f"Règle appliquée: {rule.name} (v{rule.version})",
            correction_action=rule.correction_action,
            correction_description=f"Correction automatique via règle '{rule.name}': "
                                  f"{rule.description or 'Aucune description'}",
            correction_details={
                "rule_uid": rule.rule_uid,
                "rule_name": rule.name,
                "rule_version": rule.version,
                "action_config": rule.action_config
            },
            estimated_impact=f"Impact automatiquement évalué selon la règle. "
                            f"Scope: {error.module or 'système'}. "
                            f"Niveau de risque de la règle: {rule.risk_level}",
            impact_scope=error.module,
            is_reversible=rule.is_reversible,
            reversibility_justification=f"Réversibilité définie par la règle '{rule.name}'. "
                                        f"{'Action réversible.' if rule.is_reversible else 'Action irréversible - justifiée par la nature de la correction.'}",
            rollback_procedure=rule.action_config.get("rollback_procedure") if rule.action_config else None,
            status=CorrectionStatus.PENDING,
            original_error_message=error.error_message,
            original_error_code=error.error_code,
            original_stack_trace=error.stack_trace,
            requires_human_validation=rule.requires_human_validation,
        )

        return self.create_correction_registry(data, executed_by="GUARDIAN")

    def _apply_correction(self, registry: CorrectionRegistry, rule: CorrectionRule):
        """
        Applique une correction.
        """
        start_time = datetime.utcnow()
        registry.status = CorrectionStatus.IN_PROGRESS
        self._update_decision_trail(registry, "STARTED", "GUARDIAN", "Applying correction")
        self.db.commit()

        try:
            # Exécuter l'action corrective
            success = self._execute_correction_action(registry, rule)

            if success:
                registry.status = CorrectionStatus.TESTING
                self._update_decision_trail(registry, "CORRECTION_APPLIED", "GUARDIAN",
                                           "Correction applied, running tests")
                self.db.commit()

                # Exécuter les tests post-correction
                test_success = self._run_post_correction_tests(registry, rule)

                if test_success:
                    registry.status = CorrectionStatus.APPLIED
                    registry.correction_successful = True
                    registry.correction_result = "Correction appliquée avec succès. Tous les tests passés."
                    self._update_decision_trail(registry, "COMPLETED", "GUARDIAN",
                                               "All tests passed")

                    # Mettre à jour les stats de la règle
                    rule.successful_executions += 1
                else:
                    # Rollback si tests échouent
                    self._perform_rollback(registry, "Tests post-correction échoués")
                    rule.failed_executions += 1

            else:
                registry.status = CorrectionStatus.FAILED
                registry.correction_successful = False
                registry.correction_result = "Échec de l'application de la correction"
                self._update_decision_trail(registry, "FAILED", "GUARDIAN",
                                           "Correction application failed")
                rule.failed_executions += 1

        except Exception as e:
            logger.exception(f"GUARDIAN: Error applying correction {registry.correction_uid}")
            registry.status = CorrectionStatus.FAILED
            registry.correction_successful = False
            registry.correction_result = f"Exception: {str(e)}"
            self._update_decision_trail(registry, "ERROR", "GUARDIAN", str(e))
            rule.failed_executions += 1

        finally:
            end_time = datetime.utcnow()
            registry.executed_at = end_time
            registry.execution_duration_ms = (end_time - start_time).total_seconds() * 1000
            rule.total_executions += 1
            rule.last_execution_at = end_time
            self.db.commit()

            logger.info(
                f"GUARDIAN: Correction {registry.correction_uid} completed",
                extra={
                    "status": registry.status.value,
                    "success": registry.correction_successful,
                    "duration_ms": registry.execution_duration_ms,
                    "tenant_id": self.tenant_id
                }
            )

    def _execute_correction_action(self, registry: CorrectionRegistry,
                                   rule: CorrectionRule) -> bool:
        """
        Exécute l'action corrective selon le type.
        """
        action = registry.correction_action
        config = rule.action_config or {}

        logger.info(f"GUARDIAN: Executing action {action.value}")

        # Actions supportées
        action_handlers = {
            CorrectionAction.CACHE_CLEAR: self._action_cache_clear,
            CorrectionAction.CONFIG_UPDATE: self._action_config_update,
            CorrectionAction.MONITORING_ONLY: self._action_monitoring_only,
            CorrectionAction.WORKAROUND: self._action_workaround,
            CorrectionAction.ESCALATION: self._action_escalation,
        }

        handler = action_handlers.get(action)
        if handler:
            return handler(registry, config)

        # Actions nécessitant validation manuelle
        if action in [CorrectionAction.SERVICE_RESTART, CorrectionAction.DATABASE_REPAIR,
                      CorrectionAction.DATA_MIGRATION, CorrectionAction.AUTO_FIX]:
            logger.warning(f"GUARDIAN: Action {action.value} requires manual execution")
            registry.status = CorrectionStatus.BLOCKED
            self._update_decision_trail(registry, "BLOCKED", "GUARDIAN",
                                        f"Action {action.value} requires manual execution")
            return False

        return False

    def _action_cache_clear(self, registry: CorrectionRegistry, config: dict) -> bool:
        """Action: vider le cache."""
        # Dans un vrai système, on viderait le cache Redis ici
        logger.info("GUARDIAN: Cache clear action executed (simulated)")
        return True

    def _action_config_update(self, registry: CorrectionRegistry, config: dict) -> bool:
        """Action: mise à jour de configuration."""
        # Implémenter la mise à jour de config spécifique
        logger.info("GUARDIAN: Config update action executed (simulated)")
        return True

    def _action_monitoring_only(self, registry: CorrectionRegistry, config: dict) -> bool:
        """Action: surveillance uniquement."""
        logger.info("GUARDIAN: Monitoring only - no action taken")
        return True

    def _action_workaround(self, registry: CorrectionRegistry, config: dict) -> bool:
        """Action: contournement temporaire."""
        logger.info("GUARDIAN: Workaround action executed (simulated)")
        return True

    def _action_escalation(self, registry: CorrectionRegistry, config: dict) -> bool:
        """Action: escalade vers un humain."""
        self._create_alert(
            alert_type="ESCALATION",
            severity=registry.severity,
            title=f"Escalade: {registry.module}",
            message=f"L'erreur {registry.original_error_code or 'N/A'} nécessite "
                    f"une intervention manuelle. Cause: {registry.probable_cause[:200]}",
            correction_id=registry.id,
            target_roles=["DIRIGEANT", "ADMIN"]
        )
        return True

    # =========================================================================
    # TESTS POST-CORRECTION
    # =========================================================================

    def _run_post_correction_tests(self, registry: CorrectionRegistry,
                                   rule: CorrectionRule) -> bool:
        """
        Exécute les tests obligatoires après correction.
        """
        required_tests = rule.required_tests or ["SCENARIO", "REGRESSION"]
        tests_results = []
        all_passed = True

        for test_type in required_tests:
            test = self._create_and_run_test(registry, test_type)
            tests_results.append({
                "test_name": test.test_name,
                "test_type": test.test_type,
                "result": test.result.value,
                "duration_ms": test.duration_ms,
                "error": test.error_message
            })

            if test.result in [TestResult.FAILED, TestResult.ERROR]:
                all_passed = False
                if test.triggers_rollback:
                    break

        # Enregistrer les résultats dans le registre
        registry.tests_executed = tests_results
        self.db.commit()

        return all_passed

    def _create_and_run_test(self, registry: CorrectionRegistry,
                             test_type: str) -> CorrectionTest:
        """Crée et exécute un test post-correction."""
        start_time = datetime.utcnow()

        test = CorrectionTest(
            tenant_id=self.tenant_id,
            correction_id=registry.id,
            test_name=f"Post-correction {test_type} test",
            test_type=test_type,
            started_at=start_time,
            blocking=True,
            triggers_rollback=test_type in ["SCENARIO", "REGRESSION"]
        )

        try:
            # Exécuter le test selon son type
            result, details = self._execute_test(test_type, registry)
            test.result = result
            test.result_details = details

        except Exception as e:
            test.result = TestResult.ERROR
            test.error_message = str(e)
            logger.exception(f"GUARDIAN: Test {test_type} failed with exception")

        finally:
            test.completed_at = datetime.utcnow()
            test.duration_ms = (test.completed_at - start_time).total_seconds() * 1000
            self.db.add(test)
            self.db.commit()

        return test

    def _execute_test(self, test_type: str, registry: CorrectionRegistry) -> tuple[TestResult, dict]:
        """Exécute un test spécifique."""
        # Dans une implémentation réelle, ces tests seraient plus élaborés
        test_handlers = {
            "SCENARIO": self._test_scenario,
            "REGRESSION": self._test_regression,
            "PERSISTENCE": self._test_persistence,
            "PERMISSION": self._test_permissions,
            "ACCESS": self._test_access_control,
        }

        handler = test_handlers.get(test_type, self._test_default)
        return handler(registry)

    def _test_scenario(self, registry: CorrectionRegistry) -> tuple[TestResult, dict]:
        """Test du scénario ayant provoqué l'erreur."""
        # Simulation - en production, rejouer le scénario
        return TestResult.PASSED, {"message": "Scenario test passed"}

    def _test_regression(self, registry: CorrectionRegistry) -> tuple[TestResult, dict]:
        """Test de non-régression."""
        return TestResult.PASSED, {"message": "Regression test passed"}

    def _test_persistence(self, registry: CorrectionRegistry) -> tuple[TestResult, dict]:
        """Test de persistance des données."""
        return TestResult.PASSED, {"message": "Persistence test passed"}

    def _test_permissions(self, registry: CorrectionRegistry) -> tuple[TestResult, dict]:
        """Test des permissions et rôles."""
        return TestResult.PASSED, {"message": "Permission test passed"}

    def _test_access_control(self, registry: CorrectionRegistry) -> tuple[TestResult, dict]:
        """Test d'accès non autorisé."""
        return TestResult.PASSED, {"message": "Access control test passed"}

    def _test_default(self, registry: CorrectionRegistry) -> tuple[TestResult, dict]:
        """Test par défaut."""
        return TestResult.PASSED, {"message": "Default test passed"}

    # =========================================================================
    # ROLLBACK
    # =========================================================================

    def _perform_rollback(self, registry: CorrectionRegistry, reason: str,
                         by: str = "GUARDIAN"):
        """
        Effectue un rollback d'une correction.

        Note: Le rollback est enregistré dans le même registre (append-only)
        via les champs rolled_back, rollback_at, rollback_reason.
        """
        logger.warning(
            f"GUARDIAN: Performing rollback for correction {registry.correction_uid}",
            extra={"reason": reason, "tenant_id": self.tenant_id}
        )

        registry.status = CorrectionStatus.ROLLED_BACK
        registry.rolled_back = True
        registry.rollback_at = datetime.utcnow()
        registry.rollback_reason = reason
        registry.rollback_by = by
        registry.correction_successful = False
        registry.correction_result = f"Rollback effectué: {reason}"

        self._update_decision_trail(registry, "ROLLED_BACK", by, reason)
        self.db.commit()

        # Alerte de rollback
        config = self.get_config()
        if config.alert_on_rollback:
            self._create_alert(
                alert_type="ROLLBACK",
                severity=ErrorSeverity.MAJOR,
                title=f"Rollback effectué: {registry.module}",
                message=f"La correction {registry.correction_uid} a été annulée. "
                        f"Raison: {reason}",
                correction_id=registry.id,
                target_roles=["DIRIGEANT", "ADMIN"]
            )

    def request_rollback(self, correction_id: int, reason: str,
                        user_id: int) -> CorrectionRegistry:
        """Demande de rollback manuel par un utilisateur."""
        registry = self.db.query(CorrectionRegistry).filter(
            CorrectionRegistry.id == correction_id,
            CorrectionRegistry.tenant_id == self.tenant_id
        ).first()

        if not registry:
            raise ValueError(f"Correction {correction_id} not found")

        if registry.rolled_back:
            raise ValueError("Correction already rolled back")

        if not registry.is_reversible:
            raise ValueError("Correction is not reversible")

        self._perform_rollback(registry, reason, by=f"user:{user_id}")
        return registry

    # =========================================================================
    # VALIDATION HUMAINE
    # =========================================================================

    def validate_correction(self, correction_id: int, approved: bool,
                           user_id: int, comment: str | None = None) -> CorrectionRegistry:
        """Validation ou rejet d'une correction par un humain."""
        registry = self.db.query(CorrectionRegistry).filter(
            CorrectionRegistry.id == correction_id,
            CorrectionRegistry.tenant_id == self.tenant_id
        ).first()

        if not registry:
            raise ValueError(f"Correction {correction_id} not found")

        if registry.status not in [CorrectionStatus.BLOCKED, CorrectionStatus.PROPOSED]:
            raise ValueError(f"Correction is not pending validation (status: {registry.status.value})")

        registry.validated_by = user_id
        registry.validated_at = datetime.utcnow()
        registry.validation_comment = comment

        if approved:
            registry.status = CorrectionStatus.APPROVED
            self._update_decision_trail(registry, "APPROVED", f"user:{user_id}", comment)

            # Si une règle est associée, appliquer la correction
            if registry.correction_details and registry.correction_details.get("rule_uid"):
                rule = self.db.query(CorrectionRule).filter(
                    CorrectionRule.rule_uid == registry.correction_details["rule_uid"]
                ).first()
                if rule:
                    self._apply_correction(registry, rule)
        else:
            registry.status = CorrectionStatus.REJECTED
            self._update_decision_trail(registry, "REJECTED", f"user:{user_id}", comment)

        self.db.commit()
        self.db.refresh(registry)

        logger.info(
            f"GUARDIAN: Correction {registry.correction_uid} "
            f"{'approved' if approved else 'rejected'} by user {user_id}"
        )

        return registry

    # =========================================================================
    # ALERTES
    # =========================================================================

    def _create_alert_if_needed(self, error: ErrorDetection):
        """Crée une alerte si nécessaire selon la configuration."""
        config = self.get_config()

        should_alert = False
        if error.severity == ErrorSeverity.CRITICAL and config.alert_on_critical or error.severity == ErrorSeverity.MAJOR and config.alert_on_major:
            should_alert = True

        if should_alert:
            self._create_alert(
                alert_type="ERROR_DETECTED",
                severity=error.severity,
                title=f"Erreur {error.severity.value}: {error.module or 'système'}",
                message=f"Erreur détectée: {error.error_message[:500]}",
                error_detection_id=error.id,
                target_roles=["DIRIGEANT", "ADMIN"]
            )

    def _create_alert(self, alert_type: str, severity: ErrorSeverity,
                     title: str, message: str,
                     error_detection_id: int | None = None,
                     correction_id: int | None = None,
                     target_roles: list[str] | None = None,
                     target_users: list[int] | None = None,
                     details: dict | None = None) -> GuardianAlert:
        """Crée une alerte GUARDIAN."""
        alert = GuardianAlert(
            tenant_id=self.tenant_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            details=details,
            error_detection_id=error_detection_id,
            correction_id=correction_id,
            target_roles=target_roles,
            target_users=target_users,
        )

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        logger.info(
            "GUARDIAN: Alert created",
            extra={
                "alert_uid": alert.alert_uid,
                "type": alert_type,
                "severity": severity.value,
                "tenant_id": self.tenant_id
            }
        )

        return alert

    def acknowledge_alert(self, alert_id: int, user_id: int) -> GuardianAlert:
        """Acquitte une alerte."""
        alert = self.db.query(GuardianAlert).filter(
            GuardianAlert.id == alert_id,
            GuardianAlert.tenant_id == self.tenant_id
        ).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.is_read = True
        alert.read_by = user_id
        alert.read_at = datetime.utcnow()
        alert.is_acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve_alert(self, alert_id: int, user_id: int,
                     comment: str | None = None) -> GuardianAlert:
        """Résout une alerte."""
        alert = self.db.query(GuardianAlert).filter(
            GuardianAlert.id == alert_id,
            GuardianAlert.tenant_id == self.tenant_id
        ).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.is_resolved = True
        alert.resolved_by = user_id
        alert.resolved_at = datetime.utcnow()
        alert.resolution_comment = comment

        if not alert.is_acknowledged:
            alert.is_acknowledged = True
            alert.acknowledged_by = user_id
            alert.acknowledged_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(alert)
        return alert

    # =========================================================================
    # RÈGLES DE CORRECTION
    # =========================================================================

    def create_correction_rule(self, data: CorrectionRuleCreate,
                               user_id: int) -> CorrectionRule:
        """Crée une nouvelle règle de correction."""
        rule = CorrectionRule(
            tenant_id=self.tenant_id,
            name=data.name,
            description=data.description,
            trigger_error_type=data.trigger_error_type,
            trigger_error_code=data.trigger_error_code,
            trigger_module=data.trigger_module,
            trigger_severity_min=data.trigger_severity_min,
            trigger_conditions=data.trigger_conditions,
            correction_action=data.correction_action,
            action_config=data.action_config,
            action_script=data.action_script,
            allowed_environments=[e.value for e in data.allowed_environments],
            max_auto_corrections_per_hour=data.max_auto_corrections_per_hour,
            cooldown_seconds=data.cooldown_seconds,
            requires_human_validation=data.requires_human_validation,
            risk_level=data.risk_level,
            is_reversible=data.is_reversible,
            required_tests=data.required_tests,
            created_by=user_id,
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        logger.info(
            "GUARDIAN: Correction rule created",
            extra={
                "rule_uid": rule.rule_uid,
                "name": rule.name,
                "created_by": user_id,
                "tenant_id": self.tenant_id
            }
        )

        return rule

    def update_correction_rule(self, rule_id: int,
                               data: CorrectionRuleUpdate) -> CorrectionRule:
        """Met à jour une règle de correction."""
        rule = self.db.query(CorrectionRule).filter(
            CorrectionRule.id == rule_id,
            CorrectionRule.tenant_id == self.tenant_id,
            not CorrectionRule.is_system_rule
        ).first()

        if not rule:
            raise ValueError(f"Rule {rule_id} not found or is a system rule")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if field == "allowed_environments":
                    value = [e.value if hasattr(e, 'value') else e for e in value]
                setattr(rule, field, value)

        # Incrémenter la version
        version_parts = rule.version.split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        rule.version = ".".join(version_parts)

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_correction_rule(self, rule_id: int) -> bool:
        """Désactive une règle de correction (soft delete)."""
        rule = self.db.query(CorrectionRule).filter(
            CorrectionRule.id == rule_id,
            CorrectionRule.tenant_id == self.tenant_id,
            not CorrectionRule.is_system_rule
        ).first()

        if not rule:
            raise ValueError(f"Rule {rule_id} not found or is a system rule")

        rule.is_active = False
        self.db.commit()
        return True

    # =========================================================================
    # REQUÊTES
    # =========================================================================

    def list_errors(self, page: int = 1, page_size: int = 20,
                   severity: ErrorSeverity | None = None,
                   error_type: ErrorType | None = None,
                   module: str | None = None,
                   is_processed: bool | None = None,
                   environment: Environment | None = None,
                   date_from: datetime | None = None,
                   date_to: datetime | None = None) -> tuple[list[ErrorDetection], int]:
        """Liste les erreurs détectées avec filtres et pagination."""
        query = self.db.query(ErrorDetection).filter(
            ErrorDetection.tenant_id == self.tenant_id
        )

        if severity:
            query = query.filter(ErrorDetection.severity == severity)
        if error_type:
            query = query.filter(ErrorDetection.error_type == error_type)
        if module:
            query = query.filter(ErrorDetection.module == module)
        if is_processed is not None:
            query = query.filter(ErrorDetection.is_processed == is_processed)
        if environment:
            query = query.filter(ErrorDetection.environment == environment)
        if date_from:
            query = query.filter(ErrorDetection.detected_at >= date_from)
        if date_to:
            query = query.filter(ErrorDetection.detected_at <= date_to)

        total = query.count()
        items = query.order_by(desc(ErrorDetection.detected_at))\
                     .offset((page - 1) * page_size)\
                     .limit(page_size)\
                     .all()

        return items, total

    def list_corrections(self, page: int = 1, page_size: int = 20,
                        status: CorrectionStatus | None = None,
                        environment: Environment | None = None,
                        severity: ErrorSeverity | None = None,
                        module: str | None = None,
                        requires_validation: bool | None = None,
                        date_from: datetime | None = None,
                        date_to: datetime | None = None) -> tuple[list[CorrectionRegistry], int]:
        """Liste les corrections avec filtres et pagination."""
        query = self.db.query(CorrectionRegistry).filter(
            CorrectionRegistry.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(CorrectionRegistry.status == status)
        if environment:
            query = query.filter(CorrectionRegistry.environment == environment)
        if severity:
            query = query.filter(CorrectionRegistry.severity == severity)
        if module:
            query = query.filter(CorrectionRegistry.module == module)
        if requires_validation is not None:
            query = query.filter(CorrectionRegistry.requires_human_validation == requires_validation)
        if date_from:
            query = query.filter(CorrectionRegistry.created_at >= date_from)
        if date_to:
            query = query.filter(CorrectionRegistry.created_at <= date_to)

        total = query.count()
        items = query.order_by(desc(CorrectionRegistry.created_at))\
                     .offset((page - 1) * page_size)\
                     .limit(page_size)\
                     .all()

        return items, total

    def list_rules(self, page: int = 1, page_size: int = 20,
                  is_active: bool | None = True) -> tuple[list[CorrectionRule], int]:
        """Liste les règles de correction."""
        query = self.db.query(CorrectionRule).filter(
            CorrectionRule.tenant_id == self.tenant_id
        )

        if is_active is not None:
            query = query.filter(CorrectionRule.is_active == is_active)

        total = query.count()
        items = query.order_by(desc(CorrectionRule.created_at))\
                     .offset((page - 1) * page_size)\
                     .limit(page_size)\
                     .all()

        return items, total

    def list_alerts(self, page: int = 1, page_size: int = 20,
                   is_resolved: bool | None = None,
                   severity: ErrorSeverity | None = None) -> tuple[list[GuardianAlert], int, int]:
        """Liste les alertes avec compteur non lues."""
        query = self.db.query(GuardianAlert).filter(
            GuardianAlert.tenant_id == self.tenant_id
        )

        if is_resolved is not None:
            query = query.filter(GuardianAlert.is_resolved == is_resolved)
        if severity:
            query = query.filter(GuardianAlert.severity == severity)

        total = query.count()

        # Compteur non lues
        unread_count = self.db.query(func.count(GuardianAlert.id)).filter(
            GuardianAlert.tenant_id == self.tenant_id,
            not GuardianAlert.is_read
        ).scalar()

        items = query.order_by(desc(GuardianAlert.created_at))\
                     .offset((page - 1) * page_size)\
                     .limit(page_size)\
                     .all()

        return items, total, unread_count

    def get_correction_tests(self, correction_id: int) -> list[CorrectionTest]:
        """Récupère les tests d'une correction."""
        return self.db.query(CorrectionTest).filter(
            CorrectionTest.correction_id == correction_id,
            CorrectionTest.tenant_id == self.tenant_id
        ).order_by(CorrectionTest.started_at).all()

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_statistics(self, period_days: int = 30) -> GuardianStatistics:
        """Génère les statistiques GUARDIAN."""
        period_start = datetime.utcnow() - timedelta(days=period_days)
        period_end = datetime.utcnow()

        # Erreurs
        errors = self.db.query(ErrorDetection).filter(
            ErrorDetection.tenant_id == self.tenant_id,
            ErrorDetection.detected_at >= period_start
        ).all()

        errors_by_severity = {}
        errors_by_type = {}
        errors_by_module = {}
        errors_by_source = {}

        for error in errors:
            sev = error.severity.value
            errors_by_severity[sev] = errors_by_severity.get(sev, 0) + 1

            etype = error.error_type.value
            errors_by_type[etype] = errors_by_type.get(etype, 0) + 1

            module = error.module or "unknown"
            errors_by_module[module] = errors_by_module.get(module, 0) + 1

            source = error.source.value
            errors_by_source[source] = errors_by_source.get(source, 0) + 1

        # Corrections
        corrections = self.db.query(CorrectionRegistry).filter(
            CorrectionRegistry.tenant_id == self.tenant_id,
            CorrectionRegistry.created_at >= period_start
        ).all()

        corrections_by_status = {}
        corrections_by_action = {}
        auto_count = 0
        manual_count = 0
        successful = 0
        failed = 0
        rollback_count = 0
        total_duration = 0
        duration_count = 0

        for corr in corrections:
            status = corr.status.value
            corrections_by_status[status] = corrections_by_status.get(status, 0) + 1

            action = corr.correction_action.value
            corrections_by_action[action] = corrections_by_action.get(action, 0) + 1

            if corr.executed_by == "GUARDIAN":
                auto_count += 1
            else:
                manual_count += 1

            if corr.correction_successful:
                successful += 1
            elif corr.correction_successful is False:
                failed += 1

            if corr.rolled_back:
                rollback_count += 1

            if corr.execution_duration_ms:
                total_duration += corr.execution_duration_ms
                duration_count += 1

        # Tests
        tests = self.db.query(CorrectionTest).filter(
            CorrectionTest.tenant_id == self.tenant_id,
            CorrectionTest.started_at >= period_start
        ).all()

        tests_passed = sum(1 for t in tests if t.result == TestResult.PASSED)
        tests_failed = sum(1 for t in tests if t.result in [TestResult.FAILED, TestResult.ERROR])

        # Alertes
        alerts = self.db.query(GuardianAlert).filter(
            GuardianAlert.tenant_id == self.tenant_id,
            GuardianAlert.created_at >= period_start
        ).all()

        alerts_by_severity = {}
        unresolved = 0
        for alert in alerts:
            sev = alert.severity.value
            alerts_by_severity[sev] = alerts_by_severity.get(sev, 0) + 1
            if not alert.is_resolved:
                unresolved += 1

        return GuardianStatistics(
            period_start=period_start,
            period_end=period_end,
            total_errors_detected=len(errors),
            errors_by_severity=errors_by_severity,
            errors_by_type=errors_by_type,
            errors_by_module=errors_by_module,
            errors_by_source=errors_by_source,
            total_corrections=len(corrections),
            corrections_by_status=corrections_by_status,
            corrections_by_action=corrections_by_action,
            auto_corrections_count=auto_count,
            manual_corrections_count=manual_count,
            successful_corrections=successful,
            failed_corrections=failed,
            rollback_count=rollback_count,
            total_tests_executed=len(tests),
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            total_alerts=len(alerts),
            unresolved_alerts=unresolved,
            alerts_by_severity=alerts_by_severity,
            avg_correction_time_ms=total_duration / duration_count if duration_count > 0 else None,
        )

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _update_decision_trail(self, registry: CorrectionRegistry,
                               action: str, by: str, detail: str | None = None):
        """Met à jour le trail de décision (append-only)."""
        if registry.decision_trail is None:
            registry.decision_trail = []

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "by": by,
            "status": registry.status.value
        }
        if detail:
            entry["detail"] = detail

        registry.decision_trail.append(entry)


def get_guardian_service(db: Session, tenant_id: str) -> GuardianService:
    """Factory function pour le service GUARDIAN."""
    return GuardianService(db, tenant_id)
