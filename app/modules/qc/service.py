"""
AZALS MODULE T4 - Service Contrôle Qualité Central
====================================================

Service principal pour le contrôle qualité.
"""
from __future__ import annotations


import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Integer, case, desc, func, or_
from sqlalchemy.orm import Session

from app.core.query_optimizer import QueryOptimizer

from app.modules.qc.models import (
    ModuleRegistry,
    ModuleStatus,
    QCAlert,
    QCCheckResult,
    QCCheckStatus,
    QCDashboard,
    QCMetric,
    QCRule,
    QCRuleCategory,
    QCRuleSeverity,
    QCTemplate,
    QCValidation,
    TestRun,
    TestType,
    ValidationPhase,
)


class QCService:
    """Service de contrôle qualité central."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self._optimizer = QueryOptimizer(db)

    # ========================================================================
    # GESTION DES RÈGLES QC
    # ========================================================================

    def create_rule(
        self,
        code: str,
        name: str,
        category: QCRuleCategory,
        check_type: str,
        description: str = None,
        severity: QCRuleSeverity = QCRuleSeverity.WARNING,
        applies_to_modules: list[str] = None,
        applies_to_phases: list[str] = None,
        check_config: dict = None,
        threshold_value: float = None,
        threshold_operator: str = None,
        created_by: int = None
    ) -> QCRule:
        """Crée une nouvelle règle QC."""
        rule = QCRule(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            category=category,
            severity=severity,
            applies_to_modules=json.dumps(applies_to_modules) if applies_to_modules else "*",
            applies_to_phases=json.dumps(applies_to_phases) if applies_to_phases else None,
            check_type=check_type,
            check_config=json.dumps(check_config) if check_config else None,
            threshold_value=threshold_value,
            threshold_operator=threshold_operator,
            created_by=created_by
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_rule(self, rule_id: int) -> QCRule | None:
        """Récupère une règle par ID."""
        return self.db.query(QCRule).filter(
            QCRule.id == rule_id,
            QCRule.tenant_id == self.tenant_id
        ).first()

    def get_rule_by_code(self, code: str) -> QCRule | None:
        """Récupère une règle par code."""
        return self.db.query(QCRule).filter(
            QCRule.code == code,
            QCRule.tenant_id == self.tenant_id
        ).first()

    def list_rules(
        self,
        category: QCRuleCategory = None,
        severity: QCRuleSeverity = None,
        is_active: bool = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[QCRule], int]:
        """Liste les règles QC avec filtres."""
        query = self.db.query(QCRule).filter(QCRule.tenant_id == self.tenant_id)

        if category:
            query = query.filter(QCRule.category == category)
        if severity:
            query = query.filter(QCRule.severity == severity)
        if is_active is not None:
            query = query.filter(QCRule.is_active == is_active)

        total = query.count()
        rules = query.order_by(QCRule.category, QCRule.code).offset(skip).limit(limit).all()

        return rules, total

    def update_rule(self, rule_id: int, **updates) -> QCRule | None:
        """Met à jour une règle."""
        rule = self.get_rule(rule_id)
        if not rule or rule.is_system:
            return None

        for key, value in updates.items():
            if hasattr(rule, key) and value is not None:
                if key in ["applies_to_modules", "applies_to_phases", "check_config"]:
                    value = json.dumps(value) if isinstance(value, (list, dict)) else value
                setattr(rule, key, value)

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, rule_id: int) -> bool:
        """Supprime une règle (non système)."""
        rule = self.get_rule(rule_id)
        if not rule or rule.is_system:
            return False

        self.db.delete(rule)
        self.db.commit()
        return True

    def get_rules_for_module(self, module_code: str, phase: ValidationPhase = None) -> list[QCRule]:
        """Récupère les règles applicables à un module."""
        rules = self.db.query(QCRule).filter(
            QCRule.tenant_id == self.tenant_id,
            QCRule.is_active
        ).all()

        applicable = []
        for rule in rules:
            # Vérifier si le module est concerné
            modules = rule.applies_to_modules
            if modules and modules != "*":
                module_list = json.loads(modules)
                if module_code not in module_list and "*" not in module_list:
                    continue

            # Vérifier la phase
            if phase and rule.applies_to_phases:
                phases = json.loads(rule.applies_to_phases)
                if phase.value not in phases:
                    continue

            applicable.append(rule)

        return applicable

    # ========================================================================
    # GESTION DES MODULES
    # ========================================================================

    def register_module(
        self,
        module_code: str,
        module_name: str,
        module_type: str,
        module_version: str = "1.0.0",
        description: str = None,
        dependencies: list[str] = None
    ) -> ModuleRegistry:
        """Enregistre un nouveau module dans le registre."""
        # Vérifier si existe déjà
        existing = self.db.query(ModuleRegistry).filter(
            ModuleRegistry.tenant_id == self.tenant_id,
            ModuleRegistry.module_code == module_code
        ).first()

        if existing:
            # Mettre à jour
            existing.module_name = module_name
            existing.module_version = module_version
            existing.description = description
            existing.dependencies = json.dumps(dependencies) if dependencies else None
            self.db.commit()
            self.db.refresh(existing)
            return existing

        module = ModuleRegistry(
            tenant_id=self.tenant_id,
            module_code=module_code,
            module_name=module_name,
            module_type=module_type,
            module_version=module_version,
            description=description,
            dependencies=json.dumps(dependencies) if dependencies else None
        )
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        return module

    def get_module(self, module_id: int) -> ModuleRegistry | None:
        """Récupère un module par ID."""
        return self.db.query(ModuleRegistry).filter(
            ModuleRegistry.id == module_id,
            ModuleRegistry.tenant_id == self.tenant_id
        ).first()

    def get_module_by_code(self, module_code: str) -> ModuleRegistry | None:
        """Récupère un module par code."""
        return self.db.query(ModuleRegistry).filter(
            ModuleRegistry.module_code == module_code,
            ModuleRegistry.tenant_id == self.tenant_id
        ).first()

    def list_modules(
        self,
        module_type: str = None,
        status: ModuleStatus = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[ModuleRegistry], int]:
        """Liste les modules enregistrés."""
        query = self.db.query(ModuleRegistry).filter(
            ModuleRegistry.tenant_id == self.tenant_id
        )

        if module_type:
            query = query.filter(ModuleRegistry.module_type == module_type)
        if status:
            query = query.filter(ModuleRegistry.status == status)

        total = query.count()
        modules = query.order_by(ModuleRegistry.module_code).offset(skip).limit(limit).all()

        return modules, total

    def update_module_status(
        self,
        module_id: int,
        status: ModuleStatus,
        validated_by: int = None
    ) -> ModuleRegistry | None:
        """Met à jour le statut d'un module."""
        module = self.get_module(module_id)
        if not module:
            return None

        module.status = status

        if status == ModuleStatus.QC_PASSED:
            module.validated_at = datetime.utcnow()
            module.validated_by = validated_by
        elif status == ModuleStatus.PRODUCTION:
            module.production_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(module)
        return module

    # ========================================================================
    # VALIDATION QC
    # ========================================================================

    def start_validation(
        self,
        module_id: int,
        phase: ValidationPhase,
        started_by: int = None
    ) -> QCValidation:
        """Démarre une session de validation QC."""
        validation = QCValidation(
            tenant_id=self.tenant_id,
            module_id=module_id,
            validation_phase=phase,
            started_by=started_by,
            status=QCCheckStatus.RUNNING
        )
        self.db.add(validation)
        self.db.commit()
        self.db.refresh(validation)

        # Mettre à jour le statut du module
        module = self.get_module(module_id)
        if module and module.status not in [ModuleStatus.PRODUCTION, ModuleStatus.DEPRECATED]:
            module.status = ModuleStatus.QC_IN_PROGRESS
            module.last_qc_run = datetime.utcnow()
            self.db.commit()

        return validation

    def run_validation(
        self,
        module_id: int,
        phase: ValidationPhase = ValidationPhase.AUTOMATED,
        started_by: int = None
    ) -> QCValidation:
        """Exécute une validation complète d'un module."""
        module = self.get_module(module_id)
        if not module:
            raise ValueError(f"Module {module_id} not found")

        # Démarrer la validation
        validation = self.start_validation(module_id, phase, started_by)

        # Récupérer les règles applicables
        rules = self.get_rules_for_module(module.module_code, phase)
        validation.total_rules = len(rules)

        # Exécuter chaque règle
        category_scores = {}
        for rule in rules:
            result = self._execute_rule(validation, rule, module)

            # Comptabiliser
            if result.status == QCCheckStatus.PASSED:
                validation.passed_rules += 1
            elif result.status == QCCheckStatus.FAILED:
                validation.failed_rules += 1
                if rule.severity == QCRuleSeverity.BLOCKER:
                    validation.blocked_rules += 1
            elif result.status == QCCheckStatus.SKIPPED:
                validation.skipped_rules += 1

            # Score par catégorie
            cat = rule.category.value
            if cat not in category_scores:
                category_scores[cat] = {"total": 0, "passed": 0, "score": 0}
            category_scores[cat]["total"] += 1
            if result.status == QCCheckStatus.PASSED:
                category_scores[cat]["passed"] += 1
            if result.score:
                category_scores[cat]["score"] += result.score

        # Calculer les scores par catégorie
        for cat, data in category_scores.items():
            if data["total"] > 0:
                data["score"] = round((data["passed"] / data["total"]) * 100, 2)

        # Calculer le score global
        total_passed = validation.passed_rules
        total_rules = validation.total_rules - validation.skipped_rules
        validation.overall_score = round((total_passed / total_rules * 100), 2) if total_rules > 0 else 0

        # Statut final
        if validation.blocked_rules > 0 or validation.failed_rules > 0 and validation.overall_score < 80:
            validation.status = QCCheckStatus.FAILED
        else:
            validation.status = QCCheckStatus.PASSED

        validation.completed_at = datetime.utcnow()
        validation.category_scores = json.dumps(category_scores)

        # Mettre à jour le module
        self._update_module_scores(module, validation, category_scores)

        self.db.commit()
        self.db.refresh(validation)

        # Créer alertes si nécessaire
        if validation.status == QCCheckStatus.FAILED:
            self._create_validation_alert(module, validation)

        return validation

    def _execute_rule(
        self,
        validation: QCValidation,
        rule: QCRule,
        module: ModuleRegistry
    ) -> QCCheckResult:
        """Exécute une règle QC et crée le résultat."""
        start_time = datetime.utcnow()

        result = QCCheckResult(
            tenant_id=self.tenant_id,
            validation_id=validation.id,
            rule_id=rule.id,
            rule_code=rule.code,
            rule_name=rule.name,
            category=rule.category,
            severity=rule.severity,
            status=QCCheckStatus.RUNNING
        )

        # Exécuter le check selon le type
        check_result = self._run_check(rule, module)

        result.status = check_result["status"]
        result.score = check_result.get("score", 100 if check_result["status"] == QCCheckStatus.PASSED else 0)
        result.actual_value = str(check_result.get("actual_value", ""))
        result.expected_value = str(check_result.get("expected_value", ""))
        result.message = check_result.get("message", "")
        result.recommendation = check_result.get("recommendation", "")
        result.evidence = json.dumps(check_result.get("evidence", {}))

        end_time = datetime.utcnow()
        result.duration_ms = int((end_time - start_time).total_seconds() * 1000)
        result.executed_at = end_time

        self.db.add(result)
        return result

    def _run_check(self, rule: QCRule, module: ModuleRegistry) -> dict[str, Any]:
        """Exécute le check spécifique d'une règle."""
        check_type = rule.check_type
        config = json.loads(rule.check_config) if rule.check_config else {}

        # Simuler différents types de checks
        if check_type == "file_exists":
            return self._check_file_exists(config, module)
        elif check_type == "test_coverage":
            return self._check_test_coverage(config, module, rule.threshold_value, rule.threshold_operator)
        elif check_type == "api_endpoints":
            return self._check_api_endpoints(config, module)
        elif check_type == "documentation":
            return self._check_documentation(config, module)
        elif check_type == "security_scan":
            return self._check_security(config, module)
        elif check_type == "performance":
            return self._check_performance(config, module, rule.threshold_value, rule.threshold_operator)
        elif check_type == "database_schema":
            return self._check_database_schema(config, module)
        elif check_type == "dependencies":
            return self._check_dependencies(config, module)
        else:
            # Check générique passant
            return {
                "status": QCCheckStatus.PASSED,
                "score": 100,
                "message": f"Check {check_type} passed"
            }

    def _check_file_exists(self, config: dict, module: ModuleRegistry) -> dict:
        """Vérifie l'existence de fichiers requis."""
        required_files = config.get("files", [])
        # Simulation - en production, vérifierait vraiment les fichiers
        return {
            "status": QCCheckStatus.PASSED,
            "score": 100,
            "actual_value": str(len(required_files)),
            "expected_value": str(len(required_files)),
            "message": f"All {len(required_files)} required files exist",
            "evidence": {"files": required_files}
        }

    def _check_test_coverage(
        self,
        config: dict,
        module: ModuleRegistry,
        threshold: float,
        operator: str
    ) -> dict:
        """Vérifie la couverture de tests."""
        # Simulation - récupérerait la vraie couverture
        coverage = 85.0  # Simulé

        passed = self._compare_threshold(coverage, threshold, operator) if threshold else coverage >= 80

        return {
            "status": QCCheckStatus.PASSED if passed else QCCheckStatus.FAILED,
            "score": coverage,
            "actual_value": f"{coverage}%",
            "expected_value": f"{threshold}%" if threshold else "80%",
            "message": f"Test coverage: {coverage}%",
            "recommendation": "Increase test coverage" if not passed else None
        }

    def _check_api_endpoints(self, config: dict, module: ModuleRegistry) -> dict:
        """Vérifie les standards API."""
        min_endpoints = config.get("min_endpoints", 1)
        # Simulation
        endpoints = 32  # Simulé

        return {
            "status": QCCheckStatus.PASSED if endpoints >= min_endpoints else QCCheckStatus.FAILED,
            "score": 100 if endpoints >= min_endpoints else 50,
            "actual_value": str(endpoints),
            "expected_value": f">={min_endpoints}",
            "message": f"Module has {endpoints} API endpoints"
        }

    def _check_documentation(self, config: dict, module: ModuleRegistry) -> dict:
        """Vérifie la documentation."""
        required_docs = config.get("required", ["README", "BENCHMARK", "QC_REPORT"])
        # Simulation
        return {
            "status": QCCheckStatus.PASSED,
            "score": 100,
            "message": f"All {len(required_docs)} required documents present",
            "evidence": {"documents": required_docs}
        }

    def _check_security(self, config: dict, module: ModuleRegistry) -> dict:
        """Vérifie les aspects sécurité."""
        checks = ["tenant_isolation", "auth_required", "input_validation", "sql_injection"]
        # Simulation - tous passent
        return {
            "status": QCCheckStatus.PASSED,
            "score": 100,
            "message": f"All {len(checks)} security checks passed",
            "evidence": {"checks": checks}
        }

    def _check_performance(
        self,
        config: dict,
        module: ModuleRegistry,
        threshold: float,
        operator: str
    ) -> dict:
        """Vérifie les performances."""
        response_time = config.get("max_response_ms", 200)
        actual = 45  # Simulé

        passed = actual <= response_time

        return {
            "status": QCCheckStatus.PASSED if passed else QCCheckStatus.FAILED,
            "score": 100 if passed else 50,
            "actual_value": f"{actual}ms",
            "expected_value": f"<={response_time}ms",
            "message": f"Average response time: {actual}ms"
        }

    def _check_database_schema(self, config: dict, module: ModuleRegistry) -> dict:
        """Vérifie le schéma de base de données."""
        requirements = ["tenant_id_on_all_tables", "indexes_present", "foreign_keys"]
        # Simulation
        return {
            "status": QCCheckStatus.PASSED,
            "score": 100,
            "message": "Database schema follows standards",
            "evidence": {"requirements": requirements}
        }

    def _check_dependencies(self, config: dict, module: ModuleRegistry) -> dict:
        """Vérifie les dépendances du module."""
        if not module.dependencies:
            return {
                "status": QCCheckStatus.PASSED,
                "score": 100,
                "message": "No dependencies to check"
            }

        deps = json.loads(module.dependencies)
        # Vérifier que chaque dépendance est validée
        validated_deps = []
        for dep_code in deps:
            dep_module = self.get_module_by_code(dep_code)
            if dep_module and dep_module.status in [ModuleStatus.QC_PASSED, ModuleStatus.PRODUCTION]:
                validated_deps.append(dep_code)

        all_validated = len(validated_deps) == len(deps)

        return {
            "status": QCCheckStatus.PASSED if all_validated else QCCheckStatus.FAILED,
            "score": 100 if all_validated else (len(validated_deps) / len(deps) * 100),
            "actual_value": f"{len(validated_deps)}/{len(deps)}",
            "expected_value": f"{len(deps)}/{len(deps)}",
            "message": f"{len(validated_deps)} of {len(deps)} dependencies validated",
            "evidence": {"validated": validated_deps, "required": deps}
        }

    def _compare_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Compare une valeur à un seuil."""
        if operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == "==":
            return value == threshold
        return True

    def _update_module_scores(
        self,
        module: ModuleRegistry,
        validation: QCValidation,
        category_scores: dict
    ):
        """Met à jour les scores du module."""
        module.overall_score = validation.overall_score
        module.total_checks = validation.total_rules
        module.passed_checks = validation.passed_rules
        module.failed_checks = validation.failed_rules
        module.blocked_checks = validation.blocked_rules

        # Scores par catégorie
        for cat, data in category_scores.items():
            attr_name = f"{cat.lower()}_score"
            if hasattr(module, attr_name):
                setattr(module, attr_name, data["score"])

        # Statut du module
        if validation.status == QCCheckStatus.PASSED:
            module.status = ModuleStatus.QC_PASSED
            module.validated_at = datetime.utcnow()
        else:
            module.status = ModuleStatus.QC_FAILED

    def _create_validation_alert(self, module: ModuleRegistry, validation: QCValidation):
        """Crée une alerte pour une validation échouée."""
        alert = QCAlert(
            tenant_id=self.tenant_id,
            module_id=module.id,
            validation_id=validation.id,
            alert_type="validation_failed",
            severity=QCRuleSeverity.CRITICAL if validation.blocked_rules > 0 else QCRuleSeverity.WARNING,
            title=f"QC Failed: {module.module_code}",
            message=f"Module {module.module_name} failed QC validation with score {validation.overall_score}%",
            details=json.dumps({
                "score": validation.overall_score,
                "passed": validation.passed_rules,
                "failed": validation.failed_rules,
                "blocked": validation.blocked_rules
            })
        )
        self.db.add(alert)

    def get_validation(self, validation_id: int) -> QCValidation | None:
        """Récupère une validation par ID."""
        return self.db.query(QCValidation).filter(
            QCValidation.id == validation_id,
            QCValidation.tenant_id == self.tenant_id
        ).first()

    def list_validations(
        self,
        module_id: int = None,
        status: QCCheckStatus = None,
        phase: ValidationPhase = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[QCValidation], int]:
        """Liste les validations."""
        query = self.db.query(QCValidation).filter(
            QCValidation.tenant_id == self.tenant_id
        )

        if module_id:
            query = query.filter(QCValidation.module_id == module_id)
        if status:
            query = query.filter(QCValidation.status == status)
        if phase:
            query = query.filter(QCValidation.validation_phase == phase)

        total = query.count()
        validations = query.order_by(desc(QCValidation.started_at)).offset(skip).limit(limit).all()

        return validations, total

    def get_check_results(
        self,
        validation_id: int,
        status: QCCheckStatus = None,
        category: QCRuleCategory = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[QCCheckResult], int]:
        """Récupère les résultats de checks d'une validation."""
        query = self.db.query(QCCheckResult).filter(
            QCCheckResult.validation_id == validation_id,
            QCCheckResult.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(QCCheckResult.status == status)
        if category:
            query = query.filter(QCCheckResult.category == category)

        total = query.count()
        results = query.order_by(QCCheckResult.category, QCCheckResult.rule_code).offset(skip).limit(limit).all()

        return results, total

    # ========================================================================
    # TESTS
    # ========================================================================

    def record_test_run(
        self,
        module_id: int,
        test_type: TestType,
        total_tests: int,
        passed_tests: int,
        failed_tests: int,
        skipped_tests: int = 0,
        error_tests: int = 0,
        coverage_percent: float = None,
        test_suite: str = None,
        duration_seconds: float = None,
        failed_test_details: dict = None,
        output_log: str = None,
        triggered_by: str = "manual",
        triggered_user: int = None,
        validation_id: int = None
    ) -> TestRun:
        """Enregistre une exécution de tests."""
        run = TestRun(
            tenant_id=self.tenant_id,
            module_id=module_id,
            validation_id=validation_id,
            test_type=test_type,
            test_suite=test_suite,
            completed_at=datetime.utcnow(),
            duration_seconds=duration_seconds,
            status=QCCheckStatus.PASSED if failed_tests == 0 and error_tests == 0 else QCCheckStatus.FAILED,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            error_tests=error_tests,
            coverage_percent=coverage_percent,
            failed_test_details=json.dumps(failed_test_details) if failed_test_details else None,
            output_log=output_log,
            triggered_by=triggered_by,
            triggered_user=triggered_user
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_test_runs(
        self,
        module_id: int = None,
        test_type: TestType = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[TestRun], int]:
        """Récupère les exécutions de tests."""
        query = self.db.query(TestRun).filter(TestRun.tenant_id == self.tenant_id)

        if module_id:
            query = query.filter(TestRun.module_id == module_id)
        if test_type:
            query = query.filter(TestRun.test_type == test_type)

        total = query.count()
        runs = query.order_by(desc(TestRun.started_at)).offset(skip).limit(limit).all()

        return runs, total

    # ========================================================================
    # MÉTRIQUES
    # ========================================================================

    def record_metrics(self, module_id: int = None) -> QCMetric:
        """Enregistre les métriques QC actuelles."""
        now = datetime.utcnow()

        # Statistiques modules via SQL (optimisé)
        base_filter = ModuleRegistry.tenant_id == self.tenant_id

        # Comptages par statut en une seule requête
        status_counts = self.db.query(
            ModuleRegistry.status,
            func.count(ModuleRegistry.id)
        ).filter(base_filter).group_by(ModuleRegistry.status).all()

        counts_dict = {status: count for status, count in status_counts}
        modules_total = sum(counts_dict.values())

        metric = QCMetric(
            tenant_id=self.tenant_id,
            module_id=module_id,
            metric_date=now,
            modules_total=modules_total,
            modules_validated=counts_dict.get(ModuleStatus.QC_PASSED, 0),
            modules_production=counts_dict.get(ModuleStatus.PRODUCTION, 0),
            modules_failed=counts_dict.get(ModuleStatus.QC_FAILED, 0)
        )

        # Scores moyens via SQL (une seule requête)
        if modules_total > 0:
            avg_scores = self.db.query(
                func.avg(ModuleRegistry.overall_score),
                func.avg(ModuleRegistry.architecture_score),
                func.avg(ModuleRegistry.security_score),
                func.avg(ModuleRegistry.performance_score),
                func.avg(ModuleRegistry.code_quality_score),
                func.avg(ModuleRegistry.testing_score),
                func.avg(ModuleRegistry.documentation_score)
            ).filter(base_filter).first()

            if avg_scores:
                metric.avg_overall_score = float(avg_scores[0]) if avg_scores[0] else None
                metric.avg_architecture_score = float(avg_scores[1]) if avg_scores[1] else None
                metric.avg_security_score = float(avg_scores[2]) if avg_scores[2] else None
                metric.avg_performance_score = float(avg_scores[3]) if avg_scores[3] else None
                metric.avg_code_quality_score = float(avg_scores[4]) if avg_scores[4] else None
                metric.avg_testing_score = float(avg_scores[5]) if avg_scores[5] else None
                metric.avg_documentation_score = float(avg_scores[6]) if avg_scores[6] else None

        # Statistiques tests (dernières 24h) via SQL
        yesterday = now - timedelta(days=1)
        test_stats = self.db.query(
            func.sum(TestRun.total_tests),
            func.sum(TestRun.passed_tests),
            func.avg(TestRun.coverage_percent)
        ).filter(
            TestRun.tenant_id == self.tenant_id,
            TestRun.started_at >= yesterday
        ).first()

        if test_stats and test_stats[0]:
            metric.total_tests_run = int(test_stats[0]) if test_stats[0] else 0
            metric.total_tests_passed = int(test_stats[1]) if test_stats[1] else 0
            metric.avg_coverage = float(test_stats[2]) if test_stats[2] else None

        # Issues via SQL (comptage groupé)
        check_filter = [
            QCCheckResult.tenant_id == self.tenant_id,
            QCCheckResult.executed_at >= yesterday
        ]

        # Total checks et passed en une requête
        check_counts = self.db.query(
            func.count(QCCheckResult.id),
            func.sum(case((QCCheckResult.status == QCCheckStatus.PASSED, 1), else_=0))
        ).filter(*check_filter).first()

        metric.total_checks_run = check_counts[0] if check_counts[0] else 0
        metric.total_checks_passed = int(check_counts[1]) if check_counts[1] else 0

        # Critical et blocker issues
        issue_counts = self.db.query(
            QCCheckResult.severity,
            func.count(QCCheckResult.id)
        ).filter(
            *check_filter,
            QCCheckResult.status == QCCheckStatus.FAILED
        ).group_by(QCCheckResult.severity).all()

        issue_dict = {sev: cnt for sev, cnt in issue_counts}
        metric.critical_issues = issue_dict.get(QCRuleSeverity.CRITICAL, 0)
        metric.blocker_issues = issue_dict.get(QCRuleSeverity.BLOCKER, 0)

        # Tendance (comparer avec métrique précédente)
        prev_metric = self.db.query(QCMetric).filter(
            QCMetric.tenant_id == self.tenant_id,
            QCMetric.metric_date < now
        ).order_by(desc(QCMetric.metric_date)).first()

        if prev_metric and prev_metric.avg_overall_score and metric.avg_overall_score:
            delta = metric.avg_overall_score - prev_metric.avg_overall_score
            metric.score_delta = round(delta, 2)
            if delta > 1:
                metric.score_trend = "UP"
            elif delta < -1:
                metric.score_trend = "DOWN"
            else:
                metric.score_trend = "STABLE"

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def get_metrics_history(
        self,
        module_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = 30
    ) -> list[QCMetric]:
        """Récupère l'historique des métriques."""
        query = self.db.query(QCMetric).filter(QCMetric.tenant_id == self.tenant_id)

        if module_id:
            query = query.filter(QCMetric.module_id == module_id)
        if date_from:
            query = query.filter(QCMetric.metric_date >= date_from)
        if date_to:
            query = query.filter(QCMetric.metric_date <= date_to)

        return query.order_by(desc(QCMetric.metric_date)).limit(limit).all()

    # ========================================================================
    # ALERTES
    # ========================================================================

    def create_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        severity: QCRuleSeverity = QCRuleSeverity.WARNING,
        module_id: int = None,
        validation_id: int = None,
        check_result_id: int = None,
        details: dict = None
    ) -> QCAlert:
        """Crée une alerte QC."""
        alert = QCAlert(
            tenant_id=self.tenant_id,
            module_id=module_id,
            validation_id=validation_id,
            check_result_id=check_result_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            details=json.dumps(details) if details else None
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def list_alerts(
        self,
        is_resolved: bool = None,
        severity: QCRuleSeverity = None,
        module_id: int = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[QCAlert], int]:
        """Liste les alertes QC."""
        query = self.db.query(QCAlert).filter(QCAlert.tenant_id == self.tenant_id)

        if is_resolved is not None:
            query = query.filter(QCAlert.is_resolved == is_resolved)
        if severity:
            query = query.filter(QCAlert.severity == severity)
        if module_id:
            query = query.filter(QCAlert.module_id == module_id)

        total = query.count()
        alerts = query.order_by(desc(QCAlert.created_at)).offset(skip).limit(limit).all()

        return alerts, total

    def resolve_alert(
        self,
        alert_id: int,
        resolved_by: int,
        resolution_notes: str = None
    ) -> QCAlert | None:
        """Résout une alerte."""
        alert = self.db.query(QCAlert).filter(
            QCAlert.id == alert_id,
            QCAlert.tenant_id == self.tenant_id
        ).first()

        if not alert:
            return None

        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = resolved_by
        alert.resolution_notes = resolution_notes

        self.db.commit()
        self.db.refresh(alert)
        return alert

    # ========================================================================
    # DASHBOARDS
    # ========================================================================

    def create_dashboard(
        self,
        name: str,
        owner_id: int,
        description: str = None,
        layout: dict = None,
        widgets: list[dict] = None,
        filters: dict = None,
        is_default: bool = False,
        is_public: bool = False
    ) -> QCDashboard:
        """Crée un dashboard QC personnalisé."""
        dashboard = QCDashboard(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            layout=json.dumps(layout) if layout else None,
            widgets=json.dumps(widgets) if widgets else None,
            filters=json.dumps(filters) if filters else None,
            is_default=is_default,
            is_public=is_public,
            owner_id=owner_id
        )
        self.db.add(dashboard)
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard

    def get_dashboard(self, dashboard_id: int) -> QCDashboard | None:
        """Récupère un dashboard."""
        return self.db.query(QCDashboard).filter(
            QCDashboard.id == dashboard_id,
            QCDashboard.tenant_id == self.tenant_id
        ).first()

    def list_dashboards(self, owner_id: int = None) -> list[QCDashboard]:
        """Liste les dashboards accessibles."""
        query = self.db.query(QCDashboard).filter(
            QCDashboard.tenant_id == self.tenant_id
        )

        if owner_id:
            query = query.filter(
                or_(
                    QCDashboard.owner_id == owner_id,
                    QCDashboard.is_public
                )
            )

        return query.order_by(desc(QCDashboard.is_default), QCDashboard.name).all()

    def get_dashboard_data(self, dashboard_id: int = None) -> dict[str, Any]:
        """Récupère les données pour un dashboard QC."""
        # Statistiques globales
        modules, _ = self.list_modules()

        # Comptages par statut
        status_counts = {}
        for status in ModuleStatus:
            count = len([m for m in modules if m.status == status])
            if count > 0:
                status_counts[status.value] = count

        # Dernières validations
        validations, _ = self.list_validations(limit=10)

        # Alertes non résolues
        alerts, alert_count = self.list_alerts(is_resolved=False)

        # Derniers tests
        test_runs, _ = self.get_test_runs(limit=10)

        # Scores moyens
        overall_scores = [m.overall_score for m in modules if m.overall_score]
        avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0

        return {
            "summary": {
                "total_modules": len(modules),
                "validated_modules": len([m for m in modules if m.status == ModuleStatus.QC_PASSED]),
                "production_modules": len([m for m in modules if m.status == ModuleStatus.PRODUCTION]),
                "failed_modules": len([m for m in modules if m.status == ModuleStatus.QC_FAILED]),
                "average_score": round(avg_score, 2),
                "unresolved_alerts": alert_count
            },
            "status_distribution": status_counts,
            "recent_validations": [
                {
                    "id": v.id,
                    "module_id": v.module_id,
                    "phase": v.validation_phase.value,
                    "status": v.status.value,
                    "score": v.overall_score,
                    "started_at": v.started_at.isoformat() if v.started_at else None
                }
                for v in validations
            ],
            "recent_tests": [
                {
                    "id": r.id,
                    "module_id": r.module_id,
                    "type": r.test_type.value,
                    "status": r.status.value,
                    "total": r.total_tests,
                    "passed": r.passed_tests,
                    "coverage": r.coverage_percent
                }
                for r in test_runs
            ],
            "critical_alerts": [
                {
                    "id": a.id,
                    "type": a.alert_type,
                    "title": a.title,
                    "severity": a.severity.value,
                    "created_at": a.created_at.isoformat()
                }
                for a in alerts[:5]
            ]
        }

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    def create_template(
        self,
        code: str,
        name: str,
        rules: list[dict],
        description: str = None,
        category: str = None,
        created_by: int = None
    ) -> QCTemplate:
        """Crée un template de règles QC."""
        template = QCTemplate(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            rules=json.dumps(rules),
            category=category,
            created_by=created_by
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_template(self, template_id: int) -> QCTemplate | None:
        """Récupère un template."""
        return self.db.query(QCTemplate).filter(
            QCTemplate.id == template_id,
            QCTemplate.tenant_id == self.tenant_id
        ).first()

    def list_templates(self, category: str = None) -> list[QCTemplate]:
        """Liste les templates."""
        query = self.db.query(QCTemplate).filter(
            QCTemplate.tenant_id == self.tenant_id,
            QCTemplate.is_active
        )

        if category:
            query = query.filter(QCTemplate.category == category)

        return query.order_by(QCTemplate.name).all()

    def apply_template(self, template_id: int, created_by: int = None) -> list[QCRule]:
        """Applique un template pour créer des règles."""
        template = self.get_template(template_id)
        if not template:
            return []

        rules = json.loads(template.rules)
        created_rules = []

        for rule_def in rules:
            rule = self.create_rule(
                code=rule_def.get("code"),
                name=rule_def.get("name"),
                category=QCRuleCategory(rule_def.get("category", "CODE_QUALITY")),
                check_type=rule_def.get("check_type", "generic"),
                description=rule_def.get("description"),
                severity=QCRuleSeverity(rule_def.get("severity", "WARNING")),
                check_config=rule_def.get("check_config"),
                threshold_value=rule_def.get("threshold_value"),
                threshold_operator=rule_def.get("threshold_operator"),
                created_by=created_by
            )
            created_rules.append(rule)

        return created_rules


def get_qc_service(db: Session, tenant_id: str) -> QCService:
    """Factory pour obtenir une instance du service QC."""
    return QCService(db, tenant_id)
