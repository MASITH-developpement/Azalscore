"""
Service Templates et Document Builder - GAP-057

Gestion des modèles de documents:
- Éditeur de templates WYSIWYG
- Variables dynamiques
- Sections conditionnelles
- Boucles (lignes de facture, etc.)
- Multi-formats (PDF, DOCX, HTML)
- Versioning des templates
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4
import re
import json


# ============================================================
# ÉNUMÉRATIONS
# ============================================================

class TemplateType(Enum):
    """Types de templates."""
    INVOICE = "invoice"
    QUOTE = "quote"
    ORDER = "order"
    DELIVERY_NOTE = "delivery_note"
    CREDIT_NOTE = "credit_note"
    PURCHASE_ORDER = "purchase_order"
    CONTRACT = "contract"
    LETTER = "letter"
    REPORT = "report"
    EMAIL = "email"
    CERTIFICATE = "certificate"
    LABEL = "label"
    CUSTOM = "custom"


class OutputFormat(Enum):
    """Formats de sortie."""
    PDF = "pdf"
    HTML = "html"
    DOCX = "docx"
    ODT = "odt"
    XLSX = "xlsx"
    PNG = "png"
    TEXT = "text"


class VariableType(Enum):
    """Types de variables."""
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    IMAGE = "image"
    BARCODE = "barcode"
    QRCODE = "qrcode"
    TABLE = "table"
    HTML = "html"


class TemplateStatus(Enum):
    """Statut d'un template."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class SectionType(Enum):
    """Types de sections."""
    HEADER = "header"
    BODY = "body"
    FOOTER = "footer"
    SIDEBAR = "sidebar"
    WATERMARK = "watermark"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class TemplateVariable:
    """Variable de template."""
    name: str
    label: str
    var_type: VariableType

    # Valeur par défaut
    default_value: Optional[str] = None

    # Options
    required: bool = False
    format_pattern: Optional[str] = None  # Ex: "dd/MM/yyyy"

    # Pour tables
    columns: List[str] = field(default_factory=list)

    # Description
    description: Optional[str] = None
    example: Optional[str] = None


@dataclass
class ConditionalSection:
    """Section conditionnelle."""
    id: str
    condition: str  # Ex: "{{total}} > 1000"
    content: str
    else_content: Optional[str] = None


@dataclass
class LoopSection:
    """Section de boucle."""
    id: str
    iterator_name: str  # Ex: "line"
    collection_var: str  # Ex: "invoice_lines"
    content: str
    separator: Optional[str] = None


@dataclass
class TemplateSection:
    """Section d'un template."""
    id: str
    section_type: SectionType
    content: str

    # Style
    css_styles: Dict[str, str] = field(default_factory=dict)

    # Position
    position: int = 0

    # Visibilité
    show_on_first_page: bool = True
    show_on_last_page: bool = True
    show_on_other_pages: bool = True


@dataclass
class TemplateStyle:
    """Style global du template."""
    # Polices
    font_family: str = "Arial"
    font_size: int = 10
    line_height: float = 1.5

    # Couleurs
    primary_color: str = "#1a1a1a"
    secondary_color: str = "#666666"
    accent_color: str = "#0066cc"
    background_color: str = "#ffffff"

    # Marges (en mm)
    margin_top: int = 20
    margin_bottom: int = 20
    margin_left: int = 15
    margin_right: int = 15

    # En-tête/Pied de page
    header_height: int = 30
    footer_height: int = 20

    # Page
    page_size: str = "A4"  # A4, Letter, Legal
    orientation: str = "portrait"  # portrait, landscape


