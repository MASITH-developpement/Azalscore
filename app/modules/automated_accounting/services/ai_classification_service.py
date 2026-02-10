"""
AZALS MODULE M2A - Service Classification IA
=============================================

Service d'intelligence artificielle pour la classification automatique
des documents comptables et la suggestion de comptes.
"""

import logging
import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import (
    AccountingDocument,
    AIClassification,
    ChartMapping,
    ConfidenceLevel,
    DocumentStatus,
    DocumentType,
    TaxConfiguration,
    UniversalChartAccount,
)
from ..schemas import TaxRateDetail

logger = logging.getLogger(__name__)


# ============================================================================
# AI CLASSIFICATION ENGINE
# ============================================================================

class AIClassificationEngine:
    """Moteur de classification IA pour documents comptables."""

    # Mots-clés par catégorie de dépense
    EXPENSE_KEYWORDS = {
        "LOYER": ["loyer", "bail", "location", "immobilier"],
        "TELECOM": ["téléphone", "mobile", "internet", "telecom", "fibre", "sfr", "orange", "bouygues", "free"],
        "INFORMATIQUE": ["logiciel", "software", "saas", "cloud", "hébergement", "serveur", "ordinateur", "informatique"],
        "FOURNITURES": ["fournitures", "bureau", "papeterie", "cartouche", "encre"],
        "TRANSPORT": ["transport", "train", "sncf", "avion", "taxi", "uber", "vtc", "carburant", "essence", "gasoil", "péage"],
        "RESTAURANT": ["restaurant", "repas", "déjeuner", "dîner", "traiteur"],
        "HOTEL": ["hôtel", "hotel", "hébergement", "nuit", "booking", "airbnb"],
        "ASSURANCE": ["assurance", "mutuelle", "prévoyance", "axa", "allianz", "maif"],
        "HONORAIRES": ["honoraires", "consultant", "conseil", "avocat", "expert", "comptable", "notaire"],
        "PUBLICITE": ["publicité", "marketing", "communication", "google ads", "facebook", "linkedin"],
        "FORMATION": ["formation", "stage", "cours", "séminaire", "conférence"],
        "MAINTENANCE": ["maintenance", "entretien", "réparation", "dépannage"],
        "BANQUE": ["frais bancaires", "commission", "agios", "tenue de compte"],
        "ENERGIE": ["électricité", "edf", "engie", "gaz", "énergie"],
        "EAU": ["eau", "veolia", "suez"],
    }

    # Mapping catégorie -> compte universel
    CATEGORY_TO_ACCOUNT = {
        "LOYER": "613",
        "TELECOM": "626",
        "INFORMATIQUE": "615",
        "FOURNITURES": "606",
        "TRANSPORT": "625",
        "RESTAURANT": "625",
        "HOTEL": "625",
        "ASSURANCE": "616",
        "HONORAIRES": "622",
        "PUBLICITE": "623",
        "FORMATION": "618",
        "MAINTENANCE": "615",
        "BANQUE": "627",
        "ENERGIE": "606",
        "EAU": "606",
    }

    # Mapping type document -> journal
    DOCTYPE_TO_JOURNAL = {
        DocumentType.INVOICE_RECEIVED: "PURCHASES",
        DocumentType.INVOICE_SENT: "SALES",
        DocumentType.EXPENSE_NOTE: "PURCHASES",
        DocumentType.CREDIT_NOTE_RECEIVED: "PURCHASES",
        DocumentType.CREDIT_NOTE_SENT: "SALES",
    }

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._universal_chart_cache: dict[str, UniversalChartAccount] | None = None
        self._tax_config_cache: dict[str, TaxConfiguration] | None = None

    @property
    def model_name(self) -> str:
        return "azals_classifier"

    @property
    def model_version(self) -> str:
        return "1.0.0"

    def classify_document(
        self,
        document: AccountingDocument,
        ocr_text: str
    ) -> AIClassification:
        """Classifie un document et suggère les comptes comptables.

        Args:
            document: Document à classifier
            ocr_text: Texte extrait par OCR

        Returns:
            AIClassification avec les suggestions
        """
        text_lower = ocr_text.lower() if ocr_text else ""

        # 1. Détection du type de document
        doc_type, doc_type_conf = self._detect_document_type(document, text_lower)

        # 2. Détection du fournisseur
        vendor_name, vendor_conf = self._extract_vendor(document, text_lower)

        # 3. Extraction des montants
        amounts = self._extract_amounts(document, text_lower)

        # 4. Détection de la catégorie de dépense
        expense_cat, expense_conf = self._detect_expense_category(text_lower)

        # 5. Suggestion du compte comptable
        account_code, account_conf = self._suggest_account(
            doc_type, expense_cat, text_lower
        )

        # 6. Suggestion du journal
        journal_code, journal_conf = self._suggest_journal(doc_type)

        # 7. Analyse TVA
        tax_rates = self._analyze_tax(document, amounts, text_lower)

        # 8. Calcul de la confiance globale
        overall_score, overall_level = self._calculate_overall_confidence(
            doc_type_conf, vendor_conf, account_conf,
            amounts.get("total_conf", 0)
        )

        # 9. Génération des raisons de classification
        reasons = self._generate_classification_reasons(
            doc_type, expense_cat, account_code, vendor_name
        )

        # Création de l'objet AIClassification
        classification = AIClassification(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            document_id=document.id,
            model_name=self.model_name,
            model_version=self.model_version,
            document_type_predicted=doc_type,
            document_type_confidence=Decimal(str(doc_type_conf)),
            vendor_name=vendor_name,
            vendor_confidence=Decimal(str(vendor_conf)) if vendor_name else None,
            invoice_number=document.reference,
            invoice_number_confidence=Decimal(str(85)) if document.reference else None,
            invoice_date=document.document_date,
            invoice_date_confidence=Decimal(str(90)) if document.document_date else None,
            due_date=document.due_date,
            due_date_confidence=Decimal(str(85)) if document.due_date else None,
            amount_untaxed=amounts.get("untaxed"),
            amount_untaxed_confidence=Decimal(str(amounts.get("untaxed_conf", 0))) if amounts.get("untaxed") else None,
            amount_tax=amounts.get("tax"),
            amount_tax_confidence=Decimal(str(amounts.get("tax_conf", 0))) if amounts.get("tax") else None,
            amount_total=amounts.get("total"),
            amount_total_confidence=Decimal(str(amounts.get("total_conf", 0))) if amounts.get("total") else None,
            tax_rates=[t.dict() for t in tax_rates] if tax_rates else None,
            suggested_account_code=account_code,
            suggested_account_confidence=Decimal(str(account_conf)) if account_code else None,
            suggested_journal_code=journal_code,
            suggested_journal_confidence=Decimal(str(journal_conf)) if journal_code else None,
            expense_category=expense_cat,
            expense_category_confidence=Decimal(str(expense_conf)) if expense_cat else None,
            overall_confidence=overall_level,
            overall_confidence_score=Decimal(str(overall_score)),
            classification_reasons=reasons,
            created_at=datetime.utcnow()
        )

        return classification

    def _detect_document_type(
        self,
        document: AccountingDocument,
        text: str
    ) -> tuple[DocumentType, float]:
        """Détecte le type de document."""
        # Si déjà défini, on fait confiance
        if document.document_type:
            return document.document_type, 95.0

        # Détection par mots-clés
        keywords = {
            DocumentType.INVOICE_RECEIVED: ["facture", "invoice", "fact."],
            DocumentType.CREDIT_NOTE_RECEIVED: ["avoir", "credit note", "remboursement"],
            DocumentType.EXPENSE_NOTE: ["note de frais", "expense", "remboursement frais"],
            DocumentType.QUOTE: ["devis", "quote", "proposition"],
            DocumentType.PURCHASE_ORDER: ["bon de commande", "purchase order", "commande"],
        }

        best_match = DocumentType.INVOICE_RECEIVED
        best_score = 50.0

        for doc_type, kws in keywords.items():
            for kw in kws:
                if kw in text:
                    return doc_type, 90.0

        return best_match, best_score

    def _extract_vendor(
        self,
        document: AccountingDocument,
        text: str
    ) -> tuple[str | None, float]:
        """Extrait le nom du fournisseur."""
        # Si déjà défini
        if document.partner_name:
            return document.partner_name, 90.0

        # Recherche dans les premières lignes
        lines = text.split("\n")[:10]
        for line in lines:
            # Recherche de patterns typiques
            if any(suffix in line.upper() for suffix in ["SAS", "SARL", "SA", "EURL", "SNC"]):
                # Nettoie la ligne
                vendor = line.strip()
                if len(vendor) > 3 and len(vendor) < 100:
                    return vendor, 75.0

        return None, 0.0

    def _extract_amounts(
        self,
        document: AccountingDocument,
        text: str
    ) -> dict[str, Any]:
        """Extrait les montants du document."""
        amounts = {}

        # Utilise les montants déjà extraits par OCR si disponibles
        if document.amount_untaxed:
            amounts["untaxed"] = document.amount_untaxed
            amounts["untaxed_conf"] = 90.0

        if document.amount_tax:
            amounts["tax"] = document.amount_tax
            amounts["tax_conf"] = 85.0

        if document.amount_total:
            amounts["total"] = document.amount_total
            amounts["total_conf"] = 90.0

        # Validation de cohérence HT + TVA = TTC
        if all(k in amounts for k in ["untaxed", "tax", "total"]):
            expected_total = amounts["untaxed"] + amounts["tax"]
            if abs(expected_total - amounts["total"]) < Decimal("0.02"):
                # Cohérence parfaite -> boost confiance
                amounts["untaxed_conf"] = min(98, amounts["untaxed_conf"] + 5)
                amounts["tax_conf"] = min(98, amounts["tax_conf"] + 5)
                amounts["total_conf"] = min(98, amounts["total_conf"] + 5)

        return amounts

    def _detect_expense_category(self, text: str) -> tuple[str | None, float]:
        """Détecte la catégorie de dépense."""
        best_category = None
        best_score = 0
        best_confidence = 0.0

        for category, keywords in self.EXPENSE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_category = category
                # Confiance augmente avec le nombre de mots-clés trouvés
                best_confidence = min(95.0, 60.0 + score * 10)

        return best_category, best_confidence

    def _suggest_account(
        self,
        doc_type: DocumentType,
        expense_category: str | None,
        text: str
    ) -> tuple[str | None, float]:
        """Suggère le compte comptable."""
        # Recherche dans le plan comptable universel
        if expense_category and expense_category in self.CATEGORY_TO_ACCOUNT:
            universal_code = self.CATEGORY_TO_ACCOUNT[expense_category]

            # Vérifie s'il y a un mapping local
            local_code = self._get_local_account_code(universal_code)
            if local_code:
                return local_code, 90.0

            return universal_code, 85.0

        # Par défaut selon le type de document
        default_accounts = {
            DocumentType.INVOICE_RECEIVED: "401",    # Fournisseurs
            DocumentType.INVOICE_SENT: "411",        # Clients
            DocumentType.EXPENSE_NOTE: "625",        # Déplacements
            DocumentType.CREDIT_NOTE_RECEIVED: "401",
            DocumentType.CREDIT_NOTE_SENT: "411",
        }

        if doc_type in default_accounts:
            return default_accounts[doc_type], 70.0

        return None, 0.0

    def _suggest_journal(self, doc_type: DocumentType) -> tuple[str | None, float]:
        """Suggère le journal comptable."""
        if doc_type in self.DOCTYPE_TO_JOURNAL:
            return self.DOCTYPE_TO_JOURNAL[doc_type], 95.0
        return "GENERAL", 70.0

    def _analyze_tax(
        self,
        document: AccountingDocument,
        amounts: dict[str, Any],
        text: str
    ) -> list[TaxRateDetail]:
        """Analyse les taux de TVA."""
        tax_rates = []

        # Si on a HT et TVA, on peut calculer le taux
        if amounts.get("untaxed") and amounts.get("tax"):
            ht = amounts["untaxed"]
            tva = amounts["tax"]
            if ht > 0:
                rate = (tva / ht) * 100
                # Arrondi au taux standard le plus proche
                standard_rates = [20.0, 10.0, 5.5, 2.1, 0.0]
                closest_rate = min(standard_rates, key=lambda x: abs(x - float(rate)))

                tax_rates.append(TaxRateDetail(
                    rate=Decimal(str(closest_rate)),
                    amount=tva,
                    confidence=Decimal("85.0")
                ))

        # Recherche de taux explicites dans le texte
        rate_patterns = [
            r"tva\s*(\d+(?:,\d+)?)\s*%",
            r"(\d+(?:,\d+)?)\s*%\s*tva",
        ]
        for pattern in rate_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                rate = float(match.replace(",", "."))
                if rate in [20.0, 10.0, 5.5, 2.1]:
                    # Évite les doublons
                    if not any(tr.rate == Decimal(str(rate)) for tr in tax_rates):
                        tax_rates.append(TaxRateDetail(
                            rate=Decimal(str(rate)),
                            amount=Decimal("0"),  # Montant à calculer
                            confidence=Decimal("80.0")
                        ))

        return tax_rates

    def _get_local_account_code(self, universal_code: str) -> str | None:
        """Obtient le code compte local depuis le mapping."""
        mapping = self.db.query(ChartMapping).filter(
            ChartMapping.tenant_id == self.tenant_id,
            ChartMapping.universal_code == universal_code,
            ChartMapping.is_active
        ).first()

        if mapping:
            return mapping.local_account_code
        return None

    def _calculate_overall_confidence(
        self,
        doc_type_conf: float,
        vendor_conf: float,
        account_conf: float,
        amount_conf: float
    ) -> tuple[float, ConfidenceLevel]:
        """Calcule la confiance globale."""
        # Pondération des différents scores
        weights = {
            "doc_type": 0.15,
            "vendor": 0.15,
            "account": 0.35,
            "amount": 0.35,
        }

        score = (
            doc_type_conf * weights["doc_type"] +
            vendor_conf * weights["vendor"] +
            account_conf * weights["account"] +
            amount_conf * weights["amount"]
        )

        # Détermination du niveau
        if score >= 95:
            level = ConfidenceLevel.HIGH
        elif score >= 80:
            level = ConfidenceLevel.MEDIUM
        elif score >= 60:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.VERY_LOW

        return score, level

    def _generate_classification_reasons(
        self,
        doc_type: DocumentType,
        expense_category: str | None,
        account_code: str | None,
        vendor_name: str | None
    ) -> list[str]:
        """Génère les raisons de la classification."""
        reasons = []

        if doc_type:
            reasons.append(f"Document identifié comme {doc_type.value}")

        if vendor_name:
            reasons.append(f"Fournisseur détecté: {vendor_name}")

        if expense_category:
            reasons.append(f"Catégorie de dépense: {expense_category}")

        if account_code:
            reasons.append(f"Compte suggéré: {account_code}")

        return reasons


