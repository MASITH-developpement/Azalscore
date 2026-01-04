"""
AZALS - Service de classification décisionnelle
Moteur de décision critique avec règle d'irréversibilité RED
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.models import Decision, DecisionLevel, CoreAuditJournal
from fastapi import HTTPException


class DecisionService:
    """
    Service de classification décisionnelle AZALS.
    
    Règles fondamentales :
    - GREEN → ORANGE : autorisé
    - ORANGE → RED : autorisé
    - RED → * : INTERDIT (irréversible)
    - Toute décision RED est journalisée automatiquement
    """
    
    @staticmethod
    def get_current_decision(
        db: Session,
        tenant_id: str,
        entity_type: str,
        entity_id: str
    ) -> Decision | None:
        """
        Récupère la décision actuelle pour une entité donnée.
        Retourne la décision la plus récente (ORDER BY created_at DESC).
        """
        return db.query(Decision).filter(
            Decision.tenant_id == tenant_id,
            Decision.entity_type == entity_type,
            Decision.entity_id == entity_id
        ).order_by(desc(Decision.created_at)).first()
    
    @staticmethod
    def classify(
        db: Session,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        level: DecisionLevel,
        reason: str,
        user_id: int
    ) -> Decision:
        """
        Crée une nouvelle décision de classification.
        
        Validation stricte :
        - Si décision actuelle est RED → REFUSE toute nouvelle classification
        - Toute décision RED est automatiquement journalisée
        
        Args:
            db: Session SQLAlchemy
            tenant_id: Identifiant tenant
            entity_type: Type d'entité (ex: "contract", "invoice")
            entity_id: Identifiant de l'entité
            level: Niveau de décision (GREEN, ORANGE, RED)
            reason: Raison de la classification
            user_id: ID de l'utilisateur effectuant la classification
        
        Returns:
            Decision créée
        
        Raises:
            HTTPException 403 si RED existe déjà (irréversible)
        """
        # Vérification : RED est-il déjà présent ?
        current_decision = DecisionService.get_current_decision(
            db, tenant_id, entity_type, entity_id
        )
        
        if current_decision and current_decision.level == DecisionLevel.RED:
            raise HTTPException(
                status_code=403,
                detail=f"Decision RED is IRREVERSIBLE. Entity {entity_type}:{entity_id} cannot be reclassified."
            )
        
        # Création de la nouvelle décision
        new_decision = Decision(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            level=level,
            reason=reason
        )
        
        db.add(new_decision)
        db.flush()  # Flush pour obtenir l'ID avant journalisation
        
        # Si RED : journalisation obligatoire
        if level == DecisionLevel.RED:
            journal_entry = CoreAuditJournal(
                tenant_id=tenant_id,
                user_id=user_id,
                action="DECISION_RED",
                details=f"RED decision for {entity_type}:{entity_id} - Reason: {reason}"
            )
            db.add(journal_entry)
        
        db.commit()
        db.refresh(new_decision)
        
        return new_decision
    
    @staticmethod
    def is_red(
        db: Session,
        tenant_id: str,
        entity_type: str,
        entity_id: str
    ) -> bool:
        """
        Vérifie si une entité est classée RED.
        Utilisé pour bloquer des actions automatiques.
        """
        current = DecisionService.get_current_decision(
            db, tenant_id, entity_type, entity_id
        )
        return current is not None and current.level == DecisionLevel.RED
