"""
Service de Génération de Documents - GAP-043

Gestion complète de la génération documentaire:
- Templates avec placeholders
- Génération PDF, DOCX, HTML
- Fusion de données (mail merge)
- Versioning des templates
- Multi-langues
- Signatures et cachets
- Archivage automatique
- Intégration GED
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import uuid4
import re
import json
import hashlib
import base64


class DocumentFormat(Enum):
    """Format de document."""
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    ODT = "odt"
    TXT = "txt"
    XLSX = "xlsx"
    CSV = "csv"


class TemplateType(Enum):
    """Type de template."""
    INVOICE = "invoice"  # Facture
    QUOTE = "quote"  # Devis
    ORDER = "order"  # Bon de commande
    DELIVERY = "delivery"  # Bon de livraison
    CONTRACT = "contract"  # Contrat
    LETTER = "letter"  # Courrier
    CERTIFICATE = "certificate"  # Attestation
    REPORT = "report"  # Rapport
    PAYSLIP = "payslip"  # Bulletin de paie
    STATEMENT = "statement"  # Relevé
    REMINDER = "reminder"  # Relance
    CUSTOM = "custom"  # Personnalisé


class TemplateStatus(Enum):
    """Statut d'un template."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class GenerationStatus(Enum):
    """Statut de génération."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlaceholderType(Enum):
    """Type de placeholder."""
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    IMAGE = "image"
    TABLE = "table"
    BARCODE = "barcode"
    QRCODE = "qrcode"
    SIGNATURE = "signature"
    CONDITIONAL = "conditional"
    LOOP = "loop"


# Formats de date français
DATE_FORMATS = {
    "short": "%d/%m/%Y",
    "long": "%d %B %Y",
    "full": "%A %d %B %Y",
    "iso": "%Y-%m-%d"
}

# Formats de nombres français
NUMBER_LOCALE = {
    "decimal_separator": ",",
    "thousands_separator": " ",
    "currency_symbol": "€",
    "currency_position": "after"
}


@dataclass
class Placeholder:
    """Définition d'un placeholder."""
    name: str
    placeholder_type: PlaceholderType
    label: str
    required: bool = True
    default_value: Optional[str] = None
    format_options: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class TemplateSection:
    """Section d'un template."""
    section_id: str
    name: str
    content: str
    order: int
    is_conditional: bool = False
    condition: Optional[str] = None
    is_repeatable: bool = False
    repeat_source: Optional[str] = None


@dataclass
class Template:
    """Template de document."""
    template_id: str
    tenant_id: str
    name: str
    description: str
    template_type: TemplateType
    status: TemplateStatus

    # Contenu
    content: str  # Template HTML/texte avec placeholders
    sections: List[TemplateSection] = field(default_factory=list)
    placeholders: List[Placeholder] = field(default_factory=list)

    # Format de sortie
    default_format: DocumentFormat = DocumentFormat.PDF
    supported_formats: List[DocumentFormat] = field(default_factory=list)

    # Mise en page
    page_size: str = "A4"  # A4, Letter, Legal
    orientation: str = "portrait"  # portrait, landscape
    margins: Dict[str, int] = field(default_factory=lambda: {
        "top": 20, "bottom": 20, "left": 20, "right": 20
    })

    # En-tête/pied de page
    header_content: Optional[str] = None
    footer_content: Optional[str] = None
    show_page_numbers: bool = True

    # Styles
    css_styles: Optional[str] = None
    font_family: str = "Arial"
    font_size: int = 11

    # Logo et images
    logo_position: str = "top-left"  # top-left, top-center, top-right
    logo_url: Optional[str] = None

    # Langues
    default_language: str = "fr"
    translations: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # Versioning
    version: int = 1
    is_latest: bool = True
    parent_version_id: Optional[str] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class GeneratedDocument:
    """Document généré."""
    document_id: str
    tenant_id: str
    template_id: str
    template_version: int
    format: DocumentFormat
    status: GenerationStatus

    # Données utilisées
    data: Dict[str, Any] = field(default_factory=dict)
    language: str = "fr"

    # Résultat
    content: Optional[bytes] = None
    content_hash: Optional[str] = None
    file_size: int = 0
    page_count: int = 0

    # Référence
    reference_type: Optional[str] = None  # "invoice", "order", etc.
    reference_id: Optional[str] = None

    # Stockage
    storage_path: Optional[str] = None
    storage_url: Optional[str] = None

    # Métadonnées
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = ""
    generation_time_ms: int = 0
    error_message: Optional[str] = None

    # Archivage
    archived: bool = False
    archived_at: Optional[datetime] = None
    retention_until: Optional[date] = None


