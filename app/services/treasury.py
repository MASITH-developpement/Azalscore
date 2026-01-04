"""
AZALS - Service de calcul de trésorerie
Règle critique : trésorerie < 0 → RED automatique
"""

from sqlalchemy.orm import Session
from app.core.models import TreasuryForecast, Decision, DecisionLevel, CoreAuditJournal


class TreasuryService:
    """
    Service de calcul et gestion de trésorerie prévisionnelle.
    Déclenche automatiquement une décision RED si trésorerie négative.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_forecast(
        self,
        opening_balance: int,
        inflows: int,
        outflows: int,
        tenant_id: str,
        user_id: int
    ) -> TreasuryForecast:
        """
        Calcule la trésorerie prévisionnelle.
        
        Formule : forecast_balance = opening_balance + inflows - outflows
        
        Si forecast_balance < 0 :
        - Crée une décision RED
        - Journalise l'événement
        """
        forecast_balance = opening_balance + inflows - outflows
        
        # Créer l'enregistrement de prévision
        red_triggered_value = 1 if forecast_balance < 0 else 0
        forecast = TreasuryForecast(
            tenant_id=tenant_id,
            user_id=user_id,
            opening_balance=opening_balance,
            inflows=inflows,
            outflows=outflows,
            forecast_balance=forecast_balance,
            red_triggered=red_triggered_value
        )
        self.db.add(forecast)
        self.db.commit()
        self.db.refresh(forecast)
        
        # Décision RED automatique si trésorerie négative
        if forecast_balance < 0:
            self._trigger_red_decision(forecast.id, forecast_balance, tenant_id, user_id)
        
        return forecast
    
    def _trigger_red_decision(
        self,
        forecast_id: int,
        forecast_balance: int,
        tenant_id: str,
        user_id: int
    ) -> None:
        """
        Déclenche une décision RED pour trésorerie négative.
        Journalise automatiquement.
        """
        # Créer décision RED
        decision = Decision(
            tenant_id=tenant_id,
            entity_type="treasury_forecast",
            entity_id=str(forecast_id),
            level=DecisionLevel.RED,
            reason=f"Negative treasury forecast: {forecast_balance}"
        )
        self.db.add(decision)
        
        # Journaliser
        journal = CoreAuditJournal(
            tenant_id=tenant_id,
            user_id=user_id,
            action="TREASURY_RED_TRIGGERED",
            details=f"Forecast ID: {forecast_id}, Balance: {forecast_balance}"
        )
        self.db.add(journal)
        
        self.db.commit()
    
    def get_latest_forecast(self, tenant_id: str) -> TreasuryForecast | None:
        """Récupère la dernière prévision de trésorerie pour un tenant."""
        return self.db.query(TreasuryForecast).filter(
            TreasuryForecast.tenant_id == tenant_id
        ).order_by(TreasuryForecast.created_at.desc(), TreasuryForecast.id.desc()).first()