@dataclass
class Template:
    """Template de document."""
    id: str
    tenant_id: str
    name: str
    template_type: TemplateType

    # Contenu principal
    content: str  # HTML avec variables

    # Sections
    sections: List[TemplateSection] = field(default_factory=list)

    # Variables
    variables: List[TemplateVariable] = field(default_factory=list)

    # Conditions et boucles
    conditionals: List[ConditionalSection] = field(default_factory=list)
    loops: List[LoopSection] = field(default_factory=list)

    # Style
    style: TemplateStyle = field(default_factory=TemplateStyle)
    custom_css: Optional[str] = None

    # Formats de sortie supportés
    output_formats: List[OutputFormat] = field(default_factory=lambda: [OutputFormat.PDF])

    # État
    status: TemplateStatus = TemplateStatus.DRAFT
    is_default: bool = False

    # Versioning
    version: int = 1
    parent_version_id: Optional[str] = None

    # Métadonnées
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None


@dataclass
class GeneratedDocument:
    """Document généré."""
    id: str
    tenant_id: str
    template_id: str

    # Données utilisées
    data: Dict[str, Any] = field(default_factory=dict)

    # Résultat
    output_format: OutputFormat = OutputFormat.PDF
    content: Optional[bytes] = None
    content_url: Optional[str] = None
    file_name: str = ""
    file_size: int = 0

    # État
    is_preview: bool = False

    # Métadonnées
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: Optional[str] = None
    generation_time_ms: int = 0


@dataclass
class TemplatePreset:
    """Preset de template prédéfini."""
    id: str
    name: str
    template_type: TemplateType
    description: str

    # Contenu
    content: str
    style: TemplateStyle
    variables: List[TemplateVariable]

    # Catégorie
    category: str = "default"
    preview_image_url: Optional[str] = None

    # Industrie
    industry: Optional[str] = None  # retail, services, manufacturing


# ============================================================
# PRESETS PAR DÉFAUT
# ============================================================

def _create_invoice_variables() -> List[TemplateVariable]:
    """Variables pour facture."""
    return [
        TemplateVariable("company_name", "Nom société", VariableType.TEXT, required=True),
        TemplateVariable("company_address", "Adresse société", VariableType.TEXT),
        TemplateVariable("company_siret", "SIRET", VariableType.TEXT),
        TemplateVariable("company_vat", "N° TVA", VariableType.TEXT),
        TemplateVariable("company_logo", "Logo", VariableType.IMAGE),
        TemplateVariable("invoice_number", "N° Facture", VariableType.TEXT, required=True),
        TemplateVariable("invoice_date", "Date facture", VariableType.DATE, format_pattern="dd/MM/yyyy"),
        TemplateVariable("due_date", "Date échéance", VariableType.DATE),
        TemplateVariable("customer_name", "Nom client", VariableType.TEXT, required=True),
        TemplateVariable("customer_address", "Adresse client", VariableType.TEXT),
        TemplateVariable("customer_vat", "N° TVA client", VariableType.TEXT),
        TemplateVariable("lines", "Lignes", VariableType.TABLE, columns=["description", "quantity", "unit_price", "vat_rate", "total"]),
        TemplateVariable("subtotal", "Total HT", VariableType.CURRENCY),
        TemplateVariable("vat_amount", "TVA", VariableType.CURRENCY),
        TemplateVariable("total", "Total TTC", VariableType.CURRENCY),
        TemplateVariable("payment_terms", "Conditions paiement", VariableType.TEXT),
        TemplateVariable("notes", "Notes", VariableType.TEXT),
        TemplateVariable("qrcode", "QR Code paiement", VariableType.QRCODE),
    ]


