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
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
import re
import time

from sqlalchemy.orm import Session

from .repository import (
    TemplateRepository,
    SectionRepository,
    GeneratedDocumentRepository,
    PresetRepository,
)
from .models import (
    Template,
    TemplateSection,
    GeneratedDocument,
    TemplatePreset,
    TemplateType,
    TemplateStatus,
    OutputFormat,
    VariableType,
    SectionType,
)


# ============================================================
# DATA CLASSES (Styles et Configuration)
# ============================================================

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

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "line_height": self.line_height,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "background_color": self.background_color,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
            "header_height": self.header_height,
            "footer_height": self.footer_height,
            "page_size": self.page_size,
            "orientation": self.orientation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateStyle":
        """Crée depuis un dictionnaire."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


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

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "name": self.name,
            "label": self.label,
            "var_type": self.var_type.value,
            "default_value": self.default_value,
            "required": self.required,
            "format_pattern": self.format_pattern,
            "columns": self.columns,
            "description": self.description,
            "example": self.example,
        }


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

class TemplateService:
    """Service de gestion des templates avec persistance SQLAlchemy."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        # Repositories
        self.template_repo = TemplateRepository(db, tenant_id)
        self.section_repo = SectionRepository(db, tenant_id)
        self.document_repo = GeneratedDocumentRepository(db, tenant_id)
        self.preset_repo = PresetRepository(db, tenant_id)

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
        # Extraire les variables du contenu si non fournies
        variables = kwargs.get("variables")
        if not variables:
            variables = self._extract_variables(content)
        elif isinstance(variables, list) and variables and isinstance(variables[0], TemplateVariable):
            variables = [v.to_dict() for v in variables]

        # Convertir style si fourni
        style = kwargs.get("style")
        style_config = None
        if isinstance(style, TemplateStyle):
            style_config = style.to_dict()
        elif isinstance(style, dict):
            style_config = style

        # Convertir output_formats
        output_formats = kwargs.get("output_formats", [OutputFormat.PDF])

        return self.template_repo.create(
            name=name,
            template_type=template_type,
            content=content,
            variables=variables,
            conditionals=kwargs.get("conditionals"),
            loops=kwargs.get("loops"),
            style_config=style_config,
            custom_css=kwargs.get("custom_css"),
            output_formats=output_formats,
            description=kwargs.get("description"),
            tags=kwargs.get("tags", []),
            created_by=kwargs.get("created_by"),
        )

    def create_from_preset(
        self,
        preset_id: str,
        name: str,
        **kwargs
    ) -> Optional[Template]:
        """Crée un template depuis un preset."""
        return self.preset_repo.create_template_from_preset(
            preset_id=preset_id,
            name=name,
            created_by=kwargs.get("created_by"),
        )

    def get_template(self, template_id: str) -> Optional[Template]:
        """Récupère un template."""
        return self.template_repo.get_by_id(template_id)

    def list_templates(
        self,
        template_type: Optional[TemplateType] = None,
        status: Optional[TemplateStatus] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Template], int]:
        """Liste les templates."""
        return self.template_repo.list_all(
            template_type=template_type,
            status=status,
            tags=tags,
            page=page,
            page_size=page_size,
        )

    def update_template(
        self,
        template_id: str,
        **kwargs
    ) -> Optional[Template]:
        """Met à jour un template."""
        # Convertir style si fourni
        if "style" in kwargs and isinstance(kwargs["style"], TemplateStyle):
            kwargs["style_config"] = kwargs.pop("style").to_dict()

        # Convertir variables si fournies
        if "variables" in kwargs:
            variables = kwargs["variables"]
            if isinstance(variables, list) and variables and isinstance(variables[0], TemplateVariable):
                kwargs["variables"] = [v.to_dict() for v in variables]

        # Re-extraire les variables si le contenu change
        if "content" in kwargs and "variables" not in kwargs:
            kwargs["variables"] = self._extract_variables(kwargs["content"])

        return self.template_repo.update(template_id, **kwargs)

    def delete_template(self, template_id: str) -> bool:
        """Supprime un template."""
        return self.template_repo.delete(template_id)

    def duplicate_template(
        self,
        template_id: str,
        new_name: str
    ) -> Optional[Template]:
        """Duplique un template."""
        return self.template_repo.duplicate(template_id, new_name)

    def set_default(self, template_id: str) -> bool:
        """Définit un template comme défaut pour son type."""
        return self.template_repo.set_default(template_id)

    def get_default_template(
        self,
        template_type: TemplateType
    ) -> Optional[Template]:
        """Récupère le template par défaut pour un type."""
        return self.template_repo.get_default(template_type)

    # ========================================
    # EXTRACTION DE VARIABLES
    # ========================================

    def _extract_variables(self, content: str) -> List[Dict[str, Any]]:
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
                    var_type = self._guess_variable_type(match)
                    variables.append({
                        "name": match,
                        "label": match.replace("_", " ").title(),
                        "var_type": var_type.value,
                        "required": False,
                    })

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
    # SECTIONS DE TEMPLATE
    # ========================================

    def add_section(
        self,
        template_id: str,
        section_type: SectionType,
        content: str,
        **kwargs
    ) -> Optional[TemplateSection]:
        """Ajoute une section à un template."""
        template = self.get_template(template_id)
        if not template:
            return None

        return self.section_repo.create(
            template_id=template_id,
            section_type=section_type,
            content=content,
            css_styles=kwargs.get("css_styles"),
            position=kwargs.get("position", 0),
            show_on_first_page=kwargs.get("show_on_first_page", True),
            show_on_last_page=kwargs.get("show_on_last_page", True),
            show_on_other_pages=kwargs.get("show_on_other_pages", True),
        )

    def update_section(
        self,
        section_id: str,
        **kwargs
    ) -> Optional[TemplateSection]:
        """Met à jour une section."""
        return self.section_repo.update(section_id, **kwargs)

    def delete_section(self, section_id: str) -> bool:
        """Supprime une section."""
        return self.section_repo.delete(section_id)

    def list_sections(self, template_id: str) -> List[TemplateSection]:
        """Liste les sections d'un template."""
        return self.section_repo.list_by_template(template_id)

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
        start_time = time.time()

        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} non trouvé")

        # Valider les données requises
        missing = []
        for var in (template.variables or []):
            if var.get("required") and var.get("name") not in data:
                missing.append(var.get("name"))

        if missing:
            raise ValueError(f"Variables requises manquantes: {', '.join(missing)}")

        # Rendre le contenu
        rendered_content = self._render_content(template.content, data)

        # Appliquer le style
        style = TemplateStyle.from_dict(template.style_config or {})
        full_html = self._wrap_with_style(rendered_content, style, template.custom_css)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Générer le nom de fichier
        file_name = f"{template.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format.value}"

        # Créer l'enregistrement
        document = self.document_repo.create(
            template_id=template_id,
            data=data,
            output_format=output_format,
            file_name=file_name,
            file_size=len(full_html.encode()),
            is_preview=kwargs.get("is_preview", False),
            generation_time_ms=elapsed_ms,
            generated_by=kwargs.get("generated_by"),
        )

        return document

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
    ) -> Dict[str, Any]:
        """Génère un aperçu du template."""
        start_time = time.time()

        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} non trouvé")

        # Utiliser des données exemple si non fournies
        if not data:
            data = self._generate_sample_data(template)

        # Rendre le contenu
        rendered_content = self._render_content(template.content, data)

        # Appliquer le style
        style = TemplateStyle.from_dict(template.style_config or {})
        full_html = self._wrap_with_style(rendered_content, style, template.custom_css)

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "html": full_html,
            "generation_time_ms": elapsed_ms,
            "warnings": [],
        }

    def _generate_sample_data(self, template: Template) -> Dict[str, Any]:
        """Génère des données exemple pour un template."""
        data = {}

        for var in (template.variables or []):
            var_name = var.get("name", "")
            var_type = var.get("var_type", "text")
            example = var.get("example")

            if example:
                data[var_name] = example
            elif var_type == "text":
                data[var_name] = f"Exemple {var.get('label', var_name)}"
            elif var_type == "number":
                data[var_name] = 10
            elif var_type == "currency":
                data[var_name] = "1 234,56 €"
            elif var_type == "date":
                data[var_name] = datetime.now().strftime("%d/%m/%Y")
            elif var_type == "boolean":
                data[var_name] = True
            elif var_type == "table":
                data[var_name] = [
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
        return self.preset_repo.list_all(
            template_type=template_type,
            category=category,
        )

    def get_preset(self, preset_id: str) -> Optional[TemplatePreset]:
        """Récupère un preset."""
        return self.preset_repo.get_by_id(preset_id)

    def create_preset(
        self,
        name: str,
        template_type: TemplateType,
        content: str,
        **kwargs
    ) -> TemplatePreset:
        """Crée un preset."""
        # Convertir style si fourni
        style = kwargs.get("style")
        style_config = None
        if isinstance(style, TemplateStyle):
            style_config = style.to_dict()
        elif isinstance(style, dict):
            style_config = style

        # Convertir variables si fournies
        variables = kwargs.get("variables")
        if isinstance(variables, list) and variables and isinstance(variables[0], TemplateVariable):
            variables = [v.to_dict() for v in variables]

        return self.preset_repo.create(
            name=name,
            template_type=template_type,
            content=content,
            description=kwargs.get("description"),
            style_config=style_config,
            variables=variables,
            category=kwargs.get("category", "default"),
            preview_image_url=kwargs.get("preview_image_url"),
            industry=kwargs.get("industry"),
        )

    # ========================================
    # DOCUMENTS GÉNÉRÉS
    # ========================================

    def get_generated_document(
        self,
        document_id: str
    ) -> Optional[GeneratedDocument]:
        """Récupère un document généré."""
        return self.document_repo.get_by_id(document_id)

    def list_generated_documents(
        self,
        template_id: Optional[str] = None,
        limit: int = 50
    ) -> List[GeneratedDocument]:
        """Liste les documents générés."""
        if template_id:
            return self.document_repo.list_by_template(template_id, limit)

        # Liste générale - pas de méthode dédiée, on récupère par template
        # Pour l'instant, retourner une liste vide
        return []


# ============================================================
# FACTORY
# ============================================================

def create_template_service(
    db: Session,
    tenant_id: str
) -> TemplateService:
    """Crée une instance du service Template."""
    return TemplateService(db=db, tenant_id=tenant_id)
