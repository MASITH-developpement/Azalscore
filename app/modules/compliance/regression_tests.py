"""
AZALSCORE - Tests de Régression Automatisés
============================================
Service de tests de régression pour garantir la stabilité du code.

Fonctionnalités:
- Détection des régressions API
- Validation des schemas de réponse
- Tests de contrat API
- Comparaison des snapshots
- Historique des exécutions
"""
from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, JSON
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.models import UniversalUUID

logger = logging.getLogger(__name__)


# ============================================================================
# MODÈLES
# ============================================================================

class RegressionTestRun(Base):
    """Exécution de tests de régression."""
    __tablename__ = "regression_test_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(UniversalUUID, nullable=False, index=True)
    run_id = Column(String(64), nullable=False, unique=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="running")
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    error_tests = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    git_commit = Column(String(40), nullable=True)
    git_branch = Column(String(100), nullable=True)
    triggered_by = Column(String(100), nullable=True)
    results_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class RegressionSnapshot(Base):
    """Snapshot de réponse API pour comparaison."""
    __tablename__ = "regression_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(UniversalUUID, nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    snapshot_hash = Column(String(64), nullable=False)
    response_schema = Column(JSON, nullable=True)
    sample_response = Column(JSON, nullable=True)
    is_baseline = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# ENUMS
# ============================================================================

class TestStatus(str, Enum):
    """Statuts de test."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class RegressionType(str, Enum):
    """Types de régression."""
    API_SCHEMA = "api_schema"
    API_RESPONSE = "api_response"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DATA_INTEGRITY = "data_integrity"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TestResult:
    """Résultat d'un test individuel."""
    name: str
    module: str
    status: TestStatus
    duration_ms: int = 0
    error_message: str | None = None
    stack_trace: str | None = None


@dataclass
class RegressionReport:
    """Rapport de régression."""
    run_id: str
    started_at: datetime
    completed_at: datetime | None
    status: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration_seconds: int = 0
    regressions_detected: list[dict] = field(default_factory=list)
    test_results: list[TestResult] = field(default_factory=list)
    coverage_percent: float = 0.0


# ============================================================================
# SERVICE
# ============================================================================