DEFAULT_INVOICE_TEMPLATE = """
<div class="invoice">
    <header class="invoice-header">
        <div class="company-info">
            {{#if company_logo}}<img src="{{company_logo}}" class="logo" />{{/if}}
            <h1>{{company_name}}</h1>
            <p>{{company_address}}</p>
            <p>SIRET: {{company_siret}} | TVA: {{company_vat}}</p>
        </div>
        <div class="invoice-info">
            <h2>FACTURE</h2>
            <p><strong>N°:</strong> {{invoice_number}}</p>
            <p><strong>Date:</strong> {{invoice_date}}</p>
            <p><strong>Échéance:</strong> {{due_date}}</p>
        </div>
    </header>

    <section class="customer">
        <h3>Client</h3>
        <p><strong>{{customer_name}}</strong></p>
        <p>{{customer_address}}</p>
        {{#if customer_vat}}<p>TVA: {{customer_vat}}</p>{{/if}}
    </section>

    <section class="lines">
        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Qté</th>
                    <th>Prix unit. HT</th>
                    <th>TVA</th>
                    <th>Total HT</th>
                </tr>
            </thead>
            <tbody>
                {{#each lines}}
                <tr>
                    <td>{{description}}</td>
                    <td>{{quantity}}</td>
                    <td>{{unit_price}}</td>
                    <td>{{vat_rate}}%</td>
                    <td>{{total}}</td>
                </tr>
                {{/each}}
            </tbody>
        </table>
    </section>

    <section class="totals">
        <table>
            <tr><td>Total HT</td><td>{{subtotal}}</td></tr>
            <tr><td>TVA</td><td>{{vat_amount}}</td></tr>
            <tr class="total"><td>Total TTC</td><td>{{total}}</td></tr>
        </table>
    </section>

    {{#if payment_terms}}
    <section class="payment">
        <p><strong>Conditions de paiement:</strong> {{payment_terms}}</p>
    </section>
    {{/if}}

    {{#if notes}}
    <section class="notes">
        <p>{{notes}}</p>
    </section>
    {{/if}}

    {{#if qrcode}}
    <div class="qrcode">{{qrcode}}</div>
    {{/if}}
</div>
"""


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