# ============================================================================
# AI CLASSIFICATION SERVICE
# ============================================================================

class AIClassificationService:
    """Service de classification IA pour les documents comptables."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2
        self.engine = AIClassificationEngine(db, tenant_id)

    def classify_document(self, document_id: UUID) -> AIClassification:
        """Classifie un document.

        Args:
            document_id: ID du document à classifier

        Returns:
            AIClassification avec les suggestions
        """
        # Récupère le document
        document = self.db.query(AccountingDocument).filter(
            AccountingDocument.id == document_id,
            AccountingDocument.tenant_id == self.tenant_id
        ).first()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Vérifie qu'on a le texte OCR
        ocr_text = document.ocr_raw_text or ""

        # Classification
        classification = self.engine.classify_document(document, ocr_text)

        # Sauvegarde
        self.db.add(classification)

        # Met à jour le document avec les infos IA
        document.ai_confidence = classification.overall_confidence
        document.ai_confidence_score = classification.overall_confidence_score
        document.ai_suggested_account = classification.suggested_account_code
        document.ai_suggested_journal = classification.suggested_journal_code
        document.ai_analysis = {
            "classification_id": str(classification.id),
            "expense_category": classification.expense_category,
            "tax_rates": classification.tax_rates,
            "reasons": classification.classification_reasons,
        }

        # Détermine si validation requise
        if classification.overall_confidence in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]:
            document.requires_validation = True
            document.status = DocumentStatus.PENDING_VALIDATION
        else:
            document.requires_validation = False

        self.db.commit()
        self.db.refresh(classification)

        logger.info(
            "Document %s classified with "
            "confidence %s "
            "(%s%%)",
            document_id, classification.overall_confidence.value, classification.overall_confidence_score
        )

        return classification

    def get_classifications(self, document_id: UUID) -> list[AIClassification]:
        """Récupère les classifications d'un document."""
        return self.db.query(AIClassification).filter(
            AIClassification.tenant_id == self.tenant_id,
            AIClassification.document_id == document_id
        ).order_by(AIClassification.created_at.desc()).all()

    def get_latest_classification(self, document_id: UUID) -> AIClassification | None:
        """Récupère la dernière classification d'un document."""
        return self.db.query(AIClassification).filter(
            AIClassification.tenant_id == self.tenant_id,
            AIClassification.document_id == document_id
        ).order_by(AIClassification.created_at.desc()).first()

    def record_correction(
        self,
        classification_id: UUID,
        corrected_by: UUID,
        corrected_account_code: str | None = None,
        corrected_journal_code: str | None = None,
        corrected_expense_category: str | None = None,
        feedback: str | None = None
    ):
        """Enregistre une correction pour l'apprentissage.

        Args:
            classification_id: ID de la classification corrigée
            corrected_by: ID de l'utilisateur qui corrige
            corrected_account_code: Code compte corrigé
            corrected_journal_code: Code journal corrigé
            corrected_expense_category: Catégorie corrigée
            feedback: Commentaire sur la correction
        """
        classification = self.db.query(AIClassification).filter(
            AIClassification.id == classification_id,
            AIClassification.tenant_id == self.tenant_id
        ).first()

        if not classification:
            raise ValueError(f"Classification {classification_id} not found")

        classification.was_corrected = True
        classification.corrected_by = corrected_by
        classification.corrected_at = datetime.utcnow()
        classification.correction_feedback = feedback

        # Enregistre les corrections dans un champ JSON pour apprentissage
        corrections = {
            "original_account": classification.suggested_account_code,
            "corrected_account": corrected_account_code,
            "original_journal": classification.suggested_journal_code,
            "corrected_journal": corrected_journal_code,
            "original_category": classification.expense_category,
            "corrected_category": corrected_expense_category,
        }

        if classification.classification_reasons:
            classification.classification_reasons.append(
                f"Corrigé par utilisateur: {corrections}"
            )
        else:
            classification.classification_reasons = [
                f"Corrigé par utilisateur: {corrections}"
            ]

        self.db.commit()

        logger.info(
            "Classification %s corrected by user %s", classification_id, corrected_by
        )

    def get_ai_performance_stats(
        self,
        start_date: date | None = None,
        end_date: date | None = None
    ) -> dict[str, Any]:
        """Calcule les statistiques de performance de l'IA.

        Returns:
            Dict avec les métriques de performance
        """
        query = self.db.query(AIClassification).filter(
            AIClassification.tenant_id == self.tenant_id
        )

        if start_date:
            query = query.filter(AIClassification.created_at >= start_date)
        if end_date:
            query = query.filter(AIClassification.created_at <= end_date)

        total = query.count()

        if total == 0:
            return {
                "total_processed": 0,
                "auto_validated_count": 0,
                "auto_validated_rate": Decimal("0"),
                "corrections_count": 0,
                "corrections_rate": Decimal("0"),
                "average_confidence": Decimal("0"),
                "by_confidence_level": {},
                "by_document_type": {},
            }

        # Compte par niveau de confiance
        high_conf = query.filter(
            AIClassification.overall_confidence == ConfidenceLevel.HIGH
        ).count()

        medium_conf = query.filter(
            AIClassification.overall_confidence == ConfidenceLevel.MEDIUM
        ).count()

        # Corrections
        corrections = query.filter(AIClassification.was_corrected).count()

        # Confiance moyenne
        avg_conf = self.db.query(
            func.avg(AIClassification.overall_confidence_score)
        ).filter(
            AIClassification.tenant_id == self.tenant_id
        ).scalar() or Decimal("0")

        # Auto-validés (haute confiance)
        auto_validated = high_conf

        return {
            "total_processed": total,
            "auto_validated_count": auto_validated,
            "auto_validated_rate": Decimal(str(round(auto_validated / total * 100, 2))),
            "corrections_count": corrections,
            "corrections_rate": Decimal(str(round(corrections / total * 100, 2))),
            "average_confidence": Decimal(str(round(float(avg_conf), 2))),
            "by_confidence_level": {
                "HIGH": high_conf,
                "MEDIUM": medium_conf,
                "LOW": total - high_conf - medium_conf - corrections,
            },
        }
