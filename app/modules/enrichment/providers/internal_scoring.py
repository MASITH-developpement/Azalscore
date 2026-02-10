"""
AZALS MODULE - Auto-Enrichment - Internal Scoring Provider
===========================================================

Provider pour le scoring interne des particuliers basé sur
l'historique client dans AZALSCORE.

Facteurs de scoring:
- Ancienneté du compte
- Nombre de commandes
- Montant total payé
- Incidents de paiement (factures en retard)
- Taux de paiement à temps
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from .base import BaseProvider, EnrichmentResult

logger = logging.getLogger(__name__)


class InternalScoringProvider(BaseProvider):
    """
    Provider de scoring interne pour les particuliers.

    Calcule un score de risque (0-100) basé sur:
    - Historique de paiement
    - Ancienneté client
    - Volume de commandes
    - Incidents passés
    """

    PROVIDER_NAME = "internal_scoring"

    def __init__(self, tenant_id: str, db: Session):
        """
        Initialise le provider.

        Args:
            tenant_id: ID du tenant
            db: Session SQLAlchemy pour accéder aux données
        """
        super().__init__(tenant_id)
        self.db = db

    async def lookup(
        self,
        lookup_type: str,
        lookup_value: str
    ) -> EnrichmentResult:
        """
        Calcule le score interne d'un client.

        Args:
            lookup_type: 'internal_score'
            lookup_value: ID du client (UUID)

        Returns:
            EnrichmentResult avec le score et les détails
        """
        start_time = time.time()

        if lookup_type != "internal_score":
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Type non supporté: {lookup_type}",
                response_time_ms=self._measure_time(start_time),
            )

        try:
            customer_id = UUID(lookup_value)
        except ValueError:
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error="ID client invalide",
                response_time_ms=self._measure_time(start_time),
            )

        try:
            # Récupérer les données du client
            customer_data = self._get_customer_data(customer_id)

            if not customer_data:
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Client non trouvé",
                    response_time_ms=self._measure_time(start_time),
                )

            # Calculer le score
            scoring_result = self._calculate_internal_score(customer_data)

            response_time = self._measure_time(start_time)
            logger.info(
                f"[INTERNAL_SCORING] Client {lookup_value[:8]}... -> "
                f"Score: {scoring_result['score']} ({scoring_result['level']}) "
                f"({response_time}ms)"
            )

            return EnrichmentResult(
                success=True,
                data=scoring_result,
                confidence=0.9,  # Données internes fiables
                source=self.PROVIDER_NAME,
                response_time_ms=response_time,
            )

        except Exception as e:
            logger.exception(f"[INTERNAL_SCORING] Erreur: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur de calcul: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

    def _get_customer_data(self, customer_id: UUID) -> Optional[dict]:
        """
        Récupère les données du client depuis la base.

        Returns:
            Dict avec les métriques client ou None si non trouvé
        """
        # Import des modèles ici pour éviter les imports circulaires
        from app.modules.commercial.models import Customer, CommercialDocument

        # Récupérer le client
        customer = self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.tenant_id == self.tenant_id
        ).first()

        if not customer:
            return None

        # Statistiques des documents (devis, commandes, factures)
        now = datetime.utcnow()

        # Factures du client (type = 'INVOICE')
        invoices_query = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.customer_id == customer_id,
            CommercialDocument.type == 'INVOICE',
        )

        total_invoices = invoices_query.count()

        # Factures payées (status = 'PAID')
        paid_invoices = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.customer_id == customer_id,
            CommercialDocument.type == 'INVOICE',
            CommercialDocument.status == 'PAID',
        ).count()

        # Factures en retard (émises il y a plus de 30 jours et non payées)
        overdue_date = now - timedelta(days=30)
        overdue_invoices = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.customer_id == customer_id,
            CommercialDocument.type == 'INVOICE',
            CommercialDocument.status.in_(['SENT', 'DRAFT', 'VALIDATED']),
            CommercialDocument.created_at < overdue_date
        ).count()

        # Montant total facturé (utiliser 'total' au lieu de 'total_ttc')
        total_invoiced = self.db.query(
            func.coalesce(func.sum(CommercialDocument.total), 0)
        ).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.customer_id == customer_id,
            CommercialDocument.type == 'INVOICE',
        ).scalar() or 0

        # Montant payé
        total_paid = self.db.query(
            func.coalesce(func.sum(CommercialDocument.paid_amount), 0)
        ).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.customer_id == customer_id,
            CommercialDocument.type == 'INVOICE',
        ).scalar() or 0

        # Commandes (type = 'ORDER')
        total_orders = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.customer_id == customer_id,
            CommercialDocument.type == 'ORDER',
        ).count()

        # Devis (type = 'QUOTE')
        total_quotes = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.customer_id == customer_id,
            CommercialDocument.type == 'QUOTE',
        ).count()

        # Ancienneté (jours depuis création)
        account_age_days = (now - customer.created_at).days if customer.created_at else 0

        # Dernière activité
        last_doc = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.customer_id == customer_id,
        ).order_by(CommercialDocument.created_at.desc()).first()

        days_since_last_activity = None
        if last_doc and last_doc.created_at:
            days_since_last_activity = (now - last_doc.created_at).days

        return {
            "customer_id": str(customer_id),
            "customer_name": customer.name,
            "customer_type": getattr(customer, 'customer_type', 'CUSTOMER'),
            "is_company": getattr(customer, 'is_company', False),
            "account_age_days": account_age_days,
            "total_orders": total_orders,
            "total_quotes": total_quotes,
            "total_invoices": total_invoices,
            "paid_invoices": paid_invoices,
            "overdue_invoices": overdue_invoices,
            "total_invoiced": float(total_invoiced),
            "total_paid": float(total_paid),
            "outstanding": float(total_invoiced) - float(total_paid),
            "days_since_last_activity": days_since_last_activity,
        }

    def _calculate_internal_score(self, data: dict) -> dict[str, Any]:
        """
        Calcule le score de risque interne.

        Score de 0 à 100:
        - 100 = Client parfait
        - 0 = Risque maximum

        Facteurs:
        - Ancienneté: +10 max
        - Volume commandes: +15 max
        - Taux paiement: +40 max
        - Impayés en cours: -40 max
        - Régularité: +10 max
        """
        score = 50  # Score de base pour nouveau client
        factors = []
        alerts = []

        # 1. Ancienneté du compte (max +15 points)
        age_days = data.get("account_age_days", 0)
        if age_days > 365 * 3:  # Plus de 3 ans
            score += 15
            factors.append({
                "factor": f"Client fidèle ({age_days // 365} ans)",
                "impact": 15,
                "severity": "positive"
            })
        elif age_days > 365:  # Plus d'1 an
            score += 10
            factors.append({
                "factor": f"Client régulier ({age_days // 365} an(s))",
                "impact": 10,
                "severity": "positive"
            })
        elif age_days > 180:  # Plus de 6 mois
            score += 5
            factors.append({
                "factor": "Client récent (6+ mois)",
                "impact": 5,
                "severity": "positive"
            })
        elif age_days < 30:  # Nouveau client
            score -= 10
            factors.append({
                "factor": "Nouveau client (< 30 jours)",
                "impact": -10,
                "severity": "medium"
            })

        # 2. Volume de commandes (max +15 points)
        total_orders = data.get("total_orders", 0)
        total_invoices = data.get("total_invoices", 0)

        if total_invoices >= 20:
            score += 15
            factors.append({
                "factor": f"Volume élevé ({total_invoices} factures)",
                "impact": 15,
                "severity": "positive"
            })
        elif total_invoices >= 10:
            score += 10
            factors.append({
                "factor": f"Volume correct ({total_invoices} factures)",
                "impact": 10,
                "severity": "positive"
            })
        elif total_invoices >= 3:
            score += 5
            factors.append({
                "factor": f"Quelques transactions ({total_invoices} factures)",
                "impact": 5,
                "severity": "positive"
            })
        elif total_invoices == 0:
            factors.append({
                "factor": "Aucune facture - historique insuffisant",
                "impact": 0,
                "severity": "low"
            })

        # 3. Taux de paiement (max +30 points, min -30 points)
        paid = data.get("paid_invoices", 0)
        total = data.get("total_invoices", 0)

        if total > 0:
            payment_rate = (paid / total) * 100

            if payment_rate >= 95:
                score += 30
                factors.append({
                    "factor": f"Excellent payeur ({payment_rate:.0f}% payé)",
                    "impact": 30,
                    "severity": "positive"
                })
            elif payment_rate >= 80:
                score += 15
                factors.append({
                    "factor": f"Bon payeur ({payment_rate:.0f}% payé)",
                    "impact": 15,
                    "severity": "positive"
                })
            elif payment_rate >= 50:
                score -= 10
                factors.append({
                    "factor": f"Paiements irréguliers ({payment_rate:.0f}% payé)",
                    "impact": -10,
                    "severity": "medium"
                })
            else:
                score -= 30
                factors.append({
                    "factor": f"Mauvais payeur ({payment_rate:.0f}% payé)",
                    "impact": -30,
                    "severity": "high"
                })
                alerts.append("HISTORIQUE DE PAIEMENT DEFAVORABLE")

        # 4. Impayés en cours (max -40 points)
        overdue = data.get("overdue_invoices", 0)
        outstanding = data.get("outstanding", 0)

        if overdue > 0:
            if overdue >= 5:
                score -= 40
                factors.append({
                    "factor": f"{overdue} factures en retard",
                    "impact": -40,
                    "severity": "critical"
                })
                alerts.append(f"ATTENTION: {overdue} FACTURES EN RETARD")
            elif overdue >= 2:
                score -= 25
                factors.append({
                    "factor": f"{overdue} factures en retard",
                    "impact": -25,
                    "severity": "high"
                })
                alerts.append(f"{overdue} factures en retard de paiement")
            else:
                score -= 10
                factors.append({
                    "factor": "1 facture en retard",
                    "impact": -10,
                    "severity": "medium"
                })

        # 5. Montant des impayés
        if outstanding > 5000:
            score -= 15
            factors.append({
                "factor": f"Encours élevé ({outstanding:,.0f}€)",
                "impact": -15,
                "severity": "high"
            })
        elif outstanding > 1000:
            score -= 5
            factors.append({
                "factor": f"Encours modéré ({outstanding:,.0f}€)",
                "impact": -5,
                "severity": "medium"
            })
        elif outstanding <= 0 and total > 0:
            score += 5
            factors.append({
                "factor": "Aucun impayé",
                "impact": 5,
                "severity": "positive"
            })

        # 6. Activité récente
        days_inactive = data.get("days_since_last_activity")
        if days_inactive is not None:
            if days_inactive > 365:
                score -= 10
                factors.append({
                    "factor": f"Client inactif depuis {days_inactive // 30} mois",
                    "impact": -10,
                    "severity": "medium"
                })
            elif days_inactive > 180:
                score -= 5
                factors.append({
                    "factor": f"Peu actif (dernière facture il y a {days_inactive} jours)",
                    "impact": -5,
                    "severity": "low"
                })

        # Borner le score
        score = max(0, min(100, score))

        # Déterminer le niveau
        if score >= 80:
            level = "low"
            level_label = "Risque faible"
            color = "green"
        elif score >= 60:
            level = "medium"
            level_label = "Risque modéré"
            color = "yellow"
        elif score >= 40:
            level = "elevated"
            level_label = "Risque élevé"
            color = "orange"
        else:
            level = "high"
            level_label = "Risque très élevé"
            color = "red"

        return {
            "score": score,
            "level": level,
            "level_label": level_label,
            "color": color,
            "factors": factors,
            "alerts": alerts,
            "recommendation": self._get_recommendation(score, alerts, data),
            "customer_name": data.get("customer_name", ""),
            "metrics": {
                "account_age_days": data.get("account_age_days", 0),
                "total_orders": data.get("total_orders", 0),
                "total_invoices": data.get("total_invoices", 0),
                "paid_invoices": data.get("paid_invoices", 0),
                "overdue_invoices": data.get("overdue_invoices", 0),
                "total_invoiced": data.get("total_invoiced", 0),
                "total_paid": data.get("total_paid", 0),
                "outstanding": data.get("outstanding", 0),
            },
            "_source": "internal_scoring"
        }

    def _get_recommendation(
        self,
        score: int,
        alerts: list[str],
        data: dict
    ) -> str:
        """Génère une recommandation basée sur le score."""
        outstanding = data.get("outstanding", 0)
        overdue = data.get("overdue_invoices", 0)

        if overdue >= 3:
            return "STOP - Régularisation des impayés nécessaire avant nouvelle commande"
        elif score >= 80:
            return "Client de confiance - Conditions standard"
        elif score >= 60:
            if outstanding > 1000:
                return "Limiter l'encours - Surveiller les paiements"
            return "Relations normales - Surveillance légère"
        elif score >= 40:
            return "Prudence - Demander un acompte ou paiement anticipé"
        else:
            return "Risque élevé - Paiement comptant requis"

    def map_to_entity(
        self,
        entity_type: str,
        api_data: dict
    ) -> dict[str, Any]:
        """Mappe le résultat au format enrichissement standard."""
        return {
            "risk_score": api_data.get("score"),
            "risk_level": api_data.get("level"),
            "risk_level_label": api_data.get("level_label"),
            "risk_alerts": api_data.get("alerts", []),
            "risk_recommendation": api_data.get("recommendation"),
            "_internal_scoring": api_data,
        }