class RegressionTestService:
    """Service de tests de régression."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.base_path = Path("/home/ubuntu/azalscore")

    def run_full_regression(
        self,
        modules: list[str] | None = None,
        include_slow: bool = False,
        triggered_by: str = "manual"
    ) -> RegressionReport:
        """
        Exécuter une suite complète de tests de régression.

        Args:
            modules: Liste des modules à tester (None = tous)
            include_slow: Inclure les tests lents
            triggered_by: Source du déclenchement (manual, ci, schedule)

        Returns:
            RegressionReport avec résultats
        """
        import uuid

        run_id = str(uuid.uuid4())[:8]
        started_at = datetime.utcnow()

        logger.info(f"Starting regression test run {run_id}")

        report = RegressionReport(
            run_id=run_id,
            started_at=started_at,
            completed_at=None,
            status="running"
        )

        # Obtenir info git
        git_commit = self._get_git_commit()
        git_branch = self._get_git_branch()

        # Créer l'enregistrement de run
        run = RegressionTestRun(
            tenant_id=self.tenant_id,
            run_id=run_id,
            started_at=started_at,
            status="running",
            git_commit=git_commit,
            git_branch=git_branch,
            triggered_by=triggered_by
        )
        self.db.add(run)
        self.db.commit()

        try:
            # Construire la commande pytest
            cmd = [
                sys.executable, "-m", "pytest",
                "-v", "--tb=short",
                "-q",
                "--json-report",
                f"--json-report-file=/tmp/regression_{run_id}.json"
            ]

            if modules:
                for module in modules:
                    cmd.append(f"app/modules/{module}/tests/")
            else:
                cmd.append("app/modules/")

            if not include_slow:
                cmd.extend(["-m", "not slow"])

            # Exécuter pytest
            result = subprocess.run(
                cmd,
                cwd=str(self.base_path),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )

            # Parser les résultats
            report = self._parse_pytest_output(run_id, result, started_at)

            # Vérifier les régressions
            regressions = self._detect_regressions(report)
            report.regressions_detected = regressions

        except subprocess.TimeoutExpired:
            report.status = "timeout"
            logger.error(f"Regression test run {run_id} timed out")

        except Exception as e:
            report.status = "error"
            logger.error(f"Regression test run {run_id} failed: {e}")

        finally:
            report.completed_at = datetime.utcnow()
            report.duration_seconds = int(
                (report.completed_at - report.started_at).total_seconds()
            )

            # Mettre à jour l'enregistrement
            run.completed_at = report.completed_at
            run.status = report.status
            run.total_tests = report.total_tests
            run.passed_tests = report.passed
            run.failed_tests = report.failed
            run.skipped_tests = report.skipped
            run.error_tests = report.errors
            run.duration_seconds = report.duration_seconds
            run.results_json = self._report_to_dict(report)
            self.db.commit()

        logger.info(
            f"Regression run {run_id} completed | "
            f"passed={report.passed} failed={report.failed} duration={report.duration_seconds}s"
        )

        return report

    def _parse_pytest_output(
        self,
        run_id: str,
        result: subprocess.CompletedProcess,
        started_at: datetime
    ) -> RegressionReport:
        """Parser la sortie pytest."""
        report = RegressionReport(
            run_id=run_id,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            status="completed"
        )

        # Essayer de lire le rapport JSON
        json_report_path = Path(f"/tmp/regression_{run_id}.json")
        if json_report_path.exists():
            try:
                with open(json_report_path) as f:
                    data = json.load(f)

                summary = data.get("summary", {})
                report.total_tests = summary.get("total", 0)
                report.passed = summary.get("passed", 0)
                report.failed = summary.get("failed", 0)
                report.skipped = summary.get("skipped", 0)
                report.errors = summary.get("error", 0)

                # Extraire les résultats individuels
                for test in data.get("tests", []):
                    report.test_results.append(TestResult(
                        name=test.get("nodeid", "unknown"),
                        module=test.get("nodeid", "").split("::")[0],
                        status=TestStatus(test.get("outcome", "error")),
                        duration_ms=int(test.get("duration", 0) * 1000),
                        error_message=test.get("call", {}).get("longrepr") if test.get("outcome") == "failed" else None
                    ))

            except Exception as e:
                logger.warning(f"Could not parse JSON report: {e}")

        # Fallback: parser la sortie texte
        if report.total_tests == 0:
            output = result.stdout + result.stderr
            # Pattern: "X passed, Y failed, Z skipped"
            import re
            match = re.search(r"(\d+) passed", output)
            if match:
                report.passed = int(match.group(1))
            match = re.search(r"(\d+) failed", output)
            if match:
                report.failed = int(match.group(1))
            match = re.search(r"(\d+) skipped", output)
            if match:
                report.skipped = int(match.group(1))
            match = re.search(r"(\d+) error", output)
            if match:
                report.errors = int(match.group(1))

            report.total_tests = report.passed + report.failed + report.skipped + report.errors

        # Déterminer le statut
        if report.failed > 0 or report.errors > 0:
            report.status = "failed"
        else:
            report.status = "passed"

        return report

    def _detect_regressions(self, report: RegressionReport) -> list[dict]:
        """Détecter les régressions par rapport aux runs précédents."""
        regressions = []

        # Récupérer le dernier run réussi
        last_success = self.db.query(RegressionTestRun).filter(
            RegressionTestRun.tenant_id == self.tenant_id,
            RegressionTestRun.status == "passed",
            RegressionTestRun.run_id != report.run_id
        ).order_by(RegressionTestRun.completed_at.desc()).first()

        if not last_success:
            return regressions

        # Comparer les résultats
        last_results = last_success.results_json or {}
        last_passed = last_results.get("passed", 0)
        last_failed = last_results.get("failed", 0)

        # Régression si plus de tests échouent
        if report.failed > last_failed:
            regressions.append({
                "type": "test_failures",
                "description": f"Tests échoués augmentés: {last_failed} → {report.failed}",
                "severity": "high",
                "delta": report.failed - last_failed
            })

        # Régression si moins de tests passent
        if report.passed < last_passed:
            regressions.append({
                "type": "test_coverage",
                "description": f"Tests passés diminués: {last_passed} → {report.passed}",
                "severity": "medium",
                "delta": last_passed - report.passed
            })

        # Régression de performance (si durée augmente de > 20%)
        last_duration = last_results.get("duration_seconds", 0)
        if last_duration > 0:
            duration_increase = (report.duration_seconds - last_duration) / last_duration
            if duration_increase > 0.2:
                regressions.append({
                    "type": "performance",
                    "description": f"Durée augmentée de {duration_increase*100:.1f}%",
                    "severity": "low",
                    "delta": report.duration_seconds - last_duration
                })

        return regressions

    def _get_git_commit(self) -> str | None:
        """Obtenir le commit git actuel."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.base_path),
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()[:40] if result.returncode == 0 else None
        except Exception:
            return None

    def _get_git_branch(self) -> str | None:
        """Obtenir la branche git actuelle."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.base_path),
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _report_to_dict(self, report: RegressionReport) -> dict:
        """Convertir un rapport en dictionnaire."""
        return {
            "run_id": report.run_id,
            "started_at": report.started_at.isoformat(),
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
            "status": report.status,
            "total_tests": report.total_tests,
            "passed": report.passed,
            "failed": report.failed,
            "skipped": report.skipped,
            "errors": report.errors,
            "duration_seconds": report.duration_seconds,
            "regressions": report.regressions_detected,
            "coverage_percent": report.coverage_percent
        }

    def get_history(self, limit: int = 20) -> list[dict]:
        """Récupérer l'historique des runs."""
        runs = self.db.query(RegressionTestRun).filter(
            RegressionTestRun.tenant_id == self.tenant_id
        ).order_by(
            RegressionTestRun.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "run_id": r.run_id,
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "status": r.status,
                "total_tests": r.total_tests,
                "passed": r.passed_tests,
                "failed": r.failed_tests,
                "skipped": r.skipped_tests,
                "duration": r.duration_seconds,
                "git_commit": r.git_commit,
                "git_branch": r.git_branch,
                "triggered_by": r.triggered_by
            }
            for r in runs
        ]

    def get_run(self, run_id: str) -> dict | None:
        """Récupérer les détails d'un run."""
        run = self.db.query(RegressionTestRun).filter(
            RegressionTestRun.tenant_id == self.tenant_id,
            RegressionTestRun.run_id == run_id
        ).first()

        if not run:
            return None

        return {
            "run_id": run.run_id,
            "started_at": run.started_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "status": run.status,
            "total_tests": run.total_tests,
            "passed": run.passed_tests,
            "failed": run.failed_tests,
            "skipped": run.skipped_tests,
            "errors": run.error_tests,
            "duration": run.duration_seconds,
            "git_commit": run.git_commit,
            "git_branch": run.git_branch,
            "triggered_by": run.triggered_by,
            "results": run.results_json
        }

    def compare_runs(self, run_id_1: str, run_id_2: str) -> dict:
        """Comparer deux runs."""
        run1 = self.get_run(run_id_1)
        run2 = self.get_run(run_id_2)

        if not run1 or not run2:
            return {"error": "Run not found"}

        return {
            "run_1": run1,
            "run_2": run2,
            "comparison": {
                "passed_delta": run2.get("passed", 0) - run1.get("passed", 0),
                "failed_delta": run2.get("failed", 0) - run1.get("failed", 0),
                "duration_delta": run2.get("duration", 0) - run1.get("duration", 0),
                "status_changed": run1.get("status") != run2.get("status")
            }
        }

    def create_snapshot(self, endpoint: str, method: str, response: dict) -> str:
        """Créer un snapshot de réponse API."""
        # Calculer le hash du schema
        schema_str = json.dumps(self._extract_schema(response), sort_keys=True)
        snapshot_hash = hashlib.sha256(schema_str.encode()).hexdigest()

        snapshot = RegressionSnapshot(
            tenant_id=self.tenant_id,
            endpoint=endpoint,
            method=method,
            snapshot_hash=snapshot_hash,
            response_schema=self._extract_schema(response),
            sample_response=response
        )
        self.db.add(snapshot)
        self.db.commit()

        return snapshot_hash

    def _extract_schema(self, obj: Any, depth: int = 0) -> dict:
        """Extraire le schema d'un objet JSON."""
        if depth > 10:
            return {"type": "max_depth"}

        if obj is None:
            return {"type": "null"}
        elif isinstance(obj, bool):
            return {"type": "boolean"}
        elif isinstance(obj, int):
            return {"type": "integer"}
        elif isinstance(obj, float):
            return {"type": "number"}
        elif isinstance(obj, str):
            return {"type": "string"}
        elif isinstance(obj, list):
            if len(obj) == 0:
                return {"type": "array", "items": {}}
            return {
                "type": "array",
                "items": self._extract_schema(obj[0], depth + 1)
            }
        elif isinstance(obj, dict):
            return {
                "type": "object",
                "properties": {
                    k: self._extract_schema(v, depth + 1)
                    for k, v in obj.items()
                }
            }
        else:
            return {"type": "unknown"}

    def verify_snapshot(self, endpoint: str, method: str, response: dict) -> dict:
        """Vérifier une réponse contre le snapshot baseline."""
        baseline = self.db.query(RegressionSnapshot).filter(
            RegressionSnapshot.tenant_id == self.tenant_id,
            RegressionSnapshot.endpoint == endpoint,
            RegressionSnapshot.method == method,
            RegressionSnapshot.is_baseline == True
        ).first()

        if not baseline:
            return {
                "status": "no_baseline",
                "message": "No baseline snapshot found"
            }

        current_schema = self._extract_schema(response)
        current_hash = hashlib.sha256(
            json.dumps(current_schema, sort_keys=True).encode()
        ).hexdigest()

        if current_hash == baseline.snapshot_hash:
            return {
                "status": "match",
                "message": "Response matches baseline"
            }
        else:
            return {
                "status": "mismatch",
                "message": "Response schema differs from baseline",
                "baseline_hash": baseline.snapshot_hash,
                "current_hash": current_hash,
                "baseline_schema": baseline.response_schema,
                "current_schema": current_schema
            }
