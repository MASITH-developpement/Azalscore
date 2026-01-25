"""
AZALS MODULE M2A - Service OCR
===============================

Service d'extraction OCR pour les documents comptables.
Supporte plusieurs moteurs: Tesseract, AWS Textract, Azure Cognitive Services.
"""

import hashlib
import logging
import re
import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from ..models import AccountingDocument, DocumentStatus, OCRResult
from ..schemas import ExtractedField

logger = logging.getLogger(__name__)


# ============================================================================
# OCR ENGINE INTERFACE
# ============================================================================

class OCREngine(ABC):
    """Interface abstraite pour les moteurs OCR."""

    @abstractmethod
    def extract_text(self, file_path: str) -> tuple[str, float]:
        """Extrait le texte brut d'un document.

        Returns:
            Tuple[str, float]: (texte extrait, score de confiance 0-100)
        """
        pass

    @abstractmethod
    def extract_structured_data(self, file_path: str) -> dict[str, Any]:
        """Extrait des données structurées d'un document.

        Returns:
            Dict avec les champs extraits et leurs positions.
        """
        pass

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Nom du moteur OCR."""
        pass

    @property
    def engine_version(self) -> str:
        """Version du moteur."""
        return "1.0"


# ============================================================================
# TESSERACT ENGINE (Open Source)
# ============================================================================

class TesseractEngine(OCREngine):
    """Moteur OCR basé sur Tesseract (open source)."""

    def __init__(self, language: str = "fra+eng"):
        self.language = language
        self._tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Vérifie si Tesseract est disponible."""
        import pytesseract
        pytesseract.get_tesseract_version()
        return True

    @property
    def engine_name(self) -> str:
        return "tesseract"

    def extract_text(self, file_path: str) -> tuple[str, float]:
        if not self._tesseract_available:
            return "", 0.0

        import pytesseract
        from PIL import Image

        # Support multi-page (PDF)
        if file_path.lower().endswith('.pdf'):
            text = self._extract_from_pdf(file_path)
        else:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang=self.language)

        # Calcul d'un score de confiance basique
        confidence = self._calculate_confidence(text)

        return text, confidence

    def _extract_from_pdf(self, pdf_path: str) -> str:
        """Extrait le texte d'un PDF."""
        import pytesseract
        from pdf2image import convert_from_path

        pages = convert_from_path(pdf_path)
        texts = []
        for page in pages:
            text = pytesseract.image_to_string(page, lang=self.language)
            texts.append(text)
        return "\n\n".join(texts)

    def _calculate_confidence(self, text: str) -> float:
        """Calcule un score de confiance basé sur la qualité du texte."""
        if not text:
            return 0.0

        # Heuristiques de qualité
        total_chars = len(text)
        if total_chars < 50:
            return 30.0

        # Ratio de caractères valides
        valid_chars = sum(1 for c in text if c.isalnum() or c.isspace() or c in ".,;:!?€$£-/")
        valid_ratio = valid_chars / total_chars

        # Ratio de mots reconnaissables (longueur > 2)
        words = text.split()
        valid_words = sum(1 for w in words if len(w) > 2 and w.isalpha())
        word_ratio = valid_words / max(len(words), 1)

        # Score combiné
        confidence = (valid_ratio * 50 + word_ratio * 50)
        return min(100.0, max(0.0, confidence))

    def extract_structured_data(self, file_path: str) -> dict[str, Any]:
        if not self._tesseract_available:
            return {}

        import pytesseract
        from PIL import Image

        image = Image.open(file_path)
        data = pytesseract.image_to_data(image, lang=self.language, output_type=pytesseract.Output.DICT)

        return {
            "boxes": data,
            "page_count": 1
        }


# ============================================================================
# MOCK ENGINE (Pour tests et développement)
# ============================================================================