@dataclass
class MergeJob:
    """Job de fusion en masse (mail merge)."""
    job_id: str
    tenant_id: str
    template_id: str
    format: DocumentFormat
    status: GenerationStatus

    # Données sources
    data_source: str  # "csv", "json", "database"
    data_records: List[Dict[str, Any]] = field(default_factory=list)
    total_records: int = 0

    # Progression
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)

    # Résultats
    output_mode: str = "individual"  # individual, merged
    generated_documents: List[str] = field(default_factory=list)
    merged_document_id: Optional[str] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class DocumentSignature:
    """Signature sur un document."""
    signature_id: str
    document_id: str
    signer_name: str
    signer_email: str
    signature_image: Optional[bytes] = None
    signed_at: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    position: Dict[str, int] = field(default_factory=dict)


class DocumentService:
    """Service de génération de documents."""

    def __init__(
        self,
        tenant_id: str,
        template_repository: Optional[Any] = None,
        document_repository: Optional[Any] = None,
        storage_service: Optional[Any] = None,
        pdf_generator: Optional[Callable] = None,
        docx_generator: Optional[Callable] = None
    ):
        self.tenant_id = tenant_id
        self.template_repo = template_repository or {}
        self.document_repo = document_repository or {}
        self.storage = storage_service
        self.pdf_generator = pdf_generator
        self.docx_generator = docx_generator

        # Caches
        self._templates: Dict[str, Template] = {}
        self._documents: Dict[str, GeneratedDocument] = {}
        self._merge_jobs: Dict[str, MergeJob] = {}

        # Regex pour les placeholders
        self._placeholder_pattern = re.compile(r'\{\{([^}]+)\}\}')
        self._condition_pattern = re.compile(
            r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}',
            re.DOTALL
        )
        self._loop_pattern = re.compile(
            r'\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}',
            re.DOTALL
        )

    # =========================================================================
    # Gestion des Templates
    # =========================================================================

    def create_template(
        self,
        name: str,
        description: str,
        template_type: TemplateType,
        content: str,
        **kwargs
    ) -> Template:
        """Crée un nouveau template."""
        template_id = f"tpl_{uuid4().hex[:12]}"

        # Extraire les placeholders du contenu
        placeholders = self._extract_placeholders(content)

        # Sections
        sections = []
        for i, section_data in enumerate(kwargs.get("sections", [])):
            section = TemplateSection(
                section_id=f"sec_{i+1}",
                name=section_data.get("name", f"Section {i+1}"),
                content=section_data.get("content", ""),
                order=i,
                is_conditional=section_data.get("is_conditional", False),
                condition=section_data.get("condition"),
                is_repeatable=section_data.get("is_repeatable", False),
                repeat_source=section_data.get("repeat_source")
            )
            sections.append(section)

        template = Template(
            template_id=template_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            template_type=template_type,
            status=TemplateStatus.DRAFT,
            content=content,
            sections=sections,
            placeholders=placeholders,
            default_format=kwargs.get("default_format", DocumentFormat.PDF),
            supported_formats=kwargs.get("supported_formats", [DocumentFormat.PDF]),
            page_size=kwargs.get("page_size", "A4"),
            orientation=kwargs.get("orientation", "portrait"),
            margins=kwargs.get("margins", {"top": 20, "bottom": 20, "left": 20, "right": 20}),
            header_content=kwargs.get("header_content"),
            footer_content=kwargs.get("footer_content"),
            show_page_numbers=kwargs.get("show_page_numbers", True),
            css_styles=kwargs.get("css_styles"),
            font_family=kwargs.get("font_family", "Arial"),
            font_size=kwargs.get("font_size", 11),
            logo_position=kwargs.get("logo_position", "top-left"),
            logo_url=kwargs.get("logo_url"),
            default_language=kwargs.get("default_language", "fr"),
            translations=kwargs.get("translations", {}),
            created_by=kwargs.get("created_by", "system"),
            tags=kwargs.get("tags", [])
        )

        self._templates[template_id] = template
        return template

    def _extract_placeholders(self, content: str) -> List[Placeholder]:
        """Extrait les placeholders d'un contenu."""
        placeholders = []
        seen = set()

        # Trouver tous les {{placeholder}} ou {{placeholder|format}}
        matches = self._placeholder_pattern.findall(content)

        for match in matches:
            # Parser le placeholder (nom|format|options)
            parts = match.split("|")
            name = parts[0].strip()

            if name in seen:
                continue
            seen.add(name)

            # Détecter le type
            placeholder_type = PlaceholderType.TEXT
            format_options = {}

            if len(parts) > 1:
                format_spec = parts[1].strip()
                if format_spec in ("date", "date_short", "date_long"):
                    placeholder_type = PlaceholderType.DATE
                    format_options["format"] = format_spec
                elif format_spec in ("number", "decimal"):
                    placeholder_type = PlaceholderType.NUMBER
                elif format_spec in ("currency", "amount"):
                    placeholder_type = PlaceholderType.CURRENCY
                elif format_spec == "image":
                    placeholder_type = PlaceholderType.IMAGE
                elif format_spec == "signature":
                    placeholder_type = PlaceholderType.SIGNATURE

            placeholder = Placeholder(
                name=name,
                placeholder_type=placeholder_type,
                label=name.replace("_", " ").title(),
                format_options=format_options
            )
            placeholders.append(placeholder)

        return placeholders

    def activate_template(self, template_id: str) -> Template:
        """Active un template."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} non trouvé")

        if template.status == TemplateStatus.ARCHIVED:
            raise ValueError("Impossible d'activer un template archivé")

        template.status = TemplateStatus.ACTIVE
        template.updated_at = datetime.now()
        return template

    def create_new_version(
        self,
        template_id: str,
        content: str,
        **kwargs
    ) -> Template:
        """Crée une nouvelle version d'un template."""
        original = self._templates.get(template_id)
        if not original:
            raise ValueError(f"Template {template_id} non trouvé")

        # Marquer l'ancienne version
        original.is_latest = False
        original.status = TemplateStatus.DEPRECATED

        # Créer la nouvelle version
        new_version = self.create_template(
            name=original.name,
            description=kwargs.get("description", original.description),
            template_type=original.template_type,
            content=content,
            default_format=original.default_format,
            supported_formats=original.supported_formats,
            page_size=original.page_size,
            orientation=original.orientation,
            margins=original.margins,
            header_content=kwargs.get("header_content", original.header_content),
            footer_content=kwargs.get("footer_content", original.footer_content),
            css_styles=kwargs.get("css_styles", original.css_styles),
            logo_url=original.logo_url,
            default_language=original.default_language,
            translations=original.translations,
            created_by=kwargs.get("created_by", "system"),
            tags=original.tags
        )

        new_version.version = original.version + 1
        new_version.parent_version_id = original.template_id
        new_version.is_latest = True

        return new_version

    def get_template(
        self,
        template_id: str,
        version: Optional[int] = None
    ) -> Optional[Template]:
        """Récupère un template par ID."""
        if version:
            # Chercher la version spécifique
            for t in self._templates.values():
                if (t.template_id == template_id or t.parent_version_id == template_id) \
                   and t.version == version:
                    return t
        return self._templates.get(template_id)

    def list_templates(
        self,
        template_type: Optional[TemplateType] = None,
        status: Optional[TemplateStatus] = None,
        latest_only: bool = True
    ) -> List[Template]:
        """Liste les templates."""
        templates = []

        for t in self._templates.values():
            if t.tenant_id != self.tenant_id:
                continue
            if template_type and t.template_type != template_type:
                continue
            if status and t.status != status:
                continue
            if latest_only and not t.is_latest:
                continue
            templates.append(t)

        return sorted(templates, key=lambda x: x.name)

    # =========================================================================
    # Génération de Documents
    # =========================================================================

    def generate_document(
        self,
        template_id: str,
        data: Dict[str, Any],
        format: Optional[DocumentFormat] = None,
        language: str = "fr",
        **kwargs
    ) -> GeneratedDocument:
        """Génère un document à partir d'un template."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} non trouvé")

        if template.status != TemplateStatus.ACTIVE:
            raise ValueError(f"Template non actif: {template.status}")

        format = format or template.default_format
        if format not in template.supported_formats and format != template.default_format:
            raise ValueError(f"Format {format} non supporté par ce template")

        document_id = f"doc_{uuid4().hex[:12]}"
        start_time = datetime.now()

        document = GeneratedDocument(
            document_id=document_id,
            tenant_id=self.tenant_id,
            template_id=template_id,
            template_version=template.version,
            format=format,
            status=GenerationStatus.PROCESSING,
            data=data,
            language=language,
            reference_type=kwargs.get("reference_type"),
            reference_id=kwargs.get("reference_id"),
            generated_by=kwargs.get("generated_by", "system")
        )

        try:
            # Préparer le contenu
            html_content = self._render_template(template, data, language)

            # Générer selon le format
            if format == DocumentFormat.PDF:
                content = self._generate_pdf(html_content, template)
            elif format == DocumentFormat.HTML:
                content = html_content.encode("utf-8")
            elif format == DocumentFormat.DOCX:
                content = self._generate_docx(html_content, template)
            else:
                content = html_content.encode("utf-8")

            document.content = content
            document.content_hash = hashlib.sha256(content).hexdigest()
            document.file_size = len(content)
            document.status = GenerationStatus.COMPLETED

            # Stocker si service configuré
            if self.storage:
                storage_result = self._store_document(document)
                document.storage_path = storage_result.get("path")
                document.storage_url = storage_result.get("url")

        except Exception as e:
            document.status = GenerationStatus.FAILED
            document.error_message = str(e)

        document.generation_time_ms = int(
            (datetime.now() - start_time).total_seconds() * 1000
        )

        self._documents[document_id] = document
        return document

    def _render_template(
        self,
        template: Template,
        data: Dict[str, Any],
        language: str
    ) -> str:
        """Rend un template avec les données."""
        content = template.content

        # Appliquer les traductions si nécessaire
        if language != template.default_language:
            translations = template.translations.get(language, {})
            for key, value in translations.items():
                content = content.replace(f"{{{{t:{key}}}}}", value)

        # Traiter les conditions
        content = self._process_conditions(content, data)

        # Traiter les boucles
        content = self._process_loops(content, data)

        # Remplacer les placeholders
        content = self._replace_placeholders(content, data, template.placeholders)

        # Construire le document HTML complet
        html = self._build_html_document(content, template)

        return html

    def _process_conditions(self, content: str, data: Dict[str, Any]) -> str:
        """Traite les blocs conditionnels."""
        def replace_condition(match):
            var_name = match.group(1)
            block_content = match.group(2)

            # Évaluer la condition
            value = self._get_nested_value(data, var_name)
            if value:
                return block_content
            return ""

        return self._condition_pattern.sub(replace_condition, content)

    def _process_loops(self, content: str, data: Dict[str, Any]) -> str:
        """Traite les boucles."""
        def replace_loop(match):
            item_name = match.group(1)
            list_name = match.group(2)
            block_content = match.group(3)

            items = self._get_nested_value(data, list_name)
            if not items or not isinstance(items, list):
                return ""

            result = []
            for i, item in enumerate(items):
                item_content = block_content
                # Remplacer les références à l'item
                item_content = item_content.replace(
                    f"{{{{{item_name}.", "{{"
                )

                # Ajouter l'index
                item_data = {**item, "_index": i + 1} if isinstance(item, dict) else item
                result.append(self._replace_simple_placeholders(item_content, item_data))

            return "".join(result)

        return self._loop_pattern.sub(replace_loop, content)

    def _replace_placeholders(
        self,
        content: str,
        data: Dict[str, Any],
        placeholders: List[Placeholder]
    ) -> str:
        """Remplace les placeholders par les valeurs."""
        placeholder_map = {p.name: p for p in placeholders}

        def replace_match(match):
            full_match = match.group(1)
            parts = full_match.split("|")
            name = parts[0].strip()

            value = self._get_nested_value(data, name)
            placeholder = placeholder_map.get(name)

            if value is None:
                if placeholder and placeholder.default_value:
                    value = placeholder.default_value
                else:
                    return ""

            # Formater selon le type
            if placeholder:
                value = self._format_value(value, placeholder, parts[1:])
            else:
                value = str(value)

            return value

        return self._placeholder_pattern.sub(replace_match, content)

    def _replace_simple_placeholders(
        self,
        content: str,
        data: Union[Dict[str, Any], Any]
    ) -> str:
        """Remplacement simple pour les boucles."""
        if isinstance(data, dict):
            for key, value in data.items():
                content = content.replace(f"{{{{{key}}}}}", str(value or ""))
        return content

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Récupère une valeur imbriquée (ex: customer.name)."""
        keys = path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

            if value is None:
                return None

        return value

    def _format_value(
        self,
        value: Any,
        placeholder: Placeholder,
        format_parts: List[str]
    ) -> str:
        """Formate une valeur selon le type de placeholder."""
        if placeholder.placeholder_type == PlaceholderType.DATE:
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value)
                except ValueError:
                    return value

            if isinstance(value, (date, datetime)):
                format_name = "short"
                if format_parts:
                    format_name = format_parts[0].replace("date_", "")
                date_format = DATE_FORMATS.get(format_name, DATE_FORMATS["short"])
                return value.strftime(date_format)

        elif placeholder.placeholder_type == PlaceholderType.CURRENCY:
            if isinstance(value, (int, float, Decimal)):
                # Format français: 1 234,56 €
                formatted = f"{float(value):,.2f}"
                formatted = formatted.replace(",", " ").replace(".", ",")
                return f"{formatted} €"

        elif placeholder.placeholder_type == PlaceholderType.NUMBER:
            if isinstance(value, (int, float, Decimal)):
                formatted = f"{float(value):,.2f}"
                formatted = formatted.replace(",", " ").replace(".", ",")
                return formatted

        elif placeholder.placeholder_type == PlaceholderType.IMAGE:
            if isinstance(value, str):
                return f'<img src="{value}" alt="" />'

        return str(value)

    def _build_html_document(self, content: str, template: Template) -> str:
        """Construit le document HTML complet."""
        css = template.css_styles or self._get_default_css(template)

        header = ""
        if template.header_content:
            header = f'<header class="document-header">{template.header_content}</header>'

        footer = ""
        if template.footer_content:
            footer = f'<footer class="document-footer">{template.footer_content}</footer>'
        if template.show_page_numbers:
            footer += '<div class="page-number"></div>'

        html = f"""<!DOCTYPE html>
<html lang="{template.default_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    {css}
    </style>
</head>
<body>
    {header}
    <main class="document-content">
        {content}
    </main>
    {footer}
</body>
</html>"""

        return html

    def _get_default_css(self, template: Template) -> str:
        """CSS par défaut pour les documents."""
        return f"""
@page {{
    size: {template.page_size} {template.orientation};
    margin: {template.margins['top']}mm {template.margins['right']}mm
            {template.margins['bottom']}mm {template.margins['left']}mm;
}}

body {{
    font-family: {template.font_family}, sans-serif;
    font-size: {template.font_size}pt;
    line-height: 1.5;
    color: #333;
}}

.document-header {{
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #ccc;
}}

.document-footer {{
    margin-top: 20px;
    padding-top: 10px;
    border-top: 1px solid #ccc;
    font-size: 9pt;
    color: #666;
}}

.page-number::after {{
    content: "Page " counter(page) " / " counter(pages);
    position: fixed;
    bottom: 10mm;
    right: 10mm;
    font-size: 9pt;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
}}

th, td {{
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}}

th {{
    background-color: #f5f5f5;
    font-weight: bold;
}}

.amount {{
    text-align: right;
}}

.signature-block {{
    margin-top: 40px;
    padding-top: 20px;
}}

.signature-line {{
    border-top: 1px solid #333;
    width: 200px;
    margin-top: 50px;
}}
"""

    def _generate_pdf(self, html: str, template: Template) -> bytes:
        """Génère un PDF à partir du HTML."""
        if self.pdf_generator:
            return self.pdf_generator(html, {
                "page_size": template.page_size,
                "orientation": template.orientation,
                "margins": template.margins
            })

        # Fallback: retourner le HTML encodé (à remplacer par weasyprint, etc.)
        return html.encode("utf-8")

    def _generate_docx(self, html: str, template: Template) -> bytes:
        """Génère un DOCX à partir du HTML."""
        if self.docx_generator:
            return self.docx_generator(html, template)

        # Fallback
        return html.encode("utf-8")

    def _store_document(self, document: GeneratedDocument) -> Dict[str, str]:
        """Stocke un document."""
        # Implémentation à adapter selon le service de stockage
        return {
            "path": f"/documents/{document.document_id}.{document.format.value}",
            "url": f"/api/documents/{document.document_id}/download"
        }

    # =========================================================================
    # Mail Merge (Fusion en Masse)
    # =========================================================================

    def create_merge_job(
        self,
        template_id: str,
        data_records: List[Dict[str, Any]],
        format: DocumentFormat = DocumentFormat.PDF,
        output_mode: str = "individual",
        **kwargs
    ) -> MergeJob:
        """Crée un job de fusion en masse."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} non trouvé")

        job_id = f"merge_{uuid4().hex[:12]}"

        job = MergeJob(
            job_id=job_id,
            tenant_id=self.tenant_id,
            template_id=template_id,
            format=format,
            status=GenerationStatus.PENDING,
            data_source=kwargs.get("data_source", "json"),
            data_records=data_records,
            total_records=len(data_records),
            output_mode=output_mode,
            created_by=kwargs.get("created_by", "system")
        )

        self._merge_jobs[job_id] = job
        return job

    def execute_merge_job(self, job_id: str) -> MergeJob:
        """Exécute un job de fusion."""
        job = self._merge_jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} non trouvé")

        job.status = GenerationStatus.PROCESSING
        job.started_at = datetime.now()

        template = self._templates.get(job.template_id)

        for i, record in enumerate(job.data_records):
            try:
                doc = self.generate_document(
                    template_id=job.template_id,
                    data=record,
                    format=job.format,
                    reference_type="merge_job",
                    reference_id=job.job_id
                )

                if doc.status == GenerationStatus.COMPLETED:
                    job.generated_documents.append(doc.document_id)
                    job.successful_records += 1
                else:
                    job.failed_records += 1
                    job.errors.append({
                        "record_index": i,
                        "error": doc.error_message
                    })

            except Exception as e:
                job.failed_records += 1
                job.errors.append({
                    "record_index": i,
                    "error": str(e)
                })

            job.processed_records += 1

        # Si mode merged, combiner les documents
        if job.output_mode == "merged" and job.generated_documents:
            merged_doc = self._merge_documents(job.generated_documents, job.format)
            job.merged_document_id = merged_doc.document_id

        job.status = GenerationStatus.COMPLETED
        job.completed_at = datetime.now()

        return job

    def _merge_documents(
        self,
        document_ids: List[str],
        format: DocumentFormat
    ) -> GeneratedDocument:
        """Fusionne plusieurs documents en un seul."""
        # Implémentation simplifiée - à enrichir avec PyPDF2, etc.
        merged_content = b""

        for doc_id in document_ids:
            doc = self._documents.get(doc_id)
            if doc and doc.content:
                merged_content += doc.content

        merged_doc = GeneratedDocument(
            document_id=f"doc_{uuid4().hex[:12]}",
            tenant_id=self.tenant_id,
            template_id="merged",
            template_version=0,
            format=format,
            status=GenerationStatus.COMPLETED,
            content=merged_content,
            content_hash=hashlib.sha256(merged_content).hexdigest(),
            file_size=len(merged_content)
        )

        self._documents[merged_doc.document_id] = merged_doc
        return merged_doc

    # =========================================================================
    # Récupération et Archivage
    # =========================================================================

    def get_document(self, document_id: str) -> Optional[GeneratedDocument]:
        """Récupère un document."""
        return self._documents.get(document_id)

    def download_document(self, document_id: str) -> bytes:
        """Télécharge le contenu d'un document."""
        doc = self._documents.get(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} non trouvé")

        if doc.content:
            return doc.content

        if self.storage and doc.storage_path:
            return self.storage.read(doc.storage_path)

        raise ValueError("Contenu du document non disponible")

    def archive_document(
        self,
        document_id: str,
        retention_years: int = 10
    ) -> GeneratedDocument:
        """Archive un document."""
        doc = self._documents.get(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} non trouvé")

        doc.archived = True
        doc.archived_at = datetime.now()
        doc.retention_until = date(
            date.today().year + retention_years,
            date.today().month,
            date.today().day
        )

        return doc

    def list_documents(
        self,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        template_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[GeneratedDocument]:
        """Liste les documents générés."""
        documents = []

        for doc in self._documents.values():
            if doc.tenant_id != self.tenant_id:
                continue
            if reference_type and doc.reference_type != reference_type:
                continue
            if reference_id and doc.reference_id != reference_id:
                continue
            if template_id and doc.template_id != template_id:
                continue
            if from_date and doc.generated_at < from_date:
                continue
            if to_date and doc.generated_at > to_date:
                continue

            documents.append(doc)

        return sorted(documents, key=lambda x: x.generated_at, reverse=True)

    # =========================================================================
    # Templates Prédéfinis
    # =========================================================================

    def create_invoice_template(self, company_name: str, **kwargs) -> Template:
        """Crée un template de facture standard."""
        content = """
<div class="invoice-header">
    <div class="company-info">
        <h1>{{company_name}}</h1>
        <p>{{company_address}}</p>
        <p>SIRET: {{company_siret}}</p>
        <p>TVA: {{company_tva}}</p>
    </div>
    <div class="invoice-info">
        <h2>FACTURE N° {{invoice_number}}</h2>
        <p>Date: {{invoice_date|date}}</p>
        <p>Échéance: {{due_date|date}}</p>
    </div>
</div>

<div class="customer-info">
    <h3>Facturé à:</h3>
    <p><strong>{{customer_name}}</strong></p>
    <p>{{customer_address}}</p>
    {% if customer_siret %}
    <p>SIRET: {{customer_siret}}</p>
    {% endif %}
</div>

<table class="invoice-lines">
    <thead>
        <tr>
            <th>Description</th>
            <th>Quantité</th>
            <th>Prix unitaire HT</th>
            <th>TVA</th>
            <th>Total HT</th>
        </tr>
    </thead>
    <tbody>
        {% for line in lines %}
        <tr>
            <td>{{description}}</td>
            <td class="amount">{{quantity}}</td>
            <td class="amount">{{unit_price|currency}}</td>
            <td class="amount">{{vat_rate}} %</td>
            <td class="amount">{{line_total|currency}}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="invoice-totals">
    <table>
        <tr>
            <td>Total HT</td>
            <td class="amount">{{total_ht|currency}}</td>
        </tr>
        <tr>
            <td>TVA</td>
            <td class="amount">{{total_vat|currency}}</td>
        </tr>
        <tr class="total-row">
            <td><strong>Total TTC</strong></td>
            <td class="amount"><strong>{{total_ttc|currency}}</strong></td>
        </tr>
    </table>
</div>

<div class="payment-info">
    <p>Mode de paiement: {{payment_method}}</p>
    <p>Conditions de paiement: {{payment_terms}}</p>
    {% if bank_iban %}
    <p>IBAN: {{bank_iban}}</p>
    <p>BIC: {{bank_bic}}</p>
    {% endif %}
</div>

<div class="legal-notice">
    <p>En cas de retard de paiement, une pénalité de 3 fois le taux d'intérêt légal sera appliquée,
    ainsi qu'une indemnité forfaitaire de 40€ pour frais de recouvrement.</p>
</div>
"""

        return self.create_template(
            name=f"Facture - {company_name}",
            description="Template de facture standard",
            template_type=TemplateType.INVOICE,
            content=content,
            default_format=DocumentFormat.PDF,
            supported_formats=[DocumentFormat.PDF, DocumentFormat.HTML],
            **kwargs
        )


def create_document_service(
    tenant_id: str,
    **kwargs
) -> DocumentService:
    """Factory pour créer un service de documents."""
    return DocumentService(tenant_id=tenant_id, **kwargs)
