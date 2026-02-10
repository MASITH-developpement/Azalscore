#!/usr/bin/env python3
"""
AZALS GUARDIAN - Script Cron Métriques SLA (Mode C)
===================================================

Script à exécuter régulièrement pour calculer les métriques SLA.

Usage cron:
    # Toutes les heures
    0 * * * * /app/scripts/cron/ai_sla_metrics.py --period hourly

    # Tous les jours à minuit
    0 0 * * * /app/scripts/cron/ai_sla_metrics.py --period daily

    # Toutes les semaines (dimanche minuit)
    0 0 * * 0 /app/scripts/cron/ai_sla_metrics.py --period weekly

    # Tous les mois (1er à minuit)
    0 0 1 * * /app/scripts/cron/ai_sla_metrics.py --period monthly

Usage manuel:
    python ai_sla_metrics.py --period daily [--tenant TENANT_ID]

MODE C:
- Calcul indicateurs objectifs
- Données horodatées et auditables
- AUCUNE action technique
- AUCUNE décision business
"""

import argparse
import os
import sys
from datetime import datetime

# Ajouter le chemin de l'application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def calculate_sla(period_type: str, tenant_id: str = None):
    """
    Calcule les métriques SLA Mode C.

    Args:
        period_type: hourly, daily, weekly, monthly
        tenant_id: Tenant spécifique ou None pour global
    """
    print(f"[AI_SLA] ===== CALCUL MÉTRIQUES SLA =====")
    print(f"[AI_SLA] Période: {period_type}")
    print(f"[AI_SLA] Tenant: {tenant_id or 'GLOBAL'}")
    print(f"[AI_SLA] Timestamp: {datetime.utcnow().isoformat()}")
    print()

    # Import après path setup
    from app.core.database import SessionLocal
    from app.modules.guardian.ai_service import get_ai_guardian_service

    db = SessionLocal()

    try:
        service = get_ai_guardian_service(db, tenant_id)

        print(f"[AI_SLA] Calcul en cours...")
        metric = service.calculate_sla_metrics(period_type=period_type)

        print()
        print(f"[AI_SLA] ===== RÉSULTAT =====")
        print(f"[AI_SLA] Metric UID: {metric.metric_uid}")
        print(f"[AI_SLA] Période: {metric.period_start} -> {metric.period_end}")
        print()
        print(f"[AI_SLA] DISPONIBILITÉ:")
        print(f"[AI_SLA]   Uptime: {metric.uptime_percent:.2f}%")
        print(f"[AI_SLA]   Downtime: {metric.downtime_minutes} minutes")
        print()
        print(f"[AI_SLA] INCIDENTS:")
        print(f"[AI_SLA]   Total: {metric.total_incidents}")
        print(f"[AI_SLA]   Rollbacks: {metric.rollback_count} ({metric.rollback_rate:.1f}%)")
        print(f"[AI_SLA]   Sécurité: {metric.security_incidents}")
        print()
        print(f"[AI_SLA] PERFORMANCE:")
        print(f"[AI_SLA]   Temps résolution moyen: {metric.avg_resolution_time_ms or 'N/A'} ms")
        print()
        print(f"[AI_SLA] CONFORMITÉ:")
        print(f"[AI_SLA]   Isolation tenant: {'✅' if metric.tenant_isolation_verified else '❌'}")
        print(f"[AI_SLA]   Intégrité données: {metric.data_integrity_score:.1f}/100")
        print()
        print(f"[AI_SLA] ===== FIN CALCUL =====")

        return 0

    except Exception as e:
        print(f"[AI_SLA] ❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()
        print(f"[AI_SLA] Session DB fermée")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="AZALS Guardian - Métriques SLA Mode C"
    )
    parser.add_argument(
        "--period",
        type=str,
        default="daily",
        choices=["hourly", "daily", "weekly", "monthly"],
        help="Type de période (défaut: daily)"
    )
    parser.add_argument(
        "--tenant",
        type=str,
        default=None,
        help="Tenant ID spécifique (défaut: calcul global)"
    )

    args = parser.parse_args()

    exit_code = calculate_sla(args.period, args.tenant)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