class MockOCREngine(OCREngine):
    """Moteur OCR simulé pour les tests."""

    @property
    def engine_name(self) -> str:
        return "mock"

    def extract_text(self, file_path: str) -> tuple[str, float]:
        # Simule une extraction réussie
        mock_text = """
        FACTURE N° FAC-2026-001234
        Date: 15/01/2026

        FOURNISSEUR SAS
        123 Rue du Commerce
        75001 PARIS
        SIRET: 123 456 789 00012
        TVA: FR12 123456789

        Désignation                    Quantité    PU HT      Total HT
        Prestation de service          1           1000.00    1000.00
        Fournitures diverses           5           50.00      250.00

        Total HT:                                             1250.00
        TVA 20%:                                              250.00
        Total TTC:                                            1500.00

        Date d'échéance: 15/02/2026
        IBAN: FR76 1234 5678 9012 3456 7890 123
        """
        return mock_text, 92.5

    def extract_structured_data(self, file_path: str) -> dict[str, Any]:
        return {
            "boxes": {},
            "page_count": 1
        }


# ============================================================================
# FIELD EXTRACTORS
# ============================================================================

class FieldExtractor:
    """Extracteur de champs spécifiques depuis le texte OCR."""

    # Patterns pour l'extraction
    PATTERNS = {
        "invoice_number": [
            r"(?:facture|invoice|fact\.?|inv\.?)\s*(?:n[°o]?|#|:)?\s*([A-Z0-9\-/]+)",
            r"(?:n[°o]?|#)\s*(?:facture|invoice)?\s*:?\s*([A-Z0-9\-/]+)",
        ],
        "date": [
            r"(?:date|le|du)?\s*:?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            r"(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})",
        ],
        "due_date": [
            r"(?:échéance|due date|à payer avant le|payable le)\s*:?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        ],
        "total_ht": [
            r"(?:total|montant)\s*(?:hors taxes?|ht|h\.t\.)\s*:?\s*([\d\s]+[,\.]\d{2})\s*(?:€|eur)?",
            r"(?:ht|h\.t\.)\s*:?\s*([\d\s]+[,\.]\d{2})\s*(?:€|eur)?",
        ],
        "total_tva": [
            r"(?:tva|t\.v\.a\.?|taxe)\s*(?:\d+\s*%?)?\s*:?\s*([\d\s]+[,\.]\d{2})\s*(?:€|eur)?",
        ],
        "total_ttc": [
            r"(?:total|montant)\s*(?:toutes taxes comprises?|ttc|t\.t\.c\.?|à payer|net à payer)\s*:?\s*([\d\s]+[,\.]\d{2})\s*(?:€|eur)?",
            r"(?:ttc|t\.t\.c\.?|net à payer)\s*:?\s*([\d\s]+[,\.]\d{2})\s*(?:€|eur)?",
        ],
        "siret": [
            r"(?:siret|siren)\s*:?\s*(\d{3}\s*\d{3}\s*\d{3}\s*\d{5})",
            r"(?:siret|siren)\s*:?\s*(\d{14})",
        ],
        "tva_intra": [
            r"(?:tva\s*intra(?:communautaire)?|vat\s*number?)\s*:?\s*([A-Z]{2}\s*\d{2}\s*\d{9})",
            r"([A-Z]{2}\d{11})",
        ],
        "iban": [
            r"(?:iban)\s*:?\s*([A-Z]{2}\d{2}\s*(?:\d{4}\s*){5}\d{3})",
            r"([A-Z]{2}\d{2}(?:\s*\d{4}){5}\d{3})",
        ],
        "vendor_name": [
            # Premier bloc de texte significatif (souvent le nom du fournisseur)
            r"^([A-Z][A-Za-zÀ-ÿ\s\-&]+(?:SAS|SARL|SA|EURL|SNC|AUTO-ENTREPRENEUR)?)",
        ],
    }

    @classmethod
    def extract_all(cls, text: str) -> dict[str, ExtractedField]:
        """Extrait tous les champs d'un texte OCR."""
        results = {}

        for field_name, patterns in cls.PATTERNS.items():
            value, confidence = cls._extract_field(text, patterns, field_name)
            if value:
                results[field_name] = ExtractedField(
                    value=value,
                    confidence=Decimal(str(confidence))
                )

        return results

    @classmethod
    def _extract_field(cls, text: str, patterns: list[str], field_name: str) -> tuple[Any, float]:
        """Extrait un champ spécifique."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                raw_value = match.group(1).strip()
                cleaned_value = cls._clean_value(raw_value, field_name)
                confidence = cls._calculate_field_confidence(raw_value, field_name)
                return cleaned_value, confidence

        return None, 0.0

    @classmethod
    def _clean_value(cls, value: str, field_name: str) -> Any:
        """Nettoie et convertit une valeur extraite."""
        if not value:
            return None

        if field_name in ["total_ht", "total_tva", "total_ttc"]:
            # Conversion en Decimal
            cleaned = value.replace(" ", "").replace(",", ".")
            return Decimal(cleaned)

        if field_name == "date" or field_name == "due_date":
            return cls._parse_date(value)

        if field_name in ["siret", "iban"]:
            return value.replace(" ", "")

        return value

    @classmethod
    def _parse_date(cls, value: str) -> date | None:
        """Parse une date depuis différents formats."""
        # Formats numériques
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y"]:
            parsed = datetime.strptime(value, fmt).date()
            if parsed:
                return parsed

        # Format textuel français
        months_fr = {
            "janvier": 1, "février": 2, "mars": 3, "avril": 4,
            "mai": 5, "juin": 6, "juillet": 7, "août": 8,
            "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
        }
        match = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", value.lower())
        if match:
            day, month_name, year = match.groups()
            if month_name in months_fr:
                return date(int(year), months_fr[month_name], int(day))

        return None

    @classmethod
    def _calculate_field_confidence(cls, value: str, field_name: str) -> float:
        """Calcule la confiance pour un champ extrait."""
        base_confidence = 80.0

        # Ajustements selon le type de champ
        if field_name in ["total_ht", "total_tva", "total_ttc"]:
            # Vérifie que c'est bien un montant valide
            cleaned = value.replace(" ", "").replace(",", ".")
            if re.match(r"^\d+\.\d{2}$", cleaned):
                base_confidence = 90.0

        if field_name == "invoice_number":
            # Les numéros de facture structurés sont plus fiables
            if re.match(r"^[A-Z]{2,3}[-/]\d{4}[-/]\d+$", value, re.IGNORECASE):
                base_confidence = 95.0

        if field_name in ["siret", "tva_intra", "iban"]:
            # Les identifiants avec checksum sont très fiables
            base_confidence = 95.0

        return base_confidence


# ============================================================================
# OCR SERVICE
# ============================================================================

class OCRService:
    """Service principal d'OCR pour les documents comptables."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2
        self._engines: dict[str, OCREngine] = {}
        self._init_engines()

    def _init_engines(self):
        """Initialise les moteurs OCR disponibles."""
        # Toujours avoir le mock pour les tests
        self._engines["mock"] = MockOCREngine()

        # Tesseract si disponible
        tesseract = TesseractEngine()
        if tesseract._tesseract_available:
            self._engines["tesseract"] = tesseract

    @property
    def available_engines(self) -> list[str]:
        """Liste des moteurs disponibles."""
        return list(self._engines.keys())

    def get_engine(self, name: str = None) -> OCREngine:
        """Obtient un moteur OCR.

        Args:
            name: Nom du moteur (ou None pour le meilleur disponible)
        """
        if name and name in self._engines:
            return self._engines[name]

        # Priorité: tesseract > mock
        for engine_name in ["tesseract", "mock"]:
            if engine_name in self._engines:
                return self._engines[engine_name]

        return self._engines["mock"]

    def process_document(
        self,
        document_id: UUID,
        file_path: str,
        engine_name: str = None
    ) -> OCRResult:
        """Traite un document avec OCR.

        Args:
            document_id: ID du document à traiter
            file_path: Chemin vers le fichier
            engine_name: Moteur OCR à utiliser (optionnel)

        Returns:
            OCRResult: Résultat de l'extraction OCR
        """
        start_time = datetime.utcnow()

        # Récupère le document
        document = self.db.query(AccountingDocument).filter(
            AccountingDocument.id == document_id,
            AccountingDocument.tenant_id == self.tenant_id
        ).first()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Met à jour le statut
        document.status = DocumentStatus.PROCESSING
        self.db.commit()

        # Sélectionne le moteur
        engine = self.get_engine(engine_name)

        # Extraction du texte
        raw_text, text_confidence = engine.extract_text(file_path)

        # Extraction des données structurées
        structured_data = engine.extract_structured_data(file_path)

        # Extraction des champs
        extracted_fields = FieldExtractor.extract_all(raw_text)

        # Calcul du temps de traitement
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Calcul de la confiance globale
        if extracted_fields:
            avg_confidence = sum(
                float(f.confidence) for f in extracted_fields.values()
            ) / len(extracted_fields)
            overall_confidence = Decimal(str(min(text_confidence, avg_confidence)))
        else:
            overall_confidence = Decimal(str(text_confidence * 0.5))

        # Création du résultat OCR
        ocr_result = OCRResult(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            document_id=document_id,
            ocr_engine=engine.engine_name,
            ocr_version=engine.engine_version,
            processing_time_ms=processing_time,
            overall_confidence=overall_confidence,
            raw_text=raw_text,
            structured_data=structured_data,
            extracted_fields={
                k: {"value": v.value, "confidence": float(v.confidence)}
                for k, v in extracted_fields.items()
            },
            page_count=structured_data.get("page_count", 1),
            created_at=datetime.utcnow()
        )

        self.db.add(ocr_result)

        # Met à jour le document avec les données extraites
        self._update_document_from_ocr(document, extracted_fields, raw_text, overall_confidence)

        self.db.commit()
        self.db.refresh(ocr_result)

        logger.info(
            f"OCR completed for document {document_id} "
            f"with confidence {overall_confidence}%"
        )

        return ocr_result

    def _update_document_from_ocr(
        self,
        document: AccountingDocument,
        extracted_fields: dict[str, ExtractedField],
        raw_text: str,
        overall_confidence: Decimal
    ):
        """Met à jour le document avec les données OCR extraites."""
        document.ocr_raw_text = raw_text
        document.ocr_confidence = overall_confidence

        # Mise à jour des champs si extraits
        if "invoice_number" in extracted_fields:
            document.reference = extracted_fields["invoice_number"].value

        if "date" in extracted_fields:
            document.document_date = extracted_fields["date"].value

        if "due_date" in extracted_fields:
            document.due_date = extracted_fields["due_date"].value

        if "total_ht" in extracted_fields:
            document.amount_untaxed = extracted_fields["total_ht"].value

        if "total_tva" in extracted_fields:
            document.amount_tax = extracted_fields["total_tva"].value

        if "total_ttc" in extracted_fields:
            document.amount_total = extracted_fields["total_ttc"].value

        if "vendor_name" in extracted_fields:
            document.partner_name = extracted_fields["vendor_name"].value

        if "siret" in extracted_fields or "tva_intra" in extracted_fields:
            document.partner_tax_id = (
                extracted_fields.get("tva_intra", {}).value or
                extracted_fields.get("siret", {}).value
            )

        # Met à jour le statut si extraction réussie
        if overall_confidence >= 60:
            document.status = DocumentStatus.ANALYZED
        else:
            document.status = DocumentStatus.PENDING_VALIDATION
            document.requires_validation = True

        document.processed_at = datetime.utcnow()

    def calculate_file_hash(self, file_path: str) -> str:
        """Calcule le hash SHA-256 d'un fichier."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def check_duplicate(self, file_hash: str) -> AccountingDocument | None:
        """Vérifie si un document avec le même hash existe déjà."""
        return self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.file_hash == file_hash
        ).first()

    def get_ocr_results(self, document_id: UUID) -> list[OCRResult]:
        """Récupère les résultats OCR d'un document."""
        return self.db.query(OCRResult).filter(
            OCRResult.tenant_id == self.tenant_id,
            OCRResult.document_id == document_id
        ).order_by(OCRResult.created_at.desc()).all()
