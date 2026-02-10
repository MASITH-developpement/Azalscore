"""
AZALS - MODULE IA TRANSVERSE - Service
========================================
Logique métier pour l'assistant IA.

Principes fondamentaux:
- IA assistante, JAMAIS décisionnaire finale
- Double confirmation pour points rouges critiques
- Traçabilité complète de tous les échanges
- Apprentissage transversal anonymisé
"""

import hashlib
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from .models import (
    AIAnalysis,
    AIAuditLog,
    AIConfiguration,
    AIConversation,
    AIDecisionSupport,
    AIFeedback,
    AILearningData,
    AIMessage,
    AIPrediction,
    AIRiskAlert,
)
from .schemas import (
    AIConfigUpdate,
    AnalysisRequest,
    ConversationCreate,
    DecisionConfirmation,
    DecisionSupportCreate,
    FeedbackCreate,
    MessageCreate,
    PredictionRequest,
    RiskAcknowledge,
    RiskAlertCreate,
    RiskResolve,
    SynthesisRequest,
)


class AIAssistantService:
    """Service IA Transverse Opérationnelle."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    def get_config(self) -> AIConfiguration:
        """Récupérer configuration IA."""
        config = self.db.query(AIConfiguration).filter(
            AIConfiguration.tenant_id == self.tenant_id
        ).first()

        if not config:
            config = AIConfiguration(
                tenant_id=self.tenant_id,
                is_enabled=True,
                enabled_features=["question", "analysis", "risk_detection", "prediction"],
                daily_request_limit=1000,
                response_language="fr",
                formality_level="professional",
                detail_level="balanced",
                require_confirmation_threshold="high",
                auto_escalation_enabled=True,
                notify_on_risk=True,
                notify_on_anomaly=True
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)

        return config

    def update_config(self, user_id: int, data: AIConfigUpdate) -> AIConfiguration:
        """Mettre à jour configuration."""
        config = self.get_config()

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        config.updated_at = datetime.utcnow()
        config.updated_by = user_id

        self._log_action(user_id, "config_update", "configuration", config.id)

        self.db.commit()
        self.db.refresh(config)
        return config

    def is_feature_enabled(self, feature: str) -> bool:
        """Vérifier si une fonctionnalité est activée."""
        config = self.get_config()
        if not config.is_enabled:
            return False
        if not config.enabled_features:
            return True
        return feature in config.enabled_features

    # ========================================================================
    # CONVERSATIONS
    # ========================================================================

    def create_conversation(
        self, user_id: int, data: ConversationCreate
    ) -> AIConversation:
        """Créer une nouvelle conversation."""
        conversation = AIConversation(
            tenant_id=self.tenant_id,
            user_id=user_id,
            title=data.title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            context=data.context,
            module_source=data.module_source,
            is_active=True,
            message_count=0
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        self._log_action(user_id, "conversation_create", "conversation", conversation.id)

        return conversation

    def get_conversation(self, conversation_id: int) -> AIConversation | None:
        """Récupérer une conversation."""
        return self.db.query(AIConversation).filter(
            AIConversation.tenant_id == self.tenant_id,
            AIConversation.id == conversation_id
        ).first()

    def list_conversations(
        self, user_id: int, active_only: bool = True,
        skip: int = 0, limit: int = 50
    ) -> list[AIConversation]:
        """Lister les conversations d'un utilisateur."""
        query = self.db.query(AIConversation).filter(
            AIConversation.tenant_id == self.tenant_id,
            AIConversation.user_id == user_id
        )
        if active_only:
            query = query.filter(AIConversation.is_active)

        return query.order_by(
            AIConversation.last_activity.desc()
        ).offset(skip).limit(limit).all()

    def add_message(
        self, conversation_id: int, user_id: int, data: MessageCreate
    ) -> tuple[AIMessage, AIMessage]:
        """Ajouter un message et générer une réponse."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError("Conversation introuvable")

        # Message utilisateur
        user_message = AIMessage(
            tenant_id=self.tenant_id,
            conversation_id=conversation_id,
            role="user",
            request_type=data.request_type,
            content=data.content,
            message_metadata=data.context,
            status="completed"
        )
        self.db.add(user_message)

        # Générer réponse IA
        start_time = datetime.utcnow()
        response_content = self._generate_response(data.content, data.request_type, data.context)
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        assistant_message = AIMessage(
            tenant_id=self.tenant_id,
            conversation_id=conversation_id,
            role="assistant",
            request_type=data.request_type,
            content=response_content,
            processing_time_ms=processing_time,
            status="completed"
        )
        self.db.add(assistant_message)

        # Mettre à jour conversation
        conversation.message_count += 2
        conversation.last_activity = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user_message)
        self.db.refresh(assistant_message)

        # Apprentissage anonymisé
        self._record_learning_data("conversation", data.request_type, {
            "request_length": len(data.content),
            "response_length": len(response_content),
            "processing_time": processing_time
        })

        return user_message, assistant_message

    def _generate_response(
        self, question: str, request_type: str, context: dict | None = None
    ) -> str:
        """Générer une réponse IA (placeholder pour intégration LLM)."""
        # TODO: Intégrer avec un vrai LLM (GPT, Claude, etc.)
        # Pour l'instant, réponse structurée basique

        if request_type == "question":
            return self._generate_question_response(question, context)
        elif request_type == "analysis":
            return self._generate_analysis_response(question, context)
        elif request_type == "recommendation":
            return self._generate_recommendation_response(question, context)
        elif request_type == "risk_detection":
            return self._generate_risk_response(question, context)
        elif request_type == "synthesis":
            return self._generate_synthesis_response(question, context)
        else:
            return self._generate_generic_response(question, context)

    def _generate_question_response(self, question: str, context: dict | None) -> str:
        """Générer réponse à une question."""
        return f"""**Analyse de votre question**

