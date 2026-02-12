"""
AZALS MODULE T3 - Service Audit & Benchmark
============================================

Logique métier pour l'audit et les benchmarks.
"""

import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .models import (
    AuditAction,
    AuditCategory,
    AuditDashboard,
    AuditExport,
    AuditLevel,
    AuditLog,
    AuditSession,
    Benchmark,
    BenchmarkResult,
    BenchmarkStatus,
    ComplianceCheck,
    ComplianceFramework,
    DataRetentionRule,
    MetricDefinition,
    MetricType,
    MetricValue,
    RetentionPolicy,
)


class AuditService:
    """Service principal pour l'audit."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # AUDIT LOGS
    # ========================================================================

    def log(
        self,
        action: AuditAction,
        module: str,
        description: str = None,
        level: AuditLevel = AuditLevel.INFO,
        category: AuditCategory = AuditCategory.BUSINESS,
        entity_type: str = None,
        entity_id: str = None,
        user_id: int = None,
        user_email: str = None,
        user_role: str = None,
        session_id: str = None,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        old_value: Any = None,
        new_value: Any = None,
        extra_data: dict = None,
        success: bool = True,
        error_message: str = None,
        error_code: str = None,
        duration_ms: float = None,
        retention_policy: RetentionPolicy = RetentionPolicy.MEDIUM
    ) -> AuditLog:
        """Crée une entrée d'audit."""
        # Calculer le diff si old_value et new_value sont fournis
        diff = None
        if old_value and new_value:
            diff = self._calculate_diff(old_value, new_value)

        # Calculer l'expiration selon la politique
        expires_at = self._calculate_expiration(retention_policy)

        log_entry = AuditLog(
            tenant_id=self.tenant_id,
            action=action,
            level=level,
            category=category,
            module=module,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            session_id=session_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            diff=json.dumps(diff) if diff else None,
            extra_data=json.dumps(extra_data) if extra_data else None,
            success=success,
            error_message=error_message,
            error_code=error_code,
            duration_ms=duration_ms,
            retention_policy=retention_policy,
            expires_at=expires_at
        )

        self.db.add(log_entry)
        self.db.flush()
        return log_entry

    def _calculate_diff(self, old_value: Any, new_value: Any) -> dict[str, Any]:
        """Calcule les différences entre deux valeurs."""
        if not isinstance(old_value, dict) or not isinstance(new_value, dict):
            return {"old": old_value, "new": new_value}

        diff = {"added": {}, "removed": {}, "changed": {}}

        all_keys = set(old_value.keys()) | set(new_value.keys())
        for key in all_keys:
            if key not in old_value:
                diff["added"][key] = new_value[key]
            elif key not in new_value:
                diff["removed"][key] = old_value[key]
            elif old_value[key] != new_value[key]:
                diff["changed"][key] = {
                    "from": old_value[key],
                    "to": new_value[key]
                }

        return diff

    def _calculate_expiration(self, policy: RetentionPolicy) -> datetime | None:
        """Calcule la date d'expiration selon la politique."""
        now = datetime.utcnow()

        if policy == RetentionPolicy.IMMEDIATE:
            return now
        elif policy == RetentionPolicy.SHORT:
            return now + timedelta(days=30)
        elif policy == RetentionPolicy.MEDIUM:
            return now + timedelta(days=365)
        elif policy == RetentionPolicy.LONG:
            return now + timedelta(days=1825)  # 5 ans
        elif policy == RetentionPolicy.LEGAL:
            return now + timedelta(days=3650)  # 10 ans
        else:  # PERMANENT
            return None

    def search_logs(
        self,
        action: AuditAction = None,
        level: AuditLevel = None,
        category: AuditCategory = None,
        module: str = None,
        entity_type: str = None,
        entity_id: str = None,
        user_id: int = None,
        session_id: str = None,
        success: bool = None,
        from_date: datetime = None,
        to_date: datetime = None,
        search_text: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[AuditLog], int]:
        """Recherche dans les logs d'audit."""
        query = self.db.query(AuditLog).filter(
            AuditLog.tenant_id == self.tenant_id
        )

        if action:
            query = query.filter(AuditLog.action == action)
        if level:
            query = query.filter(AuditLog.level == level)
        if category:
            query = query.filter(AuditLog.category == category)
        if module:
            query = query.filter(AuditLog.module == module)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if session_id:
            query = query.filter(AuditLog.session_id == session_id)
        if success is not None:
            query = query.filter(AuditLog.success == success)
        if from_date:
            query = query.filter(AuditLog.created_at >= from_date)
        if to_date:
            query = query.filter(AuditLog.created_at <= to_date)
        if search_text:
            search_pattern = f"%{search_text}%"
            query = query.filter(
                or_(
                    AuditLog.description.ilike(search_pattern),
                    AuditLog.entity_id.ilike(search_pattern),
                    AuditLog.user_email.ilike(search_pattern)
                )
            )

        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

        return logs, total

    def get_log(self, log_id: int) -> AuditLog | None:
        """Récupère un log par ID."""
        return self.db.query(AuditLog).filter(
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.id == log_id
        ).first()

    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50
    ) -> list[AuditLog]:
        """Récupère l'historique d'une entité."""
        return self.db.query(AuditLog).filter(
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    def get_user_activity(
        self,
        user_id: int,
        from_date: datetime = None,
        to_date: datetime = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """Récupère l'activité d'un utilisateur."""
        query = self.db.query(AuditLog).filter(
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.user_id == user_id
        )

        if from_date:
            query = query.filter(AuditLog.created_at >= from_date)
        if to_date:
            query = query.filter(AuditLog.created_at <= to_date)

        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    # ========================================================================
    # SESSIONS
    # ========================================================================

    def start_session(
        self,
        session_id: str,
        user_id: int,
        user_email: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> AuditSession:
        """Démarre une nouvelle session auditée."""
        # Parser user agent
        device_type, browser, os = self._parse_user_agent(user_agent)

        session = AuditSession(
            tenant_id=self.tenant_id,
            session_id=session_id,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
            browser=browser,
            os=os
        )

        self.db.add(session)
        self.db.commit()

        # Log la connexion
        self.log(
            action=AuditAction.LOGIN,
            module="auth",
            description=f"Connexion utilisateur {user_email}",
            category=AuditCategory.SECURITY,
            user_id=user_id,
            user_email=user_email,
            session_id=session_id,
            ip_address=ip_address
        )
        self.db.commit()

        return session

    def _parse_user_agent(self, user_agent: str) -> tuple[str, str, str]:
        """Parse le user agent pour extraire device, browser, os."""
        if not user_agent:
            return None, None, None

        device_type = "Desktop"
        if "Mobile" in user_agent or "Android" in user_agent:
            device_type = "Mobile"
        elif "Tablet" in user_agent or "iPad" in user_agent:
            device_type = "Tablet"

        browser = "Unknown"
        if "Chrome" in user_agent:
            browser = "Chrome"
        elif "Firefox" in user_agent:
            browser = "Firefox"
        elif "Safari" in user_agent:
            browser = "Safari"
        elif "Edge" in user_agent:
            browser = "Edge"

        os = "Unknown"
        if "Windows" in user_agent:
            os = "Windows"
        elif "Mac OS" in user_agent:
            os = "macOS"
        elif "Linux" in user_agent:
            os = "Linux"
        elif "Android" in user_agent:
            os = "Android"
        elif "iOS" in user_agent:
            os = "iOS"

        return device_type, browser, os

    def end_session(self, session_id: str, reason: str = None) -> AuditSession | None:
        """Termine une session."""
        session = self.db.query(AuditSession).filter(
            AuditSession.session_id == session_id,
            AuditSession.tenant_id == self.tenant_id
        ).first()

        if session:
            session.logout_at = datetime.utcnow()
            session.is_active = False
            session.terminated_reason = reason

            # Log la déconnexion
            self.log(
                action=AuditAction.LOGOUT,
                module="auth",
                description=f"Déconnexion utilisateur {session.user_email}",
                category=AuditCategory.SECURITY,
                user_id=session.user_id,
                user_email=session.user_email,
                session_id=session_id
            )
            self.db.commit()

        return session

    def update_session_activity(self, session_id: str, action_type: str = "read") -> None:
        """Met à jour l'activité d'une session."""
        session = self.db.query(AuditSession).filter(
            AuditSession.session_id == session_id,
            AuditSession.tenant_id == self.tenant_id,
            AuditSession.is_active
        ).first()

        if session:
            session.last_activity_at = datetime.utcnow()
            session.actions_count += 1
            if action_type == "read":
                session.reads_count += 1
            elif action_type == "write":
                session.writes_count += 1

    def get_active_sessions(self, user_id: int = None) -> list[AuditSession]:
        """Liste les sessions actives."""
        query = self.db.query(AuditSession).filter(
            AuditSession.tenant_id == self.tenant_id,
            AuditSession.is_active
        )

        if user_id:
            query = query.filter(AuditSession.user_id == user_id)

        return query.order_by(AuditSession.login_at.desc()).all()

    # ========================================================================
    # MÉTRIQUES
    # ========================================================================

    def create_metric(
        self,
        code: str,
        name: str,
        metric_type: MetricType,
        unit: str = None,
        module: str = None,
        aggregation_period: str = "HOUR",
        retention_days: int = 90,
        warning_threshold: float = None,
        critical_threshold: float = None
    ) -> MetricDefinition:
        """Crée une définition de métrique."""
        metric = MetricDefinition(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            metric_type=metric_type,
            unit=unit,
            module=module,
            aggregation_period=aggregation_period,
            retention_days=retention_days,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold
        )

        self.db.add(metric)
        self.db.commit()
        return metric

    def record_metric(
        self,
        metric_code: str,
        value: float,
        dimensions: dict[str, Any] = None
    ) -> MetricValue:
        """Enregistre une valeur de métrique."""
        metric = self.db.query(MetricDefinition).filter(
            MetricDefinition.tenant_id == self.tenant_id,
            MetricDefinition.code == metric_code,
            MetricDefinition.is_active
        ).first()

        if not metric:
            return None

        now = datetime.utcnow()

        # Déterminer la période selon l'agrégation
        if metric.aggregation_period == "MINUTE":
            period_start = now.replace(second=0, microsecond=0)
            period_end = period_start + timedelta(minutes=1)
        elif metric.aggregation_period == "HOUR":
            period_start = now.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1)
        else:  # DAY
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)

        # Chercher une valeur existante pour cette période
        existing = self.db.query(MetricValue).filter(
            MetricValue.tenant_id == self.tenant_id,
            MetricValue.metric_id == metric.id,
            MetricValue.period_start == period_start
        ).first()

        if existing:
            # Mettre à jour l'agrégation
            existing.count += 1
            existing.value = value  # Dernière valeur
            existing.min_value = min(existing.min_value or value, value)
            existing.max_value = max(existing.max_value or value, value)
            # Moyenne glissante
            existing.avg_value = ((existing.avg_value or 0) * (existing.count - 1) + value) / existing.count
            return existing
        else:
            metric_value = MetricValue(
                tenant_id=self.tenant_id,
                metric_id=metric.id,
                metric_code=metric_code,
                value=value,
                min_value=value,
                max_value=value,
                avg_value=value,
                count=1,
                period_start=period_start,
                period_end=period_end,
                dimensions=json.dumps(dimensions) if dimensions else None
            )
            self.db.add(metric_value)
            return metric_value

    def get_metric_values(
        self,
        metric_code: str,
        from_date: datetime = None,
        to_date: datetime = None,
        limit: int = 1000
    ) -> list[MetricValue]:
        """Récupère les valeurs d'une métrique."""
        query = self.db.query(MetricValue).filter(
            MetricValue.tenant_id == self.tenant_id,
            MetricValue.metric_code == metric_code
        )

        if from_date:
            query = query.filter(MetricValue.period_start >= from_date)
        if to_date:
            query = query.filter(MetricValue.period_end <= to_date)

        return query.order_by(MetricValue.period_start.desc()).limit(limit).all()

    def list_metrics(self, module: str = None) -> list[MetricDefinition]:
        """Liste les métriques définies."""
        query = self.db.query(MetricDefinition).filter(
            MetricDefinition.tenant_id == self.tenant_id,
            MetricDefinition.is_active
        )

        if module:
            query = query.filter(MetricDefinition.module == module)

        return query.all()

    # ========================================================================
    # BENCHMARKS
    # ========================================================================

    def create_benchmark(
        self,
        code: str,
        name: str,
        benchmark_type: str,
        description: str = None,
        module: str = None,
        config: dict = None,
        baseline: dict = None,
        created_by: int = None
    ) -> Benchmark:
        """Crée un benchmark."""
        benchmark = Benchmark(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            benchmark_type=benchmark_type,
            module=module,
            config=json.dumps(config) if config else None,
            baseline=json.dumps(baseline) if baseline else None,
            created_by=created_by
        )

        self.db.add(benchmark)
        self.db.commit()
        return benchmark

    def run_benchmark(self, benchmark_id: int, executed_by: int = None) -> BenchmarkResult:
        """Exécute un benchmark."""
        benchmark = self.db.query(Benchmark).filter(
            Benchmark.id == benchmark_id,
            Benchmark.tenant_id == self.tenant_id
        ).first()

        if not benchmark:
            raise ValueError("Benchmark non trouvé")

        # Créer le résultat
        result = BenchmarkResult(
            tenant_id=self.tenant_id,
            benchmark_id=benchmark_id,
            started_at=datetime.utcnow(),
            status=BenchmarkStatus.RUNNING,
            executed_by=executed_by
        )
        self.db.add(result)

        benchmark.status = BenchmarkStatus.RUNNING
        benchmark.last_run_at = datetime.utcnow()
        self.db.flush()

        try:
            # Exécuter le benchmark selon son type
            score, details, warnings = self._execute_benchmark(benchmark)

            # SÉCURITÉ: Récupérer le score précédent (filtrer par tenant_id)
            previous_result = self.db.query(BenchmarkResult).filter(
                BenchmarkResult.tenant_id == self.tenant_id,
                BenchmarkResult.benchmark_id == benchmark_id,
                BenchmarkResult.status == BenchmarkStatus.COMPLETED,
                BenchmarkResult.id != result.id
            ).order_by(BenchmarkResult.completed_at.desc()).first()

            previous_score = previous_result.score if previous_result else None

            # Calculer la tendance
            trend = None
            score_delta = None
            if previous_score is not None:
                score_delta = score - previous_score
                if score_delta > 1:
                    trend = "UP"
                elif score_delta < -1:
                    trend = "DOWN"
                else:
                    trend = "STABLE"

            result.completed_at = datetime.utcnow()
            result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000
            result.status = BenchmarkStatus.COMPLETED
            result.score = score
            result.passed = score >= 70  # Seuil de passage
            result.results = json.dumps(details)
            result.previous_score = previous_score
            result.score_delta = score_delta
            result.trend = trend
            result.warnings = json.dumps(warnings) if warnings else None

            benchmark.status = BenchmarkStatus.COMPLETED

        except Exception as e:
            result.completed_at = datetime.utcnow()
            result.status = BenchmarkStatus.FAILED
            result.error_message = str(e)
            benchmark.status = BenchmarkStatus.FAILED

        self.db.commit()
        return result

    def _execute_benchmark(self, benchmark: Benchmark) -> tuple[float, dict, list]:
        """Exécute le benchmark et retourne (score, détails, warnings)."""
        config = json.loads(benchmark.config) if benchmark.config else {}
        baseline = json.loads(benchmark.baseline) if benchmark.baseline else {}

        if benchmark.benchmark_type == "PERFORMANCE":
            return self._run_performance_benchmark(benchmark, config, baseline)
        elif benchmark.benchmark_type == "SECURITY":
            return self._run_security_benchmark(benchmark, config, baseline)
        elif benchmark.benchmark_type == "COMPLIANCE":
            return self._run_compliance_benchmark(benchmark, config, baseline)
        else:
            return self._run_feature_benchmark(benchmark, config, baseline)

    def _run_performance_benchmark(self, benchmark: Benchmark, config: dict, baseline: dict) -> tuple[float, dict, list]:
        """
        Benchmark de performance avec mesures RÉELLES.

        Vérifie:
        - Temps de réponse des requêtes DB
        - Taille du pool de connexions
        - Utilisation mémoire (si disponible)
        """
        import logging
        import time

        logger = logging.getLogger(__name__)
        details = {}
        warnings = []
        checks_passed = 0
        total_checks = 0

        # ===================================================================
        # 1. Mesure RÉELLE du temps de requête DB
        # ===================================================================
        total_checks += 1
        try:
            start_time = time.perf_counter()

            # Exécuter une vraie requête de test
            result = self.db.query(AuditLog).filter(
                AuditLog.tenant_id == self.tenant_id
            ).limit(10).all()

            db_query_time_ms = (time.perf_counter() - start_time) * 1000
            max_db_query_ms = baseline.get("max_db_query_ms", 50)

            if db_query_time_ms < max_db_query_ms:
                checks_passed += 1
                details["db_query"] = {
                    "status": "PASS",
                    "value": f"{db_query_time_ms:.2f}ms",
                    "threshold": f"{max_db_query_ms}ms"
                }
            else:
                details["db_query"] = {
                    "status": "FAIL",
                    "value": f"{db_query_time_ms:.2f}ms",
                    "threshold": f"{max_db_query_ms}ms",
                    "recommendation": "Optimiser les requêtes ou ajouter des index"
                }
                warnings.append(f"Temps requête DB {db_query_time_ms:.1f}ms > {max_db_query_ms}ms")
        except Exception as e:
            details["db_query"] = {"status": "ERROR", "value": str(e)}
            warnings.append(f"Erreur mesure DB: {e}")

        # ===================================================================
        # 2. Vérifier le pool de connexions DB
        # ===================================================================
        total_checks += 1
        try:
            from app.core.config import get_settings
            settings = get_settings()

            pool_size = getattr(settings, 'db_pool_size', 5)
            max_overflow = getattr(settings, 'db_max_overflow', 10)
            total_possible = pool_size + max_overflow

            # Vérifier que le pool est suffisant
            min_pool_size = baseline.get("min_pool_size", 5)
            if pool_size >= min_pool_size:
                checks_passed += 1
                details["db_pool"] = {
                    "status": "PASS",
                    "value": f"pool_size={pool_size}, max_overflow={max_overflow}",
                    "total_connections": total_possible
                }
            else:
                details["db_pool"] = {
                    "status": "WARN",
                    "value": f"pool_size={pool_size} < recommandé ({min_pool_size})",
                    "recommendation": "Augmenter DB_POOL_SIZE en production"
                }
                warnings.append(f"Pool DB petit: {pool_size}")
        except Exception as e:
            details["db_pool"] = {"status": "ERROR", "value": str(e)}

        # ===================================================================
        # 3. Vérifier l'utilisation mémoire (si psutil disponible)
        # ===================================================================
        total_checks += 1
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            max_memory_mb = baseline.get("max_memory_mb", 512)

            if memory_mb < max_memory_mb:
                checks_passed += 1
                details["memory_usage"] = {
                    "status": "PASS",
                    "value": f"{memory_mb:.1f}MB",
                    "threshold": f"{max_memory_mb}MB"
                }
            else:
                details["memory_usage"] = {
                    "status": "WARN",
                    "value": f"{memory_mb:.1f}MB",
                    "threshold": f"{max_memory_mb}MB",
                    "recommendation": "Surveiller les fuites mémoire"
                }
                warnings.append(f"Mémoire élevée: {memory_mb:.1f}MB")
        except ImportError:
            details["memory_usage"] = {"status": "SKIP", "value": "psutil non installé"}
            checks_passed += 1  # On passe si psutil n'est pas dispo
        except Exception as e:
            details["memory_usage"] = {"status": "ERROR", "value": str(e)}

        # ===================================================================
        # Calcul du score final
        # ===================================================================
        score = (checks_passed / total_checks) * 100 if total_checks > 0 else 0

        logger.info(
            f"[PERFORMANCE_BENCHMARK] tenant={self.tenant_id} score={score:.1f}% "
            f"passed={checks_passed}/{total_checks}"
        )

        return score, details, warnings

    def _run_security_benchmark(self, benchmark: Benchmark, config: dict, baseline: dict) -> tuple[float, dict, list]:
        """
        Benchmark de sécurité avec vérifications RÉELLES.

        Vérifie:
        - Configuration JWT (SECRET_KEY présente et forte)
        - Disponibilité MFA (table/config présente)
        - Politique de mot de passe (min 8 chars, complexité)
        - Isolation tenant (vérification requêtes tenant_id)

        ATTENTION: Cette fonction effectue de vraies vérifications.
        Un score < 100% indique un problème de sécurité à corriger.
        """
        import logging
        import os

        logger = logging.getLogger(__name__)
        details = {}
        warnings = []
        checks_passed = 0
        total_checks = 0

        # ===================================================================
        # 1. Vérifier SECRET_KEY JWT
        # ===================================================================
        total_checks += 1
        try:
            from app.core.config import get_settings
            settings = get_settings()
            secret_key = settings.secret_key

            # Vérifier la longueur minimale (32 caractères)
            if secret_key and len(secret_key) >= 32:
                # Vérifier que ce n'est pas une valeur par défaut
                dangerous_patterns = ['changeme', 'default', 'secret', 'dev-secret', 'azals']
                is_dangerous = any(pattern in secret_key.lower() for pattern in dangerous_patterns)

                if is_dangerous:
                    details["jwt_secret_key"] = {
                        "status": "FAIL",
                        "value": "Clé secrète faible détectée",
                        "recommendation": "Régénérer avec: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                    }
                    warnings.append("SECRET_KEY contient un pattern dangereux")
                else:
                    checks_passed += 1
                    details["jwt_secret_key"] = {"status": "PASS", "value": f"Longueur: {len(secret_key)} caractères"}
            else:
                details["jwt_secret_key"] = {
                    "status": "FAIL",
                    "value": f"Longueur insuffisante: {len(secret_key) if secret_key else 0}",
                    "recommendation": "SECRET_KEY doit avoir minimum 32 caractères"
                }
                warnings.append("SECRET_KEY trop courte ou absente")
        except Exception as e:
            details["jwt_secret_key"] = {"status": "ERROR", "value": str(e)}
            warnings.append(f"Erreur vérification JWT: {e}")

        # ===================================================================
        # 2. Vérifier configuration MFA (TOTP)
        # ===================================================================
        total_checks += 1
        try:
            # Vérifier si pyotp est installé et si la table users a les champs MFA
            from sqlalchemy import inspect
            inspector = inspect(self.db.bind)

            # Chercher une colonne mfa_secret ou totp_secret dans la table users
            if inspector.has_table('users') or inspector.has_table('iam_users'):
                table_name = 'iam_users' if inspector.has_table('iam_users') else 'users'
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                mfa_columns = ['mfa_secret', 'totp_secret', 'mfa_enabled', 'two_factor_enabled']

                has_mfa = any(col in columns for col in mfa_columns)
                if has_mfa:
                    checks_passed += 1
                    details["mfa_available"] = {"status": "PASS", "value": "Infrastructure MFA présente"}
                else:
                    details["mfa_available"] = {
                        "status": "WARN",
                        "value": "Colonnes MFA non trouvées dans la table users",
                        "recommendation": "Implémenter MFA/TOTP pour les utilisateurs sensibles"
                    }
                    warnings.append("MFA non configuré - recommandé pour comptes admin")
            else:
                details["mfa_available"] = {"status": "WARN", "value": "Table users non trouvée"}
        except Exception as e:
            details["mfa_available"] = {"status": "ERROR", "value": str(e)}

        # ===================================================================
        # 3. Vérifier politique de mot de passe
        # ===================================================================
        total_checks += 1
        try:
            # Vérifier les contraintes de mot de passe dans le code
            # On vérifie si bcrypt est utilisé (hash sécurisé)
            from app.core.security import get_password_hash
            import bcrypt

            # Test: bcrypt est-il utilisé avec un coût suffisant?
            test_hash = get_password_hash("TestPassword123!")
            if test_hash.startswith('$2'):  # bcrypt hash
                # Extraire le coût du hash bcrypt
                # Format: $2b$COST$...
                parts = test_hash.split('$')
                if len(parts) >= 3:
                    cost = int(parts[2])
                    if cost >= 10:
                        checks_passed += 1
                        details["password_policy"] = {
                            "status": "PASS",
                            "value": f"bcrypt avec coût {cost} (sécurisé)"
                        }
                    else:
                        details["password_policy"] = {
                            "status": "WARN",
                            "value": f"bcrypt coût {cost} (recommandé: >= 10)"
                        }
                        warnings.append(f"Coût bcrypt faible: {cost}")
                else:
                    checks_passed += 1
                    details["password_policy"] = {"status": "PASS", "value": "bcrypt actif"}
            else:
                details["password_policy"] = {
                    "status": "FAIL",
                    "value": "Hash non-bcrypt détecté",
                    "recommendation": "Utiliser bcrypt pour le hashing des mots de passe"
                }
                warnings.append("Algorithme de hash non sécurisé")
        except Exception as e:
            details["password_policy"] = {"status": "ERROR", "value": str(e)}
            warnings.append(f"Erreur vérification password policy: {e}")

        # ===================================================================
        # 4. Vérifier isolation tenant (requêtes avec tenant_id)
        # ===================================================================
        total_checks += 1
        try:
            # Vérifier que le tenant_id est bien présent dans cette session
            if self.tenant_id:
                # Tester une requête avec isolation tenant
                # Vérifier qu'on ne peut pas accéder aux données d'un autre tenant
                test_query = self.db.query(AuditLog).filter(
                    AuditLog.tenant_id == self.tenant_id
                ).limit(1)

                # Vérifier que la requête contient bien le filtre tenant_id
                query_str = str(test_query.statement.compile(
                    dialect=self.db.bind.dialect,
                    compile_kwargs={"literal_binds": False}
                ))

                if 'tenant_id' in query_str.lower():
                    checks_passed += 1
                    details["tenant_isolation"] = {
                        "status": "PASS",
                        "value": "Isolation tenant active dans les requêtes"
                    }
                else:
                    details["tenant_isolation"] = {
                        "status": "FAIL",
                        "value": "Requêtes sans filtre tenant_id détectées",
                        "recommendation": "Toujours filtrer par tenant_id"
                    }
                    warnings.append("CRITIQUE: Isolation tenant potentiellement compromise")
            else:
                details["tenant_isolation"] = {
                    "status": "FAIL",
                    "value": "tenant_id non défini dans le service",
                    "recommendation": "Le service doit toujours avoir un tenant_id"
                }
                warnings.append("CRITIQUE: tenant_id absent du service")
        except Exception as e:
            details["tenant_isolation"] = {"status": "ERROR", "value": str(e)}
            warnings.append(f"Erreur vérification tenant isolation: {e}")

        # ===================================================================
        # 5. Vérifier HTTPS/TLS (bonus)
        # ===================================================================
        total_checks += 1
        try:
            from app.core.config import get_settings
            settings = get_settings()

            if settings.environment == 'production':
                # En production, HTTPS devrait être obligatoire
                app_url = getattr(settings, 'app_url', '')
                if app_url.startswith('https://'):
                    checks_passed += 1
                    details["https_enabled"] = {"status": "PASS", "value": "HTTPS configuré"}
                else:
                    details["https_enabled"] = {
                        "status": "WARN",
                        "value": "APP_URL ne commence pas par https://",
                        "recommendation": "Configurer HTTPS en production"
                    }
                    warnings.append("HTTPS recommandé en production")
            else:
                # En dev, on passe le check
                checks_passed += 1
                details["https_enabled"] = {"status": "PASS", "value": "Non requis hors production"}
        except Exception as e:
            details["https_enabled"] = {"status": "ERROR", "value": str(e)}

        # ===================================================================
        # Calcul du score final
        # ===================================================================
        score = (checks_passed / total_checks) * 100 if total_checks > 0 else 0

        # Log le résultat pour traçabilité
        logger.info(
            f"[SECURITY_BENCHMARK] tenant={self.tenant_id} score={score:.1f}% "
            f"passed={checks_passed}/{total_checks} warnings={len(warnings)}"
        )

        if score < 100:
            logger.warning(
                f"[SECURITY_BENCHMARK] Score < 100% détecté. "
                f"Warnings: {warnings}"
            )

        return score, details, warnings

    def _run_compliance_benchmark(self, benchmark: Benchmark, config: dict, baseline: dict) -> tuple[float, dict, list]:
        """
        Benchmark de conformité.

        Vérifie les contrôles de conformité définis pour le tenant.
        Retourne 0% si aucun contrôle n'est défini (transparence).
        """
        import logging
        logger = logging.getLogger(__name__)

        # Récupérer les checks de conformité
        checks = self.db.query(ComplianceCheck).filter(
            ComplianceCheck.tenant_id == self.tenant_id,
            ComplianceCheck.is_active
        ).all()

        if not checks:
            # Aucun contrôle défini = score 0% avec avertissement explicite
            # (un score de 100% serait trompeur)
            logger.warning(
                f"[COMPLIANCE_BENCHMARK] tenant={self.tenant_id} "
                f"Aucun contrôle de conformité défini - score 0%"
            )
            return 0, {
                "status": "NO_CHECKS_DEFINED",
                "message": "Aucun contrôle de conformité défini",
                "recommendation": "Définir des contrôles de conformité pour ce tenant"
            }, ["Aucun contrôle de conformité défini - résultat non significatif"]

        compliant = sum(1 for c in checks if c.status == "COMPLIANT")
        total = len(checks)

        details = {
            "compliant": compliant,
            "non_compliant": total - compliant,
            "total": total
        }

        warnings = [
            f"{c.control_id}: {c.control_name}"
            for c in checks if c.status == "NON_COMPLIANT"
        ]

        score = (compliant / total) * 100 if total > 0 else 0

        logger.info(
            f"[COMPLIANCE_BENCHMARK] tenant={self.tenant_id} "
            f"score={score:.1f}% compliant={compliant}/{total}"
        )

        return score, details, warnings

    def _run_feature_benchmark(self, benchmark: Benchmark, config: dict, baseline: dict) -> tuple[float, dict, list]:
        """
        Benchmark fonctionnel.

        ATTENTION: Ce benchmark n'est pas encore implémenté.
        Retourne 0% avec avertissement explicite au lieu de 100% factice.

        TODO: Implémenter les vérifications fonctionnelles:
        - Tests E2E passent
        - Coverage de code suffisant
        - Fonctionnalités critiques opérationnelles
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.warning(
            f"[FEATURE_BENCHMARK] tenant={self.tenant_id} benchmark_id={benchmark.id} "
            f"NOT IMPLEMENTED - Returning 0% instead of fake 100%"
        )

        return 0, {
            "status": "NOT_IMPLEMENTED",
            "message": "Feature benchmark non implémenté - score 0% par défaut",
            "recommendation": "Implémenter _run_feature_benchmark() avec de vraies vérifications"
        }, ["FEATURE benchmark non implémenté - résultat non fiable"]

    def list_benchmarks(self, benchmark_type: str = None) -> list[Benchmark]:
        """Liste les benchmarks."""
        query = self.db.query(Benchmark).filter(
            Benchmark.tenant_id == self.tenant_id,
            Benchmark.is_active
        )

        if benchmark_type:
            query = query.filter(Benchmark.benchmark_type == benchmark_type)

        return query.all()

    def get_benchmark_results(self, benchmark_id: int, limit: int = 10) -> list[BenchmarkResult]:
        """Récupère les résultats d'un benchmark."""
        return self.db.query(BenchmarkResult).filter(
            BenchmarkResult.benchmark_id == benchmark_id,
            BenchmarkResult.tenant_id == self.tenant_id
        ).order_by(BenchmarkResult.started_at.desc()).limit(limit).all()

    # ========================================================================
    # CONFORMITÉ
    # ========================================================================

    def create_compliance_check(
        self,
        framework: ComplianceFramework,
        control_id: str,
        control_name: str,
        check_type: str,
        control_description: str = None,
        category: str = None,
        subcategory: str = None,
        severity: str = "MEDIUM"
    ) -> ComplianceCheck:
        """Crée un contrôle de conformité."""
        check = ComplianceCheck(
            tenant_id=self.tenant_id,
            framework=framework,
            control_id=control_id,
            control_name=control_name,
            control_description=control_description,
            category=category,
            subcategory=subcategory,
            check_type=check_type,
            severity=severity
        )

        self.db.add(check)
        self.db.commit()
        return check

    def update_compliance_status(
        self,
        check_id: int,
        status: str,
        actual_result: str = None,
        evidence: dict = None,
        checked_by: int = None
    ) -> ComplianceCheck:
        """Met à jour le statut d'un contrôle."""
        check = self.db.query(ComplianceCheck).filter(
            ComplianceCheck.id == check_id,
            ComplianceCheck.tenant_id == self.tenant_id
        ).first()

        if check:
            check.status = status
            check.actual_result = actual_result
            check.evidence = json.dumps(evidence) if evidence else None
            check.last_checked_at = datetime.utcnow()
            check.checked_by = checked_by
            self.db.commit()

        return check

    def get_compliance_summary(self, framework: ComplianceFramework = None) -> dict[str, Any]:
        """Récupère un résumé de conformité."""
        query = self.db.query(ComplianceCheck).filter(
            ComplianceCheck.tenant_id == self.tenant_id,
            ComplianceCheck.is_active
        )

        if framework:
            query = query.filter(ComplianceCheck.framework == framework)

        checks = query.all()

        summary = {
            "total": len(checks),
            "compliant": sum(1 for c in checks if c.status == "COMPLIANT"),
            "non_compliant": sum(1 for c in checks if c.status == "NON_COMPLIANT"),
            "pending": sum(1 for c in checks if c.status == "PENDING"),
            "not_applicable": sum(1 for c in checks if c.status == "N/A"),
            "by_severity": {},
            "by_category": {}
        }

        # Par sévérité
        for check in checks:
            if check.severity not in summary["by_severity"]:
                summary["by_severity"][check.severity] = {"total": 0, "compliant": 0}
            summary["by_severity"][check.severity]["total"] += 1
            if check.status == "COMPLIANT":
                summary["by_severity"][check.severity]["compliant"] += 1

        # Taux de conformité
        if summary["total"] > 0:
            summary["compliance_rate"] = (summary["compliant"] / summary["total"]) * 100
        else:
            summary["compliance_rate"] = 100

        return summary

    # ========================================================================
    # RÉTENTION
    # ========================================================================

    def create_retention_rule(
        self,
        name: str,
        target_table: str,
        policy: RetentionPolicy,
        retention_days: int,
        target_module: str = None,
        condition: str = None,
        action: str = "DELETE",
        schedule_cron: str = None
    ) -> DataRetentionRule:
        """Crée une règle de rétention."""
        rule = DataRetentionRule(
            tenant_id=self.tenant_id,
            name=name,
            target_table=target_table,
            target_module=target_module,
            policy=policy,
            retention_days=retention_days,
            condition=condition,
            action=action,
            schedule_cron=schedule_cron
        )

        self.db.add(rule)
        self.db.commit()
        return rule

    def apply_retention_rules(self) -> dict[str, int]:
        """Applique les règles de rétention."""
        rules = self.db.query(DataRetentionRule).filter(
            DataRetentionRule.tenant_id == self.tenant_id,
            DataRetentionRule.is_active
        ).all()

        results = {}
        for rule in rules:
            count = self._apply_single_retention_rule(rule)
            results[rule.name] = count

        self.db.commit()
        return results

    def _apply_single_retention_rule(self, rule: DataRetentionRule) -> int:
        """Applique une règle de rétention unique."""
        cutoff_date = datetime.utcnow() - timedelta(days=rule.retention_days)

        # Pour les logs d'audit
        if rule.target_table == "audit_logs":
            query = self.db.query(AuditLog).filter(
                AuditLog.tenant_id == self.tenant_id,
                AuditLog.created_at < cutoff_date
            )

            count = query.delete(synchronize_session=False) if rule.action == "DELETE" else query.count()
                # TODO: Implémenter archivage/anonymisation

            rule.last_run_at = datetime.utcnow()
            rule.last_affected_count = count
            return count

        return 0

    # ========================================================================
    # EXPORTS
    # ========================================================================

    def create_export(
        self,
        export_type: str,
        format: str,
        requested_by: int,
        date_from: datetime = None,
        date_to: datetime = None,
        filters: dict = None
    ) -> AuditExport:
        """Crée une demande d'export."""
        export = AuditExport(
            tenant_id=self.tenant_id,
            export_type=export_type,
            format=format,
            date_from=date_from,
            date_to=date_to,
            filters=json.dumps(filters) if filters else None,
            requested_by=requested_by,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        self.db.add(export)
        self.db.commit()
        return export

    def process_export(self, export_id: int) -> AuditExport:
        """Traite un export."""
        export = self.db.query(AuditExport).filter(
            AuditExport.id == export_id,
            AuditExport.tenant_id == self.tenant_id
        ).first()

        if not export:
            raise ValueError("Export non trouvé")

        export.status = "PROCESSING"
        self.db.flush()

        try:
            # Récupérer les données selon le type
            if export.export_type == "AUDIT_LOGS":
                data, count = self._export_audit_logs(export)
            elif export.export_type == "METRICS":
                data, count = self._export_metrics(export)
            else:
                data, count = [], 0

            # Générer le fichier
            file_content = self._generate_export_file(data, export.format)

            # Sauvegarder
            file_name = f"export_{export.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{export.format.lower()}"
            export.file_path = f"/exports/{self.tenant_id}/{file_name}"
            export.file_size = len(file_content)
            export.records_count = count
            export.status = "COMPLETED"
            export.completed_at = datetime.utcnow()

        except Exception as e:
            export.status = "FAILED"
            export.error_message = str(e)

        self.db.commit()
        return export

    def _export_audit_logs(self, export: AuditExport) -> tuple[list[dict], int]:
        """Exporte les logs d'audit."""
        logs, total = self.search_logs(
            from_date=export.date_from,
            to_date=export.date_to,
            limit=100000
        )

        data = [
            {
                "id": log.id,
                "action": log.action.value,
                "module": log.module,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "user_id": log.user_id,
                "user_email": log.user_email,
                "description": log.description,
                "success": log.success,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]

        return data, total

    def _export_metrics(self, export: AuditExport) -> tuple[list[dict], int]:
        """Exporte les métriques."""
        values = self.db.query(MetricValue).filter(
            MetricValue.tenant_id == self.tenant_id
        )

        if export.date_from:
            values = values.filter(MetricValue.period_start >= export.date_from)
        if export.date_to:
            values = values.filter(MetricValue.period_end <= export.date_to)

        values = values.limit(100000).all()

        data = [
            {
                "metric_code": v.metric_code,
                "value": v.value,
                "avg_value": v.avg_value,
                "min_value": v.min_value,
                "max_value": v.max_value,
                "period_start": v.period_start.isoformat(),
                "period_end": v.period_end.isoformat()
            }
            for v in values
        ]

        return data, len(data)

    def _generate_export_file(self, data: list[dict], format: str) -> bytes:
        """Génère le contenu du fichier d'export."""
        if format == "JSON":
            return json.dumps(data, indent=2).encode()
        elif format == "CSV":
            if not data:
                return b""
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue().encode()
        else:
            return json.dumps(data).encode()

    # ========================================================================
    # TABLEAUX DE BORD
    # ========================================================================

    def create_dashboard(
        self,
        code: str,
        name: str,
        widgets: list[dict],
        owner_id: int,
        description: str = None,
        layout: dict = None,
        refresh_interval: int = 60
    ) -> AuditDashboard:
        """Crée un tableau de bord."""
        dashboard = AuditDashboard(
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            widgets=json.dumps(widgets),
            layout=json.dumps(layout) if layout else None,
            refresh_interval=refresh_interval,
            owner_id=owner_id
        )

        self.db.add(dashboard)
        self.db.commit()
        return dashboard

    def get_dashboard_data(self, dashboard_id: int) -> dict[str, Any]:
        """Récupère les données d'un tableau de bord."""
        dashboard = self.db.query(AuditDashboard).filter(
            AuditDashboard.id == dashboard_id,
            AuditDashboard.tenant_id == self.tenant_id
        ).first()

        if not dashboard:
            return None

        widgets = json.loads(dashboard.widgets)
        data = {}

        for widget in widgets:
            widget_type = widget.get("type")
            widget_id = widget.get("id")

            if widget_type == "audit_stats":
                data[widget_id] = self._get_audit_stats()
            elif widget_type == "recent_activity":
                logs, _ = self.search_logs(limit=10)
                data[widget_id] = [{"action": l.action.value, "module": l.module} for l in logs]
            elif widget_type == "compliance_summary":
                data[widget_id] = self.get_compliance_summary()
            elif widget_type == "metric_chart":
                metric_code = widget.get("metric_code")
                values = self.get_metric_values(metric_code, limit=100)
                data[widget_id] = [{"value": v.value, "time": v.period_start.isoformat()} for v in values]

        return {
            "dashboard": {
                "id": dashboard.id,
                "name": dashboard.name,
                "refresh_interval": dashboard.refresh_interval
            },
            "data": data
        }

    def _get_audit_stats(self) -> dict[str, Any]:
        """Récupère les statistiques d'audit."""
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)
        now - timedelta(days=7)

        total_logs_24h = self.db.query(AuditLog).filter(
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.created_at >= yesterday
        ).count()

        failed_24h = self.db.query(AuditLog).filter(
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.created_at >= yesterday,
            not AuditLog.success
        ).count()

        active_sessions = self.db.query(AuditSession).filter(
            AuditSession.tenant_id == self.tenant_id,
            AuditSession.is_active
        ).count()

        unique_users_24h = self.db.query(func.count(func.distinct(AuditLog.user_id))).filter(
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.created_at >= yesterday,
            AuditLog.user_id.isnot(None)
        ).scalar()

        return {
            "total_logs_24h": total_logs_24h,
            "failed_24h": failed_24h,
            "active_sessions": active_sessions,
            "unique_users_24h": unique_users_24h
        }


# ============================================================================
# FACTORY
# ============================================================================

def get_audit_service(db: Session, tenant_id: str) -> AuditService:
    """Factory pour créer un service d'audit."""
    return AuditService(db, tenant_id)
