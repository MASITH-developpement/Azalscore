#!/usr/bin/env python3
"""
AZALSCORE – AUTONOMOUS GUARDIAN
==============================

Fonctions :
- Création automatique du service systemd
- Démarrage automatique au boot serveur
- Vérification + correction au démarrage
- Surveillance continue + auto-correction
- Maintien permanent de l’état "0 bug actif"
"""

import os
import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime

# =====================================================
# CONFIGURATION
# =====================================================

PROJECT_ROOT = Path(__file__).parent.resolve()
SCRIPT_PATH = PROJECT_ROOT / "azalscore_autonomous_guardian.py"

SERVICE_NAME = "azalscore-guardian"
SERVICE_FILE = Path("/etc/systemd/system") / f"{SERVICE_NAME}.service"

DOCKER_COMPOSE = ["docker", "compose"]
API_CONTAINER = "azals_api"

CHECK_INTERVAL = 10
MAX_LOG_LINES = 250
AI_MODEL = "gpt-4.1"

LOG_FILE = PROJECT_ROOT / "azalscore_guardian.log"

ALLOWED_PATHS = ["app/", "services/", "utils/"]
FORBIDDEN_KEYWORDS = ["docker", "nginx", "alembic", "migration", "compose"]

ERROR_SIGNS = [
    "Traceback", "Exception", "ERROR", "CRITICAL",
    "ModuleNotFoundError", "ImportError",
    "AttributeError", "TypeError", "KeyError"
]

WARNING_SIGNS = [
    "WARNING", "DeprecationWarning", "UserWarning", "RuntimeWarning"
]

# =====================================================
# UTILITAIRES
# =====================================================

def log(msg):
    line = f"[{datetime.now().isoformat()}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run(cmd, check=True):
    log(f"CMD → {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


# =====================================================
# SYSTEMD
# =====================================================

def install_systemd_service():
    if SERVICE_FILE.exists():
        log("Service systemd déjà présent")
        return

    log("Création du service systemd")

    service_content = f"""
[Unit]
Description=AZALSCORE Autonomous Guardian
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory={PROJECT_ROOT}
ExecStart=/usr/bin/python3 {SCRIPT_PATH}
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

    SERVICE_FILE.write_text(service_content.strip() + "\n")
    run(["systemctl", "daemon-reexec"])
    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", SERVICE_NAME])
    run(["systemctl", "start", SERVICE_NAME])

    log("Service systemd installé et activé")


# =====================================================
# DEMARRAGE / VERIFICATION
# =====================================================

def start_azalscore():
    log("Démarrage AZALSCORE")
    run(DOCKER_COMPOSE + ["up", "-d"])


def get_logs():
    return run(
        ["docker", "logs", API_CONTAINER, "--tail", str(MAX_LOG_LINES)],
        check=False
    )


def wait_for_api(timeout=120):
    log("Vérification disponibilité API")
    start = time.time()
    while time.time() - start < timeout:
        logs = get_logs()
        if "Application startup complete" in logs or "Uvicorn running" in logs:
            log("API opérationnelle")
            return
        time.sleep(5)
    raise TimeoutError("API non disponible")


# =====================================================
# ANALYSE ANOMALIES
# =====================================================

def detect_anomalies(logs):
    errors = [e for e in ERROR_SIGNS if e in logs]
    warnings = [w for w in WARNING_SIGNS if w in logs]
    return errors, warnings


# =====================================================
# IA DEBUG
# =====================================================

def ask_ai(logs, errors, warnings):
    from openai import OpenAI
    client = OpenAI()

    prompt = f"""
Tu es un expert Python / FastAPI.

Objectif :
Maintenir un état "0 bug actif" en continu.

BUG = erreur ou warning, bloquant ou non.

Contraintes :
- patch minimal
- format UNIFIED DIFF uniquement
- modifier uniquement du code applicatif Python
- interdit : DB, docker, nginx, migrations

ERREURS :
{errors}

WARNINGS :
{warnings}

LOGS :
{logs}
"""

    r = client.responses.create(
        model=AI_MODEL,
        input=prompt
    )

    return r.output_text.strip()


# =====================================================
# PATCH PIPELINE
# =====================================================

def patch_valid(patch):
    if not patch.startswith("diff"):
        return False
    for line in patch.splitlines():
        if line.startswith(("+++ ", "--- ")):
            path = line[4:]
            if not any(path.startswith(p) for p in ALLOWED_PATHS):
                return False
            if any(k in path.lower() for k in FORBIDDEN_KEYWORDS):
                return False
    return True


def apply_patch(patch):
    run(["git", "checkout", "-B", "ai-guardian-fix"])
    (PROJECT_ROOT / "ai_fix.diff").write_text(patch)
    run(["git", "apply", "ai_fix.diff"])


def run_tests():
    log("Lancement des tests")
    return subprocess.run(["pytest"]).returncode == 0


def deploy():
    log("Déploiement correctif")
    run(["git", "checkout", "main"])
    run(["git", "merge", "--no-ff", "ai-guardian-fix"])
    run(DOCKER_COMPOSE + ["up", "-d", "--build"])


def rollback():
    log("Rollback")
    run(["git", "checkout", "main"], check=False)
    run(["git", "branch", "-D", "ai-guardian-fix"], check=False)


# =====================================================
# BOUCLE PERMANENTE
# =====================================================

def guardian_loop():
    start_azalscore()
    wait_for_api()

    log("Surveillance continue active")

    while True:
        try:
            logs = get_logs()
            errors, warnings = detect_anomalies(logs)

            if not errors and not warnings:
                time.sleep(CHECK_INTERVAL)
                continue

            log(f"Anomalies détectées → erreurs={errors} warnings={warnings}")

            patch = ask_ai(logs, errors, warnings)

            if not patch_valid(patch):
                log("Patch refusé (sécurité)")
                rollback()
                time.sleep(CHECK_INTERVAL)
                continue

            apply_patch(patch)

            if not run_tests():
                log("Tests échoués")
                rollback()
                time.sleep(CHECK_INTERVAL)
                continue

            deploy()
            log("Correction appliquée – état stable rétabli")

        except Exception as e:
            log(f"ERREUR SYSTEME : {e}")

        time.sleep(CHECK_INTERVAL)


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    if os.geteuid() == 0:
        install_systemd_service()

    log("AZALSCORE GUARDIAN LANCÉ")
    guardian_loop()