Votre question : "{question[:100]}..."

**Éléments de réponse :**
Je suis l'assistant IA AZALS. Pour répondre précisément à votre question,
j'aurais besoin d'accéder aux données pertinentes de votre système.

**Prochaines étapes suggérées :**
1. Préciser le contexte de votre demande
2. Indiquer les modules concernés
3. Spécifier la période si applicable

*Note : Cette réponse est générée par l'IA. Toute décision importante
doit être validée par un responsable humain.*"""

    def _generate_analysis_response(self, question: str, context: dict | None) -> str:
        """Générer réponse d'analyse."""
        return f"""**Analyse demandée**

Demande : "{question[:100]}..."

**Méthodologie d'analyse :**
1. Collecte des données pertinentes
2. Analyse statistique
3. Identification des tendances
4. Détection des anomalies

**Résultats préliminaires :**
L'analyse complète nécessite l'accès aux données du module concerné.

**Recommandations :**
- Vérifier l'exactitude des données sources
- Valider les hypothèses avec les experts métier
- Confirmer les conclusions avant action

*⚠️ Cette analyse est une aide à la décision. La décision finale
revient au responsable désigné.*"""

    def _generate_recommendation_response(self, question: str, context: dict | None) -> str:
        """Générer recommandation."""
        return f"""**Recommandation IA**

Contexte : "{question[:100]}..."

**Options identifiées :**
1. Option A - [À définir selon données]
2. Option B - [À définir selon données]
3. Option C - [À définir selon données]

**Recommandation :**
Une recommandation précise nécessite l'analyse des données spécifiques.

**Points d'attention :**
- Évaluer les risques de chaque option
- Considérer l'impact à court et long terme
- Consulter les parties prenantes

*⚠️ IMPORTANT : Cette recommandation est une aide. La décision finale
appartient au dirigeant/responsable.*"""

    def _generate_risk_response(self, question: str, context: dict | None) -> str:
        """Générer analyse de risque."""
        return f"""**Analyse des risques**

Contexte : "{question[:100]}..."

**Catégories de risques évaluées :**
- Risque financier : À évaluer
- Risque opérationnel : À évaluer
- Risque juridique : À évaluer
- Risque réglementaire : À évaluer

**Méthodologie :**
1. Identification des risques potentiels
2. Évaluation probabilité/impact
3. Priorisation
4. Mesures d'atténuation

*⚠️ Cette analyse doit être validée par un expert.*"""

    def _generate_synthesis_response(self, question: str, context: dict | None) -> str:
        """Générer synthèse."""
        return f"""**Synthèse**

Demande : "{question[:100]}..."

**Points clés :**
- [Données à collecter]
- [Tendances à analyser]
- [Actions à considérer]

**Conclusion :**
La synthèse complète sera disponible après analyse des données.

*Document généré par IA - À valider par le responsable.*"""

    def _generate_generic_response(self, question: str, context: dict | None) -> str:
        """Générer réponse générique."""
        return f"""**Réponse de l'assistant AZALS**

J'ai bien reçu votre demande : "{question[:100]}..."

Je suis là pour vous aider avec :
- Questions sur vos données
- Analyses et synthèses
- Détection de risques
- Recommandations (non décisionnelles)

Comment puis-je vous aider plus précisément ?

*Note : Je suis un assistant IA. Les décisions importantes
doivent être validées par les responsables humains.*"""

    # ========================================================================
    # ANALYSES
    # ========================================================================

    def create_analysis(self, user_id: int, data: AnalysisRequest) -> AIAnalysis:
        """Créer une analyse."""
        analysis_code = f"ANA-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        analysis = AIAnalysis(
            tenant_id=self.tenant_id,
            user_id=user_id,
            analysis_code=analysis_code,
            title=data.title,
            description=data.description,
            analysis_type=data.analysis_type,
            module_source=data.module_source,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            data_period_start=data.data_period_start,
            data_period_end=data.data_period_end,
            input_data=data.parameters,
            status="processing"
        )
        self.db.add(analysis)
        self.db.flush()

        # Exécuter l'analyse
        self._execute_analysis(analysis)

        self.db.commit()
        self.db.refresh(analysis)

        self._log_action(user_id, "analysis_create", "analysis", analysis.id)

        return analysis

    def _execute_analysis(self, analysis: AIAnalysis) -> None:
        """Exécuter l'analyse."""
        # TODO: Implémenter logique d'analyse réelle selon type
        findings = []
        recommendations = []
        risks = []

        if analysis.analysis_type == "360":
            findings, recommendations, risks = self._analysis_360(analysis)
        elif analysis.analysis_type == "financial":
            findings, recommendations, risks = self._analysis_financial(analysis)
        elif analysis.analysis_type == "operational":
            findings, recommendations, risks = self._analysis_operational(analysis)
        elif analysis.analysis_type == "risk":
            findings, recommendations, risks = self._analysis_risk(analysis)

        analysis.findings = findings
        analysis.recommendations = recommendations
        analysis.risks_identified = risks
        analysis.confidence_score = 0.75
        analysis.status = "completed"
        analysis.summary = f"Analyse {analysis.analysis_type} complétée. {len(findings)} constats, {len(recommendations)} recommandations."

        if risks:
            max_level = max(r.get("level", "low") for r in risks)
            analysis.overall_risk_level = max_level

    def _analysis_360(self, analysis: AIAnalysis) -> tuple[list, list, list]:
        """Analyse 360° complète."""
        findings = [
            {"category": "general", "title": "Vue d'ensemble", "description": "Analyse globale de l'entité", "severity": "info"}
        ]
        recommendations = [
            {"priority": 1, "title": "Revue périodique", "description": "Maintenir une revue régulière des indicateurs clés"}
        ]
        risks = []
        return findings, recommendations, risks

    def _analysis_financial(self, analysis: AIAnalysis) -> tuple[list, list, list]:
        """Analyse financière."""
        findings = [
            {"category": "financial", "title": "Situation financière", "description": "État des finances", "severity": "info"}
        ]
        recommendations = [
            {"priority": 1, "title": "Suivi trésorerie", "description": "Surveiller la position de trésorerie"}
        ]
        risks = []
        return findings, recommendations, risks

    def _analysis_operational(self, analysis: AIAnalysis) -> tuple[list, list, list]:
        """Analyse opérationnelle."""
        findings = [
            {"category": "operational", "title": "Performance opérationnelle", "description": "État des opérations", "severity": "info"}
        ]
        recommendations = [
            {"priority": 1, "title": "Optimisation processus", "description": "Identifier les goulots d'étranglement"}
        ]
        risks = []
        return findings, recommendations, risks

    def _analysis_risk(self, analysis: AIAnalysis) -> tuple[list, list, list]:
        """Analyse des risques."""
        findings = [
            {"category": "risk", "title": "Cartographie des risques", "description": "Identification des risques", "severity": "warning"}
        ]
        recommendations = [
            {"priority": 1, "title": "Plan de mitigation", "description": "Élaborer des plans de contingence"}
        ]
        risks = [
            {"category": "operational", "level": "medium", "description": "Risques opérationnels identifiés"}
        ]
        return findings, recommendations, risks

    def get_analysis(self, analysis_id: int) -> AIAnalysis | None:
        """Récupérer une analyse."""
        return self.db.query(AIAnalysis).filter(
            AIAnalysis.tenant_id == self.tenant_id,
            AIAnalysis.id == analysis_id
        ).first()

    def list_analyses(
        self, user_id: int | None = None,
        analysis_type: str | None = None,
        skip: int = 0, limit: int = 50
    ) -> list[AIAnalysis]:
        """Lister les analyses."""
        query = self.db.query(AIAnalysis).filter(
            AIAnalysis.tenant_id == self.tenant_id
        )
        if user_id:
            query = query.filter(AIAnalysis.user_id == user_id)
        if analysis_type:
            query = query.filter(AIAnalysis.analysis_type == analysis_type)

        return query.order_by(AIAnalysis.created_at.desc()).offset(skip).limit(limit).all()

    # ========================================================================
    # DECISION SUPPORT (AIDE À LA DÉCISION)
    # ========================================================================

    def create_decision_support(
        self, user_id: int, data: DecisionSupportCreate
    ) -> AIDecisionSupport:
        """Créer un support de décision."""
        decision_code = f"DEC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Déterminer si c'est un point rouge
        is_red_point = self._evaluate_red_point(data)

        decision = AIDecisionSupport(
            tenant_id=self.tenant_id,
            decision_code=decision_code,
            title=data.title,
            description=data.description,
            decision_type=data.decision_type,
            module_source=data.module_source,
            priority=data.priority,
            deadline=data.deadline,
            analysis_id=data.analysis_id,
            is_red_point=is_red_point,
            requires_double_confirmation=is_red_point,
            status="pending_review",
            created_by_id=user_id
        )
        self.db.add(decision)
        self.db.flush()

        # Générer options et recommandations
        self._generate_decision_options(decision, data.context)

        self.db.commit()
        self.db.refresh(decision)

        self._log_action(user_id, "decision_create", "decision", decision.id)

        return decision

    def _evaluate_red_point(self, data: DecisionSupportCreate) -> bool:
        """Évaluer si la décision est un point rouge critique."""
        # Critères de point rouge :
        # - Impact financier majeur
        # - Impact juridique/réglementaire
        # - Irréversibilité
        # - Urgence critique

        red_keywords = [
            "licenciement", "fermeture", "cession", "acquisition",
            "contentieux", "fraude", "violation", "urgence",
            "irréversible", "critique", "majeur"
        ]

        text = f"{data.title} {data.description or ''} {data.decision_type}".lower()
        return any(keyword in text for keyword in red_keywords)

    def _generate_decision_options(
        self, decision: AIDecisionSupport, context: dict | None = None
    ) -> None:
        """Générer les options de décision."""
        # Options par défaut (à personnaliser selon le contexte)
        decision.options = [
            {
                "index": 0,
                "title": "Option 1 - Approche conservatrice",
                "description": "Maintenir le statu quo avec ajustements mineurs",
                "pros": ["Risque minimal", "Continuité assurée"],
                "cons": ["Opportunités potentiellement manquées"],
                "risk_level": "low"
            },
            {
                "index": 1,
                "title": "Option 2 - Approche modérée",
                "description": "Changements progressifs et contrôlés",
                "pros": ["Équilibre risque/bénéfice", "Adaptabilité"],
                "cons": ["Résultats plus lents"],
                "risk_level": "medium"
            },
            {
                "index": 2,
                "title": "Option 3 - Approche ambitieuse",
                "description": "Transformation significative",
                "pros": ["Fort potentiel de gains"],
                "cons": ["Risques plus élevés", "Ressources importantes"],
                "risk_level": "high"
            }
        ]
        decision.recommended_option = 1
        decision.recommendation_rationale = "L'approche modérée offre le meilleur équilibre entre risque et opportunité dans le contexte actuel."
        decision.risk_level = "medium"

    def get_decision(self, decision_id: int) -> AIDecisionSupport | None:
        """Récupérer un support de décision."""
        return self.db.query(AIDecisionSupport).filter(
            AIDecisionSupport.tenant_id == self.tenant_id,
            AIDecisionSupport.id == decision_id
        ).first()

    def list_pending_decisions(
        self, skip: int = 0, limit: int = 50
    ) -> list[AIDecisionSupport]:
        """Lister les décisions en attente."""
        return self.db.query(AIDecisionSupport).filter(
            AIDecisionSupport.tenant_id == self.tenant_id,
            AIDecisionSupport.status.in_(["pending_review", "pending_confirmation"])
        ).order_by(
            AIDecisionSupport.is_red_point.desc(),
            AIDecisionSupport.deadline.asc()
        ).offset(skip).limit(limit).all()

    def confirm_decision(
        self, decision_id: int, user_id: int, data: DecisionConfirmation
    ) -> AIDecisionSupport:
        """Confirmer une décision."""
        decision = self.get_decision(decision_id)
        if not decision:
            raise ValueError("Décision introuvable")

        if decision.status not in ["pending_review", "pending_confirmation"]:
            raise ValueError("Cette décision n'est pas en attente de confirmation")

        # Gestion double confirmation pour points rouges
        if decision.requires_double_confirmation:
            if not decision.first_confirmation_by:
                # Première confirmation
                decision.first_confirmation_by = user_id
                decision.first_confirmation_at = datetime.utcnow()
                decision.status = "pending_confirmation"
                decision.decision_made = data.decision_made
                decision.decision_notes = data.notes
            elif decision.first_confirmation_by != user_id:
                # Deuxième confirmation (par une personne différente)
                decision.second_confirmation_by = user_id
                decision.second_confirmation_at = datetime.utcnow()
                decision.decided_by_id = user_id
                decision.decided_at = datetime.utcnow()
                decision.status = "confirmed"
            else:
                raise ValueError("La double confirmation doit être effectuée par deux personnes différentes")
        else:
            # Confirmation simple
            decision.decided_by_id = user_id
            decision.decided_at = datetime.utcnow()
            decision.decision_made = data.decision_made
            decision.decision_notes = data.notes
            decision.status = "confirmed"

        self._log_action(user_id, "decision_confirm", "decision", decision.id)

        self.db.commit()
        self.db.refresh(decision)
        return decision

    def reject_decision(
        self, decision_id: int, user_id: int, reason: str
    ) -> AIDecisionSupport:
        """Rejeter une décision."""
        decision = self.get_decision(decision_id)
        if not decision:
            raise ValueError("Décision introuvable")

        decision.status = "rejected"
        decision.decided_by_id = user_id
        decision.decided_at = datetime.utcnow()
        decision.decision_notes = f"REJETÉ: {reason}"

        self._log_action(user_id, "decision_reject", "decision", decision.id)

        self.db.commit()
        self.db.refresh(decision)
        return decision

    # ========================================================================
    # RISK DETECTION
    # ========================================================================

    def create_risk_alert(self, data: RiskAlertCreate) -> AIRiskAlert:
        """Créer une alerte de risque."""
        alert_code = f"RISK-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        alert = AIRiskAlert(
            tenant_id=self.tenant_id,
            alert_code=alert_code,
            title=data.title,
            description=data.description,
            category=data.category,
            subcategory=data.subcategory,
            risk_level=data.risk_level,
            probability=data.probability,
            impact_score=data.impact_score,
            detection_source=data.detection_source,
            trigger_data=data.trigger_data,
            affected_entities=data.affected_entities,
            recommended_actions=data.recommended_actions,
            status="active"
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        self._log_action(None, "risk_detected", "risk", alert.id)

        return alert

    def detect_risks(self, module: str, data: dict) -> list[AIRiskAlert]:
        """Détecter automatiquement les risques."""
        alerts = []

        # TODO: Implémenter détection de risques par module
        # Exemples de règles de détection :

        if module == "finance":
            alerts.extend(self._detect_financial_risks(data))
        elif module == "hr":
            alerts.extend(self._detect_hr_risks(data))
        elif module == "commercial":
            alerts.extend(self._detect_commercial_risks(data))
        elif module == "compliance":
            alerts.extend(self._detect_compliance_risks(data))

        return alerts

    def _detect_financial_risks(self, data: dict) -> list[AIRiskAlert]:
        """Détecter risques financiers."""
        alerts = []
        # Logique de détection à implémenter
        return alerts

    def _detect_hr_risks(self, data: dict) -> list[AIRiskAlert]:
        """Détecter risques RH."""
        alerts = []
        return alerts

    def _detect_commercial_risks(self, data: dict) -> list[AIRiskAlert]:
        """Détecter risques commerciaux."""
        alerts = []
        return alerts

    def _detect_compliance_risks(self, data: dict) -> list[AIRiskAlert]:
        """Détecter risques conformité."""
        alerts = []
        return alerts

    def get_risk_alert(self, alert_id: int) -> AIRiskAlert | None:
        """Récupérer une alerte."""
        return self.db.query(AIRiskAlert).filter(
            AIRiskAlert.tenant_id == self.tenant_id,
            AIRiskAlert.id == alert_id
        ).first()

    def list_active_risks(
        self, category: str | None = None,
        level: str | None = None,
        skip: int = 0, limit: int = 50
    ) -> list[AIRiskAlert]:
        """Lister les risques actifs."""
        query = self.db.query(AIRiskAlert).filter(
            AIRiskAlert.tenant_id == self.tenant_id,
            AIRiskAlert.status == "active"
        )
        if category:
            query = query.filter(AIRiskAlert.category == category)
        if level:
            query = query.filter(AIRiskAlert.risk_level == level)

        return query.order_by(
            AIRiskAlert.risk_level.desc(),
            AIRiskAlert.detected_at.desc()
        ).offset(skip).limit(limit).all()

    def acknowledge_risk(
        self, alert_id: int, user_id: int, data: RiskAcknowledge
    ) -> AIRiskAlert:
        """Accuser réception d'un risque."""
        alert = self.get_risk_alert(alert_id)
        if not alert:
            raise ValueError("Alerte introuvable")

        alert.status = "acknowledged"
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()

        self._log_action(user_id, "risk_acknowledge", "risk", alert.id)

        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve_risk(
        self, alert_id: int, user_id: int, data: RiskResolve
    ) -> AIRiskAlert:
        """Résoudre un risque."""
        alert = self.get_risk_alert(alert_id)
        if not alert:
            raise ValueError("Alerte introuvable")

        alert.status = "resolved"
        alert.resolved_by = user_id
        alert.resolved_at = datetime.utcnow()
        alert.resolution_notes = data.resolution_notes

        self._log_action(user_id, "risk_resolve", "risk", alert.id)

        self.db.commit()
        self.db.refresh(alert)
        return alert

    # ========================================================================
    # PREDICTIONS
    # ========================================================================

    def create_prediction(self, user_id: int, data: PredictionRequest) -> AIPrediction:
        """Créer une prédiction."""
        prediction_code = f"PRED-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        prediction = AIPrediction(
            tenant_id=self.tenant_id,
            prediction_code=prediction_code,
            title=data.title,
            prediction_type=data.prediction_type,
            target_metric=data.target_metric,
            module_source=data.module_source,
            prediction_start=data.prediction_start,
            prediction_end=data.prediction_end,
            granularity=data.granularity,
            model_parameters=data.parameters,
            status="processing"
        )
        self.db.add(prediction)
        self.db.flush()

        # Exécuter la prédiction
        self._execute_prediction(prediction)

        self.db.commit()
        self.db.refresh(prediction)

        self._log_action(user_id, "prediction_create", "prediction", prediction.id)

        return prediction

    def _execute_prediction(self, prediction: AIPrediction) -> None:
        """Exécuter la prédiction."""
        # TODO: Implémenter modèles de prédiction réels
        # Pour l'instant, données exemple

        prediction.predicted_values = [
            {"date": prediction.prediction_start.isoformat(), "value": 100, "confidence": 0.8}
        ]
        prediction.confidence_score = 0.75
        prediction.status = "active"

    def get_prediction(self, prediction_id: int) -> AIPrediction | None:
        """Récupérer une prédiction."""
        return self.db.query(AIPrediction).filter(
            AIPrediction.tenant_id == self.tenant_id,
            AIPrediction.id == prediction_id
        ).first()

    def list_predictions(
        self, prediction_type: str | None = None,
        skip: int = 0, limit: int = 50
    ) -> list[AIPrediction]:
        """Lister les prédictions."""
        query = self.db.query(AIPrediction).filter(
            AIPrediction.tenant_id == self.tenant_id
        )
        if prediction_type:
            query = query.filter(AIPrediction.prediction_type == prediction_type)

        return query.order_by(AIPrediction.created_at.desc()).offset(skip).limit(limit).all()

    # ========================================================================
    # FEEDBACK & LEARNING
    # ========================================================================

    def add_feedback(self, user_id: int, data: FeedbackCreate) -> AIFeedback:
        """Ajouter un feedback."""
        feedback = AIFeedback(
            tenant_id=self.tenant_id,
            user_id=user_id,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            rating=data.rating,
            is_helpful=data.is_helpful,
            is_accurate=data.is_accurate,
            feedback_text=data.feedback_text,
            improvement_suggestion=data.improvement_suggestion,
            feedback_category=data.feedback_category
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)

        # Mettre à jour données d'apprentissage
        self._update_learning_from_feedback(feedback)

        return feedback

    def _update_learning_from_feedback(self, feedback: AIFeedback) -> None:
        """Mettre à jour l'apprentissage depuis le feedback."""
        if feedback.rating:
            self._record_learning_data(
                feedback.reference_type,
                "feedback",
                {"rating": feedback.rating, "is_helpful": feedback.is_helpful}
            )

    def _record_learning_data(
        self, data_type: str, category: str, pattern_data: dict
    ) -> None:
        """Enregistrer données d'apprentissage anonymisées."""
        # Créer hash pour anonymisation
        data_str = f"{data_type}:{category}:{str(sorted(pattern_data.items()))}"
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        existing = self.db.query(AILearningData).filter(
            AILearningData.data_hash == data_hash
        ).first()

        if existing:
            existing.usage_count += 1
            existing.last_seen = datetime.utcnow()
        else:
            learning = AILearningData(
                data_hash=data_hash,
                data_type=data_type,
                category=category,
                pattern_data=pattern_data,
                usage_count=1
            )
            self.db.add(learning)

    # ========================================================================
    # SYNTHESIS
    # ========================================================================

    def generate_synthesis(self, user_id: int, data: SynthesisRequest) -> dict[str, Any]:
        """Générer une synthèse."""
        # TODO: Implémenter synthèse réelle basée sur données
        synthesis = {
            "title": data.title,
            "period": f"{data.period_start} - {data.period_end}" if data.period_start else data.synthesis_type,
            "executive_summary": "Synthèse des activités sur la période demandée.",
            "key_metrics": {
                "revenue": "N/A",
                "orders": "N/A",
                "customers": "N/A"
            },
            "highlights": [
                "Point positif 1",
                "Point positif 2"
            ],
            "concerns": [
                "Point d'attention 1"
            ],
            "action_items": [
                "Action à entreprendre 1",
                "Action à entreprendre 2"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }

        self._log_action(user_id, "synthesis_generate", "synthesis", None)

        return synthesis

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> dict[str, Any]:
        """Statistiques IA."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_conversations = self.db.query(AIConversation).filter(
            AIConversation.tenant_id == self.tenant_id
        ).count()

        total_messages = self.db.query(AIMessage).filter(
            AIMessage.tenant_id == self.tenant_id
        ).count()

        total_analyses = self.db.query(AIAnalysis).filter(
            AIAnalysis.tenant_id == self.tenant_id
        ).count()

        pending_decisions = self.db.query(AIDecisionSupport).filter(
            AIDecisionSupport.tenant_id == self.tenant_id,
            AIDecisionSupport.status.in_(["pending_review", "pending_confirmation"])
        ).count()

        active_risks = self.db.query(AIRiskAlert).filter(
            AIRiskAlert.tenant_id == self.tenant_id,
            AIRiskAlert.status == "active"
        ).count()

        critical_risks = self.db.query(AIRiskAlert).filter(
            AIRiskAlert.tenant_id == self.tenant_id,
            AIRiskAlert.status == "active",
            AIRiskAlert.risk_level == "critical"
        ).count()

        requests_today = self.db.query(AIMessage).filter(
            AIMessage.tenant_id == self.tenant_id,
            AIMessage.role == "user",
            AIMessage.created_at >= today_start
        ).count()

        avg_response_time = self.db.query(func.avg(AIMessage.processing_time_ms)).filter(
            AIMessage.tenant_id == self.tenant_id,
            AIMessage.role == "assistant",
            AIMessage.processing_time_ms is not None
        ).scalar() or 0

        avg_rating = self.db.query(func.avg(AIFeedback.rating)).filter(
            AIFeedback.tenant_id == self.tenant_id,
            AIFeedback.rating is not None
        ).scalar() or 0

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_analyses": total_analyses,
            "pending_decisions": pending_decisions,
            "active_risks": active_risks,
            "critical_risks": critical_risks,
            "requests_today": requests_today,
            "avg_response_time_ms": round(float(avg_response_time), 2),
            "avg_satisfaction_rating": round(float(avg_rating), 2),
            "predictions_accuracy": 0.0  # À calculer avec données réelles
        }

    def health_check(self) -> dict[str, Any]:
        """Vérification santé IA."""
        start = datetime.utcnow()

        features_status = {}
        try:
            self.get_config()
            features_status["configuration"] = "healthy"
        except Exception as e:
            logger.warning(
                "[AI_HEALTH] Configuration check failed",
                extra={"error": str(e)[:300], "consequence": "feature_unhealthy"}
            )
            features_status["configuration"] = "unhealthy"

        try:
            self.db.execute("SELECT 1")
            features_status["database"] = "healthy"
        except Exception as e:
            logger.error(
                "[AI_HEALTH_DB] Database health check failed",
                extra={"error": str(e)[:300], "consequence": "database_unhealthy"}
            )
            features_status["database"] = "unhealthy"

        features_status["nlp_engine"] = "healthy"  # Placeholder
        features_status["prediction_engine"] = "healthy"  # Placeholder

        response_time = int((datetime.utcnow() - start).total_seconds() * 1000)

        overall = "healthy"
        if any(s == "unhealthy" for s in features_status.values()):
            overall = "degraded"

        return {
            "status": overall,
            "response_time_ms": response_time,
            "features_status": features_status,
            "last_error": None,
            "uptime_percent": 99.9
        }

    # ========================================================================
    # AUDIT
    # ========================================================================

    def _log_action(
        self, user_id: int | None, action: str,
        reference_type: str | None, reference_id: int | None,
        details: dict | None = None
    ) -> None:
        """Journaliser une action IA."""
        log = AIAuditLog(
            tenant_id=self.tenant_id,
            user_id=user_id,
            action=action,
            action_category=action.split("_")[0] if "_" in action else action,
            reference_type=reference_type,
            reference_id=reference_id,
            parameters=details,
            status="success"
        )
        self.db.add(log)

    def get_audit_logs(
        self, action: str | None = None,
        user_id: int | None = None,
        skip: int = 0, limit: int = 100
    ) -> list[AIAuditLog]:
        """Récupérer les logs d'audit."""
        query = self.db.query(AIAuditLog).filter(
            AIAuditLog.tenant_id == self.tenant_id
        )
        if action:
            query = query.filter(AIAuditLog.action == action)
        if user_id:
            query = query.filter(AIAuditLog.user_id == user_id)

        return query.order_by(AIAuditLog.created_at.desc()).offset(skip).limit(limit).all()
