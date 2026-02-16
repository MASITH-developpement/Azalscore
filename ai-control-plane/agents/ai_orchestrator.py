"""
AZALS - AI Self-Healing Orchestrator
=====================================

AVERTISSEMENT SÉCURITÉ:
Ce module a été sécurisé mais l'exécution automatique de code généré par IA
reste intrinsèquement risquée. En production, désactivez AUTO_APPLY_FIXES.

Modes de fonctionnement:
- MONITORING_ONLY: Détecte et signale les erreurs (recommandé en production)
- SUGGEST_FIXES: Génère des suggestions de fix mais ne les applique pas
- AUTO_APPLY_FIXES: DANGEREUX - Applique automatiquement les fixes (dev only)
"""

import os
import re
import time
import subprocess
import json
import logging
from pathlib import Path
from typing import Optional, Tuple

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI non disponible")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic non disponible")

print("🤖 AI Self-Healing Orchestrator is running")

# Configuration sécurisée
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

# MODE DE FONCTIONNEMENT (SÉCURITÉ)
# "monitoring" = détection seulement
# "suggest" = génère des suggestions
# "auto" = applique automatiquement (DANGEREUX)
ORCHESTRATOR_MODE = os.getenv("AI_ORCHESTRATOR_MODE", "monitoring")

# Répertoire de base pour les prompts (protection path traversal)
PROMPTS_BASE_DIR = Path(__file__).parent / "prompts"

# Commandes autorisées (whitelist)
ALLOWED_COMMANDS = {
    "docker_logs_api": ["docker", "logs", "api", "--tail", "100"],
    "docker_logs_frontend": ["docker", "logs", "azals_frontend", "--tail", "50"],
    "docker_logs_nginx": ["docker", "logs", "azals_nginx", "--tail", "50"],
    "git_diff": ["git", "diff", "HEAD~1"],
    "git_status": ["git", "status"],
}

# Initialisation des clients (si disponibles)
openai_client = None
anthropic_client = None

if OPENAI_AVAILABLE and OPENAI_KEY:
    openai_client = OpenAI(api_key=OPENAI_KEY)

if ANTHROPIC_AVAILABLE and ANTHROPIC_KEY:
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


def read_prompt(name: str) -> str:
    """
    Lit un fichier prompt de manière sécurisée.

    SÉCURITÉ: Protection contre path traversal.
    """
    # Valider le nom (alphanumeric et underscores seulement)
    if not re.match(r'^[a-zA-Z0-9_]+$', name):
        raise ValueError(f"Nom de prompt invalide: {name}")

    # Construire le chemin sécurisé
    prompt_path = (PROMPTS_BASE_DIR / f"{name}.prompt").resolve()

    # Vérifier que le chemin est bien dans le répertoire autorisé
    try:
        prompt_path.relative_to(PROMPTS_BASE_DIR.resolve())
    except ValueError:
        raise ValueError(f"Tentative d'accès hors du répertoire prompts: {name}")

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt non trouvé: {name}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def run_safe_command(command_key: str) -> Tuple[bool, str]:
    """
    Exécute une commande de la whitelist de manière sécurisée.

    SÉCURITÉ: Seules les commandes prédéfinies peuvent être exécutées.
    """
    if command_key not in ALLOWED_COMMANDS:
        logger.error(f"Commande non autorisée: {command_key}")
        return False, f"Commande non autorisée: {command_key}"

    cmd = ALLOWED_COMMANDS[command_key]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False  # SÉCURITÉ: Pas de shell
        )
        output = result.stdout + result.stderr
        return True, output[:10000]  # Limite de taille
    except subprocess.TimeoutExpired:
        return False, "Timeout dépassé"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def get_logs() -> str:
    """Récupère les logs des conteneurs de manière sécurisée."""
    logs_parts = []

    success, api_logs = run_safe_command("docker_logs_api")
    if success:
        logs_parts.append(f"=== API LOGS ===\n{api_logs}")

    success, frontend_logs = run_safe_command("docker_logs_frontend")
    if success:
        logs_parts.append(f"=== FRONTEND LOGS ===\n{frontend_logs}")

    success, nginx_logs = run_safe_command("docker_logs_nginx")
    if success:
        logs_parts.append(f"=== NGINX LOGS ===\n{nginx_logs}")

    return "\n\n".join(logs_parts)


def get_diff() -> str:
    """Récupère le diff git de manière sécurisée."""
    success, diff = run_safe_command("git_diff")
    return diff if success else ""


