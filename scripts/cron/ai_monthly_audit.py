#!/usr/bin/env python3
"""
AZALS GUARDIAN - Script Cron Audit Mensuel (Mode B)
===================================================

Script à exécuter mensuellement via cron pour générer
les rapports d'audit automatiques.

Usage cron (1er du mois à 2h):
    0 2 1 * * /app/scripts/cron/ai_monthly_audit.py

Usage manuel:
    python ai_monthly_audit.py [--year YEAR] [--month MONTH] [--tenant TENANT_ID]

RÈGLES MODE B:
- LECTURE SEULE
- AUCUNE MODIFICATION
- AUCUNE ÉCRITURE (sauf rapport)
- AUCUN REDÉMARRAGE
"""

import argparse
import os
import sys
from datetime import datetime

# Ajouter le chemin de l'application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_audit(year: int, month: int, tenant_id: str = None):
    """
    Exécute l'audit mensuel Mode B.

    Args:
        year: Année de l'audit
        month: Mois de l'audit (1-12)
        tenant_id: Tenant spécifique ou None pour global
    """
    print(f"[AI_AUDIT] ===== DÉBUT AUDIT MENSUEL =====")
    print(f"[AI_AUDIT] Période: {year}-{month:02d}")
    print(f"[AI_AUDIT] Tenant: {tenant_id or 'GLOBAL'}")
    print(f"[AI_AUDIT] Mode: LECTURE SEULE")
    print()

    # Import après path setup
    from app.core.database import SessionLocal
    from app.modules.guardian.ai_service import get_ai_guardian_service

    db = SessionLocal()

    try:
        service = get_ai_guardian_service(db, tenant_id)

        print(f"[AI_AUDIT] Démarrage de l'audit...")
        report = service.run_monthly_audit(
            year=year,
            month=month,
            tenant_id=tenant_id,
        )

        print()
        print(f"[AI_AUDIT] ===== RÉSULTAT =====")
        print(f"[AI_AUDIT] Report UID: {report.report_uid}")
        print(f"[AI_AUDIT] Statut: {report.status}")
        print(f"[AI_AUDIT] Modules audités: {report.modules_audited}")
        print(f"[AI_AUDIT] Incidents totaux: {report.total_incidents}")
        print(f"[AI_AUDIT] Incidents critiques: {report.critical_incidents}")
        print(f"[AI_AUDIT] Score moyen: {report.avg_score:.1f}" if report.avg_score else "[AI_AUDIT] Score moyen: N/A")
        print()

        if report.risks_identified:
            p1 = report.risks_identified.get("P1", [])
            p2 = report.risks_identified.get("P2", [])
            if p1:
                print(f"[AI_AUDIT] ⚠️  RISQUES P1 (critiques): {len(p1)}")
                for risk in p1:
                    print(f"[AI_AUDIT]    - {risk['module']}: {risk['reason']}")
            if p2:
                print(f"[AI_AUDIT] ⚠️  RISQUES P2 (élevés): {len(p2)}")

        print()
        print(f"[AI_AUDIT] ===== FIN AUDIT =====")
        print(f"[AI_AUDIT] Durée: {(report.completed_at - report.started_at).total_seconds():.1f}s" if report.completed_at and report.started_at else "")

        return 0 if report.status == "completed" else 1

    except Exception as e:
        print(f"[AI_AUDIT] ❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()
        print(f"[AI_AUDIT] Session DB fermée")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="AZALS Guardian - Audit Mensuel Mode B"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Année de l'audit (défaut: mois précédent)"
    )
    parser.add_argument(
        "--month",
        type=int,
        default=None,
        help="Mois de l'audit 1-12 (défaut: mois précédent)"
    )
    parser.add_argument(
        "--tenant",
        type=str,
        default=None,
        help="Tenant ID spécifique (défaut: audit global)"
    )

    args = parser.parse_args()

    # Par défaut: mois précédent
    now = datetime.utcnow()
    if args.year is None or args.month is None:
        # Mois précédent
        if now.month == 1:
            year = now.year - 1
            month = 12
        else:
            year = now.year
            month = now.month - 1
    else:
        year = args.year
        month = args.month

    # Valider
    if not (1 <= month <= 12):
        print(f"[AI_AUDIT] ❌ Mois invalide: {month}")
        sys.exit(1)

    if not (2020 <= year <= 2100):
        print(f"[AI_AUDIT] ❌ Année invalide: {year}")
        sys.exit(1)

    # Exécuter
    exit_code = run_audit(year, month, args.tenant)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