class TemplateService:
    """Service de gestion des templates."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage en mémoire (à remplacer par DB)
        self._templates: Dict[str, Template] = {}
        self._generated_documents: Dict[str, GeneratedDocument] = {}
        self._presets: Dict[str, TemplatePreset] = {}

        # Charger les presets par défaut
        self._load_default_presets()

    def _load_default_presets(self) -> None:
        """Charge les presets par défaut."""
        self._presets["invoice_classic"] = TemplatePreset(
            id="invoice_classic",
            name="Facture Classique",
            template_type=TemplateType.INVOICE,
            description="Modèle de facture classique avec logo, tableau des lignes et totaux",
            content=DEFAULT_INVOICE_TEMPLATE,
            style=TemplateStyle(),
            variables=_create_invoice_variables(),
            category="business",
        )

    # ========================================
    # GESTION DES TEMPLATES
    # ========================================

    def create_template(
        self,
        name: str,
        template_type: TemplateType,
        content: str,
        **kwargs
    ) -> Template:
        """Crée un template."""
        template = Template(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            template_type=template_type,
            content=content,
            variables=kwargs.get("variables", []),
            style=kwargs.get("style", TemplateStyle()),
            custom_css=kwargs.get("custom_css"),
            output_formats=kwargs.get("output_formats", [OutputFormat.PDF]),
            description=kwargs.get("description"),
            tags=kwargs.get("tags", []),
            created_by=kwargs.get("created_by"),
        )

        # Extraire les variables du contenu
        if not template.variables:
            template.variables = self._extract_variables(content)

        self._templates[template.id] = template
        return template

    def create_from_preset(
        self,
        preset_id: str,
        name: str,
        **kwargs
    ) -> Optional[Template]:
        """Crée un template depuis un preset."""
        preset = self._presets.get(preset_id)
        if not preset:
            return None

        return self.create_template(
            name=name,
            template_type=preset.template_type,
            content=preset.content,
            variables=preset.variables.copy(),
            style=preset.style,
            **kwargs
        )

    def get_template(self, template_id: str) -> Optional[Template]:
        """Récupère un template."""
        template = self._templates.get(template_id)
        if template and template.tenant_id == self.tenant_id:
            return template
        return None

    def list_templates(
        self,
        template_type: Optional[TemplateType] = None,
        status: Optional[TemplateStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[Template]:
        """Liste les templates."""
        templates = [
            t for t in self._templates.values()
            if t.tenant_id == self.tenant_id
        ]

        if template_type:
            templates = [t for t in templates if t.template_type == template_type]
        if status:
            templates = [t for t in templates if t.status == status]
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]

        return sorted(templates, key=lambda x: x.created_at, reverse=True)

    def update_template(
        self,
        template_id: str,
        **kwargs
    ) -> Optional[Template]:
        """Met à jour un template."""
        template = self.get_template(template_id)
        if not template:
            return None

        if "name" in kwargs:
            template.name = kwargs["name"]
        if "content" in kwargs:
            template.content = kwargs["content"]
            # Re-extraire les variables
            if "variables" not in kwargs:
                template.variables = self._extract_variables(kwargs["content"])
        if "variables" in kwargs:
            template.variables = kwargs["variables"]
        if "style" in kwargs:
            template.style = kwargs["style"]
        if "custom_css" in kwargs:
            template.custom_css = kwargs["custom_css"]
        if "status" in kwargs:
            template.status = kwargs["status"]
        if "tags" in kwargs:
            template.tags = kwargs["tags"]

        template.updated_at = datetime.now()
        template.version += 1

        return template

    def delete_template(self, template_id: str) -> bool:
        """Supprime un template."""
        template = self.get_template(template_id)
        if not template:
            return False

        del self._templates[template_id]
        return True

    def duplicate_template(
        self,
        template_id: str,
        new_name: str
    ) -> Optional[Template]:
        """Duplique un template."""
        template = self.get_template(template_id)
        if not template:
            return None

        return self.create_template(
            name=new_name,
            template_type=template.template_type,
            content=template.content,
            variables=[v for v in template.variables],
            style=template.style,
            custom_css=template.custom_css,
            output_formats=template.output_formats.copy(),
            tags=template.tags.copy(),
        )

    def set_default(self, template_id: str) -> bool:
        """Définit un template comme défaut pour son type."""
        template = self.get_template(template_id)
        if not template:
            return False

        # Retirer le défaut des autres templates du même type
        for t in self._templates.values():
            if (t.tenant_id == self.tenant_id and
                t.template_type == template.template_type and
                t.is_default):
                t.is_default = False

        template.is_default = True
        template.updated_at = datetime.now()
        return True

    def get_default_template(
        self,
        template_type: TemplateType
    ) -> Optional[Template]:
        """Récupère le template par défaut pour un type."""
        for template in self._templates.values():
            if (template.tenant_id == self.tenant_id and
                template.template_type == template_type and
                template.is_default):
                return template
        return None

    # ========================================
    # EXTRACTION DE VARIABLES
    # ========================================

    def _extract_variables(self, content: str) -> List[TemplateVariable]:
        """Extrait les variables d'un contenu template."""
        variables = []
        seen = set()

        # Pattern pour {{variable}} et {{#each variable}}
        patterns = [
            r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}',
            r'\{\{#each\s+([a-zA-Z_][a-zA-Z0-9_]*)\}\}',
            r'\{\{#if\s+([a-zA-Z_][a-zA-Z0-9_]*)\}\}',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in seen:
                    seen.add(match)
                    variables.append(TemplateVariable(
                        name=match,
                        label=match.replace("_", " ").title(),
                        var_type=self._guess_variable_type(match),
                    ))

        return variables

    def _guess_variable_type(self, name: str) -> VariableType:
        """Devine le type d'une variable selon son nom."""
        name_lower = name.lower()

        if any(x in name_lower for x in ["date", "created", "updated", "due"]):
            return VariableType.DATE
        if any(x in name_lower for x in ["price", "amount", "total", "subtotal", "vat"]):
            return VariableType.CURRENCY
        if any(x in name_lower for x in ["quantity", "count", "number", "qty"]):
            return VariableType.NUMBER
        if any(x in name_lower for x in ["logo", "image", "photo", "picture"]):
            return VariableType.IMAGE
        if any(x in name_lower for x in ["lines", "items", "products"]):
            return VariableType.TABLE
        if any(x in name_lower for x in ["qrcode", "qr"]):
            return VariableType.QRCODE
        if any(x in name_lower for x in ["barcode", "ean", "upc"]):
            return VariableType.BARCODE
        if any(x in name_lower for x in ["is_", "has_", "show_", "enabled"]):
            return VariableType.BOOLEAN

        return VariableType.TEXT

    # ========================================
    # GÉNÉRATION DE DOCUMENTS
    # ========================================

    def render(
        self,
        template_id: str,
        data: Dict[str, Any],
        output_format: OutputFormat = OutputFormat.HTML,
        **kwargs
    ) -> GeneratedDocument:
        """Génère un document à partir d'un template."""
        import time
        start_time = time.time()

        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} non trouvé")

        # Valider les données requises
        missing = []
        for var in template.variables:
            if var.required and var.name not in data:
                missing.append(var.name)

        if missing:
            raise ValueError(f"Variables requises manquantes: {', '.join(missing)}")

        # Rendre le contenu
        rendered_content = self._render_content(template.content, data)

        # Appliquer le style
        full_html = self._wrap_with_style(rendered_content, template.style, template.custom_css)

        # Convertir au format de sortie
        if output_format == OutputFormat.HTML:
            content = full_html.encode()
        elif output_format == OutputFormat.PDF:
            # En production: utiliser weasyprint ou wkhtmltopdf
            content = f"<PDF>{full_html}</PDF>".encode()
        elif output_format == OutputFormat.DOCX:
            # En production: utiliser python-docx
            content = f"<DOCX>{full_html}</DOCX>".encode()
        else:
            content = full_html.encode()

        elapsed_ms = int((time.time() - start_time) * 1000)

        doc = GeneratedDocument(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            template_id=template_id,
            data=data,
            output_format=output_format,
            content=content,
            file_name=f"{template.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format.value}",
            file_size=len(content),
            is_preview=kwargs.get("is_preview", False),
            generated_by=kwargs.get("generated_by"),
            generation_time_ms=elapsed_ms,
        )

        self._generated_documents[doc.id] = doc
        return doc

    def _render_content(self, content: str, data: Dict[str, Any]) -> str:
        """Rend le contenu avec les données."""
        rendered = content

        # Remplacer les boucles {{#each}}
        each_pattern = r'\{\{#each\s+(\w+)\}\}(.*?)\{\{/each\}\}'

        def replace_each(match):
            var_name = match.group(1)
            loop_content = match.group(2)
            items = data.get(var_name, [])

            result = []
            for item in items:
                item_rendered = loop_content
                if isinstance(item, dict):
                    for key, value in item.items():
                        item_rendered = item_rendered.replace(f"{{{{{key}}}}}", str(value or ""))
                result.append(item_rendered)

            return "".join(result)

        rendered = re.sub(each_pattern, replace_each, rendered, flags=re.DOTALL)

        # Remplacer les conditions {{#if}}
        if_pattern = r'\{\{#if\s+(\w+)\}\}(.*?)(?:\{\{else\}\}(.*?))?\{\{/if\}\}'

        def replace_if(match):
            var_name = match.group(1)
            if_content = match.group(2)
            else_content = match.group(3) or ""

            value = data.get(var_name)
            if value:
                return if_content
            return else_content

        rendered = re.sub(if_pattern, replace_if, rendered, flags=re.DOTALL)

        # Remplacer les variables simples {{var}}
        var_pattern = r'\{\{(\w+)\}\}'

        def replace_var(match):
            var_name = match.group(1)
            value = data.get(var_name, "")
            return str(value) if value is not None else ""

        rendered = re.sub(var_pattern, replace_var, rendered)

        return rendered

    def _wrap_with_style(
        self,
        content: str,
        style: TemplateStyle,
        custom_css: Optional[str] = None
    ) -> str:
        """Enveloppe le contenu avec les styles."""
        css = f"""
        @page {{
            size: {style.page_size} {style.orientation};
            margin: {style.margin_top}mm {style.margin_right}mm {style.margin_bottom}mm {style.margin_left}mm;
        }}
        body {{
            font-family: {style.font_family}, sans-serif;
            font-size: {style.font_size}pt;
            line-height: {style.line_height};
            color: {style.primary_color};
            background-color: {style.background_color};
        }}
        h1, h2, h3 {{ color: {style.primary_color}; }}
        .secondary {{ color: {style.secondary_color}; }}
        .accent {{ color: {style.accent_color}; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f5f5f5; text-align: left; }}
        .total {{ font-weight: bold; font-size: 1.2em; }}
        """

        if custom_css:
            css += custom_css

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>{css}</style>
</head>
<body>
{content}
</body>
</html>"""

    def preview(
        self,
        template_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> GeneratedDocument:
        """Génère un aperçu du template."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} non trouvé")

        # Utiliser des données exemple si non fournies
        if not data:
            data = self._generate_sample_data(template)

        return self.render(
            template_id,
            data,
            OutputFormat.HTML,
            is_preview=True
        )

    def _generate_sample_data(self, template: Template) -> Dict[str, Any]:
        """Génère des données exemple pour un template."""
        data = {}

        for var in template.variables:
            if var.var_type == VariableType.TEXT:
                data[var.name] = var.example or f"Exemple {var.label}"
            elif var.var_type == VariableType.NUMBER:
                data[var.name] = 10
            elif var.var_type == VariableType.CURRENCY:
                data[var.name] = "1 234,56 €"
            elif var.var_type == VariableType.DATE:
                data[var.name] = datetime.now().strftime("%d/%m/%Y")
            elif var.var_type == VariableType.BOOLEAN:
                data[var.name] = True
            elif var.var_type == VariableType.TABLE:
                data[var.name] = [
                    {"description": "Article 1", "quantity": 2, "unit_price": "100,00 €", "vat_rate": 20, "total": "200,00 €"},
                    {"description": "Article 2", "quantity": 1, "unit_price": "50,00 €", "vat_rate": 20, "total": "50,00 €"},
                ]

        return data

    # ========================================
    # PRESETS
    # ========================================

    def list_presets(
        self,
        template_type: Optional[TemplateType] = None,
        category: Optional[str] = None
    ) -> List[TemplatePreset]:
        """Liste les presets disponibles."""
        presets = list(self._presets.values())

        if template_type:
            presets = [p for p in presets if p.template_type == template_type]
        if category:
            presets = [p for p in presets if p.category == category]

        return sorted(presets, key=lambda x: x.name)

    def get_preset(self, preset_id: str) -> Optional[TemplatePreset]:
        """Récupère un preset."""
        return self._presets.get(preset_id)

    # ========================================
    # DOCUMENTS GÉNÉRÉS
    # ========================================

    def get_generated_document(
        self,
        document_id: str
    ) -> Optional[GeneratedDocument]:
        """Récupère un document généré."""
        doc = self._generated_documents.get(document_id)
        if doc and doc.tenant_id == self.tenant_id:
            return doc
        return None

    def list_generated_documents(
        self,
        template_id: Optional[str] = None,
        limit: int = 50
    ) -> List[GeneratedDocument]:
        """Liste les documents générés."""
        docs = [
            d for d in self._generated_documents.values()
            if d.tenant_id == self.tenant_id and not d.is_preview
        ]

        if template_id:
            docs = [d for d in docs if d.template_id == template_id]

        return sorted(docs, key=lambda x: x.generated_at, reverse=True)[:limit]


# ============================================================
# FACTORY
# ============================================================

def create_template_service(tenant_id: str) -> TemplateService:
    """Crée une instance du service Template."""
    return TemplateService(tenant_id=tenant_id)