def call_openai(prompt: str, data: str) -> Optional[str]:
    """Appelle OpenAI de manière sécurisée."""
    if not openai_client:
        logger.warning("OpenAI non configuré")
        return None

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt[:4000]},  # Limite
                {"role": "user", "content": data[:8000]}  # Limite
            ],
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Erreur OpenAI: {e}")
        return None


def call_claude(prompt: str, data: str) -> Optional[str]:
    """Appelle Claude de manière sécurisée."""
    if not anthropic_client:
        logger.warning("Anthropic non configuré")
        return None

    try:
        msg = anthropic_client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=2000,
            system=prompt[:4000],  # Limite
            messages=[{"role": "user", "content": data[:8000]}]  # Limite
        )
        return msg.content[0].text
    except Exception as e:
        logger.error(f"Erreur Claude: {e}")
        return None


def analyze_errors(logs: str) -> dict:
    """Analyse les logs pour détecter les erreurs."""
    error_patterns = [
        "ERROR", "Exception", "Traceback", "CRITICAL",
        "500 Internal Server Error", "502 Bad Gateway"
    ]

    # Filtrer les faux positifs
    ignore_patterns = ["403 Forbidden"]  # Peut être normal

    errors_found = []
    for pattern in error_patterns:
        if pattern in logs:
            # Vérifier que ce n'est pas un faux positif
            if not any(ignore in logs for ignore in ignore_patterns):
                errors_found.append(pattern)

    return {
        "has_errors": len(errors_found) > 0,
        "patterns": errors_found,
        "log_length": len(logs)
    }


def save_suggestion(suggestion: str, suggestion_type: str) -> str:
    """
    Sauvegarde une suggestion de fix pour revue manuelle.

    SÉCURITÉ: Les suggestions sont sauvegardées mais JAMAIS exécutées automatiquement.
    """
    suggestions_dir = Path(__file__).parent / "suggestions"
    suggestions_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{suggestion_type}_{timestamp}.txt"
    filepath = suggestions_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Suggestion générée le {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Type: {suggestion_type}\n")
        f.write(f"# IMPORTANT: Revue manuelle requise avant application\n\n")
        f.write(suggestion)

    return str(filepath)


def main_loop():
    """Boucle principale sécurisée."""
    logger.info(f"Mode: {ORCHESTRATOR_MODE}")

    if ORCHESTRATOR_MODE == "auto":
        logger.warning("⚠️ MODE AUTO ACTIVÉ - Déconseillé en production!")

    while True:
        try:
            logger.info("Vérification des logs...")
            logs = get_logs()
            logger.info(f"Récupéré {len(logs)} caractères de logs")

            analysis = analyze_errors(logs)

            if analysis["has_errors"]:
                logger.warning(f"⚠️ Erreurs détectées: {analysis['patterns']}")

                if ORCHESTRATOR_MODE == "monitoring":
                    # Mode monitoring: on signale seulement
                    logger.info("Mode monitoring - Erreurs signalées, pas d'action")

                elif ORCHESTRATOR_MODE in ("suggest", "auto"):
                    # Générer une analyse
                    try:
                        debug_prompt = read_prompt("debug")
                        debug_analysis = call_openai(debug_prompt, logs)

                        if debug_analysis:
                            logger.info("Analyse de debug générée")

                            if ORCHESTRATOR_MODE == "suggest":
                                # Sauvegarder pour revue manuelle
                                fix_prompt = read_prompt("fix")
                                fix_suggestion = call_claude(fix_prompt, debug_analysis)

                                if fix_suggestion:
                                    filepath = save_suggestion(fix_suggestion, "fix")
                                    logger.info(f"✅ Suggestion sauvegardée: {filepath}")
                                    logger.info("⚠️ REVUE MANUELLE REQUISE avant application")

                            elif ORCHESTRATOR_MODE == "auto":
                                # MODE DANGEREUX - Désactivé par sécurité
                                logger.error("❌ Mode auto désactivé pour raisons de sécurité")
                                logger.error("L'exécution automatique de code IA n'est pas autorisée")
                                # NE PAS exécuter de code généré par l'IA automatiquement

                    except FileNotFoundError as e:
                        logger.error(f"Fichier prompt non trouvé: {e}")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'analyse: {e}")

            else:
                logger.info("✅ Aucune erreur détectée")

        except Exception as e:
            logger.error(f"❌ Erreur dans la boucle principale: {e}")

        time.sleep(30)


if __name__ == "__main__":
    main_loop()
